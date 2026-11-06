# Rules for every Encyclopédie worker

You are one stream of a campaign coordinated by a Claude Opus session. Read this file, then `CLAUDE.md` and `AGENTS.md`
(use `git -C <your worktree> show origin/main:CLAUDE.md` if they are not checked out). These rules override anything
convenient.

## Where you work

- Work only in the worktree path and branch your brief names. It is a **sparse** checkout of a 9 GB repository. Never
  run `git sparse-checkout disable`, `git checkout <other branch>`, `git stash`, or anything that widens to the full tree.
  Add a path you need with `git sparse-checkout add <path>` only if it is small (check with
  `git ls-tree -r -l origin/main <path> | awk '{s+=$4} END {print s/2^20 " MiB"}'` first; over 50 MiB, read with
  `git show origin/main:<file>` instead).
- Write only inside the folders your brief names. Do not edit `HANDOFF/`, `jobs/kean/register/`, `HANDOFF/KEAN*.md`,
  the campaign `LOG.md`, any status, codebook, census, claim or readiness file. Put findings, owner questions and notes
  in your stream's `NOTES.md` (the coordinator records them in Kean).
- The machine is Windows 11 with Git Bash. Python is `py` (3.12); run Python with `py -I`. A venv with pandas, pyreadr,
  pyreadstat, pypdf and requests is at `C:/Users/danie/eo-venvs/enc/Scripts/python.exe`; create your own venv under
  `C:/Users/danie/eo-venvs/` if you need other packages. Code that runs on GitHub's runner must use the standard library
  or a `requirements.txt` in the job folder.

## Git Bash path mangling

Git Bash rewrites arguments that start with `/` into Windows paths, which silently corrupts sparse-checkout patterns
and git pathspecs. Prefix such commands with `MSYS_NO_PATHCONV=1`.

## Line endings (this bites)

The checkout and the file tools on this PC can write CRLF. Before every `git add`, convert your files to LF:
`py -I -c "import sys;[open(p,'wb').write(open(p,'rb').read().replace(b'\r\n',b'\n')) for p in sys.argv[1:]]" FILES`.
After staging, `git diff --cached --numstat` must show only the lines you meant to change. Never stage files you did not
write (the checkout shows thousands of spurious "modified" files; ignore them, add paths explicitly, never `git add -A`).

## Bytes (the repository is at about 9.95 GB of GitHub's 10 GB)

- Commit no PDFs, page images, archives or large raw texts. Commit code, tests, small manifests (URL, SHA-256, size,
  retrieval time), located spans and parsed tables.
- Per job run: committed `output/` at most 20 MiB in total and no file over 5 MiB. Enforce it in the job itself (count
  bytes before writing; write a `BUDGET.json` with the totals). Raw downloads stay in `$JOB_CACHE_DIR` (the runner cache).
- Per push: at most 25 MiB of new blobs. Check before every push:
  `git rev-list --objects origin/main..HEAD | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' | awk '$1=="blob"{s+=$2} END {print s/2^20 " MiB"}'`

## Jobs (Tier 2 streams)

Follow `jobs/README.md` and `jobs/_template/`. Every job has: offline tests run by `job.py` before any network work;
planted positive and negative controls with a measured error rate in its output; robots.txt and per-host pacing through
`jobs/_lib/fetch_pool.py`; `SOURCES.jsonl` and `FRAGMENTS.jsonl` with exact spans in the format the claim kit
auto-discovers (read how an existing job writes them, e.g. `jobs/selden-statutes/` or `jobs/current-law/`, before
inventing a format); a `SMOKE` mode that runs a handful of real items, run first; and a job that **fails** when most of
its requests fail (Kean F-20261106-selden-fr-api-400: one bad API field failed a whole run). A job runs on GitHub when you
push a change in its folder to your branch; the runner commits results back to your branch, so `git pull --ff-only`
before your next commit. Verify a run only from its `output/STATUS.json` and log, never from memory.

## Evidence

Anything you learn from a web page, a model, or another session is a lead until bytes are held and hashed. Never record
a legal status, a revocation fact or a count as settled. No logged-in automation of Westlaw, Lexis, HeinOnline or
ProQuest, ever. Keep credentials out of files, logs and commits; read them from environment variables or GitHub
secrets.

## Leases

Your stream holds a Kean lease (`py -I jobs/kean/lease.py list` from the coordinator's worktree
`C:/Users/danie/eo-wt/enc-diderot`). Before you dispatch a GitHub job by hand, check it:
`py -I C:/Users/danie/eo-wt/enc-diderot/jobs/kean/lease.py --repo <your worktree> check --resource job:<name> --holder claude-encyclopedie`.

## Finishing

Push your branch (no force, no pull request; the coordinator opens it). Your final message to the coordinator gives:
what you built (paths), test results with counts, the job run URL and its `STATUS.json` result if any, measured numbers,
what failed, open questions for the owner, the bytes your pushes added, and your own tokens and wall time if you know
them. Be exact; the coordinator checks your claims against the files.
