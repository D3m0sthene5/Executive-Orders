# Pergamon migration of Ptolemy's and Selden's raw files (2026-11-06 to 2026-11-07)

Owner decision: D-20261106-encyclopedie-storage ("Move Ptolemy's and Selden's raw files into the new store once it
passes its tests, and keep the SHA-256 manifest in git").

## Result

- **3,691 unique files, 3,177,188,305 bytes**, copied from git (main at `178203a83a`'s history; blobs read with
  `git cat-file`, each re-hashed) into GitHub Release assets `pergamon-00` to `pergamon-ff` with
  `jobs/_lib/pergamon_store.py migrate`. Sources:
  - `jobs/ptolemy-custody/output/raw/` (3,060 files);
  - `jobs/selden-fr-acting/output/captures/` (557 files);
  - `jobs/selden-statutes/output/pdf/` (78 files; renamed to `<sha256>.pdf` in the store).
  Four git paths shared bytes with another, hence 3,695 paths for 3,691 unique files.
- **Verified:** every one of the 3,691 was downloaded again from its public URL without a token and its SHA-256 and byte
  count compared: 3,691 match, 0 differ (`verify_store.py`, results summarized in `PERGAMON_MANIFEST.jsonl`'s
  `verified_tokenless_rehash`).
- **Manifest:** `PERGAMON_MANIFEST.jsonl` beside this file, one record per file: `sha256`, `bytes`, `ext`, `locator`
  (the release asset URL), `stored_utc`, `git_paths`, `verified_tokenless_rehash`.
- **Nothing was deleted from git.** The files are still on main and in history; the checker still reads them there.
  Removing them is step 3 of `HISTORY_REWRITE_PLAN.md`, after the checker adapter (count-sensitive, owner) is merged.

## What went wrong, and the fix

Creating each shard release made a git tag on an ordinary commit, and GitHub ignores path filters on tag pushes, so 79
tags started about 870 workflow runs and dormant stage-20/21 workflows committed five times to main (Kean
F-20261107-pergamon-tag-triggers). The upload was stopped, 75 pending runs cancelled, and the remaining 177 shard
releases were created on `pergamon-store-root`, a commit with no workflow files; one test shard confirmed that such a tag
starts nothing. Future shard tags must point there too (set the release's `target_commitish`; all 256 shards now exist,
so the store creates no new tag in normal use).

## Throughput

GitHub allows about 500 content writes an hour. Three uploaders with 20 s spacing reached about 450-600 files an hour; a
single uploader about 150-180. Wall time about 7 hours including the stop.
