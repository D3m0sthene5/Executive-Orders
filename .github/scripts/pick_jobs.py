"""Decide which jobs/<name>/ folders the runner should run.

Pushes stay light (owner, 2026-10-28: adding a file must not mean waiting on the pipeline):
- A push runs only the jobs whose own folder had a file changed outside output/, and nothing
  downstream of them. Data, claims, notes, research and rulings start no jobs on push.
- The sweep (scheduled every three hours) runs every job whose triggers.txt has a pattern
  (fnmatch, e.g. "research/readiness/claims/*") matching a path changed on the default branch
  since the previous sweep, plus every job that reads their outputs (after.txt).
- The daily scheduled run (09:17 UTC) runs every job whose folder contains a file named DAILY,
  plus their consumers.
- A manual run runs the named job(s), separated by spaces or commas, plus their consumers.
Picked jobs are ordered so that any job listed in a job's after.txt runs before it. Folders
starting with "_" (the template) are never run. The result goes to the step output "jobs" as a
space-separated list; jobs a sweep runs only as consumers go to "downstream".

The runner's initial sparse checkout contains job code/data but omits outputs.
The picker reads root entrypoints and selector manifests. The selected-job
materializer runs afterward; do not add reads of output generations here.
"""

import fnmatch
import os
import re
import subprocess
import sys

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ZERO = "0" * 40
RUNNER_FILES = {".github/workflows/run-jobs.yml"}
SMOKE_TEST = "example-hello"
DAILY_CRON = "17 9 * * *"
# A sweep looks back a little further than its 3-hour interval, so a commit is never missed between
# sweeps; a file changed twice in the overlap only reruns the same jobs once more.
SWEEP_WINDOW = "3 hours 20 minutes ago"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def runnable(name):
    folder = os.path.join("jobs", name)
    return NAME.match(name) and any(
        os.path.isfile(os.path.join(folder, f)) for f in ("job.sh", "job.py")
    )


def changed_files(before, after):
    if before and before != ZERO and git("cat-file", "-e", before).returncode == 0:
        base = before
    else:
        # New branch: compare with where it left the default branch.
        default = os.environ.get("DEFAULT_BRANCH") or "main"
        base = git("merge-base", f"origin/{default}", after).stdout.strip()
        if not base or base == after:
            base = f"{after}~1"
    out = git("diff", "--name-only", base, after)
    if out.returncode != 0:
        sys.exit(f"Could not list changed files: {out.stderr}")
    return out.stdout.splitlines()


def job_list(name, filename):
    """Non-comment lines of jobs/<name>/<filename>, or [] if it does not exist."""
    path = os.path.join("jobs", name, filename)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [l.split("#", 1)[0].strip() for l in fh if l.split("#", 1)[0].strip()]


def all_jobs():
    # The non-cone runner bootstrap includes these root entrypoints for every
    # job, but omits nested data and output generations until after selection.
    return sorted(n for n in os.listdir("jobs") if not n.startswith("_") and runnable(n))


def ordered(picked):
    """Stable order in which every job's after.txt predecessors (if picked) come first."""
    picked, done, out = list(dict.fromkeys(picked)), set(), []

    def visit(name, path=()):
        if name in path:
            raise ValueError("Job dependency cycle: " + " -> ".join((*path, name)))
        if name in done:
            return
        for before in job_list(name, "after.txt"):
            if before in picked:
                visit(before, path + (name,))
        done.add(name)
        out.append(name)

    for name in picked:
        visit(name)
    return out


def with_consumers(picked):
    """Include downstream jobs because output-only bot commits trigger no workflow."""
    selected=set(picked)
    while True:
        more={name for name in all_jobs() if any(dep in selected for dep in job_list(name,'after.txt'))}
        if more <= selected:return sorted(selected)
        selected |= more


def recent_changes(since=SWEEP_WINDOW):
    """Paths changed on this branch's first-parent history since a time (merge commits count in full)."""
    out = git("log", "--first-parent", "-m", "--name-only", "--format=", f"--since={since}", "HEAD")
    if out.returncode != 0:
        sys.exit(f"Could not list recent changes: {out.stderr}")
    return sorted({line for line in out.stdout.splitlines() if line.strip()})


def for_changes(changed, triggers=True):
    """Select direct consumers of code/data edits; outputs never start feedback loops.

    Shared-library consumers declare exact files in triggers.txt, including
    transitive imports. This keeps docs/test-only library edits from refetching
    the corpus and makes non-Python or dynamic dependencies explicit too.
    """
    picked = []
    for path in changed:
        # A change to the runner itself reruns the smoke test.
        if path in RUNNER_FILES or path.startswith(".github/scripts/"):
            if SMOKE_TEST not in picked and runnable(SMOKE_TEST):
                picked.append(SMOKE_TEST)
            continue
        parts = path.split("/")
        if len(parts) < 3 or parts[0] != "jobs" or parts[2] == "output":
            continue
        name = parts[1]
        if name.startswith("_") or name in picked or not runnable(name):
            continue
        picked.append(name)
    if not triggers:
        return picked
    # Jobs that asked to rerun when these paths change (job outputs never count).
    inputs = [p for p in changed if not re.match(r"^jobs/[^/]+/output/", p)]
    for name in all_jobs():
        patterns = job_list(name, "triggers.txt")
        if name not in picked and any(fnmatch.fnmatch(p, pat) for p in inputs for pat in patterns):
            picked.append(name)
    return picked


def downstream_only(direct, picked):
    """Jobs selected only as consumers of a selected job, not by a change to their own folder or triggers."""
    return [name for name in picked if name not in set(direct)]


def main():
    event, schedule = os.environ.get("EVENT"), os.environ.get("SCHEDULE") or ""
    sweep = event == "schedule" and schedule not in ("", DAILY_CRON)
    consumers = True
    if sweep:
        picked = for_changes(recent_changes())
    elif event == "schedule":
        picked = sorted(
            name for name in os.listdir("jobs")
            if not name.startswith("_") and runnable(name) and os.path.isfile(os.path.join("jobs", name, "DAILY"))
        )
    elif os.environ.get("EVENT") == "workflow_dispatch":
        picked = []
        for name in re.split(r"[\s,]+", os.environ.get("INPUT_JOB") or ""):
            name = name.strip().strip("/").removeprefix("jobs/")
            if not name:
                continue
            if not runnable(name):
                sys.exit(f"There is no job called '{name}'. It needs jobs/{name}/job.sh or job.py.")
            picked.append(name)
        if not picked:
            sys.exit("Type at least one job name.")
    else:
        # A push: only jobs whose own code changed, nothing downstream. The next sweep does the rest.
        picked = for_changes(changed_files(os.environ.get("BEFORE"), os.environ["AFTER"]), triggers=False)
        consumers = False

    direct = list(picked)
    try:
        picked = ordered(with_consumers(picked) if consumers else picked)
    except ValueError as exc:
        sys.exit(str(exc))
    downstream = downstream_only(direct, picked) if sweep else []
    print("Jobs to run:", ", ".join(picked) or "none")
    if downstream:
        print("Running only because a job they read changed:", ", ".join(downstream))
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"jobs={' '.join(picked)}\n")
        if downstream:
            fh.write(f"downstream={' '.join(downstream)}\n")


if __name__ == "__main__":
    main()
