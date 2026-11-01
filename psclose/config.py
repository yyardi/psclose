"""Configuration: input files and the recognition policy, read from psclose.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path("psclose.toml")


@dataclass(frozen=True)
class Policy:
    planned_rate: Decimal = Decimal("200")
    acceptance_cap: Decimal = Decimal("0.95")
    acceptance_events: tuple[str, ...] = ("customer_acceptance", "go_live", "uat_signoff")
    milestone_tranches: tuple[Decimal, ...] = (Decimal("0.5"), Decimal("0.5"))
    milestone_events: tuple[str, ...] = ("milestone_completion", "uat_signoff", "customer_acceptance")
    eac_adjustment_types: tuple[str, ...] = ("internal", "no_charge")
    tm_rate: Decimal = Decimal("200")
    tm_count_nonbillable: bool = True
    poc_source: str = "delivery_lead_confirmation"
    hours_allocation: str = "remaining_planned_hours"

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Policy":
        kwargs: dict[str, Any] = {}
        for name, current in cls.__dataclass_fields__.items():
            if name not in data:
                continue
            value = data[name]
            default = current.default
            if isinstance(default, Decimal):
                value = Decimal(str(value))
            elif isinstance(default, tuple):
                value = tuple(Decimal(str(v)) if isinstance(default[0], Decimal) else str(v) for v in value)
            kwargs[name] = value
        policy = cls(**kwargs)
        if sum(policy.milestone_tranches) != 1:
            raise ValueError("milestone_tranches must sum to 1")
        if policy.hours_allocation not in ("remaining_planned_hours", "planned_hours"):
            raise ValueError(f"unknown hours_allocation {policy.hours_allocation!r}")
        return policy


@dataclass
class Inputs:
    base: Path
    increments: list[Path] = field(default_factory=list)
    out_dir: Path = Path("out")


@dataclass
class Config:
    inputs: Inputs
    policy: Policy
    root: Path

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        path = Path(path or DEFAULT_CONFIG)
        with path.open("rb") as fh:
            data = tomllib.load(fh)
        root = path.resolve().parent
        raw_inputs = data.get("inputs", {})
        inputs = Inputs(
            base=root / raw_inputs["base"],
            increments=[root / p for p in raw_inputs.get("increments", [])],
            out_dir=root / raw_inputs.get("out_dir", "out"),
        )
        return cls(inputs=inputs, policy=Policy.from_mapping(data.get("policy", {})), root=root)
