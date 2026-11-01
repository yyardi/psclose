"""Per-project view of a closed period, with change-order child projects folded into their
parent as a second row so both views are available."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, fields
from decimal import Decimal

from .exceptions import INFO
from .ledger import fx_latest
from .model import ItemClose, dec, money
from .periods import period_end
from .schedule import PeriodResult

ZERO = Decimal("0")


@dataclass
class ProjectRollup:
    period: str
    project_id: str
    scope: str
    customer: str
    display_name: str
    billing_type: str
    project_status: str
    currency: str
    items: int
    contract_total: Decimal
    recognized_prior: Decimal
    recognized_cum: Decimal
    recognized_period: Decimal
    planned_cum: Decimal
    billable_hours_period: Decimal
    all_hours_period: Decimal
    billable_hours_cum: Decimal
    pct_recognized: Decimal
    fx_to_usd: Decimal | None
    fx_rate_date: str | None
    recognized_cum_usd: Decimal | None
    recognized_period_usd: Decimal | None
    exceptions: int

    def as_row(self) -> tuple:
        out = []
        for f in fields(self):
            v = getattr(self, f.name)
            out.append(float(v) if isinstance(v, Decimal) else v)
        return tuple(out)


def _usd(amount: Decimal, rate: Decimal | None) -> Decimal | None:
    return money(amount * rate) if rate is not None else None


def _summarize(period: str, project: sqlite3.Row, customer: str, scope: str, closes: list[ItemClose],
               rate: tuple[float, str] | None, exception_count: int) -> ProjectRollup:
    contract = sum((c.ctx.contract for c in closes), ZERO)
    recognized = sum((c.outcome.recognized for c in closes), ZERO)
    prior = sum((c.ctx.prior.recognized for c in closes), ZERO)
    planned = sum((c.planned for c in closes), ZERO)
    fx = dec(rate[0]) if rate else None
    return ProjectRollup(
        period=period,
        project_id=project["id"],
        scope=scope,
        customer=customer,
        display_name=project["display_name"],
        billing_type=project["billing_type"],
        project_status=project["status"],
        currency=closes[0].ctx.currency,
        items=len(closes),
        contract_total=money(contract),
        recognized_prior=money(prior),
        recognized_cum=money(recognized),
        recognized_period=money(recognized - prior),
        planned_cum=money(planned),
        billable_hours_period=sum((c.ctx.hours.billable_period for c in closes), ZERO),
        all_hours_period=sum((c.ctx.hours.all_period for c in closes), ZERO),
        billable_hours_cum=sum((c.ctx.hours.billable_cum for c in closes), ZERO),
        pct_recognized=(recognized / contract * 100).quantize(Decimal("0.1")) if contract else ZERO,
        fx_to_usd=fx,
        fx_rate_date=rate[1] if rate else None,
        recognized_cum_usd=_usd(recognized, fx),
        recognized_period_usd=_usd(recognized - prior, fx),
        exceptions=exception_count,
    )


def build_rollup(conn: sqlite3.Connection, result: PeriodResult) -> list[ProjectRollup]:
    period = result.period
    end = period_end(period)
    projects = {r["id"]: r for r in conn.execute("SELECT * FROM project")}
    customers = {r["id"]: r["display_name"] for r in conn.execute("SELECT * FROM customer")}
    by_project: dict[str, list[ItemClose]] = {}
    for c in result.items:
        by_project.setdefault(c.ctx.project_id, []).append(c)
    counts: dict[str, int] = {}
    for e in result.exceptions:
        if e.severity != INFO and e.project_id:
            counts[e.project_id] = counts.get(e.project_id, 0) + 1

    rows: list[ProjectRollup] = []
    for project_id in sorted(by_project):
        project = projects[project_id]
        closes = by_project[project_id]
        rate = fx_latest(conn, closes[0].ctx.currency, end)
        rows.append(_summarize(period, project, customers.get(project["customer_id"], project["customer_id"]),
                               "project", closes, rate, counts.get(project_id, 0)))

    children: dict[str, list[str]] = {}
    for project_id in by_project:
        parent = projects[project_id]["parent_project_id"]
        if parent and parent in by_project:
            children.setdefault(parent, []).append(project_id)
    for parent, kids in sorted(children.items()):
        closes = by_project[parent] + [c for k in kids for c in by_project[k]]
        if len({c.ctx.currency for c in closes}) > 1:
            continue
        project = projects[parent]
        rate = fx_latest(conn, closes[0].ctx.currency, end)
        count = counts.get(parent, 0) + sum(counts.get(k, 0) for k in kids)
        rows.append(_summarize(period, project, customers.get(project["customer_id"], project["customer_id"]),
                               "with_change_orders", closes, rate, count))
    return rows


def write_rollup(conn: sqlite3.Connection, rows: list[ProjectRollup]) -> None:
    if not rows:
        return
    conn.execute("DELETE FROM project_rollup WHERE period = ?", (rows[0].period,))
    placeholders = ", ".join("?" for _ in fields(ProjectRollup))
    conn.executemany(f"INSERT INTO project_rollup VALUES ({placeholders})", [r.as_row() for r in rows])
    conn.commit()
