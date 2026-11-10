# Daily research digest

New York date: 2026-11-10. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,238 of 14,998 orders (8.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42796414781-1:4a43d396344f899753e5b04bd12ca0c1cdd393d6e8fb33c86dbafcfaf6e78105` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,301. The other 10,697 have not been researched yet.

Ready by text evidence: {'original_supported': 713, 'transcription_dependent': 525}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 882; quotation rechecks: 882. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 284. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1551}.

## Changes since the previous day

Comparison snapshot: 2026-11-09; intervening runs may be absent.
- cassiodorus: pages_kept_total: 294 → 296
- claim-checker: claim_lines_found: 1828 → 1891; claims_all_checks_passed: 1660 → 1723; claims_checked: 1828 → 1891; claims_gate_passed: 1738 → 1801
- cotton-capture-custody: not_web_sources: 1175 → 1240; wanted_hashes: 1932 → 1997
- gessner-cards: one_step_from_ready: 216 → 214; ready_for_human_review: 1179 → 1238
- kean: decisions: 74 → 75; findings: 286 → 292; open_owner_questions: 1 → 2
- readiness-tracker: ready_for_human_review: 1179 → 1238
- selden-fr-acting: bytes_downloaded: 2729289189 → 1153355666; requests: 129 → 103
- shepard-citations: land_targets: 3536 → 3534; land_targets_with_any_edge: 1051 → 1049; land_targets_with_ending_candidate: 616 → 615
- x1-class-engine: modern_families_5_plus: 197 → 205

## Top shared unlocks

- orders_unblocked: 2167; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 703; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

- A-20261108-lean-main (2026-11-08, claude): Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?
- A-20261110-papinian-board-bytes (2026-11-09, Claude): The board rule (D-20261108-board-rule) cannot run: the 101 held National Mediation Board reports are custody records only (their PDFs, 191.8 MB, sit in source-ladder's discarded runner cache). Which do you want: (a) store the 101 PDFs in the GitHub Release-asset byte store and give claim-checker the
- A-20261110-papinian-adopt-u01b (2026-11-10, Claude): Adopt the provisional NO status of EO 9674, EO 11957 and EO 12348? Each was proposed under the claim-kit status-overlay route, accepted by an independent AI status reviewer, and upheld by two independent blind AI lifecycle arms whose planted control (EO 11816) both caught; the reviewed claims are in
- A-20261110-papinian-adopt-u23 (2026-11-10, Claude): Adopt the provisional NO status of EO 9245, EO 10679 and EO 11962 (as for A-20261110-papinian-adopt-u01b)? Each was accepted by an independent AI status reviewer and upheld by two independent blind AI lifecycle arms whose planted control (EO 10938) both caught; claims in research/excavator/claude-pa

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42796414781)
