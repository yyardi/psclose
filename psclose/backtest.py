"""Replay closed periods from their inputs and diff the result against what was posted.

If the rules reproduce six months of history to the cent, the July numbers rest on the same
rules and not on guesswork. Differences that are understood are listed in KNOWN_DEVIATIONS
with the reason; anything else is a failure.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from decimal import Decimal

from .config import Policy
from .hours import attribute_timesheets
from .identity import resolve_timesheets
from .model import dec
from .periods import period_range
from .schedule import compute_period

KNOWN_DEVIATIONS: dict[tuple[str, str], str] = {
    ("CI-PX-05", "2026-05"): (
        "History did not apply the +20h no-charge change order CO-2026-011 (effective 2026-05-18) to "
        "PX-05's estimate at completion, although the same kind of adjustment was applied on PX-22, "
        "PX-31 and PX-42. The engine applies the rule uniformly."
    ),
    ("CI-PX-05", "2026-06"): "Same cause as 2026-05; the 95% cap binds either way from July onward.",
}


@dataclass
class Diff:
    period: str
    contract_item_id: str
    field: str
    expected: object
    actual: object

    @property
    def key(self) -> tuple[str, str]:
        return (self.contract_item_id, self.period)


@dataclass
class BacktestResult:
    periods: list[str]
    rows_checked: int = 0
    postings_checked: int = 0
    diffs: list[Diff] = field(default_factory=list)

    @property
    def known(self) -> list[Diff]:
        return [d for d in self.diffs if d.key in KNOWN_DEVIATIONS]

    @property
    def unexplained(self) -> list[Diff]:
        return [d for d in self.diffs if d.key not in KNOWN_DEVIATIONS]

    @property
    def ok(self) -> bool:
        return not self.unexplained


def _num(value) -> Decimal:
    return dec(value).quantize(Decimal("0.01"))


def replay(conn: sqlite3.Connection, first: str, last: str, policy: Policy) -> BacktestResult:
    resolve_timesheets(conn)
    attribute_timesheets(conn, last, policy, redo=True)
    result = BacktestResult(period_range(first, last))
    for period in result.periods:
        computed = compute_period(conn, period, policy, check_prior=False).by_item()
        stored = {
            r["contract_item_id"]: r
            for r in conn.execute("SELECT * FROM revenue_schedule WHERE period = ?", (period,))
        }
        postings = {
            r["contract_item_id"]: r
            for r in conn.execute("SELECT * FROM accounting_posting WHERE posting_period = ? AND posting_kind != 'opening'", (period,))
        }
        for item_id in sorted(set(stored) | set(computed)):
            row, close = stored.get(item_id), computed.get(item_id)
            if row is None:
                result.diffs.append(Diff(period, item_id, "presence", "absent", "computed"))
                continue
            if close is None:
                result.diffs.append(Diff(period, item_id, "presence", "posted", "not computed"))
                continue
            result.rows_checked += 1
            checks = [
                ("recognized", _num(row["recognized_amount_native"]), close.outcome.recognized),
                ("planned", _num(row["planned_amount_native"]), close.planned),
                ("status", row["status"], close.status),
                ("source_reference", row["source_reference"], close.schedule["source_reference"]),
            ]
            posting = postings.get(item_id)
            if posting is not None or close.posting is not None:
                result.postings_checked += 1
                if posting is None or close.posting is None:
                    checks.append(("posting", posting["id"] if posting else None, close.posting["id"] if close.posting else None))
                else:
                    checks += [
                        ("posting_amount", _num(posting["amount_native"]), close.posting["amount_native"]),
                        ("posting_kind", posting["posting_kind"], close.posting["posting_kind"]),
                        ("posting_memo", posting["memo"], close.posting["memo"]),
                        ("posting_id", posting["id"], close.posting["id"]),
                    ]
            for name, expected, actual in checks:
                if expected != actual:
                    result.diffs.append(Diff(period, item_id, name, expected, actual))
    return result


def format_report(result: BacktestResult) -> str:
    lines = [
        f"Replayed {result.periods[0]}..{result.periods[-1]}: {result.rows_checked} schedule rows, "
        f"{result.postings_checked} postings compared.",
    ]
    if result.known:
        lines.append("")
        lines.append("Known deviations (documented, not errors):")
        for key in sorted({d.key for d in result.known}):
            fields = ", ".join(f"{d.field} posted {d.expected} vs rule {d.actual}" for d in result.known if d.key == key)
            lines.append(f"  {key[0]} {key[1]}: {fields}")
            lines.append(f"    {KNOWN_DEVIATIONS[key]}")
    if result.unexplained:
        lines.append("")
        lines.append(f"UNEXPLAINED DIFFERENCES ({len(result.unexplained)}):")
        for d in result.unexplained:
            lines.append(f"  {d.period} {d.contract_item_id} {d.field}: posted {d.expected!r}, rule {d.actual!r}")
    else:
        lines.append("")
        lines.append("No unexplained differences.")
    return "\n".join(lines)
