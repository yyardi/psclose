# Design notes

## What this is

A small, deterministic pipeline that turns two SQLite files into a month's revenue schedule and
the paper trail behind it. It is meant to be run by a controller's team every month, read by a
reviewer in an afternoon, and changed by editing one TOML file when a policy question is
answered.

## Shape

```
inputs (base + increments)
   -> ledger.assemble          copy, upsert, log            out/<period>/ledger.sqlite
   -> identity.resolve         name -> project              timesheet_resolution
   -> hours.attribute          row -> item (x share)        timesheet_attribution
   -> policy.infer_method      item -> method
   -> recognize.*              method -> cumulative amount
   -> schedule.compute_period  rows, postings, exceptions   (in memory)
   -> schedule.write_period    revenue_schedule, accounting_posting, close_exception, item_policy
   -> rollup, report, narrate  csv, md
```

`compute_period` never touches the schedule or posting tables; `write_period` is the only thing
that does. That split is what makes the backtest possible: it computes a closed period and
compares instead of writing. It is also what makes a rerun safe: writing deletes the period's
rows first, so closing July twice gives the same file. (Attribution of timesheets to items is
persisted as it is computed, since later periods depend on it; it is idempotent and `--redo`
style recomputation is what the backtest uses.)

## Decisions

**A working ledger, not in-place updates.** The inputs are copied and never touched. Each run
produces a self-contained SQLite file with the inputs, the new rows, and the engine's own tables
(resolution, attribution, policy, exceptions, rollup). Anyone with `sqlite3` can audit a close
without Python. The next period can start from this file or from the raw inputs; both give the
same answer and a test proves it.

**Rules inferred from columns, parameters in config.** Nothing in the code names a contract
item. The method comes from `is_ps`, `billing_type`, `service`, and the POC series; the numbers
come from `psclose.toml`. When the controller says "non-billable hours should not count", that
is one line in the config, and the next close reports what changed.

**History is the specification.** The glossary describes the vocabulary, not the client's
practice. Rather than apply textbook percent-of-completion, I replayed six months and adjusted
the rules until they reproduced every posted figure. The two things that would have been easy
to get wrong by reading the glossary alone were the flat 200/h planning rate and the T&M rule
that recognizes non-billable hours. The backtest is in the test suite and in the CLI.

**One known deviation, kept visible.** PX-05's May figure cannot be reproduced without a
per-item exception, and a per-item exception is exactly the kind of thing that rots. The
backtest carries an allowlist with the reason, and the July report raises it as a question.

**Decimal money, float hours.** Amounts are computed with `Decimal` and rounded half-up to the
cent once. Hours are stored as floats in the source and allocation shares as floats in the
ledger; aggregated hours are rounded to a millionth of an hour before any amount is derived,
which keeps 25.37 + 14.63 equal to 40.

**Standard library only.** The data is 5,000 rows. `sqlite3`, `decimal`, `csv` and `tomllib`
cover it, and a reviewer can read every line without knowing a dataframe API. The Anthropic SDK
is an optional extra.

**Claude writes prose, never numbers.** The memo step is optional, reads only the CSVs the
close already wrote, and falls back to a template. Treating the model as a writer rather than a
calculator keeps the close reproducible and auditable, which is the whole point of a close.

**Exceptions as data.** Every finding has a cause code, a severity, the amount at stake, the
ids that prove it, and the question it raises. The report, the memo, the walk table and the
rollup's flag count are all views over that one list. The "straight-line continuation" test the
brief asks for is simply "no review- or action-level finding on this row".

## Tradeoffs I accepted

- The pre-effective rule depends on a free-text timesheet note. It is the only signal in the
  data that separates the two cases, it is configurable, and the report says when it fires.
- Hour allocation for multi-item projects is a guess by rule. The alternative was to refuse to
  close those three projects. A documented default with the swing quantified is more useful
  to a controller than a blank.
- Project-level hours adjustments on a multi-item project are shared by planned hours. The data
  has no such case.
- `project.status` has no history, so a cancellation is dated from its RMA (or the project end
  date). A project cancelled without an RMA would reverse in the period of its end date.
- The CLI closes forward only. Reopening a posted period is a `--replay` that does not exist
  yet; today you would delete the period's rows from a copy of the ledger and rerun.

## What I would do next

1. **Answer intake.** A `decisions.toml` keyed by period and item (allocation ratios, excluded
   hours, overridden percent complete, a manual JE) so the controller's answers are recorded,
   versioned and applied without editing code or data.
2. **Approval state.** Schedule rows written by the engine should be `draft` until the
   controller approves the period; `posted` would then mean posted. The history's status
   vocabulary is kept as is for now because the brief asks for the same shape.
3. **Real source connectors.** The increment format is a SQLite file in the production schema.
   Replacing that with NetSuite and OpenAir exports is a loader change, nothing downstream moves.
4. **FX policy.** A USD view needs a stated rate convention (period end, average, transaction
   date). Today it uses the latest available rate and says when it is stale.
5. **Reopen and restate.** A `reopen --period` that reverses a period into a correction posting
   rather than deleting rows.
6. **Watchers.** Snapshot gaps, unresolved hours and unapplied credits should page someone
   before close week, not appear in the close report.
7. **LLM triage of free text.** Adjustment reasons, RMA notes and timesheet notes are where the
   next surprise will come from. Classifying them against the policy categories, with a human
   confirming, is the next sensible use of the model.
