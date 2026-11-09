# Daily research digest

New York date: 2026-11-09. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Numbered series: ready for human review 1,183 of 14,998 orders (7.9%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42570902277-1:ac7f6d1a84710e26c609204cc5c5108ad767e04e531af510b4522c3291ec3134` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,301. The other 10,697 have not been researched yet.

Ready by text evidence: {'original_supported': 658, 'transcription_dependent': 525}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 847; quotation rechecks: 847. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 254. Confirmations rejected: {'grade_not_a_working_text_grade': 3, 'not_confirmed': 1630}.

## Changes since the previous day

Comparison snapshot: 2026-11-08; intervening runs may be absent.
- claim-checker: claims_all_checks_passed: 1473 → 1666; claims_mechanical_fail: 267 → 74; claims_mechanical_pass: 1559 → 1752; held_distinct_sha256: 56996 → 56874
- gessner-cards: ready_for_human_review: 1083 → 1183
- kean: decisions: 71 → 74; findings: 264 → 276; open_owner_questions: 13 → 0
- lachmann: assessed: 2395 → 2409; complete_text_confirmed: 1276 → 1384; confirmed: 703 → 776; identity_confirmed: 1208 → 1185
- mabillon-held-printings: lead: 244 → 250; passages: 2460 → 2482; strong: 1771 → 1787; targets: 2015 → 2037
- readiness-tracker: formal_revocation_after_earlier_cessation: 0 → 33; original_replacement_obligations: 848 → 847; quotation_recheck_obligations: 848 → 847; ready_for_human_review: 1083 → 1183
- selden-fr-citers: bytes_downloaded: 0 → 856889; requests: 0 → 80; targets_searched_this_run: 192 → 9; targets_searched_total: 13524 → 13533
- tsiolkovsky-trajectory: W_hours: 6812.1 → 6817.3; a_hours_per_day2_latest: -3.15 → -47.85; days: 23 → 24; generations: 71 → 74

## Top shared unlocks

- orders_unblocked: 2222; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 675; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks for the owner (Kean register)

No open ask is recorded in the Kean register.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
- photius-csc-printings: unknown (no run link)
- photius-free-printings: unknown (no run link)
- photius-gpo-volumes: unknown (no run link)
- photius-replica-check: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42570902277)
