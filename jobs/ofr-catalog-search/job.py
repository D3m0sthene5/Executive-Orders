"""Run the offline tests, then record the OFR catalog search for each order the tracker lists. See README.md."""

import csv
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
if subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_ofr_catalog_search"], cwd=HERE).returncode:
    sys.exit("Tests failed; nothing searched.")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import ofr_catalog_search as S  # noqa: E402
import runner_limits  # noqa: E402

out = pathlib.Path(os.environ["OUTPUT_DIR"])
repo = pathlib.Path(os.environ["REPO_ROOT"])
t0 = time.time()
src = repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
ids = S.target_ids(src.read_text(encoding="utf-8"))
print(f"{len(ids)} orders carry {S.BLOCKER} in {src.name}")
if not ids:
    sys.exit("No target orders found; the tracker output may have changed shape.")


def save_state(s):
    s.update(elapsed_seconds=round(time.time() - t0, 1), targets=len(ids))
    (out / "STATE.json").write_text(json.dumps(s, indent=1), "utf-8")   # every page, not only at the end
    print(s)


records, info = S.run_search(ids, past_stop=runner_limits.past_safe_stop, state_cb=save_state)
cols = ["instrument_id", "searched_number", "outcome", "url", "entry_text", "page_url", "page_sha256",
        "catalog_lowest_number", "catalog_highest_number", "coverage_quote", "index_url", "index_sha256"]
with open(out / "SEARCH_RECORDS.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(records)
counts = {}
for r in records:
    counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
elapsed = time.time() - t0
(out / "STATUS.json").write_text(json.dumps({
    "job": "ofr-catalog-search", "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "targets": len(ids), "outcomes": counts, "catalog_complete": info["complete"],
    "catalog_pages": info["pages"], "catalog_records": info["catalog_records"],
    "coverage_quote": info["coverage_quote"], "index_sha256": info["index_sha256"],
    "elapsed_seconds": round(elapsed, 1), "requests": 1 + len(info["pages"]),
    "leads_only": "no status, step, blocker or count is changed by this job",
}, indent=1), "utf-8")
print("outcomes:", counts, f"elapsed {elapsed:.0f}s over {1 + len(info['pages'])} requests (measured this run)")
if not info["complete"]:
    sys.exit("Catalog not fully read; records marked search_incomplete.")
