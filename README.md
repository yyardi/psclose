# psclose

A month-end revenue close for a professional-services ledger.

Given the database the client closed through June 2026 and the July operational increment,
it writes the July `revenue_schedule` rows (one per contract item, cumulative planned and
recognized amounts in the same shape as the history), the postings behind them, a per-project
rollup, and a report that walks through every figure that is not a plain continuation of June.
August is the same command with one more input file.

## Run it

```
uv sync
uv run psclose close --period 2026-07
uv run psclose backtest
uv run pytest
```

`close` assembles a working ledger from the inputs named in `psclose.toml`, closes every period
after the last closed one up to the target, and writes to `out/2026-07/`:

| File | What it is |
|---|---|
| `revenue_schedule.csv` | The 48 July rows, same columns as the `revenue_schedule` table |
| `postings.csv` | The `accounting_posting` rows that produce them |
| `schedule_walk.csv` | Every row with June's figure, July's figure, both movements, hours, and why it moved |
| `project_rollup.csv` | Per project, plus a consolidated row for projects with change-order children |
| `exceptions.csv` | Everything the controller should look at, with cause, severity, amount, evidence and question |
| `close_report.md` | The above as one readable document |
| `close_memo.md` | A short memo to the controller (see below) |
| `ledger.sqlite` | Base plus increments plus the new rows; the starting point for the next period |

`backtest` replays January through June from the raw inputs with the same rules and diffs the
result against what the client actually posted: 234 schedule rows and 228 postings match to the
cent, with one documented exception (see below). This is the evidence that the July numbers rest
on the client's own practice rather than on my reading of the glossary.

Without `uv`: `python3.12 -m venv .venv && .venv/bin/pip install -e '.[llm]' pytest`, then use
`.venv/bin/psclose`.

### August

Drop the new file in `data/`, add it to `increments` in `psclose.toml` (or pass `--increment`
twice), and run `close --period 2026-08`. The ledger from July is not needed: both increments are
replayed on top of the June base and July is reproduced on the way. `tests/test_august.py` does
exactly this with a synthetic August file and checks the two routes (from the raw inputs, and
from the saved July ledger) give identical rows.

### The memo

`close --memo` (or `narrate --period 2026-07`) drafts `close_memo.md` for the controller. With the
`anthropic` package installed (`uv sync --extra llm`) and credentials in the environment it asks
Claude to turn the exception list into prose; otherwise, or if the call fails, it writes a
templated memo from the same data. No amount is ever produced by the model. The footer of the
memo says which path produced it.

## How a period is closed

1. **Ledger.** Copy the base database, upsert each increment in order (`psclose/ledger.py`).
   Inputs are never modified. A `load_log` table records what came from where.
2. **Identity.** Timesheets without a project id are matched by name against the project's
   display name and its `aliases_json` names (`identity.py`). Twenty-five "Redwood Transit Core"
   rows resolve to PX-18 this way; one "Legacy Support Work" row from June matches nothing and
   stays out, as it did in the client's own June close.
3. **Hours.** Each timesheet is attributed to a contract item: the project's only item, the item
   named in the worker alias, or, when a project has several open items and the row says
   nothing, a split in proportion to the hours each item still has to deliver (`hours.py`).
   July's timesheets dropped the item tag that June's carried, so three projects need the split
   and the report says so, with the alternative quantified.
4. **Method.** Each item's recognition method is inferred from the data, not from a list
   (`policy.py`): subscriptions are excluded, `Time & Materials` projects bill hours, items with
   service `Fixed Fee Delivery` are milestone tranches, projects with an unbroken series of
   delivery-lead percent-complete confirmations use that percent, and everything else is hours
   against the estimate at completion with a 95% cap until acceptance.
5. **Numbers.** `recognize.py` computes the cumulative recognized amount per method;
   `schedule.py` derives planned amount, status, the period posting, and the schedule row.
   Money is `Decimal`, rounded half-up to the cent only at the end.
6. **Exceptions, rollup, report.** `exceptions.py` collects item-level and ledger-level
   findings with a cause code; `rollup.py` and `report.py` write the rest.

The rules themselves, with the queries that justify each one, are in
[docs/recognition_rules.md](docs/recognition_rules.md). The numbers that drive them (the 200/h
planning rate, the 95% cap, the tranche split, which adjustment types move the estimate) live in
`psclose.toml` so an answer from the controller is a config edit, not a code change.

## July in brief

Recognized in the period: 242,669.97 USD, 11,252.74 EUR, 9,975.61 GBP, 6,800.00 CAD across
48 items (31 posted, 17 held). 21 items are a plain continuation of June. The rest moved because:

- Two milestone deals (PX-09, PX-10) had their second milestone confirmed on 11 July and release
  the remaining 50%: 40,000 and 30,000 USD.
- Bramwell Logistics (PX-02) accepted on 9 July, releasing the 95% cap: 4,400 USD.
- Four modernization projects received new delivery-lead percent-complete confirmations.
- Two expansion scopes (PX-29, PX-30) went live on 1 July and recognize for the first time,
  including hours ops had tagged as pre-effective.
- One new deal (PX-43) and one paid change request on an existing project (PX-38) appear for the
  first time.
- Five rollouts are past their planned hours and sit at the 95% cap waiting for acceptance.

Ten findings need an answer before posting. The largest is how to split PX-12's 109 July hours
between its two items (an 8,175 USD swing). The full list, with what I assumed in the meantime,
is in [docs/controller_questions.md](docs/controller_questions.md).

## The one place the history disagrees with itself

The June close applied approved no-charge overruns to the estimate at completion on PX-22, PX-31
and PX-42, but not on PX-05 (CO-2026-011, +20 hours, effective 18 May). The engine applies the
rule uniformly, which is why the backtest reports CI-PX-05 for May and June. It makes no
difference to July because PX-05 is at the 95% cap either way, but the report raises it as a
question rather than silently correcting history.

## Layout

```
psclose.toml          inputs and policy parameters
psclose/              the package (about 2,600 lines)
tests/                22 tests, including the history replay and a synthetic August
docs/                 recognition rules, controller questions, design notes
data/                 the two databases as received
out/2026-07/          the July outputs
```

Design decisions, tradeoffs and what I would do next are in [docs/design.md](docs/design.md).
