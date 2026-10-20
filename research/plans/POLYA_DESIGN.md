# Polya: change the problem, then measure what the change buys (design, 2026-10-20)

Named for George Polya, *How to Solve It* (1945). His moves for a problem that will not yield:
change the unknown, introduce an auxiliary element or problem, specialize, generalize, use
analogy, **work backwards**. Polya the tool applies them to our own problem statement and measures,
from committed job outputs only, how much each reformulation could move.

Status: built in `jobs/polya/` (commands `frames`, `leverage`, `compare`, `export`; 12 tests pass).
Numbers below are from `jobs/polya/output/COMPARE.json` at repo head 46f91fdac. Sister tools: Llull
(`research/plans/LLULL_DESIGN.md`, scores a plan before it runs) and Junto (token savers).

## 0. Why, and the hard rule

Measure: orders ready for human review, 135 of 14,972 (14,837 not ready: 3,224 decided, 11,613
undecided). Certified whole-lifecycle stays 0. AI statuses are hypotheses. No codebook change.

Every plan so far took the **order** as the unit of work and missed: the series plan assumed 4,134 h
and measured 463; Bowditch Y2 expected at least 50% upheld and got 6% because the orders lacked held
ending instruments and current-law predicates (`research/excavator/bowditch-2026-10-20/REPORT.md`).
Llull's postmortem finds the same class of error (unmeasured prerequisite) in 8 of 12 misses.

**Hard rule: reach is not yield.** Polya counts the not-ready orders a unit could move forward one
step. It never estimates orders made ready, hours, dollars or acceptance rates. A frame earns a claim
about value only when a Llull-registered probe on its top unit measures ready orders per dollar
(section 5). Estimates are labelled "estimate"; this document contains none.

## 1. Frames

| Frame | Polya move | Unit of work | Step advanced |
|---|---|---|---|
| F0 order | baseline | one order | all |
| F1 ending instrument | change the unknown: solve the actor, not the target | an instrument that revokes/supersedes/terminates others | ending (decided NO); NO status (undecided) |
| F2 actor provision record | auxiliary element | an acting order whose target-naming provision is not located | ending |
| F3 source document | generalize | a shared held source | original text |
| F4 legal family / X1 cluster | analogy | prove the rule once, check each member | ending; clause inventory |
| F5 owner or codebook question | work backwards to the human ruling | one decision (never a codebook change) | the gated blocker |
| F6 missing input type | decompose the unknown | ORIGINAL / ACT / CURRENT / INVENTORY | by type |
| F7 current-law table | auxiliary problem | one USC/CFR slice, YES orders | current basis |
| F8 reviewer | work backwards | a source the independent human reads | review cost |
| F9 single blocker | specialize | a blocker that is the order's only one | ready (by blocker) |

Exact files and computations are in `jobs/polya/README.md` and the code.

## 2. Measured leverage

Reach of the whole frame, concentration, and the share of the pool covered by the 10 or 100
highest-leverage units. Gini: 0 = every unit reaches the same number, toward 1 = a few units hold the reach.

| Frame | Units | Orders reachable | % of not-ready | Gini | Largest unit | Top 10 cover | Top 100 cover |
|---|---:|---:|---:|---:|---:|---:|---:|
| F0 order | 14,837 | 14,837 | 100% | 0.00 | 1 | 0.1% | 0.7% |
| F1 ending instrument | 1,772 | 2,843 | 19.2% | 0.44 | 335 | 4.6% | 8.5% |
| F2 actor provision record | 1,050 | 1,212 | 8.2% | 0.50 | 334 | 3.5% | 5.3% |
| F3 source document | 905 | 926 | 6.2% | 0.02 | 10 | 0.2% | 0.8% |
| F4 legal family / cluster | 1,595 | 3,431 | 23.1% | 0.71 | 1,066 | 15.5% | 18.7% |
| F5 owner/codebook question | 6 | 13,265 | 89.4% | 0.58 | 11,613 | 89.4% | 89.4% |
| F6 missing input type | 10 | 3,224 | 21.7% | 0.38 | 1,213 | 21.7% | 21.7% |
| F7 current-law table | 2,195 | 346 | 2.3% | 0.23 | 20 | 0.5% | 1.0% |
| F8 reviewer | 128 | 90 | 0.6% | 0.37 | 23 | 0.3% | 0.6% |
| F9 single blocker | 4 | 4,586 | 30.9% | 0.75 | 4,560 | 30.9% | 30.9% |

A unit counts an order only if a step the unit advances is still open on it (adversarial review,
2026-10-20: without this filter F3 reached 3,079 orders, but 2,177 of its source-family orders already
had original_text done; the largest held source serves 2 orders whose text step is open, the largest
tracker shared source 10). Frames overlap, so reaches are not additive; the same actor (EO:12553) is
one piece of work in F1 and F2, and the export links such actions in `same_unit_actions`. F5's 89% is a ceiling dominated by one owner
yes/no (batch adoption of reviewed status overlays, 11,613) and is not work. F9's 4,560 is one
blocker, "no provisional status", and clearing it does not make those orders ready: each still has 5
open steps (blocker codes do not track every step).

## 3. What the measurements say

1. **Concentration exists but only in a few frames.** F1 on decided-NO targets (Gini 0.66): 10
   instruments reach 18.0% of the 3,224 decided not-ready orders and 100 reach 28.6%; EO:12553 alone
   reaches 335, EO:14148 65, EO:9830 53. F2 names the same EO:12553 (334 orders whose actor
   provision is unlocated). F4's own-term families (Gini 0.72) reach 2,353 decided orders, but their
   wording is a lead (a report deadline does not end an order). F3 (source documents) is flat: the
   largest held source serves 2 orders whose original_text is still open. F7 (current-law table) is flat: 346 of 404 YES orders have a lead,
   spread over 2,195 citations, largest 20.
2. **Readiness is a conjunction, and no single-step frame closes it.** 3,152 of the 3,224 decided
   not-ready orders have 3 to 5 open steps; only 51 not-ready orders anywhere have 2 or fewer. For
   F1, F2 and F4 the number of reached orders whose only open steps are the ones the frame advances
   is 19, 13 and 23; for F3, F7 and the X1 clusters it is 0. So even a perfect run of the best
   single-step frame moves a few dozen orders to ready, which is why the order-by-order plans missed
   and a reach figure must not be read as a forecast.
3. **Two steps have no frame at all.** `compare` writes a step matrix. Open on decided not-ready
   orders: savings_residuals 3,188, clause_inventory 3,176 (only the X1 clusters touch it, 1,233
   orders), counterevidence 884 and opus_media 714 (no frame), original_text 1,047. Stacking every
   frame's units together, only **25 of 3,224** decided orders have all their open steps reachable
   by some frame; 1,469 need savings_residuals and clause_inventory with no unit that reaches them.
   The next useful reformulation is a frame for savings_residuals and counterevidence (what
   unit serves many orders there?), not another frame for the ending step.
4. **Near-ready is small and specific.** F8: 49 decided orders have 1 or 2 open steps (23 only the
   ending, 17 ending plus savings_residuals). They are the cheapest test of whether a frame converts
   reach to ready.

## 4. What Polya does not claim

- It does not rank frames by value. Reach differs from yield, and units differ in cost.
- It does not prove any ending: F1 edges are editorial leads and need not be a target's first end
  (the X1 lesson). F2 counts a missing located provision, not the provision's content.
- It does not authenticate anything: historical document discovery is not identity authentication,
  and no AI status becomes certified.
- Frame membership is read from heuristics in other jobs (claim-kit dossier text, blocker codes);
  those strings change when their jobs rerun, so compare outputs only for the same commit.

## 5. Interface to Llull

`python3 -I jobs/polya/polya.py export` writes `jobs/polya/output/CANDIDATE_ACTIONS.json`
(`polya.actions/1`, 101 actions at this commit: the top 10 units of each view with reach of at least
2). `jobs/llull/llull.py` does not exist yet and its `voi --actions` schema is not fixed, so the
format is documented in `jobs/polya/README.md`. Mapping onto Raiffa (Llull section 5):

| Polya field | Llull use |
|---|---|
| `ceiling_orders` (= not-ready reach; already-ready orders excluded) | Domesday-style ceiling for the forecast; never the forecast |
| `cost_usd`, `E_ready`, `reference_class` | null on purpose; Llull fills them from measured reference classes |
| `steps_complete_if_done_upper_bound` | cap on ready orders this one step could produce alone |
| `tier_hint`, `requires_unmeasured` | suggestion; Wheel turns each unmeasured requirement into a question |

Suggested first probes, each a registered plan with a pre-set scale rule: the 49 near-ready orders
(F8; a zero-agent tracker rerun after the missing step), and one top F1 unit (EO:12553's 335
targets, bounded to a Bowditch-sized pilot) to measure whether reach of 335 converts at all.

## 6. How Polya is scored

Not by reach. A frame is scored when a probe on one of its units has a measured outcome in a
committed file: ready orders gained per dollar against the order baseline, using Llull's outcome
records. Until a frame has one resolved probe its leverage stays "reach, unverified", as Junto's
finders stay `unverified` until `add-test` measures them. A frame whose top unit converts at or
below the order baseline is recorded as refuted and drops from `export`.

## 7. Next

1. Run `compare` after each tracker rerun and keep the step matrix; the measure is whether the "no
   frame" steps shrink.
2. Add a frame for savings_residuals / counterevidence (candidates: one repealed-statute or
   litigation record serving many orders; one residual-effect class), measured the same way.
3. When Llull's driver lands, replace the documented schema with its own and register the two
   probes above.
