"""ORM models for agent identity and the audit log.

The seeded demo dataset (the tables agents actually query) lives in seed/*.sql
and is intentionally NOT modelled here — the backend never reads it through the
ORM, only agents do, via signed read-only MCP tool calls.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base

# Agent status
ACTIVE = "active"
REVOKED = "revoked"

# Audit outcomes
EXECUTED = "executed"
REJECTED_SIGNATURE = "rejected_signature"
REJECTED_REVOKED = "rejected_revoked"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    # The agent's registered cryptographic identity: the ML-DSA-65 public key.
    public_key: Mapped[bytes] = mapped_column(LargeBinary)

    # Secret key, sealed with KMS envelope encryption. We store only ciphertext:
    #  - encrypted_secret_key: the SK encrypted locally with AES-256-GCM
    #    (the GCM tag is appended to the ciphertext by `cryptography`'s AESGCM)
    #  - encrypted_data_key: the AES data key, encrypted by KMS (its CiphertextBlob)
    #  - nonce: the 12-byte AES-GCM nonce
    # The plaintext SK and data key never touch this table.
    encrypted_secret_key: Mapped[bytes] = mapped_column(LargeBinary)
    encrypted_data_key: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)

    status: Mapped[str] = mapped_column(String, default=ACTIVE, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Plain indexed column, not a hard FK — audit rows must survive agent deletion.
    agent_id: Mapped[uuid.UUID] = mapped_column(index=True)

    tool: Mapped[str] = mapped_column(String)
    outcome: Mapped[str] = mapped_column(String, index=True)

    # Short human-readable note: the SQL run, or why a call was rejected.
    detail: Mapped[str | None] = mapped_column(String, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
