# Jacquard wave 2, 2026-10-31: full review of the remaining waiver, NRA and Canal Zone members

Wave 1 (`../jacquard-2026-10-31/`) showed that no lot passes a zero-miss sample, so wave 2 reviewed **every**
remaining member of three lots against the same rule cards (`../jacquard-2026-10-31/LOT_RULES.md`, cards L1, L4,
L5), excluding every order wave 1 had already reviewed. 58 blinded batches went to separate-context Claude
reviewers (Sonnet 5.5). Controls were planted in every lot: wave-1 failures with a clear type misfit (known
failures), wrong-type intruders, and texts swapped under another order's header.

| Lot | Members | Upheld | Failed | Coordinator holds | Adopted | Controls caught |
|---|---:|---:|---:|---:|---:|---|
| L1R one-person civil-service waivers, 1917 or earlier | 797 | 640 | 157 | 58 | **582** | 64 of 64 |
| L4R NRA code approvals | 78 | 30 | 48 | 0 | **30** | 6 of 6 |
| L5R Canal Zone orders | 162 | 103 | 59 | 1 | **102** | 11 of 11 after adjudication |
| **Total** | 1,037 | 773 | 264 | 59 | **714** | |

**Control adjudication (coordinator).** Two L5R known-failure controls, EO 370 and EO 3031, were upheld by the
original reviewers of batches 02 and 06, which voided those batches. Both batches were re-reviewed by fresh
reviewers, who upheld the same two orders. On reading the texts the coordinator agrees: EO 370 governs appointments
to Isthmian Canal service and was expressly revoked by EO 393 in 1906; EO 3031 is issued "for the Canal Zone" and
sets leave for canal employees; neither rests on Panama Railroad corporate statutes. The wave-1 failure judgments
on them were over-strict, so the two controls are voided (`CONTROL_KEY_ADJUDICATED.json`); neither order is adopted.
For the genuine orders in batches 02 and 06, an order is adopted only when both reviews upheld it; they agreed on
every one.

**Coordinator holds.** 59 upheld orders are withheld for individual review: 44 whose held text is cut off, because an
unseen remainder could carry a disqualifying condition, and 15 messenger or "boy" appointments, because the L1 card's
minimum-age assumption (14) is not shown for them (`COORDINATOR_HOLDS.json`). Upheld orders whose text and claim
differed by a day, with number and name agreeing, were accepted as OCR or compilation discrepancies.

The 714 adopted orders are appended to `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv` in this branch
(adoption on the owner's merge, ruling `2026-10-31-jacquard-and-working-texts`). With wave 1 the register goes from
3,403 to 4,291. The 325 orders for individual review, with reasons, are in `INDIVIDUAL_REVIEW.csv`. Statuses remain
provisional AI status hypotheses; certified 0. Reviewer usage: 60 Sonnet 5.5 runs, about 5.9M tokens.
