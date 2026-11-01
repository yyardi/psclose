from decimal import Decimal

import pytest

from psclose.hours import attribute_timesheets, hours_by_item, unattributed_hours
from psclose.identity import resolve_timesheets


@pytest.fixture
def june_hours(history_ledger, policy):
    resolve_timesheets(history_ledger)
    attribute_timesheets(history_ledger, "2026-06", policy)
    return hours_by_item(history_ledger, "2026-06")


def test_history_split_projects_follow_the_item_tag(june_hours):
    assert june_hours["CI-PX-12A"].billable_cum == Decimal("340")
    assert june_hours["CI-PX-12B"].billable_cum == Decimal("85")
    assert june_hours["CI-PX-21A"].billable_cum == Decimal("170")
    assert june_hours["CI-PX-21B"].billable_cum == Decimal("75")
    assert june_hours["CI-PX-23A"].billable_cum == Decimal("155")
    assert june_hours["CI-PX-23A"].all_cum == Decimal("180")
    assert june_hours["CI-PX-23B"].billable_cum == Decimal("68")
    assert june_hours["CI-PX-23B"].all_cum == Decimal("80")


def test_alias_resolved_hours_count_and_unresolved_do_not(june_hours):
    assert june_hours["CI-PX-18"].billable_cum == Decimal("195")
    assert june_hours["CI-PX-20"].billable_cum == Decimal("150")
    assert june_hours["CI-PX-01"].billable_cum == Decimal("510")
    assert "CI-PX-35" not in june_hours


def test_july_attribution(july_ledger, policy):
    resolve_timesheets(july_ledger)
    attribute_timesheets(july_ledger, "2026-07", policy)
    july = hours_by_item(july_ledger, "2026-07")

    # Change-request rows carry the CR tag; the rest of PX-38 stays on the base item.
    assert july["CI-PX-38-CR"].billable_period == Decimal("8")
    assert july["CI-PX-38"].billable_period == Decimal("40")

    # PX-12B was fully released in June, so July hours all land on 12A.
    assert july["CI-PX-12A"].billable_period == Decimal("109")
    assert july["CI-PX-12B"].billable_period == Decimal("0")
    assert july["CI-PX-12A"].methods == {"single_open_item"}

    # PX-21: 40 hours split by remaining planned hours (130 vs 75).
    a, b = july["CI-PX-21A"].billable_period, july["CI-PX-21B"].billable_period
    assert a + b == Decimal("40")
    assert a.quantize(Decimal("0.01")) == Decimal("25.37")
    assert july["CI-PX-21A"].methods == {"allocated_remaining_planned_hours"}

    # PX-23: non-billable enablement hours split the same way as billable ones.
    assert july["CI-PX-23A"].all_period + july["CI-PX-23B"].all_period == Decimal("34")
    assert july["CI-PX-23A"].billable_period + july["CI-PX-23B"].billable_period == Decimal("26")

    assert july["CI-PX-43"].billable_cum == Decimal("35")
    assert july["CI-PX-29"].billable_cum == Decimal("47")
    assert july["CI-PX-18"].billable_cum == Decimal("195") + Decimal("29")

    # Only the subscription projects (no PS item) are left without an item in July.
    left_over = unattributed_hours(july_ledger, "2026-07")
    assert {r["project_id"] for r in left_over} == {"PX-35", "PX-36"}
    june_left_over = unattributed_hours(july_ledger, "2026-06")
    assert {r["project_name_as_reported"] for r in june_left_over if r["project_id"] is None} == {
        "Legacy Support Work"
    }


def test_attribution_is_incremental(july_ledger, policy):
    resolve_timesheets(july_ledger)
    first = attribute_timesheets(july_ledger, "2026-06", policy)
    second = attribute_timesheets(july_ledger, "2026-07", policy)
    # 4402 June rows less 1 unresolved and 6 on subscription projects with no PS item.
    assert sum(first.values()) == 4402 - 1 - 6
    assert sum(second.values()) == 768 - 8
    third = attribute_timesheets(july_ledger, "2026-07", policy)
    assert third == {}
