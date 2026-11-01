"""Assemble the working ledger: the closed base database plus any increment databases.

The inputs are never written to. Each run copies the base file to the output directory and
upserts every increment on top, so an increment that restates a master row (a project that
moved to completed, say) wins, while fact rows simply accumulate. A load_log table records
what came from where.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

# Load order follows the foreign keys so a partially loaded increment still makes sense.
SOURCE_TABLES = [
    "customer",
    "project",
    "sales_order",
    "contract_item",
    "fx_rate",
    "timesheet_entry",
    "project_event",
    "project_hours_adjustment",
    "ops_poc_snapshot",
    "rma_event",
    "accounting_posting",
    "revenue_schedule",
]

ENGINE_SCHEMA = """
CREATE TABLE IF NOT EXISTS load_log (
    loaded_at TEXT NOT NULL,
    source_file TEXT NOT NULL,
    table_name TEXT NOT NULL,
    rows_loaded INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS timesheet_resolution (
    timesheet_id TEXT PRIMARY KEY,
    project_id TEXT,
    method TEXT NOT NULL,
    matched_name TEXT
);
CREATE TABLE IF NOT EXISTS timesheet_attribution (
    timesheet_id TEXT NOT NULL,
    contract_item_id TEXT NOT NULL,
    share REAL NOT NULL,
    method TEXT NOT NULL,
    PRIMARY KEY (timesheet_id, contract_item_id)
);
CREATE TABLE IF NOT EXISTS item_policy (
    contract_item_id TEXT NOT NULL,
    period TEXT NOT NULL,
    method TEXT NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (contract_item_id, period)
);
CREATE TABLE IF NOT EXISTS close_exception (
    period TEXT NOT NULL,
    code TEXT NOT NULL,
    severity TEXT NOT NULL,
    project_id TEXT,
    contract_item_id TEXT,
    amount_native REAL,
    currency TEXT,
    message TEXT NOT NULL,
    evidence TEXT,
    question TEXT
);
CREATE TABLE IF NOT EXISTS project_rollup (
    period TEXT NOT NULL,
    project_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    customer TEXT,
    display_name TEXT,
    billing_type TEXT,
    project_status TEXT,
    currency TEXT,
    items INTEGER,
    contract_total REAL,
    recognized_prior REAL,
    recognized_cum REAL,
    recognized_period REAL,
    planned_cum REAL,
    billable_hours_period REAL,
    all_hours_period REAL,
    billable_hours_cum REAL,
    pct_recognized REAL,
    fx_to_usd REAL,
    fx_rate_date TEXT,
    recognized_cum_usd REAL,
    recognized_period_usd REAL,
    exceptions INTEGER,
    PRIMARY KEY (period, project_id, scope)
);
"""


def open_ledger(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(ENGINE_SCHEMA)
    return conn


def _columns(conn: sqlite3.Connection, schema: str, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA {schema}.table_info({table})")]


def _tables(conn: sqlite3.Connection, schema: str) -> set[str]:
    rows = conn.execute(f"SELECT name FROM {schema}.sqlite_master WHERE type = 'table'")
    return {r["name"] for r in rows}


def assemble(base: Path, increments: list[Path], dest: Path) -> sqlite3.Connection:
    """Copy base to dest and upsert each increment into it, in order."""
    base, dest = Path(base), Path(dest)
    if not base.exists():
        raise FileNotFoundError(base)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    shutil.copyfile(base, dest)
    conn = open_ledger(dest)
    conn.execute(
        "INSERT INTO load_log VALUES (datetime('now'), ?, '*', ?)",
        (str(base), sum(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in SOURCE_TABLES)),
    )
    for inc in increments:
        load_increment(conn, Path(inc))
    conn.commit()
    return conn


def load_increment(conn: sqlite3.Connection, path: Path) -> dict[str, int]:
    if not path.exists():
        raise FileNotFoundError(path)
    conn.execute("ATTACH DATABASE ? AS inc", (str(path),))
    loaded: dict[str, int] = {}
    try:
        present = _tables(conn, "inc")
        for table in SOURCE_TABLES:
            if table not in present:
                continue
            cols = [c for c in _columns(conn, "inc", table) if c in _columns(conn, "main", table)]
            col_list = ", ".join(cols)
            count = conn.execute(f"SELECT COUNT(*) FROM inc.{table}").fetchone()[0]
            if count:
                conn.execute(
                    f"INSERT OR REPLACE INTO main.{table} ({col_list}) SELECT {col_list} FROM inc.{table}"
                )
            loaded[table] = count
            conn.execute(
                "INSERT INTO load_log VALUES (datetime('now'), ?, ?, ?)", (str(path), table, count)
            )
        conn.commit()
    finally:
        conn.execute("DETACH DATABASE inc")
    return loaded


def last_closed_period(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT MAX(period) FROM revenue_schedule").fetchone()
    return row[0]


def row_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def fx_latest(conn: sqlite3.Connection, currency: str, on_or_before: str) -> tuple[float, str] | None:
    """Most recent to_usd rate on or before a date, with the date it was taken."""
    row = conn.execute(
        "SELECT to_usd, rate_date FROM fx_rate WHERE currency = ? AND rate_date <= ? "
        "ORDER BY rate_date DESC LIMIT 1",
        (currency, on_or_before),
    ).fetchone()
    return (row["to_usd"], row["rate_date"]) if row else None
