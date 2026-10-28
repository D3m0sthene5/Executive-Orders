# Readiness tracker

**Ready for human review: 303 of 14,972 orders (2.0%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,403. The other 11,569 have not been researched yet.

Ready by text evidence: {'original_supported': 289, 'transcription_dependent': 14}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 16; quotation rechecks: 16. These remain work after readiness.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,403 | 3,403 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 2,371 | 3,403 | 69.7% |
| Complete inventory of the order's operative clauses | 371 | 3,403 | 10.9% |
| When and how it ended (NO), or what keeps it operating now (YES) | 323 | 3,403 | 9.5% |
| Savings clauses and surviving effects closed | 359 | 3,403 | 10.5% |
| Search for later contrary sources recorded, no open conflicts | 2,548 | 3,403 | 74.9% |
| Every shared legal source it cites has been retrieved | 209 | 236 | 88.6% |
| Opus evidence images matched to this order (Opus cases only) | 125 | 839 | 14.9% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 5,333 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 2,749 | agent check | Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held |
| 431 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 285 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 10 | one source | Retrieve shared source EO::4314 |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source USC::48 U.S.C. 863) |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |
| 1 | agent check | Settle ambiguous Opus media matches (MATCHES.csv rows graded ambiguous) |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 11,569 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 945 | 7,800 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 930 | 5,333 |
| `NO_CLAUSE_INVENTORY` | 2,982 | 2,982 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 2,982 | 2,982 |
| `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` | 76 | 2,749 |
| `FIRST_END_UNPROVED` | 2,589 | 2,589 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 672 | 672 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 431 | 431 |
| `CURRENT_BASIS_UNPROVED` | 393 | 393 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 87 | 285 |
| `OPUS_MEDIA_NONE_CITED` | 212 | 212 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 139 | 139 |
| `CLAIM_INCOMPLETE` | 88 | 88 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 27 | 27 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 18 | 18 |
| `CLAIM_CHECK_FAILED` | 14 | 14 |
| `OPEN_SOURCE_AUDIT` | 6 | 6 |
| `WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED` | 2 | 2 |
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
- richardson-volumes (lead only, never counted as the original): 68
- app-executive-orders (lead only, never counted as the original): 9,902
- hathi-gpo-orders (lead only, never counted as the original): 1,531
- numbered-early-orders (lead only, never counted as the original): 184
- wikisource-texts (lead only, never counted as the original): 1,639
- csc-annual-reports (lead only, never counted as the original): 798
- pinakes-proquest-ingest (archival replica scan, lead only until a page check and a codebook grade): 2,750
- opus-media-match status: 1,155
- source-ladder: 677
- claim-checker: 421
- machine later-source search: 6,938

## Historical census candidates — separate from the 14,972 working identities

- Distinct LOC catalog item candidates: 67 (not yet admitted).
- LOC item transcripts obtained: 10.
- LOC items with retained original-page images: 3.
- Lord indexed date-row appearances awaiting identity authentication: 1,023, including 812 nineteenth-century gap leads.
**Newly admitted EOs: 0.** Catalog data and manuscripts need independent signer, authority, duplicate and legal inclusion review.
See jobs/census-candidates/output/CENSUS_READINESS.md and ITEM_CANDIDATES.csv.
