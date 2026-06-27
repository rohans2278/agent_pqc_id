import { useState } from "react"
import { Bot, ShieldAlert, Trash2 } from "lucide-react"

import { AuditFeed } from "@/components/AuditFeed"
import { ChatPanel } from "@/components/ChatPanel"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { Agent, AuditEntry } from "@/types"

interface AgentDetailProps {
  agent: Agent
  compromised: boolean
  auditEntries: AuditEntry[]
  onChanged: () => void // refresh after tamper
  onDeleted: () => void // clear selection + refresh
}

export function AgentDetail({
  agent,
  compromised,
  auditEntries,
  onChanged,
  onDeleted,
}: AgentDetailProps) {
  const [busy, setBusy] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function tamper() {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await api.tamperAgent(agent.id)
      setNotice(
        "Agent tampered — its stored key no longer matches its identity. Ask it something to see its signed calls get rejected.",
      )
      onChanged()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    setError(null)
    try {
      await api.deleteAgent(agent.id)
      onDeleted()
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-4 border-b p-6">
        <div className="flex min-w-0 items-center gap-3">
          <div
            className={cn(
              "grid size-10 shrink-0 place-items-center rounded-lg",
              compromised ? "bg-destructive/10" : "bg-accent",
            )}
          >
            <Bot
              className={cn(
                "size-6",
                compromised ? "text-destructive" : "text-muted-foreground",
              )}
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="truncate text-xl font-semibold">{agent.name}</h2>
              {compromised ? (
                <Badge variant="destructive">COMPROMISED</Badge>
              ) : (
                <Badge variant="success">verified</Badge>
              )}
            </div>
            <p
              className="truncate font-mono text-xs text-muted-foreground"
              title={agent.public_key}
            >
              pk&nbsp;{agent.public_key.slice(0, 24)}…
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button variant="outline" onClick={tamper} disabled={busy}>
            <ShieldAlert /> Tamper
          </Button>
          {confirmDelete ? (
            <>
              <Button variant="destructive" onClick={remove} disabled={busy}>
                Confirm delete
              </Button>
              <Button
                variant="ghost"
                onClick={() => setConfirmDelete(false)}
                disabled={busy}
              >
                Cancel
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setConfirmDelete(true)}
              disabled={busy}
              aria-label="Delete agent"
            >
              <Trash2 />
            </Button>
          )}
        </div>
      </div>

      {notice && <p className="border-b bg-accent px-6 py-2 text-sm">{notice}</p>}
      {error && (
        <p className="border-b bg-destructive/10 px-6 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex min-h-0 flex-1">
        <ChatPanel agentId={agent.id} />
        <aside className="w-80 shrink-0 border-l">
          <AuditFeed entries={auditEntries} />
        </aside>
      </div>
    </div>
  )
}
