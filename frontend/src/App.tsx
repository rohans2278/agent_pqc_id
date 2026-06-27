import { useCallback, useEffect, useMemo, useState } from "react"
import { ShieldCheck } from "lucide-react"

import { AgentDetail } from "@/components/AgentDetail"
import { AgentRail } from "@/components/AgentRail"
import { AuditFeed } from "@/components/AuditFeed"
import { api } from "@/lib/api"
import type { Agent, AuditEntry } from "@/types"

const AUDIT_POLL_MS = 2000

function App() {
  // The dashboard is session-scoped: agents (and therefore the audit feed) start
  // empty on every load and only show what's created in this browser session.
  // Backend state in Postgres is untouched — a reload just resets this view.
  const [agents, setAgents] = useState<Agent[]>([])
  const [audit, setAudit] = useState<AuditEntry[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const refreshAudit = useCallback(async () => {
    try {
      setAudit(await api.audit())
    } catch {
      // transient poll failure; keep the last snapshot
    }
  }, [])

  // Poll the audit log so the feed and compromised state stay live.
  useEffect(() => {
    void refreshAudit()
    const id = setInterval(() => void refreshAudit(), AUDIT_POLL_MS)
    return () => clearInterval(id)
  }, [refreshAudit])

  // Scope the global audit log to this session's agents only.
  const sessionAudit = useMemo(() => {
    const ids = new Set(agents.map((a) => a.id))
    return audit.filter((e) => ids.has(e.agent_id))
  }, [audit, agents])

  // An agent is "compromised" once any of its signed calls fails verification.
  const compromisedIds = useMemo(
    () =>
      new Set(
        sessionAudit
          .filter((e) => e.outcome === "rejected_signature")
          .map((e) => e.agent_id),
      ),
    [sessionAudit],
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

      <div className="flex min-h-0 flex-1">
        <AgentRail
          agents={agents}
          selectedId={selectedId}
          compromisedIds={compromisedIds}
          onSelect={setSelectedId}
          onCreated={(agent) => {
            setAgents((prev) => [...prev, agent])
            setSelectedId(agent.id)
          }}
        />
        <main className="min-w-0 flex-1">
          {selected ? (
            <AgentDetail
              key={selected.id}
              agent={selected}
              compromised={compromisedIds.has(selected.id)}
              onChanged={() => void refreshAudit()}
              onDeleted={() => {
                setAgents((prev) => prev.filter((a) => a.id !== selected.id))
                setSelectedId(null)
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
            entries={sessionAudit}
            agents={agents}
            onSelectAgent={setSelectedId}
          />
        </aside>
      </div>
    </div>
  )
}

export default App
