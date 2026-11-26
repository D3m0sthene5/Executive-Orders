# Daily research digest

New York date: 2026-11-26. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,391 of 15,003 orders (9.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 1,816 identities observed, a lower bound. Not part of the numbered-series proportion above.

Generation: `45873042843-1:3ce53aa0a4bbec2e6cd4f2b5dac1894206318745df20412df86bca577f9f383b` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,801. The other 11,202 have not been researched yet.

Ready by text evidence: {'original_supported': 838, 'transcription_dependent': 551, 'custody_text_only': 2}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 884; quotation rechecks: 884. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 284. Confirmations rejected: {'grade_not_a_working_text_grade': 1, 'not_confirmed': 143}.

## Changes since the previous day

Comparison snapshot: 2026-11-25; intervening runs may be absent.
- claim-checker: claims_all_checks_passed: 1890 → 1888; claims_mechanical_fail: 80 → 82; claims_mechanical_pass: 1976 → 1974; held_distinct_sha256: 61213 → 60435
- claim-drafts: decided_orders_with_draft: 3792 → 3801; drafts_whose_only_remaining_gaps_are_judgment_fields: 1157 → 1158; of_which_decided: 1157 → 1158; orders_with_any_conflict: 952 → 954
- domesday-register: orders: 15002 → 15003; with_any_text_file: 14908 → 14918; with_date: 14996 → 14997; with_title: 14947 → 14948
- gessner-cards: president_unknown_no_date: 59 → 57; presidents_derived_from_date: 4952 → 4953; presidents_from_register: 9991 → 9992; ready_for_human_review: 1393 → 1391
- kean: decisions: 92 → 110; findings: 382 → 420; open_owner_questions: 9 → 10
- lachmann: assessed: 952 → 953; complete_text_confirmed: 858 → 859; confirmed: 808 → 809; identity_confirmed: 862 → 863
- lambertini: decided_orders_with_draft: 3788 → 3801; packet_targets: 851 → 852; pool_LAMBC: 403 → 586; pool_LAMBS: 44 → 48
- larrey-triage: orders_with_compiled_inputs: 15002 → 15003
- official-fixity: carried_forward: 7358 → 7352; files: 7358 → 7352
- readiness-tracker: ready_for_human_review: 1393 → 1391; working_text_confirmations_counting: 808 → 809
- selden-fr-citers: targets_searched_total: 13537 → 13538; targets_total: 13207 → 13057
- selden-statutes: attempted: 1937 → 1920; committed_pdf_bytes: 169760052 → 168939459; held: 1912 → 1895; orders_with_held_basis_statute: 4123 → 4070
- shepard-citations: land_targets: 3535 → 3556; land_targets_with_any_edge: 1070 → 1077; land_targets_with_ending_candidate: 626 → 630
- source-ladder: attempts_logged: 175 → 178; bytes_downloaded: 136472728 → 135955954; distinct_new_source_hashes: 3 → 0; exhausted_proposed_items: 1 → 2
- status-history: printed_snapshot_undecided_identities: 2219 → 2217; undecided_with_history: 4744 → 4735; undecided_with_own_observation: 4572 → 4563
- theophilus-sources: cfr_targets_planned: 529 → 414; eligible_yes_orders: 298 → 223; failures_total: 68 → 51; usc_sections_planned: 217 → 183
- tischendorf-originals: bytes_downloaded: 869456604 → 874351704; leads: 608 → 184; replacement_targets: 698 → 699; replacement_targets_ready: 521 → 546
- tsiolkovsky-trajectory: W_hours: 6842.0 → 7068.3; W_max_hours: 18195.0 → 18196.2; a_hours_per_day2_latest: 0.65 → 37.36; days: 39 → 41

## Top shared unlocks

- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 93; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 37; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 17; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

- A-20261108-lean-main (2026-11-08, claude): Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?
- A-20261110-respondendi-standing-rule (2026-11-10, Claude): Approve jobs/respondendi-adoption/RULE.md (sha256 85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934) as a standing adoption rule, so that undecided-route status proposals in its lot are adopted without a per-order owner decision? The lot: express, named, unqualified whole-order revoca
- A-20261110-respondendi-standing-rule-v2 (2026-11-10, Claude): Approve Respondendi rule version 2 (jobs/respondendi-adoption/RULE.md, sha256 e15ae99b3e5ae800e18d331cb2b5fe6ae233aa36052b13f512b86eabbec01423) as a standing rule covering every kind of undecided order, so that qualifying status proposals are adopted after the audits it requires, with no per-order o
- A-20261110-ulpian-named-war (2026-11-10, Claude): Count service in a named war as a dated fact? Eight returned L1R orders (EO 437, 444, 453, 411 and four others; list in research/ulpian/jacquard-l1r-correction/COORDINATOR.jsonl) say the person is a veteran of the Civil War (1861-1865) or the Spanish war (1898) but print no date. RULE.md v2 section 
- A-20261111-film709-count (2026-11-11, Claude): NYU Film 709 (11 reels, EO 1-7403) is free to scan yourself at Bobst on the ScanPro stations, and NARA New York is closed. Count your own Film 709 scans as the R38 microfilm witness, like M1118? Bytes stay private (owner inbox, as with Hein); only hashes and page facts go public. Counting starts onl
- A-20261112-generate-verify-comparison (2026-11-12, Claude): Approve one bounded comparison, generate-then-verify (Nalimov script drafts) against the current producer route, on the same 10 prescreened orders (EO 10302, 10779, 10918, 11056, 11232, 11352, 11361, 11512, 12737, 13765), with the same sources, the same blind two-arm Opus review with planted control
- A-20261112-lind-repair-12437-11943 (2026-11-12, Claude): Optional: may Claude spend up to $8 list-price allowance (all-in) to repair EO 12437 and EO 11943, the two stage-0 claims each rejected by one blind arm for a single sentence (a false search statement; an imprecise effective date)? Steps: one producer correction of those sentences, overlay-check wit
- A-20261113-lind-12753-reconfirm (2026-11-13, Claude): EO 12753's lifecycle approval was reconfirmed by script, which D-20261110-no-mechanical-reconfirmation-for-models does not allow for model producers. Choose: (a) one fresh Sonnet producer session reconfirms the working sheet as a producer (about $0.5 cap), then re-assemble, re-check and re-complete;
- A-20261124-3 (2026-11-24, Claude (Opus 5.5)): Which kinds of ProQuest unnumbered presidential document should the census count as executive orders? The 3,941 missing candidates are land orders and operative orders by title. Should any of these also count: letters of instruction (806 signed), personal actions such as passes and discharges (583),
- A-20261124-stateless-gauge (2026-11-24, Claude (Opus 5.5)): Run the stateless gauge on your PC (install Claude Code with 'irm https://claude.ai/install.ps1 | iex', log in, then the commands in jobs/maudslay-conveyor/README.md 'Stateless mode and the gauge'; dry-run forecast 24.24 USD against a 25 USD cap). Also: the gauge's disagreement threshold was given a

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/45873042843)
