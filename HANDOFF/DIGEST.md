# Daily research digest

New York date: 2026-11-06. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 1,368 of 14,972 orders (9.1%)**

Generation: `42201458542-1:b41719ca915fd3c3542d174f62b48d728a71c6581cba9df6c86fe94d5ba03259` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,291. The other 10,681 have not been researched yet.

Ready by text evidence: {'original_supported': 812, 'transcription_dependent': 556}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 1,146; quotation rechecks: 1,146. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 560. Confirmations rejected: {'grade_not_a_working_text_grade': 4, 'not_confirmed': 5970}.

## Steps finished (orders with a provisional status)

## Changes since the previous day

Comparison snapshot: 2026-11-05; intervening runs may be absent.
- claim-checker: claim_lines_found: 1466 → 1526; claims_all_checks_passed: 1369 → 1407; claims_checked: 1466 → 1526; claims_gate_passed: 1376 → 1436
- claim-drafts: orders_with_any_conflict: 434 → 707; orders_with_draft: 4291 → 14919; undecided_orders_with_draft: 0 → 10628
- gessner-cards: one_step_from_ready: 43 → 40; ready_for_human_review: 1331 → 1368
- gratian-niebuhr-leads: date_leads: unavailable → 63; date_leads_in_census: unavailable → 33; network_requests: unavailable → 0; resolved_references: unavailable → 10
- kean: decisions: 23 → 45; findings: 146 → 179; open_owner_questions: 2 → 0
- lambertini: counterevidence_records: 1248 → 1245; pool_LAMBC: 64 → 225; pool_LAMBS: 64 → 36
- later-events: catalog_records_post_cutoff_ignored: 0 → 3; catalog_records_used: 6938 → 6941; catalog_records_with_notes: 5063 → 5064; decided_no_with_full_revocation_candidate: 909 → 942
- mabillon-held-printings: frame_lead: unavailable → 108; frame_orders: unavailable → 5943; frame_strong: unavailable → 762; frame_targets: unavailable → 870
- mabillon-nara: bad_lines: unavailable → 0; bytes_downloaded: unavailable → 1846668793; chunk_errors: unavailable → 0; chunks_read: unavailable → 1410
- mabillon-scan-inventory: commons_category_pages: unavailable → 10; commons_files: unavailable → 67; frame_orders_below_5076_inside_a_listed_range: unavailable → 0; ia_items: unavailable → 151
- niebuhr-verify: pages_failed: unavailable → 126; pages_fetched: unavailable → 98; requests_used: unavailable → 186; results: unavailable → 301
- ptolemy-custody: kept_this_run_bytes: unavailable → 929459485; kept_total: unavailable → 1390; legal_conclusions: unavailable → 0; orders_with_a_kept_source: unavailable → 1231
- readiness-tracker: original_replacement_obligations: 1886 → 1146; quotation_recheck_obligations: 1886 → 1146; ready_for_human_review: 1331 → 1368; text_step_provisional_working_text: 1357 → 560
- shepard-citations: land_targets: 3547 → 3549
- status-history: printed_snapshot_undecided_identities: 2240 → 2235; undecided_with_history: 4773 → 4763; undecided_with_own_observation: 4596 → 4591
- theophilus-sources: cfr_targets_planned: unavailable → 609; eligible_yes_orders: unavailable → 364; failures_total: unavailable → 73; orders_named_in_notices: unavailable → 162
- tischendorf-originals: bytes_downloaded: unavailable → 27441440056; leads: unavailable → 492; order_errors: unavailable → 0; replacement_strong: unavailable → 25
- x1-class-engine: modern_families_5_plus: 193 → 196

## Top shared unlocks

- orders_unblocked: 2735; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 2557; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 535; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

No open ask is recorded in the Kean register.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42201458542)
