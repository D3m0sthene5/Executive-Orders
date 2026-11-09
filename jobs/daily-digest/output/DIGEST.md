# Daily research digest

New York date: 2026-11-09. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,179 of 14,998 orders (7.9%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42711809594-1:af1c6340180e4519e64610100438e2d377c2c73b1c962ad4ae746626acdf8d92` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,301. The other 10,697 have not been researched yet.

Ready by text evidence: {'original_supported': 654, 'transcription_dependent': 525}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 882; quotation rechecks: 882. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 284. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1551}.

## Changes since the previous day

Comparison snapshot: 2026-11-08; intervening runs may be absent.
- claim-checker: claims_all_checks_passed: 1473 → 1660; claims_mechanical_fail: 267 → 80; claims_mechanical_pass: 1559 → 1746; held_distinct_sha256: 56996 → 56911
- claim-drafts: orders_with_any_conflict: 928 → 929
- duodecim-tableiv: captures_discovered_unt: 2 → 0
- family-rules: saved_texts_scanned: 82591 → 82852
- gessner-cards: one_step_from_ready: 217 → 216; ready_for_human_review: 1083 → 1179
- kean: decisions: 71 → 74; findings: 264 → 286; open_owner_questions: 13 → 1
- lachmann: assessed: 2395 → 2360; complete_text_confirmed: 1276 → 1396; confirmed: 703 → 807; identity_confirmed: 1208 → 1146
- lambertini: counterevidence_records: 1245 → 1244; decided_orders_with_draft: 4291 → 4301; packet_targets: 840 → 846; packets: 114 → 120
- mabillon-held-printings: lead: 244 → 250; passages: 2460 → 2482; strong: 1771 → 1787; targets: 2015 → 2037
- readiness-tracker: formal_revocation_after_earlier_cessation: 0 → 33; original_replacement_obligations: 848 → 882; quotation_recheck_obligations: 848 → 882; ready_for_human_review: 1083 → 1179
- selden-fr-acting: bytes_downloaded: 2794249410 → 2729289189; pages_attempted: 66 → 65; pages_carried_forward: 739 → 740; requests: 131 → 129
- selden-fr-citers: bytes_downloaded: 0 → 856889; requests: 0 → 80; targets_searched_this_run: 192 → 9; targets_searched_total: 13524 → 13533
- shepard-citations: edges: 10597 → 10667; edges_with_census_actor: 6584 → 6657; edges_with_census_target: 7590 → 7661; land_targets: 3549 → 3536
- source-ladder: attempts_logged: 59 → 55; bytes_downloaded: 635954446 → 86666375; distinct_new_source_hashes: 29 → 44; embedded_cite_items: 14 → 9
- tischendorf-originals: bytes_downloaded: 19722195578 → 8180733529; leads: 633 → 603; replacement_strong: 65 → 39; replacement_targets: 719 → 699
- tsiolkovsky-trajectory: W_hours: 6812.1 → 6817.3; a_hours_per_day2_latest: -3.15 → -47.85; days: 23 → 24; generations: 71 → 74
- valla: active_claims: 1445 → 1530
- x1-class-engine: modern_families_5_plus: 196 → 197; pre1937_orders: 8014 → 8040

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

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42719702166)
