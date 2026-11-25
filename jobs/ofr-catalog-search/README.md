# OFR catalog search record (Panizzi)

Named for Anthony Panizzi, whose 91 cataloguing rules for the British Museum made a catalogue state what it did and
did not hold. This job records, for each order the readiness tracker blocks with
`NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE`, what the Office of the Federal Register (OFR) catalog holds for it.
It writes leads and search records only: no status, step, blocker, count or codebook entry changes.

## What the blocker means (jobs/readiness-tracker/tracker.py)

In `load_machine_search`, the "OFR catalog" is `jobs/later-events/output/CATALOG_INDEX.csv`: the federalregister.gov
API v1 executive-order catalog (6,941 records, EO 7532 of 8 Jan 1937 onward) fetched by `jobs/later-events`. The
`counterevidence` step counts from machine search only when the order's id is in that file. For an order with a status
but not in the file, the tracker sets the default code `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE`. It reads no other
file that could clear it.

## The 721 orders (READINESS_BY_ORDER.csv on main, 2026-11-25)

721 rows carry the code (the brief said 711; 721 is the count in the file): 719 provisional NO, 2 YES. None is in
CATALOG_INDEX.csv. 606 have plain numbers from EO 5 to EO 7510 (about 1862 to 1936); the rest carry suffix letters
("2559A", "6204B", "6205C"). All precede the catalog's first record. The National Archives disposition tables index
states coverage "from January 8, 1937", and lists Hoover's range without a table. The orders are outside the catalog's
scope; the job records that as evidence rather than assuming it.

## What the job does

1. Reads `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`; targets are rows whose `blockers` include the code.
2. Fetches the disposition index (`archives.gov/federal-register/executive-orders/disposition`), keeps its sha256 and
   quotes the sentence containing "January 8, 1937".
3. Fetches the API catalog the same way later-events does (`per_page=1000`, ordered by number, about 7 pages, 1 request
   a second), keeping each page's URL and sha256, and writes `output/STATE.json` after every page. It stops at
   `runner_limits.past_safe_stop()` (4.5 h).
4. For each target, matches `executive_order_number` exactly (case-insensitive, so "7677A" differs from "7677").

`output/SEARCH_RECORDS.csv`, one row per target, `outcome` is one of:
- `entry_found`: `entry_text` quotes number, date, title, citation and disposition notes; `url` and `page_sha256` locate it.
- `searched_complete_no_entry`: the whole catalog was read and the coverage statement was captured; `page_url` and
  `page_sha256` list every page read, and the lowest and highest catalogued number are shown. This is an
  out-of-scope result, not proof that no order was signed or that no later act touched it.
- `search_incomplete`: deadline, short catalog, or no coverage sentence; no conclusion.

`output/STATUS.json` holds outcome counts, catalog pages, the coverage quote and measured elapsed time.

## Run time: not measured

No fetch could be made from the workspace. The job needs 1 + about 7 requests, so it should take minutes, but that is
an estimate. The first run prints and records `elapsed_seconds` and the request count; quote those, not this.
Run: `gh workflow run run-jobs.yml --ref <branch> -f job=ofr-catalog-search -f only=true`.

## Not done: the tracker does not read these records

The tracker has no reader for `SEARCH_RECORDS.csv`, so running this job clears nothing by itself. A separate owner
decision is needed. A small change would load ids with `outcome == searched_complete_no_entry` into a set and accept
`i in srch["catalog"] or i in srch["absent_searched"]` at the counterevidence test. Two cautions: (a) the
tracker's `machine_search_record` text says the catalog was searched for "editorial disposition notes on EO n", which
is accurate for these orders only as "no catalog entry"; and (b) counting the step on an out-of-scope result would
mean the later-source search for 1862-1936 orders rests on text scans alone. The Hoover volumes in
`jobs/ofr-compilations` (Table 3 "affected documents") are the better later-event lead for those orders.

## Tests

`python3 -B -m unittest test_ofr_catalog_search` runs offline against invented fixtures (index page with the
coverage sentence, API pages with invented numbers). The real API response shape and the index wording are unverified
from here; `parse_api_page` and `parse_index` fail loudly, and the job marks the search incomplete, if they differ.
