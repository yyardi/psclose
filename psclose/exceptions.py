"""Everything in a close that a controller should look at before posting.

An exception is a fact about one figure (or one row of source data) with a cause code, a
severity, the amount at stake, the ids that prove it, and the question it raises. The report
groups them by cause; the memo turns them into prose.

Severities: info (no decision needed, included so the walk is complete), review (a number
moved for a reason the controller should recognize), action (something is wrong or unknown
and the figure may change once answered).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any

from .config import Policy
from .ledger import fx_latest
from .model import ItemClose, dec, money
from .periods import period_end, period_start
from . import policy as methods

INFO, REVIEW, ACTION = "info", "review", "action"
SEVERITY_ORDER = {ACTION: 0, REVIEW: 1, INFO: 2}

CODES: dict[str, tuple[str, str]] = {
    "ACCEPTANCE_RELEASE": (REVIEW, "Acceptance confirmed; remaining contract value recognized"),
    "MILESTONE_RELEASE": (REVIEW, "Milestone confirmed; next tranche recognized"),
    "POC_SNAPSHOT_UPDATE": (REVIEW, "Delivery lead revised percent complete"),
    "SNAPSHOT_MISSING": (ACTION, "No percent-complete confirmation for the period"),
    "FIRST_RECOGNITION": (REVIEW, "Item became effective; first revenue recognized"),
    "NEW_ITEM": (REVIEW, "Contract item appears on the schedule for the first time"),
    "HOURS_ALLOCATED": (ACTION, "Hours split across items by rule, not by the timesheet"),
    "CAP_BINDING": (INFO, "Recognition held at the pre-acceptance cap"),
    "EAC_REVISED": (REVIEW, "Approved no-charge hours raised the estimate at completion"),
    "PAID_ADJUSTMENT_NOTED": (INFO, "Paid change request logged; base item estimate unchanged"),
    "HOURS_OVER_PLAN": (REVIEW, "Logged hours exceed the estimate at completion"),
    "TERMINATION_CREDIT": (REVIEW, "Contract terminated; recognized revenue reversed"),
    "TERMINATED_CARRYFORWARD": (INFO, "Terminated item carried with no movement"),
    "COMPLETED_CARRYFORWARD": (INFO, "Fully recognized item carried with no movement"),
    "NO_ACTIVITY": (REVIEW, "Active item with no hours in the period"),
    "PRE_EFFECTIVE_HOURS_COUNTED": (REVIEW, "Hours logged before the effective date count toward completion"),
    "NONBILLABLE_RECOGNIZED": (REVIEW, "Non-billable hours recognized at the standard rate"),
    "NEGATIVE_DELTA": (ACTION, "Cumulative recognized revenue fell without a termination"),
    "HISTORY_INCONSISTENCY": (REVIEW, "Prior period as posted differs from the rules as configured"),
    "POC_CONFIRMATION_CHECK": (INFO, "Delivery-lead confirmation compared with the computed position"),
    "UNMATCHED_HOURS_RESOLVED": (REVIEW, "Timesheets with no project link matched by name"),
    "UNRESOLVED_HOURS": (ACTION, "Timesheets that match no project; hours excluded"),
    "NON_PS_HOURS": (INFO, "Hours on items outside the PS schedule; excluded"),
    "UNAPPROVED_HOURS": (REVIEW, "Timesheets not approved; hours excluded"),
    "UNAPPLIED_RMA": (ACTION, "Return or credit memo not reflected in the schedule"),
    "ORPHAN_SALES_ORDER": (ACTION, "Approved sales order with no project and no contract item"),
    "SO_PROJECT_LINK_MISSING": (INFO, "Sales order linked to its project by alias only"),
    "FX_RATE_STALE": (ACTION, "No exchange rate for the period; prior rate used for USD views"),
    "PROJECT_MISSING": (ACTION, "Contract item refers to a project that is not in the ledger"),
}


@dataclass
class CloseException:
    period: str
    code: str
    project_id: str | None
    contract_item_id: str | None
    message: str
    amount_native: Decimal | None = None
    currency: str | None = None
    evidence: list[str] = field(default_factory=list)
    question: str | None = None

    @property
    def severity(self) -> str:
        return CODES[self.code][0]

    @property
    def title(self) -> str:
        return CODES[self.code][1]

    def as_row(self) -> tuple:
        return (
            self.period,
            self.code,
            self.severity,
            self.project_id,
            self.contract_item_id,
            float(self.amount_native) if self.amount_native is not None else None,
            self.currency,
            self.message,
            "; ".join(self.evidence),
            self.question,
        )

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity
        d["title"] = self.title
        d["amount_native"] = float(self.amount_native) if self.amount_native is not None else None
        d["evidence"] = "; ".join(self.evidence)
        return d


def _fmt(amount: Decimal | float | int, currency: str | None = None) -> str:
    text = f"{money(amount):,.2f}"
    return f"{text} {currency}" if currency else text


def _hours(value: Decimal) -> str:
    return f"{value.normalize():f}" if value == value.to_integral() else f"{value:.2f}"


def _rate(value: Decimal) -> str:
    return f"{value:.0f}" if value == value.to_integral() else f"{value}"


def _per_hour_value(close: ItemClose, policy: Policy) -> Decimal:
    """Recognized value of one more billable hour on this item under its method."""
    if close.method == methods.TM_HOURS:
        return policy.tm_rate
    if close.method == methods.HOURS_POC:
        eac = close.outcome.facts.get("eac_hours") or dec(close.ctx.item["planned_hours"])
        return close.ctx.contract / eac if eac else Decimal(0)
    return Decimal(0)


def item_checks(close: ItemClose, policy: Policy) -> list[CloseException]:
    ctx, out, facts = close.ctx, close.outcome, close.outcome.facts
    item, project = ctx.item_id, ctx.project_id
    cur = ctx.currency
    period = ctx.period
    found: list[CloseException] = []

    def add(code: str, message: str, amount: Decimal | None = None, evidence=(), question: str | None = None) -> None:
        found.append(CloseException(period, code, project, item, message, amount, cur, list(evidence), question))

    hours = ctx.hours
    prior = ctx.prior

    if prior.period is None:
        add(
            "NEW_ITEM",
            f"{item} ({ctx.item['description']}) is new this period: {_fmt(ctx.contract, cur)} contract, "
            f"{_hours(dec(ctx.item['planned_hours']))} planned hours, effective {ctx.item['effective_date']}, "
            f"method {methods.METHOD_LABELS[close.method]}.",
            out.recognized,
            [item, ctx.item["sales_order_id"]],
        )

    if ctx.terminated:
        if ctx.terminated_this_period:
            add(
                "TERMINATION_CREDIT",
                f"{ctx.project['display_name']} terminated {facts['termination_date']}; "
                f"{_fmt(abs(facts['credit_total']), cur)} previously recognized is reversed.",
                close.delta,
                facts["rma_ids"],
                None if facts["reversed_fully"] else "The RMA credit does not equal the recognized balance; confirm the amount to reverse.",
            )
        else:
            add("TERMINATED_CARRYFORWARD", f"{item} terminated {facts['termination_date']}; no movement.", Decimal(0), [])
        return found

    if prior.status == "open" and close.status != "open":
        add(
            "FIRST_RECOGNITION",
            f"{item} became effective {ctx.item['effective_date']}; first recognition "
            f"{_fmt(out.recognized, cur)} on {_hours(hours.billable_cum)} cumulative billable hours.",
            close.delta,
            [item],
        )
    if close.status != "open" and hours.pre_effective_cum > 0 and (prior.status == "open" or hours.pre_effective_period > 0):
        still_tagged = ""
        if hours.pre_effective_period > 0 and ctx.contract_live:
            still_tagged = (
                f" {_hours(hours.pre_effective_period)} of this period's hours are still tagged "
                f"'{policy.pre_effective_note}' although the item is live from {ctx.item['effective_date']}."
            )
        planned_hours = dec(ctx.item["planned_hours"])
        add(
            "PRE_EFFECTIVE_HOURS_COUNTED",
            f"{_hours(hours.pre_effective_cum)} hours on {item} were tagged as logged before the scope was live; "
            f"they count toward percent complete, as they did toward planned value in prior periods.{still_tagged}",
            money(hours.pre_effective_cum / planned_hours * ctx.contract) if planned_hours else None,
            [item],
            "Should hours logged before the effective date count toward completion, or be excluded?",
        )

    if close.status == "open":
        return found

    if close.delta < 0:
        add(
            "NEGATIVE_DELTA",
            f"Cumulative recognized on {item} fell from {_fmt(prior.recognized, cur)} to {_fmt(out.recognized, cur)}.",
            close.delta,
            [item],
            "A negative true-up needs a manual journal entry or a credit memo; which applies?",
        )

    alloc = {m for m in hours.methods if m.startswith("allocated_") or m == "single_open_item"}
    if alloc and len(ctx.siblings) > 1:
        others = [s["id"] for s in ctx.siblings if s["id"] != item]
        project_hours = sum((h.billable_period for h in ctx.sibling_hours.values()), Decimal(0))
        total_planned = sum((dec(s["planned_hours"]) for s in ctx.siblings), Decimal(0))
        alt_hours = project_hours * dec(ctx.item["planned_hours"]) / total_planned if total_planned else hours.billable_period
        swing = money((alt_hours - hours.billable_period) * _per_hour_value(close, policy))
        if "single_open_item" in alloc:
            why = f"because {', '.join(others)} is already fully recognized"
        else:
            why = "in proportion to the hours each item still has to deliver"
        ratio = ":".join(_hours(dec(s["planned_hours"])) for s in ctx.siblings)
        add(
            "HOURS_ALLOCATED",
            f"{_hours(hours.billable_period)} of {_hours(project_hours)} billable hours on {project} were placed on "
            f"{item} {why}; the {period} timesheets name the project but not the item. A plain split by planned "
            f"hours ({ratio}) would give {item} {_hours(alt_hours.quantize(Decimal('0.01')))} h and move its "
            f"recognized revenue by {_fmt(swing, cur)}.",
            close.delta,
            [item] + others,
            f"How should {project} hours be split between {' and '.join(sorted([item] + others))}?",
        )

    if close.method == methods.HOURS_POC:
        eac = facts["eac_hours"]
        if facts["accepted_event"] and prior.recognized < ctx.contract:
            add(
                "ACCEPTANCE_RELEASE",
                f"{ctx.project['display_name']}: acceptance confirmed {facts['accepted_on']}; "
                f"{item} moves from {_fmt(prior.recognized, cur)} to the full {_fmt(ctx.contract, cur)}.",
                close.delta,
                [facts["accepted_event"]],
            )
        elif facts["cap_binding"]:
            add(
                "CAP_BINDING",
                f"{item} is {facts['pct_complete'] * 100:.1f}% complete by hours "
                f"({_hours(hours.billable_cum)} of {_hours(eac)}); recognition held at "
                f"{policy.acceptance_cap * 100:.0f}% ({_fmt(facts['cap'], cur)}) pending acceptance.",
                facts["raw_recognized"] - facts["cap"],
                [item],
            )
        new_adj = [
            a["id"] for a in ctx.adjustments
            if a["cr_type"] in policy.eac_adjustment_types and period_start(period) <= (a["effective_date"] or "") <= period_end(period)
        ]
        if new_adj:
            base_hours = dec(ctx.item["planned_hours"])
            without = min(ctx.contract * hours.billable_cum / base_hours, facts["cap"]) if base_hours else out.recognized
            add(
                "EAC_REVISED",
                f"Approved no-charge hours on {project} ({', '.join(new_adj)}) raise the estimate at completion "
                f"to {_hours(eac)} hours; {item} recognizes {_fmt(out.recognized, cur)} instead of "
                f"{_fmt(without, cur)}.",
                out.recognized - money(without),
                new_adj,
            )
        paid_adj = [
            a["id"] for a in ctx.adjustments
            if a["cr_type"] not in policy.eac_adjustment_types and period_start(period) <= (a["effective_date"] or "") <= period_end(period)
        ]
        if paid_adj and prior.period is not None:
            add(
                "PAID_ADJUSTMENT_NOTED",
                f"Paid change request on {project} ({', '.join(paid_adj)}) is priced on its own contract item; "
                f"the estimate at completion for {item} stays at {_hours(eac)} hours.",
                None,
                paid_adj,
            )
        if hours.billable_cum > eac and not facts["accepted_event"]:
            add(
                "HOURS_OVER_PLAN",
                f"{item} has {_hours(hours.billable_cum)} billable hours against an estimate of {_hours(eac)}; "
                f"planned value {_fmt(close.planned, cur)} now exceeds the {_fmt(ctx.contract, cur)} contract.",
                close.planned - ctx.contract,
                [item],
                f"Is a change order or a revised estimate expected on {item} ({_hours(hours.billable_cum)} h against {_hours(eac)})?",
            )

    elif close.method == methods.MILESTONE:
        if facts["released_this_period"]:
            add(
                "MILESTONE_RELEASE",
                f"{ctx.project['display_name']}: milestone confirmed; {item} releases tranche "
                f"{facts['steps_recognized']} of {facts['steps_total']}, {_fmt(close.delta, cur)}.",
                close.delta,
                facts["released_this_period"],
            )

    elif close.method == methods.POC_SNAPSHOT:
        if facts["snapshot_missing"]:
            add(
                "SNAPSHOT_MISSING",
                f"No delivery-lead percent-complete confirmation for {project} in {period}; "
                f"carried {facts['poc_pct']}% from {facts['carried_from']}.",
                Decimal(0),
                [item],
                f"Please confirm percent complete for {project} as of {period_end(period)}.",
            )
        elif facts["prior_poc_pct"] is not None and facts["poc_pct"] != facts["prior_poc_pct"]:
            add(
                "POC_SNAPSHOT_UPDATE",
                f"{ctx.project['display_name']}: delivery lead confirms {facts['poc_pct']}% complete "
                f"(was {facts['prior_poc_pct']}%); {item} recognizes {_fmt(close.delta, cur)} this period.",
                close.delta,
                [item],
            )

    elif close.method == methods.TM_HOURS and facts["nonbillable_period"] > 0:
        add(
            "NONBILLABLE_RECOGNIZED",
            f"{_hours(facts['nonbillable_period'])} non-billable hours on {item} were recognized at "
            f"{_rate(policy.tm_rate)}/h ({_fmt(facts['nonbillable_period'] * policy.tm_rate, cur)}), "
            f"matching how prior periods were posted.",
            money(facts["nonbillable_period"] * policy.tm_rate),
            [item],
            "Should non-billable enablement hours on T&M engagements keep being recognized as revenue?",
        )

    if hours.all_period == 0 and prior.period is not None:
        if out.recognized >= ctx.contract:
            add("COMPLETED_CARRYFORWARD", f"{item} is fully recognized; no hours in {period}.", Decimal(0), [item])
        else:
            add(
                "NO_ACTIVITY",
                f"{item} is active with no hours logged in {period}; cumulative stays at {_fmt(out.recognized, cur)}.",
                Decimal(0),
                [item],
                f"Is work on {project} paused, finished, or are timesheets missing?",
            )
    return found


def ledger_checks(
    conn: sqlite3.Connection,
    period: str,
    policy: Policy,
    closes: list[ItemClose],
) -> list[CloseException]:
    found: list[CloseException] = []
    start, end = period_start(period), period_end(period)

    def add(code, project, item, message, amount=None, currency=None, evidence=(), question=None):
        found.append(CloseException(period, code, project, item, message, amount, currency, list(evidence), question))

    rows = conn.execute(
        """
        SELECT t.id, t.project_name_as_reported AS name, t.hours, t.notes, t.approval_status,
               r.project_id, r.method, r.matched_name,
               EXISTS (SELECT 1 FROM timesheet_attribution a WHERE a.timesheet_id = t.id) AS attributed
        FROM timesheet_entry t LEFT JOIN timesheet_resolution r ON r.timesheet_id = t.id
        WHERE t.entry_date BETWEEN ? AND ?
        """,
        (start, end),
    ).fetchall()

    by_key: dict[tuple, list] = {}
    for r in rows:
        if r["project_id"] is None:
            by_key.setdefault(("UNRESOLVED_HOURS", r["name"]), []).append(r)
        elif r["approval_status"] != "Approved":
            by_key.setdefault(("UNAPPROVED_HOURS", r["project_id"]), []).append(r)
        elif not r["attributed"]:
            by_key.setdefault(("NON_PS_HOURS", r["project_id"]), []).append(r)
        elif r["method"] != "source":
            by_key.setdefault(("UNMATCHED_HOURS_RESOLVED", r["project_id"]), []).append(r)

    for (code, key), group in sorted(by_key.items()):
        total = sum((dec(g["hours"]) for g in group), Decimal(0))
        ids = [g["id"] for g in group]
        notes = sorted({g["notes"] for g in group if g["notes"]})
        if code == "UNRESOLVED_HOURS":
            hint = ""
            if any("PX-" in g["id"] for g in group):
                hint = f" The row ids mention {sorted({g['id'].split('-')[2] for g in group})[0]}, which may be the intended project."
            add(
                code, None, None,
                f"{_hours(total)} hours reported against '{key}' match no project name or alias "
                f"({'; '.join(notes)}).{hint} Excluded from every figure.",
                None, None, ids,
                f"Which project should '{key}' hours belong to?",
            )
        elif code == "UNAPPROVED_HOURS":
            add(code, key, None, f"{_hours(total)} hours on {key} are not approved and were excluded.", None, None, ids,
                f"Will the unapproved {key} timesheets be approved before close?")
        elif code == "NON_PS_HOURS":
            add(code, key, None, f"{_hours(total)} hours on {key} ({'; '.join(notes) or 'no PS contract item'}) sit outside the PS schedule.", None, None, ids)
        else:
            matched = sorted({g["matched_name"] for g in group if g["matched_name"]})
            add(
                code, key, None,
                f"{_hours(total)} hours reported as '{', '.join(matched)}' carry no project id and were linked to "
                f"{key} by alias ({'; '.join(notes)}). Included in {key}'s hours, as in prior periods.",
                None, None, ids,
                f"Can the OpenAir link for {key} be fixed so these rows arrive with a project id?",
            )

    from .identity import sales_order_links  # local import keeps module graph simple

    for link in sales_order_links(conn):
        if link.project_id is None:
            add(
                "ORPHAN_SALES_ORDER", None, None,
                f"{link.sales_order_id} ({link.tran_id}) for customer {link.customer_id} is approved for "
                f"{_fmt(link.total_native, link.currency)} with no project and no contract item; nothing is scheduled for it.",
                dec(link.total_native), link.currency, [link.sales_order_id],
                f"Is {link.sales_order_id} a real order that needs a contract item, or a duplicate to void?",
            )
        else:
            add(
                "SO_PROJECT_LINK_MISSING", link.project_id, None,
                f"{link.sales_order_id} has no project id; linked to {link.project_id} through its NetSuite hint.",
                None, link.currency, [link.sales_order_id],
            )

    applied = {
        r["source_reference"]
        for r in conn.execute("SELECT source_reference FROM accounting_posting WHERE posting_kind = 'credit'")
    }
    applied |= {ref for c in closes if c.posting and c.posting["posting_kind"] == "credit" for ref in [c.posting["source_reference"]]}
    for rma in conn.execute("SELECT * FROM rma_event WHERE event_date <= ? AND status = 'posted' ORDER BY event_date", (end,)):
        if rma["id"] in applied:
            continue
        try:
            details = json.loads(rma["raw_details_json"] or "{}")
        except json.JSONDecodeError:
            details = {}
        detail_text = "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in details.items()) or "no details"
        add(
            "UNAPPLIED_RMA", rma["project_id"], None,
            f"{rma['id']} ({rma['return_number']}, {rma['event_date']}, '{rma['reason']}') for "
            f"{_fmt(rma['amount_native'], rma['currency'])} has no matching credit in the schedule ({detail_text}).",
            dec(rma["amount_native"]), rma["currency"], [rma["id"], rma["original_sales_order_id"] or ""],
            f"Should {rma['id']} reduce recognized revenue on {rma['project_id']}, and against which item?",
        )

    for currency in sorted({c.ctx.currency for c in closes} - {"USD"}):
        rate = fx_latest(conn, currency, end)
        if rate is None:
            add("FX_RATE_STALE", None, None, f"No {currency} rate in fx_rate at all; USD views omit {currency}.", None, currency, [])
        elif rate[1] < start:
            add(
                "FX_RATE_STALE", None, None,
                f"No {currency} rate for {period}; USD views use {rate[0]} from {rate[1]}.",
                None, currency, [],
                f"Please provide the {currency}/USD rate for {end}.",
            )

    by_project: dict[str, list[ItemClose]] = {}
    for c in closes:
        by_project.setdefault(c.ctx.project_id, []).append(c)
    snaps = conn.execute(
        "SELECT * FROM ops_poc_snapshot WHERE as_of_period = ? AND source = ?", (period, policy.poc_source)
    ).fetchall()
    for snap in snaps:
        group = by_project.get(snap["project_id"], [])
        if not group or any(c.method == methods.POC_SNAPSHOT for c in group):
            continue
        contract = sum((c.ctx.contract for c in group), Decimal(0))
        recognized = sum((c.outcome.recognized for c in group), Decimal(0))
        computed = (recognized / contract * 100) if contract else Decimal(0)
        gap = abs(computed - dec(snap["poc_pct"]))
        add(
            "POC_CONFIRMATION_CHECK", snap["project_id"], None,
            f"Delivery lead confirms {snap['poc_pct']}% for {snap['project_id']}; the schedule stands at "
            f"{computed:.1f}% ({_fmt(recognized, group[0].ctx.currency)} of {_fmt(contract, group[0].ctx.currency)})"
            + (". Consistent." if gap < Decimal("0.5") else f". Gap of {gap:.1f} points."),
            None, group[0].ctx.currency, [snap["id"]],
            None if gap < Decimal("0.5") else f"Which is right for {snap['project_id']}: the confirmed percent or the computed position?",
        )
    return found


def sort_key(e: CloseException) -> tuple:
    return (SEVERITY_ORDER[e.severity], e.code, e.project_id or "", e.contract_item_id or "")
