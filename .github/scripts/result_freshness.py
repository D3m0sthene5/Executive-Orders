"""Bind runner results to the code and declared repository inputs actually read.

Git object IDs avoid rereading unchanged corpus files. Modified/untracked inputs
are hashed from disk, including outputs generated earlier in this invocation.
External servers and undeclared reads cannot be versioned by this guard.

jobs/<name>/inputs.txt declares additional repository reads as fnmatch patterns
(like triggers.txt, * spans directory separators). It versions additions as
well as existing files. Use needs.txt for literal directory roots. The prepare
command materializes matching tracked sparse inputs before a job starts.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

MANIFEST = "RUNNER_INPUTS.json"
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def git(*args, input=None):
    return subprocess.run(["git", *args], input=input, capture_output=True, check=True).stdout


def lines(path):
    p = Path(path)
    if not p.exists():
        return []
    return [s for line in p.read_text(encoding="utf-8").splitlines()
            if (s := line.split("#", 1)[0].strip())]


def scope(name):
    if not NAME.fullmatch(name):
        raise ValueError(f"Invalid job name: {name!r}")
    roots = [f"jobs/{name}", "jobs/_lib", ".github/scripts", ".github/workflows/run-jobs.yml"]
    roots += lines(f"jobs/{name}/needs.txt")
    predecessors = lines(f"jobs/{name}/after.txt")
    if any(not NAME.fullmatch(dep) for dep in predecessors):
        raise ValueError(f"Invalid after.txt dependency for {name}")
    roots += [f"jobs/{dep}/output" for dep in predecessors]
    patterns = lines(f"jobs/{name}/triggers.txt") + lines(f"jobs/{name}/inputs.txt")
    # This job explicitly enumerates the corpus, rather than just after.txt.
    if name == "daily-digest":
        patterns += ["jobs/*/output/SUMMARY.json", "jobs/*/output/STATUS.json", "HANDOFF/notes-*.md"]
    for value in roots + patterns:
        p = PurePosixPath(value)
        if p.is_absolute() or ".." in p.parts or "\\" in value or ":" in value:
            raise ValueError(f"Unsafe input declaration: {value!r}")
    return {"roots": sorted(set(p.rstrip("/") for p in roots)),
            "patterns": sorted(set(patterns)), "exclude": f"jobs/{name}/output"}


def under(path, root):
    return path == root or path.startswith(root + "/")


def select(entries, declared):
    return {p: value for p, value in entries.items()
            if not under(p, declared["exclude"])
            and (any(under(p, root) for root in declared["roots"])
                 or any(fnmatch.fnmatchcase(p, pat) for pat in declared["patterns"]))}


def tree(ref):
    entries = {}
    for record in git("ls-tree", "-r", "-z", ref).split(b"\0"):
        if record:
            header, path = record.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            entries[path.decode("utf-8")] = mode + ":" + oid
    return entries


def prepare(name):
    """Acquire declared inputs without expanding unrelated sparse directories."""
    declared = scope(name)
    sparse = subprocess.run(["git", "config", "--bool", "core.sparseCheckout"], capture_output=True)
    if sparse.stdout.strip() != b"true":
        return
    directories = set()
    for record in git("ls-files", "-t", "-z").split(b"\0"):
        if not record:
            continue
        tag, raw = record.split(b" ", 1)
        path = raw.decode("utf-8")
        if tag == b"S" and select({path: ""}, declared):
            directories.add(str(PurePosixPath(path).parent))
    if directories:
        # --stdin keeps a broad dynamic catalogue below Windows/Unix argv
        # limits. Cone mode intentionally includes each matched parent folder.
        git("sparse-checkout", "add", "--stdin", input=("\n".join(sorted(directories)) + "\n").encode())
        print(f"Materialized declared input directories for {name}: {len(directories)}")


def working(declared=None):
    entries = {}
    forced = []
    for record in git("ls-files", "--stage", "-t", "-z").split(b"\0"):
        if not record:
            continue
        header, path = record.split(b"\t", 1)
        tag, mode, oid, stage = header.decode().split()
        p = path.decode("utf-8")
        if declared is not None and not select({p: ""}, declared):
            continue
        if stage != "0":
            raise ValueError(f"Unmerged input: {p}")
        if tag == "S":
            if not Path(p).exists() and not Path(p).is_symlink():
                raise ValueError(f"Declared input is absent from sparse checkout: {p}; run result_freshness.py prepare before capture")
            forced.append(p)
        entries[p] = mode + ":" + oid
    changed = git("ls-files", "--modified", "--deleted", "--others", "--exclude-standard", "-z")
    paths = sorted(set([p.decode("utf-8") for p in changed.split(b"\0") if p] + forced))
    if declared is not None:
        paths = [p for p in paths if select({p: ""}, declared)]
    files = []
    for p in paths:
        path = Path(p)
        if path.is_symlink():
            data = os.readlink(path).encode()
            entries[p] = "120000:" + hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        elif path.is_file():
            if "\n" in p or '"' in p:
                raise ValueError(f"Unsupported input filename: {p!r}")
            files.append(p)
        else:
            entries.pop(p, None)
    if files:
        hashes = git("hash-object", "--stdin-paths", input=("\n".join(files) + "\n").encode()).decode().splitlines()
        for p, oid in zip(files, hashes, strict=True):
            mode = entries.get(p, "100755:" if os.name != "nt" and os.access(p, os.X_OK) else "100644:").split(":")[0]
            entries[p] = mode + ":" + oid
    return entries


def digest(entries):
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def output(entries, name):
    return {p: v for p, v in entries.items() if under(p, f"jobs/{name}/output")}


def capture(name, destination):
    declared = scope(name)
    inputs = working(declared)
    base = git("rev-parse", "HEAD").decode().strip()
    manifest = {"schema": 1, "job": name, "base_commit": base,
                "run_url": os.environ.get("RUN_URL") or
                f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
                "scope": declared, "inputs_sha256": digest(inputs), "inputs": inputs,
                "base_output_sha256": digest(output(tree(base), name))}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check(ref, names, report):
    latest = tree(ref)
    candidate = working({"roots": [f"jobs/{name}/output" for name in names], "patterns": [], "exclude": "\0"})
    problems, manifests, bases = [], {}, {}
    for name in names:
        p = Path("jobs") / name / "output" / MANIFEST
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            if m["schema"] != 1 or m["job"] != name or digest(m["inputs"]) != m["inputs_sha256"]:
                raise ValueError("Invalid provenance manifest")
            declared = m["scope"]
            if (not isinstance(m["inputs"], dict)
                    or not all(isinstance(declared[k], list) for k in ("roots", "patterns"))
                    or declared["exclude"] != f"jobs/{name}/output"
                    or not isinstance(m["base_output_sha256"], str)):
                raise ValueError("Invalid provenance scope or baseline")
            base = m["base_commit"]
            if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40,64}", base):
                raise ValueError("Invalid provenance base commit")
            if base not in bases:
                bases[base] = tree(base)
            if digest(output(bases[base], name)) != m["base_output_sha256"]:
                raise ValueError("Provenance output baseline does not match its commit")
            manifests[name] = m
        except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
            problems.append({"job": name, "reason": "missing_or_invalid_manifest", "detail": str(exc)})
            continue
        branch_output = digest(output(latest, name))
        if branch_output not in (m["base_output_sha256"], digest(output(candidate, name))):
            problems.append({"job": name, "reason": "concurrent_output_advanced",
                             "detail": "The branch's output changed after this run's checkout. Rerun on the current branch."})
    # Each consumer may have read a prior job's candidate or a later job's base
    # generation. Never substitute a later-produced candidate into that earlier
    # snapshot. The whole-output concurrency check above remains authoritative.
    generations = {}
    run_order = {name: position for position, name in enumerate(names)}
    for name, m in manifests.items():
        expected, projected = m["inputs"], dict(latest)
        generations[name] = {}
        for producer in names:
            produced = output(candidate, producer)
            baseline = output(bases[m["base_commit"]], producer)
            captured = output(expected, producer)
            candidate_inputs = select(produced, m["scope"])
            base_inputs = select(baseline, m["scope"])
            if not (captured or candidate_inputs or base_inputs):
                continue
            generation = "same_run_candidate"
            chosen = produced
            if captured != candidate_inputs:
                if (run_order[producer] > run_order[name] and captured == base_inputs
                        and output(latest, producer) == baseline):
                    chosen, generation = baseline, "captured_base"
                else:
                    generation = "unmatched"
            generations[name][producer] = generation
            projected = {p: v for p, v in projected.items() if not under(p, f"jobs/{producer}/output")}
            projected.update(chosen)
        expected, actual = m["inputs"], select(projected, m["scope"])
        changed = sorted(p for p in expected.keys() | actual.keys() if expected.get(p) != actual.get(p))
        if changed:
            problems.append({"job": name, "reason": "inputs_changed", "captured_inputs_sha256": m["inputs_sha256"],
                             "branch_inputs_sha256": digest(actual), "changed_path_count": len(changed),
                             "changed_paths": [{"path": p, "captured": expected.get(p), "branch": actual.get(p)} for p in changed]})
    result = {"schema": 1, "result": "rejected" if problems else "fresh", "branch_commit": git("rev-parse", ref).decode().strip(),
              "jobs": names, "problems": problems, "input_generations": generations,
              "action": "Rerun these jobs on the current branch; retained outputs were not published." if problems else "Publish only while this branch commit remains current."}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if problems:
        # The workflow's artifact-upload step precedes commit, so its summary
        # and log are the durable locations for commit-time rejection details.
        rendered = json.dumps(result, indent=2)
        print("::error::Runner results rejected as stale. " + result["action"])
        print(rendered)
        if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n### Runner freshness rejection\n\n```json\n" + rendered + "\n```\n")
        return 3
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquire = sub.add_parser("prepare")
    acquire.add_argument("job")
    cap = sub.add_parser("capture")
    cap.add_argument("job")
    cap.add_argument("destination", type=Path)
    verify = sub.add_parser("check")
    verify.add_argument("ref")
    verify.add_argument("report", type=Path)
    verify.add_argument("jobs", nargs="+")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.job)
        return 0
    if args.command == "capture":
        capture(args.job, args.destination)
        return 0
    return check(args.ref, args.jobs, args.report)


if __name__ == "__main__":
    sys.exit(main())
