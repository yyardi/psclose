import shutil
from pathlib import Path

import pytest

from psclose.config import Config
from psclose.ledger import assemble, open_ledger

ROOT = Path(__file__).resolve().parents[1]
BASE_DB = ROOT / "data" / "synthetic_ps_recon_scaled.sqlite"
JULY_DB = ROOT / "data" / "july_increment.sqlite"


@pytest.fixture(scope="session")
def config() -> Config:
    return Config.load(ROOT / "psclose.toml")


@pytest.fixture(scope="session")
def policy(config):
    return config.policy


@pytest.fixture
def history_ledger(tmp_path):
    """The June-closed base on its own, for replaying history."""
    conn = assemble(BASE_DB, [], tmp_path / "history.sqlite")
    yield conn
    conn.close()


@pytest.fixture
def july_ledger(tmp_path):
    """Base plus the July increment, before any July close has run."""
    conn = assemble(BASE_DB, [JULY_DB], tmp_path / "july.sqlite")
    yield conn
    conn.close()


def make_increment(path: Path, schema_from: Path, rows: dict[str, list[tuple]]) -> Path:
    """Build an increment database with the production schema and the given rows."""
    import sqlite3

    src = sqlite3.connect(schema_from)
    ddl = [r[0] for r in src.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND sql IS NOT NULL")]
    src.close()
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    for statement in ddl:
        conn.execute(statement)
    for table, table_rows in rows.items():
        if not table_rows:
            continue
        placeholders = ", ".join("?" for _ in table_rows[0])
        conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", table_rows)
    conn.commit()
    conn.close()
    return path


def _ts(project: str, name: str, day: str, worker: str, hours: float, n: int, billable: int = 1, notes: str = "per timesheet export"):
    return (
        f"TSA-{project}-{worker}-{n:04d}", f"OA-A-{project}-{worker}-{n:04d}", project, name, f"2026-08-{day}",
        f"worker-{project}-{worker}-2026-08", "Implementation Services", hours, "Approved", billable,
        "Billable" if billable else "Productive", notes, "2026-08",
    )


@pytest.fixture
def august_increment(tmp_path) -> Path:
    """A small, plausible August: hours on a few projects, one acceptance, one POC
    confirmation (so the other three POC projects go unconfirmed), one EUR rate."""
    timesheets = []
    n = 0
    for day in ("03", "10", "17", "24"):
        for worker in ("A", "B"):
            n += 1
            timesheets.append(_ts("PX-17", "Quarrystone Ins. Core RollOut", day, worker, 2.5, n))
            n += 1
            timesheets.append(_ts("PX-43", "Thistledown Analytics Core Delivery", day, worker, 4.0, n))
            n += 1
            timesheets.append(_ts("PX-13", "Meridian Retail Modernization", day, worker, 1.5, n))
            n += 1
            timesheets.append(_ts("PX-24", "Xylo Manufacturing Advisory Program", day, worker, 3.0, n))
    n += 1
    timesheets.append(_ts("PX-24", "Xylo Manufacturing Advisory Program", "12", "C", 2.0, n, billable=0, notes="internal enablement"))
    n += 1
    timesheets.append(_ts("PX-01", "Aurelia Hlth Data Program", "04", "A", 3.0, n))
    rows = {
        "timesheet_entry": timesheets,
        "project_event": [
            ("EVT-PX-01-AUG-1", "PX-01", "customer_acceptance", "2026-08-06", "confirmed", "delivery-lead", "{}"),
            ("EVT-PX-43-AUG-1", "PX-43", "status_review", "2026-08-12", "logged", "pm-office", "{}"),
        ],
        "ops_poc_snapshot": [
            ("POC-PX-14-2026-08", "PX-14", "2026-08", 75.0, "delivery_lead_confirmation", "per PM tracker, confirmed with delivery lead"),
        ],
        "fx_rate": [("FX-EUR-2026-08-31", "EUR", "2026-08-31", 1.07)],
    }
    return make_increment(tmp_path / "august_increment.sqlite", JULY_DB, rows)
