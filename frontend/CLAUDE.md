# Frontend — CLAUDE.md

Dashboard for the PQC Agent ID simulation. **This is a later phase — not built yet.** This file captures intent so work here stays consistent with the backend.

## Purpose
A management dashboard over the FastAPI backend:
- **Create / delete agent** — issues an ML-DSA-65 keypair (backend handles keygen + KMS envelope encryption). Users manage a limited number of agents.
- **Chat** — ask an agent a natural-language question and see its answer. The agent (LangGraph + Gemini) decides which read-only SQL tool to call; ideally surface the tool call(s) it made so the signed-access flow is visible.
- **Tamper** button — calls the tamper endpoint to simulate a compromised agent; subsequent tool calls fail signature verification.
- **Revoke** button — instantly blocks an agent.
- **Audit view** — (ideally real-time) stream of tool calls with outcome `executed | rejected_signature | rejected_revoked`.
- **Dataset view** — (optional) browse the seeded demo SQL dataset the agents query, so users can sanity-check answers.

## Stack (proposed — confirm before building)
- React + Vite + TypeScript, talking to the FastAPI backend over HTTP/JSON.
- Real-time audit via SSE or WebSocket (backend support TBD).

## Backend contract it consumes (see `backend/CLAUDE.md`)
- `POST /agents`, `GET /agents`, `GET /agents/{id}`, `DELETE /agents/{id}`
- `POST /agents/{id}/chat` — natural-language question in, agent answer out
- `POST /agents/{id}/tamper`, `POST /agents/{id}/revoke`
- `GET /audit`

## Conventions
- The frontend never handles secret keys — it only sees agent ids, names, public keys, status, chat messages, and audit entries. All crypto stays server-side.
- A tampered or revoked agent will return rejected chat/tool calls; surface the rejection outcome to the user rather than failing silently.
- Keep API base URL and any keys in env (`.env.local`), never hard-coded; `node_modules/` and build output are gitignored.
