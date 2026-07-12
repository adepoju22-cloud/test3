"""
Integration tests for the FastAPI REST API.

These use FastAPI's TestClient (built on httpx) against an isolated
in-memory SQLite database so they never touch the real compliance.db.

Run with:  pytest tests/ -v
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force an isolated in-memory database before importing the app.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_health_check():
    """GET / should report the service as running."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"


def test_get_resources():
    """GET /resources should return the bundled inventory."""
    response = client.get("/resources")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 30


def test_get_rules():
    """GET /rules should return the bundled rule set."""
    response = client.get("/rules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 40


def test_post_scan_then_get_results():
    """POST /scan should populate results retrievable via GET /results."""
    scan_response = client.post("/scan")
    assert scan_response.status_code == 200
    scan_body = scan_response.json()
    assert scan_body["findings_generated"] > 0

    results_response = client.get("/results")
    assert results_response.status_code == 200
    assert len(results_response.json()) == scan_body["findings_generated"]


def test_get_summary_after_scan():
    """GET /summary should reflect the most recent scan's statistics."""
    client.post("/scan")
    response = client.get("/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_findings"] > 0
    assert 0 <= body["compliance_percentage"] <= 100


def test_get_critical_and_failed():
    """GET /critical and GET /failed should only return FAIL status rows."""
    client.post("/scan")
    critical = client.get("/critical").json()
    failed = client.get("/failed").json()
    assert all(item["status"] == "FAIL" for item in critical)
    assert all(item["status"] == "FAIL" for item in failed)
    assert all(item["severity"] == "Critical" for item in critical)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
