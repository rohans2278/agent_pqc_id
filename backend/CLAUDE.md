# Backend — CLAUDE.md

Python backend for the PQC Agent ID simulation. Flat layout — these are plain modules, **not an installed package** (no `__init__.py`, no build backend). Run from the `backend/` directory so the modules import each other directly. Three concerns live here: the FastAPI app, the LangGraph + Gemini agent runtime, and the MCP server. Agents answer natural-language questions over a seeded demo SQL database; every tool call is signed with the agent's ML-DSA-65 key and verified against its registered public key before it runs.

## Layout (flat modules)
- `config.py` — pydantic-settings, all config from env (`AWS_REGION`, `KMS_KEY_ID`, AWS creds, `DATABASE_URL`, `QUERY_DATABASE_URL`, `GOOGLE_API_KEY`)
- `db.py` — SQLAlchemy engine + session factory
- `models.py` — `Agent`, `AuditLog` ORM models
- `kms.py` — `envelope_encrypt()` / `envelope_decrypt()` (boto3 + AES-256-GCM)
- `crypto.py` — ML-DSA-65 keygen / sign / verify via `oqs` (liboqs-python)
- `keystore.py` — `create_keypair_for_agent()`, `load_secret_key()`, `tamper_agent()`
- `audit.py` — `write_audit_entry()`
- `bootstrap.py` — startup: `create_all()` for the ORM tables, then run the demo `seed/*.sql` files
- `api.py` — FastAPI app: agent CRUD, `chat`, `tamper`, `revoke`, audit query
- `agent.py` — LangGraph graph driving Gemini; connects to the MCP server as a client. The `chat` endpoint invokes this.
- `mcp_server.py` — MCP server; read-only SQL tools (schema introspection + `SELECT` execution)
- `signing.py` — interception middleware: revocation check → load SK → sign → verify → execute → audit
- `seed/` — plain folder of `.sql` files only (demo dataset schema + rows). **No `__init__.py`** — not a Python package. The bootstrap step runs these on startup, after `create_all()`.
- `tests/` — pytest
- `pyproject.toml` — `[project]` dependencies only, installed with **uv** (no setuptools/poetry, no build backend)
- `Dockerfile` — builds liboqs and provides the runtime image (shared by both services)

## How a request flows
1. User hits the FastAPI `chat` endpoint with an `agent_id` and a natural-language question.
2. The LangGraph agent (Gemini) decides which MCP tool to call and with what args.
3. Each call carries the `agent_id` so the MCP server knows whose key to load.
4. `signing.py` runs the middleware: revocation check, then envelope-decrypt the SK, sign the canonical payload, verify against the registered PK, and either execute the tool or reject — writing exactly one audit row either way.

## Security invariants (do not violate)
- **The KMS master key never leaves KMS.** Only `GenerateDataKey` (encrypt path) and `Decrypt` (decrypt path) cross the boundary. The SK is never sent to KMS directly (it exceeds the 4 KB limit and that's not the design).
- **Never log, return, or persist a plaintext secret key or data key.** Decrypt the SK only inside `load_secret_key` / the signing path; overwrite/zero the bytes in a `finally` block immediately after signing.
- **Verification uses the agent's *registered* public key** from the `agents` row — never a key derived from the SK being used to sign. This is what makes tamper detectable.
- **Revocation is checked first**, before any KMS/crypto work, and returns `rejected_revoked`.
- **All data access is read-only and isolated to the `demo` schema.** Agent SQL runs over `query_engine` (the restricted `agent_ro` role from `QUERY_DATABASE_URL`), which has `SELECT` only on `demo` and no privileges on `agents`/`audit_log`. Belt-and-suspenders in code too: single-statement `SELECT`/`WITH` only, inside a `READ ONLY` transaction. Never run agent SQL on the privileged connection.
- New MCP tools must route through `signing.py` — never expose a tool that skips signature verification.
- Keep `.env` out of git (already in `.gitignore`). Use `.env.example` for the contract.

## Conventions
- ML-DSA mechanism name is `"ML-DSA-65"`; on import assert it's in `oqs.get_enabled_sig_mechanisms()` (older liboqs exposes `"Dilithium3"` — fail loudly with guidance rather than silently picking the wrong one).
- Canonical signing payload = deterministic JSON of `{agent_id, tool, args, timestamp, nonce}`, then SHA-256. Sign/verify over the same bytes on both sides.
- `agent_id` is passed with every MCP tool call; the middleware looks up that agent's SK/PK from Postgres.
- Every tool call writes exactly one `audit_log` row with `outcome` ∈ `executed | rejected_signature | rejected_revoked`.
- The demo dataset is fixed and seeded from `seed/`; give the agent a schema-introspection tool so Gemini can discover tables/columns before composing a query.

## Running & testing
- Built and run via Docker Compose (liboqs builds cleanly in the Linux container; native Windows is not supported). Dependencies install with uv from `pyproject.toml`.
- **One image, two services.** `docker-compose.yml` runs two startup commands from the same image: `uvicorn` for the FastAPI app on **port 8000**, and `python mcp_server.py` for the MCP server on **port 8001**.
- `test_kms.py` hits **real** AWS KMS and the agent tests hit the **real** Gemini API — they need valid credentials in the environment.
- Prefer running the full suite inside the container so the liboqs build matches.
