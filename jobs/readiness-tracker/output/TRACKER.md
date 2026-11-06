# Readiness tracker

**Numbered series: ready for human review 1,208 of 14,998 orders (8.1%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator): not measured yet; `jobs/domesday-register/output/UNNUMBERED_SUMMARY.json` is missing.

Generation: `42230618454-1:e9cc03c4b6a97bf36b05401dd6e3770691d3b21fdfb36d7814f498e2022ab7e0` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,298. The other 10,700 have not been researched yet.

Ready by text evidence: {'original_supported': 657, 'transcription_dependent': 551}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 1,146; quotation rechecks: 1,146. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 560. Confirmations rejected: {'grade_not_a_working_text_grade': 4, 'not_confirmed': 5970}.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 4,298 | 4,298 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 3,268 | 4,298 | 76.0% |
| Complete inventory of the order's operative clauses | 1,447 | 4,298 | 33.7% |
| When and how it ended (NO), or what keeps it operating now (YES) | 1,228 | 4,298 | 28.6% |
| Savings clauses and surviving effects closed | 1,434 | 4,298 | 33.4% |
| Search for later contrary sources recorded, no open conflicts | 2,869 | 4,298 | 66.8% |
| Every shared legal source it cites has been retrieved | 212 | 236 | 89.8% |
| Opus evidence images matched to this order (Opus cases only) | 125 | 825 | 15.2% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 2,762 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 2,557 | agent check | Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held |
| 535 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 431 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 10 | one source | Retrieve shared source EO::4314 |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |
| 1 | agent check | Settle ambiguous Opus media matches (MATCHES.csv rows graded ambiguous) |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 10,700 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 766 | 4,787 |
| `NO_CLAUSE_INVENTORY` | 2,779 | 2,779 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 2,779 | 2,779 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 820 | 2,762 |
| `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` | 126 | 2,557 |
| `FIRST_END_UNPROVED` | 2,408 | 2,408 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 1,244 | 1,244 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 204 | 535 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 431 | 431 |
| `CURRENT_BASIS_UNPROVED` | 371 | 371 |
| `OPUS_MEDIA_NONE_CITED` | 198 | 198 |
| `FIRST_END_UNRESOLVED` | 184 | 184 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 141 | 141 |
| `CLAIM_INCOMPLETE` | 88 | 88 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `CLAIM_CHECK_FAILED` | 33 | 33 |
| `WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED` | 30 | 30 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 24 | 24 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 18 | 18 |
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

- fr-originals: 6,497
- opus-media-match fragments: 122
- ofr-compilations: 500
- isthmian-canal-1911: 105
- indian-reservations-1912: 55
- tischendorf-originals: 687
- mabillon-held-printings: 2,015
- richardson-volumes (lead only, never counted as the original): 68
- app-executive-orders (lead only, never counted as the original): 9,902
- hathi-gpo-orders (lead only, never counted as the original): 1,531
- numbered-early-orders (lead only, never counted as the original): 184
- wikisource-texts (lead only, never counted as the original): 1,639
- csc-annual-reports (lead only, never counted as the original): 798
- pinakes-proquest-ingest (archival replica scan, lead only until a page check and a codebook grade): 2,750
- lachmann working-text confirmations (provisional text step only, never an original): 7,738
- opus-media-match status: 1,155
- source-ladder: 673
- claim-checker: 1,519
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
