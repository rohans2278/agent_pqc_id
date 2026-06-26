"""FastAPI surface: agent CRUD + tamper/revoke. Creating an agent hits KMS."""

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    # `with` triggers the lifespan, which runs init_db().
    with TestClient(app) as c:
        yield c


def test_agent_lifecycle(client):
    created = client.post("/agents", json={"name": "api-agent"})
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "active"
    assert body["public_key"]  # base64 of the ML-DSA-65 public key
    agent_id = body["id"]

    # Names are unique.
    assert client.post("/agents", json={"name": "api-agent"}).status_code == 409

    # List + fetch.
    assert any(a["id"] == agent_id for a in client.get("/agents").json())
    assert client.get(f"/agents/{agent_id}").status_code == 200

    # Delete, then it's gone.
    assert client.delete(f"/agents/{agent_id}").status_code == 204
    assert client.get(f"/agents/{agent_id}").status_code == 404


def test_tamper_preserves_identity_and_status(client):
    body = client.post("/agents", json={"name": "api-tamper"}).json()
    tampered = client.post(f"/agents/{body['id']}/tamper").json()
    # Tamper swaps the secret key only — public key and status are unchanged.
    assert tampered["public_key"] == body["public_key"]
    assert tampered["status"] == "active"


def test_revoke_sets_status(client):
    body = client.post("/agents", json={"name": "api-revoke"}).json()
    revoked = client.post(f"/agents/{body['id']}/revoke").json()
    assert revoked["status"] == "revoked"


def test_tamper_unknown_agent_404(client):
    assert client.post("/agents/00000000-0000-0000-0000-000000000000/tamper").status_code == 404
