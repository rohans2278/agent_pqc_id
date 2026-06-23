"""MCP server: the only way an agent reaches the data.

Two tools, both read-only, both routed through signing.authorize so a tampered
or revoked agent is stopped before any query runs:
  - get_schema: list the demo tables/columns so the LLM can compose a query
  - run_sql:    execute a single read-only SELECT and return the rows

Isolation is enforced at the database, not just in code: data queries run over
`query_engine`, a connection as the restricted `agent_ro` role (QUERY_DATABASE_URL)
that has SELECT only on the `demo` schema and no privileges on the system tables
(`public.agents` / `public.audit_log`). Reads are further constrained to a single
SELECT/WITH statement inside a READ ONLY transaction. The privileged SessionLocal
is used only for agent lookup and audit writes, never for agent-supplied SQL.
"""

import json

from mcp.server.fastmcp import Context, FastMCP
from sqlalchemy import create_engine, text

import signing
from audit import write_audit_entry
from config import settings
from db import SessionLocal
from models import EXECUTED

DEMO_SCHEMA = "demo"
MAX_ROWS = 100
_READ_ONLY_START = ("select", "with")

# Restricted, read-only connection for agent-supplied queries.
query_engine = create_engine(settings.query_database_url, pool_pre_ping=True)

mcp = FastMCP("pqc-agent-id", host="0.0.0.0", port=8001)


def _describe_schema() -> str:
    sql = text(
        """
        select table_name, column_name, data_type
        from information_schema.columns
        where table_schema = :schema
        order by table_name, ordinal_position
        """
    )
    with query_engine.connect() as conn:
        rows = conn.execute(sql, {"schema": DEMO_SCHEMA}).fetchall()

    tables: dict[str, list[str]] = {}
    for table_name, column_name, data_type in rows:
        tables.setdefault(table_name, []).append(f"{column_name} {data_type}")
    if not tables:
        return f"No tables found in schema '{DEMO_SCHEMA}'."
    return "\n".join(f"{t}({', '.join(cols)})" for t, cols in tables.items())


def _run_readonly(sql: str) -> str:
    statement = sql.strip().rstrip(";").strip()
    if not statement:
        raise ValueError("empty query")
    if ";" in statement:
        raise ValueError("only a single statement is allowed")
    if statement.split(None, 1)[0].lower() not in _READ_ONLY_START:
        raise ValueError("only read-only SELECT / WITH queries are allowed")

    with query_engine.connect() as conn, conn.begin():
        # Defense in depth: block writes at the DB level and scope name
        # resolution to the demo schema. Must precede the query.
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text(f"SET LOCAL search_path TO {DEMO_SCHEMA}"))
        result = conn.execute(text(statement))
        cols = list(result.keys())
        rows = result.fetchmany(MAX_ROWS)

    return json.dumps([dict(zip(cols, row)) for row in rows], default=str)


@mcp.tool()
def get_schema(ctx: Context) -> str:
    """List the tables and columns available to query."""
    db = SessionLocal()
    try:
        agent = signing.authorize(db, ctx, "get_schema", {})
        write_audit_entry(db, agent.id, "get_schema", EXECUTED)
        return _describe_schema()
    except signing.ToolRejected as e:
        return f"Request rejected: {e}"
    finally:
        db.close()


@mcp.tool()
def run_sql(sql: str, ctx: Context) -> str:
    """Run a single read-only SQL SELECT against the demo database and return the
    matching rows as JSON. Only SELECT/WITH queries are allowed."""
    db = SessionLocal()
    try:
        agent = signing.authorize(db, ctx, "run_sql", {"sql": sql})
        # Access granted: this is the one audit row for the call.
        write_audit_entry(db, agent.id, "run_sql", EXECUTED, sql[:500])
        return _run_readonly(sql)
    except signing.ToolRejected as e:
        return f"Request rejected: {e}"
    except ValueError as e:
        return f"Query error: {e}"
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
