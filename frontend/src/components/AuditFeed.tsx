import { cn } from "@/lib/utils"
import type { Agent, AuditEntry, AuditOutcome } from "@/types"

const OUTCOME_STYLE: Record<AuditOutcome, string> = {
  executed: "text-success",
  rejected_signature: "text-destructive",
  rejected_revoked: "text-destructive",
}

const OUTCOME_DOT: Record<AuditOutcome, string> = {
  executed: "bg-success",
  rejected_signature: "bg-destructive",
  rejected_revoked: "bg-destructive",
}

const OUTCOME_LABEL: Record<AuditOutcome, string> = {
  executed: "executed",
  rejected_signature: "blocked · invalid signature",
  rejected_revoked: "blocked · revoked",
}

// Plain-English phrasing per tool, in success vs attempted form.
const PHRASE: Record<string, { done: string; tried: string }> = {
  get_schema: { done: "inspected the schema", tried: "tried to inspect the schema" },
  run_sql: { done: "queried the data", tried: "tried to query the data" },
}

function describe(entry: AuditEntry): string {
  const phrase = PHRASE[entry.tool]
  if (!phrase) return entry.tool
  return entry.outcome === "executed" ? phrase.done : phrase.tried
}

interface AuditFeedProps {
  entries: AuditEntry[]
  agents: Agent[]
  onSelectAgent?: (id: string) => void
}

export function AuditFeed({ entries, agents, onSelectAgent }: AuditFeedProps) {
  const nameById = new Map(agents.map((a) => [a.id, a.name]))
  const nameFor = (id: string) => nameById.get(id) ?? `agent ${id.slice(0, 8)}`

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-3 text-sm font-medium">
        Audit
        <span className="ml-2 text-xs font-normal text-muted-foreground">
          every signed tool call
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {entries.length === 0 ? (
          <p className="px-2 py-6 text-center text-xs text-muted-foreground">
            No tool calls yet
          </p>
        ) : (
          <ul className="space-y-0.5">
            {entries.map((entry) => {
              const known = nameById.has(entry.agent_id)
              return (
                <li key={entry.id}>
                  <button
                    type="button"
                    onClick={() => known && onSelectAgent?.(entry.agent_id)}
                    title={entry.detail ?? undefined}
                    className={cn(
                      "w-full rounded-md px-2 py-1.5 text-left text-xs",
                      known ? "hover:bg-accent" : "cursor-default",
                    )}
                  >
                    <div className="flex items-center gap-1.5">
                      <span
                        className={cn(
                          "size-1.5 shrink-0 rounded-full",
                          OUTCOME_DOT[entry.outcome],
                        )}
                      />
                      <span className="min-w-0 flex-1 truncate">
                        <span className="font-medium">
                          {nameFor(entry.agent_id)}
                        </span>{" "}
                        <span className="text-muted-foreground">
                          {describe(entry)}
                        </span>
                      </span>
                    </div>
                    <div className="mt-0.5 flex items-center gap-1.5 pl-3 text-[10px]">
                      <span
                        className={cn(
                          "font-medium",
                          OUTCOME_STYLE[entry.outcome],
                        )}
                      >
                        {OUTCOME_LABEL[entry.outcome]}
                      </span>
                      <span className="text-muted-foreground">·</span>
                      <span className="text-muted-foreground">
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
