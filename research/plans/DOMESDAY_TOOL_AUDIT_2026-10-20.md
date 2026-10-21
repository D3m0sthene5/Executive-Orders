# Domesday: what each tool is worth to the goal (2026-10-20)

Named for the 1086 survey that recorded what every holding was worth. Written by Claude while
merging PRs #38, #40, #42, #43, #44 and #45 into one branch. Every number comes from a committed
output file named next to it; "est." marks an agent's estimate, not a measurement.

## The one number that matters

**225 of 14,972 orders are ready for human review** (`jobs/readiness-tracker/output/SUMMARY.json`).
All 225 got there the same way: an agent wrote a claim in `research/readiness/claims/`, the
claim-checker passed it, and the tracker counted it. No tool has made an order ready on its own.

| Claim batch | Ready orders it produced |
|---|---:|
| 1989 Codification families (Claude, Oct 18) | 129 |
| Lambertini I-III | 68 |
| Lamm | 9 |
| Rastell | 6 |
| X1 pilot | 5 |
| Bowditch Y2 | 3 |
| other small batches | 5 |

The Codification swarm took ready from 1 to 130 with 176 claims in about 360 agent-minutes,
about 2 minutes per accepted claim (`research/plans/EXCAVATOR_FUNNEL_2026-10-20.md`). Lambertini
costs about $1.55–2.26 per ready order (est., `research/production/day-review-2026-10-20/REPORT.md`).

## What blocks the 3,359 orders that already have a status

From `decided_orders_blocked_by` in the tracker summary:

| Blocker | Orders |
|---|---:|
| no clause inventory | 3,028 |
| savings/residual clauses not closed | 3,028 |
| first end of a clause not proved | 2,635 |
| no official source located | 959 |
| only a compiled transcription | 898 |
| Opus media re-fetch needed | 435 |

The top three are **claim work, not missing sources or missing tools**. `jobs/claim-drafts/output/`
already has about 1,115 drafts where only the judgment fields remain. About 890 of them belong to
orders that are not ready and have no claim yet.

## Tools in three groups

**A. Tools that move the count or remove real blockers. Keep them and feed them.**
fr-originals (6,497 Federal Register originals), official-fixity (3,426 files match GPO hashes),
opus-media-match, source-ladder (364 sources held), later-events, current-law, ofr-codification-1989,
status-history, clause-drafts, claim-drafts, claim-kit, case-bundles (median fetches per order 9→1),
claim-checker, readiness-tracker, and the Lambertini batch line.

**B. Acquisition jobs whose output the tracker never reads.** hathi-gpo-orders (1,531 texts),
numbered-early-orders, early-orders-hunt, wikisource-texts, and the early-ranger family. Also
csc-annual-reports (798 of 840 orders located), whose output exists only on the unmerged
`csc-annual-reports` branch. These texts were paid for and are mostly unused. Wiring them in is cheap.

**C. Measurement and governance tools with $0 verified time saved so far.**
Junto (18 candidates, all unverified, 0 tests), Hamilton, Llull (65 forecasts; past plans delivered a
median 0.036 of what they forecast), Polya, corpus-excavator ("demonstrated gain 0"), NEYMAN (24 of 24
pilot attempts blocked), NORTON (feasibility gate failed), Valla (−5 ready: it correctly held five
claims), Mountweazel (reviewer catch rate 7/10), and portfolio-repair-check.

Group C did catch real quality problems: five unsupported first-end claims, a mis-scored Mountweazel
trial, and plant gates passed with one plant instead of three. That protects the count's integrity,
but none of it has saved time yet. These tools mostly measure each other.

## Redundancy found while merging

1. **Two fixes of one Junto bug.** NEYMAN and the portfolio repair both stopped missing quality data
   from counting as a saving. The merge keeps the repair's stricter rule.
2. **Two test-contract formats in Junto.** NEYMAN puts `test_contract` inside each candidate; the
   repair keeps a commit-verified `contracts.jsonl`. Both now validate, but new work should use
   `contracts.jsonl` only, and NEYMAN's three candidates should be re-registered there.
3. **Two sets of holds on the same five claims.** Valla and the repair each reviewed EOs 13792, 13101,
   13148, 13783 and 13807. Both are kept; they are one finding, not ten.
4. **Duplicate IDs across parallel branches.** Junto C-20261020-14 and R-20261020-4 were each claimed
   three times, Llull L-20261020-56 twice, and O-20261020-44..46 twice. They were renumbered; see
   `jobs/llull/README.md`. Agents working in parallel need IDs that cannot collide, such as a
   prefix per agent or branch.
5. **Five "what to do next" planners:** tracker SHARED_UNLOCKS, corpus-excavator, Polya, NEYMAN and
   Llull census/rank. **Four savings/forecast ledgers:** Junto, Llull, NEYMAN costs and Hamilton.
   **Three reviewer-quality systems:** Valla, Mountweazel and the Llull/Lambertini gates.

## Recommendation: fix and wire the existing tools; build no new ones for now

The gap is not a missing tool. Claims are not being written fast enough against drafts that already
exist, and sources already fetched are not reaching the tracker. In order:

1. **Run claim batches on the ~890 judgment-only drafts**, grouped by shared ending instrument the way
   Lambertini does. This is the only proven way to raise the ready count. At Lambertini's estimated $1.55–4.43
   per ready order, all 890 would cost roughly $1.4k–3.9k. Not every draft will be upheld, so treat
   that as a ceiling on yield, not a forecast.
2. **Drain the source-ladder queue on the runner.** The last run was an offline validation that worked
   3 of 1,454 queued items. Do an online run, including the 774 Opus re-fetch items blocking 435 orders.
3. **Merge `csc-annual-reports` and wire group B's texts into the tracker** as leads or originals,
   per the codebook.
4. **Get the owner rulings that unlock whole classes of orders:** the report-deadline rule (about 52
   orders), transcription-as-copy (up to 3,216), and Y1 batch status adoption (up to 11,613 statuses,
   no ready orders directly).
5. **Freeze group C.** Build no more meta-tools. Pick one planner (keep the tracker plus Polya), one
   ledger (Junto for savings, Llull for forecasts, with NEYMAN's costs feeding Junto) and one quality
   gate path (claim-checker → Valla holds → Mountweazel plants). Only spend on a group C tool when a
   claim batch is about to run and a preregistered Junto test with a cost baseline is attached.
