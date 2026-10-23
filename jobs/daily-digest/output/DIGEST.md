# Daily research digest

New York date: 2026-10-22. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 280 of 14,972 orders (1.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,403. The other 11,569 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,403 | 3,403 | 100.0% |
| Original text saved in the project | 2,356 | 3,403 | 69.2% |
| Complete inventory of the order's operative clauses | 345 | 3,403 | 10.1% |
| When and how it ended (NO), or what keeps it operating now (YES) | 303 | 3,403 | 8.9% |

## Changes since the previous day

Comparison snapshot: 2026-10-20; intervening runs may be absent.
- census-candidates: items_with_LOC_XML_transcript: 9 → 10
- claim-checker: claim_lines_found: 385 → 389; claims_all_checks_passed: 297 → 299; claims_checked: 385 → 389; claims_gate_passed: 300 → 304
- claim-drafts: decided_orders_with_draft: 3359 → 3403; drafts_whose_only_remaining_gaps_are_judgment_fields: 1115 → 1145; of_which_decided: 1115 → 1145; orders_with_any_conflict: 421 → 434
- clause-drafts: clauses_total: 70600 → 70615; fragments_from_app_transcription: 4968 → 4964
- csc-annual-reports: bytes_downloaded: unavailable → 5103541119; cache_hits: unavailable → 0; citations: unavailable → 842; orders_located: unavailable → 798
- domesday-register: orders: unavailable → 14972; with_any_text_file: unavailable → 14882; with_date: unavailable → 14887; with_title: unavailable → 10139
- family-rules: saved_texts_scanned: 46996 → 50653
- lambertini: decided_orders_with_draft: 3359 → 3403; packet_targets: 807 → 835; packets: 84 → 109; pool_LAMBS: 91 → 93
- lewis-originals: fragments_written: unavailable → 0
- official-fixity: carried_forward: 5136 → 5158; checked_this_run: 18 → 1; files: 5154 → 5159; premis_bytes_read_this_run: 327680 → 0
- readiness-tracker: orders_with_provisional_status: 3359 → 3403; ready_for_human_review: 278 → 280
- source-ladder: attempts_logged: 50 → 41; bytes_downloaded: 475352251 → 811147260; distinct_new_source_hashes: 38 → 35; earlier_found_failing_todays_checks: 2 → 0
- status-history: printed_snapshot_undecided_identities: 2267 → 2240; undecided_with_history: 4817 → 4773; undecided_with_own_observation: 4640 → 4596
- valla: active_claims: 384 → 388
- x1-class-engine: modern_families_5_plus: 188 → 189

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
- notes-claude.md: No open ask recorded in newest entry.
- notes-codex.md: No open ask recorded in newest entry.
- notes-sol.md: - **Asks:** None while validation is running.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39864902483)
