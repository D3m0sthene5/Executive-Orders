# Daily research digest

New York date: 2026-11-06. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,185 of 14,998 orders (7.9%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator): not measured yet; `jobs/domesday-register/output/UNNUMBERED_SUMMARY.json` is missing.

Generation: `42299247852-1:808c1a847250f0283cf941324757d010e780f0c6503ac3fa383e48c9b2462bb1` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,298. The other 10,700 have not been researched yet.

Ready by text evidence: {'original_supported': 660, 'transcription_dependent': 525}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 1,146; quotation rechecks: 1,146. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 560. Confirmations rejected: {'grade_not_a_working_text_grade': 3, 'not_confirmed': 4818}.

## Changes since the previous day

Comparison snapshot: 2026-11-05; intervening runs may be absent.
- claim-checker: claim_lines_found: 1466 → 1732; claims_all_checks_passed: 1369 → 1579; claims_checked: 1466 → 1732; claims_gate_passed: 1376 → 1642
- claim-drafts: orders_with_any_conflict: 434 → 707; orders_with_draft: 4291 → 14919; undecided_orders_with_draft: 0 → 10628
- gessner-cards: not_researched: 10681 → 10700; numbered_series_orders: unavailable → 14998; one_step_from_ready: 43 → 219; orders: 14972 → 14998
- gratian-niebuhr-leads: date_leads: unavailable → 63; date_leads_in_census: unavailable → 36; network_requests: unavailable → 0; resolved_references: unavailable → 10
- kean: decisions: 23 → 45; findings: 146 → 211; open_owner_questions: 2 → 3
- lachmann: assessed: 7738 → 5832; complete_text_confirmed: 3370 → 2104; confirmed: 1764 → 1011; identity_confirmed: 3716 → 2493
- lambertini: counterevidence_records: 1248 → 1245; pool_LAMBC: 64 → 225; pool_LAMBS: 64 → 36
- later-events: catalog_records_post_cutoff_ignored: 0 → 3; catalog_records_used: 6938 → 6941; catalog_records_with_notes: 5063 → 5064; decided_no_with_full_revocation_candidate: 909 → 944
- mabillon-held-printings: frame_lead: unavailable → 108; frame_orders: unavailable → 5943; frame_strong: unavailable → 762; frame_targets: unavailable → 870
- mabillon-nara: bad_lines: unavailable → 0; bytes_downloaded: unavailable → 1846668793; chunk_errors: unavailable → 0; chunks_read: unavailable → 1410
- mabillon-scan-inventory: commons_category_pages: unavailable → 10; commons_files: unavailable → 67; frame_orders_below_5076_inside_a_listed_range: unavailable → 0; ia_items: unavailable → 151
- niebuhr-verify: pages_failed: unavailable → 126; pages_fetched: unavailable → 98; requests_used: unavailable → 186; results: unavailable → 301
- ptolemy-custody: kept_this_run_bytes: unavailable → 928544414; kept_total: unavailable → 3060; legal_conclusions: unavailable → 0; orders_with_a_kept_source: unavailable → 2528
- readiness-tracker: formal_revocation_after_earlier_cessation: unavailable → 0; numbered_series_orders: unavailable → 14998; orders_total: 14972 → 14998; orders_with_provisional_status: 4291 → 4298
- selden-fr-acting: bytes_downloaded: unavailable → 2794249410; extracts_committed_bytes: unavailable → 255048664; failures: unavailable → 1; issues_gpo_premis_match: unavailable → 804
- selden-fr-citers: bytes_downloaded: unavailable → 8156887; citations: unavailable → 19726; citations_acting_on_target: unavailable → 5534; committed_text_bytes: unavailable → 182590553
- selden-statutes: acting_pairs: unavailable → 143; acting_pairs_located: unavailable → 30; attempted: unavailable → 1956; bytes_downloaded: unavailable → 419580437
- shepard-citations: land_targets: 3547 → 3549
- source-ladder: attempts_logged: 23 → 70; bytes_downloaded: 822061830 → 640005978; distinct_new_source_hashes: 23 → 36; embedded_cite_items: 16 → 10
- status-history: census_identities: 14972 → 14998; editorial_edges_raw_span_verified: 15660 → 15656; identities_with_history: 7650 → 7651; identities_with_own_observation: 7448 → 7449
- theophilus-sources: cfr_targets_planned: unavailable → 566; eligible_yes_orders: unavailable → 346; failures_total: unavailable → 74; orders_named_in_notices: unavailable → 162
- tischendorf-originals: bytes_downloaded: unavailable → 27441440056; leads: unavailable → 492; order_errors: unavailable → 0; replacement_strong: unavailable → 25
- tsiolkovsky-trajectory: W_hours: unavailable → 6630.8; W_max_hours: unavailable → 18191.0; a_hours_per_day2_latest: unavailable → -93.05; days: unavailable → 21
- x1-class-engine: modern_families_5_plus: 193 → 196

## Top shared unlocks

- orders_unblocked: 2762; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 2557; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 535; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

- A-20261106-1 (2026-11-06, claude-selden): Does a statute that abolishes an order's body, or ends the emergency its term depends on, without naming the order, date the order's end? Default: no.
- A-20261106-dagron-nyu (2026-11-06, Claude): NYU Film 709/Hein: lift the 2026-10-19 no-microfilm rule for this collection, and approve staged images under research/dagron/acquired?
- A-20261106-pothier (2026-11-06, Claude): Adopt each Pothier family doctrine (yes/no each); rule on amending orders and PLO tables? research/pothier/REPORT.md

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42299247852)
