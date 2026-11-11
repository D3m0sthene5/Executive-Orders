# Daily research digest

New York date: 2026-11-11. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,256 of 14,998 orders (8.4%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42977837337-1:e41d48beabceedabd86eba41e50c6d0df6dc8436dbfa728bd044fb36e2b0b68e` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,274. The other 10,724 have not been researched yet.

Ready by text evidence: {'original_supported': 730, 'transcription_dependent': 526}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 846; quotation rechecks: 846. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 252. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1551}.

## Changes since the previous day

Comparison snapshot: 2026-11-10; intervening runs may be absent.
- claim-checker: claims_all_checks_passed: 1740 → 1746; claims_mechanical_fail: 80 → 74; claims_mechanical_pass: 1826 → 1832; held_distinct_sha256: 58669 → 58819
- claim-drafts: decided_orders_with_draft: 4307 → 4274; fragment_orders_not_in_universe: 41 → 40; undecided_orders_with_draft: 10646 → 10679
- cruden-fr-concordance: bytes_downloaded: 22573230144 → 3608561552; fragments_carried_forward: 0 → 655; searches_made_this_run: 1976 → 0; units_attempted: 841 → 87
- duodecim-tableiv: captures_discovered_unt: 0 → 2
- family-rules: saved_texts_scanned: 82123 → 83082
- gessner-cards: one_step_from_ready: 217 → 218; ready_for_human_review: 1252 → 1256
- kean: decisions: 75 → 82; findings: 292 → 362; open_owner_questions: 2 → 6
- lachmann: assessed: 2349 → 2361; complete_text_confirmed: 1365 → 1397; confirmed: 776 → 808; identity_confirmed: 1148 → 1147
- readiness-tracker: original_replacement_obligations: 851 → 846; quotation_recheck_obligations: 851 → 846; ready_for_human_review: 1252 → 1256; working_text_confirmations_counting: 776 → 808
- selden-fr-citers: targets_total: 13220 → 13203
- selden-statutes: attempted: 1941 → 1937; held: 1916 → 1912; orders_with_held_basis_statute: 4132 → 4124; page_number_printed: 1815 → 1811
- status-history: printed_snapshot_undecided_identities: 2230 → 2221; undecided_with_history: 4757 → 4748; undecided_with_own_observation: 4585 → 4576
- theophilus-sources: cfr_targets_planned: 527 → 529; failures_total: 69 → 68
- tischendorf-originals: bytes_downloaded: 893844547 → 1935046490; leads: 604 → 616; replacement_strong: 39 → 71; replacement_targets: 700 → 735
- tsiolkovsky-trajectory: W_hours: 6888.3 → 6893.5; a_hours_per_day2_latest: 4.87 → -5.25; days: 25 → 26; generations: 102 → 106
- valla: active_claims: 1530 → 1604; shared_rationale_references: 783 → 831; textual_leads: 24 → 33

## Top shared unlocks

- orders_unblocked: 2234; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 738; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
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
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42977837337)
