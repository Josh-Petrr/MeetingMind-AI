"""
Test script for the Qdrant Memory Store module.
Requires QDRANT_URL and QDRANT_API_KEY in .env file.

Usage:
    python tests/test_qdrant_store.py
"""

import sys
import os
import random

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from config import settings
import random

def make_fake_embedding(dim=3072):
    """Generate a random embedding vector for testing (not real embeddings)."""
    return [random.uniform(-1, 1) for _ in range(dim)]


@pytest.fixture(scope="module")
def store():
    """Pytest fixture to provide and clean up Qdrant store."""
    from memory.qdrant_store import QdrantMemoryStore
    from qdrant_client import QdrantClient

    url = settings.QDRANT_URL
    key = settings.QDRANT_API_KEY
    if not url or not key or key.startswith("mock_"):
        pytest.skip("Valid QDRANT_URL and QDRANT_API_KEY not found (mock key detected)")
        
    client = QdrantClient(url=url, api_key=key)
    try:
        client.delete_collection("meetingmind_test")
    except Exception:
        pass

    store = QdrantMemoryStore(collection_name="meetingmind_test")
    yield store
    
    try:
        store.client.delete_collection("meetingmind_test")
    except Exception:
        pass

def test_connection(store):
    """Test that we can connect to Qdrant Cloud."""
    info = store.get_collection_info()
    assert info['name'] == "meetingmind_test"


def test_store_memory(store):
    """Test storing a memory point."""
    point_id = store.store_memory(
        text="Decision: We will migrate to AWS by Q3 2026.",
        embedding=make_fake_embedding(),
        memory_type="decision",
        org_id="org_test_001",
        meeting_id="meeting_001",
        significance_score=8.5,
        is_starred=True,
        extra_metadata={"owner": "Mike Chen"},
    )
    assert point_id is not None, "FAIL: store_memory returned None"
    assert len(point_id) > 0, "FAIL: store_memory returned empty ID"
    print(f"[PASS] Stored memory with ID: {point_id[:8]}...")
    return point_id


def test_store_multiple_memories(store):
    """Store several memories to test search quality."""
    memories = [
        {
            "text": "Action item: Emily will update the privacy policy by July 22nd.",
            "memory_type": "action_item",
            "significance_score": 7.0,
            "meeting_id": "meeting_001",
        },
        {
            "text": "The recommendation engine v2 shows 23% improvement in click-through rate.",
            "memory_type": "summary",
            "significance_score": 6.0,
            "meeting_id": "meeting_001",
        },
        {
            "text": "Decision: Implement Redis caching to reduce model inference latency below 200ms.",
            "memory_type": "decision",
            "significance_score": 9.0,
            "meeting_id": "meeting_002",
        },
        {
            "text": "Action item: Raj will complete AWS cost optimization audit by July 30th.",
            "memory_type": "action_item",
            "significance_score": 7.5,
            "meeting_id": "meeting_002",
        },
    ]

    ids = []
    for mem in memories:
        pid = store.store_memory(
            text=mem["text"],
            embedding=make_fake_embedding(),
            memory_type=mem["memory_type"],
            org_id="org_test_001",
            meeting_id=mem["meeting_id"],
            significance_score=mem["significance_score"],
        )
        ids.append(pid)

    print(f"[PASS] Stored {len(ids)} additional memories")
    return ids


def test_search(store):
    """Test semantic search (note: using random embeddings so results are random)."""
    results = store.search(
        query_embedding=make_fake_embedding(),
        org_id="org_test_001",
        top_k=3,
    )
    assert isinstance(results, list), f"FAIL: search returned {type(results)}, expected list"
    print(f"[PASS] Search returned {len(results)} results")
    for r in results:
        print(f"       > [{r['memory_type']}] {r['text'][:60]}... (score: {r['score']})")


def test_search_with_filter(store):
    """Test search with memory_type filter."""
    results = store.search(
        query_embedding=make_fake_embedding(),
        org_id="org_test_001",
        top_k=10,
        memory_type="decision",
    )
    for r in results:
        assert r["memory_type"] == "decision", f"FAIL: Got memory_type '{r['memory_type']}', expected 'decision'"
    print(f"[PASS] Filtered search returned {len(results)} decisions only")


def test_get_meeting_memories(store):
    """Test retrieving all memories for a specific meeting."""
    memories = store.get_meeting_memories(meeting_id="meeting_001", org_id="org_test_001")
    assert isinstance(memories, list), f"FAIL: get_meeting_memories returned {type(memories)}"
    assert len(memories) > 0, "FAIL: No memories found for meeting_001"
    print(f"[PASS] Retrieved {len(memories)} memories for meeting_001")


def test_org_isolation(store):
    """Test that search respects org_id isolation."""
    # Store a memory under a different org
    store.store_memory(
        text="Secret decision from another org.",
        embedding=make_fake_embedding(),
        memory_type="decision",
        org_id="org_other_999",
        meeting_id="meeting_secret",
        significance_score=10.0,
    )

    # Search as org_test_001 — should NOT see the other org's data
    results = store.search(
        query_embedding=make_fake_embedding(),
        org_id="org_test_001",
        top_k=100,
    )
    for r in results:
        assert r.get("meeting_id") != "meeting_secret", (
            f"FAIL: Data leak! Found meeting_secret in org_test_001 search results"
        )
    print("[PASS] Org isolation verified -- org_test_001 cannot see org_other_999 data")


def test_delete_meeting_memories(store):
    """Test GDPR-compliant deletion of meeting memories."""
    deleted = store.delete_meeting_memories(meeting_id="meeting_001", org_id="org_test_001")
    print(f"[PASS] Deleted {deleted} memories for meeting_001")

    # Verify they're gone
    remaining = store.get_meeting_memories(meeting_id="meeting_001", org_id="org_test_001")
    assert len(remaining) == 0, f"FAIL: {len(remaining)} memories still exist after deletion"
    print("[PASS] Verified meeting_001 memories are fully deleted")



