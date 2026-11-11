# Daily research digest

New York date: 2026-11-10. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,252 of 14,998 orders (8.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42935739969-1:43e0de771c83cfc8ad871930ed1ea31884e54731acfcb0cd8b28ece87ad23ee1` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,274. The other 10,724 have not been researched yet.

Ready by text evidence: {'original_supported': 726, 'transcription_dependent': 526}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 851; quotation rechecks: 851. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 252. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1571}.

## Changes since the previous day

Comparison snapshot: 2026-11-09; intervening runs may be absent.
- cassiodorus: pages_kept_total: 294 → 297
- claim-checker: claim_lines_found: 1828 → 1908; claims_all_checks_passed: 1660 → 1740; claims_checked: 1828 → 1908; claims_gate_passed: 1738 → 1818
- claim-drafts: decided_orders_with_draft: 4301 → 4307; drafts_whose_only_remaining_gaps_are_judgment_fields: 1151 → 1157; of_which_decided: 1151 → 1157; undecided_orders_with_draft: 10652 → 10646
- clause-drafts: clauses_total: 71277 → 71401; fragments_from_app_transcription: 4976 → 4975; fragments_written: 9789 → 9792; orders_processed: 9946 → 9949
- cotton-capture-custody: not_web_sources: 1175 → 1251; published: 756 → 757; wanted_hashes: 1932 → 2009
- cruden-fr-concordance: bytes_downloaded: unavailable → 22573230144; committed_bytes: unavailable → 79999608; control_targets: unavailable → 30; fragments: unavailable → 671
- current-law: requests_made: 113 → 116
- eumenes-nmb-reports: manifest_records: unavailable → 119; orders_covered: unavailable → 126; published: unavailable → 119
- family-rules: saved_texts_scanned: 82852 → 82123
- fr-originals: found_decided: 2368 → 2426; not_found: 717 → 719; orders_already_finished_before_this_run: 7214 → 7216; orders_carried_forward_from_committed_results: 7214 → 7216
- gessner-cards: not_researched: 10697 → 10724; one_step_from_ready: 216 → 217; ready_for_human_review: 1179 → 1252; with_provisional_status: 4301 → 4274
- kean: decisions: 74 → 75; findings: 286 → 292; open_owner_questions: 1 → 2
- lachmann: assessed: 2360 → 2349; complete_text_confirmed: 1396 → 1365; confirmed: 807 → 776; identity_confirmed: 1146 → 1148
- larrey-triage: orders_with_compiled_inputs: unavailable → 14998; tracker_orders: unavailable → 14998
- later-events: decided_no_with_full_revocation_candidate: 944 → 951; decided_orders_total: 4298 → 4274; decided_orders_with_any_candidate: 1901 → 1909; decided_orders_with_event_candidate_excluding_see: 1618 → 1626
- linnaeus-types: cruden_targets: unavailable → 2110; cs_one_person_left_to_ulpian: unavailable → 802; m1118_gap_overlap: unavailable → 1037; no_lead: unavailable → 4174
- official-fixity: carried_forward: 7124 → 7358; files: 7124 → 7358; orders_with_a_gpo_matched_file: 5220 → 5606
- pacioli-double-entry: agreed_pairs: unavailable → 1652; disagreed_pairs: unavailable → 67
- readiness-tracker: orders_with_provisional_status: 4301 → 4274; original_replacement_obligations: 882 → 851; quotation_recheck_obligations: 882 → 851; ready_for_human_review: 1179 → 1252
- selden-fr-acting: bytes_downloaded: 2729289189 → 1139195521; requests: 129 → 82
- selden-fr-citers: bytes_downloaded: 856889 → 855827; requests: 80 → 71; targets_searched_this_run: 9 → 0; targets_total: 13379 → 13220
- selden-statutes: attempted: 1956 → 1941; bytes_downloaded: 419580437 → 399769600; committed_pdf_bytes: 182079919 → 169760052; held: 1931 → 1916
- shepard-citations: land_targets: 3536 → 3534; land_targets_with_any_edge: 1051 → 1049; land_targets_with_ending_candidate: 616 → 615
- source-ladder: attempts_logged: 55 → 61; bytes_downloaded: 86666375 → 27798224; distinct_new_source_hashes: 44 → 41; exhausted_proposed_items: 0 → 2
- theophilus-sources: cfr_targets_planned: 566 → 527; eligible_yes_orders: 345 → 298; failures_total: 74 → 69; usc_sections_planned: 241 → 217
- tischendorf-originals: bytes_downloaded: 8180733529 → 893844547; leads: 603 → 604; replacement_targets: 699 → 700; requests: 2437 → 139
- tsiolkovsky-trajectory: W_hours: 6817.3 → 6888.3; a_hours_per_day2_latest: -47.85 → 4.87; days: 24 → 25; generations: 74 → 102
- x1-class-engine: modern_families_5_plus: 197 → 205

## Top shared unlocks

- orders_unblocked: 2198; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 702; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

- A-20261108-lean-main (2026-11-08, claude): Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?
- A-20261110-larrey-soft-probe (2026-11-10, claude): Larrey keeps 1,014 undecided orders out only on the soft gate later_order_text_held (fitted on 28 failures, 0 of 33 successes lost). May a coordinator spend about 15-20 USD on one 30-order probe of soft-gated orders (LARREY_LEVEL=hard) to measure its lost yield before it is relied on at scale?
- A-20261110-nalimov-calibration (2026-11-10, Claude (Opus 5.5, Nalimov)): (1) Sign the Nalimov stage-0 calibration plan research/nalimov/calibration/WAVE.json, plan sha256 4c19799f9bbcb0cbfc84ee0a7d1303bf2ad79a33851e4679b2389b364d2dde96: the 8 script-drafted express-revocation claims (EO 10779, 11056, 11232, 11274, 11352, 11361, 12737, 13765) through the Maudslay conveyor
- A-20261110-respondendi-standing-rule (2026-11-10, Claude): Approve jobs/respondendi-adoption/RULE.md (sha256 85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934) as a standing adoption rule, so that undecided-route status proposals in its lot are adopted without a per-order owner decision? The lot: express, named, unqualified whole-order revoca
- A-20261110-respondendi-standing-rule-v2 (2026-11-10, Claude): Approve Respondendi rule version 2 (jobs/respondendi-adoption/RULE.md, sha256 e15ae99b3e5ae800e18d331cb2b5fe6ae233aa36052b13f512b86eabbec01423) as a standing rule covering every kind of undecided order, so that qualifying status proposals are adopted after the audits it requires, with no per-order o
- A-20261110-ulpian-l1r-correction (2026-11-10, Claude): Extend the Jacquard L1 correction to wave 2? 582 L1R provisional NO statuses (PR 119, same L1 card and its 'at least 14' premise, which you declined in D-20261110-ulpian-no-floor) were adopted; 527 are dated on or after 1904-05-03 and 26 have no exact date, plus 3 undated wave-1 L1 rows (EO 940, 159

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42935739969)
