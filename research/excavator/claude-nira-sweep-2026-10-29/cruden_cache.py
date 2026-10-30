"""Disposable source-bound candidate features for Cruden, never evidence or legal findings.

Every invocation reads and hashes all held bytes twice. The cache saves only
decimal runs and a fixed literal prefix flag; final matching uses source text.
The envelope digest detects accidental corruption, not a malicious cache writer.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

SCHEMA = "cruden-features/v1"
ALGORITHM = "utf8-replace-universal-newlines;unicode-decimal-runs;lower-prefix/v1"
CODE_PREFIX = "code of fair competition for the "


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def normalized(raw):
    # Exactly Path.read_text(encoding="utf-8", errors="replace") newline handling.
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


class SnapshotChanged(RuntimeError):
    pass


class Snapshot:
    def __init__(self, repo, discover):
        self.repo = Path(repo).resolve()
        self.discover = discover
        self.started = time.perf_counter()
        self.compiler_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self.stats = {"cache_state": "miss", "cache_errors": [], "bytes_read": 0,
                      "candidate_bytes_read": 0, "validation_bytes_read": 0,
                      "reused_sources": 0, "recomputed_sources": 0}
        cache_root = Path(os.environ.get("CRUDEN_CACHE_DIR", str(Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "cruden")))
        self.cache_path = cache_root / hashlib.sha256(str(self.repo).encode()).hexdigest()[:24] / "features.json"
        t = time.perf_counter()
        prior = self._load_cache()
        self.stats["cache_load_seconds"] = time.perf_counter() - t
        self.paths = list(discover())
        self.sources = []
        build_seconds = 0.0
        t = time.perf_counter()
        for path in self.paths:
            rel = path.relative_to(self.repo).as_posix()
            try:
                raw = self.read_raw(path)
            except OSError as exc:
                self.sources.append({"path": rel, "sha256": None, "bytes": None,
                                     "error": f"{type(exc).__name__}: {exc}"})
                continue
            self.stats["bytes_read"] += len(raw)
            sha = hashlib.sha256(raw).hexdigest()
            old = prior.get(rel)
            if old and old.get("sha256") == sha and old.get("bytes") == len(raw):
                record = old
                self.stats["reused_sources"] += 1
            else:
                ft = time.perf_counter()
                text = normalized(raw)
                record = {"path": rel, "sha256": sha, "bytes": len(raw),
                          "digits": sorted(set(re.findall(r"\d+", text))),
                          "code_prefix": CODE_PREFIX in text.lower()}
                build_seconds += time.perf_counter() - ft
                self.stats["recomputed_sources"] += 1
            self.sources.append(record)
        self.stats["source_read_hash_features_seconds"] = time.perf_counter() - t
        self.stats["feature_build_seconds"] = build_seconds
        self.payload = {"schema": SCHEMA, "algorithm": ALGORITHM, "compiler_sha256": self.compiler_sha256,
                        "repo": str(self.repo), "sources": self.sources}
        self.snapshot_sha256 = digest(self.payload)
        self.changed = self.snapshot_sha256 != getattr(self, "prior_digest", None)
        t = time.perf_counter()
        self.coverage = self._coverage()
        self.stats["coverage_seconds"] = time.perf_counter() - t
        self.stats["construction_seconds"] = time.perf_counter() - self.started

    def read_raw(self, path):
        return path.read_bytes()

    def _load_cache(self):
        try:
            envelope = json.loads(self.cache_path.read_text(encoding="utf-8"))
            payload = envelope["payload"]
            if envelope["sha256"] != digest(payload):
                raise ValueError("payload digest mismatch")
            if (payload["schema"], payload["algorithm"], payload["repo"]) != (SCHEMA, ALGORITHM, str(self.repo)):
                raise ValueError("schema, algorithm or repository mismatch")
            if payload["compiler_sha256"] != self.compiler_sha256:
                raise ValueError("feature compiler implementation changed")
            records = payload["sources"]
            if not isinstance(records, list):
                raise ValueError("sources must be a list")
            by_path = {}
            for record in records:
                if not isinstance(record["path"], str) or record["path"] in by_path:
                    raise ValueError("invalid or duplicate source path")
                if record.get("sha256") is not None:
                    if (not isinstance(record["digits"], list)
                            or any(not isinstance(n, str) or not re.fullmatch(r"\d+", n) for n in record["digits"])
                            or not isinstance(record["code_prefix"], bool)):
                        raise ValueError("invalid candidate features")
                by_path[record["path"]] = record
            self.prior_digest = envelope["sha256"]
            self.stats["cache_state"] = "verified"
            return by_path
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
            self.stats["cache_state"] = "rebuild"
            self.stats["cache_errors"].append(f"read: {type(exc).__name__}: {exc}")
            return {}

    def candidates(self, numbers=(), codes=False):
        wanted = set(numbers)
        for record in self.sources:
            if record["sha256"] is not None and (wanted.intersection(record["digits"]) or (codes and record["code_prefix"])):
                yield record

    def read_source(self, record):
        path = self.repo / record["path"]
        try:
            raw = self.read_raw(path)
        except OSError as exc:
            raise SnapshotChanged(f"source became unreadable during search: {record['path']}: {exc}") from exc
        self.stats["candidate_bytes_read"] += len(raw)
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise SnapshotChanged(f"source changed during search: {record['path']}; retry")
        return normalized(raw)

    def verify(self):
        """Reject edits/additions/deletions even in previously noncandidate sources."""
        t = time.perf_counter()
        if list(self.discover()) != self.paths:
            raise SnapshotChanged("held text inventory changed during search; retry")
        for record, path in zip(self.sources, self.paths):
            try:
                raw = self.read_raw(path)
            except OSError as exc:
                error = f"{type(exc).__name__}: {exc}"
                if record["sha256"] is None and record.get("error") == error:
                    continue
                raise SnapshotChanged(f"source became unreadable during verification: {record['path']}; retry") from exc
            self.stats["validation_bytes_read"] += len(raw)
            if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
                raise SnapshotChanged(f"source changed during verification: {record['path']}; retry")
        if list(self.discover()) != self.paths:
            raise SnapshotChanged("held text inventory changed during verification; retry")
        self.stats["final_validation_seconds"] = time.perf_counter() - t
        if self.changed:
            self._save_cache()

    def _save_cache(self):
        t = time.perf_counter()
        temp = None
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.cache_path.parent, prefix=".features-", mode="w", encoding="utf-8", delete=False) as stream:
                temp = Path(stream.name)
                json.dump({"sha256": self.snapshot_sha256, "payload": self.payload}, stream, ensure_ascii=True, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.cache_path)
        except (OSError, ValueError) as exc:
            self.stats["cache_errors"].append(f"write: {type(exc).__name__}: {exc}")
        finally:
            if temp is not None:
                try:
                    temp.unlink(missing_ok=True)
                except OSError:
                    pass
        self.stats["cache_write_seconds"] = time.perf_counter() - t

    def _coverage(self):
        present = {r["path"] for r in self.sources}
        omitted, excluded, errors = [], [], []
        tracked_status = "available"
        try:
            result = subprocess.run(["git", "-C", str(self.repo), "ls-files", "-z", "--", "jobs"], check=True, capture_output=True)
            for name in result.stdout.decode("utf-8", errors="replace").split("\0"):
                if not re.fullmatch(r"jobs/[^/]+/output/texts/.+\.txt", name):
                    continue
                if name.startswith("jobs/clause-drafts/"):
                    excluded.append(name)
                elif name not in present:
                    omitted.append(name)
        except (OSError, subprocess.SubprocessError) as exc:
            tracked_status = f"unavailable: {type(exc).__name__}: {exc}"
        # Path.rglob can suppress directory errors. Independently disclose them.
        try:
            providers = sorted((self.repo / "jobs").iterdir())
        except OSError as exc:
            providers = []
            errors.append(f"jobs: {type(exc).__name__}: {exc}")
        for provider in providers:
            folder = provider / "output/texts"
            try:
                folder.stat()
            except (FileNotFoundError, NotADirectoryError):
                continue
            except OSError as exc:
                errors.append(f"{folder}: {type(exc).__name__}: {exc}")
                continue
            def onerror(exc):
                errors.append(f"{getattr(exc, 'filename', folder)}: {type(exc).__name__}: {exc}")
            for directory, _, files in os.walk(folder, onerror=onerror):
                if provider.name == "clause-drafts":
                    excluded.extend((Path(directory) / f).relative_to(self.repo).as_posix() for f in files if f.endswith(".txt"))
        return {"scope": "Exactly held_texts(): sorted jobs/*/output/texts recursive *.txt, excluding clause-drafts; no acquisition or legal completeness claim.",
                "tracked_inventory_status": tracked_status, "tracked_not_discovered": sorted(set(omitted)),
                "excluded_clause_drafts": sorted(set(excluded)), "directory_errors": errors,
                "unreadable_sources": [r for r in self.sources if r["sha256"] is None],
                "discovered_count": len(self.sources), "readable_count": sum(r["sha256"] is not None for r in self.sources),
                "source_bytes": sum(r["bytes"] or 0 for r in self.sources)}

    def details(self):
        return {"snapshot_sha256": self.snapshot_sha256, "cache_path": str(self.cache_path),
                "algorithm": ALGORITHM, "compiler_sha256": self.compiler_sha256,
                "coverage": self.coverage, "timings": dict(self.stats),
                "sources": [{k: r[k] for k in ("path", "sha256", "bytes")} for r in self.sources],
                "integrity_notice": "Cache digest detects accidental corruption. All source bytes are hashed before and after matching; concurrent changes observed in either pass cause refusal."}


def original_span(text, lowered, start, end):
    """Map lower() indices to covering original normalized-text characters."""
    if len(text) == len(lowered):
        return start, end
    offset, first = 0, None
    for i, char in enumerate(text):
        following = offset + len(char.lower())
        if first is None and following > start:
            first = i
        if following >= end:
            return first if first is not None else i, i + 1
        offset = following
    return len(text), len(text)
