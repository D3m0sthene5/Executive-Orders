# NARA Record Group 11 executive orders: discovery findings (2026-11-05)

**Conclusions.** I could not verify that RG 11 executive orders are digitized, and I found no NAIDs for them. Every fetch of catalog.archives.gov (record pages, robots.txt, the Swagger docs) was refused by the fetch tool's robots handling, so no catalog description page was read. The "Executive Orders" series NAIDs, their number ranges, per-order file units, and the sample orders EO 1500, 3000 and 4500 are all unverified. What is verified: the Catalog API v2 needs a key (`x-api-key`), obtained by emailing Catalog_API@nara.gov, with a default 10,000 queries per month, and NARA says not to cache or store returned content. A separate route needs no key: the public S3 bucket `nara-national-archives-catalog` is listable without credentials and holds RG 11 descriptions as JSONL (one record per line), including digital-object URLs per NARA. I could not read the JSONL (the fetch tool returned it as binary), so whether it contains the executive-order series or object URLs for them is unconfirmed. Estimated coverage of the 5,943 target orders: unknown, plausibly 0 to most; I would put no confidence on any figure until one JSONL chunk is read. RG 11 finding aid says executive orders (1862-1991) exist in the textual records but says nothing about digitization.

## 1. Series, NAIDs, number ranges, per-order units

- RG 11 guide, section 11.6: "Executive orders, 1862-1991" in textual records; card indexes/lists 1862-1947; drafts 1929-42; no number ranges, no NAIDs, no digitization statement. https://www.archives.gov/research/guide-fed-records/groups/011.html (verified).
- Truman Library holds a small separate "Unpublished Executive Orders (RG 11)" set, 1945-1948, box 1 covering EO 9539-10002 (about 200 pages; outside the target range). https://trumanlibrary.gov/node/179681 (verified).
- A forum post says signed EOs are in RG 11 and copies can be requested at inquire@nara.gov. https://openhistoryhub.com/t/how-can-i-get-a-copy-of-an-executive-order/180 (verified, but anecdotal).
- Series NAIDs, date spans per series, file units per order, digital object counts, and NAIDs/object URLs for EO 1500, 3000, 4500: unverified (catalog.archives.gov pages not fetchable here). Web searches returned no catalog hit for an EO series.

## 2. Public image URLs, format, size

Unverified for EO images. NARA says the dataset contains URLs for over 148 million digital objects (https://www.archives.gov/developer/national-archives-catalog-dataset). Object storage is conventionally `s3.amazonaws.com/NARAprodstorage/...`, but I did not fetch any such URL, so public access without a key, JPEG vs PDF, and page size are unverified.

## 3. Catalog API v2

- Key required: "An assigned API key must be incorporated into each API request." Default key is read-only. https://www.archives.gov/research/catalog/help/api (verified).
- Obtaining a key: email Catalog_API@nara.gov (GitHub README and Swagger-site summary agree); the getting-started page says keys are "provided by our Catalog engineers" and describes no self-serve form. Read-write keys need a Catalog account. https://www.archives.gov/research/catalog/help/api-getting-started, https://www.github.com/usnationalarchives/Catalog-API (verified).
- Rate limits per key per month: default 10,000; higher 150,000 on request; NARA Partner 1,500,000; exceeding blocks the key until the 1st of next month. Keys unused 12 months are deactivated; publicly posted keys can be deactivated.
- Terms, quoted: "Please do not cache or store any content returned by the API." Also paraphrased: users may not scrape the Catalog or try to download all its data through the API; the page points to the AWS open-data dataset for bulk needs. Attribution line required for apps (not a binding condition for a research pipeline necessarily, but stated).
- Records are generally public domain, but check each record's "Use Restrictions" field.
- Base URL `https://catalog.archives.gov/api/v2/`; endpoint `records/search`; params shown: `q`, `availableOnline=true`, `typeOfMaterials`. Headers: `x-api-key`, `Content-Type: application/json`. Response JSON: `body.hits`, `aggregations`, `statusCode`. Pagination, ancestor/series filters and field names are in the Swagger docs, which I could not fetch: unverified.

Implication: the API's no-caching term conflicts with a pipeline that saves page images or metadata for the project. Ask NARA (Catalog_API@nara.gov) whether storing images of public-domain records for research is permitted before using it.

## 4. Bulk alternative without the API

- AWS Registry of Open Data: https://registry.opendata.aws/nara-national-archives-catalog/ (verified). Bucket `nara-national-archives-catalog`, ARN `arn:aws:s3:::nara-national-archives-catalog`, region us-east-2, no AWS account needed, `aws s3 ls --no-sign-request s3://nara-national-archives-catalog/`. License: US Government work. Update frequency: registry says biannual.
- NARA documentation: https://www.archives.gov/developer/national-archives-catalog-dataset (verified). Prefixes: `zip/`, `descriptions/record-groups/rg_<N>/` (no zero padding), `descriptions/collections/`, `authority-records/...`. Zips: `nac_export_descriptions_2026-09-14.zip` (202 GB), `nac_export_authorities_2026-09-14.zip` (46 MB). Total over 261 GB; includes URLs for over 148 million digital objects. Catalog data current as of 2026-03-01.
- Public listing verified by anonymous HTTPS: `https://nara-national-archives-catalog.s3.us-east-2.amazonaws.com/?prefix=descriptions/record-groups/&delimiter=/` returned about 560 record-group prefixes including `rg_11/`. Listing `?prefix=descriptions/record-groups/rg_11/` returned `.jsonl` chunks named `rg_11-{N}.jsonl` (N at least 1 to 333, string-sorted; about 140 KB to 1.9 MB each; last modified 2026-09-28). A second listing page was cut off by the fetch tool, so the exact chunk count is unverified.
- Direct GET of `.../rg_11/rg_11-1.jsonl` worked at HTTP level but the fetch tool saw it as binary, so field names (e.g. whether `digitalObjects` with object URLs appear, level of description, series NAID) are unverified. Whether it holds the executive-order series is unknown; the 333+ chunks span all RG 11 records.
- archives.gov/developer page lists the Catalog API (including "bulk metadata and media export"), the catalog bulk dataset, and Executive Orders CSV datasets (Clinton, Bush, Obama only, per https://www.archives.gov/open/dataset-executiveorders.html). Contact developer@nara.gov for AWS/key questions.

## 5. robots.txt

- catalog.archives.gov/robots.txt and `/api/v2/api-docs/`: fetch refused as robots_disallowed by the tool; contents unverified. That refusal suggests the site disallows automated fetchers, at least for that user agent.
- www.archives.gov/robots.txt (verified): applies to all agents, crawl delay 10 seconds; blocks Drupal system paths, `/admin/`, `/search/`, user pages. It does not block `/federal-register/` or `/research/` content pages. Says nothing about catalog or object storage (different hosts).
- Object storage (S3) has no robots.txt relevant to anonymous S3 listing; NARA invites it via the open-data registry.

## 6. Other NARA-hosted EO sets (brief)

- Disposition Tables, EOs from 1937-01-08 to 2017-01-19; Title 3 CFR; Codification 1945-1989. https://www.archives.gov/federal-register/executive-orders (verified). Tables, not texts.
- Numeric EO codification pages run from "Dated and 1-4999" to 12500-12667 (https://www.archives.gov/federal-register/codification/numeric-executive-orders.html, verified); disposition-style, no scans mentioned.
- Related, not NARA-hosted and not fetched: Historical Records Survey "Presidential executive orders, numbered 1-8030, 1862-1938" (list, 2 vols) at https://archive.org/details/PresidentialExecutiveOrdersV1 (appeared in search; unverified).

## 7. CIS / ProQuest scope

Not resolved. ProQuest pages say the collection (over 100,000 actions, 1789-2017; more than 50% before 1936; about 25% in the numbered series) was built document by document "in consultation with" NARA archivists and librarians; they name neither RG 11 nor the State Department. https://about.proquest.com/en/products-services/Executive-Orders-and-Presidential-Proclamations, https://proquest.libguides.com/congressionalhelp/eopp (verified). The scope note on filming source is unverified; the CIS Index (1986) introduction likely holds it.

## Machine route (for a GitHub Actions job)

Recommended order, untested end to end:

1. Key-free metadata probe (cheap, S3 requests are free-tier-like and unauthenticated):
   - List: `GET https://nara-national-archives-catalog.s3.us-east-2.amazonaws.com/?list-type=2&prefix=descriptions/record-groups/rg_11/&max-keys=1000` (paginate with `continuation-token` from `NextContinuationToken`).
   - Fetch each `rg_11-{N}.jsonl` (about 0.1 to 1.9 MB; 333+ files, roughly 200 MB). Parse as JSON lines (check gzip: `Accept-Encoding`, and `file` the first bytes), filter records whose title matches "Executive Order" or ancestor series is the executive-order series, and extract NAID and digital-object URLs. Use `aws s3 cp --no-sign-request` where available.
   - Cost: one GET per chunk; no per-request fee for the caller beyond bandwidth.
2. Verify the object URLs unauthenticated with `HEAD` on 3 samples (EO 1500, 3000, 4500) before any bulk fetch; check `Content-Type` and `Content-Length`.
3. Only if needed, the API: `GET https://catalog.archives.gov/api/v2/records/search?q=...&availableOnline=true` with headers `x-api-key: $NARA_API_KEY`, `Content-Type: application/json`; budget 10,000 queries per month; pagination parameters from Swagger (unverified). Observe the no-caching term (get NARA's written permission first).

Owner must supply: a `NARA_API_KEY` (email Catalog_API@nara.gov; state the research use and ask about storing public-domain images) if step 3 is used; a decision on the no-caching term; confirmation that the job's user agent is acceptable on catalog.archives.gov (robots.txt unread). Step 1 needs no secrets.

## Open items for the next worker with a different fetch tool

Read one JSONL chunk to confirm schema and whether it includes EO series; read catalog.archives.gov/robots.txt; fetch Swagger for pagination.
