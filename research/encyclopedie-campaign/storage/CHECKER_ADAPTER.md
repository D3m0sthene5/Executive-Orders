# Claim-checker adapter: fetch a Pergamon locator and re-hash it

Status: design plus a tested patch (`checker_adapter.patch`). The claim checker is count-sensitive and was **not**
edited. Nothing changes until the coordinator applies the patch, and no existing record carries a `pergamon` field, so
applying it changes no count today.

## How the checker resolves kept bytes today

1. `sources.py: load_job_sources` reads every `jobs/*/output/SOURCES.jsonl`. For each record it joins `cache_path`
   to the job's output folder (and the runner cache roots) with `_safe_child`; if the file exists it builds
   `HeldCopy(..., local_path=<file>, custody="job_cache")`, otherwise `custody="record_only"`.
2. `checker.py: check_source` (line ~683) calls `ctx.reader.verify_bytes(copy)` for each copy with `bytes_kept`.
   `TextReader.verify_bytes` -> `local_sha` re-hashes the local file with `file_sha256`; `True` becomes
   `held_bytes_verified`, `False` becomes the `held_record_but_local_bytes_differ` failure, `None` falls through to
   GPO/download/archive checks and finally `custody_record_only`.
3. Text extraction (`TextReader.texts`, `read_bytes`) reads the same local file and re-hashes before using it.

A Ptolemy record written with a non-git backend has `cache_path: null` and a `pergamon` object
(`{sha256, bytes, ext, backend, locator, stored_utc[, mirrors]}`), so today it falls to `record_only`.

## The minimal change

Treat a locator as another way to obtain the local file, then let the existing re-hash do the verifying. Everything
downstream (`verify_bytes`, `read_bytes`, `texts`, `check_source`) stays as it is, so the statuses are the existing
ones and a store can never "pass" a source by itself: bytes count only if they hash to the recorded SHA-256 on the
machine running the checker.

Functions to touch, all in `jobs/claim-checker/sources.py`:

| Function | Change |
|---|---|
| `CUSTODY_KINDS` | add `"pergamon_store"` (a kept-bytes kind; `bytes_kept` is already "not record_only") |
| `HeldCopy.__slots__` / `__init__` | new optional `pergamon` dict |
| `load_job_sources` | add `"pergamon"` to `fields`; when `local is None` and the record's `pergamon.sha256` equals the record's sha256 and has a `locator`, set `custody="pergamon_store"` and keep the dict. A locator naming a different hash is ignored (stays `record_only`). |
| `TextReader.__init__` | `self._pergamon_left = None` (fetch budget) |
| `TextReader.materialize` (new, ~35 lines) | if the copy has a locator and no local file: use `<cache_dir>/pergamon/<sha[:2]>/<sha><ext>` if present, else `pergamon_store.Store.from_env().get_verified(copy.pergamon)` (hash-checked before it is returned), write the file atomically, and set `copy.local_path`. Budget `CLAIM_CHECKER_PERGAMON_FETCHES` (default 400, 0 disables). Any exception leaves the copy unverified. |
| `TextReader.verify_bytes`, `read_bytes`, `texts` | call `self.materialize(copy)` first |

`checker.py` needs no code change. Optional follow-ups for the coordinator, not in the patch: add
`jobs/_lib/pergamon_store.py` to `jobs/claim-checker/triggers.txt`; reword the `custody_record_only` detail (checker.py
~706) to say "or a store locator that could not be fetched"; decide whether an unreachable store should instead report
`held_bytes_in_release_or_repo` (the Opus-release precedent: "bytes are kept, not re-hashed here"). The patch is the
conservative choice: unreachable stays unverified.

## Why the same code works after the switch to R2

A record carries its own backend and locator. A release locator is the public `browser_download_url` and is fetched
with no token and no configuration. An R2 record carries the object key; the checker builds the store from
`PERGAMON_BACKEND=r2` plus `PERGAMON_S3_PUBLIC_BASE` (a tokenless public read URL, so no secret reaches the checker).
`Store.get_verified` also falls back to the configured backend and mirrors by the hash-derived key, so records written
under releases keep resolving after R2 becomes primary, and vice versa.

## Evidence it works

`test_runtime_economy.py` gains `PergamonCustodyTests` (5 tests; the file's 6 existing tests still pass: 11 total):
the loader accepts only a locator that names the record's own hash; fetch, re-hash and text use the cache file; a store
that returns wrong bytes leaves the copy unverified; a tampered cache file is caught by the local re-hash (`False`);
the budget `0` disables the network step. `jobs/_lib/test_pergamon_store.py` also covers a reader built with the default
(git) configuration fetching a release record with no token. `test_checker.py` could not be run in the sparse worktree
(it needs modules outside the sparse set); the coordinator should run the full checker suite before applying.

Apply with `git apply research/encyclopedie-campaign/storage/checker_adapter.patch` (checked with `git apply --check`
against this branch's base).

## Runner note

GitHub's runner already reaches github.com, so the checker run there can fetch release assets. Each fetch is a plain
HTTPS download from `github.com/.../releases/download/...`; cost is the asset size (Ptolemy files held in git on
2026-11-06: 3,060 files, median 81 KiB, 90th percentile 1.1 MiB, largest 23.4 MiB). With 3,060 files migrated the first
full checker run downloads up to the 400-file budget, then caches under the checker's cache folder; raise the budget
deliberately, not by default.
