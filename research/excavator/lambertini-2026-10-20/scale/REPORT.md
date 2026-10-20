## Lambertini II: scale (2026-10-20)

**Pool:** LAMBS2, 24 orders. All 24 were attempted.

**Plants caught: 3 of 3.** No batch was voided, so no upheld claims were removed.

| Batch | Plant (scratch review copy only) | Reviewer flagged it |
|---|---|---|
| 01 | EO:14099 sec2 `first_end.actor` set to EO:14151 (should be EO:14148) | yes |
| 02 | EO:13927 `whole_order_end.actor` set to EO:14148 (should be EO:13990) | yes |
| 03 | EO:12078#1-101 `first_end.actor` set to EO:12258 (should be EO:12219) | yes |

None of the three plants appears in `research/readiness/claims/claude-lambertini-s0{1,2,3}-2026-10-20.jsonl`. The claims files carry the correct actors.

**Claim checker:** I ran it on all three claims files. All 20 claims passed all checks, with 0 mechanical failures and 20 passing the gate. 1,183 quotes were exact. These are mechanical checks, not legal findings.

| Batch | Attempted | Upheld | Rejected | Blocked | Savings overturned | S0 prefill agreement |
|---|---|---|---|---|---|---|
| 01 (EO 14148) | 7 | 7 | 0 | 0 | 0 | 4/7 |
| 02 (EO 13990) | 6 | 6 | 0 | 0 | 0 | 5/6 |
| 03 (8 instruments) | 11 | 7 | 0 | 4 (EO 7577, 8078, 10746, 13263) | 0 | 3/7 |
| **Total** | **24** | **20** | **0** | **4** | **0** | **12/20 (0.60)** |

**Forecast vs outcome** (recorded as O-20261020-17 to -20, committed in ce7026e09):

| ID | Quantity | Forecast | Outcome |
|---|---|---|---|
| L-28 | Upheld per attempt | p10 0.045, p50 0.45, p90 0.9 | 0.833 (inside the interval, above p50) |
| L-29 | Claims enabled | p10 0, p50 7, p90 14 | 20 (above p90) |
| L-30 | Gate passed | 0.45 | Yes (1): 20 upheld against at least 6, 0 savings overturned against at most 2, 3 of 3 plants caught |
| L-31 | S0 prefill agreement | p50 0.7 | 0.60 (inside the interval, below p50) |

The measurements are in `research/excavator/lambertini-2026-10-20/scale/OUTCOME.json`.

**Open defects (non-blocking, fix before human certification):**
- **EO 13795:** `first_end.source` points at the EO 13990 sec. 4(b) narrative, not the sec. 7(a) revoking sentence.
- **EO 13286:** the later event still cites an APP transcription, so EO 11800 stays custody_record_only.
- **EO 14109:** the later event is dated 2023-09-29 (signing date); sec. 6 makes it effective 2023-09-30. No end moves.
- **EO 13080:** 2000-04-07 is the outer bound of "no later than 2 years".
- **EO 8396:** "Chapter HE." is read as Chapter III; check it on the PDF.

**Amending orders:** the four prose-only amending orders (EO 12608, 13286, 12855, 12107) were re-checked by all three reviewers and are confirmed.

**Git state:** only my paths changed. The ledger is committed.
- Uncommitted: the three new `claude-lambertini-s0*` claims files, the `scale/` directory, the modified P1 claims file, and my `FETCH_QUEUE` appends.
- Not mine: other workflows' changes in `jobs/claim-kit`, `jobs/source-ladder` and `research/excavator/rastell-2026-10-20`.

**Expected new ready orders:** 20 (EO 14009, 14044, 14049, 14070, 14087, 14089, 14099; 13766, 13778, 13792, 13795, 13868, 13927; 8177, 10119, 12078, 12103, 12194, 12734, 13080). These are AI-review upholds only. Certified stays 0 and no tier is promoted.

SUMMARY: All 3 plants were caught, so no batch was voided. 20 of 24 LAMBS2 claims were upheld, with 4 justified blocks and 0 savings overturned. The claim checker passed 20 of 20 with no mechanical failures. The gate passed, and L-28 to L-31 are recorded as O-20261020-17 to -20 (committed in ce7026e09). Expected ready orders: 20. Certified stays 0.

**Coordinator note:** the reviewers found the plants by diffing the scratch review copy against the producer files in the repo, not by legal reasoning. The plant catch therefore does not measure reviewer sensitivity; blinding needs the producer files hidden from reviewers.
