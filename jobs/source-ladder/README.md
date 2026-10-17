# Source ladder (job 1)

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
| `EXHAUSTED_PROPOSED.jsonl` | For items where every route failed definitively (see above): one line per order, in the exact format of `research/readiness/EXHAUSTED.jsonl` (`instrument_id`, `step`, `searched`, `recorded_by: "source-ladder job"`, `recorded_on`, `note`). These are **proposals**. Nothing is written into `research/`; a person decides whether to copy a line there, ideally after a general web search, NARA, LoC and presidential libraries. |
| `RESULTS.csv` | One row per queue item. `result` is `found`, `exhausted_proposed`, `retry_later` (a passing failure; `why` says which), `no_route` (no route could be built for the citation) or `not_attempted_budget`. `carried_forward_from` is filled when the item was found by an earlier committed run and not downloaded again. |
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
