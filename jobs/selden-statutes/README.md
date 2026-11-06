# Selden statutes: Statutes at Large texts that act on or carry an order

Part of Selden (see `jobs/selden-fr-citers/README.md`). Holds the official Statutes at Large text of (a) statutes
the finding jobs name as acting on a census order (`jobs/later-events` edges whose acting instrument is a public law
or a Stat. citation; 60 statutes on 2026-11-05, led by the National Emergencies Act, 90 Stat. 1255, and the 1966
Title 5 codification, Pub. L. 89-554), and (b) statutes an open order's own held text cites as "N Stat. P", the law
it rests on, whose expiry or repeal a claim may need to show (2,150 citations in 4,399 orders, led by the Federal
Register Act 49 Stat. 500, the Pickett Act 36 Stat. 847 and the Civil Service Act 22 Stat. 403). Zero model tokens.

**Source.** govinfo's STATUTE collection: GPO's digitized volumes 1-64 (1789-1950, added in 2024) and volumes 65
on (1951 on). The link service `https://www.govinfo.gov/link/statute/{volume}/{page}` (or
`/link/statute/{congress}/public/{law}`), read without following the redirect, names the granule PDF
(`/content/pkg/STATUTE-48/pdf/STATUTE-48-Pg195.pdf`), which is downloaded through `jobs/_lib/fetch_pool.py`
(robots.txt; govinfo's disallows only search and admin paths; at most 4 requests in flight, 0.25 s apart).

**Custody.** `SOURCES.jsonl` records the granule's sha256 and its text layer (`texts/`); PDFs up to 400 KB are
committed under `pdf/` (60 MB a run) for `held_bytes_verified`; larger ones are re-downloadable by URL and hash.
PREMIS records list only whole volumes, so granules have no GPO-published hash. `page_number_printed` says whether
the wanted page number appears in the granule's text (the identity control).

**Outputs.** `FRAGMENTS.jsonl` (`later_event_candidates` for acting statutes whose text names the order, exact
spans), `BASIS.jsonl` (one row per order citing a held statute: the order's own citing sentence with its exact span
in the order's held text, and the statute source; not read by the claim kit), `SOURCES.jsonl`, `texts/`, `pdf/`,
`FAILURES.jsonl`, `SUMMARY.json`.

**Limits.** A statute an order cites is not shown to be its basis, nor to have ended or carried it: those are legal
readings for the claim. Text layers of the 1789-1950 scans are OCR. No status, census, codebook or count change.
Certified: 0. Merging registers `FRAGMENTS.jsonl` and `SOURCES.jsonl` with the claim kit, which waits for the owner.

**Running.** On a push to this folder or by hand. Budget `JOB_MAX_REQUESTS` 6,000, `JOB_TIME_BUDGET_MIN` 240; the
full list is about 4,500 requests and 3 GB. Tests (`test_statutes.py`, offline, small PDF fixture) run first.

## Overlap with Ptolemy and Pothier (checked 2026-11-06, `research/selden/tools/overlap.py`, `research/selden/census/OVERLAP.json`)

61 of the 2,179 statute granules are also on Ptolemy's request list (same sha256), and 27 granule URLs appear in Pothier's sources on `claude/pothier-family-doctrine`. Later runs carry every held page or text forward with no request, so none of these is fetched again.
