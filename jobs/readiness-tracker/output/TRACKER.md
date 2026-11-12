# Readiness tracker

**Numbered series: ready for human review 1,251 of 15,002 orders (8.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `43213002407-1:2b62530b8f1315a51b492338ae83136392ea244879cb6a3e23d99be7363dde09` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,788. The other 11,214 have not been researched yet.

Ready by text evidence: {'original_supported': 725, 'transcription_dependent': 526}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 883; quotation rechecks: 883. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 284. Confirmations rejected: {'grade_not_a_working_text_grade': 2, 'not_confirmed': 1550}.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,788 | 3,788 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 3,534 | 3,788 | 93.3% |
| Complete inventory of the order's operative clauses | 1,493 | 3,788 | 39.4% |
| When and how it ended (NO), or what keeps it operating now (YES) | 1,283 | 3,788 | 33.9% |
| Savings clauses and surviving effects closed | 1,480 | 3,788 | 39.1% |
| Search for later contrary sources recorded, no open conflicts | 2,884 | 3,788 | 76.1% |
| Every shared legal source it cites has been retrieved | 212 | 236 | 89.8% |
| Opus evidence images matched to this order (Opus cases only) | 125 | 788 | 15.9% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 2,168 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 705 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
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
| `NO_PROVISIONAL_STATUS` | 0 | 11,214 |
| `NO_CLAUSE_INVENTORY` | 2,185 | 2,185 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 2,185 | 2,185 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 229 | 2,168 |
| `FIRST_END_UNPROVED` | 1,870 | 1,870 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 124 | 1,543 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 721 | 721 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 113 | 705 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 431 | 431 |
| `CURRENT_BASIS_UNPROVED` | 315 | 315 |
| `FIRST_END_UNRESOLVED` | 184 | 184 |
| `OPUS_MEDIA_NONE_CITED` | 161 | 161 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 139 | 139 |
| `CLAIM_INCOMPLETE` | 82 | 82 |
| `CLAIM_CHECK_FAILED` | 71 | 71 |
| `WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED` | 68 | 68 |
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

## Job outputs read

- fr-originals: 6,498
- opus-media-match fragments: 122
- ofr-compilations: 500
- isthmian-canal-1911: 105
- indian-reservations-1912: 55
- tischendorf-originals: 722
- mabillon-held-printings: 2,037
- photius-gpo-volumes: 3,679
- photius-csc-printings: 143
- photius-free-printings: 471
- montfaucon-page-check: 185
- richardson-volumes (lead only, never counted as the original): 68
- app-executive-orders (lead only, never counted as the original): 9,902
- hathi-gpo-orders (lead only, never counted as the original): 1,531
- numbered-early-orders (lead only, never counted as the original): 184
- wikisource-texts (lead only, never counted as the original): 1,639
- csc-annual-reports (lead only, never counted as the original): 798
- photius-replica-check (checked ProQuest replica: credits the text step, bytes ProQuest-dependent): 2,557
- montfaucon-page-check (checked ProQuest replica: credits the text step, bytes ProQuest-dependent): 0
- pinakes-proquest-ingest (archival replica scan, lead only until a page check and a codebook grade): 2,750
- lachmann working-text confirmations (provisional text step only, never an original): 2,360
- opus-media-match status: 1,155
- source-ladder: 986
- claim-checker: 1,604
- machine later-source search: 6,938

## Historical census candidates — separate from the 14,972 working identities

- Distinct LOC catalog item candidates: 67 (not yet admitted).
- LOC item transcripts obtained: 0.
- LOC items with retained original-page images: 3.
- Lord indexed date-row appearances awaiting identity authentication: 1,023, including 812 nineteenth-century gap leads.
**Newly admitted EOs: 0.** Catalog data and manuscripts need independent signer, authority, duplicate and legal inclusion review.
See jobs/census-candidates/output/CENSUS_READINESS.md and ITEM_CANDIDATES.csv.

## Input problems

- STALE_SOURCE_AUDIT_HOLD:EO:10622: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- STALE_SOURCE_AUDIT_HOLD:EO:11040: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- STALE_SOURCE_AUDIT_HOLD:EO:11078: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- STALE_SOURCE_AUDIT_HOLD:EO:9922: reconcile changed claim with research/progress/branch-recovery-2026-10-29/MANSFIELD_AUDIT.json
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:1:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:2:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:3:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:4:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:5:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:6:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:7:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:8:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:9:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:10:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:11:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:2:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:4:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:5:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:6:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:10:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:11:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:12:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:6:source fragment changed or ambiguous
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
