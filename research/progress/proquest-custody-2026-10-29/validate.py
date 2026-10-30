"""Bounded native checker/tracker replay; never publishes canonical outputs.

Run from the repository root. The only checker selection is the three exact
claims; all native source and readiness gates run unchanged. Tracker comparisons
reuse other published receipts verbatim, so they do not establish a new global
ready count. Baseline source absence is simulated by relocating only PDFs this
script has just verified, restoring them in a finally block.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "replay"
IDS = {"EO:254", "EO:2171", "EO:4354"}
sys.path[:0] = [str(ROOT / "jobs/claim-checker"), str(ROOT / "jobs/readiness-tracker")]
import checker
import proquest_inputs
import tracker


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT / "research/readiness/claims").glob("*.jsonl")}
    materialized = proquest_inputs.materialize(ROOT, OUT / "materialization", ids=IDS)
    assert not materialized["errors"], materialized
    assert {r["instrument_id"] for r in materialized["receipts"]} == IDS
    assert all(r["state"] in {"already_held", "restored_exact_blob"}
               for r in materialized["receipts"]), materialized
    raw_paths = [ROOT / r["path"] for r in materialized["receipts"]]
    published = json.loads((ROOT / tracker.J["checker"]).read_text())
    original_reader = checker.read_claims

    def selected(paths, repo):
        rows = original_reader(paths, repo)
        result = [r for r in rows if r[3] and r[3].get("instrument_id") in IDS]
        assert len(result) == 3, "Review changed claim selection before rerunning"
        return result

    def check(label):
        out = OUT / label
        env = {"REPO_ROOT": str(ROOT), "OUTPUT_DIR": str(out),
               "JOB_CACHE_DIR": str(OUT / "cache"),
               "CLAIM_CHECKER_VERIFY_DOWNLOADS": "0", "CLAIM_CHECKER_CSV_ALL_ROWS": "1"}
        with patch.dict(os.environ, env), patch.object(checker, "read_claims", selected):
            checker.main(["--claims", str(ROOT / "research/readiness/claims/*.jsonl")])
        return json.loads((out / "PER_CLAIM.json").read_text())

    with tempfile.TemporaryDirectory(prefix="proquest-baseline-") as tmp:
        moved = []
        try:
            for i, path in enumerate(raw_paths):
                dest = Path(tmp) / str(i)
                path.rename(dest)
                moved.append((path, dest))
            baseline = check("baseline-checker")
        finally:
            for path, dest in moved:
                dest.rename(path)
    corrected = check("corrected-checker")
    results = {}
    for label, receipt in [("baseline", baseline), ("corrected", corrected)]:
        combined = copy.deepcopy(published)
        combined["by_instrument"].update(receipt["by_instrument"])
        combined_path = OUT / f"{label}-isolated-receipts.json"
        dump(combined_path, combined)
        with patch.dict(tracker.J, {"checker": str(combined_path)}):
            orders, problems = tracker.build(str(ROOT))
        rows = [r for r in orders if r["instrument_id"] in IDS]
        assert len(rows) == 3
        dump(OUT / f"{label}-tracker.json", {"orders": rows, "input_problems": problems})
        results[label] = rows
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (ROOT / "research/readiness/claims").glob("*.jsonl")}
    assert before == after, "Claim bytes changed"
    result = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
              "scope": "three exact claims; native gates; isolated receipt overlay; no global count publication",
              "claim_file_sha256": before, "claims_unchanged": True,
              "baseline": results["baseline"], "corrected": results["corrected"],
              "pdf_bytes": [{**r, "bytes": (ROOT / r["path"]).stat().st_size,
                             "actual_sha256": hashlib.sha256((ROOT / r["path"]).read_bytes()).hexdigest()}
                            for r in materialized["receipts"]]}
    dump(OUT / "RESULT.json", result)
    for label, rows in results.items():
        print(label, [(r["instrument_id"], r["ready_for_human_review"], r["blockers"]) for r in rows])


if __name__ == "__main__":
    main()
