# Pergamon: keeping source bytes outside git

Plain-English summary for the owner and the coordinator.

## The problem

GitHub reported the repository at 9,717,466 KB against a 10 GB limit. Ptolemy (the custody job) had committed about 2.1 GB
of raw source files under `jobs/ptolemy-custody/output/raw/<sha256>.<ext>` since 2026-11-05; it is now paused
(`jobs/ptolemy-custody/PAUSED`). On origin/main it holds 3,060 files (2.58 GiB unpacked; median 81 KiB, 90th percentile
1.1 MiB, largest 23.4 MiB; 1,445 PDF, 1,174 HTML, 182 JSON, 181 .htm, 49 .bin, 28 XML, 1 text) with about 7,300 requests
still due. Deleting files from git does **not** shrink the repository: history keeps every blob.

## The design

Git keeps only small manifests: SHA-256, byte count, extension, backend, locator, store time. The bytes live in a
content-addressed store, `jobs/_lib/pergamon_store.py`, standard library only. A file is trusted only if it hashes
exactly to its manifest: `Store.get_verified` returns bytes only on an exact match and raises `HashMismatch` otherwise.
The store itself is never an authority, only a place to find bytes.

| `PERGAMON_BACKEND` | Where the bytes go | State |
|---|---|---|
| `git` (default) | a folder (`output/raw/`), the old behaviour | what every job does today |
| `release` | GitHub Release assets, interim store | built; live smoke test passed (`SMOKE.md`) |
| `r2` | Cloudflare R2 (S3 API, SigV4 signed inside the library), optional Backblaze B2 mirror | built and tested against a local fake S3 that recomputes the signature, plus the AWS documentation's published SigV4 test vector; **never run against real R2** (no account) |

### Release backend, and the limits it was built to

- Verified 2026-11-06 at https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases : "Up to 1000
  release assets may be associated with a single release", "Each file included in a release must be under 2 GiB", "There
  is no limit on the total size of a release, nor bandwidth usage".
- Upload API (https://docs.github.com/en/rest/releases/assets): `POST https://uploads.github.com/repos/OWNER/REPO/releases/ID/assets?name=...`
  with the raw bytes; a duplicate name returns 422; a 502 "may leave an empty asset with a state of starter" (the code
  deletes such an asset and retries).
- Rate limits (https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api): no more than 80
  content-generating requests a minute and 500 an hour; wait for `retry-after`, else until `x-ratelimit-reset`, else at
  least a minute. The library does exactly that. For a bulk load set `PERGAMON_WRITE_INTERVAL=8` (seconds between
  writes) to stay near 450 an hour.
- Shard width: tag `pergamon-<first 2 hex digits of the SHA-256>`, asset `<sha256><ext>`. 256 releases hold up to 256,000
  files before any one is full. The 3,060 Ptolemy files put at most 56 in one release (the largest prefix, measured), and
  the 11,000-source goal about 43 on average. If a release nears 1,000 assets the library refuses the upload and says to
  set `PERGAMON_SHARD_HEX=3` (4,096 shards).
- Shard and self-test releases are prereleases with `make_latest: false`, so they never become the repository's
  "latest release". The 256 tags are refs on the default branch's head (a few bytes each).
- Downloads use the public `browser_download_url` with **no token**; the repository is public. If it ever becomes private
  the download path must change.
- Release assets do not count toward the repository's git size. The docs set no total limit, but this is an interim
  store: treat R2 plus a B2 mirror as the target.

## The switch to R2

Change environment only (GitHub secrets for the runner, the shell for a PC run):

```
PERGAMON_BACKEND=r2
PERGAMON_S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
PERGAMON_S3_BUCKET=<bucket>
PERGAMON_S3_KEY_ID=...   PERGAMON_S3_SECRET=...   PERGAMON_S3_REGION=auto
PERGAMON_S3_PUBLIC_BASE=https://<public r2.dev or custom domain>      # optional: readers fetch with no secret
PERGAMON_MIRROR_ENDPOINT=https://s3.<region>.backblazeb2.com   PERGAMON_MIRROR_BUCKET=...   # optional B2 mirror
PERGAMON_MIRROR_KEY_ID=...   PERGAMON_MIRROR_SECRET=...   PERGAMON_MIRROR_REGION=<b2 region>
```

The endpoint forms are as I understand Cloudflare's and Backblaze's S3 documentation; confirm them when the accounts
exist. Records already written keep working: each carries its backend and locator, and `get_verified` tries the record's
own locator, then its mirrors, then the configured backends by the hash-derived key. To move the data, run
`py -I jobs/_lib/pergamon_store.py migrate ...` again with the R2 environment; it re-uploads from verified local files and
skips files already in the manifest. Byte-span verification (fetch bytes, compare hash) is the same code in every case.

## Migrating the 3,060 files already in git

Do not delete them from git (deleting does not shrink history, and the claim checker resolves `cache_path` to them
today). Upload them so any later cleanup has somewhere to rely on:

1. Use a **full** checkout (the campaign worktrees are sparse and lack `output/`), for example
   `C:/Users/danie/Projects/Executive-Orders`.
2. Set `PERGAMON_BACKEND=release`, `GITHUB_REPOSITORY=D3m0sthene5/Executive-Orders`, `GITHUB_TOKEN` (for example from
   `gh auth token`) and `PERGAMON_WRITE_INTERVAL=8`.
3. `py -I jobs/_lib/pergamon_store.py migrate --dir jobs/ptolemy-custody/output/raw --manifest research/encyclopedie-campaign/storage/PTOLEMY_MANIFEST.jsonl`
   Each file's bytes must hash to its file name or it is skipped and reported. It is resumable (rerun after any stop) and
   deduplicated. Expected: 2.58 GiB up, about 3,060 asset uploads plus up to 256 release creations, which is **roughly 7
   hours at the 500-an-hour write limit** (a calculation from the documented limit, not a measurement). Use `--limit N`
   for a trial of N files.
4. Commit only `PTOLEMY_MANIFEST.jsonl` (about 3,060 records of about 400 bytes, near 1.2 MB) in a push under the 25 MiB
   budget.
5. Optionally add the `pergamon` locator to those SOURCES records in a later Ptolemy run, so the checker can fetch the
   bytes where `cache_path` does not resolve. Ptolemy's carry-forward preserves `pergamon` records; it does not yet
   rewrite old git-backed ones.

## How Ptolemy routes bytes (designed, not live)

`jobs/ptolemy-custody/ptolemy.py` builds `Store.from_env(git_root=output/raw, git_base=output)`. With the default
`PERGAMON_BACKEND=git` nothing changes (same files, same `cache_path`). With any other backend a kept file goes to the
store before it is recorded; its SOURCES record gets `cache_path: null` and a `pergamon` object, and carry-forward keeps
those records without any file. A store failure is recorded as `store_failed`, is not charged to the source's three
attempts, and five in a row stop the run. Legacy `output/raw/` files are still carried, so existing `cache_path` records
resolve. `BUDGET.json` (via `jobs/_lib/byte_budget.py`: 20 MiB per output, 5 MiB per file) is written every run and
**enforced** once a non-git backend is on; `raw/` is excluded from the enforced total while legacy files remain there.
`PAUSED` is untouched: `job.py` still carries files forward and fetches nothing.

Resuming Ptolemy needs, in order: the migration above; the runner to pass `PERGAMON_BACKEND=release`,
`GITHUB_REPOSITORY` and a release-write token as `PERGAMON_GITHUB_TOKEN` (a repository secret; the run-jobs fetch stage has
`contents: read` and no such variable today, and `.github/workflows/` is outside this stream's write scope); the checker
adapter patch (`CHECKER_ADAPTER.md`); then deleting `PAUSED` and restoring `DAILY`. One watch item: `SOURCES.jsonl` is 2.3
MB for 3,060 records (about 0.77 KB each, about 1 KB with the locator), so it passes the 5 MiB per-file limit near 5,000
records. Before the full 11,000 the job and checker need sharded `SOURCES-*.jsonl` files (the checker globs only
`SOURCES.jsonl`) or a slimmer record.

## Byte budget

`py -I jobs/_lib/byte_budget.py` measures new blob bytes on HEAD against a base ref (default `origin/main`, 25 MiB) and a
job's `output/` (20 MiB, 5 MiB per file); exit 1 over budget, 2 on a measuring error. Flags: `--job NAME`,
`--output-dir`, `--exclude`, `--max-push-mib`, `--max-output-mib`, `--max-file-mib`, `--write-json`.

## What only the owner can do

- Create the Cloudflare R2 account, bucket, API token and a public read URL or custom domain; create the Backblaze B2
  bucket and application key for the mirror; store them as GitHub secrets.
- Provide a runner secret (`PERGAMON_GITHUB_TOKEN`) with release-write rights if the interim release store is to be used
  from GitHub Actions, and approve the workflow change that passes it.
- Run or approve the 3,060-file migration (long; it uses the owner's token and upload bandwidth).
- Decide on any history rewrite (for example `git filter-repo` dropping `jobs/ptolemy-custody/output/raw/` from history).
  Only that, followed by GitHub support's garbage collection, actually reduces the repository's size; it rewrites every
  commit hash, breaks open branches and pull requests, and invalidates cited commit ids. This stream recommends nothing
  here beyond noting that a verified store makes such a rewrite safe to consider.
- Decide whether release assets stay as a permanent second copy or are retired once R2 and B2 hold the data.
