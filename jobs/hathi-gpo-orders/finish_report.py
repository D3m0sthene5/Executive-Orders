"""Offline receipts for the stopped access gate; never writes claim-kit outputs."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "output"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    state = json.loads((OUT / "STATUS.json").read_text())
    assert state["state"] == "stopped_access_check" and state["reason"] == "FetchError: blocked_by_robots_txt"
    assert state["pool_requests"] == 1 and state["texts_saved"] == state["volumes_downloaded"] == 0
    targets = json.loads((HERE / "data/TARGETS.json").read_text())
    assert len(targets["orders"]) == len({r["instrument_id"] for r in targets["orders"]}) == 1712
    assert digest(ROOT / targets["input"]) == targets["input_sha256"]
    assert digest(ROOT / "jobs/early-orders-hunt/hunt.py") == state["reused_module_sha256"]
    state.update(failed_access_checks=1, orders_not_attempted=1712,
                 extraction_failures=0, first_two_volumes_gate="not_reached")
    write_json(OUT / "STATUS.json", state)
    with (OUT / "FAILURES.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for target in targets["orders"]:
            fh.write(json.dumps({"instrument_id": target["instrument_id"], "result": "not_attempted",
                                 "stage": "anonymous_access_gate", "reason": state["reason"],
                                 "volume_download_attempted": False}, sort_keys=True) + "\n")
    (OUT / "VOLUME_FAILURES.jsonl").write_text(json.dumps({
        "url": state["url"], "stage": "viewer_access_check", "reason": state["reason"],
        "volume_download_attempted": False}, sort_keys=True) + "\n", encoding="utf-8")
    volumes = json.loads((HERE / "data/VOLUMES.json").read_text())["volumes"]
    covered = set()
    with (OUT / "VOLUMES.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["volume", "title", "order_range", "range_candidates", "url", "qualification"])
        writer.writeheader()
        for v in volumes:
            subset = {r["instrument_id"] for r in targets["orders"]
                      if v["range_min"] <= int(re.match(r"\d+", r["order_number"])[0]) <= v["range_max"]}
            covered.update(subset)
            writer.writerow({"volume": v["key"], "title": v["title"],
                             "order_range": f"{v['range_min']}-{v['range_max']}", "range_candidates": len(subset),
                             "url": v["url"], "qualification": v.get("range_note", "Advertised range only; individual contents not acquired or verified")})
    assert len(covered) == 1712
    watched = ["jobs/early-orders-hunt/hunt.py", "jobs/claim-kit/inputs.py", targets["input"],
               "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
               "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"]
    before = {p: digest(ROOT / p) for p in watched}
    kit_out = ROOT / "jobs/claim-kit/output"
    output_before = {str(p.relative_to(ROOT)): digest(p) for p in kit_out.rglob("*") if p.is_file()} if kit_out.exists() else {}
    spec = importlib.util.spec_from_file_location("claim_kit_read_only", ROOT / "jobs/claim-kit/inputs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    corpus = module.load_corpus(ROOT)
    recognized = [r for r in corpus["texts"] if r["text_path"].startswith("jobs/hathi-gpo-orders/")]
    assert not recognized
    after = {p: digest(ROOT / p) for p in watched}
    output_after = {str(p.relative_to(ROOT)): digest(p) for p in kit_out.rglob("*") if p.is_file()} if kit_out.exists() else {}
    assert before == after and output_before == output_after
    git_status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True)
    changed = [line[3:].replace("\\", "/") for line in git_status.splitlines()]
    assert all(p.startswith("jobs/hathi-gpo-orders/") or p == "HANDOFF/notes-codex.md" for p in changed), changed
    check = {"method": "unchanged jobs/claim-kit/inputs.py load_corpus, read-only", "recognized_new_order_texts": 0,
             "expected_saved_order_texts": 0, "ocr_ingestion_not_exercised": True,
             "claim_kit_output_before": output_before, "claim_kit_output_after": output_after,
             "protected_inputs_sha256": after, "protected_inputs_unchanged": before == after,
             "base_main_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
             "range_candidate_union": len(covered), "logical_volumes_identified": len(volumes),
             "warnings": corpus["warnings"]}
    write_json(OUT / "INGESTION_CHECK.json", check)
    write_json(OUT / "SUMMARY.json", {"volumes_identified": len(volumes), "volumes_used": 0,
               "orders_saved": 0, "orders_targeted": 1712, "access_checks_failed": 1,
               "extractions_attempted": 0, "orders_not_attempted": 1712,
               "reason": state["reason"], "stop": "Anonymous robots-aware access gate refused the viewer; no retry or workaround",
               "claim_kit_ingestion": "read-only call recognizes zero new texts; OCR adapter not exercised",
               "first_two_volumes_gate": "not_reached"})
    print(json.dumps({"logical_volumes_identified": len(volumes), "range_candidates": len(covered),
                      "volumes_used": 0, "orders_saved": 0, "orders_not_attempted": 1712,
                      "access_checks_failed": 1, "reason": state["reason"],
                      "claim_kit_output_unchanged": output_before == output_after}, indent=2))


if __name__ == "__main__":
    main()
