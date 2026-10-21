# Rastell claims: EO 12553 targets (2026-10-20)

**Pool:** R12553C, 10 orders (5 per batch). The other 90 of the 100 EO 12553 targets were held out. 89 are emergency boards that need a report date, which is still pending the owner's ruling. All ends use the on_signing reading, 1986-02-25.

**Plants:** 2 inserted and 2 caught (share 1.0), so no batch is void. The planter put in 1 plant per batch, not the 3 the gate text assumed.
- batch_01: EO 10644, first_end date changed to 1986-03-25. The reviewer caught it.
- batch_02: EO 10415, first_end date changed to the Federal Register publication date, 1986-03-03. The reviewer caught it.
- I compared the producer's claim lines with the reviewed copy. The planted date was the only difference in either batch.

| Batch | Attempted | Upheld | Rejected | Blocked | Savings overturned | Plants caught |
|---|---|---|---|---|---|---|
| batch_01 | 5 | 3 (EO 10587, 10906, 10962) | 1 (EO 10644, the plant) | 1 (EO 11086) | 0 | 1 of 1 |
| batch_02 | 5 | 3 (EO 10054, 11049, 11102) | 1 (EO 10415, the plant) | 1 (EO 11108) | 0 | 1 of 1 |

- **Claims written:** the 6 upheld claims, from the producer's original lines (not the planted copies), are in `research/readiness/claims/claude-rastell-c01-2026-10-20.jsonl` and `claude-rastell-c02-2026-10-20.jsonl`.
- **Review records:** copied to `research/excavator/rastell-2026-10-20/claims/batch_01/` and `batch_02/`, with `PLANT_SCORE.json` and `OUTCOME.json` alongside.
- **Claim checker:** all 6 claims pass the mechanical checks and the structural gate. It ran against the committed repo into a scratch output directory.
- **Cleanup:** no scratch build directories exist inside the repo.
- **Not committed:** the new files and the four Llull outcome rows are uncommitted.

**Plant text in research/:** no planted claim line is there. However, my attempt to redact the defective value from the copied review records was denied, so I did not work around it. The batch_01 `VERDICTS.json` and `reviews/AI_REVIEWS.jsonl` quote the planted date 1986-03-25 in their reject reasons. The batch_02 `VERDICTS.json` also describes the planted 1986-03-03 as the Federal Register date. A person may want to redact these.

**Forecast vs outcome:**

| Forecast | Prediction | Measured | Outcome row |
|---|---|---|---|
| L-20261020-36, upheld per attempt | p10 0.05, p50 0.5, p90 1.0 | 0.6 | O-20261020-21 |
| L-20261020-37, probe gate passed | 0.45 | 1 (see below) | O-20261020-22 |
| L-20261020-38, plant catch share | p10 0.08, p50 0.8, p90 1.0 | 1.0 | O-20261020-23 |
| L-20261020-39, claims enabled | p10 0, p50 4, p90 8 | 6 (claims written and checker-passed) | O-20261020-24 |

- **Gate:** batch_01 upheld 3 of 5, overturned no savings states, and caught its single plant. The literal "2 of 3" could not be met, so I recorded 1 because the workflow ran batch_02. This is a judgment call.
- **Census ceiling:** the strict ceiling from the pre-override committed output was 0, so Llull warned on the measured values for L-36 and L-39.

**Expected new ready orders:** up to 6 (EO 10587, 10906, 10962, 10054, 11049, 11102) once claim-kit rebuilds on Actions. This is uncertain for two reasons:
- **Prior blocks:** EO 10587 depends on EO 11086, which is blocked.
- **Human check:** the reviewer flagged one judgment call on EO 10587 for a human certifier.

**Left for later:**
- **EO 10415:** the reviewer said it would uphold if the date were corrected. The genuine line was not re-reviewed.
- **EO 10644:** its rationale needs an EO 11281 sec. 6 lead before it can be upheld.

SUMMARY: Rastell EO 12553 tally. 10 attempted, 6 upheld (3 per batch), 2 plants rejected, 2 justified blocks, 0 savings overturned. Both inserted plants were caught (1 per batch), so no batch is void. Six claims were written and all pass the claim checker. Llull outcomes O-21 to O-24 are recorded. The batch_01 and batch_02 review records still quote the planted dates, and the redaction was denied.
