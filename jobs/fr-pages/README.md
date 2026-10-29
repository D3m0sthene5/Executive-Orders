# fr-pages: hold the exact Federal Register pages that print wanted instruments

The land probe of 2026-10-28 found that most blocked land orders were ended by a Public Land Order (PLO) or a later
order printed in the Federal Register, and that the project held none of those pages. This job fetches the official
Federal Register PDF for each wanted page, records the issue's sha256, keeps the text of the instrument's own pages,
and commits a small PDF of just those pages, so a claim can quote the page as a held source. It costs no model
tokens.

A located page is a location lead with a confidence label, not an authenticated transcription. Nothing here changes
a status, count or the codebook.

## Input

`data/WANTED.jsonl`, one JSON object per line (lines starting with `#` are comments):

```
{"want_id": "land-probe-2026-10-28:PLO:936", "plo": 936, "fr": "19 FR 769", "targets": ["EO:7185", "EO:7212", "EO:7452"], "why": "...", "from": "..."}
```

`fr` may be left out when `plo` is given; the citation is then read from `jobs/shepard-citations/output/PLO_TABLE.csv`
(BLM's PLO tables). When both are given and the BLM table cites another page, the record is flagged. A line with
`fr` and no `plo` fetches that page (optional `printed_id` names what it prints). Several wanted lines on the same
page become one fetch. The seed list holds the 30 PLOs the two land-probe reports and the decided packet's
`decisions.csv` name as missing evidence. With `"auto_from_shepard": {"enabled": true}` in `settings.json`, the job
also adds up to `max_items` PLOs that Shepard names as revoking or ending census orders, those ending the most
orders first.

## Route for each page

1. **The previous run's copy.** If the prior output (`JOB_PRIOR_OUTPUT_DIR`) holds this page's text and its committed
   page extract still has the recorded sha256, both are carried forward with no request (`FR_PAGES_REFRESH=1`
   disables this). A record from the first runs, which committed the whole issue, is converted with no request: the
   committed issue bytes are re-hashed against the record and the extract is made from them.
2. **govinfo's link service**, `https://www.govinfo.gov/link/fr/<volume>/<page>`, read without following the
   redirect. The redirect names the daily-issue PDF for 1936-1993 (`/content/pkg/FR-1954-02-10/pdf/FR-1954-02-10.pdf`)
   or the single document's PDF for 1994 on, and sometimes a `#page=` hint.
3. **Optional, off by default (`try_issue_slice`):** a one-page slice from
   `https://archives.federalregister.gov/issue_slice/<y>/<m>/<d>/<page>-<page>.pdf`, kept only when two downloads
   give the same sha256. Slices of arbitrary page ranges could not be verified (see
   `jobs/shepard-citations/BUILD_NOTES.md`), and a slice generated on request may not re-hash; three failures in a run
   stop the route.
4. **The PDF the link service named**, downloaded whole through `jobs/_lib/fetch_pool.py` (robots.txt, one request
   at a time per host, `min_interval_seconds` apart, size bound `max_issue_bytes`, sha256 cache under
   `JOB_CACHE_DIR`).

Inside the PDF the job reads the printed page numbers from the running heads (`jobs/source-ladder/fr_pages.py`),
goes to the cited page, looks for the instrument's heading ("Public Land Order 936" or "EXECUTIVE ORDER 8861") on
that page, the next one, the one before or the one after that, and ends at the filing line "[F. R. Doc. ...]".
Only those pages' text is written. `location_confidence` is `high` when the printed page matched and both the
heading and the filing line were found, `medium` when one check is weaker (the notes say which), `low` when the page
was estimated. `needs_page_check` is true unless `high`.

**What is committed.** The whole issue PDF is never committed. For the located pages the job writes a new PDF
holding just those pages (`extract_pdf`: pypdf copies the pages in order and sets only `/Producer` to
`pypdf <version>`; pypdf writes no random file id or timestamp, so the same issue bytes and the same pypdf version
give the same extract). It is committed as `captures/<sha256 of the extract>.pdf` when it is at most
`commit_max_bytes` (4 MB) and the run has committed at most `commit_total_bytes` (100 MB); otherwise the record is
record-only. The record keeps the issue's url, sha256 and size and the PDF page numbers taken, so anyone can
re-download the issue, check its sha256 and re-derive the extract. `requirements.txt` pins the pypdf version. When a
refresh (`FR_PAGES_REFRESH=1`) downloads an issue whose sha256 equals the previous record's `issue_sha256` and the
same pages are located, the previous extract's bytes are kept, so its sha256 does not change if pypdf has changed.

`jobs/claim-checker/sources.py` (`load_job_sources`) counts the extract as held: it indexes the record by its
`sha256`, finds `cache_path` under `jobs/fr-pages/output/`, marks the copy `job_cache`, and the checker re-hashes
the file (`held_bytes_verified`). The issue's sha256 is not indexed as held, because its bytes are not committed. The
test `ClaimCheckerHeld` checks this against the checker's own code.

## Outputs (`output/`)

| File | Contents |
|---|---|
| `texts/FR_<vol>_<page>.txt` | Header (wanted ids, printed instrument, target orders, source URL, sha256, PDF pages) and the text layer of the instrument's pages with "=== PDF page N of M ===" markers. |
| `captures/<sha256>.pdf` | The page extract: a PDF of only the instrument's pages of the official issue. |
| `SOURCES.jsonl` | Shared source-record format: `url` (the issue URL with `#page=N`), `sha256`, `bytes` and `cache_path` of the committed extract, `text_path`, `text_sha256`, `page_or_item` ("19 FR 769; FR-1954-02-10.pdf PDF pages 9-9 of 40 (committed as a page extract)"), `instrument_ids`; the issue: `issue_url`, `issue_sha256`, `issue_bytes`, `issue_pdf_pages` (first and last PDF page taken), `issue_page_count`, `issue_printed_pages`; `extract_tool` and `derivation` ("PDF pages 9-9 extracted with pypdf 6.20.1 from the issue PDF whose sha256 is issue_sha256; re-download the issue to re-derive"); plus `printed_instrument_id`, `wanted_ids`, `fr_volume`, `fr_page`, `location_confidence`, `location_notes`, `needs_page_check`, `route`, `requested_url`. |
| `FAILURES.jsonl` | Wanted lines that could not be resolved or fetched, with the reason and every attempt. |
| `SUMMARY.json` | Counts, requests and bytes used, settings. |

`instrument_ids` lists the printed instrument first (`PLO:936`, or `FR-PAGE:<vol>-<page>` when unknown) and then
the target orders the page is wanted for. The printed instrument is listed so that a page wanted for a single order
never reads as that order's own text: `jobs/claim-kit/inputs.py` attributes a text to an order only when a source
record names exactly one order. The claim checker still matches the page to each target order.

## Running

On GitHub: change anything in this folder (for example add lines to `data/WANTED.jsonl`), or Actions -> Run jobs
-> `fr-pages`. It runs after `shepard-citations` when both run. The unit tests run first. Budget: `max_requests`
(120; `JOB_MAX_REQUESTS` overrides) and `max_download_bytes` (4 GB) per run.

Locally, from the repo root:

```
python -m pip install --user pypdf==6.20.1
REPO_ROOT=. OUTPUT_DIR=/tmp/fr-pages/out JOB_CACHE_DIR=/tmp/fr-pages/cache python jobs/fr-pages/job.py
```

Tests alone: `python -I -m unittest -v test_frpages` in this folder (injected HTTP responses and page texts; no
network, no PDF library).
