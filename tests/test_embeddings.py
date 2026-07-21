"""
Test script for the Embedding Service module.
Requires GOOGLE_API_KEY in .env file.

Usage:
    python tests/test_embeddings.py
"""

import sys
import os

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from config import settings


def test_embedding_generation():
    """Test that we can generate embeddings from the API."""
    # Ensure API key is present
    key = settings.GOOGLE_API_KEY
    if not key or key.startswith("mock_"):
        pytest.skip("Valid GOOGLE_API_KEY not found (mock key detected)")
    print(f"[OK] Google API key found (starts with: {key[:8]}...)")
    assert key is not None


def test_single_embedding():
    """Test generating a single embedding."""
    from utils.embeddings import EmbeddingService

    service = EmbeddingService()
    vector = service.embed("We decided to migrate our infrastructure to AWS by Q3.")

    assert isinstance(vector, list), f"FAIL: Expected list, got {type(vector)}"
    assert len(vector) == 3072, f"FAIL: Expected 3072 dimensions, got {len(vector)}"
    assert all(isinstance(v, float) for v in vector), "FAIL: Not all values are floats"
    print(f"[PASS] Single embedding generated -- {len(vector)} dimensions")
    print(f"       First 5 values: {[round(v, 4) for v in vector[:5]]}")


def test_batch_embedding():
    """Test generating embeddings for multiple texts."""
    from utils.embeddings import EmbeddingService

    service = EmbeddingService()
    texts = [
        "Action item: Emily will update the privacy policy.",
        "Decision: We will implement Redis caching for latency.",
        "Summary: The Q3 roadmap review covered migration progress.",
    ]
    vectors = service.embed_batch(texts)

    assert len(vectors) == 3, f"FAIL: Expected 3 embeddings, got {len(vectors)}"
    for i, vec in enumerate(vectors):
        assert len(vec) == 3072, f"FAIL: Embedding {i} has {len(vec)} dims, expected 3072"
    print(f"[PASS] Batch embedding generated -- {len(vectors)} vectors, each {len(vectors[0])} dims")


def test_semantic_similarity():
    """Test that semantically similar texts produce similar embeddings."""
    from utils.embeddings import EmbeddingService

    service = EmbeddingService()

    # These two should be semantically similar
    text_a = "We need to reduce our cloud infrastructure costs."
    text_b = "The team should optimize AWS spending to cut expenses."

    # This one should be semantically different
    text_c = "The new logo design uses a blue gradient with rounded corners."

    vec_a = service.embed(text_a)
    vec_b = service.embed(text_b)
    vec_c = service.embed(text_c)

    # Compute cosine similarity
    def cosine_similarity(v1, v2):
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot / (norm1 * norm2) if norm1 * norm2 > 0 else 0

    sim_ab = cosine_similarity(vec_a, vec_b)
    sim_ac = cosine_similarity(vec_a, vec_c)

    print(f"[INFO] Similarity (costs vs spending): {sim_ab:.4f}")
    print(f"[INFO] Similarity (costs vs logo):     {sim_ac:.4f}")

    assert sim_ab > sim_ac, (
        f"FAIL: Similar texts ({sim_ab:.4f}) should score higher than "
        f"different texts ({sim_ac:.4f})"
    )
    print(f"[PASS] Semantic similarity check passed -- similar texts score higher")


def test_empty_text_handling():
    """Test that empty text raises an error."""
    from utils.embeddings import EmbeddingService

    service = EmbeddingService()
    try:
        service.embed("")
        print("[FAIL] Should have raised ValueError for empty text")
    except ValueError:
        print("[PASS] Empty text correctly raises ValueError")

    try:
        service.embed("   ")
        print("[FAIL] Should have raised ValueError for whitespace-only text")
    except ValueError:
        print("[PASS] Whitespace-only text correctly raises ValueError")


def test_batch_with_empty():
    """Test batch embedding gracefully handles empty strings."""
    from utils.embeddings import EmbeddingService

    service = EmbeddingService()
    result = service.embed_batch([])
    assert result == [], f"FAIL: Expected empty list, got {result}"
    print("[PASS] Empty batch returns empty list")


if __name__ == "__main__":
    print("=" * 60)
    print("  MeetingMind AI -- Embedding Service Tests")
    print("=" * 60)
    print()

    test_embedding_generation()
    test_single_embedding()
    test_batch_embedding()
    test_semantic_similarity()
    test_empty_text_handling()
    test_batch_with_empty()

    print()
    print("=" * 60)
    print("  All Embedding Service tests completed!")
    print("=" * 60)
