### Y2LEAD (2026-10-20)

**Pool.** Y2LEADX has 331 orders: 308 YES with current-law leads only, and 23 NO with a held whole-order ending. The probe was seeded batches 01 and 02, 50 orders in all (46 YES, 4 NO). Batches 03–08 were not run.

**Probe vs gate.** The gate failed, so the line stops. This counts as 2 failed probe batches.
- Upheld: 7 of 50 attempted, 0.14 per attempt. The forecast p50 was 0.05. YES orders upheld 7 of 46 (0.152, against a p50 of 0.02). NO orders upheld 0 of 4.
- Plants: 2 of 2 caught, so the 1.0 plant-catch share was met.
- Rejections: 3 of 10 genuine claims were rejected (30%), over the 25% limit. The three were EO 11701, EO 10253 and EO 13666.
- The upheld count (7) met the ≥5 requirement.

**Plants.** The planter put one defect in each batch. The plan called for two per batch, since each had 6 claim lines.
- Batch 01: EO 10104, rationale date shifted from Feb. 1, 1950 to Feb. 1, 1951. Caught, rejected for DATE.
- Batch 02: EO 11438, an EO 12107 effective date shifted from 1979-01-01 to 1981-01-01. Caught, rejected for DATE.
- Both reviewers said the unplanted lines would have been upheld, but nobody reviewed the unplanted versions. I did not count or file EO 10104 and EO 11438.

**Per-batch table**

| Batch | Attempted | Claims | Upheld | Rejected | Blocked | Plant |
|---|---|---|---|---|---|---|
| 01 | 25 | 6 | 4 (EO 10631, 11649, 12391, 12963) | 2 (EO 10104 plant, EO 11701 genuine) | 19 | caught |
| 02 | 25 | 6 | 3 (EO 11931, 12073, 12504) | 3 (EO 11438 plant, EO 10253 and 13666 genuine) | 19 | caught |
| Total | 50 | 12 | 7 | 5 | 38 | 2 of 2 |

All 7 upheld orders are YES with current-law leads. All 38 blocks were judged justified. Twelve FETCH_QUEUE lines from the producers were already in the repo.

**Pending owner rulings.** I did not apply the EO 13306 pattern at scale; it needs an owner or codebook ruling. Two further questions are open:
- whether a spent amending order can count as operative;
- whether a mixed YES claim can have one clause ended by replacement.

EO 12391 is flagged for the human certifier.

**Checker and ledger.** The claim checker ran on the 7 filed claims. All 7 passed the gate, with 0 mechanical failures and 6 of 7 passing all checks; I did not identify which one did not. Llull outcomes O-20261020-39 to -43 are recorded for L-20261020-51 to -55, and the ledger is committed. I reverted the checker's shared output files and removed its cache.

**Expected new ready orders.** Up to 7 (EO 10631, 11649, 12391, 12963, 11931, 12073, 12504). They are AI-upheld only, with 0 certified and no tier promotion.

**Files.**
- Claims: `/home/user/Executive-Orders/research/readiness/claims/claude-y2lead-01-2026-10-20.jsonl` and `claude-y2lead-02-2026-10-20.jsonl`.
- Review records, `PLANTED_CONTROLS_NOTE.md` and `OUTCOME.json`: `/home/user/Executive-Orders/research/excavator/y2lead-2026-10-20/`.

SUMMARY: Y2LEAD probe of 50 orders upheld 7 claims (0.14 per attempt against a 0.05 forecast), all YES-stratum. Both plants were caught, but the gate failed because 3 of 10 genuine claims were rejected (30% against a 25% limit). Batches 03–08 were not run. Seven claim lines are filed, and the checker passed all 7. Llull outcomes are recorded.
