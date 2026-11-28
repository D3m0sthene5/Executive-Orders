# Readiness tracker

**Numbered series: ready for human review 1,395 of 15,003 orders (9.3%)**

Unnumbered series (class catalogued_unnumbered, a separate denominator, no readiness count): 1,816 identities observed, a lower bound. Not part of the numbered-series proportion above.

Generation: `46088413618-1:caac133b27fdf123ac32a016d4429b700f5be0f79a24e9c97e9ea22fe44cf54c` (the same id is in SUMMARY.json, READINESS_BY_ORDER.csv and STATUS.json).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,801. The other 11,202 have not been researched yet.

Ready by text evidence: {'original_supported': 842, 'transcription_dependent': 551, 'custody_text_only': 2}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 850; quotation rechecks: 850. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 255. Confirmations rejected: {'grade_not_a_working_text_grade': 1, 'not_confirmed': 179}.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,801 | 3,801 | 100.0% |
| Original or explicitly reviewed provisional working text saved | 3,763 | 3,801 | 99.0% |
| Complete inventory of the order's operative clauses | 1,613 | 3,801 | 42.4% |
| When and how it ended (NO), or what keeps it operating now (YES) | 1,432 | 3,801 | 37.7% |
| Savings clauses and surviving effects closed | 1,600 | 3,801 | 42.1% |
| Search for later contrary sources recorded, no open conflicts | 2,899 | 3,801 | 76.3% |
| Every shared legal source it cites has been retrieved | 212 | 236 | 89.8% |
| Opus evidence images matched to this order (Opus cases only) | 125 | 763 | 16.4% |

## Do these first: one action, many orders

| Orders unblocked | Kind | Action |
|---:|---|---|
| 431 | machine job | Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl |
| 170 | machine job | Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy |
| 75 | agent check | Check the page location of fr-originals and official-compilation finds marked medium/low confidence |
| 17 | agent check | Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held |
| 10 | one source | Retrieve shared source EO::4314 |
| 6 | one source | Retrieve shared source EO::6868 |
| 3 | one source | Retrieve shared source EO::6964 |
| 3 | one source | Retrieve shared source EO::6910 |
| 2 | one source | Retrieve shared source CFR::26 CFR 458.324 |
| 1 | agent check | Settle ambiguous Opus media matches (MATCHES.csv rows graded ambiguous) |

## What blocks orders

| Blocker | Orders with a status | All orders |
|---|---:|---:|
| `NO_PROVISIONAL_STATUS` | 0 | 11,202 |
| `NO_CLAUSE_INVENTORY` | 2,105 | 2,105 |
| `SAVINGS_RESIDUALS_NOT_CLOSED` | 2,105 | 2,105 |
| `FIRST_END_UNPROVED` | 1,867 | 1,867 |
| `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` | 721 | 721 |
| `OPUS_MEDIA_REFETCH_NEEDED` | 431 | 431 |
| `CURRENT_BASIS_UNPROVED` | 238 | 238 |
| `ONLY_COMPILED_TRANSCRIPTION_FOUND` | 16 | 170 |
| `NO_OFFICIAL_SOURCE_LOCATED` | 9 | 165 |
| `FIRST_END_UNRESOLVED` | 154 | 154 |
| `MACHINE_SEARCH_FOUND_CONTRARY_LEAD` | 139 | 139 |
| `OPUS_MEDIA_NONE_CITED` | 136 | 136 |
| `CLAIM_INCOMPLETE` | 82 | 82 |
| `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` | 12 | 75 |
| `OPUS_MEDIA_PARTLY_RESOLVED` | 52 | 52 |
| `CLAIM_CHECK_FAILED` | 44 | 44 |
| `WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED` | 39 | 39 |
| `QUARANTINED_RELATIONSHIP_CONFLICT` | 36 | 36 |
| `SHARED_SOURCE_NOT_RETRIEVED` | 24 | 24 |
| `OPUS_MEDIA_ORIGINAL_NOT_KEPT` | 18 | 18 |
| `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK` | 0 | 17 |
| `OPEN_SOURCE_AUDIT` | 4 | 4 |
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
- tischendorf-originals: 256
- mabillon-held-printings: 2,039
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
- photius-replica-check (checked ProQuest replica: credits the text step, bytes ProQuest-dependent): 4,648
- montfaucon-page-check (checked ProQuest replica: credits the text step, bytes ProQuest-dependent): 0
- pinakes-proquest-ingest (archival replica scan, lead only until a page check and a codebook grade): 4,841
- lachmann working-text confirmations (provisional text step only, never an original): 958
- opus-media-match status: 1,155
- source-ladder: 1,100
- claim-checker: 1,697
- machine later-source search: 6,938

## Historical census candidates — separate from the 14,972 working identities

- Distinct LOC catalog item candidates: 67 (not yet admitted).
- LOC item transcripts obtained: 0.
- LOC items with retained original-page images: 3.
- Lord indexed date-row appearances awaiting identity authentication: 1,023, including 812 nineteenth-century gap leads.
**Newly admitted EOs: 0.** Catalog data and manuscripts need independent signer, authority, duplicate and legal inclusion review.
See jobs/census-candidates/output/CENSUS_READINESS.md and ITEM_CANDIDATES.csv.

## Input problems

- STALE_SOURCE_AUDIT_HOLD:EO:13101: reconcile changed claim with research/valla/pilot-2026-10-20/METHOD_REVIEWS.jsonl
- STALE_SOURCE_AUDIT_HOLD:EO:13148: reconcile changed claim with research/valla/pilot-2026-10-20/METHOD_REVIEWS.jsonl
- STALE_SOURCE_AUDIT_HOLD:EO:13101: reconcile changed claim with research/excavator/astra-portfolio-repair-2026-10-20/lambertini-review/EO_13101.audit.v1.json
- STALE_SOURCE_AUDIT_HOLD:EO:13148: reconcile changed claim with research/excavator/astra-portfolio-repair-2026-10-20/lambertini-review/EO_13148.audit.v1.json
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
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:12:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-panama-1922.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:1:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:2:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:3:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:4:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:5:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:6:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:7:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:8:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:9:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:10:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:11:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:12:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m001-trading-1920.jsonl:14:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:5:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:6:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:7:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:8:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:9:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:10:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:11:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:12:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:14:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:15:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:16:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:17:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:18:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:19:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:20:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:21:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:22:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:23:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:24:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:25:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:26:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:27:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:29:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:30:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:31:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:32:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:33:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:35:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:36:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:37:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:38:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:39:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:40:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:41:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:42:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:43:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:44:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:45:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:46:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:47:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:48:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:49:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m008-mixed-held-originals.jsonl:50:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:16:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:17:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:18:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:19:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:20:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:21:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:22:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:23:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:24:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:25:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:26:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:27:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:28:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:29:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:30:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:31:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:32:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:33:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:34:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:35:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:36:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:37:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:38:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:39:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:40:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:41:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:42:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:43:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:44:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:45:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:46:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:47:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:48:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:49:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m009-held-1936-and-reports.jsonl:50:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:1:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:2:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:3:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:4:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:5:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:6:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:7:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:8:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:9:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:10:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:11:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:12:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:13:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:14:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:15:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:16:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:17:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:18:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:19:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:20:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:21:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:22:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:23:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:24:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:25:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:26:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:27:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:28:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:29:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:30:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:31:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:32:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:33:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:34:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:36:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:37:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:38:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:39:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:40:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:41:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:42:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:43:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:44:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:45:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:46:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:47:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:48:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:49:source fragment changed or ambiguous
- MONTFAUCON_REJECTED:research/montfaucon/checks/m010-annual-report-negatives.jsonl:50:source fragment changed or ambiguous
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
