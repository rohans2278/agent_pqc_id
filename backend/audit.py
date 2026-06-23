"""The audit log: exactly one row per tool call, recording its outcome."""

import uuid

from models import AuditLog
from sqlalchemy.orm import Session


def write_audit_entry(
    db: Session,
    agent_id: uuid.UUID,
    tool: str,
    outcome: str,
    detail: str | None = None,
) -> None:
    """Record one tool call. `outcome` is one of the constants in models:
    EXECUTED | REJECTED_SIGNATURE | REJECTED_REVOKED."""
    db.add(AuditLog(agent_id=agent_id, tool=tool, outcome=outcome, detail=detail))
    db.commit()
