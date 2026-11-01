"""The recognition rules, one function per method. Each returns the cumulative recognized
amount for the item at the end of the period, the memo the posting should carry, and the
facts the exception report needs to explain the number."""

from __future__ import annotations

from decimal import Decimal

from .config import Policy
from .model import ItemContext, Outcome, dec, money
from . import policy as methods

ZERO = Decimal("0")

MEMO_CLOSE_EXPORT = "per close export"
MEMO_PM_SNAPSHOT = "per PM tracker snapshot"
MEMO_TRANCHE_1 = "tranche 1 per delivery schedule"
MEMO_MILESTONE_PENDING = "milestone pending"
MEMO_MILESTONE_RELEASE = "release per milestone completion"
MEMO_TERMINATION_CREDIT = "credit issued per contract termination"


def eac_hours(ctx: ItemContext, policy: Policy) -> tuple[Decimal, list[str]]:
    """Planned hours plus the project's approved no-charge overruns, shared across the
    project's PS items by planned hours when there is more than one."""
    planned = dec(ctx.item["planned_hours"])
    total_planned = sum(dec(i["planned_hours"]) for i in ctx.siblings) or planned
    share = planned / total_planned if total_planned else Decimal(1)
    extra = ZERO
    refs: list[str] = []
    for adj in ctx.adjustments:
        if adj["cr_type"] in policy.eac_adjustment_types and (adj["effective_date"] or "") <= ctx.period_end:
            extra += dec(adj["delta_planned_hours"]) * share
            refs.append(adj["id"])
    return planned + extra, refs


def _acceptance(ctx: ItemContext, policy: Policy):
    events = ctx.confirmed_events(policy.acceptance_events)
    return min(events, key=lambda e: e["event_date"]) if events else None


def hours_poc(ctx: ItemContext, policy: Policy) -> Outcome:
    eac, adj_refs = eac_hours(ctx, policy)
    pct = (ctx.hours.billable_cum / eac) if eac > 0 else ZERO
    raw = ctx.contract * pct
    cap = ctx.contract * policy.acceptance_cap
    accepted = _acceptance(ctx, policy)
    if accepted:
        recognized = ctx.contract
    else:
        recognized = min(raw, cap)
    return Outcome(
        recognized=money(recognized),
        memo=MEMO_CLOSE_EXPORT,
        facts={
            "pct_complete": pct,
            "eac_hours": eac,
            "eac_adjustments": adj_refs,
            "raw_recognized": money(raw),
            "cap": money(cap),
            "cap_binding": accepted is None and raw > cap,
            "accepted_event": accepted["id"] if accepted else None,
            "accepted_on": accepted["event_date"] if accepted else None,
        },
    )


def milestone(ctx: ItemContext, policy: Policy) -> Outcome:
    tranches = policy.milestone_tranches
    releases = sorted(ctx.confirmed_events(policy.milestone_events), key=lambda e: e["event_date"])
    steps = min(1 + len(releases), len(tranches))
    recognized = money(ctx.contract * sum(tranches[:steps]))
    released_now = [e for e in releases if e["event_date"] >= f"{ctx.period}-01"]
    if ctx.prior.recognized == 0:
        memo = MEMO_TRANCHE_1
    elif recognized > ctx.prior.recognized:
        memo = MEMO_MILESTONE_RELEASE
    else:
        memo = MEMO_MILESTONE_PENDING
    return Outcome(
        recognized=recognized,
        memo=memo,
        facts={
            "steps_recognized": steps,
            "steps_total": len(tranches),
            "release_events": [e["id"] for e in releases],
            "released_this_period": [e["id"] for e in released_now] if recognized > ctx.prior.recognized else [],
            "tranche_1_amount": money(ctx.contract * tranches[0]),
        },
    )


def poc_snapshot(ctx: ItemContext, policy: Policy) -> Outcome:
    pct = ctx.snapshots.get(ctx.period)
    carried_from = None
    if pct is None:
        earlier = [p for p in ctx.snapshots if p < ctx.period]
        carried_from = max(earlier) if earlier else None
        pct = ctx.snapshots[carried_from] if carried_from else ZERO
    accepted = _acceptance(ctx, policy)
    recognized = ctx.contract if accepted else ctx.contract * pct / Decimal(100)
    prior_pct = None
    earlier = [p for p in ctx.snapshots if p < ctx.period]
    if earlier:
        prior_pct = ctx.snapshots[max(earlier)]
    return Outcome(
        recognized=money(recognized),
        memo=MEMO_PM_SNAPSHOT,
        facts={
            "poc_pct": pct,
            "prior_poc_pct": prior_pct,
            "snapshot_missing": carried_from is not None or (ctx.period not in ctx.snapshots),
            "carried_from": carried_from,
            "accepted_event": accepted["id"] if accepted else None,
        },
    )


def tm_hours(ctx: ItemContext, policy: Policy) -> Outcome:
    hours = ctx.hours.all_cum if policy.tm_count_nonbillable else ctx.hours.billable_cum
    nonbillable = ctx.hours.all_cum - ctx.hours.billable_cum
    return Outcome(
        recognized=money(hours * policy.tm_rate),
        memo=MEMO_CLOSE_EXPORT,
        facts={
            "hours_recognized": hours,
            "nonbillable_cum": nonbillable,
            "nonbillable_period": ctx.hours.all_period - ctx.hours.billable_period,
            "nonbillable_value": money(nonbillable * policy.tm_rate),
        },
    )


def terminated(ctx: ItemContext, policy: Policy) -> Outcome:
    """Full reversal in the termination period, nothing afterwards."""
    if ctx.terminated_this_period:
        credits = [r for r in ctx.rmas if "terminat" in (r["reason"] or "").lower()]
        credit_total = sum((dec(r["amount_native"]) for r in credits), ZERO)
        recognized = max(ctx.prior.recognized + credit_total, ZERO)
        return Outcome(
            recognized=money(recognized),
            memo=MEMO_TERMINATION_CREDIT,
            facts={
                "rma_ids": [r["id"] for r in credits],
                "credit_total": money(credit_total),
                "reversed_fully": recognized == 0,
                "termination_date": ctx.termination_date,
            },
        )
    return Outcome(recognized=ctx.prior.recognized, memo=None, facts={"termination_date": ctx.termination_date})


RULES = {
    methods.HOURS_POC: hours_poc,
    methods.MILESTONE: milestone,
    methods.POC_SNAPSHOT: poc_snapshot,
    methods.TM_HOURS: tm_hours,
}


def recognize(method: str, ctx: ItemContext, policy: Policy) -> Outcome:
    if ctx.terminated:
        return terminated(ctx, policy)
    if not ctx.is_effective:
        return Outcome(recognized=ZERO, memo=None, facts={"pre_effective": True})
    return RULES[method](ctx, policy)


def planned_amount(method: str, ctx: ItemContext, policy: Policy) -> Decimal:
    if ctx.terminated:
        return ctx.prior.planned
    planned = ctx.hours.billable_cum * policy.planned_rate
    if method == methods.MILESTONE and ctx.is_effective:
        planned = max(planned, ctx.contract * policy.milestone_tranches[0])
    return money(planned)


def status_for(ctx: ItemContext, recognized: Decimal, planned: Decimal) -> str:
    if not ctx.is_effective:
        return "open"
    if recognized < planned:
        return "held"
    return "posted"
