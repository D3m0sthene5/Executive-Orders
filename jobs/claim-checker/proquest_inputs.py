"""Restore narrowly selected, cited ProQuest Git blobs for the ordinary checker.

No website acquisition, LFS download, source grading, or readiness decisions.
Git may fetch a missing blob from the configured repository in a partial clone.
Existing files are never overwritten. Every restored byte is hash-checked again
by the ordinary source checker; this module emits only materialization receipts.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

DEFAULT_IDS = ("EO:254", "EO:2171", "EO:4354")
ROOTS = ("ProQuest Pre-1937 Orders/", "research/pre-1937-sources/ProQuest Pre-1937 Orders/")
FRAGMENTS = "jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl"
MAX_FILE_BYTES = 8_000_000
MAX_TOTAL_BYTES = 24_000_000
MAX_INPUT_BYTES = 32_000_000
HEX = re.compile(r"[0-9a-f]{64}\Z")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(path, *, input_hashes=None, repo=None):
    if not path.is_file():
        return
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("oversized metadata: " + str(path))
    # Bound each metadata file, not the growing claims corpus. Stream both the
    # parse and provenance hash; unrelated claims must not consume a shared
    # allowance that prevents the three cited inputs from being considered.
    digest, total = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while line := stream.readline(MAX_INPUT_BYTES + 1):
            total += len(line)
            if total > MAX_INPUT_BYTES:
                raise ValueError("oversized metadata: " + str(path))
            digest.update(line)
            if line.strip():
                row = json.loads(line.decode("utf-8"))
                if not isinstance(row, dict):
                    raise ValueError("metadata row is not an object")
                yield row
    if input_hashes is not None:
        input_hashes[str(path.relative_to(repo))] = digest.hexdigest()


def hashes(value):
    if isinstance(value, dict):
        for key in ("sha256", "local_file_sha256"):
            digest = value.get(key)
            if isinstance(digest, str) and HEX.fullmatch(digest):
                yield digest
        for child in value.values():
            yield from hashes(child)
    elif isinstance(value, list):
        for child in value:
            yield from hashes(child)


def confined(repo, rel):
    if not isinstance(rel, str) or "\\" in rel:
        raise ValueError("invalid source path")
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts or not rel.startswith(ROOTS) or p.suffix.lower() != ".pdf":
        raise ValueError("source path outside ProQuest roots")
    dest = repo.joinpath(*p.parts)
    if any((repo.joinpath(*p.parts[:i])).is_symlink() for i in range(1, len(p.parts) + 1)):
        raise ValueError("symlink source path refused")
    dest.resolve().relative_to(repo.resolve())
    return dest


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30).stdout


def restore(repo, rel, digest, remaining, commit):
    dest = confined(repo, rel)
    if dest.exists():
        if not dest.is_file() or dest.stat().st_size > MAX_FILE_BYTES:
            return "existing_file_refused", 0
        raw = dest.read_bytes()
        if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
            return "lfs_bytes_not_materialized", 0
        return ("already_held" if sha(raw) == digest and raw.startswith(b"%PDF-") else "existing_hash_mismatch"), 0
    # Resolve an exact tracked blob, never an arbitrary git expression from input.
    entry = git(repo, "ls-tree", "-z", commit, "--", rel).split(b"\0")
    entries = [x for x in entry if x]
    if len(entries) != 1:
        return "not_in_pinned_tree", 0
    meta, path = entries[0].split(b"\t", 1)
    mode, kind, oid = meta.split()
    if path.decode() != rel or mode not in (b"100644", b"100755") or kind != b"blob":
        return "not_regular_blob", 0
    size = int(git(repo, "cat-file", "-s", oid.decode()))
    if size > MAX_FILE_BYTES or size > remaining:
        return "byte_budget_hold", 0
    raw = git(repo, "cat-file", "blob", oid.decode())
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return "lfs_bytes_not_materialized", 0
    if len(raw) != size or sha(raw) != digest or not raw.startswith(b"%PDF-"):
        return "blob_hash_or_format_mismatch", 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Recheck confinement after directory creation; no overwrite of local work.
    confined(repo, rel)
    with dest.open("xb") as stream:
        stream.write(raw)
    return "restored_exact_blob", size


def materialize(repo, out_dir, ids=DEFAULT_IDS):
    repo, out = Path(repo).resolve(), Path(out_dir)
    ids = tuple(dict.fromkeys(ids))
    if len(ids) > 3:
        raise ValueError("bounded repair accepts at most three identities")
    cited = {iid: set() for iid in ids}
    pins, receipts, errors = {}, [], []
    try:
        commit = git(repo, "rev-parse", "HEAD").decode().strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    try:
        for path in sorted((repo / "research/readiness/claims").glob("*.jsonl")):
            for row in rows(path, input_hashes=pins, repo=repo):
                if row.get("instrument_id") in cited:
                    cited[row["instrument_id"]].update(hashes(row))
        source = repo / FRAGMENTS
        if source.is_file():
            if source.stat().st_size > MAX_INPUT_BYTES:
                raise ValueError("replica metadata byte bound exceeded")
            pins[FRAGMENTS] = sha(source.read_bytes())
        candidates = []
        for row in rows(source):
            iid, data = row.get("instrument_id"), row.get("data")
            if iid not in cited or not isinstance(data, dict):
                continue
            if (row.get("kind") != "original_representation" or row.get("produced_by") != "pinakes-proquest-ingest"
                    or data.get("acceptable_as_original") is not False
                    or data.get("grade") != "archival_replica_scan_pending_codebook"):
                continue
            digest, rel = data.get("sha256"), data.get("file")
            if digest in cited[iid]:
                confined(repo, rel)
                candidates.append((iid, rel, digest))
        candidates = sorted(set(candidates))
        if len({(p, h) for _, p, h in candidates}) > 3:
            raise ValueError("more than three distinct scan versions; explicit review required")
        if len({p for _, p, _ in candidates}) != len({(p, h) for _, p, h in candidates}):
            raise ValueError("conflicting hashes for the same scan path")
        used, done = 0, {}
        for iid, rel, digest in candidates:
            key = (rel, digest)
            if key not in done:
                try:
                    if commit is None:
                        raise ValueError("no pinned Git commit available")
                    state, size = restore(repo, rel, digest, MAX_TOTAL_BYTES - used, commit)
                    used += size
                    done[key] = state
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    done[key] = "unavailable:" + type(exc).__name__
            receipts.append({"instrument_id": iid, "path": rel, "sha256": digest, "state": done[key]})
        for iid in ids:
            if not any(r["instrument_id"] == iid for r in receipts):
                receipts.append({"instrument_id": iid, "state": "no_matching_cited_replica"})
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    result = {"schema": "eo-proquest-materialization/1", "commit": commit, "input_sha256": pins,
              "receipts": receipts, "errors": errors, "legal_effect": "none; ordinary checker must verify"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "PROQUEST_MATERIALIZATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
