# Daily research digest

New York date: 2026-11-08. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,083 of 14,998 orders (7.2%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42557370654-1:c2820277bc027369f87406206cab8cea9ce7a6b5e5d02e2431477f9a698b0604` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,301. The other 10,697 have not been researched yet.

Ready by text evidence: {'original_supported': 658, 'transcription_dependent': 425}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 848; quotation rechecks: 848. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 255. Confirmations rejected: {'grade_not_a_working_text_grade': 3, 'not_confirmed': 1689}.

## Changes since the previous day

Comparison snapshot: 2026-11-07; intervening runs may be absent.
- cassiodorus: pages_kept_total: 10 → 294
- claim-checker: claim_lines_found: 1760 → 1828; claims_all_checks_passed: 1414 → 1473; claims_checked: 1760 → 1828; claims_gate_passed: 1670 → 1738
- clause-drafts: clauses_total: 71268 → 71277; fragments_from_app_transcription: 4983 → 4976
- cotton-capture-custody: not_web_sources: 1095 → 1175; wanted_hashes: 1852 → 1932
- domesday-register: orders: 14972 → 14998; with_any_text_file: 14882 → 14908; with_date: 14909 → 14986; with_title: 14885 → 14943
- family-rules: saved_texts_scanned: 82522 → 82591
- gessner-cards: one_step_from_ready: 219 → 217; president_unknown_no_date: 138 → 63; presidents_derived_from_date: 4932 → 4947; presidents_from_register: 9927 → 9987
- kean: findings: 250 → 264
- lachmann: assessed: 2551 → 2395; complete_text_confirmed: 1330 → 1276; confirmed: 732 → 703; identity_confirmed: 1256 → 1208
- readiness-tracker: original_replacement_obligations: 867 → 848; quotation_recheck_obligations: 867 → 848; ready_for_human_review: 1020 → 1083; text_step_provisional_working_text: 281 → 255
- selden-fr-citers: bytes_downloaded: 8156887 → 0; documents_examined_this_run: 83 → 0; requests: 343 → 0; targets_searched_this_run: 194 → 192
- source-ladder: attempts_logged: 45 → 59; bytes_downloaded: 861192611 → 635954446; distinct_new_source_hashes: 38 → 29; embedded_cite_items: 11 → 14
- tischendorf-originals: bytes_downloaded: 27441440056 → 19722195578; leads: 492 → 633; replacement_strong: 25 → 65; replacement_targets: 843 → 719
- tsiolkovsky-trajectory: W_hours: 6630.8 → 6812.1; a_hours_per_day2_latest: -93.05 → -3.15; days: 21 → 23; generations: 41 → 71

## Top shared unlocks

- orders_unblocked: 2223; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 676; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
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

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42557370654)
