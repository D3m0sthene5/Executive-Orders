"""Decide which jobs/<name>/ folders the runner should run.

A push runs every job whose folder had a file changed outside output/.
A manual run runs the one job that was named. Folders starting with "_" (the
template) are never run. The result goes to the step output "jobs" as a
space-separated list.
"""

import os
import re
import subprocess
import sys

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ZERO = "0" * 40
RUNNER_FILES = {".github/workflows/run-jobs.yml"}
SMOKE_TEST = "example-hello"


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


def main():
    if os.environ.get("EVENT") == "workflow_dispatch":
        name = (os.environ.get("INPUT_JOB") or "").strip().strip("/")
        name = name.removeprefix("jobs/")
        if not runnable(name):
            sys.exit(f"There is no job called '{name}'. It needs jobs/{name}/job.sh or job.py.")
        picked = [name]
    else:
        picked = []
        for path in changed_files(os.environ.get("BEFORE"), os.environ["AFTER"]):
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

    print("Jobs to run:", ", ".join(picked) or "none")
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"jobs={' '.join(picked)}\n")


if __name__ == "__main__":
    main()
