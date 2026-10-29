"""Restore selected inputs while preserving unaudited dynamic job reads.

The non-cone bootstrap includes job code/data but omits output generations.
Two exact engineering-reviewed versions expand their declared closure and prior
outputs. Other or changed versions restore all jobs/ for compatibility.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import result_freshness as freshness

# Engineering-reviewed code/declaration closures only. A changed version or an
# unaudited job keeps historical jobs/ availability, including dynamic outputs.
# These are tree metadata fingerprints, not approval of scientific outputs.
NARROW_SIGNATURES = {
    "example-hello": "11168c38449395ac4700647d15f9a1b1341f0cf2a54ebf9fddea1031ef3f05a8",
    "early-ranger-transcriptions": "aa21dad4f0858cb2ed807f5942586cb5917504af3ce8a85976cdf5ae90c1b5cc",
}


def git(*args, input=None):
    return subprocess.run(["git", *args], input=input, capture_output=True, check=True).stdout


def tree_entries(ref, roots):
    """List tracked blob ids below literal roots, asking Git only for those roots."""
    if not roots:
        return {}
    specs = [":(literal)" + root for root in sorted(set(roots))]
    records = git("ls-tree", "-r", "-z", ref, "--", *specs)
    out = {}
    for record in records.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        if kind == "blob":
            out[raw_path.decode("utf-8")] = mode + ":" + oid
    return out


def literal_pattern(path):
    """Encode a tracked path as an exact non-cone sparse-checkout rule."""
    if "\n" in path or "\r" in path:
        raise ValueError(f"Sparse checkout cannot safely encode a newline path: {path!r}")
    escaped = path.replace("\\", "\\\\").replace("*", "\\*").replace("?", "\\?").replace("[", "\\[")
    trailing = len(escaped) - len(escaped.rstrip(" "))
    escaped = escaped.rstrip(" ") + "\\ " * trailing
    return "/" + escaped


def directory_pattern(path):
    """Select one declared directory subtree with a single non-cone rule."""
    return literal_pattern(path.rstrip("/")) + "/**"


def narrow_signature(name, ref="HEAD"):
    entries = tree_entries(ref, [f"jobs/{name}", "jobs/_lib"])
    entries = {p: value for p, value in entries.items()
               if not freshness.under(p, f"jobs/{name}/output")}
    return entries_digest(entries)


def fallback_jobs(names, ref="HEAD"):
    return {name: ("unaudited_job" if name not in NARROW_SIGNATURES else "audited_version_changed")
            for name in names
            if name not in NARROW_SIGNATURES or narrow_signature(name, ref) != NARROW_SIGNATURES[name]}


def input_closure(names, ref="HEAD"):
    """Return exact closure and per-job digest for a fixed selected-job list."""
    all_entries, by_job = {}, {}
    by_job_patterns = {}
    for name in names:
        if not freshness.NAME.fullmatch(name):
            raise ValueError(f"Invalid job name: {name!r}")
        # The runner moves the prior generation before starting; retain that
        # exact output and any job-local custody even though it is not an input
        # to the freshness manifest itself.
        own = tree_entries(ref, [f"jobs/{name}"])
        declared_scope = freshness.scope(name)
        declared = freshness.tracked_entries(ref, declared_scope)
        entries = {**own, **declared}
        by_job[name] = entries
        all_entries.update(entries)
        root_dirs = {f"jobs/{name}"}
        root_files = set()
        for root in declared_scope["roots"]:
            if root in entries:
                root_files.add(root)
            elif any(freshness.under(p, root) and p != root for p in entries):
                root_dirs.add(root)
        # Prefix rules cover complete declared directory roots. Keep exact
        # literal rules only for pattern-selected paths outside those roots.
        exact = {p for p in entries if not any(freshness.under(p, root) for root in root_dirs)}
        by_job_patterns[name] = ({directory_pattern(root) for root in root_dirs}
                                 | {literal_pattern(root) for root in root_files}
                                 | {literal_pattern(p) for p in exact})
    fallback = fallback_jobs(names, ref)
    if fallback:
        # Existing jobs dynamically enumerate outputs and import siblings that
        # their manifests do not name. Preserve the old availability until each
        # exact code/declaration version has had a complete read audit.
        historical = tree_entries(ref, ["jobs"])
        all_entries.update(historical)
        for name in fallback:
            by_job[name].update(historical)
            by_job_patterns[name].add("/jobs/**")
    return all_entries, by_job, by_job_patterns


def entries_digest(entries):
    """Fingerprint exact selected tracked object ids without reading blob bodies."""
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def materialized_bytes(paths):
    """Count bytes already materialized on disk; never ask Git to fetch for sizes."""
    total = 0
    for p in paths:
        path = Path(p)
        if path.is_symlink():
            total += len(os.readlink(path).encode())
        else:
            total += path.stat().st_size
    return total


def materialize(names, receipt=None):
    if not names:
        print("No selected jobs; checkout remains at runner bootstrap.")
        return {"schema": 1, "jobs": [], "path_count": 0, "blob_bytes": 0}
    sparse = subprocess.run(["git", "config", "--bool", "core.sparseCheckout"], capture_output=True)
    if sparse.stdout.strip() != b"true":
        raise RuntimeError("Expected the workflow's sparse checkout to be enabled")
    cone = subprocess.run(["git", "config", "--bool", "core.sparseCheckoutCone"], capture_output=True)
    if cone.stdout.strip() == b"true":
        raise RuntimeError("Expected non-cone sparse checkout; broad cone materialization is unsafe")
    entries, by_job, by_job_patterns = input_closure(names)
    paths = set(entries)
    patterns = sorted(set().union(*by_job_patterns.values()))
    if patterns:
        # `add` preserves the already-configured non-cone mode; it does not
        # expose a --no-cone switch on every supported Git version.
        git("sparse-checkout", "add", "--stdin", input=("\n".join(patterns) + "\n").encode())
    # Confirm selected tracked inputs reached the worktree. Sparse checkout may
    # leave unselected files as skip-worktree entries even after an add error.
    missing = [p for p in paths if not (Path(p).exists() or Path(p).is_symlink())]
    if missing:
        raise RuntimeError(f"Sparse checkout did not materialize {len(missing)} declared paths; first: {sorted(missing)[:5]}")
    total = materialized_bytes(paths)
    report = {
        "schema": 1,
        "base_commit": git("rev-parse", "HEAD").decode().strip(),
        "jobs": names,
        "compatibility_fallback_jobs": fallback_jobs(names),
        "path_count": len(paths),
        "sparse_pattern_count": len(patterns),
        "materialized_bytes": total,
        "input_objects_sha256": entries_digest(entries),
        "per_job": {name: {"path_count": len(selected), "sparse_pattern_count": len(by_job_patterns[name]),
                            "inputs_sha256": entries_digest(selected)}
                    for name, selected in by_job.items()},
    }
    if receipt:
        Path(receipt).parent.mkdir(parents=True, exist_ok=True)
        Path(receipt).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Selected input materialization: " + json.dumps(report, sort_keys=True), flush=True)
    return report


def main():
    names = os.environ.get("JOBS", "").split()
    receipt = os.environ.get("CHECKOUT_INPUT_RECEIPT", "oversized/runner-freshness/CHECKOUT_INPUTS.json")
    materialize(names, receipt)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"::error::Input materialization failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
