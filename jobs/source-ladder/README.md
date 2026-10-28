# Source ladder (job 1)

## Optional institutional-series identity leads

`record_series.py` reads pinned official NMB annual-report HTML/text and the
existing board index. It connects an exact EO heading/date and original-bound
entity terms to a bounded annual case narrative, then proposes the index's report
URL through the existing request contract. This can bridge an order date to a
later board-appointment date without widening `match_peb`'s date window or
changing ordinary acquisition defaults. It does not fetch, enqueue, approve a
fact, or infer receipt, exhaustion or legal effect. Source/identity review still
governs use of each proposed route.

```sh
python -B jobs/source-ladder/record_series.py --repo . \
  --manifest research/excavator/nmb-series-2026-10-25/SERIES_PLAN.v2.json \
  --out research/excavator/nmb-series-2026-10-25/new-replay
python -B -m unittest discover -s jobs/source-ladder -p test_record_series.py
```

Use a new output directory. The manifest pins raw/text source hashes and fiscal
years, the raw index, and each original identity span, EO reference date and
literal entity terms. Paths stay inside the repository; original headings must
bind the exact EO. At most four annual sources/twelve questions, five MB per
input, 1,400 characters for the EO-reference search and 20,000 characters per
case are considered. Missing/ambiguous matches and oversized cases remain
explicit; unrecognized headings are outside this narrow grammar. Annual report
dates, dates of board reports, appointment dates and EO dates are distinct.

The pilot adds two correct target routes to a native index-matcher replay and
retains one existing-route control. Three original report PDFs and scoped dated
transmittal-letter findings were independently AI-reviewed; they enter the
existing NORTON registry and native claim-kit later-event bridge, with no legal
promotion. See `research/excavator/nmb-series-2026-10-25/REPORT.md` for printed
source conflicts, acquisition failures, exact limits and costs. No net agent-hour
or campaign saving has been demonstrated. Normal jobs and the NORTON twelve-order
pilot limit are unchanged.

## Request and carry-forward repair (Astra, 2026-10-20)

Use the same request contract before appending and at execution. `request_contract.py`
provides `normalize_request(raw)` and `enqueue_requests(queue_path, requests)`; the latter
validates the entire batch before any append and skips exact duplicates:

```sh
python jobs/source-ladder/request_contract.py validate --input proposed-requests.jsonl
python jobs/source-ladder/request_contract.py enqueue --input proposed-requests.jsonl --queue research/readiness/FETCH_QUEUE.jsonl
```

Historical queue lines remain unchanged. `current_basis` means `ending_or_current_basis`;
`original_page_check` means an `original_text` source request with page review still required.
`original_and_ending_basis` produces distinct tasks. A precisely named second EO can be routed
as the acting instrument; an unidentified ending remains an unresolved task and does not
cause another download of the original. An exact “Original text of EO N” note can supply a
missing citation only for that same EO. Other missing or ambiguous mappings remain visible.
The seventeen rejected rows at `91116f8` become fifteen corrected requests and two partly
unresolved requests (EO8586 and EO9518 need their ending instruments identified).

`QUEUE_AUDIT.jsonl` preserves every original, its SHA-256, stable request/task IDs, corrections,
and unresolved tasks. `UNRESOLVED_REQUESTS.jsonl` exposes invalid and unresolved requests.
`as_of`, `required_date`, and `edition_year` survive embedded-citation splitting. Invalid
in-memory requests stop before network calls. Different tasks using the same URL reuse the
existing download cache; task counts and distinct source hashes remain separate.

Every retained receipt is revalidated, **including offline runs and requests outside the
bounded selection**. `SOURCE_REVALIDATION.jsonl` records the results. Known invalid receipts
and exact historical text move to `REJECTED_PRIOR_SOURCES.jsonl` and `rejected_texts/`; they
remain reproducible but do not appear in usable `SOURCES.jsonl` or `found` counts. Records
awaiting another attempt have `needs_revalidation` results. A replacement still identifies
the previous URL, hash, and rejection reason. This retention applies to explicit `JOB_ONLY`
and `JOB_LIMIT` selections as well as fingerprinted plans.

Checks now include metadata, wrong document identifiers, expected-file and extracted-text
hashes, changed request content, exact requested eCFR dates and explicit edition years.
Report records receive the same checks; a report word elsewhere in a multi-page extraction
does not establish that the named body's report was found. The local-association screen is
a retrieval heuristic and can leave a relevant document for review. It establishes no
delivery date or legal ending. A numbered annual edition likewise does not establish which
provision was in force on a specific day.

`source_evidence_tiers` separates `document_text`, `report_record`, and `custody_only`.
Metadata and finding aids are preserved as failed attempts or rejected prior receipts, not
document text. All tiers remain below authentication and substantive legal review.

Bounded default (PANIZZI, 2026-10-20): absent `JOB_ONLY`/`JOB_LIMIT`, build a **queue-first plan** and work
at most 50 items within 300 HTTP requests and 800 MB (`JOB_PLAN_LIMIT`, `JOB_MAX_REQUESTS`,
`JOB_MAX_DOWNLOAD_MB`). Requests from `FETCH_QUEUE.jsonl` come first, never-tried before tried-and-failed (so a
failing source cannot starve the rest), even when the readiness tracker shows their step closed; shared-source and
Opus re-fetch items follow only if they could complete a step. Requests with no route at all are recorded as
`no_route` ahead of the plan (they cost nothing, take no place in it, and a budget stop cannot skip them). `JOB_PLAN_FILE` accepts the excavator's
fingerprinted plan (0-50 requests, 1-300 HTTP requests); stale plans fail before network acquisition. Explicit
legacy selections also default to an 80-request ceiling. `JOB_READINESS_PLAN=0` disables ranking, not the finite
budget. This ranking is acquisition scheduling only.
Successful prior receipts and exact text bytes outside a bounded selection are
retained, including when selected items are refetched. Preserve the prior committed
output and failure records when diagnosing an unsuccessful job. Offline runs
cannot establish exhaustion. New source counts exclude retained receipts.

**Citations inside prose (`embedded_cites.py`).** A queue line whose citation is a sentence and which has no link
(`Pub. L. 94-412, ... 90 Stat. 1255 (Sept. 14, 1976); status of Proclamation 2914`) used to end as `no_route`
without a request. It is now split into one item per embedded Statutes at Large, Public Law, Federal Register,
U.S. Code, CFR or Reorganization Plan cite (wanted id `<original id> <71 Stat. 78>`, `SOURCES.jsonl` carries
`embedded_in_request`). Rules: a Public Law is dropped when the line gives a Stat. cite in a volume of that Congress (same enactment;
an unrelated Stat. cite does not drop it); a plan is dropped when the line gives a Stat. cite in its Congress's volumes; the Federal Register page where a named order was itself
printed is skipped (already held); title 3 CFR is skipped; at most 6 cites per line. A line that holds no cite
stays as one `no_route` item, so the failure is still recorded. A prose line that already has a link keeps it, and
gains the official route of an embedded Stat./Pub. L./U.S.C./CFR cite as a fallback only when that cite names the
same document as the link (a different cite in the line is a different document; a dated Code/CFR edition link gets
no current-edition fallback).
New official routes: `govinfo.gov/link/statute/<congress>/public/<n>` (any Congress; slip law
`link/plaw/...` from the 104th; checked back to 52 Stat., 75th Congress), and Reorganization Plans, which are read from the heading of the Title 5 Appendix on govinfo (index only: no Wayback copy of it is tried, and a
compilation is rejected as the source) and then fetched by their own Statutes at Large / Federal Register cite.
No eCFR API route: ecfr.gov/robots.txt disallows `/api/renderer/v1/content/`, `/api/versioner/v1/full/` and `/on/`,
and the ladder obeys robots.txt, so CFR text comes from the govinfo annual edition (`year=mostrecent`, labelled with
its edition). A govinfo PREMIS/MODS metadata file is hashed and logged but never accepted as the requested document.

**Report dates (`report_dates.py`, PANIZZI-2, 2026-10-20).** Many endings are written "N days after the report is
submitted" (emergency boards, commissions, task forces). A queue line that asks for the date a report was submitted
(report + a submission word + "date" or "actual", or an emergency board that was created/established; the
line's `note` counts too) is kept whole and gets a `report_date` spec (body name, order numbers and their OFR signing
dates, a due date or `week of A to B` window, the lane) and these routes instead of a citation route:
- **Emergency boards:** the National Mediation Board table (`nmb.gov/NMB_Application/index.php/peb/`) is read as an
  index; boards whose *created* date is within 3 days of an order's signing date (or, for an amending order, whose life
  contains the order date and whose carrier/union the request names) are ranked, and each report PDF (under 1 MB)
  is saved with its first 8 pages. Two boards created the same day are both fetched.
- **1993-01-25 to 2009-01-19, Weekly Compilation of Presidential Documents:** up to 20 Monday issues around the
  due date (`govinfo.gov/metadata/pkg/WCPD-YYYY-MM-DD/mods.xml`, about 100 KB each); a title that says "report" and
  names the body (words in order) is fetched; the issue's Digest is a fallback.
- **Before 1993-01-25, Public Papers of the Presidents:** `PPP_YYYY_sitemap.xml` lists the year's books; each is a single
  0.7-1.0 GB PDF read **by HTTP Range** (`Fetcher.open_range`, pypdf `strict=True`), never downloaded. The running heads
  ("Feb. 26 / Administration of ...") are bisected to the target date, then pages are scanned (backward from a due date;
  forward through a request window). pypdf loads a scanned page's image stream (~0.8 MB) whenever it resolves the page,
  so `RangeFile` returns zeros, without fetching, for a long read that follows an `/Image` dictionary (text identical in
  a side-by-side test; about 10x fewer bytes: 30 pages cost ~2.6 MB). Bounds per case: 40 MB and 600 Range requests; per run `JOB_MAX_RANGE_REQUESTS`
  (default 1500) and the 800 MB download ceiling. Range reads are counted apart from the 300 page requests and are
  spaced 0.25 s (they are blocks of one open file), or the host's robots crawl delay. The record kept is the
  assembled page text (hashed) plus the file's Content-Length, Last-Modified and ETag; the whole volume is not hashed.
- **Reports to an agency head, or with no named body, or after 2009-01-19** have no presidential-documents route and
  end `no_route` with the reason.
The job returns **custody, not a date**: the source record carries `report_date_request` (the spec),
`report_date_basis` (the board row or issue/title or pages used; NMB table dates are marked "index, not proof") and
`report_date_leads` (verbatim lines that carry a date, with page numbers, unlabelled). There is no `report_date` field;
whether a dated line is the transmittal letter, the date received, or only "recommendations" (EO 12335 got a
1983-01-15 "recommendations" record) is the claim producer's / reviewer's call. A found document is custody, not
authentication. Index steps that match nothing are passing failures (`rd_*`), never "exhausted".

**Five defects fixed (Craigellachie II, PANIZZI-2).**
1. *Wayback pages saved as gzip bytes* (EO 12335, 11065, lines 50-54): a body that starts with the gzip magic (or says
   `Content-Encoding: gzip`/`deflate`) is decoded, bounded, **before** it is hashed or read. `sha256`/`bytes` are the
   decoded document; `raw_sha256`/`raw_bytes` and `content_encoding_decoded` are kept in the source record, and both
   blobs stay in the cache. Old cache entries holding undecoded gzip are re-decoded offline on first use. A corrupt,
   truncated or oversize stream, or any non-PDF body more than 5% U+FFFD, is rejected (`undecodable_gzip`,
   `binary_or_undecodable_text`) and is a passing failure.
2. *Only pages 1-40 of a Public Law:* statutes (`STATUTE-`/`PLAW-` PDFs) are read in full up to 500 pages; `PDF pages
   a-b` in the request, a `#page=` fragment and the Stat. cite's page inside the granule choose pages for other PDFs;
   `page_or_item` lists every span and says `PARTIAL` when pages were left out. A request for "sec. N of Pub. L. ..."
   is rejected when the extraction is partial and the section is missing (`partial_extraction`) and notes "section N
   seen/NOT seen".
3. *Table of contents or editions list taken as the document:* extracted pages that are a table of contents with almost
   no operative text are rejected (`toc_only`); the uscode.house.gov editions menu is stripped from the text, and a page
   that is only the menu is rejected (`index_page`). A Wayback capture older than the legal cutoff is flagged in `notes`.
   A live official Code/CFR page is tried before a Wayback copy of the same page.
4. *A current edition for a question dated earlier* (5 CFR 6 for a 1953 question): `request_year` takes the latest year
   the request names (cite numbers excluded; "current" or `extra['as_of']` overrides). For USC/CFR requests dated before
   2026 the route is the govinfo edition of that year (`link/cfr/..?year=Y`, `link/uscode/..?year=Y`); the current
   edition, eCFR, uscode.house.gov and Cornell are not tried; a numbered edition later than Y+1, or a current page,
   is refused even if some other route returns it (`current_edition_for_dated_request`). Before the first govinfo
   edition (CFR 1996, Code 1994) there is no route: `no_route` with `historical_cfr_not_on_govinfo`.
5. *A listing of laws taken as the instrument* (`congress.gov/public-laws/119th-congress`, the Federal Register
   executive-orders list): rejected as `index_page`; never proposed as exhausted.
`index_page`, `toc_only`, `partial_extraction`, `current_edition_for_dated_request` and `rd_*` mean "this copy cannot
be used", not "the document is not there", so they never feed an exhausted proposal.

**Review fixes (Panizzi II, 2026-10-20).**
- *Earlier found records are re-checked.* Carry-forward used to keep every found record for ever, so the fixes above
  never reached the records that showed the defects (Pub. L. 98-525 pages 1-40, the gzip pages for EO 12335/11065, the
  2026 CFR for 1953, the congress.gov listing). `fetch_ladder.carried_defect` re-checks each carried record (listing or
  finding-aid URL, current edition for a dated question, undecodable text, editions list, table of contents, a statute
  PDF kept in part). A failing record is walked again; it is preserved outside usable `SOURCES.jsonl`,
  and a new record names the old one in `supersedes_defective_source` (URL, sha256, why). A failed re-walk names the
  old URL and hash in its RESULTS row. Offline runs also re-check. Historical Panizzi II audit: 31 of 251 records.
- *A request that ended `no_route` is not "tried".* It now ranks with untried requests once it has a route, so the new
  report-date lines enter the 50-item plan (29 of them on the current queue, instead of 6).
- *NARA Guide to Federal Records pages* (`archives.gov/research/guide-fed-records/`) describe a record group; they are
  `index_page`, not the record (EO 12095, 12159, 12182 had "found" the RG 13 guide page).
- *Same-day emergency boards:* a board report whose front matter names a different order (by number, or "Executive
  Order dated ...") is refused; equal NMB candidates are listed in `equal_candidates`.
- *Range budget:* a spent `JOB_MAX_RANGE_REQUESTS` fails only the Range route (`rd_range_budget_reached`, a passing
  failure); it no longer stops the whole run.
- Upper-case title-page dates ("FEBRUARY 9, 1979") are leads; a report PDF with no text layer ends
  `rd_no_meaningful_text` (PEBs 205/206, 1984, are scans without OCR).

**Named pages kept in part (Mabillon, 2026-10-20).** The EO 11490 line asks for `PDF pages 63-95` of
FR-1969-10-30.pdf (96 pages), but the record found on 2026-10-18, before pages named in a request were honoured, holds
pages 1-40, and carry-forward kept it. `carried_defect` now applies the `partial_extraction` re-check to **any** PDF
(not only statutes) when the request (its line, its parent line or its citation) names `PDF pages a-b` that lie in the
document and are not all among the kept spans. Pages beyond the document's last page never trigger it, so a bad request
cannot loop. No new cap or fetch: the walk reads the named pages through the existing `page_ranges` path, within the
existing 300-request / 800 MB budget (the issue PDF is 15.2 MB, sha256 `0e1eda31...95ea`), and the new record names the
old one in `supersedes_defective_source`. Against the committed output this flags 2 records: EO 11490 (pages 63-95) and
EO 11022/12107 (44 FR, pages 319-330 of 336). To force them in one run: `JOB_ONLY="queue:EO:11490:,queue:EO:11022:44 FR 1053"`.

**Defective records re-walked first (2026-10-20).** The 21:48Z run (commit 874f970f5) flagged EO 11490 but did not
re-walk it: the queue-first plan ranked it below other untried requests, and `JOB_ONLY` cannot be set from Actions.
The default plan now puts up to 10 (`plan.MAX_DEFECTIVE_FIRST`) records flagged by `carried_defect` ahead of
everything else, FETCH_QUEUE requests first, then by wanted_id; they stay within the same 50-item / 300-request /
800 MB limits, and the rest of the ranking is unchanged. A flagged record that is itself the result of a re-walk
(`supersedes_defective_source`) ranks normally instead, so it cannot hold a front place run after run. Against the
committed output at this change, 17 records are flagged (EO 11022/12107 no longer is); EO 11490 is first.

**What it does, in plain words.** Research agents used to spend a lot of time
hunting for a copy of a document by hand: try the link, try another form of
the link, try the Wayback Machine, try another official site, try a mirror.
This job does that hunt automatically and keeps a written record of every
try. It costs no model tokens when it runs.

It has two parts:

1. **`fetch_ladder.py`**, a reusable module. Give it a wanted document (the
   order ids it matters for, any known links, and a citation such as
   `66 Stat. 259`, `2 FR 63`, `31 U.S.C. 1552`, `5 CFR 352` or `EO 9337`).
   It walks the owner's "never give up" ladder, in this order:
   1. the known links, retrying with growing pauses when a site is busy;
   2. other spellings of the same official link (http to https, with or
      without `www.`, govinfo `/app/details/...` to the `/content/pkg/...` PDF,
      a federalregister.gov page to its API record and the PDF it lists);
   3. the Wayback Machine for those links (its CDX index first, then the
      capture's original bytes through an `id_` link);
   4. other official copies worked out from the citation: the govinfo link
      service and package links for the Federal Register, Statutes at Large,
      U.S. Code and CFR; uscode.house.gov; eCFR's view of the CFR on the
      legal cutoff date (`ecfr.gov/on/2026-10-14/...`);
   5. the Wayback Machine for those official links;
   6. reputable mirrors: Wikisource, Cornell LII, and American Presidency
      Project links already found by Stage 14.

   Pages that are really a CAPTCHA, a bot wall, a "page not found" or a
   govinfo error redirect are recorded as failures, never saved as documents.
   robots.txt is obeyed (including Cornell's 10-second crawl delay), every
   site gets at most about one request per second, and the user agent says
   who is asking. No login, paywall or CAPTCHA is ever bypassed. (The owner
   can add a public contact, such as a web address, to the user agent with the
   setting `EO_USER_AGENT_CONTACT`; Wikimedia asks for one. Nothing personal
   is added by default.)

   **When is something "exhausted"?** Every failed try is sorted into one of
   two kinds. *Definitive*: the server said the document is not there (HTTP
   404 or 410, a govinfo error page, a "page not found" page), robots.txt
   forbids it, or the file was the wrong document. *Passing*: no network, a
   timeout, a busy server (429, 5xx), a block or bot wall (401, 403, CAPTCHA,
   the federalregister.gov "unblock" page), or an offline run. An item is
   proposed as exhausted only when at least one route really got an answer
   and every route failed definitively. Anything else is marked
   `retry_later` and is NOT proposed, so a network outage or a run with
   `JOB_OFFLINE=1` can never mark steps exhausted.

   Other jobs use it like this:

   ```python
   sys.path.insert(0, str(REPO_ROOT / "jobs" / "source-ladder"))
   import fetch_ladder
   fetcher = fetch_ladder.Fetcher(cache_dir)
   result = fetch_ladder.Ladder(fetcher).walk(fetch_ladder.Wanted(
       wanted_id="EO:1234", instrument_ids=["EO:1234"], citation="2 FR 63"))
   # result["outcome"] is found | exhausted | retry_later | no_route;
   # result["source"] is a SOURCE RECORD, result["exhausted"] lists proposals (only for "exhausted")
   ```

   `fr_pages.py` finds one order's own pages inside a scanned Federal
   Register issue, and `eo_extract.py` uses it to check that a fetched file
   really holds the wanted order. Its safeguards: if the issue's printed page
   numbers do not include the cited page, the file is treated as the wrong
   issue and the ladder moves on (to the govinfo link service); the order's
   number is looked for on the cited page and the three after it (then the
   one before), never far away in the issue; "AMENDING EXECUTIVE ORDER NO. ..."
   and "pursuant to Executive Order ..." are references, not headings;
   "Docket No. 9337" is not order 9337, and "7700-A" is not order 7700; and
   every `medium` label says why. `prior_output.py` reads a job's last
   committed results (read-only git), so results are carried forward. `ofr_index.py` reads the frozen Office of
   the Federal Register order index kept in `jobs/fr-originals/data/`.

2. **`job.py`**, which works through a queue (below) and saves the results.

## The queue

The job reads, in this order:

1. **`research/readiness/FETCH_QUEUE.jsonl`**, if it exists. Anyone can add a
   line to ask for a source. One JSON object per line:

   ```json
   {"instrument_id": "EO:1234", "urls": ["https://..."], "citation": "66 Stat. 259", "step": "shared_sources", "requested_by": "Astra"}
   ```

   `urls` and `citation` are each optional, but give at least one. `step` is a
   readiness step (`original_text`, `shared_sources`, ...; default
   `original_text`). Bad lines are reported in the log and in SUMMARY.json.
3. **Opus originals to re-fetch** (added after the list below): every file on
   `jobs/opus-media-match/output/REFETCH_LIST.jsonl`, which Opus downloaded but
   its release left out (848 URLs, 774 distinct files, about 3 GB, on
   2026-10-17). URLs with the same expected sha256 are one item, fetched once.
   Each SOURCES record then carries `expected_sha256` and
   `matches_expected_sha256`, so a copy that is byte-identical to Opus's
   original is proven; the readiness tracker only counts matching copies.
2. **The Stage 20 shared sources not yet retrieved**: every authority in
   `research/stage20/output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv` whose
   `source_already_retrieved` is not `yes` and that
   `STATUTE_CASE_REVIEW_QUEUE.csv` does not already show as downloaded
   (90 items on 2026-10-17: 73 cited executive orders, 9 U.S. Code sections,
   6 CFR provisions, 3 Statutes at Large pages; spellings of the same citation
   are merged). Each item carries every order that cites it. Items cited by
   the most orders go first.

## What it writes (to OUTPUT_DIR)

| File | What is in it |
| --- | --- |
| `SOURCES.jsonl` | One SOURCE RECORD per document found: `source_id`, `instrument_ids`, `url` (where the bytes came from), `requested_url`, `sha256` of the exact bytes, `bytes`, `content_type`, `retrieved_utc`, `route` (which ladder step found it), `page_or_item`, `text_path`, `cache_path`, `notes`, plus `wanted_id` and `citation`. |
| `ATTEMPTS.jsonl` | Every request the ladder made: url, ladder step, time, HTTP status or error, bytes, sha256, why a response was rejected. |
| `PREVIOUS_ATTEMPTS.jsonl`, `PREVIOUS_UNRESOLVED.jsonl` | Deduplicated history retained across bounded runs. Earlier failures remain available to the scheduler even if outside the immediately preceding selection. |
| `QUEUE_AUDIT.jsonl`, `UNRESOLVED_REQUESTS.jsonl` | Original request objects and fingerprints, stable identities, corrections and errors; unresolved mappings remain visible. The queue's original bytes are not rewritten. |
| `SOURCE_REVALIDATION.jsonl` | The retrieval checks applied to every prior found receipt, including unselected and offline carries. |
| `REJECTED_PRIOR_SOURCES.jsonl`, `rejected_texts/` | Rejected original receipts and exact held text, excluded from the usable catalog. Rejection applies to the request, not necessarily to every possible use of the document. |
| `EXHAUSTED_PROPOSED.jsonl` | For items where every route failed definitively (see above): one line per order, in the exact format of `research/readiness/EXHAUSTED.jsonl` (`instrument_id`, `step`, `searched`, `recorded_by: "source-ladder job"`, `recorded_on`, `note`). These are **proposals**. Nothing is written into `research/`; a person decides whether to copy a line there, ideally after a general web search, NARA, LoC and presidential libraries. |
| `RESULTS.csv` | Selected and retained results. `result` is `found`, `exhausted_proposed`, `retry_later` (a passing failure; `why` says which), `no_route` (no route could be built for the citation), `invalid_request`, `needs_revalidation` or `not_attempted_budget`. `carried_forward_from` is filled for usable prior evidence retained without downloading it again. |
| `texts/` | Plain text pulled from each document found (for scanned Federal Register issues, only the cited order's pages). File names end in a short hash of the item id, so two items never share a file. All text files use plain `
` line endings on every computer. |
| `SUMMARY.json` | Counts. |

Downloaded files themselves stay in the cache folder (`JOB_CACHE_DIR`,
default `<OUTPUT_DIR>/../source-ladder-cache`), stored once by their sha256,
so a rerun reuses them and nothing large is committed. With the url, sha256
and retrieval time in SOURCES.jsonl anyone can fetch the file again and check
it is the same.

## How to run it

**On GitHub:** change any file in this folder (outside `output/`) and push, or
use Actions → Run jobs → type `source-ladder`. Results land in `output/`.
Items that the last committed `output/` already found are **carried forward**
(their source record and text are copied from it with read-only git) instead
of being downloaded again, so repeated GitHub runs only work on what is new
or still missing. `JOB_REFETCH=1` walks them again; `JOB_CARRY_FORWARD=0`
ignores the earlier output.
Note that federalregister.gov blocks GitHub's machines; govinfo, the Wayback
Machine and the mirrors work.

**On the PC** (from the repo folder):

```
python -m pip install --user -r jobs/source-ladder/requirements.txt
REPO_ROOT=. OUTPUT_DIR=C:/Users/danie/AppData/Local/Temp/eo-jobs/source-ladder/out python jobs/source-ladder/job.py
```

(In PowerShell set the variables first: `$env:REPO_ROOT="."; $env:OUTPUT_DIR="..."`.)
Useful settings: `JOB_LIMIT=10` (only the first 10 items), `JOB_ONLY=USC::,CFR::`
(only those items), `JOB_MAX_REQUESTS=200` (stop after 200 requests),
`JOB_CACHE_DIR=...`, `JOB_OFFLINE=1` (use only the cache; never proposes
"exhausted"), `JOB_PRIOR_OUTPUT_DIR=<folder>` (carry forward from a folder
instead of the last committed output).

The job runs its unit tests first (`python -m unittest discover -s jobs/source-ladder -p "test_*.py"`, no network) and stops if any fail.

## What it does NOT establish

- A found file is **source custody**: these exact bytes came from this URL at
  this time. It is not proof that the document is authentic, complete, or the
  version in force on a given date.
- U.S. Code and CFR copies are **current editions** (the notes say which
  year, and flag any edition dated after the 2026-10-14 cutoff). The text in
  force when an order was issued may have been different. Historical
  editions are not fetched automatically.
- eCFR currently answers this job's requests with its "unblock" page (a
  bot wall), so eCFR routes end as `retry_later`, never as found or exhausted;
  CFR items that govinfo also lacks (e.g. 26 CFR 458.324) stay `retry_later`.
- For scanned Federal Register issues, the order's pages are found by machine
  (printed page number plus the order's number in the scan's OCR text). The
  confidence is recorded; a person must check the pages.
- An "exhausted" proposal means the automatic routes failed, not that no copy
  exists.
- Nothing here changes a provisional status, the ledger, or any count.
