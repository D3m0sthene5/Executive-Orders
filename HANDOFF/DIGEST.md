# Daily research digest

New York date: 2026-10-21. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 278 of 14,972 orders (1.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 342 | 3,359 | 10.2% |
| When and how it ended (NO), or what keeps it operating now (YES) | 300 | 3,359 | 8.9% |

## Changes since the previous day

Comparison snapshot: 2026-10-20; intervening runs may be absent.
- lewis-originals: fragments_written: unavailable → 11

## Top shared unlocks

- orders_unblocked: 4644; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 2750; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and decide the custody grade; a replica scan counts only after that decision is written into the codebook; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 435; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 19; kind: one_source; action: Retrieve shared source STAT::66 Stat. 259; blocker: SHARED_SOURCE_NOT_RETRIEVED:STAT::66 Stat. 259
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-claude.md: - **Asks:** `@Owner`: 1. `ProQuest Pre-1937 Orders/LRS-10-21-Cold-Calls-Plain.pdf` is not a ProQuest file (listed in STRAY_FILES.csv); remove it if it was uploaded by mistake. 2. The upload sits at the repo root, not under `research/pre-1937-sources/`; both are read, so moving it is optional. 3. Whether a replica scan may count as the original after a page check is still your codebook call; the tracker rule is ready to write once decided.
- notes-codex.md: No open ask recorded in newest entry.
- notes-sol.md: - **Asks:** None while validation is running.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39668376194)
