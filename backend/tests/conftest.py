"""Shared fixtures. The suite runs against the real stack (liboqs, KMS, Postgres,
and — for the e2e test — Gemini), so run it inside the container with a populated
.env. See backend/CLAUDE.md.
"""

import pytest
from sqlalchemy import delete

from bootstrap import init_db
from db import SessionLocal
from models import Agent, AuditLog


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    """Create the tables and seed the demo schema once for the whole run."""
    init_db()


@pytest.fixture
def db():
    """A privileged session for tests that touch agents/audit directly."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _clean_agents():
    """Wipe agents + audit between tests so each starts from a clean slate.
    The demo schema is left intact."""
    yield
    with SessionLocal() as session:
        session.execute(delete(AuditLog))
        session.execute(delete(Agent))
        session.commit()
