"""
MeetingMind AI - Qdrant Memory Store Module
=============================================
Manages long-term semantic memory using Qdrant vector database.

This module handles:
- Connecting to Qdrant Cloud (or local instance)
- Creating and managing the meetings memory collection
- Storing meeting artifacts (summaries, action items, decisions) as vectors
- Retrieving relevant past context via semantic search
- Metadata filtering by org_id, meeting_id, significance_score, is_starred

Usage:
    from memory.qdrant_store import QdrantMemoryStore

    store = QdrantMemoryStore()
    store.store_memory(text="We decided to migrate to AWS", metadata={...})
    results = store.search("cloud migration decision", top_k=5)
"""

import os
import uuid
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)
from config import settings


class QdrantMemoryStore:
    """Manages long-term semantic memory in Qdrant vector database."""

    # Default collection name for meeting memories
    DEFAULT_COLLECTION = "meetingmind_memories"

    # Dimension of Gemini text-embedding vectors
    EMBEDDING_DIMENSION = 3072

    def __init__(
        self,
        collection_name: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Qdrant Memory Store.

        Args:
            collection_name: Name of the Qdrant collection. Defaults to "meetingmind_memories".
            url: Qdrant Cloud URL. Falls back to QDRANT_URL env var.
            api_key: Qdrant API key. Falls back to QDRANT_API_KEY env var.
        """
        self.collection_name = collection_name or self.DEFAULT_COLLECTION
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY

        if not self.url or not self.api_key:
            raise ValueError(
                "Qdrant URL and API key are required. "
                "Set QDRANT_URL and QDRANT_API_KEY in your .env file."
            )

        # Connect to Qdrant Cloud
        self.client = QdrantClient(url=self.url, api_key=self.api_key)

        # Ensure the collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create the collection and payload indexes if they don't already exist."""
        collections = self.client.get_collections().collections
        existing_names = [c.name for c in collections]

        if self.collection_name not in existing_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            print(f"[INFO] Created Qdrant collection: '{self.collection_name}'")

        # Create payload indexes for fields used in filters
        for field_name in ["org_id", "meeting_id", "memory_type"]:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass  # Index may already exist

    def store_memory(
        self,
        text: str,
        embedding: list[float],
        memory_type: str,
        org_id: str,
        meeting_id: str,
        significance_score: float = 5.0,
        is_starred: bool = False,
        extra_metadata: Optional[dict] = None,
    ) -> str:
        """
        Store a memory (summary, action item, or decision) as a vector in Qdrant.

        Args:
            text: The text content of the memory.
            embedding: The vector embedding of the text (768-dim for Gemini).
            memory_type: Type of memory: "summary", "action_item", or "decision".
            org_id: Organization ID for data isolation.
            meeting_id: Meeting ID this memory belongs to.
            significance_score: Score from 0-10 assigned by Max agent. Defaults to 5.0.
            is_starred: Whether the user manually starred this item. Defaults to False.
            extra_metadata: Any additional metadata to store.

        Returns:
            The unique ID of the stored memory point.
        """
        point_id = str(uuid.uuid4())

        payload = {
            "text": text,
            "memory_type": memory_type,
            "org_id": org_id,
            "meeting_id": meeting_id,
            "significance_score": significance_score,
            "is_starred": is_starred,
        }

        if extra_metadata:
            payload.update(extra_metadata)

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        return point_id

    def search(
        self,
        query_embedding: list[float],
        org_id: str,
        top_k: int = 5,
        memory_type: Optional[str] = None,
        min_significance: Optional[float] = None,
    ) -> list[dict]:
        """
        Search for relevant past memories using semantic similarity.

        Args:
            query_embedding: The vector embedding of the search query.
            org_id: Organization ID to scope the search (data isolation).
            top_k: Number of results to return. Defaults to 5.
            memory_type: Optional filter by memory type ("summary", "action_item", "decision").
            min_significance: Optional minimum significance score filter.

        Returns:
            List of dicts with keys: id, text, memory_type, meeting_id,
            significance_score, is_starred, score (similarity).
        """
        # Build filter conditions — always filter by org_id for data isolation
        must_conditions = [
            FieldCondition(key="org_id", match=MatchValue(value=org_id))
        ]

        if memory_type:
            must_conditions.append(
                FieldCondition(key="memory_type", match=MatchValue(value=memory_type))
            )

        search_filter = Filter(must=must_conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k,
        )

        # Format results
        memories = []
        for result in results:
            payload = result.payload

            # Apply significance filter in post-processing
            if min_significance and payload.get("significance_score", 0) < min_significance:
                continue

            memories.append(
                {
                    "id": result.id,
                    "text": payload.get("text", ""),
                    "memory_type": payload.get("memory_type", ""),
                    "meeting_id": payload.get("meeting_id", ""),
                    "significance_score": payload.get("significance_score", 0),
                    "is_starred": payload.get("is_starred", False),
                    "score": round(result.score, 4),
                }
            )

        return memories

    def get_meeting_memories(self, meeting_id: str, org_id: str) -> list[dict]:
        """
        Retrieve all stored memories for a specific meeting.

        Args:
            meeting_id: The meeting ID to look up.
            org_id: Organization ID for data isolation.

        Returns:
            List of memory dicts for the specified meeting.
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="org_id", match=MatchValue(value=org_id)),
                    FieldCondition(key="meeting_id", match=MatchValue(value=meeting_id)),
                ]
            ),
            limit=100,
        )

        memories = []
        for point in results[0]:  # scroll returns (points, next_page_offset)
            payload = point.payload
            memories.append(
                {
                    "id": point.id,
                    "text": payload.get("text", ""),
                    "memory_type": payload.get("memory_type", ""),
                    "meeting_id": payload.get("meeting_id", ""),
                    "significance_score": payload.get("significance_score", 0),
                    "is_starred": payload.get("is_starred", False),
                }
            )

        return memories

    def delete_meeting_memories(self, meeting_id: str, org_id: str) -> int:
        """
        Delete all memories for a specific meeting (for GDPR compliance).

        Args:
            meeting_id: The meeting ID to delete.
            org_id: Organization ID for data isolation.

        Returns:
            Number of points deleted.
        """
        # Get count before deletion
        before = self.get_meeting_memories(meeting_id, org_id)

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(key="org_id", match=MatchValue(value=org_id)),
                    FieldCondition(key="meeting_id", match=MatchValue(value=meeting_id)),
                ]
            ),
        )

        return len(before)

    def get_collection_info(self) -> dict:
        """Get info about the current Qdrant collection (for health checks)."""
        info = self.client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status.value,
        }
