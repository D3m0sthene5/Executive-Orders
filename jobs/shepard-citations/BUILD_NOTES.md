# Build notes: shepard-citations and fr-pages (2026-10-28)

Both jobs were written in a session whose shell had no internet access. They were checked offline here: the unit
tests of both pass with sockets disabled, and Shepard ran in full against the repository's held inputs (without
the BLM tables, which need the network). Source formats were inspected with WebFetch and WebSearch. Nothing has run
on GitHub yet.

## What was verified, and how

**BLM listing page** (`https://www.blm.gov/programs/lands-and-realty/land-tenure/withdrawals/public-land-orders`,
WebFetch). The page links 24 PDFs covering PLOs 1-7898, signed from June 20, 1942 to October 9, 2020, and says each
list "shows the date for each Order and the page number on which it appears in the Federal Register." The links
use three URL forms: 21 of them `/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_<lo>-<hi>.pdf`,
plus `/sites/blm.gov/files/Public_Land_%20Orders_7753_7787.pdf` and
`/sites/default/files/docs/2022-02/Table%20of%20Public%20Land%20Orders%207853-7898.pdf`. All 24 are in
`data/blm_plo_tables.json`. `blm.gov/robots.txt` disallows only `/sites/README.txt` and `/*/media/oembed` under
these paths and sets no crawl delay.

**BLM table layout** (WebFetch excerpts of the 1-694, 695-2250 and 7853-7898 tables). The column heads are "No.",
"Signature Date", "Subject Heading" and "FR Citation". A row starts with the number and the date ("936 Feb. 4, 1954
.. Illinois, ..."). The subject wraps over several lines, and the FR citation stands on its own line in the older
tables but at the end of the first line in the 2016-2020 table. Citations are written "7 FR 4866", ranges with an en
dash ("7 FR 4866–7"), sometimes broken over two lines, and once without a space ("83 FR19093"). Citations of other
PLOs sit in brackets ("Amended by PLO No. 956 (19 FR 2353)"). Relation phrasing varies by era: "revoking EO No.
5214 of Oct. 30, 1929", "revoking in part EO No. 4796", "modifying EO creating powersite reserve No. 26", "Partial
Revocation to Executive Order Dated April 17, 1926, Public Water Reserve No. 107", "Partial Revocation Power Site
Classification No. 361 And Modification of PLO 7448". These rows checked: PLO 711 (EO 6604, 16 FR 3348), 936 (EOs
7185, 7212, 7452, 8331; 19 FR 769), 945 (EO 5214; 19 FR 1583), 1149 (20 FR 3439), 1249 (EO 7510; 20 FR 8471).

**govinfo link service** (WebFetch, and the source-ladder's own records). `https://www.govinfo.gov/link/fr/19/769`
resolves to the whole daily issue of February 10, 1954 (printed pages from 761 visible). The source ladder's
`SOURCES.jsonl` already records the same behaviour: `/link/fr/19/1809` redirected to
`/content/pkg/FR-1954-04-02/pdf/FR-1954-04-02.pdf`, 10,572,534 bytes, 54 PDF pages. `/link/fr/63/28516` returned
pages 28516-28521 of the May 26, 1998 issue, which print "Public Land Order No. 7330; Modification and Partial
Revocation of 9 Executive Orders ...". That six-page span suggests the single document's PDF for 1994 on, although
WebFetch described it as the issue. `govinfo.gov/robots.txt` does not disallow `/link/` or `/content/pkg/`.

**archives.federalregister.gov.** A web search index lists URLs of the form
`https://archives.federalregister.gov/issue_slice/1970/10/13/16033-16038.pdf` (year/month/day without zero padding,
then a page range). That URL opened in WebFetch and showed the October 13, 1970 issue from its cover. A different
range in the same issue (`16035-16036`) and a 1954 range (`1954/2/10/768-770`) both failed with a client error, and
`robots.txt` could not be read. `federalregister.gov/citation/19-FR-769` is closed to robots. So per-page slices are
not shown to work for arbitrary pages, and the route is off by default in fr-pages (`try_issue_slice`).

**Held inputs** (read here). The 1989 table rows (`DISPOSITION_1989.csv`, `acting_documents` pipe-separated as
`PLO:4620`, `EO:7442`, `Proc:2318`) and its fragments (only EO and Proc actors, mechanisms revocation, supersession
and termination; no PLO actor). `later-events` EDGES.csv (334 rows with a PLO actor, from OFR notes on 1937-and-later
orders). The source ladder's and fr-originals' held Federal Register texts: 354 of them contain a codification guide,
giving 789 entries such as "8622 (revoked by PLO 949)". `jobs/claim-kit/inputs.py`: `load_corpus` reads every
`jobs/*/output/EDGES.csv` and calls `add_pair(row["target_id"], row, ...)`; `add_pair` takes the actor from
`acting_id` (or `actor_id`, `actor`) and keeps a pair only when **both** the target and the actor are census ids.

**Local Shepard run without BLM tables** (2026-10-28, about 2 minutes on this machine; 30,725 held texts
scanned). 6,875 rows: 4,303 number citations, 465 date citations, 182 reserve citations, 699 Wikisource notes, 909
from the 1989 table and 317 from codification guides; 8,124 more were skipped as already present in later-events or
the codification job. Against the 30 land-probe orders it found the probe's ends that are not already in
later-events: EO 1237 rescinded by EO 4204 (the verb sits after a long land description), EO 1304 replaced "in lieu
of" by EO 1311, EO 4810 revoked by EO 6679, and the PLO ends of EOs 4872, 5038, 6143, 6276, 7373, 7435, 7504, 7509
and 7510 from the 1989 table. The ends of EOs 5214, 6604, 7185, 7212 and 7452 come only from the BLM tables. They
were found when a short reconstruction of the 695-2250 table was supplied as the previous run's text.

## What could not be verified

- **The pypdf text layer of the BLM PDFs.** The row parser was written from WebFetch's rendering, which may differ
  from pypdf's in line breaks and column order. The parser is built to tolerate this: a row starts at a line opening
  with a number and a date, and a number left alone on its line joins the date on the next line. The longest run of
  rising PLO numbers is kept, and the FR citation is the last one outside brackets. The first real run must still be
  checked: `SUMMARY.json` -> `plo_tables[].rows_parsed` should be close to `hi - lo + 1` for each table, and
  `PLO_TABLE.csv` rows with `fr_citation_not_found` show where it failed.
- **The size of each BLM PDF**, and so how many are committed (the cap is 2,000,000 bytes each).
- **Whether blm.gov serves the PDFs to a non-browser client from GitHub's network.** Some government sites answer
  403 behind a CDN. If that happens, `SUMMARY.json` -> `blm_tables_failed` lists the tables. Tables an earlier run
  read are carried forward. If none can be read, a run fails (keeping the previous output) when a previous
  `PLO_TABLE.csv` had rows; a first run publishes the other leads with an empty `PLO_TABLE.csv`.
- **Whether `archives.federalregister.gov` issue slices are stable bytes**, and for which ranges they exist.
- **Whether the govinfo link service gives a `#page=` hint for these citations.** Without one, fr-pages reads every
  page of the issue's text layer, which is slower but gives the same result.
- **The size of each wanted Federal Register issue.** Sizes grow from about 3-10 MB an issue in the 1950s to
  100-200 MB in the early 1990s, according to fr-originals' README.

## How to run

Shepard on GitHub: Actions -> Run jobs -> `shepard-citations` (or push a change in its folder). Locally:
`REPO_ROOT=. OUTPUT_DIR=<out> JOB_CACHE_DIR=<cache> python jobs/shepard-citations/job.py`. Use
`SHEPARD_OFFLINE=1` for no web requests and `SHEPARD_TEXT_LIMIT=<n>` for a trial.

fr-pages on GitHub: Actions -> Run jobs -> `fr-pages` after Shepard has committed `PLO_TABLE.csv`, or run both in
one manual run (`shepard-citations fr-pages`; `after.txt` orders them). Locally:
`REPO_ROOT=. OUTPUT_DIR=<out> JOB_CACHE_DIR=<cache> python jobs/fr-pages/job.py`. Eight of the 30 seeded PLOs
(1247, 1307, 1397, 2951, 4079, 4588, 5596, 5682) have no FR citation in the probe. They stay in `FAILURES.jsonl`
until `PLO_TABLE.csv` exists.

Tests: `python -I -m unittest -v test_shepard` (in `jobs/shepard-citations`) and
`python -I -m unittest -v test_frpages` (in `jobs/fr-pages`). Both jobs also run their tests first.

## Expected sizes and run times (estimates)

| | Shepard | fr-pages (30 seeded lines: 22 distinct pages now, 30 once PLO_TABLE.csv exists) |
|---|---|---|
| Requests | about 27 on the first run (robots.txt, listing page, 24 PDFs); 2 on later runs (PDFs cached) | about 2 a page (link service and PDF) plus robots.txt: about 45 the first time (about 61 with all 30), 0 for pages carried forward |
| Download | BLM PDFs, likely 5-40 MB in all (sizes unverified) | about 0.5-1.5 GB the first time (1949-1983 daily issues; the 1998 page is a small document PDF) |
| Run time | about 2-3 minutes for the text scan and 1-3 minutes for the BLM downloads and pypdf reading | download is a few minutes at 20-50 MB/s; reading the issue text without a page hint can take up to about 1 minute an issue, so up to about 30 minutes in the worst case |
| Committed output | EDGES.csv about 6 MB measured without the BLM tables, likely 10-15 MB with them; PLO_TABLE.csv about 3-5 MB; BLM texts a few MB; PDFs only if at most 2 MB each | texts a few KB each; PDFs at most 16 MB each and 200 MB a run (likely 10-15 issues of the 1940s-1950s, roughly 50-120 MB) |

## Open risks

1. **claim-kit drops every PLO actor (change needed in `jobs/claim-kit/inputs.py`, not made here).** `add_pair` keeps
   a pair only when the actor is a census id, so `PLO:936 -> EO:7185` from Shepard never reaches a packet. The same
   happens to the 334 PLO rows later-events already writes and to every proclamation actor. The fix is to let
   `add_pair` accept actor ids with a known non-census prefix (`PLO:`, `PROC:`, `PL:`) while still requiring a
   census target. Until then, Shepard's PLO leads are usable only from `EDGES.csv` and `PLO_TABLE.csv` directly.
2. **Volume of cross-references.** About 43% of Shepard's rows (2,975 of 6,875 in the local run) have no relation word (`cross_reference`).
   For land orders a later citation by number usually does act on the order, so they are kept, but claim-kit will
   offer each one as a pair. If packets become noisy, claim-kit (or packet preparation) could skip
   `cross_reference` rows from `shepard_text_*`.
3. **Date and reserve resolution are inferences.** The census holds numbered orders almost only, so an "Executive
   order of <date>" that names an unnumbered order can resolve to the one numbered order of that day. Every such row
   is flagged `unnumbered_orders_outside_census_may_share_date`, and 1,500 ambiguous or unmatched date citations are
   listed in `UNRESOLVED.csv`. A reserve is resolved to the earliest held order naming it, which can be an
   amending order when the creating order is not held.
4. **OCR and neighbouring documents.** Federal Register page texts are cut to the citing order's own span when its
   heading or closing tag can be read. About 20% of a 400-text sample could not be cut, and those rows are flagged
   `citing_span_not_located_neighbouring_documents_possible`. ProQuest and Hathi OCR misreads numbers and dates.
5. **BLM subject headings are editorial summaries.** "revoking EO No." in a heading does not say whether the
   revocation was whole or partial (the EO 7509 / PLO 4588 conflict in the probe is an example); only the PLO's FR
   text settles that, which is what fr-pages is for.
6. **The relation word is a proximity heuristic.** In sentences that cite several orders and several verbs, the
   nearest word may belong to another clause.
7. **fr-pages `instrument_ids` lists the printed PLO first.** The task asked for the target orders, and they are
   present. The PLO is added before them so that `claim-kit/inputs.py` never treats a PLO page wanted for a single
   order as that order's own text. A consumer that requires `instrument_ids` to contain only census orders would
   need to skip the first element (`printed_instrument_id` names it).
8. **Official-copy registration.** The probe found that `source_supplement` registers an FR text as official only
   when the raw issue PDF is held. fr-pages records with `cache_path` carry held bytes; record-only records (large
   issues) will not pass that gate unless the checker re-downloads and compares sha256. Committing larger PDFs would
   need a higher `commit_max_bytes`, or a release asset for the big issues.
9. **Repository growth.** Committed issue PDFs accumulate across runs, because pages carried forward keep their
   bytes. `auto_from_shepard` is off by default for this reason. Turning it on adds up to `max_items` issues a run.

## Changes other jobs would need (not made)

- `jobs/claim-kit/inputs.py` `add_pair`: accept non-census actors with known prefixes (risk 1).
- `jobs/ofr-codification-1989`: it could emit its PLO rows ("Revoked by PLO 4620") as fragments. Shepard covers
  them meanwhile as `shepard_ofr1989_table`.
- `jobs/source-ladder`: when an issue PDF it holds is cited for a PLO page beyond pages 1-6, it could extract that
  page. fr-pages covers the wanted pages, but it downloads the issue again because job caches are separate.
- Packet preparation (probe recommendation 3): read `PLO_TABLE.csv` and Shepard's `EDGES.csv` as leads, and offer
  fr-pages' held pages as the actor's official text.
