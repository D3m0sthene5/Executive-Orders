# Sol's handoff notes

## 2026-10-18: claim-kit implementation and runner validation in progress

- **Done:** Created `sol-claim-kit` from `wire-new-sources` commit `5e3e00b2c1bdb0fcd68202b4aff735f7dd691353`. Read the complete Sol brief, handoffs, claim guide, schema, funnel and existing runner. Added generic evidence discovery, exact-span excavators, whole-corpus dossiers and status leads, blank decision sheets, fail-closed Stage19 assembler, reservations CLI and model-neutral protocol. Only pointers added to AGENTS/readiness. Source metadata on the base branch pins 14,972 identities / 3,359 provisional statuses; tracker baseline is **130 ready**.
- **Running:** Initial `jobs/claim-kit` branch run. Read `output/STATUS.json`, `SUMMARY.json`, `ASSEMBLY_REPORT.json` and the exact `commit_run` before using dossiers. Corpus outputs are leads, never accepted findings. Implementation has separate ingest/excavator/assembler agents and independent integration review; the pilot has not yet been promoted.
- **Next:** Inspect full-corpus coverage, fix runner failures if any, then produce and separately review 50 disjoint decided orders in eligible families. Record exact reviewer outcomes, checker and tracker effect.
- **Asks:** None while validation is running.
- **Do not:** Merge this branch, change census/status/ledger/codebook, edit others' claims or notes, treat an AI review as a human review, or infer pilot savings from synthetic tests. Model billing/cache token telemetry is unavailable in this session; do not fabricate token-per-claim measurements.
