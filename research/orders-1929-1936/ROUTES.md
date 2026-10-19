# Routes to text for the 1,712 missing orders, 1929–1936

This route plan was written **before this run's order-text downloads**. The
fixed population is `jobs/hathi-gpo-orders/data/TARGETS.json`, from main
`224fd70cb6982f764d7f95f99102d1f1ab7d3fce`. There are 791 targets in
5076–6070, 921 in 6071–7531, and 117 in 7316–7531. These number-range counts
are ceilings, not proof that a collection prints each order. Letter suffixes
remain distinct. We will update outcomes below without treating a failed
search as proof of absence.

Rank is a qualitative coverage/work ranking for this assignment, not a
benchmark or a savings calculation. Permission is checked per host and item;
an unknown permission is not permission to fetch. One request at a time,
at least two seconds between starts, honoring longer robots delays. No login,
access challenge bypass, restricted book reconstruction, or mass Catalog scrape.

| Rank | Route and discovery links | Rough potential overlap | Automated access | Work needed |
|---:|---|---:|---|---|
| 1 | [UCSB American Presidency Project](https://www.presidency.ucsb.edu/): per-order executive-order transcriptions and dated search listings | Potentially hundreds of the 921 FDR targets, plus some of the 791 Hoover targets; actual title intersection must be counted | Check `/robots.txt` before listings or documents; only permitted public HTML, stop on host challenge/throttling | Low/medium: collect exact numbered links, validate each title including letters, keep attributed website transcriptions |
| 2 | [Internet Archive](https://archive.org/advancedsearch.php): alternate scans of *Herbert Hoover: Proclamations and Executive Orders* (GPO 1974), GPO bound orders, FDR papers | Up to 791 Hoover targets; potentially much of the other 921 if matching GPO scans exist | Public metadata and unrestricted download files only; respect robots, restricted/borrow-only/access-limited items excluded | Low/medium if complete OCR exists: reuse early-orders-hunt book custody, DjVu page parser and printed-page mapping; add number-heading segmentation locally |
| 3 | [GovInfo historical Federal Register](https://www.govinfo.gov/app/collection/FR/1936): daily issues from March 14, 1936 | At most 117 targets in 7316–7531, fewer if not published or outside the date window | Public content downloads; check robots. API search needs a free key, but known issue/content URLs do not | Low/medium: reuse fr-originals number/location and filing-end checks; its frozen OFR index starts in 1937, so use 1936 issue metadata or citations |
| 4 | [Library of Congress digitized CFR](https://www.loc.gov/collections/code-of-federal-regulations/): 1938 Title 3 compilation, 1936–1938 supplements | Up to the same 117 late-period targets; codifications can omit or amend text | LOC offers machine-readable item/resource metadata and public files; check robots and observe its delay | Medium: find actual Title 3 text volume, not a table listing orders; reuse PDF/page machinery and label printed/codified copy |
| 5 | [GovInfo GOVPUB and public-papers collections](https://www.govinfo.gov/app/collection/GOVPUB): alternate government scans of Hoover/GPO volumes | 791 Hoover ceiling; up to 1,712 if the bound series is deposited | Public offered content permitted subject to robots; API discovery requires key; public catalog/search may suffice | Medium: search bibliographic title and volume numbers, fetch a matching book once, parse numbered headings |
| 6 | [Google Books](https://books.google.com/): alternate scans and offered full-view PDFs of the same books | Up to 791 in Hoover set and 921 in GPO/FDR volumes; availability unverified | Only an explicitly offered unrestricted download; no snippet stitching, page-image scraping, captcha handling, or login | Medium; download offers may need a person; imports must accept supplied PDFs/OCR |
| 7 | [University of Pennsylvania Online Books Page](https://onlinebooks.library.upenn.edu/webbin/book/lookupname?key=Hoover%2C+Herbert%2C+1874-1964) and university/state-library repositories | A complete Hoover copy could cover up to 791; GPO series up to 1,712 | Discovery indexes can be public; verify each repository's robots and rights. A HathiTrust redirect does not reopen HathiTrust | Medium: follow genuine independent download deposits; exclude subscription copies and catalog-only hits |
| 8 | [FDR Presidential Library digital collections](https://www.fdrlibrary.org/digital-collections), *Public Papers and Addresses* and Master Speech File | 921 FDR ceiling; probably a selective subset, not every order | Public offered files after robots check; catalog/API access subject to service terms | Medium/high: identify full-order reproductions rather than speech references or EO indexes |
| 9 | [Hoover Presidential Library](https://hoover.archives.gov/research): executive-order/proclamation files and official e-books | 791 Hoover ceiling; public-papers appendices may only list orders | Public static files after robots check; digitized archival objects via the sanctioned collection route | Medium: distinguish actual order pages from finding aids and the public-papers list; a finding aid is not text |
| 10 | Agency annual reports, land-withdrawal compilations, and congressional documents through [LOC](https://www.loc.gov/) / [GovInfo](https://www.govinfo.gov/) / [IA](https://archive.org/) | Planning estimate tens to a few hundred, heavily overlapping; not yet enumerated | Public-domain offered files and documented APIs only; each host/item checked | Higher: target still-missing numbers, require the full order heading and passage, exclude mere citations and summaries |
| 11 | [FRASER, Federal Reserve Bank of St. Louis](https://fraser.stlouisfed.org/): monetary/banking orders reproduced in bulletins and circulars | Planning estimate 10–60; overlap and exact coverage unknown | Public download links after robots/terms check; do not assume API key-free access | Medium: subject-specific discovery, exact order-number and complete-text checks |
| 12 | [NARA static executive-order codification](https://www.archives.gov/federal-register/codification/executive-orders.html): official HTML copies, separate from Catalog API | Planning estimate 0–30 still-missing targets; selected codified orders, not a complete historical corpus | Check archives.gov robots; public HTML can be used under site policy | Low: enumerate official links, exact-ID intersection, label government codification rather than original as issued |
| 13 | [NARA Catalog official API](https://www.archives.gov/research/catalog/help/api), RG 11 Executive Orders series | Potential ceiling 1,712; per-order digitized/OCR subset unknown | Requires owner's API key. Current terms also say not to cache/store API-returned content, so archival download/storage scope needs clarification; no Catalog scraping | Human key request and storage-permission question, then a narrow numbered-series query; not an automatic no-key route |
| 14 | [NARA official open-data Catalog export](https://www.archives.gov/developer) / dataset request | Potential ceiling 1,712, with unknown OCR/image completeness | Official export is the suggested bulk-metadata route; verify export/object reuse terms; do not download the entire Catalog | Higher: narrowly filter description metadata for RG 11 and period; request a small item/OCR manifest from the library/archive if no selective public index |
| 15 | Human downloads from the [ten-volume inventory](../../jobs/hathi-gpo-orders/data/VOLUMES.json), or a librarian's permitted OCR dataset | 791 Hoover targets; all ten ranges jointly contain all 1,712 candidates, not verified inclusions | Human use must follow the site's offered download rights; no logging in or bypass by this job; do not reconstruct restricted books page by page | Under-30-minute actions will be listed in HUMAN_STEPS.md; job must accept local PDF, OCR text, or DjVu XML plus source metadata |

## Source-specific cautions

- HathiTrust remains closed to automation; it will not be contacted again.
- Hoover's *Public Papers* e-book says the complete orders are in the separate
  1974 *Proclamations and Executive Orders*; an appendix listing is not a text.
- FDR's *Public Papers* includes order lists as well as selected reproductions;
  a number occurrence or a date does not establish a recovered order.
- NARA's [API terms](https://www.archives.gov/research/catalog/help/api) are
  distinct from its [official bulk-export guidance](https://www.archives.gov/developer).
  A free key alone does not resolve storage permission or prove digitization.
- Each lower-ranked route will see only the IDs still missing after earlier
  routes. An attributed derivative never becomes an authenticated original.

## Run outcomes

The run saved **1,531 unique target texts; 181 remain missing**. The unchanged
claim-kit loader recognizes all 1,531, each with `acceptable_as_original:false`.
The fixed-population [RESULTS.csv](../../jobs/hathi-gpo-orders/output/RESULTS.csv)
has exactly 1,712 data rows. Counts below are additions after earlier routes,
so there is no double counting. `SOURCES.jsonl` identifies each text's route,
source-byte hash, copy type and page. No status was decided.

| Route | Result for the fixed population | Access or content outcome |
|---|---:|---|
| Internet Archive Hoover GPO compilation | **781** | Two unrestricted 1974 GPO volumes, existing custody/checksum/page-map code; dated captions and exact-number ends. Damaged OCR remains labelled. |
| GovInfo 1936 Federal Register | **54** | Existing locator/filing-end checks across 206 daily issues; 37 supplying issues retained, page context included. |
| Wikimedia Commons GPO scans | **689** | Eight independently offered public-domain DjVu volumes; no embedded text, so local OCR. Five additions are Hoover-period; 684 are FDR-period. |
| UCSB APP | 0 | Robots expressly exclude GPTBot and ChatGPT-User. No order pages acquired; human permission/export route. |
| IA FDR Public Papers, 1933–1936 | 0 additional | Four open books checked for full residual-order entries; candidate excerpts had ellipses or unreadable exact-caption boundaries. Commercial book OCR is cache-only, not republished. |
| LOC early Title 3 CFR | 0 additional | Three 1938 executive-order resources offered PDFs; tables/indexes, not full residual-order passages. |
| Agency/congressional reprints | 0 additional | Three unrestricted IA books checked (coal code, veterans public acts, Canal Zone measures). No new complete exact-ID passage recovered. |
| FRASER | 0 additional | Ten monetary/banking result pages checked, including publicly offered PDF links in citation metadata. No complete exact-number residual passage recovered. |
| NARA static codification | 0 additional | Correct numeric index and 5000–6999/7000–7999 tables checked. One linked full-text order (6166) was already held. Disposition entries were not adopted as status decisions. |
| Direct residual Wikisource titles | 0 additional | All 188 exact titles checked sequentially, no API; all returned HTTP 404. This closes only these exact titles, not every possible alias. |
| Wikisource scan-page namespace | **7** | Eight volume indexes checked; three absent, two sparse, one with no page text. Exact numbered passages in the 7262–8027 volume supplied seven new volunteer transcriptions, each with page revision custody. |
| Google Books | 0 | First public metadata request returned HTTP 429; host stopped, no retries or download workaround. |
| University/state-library discovery | 0 additional | Penn's Hoover bibliography inspected; no independent unrestricted download of missing-order texts identified. Hathi links remained excluded. This does not establish absence from university repositories. |
| Hoover Presidential Library | 0 additional | Public e-book catalog inspected; public-papers appendices are finding aids, separate from the 1974 order compilation used via IA. |
| FDR Presidential Library | 0 | Digital-collections landing page failed TLS certificate validation. No bypass. FDR reprints were checked independently through IA. |
| GovInfo GOVPUB/API | 0 | UI search wildcard restriction enforced after detecting that the shared parser missed it; the fetched SPA supplied no texts. Separately offered API demonstration route stopped when its robots access returned HTTP 500, before a search POST. |
| NARA Catalog API/export | 0 | Key required; official API terms prohibit caching/storing returned content. No API calls or Catalog scrape. No selective public OCR manifest identified; request an authorized narrow export. |
| Human/library-supplied files | Not supplied in this run | Offline importer implemented for lawful PDFs, DjVu/XML, page text and per-order exports. See HUMAN_STEPS.md. |

These outcomes exhaust the concrete public download candidates discovered in
this run, not every book or agency publication on the web. The remaining
181 are not a finding that text does not exist. They include five Hoover
targets and 176 FDR targets. OCR number/boundary failures remain in the
historical extraction log. A navigation queue has number occurrences for 105
remaining identities; an occurrence can be a citation to a different order.

Receipts: [summary](../../jobs/hathi-gpo-orders/output/SUMMARY.json),
[read-only ingestion check](../../jobs/hathi-gpo-orders/output/INGESTION_CHECK.json),
[attempts](../../jobs/hathi-gpo-orders/output/ROUTE_ATTEMPTS.jsonl),
[remaining texts](../../jobs/hathi-gpo-orders/output/MISSING.csv),
[page-check leads](../../jobs/hathi-gpo-orders/output/PAGE_CHECK_QUEUE.csv).
No download/extraction dependency or status record was edited.

## Additional route found during discovery, before its downloads

**Wikimedia Commons independent copies of the GPO volumes.** The public
[Executive Orders category](https://commons.wikimedia.org/wiki/Category:Executive_orders_of_the_United_States)
lists DjVu files such as
[6071–6250](https://commons.wikimedia.org/wiki/File:Executive_Orders_6071-6250.djvu).
The potential range overlap is the 921 FDR targets in the eight GPO volumes,
plus some of the 120 Hoover targets left after the first IA extraction. This
route ranks immediately after the open IA Hoover copies: one offered file
per book and its embedded OCR, with public-domain government-work notices.
Automation still requires Commons/upload-host robots checks. No HathiTrust
request or API bypass is involved. Work is medium: reuse the book page mapper,
decode offered DjVu OCR with an existing codec if available, and validate
exact order headings and closing boundaries. Raw scan availability alone
will not be counted as usable text.

**Direct Wikisource page check for the residual IDs (additional route).** The
earlier 1,639 matches were a lower bound from author indexes, and three index
reads failed. A title missing from that inventory is not proof that its page
does not exist. Before this additional route is downloaded, 188 targets remain.
Their exact canonical page titles can be checked using the same permitted
HTML route, number-heading check, revision custody, and source-ladder extractor
as `jobs/wikisource-texts`. Potential coverage is 0–188; actual intersection is
unknown. Work is low, with one request at a time, two-second spacing and no
API. Each success will be a website/volunteer transcription, not an original;
404s and redirects to a different order will remain failures.

**GovInfo API discovery clarification, before its requests.** GPO's
[official API documentation](https://github.com/usgpo/api#search-service) and
[demo examples](https://www.govinfo.gov/features/api) explicitly offer a public
`DEMO_KEY` for initial exploration. The UI search path remains robots-excluded;
the documented API is a separate offered interface. We will make at most three
narrow POST searches for the missing-era government books, honoring the API
host's rules and stopping on any denial or limit. A personal key is only a
human fallback if the public demonstration requests cannot be used. This is
metadata discovery, followed only by offered public files with plausible
coverage of residual IDs.

**Wikisource scan-page namespace (last discovery check, before downloads).**
A missing standalone order title does not exclude a volunteer transcription
under a volume's `Page:` namespace. Public `Index:` pages for the eight GPO
volumes can show whether those transcriptions exist. Potential overlap is
0–184 remaining targets in those volume ranges (four Hoover targets precede
them); individual coverage is unknown. Inspect indexes first; follow only
existing page links if they offer actual text, use the same robots-aware HTML
route and revision custody, and label any success as a volunteer transcription.
Work is low if pages are already proofread; absent/red-link pages supply no
text and will not trigger page creation or editing.
