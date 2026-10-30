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
import os
from pathlib import Path, PurePosixPath

DEFAULT_IDS = ("EO:254", "EO:2171", "EO:4354")
# DEFAULT_IDS remains available to callers reproducing the original three-case
# experiment. Ordinary selection now follows effective claims and associations.
MAX_ARTIFACTS = 8
ROOTS = ("ProQuest Pre-1937 Orders/", "research/pre-1937-sources/ProQuest Pre-1937 Orders/")
FRAGMENTS = "jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl"
MAX_FILE_BYTES = 8_000_000
MAX_TOTAL_BYTES = 24_000_000
MAX_INPUT_BYTES = 32_000_000
HEX = re.compile(r"[0-9a-f]{64}\Z")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(path, *, input_hashes=None, repo=None, numbered=False):
    if not path.is_file():
        return
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("oversized metadata: " + str(path))
    # Bound each metadata file, not the growing claims corpus. Stream both the
    # parse and provenance hash; unrelated claims must not consume a shared
    # allowance that prevents the three cited inputs from being considered.
    digest, total = hashlib.sha256(), 0
    with path.open("rb") as stream:
        number = 0
        while line := stream.readline(MAX_INPUT_BYTES + 1):
            number += 1
            total += len(line)
            if total > MAX_INPUT_BYTES:
                raise ValueError("oversized metadata: " + str(path))
            digest.update(line)
            decoded = line.decode("utf-8-sig" if number == 1 else "utf-8")
            if decoded.strip():
                row = json.loads(decoded)
                if not isinstance(row, dict):
                    raise ValueError("metadata row is not an object")
                yield (number, row) if numbered else row
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


def git(repo, *args, input=None):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30).stdout


def restore(repo, rel, digest, remaining, commit, *, audit=None):
    audit = audit if audit is not None else {}
    dest = confined(repo, rel)
    # A locally present file must also have an allowed, pinned repository path.
    entries = [x for x in git(repo, "ls-tree", "-z", commit, "--", rel).split(b"\0") if x]
    if len(entries) != 1:
        return "not_in_pinned_tree", 0
    meta, path = entries[0].split(b"\t", 1)
    mode, kind, oid = meta.split()
    if path.decode() != rel or mode not in (b"100644", b"100755") or kind != b"blob":
        return "not_regular_blob", 0
    audit["git_blob"] = oid.decode()
    if dest.exists():
        if not dest.is_file() or dest.stat().st_size > MAX_FILE_BYTES:
            return "existing_file_refused", 0
        if dest.stat().st_size > remaining:
            return "deferred_byte_budget", 0
        with dest.open("rb") as stream:
            raw = stream.read(min(MAX_FILE_BYTES, remaining) + 1)
        if len(raw) > MAX_FILE_BYTES or len(raw) > remaining:
            return "existing_file_changed_during_read", 0
        if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
            return "lfs_bytes_not_materialized", len(raw)
        if sha(raw) != digest or not raw.startswith(b"%PDF-"):
            return "existing_hash_mismatch", len(raw)
        if git(repo, "hash-object", "--stdin", input=raw).strip() != oid:
            return "existing_bytes_not_pinned_blob", len(raw)
        return "already_held", len(raw)
    # Resolve an exact tracked blob, never an arbitrary git expression from input.
    present = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", oid.decode()],
                             env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    audit["git_object_present_before_read"] = present.returncode == 0
    audit["git_object_fetch_attempted"] = present.returncode != 0
    size = int(git(repo, "cat-file", "-s", oid.decode()))
    if size > MAX_FILE_BYTES:
        return "byte_budget_hold", 0
    if size > remaining:
        return "deferred_byte_budget", 0
    raw = git(repo, "cat-file", "blob", oid.decode())
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return "lfs_bytes_not_materialized", size
    if len(raw) != size or sha(raw) != digest or not raw.startswith(b"%PDF-"):
        return "blob_hash_or_format_mismatch", size
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Recheck confinement after directory creation; no overwrite of local work.
    confined(repo, rel)
    with dest.open("xb") as stream:
        stream.write(raw)
    return "restored_exact_blob", size


def fingerprint(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def effective_references(repo, pins):
    # Reuse the checker's exact source-field convention. Last physical record in
    # filename/line order wins, just as checker.main and tracker.build select.
    from checker import SOURCE_KEYS, SOURCE_LIST_KEYS, walk
    effective = {}
    for path in sorted((repo / "research/readiness/claims").glob("*.jsonl"), key=lambda p: (p.name, str(p))):
        for number, row in rows(path, input_hashes=pins, repo=repo, numbered=True):
            iid = row.get("instrument_id")
            if not isinstance(iid, str):
                continue
            refs = []
            for field, key, value, _ in walk(row):
                selected = [(field, value)] if key in SOURCE_KEYS and isinstance(value, dict) else []
                if key in SOURCE_LIST_KEYS and isinstance(value, list):
                    selected = [(f"{field}[{n}]", v) for n, v in enumerate(value) if isinstance(v, dict)]
                for field, ref in selected:
                    raw = ref.get("sha256") or ref.get("local_file_sha256")
                    digest = raw.strip().lower() if isinstance(raw, str) else ""
                    if HEX.fullmatch(digest):
                        refs.append({"field": field, "sha256": digest,
                                     "source_instrument_id": ref.get("instrument_id")})
            effective[iid] = {"claim_key": f"{path.relative_to(repo).as_posix()}:{number}",
                              "claim_sha256": fingerprint(row), "references": refs}
    return effective


def materialize(repo, out_dir, ids=None, *, max_artifacts=MAX_ARTIFACTS,
                max_total_bytes=MAX_TOTAL_BYTES, resume=None):
    repo, out = Path(repo).resolve(), Path(out_dir)
    if type(max_artifacts) is not int or not 1 <= max_artifacts <= MAX_ARTIFACTS:
        raise ValueError("invalid artifact batch bound")
    if type(max_total_bytes) is not int or not 1 <= max_total_bytes <= MAX_TOTAL_BYTES:
        raise ValueError("invalid invocation byte bound")
    ids = tuple(dict.fromkeys(ids)) if ids is not None else None
    pins, receipts, errors, artifacts = {}, [], [], []
    selection_sha, next_cursor, used, attempted = None, None, 0, 0
    try:
        commit = git(repo, "rev-parse", "HEAD").decode().strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    try:
        effective = effective_references(repo, pins)
        if ids is not None:
            effective = {iid: row for iid, row in effective.items() if iid in ids}
        source = repo / FRAGMENTS
        if not source.is_file():
            raise ValueError("missing Pinakes association metadata")
        if source.is_file():
            if source.stat().st_size > MAX_INPUT_BYTES:
                raise ValueError("replica metadata byte bound exceeded")
            pins[FRAGMENTS] = sha(source.read_bytes())
        candidates, path_hashes = {}, {}
        for row in rows(source):
            iid, data = row.get("instrument_id"), row.get("data")
            if not isinstance(iid, str) or not isinstance(data, dict):
                continue
            if (row.get("kind") != "original_representation" or row.get("produced_by") != "pinakes-proquest-ingest"
                    or data.get("acceptable_as_original") is not False
                    or data.get("grade") != "archival_replica_scan_pending_codebook"):
                continue
            digest, rel = data.get("sha256"), data.get("file")
            digest = digest.strip().lower() if isinstance(digest, str) else ""
            if not HEX.fullmatch(digest):
                continue
            if isinstance(rel, str):
                path_hashes.setdefault(rel, set()).add(digest)
            if iid in effective:
                matches = [r for r in effective[iid]["references"] if r["sha256"] == digest]
            else:
                matches = []
            if matches:
                confined(repo, rel)
                item = candidates.setdefault(digest, {"sha256": digest, "paths": set(), "claims": {}})
                item["paths"].add(rel)
                item["claims"][iid] = {**effective[iid], "references": matches}
        selected = []
        for digest, item in sorted(candidates.items()):
            paths = sorted(item.pop("paths"))
            conflict = (len(paths) != 1 or any(len(path_hashes[p]) != 1 for p in paths)
                        or any(r.get("source_instrument_id") not in (None, iid)
                               for iid, c in item["claims"].items() for r in c["references"]))
            selected.append({**item, "path": paths[0], "association_paths": paths,
                             "association_conflict": conflict})
        selected.sort(key=lambda r: (r["path"], r["sha256"]))
        selection_sha = fingerprint({"commit": commit, "input_sha256": pins, "selection": selected})
        offset = 0
        if resume is not None:
            if (not isinstance(resume, dict) or resume.get("selection_sha256") != selection_sha
                    or type(resume.get("next_index")) is not int
                    or not 0 <= resume["next_index"] <= len(selected)):
                raise ValueError("resume selection changed or cursor invalid")
            offset = resume["next_index"]
        for n, item in enumerate(selected):
            audit, size = {}, 0
            if n < offset:
                state = "before_cursor_not_reverified"
            elif next_cursor is not None or attempted >= max_artifacts:
                state = "deferred_batch_bound"
                if next_cursor is None:
                    next_cursor = {"selection_sha256": selection_sha, "next_index": n}
            elif item["association_conflict"]:
                state = "conflicting_identity_path_or_hash"
                attempted += 1
            else:
                attempted += 1
                try:
                    if commit is None:
                        raise ValueError("no pinned Git commit available")
                    state, size = restore(repo, item["path"], item["sha256"], max_total_bytes - used, commit, audit=audit)
                    used += size
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    state = "unavailable:" + type(exc).__name__
                if state == "deferred_byte_budget":
                    next_cursor = {"selection_sha256": selection_sha, "next_index": n}
            artifacts.append({**item, "state": state, "bytes_read": size, **audit})
            for iid, claim in sorted(item["claims"].items()):
                receipts.append({"instrument_id": iid, "path": item["path"], "sha256": item["sha256"],
                                 "state": state, **claim})
        for iid in ids or ():
            if not any(r["instrument_id"] == iid for r in receipts):
                receipts.append({"instrument_id": iid, "state": "no_matching_cited_replica"})
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    result = {"schema": "eo-proquest-materialization/2", "commit": commit, "input_sha256": pins,
              "selection_sha256": selection_sha, "next_cursor": next_cursor,
              "bounds": {"max_artifacts": max_artifacts, "max_artifact_bytes": MAX_FILE_BYTES,
                         "max_invocation_bytes": max_total_bytes}, "bytes_read": used,
              "artifacts_attempted": attempted, "artifacts": artifacts,
              "receipts": receipts, "errors": errors, "new_source_acquisitions": 0,
              "git_fetch_note": "Exact retained objects may be fetched; transport/pack bytes are not measured.",
              "legal_effect": "none; ordinary checker must verify"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "PROQUEST_MATERIALIZATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
