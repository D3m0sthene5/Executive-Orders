"""Bounded Geddes job: unit checks, telemetry summary, optional one-batch lint."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[2])).resolve()
OUT = Path(os.environ.get("OUTPUT_DIR", ROOT / "jobs/geddes/output"))
JOB = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
started = time.monotonic()
started_utc = datetime.now(timezone.utc).isoformat()
summary = {"schema": "geddes-job/v1", "tests": None, "cost": None, "lint": None}

def publish_status(status, exit_code, error=None):
    doc = {"schema": "geddes-status/v1", "status": status, "exit_code": exit_code,
           "started_utc": started_utc, "finished_utc": datetime.now(timezone.utc).isoformat(),
           "wall_seconds": round(time.monotonic() - started, 4), "error": error}
    (OUT / "STATUS.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

try:
    test = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s", str(JOB), "-p", "test_*.py"], cwd=ROOT,
                          text=True, capture_output=True)
    summary["tests"] = {"exit_code": test.returncode, "output": test.stdout + test.stderr}
    if test.returncode: raise RuntimeError("Geddes unit tests failed")
    sys.path.insert(0, str(JOB))
    import geddes

    telemetry = ROOT / "research/excavator/claude-apollo-2026-10-31/TELEMETRY.csv"
    if telemetry.is_file():
        result = geddes.cost(telemetry)
        (OUT / "COST.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary["cost"] = {"status": "reported_telemetry_summarized", "path": "COST.json"}

    applied = os.environ.get("GEDDES_APPLIED_DIR")
    if applied:
        path = Path(applied)
        if not path.is_absolute(): path = ROOT / path
        result = geddes.lint(path, ROOT)
        (OUT / "LINT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary["lint"] = {"status": "one_explicit_applied_directory_linted", "path": "LINT.json",
                           "claims_checked": result["claims_checked"], "defect_flags": result["defect_flags"],
                           "coverage_gaps": result["coverage_gaps"]}
    else:
        summary["lint"] = {"status": "not_run", "reason": "GEDDES_APPLIED_DIR was not supplied"}
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    publish_status("succeeded", 0)
    print(json.dumps({"tests_passed": True, "lint_status": summary["lint"]["status"]}))
except BaseException as exc:
    publish_status("failed", 1, f"{type(exc).__name__}: {exc}")
    raise
