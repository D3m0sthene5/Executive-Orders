# Youngstown: court decisions that print an executive order's number

Named for *Youngstown Sheet & Tube Co. v. Sawyer*, 343 U.S. 579 (1952), where the Supreme Court held Truman's steel-seizure
order, EO 10340, unlawful. This job finds court opinions that print a register order's number and marks, by transparent
rules, whether the sentence holds words of enjoining or vacating, upholding, or construing the order. Zero model tokens.

**A hit is a lead, never a status.** `enjoined_vacated_invalidated` means the sentence around the citation contains a word
such as *enjoin*, *vacate* or *unlawful*, not that a court held the order invalid. Nothing here changes a status, census,
codebook or count. Certified: 0.

## Route: CourtListener's public bulk files, not its API (measured 2026-11-06)

- **API.** `GET /api/rest/v4/search/` answers `401 Authentication credentials were not provided` without a token. With one,
  the documented default limits are 5 requests a minute, 50 an hour and 125 a day (wiki.free.law, API Overview, Rate Limits),
  so one search per order (14,913 register orders) is out of reach, token or not. The job reads `COURTLISTENER_TOKEN` from the
  environment and, when it is set, uses it for one small optional step (below). The bulk scan needs no token.
- **Bulk.** S3 bucket `com-courtlistener-storage`, prefix `bulk-data/`, listable and readable with no account, regenerated
  quarterly (2026-09-30 is the newest), Public Domain Mark. Sizes on 2026-09-30: opinions 55.25 GB (bzip2, one stream),
  opinion-clusters 2.47 GB, dockets 5.14 GB, citations 0.13 GB, courts 81 kB. The opinions file is about 6 times larger
  decoded (about 330 GB of CSV), too big to download to a 14 GB runner, so the job **streams** it: bzip2 is a series of
  independent blocks that start with a 48-bit magic at any bit offset (`bz2seg.py`), so the file is cut at verified block
  starts into 256 MB segments, two worker processes decode them over HTTP range requests (resuming a broken stream from the
  last byte), and a finished segment is kept in the runner cache so a stopped run resumes.
- **Rows.** Quoted CSV with newlines inside fields and PostgreSQL `ESCAPE '\'` quoting (`\"`). A row is split on
  `\n"<id>","<timestamp>`, a pattern text cannot contain (`bulk.py`).
- **Pass 1** finds opinions whose text prints a register order after "Executive Order", "Exec. Order", "E.O." (lists, ranges,
  "No."/"Nos.", comma thousands), classifies each citation's sentence, and holds the opinion's raw text column in
  `$JOB_CACHE_DIR`. **Pass 2** reads cluster, docket, citation and court tables for the hit clusters only (date, case name,
  court, reporter citation). An opinion dated before the order it cites is dropped.

## Second sources checked

- **Official CourtListener MCP server.** Exists (Free Law Project, announced 2026-05-12, in Anthropic's connector directory;
  OAuth with a CourtListener account, tools for search, citation verification, alerts, and generic endpoint calls). It wraps the
  same API, so the same limits; bulk data is not part of it (Free Law Project's own post says so). It adds nothing for this
  job; it is useful in a session to read one opinion or confirm one citation by hand.
- **Harvard Caselaw Access Project (CAP): not used.** `https://static.case.law/robots.txt` is `User-agent: *` / `Disallow: /`
  (last modified 2024-03-04), so the fetch pool would refuse every request and this job makes none. The job makes no request to that host
  (`SUMMARY.json` -> `second_source` records this). Before
  the robots file was weighed, the author (a research session, not the job) made one-off requests to static.case.law from the
  owner's PC to look at coverage: `ReportersMetadata.json`, `VolumesMetadata.json` (30 MB, deleted), one case JSON and HTML,
  one volume zip, and two more case JSON files; nothing from it is in this job, its fixtures or its outputs, and the
  downloaded files are deleted. CAP's federal reporters run through about 2018, and CourtListener already holds that text:
  in the first 30 MB of its opinions file 7,494 of 7,701 rows carry the Harvard XML column (`xml_harvard`). Every hit records
  its `source` (`courtlistener_bulk`) and `text_origin` (the column; a Harvard-origin text shows as `xml_harvard` or
  `html_with_citations`). **Option, not used and awaiting an owner decision:** the CAP mirror on Hugging Face
  (`common-pile`, 22.6 GiB), third-party repackaging.
- **eyecite** (Free Law Project, also checked in a scratch venv): finds case, `U.S.C.` and `Fed. Reg.` citations (it read
  "17 Fed. Reg. 2955" beside EO 10340) but **not** "Executive Order No. N", so it cannot find order numbers. Not used. Kean
  F-20261017-4 (eyecite pilot, 54 citation leads, no accuracy scoring) is consistent with this.

## Outputs (`output/`)

`COURT_HITS.csv` (one row per order and cluster: eo, court, date, case name, cluster id, URL, citation span, rule class, cue,
sentence, source and text column), `FRAGMENTS.jsonl` (`kind: court_decision_candidates`, exact sentence quote and its span in
the opinion's derived text, `derive-1` rules, text hash; no `text_path`, the text is not committed), `SOURCES.jsonl` (one
record per held opinion: sha256 of its raw text column, bulk object key and ETag, `instrument_ids` led by
`COURT:cl-op-<id>`, `acceptable_as_original: false`), `ORDER_TALLY.csv` (every order's counts, committed or not),
`CONTROLS.json`, `SUMMARY.json`, `BUDGET.json` (stop above 20 MiB or any file over 5 MiB; the job fails over it),
`FAILURES.jsonl`.

The claim kit auto-discovers `FRAGMENTS*.jsonl` and `SOURCES.jsonl`. It reads only `later_event_candidates` fragments as events
and accepts actors named `PLO|PROC|STAT|PL|PUBRES|ACT|NOTICE|MEMORANDUM|PRES_DETERMINATION:`, so this job's fragments are read
as data and **not** attached to an order until someone adds `court_decision_candidates` to `EVENT_KINDS` and `CASE` to
`NON_EO_ACTOR` in `jobs/claim-kit/inputs.py`. That change is the coordinator's (not made here).

Because the budget is bytes, `COURT_HITS.csv` holds every federal-signal hit of the three holding classes first, then up to 3
mention-only hits per order (highest court first); `SUMMARY.json` -> `omitted` and `ORDER_TALLY.csv` count the rest. The full
hit list stays in the runner cache. A hit needs a federal signal near the number (President, Fed. Reg., C.F.R., U.S.C., ...);
numbers beside Governor or Mayor are marked state or local and left out of the commit.

## Rules (`scan.py`, versioned `youngstown-class-1`)

Class comes only from cues in the citation's own sentence; the cue nearest the citation wins, holding words before
interpretive ones. A cue in a party's request or contention ("moved for an injunction to enjoin", "argues") is demoted to
`mentioned` (flag `argument_frame`). "Did not enjoin" is a mention; "not valid" reads as invalidated. A strong cue in the
neighbouring sentence is shown in `adjacent_class`, never as the class. An opinion's class is its strongest citation class.

## Controls (`controls.py`, `fixtures/CONTROL_OPINIONS.json`; measured on 2026-11-06, deterministic)

Eight real opinions read in full, excerpts around every citation of the order (public-domain text fetched from Cornell LII,
law.resource.org and the circuits' own sites; the excerpt, source URL and hash of the fetched bytes are in the fixture):
Youngstown (EO 10340), Korematsu and *Ex parte Endo* (EO 9066, 9102), *Washington v. Trump* and *IRAP v. Trump* (EO 13769,
13780), *Chamber of Commerce v. Reich* (EO 12954), *Contractors Ass'n v. Secretary of Labor* (EO 11246), *Dames & Moore v.
Regan* (EO 12294). 62 citations were marked and labelled by hand.

| Control | Result |
| --- | --- |
| Locator: order number found at each hand-marked citation | 62 of 62 |
| Mention class vs hand labels | 51 of 62 correct, error rate 17.7% (enjoined: 2 of 2 found, 3 said; upheld: 1 of 2 found, 2 said; interpreted: 3 of 10 found, 4 said; mentioned: 45 of 48 found, 53 said) |
| Opinion class vs what the hand-read opinion holds | 3 of 8 agree (Youngstown, Endo, IRAP agree; Korematsu, Reich, Washington, Contractors, Dames & Moore are `mentioned` or `interpreted` because the sentences that print the number carry no holding word) |
| Negatives (invented numbers, statute and Federal Register digits, Proclamation or board "Order No.", a year after the lead) | 0 false hits in 8 |
| Citation shapes (12,954 beside a Fed. Reg. page; E.O. lists with C.F.R. cites; ranges) | 9 of 9 exact |
| Stream control: the planted text inside a synthetic bzip2 CSV, read through the real segment decoder, scanner and analysis | 21 of 21 found, 0 false rows, 0 rows lost at segment edges |
| Dated-before-the-order and Governor's-order cases | dropped or left out of the commit (tested in `test_courts.py`) |

The labels were written after the rules were drafted, and two weak cues ("defined", "covered by") were dropped after the first smoke run showed them firing on plain description, all on the same opinions, so the 17.7% is optimistic, not a held-out figure. The sentence rule's
weakness is plain: a court's holding about an order often sits in sentences that say "the Order" and not its number
(Reich, Korematsu). The class is a sort key for a reader, not a finding. A full run adds `bulk_stream_recall`: each planted
opinion must appear among the real hits (matched by case name and order id); with `complete: true` a miss means the bulk scan
missed it.

## Modes

`config.json` `mode`: `smoke` reads six 48 MB windows of the opinions file (about 1.7 GB decoded), then the full cluster and
docket scans for the hits' metadata, and limits the committed output to `focus_orders` (the controls' orders and a few
well-known litigated ones). `full` reads the whole file in 256 MB segments, stops opening new segments 80 minutes before the
time budget (`JOB_TIME_BUDGET_MIN`, default 320), and writes a partial but valid result (`complete: false`, resume on the next
run from the cache). Environment: `JOB_WORKERS` (default 2), `JOB_MODE`, `JOB_SEG_MB`, `JOB_TIME_BUDGET_MIN`.
The job fails when most segments fail, when more than half its HTTP requests fail, when a control fails, or over budget.

## The token

Not needed for the bulk scan. It is read from `COURTLISTENER_TOKEN` and, when set, spends up to `api_requests` (40) search
requests, 13 seconds apart, on phrase-search counts for the orders with the most bulk hits (`CONTROLS.json` ->
`api_crosscheck`), a rough bound beside the scan, not a recall test. This step is untested against the live API (no token
yet). To make the secret reach the job, add one line under `Run the jobs` -> `env:` in `.github/workflows/run-jobs.yml`, beside
`BRAVE_SEARCH_KEY`:

    COURTLISTENER_TOKEN: ${{ secrets.COURTLISTENER_TOKEN }}

and add the secret under Settings -> Secrets and variables -> Actions. The token is never printed or written.

## Register snapshot

`data/ORDER_DATES.csv`: 14,913 order ids with signing dates from `jobs/domesday-register/output/REGISTER.csv` (sha256 of that
file `42880e1f...3803d9` at origin/main `dcfdd579d1`); ids with a letter suffix are kept, ids like `EO:8-1` are not. Refresh by
re-exporting those two columns. It is a copy so this job reads no other job's output.

## Running and limits

On a push to this folder or by hand. `python -I test_courts.py` (offline, 15 tests) runs first. Limits: the rules read English
text with the lead words above (an order cited only by date, or by title, is missed); OCR text (see `extracted_by_ocr`) can
hide or garble a number; "Executive Order 119" style numbers below the 1937 renumbering match state and local orders too (the
federal-signal rule and the date rule cut most, not all); CourtListener holds about 10 million opinions, not all of US law.
