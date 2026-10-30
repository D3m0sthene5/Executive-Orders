"""Five effective claims, unchanged native gates, isolated receipt overlays.

Historical PR105 three-case restoration is the baseline. Only the two additional
exact PDFs are absent in that baseline; all five are checked in both conditions.
No canonical checker/tracker output is written. Run from the repository root.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / "replay"
ORIGINAL = "77abf218aa88ed89f4a16f4c93ed1baaf29098e0"
PUBLISHED = "e87c9ad658a6708705f83a6dd43fd238f472926d"
OLD = {"EO:254", "EO:2171", "EO:4354"}
NEW = {"EO:1547", "EO:4782"}
IDS = OLD | NEW
sys.path[:0] = [str(ROOT / "jobs/claim-checker"), str(ROOT / "jobs/readiness-tracker")]
import checker
import proquest_inputs
import tracker


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def pins():
    # Includes checked-out canonical claims, scientific reviews, policy and gates.
    paths = git("ls-files", "-z", "research/readiness", "research/stage19/code",
                "jobs/claim-checker", "jobs/readiness-tracker",
                "jobs/pinakes-proquest-ingest/output").split(b"\0")
    return {p.decode(): sha((ROOT / p.decode()).read_bytes()) for p in paths
            if p and (ROOT / p.decode()).is_file()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = pins()
    old = types.ModuleType("historical_proquest_inputs")
    exec(compile(git("show", f"{ORIGINAL}:jobs/claim-checker/proquest_inputs.py"),
                 "PR105:proquest_inputs.py", "exec"), old.__dict__)
    original = old.materialize(ROOT, OUT / "original-three-materialization")
    assert not original["errors"] and {r["instrument_id"] for r in original["receipts"]} == OLD
    assert all(r["state"] in {"already_held", "restored_exact_blob"} for r in original["receipts"])
    # Pin the already published, successful full branch-run generation without
    # changing the checkout's canonical checker receipt or any tracker output.
    published_raw = git("show", f"{PUBLISHED}:{tracker.J['checker']}")
    published = json.loads(published_raw)
    reader = checker.read_claims

    def selected(paths, repo):
        effective = {}
        for row in reader(paths, repo):
            if row[3] and row[3].get("instrument_id") in IDS:
                effective[row[3]["instrument_id"]] = row
        assert set(effective) == IDS
        return list(effective.values())

    def check(label):
        out = OUT / f"{label}-checker"
        env = {"REPO_ROOT": str(ROOT), "OUTPUT_DIR": str(out),
               "JOB_CACHE_DIR": str(OUT / "cache"),
               "CLAIM_CHECKER_VERIFY_DOWNLOADS": "0", "CLAIM_CHECKER_CSV_ALL_ROWS": "1"}
        with patch.dict(os.environ, env), patch.object(checker, "read_claims", selected):
            checker.main(["--claims", str(ROOT / "research/readiness/claims/*.jsonl")])
        return json.loads((out / "PER_CLAIM.json").read_text())

    new_paths = []
    for line in (ROOT / proquest_inputs.FRAGMENTS).read_text().splitlines():
        row = json.loads(line)
        if row.get("instrument_id") in NEW and row.get("kind") == "original_representation":
            new_paths.append((ROOT / row["data"]["file"], row["data"]["sha256"]))
    assert len(new_paths) == 2
    with tempfile.TemporaryDirectory(prefix="proquest-follow-on-") as tmp:
        moved = []
        try:
            for n, (path, digest) in enumerate(new_paths):
                if path.exists():
                    assert sha(path.read_bytes()) == digest, "Refuse to relocate unverified local file"
                    dest = Path(tmp) / str(n)
                    path.rename(dest)
                    moved.append((path, dest))
            assert all(not path.exists() for path, _ in new_paths), "Baseline requires two absent PDFs"
            baseline = check("baseline")
            assert all(not path.exists() for path, _ in new_paths), "Sources changed during baseline"
            cursor, batches = None, []
            for n in range(3):
                receipt = proquest_inputs.materialize(ROOT, OUT / f"batch-{n+1}",
                                                       max_artifacts=2, resume=cursor)
                assert not receipt["errors"], receipt
                batches.append(receipt)
                cursor = receipt["next_cursor"]
                if cursor is None:
                    break
            assert cursor is None and len(batches) == 3
            attempts = [a for batch in batches for a in batch["artifacts"]
                        if a["state"] in {"already_held", "restored_exact_blob"}]
            assert len(attempts) == 5
            assert sum(a["state"] == "restored_exact_blob" for a in attempts) == 2
            corrected = check("corrected")
        finally:
            for path, saved in moved:
                if path.exists():
                    assert path.read_bytes() == saved.read_bytes()
                    saved.unlink()
                else:
                    saved.rename(path)
    results, overlay_pins = {}, {}
    for label, receipt in [("baseline", baseline), ("corrected", corrected)]:
        combined = copy.deepcopy(published)
        combined["by_instrument"].update(receipt["by_instrument"])
        assert all(combined["by_instrument"][iid] == value for iid, value
                   in published["by_instrument"].items() if iid not in IDS)
        with tempfile.TemporaryDirectory(prefix="isolated-checker-overlay-") as tmp:
            path = Path(tmp) / "PER_CLAIM.json"
            dump(path, combined)
            overlay_pins[label] = sha(path.read_bytes())
            with patch.dict(tracker.J, {"checker": str(path)}):
                orders, problems = tracker.build(str(ROOT))
        rows = [r for r in orders if r["instrument_id"] in IDS]
        assert len(rows) == 5
        dump(OUT / f"{label}-tracker.json", {"orders": rows, "input_problems": problems})
        results[label] = rows
    assert before == pins(), "Other checked-out research/checker/tracker inputs changed"
    result = {"commit": git("rev-parse", "HEAD").decode().strip(),
              "scope": "five effective claims; original PR105 baseline; isolated overlays; no global count",
              "published_checker_commit": PUBLISHED, "published_checker_sha256": sha(published_raw),
              "overlay_sha256": overlay_pins, "only_overlaid_instruments": sorted(IDS),
              "other_inputs_unchanged": True, "input_sha256": before,
              "helper_sha256": sha((ROOT / "jobs/claim-checker/proquest_inputs.py").read_bytes()),
              "additional_pdf_bytes": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p.read_bytes()),
                                        "bytes": p.stat().st_size} for p, _ in new_paths],
              "baseline": results["baseline"], "corrected": results["corrected"]}
    dump(OUT / "RESULT.json", result)
    for label, rows in results.items():
        print(label, [(r["instrument_id"], r["ready_for_human_review"], r["blockers"]) for r in rows])


if __name__ == "__main__":
    main()
