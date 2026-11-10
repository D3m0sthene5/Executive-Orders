# Readiness tracker

**Numbered series: ready for human review 660 of 14,998 orders (4.4%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator): not measured yet; `jobs/domesday-register/output/UNNUMBERED_SUMMARY.json` is missing.

Generation: `local-unpublished` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,301. The other 10,697 have not been researched yet.

Ready by text evidence: {'original_supported': 654, 'transcription_dependent': 6}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 804; quotation rechecks: 804. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 206. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1551, 'pinned_fields_match_no_loaded_fragment': 515}.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 4,301 | 4,301 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 3,541 | 4,301 | 82.3% |
| Complete inventory of the order's operative clauses | 896 | 4,301 | 20.8% |
| When and how it ended (NO), or what keeps it operating now (YES) | 685 | 4,301 | 15.9% |
| Savings clauses and surviving effects closed | 883 | 4,301 | 20.5% |
| Search for later contrary sources recorded, no open conflicts | 2,555 | 4,301 | 59.4% |
| Every shared legal source it cites has been retrieved | 212 | 236 | 89.8% |
| Opus evidence images matched to this order (Opus cases only) | 125 | 825 | 15.2% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 2,252 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 729 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 431 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 10 | agent check | Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held |
| 10 | one source | Retrieve shared source EO::4314 |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |
| 1 | agent check | Settle ambiguous Opus media matches (MATCHES.csv rows graded ambiguous) |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 10,697 |
| `NO_CLAUSE_INVENTORY` | 2,770 | 2,770 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 2,770 | 2,770 |
| `FIRST_END_UNPROVED` | 2,400 | 2,400 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 742 | 2,252 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 552 | 1,599 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 1,243 | 1,243 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 198 | 729 |
| `CLAIM_CHECK_FAILED` | 596 | 596 |
| `WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED` | 592 | 592 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 431 | 431 |
| `CURRENT_BASIS_UNPROVED` | 370 | 370 |
| `OPUS_MEDIA_NONE_CITED` | 198 | 198 |
| `FIRST_END_UNRESOLVED` | 184 | 184 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 139 | 139 |
| `CLAIM_INCOMPLETE` | 88 | 88 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 24 | 24 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 18 | 18 |
| `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` | 0 | 10 |
| `OPEN_SOURCE_AUDIT` | 6 | 6 |
| `OPUS_MEDIA_MATCH_AMBIGUOUS` | 1 | 1 |

## How to move an order forward

- Add or extend its claim in `research/readiness/claims/*.jsonl` (format: `research/stage19/CLAIM_SCHEMA.md`).
  Partial claims count: each step lights up once its part passes the gate and claim-checker.
- Start from the order's draft in `jobs/claim-drafts/output/` (see `jobs/claim-drafts/AGENT_GUIDE.md`).
- Need a source? Add it to `research/readiness/FETCH_QUEUE.jsonl`; source-ladder fetches it.
- If a step cannot be finished by machine, add a line to `research/readiness/EXHAUSTED.jsonl` with
  `instrument_id`, `step`, `searched` (list of repositories and queries), `recorded_by`, `recorded_on`.
- Step names: `provisional_status`, `original_text`, `clause_inventory`, `ending_or_current_basis`, `savings_residuals`, `counterevidence`, `shared_sources`, `opus_media`.
- Per-order detail is in `READINESS_BY_ORDER.csv`.

## Input problems

- STALE_SOURCE_AUDIT_HOLD:EO:10622: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- STALE_SOURCE_AUDIT_HOLD:EO:11040: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- STALE_SOURCE_AUDIT_HOLD:EO:11078: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- STALE_SOURCE_AUDIT_HOLD:EO:9922: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:1:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:2:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:3:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:4:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:5:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:6:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:7:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:8:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:9:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:10:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:11:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-panama-1922.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:2:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:4:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:5:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:6:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:10:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:11:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:12:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m001-trading-1920.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research\montfaucon\checks\m008-mixed-held-originals.jsonl:6:source fragment changed or ambiguous
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
- INVALID_MONTFAUCON_OFFICIAL_FRAGMENT
