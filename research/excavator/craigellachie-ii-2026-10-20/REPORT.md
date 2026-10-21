# Craigellachie II: retry after fetch (2026-10-20)

**Pool:** Llull CRAIG2, 5 orders (census D-20261020-26).

**Plants caught:** None scored. `/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/craig2/plant_keys` does not exist. Both reviewers also reported receiving no plants (batch 01 had 4 producer proposals, batch 02 had none). So the planter step did not run or wrote nothing. The plant condition of the gate has no evidence, and the gate fails on both parts (no upheld claim, no plant flagged). No upheld claims existed, so none had to be voided. No file matching `claude-craig2-*` is in `research/readiness/claims`, so no plant can be there.

**Claim checker:** Rerun by the reviewers.
- Batch 01: 1 checked, 1 passed, 0 failed.
- Batch 02: 0 checked.
- Nothing was written to the claims folder.

| Batch | Attempted | Upheld | Rejected | Blocked (justified) | Notes |
|---|---|---|---|---|---|
| 01 | 4 | 0 | 1 (EO 11367) | 3 (EO 8399, 11293, 11299) | EO 11367 failed D6: EO 11540 removed the inserted words on 1970-07-01. Its end quote also has no date. |
| 02 | 1 | 0 | 0 | 1 (EO 10061) | The own-terms end of 1950-06-30 is not confirmed. The statute TERM records carry the mechanism `own_terms_condition`, so citing them would mislabel the end. |

**Forecast vs outcome:**

| Forecast | Predicted | Measured | Outcome id |
|---|---|---|---|
| L-20261020-26, upheld per attempt | p10 0.0, p50 0.1, p90 0.4 | 0.0 | O-20261020-15 |
| L-20261020-27, P(at least 1 of 5 upheld) | 0.45 | 0 | O-20261020-16 |

The measurement is at the p10 end of the interval and within it. The source is `research/excavator/craigellachie-ii-2026-10-20/OUTCOME.json`. The outcome rows are in `jobs/llull/ledger/outcomes.jsonl`, modified but not committed (the protocol commits only the preregistration ledger).

**Expected new ready orders:** 0. The remaining blockers are the FETCH lines already queued (HUD and OMB organization records, 31 U.S.C. 16a/16c, 84 Stat. 785, the sec. 303(h) regulations, 60 Stat. 853 and 858). Retry once those land.

**Git status:** My paths show `research/excavator/craigellachie-ii-2026-10-20/` untracked and `jobs/llull/ledger/outcomes.jsonl` modified. `FETCH_QUEUE.jsonl` is modified because of appended lines. The Lambertini claims file and `research/readiness/act_overrides/` are not mine.

SUMMARY: Craigellachie II (CRAIG2, 5 orders) upheld 0. EO 11367 was rejected on D6, and 4 blocks were justified. No plant keys exist, so the planter step did not run and plants caught is unscored. Nothing was voided and no claims were written. Llull outcomes recorded: 0.0 per attempt and 0 for at-least-1, at the forecast's p10 end. Uncommitted: outcomes.jsonl and the OUTCOME.json folder.

**Coordinator note:** both planter agents were denied by the auto-mode classifier when writing a defective record into the in-repo review packet; nothing was planted and the denial was not worked around. Protocol now plants only in scratch copies.
