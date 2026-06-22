# PQC Agent ID

A simulation of a **post-quantum cryptographic identity and access-control system for AI agents**. Users create LangGraph + Google Gemini agents that answer natural-language questions over a SQL database. Every agent is issued an **ML-DSA-65** (CRYSTALS-Dilithium, NIST Level 3) keypair at creation, and **every tool call an agent makes is signed and verified** before it touches the data — so a compromised or revoked agent is locked out.

The agent never holds its own keys. The public key is the agent's registered identity in Postgres; the secret key is sealed with **AWS KMS envelope encryption** and only ever decrypted, briefly, inside the signing path. A **tamper** action swaps an agent's stored secret key for a random one to model a compromise — its signatures stop matching its registered public key, and every request it makes is rejected.

## How it works

- **Create an agent** — the backend generates an ML-DSA-65 keypair. The public key is stored as the agent's identity record (linked to its human-readable name); the secret key is envelope-encrypted under AWS KMS and stored as ciphertext.
- **Chat with an agent** — a FastAPI endpoint runs the agent's LangGraph graph (Gemini as the LLM). Given a natural-language question, the agent decides which MCP tool to call to answer it.
- **Signed tool calls** — the agent is an MCP client. The MCP server intercepts every call, checks revocation, briefly decrypts the agent's secret key via KMS, signs the call payload, and verifies that signature against the agent's *registered* public key. Match → the call runs; mismatch → it's rejected.
- **Query the data** — agents read a seeded demo SQL database through **read-only** MCP tools (schema introspection + `SELECT` execution). No writes, ever.
- **Tamper** — replaces the agent's stored secret key with a random one. Future signatures no longer verify against the registered public key, so all of the agent's requests are blocked.
- **Revoke** — instantly blocks an agent. Revocation is checked before any cryptographic work.
- **Audit** — every tool call writes exactly one audit record with its outcome: `executed`, `rejected_signature`, or `rejected_revoked`.

## Features

- **Per-agent ML-DSA-65 identity** issued at creation; the public key is the agent's identity record.
- **KMS envelope encryption** of every secret key — the master key never leaves AWS KMS.
- **Signed MCP tool calls** — each call is verified against the agent's registered public key before execution.
- **Natural-language data access** — LangGraph + Gemini agents translate questions into read-only SQL tool calls.
- **Instant revocation** — revoked agents are blocked before any crypto runs.
- **Tamper simulation** — swaps an agent's signing key so its calls fail verification, modelling a compromised agent.
- **Full audit log** — every tool call is recorded with its outcome.

## Stack

- **Crypto:** ML-DSA-65 via [liboqs](https://github.com/open-quantum-safe/liboqs) (liboqs-python)
- **Key protection:** AWS KMS envelope encryption (boto3) + AES-256-GCM (`cryptography`)
- **Agent runtime:** Google Gemini via LangGraph
- **API:** FastAPI (agent CRUD, chat, tamper, revoke, audit)
- **Tool layer:** MCP server (Python MCP SDK / FastMCP) + signing middleware
- **Storage:** Postgres (agent identity, key material, audit log, and the seeded demo dataset)
- **Runtime:** Docker Compose (the Linux container builds liboqs cleanly)

## Layout

```
backend/      flat Python modules (see backend/CLAUDE.md)
  api.py        FastAPI app (agent CRUD, chat, tamper, revoke, audit) — port 8000
  agent.py      LangGraph + Gemini agent, MCP client
  mcp_server.py MCP server (read-only SQL tools) — port 8001
  signing.py    signing/verification middleware
  kms.py crypto.py keystore.py    key protection + ML-DSA-65
  config.py db.py models.py audit.py bootstrap.py
  seed/         demo dataset (.sql files, seeded on startup)
  tests/        pytest suite
frontend/     dashboard (later phase)
```

## Setup

1. Create an AWS KMS symmetric CMK; obtain a Google API key with the Gemini API enabled.
2. Copy `.env.example` → `.env` and fill in `AWS_REGION`, `KMS_KEY_ID`, AWS credentials, `DATABASE_URL`, `GOOGLE_API_KEY`.
3. `docker compose up` — starts Postgres (with the demo dataset seeded) and the backend.
4. Run the test suite to exercise keygen, KMS, signing, revocation/tamper, and the agent's SQL access end-to-end.
