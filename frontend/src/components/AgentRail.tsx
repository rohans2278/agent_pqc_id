import { type FormEvent, useState } from "react"
import { Bot, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { Agent } from "@/types"

interface AgentRailProps {
  agents: Agent[]
  selectedId: string | null
  compromisedIds: Set<string>
  onSelect: (id: string) => void
  onCreated: (agent: Agent) => void
}

export function AgentRail({
  agents,
  selectedId,
  compromisedIds,
  onSelect,
  onCreated,
}: AgentRailProps) {
  const [name, setName] = useState("")
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function create(e: FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    setCreating(true)
    setError(null)
    try {
      const agent = await api.createAgent(trimmed)
      setName("")
      onCreated(agent)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r">
      <form onSubmit={create} className="flex gap-2 border-b p-3">
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New agent name"
          disabled={creating}
        />
        <Button
          type="submit"
          size="icon"
          disabled={creating || !name.trim()}
          aria-label="Create agent"
        >
          <Plus />
        </Button>
      </form>

      {error && <p className="px-3 py-2 text-xs text-destructive">{error}</p>}

      <div className="flex-1 overflow-y-auto p-2">
        {agents.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            No agents yet
          </p>
        ) : (
          <ul className="space-y-1">
            {agents.map((agent) => {
              const compromised = compromisedIds.has(agent.id)
              return (
                <li key={agent.id}>
                  <button
                    onClick={() => onSelect(agent.id)}
                    className={cn(
                      "flex w-full items-center gap-2.5 rounded-md px-2 py-2 text-left text-sm transition-colors hover:bg-accent",
                      selectedId === agent.id && "bg-accent",
                    )}
                  >
                    <Bot
                      className={cn(
                        "size-5 shrink-0",
                        compromised ? "text-destructive" : "text-muted-foreground",
                      )}
                    />
                    <span className="min-w-0 flex-1 truncate">{agent.name}</span>
                    {compromised && (
                      <span
                        className="size-2 shrink-0 rounded-full bg-destructive"
                        title="compromised — signatures no longer verify"
                      />
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </aside>
  )
}
