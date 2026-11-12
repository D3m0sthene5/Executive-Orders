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
4. Commit and push, then start it once it is ready:
   `gh workflow run run-jobs.yml --ref <your-branch> -f job=<name> -f only=true`
   (or **Actions** tab → **Run jobs** → **Run workflow**, pick the branch, type the name and tick
   *only*). `only` runs exactly the named jobs, without the jobs that read their outputs.

To run a job every day, add an empty file named `DAILY` to its folder. It then
runs once a day (09:17 UTC) on `main`, and commits only if its results changed.

**No push starts a run (owner, 2026-11-09, Kean D-20261109-no-push-runs).** Push-started runs raced
each other and the runner's own result commits, and over 2026-11-06..09 most of them finished only to
have their results refused as stale; a tag push started them too. On `main`, the **sweep** (every three
hours, at 00:47, 03:47, ... UTC, and with the daily run) runs every job whose own folder changed, or whose
`triggers.txt` patterns (for example `research/readiness/claims/*`) match a path changed, in every commit
since the previous sweep's input commit, plus every job that lists it in `after.txt`. Committed job
outputs never trigger. To make a job run after others when they run together, list their names in
`after.txt`. When you need a result sooner than the next sweep, start the job by hand; a manual run can
name several jobs at once, and without `only` it also runs their consumers.
`.github/scripts/test_workflow_triggers.py` fails CI if a push trigger is added back to any job workflow.

To run a job again without changing it, start it by hand the same way.

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

## Long jobs: measure first, stop in time (Kean F-20261112-runner-deadline)

A job is killed at 6 hours (the 350-minute workflow timeout) and then publishes nothing. On 2026-11-11 a one-shot web
search over 2,251 orders ran into that wall after 5 h 50 min: about 30 s an order, never measured beforehand.

- Time 5-10 real items before the first full run and multiply. Over about 4 hours: shard the work across several job
  folders (they run side by side as separate stations) or stop starting new items at 4.5 h and continue next run.
- Use `jobs/_lib/runner_limits.py` (`past_safe_stop()`; `JOB_DEADLINE_SECONDS` overrides 4.5 h). The shared web search
  (`eo_websearch.run_campaign`) already obeys it.
- Write state, results and any paid-spend ledger every batch, never only at the end.

## Telling a slow job from a stuck one (Rattle Watch)

While a job runs, the run log prints one line a minute, for example
`[Rattle Watch] clark-discovery: 22m elapsed (last successful run 47m), last output 20m ago, CPU 31.0s in the
last 60s, network 4.2 MB in the last 60s`. Rising CPU or network means the job is working even when it prints
nothing. A job that prints nothing and uses neither CPU nor network for 20 minutes is stopped with exit code 124
and recorded as failed, instead of running to the workflow's 350-minute limit. A job that legitimately waits
longer in silence can raise its limit with a `STALL_MINUTES` file (1-340).

When the sweep runs a job only because a job it reads changed, web-search jobs among them (those whose
`triggers.txt` lists `jobs/_lib/eo_websearch.py`, such as Clark and Lewis) get 12 web requests instead of
their full budget; their daily run and any change to their own code still search in full.

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

**Parallel stations (Arsenale, `.github/scripts/arsenale.py`).** A run has three stages. *Plan* picks
the jobs and pins one input commit. *Execute* splits them into stations: jobs joined by `after.txt` share
a station and run there in order; other stations run at the same time on separate machines, with no
lock and a read-only token. *Publish* is the only stage that holds the branch writer lock: it checks out
the latest branch, keeps only the jobs whose declared inputs are unchanged since the input commit, commits
them in one `Results of job(s): ...` commit, and retries a rejected push up to five times. A job whose
inputs changed while it ran is refused (the summary and `oversized/runner-freshness/ARSENALE.json` say
why; its output is kept in the run's downloads) and re-run automatically on the current branch, at most
twice. A job that reads another job's output must say so (`after.txt`, `needs.txt`, `inputs.txt` or
`triggers.txt`); an undeclared read of another selected job may now see that job's previous output.

The runner prepares and fingerprints inputs before replacing a job's output. It keeps the previous generation until the new job succeeds. A failed or blocked attempt is retained under `jobs/_attempts/<job>/<run>-<attempt>/`, including its status, log and any captured input manifest; the prior output is restored. Same-run dependent jobs are blocked. Independent successful jobs retain the normal provenance and publication checks. Failure receipts are published separately and never promote an older output to a new generation.
