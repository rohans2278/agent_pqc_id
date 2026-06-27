import { type FormEvent, useEffect, useRef, useState } from "react"
import { Send } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

interface Message {
  role: "user" | "agent"
  content: string
  error?: boolean
}

export function ChatPanel({ agentId }: { agentId: string }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, sending])

  async function send(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return
    setInput("")
    setMessages((prev) => [...prev, { role: "user", content: text }])
    setSending(true)
    try {
      const { answer } = await api.chat(agentId, text)
      const trimmed = answer.trim()
      setMessages((prev) => [
        ...prev,
        trimmed
          ? { role: "agent", content: trimmed }
          : {
              role: "agent",
              content: "(the agent returned an empty response — try rephrasing)",
              error: true,
            },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: (err as Error).message, error: true },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <p className="grid h-full place-items-center text-center text-sm text-muted-foreground">
            Ask this agent about the database — e.g. “How many customers are
            there?”
          </p>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-3">
            {messages.map((m, i) => (
              <div
                key={i}
                className={cn(
                  "max-w-[80%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm",
                  m.role === "user"
                    ? "self-end bg-primary text-primary-foreground"
                    : m.error
                      ? "self-start bg-destructive/10 text-destructive"
                      : "self-start bg-muted",
                )}
              >
                {m.content}
              </div>
            ))}
            {sending && (
              <div className="self-start rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                thinking…
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>

      <form onSubmit={send} className="flex gap-2 border-t p-4">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about the data…"
          disabled={sending}
        />
        <Button
          type="submit"
          size="icon"
          disabled={sending || !input.trim()}
          aria-label="Send"
        >
          <Send />
        </Button>
      </form>
    </div>
  )
}
