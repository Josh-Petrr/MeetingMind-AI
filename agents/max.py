"""
MeetingMind AI - Max: Memory Agent
====================================
Max is the "Meeting Archivist" of the Agentic Squad.

Responsibilities:
- Evaluate the significance of meeting outputs (summaries, action items, decisions)
- Score each item on a 0-10 scale for long-term memory storage
- Determine which items should be stored in Qdrant vector memory
- Retrieve relevant historical context for new meetings (Memory Loop)

Input: Boris's summary + Anna's extractions
Output: Significance scores + memory storage decisions
"""

import json
from typing import Optional

from agents.lyzr_manager import LyzrManager
from memory.qdrant_store import QdrantMemoryStore
from utils.embeddings import EmbeddingService


# Max's detailed instructions
MAX_INSTRUCTIONS = """You are Max, the Meeting Archivist and Memory Agent for MeetingMind AI.

YOUR ROLE:
You receive processed meeting outputs (summaries, action items, decisions) from other agents
and evaluate their significance for long-term organizational memory.

YOUR OUTPUT FORMAT:
You MUST return ONLY a valid JSON object with NO markdown formatting, NO code blocks, NO extra text.
Return exactly this structure:

{
    "memory_items": [
        {
            "text": "The content to be stored in long-term memory",
            "memory_type": "summary|action_item|decision",
            "significance_score": 8.5,
            "reasoning": "Why this item is significant for organizational memory",
            "should_store": true
        }
    ],
    "meeting_significance": 7.5,
    "meeting_significance_reasoning": "Overall assessment of this meeting's importance"
}

SCORING GUIDELINES:
- 9-10: Critical organizational decisions, strategic pivots, high-impact blockers
- 7-8: Important action items with deadlines, significant technical decisions
- 5-6: Routine updates, standard progress reports
- 3-4: Minor details, casual remarks
- 1-2: Off-topic chat, pleasantries

RULES:
1. Score EVERY summary, action item, and decision provided to you.
2. Set should_store=true for items scoring >= 6.0 (these go to long-term memory).
3. Set should_store=false for items scoring < 6.0 (these are transient).
4. User-starred items always get should_store=true regardless of score.
5. Be conservative — only truly significant items should have high scores.
6. Do NOT hallucinate or modify the original text content.
7. Return ONLY the JSON object. No markdown, no explanations, no code fences.
"""


class MaxAgent:
    """Max: Meeting Archivist and Memory Agent."""

    AGENT_NAME = "Max"
    AGENT_ROLE = "Meeting Archivist and Memory Agent"
    AGENT_GOAL = (
        "Evaluate the significance of meeting outputs and manage long-term "
        "organizational memory in Qdrant vector database."
    )

    # Items scoring at or above this threshold are stored in Qdrant
    STORAGE_THRESHOLD = 6.0

    def __init__(
        self,
        manager: Optional[LyzrManager] = None,
        memory_store: Optional[QdrantMemoryStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize Max.

        Args:
            manager: LyzrManager instance. Creates one if not provided.
            memory_store: QdrantMemoryStore instance. Creates one if not provided.
            embedding_service: EmbeddingService instance. Creates one if not provided.
        """
        self.manager = manager or LyzrManager()
        self.memory_store = memory_store or QdrantMemoryStore()
        self.embedding_service = embedding_service or EmbeddingService()
        self.agent_id = self._ensure_agent()

    def _ensure_agent(self) -> str:
        """Create Max on Lyzr platform (or return cached ID)."""
        return self.manager.create_agent(
            name=self.AGENT_NAME,
            role=self.AGENT_ROLE,
            goal=self.AGENT_GOAL,
            instructions=MAX_INSTRUCTIONS,
            description="MeetingMind AI Memory Agent - manages organizational memory",
        )

    def evaluate_and_store(
        self,
        boris_output: dict,
        anna_output: dict,
        org_id: str,
        meeting_id: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Evaluate meeting outputs for significance and store worthy items in Qdrant.

        Args:
            boris_output: Boris's structured summary output.
            anna_output: Anna's structured action items and decisions output.
            org_id: Organization ID for data isolation.
            meeting_id: Meeting ID for this meeting.
            session_id: Optional session ID for conversation continuity.

        Returns:
            Dict with memory_items (scored), stored_count, and skipped_count.
        """
        # Build the prompt with all meeting outputs
        prompt = self._build_evaluation_prompt(boris_output, anna_output)

        # Send to Max via Lyzr for significance scoring
        raw_response = self.manager.chat(
            agent_id=self.agent_id,
            message=prompt,
            session_id=session_id,
        )

        # Parse Max's scoring response
        evaluation = self._parse_response(raw_response)

        # Store worthy items in Qdrant
        stored_count = 0
        skipped_count = 0

        for item in evaluation.get("memory_items", []):
            if item.get("should_store", False):
                try:
                    # Generate embedding for the memory text
                    embedding = self.embedding_service.embed(item["text"])

                    # Store in Qdrant
                    self.memory_store.store_memory(
                        text=item["text"],
                        embedding=embedding,
                        memory_type=item.get("memory_type", "summary"),
                        org_id=org_id,
                        meeting_id=meeting_id,
                        significance_score=item.get("significance_score", 5.0),
                        extra_metadata={
                            "reasoning": item.get("reasoning", ""),
                        },
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"[WARN] Failed to store memory item: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1

        evaluation["stored_count"] = stored_count
        evaluation["skipped_count"] = skipped_count

        print(
            f"[INFO] Max stored {stored_count} items, "
            f"skipped {skipped_count} items for meeting {meeting_id}"
        )

        return evaluation

    def retrieve_context(
        self,
        transcript_snippet: str,
        org_id: str,
        top_k: int = 5,
    ) -> str:
        """
        Retrieve relevant historical context from Qdrant for a new meeting.
        This is the "Memory Loop" — priming Boris and Anna with past context.

        Args:
            transcript_snippet: A snippet or summary of the new meeting's topic.
            org_id: Organization ID for data isolation.
            top_k: Number of past memories to retrieve.

        Returns:
            Formatted string of relevant past context, ready to inject into prompts.
        """
        # Generate embedding for the query
        query_embedding = self.embedding_service.embed(transcript_snippet)

        # Search Qdrant for relevant past memories
        results = self.memory_store.search(
            query_embedding=query_embedding,
            org_id=org_id,
            top_k=top_k,
        )

        if not results:
            return ""

        # Format results as context string
        context_parts = ["RELEVANT CONTEXT FROM PAST MEETINGS:"]
        for i, mem in enumerate(results, 1):
            context_parts.append(
                f"\n[{i}] ({mem['memory_type'].upper()}, "
                f"relevance: {mem['score']:.2f}, "
                f"significance: {mem['significance_score']}/10)\n"
                f"   {mem['text']}"
            )

        return "\n".join(context_parts)

    def _build_evaluation_prompt(self, boris_output: dict, anna_output: dict) -> str:
        """Build the evaluation prompt with Boris and Anna's outputs."""
        parts = ["Please evaluate the following meeting outputs for significance:\n"]

        # Boris's summary
        parts.append("=== SUMMARY (from Boris) ===")
        parts.append(boris_output.get("summary", "No summary available"))
        parts.append("")

        # Boris's decisions
        decisions_from_boris = boris_output.get("decisions", [])
        if decisions_from_boris:
            parts.append("=== DECISIONS (from Boris) ===")
            for d in decisions_from_boris:
                if isinstance(d, dict):
                    parts.append(f"- {d.get('decision', str(d))}")
                else:
                    parts.append(f"- {d}")
            parts.append("")

        # Anna's action items
        action_items = anna_output.get("action_items", [])
        if action_items:
            parts.append("=== ACTION ITEMS (from Anna) ===")
            for ai in action_items:
                if isinstance(ai, dict):
                    parts.append(
                        f"- {ai.get('task', 'Unknown task')} "
                        f"(Owner: {ai.get('owner', 'Unassigned')}, "
                        f"Deadline: {ai.get('deadline', 'Not specified')})"
                    )
                else:
                    parts.append(f"- {ai}")
            parts.append("")

        # Anna's decisions
        decisions_from_anna = anna_output.get("decisions", [])
        if decisions_from_anna:
            parts.append("=== DECISIONS (from Anna) ===")
            for d in decisions_from_anna:
                if isinstance(d, dict):
                    parts.append(f"- {d.get('decision', str(d))}")
                else:
                    parts.append(f"- {d}")
            parts.append("")

        parts.append(
            "Score each item for long-term memory significance and return "
            "the JSON evaluation."
        )

        return "\n".join(parts)

    def _parse_response(self, raw: str) -> dict:
        """Parse Max's JSON response."""
        text = raw.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    result = json.loads(text[start:end])
                except json.JSONDecodeError:
                    result = {
                        "memory_items": [],
                        "meeting_significance": 5.0,
                        "meeting_significance_reasoning": "Failed to parse Max's evaluation",
                        "_parse_error": "Failed to parse structured JSON from Max",
                    }
            else:
                result = {
                    "memory_items": [],
                    "meeting_significance": 5.0,
                    "meeting_significance_reasoning": "No JSON found in Max's response",
                    "_parse_error": "No JSON found in Max's response",
                }

        return result
