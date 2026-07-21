"""
MeetingMind AI - Lyzr Agent Manager
=====================================
Central manager for creating and interacting with Lyzr agents.

This module handles the Lyzr SDK lifecycle:
- Initializing the LyzrAgentAPI client
- Creating agents (Boris, Anna, Max) on the Lyzr platform
- Sending messages to agents and receiving responses
- Caching agent IDs so we don't recreate them on every run

Usage:
    from agents.lyzr_manager import LyzrManager

    manager = LyzrManager()
    agent_id = manager.create_agent(name="Boris", ...)
    response = manager.chat(agent_id, message="Summarize this transcript...")
"""

import os
import json
from typing import Optional

from dotenv import load_dotenv
from lyzr_python_sdk import LyzrAgentAPI

load_dotenv()

# Path to cache agent IDs between runs
AGENT_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".agent_cache.json"
)


class LyzrManager:
    """Manages the lifecycle of Lyzr agents."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Lyzr Manager.

        Args:
            api_key: Lyzr API key. Falls back to LYZR_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("LYZR_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Lyzr API key is required. "
                "Set LYZR_API_KEY in your .env file."
            )

        self.client = LyzrAgentAPI(api_key=self.api_key)
        self._agent_cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cached agent IDs from disk."""
        if os.path.exists(AGENT_CACHE_FILE):
            try:
                with open(AGENT_CACHE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self):
        """Save agent IDs to disk."""
        with open(AGENT_CACHE_FILE, "w") as f:
            json.dump(self._agent_cache, f, indent=2)

    def create_agent(
        self,
        name: str,
        role: str,
        goal: str,
        instructions: str,
        description: str = "",
        model: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        force_recreate: bool = False,
    ) -> str:
        """
        Create a Lyzr agent. Returns cached agent_id if already created.

        Args:
            name: Agent name (e.g., "Boris").
            role: Agent role description.
            goal: What the agent is trying to achieve.
            instructions: Detailed behavioral instructions.
            description: Short description of the agent.
            model: LLM model to use. Defaults to gemini-2.5-flash.
            temperature: LLM temperature. Defaults to 0.3 for precision.
            force_recreate: If True, creates a new agent even if cached.

        Returns:
            The agent_id string.
        """
        cache_key = f"agent_{name.lower().replace(' ', '_')}"

        # Return cached agent if available
        if not force_recreate and cache_key in self._agent_cache:
            agent_id = self._agent_cache[cache_key]
            print(f"[INFO] Using cached agent '{name}' (ID: {agent_id[:8]}...)")
            return agent_id

        # Create new agent
        agent_config = {
            "name": name,
            "description": description or f"MeetingMind AI - {name}",
            "agent_role": role,
            "agent_goal": goal,
            "agent_instructions": instructions,
            "template_type": "single_task",
            "model": model,
            "temperature": temperature,
            "provider_id": "google",
            "top_p": 1.0,
        }

        result = self.client.agents.create_agent(agent_config=agent_config)

        # Extract agent_id from response
        agent_id = result.get("agent_id") or result.get("id")
        if not agent_id:
            raise RuntimeError(f"Failed to create agent '{name}'. Response: {result}")

        # Cache it
        self._agent_cache[cache_key] = agent_id
        self._save_cache()

        print(f"[INFO] Created agent '{name}' (ID: {agent_id[:8]}...)")
        return agent_id

    def chat(
        self,
        agent_id: str,
        message: str,
        user_id: str = "meetingmind_system",
        session_id: Optional[str] = None,
    ) -> str:
        """
        Send a message to a Lyzr agent and get a response.

        Args:
            agent_id: The agent's ID.
            message: The message/prompt to send.
            user_id: User identifier. Defaults to "meetingmind_system".
            session_id: Optional session ID for conversation continuity.

        Returns:
            The agent's text response.
        """
        import uuid
        
        payload = {
            "user_id": user_id,
            "agent_id": agent_id,
            "message": message,
            "session_id": session_id or str(uuid.uuid4()),
        }

        response = self.client.inference.chat(payload)

        # Extract text from response
        if isinstance(response, dict):
            return response.get("response", response.get("message", str(response)))
        return str(response)

    def list_agents(self) -> list:
        """List all agents on the Lyzr platform."""
        return self.client.agents.get_agents()

    def clear_cache(self):
        """Clear the local agent cache (forces recreation on next run)."""
        self._agent_cache = {}
        if os.path.exists(AGENT_CACHE_FILE):
            os.remove(AGENT_CACHE_FILE)
        print("[INFO] Agent cache cleared")
