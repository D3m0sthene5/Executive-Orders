# Daily research digest

New York date: 2026-11-12. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,251 of 15,002 orders (8.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `43304573666-1:1cef4f55050117e6d83a542d535b39711468ddb2e05389956ea2ffb870a37b1a` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,788. The other 11,214 have not been researched yet.

Ready by text evidence: {'original_supported': 725, 'transcription_dependent': 526}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 883; quotation rechecks: 883. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 284. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1550}.

## Changes since the previous day

Comparison snapshot: 2026-11-11; intervening runs may be absent.
- claim-checker: held_distinct_sha256: 58657 → 58673
- claim-drafts: fragment_orders_not_in_universe: 40 → 39; orders_with_draft: 14953 → 14954; undecided_orders_with_draft: 11165 → 11166
- clause-drafts: clauses_total: 71430 → 71749; fragments_from_app_transcription: 4974 → 4958; fragments_written: 9795 → 9796; orders_in_universe: 14998 → 15002
- family-rules: saved_texts_scanned: 86512 → 86549
- gessner-cards: not_researched: 11210 → 11214; numbered_series_orders: 14998 → 15002; orders: 14998 → 15002; president_unknown_no_date: 63 → 67
- gratian-niebuhr-leads: date_leads_in_census: 36 → 40
- kean: decisions: 88 → 90; findings: 364 → 372; open_owner_questions: 5 → 7
- lachmann: assessed: 2356 → 2360; complete_text_confirmed: 1366 → 1397; confirmed: 777 → 808; identity_confirmed: 1149 → 1147
- larrey-triage: orders_with_compiled_inputs: 14998 → 15002; tracker_orders: 14998 → 15002
- niebuhr-verify: requests_used: 186 → 185
- official-fixity: carried_forward: 7355 → 7356; files: 7356 → 7357; premis_bytes_read_this_run: 196608 → 262144
- readiness-tracker: numbered_series_orders: 14998 → 15002; orders_total: 14998 → 15002; original_replacement_obligations: 851 → 883; quotation_recheck_obligations: 851 → 883
- selden-fr-citers: bytes_downloaded: 855827 → 468; requests: 71 → 5; targets_searched_this_run: 0 → 4; targets_searched_total: 13533 → 13537
- shepard-citations: edges: 10665 → 10667; edges_with_census_actor: 6655 → 6657; edges_with_census_target: 7659 → 7661; targets: 8575 → 8579
- source-ladder: attempts_logged: 79 → 63; bytes_downloaded: 67273510 → 183071370; distinct_new_source_hashes: 23 → 32; exhausted_proposed_items: 5 → 13
- status-history: census_identities: 14998 → 15002

## Top shared unlocks

- orders_unblocked: 2168; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
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
- A-20261111-film709-count (2026-11-11, Claude): NYU Film 709 (11 reels, EO 1-7403) is free to scan yourself at Bobst on the ScanPro stations, and NARA New York is closed. Count your own Film 709 scans as the R38 microfilm witness, like M1118? Bytes stay private (owner inbox, as with Hein); only hashes and page facts go public. Counting starts onl
- A-20261112-cis-unnumbered-check (2026-11-12, Claude): Check the 875 CIS unnumbered executive orders that fall on dates with no known order (research/graunt-census-audit-2026-11-12/cis-kaufman/CIS_UNNUMBERED_EO_GROUPS_PRE1937.csv) for admission to the unnumbered series? A pilot of 30 on the CIS fiche at Bobst or ProQuest would show how many are presiden
- A-20261112-lind-stage0 (2026-11-12, Claude): After the claim-kit rebuild publishes, may Claude run one Lind stage-0 batch: 30 undecided orders (15 passing every Larrey gate, 15 passing only the hard gates, drawn by research/lind/stage0/draw.py), Papinian configuration, one pooled review set, hard cap $35 list-price allowance? It also needs an 
- A-20261112-lind-stage0-v2 (2026-11-12, Claude): Approve the Lind stage-0 pilot exactly as research/lind/stage0/WAVE.json (sha256 f2b07a1923354e3484a9f510a3419fbb2d882150ce68cce9dc02f6ff0d3b8a1d): 30 undecided orders, 15 drawn at random from the 3,447 that pass every Larrey gate and 15 from the 1,834 that pass only the hard gates (never attempted)

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/43304573666)
