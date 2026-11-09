"""Ariadne: learn which tracked files each job really reads, so its checkout can later follow that thread.

Named for Ariadne's thread, which let Theseus walk only the passages he needed through the labyrinth and
find his way back. Today every job without a hand-audited input list (all but three of ~106) restores all of
jobs/** before it runs: 165,000 paths and 10.8 GB for a Kean run whose job takes 7 seconds, about 3.5 minutes
per station on every run. Hand audits did not scale, so Ariadne measures instead.

Shadow mode (this file): on Linux runners with ARIADNE_TRACE=1, run_jobs.py runs the job under strace, which
follows every child process (Python, bash, git, cat) and sees every open, existence check and directory
listing, including ones Python's own audit hooks miss (os.path.exists has no audit event, `python -I` ignores
PYTHONPATH hooks). Afterwards Ariadne writes oversized/runner-freshness/ariadne/<job>.json:

- closure: the tracked files the job read or checked and the direct files of each directory it listed,
  plus required_directories (subdirectories a listing showed, which must exist but need not be full),
  with counts and bytes against what this station materialized;
- silent misses: tracked paths the job looked for that the sparse checkout had left out (skip-worktree),
  and listed directories that were missing tracked children. Each is a place where today's fallback may
  already give a job less than the repository holds; the runner prints a warning, it does not fail the job.

Nothing here changes what a job reads, writes or publishes. The record rides the station bundle into the
run's 90-day oversized download; it is never committed. A later, separate change may restore only a learned
closure for a job whose code signature (materialize_job_inputs.narrow_signature) matches stable records,
with the same trace as referee: any silent miss would discard that run's outputs and rerun it in full.

Switches: ARIADNE_TRACE=1 enables tracing; ARIADNE_SKIP_JOBS="a b" leaves named jobs untraced;
ARIADNE_KEEP_TRACE=1 keeps the compressed trace beside the record. If strace or gzip is missing, or strace
cannot trace on this machine, jobs run exactly as before.

What tracing must not change, and how it is kept out:
- sudo: a non-root tracer stops setuid from working, so a job whose scripts mention sudo runs untraced.
- detached children: strace -f waits for every traced process. Git's automatic gc detaches and can run for
  minutes in a blobless clone full of lazily fetched packs, so traced jobs run with gc.auto=0 and
  maintenance.auto=false (an ephemeral runner never needs either; outputs do not depend on them).
- disk: the trace streams through gzip -1, and a trace over ARIADNE_MAX_TRACE_MB compressed is not parsed.
- outcome: wrap() and finish() never raise, and run_jobs.py records after writing STATUS.json, so parsing
  does not count toward the job's recorded duration. Tracing itself slows a job; the record keeps both its
  traced duration and the last untraced one, so the cost is measured, not assumed.
"""
from __future__ import annotations

import bisect
import gzip
import json
import os
from pathlib import Path
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

SCHEMA = 1
RECORDS = Path("oversized/runner-freshness/ariadne")
TRACE_SET = "%file,getdents,getdents64,fchdir,clone,clone3,fork,vfork"
STRACE_FLAGS = ["-f", "-qq", "--seccomp-bpf", "-y", "-e", "signal=none", "-e", "trace=" + TRACE_SET]
LIST_LIMIT = 200  # silent misses and listed directories kept in the record; counts are always complete
MAX_TRACE_MB = 1024  # compressed; larger traces are not parsed
PRIVILEGED = re.compile(r"\bsudo\b")
NO_DETACHED_GIT = (("gc.auto", "0"), ("maintenance.auto", "false"))

# Path argument position for each syscall Ariadne reads; *at variants take a directory fd just before it.
OPENS = {"open": 0, "creat": 0, "openat": 1, "openat2": 1}
PROBES = {"stat": 0, "lstat": 0, "access": 0, "readlink": 0, "statfs": 0, "execve": 0,
          "newfstatat": 1, "fstatat64": 1, "statx": 1, "faccessat": 1, "faccessat2": 1, "readlinkat": 1,
          "execveat": 1}
LISTINGS = {"getdents", "getdents64"}
FORKS = {"clone", "clone3", "fork", "vfork"}
ABSENT = {"ENOENT", "ENOTDIR"}
SKIPPED_ROOTS = (".git", ".job-cache", "oversized")

_CALL = re.compile(r"^(\d+)\s+([a-z_0-9]+)\((.*)\)\s+=\s+(.*)$")
_UNFINISHED = re.compile(r"^(\d+)\s+(.*) <unfinished \.\.\.>$")
_RESUMED = re.compile(r"^(\d+)\s+<\.\.\. ([a-z_0-9]+) resumed>(.*)$")
_ESCAPE = re.compile(rb"\\(x[0-9a-fA-F]{2}|[0-7]{1,3}|.)")
_SIMPLE = {b"n": b"\n", b"t": b"\t", b"r": b"\r", b"v": b"\v", b"f": b"\f", b"\\": b"\\", b'"': b'"'}
_preflight = {}


# ------------------------------------------------------------------ running under the tracer

def privileged(folder):
    """True when a job's own scripts mention sudo, which cannot work under a non-root tracer."""
    folder = Path(folder)
    for path in folder.rglob("*"):
        rel = path.relative_to(folder).parts
        if rel[0] in {"output", "data", "work"} or path.suffix not in {".sh", ".py"} or not path.is_file():
            continue
        try:
            if PRIVILEGED.search(path.read_text(encoding="utf-8", errors="replace")):
                return True
        except OSError:
            return True
    return False


def sink(path):
    """strace -o target that streams the trace through gzip -1 into path."""
    return "|exec gzip -1 > " + shlex.quote(str(path))


def tracer(name, folder=None):
    """The strace executable to wrap this job with, or None to run it untraced."""
    if os.environ.get("ARIADNE_TRACE") != "1" or not sys.platform.startswith("linux"):
        return None
    if name in os.environ.get("ARIADNE_SKIP_JOBS", "").split():
        return None
    if folder is not None and privileged(folder):
        print(f"[Ariadne] {name} uses sudo, which cannot run under the tracer; it runs untraced.", flush=True)
        return None
    exe = shutil.which("strace")
    if not exe or not shutil.which("gzip"):
        return None
    if exe not in _preflight:
        # Refuse to wrap a job unless this exact command line traces a child cleanly here.
        probe = [exe, *STRACE_FLAGS, "-o", sink(os.devnull), "--", sys.executable, "-c",
                 "import os; os.listdir('.')"]
        try:
            _preflight[exe] = subprocess.run(probe, capture_output=True, timeout=60).returncode == 0
        except (OSError, subprocess.SubprocessError):
            _preflight[exe] = False
        if not _preflight[exe]:
            print("[Ariadne] strace cannot trace on this runner; jobs run untraced.", flush=True)
    return exe if _preflight[exe] else None


def wrap(args, name, token, folder=None, env=None):
    """Return (command, environment, trace path); all unchanged, trace None, when tracing is off."""
    try:
        exe = tracer(name, folder)
        if not exe:
            return args, env, None
        where = Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()) / "ariadne" / token
        where.mkdir(parents=True, exist_ok=True)
        trace = where / (name + ".strace.gz")
        traced_env = dict(os.environ if env is None else env)
        count = int(traced_env.get("GIT_CONFIG_COUNT") or 0)
        for i, (key, value) in enumerate(NO_DETACHED_GIT, start=count):
            traced_env[f"GIT_CONFIG_KEY_{i}"], traced_env[f"GIT_CONFIG_VALUE_{i}"] = key, value
        traced_env["GIT_CONFIG_COUNT"] = str(count + len(NO_DETACHED_GIT))
        return [exe, *STRACE_FLAGS, "-o", sink(trace), "--", *args], traced_env, trace
    except Exception as exc:
        print(f"[Ariadne] {name}: tracing not set up ({type(exc).__name__}: {exc}); it runs untraced.", flush=True)
        return args, env, None


# ------------------------------------------------------------------ reading strace output

def unquote(text):
    """Decode one strace C-style string body (without the quotes) to a str."""
    def one(match):
        code = match.group(1)
        if code[:1] == b"x" and len(code) == 3:
            return bytes([int(code[1:], 16)])
        if code[:1].isdigit():
            return bytes([int(code, 8) & 0xFF])
        return _SIMPLE.get(code, b"\\" + code)
    return _ESCAPE.sub(one, text.encode("utf-8", "surrogateescape")).decode("utf-8", "surrogateescape")


def split_args(text):
    """Split a syscall argument list at top-level commas, keeping strings, structs and <fd paths> whole."""
    args, depth, start, i, quoted = [], 0, 0, 0, False
    while i < len(text):
        char = text[i]
        if quoted:
            if char == "\\":
                i += 1
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif char == "<" and i and (text[i - 1].isalnum() or text[i - 1] == "_"):
            end = text.find(">", i)
            if end < 0:
                break
            i = end
        elif char == "," and depth == 0:
            args.append(text[start:i].strip())
            start = i + 1
        i += 1
    tail = text[start:].strip()
    if tail:
        args.append(tail)
    return args


def string_arg(arg):
    """The decoded value of a quoted string argument, or None (strace may append ... when truncating)."""
    if len(arg) >= 2 and arg[0] == '"':
        end = arg.rfind('"')
        if end > 0:
            return unquote(arg[1:end])
    return None


def fd_path(arg):
    """The absolute path strace -y printed for a descriptor argument (3</a/b> or AT_FDCWD</a>), else None."""
    match = re.match(r"^(?:\d+|AT_FDCWD)<(/.*)>$", arg)
    return unquote(match.group(1)) if match else None


def events(lines, start_cwd):
    """Yield (kind, absolute path, ok, errno) for each file access in strace -f -y output.

    kind is "read", "probe" or "list"; writes, sockets and unresolved relative paths are skipped.
    Each process's working directory is followed through chdir/fchdir and inherited across forks.
    """
    cwd, pending = {}, {}
    for raw in lines:
        line = raw.rstrip("\n")
        unfinished = _UNFINISHED.match(line)
        if unfinished:
            pending[unfinished.group(1)] = unfinished.group(2)
            continue
        resumed = _RESUMED.match(line)
        if resumed and resumed.group(1) in pending:
            line = resumed.group(1) + " " + pending.pop(resumed.group(1)) + resumed.group(3)
        call = _CALL.match(line)
        if not call:
            continue
        pid, name, arg_text, result = call.groups()
        result = result.strip()
        ok = not result.startswith("-")
        errno = result.split()[1] if not ok and len(result.split()) > 1 else None
        here = cwd.get(pid, start_cwd)
        if name in FORKS:
            if ok and result.split("<")[0].isdigit():
                cwd[result.split("<")[0]] = here
            continue
        args = split_args(arg_text)
        if name == "chdir":
            target = string_arg(args[0]) if args else None
            if ok and target is not None:
                cwd[pid] = posixpath.normpath(posixpath.join(here, target))
            continue
        if name == "fchdir":
            target = fd_path(args[0]) if args else None
            if ok and target:
                cwd[pid] = posixpath.normpath(target)
            continue
        if name in LISTINGS:
            target = fd_path(args[0]) if args else None
            if ok and target:
                yield "list", posixpath.normpath(target), True, None
            continue
        if name in OPENS:
            index, kind = OPENS[name], "read"
            flags = args[index + 1] if len(args) > index + 1 else ""
            if name == "creat" or re.search(r"\bO_(WRONLY|TRUNC|CREAT)\b", flags) and "O_RDWR" not in flags:
                continue
            if "O_DIRECTORY" in flags:
                kind = "probe"
        elif name in PROBES:
            index, kind = PROBES[name], "probe"
        else:
            continue
        if len(args) <= index:
            continue
        path = string_arg(args[index])
        if not path:
            continue  # empty path with AT_EMPTY_PATH: the descriptor itself, already counted when opened
        if not path.startswith("/"):
            base = here
            if index:
                dirfd = args[index - 1]
                if dirfd != "AT_FDCWD":
                    base = fd_path(dirfd)
                    if base is None:
                        continue
            path = posixpath.join(base, path)
        yield kind, posixpath.normpath(path), ok, errno


def accesses(lines, repo, own_output):
    """Collect repository-relative reads, probes, listings and absent lookups from a trace."""
    root = posixpath.normpath(str(repo).replace("\\", "/"))
    found = {"read": set(), "probe": set(), "list": set(), "absent": set()}
    outside = 0
    for kind, path, ok, errno in events(lines, root):
        if path != root and not path.startswith(root + "/"):
            outside += 1
            continue
        rel = path[len(root) + 1:]
        top = rel.split("/", 1)[0]
        if top in SKIPPED_ROOTS or rel == own_output or rel.startswith(own_output + "/"):
            continue
        if ok:
            found[kind].add(rel)
        elif errno in ABSENT:
            found["absent"].add(rel)
    found["outside_repository_events"] = outside
    return found


# ------------------------------------------------------------------ judging against the checkout

def index_flags(repo):
    """Map each tracked path to its `git ls-files -t` tag (H present, S left out by sparse checkout)."""
    raw = subprocess.run(["git", "ls-files", "-t", "-z"], cwd=repo, capture_output=True, check=True).stdout
    flags = {}
    for record in raw.split(b"\0"):
        if len(record) > 2:
            flags[record[2:].decode("utf-8", "surrogateescape")] = record[:1].decode()
    return flags


def under(paths, folder):
    """Tracked paths below folder, from a sorted list."""
    prefix = folder.rstrip("/") + "/" if folder else ""
    start = bisect.bisect_left(paths, prefix)
    end = bisect.bisect_left(paths, prefix + "\U0010ffff")
    return paths[start:end]


def judge(found, flags, repo, own_output):
    """What a narrow checkout would need, and lookups the current checkout silently failed.

    Returns (closure files, directories that must exist, tracked files per listed directory, misses).
    Listing a directory needs its direct tracked files and the existence of its tracked subdirectories;
    a walk lists each subdirectory in turn, so deeper files join only when the job actually goes there.
    """
    ordered = sorted(flags)
    skipped = sorted(p for p, tag in flags.items() if tag == "S")
    closure, directories, listed_closure, misses = set(), set(), {}, []
    for path in found["read"] | found["probe"]:
        if path in flags:
            closure.add(path)
    for folder in sorted(found["list"]):
        entries, missing_children = set(), set()
        for path in under(ordered, folder):
            if path == own_output or path.startswith(own_output + "/"):
                continue
            rest = path[len(folder) + 1:] if folder else path
            entries.add(rest.split("/", 1)[0])
            if "/" in rest:
                directories.add(posixpath.join(folder, rest.split("/", 1)[0]))
            else:
                closure.add(path)
        listed_closure[folder] = len(entries)
        for path in under(skipped, folder):
            child = (path[len(folder) + 1:] if folder else path).split("/", 1)[0]
            if not os.path.lexists(Path(repo, folder, child)):
                missing_children.add(child)
        if missing_children:
            misses.append({"kind": "listing_incomplete", "path": folder,
                           "missing_children": len(missing_children),
                           "examples": sorted(missing_children)[:5]})
    for path in sorted(found["absent"]):
        if flags.get(path) == "S":
            misses.append({"kind": "file_left_out", "path": path})
            closure.add(path)
        elif under(skipped, path):
            misses.append({"kind": "folder_left_out", "path": path, "tracked_below": len(under(ordered, path))})
            directories.add(path)
    return closure, directories, listed_closure, misses


def disk_bytes(repo, paths):
    total = 0
    for path in paths:
        try:
            total += os.lstat(Path(repo, path)).st_size
        except OSError:
            pass
    return total


def areas(paths, depth=3):
    """Closure files counted by their folder, cut to the first `depth` path parts (largest 30)."""
    counts = {}
    for path in paths:
        key = "/".join(path.split("/")[:-1][:depth]) or "."
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:30])


def trace_lines(trace, state):
    """Lines of a trace (gzip or plain); a truncated gzip tail ends the lines and sets state['truncated']."""
    opener = gzip.open if str(trace).endswith(".gz") else open
    with opener(trace, "rt", encoding="utf-8", errors="surrogateescape") as stream:
        try:
            for line in stream:
                yield line
        except (EOFError, OSError):
            state["truncated"] = True


def record(name, repo, trace, exit_code, seconds, usual_seconds):
    """Summarize one job's trace into its Ariadne record and print the result; returns the record."""
    repo = Path(repo)
    own_output = f"jobs/{name}/output"
    limit = float(os.environ.get("ARIADNE_MAX_TRACE_MB") or MAX_TRACE_MB)
    size_mb = Path(trace).stat().st_size / 1e6
    if size_mb > limit:
        print(f"[Ariadne] {name}: trace is {size_mb:,.0f} MB compressed, over {limit:,.0f} MB; not parsed.",
              flush=True)
        return None
    state = {"truncated": False}
    found = accesses(trace_lines(trace, state), repo, own_output)
    flags = index_flags(repo)
    closure, directories, listed_closure, misses = judge(found, flags, repo, own_output)
    materialized = sum(1 for tag in flags.values() if tag == "H")
    station = {}
    receipt = repo / "oversized/runner-freshness/CHECKOUT_INPUTS.json"
    if receipt.is_file():
        try:
            data = json.loads(receipt.read_text(encoding="utf-8"))
            station = {key: data.get(key) for key in ("path_count", "materialized_bytes", "jobs")}
        except (OSError, ValueError):
            pass
    try:
        import materialize_job_inputs
        signature = materialize_job_inputs.narrow_signature(name)
    except Exception as exc:  # the record is still useful without it
        signature = "unavailable: " + type(exc).__name__
    exe = shutil.which("strace")
    version = subprocess.run([exe, "-V"], capture_output=True, text=True).stdout.splitlines()[:1] if exe else []
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
    result = {
        "schema": SCHEMA, "job": name, "input_commit": head, "narrow_signature": signature,
        "exit_code": exit_code, "job_seconds": round(seconds, 1), "last_untraced_success_seconds": usual_seconds,
        "tracer": version[0] if version else "strace", "trace_truncated": state["truncated"],
        "trace_compressed_mb": round(size_mb, 1),
        "tracked_files": len(flags), "materialized_tracked_files": materialized, "station_checkout": station,
        "reads": len(found["read"]), "probes": len(found["probe"]), "listings": len(found["list"]),
        "absent_lookups": len(found["absent"]), "outside_repository_events": found["outside_repository_events"],
        "closure_files": len(closure), "closure_bytes": disk_bytes(repo, closure),
        "closure_areas": areas(closure),
        "listed_directories": dict(list(sorted(listed_closure.items(), key=lambda kv: -kv[1]))[:LIST_LIMIT]),
        "silent_misses": len(misses), "silent_miss_examples": misses[:LIST_LIMIT],
        "closure": sorted(closure), "required_directories": sorted(directories),
    }
    out = repo / RECORDS / (name + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    station_files = station.get("path_count") or materialized
    print(f"[Ariadne] {name}: needs {len(closure):,} tracked files ({result['closure_bytes'] / 1e6:,.1f} MB) "
          f"of {station_files:,} materialized; {len(found['list']):,} directories listed; "
          f"{len(misses)} silent misses; record {out.relative_to(repo).as_posix()}", flush=True)
    if misses:
        first = misses[0]
        print(f"::warning::Ariadne: {name} looked for {len(misses)} tracked path(s) this checkout left out "
              f"(first: {first['kind']} {first['path']}); see {out.relative_to(repo).as_posix()}", flush=True)
    return result


def finish(name, repo, trace, exit_code, seconds, usual_seconds):
    """Record a traced job; never let tracing change the job's outcome."""
    if trace is None:
        return None
    try:
        if not Path(trace).is_file():
            print(f"[Ariadne] {name}: no trace was written; nothing recorded.", flush=True)
            return None
        return record(name, repo, trace, exit_code, seconds, usual_seconds)
    except Exception as exc:
        print(f"[Ariadne] {name}: could not record the trace ({type(exc).__name__}: {exc}).", flush=True)
        return None
    finally:
        try:
            if os.environ.get("ARIADNE_KEEP_TRACE") == "1" and Path(trace).is_file():
                keep = Path(repo) / RECORDS / Path(trace).name
                keep.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(trace), str(keep))
            else:
                Path(trace).unlink(missing_ok=True)
        except OSError:
            pass
