Lambertini III: ending instruments (2026-10-20)

**Pool.** LAMB3: 82 orders under 28 ending instruments. Certified stays 0, and nothing was adopted or committed.

**Plants.** 5 of 5 caught, 0 missed.
- Batches 01, 03, 04, 06 and 07 each had one planted wrong first-end date: EO 14055, EO 13986, EO 10373, EO 13123 and EO 5624.
- Each reviewer rejected exactly that order.
- I confirmed the only differences between work/ and review_copy/ are those 5 dates.
- Batches 05 and 08 have no plant key and their review_copy matches work/ exactly. They are unscored for plants, not void.
- Batch 02 has no review packet, so it is unscored.
- No planted claim line is in research/. The reviews under instruments/ quote the planted dates when describing the rejections.

| Batch | Attempted | Upheld | Rejected | Blocked | Plant | Copied to claims/ |
|---|---|---|---|---|---|---|
| 01 (probe) | 8 | 6 | 1 | 1 | caught (1/1) | 6 |
| 02 | 8 | not reviewed | - | - | unscored | 0 |
| 03 | 8 | 6 | 1 | 1 | caught | 6 |
| 04 | 13 | 8 | 3 | 2 | caught | 8 |
| 05 | 15 | 12 | 0 | 3 | unscored | 12 |
| 06 | 8 | 3 | 1 | 4 | caught | 3 |
| 07 | 8 | 4 | 1 | 3 | caught | 4 |
| 08 | 14 | 13 | 0 | 1 | unscored | 13 |
| **Total** | **82** | **52** | 7 | 15 | 5/5 | **52** |

- In batch 04 the two non-plant rejects, EO 10169 and EO 10390, should be blocked instead.
- No savings state was overturned.
- Probe gate: batch 01 upheld 6 of 8 and overturned 0 savings states, so it passes. The plant clause (catch at least 2 of 3) could not be tested as written, because the planter planted only 1.
- The claims are in `research/readiness/claims/claude-lambertini-i{01,03,04,05,06,07,08}-2026-10-20.jsonl` and are copied from work/.
- Review records, readings and order logs are in `research/excavator/lambertini-2026-10-20/instruments/<NN>/`, with `OUTCOME.json` at the top level.

**Claim checker** on the 52 upheld claims: 49 pass every check, none fail the gate, and 3 are unverified.
- EO 10324 and EO 10467 are unverified because their ending source (the EO 10480 FR text) is custody-record only.
- EO 12977 is unverified because of unverified later-event sources.

**Forecast vs outcome (Llull, recorded as O-20261020-35 to -38):**

| Forecast | Quantity | Forecast | Measured |
|---|---|---|---|
| L-20261020-32 | upheld per attempt | p10 0.06, p50 0.65, p90 1.0 | 0.634 (52 of 82; 0.703 of the 74 reviewed) |
| L-20261020-33 | probe gate passes | 0.6 | 1 (yes, with the plant-clause caveat above) |
| L-20261020-34 | plant catch share | p10 0.06, p50 0.67, p90 1.0 | 1.0 (5 of 5) |
| L-20261020-35 | claims enabled | p10 4, p50 40, p90 80 | 49 |

Llull flagged L-32 and L-35 as exceeding the census ceiling, so a gate missed a route. The ledger passes `llull check`. The outcomes are written to `jobs/llull/ledger/outcomes.jsonl` but not committed.

**Expected new ready orders:** 49 now. EO 10324, EO 10467 and EO 12977 follow once their sources are held or an `act_overrides` record is added. Four more are likely after a one-claim re-review, because their rejection came from the plant, not the genuine claim: EO 14055, EO 13986, EO 13123 and EO 5624. I did not copy those. Batch 02's 8 claims also need the planter and reviewer to run.

SUMMARY: 52 of 82 upheld (0.634). All 5 planted defects caught; batches 02, 05 and 08 are unscored for plants. 52 claims copied, 49 pass the checker. Llull outcomes recorded. Batch 02 never reviewed; four plant-rejected claims await re-review. Nothing committed, certified 0.
