import hashlib

from psclose.ledger import assemble, last_closed_period, row_count
from tests.conftest import BASE_DB, JULY_DB


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_assemble_unions_increment_without_touching_inputs(tmp_path):
    before = (_digest(BASE_DB), _digest(JULY_DB))
    conn = assemble(BASE_DB, [JULY_DB], tmp_path / "ledger.sqlite")
    assert row_count(conn, "timesheet_entry") == 4402 + 768
    assert row_count(conn, "project") == 46
    assert row_count(conn, "contract_item") == 50
    assert row_count(conn, "revenue_schedule") == 236
    assert last_closed_period(conn) == "2026-06"
    sources = {r["source_file"] for r in conn.execute("SELECT source_file FROM load_log")}
    assert sources == {str(BASE_DB), str(JULY_DB)}
    assert (_digest(BASE_DB), _digest(JULY_DB)) == before


def test_assemble_is_repeatable(tmp_path):
    first = assemble(BASE_DB, [JULY_DB], tmp_path / "ledger.sqlite")
    counts = {t: row_count(first, t) for t in ("timesheet_entry", "project", "contract_item")}
    first.close()
    second = assemble(BASE_DB, [JULY_DB], tmp_path / "ledger.sqlite")
    assert {t: row_count(second, t) for t in counts} == counts


def test_increment_restating_a_master_row_wins(tmp_path):
    import sqlite3

    inc = tmp_path / "restate.sqlite"
    src = sqlite3.connect(JULY_DB)
    src.execute("ATTACH DATABASE ? AS new", (str(inc),))
    src.execute("CREATE TABLE new.project AS SELECT * FROM project WHERE 0")
    src.execute(
        "INSERT INTO new.project SELECT * FROM project"
    )
    src.execute("UPDATE new.project SET status = 'completed'")
    src.commit()
    src.close()
    conn = assemble(BASE_DB, [JULY_DB, inc], tmp_path / "ledger.sqlite")
    assert conn.execute("SELECT status FROM project WHERE id = 'PX-43'").fetchone()[0] == "completed"
    assert row_count(conn, "project") == 46
