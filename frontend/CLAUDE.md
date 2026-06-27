# Frontend — CLAUDE.md

Dashboard for the PQC Agent ID simulation: a single-page app over the FastAPI backend. Built incrementally, module by module. The frontend never sees secret keys — only agent ids, names, public keys, status, chat messages, and audit entries.

## Stack
- **React 19 + Vite 6 + TypeScript** (SPA, talks to FastAPI over HTTP/JSON).
- **Tailwind CSS v4** (`@tailwindcss/vite`, no `tailwind.config.js`) + **shadcn/ui** (new-york style, neutral base; components hand-added under `components/ui/`). Theme tokens live in `src/index.css`.
- **lucide-react** icons. Data fetching is plain `fetch` wrapped in a typed client — no query library yet.

## Layout
- `src/lib/api.ts` — typed client for every endpoint the UI uses (list/get/create/delete/tamper/chat/audit). `VITE_API_BASE_URL` sets the backend URL (default `http://localhost:8000`). Revoke exists on the backend but is intentionally not surfaced.
- `src/types.ts` — TS mirrors of the FastAPI response models (`Agent`, `AuditEntry`, `ChatResponse`).
- `src/components/ui/` — shadcn primitives (`button`, `input`, `badge`, …).
- `src/components/` — app components (`AgentRail`, and later the detail/chat/audit panels).
- `src/App.tsx` — two-pane shell: left agent rail, right selected-agent detail.
- `src/index.css` — Tailwind import + shadcn CSS variables (light/dark, plus a `--success` for audit greens).
- `@/*` is aliased to `src/*` (in `tsconfig.json` and `vite.config.ts`).

## UX / behaviour
- **Session-scoped view:** the dashboard shows only what's created in the current browser session — the agent rail and audit feed start **empty on every load** and populate as you create agents and chat. A reload resets the view; backend state in Postgres (the `agents` and `audit_log` rows) is left untouched. `App.tsx` builds its agent list from create responses (no list fetch on mount) and filters the global `GET /audit` poll down to the session's agents.
- **Left rail:** agents as little robot icons (`Bot`), with an inline create form. Click one to select it.
- **Agent detail:** chat with the agent, plus **Tamper** and **Delete** buttons (no revoke in the UI).
- **Security story is front and center:** the audit feed is color-coded (green `executed`, red `rejected_*`), and an agent is shown **COMPROMISED** when its recent audit contains `rejected_signature` — there is no "tampered" status on the backend, so the UI *infers* it.
- **Chat is multi-turn:** the backend remembers per-agent history (`MemorySaver` keyed by `agent_id`), so follow-up questions work. Each request still sends only the new message.
- **Audit is polled** (`GET /audit`) — the backend has no SSE/WebSocket.

## Conventions
- All crypto stays server-side; the UI only renders identity/status/audit data.
- Surface backend rejections (tampered/revoked → blocked calls, `502` on agent run failures) to the user rather than failing silently.
- Keep the API base URL in env (`.env.local`), never hard-coded; `node_modules/` and build output are gitignored.

## Running
- `npm install`, then `npm run dev` (Vite dev server on **port 5173** — the origin the backend's CORS allows). `npm run build` runs `tsc --noEmit` then `vite build`.
- The backend must be running (`docker compose up --build` in `backend/`) for the dashboard to load agents.
