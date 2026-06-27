// Mirrors the FastAPI response models (see backend/api.py).

export type AgentStatus = "active" | "revoked"

export interface Agent {
  id: string
  name: string
  public_key: string // base64-encoded ML-DSA-65 public key
  status: AgentStatus
  created_at: string
}

export type AuditOutcome = "executed" | "rejected_signature" | "rejected_revoked"

export interface AuditEntry {
  id: number
  agent_id: string
  tool: string
  outcome: AuditOutcome
  detail: string | null
  timestamp: string
}

export interface ChatResponse {
  answer: string
}
