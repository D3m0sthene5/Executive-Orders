# Official fixity: is our copy byte-identical to GPO's?

govinfo publishes a preservation record (PREMIS) for every package, listing the
SHA-256 that GPO computed for its files:
`https://www.govinfo.gov/metadata/pkg/<package>/premis.xml`. This job compares
that official SHA-256 with the sha256 the project recorded for every govinfo
file it holds: every `jobs/*/output/SOURCES.jsonl`, `jobs/fr-originals/data/full_run/`
and the family rule files in `research/readiness/rules/`. A match proves that
the project's copy is exactly the file GPO publishes. That is stronger custody
than our own hash alone, and the evidence agents cite before setting a rule's
`original_custody_verified`.

**What it covers.** Scanned Federal Register issues (1936-1994): the issue PDF is
the first object in the record, so each record is streamed and closed after a
few KB (median 64 KB; records can be 17 MB). Single-document PDFs (1995 on) are
**not listed** in these records, so they show `not_listed` and keep only the
project's own sha256. The metadata server ignores Range requests, so each
record is fetched once and stopped early, never re-requested.

**Measured 2026-10-17 on the owner's PC:** 300 files in 10 s with 6 workers;
291 match, 9 not listed, 0 mismatches.

## Outputs

| File | Contents |
|---|---|
| `FIXITY.csv` | One row per govinfo file: url, package, filename, the project's sha256, GPO's sha256, result (`match`, `mismatch`, `partial_match`, `not_listed`, `no_premis_record`, `unavailable`, `other_algorithm`), the PREMIS URL, bytes read, check time, the orders that cite the file, where it was found |
| `MATCHED_BY_SHA256.json` | Matched files keyed by sha256, so another job or an agent can look up a source in one step |
| `SUMMARY.json` | Counts, orders with a GPO-matched file, bytes read, time |

A `mismatch` means the project's bytes differ from GPO's current file. That is
worth a look (re-fetch through `research/readiness/FETCH_QUEUE.jsonl`), not proof
of an error: GPO occasionally replaces a scan.

## Running

It runs when its folder, a family rule file or the fr-originals full run
changes (`triggers.txt`), after the jobs that write sources (`after.txt`), and
by hand. Earlier results are carried forward from the last commit, so a run
only checks new files or files whose recorded hash changed. `JOB_WORKERS`
(default 6, one per connection to govinfo) and `JOB_LIMIT` work as in other
jobs. Standard library only; tests use no network.

Custody evidence only; nothing here changes a status or count.
