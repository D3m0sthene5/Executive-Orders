# Readiness tracker job

Counts orders that are **ready for human review**: the machines have done every
step the order needs. Output: [`output/TRACKER.md`](output/TRACKER.md) (read this first),
`output/SHARED_UNLOCKS.csv` (one action → many orders, largest first),
`output/READINESS_BY_ORDER.csv` (all 14,972 orders, one row each) and
`output/SUMMARY.json`.

Runs daily (the `DAILY` file), whenever this folder or `research/readiness/` changes
(`triggers.txt`), after the jobs it reads when they run together (`after.txt`), or by
hand from the Actions tab. `SUMMARY.json` → `inputs.job_outputs_used` shows which job
outputs it read. The tests in `test_tracker.py` run first; the tracker does not run if
they fail.

## Steps per order

| Step | Done when |
|---|---|
| `provisional_status` | It has a provisional YES/NO (`research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`) |
| `original_text` | Stage 19 marks a locally preserved original, Stage 21 captured the official PDF, fr-originals found it with high confidence (medium/low show `ORIGINAL_FOUND_NEEDS_PAGE_CHECK`), opus-media-match matched an Opus copy to it, or its claim's original passes the gate and claim-checker |
| `clause_inventory`, `ending_or_current_basis`, `savings_residuals`, `counterevidence` | That part of its claim in `research/readiness/claims/` passes `claim_gate.py` **and** claim-checker passed that step for this exact claim (`jobs/claim-checker/output/PER_CLAIM.json`, matched by claim sha256); `counterevidence` also needs no quarantined relationship conflict |
| `shared_sources` | Only for orders citing a Stage 20 shared source: all of them retrieved (Stage 20 records or `jobs/source-ladder/output/SOURCES.jsonl`) |
| `opus_media` | Only for Opus cases: opus-media-match resolved every medium its records cite (`all_cited_media_resolved`); otherwise a specific blocker (re-fetch needed, original not kept, ambiguous match, none cited). Falls back to the Stage 20 audit until that job has run |

A step recorded in `research/readiness/EXHAUSTED.jsonl` counts as done. An order is
ready when all its steps are done and either its claim passes the gate in full
(tier `complete_claim`) or the only remaining gaps are exhausted steps (tier
`machine_exhausted`). Human verification is not counted here.

To add a new source of evidence, add its file to `P` in `tracker.py`, its folder
to `needs.txt`, and a test.

## Historical census candidate track

The separately run census-candidates job publishes an item-level register for the early rangers and Lord's index appearances. Its counts are appended in a separate section of TRACKER.md and SUMMARY.json when the job output exists. They are excluded from the 14,972 working-EO denominator. No catalog hit or scanned document is automatically admitted.
