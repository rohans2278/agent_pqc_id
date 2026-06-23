-- Demo dataset: a small e-commerce store. Lives in its own `demo` schema,
-- separate from the system tables (public.agents / public.audit_log).
-- Idempotent: safe to run on every startup.

CREATE SCHEMA IF NOT EXISTS demo;

CREATE TABLE IF NOT EXISTS demo.customers (
    id          integer PRIMARY KEY,
    name        text NOT NULL,
    email       text NOT NULL,
    country     text NOT NULL,
    created_at  date NOT NULL
);

CREATE TABLE IF NOT EXISTS demo.products (
    id        integer PRIMARY KEY,
    name      text NOT NULL,
    category  text NOT NULL,
    price     numeric(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS demo.orders (
    id           integer PRIMARY KEY,
    customer_id  integer NOT NULL REFERENCES demo.customers (id),
    ordered_at   date NOT NULL,
    status       text NOT NULL
);

CREATE TABLE IF NOT EXISTS demo.order_items (
    id          integer PRIMARY KEY,
    order_id    integer NOT NULL REFERENCES demo.orders (id),
    product_id  integer NOT NULL REFERENCES demo.products (id),
    quantity    integer NOT NULL,
    unit_price  numeric(10, 2) NOT NULL
);

-- Restricted role the MCP server connects as for agent queries (QUERY_DATABASE_URL).
-- It can read ONLY the demo schema; it has no privileges on public.agents /
-- public.audit_log, so a query like `SELECT * FROM public.agents` fails outright.
-- (Demo-only password; this is a local simulation.)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'agent_ro') THEN
        CREATE ROLE agent_ro LOGIN PASSWORD 'agent_ro';
    END IF;
END $$;

GRANT USAGE ON SCHEMA demo TO agent_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA demo TO agent_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA demo GRANT SELECT ON TABLES TO agent_ro;
ALTER ROLE agent_ro SET search_path = demo;
