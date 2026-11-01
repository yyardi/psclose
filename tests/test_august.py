"""The brief asks for a close that keeps working in August. These tests run one, twice:
from the raw inputs with both increments, and from the July ledger the previous close left
behind. Both routes must agree."""

from decimal import Decimal

from psclose.ledger import assemble, last_closed_period
from psclose.schedule import close_through
from tests.conftest import BASE_DB, JULY_DB


def test_august_closes_from_raw_inputs(tmp_path, policy, august_increment):
    conn = assemble(BASE_DB, [JULY_DB, august_increment], tmp_path / "ledger.sqlite")
    july, august = close_through(conn, "2026-08", policy)
    assert (july.period, august.period) == ("2026-07", "2026-08")
    assert last_closed_period(conn) == "2026-08"
    items = august.by_item()
    assert len(items) == 48
    codes = {(e.code, e.contract_item_id or e.project_id or e.currency) for e in august.exceptions}

    # Acceptance in August releases PX-01 from the 95% cap.
    assert items["CI-PX-01"].outcome.recognized == Decimal("100000.00")
    assert ("ACCEPTANCE_RELEASE", "CI-PX-01") in codes

    # Only PX-14 was confirmed; the other three POC projects carry July's percent and get flagged.
    assert items["CI-PX-14"].outcome.recognized == Decimal("75000.00")
    assert items["CI-PX-13"].outcome.recognized == Decimal("67050.00")
    assert items["CI-PX-13"].ctx.hours.billable_period == Decimal("12")
    for item in ("CI-PX-13", "CI-PX-15", "CI-PX-16"):
        assert ("SNAPSHOT_MISSING", item) in codes
    assert ("SNAPSHOT_MISSING", "CI-PX-14") not in codes

    # Hours-based items keep accruing; the new deal continues; T&M still counts every hour.
    assert items["CI-PX-17"].outcome.recognized == Decimal("52800.00")  # (244 + 20) / 400 * 80000
    assert items["CI-PX-43"].outcome.recognized == Decimal("13400.00")  # (35 + 32) / 300 * 60000
    assert items["CI-PX-24"].outcome.recognized == Decimal("56200.00")  # 255 + 24 + 2 hours at 200

    # Items with no August hours are called out, except those already complete or terminated.
    assert ("NO_ACTIVITY", "CI-PX-03") in codes
    assert ("COMPLETED_CARRYFORWARD", "CI-PX-02") in codes
    assert ("TERMINATED_CARRYFORWARD", "CI-PX-27") in codes

    # The EUR rate arrived; CAD and GBP did not.
    assert ("FX_RATE_STALE", "EUR") not in codes
    assert ("FX_RATE_STALE", "CAD") in codes and ("FX_RATE_STALE", "GBP") in codes


def test_august_from_the_july_ledger_matches(tmp_path, policy, august_increment):
    conn = assemble(BASE_DB, [JULY_DB], tmp_path / "july.sqlite")
    close_through(conn, "2026-07", policy)
    conn.close()

    from_ledger = assemble(tmp_path / "july.sqlite", [august_increment], tmp_path / "aug_a.sqlite")
    (aug_a,) = close_through(from_ledger, "2026-08", policy)

    from_raw = assemble(BASE_DB, [JULY_DB, august_increment], tmp_path / "aug_b.sqlite")
    _, aug_b = close_through(from_raw, "2026-08", policy)

    def rows(result):
        return sorted((c.ctx.item_id, c.outcome.recognized, c.planned, c.status) for c in result.items)

    assert rows(aug_a) == rows(aug_b)
    assert sorted(e.code for e in aug_a.exceptions) == sorted(e.code for e in aug_b.exceptions)
