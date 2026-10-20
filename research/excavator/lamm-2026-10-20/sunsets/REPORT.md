### Lamm II: sunsets (2026-10-20)

**Queue lines added:** 28 appended to `research/readiness/FETCH_QUEUE.jsonl` (6 Lambertini, 22 Lamm). I skipped EO 9299, 12285, 12575 and 13090. The file now has 302 lines. Nothing is committed.

**Plants caught: 3 of 3, so no batch is void.** Each plant was a wrong first-end date in `CLAIMS.proposed.jsonl`, and each reviewer flagged the exact record without seeing the key.
- batch_03: EO 10270, planted 1952-12-31 (correct 1952-07-01).
- batch_04: EO 12660#lead, planted 1992-12-16 (correct 1993-12-16).
- batch_05: EO 13147#sec1, planted 2002-09-07 (correct 2002-03-07).

**Plant text in research/:** none in any claim line or review record. The only matches are the reviewers' own VERDICTS.json notes, which describe the defects they caught.

| Batch | Attempted | Upheld | Rejected | Negative confirmed | Claim lines copied |
|---|---|---|---|---|---|
| batch_03 | 20 | 7 (6 whole, 1 partial) | 1 (EO 10270, the plant) | 12 | 6 (EO 9886, 10110, 10145, 10164, 10345, 10957) |
| batch_04 | 20 | 10 (8 whole, 2 partial) | 3 claim lines (EO 12660 plant, EO 12358, EO 12528) | 10 | 4 (EO 12219, 12229, 12427, 12970) |
| batch_05 | 14 records plus 1 claim line | 2 (1 whole, 1 partial) | 1 (EO 13147 claim line, the plant) | 12 | 0 |

- **Claim files written:** `research/readiness/claims/claude-lamm-s03-2026-10-20.jsonl` (6 lines) and `claude-lamm-s04-2026-10-20.jsonl` (4 lines). No s05 file, because its only claim line was the planted one.
- **Review records:** `research/excavator/lamm-2026-10-20/sunsets/batch_03/`, `batch_04/` and `batch_05/`. Each holds the OWN_TERM_END_RECORDS, producer telemetry and VERDICTS files.
- **Claim checker on the 10 copied lines:** all 10 passed all checks, with no mechanical failures. EO 9886 passed here, where the batch reviewer's run had flagged two custody-record-only checks. I restored the checker's output files in the repo afterwards.
- **Not copied:** EO 12358 and EO 12528 (claim lines must cite their extending orders, EO 12415 and EO 12604), and EO 12660 (needs the corrected date and a fresh checker run).

**Forecast vs outcome (L-20261020-23, batch_03 claims enabled):**
- Forecast was p10 0, p50 5, p90 10. Measured: **6**, so it landed just above the median and well inside the interval.
- Recorded in Llull as O-20261020-25, and `llull check` is ok.
- I merged the result into the existing `OUTCOME.json` without overwriting its earlier probe data.

**Expected new ready orders:** none. Claim-enabled whole ends are AI hypotheses until independent human certification, and the certified count stays 0. Ten claim lines are now eligible for human review.

**Residual risks:**
- EO 10110 may have an extension outside the held texts.
- The enlistment orders (EO 10145, 10164, 10345) are accepted at the window cutoff as their end.
- EO 12970 is weak: a charter renewal is possible but none is held.

SUMMARY: Plants 3/3 caught (EO 10270, 12660, 13147); no batch void. Copied 10 upheld claim lines (s03 x6, s04 x4); checker 10/10 passed. Rejected lines (EO 12358, 12528, 12660, 13147) were not copied. Llull L-20261020-23 recorded: measured 6 against p50 5. 28 queue lines added. No new ready orders; certified count stays 0. Nothing committed.
