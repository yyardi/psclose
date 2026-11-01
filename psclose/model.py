"""Shared value types for a period close."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .hours import ItemHours
from .periods import period_end, period_of

CENT = Decimal("0.01")


def money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def dec(value: Any) -> Decimal:
    return Decimal(str(value if value is not None else 0))


@dataclass
class PriorState:
    period: str | None
    recognized: Decimal
    planned: Decimal
    status: str | None


@dataclass
class ItemContext:
    period: str
    item: sqlite3.Row
    project: sqlite3.Row
    hours: ItemHours
    events: list[sqlite3.Row]
    adjustments: list[sqlite3.Row]
    snapshots: dict[str, Decimal]
    rmas: list[sqlite3.Row]
    prior: PriorState
    siblings: list[sqlite3.Row]
    sibling_hours: dict[str, ItemHours] = field(default_factory=dict)

    @property
    def item_id(self) -> str:
        return self.item["id"]

    @property
    def project_id(self) -> str:
        return self.project["id"]

    @property
    def contract(self) -> Decimal:
        return dec(self.item["contract_amount_native"])

    @property
    def currency(self) -> str:
        return self.item["currency"]

    @property
    def period_end(self) -> str:
        return period_end(self.period)

    @property
    def first_period(self) -> str:
        return period_of(self.item["signed_date"] or self.item["effective_date"])

    @property
    def contract_live(self) -> bool:
        effective = self.item["effective_date"] or self.item["signed_date"]
        return bool(effective) and effective <= self.period_end

    @property
    def is_effective(self) -> bool:
        """Revenue starts when the contract is live, or earlier once approved hours are
        being logged against the scope without being tagged as pre-effective. History
        recognised January hours on items effective 1 February but kept items open whose
        only hours carried the pre-effective tag."""
        return self.contract_live or self.hours.started

    def confirmed_events(self, types: tuple[str, ...]) -> list[sqlite3.Row]:
        return [e for e in self.events if e["event_type"] in types and e["status"] == "confirmed"]

    @property
    def termination_date(self) -> str | None:
        """Date the project was terminated, if it is cancelled as of this period."""
        if self.project["status"] != "cancelled":
            return None
        for rma in self.rmas:
            if "terminat" in (rma["reason"] or "").lower():
                return rma["event_date"]
        return self.project["end_date"]

    @property
    def terminated(self) -> bool:
        date = self.termination_date
        return bool(date) and date <= self.period_end

    @property
    def terminated_this_period(self) -> bool:
        return self.terminated and period_of(self.termination_date) == self.period


@dataclass
class Outcome:
    recognized: Decimal
    memo: str | None
    facts: dict[str, Any] = field(default_factory=dict)


@dataclass
class ItemClose:
    ctx: ItemContext
    method: str
    reason: str
    outcome: Outcome
    planned: Decimal
    status: str
    delta: Decimal
    posting: dict[str, Any] | None
    schedule: dict[str, Any]
