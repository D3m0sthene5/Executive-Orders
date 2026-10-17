# Stage 22 — early executive-order ranger, recovered sources and review pipeline

**State: completed discovery and document-acquisition pilot.** All research is additive and uncounted. Legal cutoff October 14, 2026; immutable legal codebook 2.0.0.

## Substantive results

The original Stage 19 early ranger had **1,023 unverified Lord OCR date leads**, six Stage 18 curated candidate source representations and **3,403 planned search routes**. The Stage 20 ranger added **438 planned annual routes** across 1789–1861. The difference this stage makes is **actual searches, manuscript metadata, historical transcripts, source page scans and reviewer worklists**.

| Recovery tier | Completed outcome | Source |
|---|---:|---|
| Live LOC/Internet Archive JSON queries | **28 successful** out of 56 prepared; four failures and 24 skipped after provider blockage | [Live scout](../../jobs/early-ranger-scout/output/SCOUT_SUMMARY.json) |
| Distinct LOC manuscript/resource catalog links recovered | **65**, based on cached JSON response reparsing | [LOC reparse](../../jobs/early-ranger-reparse/output/REPARSE_SUMMARY.json) |
| Years without an inherited Lord lead now containing LOC metadata leads | **17** in 1789–1861; does not prove actual presidential issuance | [Triage](../../jobs/early-ranger-triage/output/TRIAGE_SUMMARY.json) |
| LOC in-term paper shortlists | **6** titled directive leads, **14** other presidential-period paper leads | [Candidate review list](../../jobs/early-ranger-triage/output/CAPACITY_TRIAGE_REPORT.md) |
| Official LOC item metadata packets | **19 of 21** targeted records (2 requests timed out) | [Item metadata](../../jobs/early-ranger-original-items/output/METRICS.json) |
| LOC manuscript full-text XML/transcriptions | **9 of 9** LOC XML links downloaded, 10,006 words, retained original XML and derived text | [Transcriptions](../../jobs/early-ranger-transcriptions/output/TRANSCRIPTION_METRICS.json) |
| Early item preliminary facsimiles | **14** source-file representations for **7** candidates; note that tiny PDF service derivatives are not substitutes for checking the master JPG pages | [Pilot facsimiles](../../jobs/early-ranger-facsimiles/output/FACSIMILE_METRICS.json) |
| Official full-resolution/master manuscript JPEGs retained | **10 of 10** known LOC master-resource pages across **3** targeted documents (Madison 1814, Jackson 1832, Jefferson 1803) | [Page image custody](../../jobs/early-ranger-full-pages/output/PAGE_IMAGE_METRICS.json) |
| New combined historical-review workbench | **21** source items; **9** searchable transcriptions; **10** direct manuscript page images | [Open/download HTML workbench](../../jobs/early-ranger-workbench/output/EARLY_SOURCE_REVIEW_WORKBENCH.html) |
| Admitted additional historical executive orders | **0** | Inclusion remains unadjudicated |

[Historical directive shortlist](HISTORICAL_DIRECTIVE_PILOT.md) and [machine-readable candidate entries](CANDIDATE_DIRECTIVES.json) discuss three particularly promising historical presidential instructions.

The strongest operative candidate is **Madison's August 13, 1814 memorandum to Secretary of War John Armstrong**, which gives ten categories of War Department action requiring previous communication to the president, with an urgency exception and an immediate military-intelligence reporting rule. LOC item [mjm017456](https://www.loc.gov/item/mjm017456/) supplies the manuscript page series, LOC-derived transcription and original-source candidate. Two subsequent Madison memoranda refer to the instructions and may corroborate the historical instruction's use. Whether it is within the project's executive-order inclusion criteria, and its first cessation if any, remain unanswered.

**Jackson's October 29, 1832 direction to Secretary of War Lewis Cass** to issue confidential Charleston harbor fort-defense orders is another concrete presidential command candidate. **Jefferson's June 1803 instructions to Meriwether Lewis** contain concrete expedition-related federal directions and statutory authority; the edited transcript uses an *ante June 20* qualifier, so the catalog date must not be treated as unquestioned signing date. These findings allow document-level review instead of guessing from titles.

## Post-1861 scientific frame correction

The initial [1862–1906 gap study](../../jobs/early-ranger-1862-1906/output/GAP_SUMMARY.json) found **812 Lord OCR date markers**, unverified, and **611** included proxy identities in Stage 15's older projected year frame. The [verified canonical Stage 17 SQLite reconciliation](../../jobs/early-ranger-year-reconcile/output/BRIDGE_SUMMARY.json) corrects the latter to **617 included identities** and identifies **18 year-field changes** across the entire working population (including previously missing dates on unnumbered proxies).

**Twelve years** still have zero included 1862–1906 proxy identities under Stage 17, despite Lord OCR date leads: **1864, 1867, 1869, 1870, 1877, 1878, 1879, 1880, 1882, 1883, 1888 and 1889**. They need focused original-document crosswalks, not an automatic 1800s issuance estimate. The [annual matrix](../../jobs/early-ranger-year-reconcile/output/LATEST_1862_1906_CENSUS_YEAR_MATRIX.csv) and the [812-marker queue](../../jobs/early-ranger-1862-1906/output/UNAUTHENTICATED_19C_LORD_DATE_LEADS.csv) are now ready for targeted research. The 180 new annual routes have been planned; those are **not live searches**.

The official Library of Congress research guide cautions that many pre-1936 executive orders were not deposited with the Department of State and some records may have been lost: https://guides.loc.gov/executive-orders/publications. The 1936–37 Archivist annual report identifies substantial agency-held documents outside the primary executive-order holdings: https://www.archives.gov/files/about/history/sources/reports/1937-annual-report.pdf. Accordingly, an unverified historical denominator must remain unknown.

## How to use the workbench to accelerate later batches

1. Choose a candidate and read the LOC-derived transcription beside its original master-image pages where available. For records lacking pages, follow the LOC catalog/resource links.
2. Record source identity, actual issuer and capacity, page/folio, all potentially operative instructions, original date ambiguity, and whether the document is already represented in Lord or the analytic bibliography.
3. Export the **uncertified research-only** worksheet, preserve source-image/transcription links, and place it in a new historical inclusion-review queue before deciding whether the document is an EO under immutable codebook 2.0.0.
4. Only after the identity/inclusion problem is resolved should a researcher undertake the separate whole-lifecycle first-end/current-predicate, savings and independent review gates. No mechanical search or catalog presence certifies a historical legal conclusion.

**Recommended next machine investment:** Scale the metadata-to-XML-and-master-image pipeline across the most promising Lord date leads and 12 zero-proxy years, reusing downloaded pages and measuring cost per correctly classified potential instrument. Keep uncertain/irrelevant candidates in the audit denominator to measure search precision; do not silently drop negative leads.

## Status retained

Working bibliographic population **14,972**; provisional substantive YES/NO classifications **3,359**; independent human-reviewed complete-lifecycle dossiers **0**. Stage 22 adds documentary research and a reproducible review interface, with **zero** automatic promotions to the EO census or certified legal-effect ledger.
