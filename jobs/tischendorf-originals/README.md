# Tischendorf: official printings for orders held only as transcriptions

Named for Constantin von Tischendorf (1815–1874), who spent his life tracking down the oldest surviving
manuscripts behind texts everyone else knew only from later copies, and who found the Codex Sinaiticus at
St Catherine's Monastery in 1844. This job does the same for executive orders the project holds only as a
transcription (American Presidency Project, Wikisource, Richardson, a Civil Service report reprint): it looks
for the official printing and proves, page by page, that it carries the same order.

## How it differs from Lewis

Lewis (`jobs/lewis-originals`) routes each order to the place its original should be and searches the open web
for pages that name it; it downloads no originals and confirms a page by the order's number. Tischendorf reads
the candidate pages themselves and compares their wording with the transcription already held. That comparison
is what lets a machine say "this page holds this order" with a measured error rate instead of handing every find
to a person.

## The text fingerprint (`fingerprint.py`)

Each held transcription is cut into overlapping three-word sequences. Each sequence is weighted by how rare it
is across all 12,000-odd transcriptions the project holds: boilerplate ("by virtue of the authority vested in
me") and web-page furniture appear in thousands and weigh nothing; place names, persons, acreages and operative
wording appear in one or two and carry the score. A candidate page's score is the weighted share of the order's
rare sequences found on it. OCR damage lowers the score gradually.

Calibration on 600 orders held both as an APP transcription and as a counted Federal Register original: the true
pair scores a median of 0.87 (5th percentile 0.55); an unrelated pair never scored above 0.06.

## Routes, cheapest first

| Route | Orders (2026-11-05) | What it does |
|---|---:|---|
| `corroborate` | 285 | An official find is already on file but flagged for a page check (fr-originals, ofr-compilations, isthmian-canal-1911, indian-reservations-1912). Offline: the found pages' text is compared with the transcription. |
| `fr_by_date` | 239 | Signed on or after 14 March 1936 with no official find (mostly 1936 orders before the OFR index begins, and index entries with no citation). Reads the govinfo scans of the daily Federal Register issues for the three weeks after signing, finds the order's own heading or closing number tag with source-ladder's `fr_pages` locator, and scores its text. |
| `ia_fulltext` | 3,143 | Everything earlier. The transcription's three rarest six-word runs are searched in the Internet Archive's full-text index; each matching volume's publisher and lending status are checked, its OCR is read page by page, and the best one- or two-page window is scored for the order's text, its number and its signing date. |

Within a route, orders that already have a provisional status go first. State carries forward in
`output/STATE.json`: an issue, a search phrase or a volume already examined for an order is not examined again.

## When a find is strong

`needs_page_check` is false only when all of these hold:

- the order's own number appears on the pages as a heading or closing tag (an OCR-damaged or mid-line heading
  only with a text score of 0.6 or more; in a compilation that prints no numbers, such as the 1912 Indian
  reservations volume, the signing date instead);
- the text score is at least 0.5 and the transcription has at least 8 rare sequences;
- the source is government-printed: the Federal Register, an official find already on file, or an Internet
  Archive volume whose title names executive orders and whose publisher is the Government Printing Office or a
  federal department;
- the run's planted controls passed.

Anything weaker with a score of 0.3 or more and a number or date on the page is written as a lead
(`needs_page_check: true`). A report or department publication that reprints an order (for example a Civil
Service Commission annual report) is never strong: the project treats such reprints as leads, not originals.

## Planted controls (every run)

Sixty orders whose official find already counts are re-checked offline. Each true pair (the order's own
transcription and pages) should be confirmed; two false pairs per order (the same pages under a number that is
not the order's, and the pages paired with an unrelated order's transcription) must never be. If a single false
pair is accepted, every strong verdict in that run is written as a lead instead. Results are in
`SUMMARY.json` → `controls`. On 2026-11-05: 56 of 60 true pairs confirmed, 0 of 120 false pairs accepted.

## Outputs (`output/`)

| File | What it is |
|---|---|
| `FRAGMENTS.jsonl` | One fragment per order with a strong find or lead, in the producer schema the tracker reads (`kind: original_representation`, `acceptable_as_original: false`, `needs_page_check`, URL, SHA-256 of the bytes read, page locator, match details). |
| `texts/` | The located pages' text layer with a provenance header. |
| `FINDS.csv` | One row per find: verdict, route, score, marker, page, URL, kind of source. |
| `STATE.json` | What has been examined for each order, carried to the next run. |
| `SUMMARY.json`, `REPORT.md` | Counts by route and verdict, controls, requests, timings. |

## What Tischendorf does not do

It changes no status, identity, census entry, codebook grade or count. The readiness tracker does not read this
job's fragments until the job is registered in `jobs/readiness-tracker/tracker.py` (`official_compilation_fragments`),
which changes the ready-for-human-review count and so waits for the owner. A strong find is a machine location, not
an authentication; human certification stays a separate count.

## Running

Daily (`DAILY`); after `readiness-tracker`, `fr-originals` and `ofr-compilations` when they run together. Tests in
`test_tischendorf.py` run first. Offline work (controls, corroboration, carried results) takes about ten seconds;
network orders then run on `JOB_WORKERS` threads (default 8), with PDF text extraction in separate processes, so
waiting on one site overlaps work on others. Budget per run: `JOB_MAX_REQUESTS` (default 2,400 in all, of which
`JOB_MAX_REQUESTS_FR` 900 and `JOB_MAX_REQUESTS_IA` 1,500) and `JOB_TIME_BUDGET_MIN` (default 200). The first run,
before these changes, took 62 minutes because it fetched one Federal Register issue at a time and spent its whole
request budget there. Polite fetching through `jobs/_lib/fetch_pool.py` (HTTPS only, robots.txt obeyed, per-host
throttling, every download hashed).
