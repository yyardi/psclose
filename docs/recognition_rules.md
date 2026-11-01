# Recognition rules, and where they come from

The brief gives a schema and a glossary, not a policy. These rules were read off the closed
history (December 2025 through June 2026) and then checked by replaying it: `psclose backtest`
recomputes every period from the raw inputs and diffs against the stored schedule and postings.
Each rule below comes with the query that shows it. Run them against
`data/synthetic_ps_recon_scaled.sqlite`.

## Invariants

**Recognized is the running sum of postings.** All 236 rows match, credits included.

```sql
SELECT COUNT(*) FROM revenue_schedule rs
WHERE ABS(rs.recognized_amount_native - (
  SELECT COALESCE(SUM(amount_native), 0) FROM accounting_posting ap
  WHERE ap.contract_item_id = rs.contract_item_id AND ap.posting_period <= rs.period)) < 0.01;
-- 236
```

**Planned is cumulative billable hours times 200, in the item's currency**, whatever the item's
own contract rate. CI-PX-16 is priced at 272.73/h and CI-PX-13 at 243.24 EUR/h; both plan at
200. Milestone items are floored at the first tranche.

```sql
SELECT rs.contract_item_id, rs.period, rs.planned_amount_native,
       200 * (SELECT SUM(hours) FROM timesheet_entry t
              WHERE t.id LIKE 'TS-' || rs.contract_item_id || '-%' AND t.billable = 1
                AND substr(t.entry_date, 1, 7) <= rs.period) AS hours_x_200
FROM revenue_schedule rs WHERE rs.contract_item_id IN ('CI-PX-16', 'CI-PX-13', 'CI-PX-24');
```

**Status** is `open` until the item recognizes, `held` when recognized is below planned, and
`posted` otherwise. This holds for every June row, including the completed PX-08 (`held`
because its planned value crept past the contract) and the T&M items (`posted` because they
recognize more than they plan).

**An item enters the schedule in the month it was signed**, not the month it became effective.
CI-PX-30 was signed 1 April and effective 1 July; it has rows from April, all `open`.

## Methods

The method is decided per item from columns, not from a list of ids, so a new August item
lands in the right bucket without a code change.

| Order | Signal | Method | Items in the data |
|---|---|---|---|
| 1 | `contract_item.is_ps = 0` | excluded | CI-PX-35, CI-PX-36 (subscriptions; their timesheets say "out of PS scope") |
| 2 | `project.billing_type = 'Time & Materials'` | `tm_hours` | CI-PX-23A, 23B, 24, 25, 26 |
| 3 | `contract_item.service = 'Fixed Fee Delivery'` | `milestone` | CI-PX-09, 10, 11, 12B |
| 4 | delivery-lead POC confirmed every period since the item's first | `poc_snapshot` | CI-PX-13, 14, 15, 16 |
| 5 | otherwise | `hours_poc` | the other 37 |

### Hours against estimate at completion (`hours_poc`)

```
recognized = contract × cumulative billable hours / (planned hours + approved no-charge hours)
             capped at 95% of contract until an acceptance event is confirmed,
             then 100% of contract
```

The denominator moves when `project_hours_adjustment.cr_type` is `internal` or `no_charge`
and the adjustment is effective by period end. Paid change requests do not move it; they come
with their own contract item (PX-12-CR, PX-21-CR, PX-22-CR as child projects; CI-PX-38-CR in
July as a second item on the same project). The odd decimals on held items are this rule:

```sql
-- CI-PX-40 June: 84000 × 220 / (420 + 30 + 25) = 38905.26
SELECT recognized_amount_native FROM revenue_schedule WHERE id = 'SCH-CI-PX-40-2026-06';
```

Acceptance events are `customer_acceptance`, `go_live` and `uat_signoff` with status
`confirmed`. PX-07 (accepted 4 June) and PX-08 (go-live 10 June) went to 100% in June although
PX-07's hours put it at 96.7%.

The 95% cap is visible on CI-PX-01 through 06: May and June recognized exactly 0.95 × contract
while planned kept growing.

### Milestones (`milestone`)

50% of contract from the effective period, memo "tranche 1 per delivery schedule"; "milestone
pending" with a 0.00 posting until a confirmed `milestone_completion` (or `uat_signoff`), then
the remaining 50%, memo "release per milestone completion". All four items took exactly 50%
first:

```sql
SELECT ap.contract_item_id, ROUND(ap.amount_native / ci.contract_amount_native, 2) AS first_share
FROM accounting_posting ap JOIN contract_item ci ON ci.id = ap.contract_item_id
WHERE ci.service = 'Fixed Fee Delivery'
  AND ap.posting_period = (SELECT MIN(posting_period) FROM accounting_posting
                           WHERE contract_item_id = ap.contract_item_id);
-- 0.5 for all four
```

The tranche split is `milestone_tranches` in `psclose.toml`. Nothing in the data states it; it
is inferred from four examples and is a question for the controller if a three-step deal shows up.

### Delivery-lead percent complete (`poc_snapshot`)

```
recognized = contract × poc_pct / 100, from ops_poc_snapshot where source = 'delivery_lead_confirmation'
```

Only PX-13 through PX-16 have a monthly series (January through July). Other projects carry
one-off June confirmations (PX-09, 10, 11, 12, 21) that equal the position the schedule already
held; the engine cross-checks those and reports agreement rather than applying them. If a
series breaks (no August confirmation), the item carries the last percent and raises
`SNAPSHOT_MISSING`.

### Time and materials (`tm_hours`)

```
recognized = cumulative hours (billable and non-billable) × 200
planned    = cumulative billable hours × 200
```

This is the one rule I would not have guessed. CI-PX-24 recognized 44,000 in June on 180
billable and 40 non-billable "internal enablement" hours; 220 × 200 is the only reading that
fits every month for every T&M item. The engine follows it (`tm_count_nonbillable = true`) and
flags the amount each month under `NONBILLABLE_RECOGNIZED`.

### Terminations

A project with `status = 'cancelled'` is reversed in full in the period of its termination RMA
(credit posting, source reference the RMA id, memo "credit issued per contract termination"),
planned frozen, status `held`. PX-27 and PX-28 in June. An RMA on a project that is not
cancelled (RMA-PX-20, -3,000, "unresolved cross-reference to prior SO") is reported as
unapplied, not posted; history did not post it either.

## When recognition starts

An item recognizes from its first period if approved billable hours are being logged against
it, unless those hours carry the note `pre-effective scope start`; then it stays `open` until its
effective date. January hours on items effective 1 February (CI-PX-12A, 23A, 24, 25, 26) were
recognized; April to June hours on CI-PX-29 and CI-PX-30 (effective 1 July) were not. The note
text is `pre_effective_note` in `psclose.toml`. In July those two items go live and their
pre-effective hours count toward percent complete, which the report flags with the amount.

## Attribution of hours to items

June timesheets carry the item in the id and the worker alias (`TS-CI-PX-12A-…`,
`worker-CI-PX-12A-…`). July timesheets carry only the project (`TSJ-PX-12-A-…`, A/B/C being
workers), except PX-38's change-request rows (`worker-PX-38-CR-…`). The engine therefore:

1. puts the row on the project's only PS item when there is one;
2. otherwise on the item whose id appears as a token in the alias or row id (longest match, so
   `PX-38-CR` beats `PX-38`);
3. otherwise splits it across the project's items that are signed, not superseded and not yet
   fully recognized, in proportion to remaining planned hours (`hours_allocation`).

Rule 2 reproduces every June split exactly (CI-PX-12A 340 h / 12B 85 h, and so on). Rule 3
fires for PX-12, PX-21 and PX-23 in July and is the first controller question.

## Things the schema allows that the data never uses

`contract_item.superseded_by_item_id` is always null, `metadata_json` is always `{}`,
`rma_event.replacement_sales_order_id` is always null, `accounting_book` is always 1 and every
posting is `posted`. The engine respects `superseded_by_item_id` (excludes such items from
splits) and ignores the rest.
