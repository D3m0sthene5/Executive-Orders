# Daily research digest

New York date: 2026-10-22. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 280 of 14,972 orders (1.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 344 | 3,359 | 10.2% |
| When and how it ended (NO), or what keeps it operating now (YES) | 302 | 3,359 | 9.0% |

## Changes since the previous day

Comparison snapshot: 2026-10-20; intervening runs may be absent.
- census-candidates: items_with_LOC_XML_transcript: 9 → 10
- claim-checker: claim_lines_found: 385 → 387; claims_all_checks_passed: 297 → 299; claims_checked: 385 → 387; claims_gate_passed: 300 → 302
- csc-annual-reports: bytes_downloaded: unavailable → 5103541119; cache_hits: unavailable → 0; citations: unavailable → 842; orders_located: unavailable → 798
- domesday-register: orders: unavailable → 14972; with_any_text_file: unavailable → 11517; with_date: unavailable → 14887; with_title: unavailable → 10139
- family-rules: saved_texts_scanned: 46996 → 50581
- lewis-originals: fragments_written: unavailable → 11
- official-fixity: carried_forward: 5136 → 5154; checked_this_run: 18 → 3; files: 5154 → 5157; premis_bytes_read_this_run: 327680 → 0
- readiness-tracker: ready_for_human_review: 278 → 280
- source-ladder: attempts_logged: 50 → 30; bytes_downloaded: 475352251 → 850521061; distinct_new_source_hashes: 38 → 29; earlier_found_failing_todays_checks: 2 → 0
- valla: active_claims: 384 → 386

## Top shared unlocks

- orders_unblocked: 5347; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 2750; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and decide the custody grade; a replica scan counts only after that decision is written into the codebook; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-claude.md: - **Asks:** `@Owner`: add search keys as repository secrets to switch on the big engines (`GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX`, `BING_SEARCH_KEY`, `BRAVE_SEARCH_KEY`, `SERPAPI_KEY`, `NARA_API_KEY`); the jobs pick them up on the next run with no code change.
- notes-codex.md: No open ask recorded in newest entry.
- notes-sol.md: - **Asks:** None while validation is running.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39802916101)
