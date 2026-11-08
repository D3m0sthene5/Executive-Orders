# Sol's handoff notes

## 2026-11-08 13:03 ET: Bracton board and YES packets staged for Monday review

- **Done:** Recomputed Bentham's $300 plan after filtering historical recoveries through current tracker readiness (48 old rejected-mechanical identities, 9 still not ready). Fixed Valla's canonical v2 review-context acceptance. All 35 Valla and 13 Bentham candidate/planner tests pass. `research/bracton/STAGING.md` records the packet seals and source custody; Kean findings F-20261108-1 through F-20261108-4 record attempts and lessons. Cujas c01 identities are disjoint. EO:10538 is locked to `sol-bracton`.
- **Running:** No producer, reviewer, or job. Board packet EO:10010/10923/10944 and YES packet EO:10538 both pass fresh offline dispatch checks in this checkout. Four APP archive captures are retained in `jobs/bracton-source-custody/`; ten exact public PDFs are in local untracked job caches and must be reacquired in a fresh checkout.
- **Next:** After Monday 2026-11-09 6 PM ET reset, pull main and Cujas, reconcile any changed frozen inputs, recheck dispatch, then follow Bentham recovery/correction gates and run different-family blind reviews with controls. YES remains staged until budget and gate permit. File only accepted claims and report checker/tracker deltas.
- **Asks:** @Owner: none.
- **Do not:** Treat a staged source match as a legal finding or human review; dispatch from a stale receipt; edit Cujas's c02 packet or another agent's claims; check out restricted ProQuest or `_attempts` trees.

## 2026-10-18: claim-kit implementation and runner validation in progress

- **Done:** Created `sol-claim-kit` from `wire-new-sources` commit `5e3e00b2c1bdb0fcd68202b4aff735f7dd691353`. Read the complete Sol brief, handoffs, claim guide, schema, funnel and existing runner. Added generic evidence discovery, exact-span excavators, whole-corpus dossiers and status leads, blank decision sheets, fail-closed Stage19 assembler, reservations CLI and model-neutral protocol. Only pointers added to AGENTS/readiness. Source metadata on the base branch pins 14,972 identities / 3,359 provisional statuses; tracker baseline is **130 ready**.
- **Running:** Initial `jobs/claim-kit` branch run. Read `output/STATUS.json`, `SUMMARY.json`, `ASSEMBLY_REPORT.json` and the exact `commit_run` before using dossiers. Corpus outputs are leads, never accepted findings. Implementation has separate ingest/excavator/assembler agents and independent integration review; the pilot has not yet been promoted.
- **Next:** Inspect full-corpus coverage, fix runner failures if any, then produce and separately review 50 disjoint decided orders in eligible families. Record exact reviewer outcomes, checker and tracker effect.
- **Asks:** None while validation is running.
- **Do not:** Merge this branch, change census/status/ledger/codebook, edit others' claims or notes, treat an AI review as a human review, or infer pilot savings from synthetic tests. Model billing/cache token telemetry is unavailable in this session; do not fabricate token-per-claim measurements.
