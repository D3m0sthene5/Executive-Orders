"""Refuse a merge that carries job outputs generated on another branch (Justinian, 2026-11-06).

A push to a pull-request branch runs that branch's changed jobs, and the runner commits their
outputs to the branch with STATUS.json "branch": "<that branch>". Merged as is, main then holds
outputs that no run on main produced (on 2026-11-06, 30 jobs' STATUS.json on main named another
branch). This check lists every jobs/*/output/STATUS.json that the pull request adds or changes
and whose "branch" is not the merge target, and fails with the command that restores the
target's outputs; the runner rebuilds them on the target after the merge.

    python .github/scripts/output_branch_check.py --base origin/main --target main
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def violations(base, head, target):
    changed = git("diff", "--name-only", "--diff-filter=AM", f"{base}...{head}").splitlines()
    found = []
    for path in changed:
        if not fnmatch.fnmatchcase(path, "jobs/*/output/STATUS.json") or path.count("/") != 3:
            continue
        try:
            status = json.loads(git("show", f"{head}:{path}"))
        except (subprocess.CalledProcessError, ValueError):
            found.append((path, "unreadable"))
            continue
        branch = status.get("branch") if isinstance(status, dict) else None
        if branch != target:
            found.append((path, branch))
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True, help="the merge target as fetched, e.g. origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--target", required=True, help="the target branch name recorded by its runs, e.g. main")
    args = ap.parse_args(argv)
    found = violations(args.base, args.head, args.target)
    if not found:
        print(f"No job output in this pull request was generated outside {args.target}.")
        return 0
    jobs = sorted({p.split("/")[1] for p, _ in found})
    print(f"::error::This pull request carries job outputs generated outside {args.target}:")
    for path, branch in found:
        print(f"  {path}: branch {branch!r}")
    print(f"Restore the target's outputs (the runner rebuilds them on {args.target} after the merge):")
    print("  git checkout " + args.base + " -- " + " ".join(f"jobs/{j}/output" for j in jobs))
    print("A job that is new in this pull request has no target output: remove its output folder with git rm -r.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
