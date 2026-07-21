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

app = FastAPI(
    title="MeetingMind AI API",
    description="Agentic Meeting Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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


# --- Helper Methods ---

def get_meeting_data_path(meeting_id: str) -> str:
    """Helper to get the path to save/load meeting data."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "meetings")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, f"{meeting_id}.json")


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
        
        # Save results to a file (in a real app, this goes to PostgreSQL/Supabase)
        output_path = get_meeting_data_path(meeting_id)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"[INFO] Background processing complete for meeting {meeting_id}.")
    except Exception as e:
        print(f"[ERROR] Pipeline failed for meeting {meeting_id}: {e}")
        # Save error state
        output_path = get_meeting_data_path(meeting_id)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"meeting_id": meeting_id, "pipeline_status": "error", "error": str(e)}, f)


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
    List all processed meetings stored in the data directory.
    """
    meetings = []
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "meetings")
    
    # Check custom processed meetings
    if os.path.exists(data_dir):
        for fname in os.listdir(data_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(data_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        mdata = json.load(f)
                        meetings.append({
                            "meeting_id": mdata.get("meeting_id", fname.replace(".json", "")),
                            "org_id": mdata.get("org_id", "Unknown"),
                            "status": mdata.get("pipeline_status", "completed"),
                            "action_items_count": mdata.get("anna_output", {}).get("total_action_items", 0),
                            "decisions_count": mdata.get("anna_output", {}).get("total_decisions", 0),
                            "summary_snippet": mdata.get("boris_output", {}).get("summary", "")[:120] + "..." if mdata.get("boris_output", {}).get("summary") else "No summary available"
                        })
                except Exception:
                    pass

    # Check demo meeting output if present
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pipeline_output.json")
    if os.path.exists(demo_path) and not any(m["meeting_id"] == "meeting_demo_001" for m in meetings):
        try:
            with open(demo_path, "r", encoding="utf-8") as f:
                mdata = json.load(f)
                meetings.append({
                    "meeting_id": "meeting_demo_001",
                    "org_id": mdata.get("org_id", "org_demo_001"),
                    "status": "completed",
                    "action_items_count": mdata.get("anna_output", {}).get("total_action_items", 0),
                    "decisions_count": mdata.get("anna_output", {}).get("total_decisions", 0),
                    "summary_snippet": mdata.get("boris_output", {}).get("summary", "")[:120] + "..."
                })
        except Exception:
            pass

    return {"meetings": meetings}


@app.get("/review/{meeting_id}")
def review_meeting(meeting_id: str):
    """
    Get the processed summary and action items for a meeting.
    """
    output_path = get_meeting_data_path(meeting_id)
    
    # Check if the specific meeting file exists
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # For hackathon demo purposes, if it's the demo meeting, check the root data folder
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pipeline_output.json")
    if meeting_id == "meeting_demo_001" and os.path.exists(demo_path):
        with open(demo_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
