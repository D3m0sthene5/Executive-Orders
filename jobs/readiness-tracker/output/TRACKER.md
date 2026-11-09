# Readiness tracker

**Numbered series: ready for human review 1,183 of 14,998 orders (7.9%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 2,334 identities observed, a lower bound; estimated total 4,101 to 5,095 (95% interval). Not part of the numbered-series proportion above.

Generation: `42582944082-1:6c0d808e5e581640b7a559f15196564c84a93e7243075be64d69107aa5d696e7` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,301. The other 10,697 have not been researched yet.

Ready by text evidence: {'original_supported': 658, 'transcription_dependent': 525}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 847; quotation rechecks: 847. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 254. Confirmations rejected: {'grade_not_a_working_text_grade': 3, 'not_confirmed': 1630}.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 4,301 | 4,301 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 3,545 | 4,301 | 82.4% |
| Complete inventory of the order's operative clauses | 1,425 | 4,301 | 33.1% |
| When and how it ended (NO), or what keeps it operating now (YES) | 1,208 | 4,301 | 28.1% |
| Savings clauses and surviving effects closed | 1,412 | 4,301 | 32.8% |
| Search for later contrary sources recorded, no open conflicts | 2,874 | 4,301 | 66.8% |
| Every shared legal source it cites has been retrieved | 212 | 236 | 89.8% |
| Opus evidence images matched to this order (Opus cases only) | 125 | 825 | 15.2% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 2,222 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 675 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
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
| `NO_CLAUSE_INVENTORY` | 2,771 | 2,771 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 2,771 | 2,771 |
| `FIRST_END_UNPROVED` | 2,401 | 2,401 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 731 | 2,222 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 547 | 1,623 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 1,244 | 1,244 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 192 | 675 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 431 | 431 |
| `CURRENT_BASIS_UNPROVED` | 370 | 370 |
| `OPUS_MEDIA_NONE_CITED` | 198 | 198 |
| `FIRST_END_UNRESOLVED` | 184 | 184 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 139 | 139 |
| `CLAIM_INCOMPLETE` | 88 | 88 |
| `CLAIM_CHECK_FAILED` | 66 | 66 |
| `WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED` | 63 | 63 |
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

- fr-originals: 6,497
- opus-media-match fragments: 122
- ofr-compilations: 500
- isthmian-canal-1911: 105
- indian-reservations-1912: 55
- tischendorf-originals: 701
- mabillon-held-printings: 2,037
- photius-gpo-volumes: 3,679
- photius-csc-printings: 143
- photius-free-printings: 471
- montfaucon-page-check: 206
- richardson-volumes (lead only, never counted as the original): 68
- app-executive-orders (lead only, never counted as the original): 9,902
- hathi-gpo-orders (lead only, never counted as the original): 1,531
- numbered-early-orders (lead only, never counted as the original): 184
- wikisource-texts (lead only, never counted as the original): 1,639
- csc-annual-reports (lead only, never counted as the original): 798
- photius-replica-check (checked ProQuest replica: credits the text step, bytes ProQuest-dependent): 2,557
- montfaucon-page-check (checked ProQuest replica: credits the text step, bytes ProQuest-dependent): 0
- pinakes-proquest-ingest (archival replica scan, lead only until a page check and a codebook grade): 2,750
- lachmann working-text confirmations (provisional text step only, never an original): 2,408
- opus-media-match status: 1,155
- source-ladder: 821
- claim-checker: 1,530
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
