# Daily research digest

New York date: 2026-11-07. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 992 of 14,998 orders (6.6%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator): not measured yet; `jobs/domesday-register/output/UNNUMBERED_SUMMARY.json` is missing.

Generation: `42382847594-1:85c24a50626eef5982782fc869869b83a1c0e9cf2a70c59e9627485221eb7723` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,298. The other 10,700 have not been researched yet.

Ready by text evidence: {'original_supported': 660, 'transcription_dependent': 332}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 867; quotation rechecks: 867. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 281. Confirmations rejected: {'grade_not_a_working_text_grade': 3, 'not_confirmed': 4818}.

## Changes since the previous day

Comparison snapshot: 2026-11-06; intervening runs may be absent.
- claim-checker: claims_all_checks_passed: 1579 → 1386; claims_mechanical_fail: 65 → 258; claims_mechanical_pass: 1665 → 1472; held_distinct_sha256: 55081 → 56961
- clause-drafts: clauses_total: 70615 → 71253; fragments_from_app_transcription: 4964 → 4983; fragments_written: 9761 → 9788; ocr_fragments_with_candidate_fr_page: 60 → 58
- duodecim-tableiv: captures_discovered_internet_archive: unavailable → 99; captures_discovered_unt: unavailable → 2; control_error_rate: unavailable → 0.0; controls_errors: unavailable → 0
- family-rules: saved_texts_scanned: 51201 → 82481
- gessner-cards: ready_for_human_review: 1185 → 992
- kean: decisions: 45 → 67; findings: 211 → 245; open_owner_questions: 3 → 14
- lachmann: in_scope: 5832 → 5859
- official-fixity: carried_forward: 5158 → 5021; checked_this_run: 1 → 2103; files: 5159 → 7124; orders_with_a_gpo_matched_file: 5070 → 5220
- photius-csc-printings: checked: unavailable → 145; counting_as_official_printing: unavailable → 6; fragments: unavailable → 145; located_rows: unavailable → 803
- photius-free-printings: checked: unavailable → 471; counting_as_official_printing: unavailable → 117; fragments: unavailable → 471; orders_with_candidates: unavailable → 560
- photius-gpo-volumes: counting_as_official_printing: unavailable → 3676; counting_in_4306_7315: unavailable → 3200; in_4306_7315: unavailable → 3201; orders_located: unavailable → 3679
- photius-replica-check: adjudicated: unavailable → 219; adjudication_queue: unavailable → 0; credited_archival_replica_checked: unavailable → 2544; credited_below_4306: unavailable → 1967
- ptolemy-custody: kept_this_run_bytes: 928544414 → 0; still_due: 7384 → 7364
- readiness-tracker: original_replacement_obligations: 1146 → 867; quotation_recheck_obligations: 1146 → 867; ready_for_human_review: 1185 → 992; text_step_from_checked_replica: unavailable → 1968
- repetita-lsa: bytes_downloaded: unavailable → 18763858; control_error_rate: unavailable → 0.0; entries_parsed_all_titles: unavailable → 2459761; eo_category_rows_with_target: unavailable → 6886
- source-ladder: attempts_logged: 70 → 50; bytes_downloaded: 640005978 → 462367889; distinct_new_source_hashes: 36 → 40; exhausted_proposed_items: 0 → 1
- youngstown-courts: clusters_with_conflicting_cues: unavailable → 85; compressed_bytes_planned: unavailable → 55252643327; compressed_bytes_read: unavailable → 56112475940; decoded_bytes: unavailable → 359308723901

## Top shared unlocks

- orders_unblocked: 2269; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 594; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

- A-20261106-1 (2026-11-06, claude-selden): Does a statute that abolishes an order's body, or ends the emergency its term depends on, without naming the order, date the order's end? Default: no.
- A-20261106-2 (2026-11-06, claude-peiresc): The repo is near GitHub's 10 GB cap. Stop committing source bytes (R2 plus hash manifest), and shrink by history rewrite or a fresh repository? Default: stop new bytes now; you choose how to shrink.
- A-20261106-dagron-nyu (2026-11-06, Claude): NYU Film 709/Hein: lift the 2026-10-19 no-microfilm rule for this collection, and approve staged images under research/dagron/acquired?
- A-20261106-pothier (2026-11-06, Claude): Adopt each Pothier family doctrine (yes/no each); rule on amending orders and PLO tables? research/pothier/REPORT.md
- A-20261107-cap-mirror (2026-11-06, claude-encyclopedie): Is the Hugging Face common-pile mirror of Harvard's Caselaw Access Project (22.6 GiB, third-party repackaging) acceptable as a case-text source for court-ended orders, given static.case.law disallows robots?
- A-20261107-claimkit-court-fragments (2026-11-06, claude-encyclopedie): Let the claim kit attach Youngstown's court-decision fragments to orders (add court_decision_candidates to EVENT_KINDS and CASE to NON_EO_ACTOR in jobs/claim-kit/inputs.py)? This is count-sensitive.
- A-20261107-courtlistener-robots (2026-11-06, claude-encyclopedie): CourtListener answers robots.txt with HTTP 403 for every agent (RFC 9309 treats a 4xx robots.txt as 'unavailable', allowing access), while its documented API answers normally. Allow Youngstown's 40 authenticated API cross-check calls despite fetch_pool's stricter disallow-all reading, or ask Free La
- A-20261107-fetchpool-wildcards (2026-11-06, claude-encyclopedie): Fix jobs/_lib/fetch_pool.py so robots.txt wildcard rules ('*', '$') are honoured (Duodecim's tested check is ready to move into it)? The change makes the next sweep rerun every job that lists fetch_pool.py in triggers.txt.
- A-20261107-loc-hein (2026-11-06, claude-encyclopedie): The Library of Congress's free CFR, Federal Register and U.S. Code scans are HeinOnline-origin with a stated no-bulk-download term. Allow targeted, throttled pulls of a few hundred items (for example the U.S. Code EO tables 1934-1988 and 3 CFR 1940-1995), or wait for LOC's reply to the drafted reque
- A-20261107-lowande-email (2026-11-06, claude-encyclopedie): Send research/bayle-prior-art/lowande-poznansky/REQUEST_EMAIL.md (corrected after independent check) to Kenneth Lowande asking for the order-level dataset and the 20 missing revocations and 65 misattributions? Confirm the bracketed identity line and the offer of corrections.
- A-20261107-mountweazel-plants-leak (2026-11-06, claude-encyclopedie): Mountweazel's whole-repository check fails because research/excavator/dorotheus-sample-2026-11-06/PLANTS.csv names seeded item MW-C720-01 (red in the Valla pilot check). Allow the check to accept revealed plant keys under research/excavator/*/PLANTS.csv after reveal, or move revealed keys under jobs
- A-20261107-ocr-reference-rule (2026-11-06, claude-encyclopedie): OCR pilot: exact GPO-and-engine agreement leaves 1 of 43 reference passages. Choose: (a) enlarge your hand-transcribed set, (b) agreement within a CER threshold (0.5% gives 8, 1% gives 18), or (c) GPO, Surya and Claude agree after lenient folding?
- A-20261107-tracker-thesis-fix (2026-11-06, claude-encyclopedie): Apply TRACKER_FIX.md (about 80 lines) so the tracker fills formal_revocation_after_earlier_cessation from filed claims (32 yes, 487 no)? It is count-sensitive, so it would go in a count-changing PR for you to merge.
- A-20261107-photius-193-recheck (2026-11-07, claude): 193 ready orders (EO 8032-9208) left ready because Photius found an official GPO printing for each, which made their frozen working-text confirmations stale. Run a page check of each transcription against its new official printing (an Opus wave like Photius lane 1; upgrades them to original-backed i

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42382847594)
