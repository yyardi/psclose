"""Close one period: build the context for every contract item, apply its rule, and turn
the result into revenue_schedule and accounting_posting rows plus the exceptions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from decimal import Decimal

from .config import Policy
from .exceptions import CloseException, item_checks, ledger_checks, sort_key
from .hours import ItemHours, attribute_timesheets, hours_by_item
from .identity import resolve_timesheets
from .ledger import last_closed_period
from .model import ItemClose, ItemContext, PriorState, dec, money
from .periods import next_period, period_end, period_range, prev_period
from .policy import EXCLUDED, infer_method
from .recognize import planned_amount, recognize, status_for

ZERO = Decimal("0")


@dataclass
class PeriodResult:
    period: str
    items: list[ItemClose]
    exceptions: list[CloseException]
    excluded: list[tuple[str, str]] = field(default_factory=list)
    prior_deltas: dict[str, Decimal] = field(default_factory=dict)

    def by_item(self) -> dict[str, ItemClose]:
        return {c.ctx.item_id: c for c in self.items}


def _group(rows: list[sqlite3.Row], key: str) -> dict[str, list[sqlite3.Row]]:
    out: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        out.setdefault(r[key], []).append(r)
    return out


def _prior_states(conn: sqlite3.Connection, period: str) -> dict[str, PriorState]:
    rows = conn.execute(
        """
        SELECT contract_item_id, period, planned_amount_native, recognized_amount_native, status
        FROM revenue_schedule WHERE period < ? ORDER BY contract_item_id, period
        """,
        (period,),
    )
    out: dict[str, PriorState] = {}
    for r in rows:  # ordered by period, so the last row per item wins
        out[r["contract_item_id"]] = PriorState(
            r["period"], dec(r["recognized_amount_native"]), dec(r["planned_amount_native"]), r["status"]
        )
    return out


def _prior_deltas(conn: sqlite3.Connection, period: str) -> dict[str, Decimal]:
    rows = conn.execute(
        "SELECT contract_item_id, SUM(amount_native) AS amt FROM accounting_posting "
        "WHERE posting_period = ? GROUP BY contract_item_id",
        (prev_period(period),),
    )
    return {r["contract_item_id"]: dec(r["amt"]) for r in rows}


def build_contexts(conn: sqlite3.Connection, period: str, policy: Policy) -> tuple[list[ItemContext], list[CloseException]]:
    end = period_end(period)
    projects = {r["id"]: r for r in conn.execute("SELECT * FROM project")}
    items = conn.execute("SELECT * FROM contract_item ORDER BY id").fetchall()
    siblings = _group([i for i in items if i["is_ps"]], "project_id")
    events = _group(conn.execute(
        "SELECT * FROM project_event WHERE event_date <= ? ORDER BY event_date, id", (end,)).fetchall(), "project_id")
    adjustments = _group(conn.execute(
        "SELECT * FROM project_hours_adjustment WHERE COALESCE(effective_date, '') <= ? ORDER BY effective_date, id",
        (end,)).fetchall(), "project_id")
    rmas = _group(conn.execute(
        "SELECT * FROM rma_event WHERE event_date <= ? AND status = 'posted' ORDER BY event_date", (end,)).fetchall(), "project_id")
    snapshots: dict[str, dict[str, Decimal]] = {}
    for r in conn.execute(
        "SELECT project_id, as_of_period, poc_pct FROM ops_poc_snapshot WHERE source = ? AND as_of_period <= ?",
        (policy.poc_source, period),
    ):
        snapshots.setdefault(r["project_id"], {})[r["as_of_period"]] = dec(r["poc_pct"])
    hours = hours_by_item(conn, period, policy.pre_effective_note)
    priors = _prior_states(conn, period)

    contexts: list[ItemContext] = []
    problems: list[CloseException] = []
    for item in items:
        project = projects.get(item["project_id"])
        if project is None:
            problems.append(CloseException(
                period, "PROJECT_MISSING", item["project_id"], item["id"],
                f"{item['id']} refers to project {item['project_id']}, which is not in the ledger; skipped.",
                dec(item["contract_amount_native"]), item["currency"], [item["id"]],
                f"Which project does {item['id']} belong to?",
            ))
            continue
        contexts.append(ItemContext(
            period=period,
            item=item,
            project=project,
            hours=hours.get(item["id"], ItemHours()),
            events=events.get(project["id"], []),
            adjustments=adjustments.get(project["id"], []),
            snapshots=snapshots.get(project["id"], {}),
            rmas=rmas.get(project["id"], []),
            prior=priors.get(item["id"], PriorState(None, ZERO, ZERO, None)),
            siblings=siblings.get(project["id"], [item]),
            sibling_hours={s["id"]: hours.get(s["id"], ItemHours()) for s in siblings.get(project["id"], [item])},
        ))
    return contexts, problems


def _close_item(ctx: ItemContext, policy: Policy) -> ItemClose | None:
    method, reason = infer_method(ctx)
    if method == EXCLUDED:
        return None
    outcome = recognize(method, ctx, policy)
    planned = planned_amount(method, ctx, policy)
    status = status_for(ctx, outcome.recognized, planned)
    delta = outcome.recognized - ctx.prior.recognized
    end = ctx.period_end
    item_id, period = ctx.item_id, ctx.period

    posting = None
    source_ref = f"RPPR-{item_id}-{period}"
    if status == "open" or (ctx.terminated and not ctx.terminated_this_period):
        source_ref = f"NA-{item_id}-{period}"
    elif ctx.terminated_this_period:
        source_ref = outcome.facts["rma_ids"][0] if outcome.facts["rma_ids"] else f"RMA-{ctx.project_id}"
        posting = {
            "id": f"CREDIT-{item_id}",
            "contract_item_id": item_id,
            "posting_period": period,
            "posting_date": end,
            "posting_kind": "credit",
            "amount_native": delta,
            "currency": ctx.currency,
            "accounting_book": 1,
            "status": "posted",
            "source_reference": source_ref,
            "memo": outcome.memo,
        }
    else:
        posting = {
            "id": f"ACT-{item_id}-{period}",
            "contract_item_id": item_id,
            "posting_period": period,
            "posting_date": end,
            "posting_kind": "actual",
            "amount_native": delta,
            "currency": ctx.currency,
            "accounting_book": 1,
            "status": "posted",
            "source_reference": source_ref,
            "memo": outcome.memo,
        }

    schedule = {
        "id": f"SCH-{item_id}-{period}",
        "contract_item_id": item_id,
        "period": period,
        "planned_amount_native": planned,
        "recognized_amount_native": outcome.recognized,
        "currency": ctx.currency,
        "status": status,
        "last_updated": end,
        "source_reference": source_ref,
    }
    return ItemClose(ctx, method, reason, outcome, planned, status, delta, posting, schedule)


def compute_period(conn: sqlite3.Connection, period: str, policy: Policy, *, check_prior: bool = True) -> PeriodResult:
    """Everything the close produces for one period, without writing any of it."""
    attribute_timesheets(conn, period, policy)
    contexts, exceptions = build_contexts(conn, period, policy)
    closes: list[ItemClose] = []
    excluded: list[tuple[str, str]] = []
    for ctx in contexts:
        if ctx.first_period > period:
            continue
        close = _close_item(ctx, policy)
        if close is None:
            excluded.append((ctx.item_id, infer_method(ctx)[1]))
            continue
        closes.append(close)
        exceptions.extend(item_checks(close, policy))
    exceptions.extend(ledger_checks(conn, period, policy, closes))
    if check_prior:
        exceptions.extend(prior_consistency(conn, period, policy))
    exceptions.sort(key=sort_key)
    return PeriodResult(period, closes, exceptions, excluded, _prior_deltas(conn, period))


def prior_consistency(conn: sqlite3.Connection, period: str, policy: Policy) -> list[CloseException]:
    """Recompute the previous period with the current rules and report where the posted
    figures differ. These are not corrected; the controller decides."""
    prior = prev_period(period)
    stored = {
        r["contract_item_id"]: r
        for r in conn.execute("SELECT * FROM revenue_schedule WHERE period = ?", (prior,))
    }
    if not stored:
        return []
    recomputed = compute_period(conn, prior, policy, check_prior=False)
    found: list[CloseException] = []
    for close in recomputed.items:
        row = stored.get(close.ctx.item_id)
        if row is None:
            continue
        posted = dec(row["recognized_amount_native"])
        if posted == close.outcome.recognized:
            continue
        found.append(CloseException(
            period, "HISTORY_INCONSISTENCY", close.ctx.project_id, close.ctx.item_id,
            f"{prior} was posted at {money(posted):,.2f} {close.ctx.currency} for {close.ctx.item_id}; the rules as "
            f"configured give {close.outcome.recognized:,.2f}. Left as posted; the current period is computed "
            f"cumulatively so the difference does not compound unless the cause persists.",
            close.outcome.recognized - posted, close.ctx.currency, [row["id"]],
            f"Was {close.ctx.item_id} in {prior} meant to follow the standard rule, or was the posted figure a deliberate override?",
        ))
    return found


def write_period(conn: sqlite3.Connection, result: PeriodResult) -> None:
    p = result.period
    conn.execute("DELETE FROM revenue_schedule WHERE period = ?", (p,))
    conn.execute("DELETE FROM accounting_posting WHERE posting_period = ?", (p,))
    conn.execute("DELETE FROM close_exception WHERE period = ?", (p,))
    conn.execute("DELETE FROM item_policy WHERE period = ?", (p,))
    for close in result.items:
        s = close.schedule
        conn.execute(
            "INSERT INTO revenue_schedule VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (s["id"], s["contract_item_id"], s["period"], float(s["planned_amount_native"]),
             float(s["recognized_amount_native"]), s["currency"], s["status"], s["last_updated"], s["source_reference"]),
        )
        if close.posting:
            a = close.posting
            conn.execute(
                "INSERT INTO accounting_posting VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (a["id"], a["contract_item_id"], a["posting_period"], a["posting_date"], a["posting_kind"],
                 float(a["amount_native"]), a["currency"], a["accounting_book"], a["status"], a["source_reference"], a["memo"]),
            )
        conn.execute("INSERT INTO item_policy VALUES (?, ?, ?, ?)", (close.ctx.item_id, p, close.method, close.reason))
    for item_id, reason in result.excluded:
        conn.execute("INSERT INTO item_policy VALUES (?, ?, ?, ?)", (item_id, p, EXCLUDED, reason))
    conn.executemany("INSERT INTO close_exception VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [e.as_row() for e in result.exceptions])
    conn.commit()


def close_through(conn: sqlite3.Connection, target: str, policy: Policy) -> list[PeriodResult]:
    """Close every period after the last closed one, up to and including target."""
    resolve_timesheets(conn)
    last = last_closed_period(conn)
    if last is None:
        raise RuntimeError("the ledger has no closed periods to start from")
    periods = period_range(next_period(last), target)
    if not periods:
        raise RuntimeError(f"{target} is already closed in this ledger (closed through {last})")
    results = []
    for period in periods:
        result = compute_period(conn, period, policy)
        write_period(conn, result)
        results.append(result)
    return results
