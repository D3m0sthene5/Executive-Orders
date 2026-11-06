# Duodecim: U.S. Code Table IV read across editions

Named for Table IV of the Twelve Tables. Table IV of the U.S. Code lists the executive orders that "implement general
and permanent law as contained in the United States Code", with the U.S.C. title and section where each is printed
(usually a note) and a status column that is blank or says `Elim.`. This job reads every edition of that table it can
hold, by routes robots.txt allows, and builds a time series: when an order's listing is first seen, where it sits in
each edition, when the section changes, when `Elim.` first appears, and when the order leaves the table. Zero model
tokens. It bears on one common blocker, an order's current legal basis (in an earlier 30-order proof, 3 orders were
blocked on an accepted current-law source).

## An `Elim.` marker is a lead about editorial classification, not proof that an order ceased

Read this before using any output.

* **The held pages do not define `Elim.` for Table IV.** Every held edition was read: the only legend any prints for
  Table IV is "Rep." (revoked or rescinded), and `Rep.` never appears in a row. `Elim.` is defined only for Table I
  ("Revised Titles"), a different table, as a section not restated in a revised title. `SUMMARY.json`
  `elim_legend_in_held_pages` lists the legend text found.
* **What was measured, not what it means.** In the current edition, of the 1,432 `Elim.` rows that point at a note,
  1,358 (94.8%) have no printed executive-order note in the Code held by `jobs/current-law`; of the 1,734 other note
  rows, 932 (53.8%) do (`SUMMARY.json` `elim_vs_printed_note_current_edition_note_rows`). That fits `Elim.` meaning
  the order's text is no longer printed in the Code's notes. It is a correlation in one edition, against a different
  release point, not a definition.
* **The codebook separates formal validity, operative force and editorial treatment.** `Elim.` is at most evidence
  about editorial treatment: how the Office of the Law Revision Counsel treats the order's place in the Code. It does
  not show that an order was revoked, expired, executed or superseded, and an order can leave the Code's notes while
  remaining in force (or the reverse). Nothing here emits an event, a status or an ending: `Elim.` rows are never
  written as `later_event_candidates`, `whole_order_end_candidates` or `current_predicate_candidates`. The claim kit
  decides.
* **First sighting is not entry.** The earliest held edition is dated 2009-01-05. An order first listed there may
  have been listed for decades; `first_listed_is_left_censored` says so (2,316 of 2,909 orders). Likewise
  `elim_present_at_first_listing`. An edition's date is the table's own "updated through" statement, not the capture
  date, and the table is an index that can lag the Code.
* **Table IV almost never drops an order.** Across 16 editions, 1 order left the table (13218, after 2015-01-05);
  orders leave the Code's notes by gaining `Elim.` instead (200 orders were first seen with `Elim.` after being listed
  without it; 2 later lost it again: 13690 and 13754).

## Where Table IV lives (verified by reading, 2026-11-06; `SOURCE_COVERAGE.json` records the probes)

| Source | What it holds | Used |
|---|---|---|
| `uscode.house.gov/tables/usctable4.html` | The current Table IV, "updated through the 2024 Main Edition (01/06/2025)". The OLRC site was in a "temporary format" (Code current through Pub. L. 119-138). | Yes: the newest edition |
| Internet Archive Wayback Machine, through its CDX listing of `uscode.house.gov/tables/usctable4.htm` (one capture per distinct digest) | Captures from 2010 to 2024; 14 distinct editions on 2026-11-06 (2009-01-05 to 2024-01-03). `id_` replay returns the original bytes. A repeat capture answers 302 to the capture holding the bytes; that redirect is followed. | Yes. It was offline ("Temporarily Offline") earlier on 2026-11-06, which is why the job must run when it is up. |
| University of North Texas End of Term web archive, collection `eot2012` | One capture (2012-11-07) of the table updated through 2012-01-03. Collections 2008, 2016, 2020 and 2024 hold none. UNT's robots.txt blocks only named AI crawlers; this job's agent string is its own. | Yes, as a second custody of the 2012-01-03 edition |
| OLRC annual historical archives (`/download/annualhistoricalarchives/XHTML/{year}/{year}uscTable4.htm`) | Existed for earlier years. | Probed for 2010-2024: all 404 on the temporary site. Not used |
| `webharvest.gov` (NARA/GPO end-of-term harvests, Archive-It replay) | Eight captures of the table (2010-12, 2012-12, 2014-12, 2016-09, 2018-09, 2020-08, 2022-09, 2024-09). | **Not fetched.** Its robots.txt disallows `/congress*/*/http://` and `/congress*/*/https://` (and a crawl delay of 10 s) for every agent. The rules use wildcards, which the standard library's robotparser (and so `jobs/_lib/fetch_pool.py`) ignores; this job checks them itself. The Wayback captures above hold copies of most of the same crawls. Reading webharvest would need an owner decision, for example a person fetching the pages. |
| Library of Congress scans of the U.S. Code, 1934-1988 (Table IV or VI for 1964-1988; lists of included, repealed and eliminated orders for 1940-1958) | Older editions, from HeinOnline scans. | **Pending owner decision.** Hein has not made the items available for commercial purposes, including bulk download. This job makes no request to loc.gov. A smoke test of at most 3 items, slowly, is allowed; the text layer has scrambled columns and would need column-aware parsing or OCR. |
| govinfo USCODE collection | Titles only. The sitemaps for 1994-2024 list `USCODE-{year}-title{n}` packages and nothing else; no Tables volume is published (the print Tables volume is a GPO sale item). The Federal Register's "Disposition Tables" of presidential documents are a different table. | Probed (sitemaps); not a source of Table IV |
| HathiTrust full view (print Tables volumes) | `robots.txt` disallows `/cgi/` (the page reader) for generic agents. | Not fetched |

Two captures that say the same "updated through" statement and hold identical rows are one edition (the repeat is
listed as a duplicate capture on the first's source record). Two editions whose statements differ only in the date
(2014-01-15 and 2014-01-16, both "2012 Main Edition, Supplement I") stay separate, as printed; they differ in 3 rows
(orders 12642, 12648 and 12926, moved to title 52).
`EDITIONS.csv` lists each edition.

## Outputs (`output/`, committed; raw page bytes stay in `$JOB_CACHE_DIR`)

| File | One row per | Notes |
|---|---|---|
| `TABLE_IV_ROWS.csv` (+ `_2`) | table row, per edition | `edition_id`, date parts, `eo_number` (`eo_number_carried` = the cell was blank and the previous row's number applies), `instrument_id` (census id or blank), `title`, `section` (as printed, e.g. `668dd nt`), `section_kind`, `status_text`, `elim`, `row_span`, `flags`. `row_span` is start-end byte offsets of the row's markup in the exact bytes whose sha256 is the edition's `SOURCES.jsonl` record. Files over 4.5 MiB shard as `_2`, `_3`. |
| `TIMESERIES.csv` | order number | First and last edition listed, `first_listed_is_left_censored`, `listed_in_current_edition`, `dropped_after_edition`, `edition_gaps`, `first_edition_with_elim_row`, `first_edition_all_rows_elim`, `elim_present_at_first_listing`, `elim_in_current_edition`, `elim_then_not_elim`, `location_changes` with JSON detail (removed and added locations between consecutive editions), `status_sequence` (`date:L` listed, `E` all rows Elim., `M` mixed, `-` absent). |
| `EDITIONS.csv` | edition | Label, date, source, capture URL, sha256, bytes, rows, distinct orders, Elim. rows, duplicate captures, `carried_forward`. |
| `CURRENT_NOTE_HOLDINGS.csv` | row of the current edition | Whether the note text itself is held (below). |
| `SOURCES.jsonl` | edition | URL, sha256 of the exact bytes, size, retrieval time, route, label, rows parsed. `instrument_ids` is empty on purpose (a table is not any one order's text); `cache_path` and `text_path` are null (raw bytes are not committed); `acceptable_as_original` is false. |
| `FRAGMENTS.jsonl` | order | Kind `current_predicate_candidates`, one entry per non-`Elim.` row of the current edition, in the format `jobs/current-law` writes (`legal_basis_candidate`, `basis_code`, `where`, `edition`, `snippet`, `checked_through` = the edition's date, `source` = url, sha256, page_or_item, plus `row_span` and `note_text_held`). |
| `FRAGMENTS_HISTORY.jsonl` (+ `_2`) | order | Kind `table_iv_history_candidates`: first listed, each location change, first `Elim.`, last listed, each with edition, row text, exact `row_span` and `source_id` (the fragment's `sources` list carries url, sha256). Deliberately not an event kind: it cannot become a later event, an ending or a status. |
| `CONTROLS.json` | control | Planted positives and negatives and parser self-checks, with the measured error rate. |
| `SOURCE_COVERAGE.json` | source | Every probe above, with status. |
| `SUMMARY.json`, `BUDGET.json`, `FETCH_LOG.jsonl` | | Counts; byte totals (stop above 20 MiB committed or any file over 5 MiB); every request. |

### Is the note text itself held? (`CURRENT_NOTE_HOLDINGS.csv`, current edition only)

Table IV points to a note; the note's words are in the Code. `jobs/current-law` already extracts the printed
executive-order notes from the OLRC USLM XML (`USC_EO_NOTES.jsonl`, release point 119-121, current through Pub. L.
119-121 of 2026-10-09), so this job reads that output and does not fetch or duplicate it (`after.txt` orders it after
`current-law`). For each current row `note_text_held` is `yes_exact_citation` (a printed note for this order at the same
title and section), `yes_other_citation` (the order has a printed note elsewhere), `no_printed_note_in_current_law`, or
`not_a_note_row_*` (the row points at section text, not a note). A `yes` row gives the note id, the sha256 of the note
text, the title file (`member`) and its sha256, and the URL and sha256 of the release-point ZIP, so a claim can cite
it. `edition_gap` states that the table is updated through 2025-01-06 while the notes are from release point 119-121:
a newer Public Law can move or remove a note after the table was last updated. `no` means "not in `jobs/current-law`'s
output", not that the Code prints nothing.

## Controls (`CONTROLS.json`)

Positives were read by hand from the raw HTML (not from the parser) on 2026-11-06, from the current OLRC page and the
UNT capture of the 2012-01-03 edition only: order 703 at 16 U.S.C. 668dd note in both; 5200 with `Elim.` in both; 1216
at 16 U.S.C. 431 note in 2012 and at 54 U.S.C. 320301 note now (a section change); 6237A (a letter suffix) without
`Elim.` in 2012 and with it now (an `Elim.` transition); 14132 as the last row of the current edition (a continuation
row). Negatives are numbers absent from the pages read (704, 1217, 5201 in both), 14999 and 99999 in every edition,
and 14132 in the 2012 edition. Parser self-checks compare the parser with independent counts from the bytes (row tags,
`Elim.` cells, malformed rows) for every edition. `error_rate` = failures / evaluated; any failure fails the job. A
control for an edition not held in a run is reported `not_evaluated`. Editions between 2012 and now are checked by the
parser self-checks and the negatives only.

## Running

On GitHub, a push to this folder runs it. A `SMOKE` file in the folder (or `JOB_SMOKE=1`) reads three captures (the
live page, the middle and the last of the list) and skips the coverage probes; delete the file for the full run. A full
run makes about 190 requests, paced (1 s on uscode.house.gov, 5 s on the Wayback Machine, 6 s on UNT, 0.5 s on
govinfo), robots.txt obeyed with wildcards, and takes about 6 to 25 minutes (cached pages are not fetched again).
Tests (`test_duodecim.py`, offline, fake network, 18 tests) run first and the job does not run if they fail.

**Resume.** Raw pages are cached in `$JOB_CACHE_DIR`. If a capture cannot be fetched now, the previous run's rows for
it are carried forward and flagged (`carried_forward`), never silently dropped; with nothing to carry, an archive
capture is recorded as a failure and the current page's absence fails the job.

**Failure.** The job exits with an error when most requests fail (a missing collection or archive page, HTTP 404, is
an answer, not a failure; archive captures are `optional`, so one unreadable capture is recorded but cannot fail a
run), when fewer than 2 editions parse (1 in smoke), when the current page is not held, when any control fails, or when
the byte budget would be exceeded (`BUDGET.json` then says `stopped`). The Wayback Machine being offline leaves the run
with the current page and the UNT capture only: 2 editions, which the minimum allows. The coordinator should read
`SUMMARY.json` `routes` to see whether it was up.

## What it does not establish

* No legal conclusion, event, status or count. Nothing changes a provisional status, a ledger or the 0 certified
  whole-lifecycle count.
* A listing in Table IV is an editorial index entry. It is not the order's text, not its authority, and not a
  finding that it is in force.
* Sixteen dated editions, 2009-2025, are all that could be held; earlier editions (the Library of Congress scans,
  HathiTrust, webharvest.gov) are not read, so "first listed" is left-censored.
* Some rows have a blank section or title in some editions (`flags`); they are kept as printed.
