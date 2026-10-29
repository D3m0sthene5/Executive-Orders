# Daily research digest

New York date: 2026-10-28. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 395 of 14,972 orders (2.6%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,403. The other 11,569 have not been researched yet.

Ready by text evidence: {'original_supported': 298, 'transcription_dependent': 97}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 103; quotation rechecks: 103. These remain work after readiness.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,403 | 3,403 | 100.0% |

## Changes since the previous day

Comparison snapshot: 2026-10-22; intervening runs may be absent.
- astra-source-retention: attempted: 28 → 18; download_bytes: 656737188 → 17475798; extractions_completed: unavailable → 18; http_requests: 29 → 7
- claim-checker: claim_lines_found: 387 → 510; claims_all_checks_passed: 299 → 410; claims_checked: 387 → 510; claims_gate_passed: 302 → 420
- claim-drafts: decided_orders_with_draft: 3359 → 3403; drafts_whose_only_remaining_gaps_are_judgment_fields: 1115 → 1145; of_which_decided: 1115 → 1145; orders_with_any_conflict: 421 → 434
- clause-drafts: clauses_total: 70600 → 70615; fragments_from_app_transcription: 4968 → 4964
- cotton-capture-custody: failed: unavailable → 2; not_web_sources: unavailable → 575; published: unavailable → 526; wanted_hashes: unavailable → 1103
- domesday-register: with_any_text_file: 11517 → 14882; with_date: 14887 → 14909; with_title: 10139 → 14885
- family-rules: saved_texts_scanned: 50581 → 51201
- fr-pages: bytes_committed_this_run: unavailable → 15402202; bytes_downloaded: unavailable → 612727745; cache_hits: unavailable → 0; carried_forward: unavailable → 0
- kean: decisions: unavailable → 11; findings: unavailable → 44; legacy_reports_unsummarized: unavailable → 16; open_owner_questions: unavailable → 10
- lambertini: counterevidence_records: 687 → 672; decided_orders_with_draft: 3359 → 3403; packet_targets: 807 → 835; packets: 84 → 109
- lewis-originals: fragments_written: 11 → 0
- official-fixity: carried_forward: 5154 → 5158; checked_this_run: 3 → 1; files: 5157 → 5159
- readiness-tracker: orders_with_provisional_status: 3359 → 3403; original_replacement_obligations: unavailable → 103; quotation_recheck_obligations: unavailable → 103; ready_for_human_review: 280 → 395
- shepard-citations: edges: unavailable → 10597; edges_with_census_actor: unavailable → 6584; edges_with_census_target: unavailable → 7590; land_targets: unavailable → 3516
- source-ladder: attempts_logged: 30 → 23; bytes_downloaded: 850521061 → 822061830; distinct_new_source_hashes: 29 → 23; embedded_cite_items: 10 → 16
- status-history: printed_snapshot_undecided_identities: 2267 → 2240; undecided_with_history: 4817 → 4773; undecided_with_own_observation: 4640 → 4596
- valla: active_claims: 386 → 421; shared_rationale_references: 291 → 525
- x1-class-engine: modern_families_5_plus: 188 → 195

## Top shared unlocks

- orders_unblocked: 5251; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 2750; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 285; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-boundary-review.md: No open ask recorded in newest entry.
- notes-ce-review-pair1.md: No open ask recorded in newest entry.
- notes-ce-review-pair2.md: No open ask recorded in newest entry.
- notes-ce-review-pair3.md: - **Asks:** none.
- notes-claude.md: No open ask recorded in newest entry.
- notes-codex.md: No open ask recorded in newest entry.
- notes-inventory-a.md: No open ask recorded in newest entry.
- notes-inventory-b.md: No open ask recorded in newest entry.
- notes-nmb-series-independent-review.md: No open ask recorded in newest entry.
- notes-production-batch1.md: No open ask recorded in newest entry.
- notes-production-review1.md: No open ask recorded in newest entry.
- notes-sol.md: - **Asks:** None while validation is running.
- notes-source-first-control-preparer.md: No open ask recorded in newest entry.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/40807928521)
