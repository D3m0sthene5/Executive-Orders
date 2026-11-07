# 03 Legal data sources, APIs, citators and datasets (written 2026-11-06)

## How this was researched, and its limits

- I opened pages with WebFetch (Anthropic's fetcher, which answers a prompt over the page) and probed the Federal Register API directly.
  Direct `curl` from this sandbox is blocked by the egress proxy for federalregister.gov, ecfr.gov, api.govinfo.gov, govinfo.gov/bulkdata,
  uscode.house.gov, archives.gov and static.case.law (HTTP 403 on CONNECT), so I could not download sample files. Everything below about field
  names and coverage comes from fetched pages or fetched API records. WebFetch also refused several hosts via robots.txt (api.govinfo.gov/docs, congress.gov,
  dataverse.harvard.edu, bloomberglaw.com) and blocked courtlistener.com bulk-data pages.
- The shared WebSearch budget ran out partway through. I could not run forum searches (Hacker News, Reddit, GitHub issues) for the legal databases
  after that point, and I found no user-experience reports for most items. Where I say "no user evidence found", that means not searched or not found, not "none exists".
- Nothing here about vendor terms of use (Westlaw, Lexis, Bloomberg Law, HeinOnline, ProQuest) was read from the actual contracts. The usual position of
  those vendors is that systematic downloading and scraping are barred; treat that as an assumption to check with the NYU Law librarians before any automation.
- Two claims in the fetched summaries were inconsistent and are flagged where they matter (govinfo API rate limit; APP document counts).
- The repo already uses several of these sources. I checked jobs READMEs and `kean.py search`: the repo already has the Federal Register API notes (`jobs/status-history`,
  `jobs/later-events`), the 1989 OFR Codification and its disposition tables (`jobs/ofr-codification-1989`), eCFR and U.S. Code scans (`jobs/current-law`),
  NARA catalog (`jobs/mabillon-nara`), ProQuest PDFs uploaded by the owner (`jobs/pinakes-proquest-ingest`), HathiTrust and Internet Archive Hoover volumes, a Shepard-style
  citer job (`jobs/shepard-citations`), and Lowande and Poznansky cited in the audit dossier. The Kean register had no earlier work on CourtListener, CAP, KeyCite,
  HeinOnline, or Wikidata.

## The central finding

No source in scope records "when and how did this order end" as structured data. Every status source is editorial free text produced or inherited from one chain:
the Office of the Federal Register (OFR) disposition tables, which now live in the federalregister.gov fields `executive_order_notes` and `disposition_notes`.
The commercial citators and HeinOnline/ProQuest mostly re-present that chain or the primary texts. None records lapse by own terms, spent orders, implicit supersession,
or loss of statutory authority, and none distinguishes a cleanup revocation from the real end. The project's own sealed-evidence method is therefore not replaceable by
a database lookup; databases can only supply candidate end events earlier and cheaper. All academic datasets measure formal revocation only.

---

## A. Federal and official sources

- **Federal Register API, executive-order records** ([API intro](https://www.federalregister.gov/developers/documentation/api/v1); record fetched at
  `https://www.federalregister.gov/api/v1/documents/2017-02095.json`) — JSON for every Federal Register document, including presidential documents, with no API key.
  - Fields (opened a real record, EO 13767, 48 keys): `executive_order_number`, `presidential_document_number`, `signing_date`, `publication_date`, `citation`, `document_number`,
    `executive_order_notes`, `disposition_notes`, `correction_of`, `corrections`, `subtype`, `pdf_url`, `full_text_xml_url`, `body_html_url`, `raw_text_url`, `mods_url`,
    `cfr_references`, `start_page`, `end_page`, `volume`, `page_views`, and others. For EO 13767 both `executive_order_notes` and `disposition_notes` read
    "Revoked by: EO 14010, February 2, 2021" (one sample, so I cannot say the two fields are always identical). For EO 13981 (2021) both were null. The record has no "president"
    key; `related` links were empty.
  - Coverage and completeness: the year-browse pages (opened Truman 1953) show per-order relationship lines: "Amends", "Amended by", "Revokes", "Revoked by", "Supersedes",
    "Superseded in part by", "See". Examples: EO 10427 "Revoked by: EO 11575, December 31, 1970"; EO 10426 "Revoked by: Public Law 212, August 7, 1953, 43 USC 1331 note";
    EO 10431 "Amended by: EO 13709, October 2, 2015" (so OFR updates old orders when a modern order touches them). Many orders have no line at all. The Desktop copy of the Legal Status
    disclaimer says the site is not an official legal edition. The sample dates are the later instrument's signing date, not its effective date.
  - Terms and limits: documented as keyless; one blog says only a "polite rate cap" with no numbers. The interactive endpoint docs were not retrievable, so I cannot confirm per-page and
    10,000-result limits from a page I opened. Text is a government work. Weaker point: `executive_order_notes` is free text, so parsing relation type and date needs a rule set (the repo has one).
  - Answers "when and how did this order end"? Partly: gives a candidate end instrument and its signing date for orders OFR treats as revoked or amended; silent on lapse, spent, statute.
  - Access route for the project: already in use. Cost: free. Maturity: long-running, maintained by OFR.
  - Evidence from users: only vendor and blog summaries of the API; no measured accuracy study found. Hype: none; the claim that notes are "disposition tables" is OFR's own.
  - Fit: finding when a later order ended an order. Adoption: already done; remaining work is a periodic diff (the API supports modification-date filtering; unverified here) and an audit of
    note-versus-table disagreements.
  - Verdict: **ADOPT NOW** (already adopted); keep as the first candidate source, never as proof.

- **NARA Executive Orders Disposition Tables** ([page](https://www.archives.gov/federal-register/executive-orders/disposition)) — OFR's per-president tables of every executive order.
  - Coverage: January 8, 1937 to January 19, 2017, from FDR (EO 6071-9537) to Obama (EO 13489-13764). The page also lists Hoover EO 5075-6070, but the tables start with Roosevelt.
    Fields: EO number, signing date, Federal Register volume, page and issue date, title, amendments, current status. Download: "CSV/Excel or JSON" per the page. Orders from
    January 20, 2017 onward exist only on federalregister.gov.
  - Terms and access: public, free, no key. Maturity: official; last reviewed date not shown on the page I opened.
  - Completeness: the tables stop in 2017, so later amendments to old orders live only in the API notes; the tables are a snapshot. Check whether NARA refreshed any per-president table after the original
    publication (I did not).
  - Answers the question? Gives a status string and amender, not a cause or date of cessation.
  - Fit: baseline cross-check against the API notes; disagreements between the two are leads. Cost to adopt: a few hours; no model tokens.
  - Verdict: **ADOPT NOW** as a second, partly independent status chain (the repo already holds the 1989 table; check the 2017 tables for the 1990-2017 gap).

- **Codification of Presidential Proclamations and Executive Orders, April 13, 1945 – January 20, 1989** ([foreword](https://www.archives.gov/federal-register/codification/forward.html)) — an editorial book
  printing every general, continuing proclamation and EO as amended through January 20, 1989, in 50 subject chapters, plus disposition tables for all 1945-1989 documents.
  - Orders before April 13, 1945 appear only if later documents affected them. It says it is "not intended to be used as a definitive legal authority". The foreword does not explain how revoked orders are handled in the main text.
  - Access: free on archives.gov and govinfo; the repo already ingests it (`jobs/ofr-codification-1989`).
  - Answers the question? For 1989 snapshot only: "was it in force on January 20, 1989 and where was it codified". Its absence is weak evidence (it omits land, selective service, tariff material).
  - Verdict: **ADOPT NOW** (already adopted); limited to a 1989 anchor, as the repo already treats it.

- **govinfo API, bulk data and link service** ([developers page](https://www.govinfo.gov/developers); [API repo](https://github.com/usgpo/api); [link-service repo](https://github.com/usgpo/link-service);
  [bulk-data repo](https://github.com/usgpo/bulk-data)) — GPO's official publications as packages with metadata.
  - API: needs a free api.data.gov key; `/collections`, `/published` (by date issued), `/packages/{id}/summary`, `/related/{accessId}`, `offsetMark` paging past 10,000 records.
    The API repo README states 36,000 requests per hour, 1,200 per minute, 40 per second; a third-party blog says 1,000 per hour per key and DEMO_KEY 30 per hour. I cannot reconcile the two; test with a real key.
  - Related service: relationships exist only for BILLS, BILLSTATUS, PLAW, Federal Register documents and CHRG packages. There is no executive-order-to-order relationship service, so it will not return "revoked by".
  - Link service: collections CFR, CPD, FR, PLAW, STATUTE, USCODE and others; predictable links such as `/link/cpd/executiveorder/14104`, `/link/fr/76/575`, `/link/statute/118/3910`, `/link/uscode/50/797`,
    `/link/cfr/3/100?year=2018`. Useful for building stable, citation-keyed URLs, not for status.
  - Bulk XML (listing page): CFR annual edition 1996-present; eCFR current XML; Federal Register 2000-present; Statutes at Large 1789-present; Statutes Compilations 1862-present;
    Public Papers of the Presidents 2009-2016; Bills; US Government Manual. The Federal Register 1936-1999 is browsable on govinfo but the bulk listing starts in 2000. Terms: not stated on the pages; public domain.
  - Not found on pages opened: coverage years for the Compilation of Presidential Documents (CPD) and Public Papers on govinfo (LLSDC and the Drake guide give CPD from 1993 and Public Papers from 1929 on
    different pages; they disagree by a year on CPD 1992/1993); LSA collection details. A Title 3 CFR bulk path on govinfo was not confirmed (a guessed URL returned an error page).
  - Answers the question? No. It supplies texts and CFR snapshots.
  - Fit: the project already downloads from govinfo; the free key and offsetMark paging fix slow crawls by listing exactly which packages exist per day. Adoption: hours.
  - Verdict: **ADOPT NOW** for listing and fetching (already used); **SKIP** the related and link services for status.

- **List of CFR Sections Affected (LSA) and CFR Title 3** ([GWU guide](https://law.gwu.libguides.com/presdocs/tips); [LLSDC guide](https://llsdc.memberclicks.net/executive-orders-and-other-presidential-documents)) —
  the monthly LSA lists Title 3 presidential documents with amending documents and Federal Register citations; per the guide it is on govinfo from 1997 and in HeinOnline.
  - Title 3 annual editions: govinfo 1997 onward per LLSDC (bulk CFR folders start at 1996); HeinOnline CFR Library 1938 onward (annual Title 3 from 1967).
  - Fit: LSA is an OFR-made independent-in-process index of amendments and revocations of EOs from 1997, in dated monthly form, and costs no model tokens to parse. It overlaps the API notes
    (same office), so it detects errors and omissions in the notes but is not independent evidence.
  - Verdict: **TRY** (small pilot: parse LSA Title 3 for 1997-2016 and compare with the notes for 14 revocations picked at random).

- **eCFR API and govinfo CFR annual editions** ([vaquill guide](https://www.vaquill.ai/blog/ecfr-api-official-guide-cfr-as-json-xml-and-bulk-data); [point-in-time guide](https://www.vaquill.ai/blog/cfr-annual-editions-point-in-time-api);
  [eCFR docs](https://www.ecfr.gov/developers/documentation/api/v1)) — current and dated regulation text.
  - Endpoints: `versioner/v1/titles.json`, `full/{date}/title-{N}.xml` (compression required, plain returns 406), `structure`, `ancestry`, `versions/title-{N}.json` (fields `amendment_date`, `issue_date`, `substantive`, `removed`),
    `search/v1/results` (stops at 10,000 results). No key. Point-in-time history begins January 2017; earlier dates return 404. For earlier text use annual CFR editions (1996 onward on govinfo bulk).
  - Answers the question? Only for regulations that cite an EO as authority (an EO dropping out of an AUTHORITY line is a weak lead). The eCFR is "authoritative but unofficial".
  - Verdict: **WATCH** beyond what `jobs/current-law` already does.

- **U.S. Code (OLRC) downloads, notes, and Table IV Executive Orders** ([download page](https://uscode.house.gov/download/download.shtml); [Table IV PDF](https://uscodeweb1.house.gov/static/table4.pdf);
  [classification tables](https://uscode.house.gov/classification/tables.shtml)) — the Code in USLM XML and XHTML with notes, release points per Public Law, annual historical archives, and a table of EOs by number.
  - Table IV (opened PDF): columns date, EO number, U.S.C. title, U.S.C. section ("nt" = note), status ("Elim." = eliminated, blank = not marked). The PDF I could read covers 1907 through at least EO 12174 (Nov. 30, 1979);
    the PDF was cut off there, so I do not know its end date or as-of date. An archived copy of Table IV exists in the annual historical archives (2012 file named in search results; I could not open it).
    The classification tables page does not mention executive orders, so Table IV lives elsewhere on the site.
  - Download: all titles as zip in XML, XHTML or PCC text; prior release points and annual archives are linked. The page showed "current through Public Law 119-43" (December 1, 2025); the tables page showed laws to 119-100,
    so the cached download page lagged. The project's cutoff is October 14, 2026, so confirm the release point.
  - Terms and limits: none stated; public domain. Completeness: only EOs that are cited in Code notes; most orders never appear.
  - Answers the question? The note history in dated release points can show when an EO text was dropped or marked eliminated; "Elim." is a candidate event, not a cause.
  - Fit: use the annual archives to date the disappearance of notes (a time series), cheaply, with no tokens. Adoption: a day.
  - Verdict: **TRY**.

- **Library of Congress and congress.gov APIs** ([congress.gov API repo](https://github.com/LibraryOfCongress/api.congress.gov); [loc.gov API](https://www.loc.gov/apis/json-and-yaml/);
  [Statutes at Large collection](https://www.loc.gov/collections/united-states-statutes-at-large/about-this-collection/)) —
  congress.gov API: 5,000 requests per hour, key needed, JSON or XML; endpoints not enumerated on the page I opened, and I could not confirm any Statutes at Large or executive-order endpoint.
  loc.gov JSON API: no key, rate-limited, deep paging stops at 100,000 items. loc.gov's Statutes at Large page lists volumes 1-64 (1789-1951) and says the collection "is in process"; format and bulk terms not stated.
  - Answers the question? Only for statute-based endings: congress.gov public laws help identify a statute that repealed or superseded an order, but the project already has govinfo Statutes at Large (1789-present).
  - Verdict: **SKIP** for status; **WATCH** the loc.gov Statutes collection as a second copy for original-page scans.

- **CRS reports on issuance and revocation** ([R46738](https://www.everycrsreport.com/reports/R46738.html); [RS20846](https://www.everycrsreport.com/reports/RS20846.html)) —
  doctrine, not data. R46738 (read in full): orders "do not, by default, expire when the issuing President leaves office"; they end by presidential revocation or amendment, court invalidation, congressional repeal or nullification, or
  by codification. It lists no official register of in-force or revoked orders and does not mention disposition tables. RS20846 notes revocation by Congress including by sunset lapse or removal of authority.
  - Fit: supports the project's legal rulings (orders persist until ended; statutory authority loss can end them). Usable citations, free, EveryCRSReport mirrors the text.
  - I found no CRS report that lists revoked or expired orders; I did not run the searches that would exhaust that, so treat "no such list" as likely, not proven.
  - Verdict: **ADOPT NOW** as authorities in the article; **SKIP** as data.

## B. Free Law Project and case-law sources

- **CourtListener API, citation lookup, eyecite, reporters-db** ([API membership post, May 7, 2026](https://free.law/2026/05/07/api-included-in-memberships/);
  [citation lookup docs](https://wiki.free.law/c/courtlistener/help/api/rest/v4/citation-lookup); [eyecite](https://github.com/freelawproject/eyecite); [reporters-db](https://github.com/freelawproject/reporters-db)) —
  open case-law search and API.
  - Access: since May 7, 2026 any account can use the full API; the default rate was cut from 5,000 requests per hour (users with 1,000+ past requests keep their rate); students and academics can get a no-cost EDU membership with a
    higher tier; use is meant for personal, educational, research and exploratory purposes. Free Law also announced an MCP connector for Claude (planned the week after the post).
  - Citation lookup: POST up to 64,000 characters of text; 250 citations per request, 60 valid citations per minute; matches case-law citations only (no statutes, no executive orders). eyecite (BSD-2): README lists
    full case, short case, id., supra, statutory and law-journal citations but does not name U.S.C., Stat., Fed. Reg. or Exec. Order forms. reporters-db (BSD-2, version 3.2.32 per README) has a `LAWS` mapping of
    statutory abbreviations; the page does not say it covers Exec. Order. Bulk data pages were blocked, so I cannot confirm the bulk file list.
  - Answers the question? Only for court-ended orders (for example invalidated in a court). The way to use it is full-text search of opinions for "Executive Order NNNNN" plus words like "invalid" or "unlawful", then manual reading; no
    citator flag for EOs exists here.
  - Evidence from users: none I opened. Hype versus measured: unmeasured.
  - Fit: low yield; court invalidation is the rarest ending. Adoption: a day for a pilot on known invalidated orders (e.g., EO 10340 steel seizure, Youngstown, 1952).
  - Verdict: **TRY** (one small pilot, only for court-ended leads); **SKIP** eyecite and reporters-db unless you write an EO citation pattern (about an hour; the repo has its own citation-pattern logic already).

- **Caselaw Access Project (CAP)** ([transitions post, March 26, 2024](https://lil.law.harvard.edu/blog/2024/03/26/transitions-for-the-caselaw-access-project)) — Harvard's scan of about 6 million U.S. cases.
  - Search and API were wound down in 2024; bulk data and readable cases stay at case.law; access limits expired in March 2024; CourtListener includes all CAP cases. The page does not give the license or schema.
  - Fit: none that CourtListener does not cover. Verdict: **SKIP**.

## C. Commercial databases (all free to NYU Law students per the school's A-Z list, [NYU Law A-Z](https://nyulaw.libguides.com/az.php))

NYU Law lists HeinOnline, ProQuest Congressional, Westlaw, Lexis Plus and Bloomberg Law (Bloomberg needs a separate account activation). Remote access was not stated on the page I opened, but links go through proxies. Terms of use not read.

- **HeinOnline** ([EO tip](https://heinonline.com/blog/2022/06/tip-of-the-week-how-to-locate-an-executive-order/); [Federal Register Library](https://heinonline.com/content/federal-register-library);
  [Harvard guide](https://guides.library.harvard.edu/uspresident/execorders)) —
  - U.S. Presidential Library: Richardson's Messages and Papers, Public Papers (Hoover to G. W. Bush), CFR Title 3 (1936-2001), Weekly Compilation of Presidential Documents (1965-2005), and Clifford Lord's
    *Presidential Executive Orders* (1862-1938). Federal Register Library: Federal Register from 1936, updated daily; the CFR and List of Sections Affected; a citation lookup that retrieves any Federal Register page by citation;
    a "Sections Affected Locator". Hein's own EO page says orders stay in force until cancelled, revoked, adjudicated unlawful or expired but describes no status tool. The Harvard guide warns that "HeinOnline does not review the OCR scanned text for errors".
  - Answers the question? Provides page images and OCR of primary texts: the original-page custody problem for 1936-1993 Federal Register and CFR/LSA pre-1997 (not on govinfo). Not a status database.
  - Terms: assumed to bar bulk download; not verified. Fit: manual retrieval of specific pages that govinfo scans OCR badly, and 1938-1996 LSA/Title 3 lookups. Hours per batch of manual work; no automation.
  - Evidence from users: none opened except the OCR warning.
  - Verdict: **TRY** for human page retrieval on stuck orders; the owner should ask NYU librarians whether researcher-scale export is permitted.

- **ProQuest Congressional: Executive Orders and Presidential Proclamations** ([product page](https://about.proquest.com/en/products-services/Executive-Orders-and-Presidential-Proclamations);
  [help guide](https://proquest.libguides.com/congressionalhelp/eopp)) — over 100,000 executive actions, 1789 to 2017 per the product page (Harvard's guide says "present"); more than 50% pre-1936; about 25% are numbered EO and
  proclamation series, the rest hand-collected by editors (so unnumbered orders appear to be included, not confirmed). Subject indexing; search by accession or publication number; filters by administration and document type.
  - The pages do not mention amended or revoked cross-references or related links. Replica-of-original scans exist (the owner has already downloaded PDFs for pre-1937 orders; `jobs/pinakes-proquest-ingest`).
  - Terms: not read; manual download only.
  - Answers the question? No status data documented. It is a custody source for original pages of pre-1937 and unnumbered orders.
  - Verdict: **ADOPT NOW** as a manual source (already used); no automation.

- **Westlaw KeyCite and Lexis Shepard's for executive orders** ([GWU guide](https://law.gwu.libguides.com/presdocs/tips); [KeyCite page](https://legal.thomsonreuters.com/en/products/westlaw/keycite)) —
  - GWU's guide says to enter an EO citation and use KeyCite ("kc Exec. Order 11518": History, Negative Treatment, Citing References tabs) or Shepard's ("shep: Exec. Order 11518"). Thomson Reuters' KeyCite page lists coverage as cases, statutes,
    regulations, administrative decisions, patents and trademarks and does not mention executive orders; so whether KeyCite flags EOs consistently, and from what editorial source, is unverified here. I could not find anything on Lexis EO coverage
    beyond the "shep:" command, nor any API or text-mining terms for either.
  - Likely content (inference, not verified): amendments and revocations drawn from the same OFR chain plus annotated-code notes; "Citing References" overlap `jobs/shepard-citations`.
  - Answers the question? Possibly flags a revoked order and the revoking order, but not independent of OFR. No bulk route; treat as manual spot-check only, and an owner decision on whether that adds value.
  - Evidence from users: none found. Verdict: **TRY** one manual comparison of 20 orders (about 2 hours, free to NYU students) to measure whether either citator knows an end event that the OFR notes lack; **SKIP** automation.

- **Bloomberg Law** — I could not open its product pages (robots) or search for it. No evidence it adds status data for executive orders. **SKIP** unless a librarian says otherwise.

## D. Other free text and metadata sources

- **American Presidency Project (UCSB)** ([EO list](https://www.presidency.ucsb.edu/documents/app-categories/written-presidential-orders/presidential/executive-orders); [About](https://www.presidency.ucsb.edu/about)) —
  presidential documents from 1789. The listing shows date, EO number, title, president; no status or revocation fields. It reports the count "Displaying 1 - 10 of 10880", while a category menu says "Executive Orders (10879)" with a tooltip of
  5885; the numbers disagree. Sources include Richardson, Public Papers and the Federal Register; discrepancies are resolved in favor of Public Papers. No API or bulk download is mentioned; terms page not read; the repo already crawls it with robots.txt respect.
  Verdict: **WATCH** (already used as a mirror transcription, graded below the originals in the repo).

- **HathiTrust and HathiTrust Research Center (HTRC)** ([data overview](https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/); [HTRC data access](https://htrc.atlassian.net/wiki/spaces/COM/pages/43293057/HTRC+data+access)) —
  - Bibliographic API and tab-delimited HathiFiles (CC0). HTRC Data Capsule: about 6.5 million public-domain volumes for anyone with an account, about 17 million for member-institution affiliates; delivers uncorrected OCR as zipped text. Extracted Features:
    open to all, about 18.7 million volumes, JSON-LD bags of words, no OCR text. The HTRC Data API is not public. I could not open the HathiTrust terms of use, so I cannot state limits on page-level downloading.
  - Answers the question? No. Custody and OCR source for volumes such as the 1974 Hoover compilation and Statutes at Large volumes (the repo already uses HathiTrust).
  - Fit: bulk OCR text for public-domain volumes through Data Capsule could replace page-by-page downloads, if the project needs volumes the repo does not yet hold. Cost: an HTRC account and a day to learn the capsule workflow.
  - Verdict: **WATCH**; **TRY** only if a downloads-for-OCR bottleneck is confirmed on HathiTrust specifically.

- **Harvard Lamont microfilm, "Executive Orders, 1845-1936 (nos. 1-7403)", Film S 1130** ([Harvard guide](https://guides.library.harvard.edu/uspresident/execorders)) —
  the full-text source for EO 1-7403 that the repo's notes already ask the owner to reach. The Harvard guide also lists *Executive Orders* 1929-1936 (nos. 5076-7315, US Doc 1020.5) and the Hoover proclamations volume in print; the
  1974 Hoover volumes are already on Internet Archive and used. Access requires a person at Lamont; reading film is not machine-checkable until scanned.
  Verdict: **WATCH** (owner-only physical request; use only for orders ProQuest, Hathi and the Federal Register cannot supply).

- **Internet Archive Scholar (fatcat)** — a search index of open-access scholarly papers ([blog](https://blog.archive.org/2021/03/09/search-scholarly-materials-preserved-in-the-internet-archive/)). It could locate law-review
  articles that cite revocation chains but holds no executive order data. **SKIP** for data.

- **Wikidata** — I could not retrieve any Wikidata page (the one API call failed) and have no evidence on how many executive orders have items or properties. **WATCH, unverified**; an EO-number-to-item match job would cost little only if the item
  count is large, which I could not check.

## E. Academic datasets

All of these measure formal revocation or issuance, not cessation. Their value is as an external benchmark for revocation dates and counts.

- **Lowande and Poznansky, "Executive action that lasts"** ([article](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/AABF3ACB297FA8B252507582A9B4B68E/S0143814X23000442a.pdf/executive-action-that-lasts.pdf)) —
  Journal of Public Policy 44 (2024). About 6,500 EOs from 1937 to January 18, 2021; outcome is formal revocation; they report 74% never revoked, 11% baseline probability of revocation in the following term.
  Hand-coded "immutability" for 41% of orders. Replication data at Dataverse doi:10.7910/DVN/TZ2QKY (the Dataverse page blocked my fetch, so file contents and the revocation-date field are unverified). The article does not name the source of the order list or revocation facts,
  which suggests the OFR chain. It extends Thrower (2017) and reports a coding step in which 63% of orders were coded without a human reading them (89% agreement, kappa 0.76), which is a data point on how little human reading exists in this literature.
  Verdict: **TRY** (download and compare revocation flags to the project's: any mismatch is a lead).

- **Thrower, "To Revoke or Not Revoke?" AJPS 2017** ([summary](https://www.poliscidata.com/insights/1285)) — survival analysis of all revoked EOs, 1937-2013; replication at Dataverse doi:10.7910/DVN/LZGQOH (R and Stata files, two datasets). Revoked orders only; no lapse. **TRY** with the Lowande file (same comparison).

- **Chiou and Rothenberg latent-significance ratings** (as described in Lowande and Poznansky): 3,512 orders from 1947-2002; a significance score, not status. **SKIP** for status; possible stratification variable.

- **Policy Agendas Project EO dataset** ([page](https://www.maxwell.syr.edu/research/campbell-public-affairs-institute/united-states-policy-agendas-project/datasets-and-codebooks/executive-orders)) —
  CSV and PDF codebook (March 2025 version); fields: topic codes, party, divided government, term timing; no revocation field. Years and N not stated on the page. **SKIP** for status; possible topic labels.

- **Mayer, *With the Stroke of a Pen* (Princeton, 2001) and Fine and Warber** — I found the book and a related replication-data listing but did not open a dataset or confirm availability, fields or years. **WATCH, unverified**.

- **Data.gov / NARA CSVs** ([NARA dataset page](https://www.archives.gov/open/dataset-executiveorders.html); [Data.gov 1994-present](https://catalog.data.gov/dataset/executive-orders-from-1994-present)) —
  CSV exports of Federal Register EO metadata; the Data.gov file lists fields: citation, document number, pages, URLs, type, subtype, dates, title, disposition notes, EO number; last updated September 6, 2022 per the catalog, though the combined file is
  described as updated in real time. The NARA page covers Clinton, G. W. Bush and Obama files only (last reviewed February 3, 2020). Same data as the API; no new information. **SKIP** (use the API directly).

- **2024-2026 datasets on lapsed or revoked orders** — none found in the searches I ran before the budget ended. Trump's 2025 rescission orders (EO 14148 and EO 14236) are tracked by law firms and Wikipedia
  ([Lawfare explainer](https://www.lawfaremedia.org/article/understanding-executive-orders-14148-and-14236)); that is commentary on two orders, not a dataset. No sign of a competing project doing the project's task, but my search was incomplete.

---

## Considered and rejected

- CAP (superseded by CourtListener), eyecite and reporters-db for EO citations (case-law and statute patterns only; write a regex instead), Data.gov and NARA CSV copies (duplicates of the API), Internet Archive Scholar (papers, not orders),
  Chiou-Rothenberg and Policy Agendas data (no status), congress.gov API (no EO endpoint confirmed), Bloomberg Law (nothing shown).

## Ranked top 5 for "when and how did this order end"

1. **Federal Register API notes (ADOPT NOW, already in use).** The only machine-readable, current, per-order revocation and amendment chain from 1937 to the present, with later instrument and date in text. Next step is a periodic diff and a parser audit, not new acquisition.
2. **NARA 1937-2017 disposition tables plus the 1989 Codification (ADOPT NOW).** Independent-in-time snapshots of the same OFR chain; disagreements with the API notes are a cheap, token-free lead generator.
3. **GovInfo LSA monthly (1997 onward) and HeinOnline CFR/LSA (1938 onward) (TRY).** A dated month-by-month record of Title 3 amendments; pilot on the post-1997 span with a script, use Hein by hand for pre-1997 stuck cases.
4. **U.S. Code Table IV and annual historical archives (TRY).** Time series of EO notes entering and leaving the Code, with the "Elim." marker; no tokens, about a day.
5. **Lowande-Poznansky and Thrower Dataverse files (TRY).** Not new evidence but an external check on formal-revocation counts and dates for 1937-2020; mismatches show where the OFR chain, or the project's, is wrong.

Next in line, not in the top 5: a manual 20-order KeyCite and Shepard's comparison; one CourtListener pilot for court-ended orders; HTRC Data Capsule for bulk OCR of public-domain volumes.

## Items for the owner to decide or check (not verified in this research)

- Whether NYU Law's HeinOnline, ProQuest and Westlaw/Lexis contracts allow any programmatic or high-volume retrieval; ask the NYU Law librarians in writing before any automation.
- A real govinfo API key (free) to settle the rate-limit discrepancy and to confirm LSA, CPD and Public Papers collection coverage.
- The Dataverse files and the Wikidata item counts, which this sandbox's blocked hosts and exhausted search budget prevented me from opening.
