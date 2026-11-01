"""Attribute logged hours to contract items.

A timesheet names a project, not a contract item, and most projects have exactly one item.
When a project has several, the worker alias or the row id sometimes carries the item
(history tags rows "worker-CI-PX-12A-…", July tags change-request rows "worker-PX-38-CR-…").
When nothing on the row says which item, the hours are split across the project's open items
in proportion to the hours each one still has to deliver. Every attribution is stored with
the method that produced it, and the split case is surfaced in the exception report because
the controller may know better.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from decimal import Decimal

from .config import Policy
from .periods import period_end, period_of, period_start, prev_period

ZERO = Decimal("0")


@dataclass
class ItemHours:
    billable_cum: Decimal = ZERO
    all_cum: Decimal = ZERO
    billable_period: Decimal = ZERO
    all_period: Decimal = ZERO
    methods: set[str] = field(default_factory=set)


def _dec(value: float | int | str | None) -> Decimal:
    return Decimal(str(value if value is not None else 0))


def _items_by_project(conn: sqlite3.Connection) -> dict[str, list[sqlite3.Row]]:
    out: dict[str, list[sqlite3.Row]] = {}
    for row in conn.execute("SELECT * FROM contract_item WHERE is_ps = 1 ORDER BY id"):
        out.setdefault(row["project_id"], []).append(row)
    return out


def _token_pattern(item_id: str) -> re.Pattern[str]:
    token = item_id[3:] if item_id.startswith("CI-") else item_id
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(token) + r"(?![A-Za-z0-9])")


def _recognized_prior(conn: sqlite3.Connection, period: str) -> dict[str, Decimal]:
    prior = prev_period(period)
    rows = conn.execute(
        "SELECT contract_item_id, recognized_amount_native FROM revenue_schedule WHERE period = ?",
        (prior,),
    )
    return {r["contract_item_id"]: _dec(r["recognized_amount_native"]) for r in rows}


def _billable_cum_before(conn: sqlite3.Connection, period: str) -> dict[str, Decimal]:
    rows = conn.execute(
        """
        SELECT a.contract_item_id, SUM(t.hours * a.share) AS hours
        FROM timesheet_attribution a
        JOIN timesheet_entry t ON t.id = a.timesheet_id
        WHERE t.billable = 1 AND t.entry_date < ?
        GROUP BY a.contract_item_id
        """,
        (period_start(period),),
    )
    return {r["contract_item_id"]: _dec(r["hours"]) for r in rows}


def attribute_timesheets(
    conn: sqlite3.Connection, through: str, policy: Policy, *, redo: bool = False
) -> dict[str, int]:
    """Attribute every resolved timesheet dated on or before the end of `through`.

    Rows already attributed are left alone unless redo is set. Periods are processed in
    order so that a split in July uses the item balances as they stood at the end of June.
    """
    if redo:
        conn.execute("DELETE FROM timesheet_attribution")
    items_by_project = _items_by_project(conn)
    patterns = {
        item["id"]: _token_pattern(item["id"])
        for items in items_by_project.values()
        for item in items
    }
    pending = conn.execute(
        """
        SELECT t.id, t.user_alias, t.entry_date, r.project_id
        FROM timesheet_entry t
        JOIN timesheet_resolution r ON r.timesheet_id = t.id
        WHERE r.project_id IS NOT NULL AND t.entry_date <= ?
          AND EXISTS (SELECT 1 FROM contract_item ci WHERE ci.project_id = r.project_id AND ci.is_ps = 1)
          AND t.id NOT IN (SELECT timesheet_id FROM timesheet_attribution)
        ORDER BY t.entry_date, t.id
        """,
        (period_end(through),),
    ).fetchall()
    counts: dict[str, int] = {}
    by_period: dict[str, list[sqlite3.Row]] = {}
    for row in pending:
        by_period.setdefault(period_of(row["entry_date"]), []).append(row)

    for period in sorted(by_period):
        recognized_prior = _recognized_prior(conn, period)
        billable_prior = _billable_cum_before(conn, period)
        out: list[tuple[str, str, float, str]] = []
        for row in by_period[period]:
            items = items_by_project.get(row["project_id"], [])
            shares = _attribute_one(row, items, patterns, recognized_prior, billable_prior, policy)
            for item_id, share, method in shares:
                out.append((row["id"], item_id, float(share), method))
            counts[shares[0][2]] = counts.get(shares[0][2], 0) + 1
        conn.executemany("INSERT OR REPLACE INTO timesheet_attribution VALUES (?, ?, ?, ?)", out)
        conn.commit()
    return counts


def _attribute_one(
    row: sqlite3.Row,
    items: list[sqlite3.Row],
    patterns: dict[str, re.Pattern[str]],
    recognized_prior: dict[str, Decimal],
    billable_prior: dict[str, Decimal],
    policy: Policy,
) -> list[tuple[str, Decimal, str]]:
    if not items:
        return []
    if len(items) == 1:
        return [(items[0]["id"], Decimal(1), "single_item")]

    haystack = f"{row['user_alias'] or ''} {row['id']}"
    tagged = [item for item in items if patterns[item["id"]].search(haystack)]
    if tagged:
        best = max(tagged, key=lambda item: len(item["id"]))
        return [(best["id"], Decimal(1), "alias_token")]

    entry_date = row["entry_date"]
    candidates = [
        item
        for item in items
        if (item["signed_date"] or item["effective_date"] or "") <= entry_date
        and not item["superseded_by_item_id"]
        and recognized_prior.get(item["id"], ZERO) < _dec(item["contract_amount_native"])
    ]
    if not candidates:
        candidates = [item for item in items if (item["signed_date"] or "") <= entry_date] or items

    if policy.hours_allocation == "remaining_planned_hours":
        weights = {
            item["id"]: max(_dec(item["planned_hours"]) - billable_prior.get(item["id"], ZERO), ZERO)
            for item in candidates
        }
        if sum(weights.values()) == 0:
            weights = {item["id"]: _dec(item["planned_hours"]) for item in candidates}
    else:
        weights = {item["id"]: _dec(item["planned_hours"]) for item in candidates}
    total = sum(weights.values())
    if total == 0:
        weights = {item["id"]: Decimal(1) for item in candidates}
        total = Decimal(len(candidates))
    method = "single_open_item" if len(candidates) == 1 else f"allocated_{policy.hours_allocation}"
    return [(item_id, weight / total, method) for item_id, weight in weights.items()]


def hours_by_item(conn: sqlite3.Connection, period: str) -> dict[str, ItemHours]:
    """Cumulative and in-period approved hours per contract item at the end of `period`."""
    rows = conn.execute(
        """
        SELECT a.contract_item_id AS item, a.method, t.billable, t.entry_date,
               SUM(t.hours * a.share) AS hours
        FROM timesheet_attribution a
        JOIN timesheet_entry t ON t.id = a.timesheet_id
        WHERE t.entry_date <= ? AND t.approval_status = 'Approved'
        GROUP BY a.contract_item_id, a.method, t.billable, t.entry_date
        """,
        (period_end(period),),
    )
    start = period_start(period)
    out: dict[str, ItemHours] = {}
    for r in rows:
        # Shares are stored as floats; six decimals of an hour is far below a cent.
        hours = _dec(r["hours"]).quantize(Decimal("0.000001"))
        ih = out.setdefault(r["item"], ItemHours())
        ih.all_cum += hours
        in_period = r["entry_date"] >= start
        if in_period:
            ih.all_period += hours
            ih.methods.add(r["method"])
        if r["billable"]:
            ih.billable_cum += hours
            if in_period:
                ih.billable_period += hours
    return out


def unattributed_hours(conn: sqlite3.Connection, period: str) -> list[sqlite3.Row]:
    """Timesheets in `period` that reached no contract item, with the reason."""
    return conn.execute(
        """
        SELECT t.id, t.project_name_as_reported, t.entry_date, t.hours, t.billable, t.notes,
               t.approval_status, r.method AS resolution, r.project_id
        FROM timesheet_entry t
        LEFT JOIN timesheet_resolution r ON r.timesheet_id = t.id
        WHERE t.entry_date BETWEEN ? AND ?
          AND (r.project_id IS NULL
               OR t.approval_status != 'Approved'
               OR t.id NOT IN (SELECT timesheet_id FROM timesheet_attribution))
        ORDER BY t.entry_date, t.id
        """,
        (period_start(period), period_end(period)),
    ).fetchall()
