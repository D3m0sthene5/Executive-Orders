# Storage stream (Pergamon) notes

For the coordinator to record in Kean. Nothing here is a legal status, count or finding.

Owner questions
1. Will the owner create Cloudflare R2 and Backblaze B2 accounts (buckets, keys, a public read URL) and add them as GitHub
   secrets? The R2 backend is tested only against a local fake S3 and the AWS SigV4 documentation vector.
2. Approve a runner secret `PERGAMON_GITHUB_TOKEN` (release-write) and a one-line workflow change to pass
   `PERGAMON_BACKEND`, `GITHUB_REPOSITORY` and it to the job stage, if Ptolemy is to resume before R2 exists.
3. Approve running the 3,060-file migration of `jobs/ptolemy-custody/output/raw` to release assets (about 7 hours at
   GitHub's 500 content-writes an hour; resumable).
4. Any history rewrite (`git filter-repo`) is the owner's decision alone; only a rewrite shrinks the repository.

Owner decisions the tools do not yet carry out
- Ptolemy resumes only after migration, the runner secret, and the checker adapter patch are applied (STORAGE.md).

Findings
- GitHub release limits (verified 2026-11-06): 1,000 assets per release, each file under 2 GiB, no total or bandwidth
  limit; secondary rate limit 80 content writes a minute, 500 an hour.
- `SOURCES.jsonl` for Ptolemy will exceed the 5 MiB per-file budget near 5,000 records; it needs sharding or a slimmer
  record, and the claim checker globs only `SOURCES.jsonl`.
- Pushing any change under `jobs/ptolemy-custody/` starts a Ptolemy run on the pushed branch (paused: carries files forward,
  fetches nothing). It writes a small `BUDGET.json` into output and may commit results back to the branch; pull before the
  next commit.
- Sparse worktree: to run Ptolemy's tests this stream added `jobs/cassiodorus`, `jobs/app-executive-orders` and
  `jobs/source-ladder` (code only, output excluded, about 3.5 MiB) to its sparse set.
- `test_checker.py` for the claim checker cannot run in a sparse worktree; the adapter patch was tested with
  `test_runtime_economy.py` only. Run the full suite before applying it.
- WORKER_RULES.md's line-ending one-liner `open(p,'wb').write(open(p,'rb').read().replace(...))` truncates every file to
  zero bytes, because `open(p,'wb')` runs before the read. This stream lost and rebuilt its files to find out. Read the bytes
  first: `b=open(p,'rb').read(); open(p,'wb').write(b.replace(b'\r\n',b'\n'))`. The rules file should be corrected.
