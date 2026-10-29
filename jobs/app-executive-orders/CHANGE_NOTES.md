# Archive captures for live-only APP pages (Poggio backfill)

The American Presidency Project (APP) texts of 516 numbered orders were saved only from the live site
(`output/DOCUMENTS.jsonl`). The project kept each page's SHA-256 hash but not its bytes, and the live page keeps
changing, so no later download can reproduce the hash and every claim citing one of these texts fails the custody
check. A web-archive capture (a Common Crawl WARC record or a Wayback Machine raw capture) never changes, so its
hash can be reproduced at any time. This change lets the archive lane (`app_mirror.py`) find and record captures
of exactly these pages, through a runner job that cannot send a request to APP, and appends the results without
changing any existing row.

## What changed

**`app_mirror.py`** (this folder)

- Host guard. `http_get`, the lane's only network function, refuses every URL that is not `https` on
  `index.commoncrawl.org`, `data.commoncrawl.org` or `web.archive.org`, before connecting and on every
  redirect. A refused request raises `ArchiveRefused`, which is never retried or recorded as an ordinary
  failure. `lock_to_archives()` also makes DNS lookups of any other host fail for the whole process (a
  configured proxy host is allowed; `www.presidency.ucsb.edu` never is). The module asserts that APP's host is
  not in the allowed set.
- Refactor without behaviour change. The capture reading, parsing with the identity check, and row writing
  that the `documents` phase did inline are now the functions `read_capture`, `parse_capture` and
  `append_capture`, so the backfill uses identical code and identical record shapes.
- Four new phases:
  - `seed` (offline) prints the numbered instrument ids in `DOCUMENTS.jsonl` that have no row in
    `MIRROR_DOCUMENTS.jsonl`. Today this gives 516 ids; the seven live-only pages without an EO number are
    outside this definition and are not handled.
  - `backfill-index` finds a capture pointer for seed pages that have none. Of the 516 pages, 456 already
    have one in `MIRROR_INDEX.jsonl` (448 Common Crawl, 8 Wayback), because the original `cc-index` run
    recorded them and only the documents phase skipped them. For the other 60 (44 orders from 1933 to 1936,
    14 from 2026, EO 1216 and EO 12577) it asks the newest Common Crawl crawls one by one, skipping the
    16 crawls that already appear in `MIRROR_INDEX.jsonl` (those were read in full by `cc-index`), and stops
    once every page is covered. It then sends one Wayback CDX query for each page still without a pointer.
    It sends no request at all when every seed page already has a pointer.
  - `backfill-documents` reads one capture per seed page (a Common Crawl capture is preferred to a Wayback
    capture because its WARC byte range is exact; otherwise the newest capture is used) and keeps the archive
    lane's identity check: the EO number in the APP listing must equal the number in the captured page's
    heading, and must also equal the number of the live record. A capture without usable text or with a
    different number is a permanent failure in `MIRROR_FAILURES.jsonl` and produces no document row; an
    archive outage is only logged in `MIRROR_ATTEMPTS.jsonl` and is retried on the next run. Each saved row
    has the normal archive-lane shape plus `live_backfill: true` and a `live_comparison` block that records
    whether the capture's text and page bytes match the live harvest. The capture's text is written to
    `texts/<slug>.capture.txt`, so the live text at `texts/<slug>.txt` is never overwritten. The phase writes
    `BACKFILL_STATE.json`, which lists the orders still without a capture.
  - `merge` (offline) appends a backfill folder's rows and texts to this folder's output. Before writing it
    checks every new document row: the route is an archive route, the listing number, the record number
    and the heading number are equal, the capture text exists and matches its hash, and no existing text would
    be replaced. One failed check stops the merge before anything is written. After writing, it confirms that
    every base file still begins with exactly its previous bytes. A second merge of the same folder adds
    nothing.
- The backfill phases take `--base` (the folder they read; by default this job's `output/`) and `--out` (the
  folder they append to). When `--out` is `--base`, a local run appends directly and needs no merge.

**`app_harvest.py`** (this folder). `mirror_covered` leaves `live_backfill` rows out when it picks the live
lane's audit sample (every Nth mirrored path, fetched live again by `--audit-every`). Without this change the
new rows would shift the sample and add roughly 200 unaudited paths to the next live audit run, which would
mean about 35 extra minutes of requests to APP. With the change, the sample is the same as before the backfill.

**`test_app_mirror_backfill.py`** (this folder, new). There are 13 offline tests. They check the host guard
(APP URLs, plain `http`, other hosts and redirects to APP are refused, and the process lock refuses APP DNS
lookups); the seed definition; that the index phase asks only for pages without a pointer, skips crawls
already read, stops early, falls back to one Wayback query per page and sends nothing when everything is
covered; the documents phase (the capture is saved beside the live text, the base folder stays byte-identical,
saved pages are not read again, identity mismatches become permanent failures and outages are retried); a
local run into the base folder appending only; merge (it appends once, preserves base files as prefixes and
refuses a tampered row before writing); and the unchanged audit sample.

**`jobs/poggio-archive-backfill/`** (new runner job). It is named for Poggio Bracciolini, who recovered
classical texts by finding the copies that monastery libraries had kept.

- `job.py` runs both test files and stops if either fails. It then calls `lock_to_archives()`, runs
  `backfill-index` (newest 48 crawls, which goes back to about 2018, when APP adopted its
  `/documents/executive-order-*` addresses) and runs `backfill-documents` with 4 workers. It imports only
  `app_mirror`; it never builds the live lane's `FetchPool`, and no APP phase can be selected.
  `jobs/app-executive-orders/output` is only read. New rows go to the job's own `output/`, and rows from an
  earlier unmerged run are carried forward, so a rerun only appends.
- `data/LIVE_ONLY_IDS.txt` contains the 516 seed ids, produced by `app_mirror.py seed` from the committed outputs.
- `inputs.txt` declares the APP code and outputs it reads, for the runner's input-freshness record.
- The job has no `DAILY` file, no `triggers.txt` and no `after.txt`. It runs when its own folder changes or when
  someone starts it by hand.

This folder still has no `job.py`. Adding one here would make every push to the folder start a run. It would
also let a runner replace the whole 80 MB output folder that the local live lane writes, which could
collide with a local run. The separate job plus an offline merge avoids both problems.

**`jobs/cotton-capture-custody/`.** A small change is needed, for two reasons.

1. Cotton read captures only from `jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl`, so it could not see
   Poggio's rows until they are merged. It now also reads `jobs/poggio-archive-backfill/output/MIRROR_DOCUMENTS.jsonl`.
   Its existing archive route already handles both Common Crawl and Wayback captures, so no other change was
   needed for fetching.
2. Cotton preserves only hashes that a claim (or `data/WANTED.jsonl`) cites, and the existing claims cite the
   live hash, which a capture can never reproduce. Cotton now adds an archive successor: when a wanted hash is
   a live APP page and a capture of the same URL exists, Cotton also preserves the capture and records it with
   `successor_of: <live hash>`. It never tries the live route for a successor. The live hash stays in
   `FAILURES.jsonl`. The claim must then be re-cited to the capture's hash through the normal claim workflow;
   Cotton changes no claim. `SUMMARY.json` gains `archive_successors`, and `wanted_hashes` still counts only
   cited hashes.

New claims that cite the merged mirror fragments need no further change, because Cotton and the claim checker
both read `MIRROR_DOCUMENTS.jsonl`. One new offline test covers an unmerged capture preserved as a successor. A
stubbed offline run on the current repository gave the same published and failed counts as before, with 0
successors, because no capture of a live-only page exists yet.

## How to run it

1. Commit `jobs/poggio-archive-backfill/` and push. A push that changes the job's folder starts the job, and
   only that job. To rerun it later, open Actions, choose Run jobs, then Run workflow, and enter
   `poggio-archive-backfill`.
2. Check `jobs/poggio-archive-backfill/output/STATUS.json` (it should say succeeded), `BACKFILL_STATE.json`
   (number saved and orders still without a capture) and `log.txt`.
3. Merge offline from the repository root, then commit `jobs/app-executive-orders/output/`:

   ```
   python jobs/app-executive-orders/app_mirror.py merge --from jobs/poggio-archive-backfill/output
   python jobs/app-executive-orders/app_mirror.py seed | wc -l   # orders still live-only after the merge
   ```

4. Start `cotton-capture-custody` by hand, or wait for its next claims-triggered run. Re-cite affected claims to
   the capture hashes in the normal claim workflow.

To run locally without the runner (the cache folder is not committed):

```
python jobs/app-executive-orders/app_mirror.py seed > ids.txt
python jobs/app-executive-orders/app_mirror.py backfill-index     --download --cache-dir <dir> --ids-file ids.txt --crawls 48
python jobs/app-executive-orders/app_mirror.py backfill-documents --download --cache-dir <dir> --ids-file ids.txt --workers 4
```

Run this way, the phases append straight to `output/`, and no merge is needed. Pass `--out <folder>` to keep a
separate delta instead.

Offline tests:

```
python -I jobs/app-executive-orders/test_app_harvest.py
python -I jobs/app-executive-orders/test_app_mirror_backfill.py
python -I jobs/cotton-capture-custody/test_cotton.py
```

## Expected requests and time (estimates; no network was available to measure them)

All requests go to Common Crawl or the Wayback Machine. None go to APP.

| Step | Requests | Pacing | Estimated time |
| --- | --- | --- | --- |
| Crawl list (`collinfo.json`) | 1 | none | seconds |
| Common Crawl index, about 32 crawls not yet read | about 65 to 100 (one page count plus 1 to 2 result pages per crawl) | 1 s between starts; the index server is often slow and returns 503 errors, which are retried with backoff | 5 to 30 min |
| Wayback CDX, pages still uncovered | at most 60 | 1.5 s | 2 to 5 min |
| Capture reads | 456 already known plus any found above, at most 516 (about 20 KB each for Common Crawl) | 4 workers, 0.25 s between Common Crawl starts, 1.5 s for Wayback | 3 to 6 min |
| Total | about 520 to 680 | | about 10 to 40 min, plus runner setup |

The Common Crawl search will probably not stop early. Orders 14393 to 14435 date from 2026, after Common Crawl's
last APP crawl (CC-MAIN-2026-04), so only the Wayback Machine can have them. The 1935 orders may not have been
captured at all. A realistic outcome is that the 456 pages with known pointers are saved (minus a few
truncated or textless captures), plus whatever part of the 60 the older crawls and Wayback hold. The committed
delta is about 1 to 2 MB. Later reruns reuse the runner's download cache when it survives, and they skip
pages already saved.

## Risks

- **A capture is an older state of the page.** Captures in this set date from 2023 to 2026 (most from 2025),
  and the live harvest is from October 2026. A claim re-cited to a capture cites the APP text as of the capture
  date. `live_comparison.text_agrees` records, for every backfilled page, whether the two texts are identical;
  this measures staleness directly, alongside the earlier 205-page audit. These remain APP editorial
  transcriptions: every row keeps `grade: mirror_transcription` and `acceptable_as_original: false`, and none
  makes a legal or status finding.
- **Until the merge, only Cotton sees the new rows.** The claim checker reads archive captures only from this
  folder's `MIRROR_DOCUMENTS.jsonl`, and claim-kit finds APP fragments through `app-transcriptions`, which
  reads this folder. The merge is a manual offline step.
- **Existing claims still fail until they are re-cited.** A capture's hash never equals a live hash. A stubbed
  offline Cotton run today shows two such failures among cited hashes (Cotton's committed output shows three:
  EO 7188, EO 7208 and the EO 13286 page cited for EO 10631 and EO 12743). Cotton's successor records show
  which capture to cite.
- **Two APP representations per order.** After the merge, these 516 orders have both a live row and a capture
  row, as the 205 audited pages already do. Consumers that read both files (app-footnote-leads, app-transcriptions,
  clause-drafts, readiness-tracker) already handle that case, but their counts of APP rows will rise.
- **Residue.** Some of the 60 pages without a pointer will probably stay without a capture. The 7 unnumbered
  live-only pages are outside the seed. `BACKFILL_STATE.json` lists what remains.
- **Archive behaviour.** A Common Crawl index query that keeps failing is skipped for that run and logged, and
  rerunning asks again. A Wayback raw capture can redirect to a nearby timestamp; such a redirect is allowed
  only within `web.archive.org`, and the recorded `wayback_url` remains the URL that reproduces the stored
  hash, as it already was in the archive lane.
- **Index file order.** Rows are appended to `MIRROR_INDEX.jsonl` instead of being re-sorted, and
  `MIRROR_INDEX_SUMMARY.json` and `MIRROR_STATE.json` are left unchanged. The next full `cc-index` run
  re-sorts the index.
- **Cotton uses fixed captures.** Its live APP route is removed, and both initial URLs and redirects to
  APP are refused. Commons file redirects remain supported. Missing exact live bytes remain a custody hold;
  archive successors require ordinary claim re-citation and review.
