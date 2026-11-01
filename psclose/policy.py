"""Decide how each contract item earns revenue, from what the data says about it."""

from __future__ import annotations

from .model import ItemContext
from .periods import next_period

EXCLUDED = "excluded"
TM_HOURS = "tm_hours"
MILESTONE = "milestone"
POC_SNAPSHOT = "poc_snapshot"
HOURS_POC = "hours_poc"

METHOD_LABELS = {
    EXCLUDED: "excluded from the PS schedule",
    TM_HOURS: "time and materials, hours at the standard rate",
    MILESTONE: "fixed fee, milestone tranches",
    POC_SNAPSHOT: "fixed fee, delivery-lead percent complete",
    HOURS_POC: "fixed fee, hours against estimate at completion",
}


def _contiguous(periods: list[str]) -> bool:
    return all(next_period(a) == b for a, b in zip(periods, periods[1:]))


def infer_method(ctx: ItemContext) -> tuple[str, str]:
    """Return (method, reason). Order matters: the first matching signal wins."""
    if not ctx.item["is_ps"]:
        return EXCLUDED, "contract item has is_ps = 0"
    if ctx.project["billing_type"] == "Time & Materials":
        return TM_HOURS, "project billing_type is Time & Materials"
    if ctx.item["service"] == "Fixed Fee Delivery":
        return MILESTONE, "contract item service is Fixed Fee Delivery"
    series = sorted(ctx.snapshots)
    if series and ctx.first_period in series and _contiguous(series):
        return POC_SNAPSHOT, f"delivery-lead POC confirmed every period since {series[0]}"
    return HOURS_POC, "fixed fee with no milestone schedule or POC series"
