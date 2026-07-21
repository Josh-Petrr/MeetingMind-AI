"""
MeetingMind AI - Boris: Summary Agent
=======================================
Boris is the "Executive Summary Writer" of the Agentic Squad.

Responsibilities:
- Generate a structured executive narrative summary of a meeting transcript
- Highlight key decisions made during the meeting
- Maintain a consistent, professional executive tone
- Use Gemini 1.5 Pro for high-quality synthesis

Input: PII-masked meeting transcript (+ optional historical context from Qdrant)
Output: Structured JSON with summary, decisions, and key topics
"""

import json
from typing import Optional

from agents.lyzr_manager import LyzrManager


# Boris's detailed instructions
BORIS_INSTRUCTIONS = """You are Boris, an expert Executive Summary Writer for MeetingMind AI.

YOUR ROLE:
You receive PII-masked meeting transcripts and produce structured executive summaries.

YOUR OUTPUT FORMAT:
You MUST return ONLY a valid JSON object with NO markdown formatting, NO code blocks, NO extra text.
Return exactly this structure:

{
    "summary": "A concise 3-5 paragraph executive narrative of the meeting. Cover what was discussed, what was decided, and what the next steps are.",
    "decisions": [
        {
            "decision": "Clear statement of the decision made",
            "context": "Brief context on why this decision was made",
            "impact": "Expected impact or consequence of this decision"
        }
    ],
    "key_topics": ["topic1", "topic2", "topic3"],
    "sentiment": "positive|neutral|negative|mixed",
    "meeting_effectiveness": "high|medium|low"
}

RULES:
1. Write the summary in third person, professional executive tone.
2. Every decision explicitly stated in the transcript must appear in the "decisions" array.
3. Look for phrases like "Decision:", "We will", "We decided", "Let's go with", "The plan is" to identify decisions.
4. If historical context from past meetings is provided, reference how current decisions relate to previous ones.
5. Do NOT hallucinate information not present in the transcript.
6. Do NOT include any PII — the transcript is already masked, preserve the masking.
7. Return ONLY the JSON object. No markdown, no explanations, no code fences.
"""


class BorisAgent:
    """Boris: Executive Summary Writer."""

    AGENT_NAME = "Boris"
    AGENT_ROLE = "Executive Summary Writer"
    AGENT_GOAL = (
        "Generate structured executive summaries with decisions, key topics, "
        "and sentiment analysis from PII-masked meeting transcripts."
    )

    def __init__(self, manager: Optional[LyzrManager] = None):
        """
        Initialize Boris.

        Args:
            manager: LyzrManager instance. Creates one if not provided.
        """
        self.manager = manager or LyzrManager()
        self.agent_id = self._ensure_agent()

    def _ensure_agent(self) -> str:
        """Create Boris on Lyzr platform (or return cached ID)."""
        return self.manager.create_agent(
            name=self.AGENT_NAME,
            role=self.AGENT_ROLE,
            goal=self.AGENT_GOAL,
            instructions=BORIS_INSTRUCTIONS,
            description="MeetingMind AI Summary Agent - generates executive summaries",
        )

    def summarize(
        self,
        transcript: str,
        historical_context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Generate an executive summary of a meeting transcript.

        Args:
            transcript: PII-masked meeting transcript text.
            historical_context: Optional relevant context from past meetings
                                (retrieved from Qdrant by Max).
            session_id: Optional session ID for conversation continuity.

        Returns:
            Parsed dict with keys: summary, decisions, key_topics, sentiment,
            meeting_effectiveness.
        """
        # Build the prompt
        prompt_parts = []

        if historical_context:
            prompt_parts.append(
                f"HISTORICAL CONTEXT FROM PAST MEETINGS:\n{historical_context}\n\n"
                "Use this context to enrich your summary and note any continuity "
                "with previous decisions.\n\n---\n\n"
            )

        prompt_parts.append(
            f"MEETING TRANSCRIPT:\n{transcript}\n\n"
            "Generate the executive summary as a JSON object."
        )

        prompt = "".join(prompt_parts)

        # Send to Boris via Lyzr
        raw_response = self.manager.chat(
            agent_id=self.agent_id,
            message=prompt,
            session_id=session_id,
        )

        # Parse JSON from response
        return self._parse_response(raw_response)

    def _parse_response(self, raw: str) -> dict:
        """Parse Boris's JSON response, handling potential formatting issues."""
        # Strip markdown code fences if present
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
            # If JSON parsing fails, try to extract JSON from the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    result = json.loads(text[start:end])
                except json.JSONDecodeError:
                    result = {
                        "summary": text,
                        "decisions": [],
                        "key_topics": [],
                        "sentiment": "unknown",
                        "meeting_effectiveness": "unknown",
                        "_parse_error": "Failed to parse structured JSON from Boris",
                    }
            else:
                result = {
                    "summary": text,
                    "decisions": [],
                    "key_topics": [],
                    "sentiment": "unknown",
                    "meeting_effectiveness": "unknown",
                    "_parse_error": "No JSON found in Boris's response",
                }

        return result
