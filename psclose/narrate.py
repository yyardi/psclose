"""Draft the controller memo from the close outputs.

Every figure in the memo comes from exceptions.csv and project_rollup.csv, which the close
wrote from code. Claude only turns that structured list into readable prose for the
controller. When no API credentials are available, or the call fails for any reason, a
templated memo is written instead so the close never depends on the network.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

from .periods import label

DEFAULT_MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """You are a senior revenue accountant drafting the month-end close memo for the
controller of a professional-services firm. You are given the period totals, the list of
exceptions the close engine raised (each with a cause, a severity, the amount at stake and the
question it raises), and the per-project rollup.

Write the memo in plain, direct English, the way a careful colleague would. Use only the figures
provided; never invent, estimate or round away a number, and quote amounts with their currency.
Open with two or three sentences on the period totals and how many items moved. Then cover, in
this order: the decisions the controller must make before posting (severity "action"), each with
the amount at stake and the specific question; the movements worth a glance (severity "review"),
grouped by cause rather than listed one by one; and a single short paragraph on the housekeeping
items (severity "info"). Close with a numbered list of the open questions, deduplicated and
ordered by the money at stake. Short paragraphs beat bullet lists. Stay under 700 words. Do not
use headings larger than level 2, do not use emoji, and do not add a sign-off."""


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def load_inputs(out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    exceptions = _read_csv(out_dir / "exceptions.csv")
    rollups = _read_csv(out_dir / "project_rollup.csv")
    schedule = _read_csv(out_dir / "schedule_walk.csv")
    period = schedule[0]["period"] if schedule and "period" in schedule[0] else rollups[0]["period"]
    totals: dict[str, dict[str, float]] = {}
    for row in schedule:
        bucket = totals.setdefault(row["currency"], {"items": 0, "recognized_period": 0.0, "recognized_cum": 0.0, "planned_cum": 0.0})
        bucket["items"] += 1
        bucket["recognized_period"] += float(row["recognized_delta"])
        bucket["recognized_cum"] += float(row["recognized_cum"])
        bucket["planned_cum"] += float(row["planned_cum"])
    moved = sum(1 for row in schedule if row["straight_line"] == "no")
    return {
        "period": period,
        "period_label": label(period),
        "totals_by_currency": totals,
        "items": len(schedule),
        "items_moved": moved,
        "exceptions": [
            {k: row[k] for k in ("severity", "code", "title", "project_id", "contract_item_id", "amount_native", "currency", "message", "question")}
            for row in exceptions
        ],
        "projects": [
            {k: row[k] for k in ("project_id", "display_name", "billing_type", "currency", "contract_total",
                                  "recognized_cum", "recognized_period", "pct_recognized", "exceptions")}
            for row in rollups if row["scope"] == "project"
        ],
    }


def _fmt(amount: str | float, currency: str) -> str:
    return f"{float(amount):,.2f} {currency}"


def template_memo(data: dict) -> str:
    period = data["period_label"]
    lines = [f"# {period} close memo", ""]
    totals = data["totals_by_currency"]
    total_text = "; ".join(
        f"{_fmt(b['recognized_period'], cur)} on {int(b['items'])} item{'s' if b['items'] != 1 else ''}"
        for cur, b in sorted(totals.items())
    )
    lines.append(
        f"The {period} schedule covers {data['items']} contract items. Revenue recognized in the period: "
        f"{total_text}. {data['items_moved']} items moved for a reason other than another month of the same "
        f"work; the rest are a plain continuation of the prior month."
    )
    lines.append("")
    by_sev: dict[str, list[dict]] = {"action": [], "review": [], "info": []}
    for e in data["exceptions"]:
        by_sev.setdefault(e["severity"], []).append(e)

    if by_sev["action"]:
        lines.append("## Before posting")
        lines.append("")
        lines.append("These figures may change once you answer:")
        lines.append("")
        for e in by_sev["action"]:
            who = " / ".join(x for x in (e["project_id"], e["contract_item_id"]) if x) or "ledger"
            amount = f" Amount at stake: {_fmt(e['amount_native'], e['currency'])}." if e["amount_native"] else ""
            lines.append(f"- {who}: {e['message']}{amount}")
            if e["question"]:
                lines.append(f"  {e['question']}")
        lines.append("")

    if by_sev["review"]:
        lines.append("## Movements to look at")
        lines.append("")
        groups: dict[str, list[dict]] = {}
        for e in by_sev["review"]:
            groups.setdefault(e["title"], []).append(e)
        for title, group in groups.items():
            total_by_cur: dict[str, float] = {}
            for e in group:
                if e["amount_native"]:
                    total_by_cur[e["currency"]] = total_by_cur.get(e["currency"], 0.0) + float(e["amount_native"])
            who = ", ".join(dict.fromkeys(e["contract_item_id"] or e["project_id"] for e in group))
            amounts = "; ".join(_fmt(v, c) for c, v in sorted(total_by_cur.items()))
            lines.append(f"- {title}: {who}." + (f" Net {amounts}." if amounts else ""))
        lines.append("")

    if by_sev["info"]:
        counts: dict[str, int] = {}
        for e in by_sev["info"]:
            counts[e["title"]] = counts.get(e["title"], 0) + 1
        lines.append("## Noted")
        lines.append("")
        lines.append("For completeness: " + "; ".join(f"{t.lower()} ({n})" for t, n in counts.items()) + ".")
        lines.append("")

    questions = list(dict.fromkeys(e["question"] for e in data["exceptions"] if e["question"]))
    if questions:
        lines.append("## Open questions")
        lines.append("")
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")
        lines.append("")
    return "\n".join(lines)


def claude_memo(data: dict, model: str) -> str:
    """Ask Claude for the memo. Raises on any failure; the caller decides what to do."""
    import anthropic  # optional dependency, imported lazily

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=8000,
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Draft the {data['period_label']} close memo from this data.\n\n"
                + json.dumps(data, indent=1, default=str)
            ),
        }],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("the model declined to draft the memo")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise RuntimeError("the model returned no text")
    return text


def write_memo(out_dir: Path, model: str | None = None, *, use_claude: bool = True) -> Path:
    out_dir = Path(out_dir)
    data = load_inputs(out_dir)
    model = model or DEFAULT_MODEL
    source = f"templated from exceptions.csv and project_rollup.csv"
    text = None
    if use_claude:
        try:
            text = claude_memo(data, model)
            source = f"drafted by {model} from exceptions.csv and project_rollup.csv; figures are the engine's, prose is the model's"
        except ImportError:
            print("anthropic SDK not installed (uv sync --extra llm); writing the templated memo", file=sys.stderr)
        except Exception as exc:  # any API, auth or network problem falls back to the template
            print(f"Claude memo unavailable ({type(exc).__name__}: {exc}); writing the templated memo", file=sys.stderr)
    if text is None:
        text = template_memo(data)
    path = out_dir / "close_memo.md"
    path.write_text(text.rstrip() + f"\n\n---\n*{source}.*\n")
    return path
