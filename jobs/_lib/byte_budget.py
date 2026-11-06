"""Byte budget: refuse to push or commit more bytes than the repository can carry.

The repository sits near GitHub's 10 GB cap, so every push and every job run is measured:

  push     new blob bytes on HEAD relative to a base ref (git rev-list --objects BASE..HEAD | git cat-file
           --batch-check), default 25 MiB, and no new blob over the per-file limit
  output   the size of a job's output/ folder, default 20 MiB in total and 5 MiB per file

Usage
  py -I jobs/_lib/byte_budget.py                         # push check against origin/main
  py -I jobs/_lib/byte_budget.py --base origin/main --max-push-mib 25
  py -I jobs/_lib/byte_budget.py --job ptolemy-custody   # jobs/ptolemy-custody/output
  py -I jobs/_lib/byte_budget.py --output-dir path/to/output --max-output-mib 20 --max-file-mib 5
  py -I jobs/_lib/byte_budget.py --no-push --job selden-statutes --write-json BUDGET.json

Exit status: 0 within budget, 1 over budget, 2 could not measure. Jobs can import `measure_dir` and
`write_budget_json` to enforce the limit themselves before writing. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

MIB = 1024 * 1024
DEFAULT_PUSH_MIB = 25
DEFAULT_OUTPUT_MIB = 20
DEFAULT_FILE_MIB = 5


def _git(repo, args, input_bytes=None):
    r = subprocess.run(["git", "-C", str(repo)] + args, input=input_bytes, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.decode('utf-8', 'replace').strip()[:300]}")
    return r.stdout


def new_blobs(repo, base, head="HEAD"):
    """[(size, path, sha)] for every blob reachable from head and not from base (the bytes a push would add)."""
    listing = _git(repo, ["rev-list", "--objects", f"{base}..{head}"])
    if not listing.strip():
        return []
    paths = {}
    lines = []
    for line in listing.decode("utf-8", "replace").splitlines():
        sha, _, rest = line.partition(" ")
        if sha:
            paths.setdefault(sha, rest)
            lines.append(sha)
    out = _git(repo, ["cat-file", "--batch-check=%(objecttype) %(objectsize) %(objectname)"],
               ("\n".join(lines) + "\n").encode())
    blobs = []
    for row in out.decode("utf-8", "replace").splitlines():
        parts = row.split()
        if len(parts) == 3 and parts[0] == "blob":
            blobs.append((int(parts[1]), paths.get(parts[2], ""), parts[2]))
    return blobs


def push_report(repo, base, max_push, max_file, head="HEAD"):
    blobs = new_blobs(repo, base, head)
    total = sum(s for s, _, _ in blobs)
    big = sorted([b for b in blobs if b[0] > max_file], reverse=True)
    problems = []
    if total > max_push:
        problems.append(f"push adds {total / MIB:.2f} MiB of new blobs, over the {max_push / MIB:g} MiB budget")
    for size, path, _ in big[:10]:
        problems.append(f"new blob {path or '(unnamed)'} is {size / MIB:.2f} MiB, over the {max_file / MIB:g} MiB per-file limit")
    return {"kind": "push", "base": base, "head": head, "new_blobs": len(blobs), "bytes": total,
            "largest": [{"path": p, "bytes": s} for s, p, _ in sorted(blobs, reverse=True)[:5]],
            "limit_bytes": max_push, "file_limit_bytes": max_file, "ok": not problems, "problems": problems}


def measure_dir(folder, exclude=()):
    """(total_bytes, file_count, [(size, relative path)] largest first) for every file under folder.
    `exclude` names sub-folders (relative to folder) left out, for example a legacy raw/ awaiting migration."""
    folder = Path(folder)
    files = []
    skip = tuple(e.strip("/") + "/" for e in exclude)
    if folder.is_dir():
        for p in folder.rglob("*"):
            if p.is_file() and not p.is_symlink():
                rel = p.relative_to(folder).as_posix()
                if not rel.startswith(skip):
                    files.append((p.stat().st_size, rel))
    files.sort(reverse=True)
    return sum(s for s, _ in files), len(files), files


def output_report(folder, max_total, max_file, exclude=()):
    total, count, files = measure_dir(folder, exclude)
    problems = []
    if total > max_total:
        problems.append(f"{folder} holds {total / MIB:.2f} MiB in {count} files, over the {max_total / MIB:g} MiB budget")
    for size, rel in [f for f in files if f[0] > max_file][:10]:
        problems.append(f"{rel} is {size / MIB:.2f} MiB, over the {max_file / MIB:g} MiB per-file limit")
    return {"kind": "output", "folder": str(folder), "files": count, "bytes": total, "excluded": list(exclude),
            "largest": [{"path": r, "bytes": s} for s, r in files[:5]], "limit_bytes": max_total,
            "file_limit_bytes": max_file, "ok": not problems, "problems": problems}


def write_budget_json(path, report):
    """Write the BUDGET.json a job commits beside its output (totals only)."""
    Path(path).write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fail when a push or a job output folder is over its byte budget.")
    ap.add_argument("--repo", default=".", help="git worktree to measure (default: current directory)")
    ap.add_argument("--base", default="origin/main", help="base ref for the push check")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--no-push", action="store_true", help="skip the push check")
    ap.add_argument("--max-push-mib", type=float, default=DEFAULT_PUSH_MIB)
    ap.add_argument("--job", action="append", default=[], help="job name: measures jobs/NAME/output (repeatable)")
    ap.add_argument("--output-dir", action="append", default=[], help="folder to measure (repeatable)")
    ap.add_argument("--max-output-mib", type=float, default=DEFAULT_OUTPUT_MIB)
    ap.add_argument("--max-file-mib", type=float, default=DEFAULT_FILE_MIB)
    ap.add_argument("--exclude", action="append", default=[], help="sub-folder of each output folder to leave out")
    ap.add_argument("--write-json", default=None, help="write the reports as JSON to this path")
    a = ap.parse_args(argv)
    repo = Path(a.repo).resolve()
    reports = []
    try:
        if not a.no_push:
            reports.append(push_report(repo, a.base, int(a.max_push_mib * MIB), int(a.max_file_mib * MIB), a.head))
        folders = [repo / "jobs" / j / "output" for j in a.job] + [Path(d) for d in a.output_dir]
        for f in folders:
            reports.append(output_report(f, int(a.max_output_mib * MIB), int(a.max_file_mib * MIB), a.exclude))
    except (RuntimeError, OSError) as exc:
        print(f"byte_budget: cannot measure: {exc}", file=sys.stderr)
        return 2
    for r in reports:
        label = r.get("folder") or f"{r['base']}..{r['head']}"
        print(f"{'OK  ' if r['ok'] else 'OVER'} {r['kind']} {label}: {r['bytes'] / MIB:.2f} MiB "
              f"of {r['limit_bytes'] / MIB:g} MiB ({r.get('new_blobs', r.get('files'))} "
              f"{'new blobs' if r['kind'] == 'push' else 'files'})")
        for p in r["problems"]:
            print("     " + p)
    if a.write_json:
        write_budget_json(a.write_json, {"reports": reports, "ok": all(r["ok"] for r in reports)})
    return 0 if all(r["ok"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
