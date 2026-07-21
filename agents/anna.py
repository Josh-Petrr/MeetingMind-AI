"""
MeetingMind AI - Anna: Action Item & Decision Extractor
=========================================================
Anna is the "Precision Task Extractor" of the Agentic Squad.

Responsibilities:
- Extract structured action items with Owner, Task, and Deadline
- Extract explicit decisions made during the meeting
- Use Gemini 1.5 Flash for high-speed, structured extraction
- Return clean JSON for downstream processing

Input: PII-masked meeting transcript
Output: Structured JSON with action_items and decisions arrays
"""

import json
from typing import Optional

from agents.lyzr_manager import LyzrManager


# Anna's detailed instructions
ANNA_INSTRUCTIONS = """You are Anna, a Precision Task and Decision Extractor for MeetingMind AI.

YOUR ROLE:
You receive PII-masked meeting transcripts and extract every action item and decision with surgical precision.

YOUR OUTPUT FORMAT:
You MUST return ONLY a valid JSON object with NO markdown formatting, NO code blocks, NO extra text.
Return exactly this structure:

{
    "action_items": [
        {
            "task": "Clear description of what needs to be done",
            "owner": "Name of the person responsible (use masked name if PII-masked)",
            "deadline": "Deadline if mentioned, otherwise 'Not specified'",
            "priority": "high|medium|low",
            "source_quote": "The exact quote from the transcript where this was mentioned"
        }
    ],
    "decisions": [
        {
            "decision": "Clear statement of what was decided",
            "made_by": "Who made or proposed the decision",
            "source_quote": "The exact quote from the transcript"
        }
    ],
    "total_action_items": 3,
    "total_decisions": 4
}

RULES:
1. Extract EVERY action item — even implicit ones (e.g., "I'll take care of that" = action item).
2. Look for signals like: "Action item:", "will do", "by [date]", "I'll", "let's", "please", "need to", "should", "assigned to".
3. Extract EVERY decision — look for: "Decision:", "We decided", "We will", "The plan is", "Let's go with", "agreed to".
4. For priority: high = has a deadline or is blocking work; medium = important but no urgency; low = nice-to-have.
5. NEVER hallucinate action items or decisions that are not in the transcript.
6. If no owner is identifiable, use "Unassigned".
7. If no deadline is mentioned, use "Not specified".
8. The source_quote must be a real excerpt from the transcript.
9. Return ONLY the JSON object. No markdown, no explanations, no code fences.
"""


class AnnaAgent:
    """Anna: Precision Action Item & Decision Extractor."""

    AGENT_NAME = "Anna"
    AGENT_ROLE = "Precision Task and Decision Extractor"
    AGENT_GOAL = (
        "Extract every action item (with owner, deadline, priority) and every "
        "decision from PII-masked meeting transcripts with zero hallucination."
    )

    def __init__(self, manager: Optional[LyzrManager] = None):
        """
        Initialize Anna.

        Args:
            manager: LyzrManager instance. Creates one if not provided.
        """
        self.manager = manager or LyzrManager()
        self.agent_id = self._ensure_agent()

    def _ensure_agent(self) -> str:
        """Create Anna on Lyzr platform (or return cached ID)."""
        return self.manager.create_agent(
            name=self.AGENT_NAME,
            role=self.AGENT_ROLE,
            goal=self.AGENT_GOAL,
            instructions=ANNA_INSTRUCTIONS,
            description="MeetingMind AI Action Extractor - extracts tasks and decisions",
        )

    def extract(
        self,
        transcript: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Extract action items and decisions from a meeting transcript.

        Args:
            transcript: PII-masked meeting transcript text.
            session_id: Optional session ID for conversation continuity.

        Returns:
            Parsed dict with keys: action_items, decisions,
            total_action_items, total_decisions.
        """
        prompt = (
            f"MEETING TRANSCRIPT:\n{transcript}\n\n"
            "Extract all action items and decisions as a JSON object."
        )

        # Send to Anna via Lyzr
        raw_response = self.manager.chat(
            agent_id=self.agent_id,
            message=prompt,
            session_id=session_id,
        )

        # Parse JSON from response
        return self._parse_response(raw_response)

    def _parse_response(self, raw: str) -> dict:
        """Parse Anna's JSON response, handling potential formatting issues."""
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
                        "action_items": [],
                        "decisions": [],
                        "total_action_items": 0,
                        "total_decisions": 0,
                        "_parse_error": "Failed to parse structured JSON from Anna",
                    }
            else:
                result = {
                    "action_items": [],
                    "decisions": [],
                    "total_action_items": 0,
                    "total_decisions": 0,
                    "_parse_error": "No JSON found in Anna's response",
                }

        # Ensure counts are accurate
        if "action_items" in result:
            result["total_action_items"] = len(result["action_items"])
        if "decisions" in result:
            result["total_decisions"] = len(result["decisions"])

        return result
