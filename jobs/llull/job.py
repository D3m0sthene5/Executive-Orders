#!/usr/bin/env python3
"""Refresh calibration from the current, pinned append-only ledgers; no ledger writes."""
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import llull


def main():
    output = Path(os.environ["OUTPUT_DIR"])
    output.mkdir(parents=True, exist_ok=True)
    ledger = llull.Ledger(Path(__file__).resolve().parent / "ledger")
    errors, warnings = llull.run_check(ledger)
    rule_commit = llull.first_commit("-S", "CEILING_EXCEEDED", "--", "jobs/llull/llull.py")
    if not rule_commit:
        errors.append("selfscore rule history unavailable; cannot classify forecasts as out-of-sample")
    provenance = {"schema": "llull-refresh/v1", "commit_run": llull.git("rev-parse", "HEAD"),
                  "ledger_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(ledger.dir.iterdir()) if p.is_file()},
                  "errors": errors, "warnings": warnings,
                  "status": "failed" if errors else "succeeded",
                  "forecast_and_outcome_ledgers_modified": False}
    (output / "CHECK.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    if errors:
        print("Llull ledger check failed: " + "; ".join(errors))
        return 4
    calibration = llull.score_all(ledger)
    selfscore = llull.selfscore_all(ledger, rule_commit)
    for name, value in (("CALIBRATION.json", calibration), ("SELFSCORE.json", selfscore)):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print("Llull: %s forecasts, %s measured current outcomes, %s prospectively scorable quantities in %s experiments" % (
        calibration["n_forecasts"], calibration["n_resolved"], calibration["n_scored"], calibration["n_experiments_scored"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
