"""Helpers for the YYYY-MM accounting period strings used throughout the ledger."""

from __future__ import annotations

import calendar
import datetime as dt

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _split(period: str) -> tuple[int, int]:
    try:
        year, month = int(period[:4]), int(period[5:7])
    except ValueError as exc:
        raise ValueError(f"not a YYYY-MM period: {period!r}") from exc
    if len(period) != 7 or period[4] != "-" or not 1 <= month <= 12:
        raise ValueError(f"not a YYYY-MM period: {period!r}")
    return year, month


def period_start(period: str) -> str:
    year, month = _split(period)
    return f"{year:04d}-{month:02d}-01"


def period_end(period: str) -> str:
    year, month = _split(period)
    return f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"


def next_period(period: str) -> str:
    year, month = _split(period)
    if month == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month + 1:02d}"


def prev_period(period: str) -> str:
    year, month = _split(period)
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"


def period_of(date_str: str) -> str:
    """Period containing an ISO date string."""
    dt.date.fromisoformat(date_str[:10])
    return date_str[:7]


def period_range(first: str, last: str) -> list[str]:
    """Inclusive list of periods from first to last."""
    if first > last:
        return []
    out = [first]
    while out[-1] != last:
        out.append(next_period(out[-1]))
    return out


def label(period: str) -> str:
    year, month = _split(period)
    return f"{_MONTHS[month - 1]} {year}"
