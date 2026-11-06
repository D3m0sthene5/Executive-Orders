# YES probe: filed per attempt for provisional-YES Federal Register orders

Dorotheus, 2026-11-06 (owner ruling R16). Provisional, AI-reviewed, uncertified.

Draw: 30 orders, seed 20261106, from the 359 orders of Bentham stratum `production.claim_ready.yes.fr` (`research/excavator/dorotheus-yesprobe-2026-11-06/DRAW.json`).

**filed_per_attempt.yes.fr = 7/30 = 0.233** (ice core 2026-11-05: 11/30). Filed: EO:10057, EO:10104, EO:10153, EO:11219, EO:11600, EO:11961, EO:12046 (`research/readiness/claims/dorotheus-2026-11-06-yesprobe.jsonl`).

Blockers among the 23 not filed:

- current-law or statute text not held: 6
- custody_record_only (bytes not held): 6
- later instrument text not held or misregistered: 4
- other: 4
- performance or dates not shown: 2
- already filed (another claim): 1

One order (EO 14131) was upheld but not filed because its batch planted control was missed by two of three reviewers; the Bentham gate returns STOP on a missed control, which owner ruling R16 makes non-binding for this protected work but which still withholds that batch claim.

Bentham: `research/excavator/dorotheus-yesprobe-2026-11-06/evidence/DISPOSITION.json` and `tools/batches.json` declare the probe `pool_into_rates` and `sample_of_remaining`, so `jobs/bentham/measure.py` uses it alone for `filed_per_attempt.yes.fr` on the next plan (30 attempts, the ranking minimum). Per-order details: `research/excavator/dorotheus-sample-2026-11-06/DISPOSITION.csv` (wave=yesprobe) and `research/excavator/dorotheus-yesprobe-2026-11-06/REPORT.md`.
