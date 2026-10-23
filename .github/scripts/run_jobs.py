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
import time

import result_freshness as freshness

LIMIT = 95 * 1024 * 1024


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def command(args, log, env=None):
    with log.open("a", encoding="utf-8") as stream:
        process = subprocess.Popen(args, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, errors="replace")
        try:
            for line in process.stdout:
                print(line, end="", flush=True)
                stream.write(line)
            return process.wait()
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
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
                   "JOB_NAME": name, "JOB_DIR": str(folder), "OUTPUT_DIR": str(out), "REPO_ROOT": str(repo)}
            code = 0
            if (folder / "requirements.txt").is_file():
                code = command([sys.executable, "-m", "pip", "install", "--quiet", "-r",
                                str(folder / "requirements.txt")], out / "install-log.txt", env)
            if code == 0:
                args = ["bash", str(folder / "job.sh")] if (folder / "job.sh").is_file() else [sys.executable, str(folder / "job.py")]
                code = command(args, out / "log.txt", env)
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
                if path.is_file() and path.stat().st_size > LIMIT:
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
