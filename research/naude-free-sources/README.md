# Naudé: free, lawful, machine-accessible routes to the licensed-database material

Stream "Naudé" of the Encyclopédie campaign (after Gabriel Naudé, whose 1627 *Advis pour dresser une bibliothèque*
argued for a library open to every reader). Date of work: 2026-11-06. Every route below was opened, not assumed.
`SOURCE_MAP.csv` has one row per route with coverage checked, access, robots and terms findings, a smoke item with
SHA-256, quality notes and a verdict. Smoke downloads are kept outside git in `C:/Users/danie/eo-naude-work/`.
Nothing here is a legal finding; everything fetched is a lead until a job holds and hashes the bytes.

## Conclusions first

1. **Most of the licensed-database material has a free route.** The gaps are narrow: page-level HathiTrust text,
   OLC and GAO web pages (blocked to scripts), the Congressional Record section granules (need a free API key), and
   any editorial citator flags (none exist free).
2. **The Library of Congress hosts the Hein scans for free.** Its Federal Register (1936-1993), Code of Federal
   Regulations (1938-1995, chapter level, including the Title 3 executive-order tables), and U.S. Code (1934-1988
   editions and supplements, including the executive-order tables, among them the "repealed" and "eliminated"
   tables) collections are HeinOnline-origin. Each item says the collection exists by agreement with Hein, who "has not
   made its materials available for commercial purposes including bulk download", and that LOC may restrict
   downloading. That is a stated term, not a robots rule. Treat these as targeted-retrieval sources (hundreds of
   items, 5-second spacing, which is the robots Crawl-Delay), not bulk sweeps, and send the LOC request in
   `REQUESTS.md` (R1) before anything larger. Owner decision needed: the owner wants to avoid Hein entirely; this is
   Hein content under LOC's own free platform. See Questions.
3. **govinfo is the strongest keyless source** and covers more than assumed: Federal Register 1936 on, Statutes at
   Large volumes 1-138, Serial Set 1817-1998, bound Congressional Record 1873-1998 (digitized) and 1999-2018,
   U.S. Reports, Public Papers 1929-2020. Sitemaps enumerate every package with no API key.
4. **Two hosts block compliant automation:** `babel.hathitrust.org` (`Disallow: /cgi/` for generic agents) and
   `static.case.law` (`Disallow: /`). Also `justice.gov/olc` and `gao.gov` answer HTTP 403 to scripted requests; I did
   not try to get around them.
5. **A trap:** Internet Archive catalogue titles for CFR volumes can be wrong. Two Google-scan items catalogued as the
   1938 and 1939 CFR are the 1999 and 1972 editions.

## Verdict per need

| Need | Best free route | What stays unavailable |
|---|---|---|
| N1 FR pages 1936-1994 | govinfo FR issue PDFs, 1936-2026, all issues (206 issues in 1936, about 250 a year after). LOC FR 1936-1993 is an independent second copy (Hein terms). | Nothing for coverage. Text is OCR (noisy mastheads); page images are inside the PDFs. |
| N2 CFR before 1996 | LOC CFR (1938-1995, chapter-level PDFs, Title 3 tables 1940-1995 seen for most years); IA umich Title 3 1936-38 compilation and GPO microfiche volumes 1981-1991; HathiTrust inventory of the 1938 edition and 1939-1947 supplements (full view, text not reachable). | Whole-volume annual editions 1949-1980 as books; Hathi page text without a request. Not found: complete Title 3 compilations for 1943-1980 as whole volumes (only chapter items on LOC). |
| N3 LSA before 1997 | govinfo LSA 1997 on. LOC has LSA items for sample years 1971-1982; IA has a 1973-1985 LSA volume; the FR "Codification Guide" is inside FR issues. | Complete 1949-1996 LSA run not found. |
| N4 U.S. Code 1925-1993 | govinfo USCODE 1994-2024; LOC editions 1934-1988 with supplements and the executive-order tables (1940, 1946, 1952, 1958, 1964, 1970, 1976, 1982, 1988). | 1926 edition (one LOC item only); 1989-1993 supplements not verified. Table text layer is column-scrambled. |
| N5 Statutes at Large | govinfo STATUTE vols 1-138 (granule PDFs and volumes). | None. |
| N6 Serial Set, documents, hearings | govinfo SERIALSET 1817-1998 (233,921 packages, sitemap-enumerable). | Pre-1990 hearings: govinfo CHRG is sparse (1940: 0 packages; 1960: 3); try IA/Hathi. Committee reports before 1995 are in the Serial Set. |
| N7 Congressional Record, bound | govinfo CRECB: digitized 1873-1998 per the help page, plus 1999-2018 in sitemaps. Verified for 1873 and 1936 parts. | Section granule ids need the API (free key). Other-year naming not established. Not verified OCR quality. |
| N8 Citator | No free editorial citator exists. Build a derived one by scanning case text for executive-order citations (see jobs). | KeyCite/Shepard's editorial treatment flags (overruled, distinguished, etc.): not found. |
| N9 Case law | CourtListener bulk S3 (public-domain mark; citation graph plus opinions); CAP through the Hugging Face common-pile mirror (22.6 GiB, 6.9M cases); govinfo U.S. Reports volumes. | `static.case.law` direct (robots forbids); law.resource.org reporters (withdrawn 2015). Justia/FindLaw terms unverified. |
| N10 Agency materials | IA: Comptroller General decisions 1921-1984 (239 items), Attorney General opinions (39 items), Weekly Compilation 1965-1993 (1,516 issues); govinfo: WCPD 1993-2009, Public Papers 1929-2020, GAO reports 1989-2008, Serial Set (CSC annual reports). | OLC and GAO websites (403 to scripts); Public Land Orders as a series (not found; FR plus 3 CFR PLO tables only); NYU or NYPL bulk data (nothing found). Google Books: terms not verified, not used. |

Not found, said plainly: any free equivalent of editorial citators; NYU/NYPL bulk programs; Law Library of Congress
Guide to Law Online as a data source (it is a directory, not checked further).

## Ranked zero-token jobs worth building

All run on GitHub's runner or the owner's PC with standard-library Python. None is built here.

| Rank | Job (suggested name) | Fetches | Rough volume | Blockers served | Overlap with existing jobs |
|---|---|---|---|---|---|
| 1 | **USC executive-order tables job** (`loc-usc-eo-tables`) | LOC USC tables of executive orders, all editions and supplements 1934-1988 (Tables II/IV/VI "included", VIII/IX "repealed", X/XI "eliminated"), then re-OCR page images for column order | ~100 PDFs, ~15 MB, 5 s spacing = about 10 minutes | Codification and repeal events per edition; Table IV and the "repealed" tables bear directly on whether an order was still in force at a date | None found for `ll/uscode` or `united-states-code`. Hein-terms caution: targeted pull only; send R1 first |
| 2 | **LOC and IA Title 3 job** (`cfr-title3-sweep`) | 3 CFR Executive Orders and Proclamations items 1940-1995 from LOC (search `q=executive orders 3 C.F.R.`), plus IA umich Title 3 1936-38 and GPO-microfiche Title 3 compilations, each identified by first-page text and hash | ~70 items, 0.2-3 MB each (LOC), ~2-70 MB (IA) | Which orders were carried as in force in each CFR edition; supplies Title 3 Table 2 status listings | Partial: `hathi-gpo-orders/discover_routes.py` and `supplementary_routes.py` list the LOC CFR collection for 1938 only; no job reads Title 3 tables |
| 3 | **Case-text citator job** (`caselaw-eo-cites`) | Stream the 175 Hugging Face CAP shards (matrix of shards) and scan text for "Exec. Order No. N", "E.O. N", "Executive Order N", plus FR cites; output only case id, snippet, EO number | 22.6 GiB read, a few MB written | N8 and N9: later court decisions that cite, enjoin or construe an order; leads for status events | None (no job uses case.law, CAP or CourtListener). Add CourtListener 2018-2026 opinions as a second pass |
| 4 | **CRECB granule job** (`crecb-granules`) | For Congressional Record pages cited by order texts or tables, the House/Senate/Extensions granule PDF | hundreds of granules, ~1-10 MB each | N7 and congressional ratification or disapproval events | None (CRECB unused). Needs a registered api.data.gov key (owner) for granule ids |
| 5 | **Serial Set by sitemap** (`serialset-sitemap`) | Enumerate SERIALSET packages by sitemap, fetch only those that match targets (CSC annual reports, committee reports on named orders) | tens to hundreds of PDFs; use Range, volumes can be 230 MB | N6, N10 | Partial: `csc-annual-reports` (ids from the search API, which recorded HTTP 500), `early-orders-hunt` |
| 6 | **IA Weekly Compilation 1965-1993** (`wcpd-ia`) | issue djvu text | 1,516 issues x ~0.2 MB = ~300 MB cache | N10; order texts are already in FR | None; low priority |
| 7 | **Hathi inventory** (`hathi-fullview-inventory`) | Bib API records for CFR, USC, FR index, AG opinions: htid, volume label, rights code | a few hundred small JSON records | Rights proof and a ready list for a request or a human download | Overlaps `hathi-gpo-orders`; metadata only. Never touch babel /cgi/ |

Rank 1 and 2 first: they answer the lifecycle questions (codified, repealed, eliminated) from official tables rather
than from inference. Rank 3 is the largest net-new capability but heaviest in bytes read.

## Cautions for whoever builds these

- Identify every Internet Archive item by content, not catalogue title (see the CFR row in `SOURCE_MAP.csv`).
- govinfo whole-volume PDFs are 100-500 MB; use HTTP Range (supported) or granule ids. My own smoke fetches of the
  1998 Serial Set volume (231 MB) and, by mistake, 491 MB of the 1936 Congressional Record part were larger than
  needed.
- The govinfo search API accepted `DEMO_KEY` but exhausted its 10-request allowance within about ten calls; the
  collections endpoint filters by ingest date, not publication date, so historical volumes need package ids from the
  sitemaps.
- LOC: robots `Crawl-Delay: 5`; never use `/search/`; pace 5 s; stop on any 429.
- `tile.loc.gov/robots.txt` returns a 404 page, so only the `www.loc.gov` robots and the Hein notice apply.

## Questions for the owner

1. LOC's USC, CFR and FR collections are Hein-origin; are targeted, throttled pulls of a few hundred items acceptable,
   or must these wait for LOC's answer to R1?
2. A free api.data.gov key (email only) would lift the govinfo API limit and unlock Congressional Record granules. I
   did not create one (no account creation).
3. Should the HF mirror of CAP be accepted as a source for case text, given it is a third-party repackaging, or should
   Harvard be asked for direct access (R3)?

## Verification limits

Not verified: OCR accuracy on any source beyond the smoke pages; the OLC and GAO sites (403); Hathi page text (robots);
Google Books terms; Justia/FindLaw terms; Congressional Record package naming for years other than 1873, 1936 and
1999+; LOC Title 3 coverage for every year; LSA before 1971; whether eyecite recognises Federal Register or executive
order citations (the repo's `library-survey` job pilots eyecite).
