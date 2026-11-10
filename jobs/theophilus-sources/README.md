# theophilus-sources (Theophilus)

Named for Theophilus, the law professor who with Tribonian and Dorotheus compiled Justinian's Institutes (533).
This job gathers the sources that the write-ups of the provisional-YES orders must cite and that are not yet held.

**Problem.** Many provisional-YES orders cannot be written up because the current legal basis that keeps each
order operating is not held as a source (readiness blocker `CURRENT_BASIS_UNPROVED`). Two kinds of official,
free source can supply that basis. The job costs no model tokens.

## What it does

1. **National Emergencies Act continuation notices.** Lists every presidential document whose title contains
   "Continuation of the National Emergency" through the Federal Register API
   (`documents.json`, type `PRESDOCU`, phrase search, 1,000 per page, all pages), fetches each notice's official
   raw text, saves it as `texts/fr-<document number>.txt`, and records its SHA-256. `instrument_ids` holds the census
   orders (ids in `jobs/domesday-register/output/REGISTER.csv`) whose number the notice text names, in the forms
   "Executive Order 12170", "Executive Order (E.O.) 12170", "E.O. 12170" and lists such as "Executive Orders 12957
   and 13222". This is a mention only.
2. **Current U.S. Code and CFR sections.** Takes provisional-YES orders in
   `jobs/current-law/output/ORDERS_CURRENT_LAW.csv` whose row in `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`
   is not ready and lists `CURRENT_BASIS_UNPROVED` among its blockers, and reads their
   `usc_predicate_citations` and `cfr_predicate_citations`.
   * U.S. Code: only the needed title ZIPs from the release point `jobs/current-law` pinned
     (`output/SUMMARY.json`, `usc.release_point`, ZIP address pattern of `usc_scan.py`); each cited `<section>`
     is extracted with its notes to `texts/usc-t<title>-s<section>.txt`. A "note" citation maps to its section.
   * CFR: the eCFR versioner full-text XML for the cited section or part at the date `titles.json` reports as
     up to date. `www.ecfr.gov/robots.txt` forbids that endpoint (see `jobs/current-law/README.md`); the job obeys
     robots, so when it is refused the job falls back to the GovInfo bulk XML of the whole title (same eCFR
     schema, current copy), downloaded once per title and read as a stream. Parts larger than 6 MB of text are
     reported as failures, not saved.
   * One `SOURCES.jsonl` record per section or part, declared by its own identity: `instrument_ids` is empty (a
     section is not the text of the order that cites it), `mentioned_instrument_ids` lists the YES orders that cite
     it, `citation` names it, and `extracted_from` gives the url and sha256 of the downloaded response it was cut
     from (also in `notes`); `item_extract: "citation"` lets the claim kit match a current-law lead on that same
     response and citation to this text. Its `sha256` is the hash of the committed extracted text.
     (Until 2026-11-10 `instrument_ids` held the citing orders, so the claim kit read each section as that order's
     own text and its mention scan made bogus ACT records; `python theophilus.py --redeclare output/SOURCES.jsonl`
     rewrote the committed rows.)

## Output (`output/`)

`SOURCES.jsonl` (shared source-record format, discovered automatically by the claim kit), `texts/`,
`SUMMARY.json` (notices listed and fetched, orders named, sections fetched, YES orders covered, failures by
reason), `FAILURES.jsonl`, `log.txt`, `STATUS.json`.

## What it does not do

* It makes no legal finding. A notice that names an order is not proof that the emergency still covers that order;
  a cited section is a lead, not proof that the order operates under it.
* Notices before 1994 are not in the Federal Register API and are left for a later route.
* Citations that are not a single section or part (for example "10 U.S.C. subtitle A, pt. II, ch. 57 note") are
  listed as failures with reason `usc_citation_not_a_single_section`.
* It does not change any status, count or the codebook. Certified whole-lifecycle count: 0.

## Running

`job.py` runs `test_job.py` (offline, fake transport) first, then the job. Every request goes through
`jobs/_lib/fetch_pool.py` (HTTPS only, robots obeyed, throttled, hashed). `JOB_WORKERS` sets parallel workers
(default 4). A `DAILY` file reruns it once a day.
