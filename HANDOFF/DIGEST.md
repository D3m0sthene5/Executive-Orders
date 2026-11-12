# Daily research digest

New York date: 2026-11-11. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,251 of 14,998 orders (8.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `43131686037-1:08e297ec3c4c496a0c957101c1d6faf761eb7350656d5a3b272a53f2a1968c40` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,788. The other 11,210 have not been researched yet.

Ready by text evidence: {'original_supported': 725, 'transcription_dependent': 526}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 851; quotation rechecks: 851. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 252. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1577}.

## Changes since the previous day

Comparison snapshot: 2026-11-10; intervening runs may be absent.
- claim-checker: held_distinct_sha256: 58669 → 58461
- claim-drafts: decided_orders_with_draft: 4307 → 3788; fragment_orders_not_in_universe: 41 → 40; undecided_orders_with_draft: 10646 → 11165
- clause-drafts: clauses_total: 71401 → 71430; fragments_from_app_transcription: 4975 → 4974; fragments_written: 9792 → 9795; orders_processed: 9949 → 9952
- cruden-fr-concordance: bytes_downloaded: 22573230144 → 3608561552; fragments_carried_forward: 0 → 655; searches_made_this_run: 1976 → 0; units_attempted: 841 → 87
- duodecim-tableiv: captures_discovered_unt: 0 → 2
- family-rules: saved_texts_scanned: 82123 → 86512
- gessner-cards: not_researched: 10724 → 11210; ready_for_human_review: 1252 → 1251; with_provisional_status: 4274 → 3788
- kean: decisions: 75 → 88; findings: 292 → 364; open_owner_questions: 2 → 5
- lachmann: assessed: 2349 → 2356; complete_text_confirmed: 1365 → 1366; confirmed: 776 → 777; identity_confirmed: 1148 → 1149
- lambertini: counterevidence_records: 1244 → 721; decided_orders_with_draft: 4301 → 3788; packet_targets: 846 → 851; packets: 120 → 125
- official-fixity: carried_forward: 7358 → 7355; checked_this_run: 0 → 1; files: 7358 → 7356; orders_with_a_gpo_matched_file: 5606 → 5607
- readiness-tracker: orders_with_provisional_status: 4274 → 3788; ready_for_human_review: 1252 → 1251; working_text_confirmations_counting: 776 → 777
- selden-fr-acting: bytes_downloaded: 1139195521 → 2729289189; requests: 82 → 129
- selden-fr-citers: targets_total: 13220 → 13199
- selden-statutes: attempted: 1941 → 1937; held: 1916 → 1912; orders_with_held_basis_statute: 4132 → 4123; page_number_printed: 1815 → 1811
- shepard-citations: edges: 10667 → 10665; edges_with_census_actor: 6657 → 6655; edges_with_census_target: 7661 → 7659; reserves_resolved: 180 → 179
- source-ladder: attempts_logged: 61 → 79; bytes_downloaded: 27798224 → 67273510; distinct_new_source_hashes: 41 → 23; exhausted_proposed_items: 2 → 5
- status-history: printed_snapshot_undecided_identities: 2230 → 2221; undecided_with_history: 4757 → 4748; undecided_with_own_observation: 4585 → 4576
- theophilus-sources: cfr_targets_planned: 527 → 529; failures_total: 69 → 68
- tischendorf-originals: bytes_downloaded: 893844547 → 920039758; leads: 604 → 606; replacement_targets: 700 → 701; replacement_targets_ready: 520 → 521
- tsiolkovsky-trajectory: W_hours: 6888.3 → 6841.3; a_hours_per_day2_latest: 4.87 → -13.96; days: 25 → 26; generations: 102 → 111
- valla: active_claims: 1530 → 1604; shared_rationale_references: 783 → 831; textual_leads: 24 → 33

## Top shared unlocks

- orders_unblocked: 2200; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 705; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

- A-20261108-lean-main (2026-11-08, claude): Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?
- A-20261110-larrey-soft-probe (2026-11-10, claude): Larrey keeps 1,014 undecided orders out only on the soft gate later_order_text_held (fitted on 28 failures, 0 of 33 successes lost). May a coordinator spend about 15-20 USD on one 30-order probe of soft-gated orders (LARREY_LEVEL=hard) to measure its lost yield before it is relied on at scale?
- A-20261110-respondendi-standing-rule (2026-11-10, Claude): Approve jobs/respondendi-adoption/RULE.md (sha256 85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934) as a standing adoption rule, so that undecided-route status proposals in its lot are adopted without a per-order owner decision? The lot: express, named, unqualified whole-order revoca
- A-20261110-respondendi-standing-rule-v2 (2026-11-10, Claude): Approve Respondendi rule version 2 (jobs/respondendi-adoption/RULE.md, sha256 e15ae99b3e5ae800e18d331cb2b5fe6ae233aa36052b13f512b86eabbec01423) as a standing rule covering every kind of undecided order, so that qualifying status proposals are adopted after the audits it requires, with no per-order o
- A-20261110-ulpian-named-war (2026-11-10, Claude): Count service in a named war as a dated fact? Eight returned L1R orders (EO 437, 444, 453, 411 and four others; list in research/ulpian/jacquard-l1r-correction/COORDINATOR.jsonl) say the person is a veteran of the Civil War (1861-1865) or the Spanish war (1898) but print no date. RULE.md v2 section 

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/43131686037)
