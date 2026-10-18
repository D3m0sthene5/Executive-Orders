# Federal Register originals (job 2)

**What it does, in plain words.** For every executive order printed in the
Federal Register (1937 onward), this job fetches the official govinfo copy,
finds the order's own pages, saves their text, and records exactly which file
(and which pages of it) the text came from. The 3,359 orders with a
provisional status go first (2,665 of them are in the Federal Register's
index; the rest are older than the Federal Register or were never printed in it).

## How it finds each order

The list of orders comes from the **Office of the Federal Register's own
executive-order index**: 6,939 records from 1937 to 2026, each with the FR
citation (for example `2 FR 63`), publication and signing dates, title and,
from 1994, the document's PDF link. A frozen copy of the exact API response is
kept in `data/ofr_index/` (gzip-compressed; `PROVENANCE.json` gives the
sha256 of every original file and where it came from: the Stage 1 capture
inside the consolidated archive). It is catalog data, not proof.

Then, for each order:

1. **Already captured by Stage 21?** (`research/stage21/original_sources/`,
   40 PDFs) The job checks the file's sha256 against the custody record and
   reuses it. No download.
2. **1994 and later:** the per-document PDF on govinfo (the index's
   `pdf_url`, or one built from the document number). The whole PDF is the
   order.
3. **1937 to 1994:** govinfo's scan of the whole daily issue
   (`.../content/pkg/FR-1937-01-12/pdf/FR-1937-01-12.pdf`), or the issue the
   govinfo link service gives for the citation (`/link/fr/<volume>/<page>`,
   which also says which PDF page). Inside the issue it reads the printed page
   numbers from the running heads, goes to the cited page, looks for the
   order's number ("EXECUTIVE ORDER 10586", "Executive Order 12890 of ...", or
   the 1930s closing tag "[No. 7532]"), and ends at the filing line
   ("[F. R. Doc. ...]") after it. Only those pages' text is saved.
   Safeguards: if the issue's printed page numbers do not include the cited
   page, it is the wrong issue and nothing is taken from it (the govinfo link
   service is asked next; this is how EO 10153, whose OFR date points at the
   wrong day, is found). The number is only looked for on the cited page and
   the three after it (then the one before). References such as "AMENDING
   EXECUTIVE ORDER NO. 10153" or "pursuant to Executive Order 10153",
   "Docket No. 9337", and "No. 7700-A" (a different order, EO 7700A) are
   never taken as the order.
   For 1994 the link service is asked before the whole daily issue, because
   1994 issues are often 300 MB or more.
4. If govinfo fails, the Wayback Machine copies of the same links are tried
   (through the source-ladder module in `jobs/source-ladder/`).

Every order gets a **confidence** label:
- `high`: the cited page and the order's number were both found and the end
  line was found;
- `medium`: one check is weaker, and the notes always say which (the number
  is OCR-damaged, the order starts a page away from the cited page, the cited
  page number could not be read, the end line is missing so two following
  pages are included, or the range is longer than 12 pages);
- `low`: the pages were chosen from the printed page number only; the order's
  number could not be read in the scan.

**Only `high` may count without a person looking.** Every fragment carries
`location_verified: false` (no person has checked it) and `needs_page_check`
(true for `medium` and `low`). Job 8 must not count a fragment with
`needs_page_check: true` as satisfying the tracker's `original_text` step
until someone has looked at the PDF pages. In the samples, about 1 order in 6
from 1937 needed a page check (OCR of that year is poor); later years were
mostly `high`.

## What it writes (to OUTPUT_DIR)

| File | What is in it |
| --- | --- |
| `SOURCES.jsonl` | One SOURCE RECORD per order found: `url`, `sha256` of the downloaded file, `bytes`, `content_type`, `retrieved_utc`, `route` (`official/govinfo_fr_issue_pdf`, `official/ofr_index_pdf_url`, `reuse/stage21_original_sources`, ...), `page_or_item` = `"<vol> FR <page>, PDF pages x-y"`, `text_path`, `cache_path`, `notes`, `location_confidence`. |
| `FRAGMENTS.jsonl` | One CLAIM FRAGMENT per order found, kind `original_representation`, with `data` = `{url, sha256, page_or_item, ..., location_confidence, location_verified: false, needs_page_check}` (the shape the claim gate needs) and a plain `confidence_note`. |
| `texts/EO_<number>.txt` | The text layer of the order's own pages, with a header naming the file, its sha256 and the pages. For scans this is OCR: expect errors and bits of neighbouring documents. |
| `NOT_FOUND.csv` | Every order in scope that has no original yet, with a reason: `ofr_index_not_received_for_publication` (OFR says it was never printed in the FR; 436 orders), `ofr_index_has_no_fr_citation`, `fr_volume_1_1936_not_in_ofr_index` (1936 orders: the index starts in 1937), `not_in_ofr_index`, `downloaded_but_order_not_located`, `every_route_failed`, `downloads_rejected`. `permanent = no` means a rerun will try again. |
| `ATTEMPTS.jsonl` | Every request made for these orders. |
| `SUMMARY.json` | Counts (including `found_needing_page_check`, orders carried forward, and a `shrink_check` that warns if the outputs ever hold fewer found orders than the committed results did), and a projection of disk and time for the orders not yet done. |
| `RECHECK.jsonl`, `RECHECK_SUMMARY.json`, `texts/EO_<n>.recheck.txt` | Only after the opt-in recheck pass has run (see "Recheck pass" below): one record per rechecked order with the evidence used, a summary with counts and examples, and for each upgraded order the reading-order text from its heading to its filing line. |

The downloaded PDFs stay in the cache (`JOB_CACHE_DIR`, default
`<OUTPUT_DIR>/../fr-originals-cache`), stored once by sha256. The cache also
holds `state/`, one small file per finished order, which is how a stopped run
**resumes**: run the same command again and finished orders are skipped.

**The outputs always hold every order finished so far**, not only this run's.
`JOB_LIMIT=50` means "work on 50 orders that are not done yet"; orders done
earlier stay in the outputs. Stage 21 reuse records also give `repo_path`
(where the bytes are kept in this repo).

## How to run it

**The full run belongs on the PC.** About 6,500 orders need a download:
roughly 3,400 scanned daily issues plus 1,500 small PDFs. The scans grow from
about 3 MB an issue in the 1930s to about 200 MB in the early 1990s, so the
whole run downloads **about 130 GB**. With parallel workers (below) it takes
about 1.5–2 hours on the owner's PC, limited by the internet connection; one
process alone took 8 to 16 hours. It can be stopped and restarted at any time.

```
python -m pip install --user -r jobs/fr-originals/requirements.txt
REPO_ROOT=. OUTPUT_DIR=C:/Users/danie/eo-runs/fr-originals/output JOB_CACHE_DIR=C:/Users/danie/eo-runs/fr-originals-cache python jobs/fr-originals/job.py
```

(PowerShell: `$env:REPO_ROOT="."; $env:OUTPUT_DIR="C:/Users/danie/eo-runs/fr-originals/output"; $env:JOB_CACHE_DIR="C:/Users/danie/eo-runs/fr-originals-cache"; python jobs/fr-originals/job.py`.)
To save disk, add `JOB_KEEP_PDFS=0`: each scanned issue is deleted once its
orders are done (its sha256, size and URL stay recorded, so it can be fetched
again and checked).

**Parallel workers (`JOB_WORKERS`).** Whole issues are spread over that many
worker processes, each downloading and reading its own issue; they share the
cache and the per-order state files, so a stopped run still resumes and the
results are identical to a one-process run (tested on real 1940 orders:
SOURCES, FRAGMENTS and texts byte-identical with 1 and 6 workers). Default: every
CPU thread on a PC (16 on the owner's Ryzen 7 9800X3D), 4 on GitHub
(`settings.json` → `github_workers`); `JOB_WORKERS=1` gives the old one-at-a-time
run. On 2026-10-17 one process managed about 5–15 orders a minute (one 3.5 MB/s
download at a time, one CPU core); with parallel downloads and processing the
same run did about 50–60 a minute, limited by the internet connection
(about 45–55 MB/s on Wi-Fi), not the processor.

**Where to put the finished PC run (important).** GitHub's runner deletes
`jobs/fr-originals/output/` before every run of this job, and any push that
changes a file in this folder (or a manual "Run workflow") starts a run. So
do **not** rely on copying the PC run into `output/`. Instead copy the PC
output folder's contents (SOURCES.jsonl, FRAGMENTS.jsonl, NOT_FOUND.csv,
ATTEMPTS.jsonl, SUMMARY.json and texts/) into
**`jobs/fr-originals/data/full_run/`** and commit that (texts total roughly
60 to 100 MB). Every later run, on GitHub or on the PC, first loads
`data/full_run/` and then the last committed `output/` into its state folder
(this is called "carrying forward"; nothing is downloaded again for those
orders), and only then works on orders that are still missing. So a 40-order
GitHub run *adds* 40 orders to the full run's results; it can never replace
them with a smaller set. The commit itself starts one GitHub run, which
copies the full run into `output/` and adds up to 40 new orders.
`JOB_CARRY_FORWARD=0` switches this off; `JOB_PRIOR_OUTPUT_DIR=<folder>`
carries forward from another folder as well (for example a PC output folder
outside the repo).

Other settings: `JOB_LIMIT=50` (only the first 50 orders in priority order),
`JOB_ONLY_IDS=EO:9337,EO:10586`, `JOB_TIME_BUDGET_MIN=120`,
`JOB_MAX_REQUESTS=500`, `JOB_RETRY_NOT_FOUND=1` (try "not found" orders
again), `JOB_OFFLINE=1`. An order whose routes failed only for a passing
reason (no network, timeout, busy server, block) is marked `permanent = no` in
NOT_FOUND.csv and is tried again by the next run automatically. The console
prints a disk and time projection only once every decade still to do has a
measured issue size; before that it points to the figures above.

**On GitHub** a push of this folder runs it with the limits in
`settings.json` (40 new orders, 5-hour budget, scans deleted after use),
because GitHub's machines have 14 GB of disk and no memory between runs. Use
GitHub for small top-ups only; earlier results are carried forward as
described above. The 40 are spent on orders that need a download (orders the
OFR marks "not received for publication", and other no-download rows, come
last).

The job runs its unit tests first (`python -m unittest discover -s jobs/fr-originals -p "test_*.py"`, no network) and stops if any fail.

## Recheck pass for medium/low finds (opt-in, pdfplumber)

**What it is.** A separate pass, off by default, for orders whose result is
`medium` or `low` (`needs_page_check: true`). FR pages are printed in two or
three columns and the default locator reads the pypdf text layer, whose order
mixes neighbouring columns and the table of contents (for example EO 10193:
its heading is on the cited page, but in the middle column of a page that
starts with "CONTENTS", so the default locator skips it). The recheck fetches
only that order's issue again (same fetch module and cache), uses
**pdfplumber** (MIT) word coordinates to rebuild each page in reading order,
column by column, and looks for: the order's heading ("EXECUTIVE ORDER
10193"; for 1937-1945, a bare "EXECUTIVE ORDER" heading followed by the
order's closing tag "[No. 8336]", also when OCR reads its "]" as "3" or "J"),
the first filing line "[F. R. Doc. ... Filed ...]" after it with no other
document's heading or closing tag in between, and the printed FR page number
in the running head of the heading's page (the issue date in the running
head, "April 17, 1941", is not read as a page number, so 6 FR 1941 is not
confirmed by the year). A closing tag needs its opening "[" ("No. 8792)." on
its own line is a wrapped reference), and "Executive Order No. 10269 of July
6, 1951" at the start of a line is a reference, not another order's heading
(the modern "of <date>" heading has no "No.").

**When it upgrades.** Only to `high`, and only when ALL of these hold: the
heading (or bare heading + closing tag) for this order number and the filing
line are both located; the heading is on the cited FR page (that number read
in the page's running head, or the default locator's exact printed-page
match, and the two do not disagree); the issue's date is the OFR publication
date; the downloaded bytes have the same sha256 as the result being
rechecked; the span is 12 pages or fewer; and (a brake only) at least a
third of the OFR title's longer words appear near the heading. Otherwise the
result stays exactly as it was and the reasons are recorded. A `high` result
is never rechecked, downgraded or overwritten. Nothing is ever downgraded.

**What it writes.** `RECHECK.jsonl` (every rechecked order: result
`upgraded`/`stays`/`error`, reasons, and the evidence: heading, closing tag
and filing line text with PDF page and position, the running head read, the
cited-page method, OFR title words found) and `RECHECK_SUMMARY.json`. For an
upgraded order, `FRAGMENTS.jsonl` carries a new fragment in place of the old
one, same format, with `location_confidence: high`, `needs_page_check: false`,
`location_verified: false` (still no person has looked), the recheck's page
range, `text_path: texts/EO_<n>.recheck.txt` and a `recheck_evidence` field
(which also keeps the old confidence, pages and text path).
`SOURCES.jsonl` keeps the default locator's record unchanged, with an added
`recheck` field; its old text file is kept too. SUMMARY.json adds
`recheck_upgrades_applied`, `found_by_confidence_after_recheck` and
`found_needing_page_check_after_recheck` (and, in recheck mode, a `recheck`
section). Recheck results live in `<JOB_CACHE_DIR>/recheck/` (a stopped pass
resumes) and are carried forward from a committed `RECHECK.jsonl` plus the
`.recheck.txt` texts.
Without a recheck, the outputs are byte-for-byte what they were (checked on
the 1,395-order snapshot below).

**An upgrade is an overlay and can always be withdrawn.** The order's state,
and what is carried forward from a committed `FRAGMENTS.jsonl` /
`SOURCES.jsonl`, always holds the default locator's own result: a carried
fragment that has `recheck_evidence` is rebuilt from the unchanged SOURCES
record (and the added `recheck` field is dropped) before it is saved as
state; a state file that already holds one is read back the same way. The
upgrade is applied only at output time, and only from a recheck record of
the current `RECHECK_VERSION` whose `.recheck.txt` exists and whose base
sha256 still matches. So bumping `RECHECK_VERSION`, deleting `RECHECK.jsonl`
or losing a recheck text puts that order back to its `medium`/`low` fragment
(and its own text file) on the next run, makes it eligible for a recheck
again, and keeps SUMMARY.json consistent with FRAGMENTS.jsonl. A later rule
fix can therefore withdraw a wrong heuristic upgrade.

**How to run it** (PC; it needs `pdfplumber`, `pdfminer.six`, `pypdfium2`,
`Pillow`, pinned in requirements.txt):

```
REPO_ROOT=. OUTPUT_DIR=<out> JOB_CACHE_DIR=<cache> JOB_RECHECK=1 python jobs/fr-originals/job.py
```

`JOB_RECHECK_LIMIT=30`, `JOB_RECHECK_ONLY_IDS=EO:10193,EO:8336`,
`JOB_RECHECK_REDO=1` (recheck again), `JOB_KEEP_PDFS=0` (delete each issue
after use). In recheck mode no new orders are located unless `JOB_LIMIT` is
given. On GitHub set `"recheck": true` in settings.json (at most
`recheck_github_limit` = 60 orders a run). Without pdfplumber the pass logs
one line, rechecks nothing and says so in RECHECK_SUMMARY.json.

**Measured on real data (2026-10-17).** Input: a read-only snapshot of the
owner's full run in progress (1,395 found orders, 1937-1955; 133 `low`, 23
`medium`). 46 of the 156 medium/low orders were rechecked (30 used while
tuning the rules, then 16 held out; 31 issues, 162 MB downloaded):

| | rechecked | upgraded to high | stayed |
| --- | --- | --- | --- |
| tuning sample | 30 | 19 | 11 |
| held-out sample | 16 | 5 (4 before one fix: a bare "1925" line was taken for a contents entry) | 11 |
| by old label | 35 low / 11 medium | 17 low / 7 medium | 18 / 4 |

All 24 upgrades had every OFR title word (or all but one) next to the
heading. 11 of them have a different page range from the default locator,
for example EO 10412: the default locator took a footnote on PDF page 6
("See Title 3, Executive Order 10412, supra"); the order's heading is on
the cited page, PDF page 3. EO 8293/8294/8295/8296 (1939-12-05) were put on
PDF page 1 by the default locator; they are on pages 2-3. For all 24 the
recorded heading, closing tag, filing line and title words were reviewed;
spot checks reading the rebuilt page text (and, for EO 10193 and EO 8295,
the rendered page image): EO 10193 (heading in the middle column of a contents page, filing
line at the foot of the right column), EO 8295 (bare heading, "[No. 8295]", filing 39-4472), EO 10570 and
10571, EO 8293, EO 8296, EO 7578, EO 7579, EO 8086, EO 8424, EO 8790 (titles
and signing dates match the OFR index). Why the 22 stayed: 18 have no
heading or closing tag for the number in the text layer at all (OCR damage
such as "EXECUTIVE ORDER T0495", "994*", "9£01", or "[No. 7700-A]" which is
EO 7700A), and 4 have the heading on a different page than the OFR citation
(EO 8336 and 8337: cited 5 FR 593, printed on page 594, as the issue's own
contents list says; EO 7594: 740 not 739; EO 8332: 315 not 313) - these stay
for a person to decide. The pass took about
1.3 s per order with the issue already downloaded.

**Re-measured after the review fixes (2026-10-17).** A review rechecked 21
more medium/low orders (11 upgraded, 10 stayed; 10 of the 11 checked against
rendered page images). With the fixes (overlay kept out of the state, no
date tokens as page numbers, "[" required in a closing tag, no "No." in a
modern heading) all 67 sampled orders were rechecked again from a fresh
state (38 HTTP requests, 212 MB): 36 upgraded, 31 stayed, 0 errors (low: 29
upgraded / 26 stayed; medium: 7 / 5; 26 bare heading + closing tag, 10
numbered headings). 66 of 67 results and page ranges are identical to the
earlier ones. The one change is EO 10461 (18 FR 3513), which earlier stayed
`low` because the wrapped reference "Executive Order No. 10269 of July 6,
1951" in its own text was taken for another heading; it is now upgraded to
PDF pages 1-3 ("(Continued on p. 3515)", filing line F. R. Doc. 53-5528,
signed June 17, 1953, 10/10 title words; the base result had PDF page 1
only). The issue year had been in the running-head number set of 30 of the
records; it is now left out, and every upgrade except one (EO 10494,
confirmed by the default locator's exact printed-page match) is still
confirmed by the running head. On the snapshot, after the recheck:
high 1,275, low 104, medium 16; `needs_page_check` 120 (was 156).
Carry-forward on the same real data: with `RECHECK.jsonl` deleted, or its
records set to another `recheck_version`, a default run from a fresh cache
puts all 36 upgrades back and FRAGMENTS.jsonl, SOURCES.jsonl and texts/ are
byte-identical to a run that never rechecked; with `RECHECK.jsonl` kept, they
are byte-identical to the recheck output.

## What it does NOT establish

- That the text is the order's authentic, complete wording. The govinfo PDFs
  are official, but the page boundaries are found by machine and the scan
  text is OCR. A person must look at the PDF pages before relying on it,
  and must do so for every `medium` and `low` location before it counts.
- Anything about whether the order still has legal effect. The OFR index's
  "disposition notes" are not used here, and nothing here changes a
  provisional status, the ledger or any count.
- Orders never printed in the Federal Register (OFR's "not received for
  publication"), 1936 orders, and orders before 1936 are not covered; they are
  listed in NOT_FOUND.csv (1936 and later) for other routes (NARA, the
  presidential libraries, the American Presidency Project, Clifford Lord's
  lists).
