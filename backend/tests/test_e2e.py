"""End-to-end: a real Gemini agent answers over the demo data, and a tampered
agent is blocked at the tool layer. Needs the MCP server running and a Gemini
key — run via `docker compose` with both services up.
"""

import socket
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from api import app
from config import settings

CUSTOMER_QUESTION = "How many customers are in the database?"


def _mcp_reachable() -> bool:
    url = urlparse(settings.mcp_server_url)
    try:
        with socket.create_connection((url.hostname, url.port or 80), timeout=3):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _mcp_reachable(), reason="MCP server not reachable on MCP_SERVER_URL"
)


def test_agent_answers_then_is_blocked_after_tamper():
    with TestClient(app) as client:
        agent_id = client.post("/agents", json={"name": "e2e"}).json()["id"]

        # Healthy agent answers from the seeded data (5 customers).
        first = client.post(f"/agents/{agent_id}/chat", json={"message": CUSTOMER_QUESTION})
        assert first.status_code == 200
        assert "5" in first.json()["answer"]
        audits = client.get(f"/audit?agent_id={agent_id}").json()
        assert any(a["outcome"] == "executed" for a in audits)

        # Compromise it: its signed tool calls must now fail verification.
        client.post(f"/agents/{agent_id}/tamper")
        client.post(f"/agents/{agent_id}/chat", json={"message": CUSTOMER_QUESTION})
        audits = client.get(f"/audit?agent_id={agent_id}").json()
        assert any(a["outcome"] == "rejected_signature" for a in audits)
