"""
MeetingMind AI - Embedding Service Module
==========================================
Generates vector embeddings using Google's Gemini text-embedding-004 model.

This module is used by:
- The Qdrant Memory Store (to embed memories before storage)
- The Search functionality (to embed queries for semantic search)
- The Max agent (to embed action items and decisions for significance scoring)

Output: 768-dimensional float vectors (matching Qdrant collection config)

Usage:
    from utils.embeddings import EmbeddingService

    service = EmbeddingService()
    vector = service.embed("We decided to migrate to AWS")
    vectors = service.embed_batch(["text1", "text2", "text3"])
"""

import os
from typing import Optional

from dotenv import load_dotenv
from google import genai

load_dotenv()


class EmbeddingService:
    """Generates vector embeddings using Google Gemini gemini-embedding-001."""

    DEFAULT_MODEL = "gemini-embedding-001"
    EXPECTED_DIMENSION = 3072

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Embedding Service.

        Args:
            model: Embedding model name. Defaults to "text-embedding-004".
            api_key: Google API key. Falls back to GOOGLE_API_KEY env var.
        """
        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Google API key is required. "
                "Set GOOGLE_API_KEY in your .env file."
            )

        # Initialize the Gemini client
        self.client = genai.Client(api_key=self.api_key)

    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector for a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of 768 floats representing the embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty or whitespace-only text.")

        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
        )

        # The API returns a list of embeddings; we want the first one
        embedding = result.embeddings[0].values

        # Sanity check dimension
        if len(embedding) != self.EXPECTED_DIMENSION:
            raise RuntimeError(
                f"Expected {self.EXPECTED_DIMENSION}-dim embedding, "
                f"got {len(embedding)}-dim. Model may have changed."
            )

        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embedding vectors for multiple texts in a single API call.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each 768 floats).
        """
        if not texts:
            return []

        # Filter out empty strings
        valid_texts = [t for t in texts if t and t.strip()]
        if len(valid_texts) != len(texts):
            print(
                f"[WARN] Skipped {len(texts) - len(valid_texts)} empty texts "
                f"in batch of {len(texts)}"
            )

        if not valid_texts:
            return []

        result = self.client.models.embed_content(
            model=self.model,
            contents=valid_texts,
        )

        embeddings = [e.values for e in result.embeddings]

        # Sanity check dimensions
        for i, emb in enumerate(embeddings):
            if len(emb) != self.EXPECTED_DIMENSION:
                raise RuntimeError(
                    f"Embedding {i}: expected {self.EXPECTED_DIMENSION}-dim, "
                    f"got {len(emb)}-dim."
                )

        return embeddings
