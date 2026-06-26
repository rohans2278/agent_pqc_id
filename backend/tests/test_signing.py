"""signing.authorize: the three outcomes plus a missing-identity guard."""

from types import SimpleNamespace

import pytest
from sqlalchemy import select

import keystore
import signing
from models import REJECTED_REVOKED, REJECTED_SIGNATURE, REVOKED, AuditLog

ARGS = {"sql": "select 1"}


def _ctx(agent_id) -> SimpleNamespace:
    """Minimal stand-in for a FastMCP Context carrying the X-Agent-Id header."""
    request = SimpleNamespace(headers={"x-agent-id": str(agent_id)})
    return SimpleNamespace(request_context=SimpleNamespace(request=request))


def _last_outcome(db, agent_id):
    return db.scalar(select(AuditLog).where(AuditLog.agent_id == agent_id)).outcome


def test_authorize_allows_a_healthy_agent(db):
    agent = keystore.create_keypair_for_agent(db, "sign-ok")
    result = signing.authorize(db, _ctx(agent.id), "run_sql", ARGS)
    assert result.id == agent.id
    # Success writes no audit row here — the tool records EXECUTED.
    assert db.scalar(select(AuditLog).where(AuditLog.agent_id == agent.id)) is None


def test_authorize_rejects_revoked_before_crypto(db):
    agent = keystore.create_keypair_for_agent(db, "sign-revoked")
    agent.status = REVOKED
    db.commit()

    with pytest.raises(signing.ToolRejected):
        signing.authorize(db, _ctx(agent.id), "run_sql", ARGS)
    assert _last_outcome(db, agent.id) == REJECTED_REVOKED


def test_authorize_rejects_tampered_agent(db):
    agent = keystore.create_keypair_for_agent(db, "sign-tampered")
    keystore.tamper_agent(db, agent.id)

    with pytest.raises(signing.ToolRejected):
        signing.authorize(db, _ctx(agent.id), "run_sql", ARGS)
    assert _last_outcome(db, agent.id) == REJECTED_SIGNATURE


def test_authorize_rejects_missing_header(db):
    request = SimpleNamespace(headers={})
    ctx = SimpleNamespace(request_context=SimpleNamespace(request=request))
    with pytest.raises(signing.ToolRejected):
        signing.authorize(db, ctx, "run_sql", ARGS)
