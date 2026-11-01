# July 2026 revenue close

Period end 2026-07-31. Prior closed period 2026-06. Sources: synthetic_ps_recon_scaled.sqlite, july_increment.sqlite.

48 contract items on the schedule (17 held, 31 posted). 21 are a plain continuation of 2026-06; 27 moved for a reason listed below. 10 items need an answer before posting, 27 are for review, 17 are noted for completeness.

## Totals

| Currency | Items | Contract value | Recognized to date | Recognized in 2026-07 | Planned to date |
| --- | ---: | ---: | ---: | ---: | ---: |
| CAD | 1 | 92,000.00 | 52,800.00 | 6,800.00 | 52,800.00 |
| EUR | 2 | 158,000.00 | 105,055.48 | 11,252.74 | 79,400.00 |
| GBP | 2 | 136,000.00 | 76,121.95 | 9,975.61 | 79,400.00 |
| USD | 43 | 2,954,000.00 | 2,078,642.36 | 242,669.97 | 2,036,000.00 |

USD view at the latest available rates: 2,327,087.94 recognized to date, 272,424.20 in 2026-07. Rates for CAD, EUR, GBP are carried from the prior month end; see exceptions.

## What moved, and why

Grouped by cause. Amounts are the effect on the period in the item's own currency. Items marked *action* may change once the controller answers the question.

### Needs an answer

**No exchange rate for the period; prior rate used for USD views** (`FX_RATE_STALE`)

- ledger: No CAD rate for 2026-07; USD views use 0.74 from 2026-06-30.
  Question: Please provide the CAD/USD rate for 2026-07-31.
- ledger: No EUR rate for 2026-07; USD views use 1.08 from 2026-06-30.
  Question: Please provide the EUR/USD rate for 2026-07-31.
- ledger: No GBP rate for 2026-07; USD views use 1.26 from 2026-06-30.
  Question: Please provide the GBP/USD rate for 2026-07-31.

**Hours split across items by rule, not by the timesheet** (`HOURS_ALLOCATED`)

- PX-12 / CI-PX-12A: 109 of 109 billable hours on PX-12 were placed on CI-PX-12A because CI-PX-12B is already fully recognized; the 2026-07 timesheets name the project but not the item. A plain split by planned hours (500:300) would give CI-PX-12A 68.12 h and move its recognized revenue by -8,175.00 USD. **21,800.00 USD**.
  Question: How should PX-12 hours be split between CI-PX-12A and CI-PX-12B?
- PX-21 / CI-PX-21A: 25.37 of 40 billable hours on PX-21 were placed on CI-PX-21A in proportion to the hours each item still has to deliver; the 2026-07 timesheets name the project but not the item. A plain split by planned hours (300:150) would give CI-PX-21A 26.67 h and move its recognized revenue by 260.16 USD. **5,073.17 USD**.
  Question: How should PX-21 hours be split between CI-PX-21A and CI-PX-21B?
- PX-21 / CI-PX-21B: 14.63 of 40 billable hours on PX-21 were placed on CI-PX-21B in proportion to the hours each item still has to deliver; the 2026-07 timesheets name the project but not the item. A plain split by planned hours (300:150) would give CI-PX-21B 13.33 h and move its recognized revenue by -260.16 USD. **2,926.83 USD**.
  Question: How should PX-21 hours be split between CI-PX-21A and CI-PX-21B?
- PX-23 / CI-PX-23A: 16.69 of 26 billable hours on PX-23 were placed on CI-PX-23A in proportion to the hours each item still has to deliver; the 2026-07 timesheets name the project but not the item. A plain split by planned hours (320:160) would give CI-PX-23A 17.33 h and move its recognized revenue by 128.15 USD. **4,365.76 USD**.
  Question: How should PX-23 hours be split between CI-PX-23A and CI-PX-23B?
- PX-23 / CI-PX-23B: 9.31 of 26 billable hours on PX-23 were placed on CI-PX-23B in proportion to the hours each item still has to deliver; the 2026-07 timesheets name the project but not the item. A plain split by planned hours (320:160) would give CI-PX-23B 8.67 h and move its recognized revenue by -128.15 USD. **2,434.24 USD**.
  Question: How should PX-23 hours be split between CI-PX-23A and CI-PX-23B?

**Approved sales order with no project and no contract item** (`ORPHAN_SALES_ORDER`)

- ledger: SO-PX-20-ORPHAN (NS-PX-20-ORPHAN) for customer CU20 is approved for 15,000.00 USD with no project and no contract item; nothing is scheduled for it. **15,000.00 USD**.
  Question: Is SO-PX-20-ORPHAN a real order that needs a contract item, or a duplicate to void?

**Return or credit memo not reflected in the schedule** (`UNAPPLIED_RMA`)

- PX-20: RMA-PX-20 (RET-PX20, 2026-06-24, 'partial scope return') for -3,000.00 USD has no matching credit in the schedule (credit memo: CM-PX20; note: unresolved cross-reference to prior SO). **-3,000.00 USD**.
  Question: Should RMA-PX-20 reduce recognized revenue on PX-20, and against which item?

### For review

**Acceptance confirmed; remaining contract value recognized** (`ACCEPTANCE_RELEASE`)

- PX-02 / CI-PX-02: Bramwell Logistics | Core Delivery: acceptance confirmed 2026-07-09; CI-PX-02 moves from 83,600.00 USD to the full 88,000.00 USD. **4,400.00 USD**.

**Item became effective; first revenue recognized** (`FIRST_RECOGNITION`)

- PX-29 / CI-PX-29: CI-PX-29 became effective 2026-07-01; first recognition 9,400.00 USD on 47 cumulative billable hours. **9,400.00 USD**.
- PX-30 / CI-PX-30: CI-PX-30 became effective 2026-07-01; first recognition 7,400.00 USD on 37 cumulative billable hours. **7,400.00 USD**.

**Prior period as posted differs from the rules as configured** (`HISTORY_INCONSISTENCY`)

- PX-05 / CI-PX-05: 2026-06 was posted at 79,800.00 USD for CI-PX-05; the rules as configured give 78,845.45. Left as posted; the current period is computed cumulatively so the difference does not compound unless the cause persists. **-954.55 USD**.
  Question: Was CI-PX-05 in 2026-06 meant to follow the standard rule, or was the posted figure a deliberate override?

**Logged hours exceed the estimate at completion** (`HOURS_OVER_PLAN`)

- PX-01 / CI-PX-01: CI-PX-01 has 539 billable hours against an estimate of 500; planned value 107,800.00 USD now exceeds the 100,000.00 USD contract. **7,800.00 USD**.
  Question: Is a change order or a revised estimate expected on CI-PX-01 (539 h against 500)?
- PX-03 / CI-PX-03: CI-PX-03 has 666 billable hours against an estimate of 600; planned value 133,200.00 USD now exceeds the 120,000.00 USD contract. **13,200.00 USD**.
  Question: Is a change order or a revised estimate expected on CI-PX-03 (666 h against 600)?
- PX-04 / CI-PX-04: CI-PX-04 has 372 billable hours against an estimate of 360; planned value 74,400.00 USD now exceeds the 72,000.00 USD contract. **2,400.00 USD**.
  Question: Is a change order or a revised estimate expected on CI-PX-04 (372 h against 360)?
- PX-06 / CI-PX-06: CI-PX-06 has 617 billable hours against an estimate of 560; planned value 123,400.00 USD now exceeds the 112,000.00 USD contract. **11,400.00 USD**.
  Question: Is a change order or a revised estimate expected on CI-PX-06 (617 h against 560)?
- PX-12-CR / CI-PX-12-CR: CI-PX-12-CR has 112 billable hours against an estimate of 100; planned value 22,400.00 USD now exceeds the 20,000.00 USD contract. **2,400.00 USD**.
  Question: Is a change order or a revised estimate expected on CI-PX-12-CR (112 h against 100)?
- PX-21-CR / CI-PX-21-CR: CI-PX-21-CR has 82 billable hours against an estimate of 80; planned value 16,400.00 USD now exceeds the 16,000.00 USD contract. **400.00 USD**.
  Question: Is a change order or a revised estimate expected on CI-PX-21-CR (82 h against 80)?
- PX-22-CR / CI-PX-22-CR: CI-PX-22-CR has 63 billable hours against an estimate of 60; planned value 12,600.00 USD now exceeds the 12,000.00 USD contract. **600.00 USD**.
  Question: Is a change order or a revised estimate expected on CI-PX-22-CR (63 h against 60)?

**Milestone confirmed; next tranche recognized** (`MILESTONE_RELEASE`)

- PX-09 / CI-PX-09: Ironwood Freight | Platform Build: milestone confirmed; CI-PX-09 releases tranche 2 of 2, 40,000.00 USD. **40,000.00 USD**.
- PX-10 / CI-PX-10: Juniper Analytics | Platform Build: milestone confirmed; CI-PX-10 releases tranche 2 of 2, 30,000.00 USD. **30,000.00 USD**.

**Contract item appears on the schedule for the first time** (`NEW_ITEM`)

- PX-38 / CI-PX-38-CR: CI-PX-38-CR (PX-38 paid change request) is new this period: 10,000.00 USD contract, 50 planned hours, effective 2026-07-15, method fixed fee, hours against estimate at completion. **1,600.00 USD**.
- PX-43 / CI-PX-43: CI-PX-43 (Thistledown Analytics core delivery) is new this period: 60,000.00 USD contract, 300 planned hours, effective 2026-07-06, method fixed fee, hours against estimate at completion. **7,000.00 USD**.

**Non-billable hours recognized at the standard rate** (`NONBILLABLE_RECOGNIZED`)

- PX-23 / CI-PX-23A: 5.14 non-billable hours on CI-PX-23A were recognized at 200/h (1,027.24 USD), matching how prior periods were posted. **1,027.24 USD**.
  Question: Should non-billable enablement hours on T&M engagements keep being recognized as revenue?
- PX-23 / CI-PX-23B: 2.86 non-billable hours on CI-PX-23B were recognized at 200/h (572.76 USD), matching how prior periods were posted. **572.76 USD**.
  Question: Should non-billable enablement hours on T&M engagements keep being recognized as revenue?
- PX-24 / CI-PX-24: 12 non-billable hours on CI-PX-24 were recognized at 200/h (2,400.00 USD), matching how prior periods were posted. **2,400.00 USD**.
  Question: Should non-billable enablement hours on T&M engagements keep being recognized as revenue?
- PX-25 / CI-PX-25: 8 non-billable hours on CI-PX-25 were recognized at 200/h (1,600.00 USD), matching how prior periods were posted. **1,600.00 USD**.
  Question: Should non-billable enablement hours on T&M engagements keep being recognized as revenue?
- PX-26 / CI-PX-26: 9 non-billable hours on CI-PX-26 were recognized at 200/h (1,800.00 USD), matching how prior periods were posted. **1,800.00 USD**.
  Question: Should non-billable enablement hours on T&M engagements keep being recognized as revenue?

**Delivery lead revised percent complete** (`POC_SNAPSHOT_UPDATE`)

- PX-13 / CI-PX-13: Meridian Retail | Modernization: delivery lead confirms 74.5% complete (was 68.0%); CI-PX-13 recognizes 5,850.00 EUR this period. **5,850.00 EUR**.
- PX-14 / CI-PX-14: Nightingale Health Systems | Modernization: delivery lead confirms 68.0% complete (was 62.0%); CI-PX-14 recognizes 6,000.00 USD this period. **6,000.00 USD**.
- PX-15 / CI-PX-15: Obsidian Capital | Modernization: delivery lead confirms 71.0% complete (was 65.0%); CI-PX-15 recognizes 4,800.00 USD this period. **4,800.00 USD**.
- PX-16 / CI-PX-16: Pinnacle Foods | Modernization: delivery lead confirms 63.0% complete (was 57.0%); CI-PX-16 recognizes 7,200.00 USD this period. **7,200.00 USD**.

**Hours logged before the effective date count toward completion** (`PRE_EFFECTIVE_HOURS_COUNTED`)

- PX-29 / CI-PX-29: 47 hours on CI-PX-29 were tagged as logged before the scope was live; they count toward percent complete, as they did toward planned value in prior periods. 12 of this period's hours are still tagged 'pre-effective' although the item is live from 2026-07-01. **9,400.00 USD**.
  Question: Should hours logged before the effective date count toward completion, or be excluded?
- PX-30 / CI-PX-30: 37 hours on CI-PX-30 were tagged as logged before the scope was live; they count toward percent complete, as they did toward planned value in prior periods. 9 of this period's hours are still tagged 'pre-effective' although the item is live from 2026-07-01. **7,400.00 USD**.
  Question: Should hours logged before the effective date count toward completion, or be excluded?

**Timesheets with no project link matched by name** (`UNMATCHED_HOURS_RESOLVED`)

- PX-18: 29 hours reported as 'Redwood Transit Core' carry no project id and were linked to PX-18 by alias (openair project link pending). Included in PX-18's hours, as in prior periods.
  Question: Can the OpenAir link for PX-18 be fixed so these rows arrive with a project id?

### Noted

**Recognition held at the pre-acceptance cap** (`CAP_BINDING`)

- PX-01 / CI-PX-01: CI-PX-01 is 107.8% complete by hours (539 of 500); recognition held at 95% (95,000.00 USD) pending acceptance. **12,800.00 USD**.
- PX-03 / CI-PX-03: CI-PX-03 is 111.0% complete by hours (666 of 600); recognition held at 95% (114,000.00 USD) pending acceptance. **19,200.00 USD**.
- PX-04 / CI-PX-04: CI-PX-04 is 103.3% complete by hours (372 of 360); recognition held at 95% (68,400.00 USD) pending acceptance. **6,000.00 USD**.
- PX-05 / CI-PX-05: CI-PX-05 is 98.6% complete by hours (434 of 440); recognition held at 95% (79,800.00 USD) pending acceptance. **3,054.55 USD**.
- PX-06 / CI-PX-06: CI-PX-06 is 110.2% complete by hours (617 of 560); recognition held at 95% (106,400.00 USD) pending acceptance. **17,000.00 USD**.
- PX-12-CR / CI-PX-12-CR: CI-PX-12-CR is 112.0% complete by hours (112 of 100); recognition held at 95% (19,000.00 USD) pending acceptance. **3,400.00 USD**.
- PX-21-CR / CI-PX-21-CR: CI-PX-21-CR is 102.5% complete by hours (82 of 80); recognition held at 95% (15,200.00 USD) pending acceptance. **1,200.00 USD**.
- PX-22-CR / CI-PX-22-CR: CI-PX-22-CR is 105.0% complete by hours (63 of 60); recognition held at 95% (11,400.00 USD) pending acceptance. **1,200.00 USD**.

**Fully recognized item carried with no movement** (`COMPLETED_CARRYFORWARD`)

- PX-07 / CI-PX-07: CI-PX-07 is fully recognized; no hours in 2026-07.
- PX-08 / CI-PX-08: CI-PX-08 is fully recognized; no hours in 2026-07.
- PX-12 / CI-PX-12B: CI-PX-12B is fully recognized; no hours in 2026-07.

**Hours on items outside the PS schedule; excluded** (`NON_PS_HOURS`)

- PX-35: 5 hours on PX-35 (out of PS scope) sit outside the PS schedule.
- PX-36: 5 hours on PX-36 (out of PS scope) sit outside the PS schedule.

**Paid change request logged; base item estimate unchanged** (`PAID_ADJUSTMENT_NOTED`)

- PX-38 / CI-PX-38: Paid change request on PX-38 (ADJ-PX-38-JUL-01) is priced on its own contract item; the estimate at completion for CI-PX-38 stays at 500 hours.

**Sales order linked to its project by alias only** (`SO_PROJECT_LINK_MISSING`)

- PX-19: SO-PX-19 has no project id; linked to PX-19 through its NetSuite hint.

**Terminated item carried with no movement** (`TERMINATED_CARRYFORWARD`)

- PX-27 / CI-PX-27: CI-PX-27 terminated 2026-06-22; no movement.
- PX-28 / CI-PX-28: CI-PX-28 terminated 2026-06-27; no movement.

## Project rollup

| Project | Name | Billing | Cur | Items | Contract | Rec. 2026-06 | Rec. 2026-07 | Period | Planned | % rec. | Bill. h | Rec. USD | Flags |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PX-01 | Aurelia Health \| Core Delivery | Fixed Fee | USD | 1 | 100,000.00 | 95,000.00 | 95,000.00 | 0.00 | 107,800.00 | 95.0% | 29 | 95,000.00 | 1 |
| PX-02 | Bramwell Logistics \| Core Delivery | Fixed Fee | USD | 1 | 88,000.00 | 83,600.00 | 88,000.00 | 4,400.00 | 91,600.00 | 100.0% | 8 | 88,000.00 | 1 |
| PX-03 | Cascade Robotics \| Core Delivery | Fixed Fee | USD | 1 | 120,000.00 | 114,000.00 | 114,000.00 | 0.00 | 133,200.00 | 95.0% | 46 | 114,000.00 | 1 |
| PX-04 | Driftwood Media \| Core Delivery | Fixed Fee | USD | 1 | 72,000.00 | 68,400.00 | 68,400.00 | 0.00 | 74,400.00 | 95.0% | 17 | 68,400.00 | 1 |
| PX-05 | Ember Insurance \| Core Delivery | Fixed Fee | USD | 1 | 84,000.00 | 79,800.00 | 79,800.00 | 0.00 | 86,800.00 | 95.0% | 21 | 79,800.00 | 1 |
| PX-06 | Falcon Grid Utilities \| Core Delivery | Fixed Fee | USD | 1 | 112,000.00 | 106,400.00 | 106,400.00 | 0.00 | 123,400.00 | 95.0% | 52 | 106,400.00 | 1 |
| PX-07 | Granite Peak Bank \| Rollout | Fixed Fee | USD | 1 | 90,000.00 | 90,000.00 | 90,000.00 | 0.00 | 87,000.00 | 100.0% | 0 | 90,000.00 | 0 |
| PX-08 | Halcyon Biotech \| Rollout | Fixed Fee | USD | 1 | 76,000.00 | 76,000.00 | 76,000.00 | 0.00 | 76,600.00 | 100.0% | 0 | 76,000.00 | 0 |
| PX-09 | Ironwood Freight \| Platform Build | Fixed Fee | USD | 1 | 80,000.00 | 40,000.00 | 80,000.00 | 40,000.00 | 65,800.00 | 100.0% | 69 | 80,000.00 | 1 |
| PX-10 | Juniper Analytics \| Platform Build | Fixed Fee | USD | 1 | 60,000.00 | 30,000.00 | 60,000.00 | 30,000.00 | 49,400.00 | 100.0% | 52 | 60,000.00 | 1 |
| PX-11 | Kestrel Aerospace \| Platform Build | Fixed Fee | USD | 1 | 70,000.00 | 70,000.00 | 70,000.00 | 0.00 | 51,200.00 | 100.0% | 46 | 70,000.00 | 0 |
| PX-12 | Lattice Semiconductor \| Core Rollout | Fixed Fee | USD | 2 | 150,000.00 | 118,000.00 | 139,800.00 | 21,800.00 | 114,800.00 | 93.2% | 109 | 139,800.00 | 1 |
| PX-12-CR | Lattice Semiconductor \| CR1 | Fixed Fee | USD | 1 | 20,000.00 | 19,000.00 | 19,000.00 | 0.00 | 22,400.00 | 95.0% | 17 | 19,000.00 | 1 |
| PX-13 | Meridian Retail \| Modernization | Fixed Fee | EUR | 1 | 90,000.00 | 61,200.00 | 67,050.00 | 5,850.00 | 38,600.00 | 74.5% | 23 | 72,414.00 | 1 |
| PX-14 | Nightingale Health Systems \| Modernization | Fixed Fee | USD | 1 | 100,000.00 | 62,000.00 | 68,000.00 | 6,000.00 | 46,800.00 | 68.0% | 29 | 68,000.00 | 1 |
| PX-15 | Obsidian Capital \| Modernization | Fixed Fee | USD | 1 | 80,000.00 | 52,000.00 | 56,800.00 | 4,800.00 | 34,400.00 | 71.0% | 17 | 56,800.00 | 1 |
| PX-16 | Pinnacle Foods \| Modernization | Fixed Fee | USD | 1 | 120,000.00 | 68,400.00 | 75,600.00 | 7,200.00 | 54,800.00 | 63.0% | 34 | 75,600.00 | 1 |
| PX-17 | Quarrystone Insurance \| Core Rollout | Fixed Fee | USD | 1 | 80,000.00 | 42,000.00 | 48,800.00 | 6,800.00 | 48,800.00 | 61.0% | 34 | 48,800.00 | 0 |
| PX-18 | Redwood Transit \| Core Services | Fixed Fee | USD | 1 | 76,000.00 | 39,000.00 | 44,800.00 | 5,800.00 | 44,800.00 | 58.9% | 29 | 44,800.00 | 1 |
| PX-19 | Sable Energy \| Transition | Fixed Fee | USD | 1 | 84,000.00 | 43,000.00 | 48,800.00 | 5,800.00 | 48,800.00 | 58.1% | 29 | 48,800.00 | 0 |
| PX-20 | Tundra Apparel \| Legacy Services | Fixed Fee | USD | 1 | 60,000.00 | 30,000.00 | 34,600.00 | 4,600.00 | 34,600.00 | 57.7% | 23 | 34,600.00 | 1 |
| PX-21 | Umbra Studios \| Platform Rebuild | Fixed Fee | USD | 2 | 90,000.00 | 49,000.00 | 57,000.00 | 8,000.00 | 57,000.00 | 63.3% | 40 | 57,000.00 | 2 |
| PX-21-CR | Umbra Studios \| CR1 | Fixed Fee | USD | 1 | 16,000.00 | 13,000.00 | 15,200.00 | 2,200.00 | 16,400.00 | 95.0% | 17 | 15,200.00 | 1 |
| PX-22 | Vellum Publishing \| Content Migration | Fixed Fee | USD | 1 | 70,000.00 | 33,636.36 | 38,909.09 | 5,272.73 | 42,800.00 | 55.6% | 29 | 38,909.09 | 0 |
| PX-22-CR | Vellum Publishing \| CR1 | Fixed Fee | USD | 1 | 12,000.00 | 9,600.00 | 11,400.00 | 1,800.00 | 12,600.00 | 95.0% | 15 | 11,400.00 | 1 |
| PX-23 | Wrenfield University \| Advisory Program | Time & Materials | USD | 2 | 96,000.00 | 52,000.00 | 58,800.00 | 6,800.00 | 49,800.00 | 61.2% | 26 | 58,800.00 | 4 |
| PX-24 | Xylo Manufacturing \| Advisory Program | Time & Materials | USD | 1 | 80,000.00 | 44,000.00 | 51,000.00 | 7,000.00 | 40,600.00 | 63.8% | 23 | 51,000.00 | 1 |
| PX-25 | Yarrow Agritech \| Advisory Program | Time & Materials | USD | 1 | 72,000.00 | 38,000.00 | 43,800.00 | 5,800.00 | 35,800.00 | 60.8% | 21 | 43,800.00 | 1 |
| PX-26 | Zenith Telecom \| Advisory Program | Time & Materials | USD | 1 | 88,000.00 | 46,000.00 | 52,800.00 | 6,800.00 | 45,400.00 | 60.0% | 25 | 52,800.00 | 1 |
| PX-27 | Aldergate Public Works \| Pilot Engagement | Fixed Fee | USD | 1 | 50,000.00 | 0.00 | 0.00 | 0.00 | 20,000.00 | 0.0% | 0 | 0.00 | 0 |
| PX-28 | Briarwood Hospitality \| Pilot Engagement | Fixed Fee | USD | 1 | 60,000.00 | 0.00 | 0.00 | 0.00 | 22,000.00 | 0.0% | 0 | 0.00 | 0 |
| PX-29 | Copperline Rail \| Expansion Scope | Fixed Fee | USD | 1 | 40,000.00 | 0.00 | 9,400.00 | 9,400.00 | 9,400.00 | 23.5% | 12 | 9,400.00 | 2 |
| PX-30 | Dovetail Furniture \| Expansion Scope | Fixed Fee | USD | 1 | 36,000.00 | 0.00 | 7,400.00 | 7,400.00 | 7,400.00 | 20.6% | 9 | 7,400.00 | 2 |
| PX-31 | Elmswood Legal \| Core Delivery | Fixed Fee | EUR | 1 | 68,000.00 | 32,602.74 | 38,005.48 | 5,402.74 | 40,800.00 | 55.9% | 29 | 41,045.92 | 0 |
| PX-32 | Fernbank Municipal \| Core Delivery | Fixed Fee | CAD | 1 | 92,000.00 | 46,000.00 | 52,800.00 | 6,800.00 | 52,800.00 | 57.4% | 34 | 39,072.00 | 0 |
| PX-33 | Gantry Shipping \| Core Delivery | Fixed Fee | GBP | 1 | 76,000.00 | 36,146.34 | 41,521.95 | 5,375.61 | 44,800.00 | 54.6% | 29 | 52,317.66 | 0 |
| PX-34 | Heathfield Pharma \| Core Delivery | Fixed Fee | GBP | 1 | 60,000.00 | 30,000.00 | 34,600.00 | 4,600.00 | 34,600.00 | 57.7% | 23 | 43,596.00 | 0 |
| PX-37 | Kelso Marine \| Core Delivery | Fixed Fee | USD | 1 | 64,000.00 | 33,000.00 | 38,800.00 | 5,800.00 | 38,800.00 | 60.6% | 29 | 38,800.00 | 0 |
| PX-38 | Larkspur Foods \| Core Delivery | Fixed Fee | USD | 2 | 110,000.00 | 51,000.00 | 60,600.00 | 9,600.00 | 60,600.00 | 55.1% | 48 | 60,600.00 | 1 |
| PX-39 | Mistport Utilities \| Core Delivery | Fixed Fee | USD | 1 | 56,000.00 | 29,000.00 | 33,600.00 | 4,600.00 | 33,600.00 | 60.0% | 23 | 33,600.00 | 0 |
| PX-40 | Norwich Data Systems \| Core Delivery | Fixed Fee | USD | 1 | 84,000.00 | 38,905.26 | 44,917.89 | 6,012.63 | 50,800.00 | 53.5% | 34 | 44,917.89 | 0 |
| PX-41 | Orinda Wealth Partners \| Core Delivery | Fixed Fee | USD | 1 | 52,000.00 | 27,000.00 | 31,600.00 | 4,600.00 | 31,600.00 | 60.8% | 23 | 31,600.00 | 0 |
| PX-42 | Pemberton Steelworks \| Core Delivery | Fixed Fee | USD | 1 | 96,000.00 | 45,230.77 | 52,615.38 | 7,384.61 | 57,000.00 | 54.8% | 40 | 52,615.38 | 0 |
| PX-43 | Thistledown Analytics \| Core Delivery | Fixed Fee | USD | 1 | 60,000.00 | 0.00 | 7,000.00 | 7,000.00 | 7,000.00 | 11.7% | 35 | 7,000.00 | 1 |
| PX-12 | Lattice Semiconductor \| Core Rollout (incl. change orders) | Fixed Fee | USD | 3 | 170,000.00 | 137,000.00 | 158,800.00 | 21,800.00 | 137,200.00 | 93.4% | 126 | 158,800.00 | 2 |
| PX-21 | Umbra Studios \| Platform Rebuild (incl. change orders) | Fixed Fee | USD | 3 | 106,000.00 | 62,000.00 | 72,200.00 | 10,200.00 | 73,400.00 | 68.1% | 57 | 72,200.00 | 3 |
| PX-22 | Vellum Publishing \| Content Migration (incl. change orders) | Fixed Fee | USD | 2 | 82,000.00 | 43,236.36 | 50,309.09 | 7,072.73 | 55,400.00 | 61.4% | 44 | 50,309.09 | 1 |

## Schedule walk

Every row of the 2026-07 schedule, cumulative as in the ledger, with the period movement next to 2026-06's movement so a straight-line month is visible at a glance.

| Item | Project | Method | Status | Cur | Rec. 2026-06 | Rec. 2026-07 | 2026-07 move | 2026-06 move | Planned | % rec. | Bill. h | Why |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CI-PX-01 | PX-01 | fixed fee | held | USD | 95,000.00 | 95,000.00 | 0.00 | 0.00 | 107,800.00 | 95.0% | 29 | Logged hours exceed the estimate at completion |
| CI-PX-02 | PX-02 | fixed fee | held | USD | 83,600.00 | 88,000.00 | 4,400.00 | 0.00 | 91,600.00 | 100.0% | 8 | Acceptance confirmed; remaining contract value recognized |
| CI-PX-03 | PX-03 | fixed fee | held | USD | 114,000.00 | 114,000.00 | 0.00 | 0.00 | 133,200.00 | 95.0% | 46 | Logged hours exceed the estimate at completion |
| CI-PX-04 | PX-04 | fixed fee | held | USD | 68,400.00 | 68,400.00 | 0.00 | 400.00 | 74,400.00 | 95.0% | 17 | Logged hours exceed the estimate at completion |
| CI-PX-05 | PX-05 | fixed fee | held | USD | 79,800.00 | 79,800.00 | 0.00 | 800.00 | 86,800.00 | 95.0% | 21 | Prior period as posted differs from the rules as configured |
| CI-PX-06 | PX-06 | fixed fee | held | USD | 106,400.00 | 106,400.00 | 0.00 | 2,400.00 | 123,400.00 | 95.0% | 52 | Logged hours exceed the estimate at completion |
| CI-PX-07 | PX-07 | fixed fee | posted | USD | 90,000.00 | 90,000.00 | 0.00 | 4,500.00 | 87,000.00 | 100.0% | 0 | Fully recognized item carried with no movement |
| CI-PX-08 | PX-08 | fixed fee | held | USD | 76,000.00 | 76,000.00 | 0.00 | 3,800.00 | 76,600.00 | 100.0% | 0 | Fully recognized item carried with no movement |
| CI-PX-09 | PX-09 | fixed fee | posted | USD | 40,000.00 | 80,000.00 | 40,000.00 | 0.00 | 65,800.00 | 100.0% | 69 | Milestone confirmed; next tranche recognized |
| CI-PX-10 | PX-10 | fixed fee | posted | USD | 30,000.00 | 60,000.00 | 30,000.00 | 0.00 | 49,400.00 | 100.0% | 52 | Milestone confirmed; next tranche recognized |
| CI-PX-11 | PX-11 | fixed fee | posted | USD | 70,000.00 | 70,000.00 | 0.00 | 35,000.00 | 51,200.00 | 100.0% | 46 | Milestone pending; tranche 1 held |
| CI-PX-12-CR | PX-12-CR | fixed fee | held | USD | 19,000.00 | 19,000.00 | 0.00 | 3,000.00 | 22,400.00 | 95.0% | 17 | Logged hours exceed the estimate at completion |
| CI-PX-12A | PX-12 | fixed fee | posted | USD | 68,000.00 | 89,800.00 | 21,800.00 | 8,000.00 | 89,800.00 | 89.8% | 109 | Hours split across items by rule, not by the timesheet |
| CI-PX-12B | PX-12 | fixed fee | posted | USD | 50,000.00 | 50,000.00 | 0.00 | 25,000.00 | 25,000.00 | 100.0% | 0 | Fully recognized item carried with no movement |
| CI-PX-13 | PX-13 | fixed fee | posted | EUR | 61,200.00 | 67,050.00 | 5,850.00 | 7,200.00 | 38,600.00 | 74.5% | 23 | Delivery lead revised percent complete |
| CI-PX-14 | PX-14 | fixed fee | posted | USD | 62,000.00 | 68,000.00 | 6,000.00 | 7,000.00 | 46,800.00 | 68.0% | 29 | Delivery lead revised percent complete |
| CI-PX-15 | PX-15 | fixed fee | posted | USD | 52,000.00 | 56,800.00 | 4,800.00 | 5,600.00 | 34,400.00 | 71.0% | 17 | Delivery lead revised percent complete |
| CI-PX-16 | PX-16 | fixed fee | posted | USD | 68,400.00 | 75,600.00 | 7,200.00 | 8,400.00 | 54,800.00 | 63.0% | 34 | Delivery lead revised percent complete |
| CI-PX-17 | PX-17 | fixed fee | posted | USD | 42,000.00 | 48,800.00 | 6,800.00 | 6,000.00 | 48,800.00 | 61.0% | 34 | 34 billable h against plan |
| CI-PX-18 | PX-18 | fixed fee | posted | USD | 39,000.00 | 44,800.00 | 5,800.00 | 5,000.00 | 44,800.00 | 58.9% | 29 | 29 billable h against plan |
| CI-PX-19 | PX-19 | fixed fee | posted | USD | 43,000.00 | 48,800.00 | 5,800.00 | 5,000.00 | 48,800.00 | 58.1% | 29 | 29 billable h against plan |
| CI-PX-20 | PX-20 | fixed fee | posted | USD | 30,000.00 | 34,600.00 | 4,600.00 | 4,000.00 | 34,600.00 | 57.7% | 23 | 23 billable h against plan |
| CI-PX-21-CR | PX-21-CR | fixed fee | held | USD | 13,000.00 | 15,200.00 | 2,200.00 | 3,000.00 | 16,400.00 | 95.0% | 17 | Logged hours exceed the estimate at completion |
| CI-PX-21A | PX-21 | fixed fee | posted | USD | 34,000.00 | 39,073.17 | 5,073.17 | 4,000.00 | 39,073.17 | 65.1% | 25.37 | Hours split across items by rule, not by the timesheet |
| CI-PX-21B | PX-21 | fixed fee | posted | USD | 15,000.00 | 17,926.83 | 2,926.83 | 3,000.00 | 17,926.83 | 59.8% | 14.63 | Hours split across items by rule, not by the timesheet |
| CI-PX-22 | PX-22 | fixed fee | held | USD | 33,636.36 | 38,909.09 | 5,272.73 | 4,545.45 | 42,800.00 | 55.6% | 29 | 29 billable h against plan |
| CI-PX-22-CR | PX-22-CR | fixed fee | held | USD | 9,600.00 | 11,400.00 | 1,800.00 | 2,600.00 | 12,600.00 | 95.0% | 15 | Logged hours exceed the estimate at completion |
| CI-PX-23A | PX-23 | time and materials | posted | USD | 36,000.00 | 40,365.76 | 4,365.76 | 4,000.00 | 34,338.52 | 63.1% | 16.69 | Hours split across items by rule, not by the timesheet; Non-billable hours recognized at the standard rate |
| CI-PX-23B | PX-23 | time and materials | posted | USD | 16,000.00 | 18,434.24 | 2,434.24 | 2,000.00 | 15,461.48 | 57.6% | 9.31 | Hours split across items by rule, not by the timesheet; Non-billable hours recognized at the standard rate |
| CI-PX-24 | PX-24 | time and materials | posted | USD | 44,000.00 | 51,000.00 | 7,000.00 | 6,000.00 | 40,600.00 | 63.8% | 23 | Non-billable hours recognized at the standard rate |
| CI-PX-25 | PX-25 | time and materials | posted | USD | 38,000.00 | 43,800.00 | 5,800.00 | 5,000.00 | 35,800.00 | 60.8% | 21 | Non-billable hours recognized at the standard rate |
| CI-PX-26 | PX-26 | time and materials | posted | USD | 46,000.00 | 52,800.00 | 6,800.00 | 6,000.00 | 45,400.00 | 60.0% | 25 | Non-billable hours recognized at the standard rate |
| CI-PX-27 | PX-27 | fixed fee | held | USD | 0.00 | 0.00 | 0.00 | -20,000.00 | 20,000.00 | 0.0% | 0 | Terminated item carried with no movement |
| CI-PX-28 | PX-28 | fixed fee | held | USD | 0.00 | 0.00 | 0.00 | -22,000.00 | 22,000.00 | 0.0% | 0 | Terminated item carried with no movement |
| CI-PX-29 | PX-29 | fixed fee | posted | USD | 0.00 | 9,400.00 | 9,400.00 | 0.00 | 9,400.00 | 23.5% | 12 | Item became effective; first revenue recognized; Hours logged before the effective date count toward completion |
| CI-PX-30 | PX-30 | fixed fee | posted | USD | 0.00 | 7,400.00 | 7,400.00 | 0.00 | 7,400.00 | 20.6% | 9 | Item became effective; first revenue recognized; Hours logged before the effective date count toward completion |
| CI-PX-31 | PX-31 | fixed fee | held | EUR | 32,602.74 | 38,005.48 | 5,402.74 | 4,657.53 | 40,800.00 | 55.9% | 29 | 29 billable h against plan |
| CI-PX-32 | PX-32 | fixed fee | posted | CAD | 46,000.00 | 52,800.00 | 6,800.00 | 6,000.00 | 52,800.00 | 57.4% | 34 | 34 billable h against plan |
| CI-PX-33 | PX-33 | fixed fee | held | GBP | 36,146.34 | 41,521.95 | 5,375.61 | 4,634.14 | 44,800.00 | 54.6% | 29 | 29 billable h against plan |
| CI-PX-34 | PX-34 | fixed fee | posted | GBP | 30,000.00 | 34,600.00 | 4,600.00 | 4,000.00 | 34,600.00 | 57.7% | 23 | 23 billable h against plan |
| CI-PX-37 | PX-37 | fixed fee | posted | USD | 33,000.00 | 38,800.00 | 5,800.00 | 5,000.00 | 38,800.00 | 60.6% | 29 | 29 billable h against plan |
| CI-PX-38 | PX-38 | fixed fee | posted | USD | 51,000.00 | 59,000.00 | 8,000.00 | 7,000.00 | 59,000.00 | 59.0% | 40 | Paid change request logged; base item estimate unchanged |
| CI-PX-38-CR | PX-38 | fixed fee | posted | USD | 0.00 | 1,600.00 | 1,600.00 | 0.00 | 1,600.00 | 16.0% | 8 | Contract item appears on the schedule for the first time |
| CI-PX-39 | PX-39 | fixed fee | posted | USD | 29,000.00 | 33,600.00 | 4,600.00 | 4,000.00 | 33,600.00 | 60.0% | 23 | 23 billable h against plan |
| CI-PX-40 | PX-40 | fixed fee | held | USD | 38,905.26 | 44,917.89 | 6,012.63 | 3,438.59 | 50,800.00 | 53.5% | 34 | 34 billable h against plan |
| CI-PX-41 | PX-41 | fixed fee | posted | USD | 27,000.00 | 31,600.00 | 4,600.00 | 4,000.00 | 31,600.00 | 60.8% | 23 | 23 billable h against plan |
| CI-PX-42 | PX-42 | fixed fee | held | USD | 45,230.77 | 52,615.38 | 7,384.61 | 6,461.54 | 57,000.00 | 54.8% | 40 | 40 billable h against plan |
| CI-PX-43 | PX-43 | fixed fee | posted | USD | 0.00 | 7,000.00 | 7,000.00 | 0.00 | 7,000.00 | 11.7% | 35 | Contract item appears on the schedule for the first time |

## Questions for the controller

1. Please provide the CAD/USD rate for 2026-07-31.
2. Please provide the EUR/USD rate for 2026-07-31.
3. Please provide the GBP/USD rate for 2026-07-31.
4. How should PX-12 hours be split between CI-PX-12A and CI-PX-12B?
5. How should PX-21 hours be split between CI-PX-21A and CI-PX-21B?
6. How should PX-23 hours be split between CI-PX-23A and CI-PX-23B?
7. Is SO-PX-20-ORPHAN a real order that needs a contract item, or a duplicate to void?
8. Should RMA-PX-20 reduce recognized revenue on PX-20, and against which item?
9. Was CI-PX-05 in 2026-06 meant to follow the standard rule, or was the posted figure a deliberate override?
10. Is a change order or a revised estimate expected on CI-PX-01 (539 h against 500)?
11. Is a change order or a revised estimate expected on CI-PX-03 (666 h against 600)?
12. Is a change order or a revised estimate expected on CI-PX-04 (372 h against 360)?
13. Is a change order or a revised estimate expected on CI-PX-06 (617 h against 560)?
14. Is a change order or a revised estimate expected on CI-PX-12-CR (112 h against 100)?
15. Is a change order or a revised estimate expected on CI-PX-21-CR (82 h against 80)?
16. Is a change order or a revised estimate expected on CI-PX-22-CR (63 h against 60)?
17. Should non-billable enablement hours on T&M engagements keep being recognized as revenue?
18. Should hours logged before the effective date count toward completion, or be excluded?
19. Can the OpenAir link for PX-18 be fixed so these rows arrive with a project id?

## Not on the PS schedule

- CI-PX-35: contract item has is_ps = 0
- CI-PX-36: contract item has is_ps = 0
