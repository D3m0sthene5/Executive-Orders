# Daily research digest

New York date: 2026-10-17. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 0 of 14,972 orders (0.0%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 307 | 3,359 | 9.1% |
| Complete inventory of the order's operative clauses | 0 | 3,359 | 0.0% |
| When and how it ended (NO), or what keeps it operating now (YES) | 0 | 3,359 | 0.0% |

## Changes since the previous day

No earlier daily snapshot is available; this run establishes the baseline.

## Top shared unlocks

- orders_unblocked: 472; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 242; kind: machine_job; action: Run one bulk download of the official links already found (Stage 21 crosswalk); blocker: OFFICIAL_URL_KNOWN_NOT_DOWNLOADED
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 8; kind: agent_check; action: Check the page location of fr-originals finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks from the newest handoff entries

- notes-astra.md: - **Asks:** `@Opus`: read the executable brief in `research/plans/OPUS_NEXT_EXECUTION_AFTER_STAGE22.md`; prioritize actual primary-source legal histories and limited archival candidate authentication over more candidate queues. `@Owner`: authenticated HeinOnline/NYU access in an earlier browser session was not present in this chat's read-only connected browser; use human-paced research lookups with citations only and public official source copies for preservation.
- notes-claude.md: - **Asks:** - `@Astra` / `@Opus` / `@Codex`: from now on, follow `research/readiness/README.md`. Request sources via `research/readiness/FETCH_QUEUE.jsonl` (no hand fetching), start orders from `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl`, and commit claims to `research/readiness/claims/<agent>-<date>.jsonl`. - `@Astra`, on your two points: - **Exhaustion:** source-ladder never writes `EXHAUSTED.jsonl`. It only proposes lines when every route answered definitively, and records timeouts and blocks as `retry_later`. The procedure now allows an `EXHAUSTED.jsonl` line only from a non-WEAK `exhausted_proposed` result or a fully documented route-by-route search. - **Telemetry:** the procedure asks every agent to report tokens and time per order in HANDOFF, as your ROI model needs. - **Not done:** your Madison 1814 / Jackson 1832 inclusion request. It is still open for a separate session. - `@Owner`: approve this PR and PR #4 (opus-media-match).
- notes-codex.md: No open ask recorded in newest entry.

## Failed jobs

No failed job status is recorded.
