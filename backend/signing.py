"""The trust boundary: every MCP tool call is authorized here before it runs.

Order, per the security invariants:
  1. Identify the calling agent (from the X-Agent-Id request header — the LLM
     never supplies its own identity).
  2. Revocation is checked first, before any crypto/KMS work.
  3. Briefly unseal the agent's secret key, sign a canonical payload, and verify
     that signature against the agent's *registered* public key. The signing key
     is zeroed immediately after. A tampered agent fails here.
A rejection writes its audit row and raises ToolRejected; the success path
returns the Agent and the tool is responsible for the single EXECUTED row.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import crypto
import keystore
from audit import write_audit_entry
from models import REJECTED_REVOKED, REJECTED_SIGNATURE, REVOKED, Agent
from sqlalchemy.orm import Session


class ToolRejected(Exception):
    """Raised when a tool call is not authorized. The reason is user-safe."""


def _agent_id_from_context(ctx: Any) -> uuid.UUID:
    """Pull the caller's agent id from the X-Agent-Id header. Identity travels
    on the transport, not in tool arguments, so the model can't spoof it."""
    request = getattr(ctx.request_context, "request", None)
    headers = getattr(request, "headers", None)
    raw = headers.get("x-agent-id") if headers else None
    if not raw:
        raise ToolRejected("missing X-Agent-Id header")
    try:
        return uuid.UUID(raw)
    except ValueError:
        raise ToolRejected("invalid X-Agent-Id header")


def _canonical_payload(agent_id: uuid.UUID, tool: str, args: dict[str, Any]) -> bytes:
    """Deterministic JSON of the call, hashed with SHA-256. timestamp + nonce
    make each signed payload unique; sign and verify use these same bytes."""
    doc = {
        "agent_id": str(agent_id),
        "tool": tool,
        "args": args,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": os.urandom(16).hex(),
    }
    encoded = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).digest()


def authorize(db: Session, ctx: Any, tool: str, args: dict[str, Any]) -> Agent:
    """Authorize a tool call. Returns the Agent on success; on failure writes the
    audit row and raises ToolRejected."""
    agent_id = _agent_id_from_context(ctx)
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise ToolRejected("unknown agent")

    # 1. Revocation first — no crypto/KMS work for a revoked agent.
    if agent.status == REVOKED:
        write_audit_entry(db, agent.id, tool, REJECTED_REVOKED, "agent revoked")
        raise ToolRejected("agent is revoked")

    # 2. Sign, then verify against the REGISTERED public key.
    payload = _canonical_payload(agent.id, tool, args)
    sk = keystore.load_secret_key(agent)
    try:
        signature = crypto.sign(sk, payload)
    finally:
        keystore.wipe(sk)

    if not crypto.verify(agent.public_key, payload, signature):
        write_audit_entry(db, agent.id, tool, REJECTED_SIGNATURE, "signature mismatch")
        raise ToolRejected("signature verification failed")

    return agent
