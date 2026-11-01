from decimal import Decimal

import pytest

from psclose.ledger import last_closed_period, row_count
from psclose.schedule import close_through, compute_period


@pytest.fixture
def july(july_ledger, policy):
    results = close_through(july_ledger, "2026-07", policy)
    assert [r.period for r in results] == ["2026-07"]
    return results[0]


def test_one_row_per_contract_item(july, july_ledger):
    items = july.by_item()
    assert len(items) == 48
    assert set(items) >= {"CI-PX-43", "CI-PX-38-CR", "CI-PX-27", "CI-PX-07"}
    assert "CI-PX-35" not in items and "CI-PX-36" not in items
    assert july_ledger.execute("SELECT COUNT(*) FROM revenue_schedule WHERE period = '2026-07'").fetchone()[0] == 48
    assert last_closed_period(july_ledger) == "2026-07"
    assert not [c for c in july.items if c.status == "open"]


def test_july_movements(july):
    items = july.by_item()

    def rec(item_id):
        return items[item_id].outcome.recognized

    # Acceptance releases the 95% cap on PX-02; its peers stay capped with zero movement.
    assert rec("CI-PX-02") == Decimal("88000.00") and items["CI-PX-02"].delta == Decimal("4400.00")
    for capped in ("CI-PX-01", "CI-PX-03", "CI-PX-04", "CI-PX-05", "CI-PX-06"):
        assert items[capped].delta == 0 and items[capped].status == "held"
    assert items["CI-PX-01"].planned == Decimal("107800.00")

    # Milestones confirmed 2026-07-11 release the second tranche.
    assert rec("CI-PX-09") == Decimal("80000.00") and items["CI-PX-09"].delta == Decimal("40000.00")
    assert rec("CI-PX-10") == Decimal("60000.00")
    assert items["CI-PX-09"].posting["memo"] == "release per milestone completion"

    # Delivery-lead percent complete for July.
    assert rec("CI-PX-13") == Decimal("67050.00")
    assert rec("CI-PX-14") == Decimal("68000.00")
    assert rec("CI-PX-15") == Decimal("56800.00")
    assert rec("CI-PX-16") == Decimal("75600.00")

    # First recognition for the two items that went live on 1 July, pre-effective hours included.
    assert rec("CI-PX-29") == Decimal("9400.00") and items["CI-PX-29"].status == "posted"
    assert rec("CI-PX-30") == Decimal("7400.00")

    # New deal and the paid change request on PX-38.
    assert rec("CI-PX-43") == Decimal("7000.00")
    assert rec("CI-PX-38-CR") == Decimal("1600.00")
    assert rec("CI-PX-38") == Decimal("59000.00")

    # PX-12 hours all land on 12A; EAC revision on PX-40 still in force; T&M counts every hour.
    assert rec("CI-PX-12A") == Decimal("89800.00")
    assert rec("CI-PX-40") == Decimal("44917.89")
    assert rec("CI-PX-24") == Decimal("51000.00")

    # Carry-forwards.
    assert rec("CI-PX-27") == 0 and items["CI-PX-27"].posting is None
    assert items["CI-PX-27"].schedule["source_reference"] == "NA-CI-PX-27-2026-07"
    assert rec("CI-PX-07") == Decimal("90000.00") and items["CI-PX-07"].posting["amount_native"] == 0


def test_exception_codes_cover_the_movements(july):
    codes = {(e.code, e.contract_item_id or e.project_id) for e in july.exceptions}
    assert ("ACCEPTANCE_RELEASE", "CI-PX-02") in codes
    assert ("MILESTONE_RELEASE", "CI-PX-09") in codes
    assert ("POC_SNAPSHOT_UPDATE", "CI-PX-16") in codes
    assert ("FIRST_RECOGNITION", "CI-PX-29") in codes
    assert ("PRE_EFFECTIVE_HOURS_COUNTED", "CI-PX-29") in codes
    assert ("NEW_ITEM", "CI-PX-43") in codes
    assert ("NEW_ITEM", "CI-PX-38-CR") in codes
    assert ("HOURS_ALLOCATED", "CI-PX-21A") in codes
    assert ("HOURS_ALLOCATED", "CI-PX-12A") in codes
    assert ("CAP_BINDING", "CI-PX-01") in codes
    assert ("HOURS_OVER_PLAN", "CI-PX-01") in codes
    assert ("NONBILLABLE_RECOGNIZED", "CI-PX-24") in codes
    assert ("UNMATCHED_HOURS_RESOLVED", "PX-18") in codes
    assert ("UNAPPLIED_RMA", "PX-20") in codes
    assert ("ORPHAN_SALES_ORDER", None) in codes
    assert ("FX_RATE_STALE", None) in codes
    assert ("HISTORY_INCONSISTENCY", "CI-PX-05") in codes
    assert ("TERMINATED_CARRYFORWARD", "CI-PX-27") in codes
    assert ("COMPLETED_CARRYFORWARD", "CI-PX-07") in codes
    assert ("PAID_ADJUSTMENT_NOTED", "CI-PX-38") in codes


def test_close_is_idempotent_and_refuses_to_reclose(july_ledger, policy, july):
    before = july_ledger.execute(
        "SELECT id, recognized_amount_native, planned_amount_native, status FROM revenue_schedule WHERE period='2026-07' ORDER BY id"
    ).fetchall()
    again = compute_period(july_ledger, "2026-07", policy)
    assert [(c.schedule["id"], float(c.outcome.recognized), float(c.planned), c.status) for c in sorted(again.items, key=lambda c: c.ctx.item_id)] == [tuple(r) for r in before]
    with pytest.raises(RuntimeError):
        close_through(july_ledger, "2026-07", policy)
    assert row_count(july_ledger, "close_exception") == len(july.exceptions)
