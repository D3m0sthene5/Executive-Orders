# Daily research digest

New York date: 2026-11-10. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,248 of 14,998 orders (8.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42885309594-1:18cd83e00acfaa721799925ff8696e21c9bd18ede581c8b44f0f6844a0a4dc0c` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,307. The other 10,691 have not been researched yet.

Ready by text evidence: {'original_supported': 723, 'transcription_dependent': 525}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 848; quotation rechecks: 848. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 255. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1571}.

## Changes since the previous day

Comparison snapshot: 2026-11-09; intervening runs may be absent.
- cassiodorus: pages_kept_total: 294 → 296
- claim-checker: claim_lines_found: 1828 → 1897; claims_all_checks_passed: 1660 → 1735; claims_checked: 1828 → 1897; claims_gate_passed: 1738 → 1807
- cotton-capture-custody: not_web_sources: 1175 → 1240; wanted_hashes: 1932 → 1997
- eumenes-nmb-reports: manifest_records: unavailable → 119; orders_covered: unavailable → 126; published: unavailable → 119
- family-rules: saved_texts_scanned: 82852 → 83308
- gessner-cards: not_researched: 10697 → 10691; one_step_from_ready: 216 → 215; ready_for_human_review: 1179 → 1248; with_provisional_status: 4301 → 4307
- kean: decisions: 74 → 75; findings: 286 → 292; open_owner_questions: 1 → 2
- lachmann: assessed: 2360 → 2349; complete_text_confirmed: 1396 → 1365; confirmed: 807 → 776; identity_confirmed: 1146 → 1148
- official-fixity: carried_forward: 7124 → 7116; files: 7124 → 7116
- readiness-tracker: orders_with_provisional_status: 4301 → 4307; original_replacement_obligations: 882 → 848; quotation_recheck_obligations: 882 → 848; ready_for_human_review: 1179 → 1248
- selden-fr-acting: bytes_downloaded: 2729289189 → 1139195521; requests: 129 → 82
- selden-fr-citers: bytes_downloaded: 856889 → 855827; requests: 80 → 71; targets_searched_this_run: 9 → 0; targets_total: 13379 → 13220
- selden-statutes: attempted: 1956 → 1941; bytes_downloaded: 419580437 → 399769600; committed_pdf_bytes: 182079919 → 169760052; held: 1931 → 1916
- shepard-citations: land_targets: 3536 → 3534; land_targets_with_any_edge: 1051 → 1049; land_targets_with_ending_candidate: 616 → 615
- source-ladder: attempts_logged: 55 → 50; bytes_downloaded: 86666375 → 66385834; distinct_new_source_hashes: 44 → 47; found: 870 → 920
- tischendorf-originals: bytes_downloaded: 8180733529 → 2456099185; leads: 603 → 624; replacement_strong: 39 → 71; replacement_targets: 699 → 734
- x1-class-engine: modern_families_5_plus: 197 → 205

## Top shared unlocks

- orders_unblocked: 2224; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 737; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

- A-20261108-lean-main (2026-11-08, claude): Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42885309594)
