# cotton-capture-custody (Cotton)

Named for Sir Robert Cotton (1571-1631), whose library preserved manuscripts that would otherwise have been lost.

**Problem.** The American Presidency Project (APP) mirror saved each page's extracted text and the SHA-256 of the
page bytes, but not the bytes. The claim checker therefore marked every claim resting on an APP text
`custody_record_only` (unverified), because a hash record alone is not custody.

**What Cotton does.** For every source hash cited by a published claim (`research/readiness/claims/*.jsonl`) or
listed in `data/WANTED.jsonl` (claims awaiting completion), it fetches the page again from the same fixed source,
and keeps it only if its SHA-256 equals the recorded hash:

1. the exact Common Crawl WARC byte range, or the Wayback raw capture, recorded in
   `jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl`, decoded as `app_mirror.split_warc` decodes it;
2. a Wikimedia Commons file via `Special:FilePath`, up to 60 MB.

Archive captures are read from `jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl` and from
`jobs/poggio-archive-backfill/output/MIRROR_DOCUMENTS.jsonl` (captures of live-only pages not yet merged). When a
wanted hash is a live APP page and the archive lane holds a capture of the same URL, Cotton also preserves that
capture as an archive successor (`successor_of` names the live hash; it never tries the live route), so the claim
can be re-cited to bytes that stay provable. `SUMMARY.json` counts these as `archive_successors`.

Outputs: `captures/<sha256>.bin` (the exact bytes), `SOURCES.jsonl` (shared source-record format; `cache_path`
points at the committed copy, so `jobs/claim-checker` re-hashes it as held bytes), `FAILURES.jsonl` (hashes no
route reproduced, with each route's error) and `SUMMARY.json`. Bytes committed by an earlier run are re-hashed
and kept without a new download. Hashes that are not web sources (held PDFs, scans, books) are skipped.

**Limits.** Custody copies only: a matching hash shows these are the bytes the producer recorded, not that the
page is an authentic original. Nothing here changes a claim, status, count or the codebook. Certified: 0.

Tests (offline): `python -I test_cotton.py`.

Cotton never requests the live APP site: APP asks crawlers for a 10-second delay, and a live page that has changed can
never be re-proven. Live-harvested hashes are reproduced only through an archive capture of the same page.
