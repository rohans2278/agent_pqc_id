import { useCallback, useEffect, useState } from "react"

import { AgentDetail } from "@/components/AgentDetail"
import { AgentRail } from "@/components/AgentRail"
import { api } from "@/lib/api"
import type { Agent } from "@/types"

function App() {
  const [agents, setAgents] = useState<Agent[]>([])
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

  useEffect(() => {
    void refresh()
  }, [refresh])

  const selected = agents.find((a) => a.id === selectedId) ?? null

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <header className="border-b">
        <div className="flex items-center gap-2 px-6 py-3">
          <h1 className="text-lg font-semibold">PQC Agent ID</h1>
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
              onChanged={() => void refresh()}
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
      </div>
    </div>
  )
}

export default App
