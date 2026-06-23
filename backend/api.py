"""FastAPI app: agent CRUD, chat, tamper, revoke, and audit queries.

The data the agents query is never exposed here — that only happens through the
signed MCP tools. This API manages agent identities and surfaces the audit log.
"""

import base64
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import agent as agent_runtime
from bootstrap import init_db
from db import get_db
from keystore import create_keypair_for_agent, tamper_agent
from models import REVOKED, Agent, AuditLog

MAX_AGENTS = 10


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="PQC Agent ID", lifespan=lifespan)


# --- schemas ---------------------------------------------------------------

class AgentCreate(BaseModel):
    name: str


class AgentOut(BaseModel):
    id: uuid.UUID
    name: str
    public_key: str  # base64-encoded ML-DSA-65 public key
    status: str
    created_at: datetime

    @classmethod
    def of(cls, a: Agent) -> "AgentOut":
        return cls(
            id=a.id,
            name=a.name,
            public_key=base64.b64encode(a.public_key).decode(),
            status=a.status,
            created_at=a.created_at,
        )


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


class AuditOut(BaseModel):
    id: int
    agent_id: uuid.UUID
    tool: str
    outcome: str
    detail: str | None
    timestamp: datetime


# --- helpers ---------------------------------------------------------------

def _get_or_404(db: Session, agent_id: uuid.UUID) -> Agent:
    a = db.get(Agent, agent_id)
    if a is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return a


# --- agent CRUD ------------------------------------------------------------

@app.post("/agents", response_model=AgentOut, status_code=201)
def create_agent(body: AgentCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Agent).where(Agent.name == body.name)):
        raise HTTPException(status_code=409, detail="name already in use")
    if db.scalar(select(func.count()).select_from(Agent)) >= MAX_AGENTS:
        raise HTTPException(status_code=409, detail="agent limit reached")
    a = create_keypair_for_agent(db, body.name)
    return AgentOut.of(a)


@app.get("/agents", response_model=list[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    return [AgentOut.of(a) for a in db.scalars(select(Agent)).all()]


@app.get("/agents/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    return AgentOut.of(_get_or_404(db, agent_id))


@app.delete("/agents/{agent_id}", status_code=204)
def delete_agent(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, agent_id))
    db.commit()


# --- compromise simulation -------------------------------------------------

@app.post("/agents/{agent_id}/tamper", response_model=AgentOut)
def tamper(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    a = tamper_agent(db, agent_id)
    if a is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return AgentOut.of(a)


@app.post("/agents/{agent_id}/revoke", response_model=AgentOut)
def revoke(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    a = _get_or_404(db, agent_id)
    a.status = REVOKED
    db.commit()
    db.refresh(a)
    return AgentOut.of(a)


# --- chat ------------------------------------------------------------------

@app.post("/agents/{agent_id}/chat", response_model=ChatResponse)
async def chat(agent_id: uuid.UUID, body: ChatRequest, db: Session = Depends(get_db)):
    _get_or_404(db, agent_id)  # 404 fast; tamper/revoke are enforced at the tool layer
    answer = await agent_runtime.answer(agent_id, body.message)
    return ChatResponse(answer=answer)


# --- audit -----------------------------------------------------------------

@app.get("/audit", response_model=list[AuditOut])
def audit(
    agent_id: uuid.UUID | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if agent_id is not None:
        stmt = stmt.where(AuditLog.agent_id == agent_id)
    return db.scalars(stmt).all()
