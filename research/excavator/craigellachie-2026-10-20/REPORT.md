# Craigellachie: last-step orders (2026-10-20)

**Pool:** 23 orders whose only open readiness step is `ending_or_current_basis`. All are provisional NO.

**Forecast vs outcome**
- `L-20261020-1` (upheld per attempt): p10 0.015, p50 0.15, p90 0.35. Measured 0.0, which is below p10. The outside view was 0.06. Recorded as `O-20261020-1`.
- `L-20261020-2` (at least 3 of 23 upheld, P = 0.55): measured 0, so it resolves NO (Brier 0.30). Recorded as `O-20261020-2`.
- Both outcomes cite `research/excavator/craigellachie-2026-10-20/OUTCOME.json`, which I wrote as the measurement file.
- `llull check` passes with one warning: the forecast line is not committed yet.

**Checker:** There are no `claude-craigellachie-*` claim files, so it checked 0 claims. Certified count stays 0.

| Batch | Attempted | Upheld | Rejected | Blocked |
|---|---|---|---|---|
| 01 (EO 12534 committees, 12487) | 7 | 0 | 0 | 7 |
| 02 (EO 12110 committees, 11941, 9303, 9591, 8399) | 8 | 0 | 0 | 8 |
| 03 (1969-73 deletions and reorganizations, 10440) | 8 | 0 | 0 | 8 |

**Blockers** (all 23 judged justified)
- **Report dates not held** (EO 12335, 12401, 12433, 12439, 12499, 12502, 11971, 11973, 11998): the end is a report date plus a set number of days, and no held source gives the report date.
- **Statutes** (Pub. L. 98-525 secs. 1632 and 1511, for EO 12499 and 12502).
- **Pay-period date** (EO 12487).
- **Only an upper bound held** (EO 12534 sec. 3, EO 12110 sec. 1-103, and the 1969-73 orders): a later revocation or deletion is held, but the earlier statutory, reorganization or self-termination source is not.
- **Other** (EO 11849, 11941, 9303, 9591, 8399):
  - EO 11849: its FACA lapse is conditional.
  - EO 11941: the supersession date under EO 12010 sec. 4 is unsettled. Sec. 4 supersedes the whole order, so Schedules 5-7 also end with it.
  - EO 9303, 9591, 8399: the State Department regulations and Reorganization Plan No. 2 of 1946 are not held.
- **Citation error:** the EO 12335 gap text cites 49 FR 61634, but the held text is 46 FR 61633.

**FETCH requests:** 27 new lines in `research/readiness/FETCH_QUEUE.jsonl`, matching the gaps above. They cover EO 12335, 12401, 12433, 12439, 12499 (two), 12502 (two), 12487, 11849, 11971, 11973, 11998, 11941 (two), 9303, 9591, 8399, 11262, 11293 (two), 11299, 11367, 11409, 11468, 11499 and 10440. I did not fetch anything by hand.

**Expected new ready orders after the tracker runs:** 0 now. Each order needs its FETCH sources to arrive and be read before a claim can be upheld.

**git status:** Craigellachie changes are only in `research/excavator/craigellachie-2026-10-20/` and `research/readiness/FETCH_QUEUE.jsonl`. Other workflows' files also show as modified, which I left alone: `jobs/llull/*`, `jobs/mountweazel/mountweazel.py` and `research/plans/LLULL_DESIGN.md`.

SUMMARY: Pool of 23 last-step orders; 0 upheld, 0 rejected, 23 blocked. Every blocker was justified: report dates, statutes and regulations are not held. 27 FETCH lines were queued. The checker had no claims to check. Llull forecasts L-20261020-1 and -2 resolved as misses (measured 0 against p50 0.15 and P 0.55). Certified count stays 0, and the tracker should add no new ready orders until the fetches arrive.
