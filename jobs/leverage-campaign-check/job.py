"""One-off offline verification using real job entry points; output only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


SAMPLE = [10032, 10056, 10112, 10140, 10449, 10570, 10693, 10749,
          10750, 10878, 10923, 11101, 10915, 11927, 12975, 9333, 12607, 8072]
JOBS = ("norton", "claim-kit", "claim-checker", "readiness-tracker", "polya")


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    root = Path(os.environ["REPO_ROOT"]).resolve()
    out = Path(os.environ["OUTPUT_DIR"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    view = out / "replay"
    if view.exists():
        raise RuntimeError("Refusing to reuse an existing replay view")
    started = time.monotonic()
    receipts = []
    # Never recurse into this job's output or any runner/cache internals.
    def ignore(directory, names):
        rel = Path(directory).relative_to(root)
        ignored = {n for n in names if n in {".git", ".job-cache", "__pycache__", "oversized"}}
        if rel == Path("jobs/leverage-campaign-check"):
            ignored.add("output")
        if rel == Path("jobs"):
            ignored.add("_attempts")
        return ignored

    def link_or_copy(src, dst):
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)

    env = dict(os.environ, REPO_ROOT=str(view), PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8", CLAIM_CHECKER_VERIFY_DOWNLOADS="0",
               CLAIM_CHECKER_FETCH_MAX_REQUESTS="0", JOB_OFFLINE="1")
    success = False
    try:
        shutil.copytree(root, view, copy_function=link_or_copy, ignore=ignore, symlinks=True)
        for name in JOBS:
            target = view / "jobs" / name / "output"
            # Hardlinks are read-only inputs; remove them before these jobs write.
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True)
            tick = time.monotonic()
            log = out / (name + ".log")
            command = [sys.executable, "-B", str(view / "jobs" / name / "job.py")]
            timed_out = False
            with log.open("w", encoding="utf-8") as fh:
                try:
                    process = subprocess.run(command, cwd=view,
                        env=dict(env, OUTPUT_DIR=str(target), JOB_CACHE_DIR=str(out / "parser-cache")),
                        stdout=fh, stderr=subprocess.STDOUT, timeout=1800, check=False)
                    exit_code = process.returncode
                except subprocess.TimeoutExpired:
                    exit_code, timed_out = 124, True
                    fh.write("\nBounded verification timed out after 1800 seconds.\n")
            receipt = {"job": name, "exit_code": exit_code, "timed_out": timed_out,
                       "wall_seconds": round(time.monotonic() - tick, 3),
                       "input_commit": os.environ.get("GITHUB_SHA"),
                       "network_verification_disabled": True}
            receipts.append(receipt)
            dump(out / "COMMAND_RECEIPTS.json", receipts)
            if name == "claim-kit":
                keep = ("SUMMARY.json", "INDEX.json", "METRICS.json", "POPULATION_VALIDATION.json",
                        "ACT_OVERRIDES_REPORT.json", "ASSEMBLY_REPORT.json")
                for filename in keep:
                    if (target / filename).is_file():
                        (out / name).mkdir(exist_ok=True)
                        shutil.copyfile(target / filename, out / name / filename)
                for number in SAMPLE:
                    p = target / "dossiers" / f"EO_{number}.json"
                    if p.is_file():
                        (out / name / "dossiers").mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(p, out / name / "dossiers" / p.name)
            else:
                shutil.copytree(target, out / name)
            if exit_code:
                raise RuntimeError(f"{name} failed; inspect {name}.log")
        success = True
    finally:
        dump(out / "VALIDATION.json", {
            "schema": "eo-bounded-offline-verification/v1", "success": success,
            "input_commit": os.environ.get("GITHUB_SHA"),
            "run_url": os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" +
                       os.environ.get("GITHUB_REPOSITORY", "D3m0sthene5/Executive-Orders") +
                       "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "local"),
            "machine_wall_seconds": round(time.monotonic() - started, 3),
            "commands": receipts, "canonical_outputs_modified": False,
            "new_claims": 0, "status_changes": 0, "human_certifications": 0,
            "model_tokens": None, "aggregate_agent_seconds": None, "cash_usd": None,
            "notice": "Offline integrated replay; no canonical publication or legal approval."})
        shutil.rmtree(view, ignore_errors=True)
        shutil.rmtree(out / "parser-cache", ignore_errors=True)


if __name__ == "__main__":
    subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                    str(Path(__file__).parent), "-p", "test_*.py"], check=True)
    main()
