import type { Agent, AuditEntry, ChatResponse } from "@/types"

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// Note: revoke exists on the backend but is intentionally not surfaced here —
// the UI exposes tamper + delete only.
export const api = {
  listAgents: () => request<Agent[]>("/agents"),
  getAgent: (id: string) => request<Agent>(`/agents/${id}`),
  createAgent: (name: string) =>
    request<Agent>("/agents", { method: "POST", body: JSON.stringify({ name }) }),
  deleteAgent: (id: string) =>
    request<void>(`/agents/${id}`, { method: "DELETE" }),
  tamperAgent: (id: string) =>
    request<Agent>(`/agents/${id}/tamper`, { method: "POST" }),
  chat: (id: string, message: string) =>
    request<ChatResponse>(`/agents/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  audit: (agentId?: string) =>
    request<AuditEntry[]>(`/audit${agentId ? `?agent_id=${agentId}` : ""}`),
}
