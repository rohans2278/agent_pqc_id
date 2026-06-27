import { cn } from "@/lib/utils"
import type { AuditEntry, AuditOutcome } from "@/types"

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

export function AuditFeed({ entries }: { entries: AuditEntry[] }) {
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
          <ul className="space-y-1">
            {entries.map((entry) => (
              <li
                key={entry.id}
                className="rounded-md px-2 py-1.5 text-xs hover:bg-accent"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-1.5 font-mono">
                    <span
                      className={cn(
                        "size-1.5 shrink-0 rounded-full",
                        OUTCOME_DOT[entry.outcome],
                      )}
                    />
                    {entry.tool}
                  </span>
                  <span
                    className={cn("font-medium", OUTCOME_STYLE[entry.outcome])}
                  >
                    {entry.outcome}
                  </span>
                </div>
                {entry.detail && (
                  <p
                    className="mt-0.5 truncate font-mono text-muted-foreground"
                    title={entry.detail}
                  >
                    {entry.detail}
                  </p>
                )}
                <p className="text-[10px] text-muted-foreground">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
