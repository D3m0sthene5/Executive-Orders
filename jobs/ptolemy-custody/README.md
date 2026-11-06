# Ptolemy: keep the bytes of every source held only as a hash

Named for the Ptolemies' rule at Alexandria that every book arriving on a ship was copied for the Library
before the ship sailed.

## The blocker it removes

About 11,000 sources that the project's dossiers cite were read once: their SHA-256 and text were
recorded, but their bytes were never kept in a committed place. On GitHub's runner the claim checker can
re-download some of them. Agents, however, work where those hosts are unreachable, so their checks report
`custody_record_only`, and the claim kit refuses to file however sound the work is. The Herschel survey
(2026-11-05, `research/herschel/REPORT.md`) found that this alone blocks work on about 2,900 open orders.

## What it does

`build_requests.py` reads the claim checker's own source index and lists every source with no kept bytes.
It leaves out sources that GPO publishes with the same SHA-256, which the checker already accepts. The
list goes to `REQUESTS.jsonl` in this folder, so a run's inputs stay fixed while it is going. Each source
takes one route:

| Route | Sources (2026-11-05) | How |
|---|---:|---|
| `archive` | 8,386 American Presidency Project pages | Re-read from the recorded Common Crawl or Wayback capture with Cassiodorus's reader. The live APP site is never requested. |
| `live` | 2,899 files, mostly govinfo.gov PDFs | Re-downloaded from their own URL through the shared fetch pool (`jobs/_lib/fetch_pool.py`), which obeys robots.txt and paces each host. |
| skipped | 3,116 | Live-only APP pages, search pages, wiki pages, and daily-regenerated pages, whose recorded bytes cannot recur. The list builder prints the reason for each. |

A file is kept only if it hashes exactly as first recorded. It is saved as `output/raw/<sha256>.<ext>`
with a `SOURCES.jsonl` record whose `cache_path` the checker's existing index resolves (custody
`job_cache`, re-hashed on every check). Every attempt is written to `LEDGER.jsonl`. A hash mismatch, a
robots.txt refusal or a missing page is final. Other failures are retried, at most three times across runs.

Each run does a bounded share and carries every earlier kept file and attempt forward:

- at most 6,000 archive reads, at one a second;
- at most 3,000 downloads;
- at most 900 MB and 150 minutes per run.

It runs daily (`DAILY`) and on any change to this folder or to the shared code it imports (`triggers.txt`).
The request list covers the first pass in about two daily runs.

## What it is not

Keeping bytes proves only that a file is the one first read. It does not grade a source, authenticate an
original, establish identity, or change any claim, status or count. Certified: 0.

## Refreshing the list

Run `python3 -I jobs/ptolemy-custody/build_requests.py` after new sources are recorded, then commit
`REQUESTS.jsonl`. Sources already kept here drop out of the new list, because the checker index then shows
their bytes.
