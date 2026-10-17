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
whole run downloads **about 130 GB** and takes **roughly 8 to 16 hours** (the
sample measured 2.5 to 5 MB/s including text extraction). It can be stopped
and restarted at any time.

```
python -m pip install --user -r jobs/fr-originals/requirements.txt
REPO_ROOT=. OUTPUT_DIR=C:/Users/danie/eo-runs/fr-originals/output JOB_CACHE_DIR=C:/Users/danie/eo-runs/fr-originals-cache python jobs/fr-originals/job.py
```

(PowerShell: `$env:REPO_ROOT="."; $env:OUTPUT_DIR="C:/Users/danie/eo-runs/fr-originals/output"; $env:JOB_CACHE_DIR="C:/Users/danie/eo-runs/fr-originals-cache"; python jobs/fr-originals/job.py`.)
To save disk, add `JOB_KEEP_PDFS=0`: each scanned issue is deleted once its
orders are done (its sha256, size and URL stay recorded, so it can be fetched
again and checked).

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
