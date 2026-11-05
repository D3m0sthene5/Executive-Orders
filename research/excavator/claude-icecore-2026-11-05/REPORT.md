# Ice core probe, 2026-11-05: what a stratified sample of the remaining claim-ready orders yields

The probe drew 30 orders by decade from each of the two remaining claim-ready strata, the 886 provisional-NO orders and the 359 provisional-YES orders (both Federal Register era). It ran each layer as one batch through the ordinary claim-kit route. A Sonnet producer researched each batch. Two independent blind Opus reviewers in fresh contexts then checked every submitted claim, with planted controls in each review set, and a claim filed only if both reviewers upheld it. Completion ran through `kit.py complete`. No order was replaced: an order that could not be prepared or failed the dispatch check stays in its layer as attempted and not submitted.

**Result.** The NO layer filed **1 of 30** orders and the YES layer filed **11 of 30**. Both planted controls were caught by both reviewers. The 12 filed claims are in `research/readiness/claims/claude-2026-11-05-icecore-no.jsonl` and `-yes.jsonl`. No status, codebook entry, census entry or human review changed, and the certified count stays **0**.

**What this means for the allocator.** Before the probe, Bentham ranked the 886-order NO wave at 73.6 dossiers per $100. That figure rested on the 2026-11-04 Tribonian wave's 47.6% yield. The orders that yield came from have mostly filed and left the stratum. What remains is Tribonian's failures plus orders it never drew: 11 of the 30 sampled NO orders were attempted and blocked in Tribonian (1 filed now, EO 13071), and the 19 never attempted filed none. The remaining NO orders filed at 3.3%, and the plan now ranks the NO wave at 5.2 dossiers per $100, near the bottom. Before the probe, the YES stratum could not be ranked at all, because its yield rested on only 7 attempts. It now ranks at 56.7 per $100 (36.7%), below the custody recovery and one-step actions. The Bentham gate returned STOP for the probe as a wave. Run on the YES batch alone it also returns STOP (P = 0.15 against the 0.74 next-best).

## Per layer

| | NO layer | YES layer |
|---|---:|---:|
| Attempted (orders drawn) | 30 | 30 |
| Not prepared: existing claim of another owner | 2 (EO 9717, 9555) | 1 (EO 13472) |
| Dispatch-blocked before any producer | 2 | 5 |
| Assigned to the producer | 26 | 24 |
| Producer blocked | 25 | 7 |
| Submitted | 1 | 17 |
| Rejected by a blind reviewer | 0 genuine (1 planted control) | 3 genuine (EO 12228, 12372, 9998) plus 1 planted control |
| Passed review but failed the actual checker (custody) | 0 | 3 (EO 12019, 12293, 12748) |
| **Filed** | **1** | **11** |
| Controls caught (by both arms) | 1 of 1 (EO 13071) | 1 of 1 (EO 12292) |
| API-equivalent cost, producer + review | $7.08 | $29.69 |

Totals: 60 attempted, 18 submitted, 12 filed, no control missed, $36.77 for producers and reviewers, plus $22.47 coordination, for $59.25 in all.

### Dispatch-blocked members, with the missing source

Every dispatch block was a mandatory original source held only as a custody record (`custody_record_only`): its hash is recorded but its bytes are in no committed place. All are recent orders.

- NO: EO 13682 (79 FR 73459, govinfo FR-2014-12-10/2014-29121.pdf) and EO 14011 (86 FR 8273, FR-2021-02-05/2021-02562.pdf).
- YES: EO 13736 (FR-2016-08-17/2016-19724.pdf), EO 13827 (FR-2018-03-21/2018-05916.pdf), EO 14038 (FR-2021-08-11/2021-17253.pdf), EO 14306 (FR-2025-06-11/2025-10804.pdf) and EO 14404 (FR-2026-05-07/2026-09173.pdf).

Retaining those seven PDFs, at the hashes already recorded, would make them dispatchable.

### Why the NO layer yields so little

The producer read all 26 assigned orders and blocked 25, each with a specific gap. Most of these orders have no held instrument that ends them, so the first-end date cannot be proved. The blocks fall into five groups:

1. **Land withdrawals and reservations with no held revocation (EO 7678, 8932, 9026, 10126).** The order says it lasts until revoked. No held public land order or revocation names it.
2. **Orders resting on a statute whose expiry or repeal text is not held (EO 9023, 9519 and 10227 under Title II of the First War Powers Act; EO 10907, 10911 and 11631 under the Internal Revenue Code return-inspection rule; EO 10240, 10311 and 12079).** The order ends when its statutory basis ends, but that statute's ending text is not held.
3. **Boards that end on submitting a report whose date is not held (EO 12650, 13351), and actions performed on a date the sources do not show (EO 9776).** Under the owner's report-deadline ruling, a deadline is not an end, so these stay open.
4. **Amending orders whose parent's end is not citable in the packet (EO 11309, 11949), partial own-terms ends with a continuing clause (EO 11503), and amendments without an ending (EO 8215).**
5. **Text and inventory problems (EO 8766, 9709, 12328), and a checker false positive (EO 10359).** For EO 10359 the substance was found: EO 10480 §607(8) supersedes it on 1953-08-14. The actual checker fails `order_exists`, however, on OCR tokens ("Executive Order 96361", "E. O. 1-C") inside the whole-record quote. A cleaner registered text or a checker fix would file it.

The one submission, EO 13071 (superseded by EO 13106 on 1998-12-07), passed both reviewers after reveal and filed.

By decade, the only filing came from the 1990s. Every 1930s–1980s order (26) and the 2000s order were blocked or owner-routed, and the 2010s and 2020s orders were dispatch-blocked. The layer is too small to estimate a per-decade yield, but the pattern is uniform: older NO orders that remain lack a held ending instrument.

### Why the YES layer yields more, and what blocked it

YES claims use the established `original_plus_bounded_search` predicate. The predicate rests on four things: the held original, every held later instrument attached as a later event, no own-terms end, and the three bounded machine searches (U.S. Code release point 119-121 through 2026-10-09, eCFR as of 2026-10-14, and the Federal Register executive-order catalogue). Review had upheld claims of this form before this probe, including EO 13128 and 13274 in Tribonian o27.

On its first pass the YES producer blocked all 24 orders without reading any of them, claiming that no current-law source was held. That premise contradicts the filed precedents. The coordinator sent the producer back with the precedent named, and the second pass worked each order. Both passes count in the cost ($16.62 of producer tokens in all).

The seven producer blocks:
- EO 7724: Public Land Order 326 (11 FR 10298), which partly revoked it, is not held.
- EO 10173: its 33 CFR Part 6 regulations were rewritten section by section, and the current Part 6 text is not held.
- EO 10789 and 11438: the official texts of EO 11051, 11610 and 13286 are in the corpus but are registered in the packet only as presidency-project mirrors, so the working-text check rejects them as later-event sources.
- EO 12957 and 13553 (Iran) and EO 13611 (Yemen): the yearly National Emergencies Act continuation notices through 2026 are not held.

Reviewer rejections with defects:
- **EO 12228 (both arms).** The claim says §1-101 can rely on EO 10000 because only §§402–404 were revoked. Held EO 10903 §5(a) revoked Part I of EO 10000, which is the part §1-101 points to.
- **EO 9998 (both arms).** Arm A found that the rationale cites "Code and CFR leads" when all three searches returned zero hits. Arm B found that the claim never addresses the held 1989 codification table's entry "Authority repealed by Pub. L. 96-465".
- **EO 12372 (arm A only).** The claim dates EO 13132's later event 1999-08-04, its signing date. The coordinator checked the held EO 13132 text: §10(c) says "This order shall be effective 90 days after the date of this order." The rejection therefore stands.

Three upheld claims then failed completion as `rejected_mechanical`. Each cites later-event sources that are custody-only (EO 12019: EO 13666; EO 12293: EO 12363, 12388, 12536, 13118, 13325 and 13374; EO 12748: EO 12883, 13106 and 13415). The dispatch check covers only sources the dossier declares mandatory, not the later events a producer adds, so it did not catch them; Tribonian o27 failed the same way. When those bytes are held, these three need a new packet and fresh review.

By decade, the YES filings fall in the 1950s (1 of 3), 1960s (3 of 4), 1970s (4 of 5), 1980s (2 of 5) and 2000s (1 of 2). The 1930s and 1940s orders (1 each) did not file, and neither did any 2010s or 2020s order: five of those seven were dispatch-blocked and two were emergency orders.

## Process notes

- **Reviewer independence.** Arm B used a web search (50 U.S.C. 2406 and 2511 notes) while reviewing EO 12344, which is outside the held-source rule. Arm A upheld the same claim from held sources alone, so the filing does not depend on the web material.
- **The second reviewer mattered.** Arm A alone caught the EO 12372 effective-date error, which filing on arm B's review alone would have missed. This repeats the Lind trial's finding that pairing two reviewers adds catches.
- **Owner-routed members.** Prepare refused EO 9717, 9555 and 13472 because each has an existing incomplete Astra claim (`astra-2026-10-17-p12553a.jsonl`, `astra-2026-10-17-p3originals.jsonl`). They count as attempted and not submitted. Finishing them needs the owner's route or an explicit replacement proposal.
- **Reservations.** All 57 prepared members were reserved through the claim-kit lock before preparation and released afterwards. The lock file is unchanged on the branch.

## Measured cost

These figures come from `python3 -I jobs/bentham/sessions.py --since 2026-11-05T21:10:00Z`, restricted by phase map to this coordinator and its six worker sessions. They are API-equivalent dollars at the list prices in `measure.py`, not an invoice. Sanitized rows are in `telemetry/AGENT_USAGE.csv` and totals in `telemetry/SUMMARY.json`.

| Phase / batch | Agents | Calls | Cache read | Cache write | Output | USD |
|---|---:|---:|---:|---:|---:|---:|
| Production, NO (Sonnet) | 1 | 76 | 11.6M | 0.22M | 72k | 5.36 |
| Production, YES (Sonnet, two passes) | 1 | 208 | 39.0M | 0.52M | 197k | 16.62 |
| Review, NO (Opus, 2 arms) | 2 | 27 | 1.6M | 0.09M | 15k | 1.72 |
| Review, YES (Opus, 2 arms) | 2 | 115 | 17.6M | 0.41M | 68k | 13.07 |
| Coordination (Opus) | 1 | 126 | 26.5M | 1.10M | 94k | 22.47 |
| **Total** | 7 | 552 | 96.2M | 2.34M | 446k | **59.25** |

Per filed claim, producer and review cost $7.08 in the NO layer and $2.70 in the YES layer. Tribonian's measured figure for a whole wave was $1.37 per filed dossier.

## What Bentham now ranks differently

`jobs/bentham/measure.py` now pools any wave whose `evidence/DISPOSITION.json` says `"pool_into_rates": true` and that has a matching `tools/batches.json`. When a wave also says `"sample_of_remaining": true` and has at least 30 attempts in a stratum, that stratum's rate is the sample's alone, because Tribonian's attempted orders are no longer in the pool. The pooled figure is kept as `pooled_alternative`. Costs stay Tribonian's. Tests: `test_measure.py`, 11 pass. `python3 -I jobs/bentham/measure.py` now gives:

- `filed_per_attempt.no.fr` = 1/30 = 3.3%, from this probe. Pooled with Tribonian it would be 493/1064, or 46.3%.
- `filed_per_attempt.yes.fr` = 11/30 = 36.7%, from this probe. Pooled it would be 11/37.

The plan, rebuilt with a $100 budget, changes as follows. The YES stratum moves from unranked to rank 10, at 56.7 dossiers per $100 (131.6 expected from 359 orders, $232). The NO stratum falls from rank 12 at 73.6 per $100 to rank 13 at 5.2 (29.5 expected from 886 orders, $573). The fecundity of acquisitions that feed the NO stratum falls with it; EO 4314's shared source, for example, drops from 3.7 to 0.3 later dossiers. The custody recovery (48 orders, $19) and the one-step closures (43 orders, $28) remain the best agent actions.

## Next steps, by measured value

1. **Do not run the 886-order NO wave.** Its measured value is now 5.2 dossiers per $100.
2. **Retain the custody-only bytes.** The seven dispatch-blocked originals are listed above, and the three YES later-event sets are in the YES rejections section. Retaining them reopens 10 sampled orders without new research.
3. **Acquire the National Emergencies Act continuation notices.** Three of the 24 assigned YES orders were blocked only by these notices; Theophilus's `theophilus-sources` job is fetching them. Also register the official FR texts of later orders that are now held only as mirrors (EO 13286, 11051, 11610).
4. **Do not draft NO orders that lack an ending source.** Their first step is source acquisition: public land orders for withdrawals, and the expiry texts of the First War Powers Act Title II and the IRC return-inspection rule.

## Files

- `orders/`: the two sample lists.
- `evidence/DISPOSITION.json` and `.csv`: per-batch disposition, in Tribonian's shape, with pooling flags.
- `evidence/MEMBERS.json`: one row per drawn order with its decade and outcome.
- `evidence/<layer>/`: decisions, producer report, dispatch receipts, both arms' blind and after-reveal reviews, the completion manifest, the two-reviewer rule receipt, tally, exceptions and publication receipt.
- `BATCHES.json`: the gate input.
- `tools/`: scripts adapted from Tribonian, plus `finish2.py` (two-arm completion), `launch.sh` and `resume.sh` (fresh headless workers) and `batches.json`.
- `COORDINATOR_LOG.txt`: the run log.
- The full packets (about 270 MB with the completion tracker replays) stay on the coordinator's machine and are not committed. The private control keys never left scratch space.
