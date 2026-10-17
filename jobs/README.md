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

Files over 95 MB cannot go into git. They are listed in `STATUS.json` and kept
as a download on the run's page (Actions tab → the run → Artifacts) for 90
days. Publish anything that must last longer as a release.

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
