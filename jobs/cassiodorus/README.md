# Cassiodorus: keep the page bytes that claims cite

Named for Cassiodorus, whose monastery at Vivarium copied and kept the texts later ages could check
against. This job keeps the raw bytes of the American Presidency Project (APP) pages that claims cite,
so the claim checker can re-hash them.

## The blocker it removes

Thousands of orders are held only as APP transcriptions, which the owner's 2026-10-21 ruling admits as
provisional working texts. Each transcription page was read once (live, or from a Common Crawl or
Wayback capture), hashed, and parsed; the page bytes stayed in a download cache that is not committed.
The claim checker therefore reports every reference to such a page as `source_held: custody_record_only`
("only a custody record exists; the original bytes are in no committed place"), `all_checks_passed`
stays false, and `kit.py complete` rejects the claim as `rejected_mechanical` however sound the research
and review are. In the first Namier batch (`research/excavator/namier-serial-exemptions-2026-10-28`) all
seven independently upheld claims were stopped by this alone (36 `custody_record_only` rows, no other
failure).

## What it does

For each requested page it re-reads the capture the APP job recorded (`MIRROR_DOCUMENTS.jsonl`: Common
Crawl WARC byte range, or Wayback original bytes), checks that the bytes hash to the recorded sha256, and
keeps them at `output/raw/<sha256>.html` with a `SOURCES.jsonl` record whose `cache_path` the checker's
existing index resolves (custody `job_cache`; the checker re-hashes the file on every run). Bytes that no
longer hash as recorded are reported as `hash_mismatch` and not kept under the recorded hash; a page with
no document record is reported as `no_capture_record`. A recorded live page without a supported fixed
archive capture is reported as `no_archive_capture`; it is never requested from APP and does not count
as an archive outage. Previously kept pages, including exact live-page bytes already retained, are
carried forward from the prior generation after re-hashing.

Requests are bounded (300 pages per run): the APP pages cited in `research/readiness/claims/*.jsonl` and in
claim-kit packets' `CLAIMS.proposed.jsonl` under `research/excavator`, plus `REQUESTS.json` in this folder
(`sha256` list or `instrument_ids`, whose recorded pages are all kept). The archives are reached from
GitHub's runner; the cloud container used by agents refuses `data.commoncrawl.org`, so a local run only
reports.

## What it is not

Keeping a page's bytes makes a transcription verifiable as the transcription the claim read. It does not
grade the source, authenticate an original, or change any claim, status or count: `acceptable_as_original`
stays false, the standing note "original not yet held; replace and re-check quotes when an official copy
is retrieved" stays on every dependent claim, and the tracker keeps counting such orders separately.

## Running

`python3 -I jobs/cassiodorus/job.py` (`REPO_ROOT`, `OUTPUT_DIR`, `JOB_CACHE_DIR`, `JOB_PRIOR_OUTPUT_DIR`).
The sweep reruns it when claims or packet proposals change (`triggers.txt`). Tests:
`python3 -I -m unittest discover -s jobs/cassiodorus -p 'test_*.py'`. Standard library plus
`jobs/app-executive-orders/app_mirror.py`'s archive readers.
