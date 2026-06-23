"""Startup: create the ORM tables, then run the demo seed SQL.

Called once when the FastAPI app starts. `create_all` makes the `agents` and
`audit_log` tables; the seed/*.sql files (run in filename order) build and
populate the `demo` schema the agents query. The seed files are expected to be
idempotent, since this runs on every startup.
"""

from pathlib import Path

import models  # noqa: F401  — import so the tables register on Base.metadata
from db import Base, engine

SEED_DIR = Path(__file__).parent / "seed"


def init_db() -> None:
    Base.metadata.create_all(engine)
    _run_seed()


def _run_seed() -> None:
    if not SEED_DIR.is_dir():
        return
    for path in sorted(SEED_DIR.glob("*.sql")):
        sql = path.read_text()
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)  # raw, so ':' in SQL isn't read as a bind param
