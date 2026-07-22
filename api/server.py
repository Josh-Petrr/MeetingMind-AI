"""
MeetingMind AI - FastAPI Backend Server
=========================================
REST API exposing the MeetingMind Agentic Pipeline.

Endpoints:
- POST /process-meeting : Upload a meeting transcript for full processing
- GET /review/{meeting_id} : Get the extracted summary and action items for a meeting
- GET /memory/search : Semantic search across past meeting memories

Usage:
    uvicorn api.server:app --reload --port 8000
"""

import sys
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import json
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import MeetingOrchestrator
from memory.qdrant_store import QdrantMemoryStore
from utils.embeddings import EmbeddingService
from memory.db import db_manager

app = FastAPI(
    title="MeetingMind AI API",
    description="Agentic Meeting Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for the hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances for the API
try:
    orchestrator = MeetingOrchestrator()
    memory_store = QdrantMemoryStore()
    embedding_service = EmbeddingService()
    print("[INFO] API Services Initialized Successfully.")
except Exception as e:
    print(f"[ERROR] Failed to initialize API services: {e}")
    # We don't exit here so the API can still start and return 500s, 
    # but in production you might want to fail fast.


# --- Request/Response Models ---

class ProcessMeetingRequest(BaseModel):
    transcript: str
    org_id: str
    meeting_id: Optional[str] = None
    skip_memory_retrieval: bool = False

class ProcessMeetingResponse(BaseModel):
    meeting_id: str
    status: str
    message: str

class SearchRequest(BaseModel):
    query: str
    org_id: str
    top_k: int = 5
    memory_type: Optional[str] = None
    min_significance: Optional[float] = None

class ChatRequest(BaseModel):
    query: str
    org_id: str
    history: Optional[List[dict]] = None


# Database Manager handles meeting data internally


def run_pipeline_background(request: ProcessMeetingRequest, meeting_id: str):
    """Run the orchestrator pipeline in the background and save results."""
    try:
        print(f"[INFO] Starting background processing for meeting {meeting_id}...")
        result = orchestrator.process_meeting(
            transcript=request.transcript,
            org_id=request.org_id,
            meeting_id=meeting_id,
            skip_memory_retrieval=request.skip_memory_retrieval,
        )
        
        # Save results to PostgreSQL database
        db_manager.save_meeting(meeting_id, request.org_id, "completed", result)
            
        print(f"[INFO] Background processing complete for meeting {meeting_id}.")
    except Exception as e:
        print(f"[ERROR] Pipeline failed for meeting {meeting_id}: {e}")
        # Save error state to DB
        db_manager.save_meeting(meeting_id, request.org_id, "error", {"meeting_id": meeting_id, "pipeline_status": "error", "error": str(e)})


# --- Endpoints ---

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "MeetingMind AI API"}


@app.post("/process-meeting", response_model=ProcessMeetingResponse)
def process_meeting(request: ProcessMeetingRequest, background_tasks: BackgroundTasks):
    """
    Submit a meeting transcript for asynchronous processing.
    The pipeline will mask PII, summarize, extract actions, and store memories.
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")
        
    meeting_id = request.meeting_id or f"meeting_{uuid.uuid4().hex[:8]}"
    
    # Run the heavy pipeline in the background so we return immediately
    background_tasks.add_task(run_pipeline_background, request, meeting_id)
    
    return ProcessMeetingResponse(
        meeting_id=meeting_id,
        status="processing",
        message="Meeting processing started in the background. Check /review/{meeting_id} for results."
    )


@app.get("/meetings")
def list_meetings(org_id: Optional[str] = "org_demo_123"):
    """
    List all processed meetings stored in the database.
    """
    meetings = []
    rows = db_manager.list_meetings(org_id)
    for row in rows:
        mdata = row["data"] or {}
        boris_output = mdata.get("boris_output") or {}
        anna_output = mdata.get("anna_output") or {}
        
        # Robustly extract the summary text
        summary_text = ""
        if isinstance(boris_output, dict):
            summary_text = boris_output.get("summary", "")
        elif isinstance(boris_output, str):
            summary_text = boris_output
            
        # If the extracted summary_text is actually a stringified JSON (due to parser fallback), extract the real summary
        if isinstance(summary_text, str) and summary_text.strip().startswith("{"):
            import re
            try:
                clean_str = summary_text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_str)
                summary_text = parsed.get("summary", summary_text)
            except Exception:
                match = re.search(r'"summary"\s*:\s*"([\s\S]*?)"(?=\s*,\s*"key_topics"|\s*,\s*"decisions"|\s*\})', summary_text)
                if match:
                    summary_text = match.group(1).replace('\\n', '\n').replace('\\"', '"')
                    
        # Parse anna_output if it's a string
        if isinstance(anna_output, str):
            try:
                clean_str = anna_output.replace("```json", "").replace("```", "").strip()
                anna_output = json.loads(clean_str)
            except Exception:
                anna_output = {}
        
        meetings.append({
            "meeting_id": row["meeting_id"],
            "org_id": row["org_id"],
            "status": row["pipeline_status"],
            "action_items_count": anna_output.get("total_action_items", 0) if isinstance(anna_output, dict) else 0,
            "decisions_count": anna_output.get("total_decisions", 0) if isinstance(anna_output, dict) else 0,
            "summary_snippet": (summary_text[:120] + "...") if summary_text else "No summary available"
        })

    return {"meetings": meetings}


@app.get("/review/{meeting_id}")
def review_meeting(meeting_id: str):
    """
    Get the processed summary and action items for a meeting.
    """
    # Fetch from Postgres
    meeting_data = db_manager.get_meeting(meeting_id)
    if meeting_data:
        return meeting_data
            
    raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found or still processing.")


@app.post("/memory/search")
def search_memory(request: SearchRequest):
    """
    Search past meeting memories using semantic similarity.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
        
    try:
        # Embed the query
        query_embedding = embedding_service.embed(request.query)
        
        # Search Qdrant
        results = memory_store.search(
            query_embedding=query_embedding,
            org_id=request.org_id,
            top_k=request.top_k,
            memory_type=request.memory_type,
            min_significance=request.min_significance,
        )
        
        return {"query": request.query, "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/chat")
def chat_with_memory(request: ChatRequest):
    """Interactive RAG chat endpoint."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    try:
        query_embedding = embedding_service.embed(request.query)
        memories = memory_store.search(
            query_embedding=query_embedding,
            org_id=request.org_id,
            top_k=5,
        )
        
        context_blocks = []
        for mem in memories:
            context_blocks.append(f"- {mem['text']}")
        context_str = "\n".join(context_blocks)
        
        prompt = f"""You are a helpful AI assistant with access to the organization's past meeting memories.
Answer the user's question clearly and concisely using ONLY the provided memory snippets below. 
If the answer is not in the context, say you don't know based on past meetings. Do not hallucinate.

CONTEXT MEMORIES:
{context_str}

USER QUESTION:
{request.query}
"""
        
        agent_id = orchestrator.lyzr_manager.create_agent(
            name="RAG Assistant",
            role="Knowledge Retrieval Assistant",
            goal="Answer questions strictly using provided context",
            instructions="Answer using only the context provided. Do not hallucinate.",
            description="Chat agent"
        )
        
        raw_response = orchestrator.lyzr_manager.chat(
            agent_id=agent_id,
            message=prompt
        )
        
        return {
            "answer": raw_response,
            "sources": memories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
