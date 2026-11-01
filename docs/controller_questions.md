# Questions for the controller

The brief says the finance team will answer questions. These are the ones the July close
raises, in the order I would ask them. Each says what the engine assumed in the meantime, so
the July figures stand as a complete draft until an answer changes a config value.

## Changes a July number

**1. PX-12 (Lattice Semiconductor): how should July's 109 hours be split between CI-PX-12A
(base scope, 340 of 500 hours delivered) and CI-PX-12B (extension milestone, fully
recognized 20 June)?** July timesheets name the project, not the item. Assumed: all 109 hours
continue the base scope, since the extension's milestone has been delivered and accepted. That
recognizes 21,800 USD on 12A. A plain split by planned hours would recognize 8,175 USD less.
The same question applies to PX-21 (40 hours, 260 USD swing) and PX-23 (26 billable hours,
128 USD swing). If ops can restore the item tag on the OpenAir export, the question goes away.
Config: `hours_allocation`.

**2. Time and materials: should non-billable "internal enablement" hours keep being recognized
at 200/h?** Every T&M month in the history recognizes all logged hours, billable or not. July
follows that: 37 non-billable hours, 7,400 USD across PX-23 to PX-26. If the answer is no, set
`tm_count_nonbillable = false`; the engine will then also report the cumulative amount that
history recognized on this basis. Config: `tm_count_nonbillable`.

**3. PX-29 and PX-30 (expansion scopes, effective 1 July): do the 63 hours logged April to June
and tagged "pre-effective scope start" count toward percent complete?** Assumed yes, because
history already counted them in planned value and they are real delivery effort on the scope.
This is worth 7,000 USD on PX-29 and 5,600 USD on PX-30 in July. Note that ops is still tagging
July hours on both projects as pre-effective (21 more hours) although the items are now live.

## Changes a prior period, or needs a decision

**4. CI-PX-05 (Ember Insurance): was the May close meant to skip the no-charge change order
CO-2026-011 (+20 hours)?** PX-22, PX-31 and PX-42 had the same kind of adjustment applied to
their estimate at completion; PX-05 did not, and recognized 3,590.91 USD more in May than the
rule gives. No July effect (the 95% cap binds either way), but either the rule or the posting
is wrong.

**5. Tundra Apparel (PX-20): three open items.** An approved sales order SO-PX-20-ORPHAN for
15,000 USD with no project and no contract item; an RMA for -3,000 USD (credit memo CM-PX20,
"unresolved cross-reference to prior SO") that was never posted; and 12 June hours reported as
"Legacy Support Work" that match no project, with a row id that points at the orphan order.
Is this one unprocessed change order, and against which item should the credit go?

**6. Milestone deals: is the delivery schedule always 50/50?** All four milestone items took 50%
up front. A new deal with three tranches would be recognized wrongly until
`milestone_tranches` is changed.

## Data quality

**7. PX-18 (Redwood Transit): can the OpenAir link be fixed?** Its timesheets arrive with no
project id and are matched by the project's alias list. 195 hours through June and 29 in July
depend on that match holding.

**8. SO-PX-19 has no project id** and is linked to PX-19 only through the `netsuite_so_hint`
alias. No revenue effect; a reconciliation nuisance.

## Routine

**9. July exchange rates for CAD, EUR and GBP.** None in the data. The USD view of the rollup
uses the 30 June rates and says so.

**10. Overruns past plan without acceptance.** PX-01, 03, 04, 06 and the three change-order
children are past their planned hours and capped at 95%. PX-03 is at 111% of plan. Are change
orders or revised estimates coming?

**11. PX-09 and PX-10 (platform builds):** milestone_completion was confirmed 11 July and the
engine releases the remaining 50% (70,000 USD between them). Confirming that the event in the
PM system is the trigger finance wants.
