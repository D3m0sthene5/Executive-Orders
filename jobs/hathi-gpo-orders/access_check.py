"""Bounded anonymous HathiTrust access gate; never log in or bypass a restriction."""
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("early_orders_hunt", ROOT / "jobs/early-orders-hunt/hunt.py")
hunt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hunt)


def main():
    out = HERE / "output"
    out.mkdir(exist_ok=True)
    source = ROOT / "research/gap-census/census.csv"
    population = []
    with source.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            match = re.match(r"^(\d+)", row["order_number"])
            evidence = [v for k, v in row.items() if k not in ("order_number", "instrument_id")]
            if match and 5076 <= int(match[1]) <= 7531 and all(v == "no" for v in evidence):
                population.append({"instrument_id": row["instrument_id"], "order_number": row["order_number"]})
    assert len(population) == 1712, f"Population changed: {len(population)} rather than 1712"
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data/TARGETS.json").write_text(json.dumps({
        "input": "research/gap-census/census.csv", "input_sha256": hunt.sha256_bytes(source.read_bytes()),
        "selection": "all evidence columns no; numeric order prefix 5076 through 7531 inclusive",
        "count": len(population), "orders": population}, indent=2) + "\n", encoding="utf-8")
    url = "https://babel.hathitrust.org/cgi/pt?id=mdp.39015087537604"
    pool = hunt.FetchPool(HERE / ".cache", workers=1, per_host=1, min_interval=2,
                          max_bytes=2_000_000, timeout=30,
                          user_agent="EO-Historical-Research/1.0 (https://github.com/D3m0sthene5/Executive-Orders)")
    state = {"checked_utc": datetime.now(timezone.utc).isoformat(), "url": url,
             "target_orders": len(population), "anonymous": True, "workers": 1,
             "min_interval_seconds": 2, "volumes_downloaded": 0, "texts_saved": 0,
             "attempted_order_extractions": 0, "login_attempted": False,
             "alternate_routes_attempted": False,
             "reused_module": "jobs/early-orders-hunt/hunt.py",
             "reused_module_sha256": hunt.sha256_bytes((ROOT / "jobs/early-orders-hunt/hunt.py").read_bytes()),
             "page_mapping_function": "early_orders_hunt.printed_page_map (not reached)"}
    try:
        result = pool.fetch(url)
        html = result["body"].decode("utf-8", "replace")
        state.update(viewer_sha256=hunt.sha256_bytes(result["body"]), viewer_bytes=len(result["body"]))
        if any(marker in html.lower() for marker in ("<title>just a moment", "cf-chl-", "challenge-platform", "challenge-form")):
            state.update(state="stopped_access_challenge", reason="HathiTrust presented an automated-access challenge; no bypass or retry")
        else:
            state.update(state="stopped_pending_offered_download_review", reason="Viewer obtained; no volume download authorized until anonymous offered download and limits are verified")
    except Exception as exc:
        state.update(state="stopped_access_check", reason=f"{type(exc).__name__}: {exc}")
    state["pool_requests"] = pool.requests
    state["requests_after_stop"] = 0
    state["failed_access_checks"] = 1
    state["orders_not_attempted"] = len(population)
    failures = [{"instrument_id": row["instrument_id"], "result": "not_attempted",
                 "stage": "anonymous_access_gate", "reason": state["reason"],
                 "volume_download_attempted": False} for row in population]
    with (out / "FAILURES.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for failure in failures:
            fh.write(json.dumps(failure, sort_keys=True) + "\n")
    (out / "VOLUME_FAILURES.jsonl").write_text(json.dumps({
        "url": url, "stage": "viewer_access_check", "reason": state["reason"],
        "volume_download_attempted": False}, sort_keys=True) + "\n", encoding="utf-8")
    for filename in ("SOURCES.jsonl", "FRAGMENTS.jsonl"):
        (out / filename).write_bytes(b"")
    (out / "STATUS.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
