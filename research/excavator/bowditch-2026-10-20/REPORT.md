# Bowditch: Y2 claim factory and Y1 status probe (2026-10-20)

**Pools.** Both pools come from the readiness tracker CSV (run 100c3ee4). "Modern" means EO 7532 or later. 314 ids were excluded: existing claims, the unmerged sol-claim-kit file, the claim-kit-pilot freeze, excavator decisions/claims/overlays, and the Astra reservation.
- **Y2:** 2,022 orders. Each has a provisional status, official text done, a claim-drafts draft, is not ready, and has no claim.
- **Y1:** 4,271 orders with no status.

**Sampling.** The pool is sorted by EO number, then shuffled with `random.Random` using seed `bowditch-2026-10-20:y2` or `:y1`. Batches are 25 orders each. Only 2 of 12 Y2 batches and 2 of 2 Y1 batches were run (50 orders per pool), so the probe did not scale.

| Batch | Attempted | Claims written | Upheld / accepted | Rejected | Blocked | FETCH lines | Minutes |
|---|---|---|---|---|---|---|---|
| y2_01 | 25 | 1 (plus 2 rejected, in applied-v3 only) | 1 | 2 | 22 | 2 | 36.6 (reviewer only) |
| y2_02 | 25 | 2 | 2 | 0 | 23 | 17 | 9.5 |
| y1_01 | 25 | 0 (status proposals) | 7 | 0 | 18 | 18 | about 13 (1.9 per accepted) |
| y1_02 | 25 | 0 (status proposals) | 8 | 0 | 17 | 16 | 9.8 |

The y1_01 minutes are my estimate from the batch's own "1.9 per accepted" note. Its reported `agent_minutes` field says 4, which is only the reviewer's wall time.

**Checks.**
- The claim checker ran on all `claude-bowditch-*` files in 3 s: 3 of 3 passed, no mechanical failures, gate passed 3.
- The two Y2 claim files are `research/readiness/claims/claude-bowditch-y2-01-2026-10-20.jsonl` and `claude-bowditch-y2-02-2026-10-20.jsonl`.
- `git status` shows only these changes: `research/readiness/FETCH_QUEUE.jsonl` (72 lines added, none removed, all valid JSONL), the two claim files, and the new `research/excavator/bowditch-2026-10-20/` directory. The codebook, ledger, census and reconciled CSV are untouched.

**Y2 against the funnel test.**
- **Upheld per attempted:** 3 of 50, or 6%, against a target of at least 50%. Fail.
- **Rejected per submitted:** 2 of 5, or 40%, against a target of at most 11%. Fail.
- **Sample size:** very small, so these rates are noisy.
- **Reason for the low yield:** the kit cannot cite an end that has no TERM or ACT mechanism record. Most YES orders have no held current-law predicate. Some clause inventories are wrong.
- **Rejected claims:** EO 13792 (a one-time report, so the 2021 revocation does not prove first cessation). EO 10192 (the cited quote does not support the end date; ACTOR_TEXT has no mechanism field).

**Y1 against the reviewer tests.**
- **Disagreement:** 0 of 15, against a limit of 11%. Pass.
- **Minutes per accepted status:** about 1.5 combined (about 1.9 and 1.2 per batch), against a limit of 5. Pass.
- **Quality:** 15 NO proposals accepted, with owner acceptance false on all of them.
- **Caveat:** the Y1 reviewer was a single pass by the same agent family that produced the proposals.

**Top blockers.**
- No held CURRENT: predicate for modern orders (about 13 in y1_02 alone).
- No held ending instrument (TERM/ACT).
- Pure amendments whose base order is not held (12602, 13044, 7794).
- Unresolved partial-scope supersession (11251, 10355, 13159, 9007).
- APP-only or missing originals (7737; 8006, 8061, 8093, 9324, 9522, 7624).

**FETCH_QUEUE.** 53 request lines were added by the producers and reviewers (2 + 17 + 18 + 16); the file went from 157 to 229 lines. These are queued, not fetched by hand.

**Estimated new ready orders (estimate until the tracker runs on main).**
- A local tracker run gave 135 of 14,972 ready, the same as the committed `jobs/readiness-tracker/output/TRACKER.md`.
- The tracker only sees the 3 new claims as `CLAIM_NOT_YET_CHECKED`, because the checker output lives in job output directories I was told not to write to. The real effect waits on the GitHub Actions run after merge.
- My estimate is 0 to 3 new ready orders. For EO 10999, 11756 and 12150 the tracker also lists the ending/current-basis, savings and counterevidence steps as open, so a passed claim may not close them.

**Needs the owner.**
- Decide whether to adopt the 15 Y1 NO proposals. They are in `y1_01/PROPOSALS.jsonl` and `y1_02/PROPOSALS.jsonl`. Nothing was adopted.
- EO 12080 needs an owner rule for a spent amending order.
- EO 12086 has a ledger NO that the held record may contradict.
- EO 14125 Sec. 4 has a contradiction. EO 9704 has an unsupported NO.
- EO 14228: EO 14357 (90 FR 50725) is very probably its first end, which strengthens the NO.
- EO 13018: EO 13316 sec. 3(b) names it, so it is not an inference.
- EO 9811 (rests on the 25-year term) and EO 11417 (savings-clause reading) are contestable.

**Agent-minutes per accepted item.**
- **Y2 claims:** about 15.4 reviewer-only minutes per accepted claim (46.1 minutes for 3). Producer minutes were not reported, so the true figure is higher.
- **Y1 statuses:** about 1.5 combined minutes per accepted proposal (15 accepted).
- **Tokens:** y2_01 reviewer about 178k, y2_02 reviewer about 120k, y1 reviewers about 91k and 60k. Per-order token counts were not reported.

**Housekeeping.** The coordinator should commit `research/excavator/bowditch-2026-10-20/`, the two claim files and the FETCH_QUEUE additions. The helpers `keep_upheld.py` and `collect_proposals.py` are in the scratchpad `tools/` directory. The human-certified count stays 0, and no tier changes were made.

SUMMARY: Probe failed the Y2 funnel and was not scaled. 3 of 50 Y2 orders were upheld (6%, target at least 50%), and 2 of 5 submitted claims were rejected (40%, target at most 11%). The cause is missing TERM/ACT and CURRENT records. The Y1 status probe passed on its measures: 15 NO proposals accepted of 50, 0% reviewer disagreement, about 1.5 minutes per accepted status. All 3 claims pass the checker. Estimated new ready orders: 0 to 3, pending the Actions tracker run. 53 FETCH requests were queued. No files outside `research/` were modified, and the certified count stays 0. The owner must decide whether to adopt the 15 Y1 proposals and rule on EO 12080, 12086 and 14125.
