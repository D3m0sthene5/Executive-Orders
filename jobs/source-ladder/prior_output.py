"""Read a job's earlier results, so a new run adds to them instead of replacing them.

The GitHub runner deletes jobs/<name>/output/ before every run, and nothing
in its download cache survives between runs. These helpers read the last
committed copy of a job's output with read-only git (git show / git archive
of HEAD), or a plain folder (for example a full PC run the owner committed
under jobs/<name>/data/full_run/). Nothing here writes to git.
"""
from __future__ import annotations

import csv
import io
import json
import subprocess
import tarfile
from pathlib import Path


def _git(repo, args, timeout=600):
    try:
        # No line-ending conversion: the exact committed bytes (git archive would apply autocrlf).
        r = subprocess.run(["git", "-C", str(repo), "-c", "core.autocrlf=false", "-c", "core.eol=lf"] + args,
                           capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


class PriorOutput:
    """The files of an earlier output, from a folder or from git HEAD:<rel_dir>."""

    def __init__(self, label, folder=None, repo=None, rel_dir=None, ref="HEAD"):
        self.label = label
        self.folder = Path(folder) if folder else None
        self.repo, self.rel_dir = repo, (rel_dir or "").strip("/")
        self.ref = ref
        self._texts = None

    @classmethod
    def from_folder(cls, folder, label=None):
        return cls(label or f"folder {Path(folder).as_posix()}", folder=folder)

    @classmethod
    def from_git_head(cls, repo, rel_dir):
        return cls(f"git HEAD:{rel_dir}", repo=repo, rel_dir=rel_dir)

    @classmethod
    def from_git_ref(cls, repo, rel_dir, ref):
        import re
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError("A source import must pin a full commit SHA")
        return cls(f"git {ref}:{rel_dir}", repo=repo, rel_dir=rel_dir, ref=ref)

    def read(self, name):
        """Bytes of one file (e.g. 'SOURCES.jsonl'), or None if it is not there."""
        if self.folder is not None:
            p = self.folder / name
            return p.read_bytes() if p.is_file() else None
        if self.repo is None:
            return None
        return _git(self.repo, ["show", f"{self.ref}:{self.rel_dir}/{name}"])

    def jsonl(self, name):
        raw = self.read(name)
        if not raw:
            return []
        out = []
        for line in raw.decode("utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
        return out

    def csv_rows(self, name):
        raw = self.read(name)
        if not raw:
            return []
        return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))

    def texts(self, subdir="texts"):
        """{file name: bytes} for every file in <output>/<subdir>/ (read once)."""
        if self._texts is not None:
            return self._texts
        out = {}
        if self.folder is not None:
            d = self.folder / subdir
            if d.is_dir():
                for p in d.iterdir():
                    if p.is_file():
                        out[p.name] = p.read_bytes()
        elif self.repo is not None:
            raw = _git(self.repo, ["archive", "--format=tar", self.ref, f"{self.rel_dir}/{subdir}"])
            if raw:
                with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
                    for m in tar.getmembers():
                        if m.isfile():
                            fh = tar.extractfile(m)
                            if fh is not None:
                                out[m.name.rsplit("/", 1)[-1]] = fh.read()
        self._texts = out
        return out


class UnionPriorOutput:
    """Reconcile pinned acquisition generations; current quarantines take precedence."""

    def __init__(self, priors):
        self.priors = priors
        self.label = "union: " + "; ".join(p.label for p in priors)
        self.sources, self.results, self.owners = {}, {}, {}
        rejected = {(r.get("wanted_id"), r.get("sha256"))
                    for p in priors for r in p.jsonl("REJECTED_PRIOR_SOURCES.jsonl")}
        for prior in priors:
            rows = {r["wanted_id"]: r for r in prior.csv_rows("RESULTS.csv")}
            for wid, row in rows.items():
                self.results.setdefault(wid, row)
            for source in prior.jsonl("SOURCES.jsonl"):
                wid = source.get("wanted_id")
                if (wid not in rows or rows[wid].get("result") != "found" or wid in self.sources
                        or (wid, source.get("sha256")) in rejected):
                    continue
                self.sources[wid], self.results[wid] = source, rows[wid]
                if source.get("text_path"):
                    name = source["text_path"]
                    if name in self.owners and self.owners[name].read(name) != prior.read(name):
                        raise ValueError("Conflicting imported text bytes at " + name)
                    self.owners[name] = prior

    def csv_rows(self, name):
        if name != "RESULTS.csv":
            raise ValueError("Unsupported union CSV: " + name)
        return list(self.results.values())

    def jsonl(self, name):
        if name == "SOURCES.jsonl":
            return list(self.sources.values())
        result, seen = [], set()
        for prior in self.priors:
            for row in prior.jsonl(name):
                key = json.dumps(row, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    result.append(row)
                    if name == "REJECTED_PRIOR_SOURCES.jsonl" and row.get("preserved_text_path"):
                        self.owners.setdefault(row["preserved_text_path"], prior)
        return result

    def read(self, name):
        if name in self.owners:
            return self.owners[name].read(name)
        for prior in self.priors:
            raw = prior.read(name)
            if raw is not None:
                return raw
        return None
