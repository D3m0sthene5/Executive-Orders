#!/usr/bin/env python3
"""Validate Hamilton and reconcile historical profile coverage without raw transcripts."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("REPO_ROOT", HERE.parents[1]))
OUT = Path(os.environ["OUTPUT_DIR"])
subprocess.run([sys.executable, "-I", str(HERE / "test_profile.py")], check=True)
OUT.mkdir(parents=True, exist_ok=True)
rows = []
for path in sorted((REPO / "research/production/hamilton-2026-10-20").glob("PROFILE_*.json")):
    raw = path.read_bytes()
    old = json.loads(raw)
    rows.append({
        "path": path.relative_to(REPO).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
        "observed_transcript_tokens": old.get("tokens"), "model_calls": old.get("model_calls"),
        "legacy_usd_per_cost_unit": old.get("usd_per_unit"),
        "historical_scaling_status": "unverified_full_category_coverage" if old.get("usd_per_unit") is not None else "already_unpriced",
        "full_session_token_totals": None, "corrected_observed_window_token_value_usd": None,
        "cash_charge_usd": None,
        "reason": "Raw transcripts and independently reported complete category totals are not held in this repository. Retain the original observations; do not fabricate a remeasurement or infer complete capture from cache reads alone.",
    })
result = {
    "schema": "hamilton.historical-coverage/1",
    "input_commit": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
    "profiles": rows,
    "profiles_examined": len(rows),
    "scaled_profiles_needing_category_totals": sum(r["legacy_usd_per_cost_unit"] is not None for r in rows),
    "new_session_measurements": 0, "verified_savings_usd": 0,
    "sensor_array": "No published implementation found in the refreshed main/dependency branch; existing offline collector reused.",
    "note": "Legacy files are immutable inputs. This addendum withdraws unsupported completeness, not the session totals reported by their source.",
}
(OUT / "COVERAGE_RECONCILIATION.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("profiles_examined", "scaled_profiles_needing_category_totals", "new_session_measurements", "verified_savings_usd")}))
