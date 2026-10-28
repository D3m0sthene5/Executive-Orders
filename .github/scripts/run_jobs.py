"""Run jobs transactionally; failed attempts never replace successful outputs."""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

import result_freshness as freshness

LIMIT = 95 * 1024 * 1024
MAX_OUTPUT_FILE_BYTES = 100 * 1024 * 1024 - 1


def output_file_limit(folder):
    """Explicit per-job opt-in; never admit a GitHub-limit-sized output."""
    path = folder / "MAX_OUTPUT_FILE_BYTES"
    if not path.exists():
        return LIMIT
    value = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+", value) or not 1 <= int(value) <= MAX_OUTPUT_FILE_BYTES:
        raise ValueError(f"Invalid MAX_OUTPUT_FILE_BYTES for {folder.name}: require 1..{MAX_OUTPUT_FILE_BYTES}")
    return int(value)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


# ---------------------------------------------------------------- Rattle Watch
# Named for New Amsterdam's rattle watch (1658), night watchmen who walked the streets calling the hour.
# While a job runs, the runner prints one line a minute: elapsed time, the job's last successful duration,
# how long since the job printed anything, and its CPU and network use over the last minute. A job that has
# printed nothing and used neither CPU nor network for STALL_MINUTES (default 20, per-job file STALL_MINUTES)
# is stopped and recorded as stalled, so a hang fails in minutes instead of running to the 350-minute limit.
STALL_MINUTES = 20
STALL_EXIT = 124
CPU_IDLE_SECONDS = 1.0          # less CPU than this across the stall window counts as idle
NET_IDLE_BYTES = 256 * 1024     # less network traffic than this across the stall window counts as idle
WEB_SEARCH_LIBRARY = "jobs/_lib/eo_websearch.py"
PUSH_WEB_REQUESTS = 12          # web requests allowed to a search job that runs only downstream of a push


def tree_cpu_seconds(pid):
    """CPU seconds used by a process and all its descendants (Linux /proc); None where unavailable."""
    try:
        tick = os.sysconf("SC_CLK_TCK")
        parents, times = {}, {}
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/stat", encoding="utf-8") as fh:
                    fields = fh.read().rsplit(")", 1)[1].split()
            except OSError:
                continue
            parents[int(entry)] = int(fields[1])
            times[int(entry)] = sum(int(x) for x in fields[11:15])
    except (OSError, ValueError, AttributeError):
        return None
    tree, frontier = {pid}, [pid]
    while frontier:
        parent = frontier.pop()
        for child, ppid in parents.items():
            if ppid == parent and child not in tree:
                tree.add(child)
                frontier.append(child)
    return sum(times.get(p, 0) for p in tree) / tick if pid in times else None


def net_bytes():
    """Bytes received plus sent on this machine's interfaces (Linux /proc/net/dev); None where unavailable."""
    try:
        with open("/proc/net/dev", encoding="utf-8") as fh:
            rows = fh.read().splitlines()[2:]
    except OSError:
        return None
    total = 0
    for row in rows:
        name, _, data = row.partition(":")
        if name.strip() != "lo":
            cols = data.split()
            total += int(cols[0]) + int(cols[8])
    return total


def stall_minutes(folder):
    path = folder / "STALL_MINUTES"
    if not path.is_file():
        return STALL_MINUTES
    value = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+", value) or not 1 <= int(value) <= 340:
        raise ValueError(f"Invalid STALL_MINUTES for {folder.name}: require 1..340")
    return int(value)


def last_success_seconds(prior_output):
    """Duration of the job's last successful run, from the output it is about to replace."""
    try:
        status = json.loads((prior_output / "STATUS.json").read_text(encoding="utf-8"))
        if status.get("result") != "succeeded":
            return None
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        start = time.mktime(time.strptime(status["started_utc"], fmt))
        return max(0.0, time.mktime(time.strptime(status["finished_utc"], fmt)) - start)
    except (OSError, ValueError, KeyError, TypeError):
        return None


def is_web_search_job(folder):
    return WEB_SEARCH_LIBRARY in freshness.lines(folder / "triggers.txt")


def _minutes(seconds):
    return f"{seconds / 60:.0f}m" if seconds >= 90 else f"{seconds:.0f}s"


def is_stalled(samples, silent_seconds, stall_seconds):
    """True when the job printed nothing and used no CPU or network across the whole stall window."""
    if silent_seconds < stall_seconds or not samples:
        return False
    now, cpu_now, net_now = samples[-1]
    base = [s for s in samples if s[0] <= now - stall_seconds]
    if not base or cpu_now is None or base[-1][1] is None:
        return False  # cannot tell without CPU readings; never stop a job on silence alone
    _, cpu_then, net_then = base[-1]
    if cpu_now - cpu_then >= CPU_IDLE_SECONDS:
        return False
    if net_now is not None and net_then is not None and net_now - net_then >= NET_IDLE_BYTES:
        return False
    return True


def heartbeat_line(name, elapsed, usual, silent, samples):
    parts = [f"[Rattle Watch] {name}: {_minutes(elapsed)} elapsed"]
    parts[0] += f" (last successful run {_minutes(usual)})" if usual is not None else " (no earlier successful run)"
    parts.append(f"last output {_minutes(silent)} ago")
    if len(samples) >= 2:
        (t0, c0, n0), (t1, c1, n1) = samples[-2], samples[-1]
        span = _minutes(t1 - t0)
        if c0 is not None and c1 is not None:
            parts.append(f"CPU {c1 - c0:.1f}s in the last {span}")
        if n0 is not None and n1 is not None:
            parts.append(f"network {(n1 - n0) / 1e6:.1f} MB in the last {span}")
    return ", ".join(parts)


def _stop(process, group):
    try:
        if group and hasattr(os, "killpg"):
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if group and hasattr(os, "killpg"):
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()
    except ProcessLookupError:
        pass


def _watched(process, stream, watch):
    clock, sleep = watch.get("clock", time.monotonic), watch.get("sleep", time.sleep)
    cpu_of, net_of = watch.get("cpu", tree_cpu_seconds), watch.get("net", net_bytes)
    beat, stall = watch["heartbeat"], watch["stall_minutes"] * 60
    lock, state = threading.Lock(), {"last": clock()}

    def reader():
        for line in process.stdout:
            print(line, end="", flush=True)
            stream.write(line)
            with lock:
                state["last"] = clock()

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    start = clock()
    samples = [(start, cpu_of(process.pid), net_of())]
    next_beat = start + beat
    while process.poll() is None:
        sleep(min(5.0, beat))
        now = clock()
        if now < next_beat:
            continue
        next_beat = now + beat
        samples.append((now, cpu_of(process.pid), net_of()))
        samples = samples[-(int(stall // beat) + 3):]
        with lock:
            silent = now - state["last"]
        print(heartbeat_line(watch["name"], now - start, watch.get("usual"), silent, samples), flush=True)
        if is_stalled(samples, silent, stall):
            message = (f"Rattle Watch stopped {watch['name']}: no output, CPU or network activity for "
                       f"{watch['stall_minutes']} minutes (exit {STALL_EXIT}).")
            print("::error::" + message, flush=True)
            stream.write(message + "\n")
            _stop(process, watch.get("group", False))
            thread.join(timeout=10)
            return STALL_EXIT
    thread.join()
    return process.wait()


def command(args, log, env=None, watch=None):
    with log.open("a", encoding="utf-8") as stream:
        group = bool(watch) and os.name == "posix"
        process = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   errors="replace", **({"start_new_session": True} if group else {}))
        try:
            if watch is None:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    stream.write(line)
                return process.wait()
            return _watched(process, stream, {**watch, "group": group})
        except BaseException:
            _stop(process, group)
            raise


def main():
    repo = Path.cwd().resolve()
    names = os.environ.get("JOBS", "").split()
    if any(not freshness.NAME.fullmatch(name) for name in names):
        raise ValueError("Invalid job name")
    token = "-".join((os.environ.get("GITHUB_RUN_ID", str(time.time_ns())),
                      os.environ.get("GITHUB_RUN_ATTEMPT", "1")))
    if not re.fullmatch(r"[A-Za-z0-9._-]+", token):
        raise ValueError("Invalid execution identifier")
    downstream = set(os.environ.get("DOWNSTREAM_ONLY", "").split())
    heartbeat = float(os.environ.get("RATTLE_HEARTBEAT_SECONDS", "60"))
    receipts = repo / "oversized/runner-freshness/ATTEMPTS.json"
    attempts, failed = [], set()
    write(receipts, attempts)

    def interrupted(signum, frame):
        raise KeyboardInterrupt("runner signal " + str(signum))

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, interrupted)
    for name in names:
        print("::group::Job " + name, flush=True)
        folder = repo / "jobs" / name
        out = folder / "output"
        backup = repo / ".job-cache/runner-prior" / token / name
        attempt = repo / "jobs/_attempts" / name / token
        scratch = repo / ".job-cache/runner-attempt" / token / name
        scratch.mkdir(parents=True, exist_ok=True)
        started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        inputs = repo / "oversized/runner-freshness" / (name + "-inputs.json")
        code, blocked, active, stopped, captured = 1, [], False, False, False
        file_limit = LIMIT
        try:
            blocked = [dep for dep in freshness.lines(folder / "after.txt") if dep in failed]
            if blocked:
                code = 125
                raise RuntimeError("blocked by failed current-run dependencies: " + ", ".join(blocked))
            needs = freshness.lines(folder / "needs.txt")
            sparse = subprocess.run(["git", "config", "--bool", "core.sparseCheckout"], capture_output=True)
            if needs and sparse.stdout.strip() == b"true":
                subprocess.run(["git", "sparse-checkout", "add", "--stdin"],
                               input="\n".join(needs) + "\n", text=True, check=True)
            freshness.prepare(name)
            freshness.capture(name, inputs)
            captured = True
            file_limit = output_file_limit(folder)
            if backup.exists():
                raise RuntimeError("previous generation backup already exists")
            backup.parent.mkdir(parents=True, exist_ok=True)
            if out.exists():
                out.replace(backup)
            active = True
            out.mkdir(parents=True)
            cap = int((folder / "CACHE_MB").read_text().strip()) if (folder / "CACHE_MB").is_file() else 1024
            if not 1 <= cap <= 4096:
                raise ValueError("Invalid CACHE_MB for " + name)
            cache = repo / ".job-cache" / name
            cache.mkdir(parents=True, exist_ok=True)
            env = {**os.environ, "JOB_CACHE_MB": str(cap), "JOB_CACHE_DIR": str(cache),
                   "JOB_NAME": name, "JOB_DIR": str(folder), "OUTPUT_DIR": str(out), "REPO_ROOT": str(repo),
                   "JOB_PRIOR_OUTPUT_DIR": str(backup)}
            if name in downstream and is_web_search_job(folder):
                env["JOB_MAX_REQUESTS"] = str(PUSH_WEB_REQUESTS)
                print(f"[Rattle Watch] {name} runs only because a job it reads changed on this push: web search "
                      f"limited to {PUSH_WEB_REQUESTS} requests; its daily run does the full search.", flush=True)
            watch = {"name": name, "heartbeat": heartbeat, "stall_minutes": stall_minutes(folder),
                     "usual": last_success_seconds(backup)}
            code = 0
            if (folder / "requirements.txt").is_file():
                code = command([sys.executable, "-m", "pip", "install", "--quiet", "-r",
                                str(folder / "requirements.txt")], out / "install-log.txt", env)
            if code == 0:
                args = ["bash", str(folder / "job.sh")] if (folder / "job.sh").is_file() else [sys.executable, str(folder / "job.py")]
                code = command(args, out / "log.txt", env, watch)
            cache_code = subprocess.run([sys.executable, str(repo / "jobs/_lib/cache_cap.py"), str(cache), str(cap)]).returncode
            if code == 0 and cache_code:
                code = cache_code
        except BaseException as exc:
            stopped = isinstance(exc, (KeyboardInterrupt, SystemExit))
            code = 130 if stopped else (code or 1)
            with (out if active else scratch).joinpath("log.txt").open("a", encoding="utf-8") as stream:
                stream.write(type(exc).__name__ + ": " + str(exc) + "\n")
            print(type(exc).__name__ + ": " + str(exc), flush=True)
        finally:
            result = out if active else scratch
            moved = []
            for path in sorted(result.rglob("*")):
                if path.is_file() and path.stat().st_size > file_limit:
                    relative = path.relative_to(result)
                    target = repo / "oversized" / name / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(path), str(target))
                    moved.append(relative.as_posix())
            status = {"job": name, "result": "succeeded" if code == 0 else "blocked" if blocked else "failed",
                      "exit_code": code, "started_utc": started,
                      "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "commit_run": os.environ.get("GITHUB_SHA"), "branch": os.environ.get("GITHUB_REF_NAME"),
                      "trigger": os.environ.get("TRIGGER"),
                      "run_url": os.environ.get("RUN_URL") or "/".join((os.environ.get("GITHUB_SERVER_URL", ""), os.environ.get("GITHUB_REPOSITORY", ""), "actions/runs", os.environ.get("GITHUB_RUN_ID", ""))),
                      "machine": f"{platform.platform()}, Python {platform.python_version()}",
                      "max_output_file_bytes": file_limit,
                      "oversized_files_moved_to_run_download": moved, "blocked_by": blocked}
            write(result / "STATUS.json", status)
            if captured:
                shutil.copyfile(inputs, result / freshness.MANIFEST)
            record = {"job": name, "exit_code": code, "publish_output": code == 0}
            if code:
                failed.add(name)
                attempt.parent.mkdir(parents=True, exist_ok=True)
                result.replace(attempt)
                if active and backup.exists():
                    backup.replace(out)
                record["attempt_path"] = attempt.relative_to(repo).as_posix()
                record["previous_output_preserved"] = out.exists()
                print(f"::error::Job {name} {status['result']}; attempt: {record['attempt_path']}", flush=True)
            elif backup.exists():
                shutil.rmtree(backup)
            attempts.append(record)
            write(receipts, attempts)
            print("::endgroup::", flush=True)
        if stopped:
            return 130
    return int(bool(failed))


if __name__ == "__main__":
    sys.exit(main())
