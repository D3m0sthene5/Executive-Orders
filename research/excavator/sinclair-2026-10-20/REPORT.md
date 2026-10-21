# Sinclair: Y1 status sweep (2026-10-20)

**Sample:** 150 orders from the 4,137-order pool, seed `sinclair-2026-10-20:y1`, in 6 batches of 25. The blinded Opus reviewers worked from held sources with a D6 step. Batch 01 was the probe. Batches 02-06 ran even though the probe gate failed.

**Plants:** 6 of 6 caught, one per batch, all of the wrong-revoking-instrument type. The brief asked for 3 in the probe and 2 in each scale batch, so the planter under-planted. It also left FETCH_LINES, telemetry and the extra OUTCOMES columns in every review copy. No batch is void, because no plant was missed. Each planted order was a genuine proposal, so its review was lost. Those six orders (9762, 10704, 12573, 13975, 11796, 12604) are pending re-review.

| Batch | Attempted | Proposed | Upheld (NO / YES) | Rejected | Blocked (all justified) | Plant caught | Valid repo proposals |
|---|---|---|---|---|---|---|---|
| 01 (probe) | 25 | 5 | 4 / 0 | 1 (plant) | 20 | 1 of 1 | 0 (stale) |
| 02 | 25 | 8 | 6 / 0 | 2 (1 plant, 1 genuine) | 17 | 1 of 1 | 0 (stale) |
| 03 | 25 | 5 | 4 / 0 | 1 (plant) | 20 | 1 of 1 | 0 (stale) |
| 04 | 25 | 8 | 7 / 0 | 1 (plant) | 17 | 1 of 1 | 0 (stale) |
| 05 | 25 | 9 | 8 / 0 | 1 (plant) | 16 | 1 of 1 | 0 (stale) |
| 06 | 25 | 7 | 6 / 0 | 1 (plant) | 18 | 1 of 1 | 6 |
| Total | 150 | 42 | 35 / 0 | 7 | 108 | 6 of 6 | 6 |

There are no YES proposals. The one genuine rejection is EO 8553, where no held source records the ending.

**Stale-generation problem (my finding):**
- `overlay-propose` refuses batches 01-05 with `stale_compiled_generation`. Their freezes predate a regeneration of the claim-kit compiled output. Batch 06 was frozen after it.
- The 29 reviewer-accepted orders in batches 01-05 are therefore not proposals. I did not work around the refusal.
- Their review sheets are kept under `research/excavator/sinclair-2026-10-20/<NN>/reviews/`.
- They need a re-freeze at the current generation and a fresh independent review. The review sheet pins the evidence fingerprint, so the old reviews cannot be reused.

**Forecast vs outcome** (recorded as Llull O-20261020-26 to -30):

| Forecast | Predicted | Measured |
|---|---|---|
| L-40, probe gate passed | 0.45 | 0 (failed: batch 01 had 4 accepted, 5 needed; only 1 plant existed) |
| L-41, rejected per submitted | p10 0 / p50 0.07 / p90 0.25 | 0.028 (1 genuine rejection of 36 genuine submitted) |
| L-42, accepted per attempt | p10 0.025 / p50 0.26 / p90 0.52 | 0.243 (35 of 144; the 6 lost plant reviews are out of the denominator) |
| L-43, plants caught share | p10 0.075 / p50 0.75 / p90 1.0 | 1.0 (6 of 6) |
| L-44, accepted count | p10 2 / p50 22 / p90 50 | 35 reviewer-accepted, but only 6 are valid proposals |

**Time per accepted status:** producers took about 116 minutes and reviewers about 156 minutes, roughly 272 minutes in all. That is about 7.8 minutes per reviewer-accepted status, or about 45 minutes per valid proposal as things stand. All the minute figures are estimates.

**Files written:**
- `research/excavator/sinclair-2026-10-20/OUTCOME.json`, plus `PLANTED_CONTROLS_NOTE.md` (planted rows removed from the review logs; reviewer text quoting planted values redacted).
- `research/excavator/sinclair-2026-10-20/06/PROPOSALS.jsonl`, and review records for batches 01-06 under the same folder.
- 100 new fetch lines appended to `research/readiness/FETCH_QUEUE.jsonl`. They are uncommitted, alongside other workflows' uncommitted edits to that file.
- `_staging/` is gone and `DECIDED_CASE_COMPLETENESS_RECONCILED.csv` was not written. The certified count stays 0.

**What the owner must decide:**
1. Whether to adopt the 6 batch-06 NO proposals (EO 8714, 12488, 10610, 12240, 10656, 12246). All are AI hypotheses with `accepted: false`.
2. Whether to re-freeze and re-review the 29 accepted orders in batches 01-05.
3. Whether to re-review the 6 plant-lost orders.
4. Whether to fix the planter and cleanup steps before any scaling.
5. Whether to push `FETCH_QUEUE.jsonl`, which triggers the fetch job. The 108 blocked orders mostly need ending or CURRENT records.

SUMMARY: Sinclair swept 150 orders in 6 batches: 6/6 plants caught, 35 NO upheld (0 YES), 108 blocks justified. The probe gate failed (4 accepted, 5 needed), but accepted-per-attempt was 0.243 against a p50 of 0.26. Only batch 06's 6 proposals passed overlay-propose; batches 01-05 are stale-generation and need re-freeze and re-review. The 5 Llull outcomes are recorded and the certified count stays 0.
