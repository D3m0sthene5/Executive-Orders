# Readiness tracker job

Counts orders that are **ready for human review**: the machines have done every
step the order needs. Output: [`output/TRACKER.md`](output/TRACKER.md) (read this first),
`output/SHARED_UNLOCKS.csv` (one action → many orders, largest first),
`output/READINESS_BY_ORDER.csv` (all 14,972 orders, one row each) and
`output/SUMMARY.json`.

Runs daily (the `DAILY` file), whenever this folder changes, or by hand from the
Actions tab. The tests in `test_tracker.py` run first; the tracker does not run if
they fail.

## Steps per order

| Step | Done when |
|---|---|
| `provisional_status` | It has a provisional YES/NO (`research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`) |
| `original_text` | Stage 19 marks a locally preserved original, Stage 21 captured the official PDF, or its claim's original passes the gate |
| `clause_inventory`, `ending_or_current_basis`, `savings_residuals`, `counterevidence` | That part of its claim in `research/readiness/claims/` passes `claim_gate.py`; `counterevidence` also needs no quarantined relationship conflict |
| `shared_sources` | Only for orders citing a Stage 20 shared source: all of them retrieved |
| `opus_media` | Only for Opus cases: an evidence image is matched to the order by content |

A step recorded in `research/readiness/EXHAUSTED.jsonl` counts as done. An order is
ready when all its steps are done and either its claim passes the gate in full
(tier `complete_claim`) or the only remaining gaps are exhausted steps (tier
`machine_exhausted`). Human verification is not counted here.

To add a new source of evidence, add its file to `P` in `tracker.py`, its folder
to `needs.txt`, and a test.
