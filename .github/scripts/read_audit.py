"""Quo Warranto: record what a job actually reads, and refuse results whose reads its declarations do not cover.

Named for the writ that asks by what warrant a franchise is exercised. Edward I's Quo Warranto inquiry
(1278) made every lord show the charter for each right he claimed. Here every repository read must show
the declaration (needs.txt, inputs.txt, triggers.txt, after.txt, references.txt, the job's own folder or
its library closure) that puts it inside the job's freshness scope (result_freshness.scope).

Why: freshness versions a result on its declared inputs. A declaration wider than the code's reads makes
any publish of an unrelated file invalidate the job (Repetita refused the tracker on 2026-11-07 because
``jobs/*/output/*.csv`` matched an unrelated table). A declaration narrower than the reads is worse: a
changed input is not seen and a stale result publishes. Narrowing is safe only if a too-narrow
declaration cannot publish. Quo Warranto makes that so for jobs that opt in with ``jobs/<name>/AUDIT_READS``:

* the runner starts ``job.py`` through ``read_audit.py run``, which installs a Python audit hook
  (PEP 578) before the job's first line and records every file opened for reading, every glob pattern,
  every directory listed, and every child process, in all threads;
* after a successful exit, ``check`` compares the record with ``result_freshness.scope(name)``:
  - an opened file must lie under a declared root or match a declared pattern;
  - a glob must be covered as a pattern, so files it would find later are versioned too: its literal
    prefix lies under a root, or a declared pattern matches the glob's own text (wildcards of the glob
    consumed by ``*`` of the declaration);
  - a directory listed outside any glob must lie under a root or be the literal prefix of a declared
    pattern (an approximation; stated);
  - a child Python process other than the job's own unit tests is not audited, so it is a violation;
    a git command's path arguments are reads;
* any violation turns the job's exit code into a failure: its outputs are not published, and
  ``READ_AUDIT.json`` names each undeclared read.

Reads outside the repository (system libraries, temporary files), the job's own output folder, its prior
output and cache, ``.git`` and compiled bytecode are not repository inputs and are ignored.

Usage (the runner does this): python3 read_audit.py run --record FILE -- JOB.py [ARGS...]
                               python3 read_audit.py check --job NAME --record FILE --report FILE
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import runpy
import sys
import threading
from pathlib import Path, PurePosixPath

SCHEMA = "quo-warranto/1"
WILD = set("*?[")


def _repo():
    return Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[2]).resolve()


class Recorder:
    def __init__(self, repo: Path):
        self.repo = repo
        self.lock = threading.Lock()
        self.opened, self.globs, self.listed, self.children = set(), set(), set(), []
        self.in_glob = 0

    def rel(self, p):
        try:
            if isinstance(p, int):
                return None
            path = Path(os.fsdecode(p))
            if not path.is_absolute():
                path = Path.cwd() / path
            path = Path(os.path.normpath(path))
            r = path.relative_to(self.repo)
        except (ValueError, TypeError):
            return None
        return r.as_posix()

    def hook(self, event, args):
        try:
            if event == "open":
                path, mode, flags = (list(args) + [None, None, None])[:3]
                if isinstance(mode, str) and any(c in mode for c in "wax+"):
                    return
                if mode is None and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
                    return
                r = self.rel(path)
                if r:
                    with self.lock:
                        self.opened.add(r)
            elif event in ("glob.glob", "glob.glob/2"):
                pattern, root = args[0], (args[2] if len(args) > 2 else None)
                base = Path(os.fsdecode(root)) if root is not None else None
                full = os.fsdecode(pattern) if base is None else str(base / os.fsdecode(pattern))
                self._glob(full)
            elif event in ("pathlib.Path.glob", "pathlib.Path.rglob"):
                base, pattern = args[0], os.fsdecode(args[1])
                if event == "pathlib.Path.rglob":
                    pattern = "**/" + pattern
                self._glob(str(Path(base) / pattern))
            elif event in ("os.listdir", "os.scandir"):
                r = self.rel(args[0] if args and args[0] is not None else ".")
                if r is not None:
                    with self.lock:
                        self.listed.add(r or ".")
            elif event == "subprocess.Popen":
                exe, argv = args[0], args[1]
                argv = [os.fsdecode(a) for a in argv] if isinstance(argv, (list, tuple)) else [os.fsdecode(argv)]
                with self.lock:
                    self.children.append({"executable": os.fsdecode(exe) if exe else None, "argv": argv,
                                          "cwd": self.rel(args[2]) if len(args) > 2 and args[2] else None})
        except Exception:  # an audit hook must never break the job; a missed read fails safe in check
            with self.lock:
                self.children.append({"hook_error": event})

    def _glob(self, full):
        p = Path(full)
        if not p.is_absolute():
            p = Path.cwd() / p
        try:
            r = PurePosixPath(os.path.normpath(p)).relative_to(self.repo.as_posix()).as_posix()
        except ValueError:
            return
        with self.lock:
            self.globs.add(r)

    def dump(self):
        return {"schema": SCHEMA, "opened": sorted(self.opened), "globs": sorted(self.globs),
                "listed": sorted(self.listed), "children": self.children}


def run(record, job, job_args):
    repo = _repo()
    rec = Recorder(repo)
    sys.addaudithook(rec.hook)
    sys.argv = [job, *job_args]
    sys.path.insert(0, str(Path(job).resolve().parent))
    code = 0
    try:
        runpy.run_path(job, run_name="__main__")
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        if not isinstance(e.code, (int, type(None))):
            print(e.code, file=sys.stderr)
    finally:
        Path(record).write_text(json.dumps(rec.dump(), indent=1) + "\n", encoding="utf-8")
    return code


# ---------------------------------------------------------------- check

def _under(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def _literal_prefix(pattern):
    parts = []
    for part in pattern.split("/"):
        if set(part) & WILD:
            break
        parts.append(part)
    return "/".join(parts)


def _pattern_ok(declared):
    return not (set(declared) & set("?["))


def ignored(path, name, prior=None):
    parts = path.split("/")
    if parts[0] in (".git", ".job-cache", "oversized") or "__pycache__" in parts or path.endswith(".pyc"):
        return True
    if _under(path, f"jobs/{name}/output") or (prior and _under(path, prior)):
        return True
    return False


def covered_file(path, scope):
    return any(_under(path, r) for r in scope["roots"]) or any(fnmatch.fnmatchcase(path, p) for p in scope["patterns"])


def covered_glob(glob, scope):
    prefix = _literal_prefix(glob)
    if prefix and any(_under(prefix, r) for r in scope["roots"]):
        return True
    return any(_pattern_ok(p) and fnmatch.fnmatchcase(glob, p) for p in scope["patterns"])


def covered_listing(d, scope):
    if any(_under(d, r) for r in scope["roots"]):
        return True
    return any(_under(_literal_prefix(p), d) or _literal_prefix(p) == d for p in scope["patterns"]
               if _literal_prefix(p))


def _glob_traverses(glob, d):
    """True if directory d is one the glob's own segments walk through (an ancestor of what it can match)."""
    gs, ds = glob.split("/"), d.split("/")

    def walk(i, j):
        if j == len(ds):
            return True
        if i == len(gs):
            return False
        if gs[i] == "**":
            return walk(i + 1, j) or walk(i, j + 1)
        return fnmatch.fnmatchcase(ds[j], gs[i]) and walk(i + 1, j + 1)
    return walk(0, 0)


def _python_child(c):
    exe = os.path.basename(c.get("executable") or (c.get("argv") or [""])[0])
    return exe.startswith("python") or (c.get("argv") and os.path.basename(c["argv"][0]).startswith("python"))


def _test_child(c):
    a = c.get("argv") or []
    return "-m" in a and a[a.index("-m") + 1:a.index("-m") + 2] == ["unittest"]


def check(name, record, scope=None, repo=None, prior=None):
    import importlib.util
    repo = Path(repo or _repo())
    if scope is None:
        spec = importlib.util.spec_from_file_location("result_freshness", Path(__file__).with_name("result_freshness.py"))
        rf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rf)
        cwd = os.getcwd()
        os.chdir(repo)
        try:
            scope = rf.scope(name)
        finally:
            os.chdir(cwd)
    prior = prior or os.environ.get("JOB_PRIOR_OUTPUT_DIR")
    if prior:
        try:
            prior = Path(prior).resolve().relative_to(repo).as_posix()
        except ValueError:
            prior = None
    v = []
    for p in record.get("opened", []):
        if not ignored(p, name, prior) and not covered_file(p, scope):
            v.append({"kind": "file", "path": p})
    enumerations = []
    for g in record.get("globs", []):
        if ignored(g, name, prior) or covered_glob(g, scope):
            continue
        # A bare name enumeration ("jobs/*") feeds the globs recorded under it; each of those is judged itself, and a
        # new directory with no matching file changes no read. Accept it only when every such glob is covered.
        parts = g.split("/")
        under = [h for h in record.get("globs", []) if h != g and h.startswith(_literal_prefix(g) + "/")]
        if parts[-1] == "*" and not (set(_literal_prefix(g)) & WILD) and len(parts) == len(_literal_prefix(g).split("/")) + 1 \
                and under and all(ignored(h, name, prior) or covered_glob(h, scope) for h in under):
            enumerations.append(g)
            continue
        v.append({"kind": "glob", "path": g})
    globs = record.get("globs", [])
    for d in record.get("listed", []):
        if d == "." or ignored(d, name, prior):
            continue
        # A directory a recorded glob traverses is judged by that glob.
        if any(_glob_traverses(g, d) for g in globs):
            continue
        if not covered_listing(d, scope):
            v.append({"kind": "listing", "path": d})
    for c in record.get("children", []):
        if c.get("hook_error"):
            v.append({"kind": "hook_error", "path": c["hook_error"]})
        elif _python_child(c) and not _test_child(c):
            v.append({"kind": "unaudited_python_child", "path": " ".join(c.get("argv") or [])[:200]})
        elif os.path.basename(c.get("executable") or (c.get("argv") or [""])[0]) == "git":
            for a in (c.get("argv") or [])[1:]:
                a = a.split(":", 1)[1] if a.startswith(("HEAD:", ":")) else a
                if "/" in a and not a.startswith("-") and (repo / a).exists() and not Path(a).is_absolute():
                    if not ignored(a, name, prior) and not covered_file(a.rstrip("/"), scope) \
                            and not covered_glob(a.rstrip("/") + "/*", scope):
                        v.append({"kind": "git_path", "path": a})
    return {"schema": SCHEMA, "job": name, "violations": v, "enumerations": enumerations,
            "opened": len(record.get("opened", [])),
            "globs": record.get("globs", []), "listed": len(record.get("listed", [])),
            "children": len(record.get("children", [])), "verdict": "covered" if not v else "undeclared_reads"}


def groups(record, name):
    """Opened repository files counted by folder (three path segments, four under jobs/*/output)."""
    out = {}
    for p in record.get("opened", []):
        if ignored(p, name):
            continue
        parts = p.split("/")
        depth = 4 if parts[0] == "jobs" and len(parts) > 3 and parts[2] in ("output", "data") else 3
        key = "/".join(parts[:min(depth, len(parts) - 1)]) or p
        out[key] = out.get(key, 0) + 1
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["run"]:
        ap = argparse.ArgumentParser(prog="read_audit.py run")
        ap.add_argument("--record", required=True)
        i = argv.index("--")
        a = ap.parse_args(argv[1:i])
        return run(a.record, argv[i + 1], argv[i + 2:])
    ap = argparse.ArgumentParser(prog="read_audit.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--job", required=True)
    c.add_argument("--record", required=True)
    c.add_argument("--report", required=True)
    a = ap.parse_args(argv)
    record = json.loads(Path(a.record).read_text(encoding="utf-8"))
    rep = check(a.job, record)
    rep["groups"] = groups(record, a.job)
    if os.environ.get("QUO_WARRANTO_MODE") == "report":
        # Report mode derives a declaration: keep every read so a narrower one can be proven against it.
        rep["opened_paths"] = sorted(p for p in record.get("opened", []) if not ignored(p, a.job))
    Path(a.report).write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    # A compact read summary in the job log, so a declaration can be derived from a run whose artifacts expire.
    for g, n in sorted(rep["groups"].items()):
        print(f"Quo Warranto: {a.job} opened {n} file(s) under {g}", flush=True)
    for g in rep["globs"]:
        print(f"Quo Warranto: {a.job} glob {g}", flush=True)
    print(f"Quo Warranto: {a.job} verdict {rep['verdict']} ({len(rep['violations'])} undeclared)", flush=True)
    for x in rep["violations"][:50]:
        print(f"::error::Quo Warranto: {a.job} read {x['kind']} {x['path']} outside its declared inputs", flush=True)
    return 0 if rep["verdict"] == "covered" else 4


if __name__ == "__main__":
    sys.exit(main())
