"""Write the close outputs: CSV extracts that mirror the ledger tables, a walk of every
schedule row from the prior period to this one, and a Markdown report for the controller."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import fields
from decimal import Decimal
from pathlib import Path

from .exceptions import ACTION, INFO, REVIEW, CloseException
from .model import ItemClose, money
from .periods import label, period_end, prev_period
from .policy import METHOD_LABELS
from .rollup import ProjectRollup
from .schedule import PeriodResult

SCHEDULE_COLUMNS = [
    "id", "contract_item_id", "period", "planned_amount_native", "recognized_amount_native",
    "currency", "status", "last_updated", "source_reference",
]
POSTING_COLUMNS = [
    "id", "contract_item_id", "posting_period", "posting_date", "posting_kind", "amount_native",
    "currency", "accounting_book", "status", "source_reference", "memo",
]
WALK_COLUMNS = [
    "period", "contract_item_id", "project_id", "project", "currency", "method", "status",
    "recognized_prior", "recognized_cum", "recognized_delta", "prior_period_delta",
    "planned_cum", "contract_amount", "pct_recognized", "billable_hours_period", "all_hours_period",
    "billable_hours_cum", "straight_line", "explanation",
]


def _fmt(value, places: int = 2) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, Decimal):
        return f"{value:,.{places}f}"
    if isinstance(value, float):
        return f"{value:,.{places}f}"
    return str(value)


def _hours(value: Decimal) -> str:
    return f"{value.normalize():f}" if value == value.to_integral() else f"{value:.2f}"


def _csv(path: Path, header: list[str], rows: list[list]) -> Path:
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if v is None else (f"{v:.2f}" if isinstance(v, Decimal) else v) for v in row])
    return path


def item_explanation(close: ItemClose, exceptions: list[CloseException]) -> tuple[bool, str]:
    """Whether the row is a plain continuation, and a short reason either way."""
    own = [e for e in exceptions if e.contract_item_id == close.ctx.item_id]
    flagged = [e for e in own if e.severity != INFO]
    if flagged:
        return False, "; ".join(dict.fromkeys(e.title for e in flagged))
    notes = [e for e in own if e.severity == INFO]
    hours = close.ctx.hours
    if notes:
        return True, "; ".join(dict.fromkeys(e.title for e in notes))
    if close.method == "poc_snapshot":
        return True, "Percent complete unchanged"
    if close.method == "milestone":
        return True, "Milestone pending; tranche 1 held"
    if close.method == "tm_hours":
        return True, f"{_hours(hours.all_period)} h at the standard rate"
    return True, f"{_hours(hours.billable_period)} billable h against plan"


def walk_rows(result: PeriodResult) -> list[list]:
    rows = []
    for c in sorted(result.items, key=lambda c: c.ctx.item_id):
        straight, why = item_explanation(c, result.exceptions)
        pct = (c.outcome.recognized / c.ctx.contract * 100).quantize(Decimal("0.1")) if c.ctx.contract else Decimal(0)
        rows.append([
            result.period, c.ctx.item_id, c.ctx.project_id, c.ctx.project["display_name"], c.ctx.currency, c.method, c.status,
            money(c.ctx.prior.recognized), c.outcome.recognized, c.delta, money(result.prior_deltas.get(c.ctx.item_id, Decimal(0))),
            c.planned, c.ctx.contract, pct, c.ctx.hours.billable_period, c.ctx.hours.all_period,
            c.ctx.hours.billable_cum, "yes" if straight else "no", why,
        ])
    return rows


def write_csvs(result: PeriodResult, rollups: list[ProjectRollup], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    written.append(_csv(out_dir / "revenue_schedule.csv", SCHEDULE_COLUMNS,
                        [[c.schedule[k] for k in SCHEDULE_COLUMNS] for c in sorted(result.items, key=lambda c: c.ctx.item_id)]))
    written.append(_csv(out_dir / "postings.csv", POSTING_COLUMNS,
                        [[c.posting[k] for k in POSTING_COLUMNS] for c in sorted(result.items, key=lambda c: c.ctx.item_id) if c.posting]))
    written.append(_csv(out_dir / "schedule_walk.csv", WALK_COLUMNS, walk_rows(result)))
    written.append(_csv(out_dir / "project_rollup.csv", [f.name for f in fields(ProjectRollup)],
                        [[getattr(r, f.name) for f in fields(ProjectRollup)] for r in rollups]))
    exc_header = ["period", "severity", "code", "title", "project_id", "contract_item_id", "amount_native", "currency",
                  "message", "evidence", "question"]
    written.append(_csv(out_dir / "exceptions.csv", exc_header,
                        [[e.period, e.severity, e.code, e.title, e.project_id, e.contract_item_id, e.amount_native, e.currency,
                          e.message, "; ".join(e.evidence), e.question] for e in result.exceptions]))
    return written


def _table(header: list[str], rows: list[list[str]], right: set[int] = frozenset()) -> str:
    align = ["---:" if i in right else "---" for i in range(len(header))]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v).replace("|", "\\|") for v in row) + " |")
    return "\n".join(lines)


def render_report(conn: sqlite3.Connection, result: PeriodResult, rollups: list[ProjectRollup]) -> str:
    period = result.period
    prior = prev_period(period)
    items = sorted(result.items, key=lambda c: c.ctx.item_id)
    sources = [r["source_file"] for r in conn.execute("SELECT DISTINCT source_file FROM load_log ORDER BY rowid")]

    by_currency: dict[str, dict[str, Decimal]] = {}
    for c in items:
        bucket = by_currency.setdefault(c.ctx.currency, {"period": Decimal(0), "cum": Decimal(0), "planned": Decimal(0), "contract": Decimal(0), "items": Decimal(0)})
        bucket["period"] += c.delta
        bucket["cum"] += c.outcome.recognized
        bucket["planned"] += c.planned
        bucket["contract"] += c.ctx.contract
        bucket["items"] += 1
    usd_period = sum((r.recognized_period_usd or Decimal(0) for r in rollups if r.scope == "project"), Decimal(0))
    usd_cum = sum((r.recognized_cum_usd or Decimal(0) for r in rollups if r.scope == "project"), Decimal(0))

    straight = [c for c in items if item_explanation(c, result.exceptions)[0]]
    moved = [c for c in items if c not in straight]
    sev = {s: [e for e in result.exceptions if e.severity == s] for s in (ACTION, REVIEW, INFO)}
    status_counts: dict[str, int] = {}
    for c in items:
        status_counts[c.status] = status_counts.get(c.status, 0) + 1

    out: list[str] = []
    out.append(f"# {label(period)} revenue close")
    out.append("")
    out.append(f"Period end {period_end(period)}. Prior closed period {prior}. "
               f"Sources: {', '.join(Path(s).name for s in sources)}.")
    out.append("")
    out.append(f"{len(items)} contract items on the schedule "
               f"({', '.join(f'{n} {s}' for s, n in sorted(status_counts.items()))}). "
               f"{len(straight)} are a plain continuation of {prior}; {len(moved)} moved for a reason listed below. "
               f"{len(sev[ACTION])} items need an answer before posting, {len(sev[REVIEW])} are for review, "
               f"{len(sev[INFO])} are noted for completeness.")
    out.append("")
    out.append("## Totals")
    out.append("")
    rows = [[cur, int(b["items"]), _fmt(b["contract"]), _fmt(b["cum"]), _fmt(b["period"]), _fmt(b["planned"])]
            for cur, b in sorted(by_currency.items())]
    out.append(_table(["Currency", "Items", "Contract value", "Recognized to date", f"Recognized in {period}", "Planned to date"], rows, {1, 2, 3, 4, 5}))
    out.append("")
    stale = [e for e in result.exceptions if e.code == "FX_RATE_STALE"]
    out.append(f"USD view at the latest available rates: {_fmt(usd_cum)} recognized to date, {_fmt(usd_period)} in {period}."
               + (f" Rates for {', '.join(e.currency for e in stale)} are carried from the prior month end; see exceptions." if stale else ""))
    out.append("")

    out.append("## What moved, and why")
    out.append("")
    out.append("Grouped by cause. Amounts are the effect on the period in the item's own currency. "
               "Items marked *action* may change once the controller answers the question.")
    for severity, heading in ((ACTION, "Needs an answer"), (REVIEW, "For review"), (INFO, "Noted")):
        group = sev[severity]
        if not group:
            continue
        out.append("")
        out.append(f"### {heading}")
        current = None
        for e in group:
            if e.code != current:
                current = e.code
                out.append("")
                out.append(f"**{e.title}** (`{e.code}`)")
                out.append("")
            who = " / ".join(x for x in (e.project_id, e.contract_item_id) if x) or "ledger"
            amount = f" **{_fmt(e.amount_native)} {e.currency}**." if e.amount_native not in (None, 0) else ""
            out.append(f"- {who}: {e.message}{amount}")
            if e.question:
                out.append(f"  Question: {e.question}")
    out.append("")

    out.append("## Project rollup")
    out.append("")
    rows = []
    for r in rollups:
        name = r.display_name + (" (incl. change orders)" if r.scope == "with_change_orders" else "")
        rows.append([r.project_id, name, r.billing_type, r.currency, r.items, _fmt(r.contract_total), _fmt(r.recognized_prior),
                     _fmt(r.recognized_cum), _fmt(r.recognized_period), _fmt(r.planned_cum), f"{r.pct_recognized}%",
                     _hours(r.billable_hours_period), _fmt(r.recognized_cum_usd), r.exceptions])
    out.append(_table(["Project", "Name", "Billing", "Cur", "Items", "Contract", f"Rec. {prior}", f"Rec. {period}",
                       "Period", "Planned", "% rec.", "Bill. h", "Rec. USD", "Flags"], rows, {4, 5, 6, 7, 8, 9, 10, 11, 12, 13}))
    out.append("")

    out.append("## Schedule walk")
    out.append("")
    out.append(f"Every row of the {period} schedule, cumulative as in the ledger, with the period movement next to "
               f"{prior}'s movement so a straight-line month is visible at a glance.")
    out.append("")
    rows = []
    for row in walk_rows(result):
        (_, item, project_id, project, cur, method, status, rec_prior, rec, delta, prior_delta,
         planned, contract, pct, bh, ah, bh_cum, straight_flag, why) = row
        rows.append([item, project_id, METHOD_LABELS[method].split(",")[0], status, cur, _fmt(rec_prior), _fmt(rec),
                     _fmt(delta), _fmt(prior_delta), _fmt(planned), f"{pct}%", _hours(bh), why])
    out.append(_table(["Item", "Project", "Method", "Status", "Cur", f"Rec. {prior}", f"Rec. {period}", f"{period} move",
                       f"{prior} move", "Planned", "% rec.", "Bill. h", "Why"], rows, {5, 6, 7, 8, 9, 10, 11}))
    out.append("")

    questions = list(dict.fromkeys(e.question for e in result.exceptions if e.question))
    if questions:
        out.append("## Questions for the controller")
        out.append("")
        for i, q in enumerate(questions, 1):
            out.append(f"{i}. {q}")
        out.append("")

    if result.excluded:
        out.append("## Not on the PS schedule")
        out.append("")
        for item_id, reason in result.excluded:
            out.append(f"- {item_id}: {reason}")
        out.append("")
    return "\n".join(out)


def write_report(conn: sqlite3.Connection, result: PeriodResult, rollups: list[ProjectRollup], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "close_report.md"
    path.write_text(render_report(conn, result, rollups))
    return path
