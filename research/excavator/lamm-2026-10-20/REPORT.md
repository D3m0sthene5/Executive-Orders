# Lamm: fixed-term orders (2026-10-20)**

**Pool.** 577 orders in family own_term:fixed_term. The pool excludes Rastell's batch orders, the Lambertini pools LAMBS and LAMBC, and orders with claims filed. A zero-agent screen sorted it into:
- 290 retirement-age exemptions, 276 of them held only as a compiled transcription.
- 188 detector noise.
- 66 sunsets.
- 26 report-relative.
- 7 other.

**Mechanism.** claim-kit already has an own-terms end mechanism: a TERM record can be cited as a clause's end, and report deadlines are blocked as ends. I made no claim-kit change. The EO 5763/5930 gap (no TERM record detected) is separate and still open.

**Forecast vs outcome.** Outcomes are recorded in the ledger and in `research/excavator/lamm-2026-10-20/OUTCOME.json`.

| Forecast | p10 / p50 / p90 | Measured | Outcome id |
|---|---|---|---|
| L-20261020-20, own-term ends upheld per attempt | 0.02 / 0.25 / 0.6 | 0.575 (23 of 40) | O-20261020-7 |
| L-20261020-21, probe orders with ending step enabled | 0 / 1 / 3 | 0 of 40 | O-20261020-8 |
| L-20261020-22, full kit claims accepted | 0 / 0.5 / 2 | 0 | O-20261020-9 |
| L-20261020-23, batch_03 enabled | 0 / 5 / 10 | not run | not recorded |

The -20 value is provisional. It comes from AI review, and neither probe batch had a working plant check.

**Per-batch table**

| Batch | Attempted | Upheld | Negative confirmed | Blocked | Rate | Claims enabled |
|---|---|---|---|---|---|---|
| 01 | 20 | 12 | 8 | 0 | 0.60 | 0 |
| 02 | 20 | 11 | 9 | 1 (EO 12575) | 0.55 | 0 |

**Gate.** The gate failed, so nothing was scaled. The upheld rates passed (pooled 0.575, neither batch below 0.10). But no `review/PLANT.json` existed and neither reviewer caught a plant, so both batches count as void. Batches 03 to 12 did not run.

**Blockers**
- No Mountweazel plants were inserted. The probes need to be rerun with plants and a working plant check.
- Every upheld end rests on a derivative or compiled transcription, so the original-text step is open on all of them. Retirement-exemption batches 10 to 12 hold only compiled transcriptions and are gated on the owner ruling that such a copy is acceptable.
- Owner rulings needed:
  - Whether a "further exempt" order extends its predecessor. This affects EO 8554, 8392, 8828 and 8058.
  - Whether the stated "until" day is included, for EO 7300 and 6933.
- EO 12575 needs a source for the Tower Board report date; its FETCH_QUEUE line is present.
- EO 13125 needs a source on whether it was renewed before 2003-06-07. Its FETCH_QUEUE line is one uncommitted append.

**Claim-checker and git status.** There are no `claude-lamm-*` claims, so I did not run claim-checker. `git status` shows my files are `research/excavator/lamm-2026-10-20/` (including OUTCOME.json), the `jobs/llull/ledger/outcomes.jsonl` change, and the FETCH_QUEUE append. The other modified paths (claim-kit files, `jobs/lambertini/`, `research/excavator/lambertini-2026-10-20/`, `research/readiness/act_overrides/`) are not mine. Nothing was committed.

**Expected new ready orders:** 0 now. Subject to the owner rulings above, about 20 to 23 pooled ends could become claim-eligible once original texts are obtained.

SUMMARY: Lamm probe on 40 fixed-term orders found 23 own-term ends upheld (0.575), well above the 0.25 median. But no plants were inserted or caught, so the gate failed and nothing was scaled. Zero claims are enabled, and every upheld end still lacks original text. Outcomes are recorded for L-20, -21 and -22; claim-kit was not changed. Next step is to rerun the probes with plants.
