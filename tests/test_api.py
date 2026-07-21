import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.server import app

client = TestClient(app)

def test_read_root():
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "MeetingMind AI API"}

def test_process_meeting_empty_transcript():
    """Test validation on empty transcript upload."""
    payload = {
        "transcript": "   ",
        "org_id": "test_org",
        "skip_memory_retrieval": True
    }
    response = client.post("/process-meeting", json=payload)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_process_meeting_success():
    """Test a valid meeting submission returns 200 and a meeting_id."""
    payload = {
        "transcript": "Hello, we decided to migrate to AWS.",
        "org_id": "test_org",
        "skip_memory_retrieval": True
    }
    response = client.post("/process-meeting", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "meeting_id" in data
    assert data["status"] == "processing"

def test_search_empty_query():
    """Test search with empty query fails validation."""
    payload = {
        "query": "",
        "org_id": "test_org"
    }
    response = client.post("/memory/search", json=payload)
    assert response.status_code == 400
