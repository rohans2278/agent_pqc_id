import { useCallback, useEffect, useMemo, useState } from "react"
import { ShieldCheck } from "lucide-react"

import { AgentDetail } from "@/components/AgentDetail"
import { AgentRail } from "@/components/AgentRail"
import { AuditFeed } from "@/components/AuditFeed"
import { api } from "@/lib/api"
import type { Agent, AuditEntry } from "@/types"

const AUDIT_POLL_MS = 2000

function App() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [audit, setAudit] = useState<AuditEntry[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setAgents(await api.listAgents())
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  const refreshAudit = useCallback(async () => {
    try {
      setAudit(await api.audit())
    } catch {
      // transient poll failure; keep the last snapshot
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  // Poll the audit log so the feed and compromised state stay live.
  useEffect(() => {
    void refreshAudit()
    const id = setInterval(() => void refreshAudit(), AUDIT_POLL_MS)
    return () => clearInterval(id)
  }, [refreshAudit])

  // An agent is "compromised" once any of its signed calls fails verification.
  const compromisedIds = useMemo(
    () =>
      new Set(
        audit
          .filter((e) => e.outcome === "rejected_signature")
          .map((e) => e.agent_id),
      ),
    [audit],
  )

  const selected = agents.find((a) => a.id === selectedId) ?? null

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <header className="border-b">
        <div className="flex items-center gap-2.5 px-6 py-3">
          <ShieldCheck className="size-5 text-primary" />
          <h1 className="text-lg font-semibold">PQC Agent ID</h1>
          <span className="text-muted-foreground">·</span>
          <span className="text-sm text-muted-foreground">
            Post-quantum identity for AI agents
          </span>
        </div>
      </header>

      {error && (
        <p className="border-b bg-destructive/10 px-6 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex min-h-0 flex-1">
        <AgentRail
          agents={agents}
          selectedId={selectedId}
          compromisedIds={compromisedIds}
          onSelect={setSelectedId}
          onCreated={async (agent) => {
            await refresh()
            setSelectedId(agent.id)
          }}
        />
        <main className="min-w-0 flex-1">
          {selected ? (
            <AgentDetail
              key={selected.id}
              agent={selected}
              compromised={compromisedIds.has(selected.id)}
              onChanged={() => {
                void refresh()
                void refreshAudit()
              }}
              onDeleted={() => {
                setSelectedId(null)
                void refresh()
              }}
            />
          ) : (
            <div className="grid h-full place-items-center text-sm text-muted-foreground">
              Select an agent, or create one on the left.
            </div>
          )}
        </main>
        <aside className="w-80 shrink-0 border-l">
          <AuditFeed
            entries={audit}
            agents={agents}
            onSelectAgent={setSelectedId}
          />
        </aside>
      </div>
    </div>
  )
}

export default App
