# Shared script runner

Any agent working on this project (Claude, Astra, Codex) or the owner can run a
script on GitHub's own machines by committing it here. Nothing runs inside a
chat's container, and the owner's PC does not need to be on.

Each run gets a fresh Linux machine with Python 3.12, about 7 GB of memory,
about 14 GB of free disk and up to about 5½ hours. Results are committed back
to the same branch, so the next agent can read them.

## Run a script

1. Copy `jobs/_template/` to `jobs/<name>/`. Use a short name with letters,
   digits, `-`, `_` or `.`, for example `jobs/stage20-dedupe/`.
2. Put the script in `job.py` (Python) or `job.sh` (bash). If both exist,
   `job.sh` runs.
3. Optional: `requirements.txt` for Python packages to install, and
   `needs.txt` for the repo folders the script reads (see below).
4. Commit and push. The run starts by itself.

To run a job every day, add an empty file named `DAILY` to its folder. It then
runs once a day (09:17 UTC) on `main`, and commits only if its results changed.

To rerun a job when files outside its folder change, list fnmatch patterns in
`triggers.txt` (for example `research/readiness/claims/*`). Committed job outputs
never trigger. To make a job run after others when they run together, list
their names in `after.txt`. A manual run can name several jobs at once.

To run a job again without changing it, open the **Actions** tab, choose
**Run jobs**, then **Run workflow**, pick the branch and type the job name.
Changing any file in the job's folder (outside `output/`) also reruns it.

## What the script gets

The script runs from the repo root. These environment variables are set:

| Variable     | Meaning                                                    |
| ------------ | ---------------------------------------------------------- |
| `OUTPUT_DIR` | Write every result here. It is emptied before each run.    |
| `JOB_DIR`    | The job's own folder, for reading its inputs.              |
| `REPO_ROOT`  | The repo root.                                             |
| `JOB_NAME`   | The folder name.                                           |

**Mass downloads and other long jobs: work in parallel.** A job that fetches
or processes many files should spread the work over worker processes (see
`fr-originals`: `JOB_WORKERS`, `make_ctx`, `_run_parallel`) and keep one result
file per item, so workers never collide and a stopped run resumes. Default to
every CPU thread on the owner's PC and about 4 workers on GitHub's 2-CPU
runner. Measured on 2026-10-17: one process downloading one file at a time
reached 3.5 MB/s; parallel workers reached 45–55 MB/s on the same connection.

The repo is several GB, so only `.github/`, `jobs/` and `HANDOFF/` are
downloaded by default. List any other folders the script reads in `needs.txt`,
one per line, for example `research/stage19`. Git LFS files (such as the
archive `.part` files and `releases/**/*.zip`) arrive as small pointer files;
a script that needs one runs `git lfs pull --include "<path>"` itself.

## What comes back

After the run, `jobs/<name>/output/` is committed to the branch with:

- `log.txt`: everything the script printed.
- `STATUS.json`: succeeded or failed, exit code, times, the commit that ran
  and a link to the run.
- Every file the script wrote to `OUTPUT_DIR`.

By default the runner moves files over 95 MiB (99,614,720 bytes) out of committed
output. A job may explicitly set `MAX_OUTPUT_FILE_BYTES` in its folder to a
positive integer at most 104,857,599, strictly below 100 MiB. Invalid values fail
before replacing the previous output. The effective cap is recorded in
`STATUS.json`, and its configuration is covered by ordinary input freshness checks.
Files above the cap are listed there and kept as a download on the run's page
(Actions tab → the run → Artifacts) for 90 days; they are not discarded. Publish
anything above the repository cap that must last longer as a release.

## Rules

- Scripts must not change files outside `OUTPUT_DIR`; only `output/` is
  committed.
- Never put passwords, API keys or tokens in a job. If a job needs a key, ask
  the owner to add it under Settings → Secrets and variables → Actions; the
  workflow then has to be changed to pass it to jobs.
- Running a script does not make its results accepted research. Findings still
  go through the project's normal review before any count changes.
- Write a line in `HANDOFF/` saying which job you started and why, so the
  other agents know to look for its results.
# Output publication and failed attempts

The runner prepares and fingerprints inputs before replacing a job's output. It keeps the previous generation until the new job succeeds. A failed or blocked attempt is retained under `jobs/_attempts/<job>/<run>-<attempt>/`, including its status, log and any captured input manifest; the prior output is restored. Same-run dependent jobs are blocked. Independent successful jobs retain the normal provenance and publication checks. Failure receipts are published separately and never promote an older output to a new generation.
