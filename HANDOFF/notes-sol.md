# Sol's handoff notes

## 2026-11-08 ET: Montfaucon first 50 page checks prepared

- **Done:** PR #225 merged the fail-closed page-check interface after Ubuntu/Windows road checks, local Mission checks, and the output-branch check. On `sol/montfaucon-2026-11-08`, the m001 50-order pilot has 34 independently agreed passes and 16 agreed failures across July/November 1940 Federal Register, GPO Indian Reservations 1912, GPO Panama Canal 1922 and GPO Trading with the Enemy Act 1920. `research/montfaucon/checks/m001-*.jsonl` pins both reviews, source fragments, held text and passing page images. Local assembly accepts all 50 and rejects none. No claims, provisional statuses, census, codebook, source grades, or restricted ProQuest files changed.
- **Controls:** Two full Panama Luna assignments missed the planted Section 1/2 substitution; one July FR Luna control matched the neighboring order's closing number. All cheap-tier real verdicts were quarantined. Fresh stronger readers caught all controls and reviewed in small blocks. See `research/montfaucon/CONTROL_INCIDENT.md` and Kean F-20261108-montfaucon-control-binding.
- **Gate/cost:** Native Bentham wrapper cannot gate the current page-check action because its PLAN row has `orders: 0` and no rate. Direct `gate.py` yields conditional CONTINUE after 50 (34/50), with declared Beta(1,1) prior and plan cost proxy $0.38/order. Actual model tokens and spend are unavailable; `COST.md` does not call them zero.
- **Running:** These 50 research records are prepared locally, not yet merged. No new production job has been dispatched by this wave. The ten rank-13 replica orders have existing fail/unsure reviews from PR #194 and require no duplicate credit.
- **Next:** Verify tracker delta from the 34 passes, prepare the 50-record pilot PR without branch-run outputs, then continue the 831 remaining rank-10 original page targets in 50-order batches. Recheck current main and Bracton/Cujas notes before integration. Stop any lane on a missed planted control.
- **Asks:** None.

## 2026-10-18: claim-kit implementation and runner validation in progress

- **Done:** Created `sol-claim-kit` from `wire-new-sources` commit `5e3e00b2c1bdb0fcd68202b4aff735f7dd691353`. Read the complete Sol brief, handoffs, claim guide, schema, funnel and existing runner. Added generic evidence discovery, exact-span excavators, whole-corpus dossiers and status leads, blank decision sheets, fail-closed Stage19 assembler, reservations CLI and model-neutral protocol. Only pointers added to AGENTS/readiness. Source metadata on the base branch pins 14,972 identities / 3,359 provisional statuses; tracker baseline is **130 ready**.
- **Running:** Initial `jobs/claim-kit` branch run. Read `output/STATUS.json`, `SUMMARY.json`, `ASSEMBLY_REPORT.json` and the exact `commit_run` before using dossiers. Corpus outputs are leads, never accepted findings. Implementation has separate ingest/excavator/assembler agents and independent integration review; the pilot has not yet been promoted.
- **Next:** Inspect full-corpus coverage, fix runner failures if any, then produce and separately review 50 disjoint decided orders in eligible families. Record exact reviewer outcomes, checker and tracker effect.
- **Asks:** None while validation is running.
- **Do not:** Merge this branch, change census/status/ledger/codebook, edit others' claims or notes, treat an AI review as a human review, or infer pilot savings from synthetic tests. Model billing/cache token telemetry is unavailable in this session; do not fabricate token-per-claim measurements.
