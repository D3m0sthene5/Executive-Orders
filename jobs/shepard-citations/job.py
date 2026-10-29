"""Shepard runner entry: offline tests first, then the BLM tables (network), then the citation index. See README.md.

Environment (all optional):
  JOB_MAX_REQUESTS       web requests allowed this run (default 60: robots.txt, the listing page, 24 PDFs)
  SHEPARD_OFFLINE=1      no web requests; BLM tables come only from the previous run's committed texts
  BLM_COMMIT_MAX_BYTES   commit a BLM PDF's bytes when it is at most this size (default 2,000,000)
  SHEPARD_TEXT_LIMIT     scan only the first N held texts (trial runs)
"""
import json
import os
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
tests = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_shepard"], cwd=here)
if tests.returncode:
    sys.exit("Unit tests failed; Shepard did not run.")

sys.path.insert(0, str(here))
import blm  # noqa: E402
import shepard  # noqa: E402

root = os.environ.get("REPO_ROOT") or str(here.parent.parent)
out = os.environ.get("OUTPUT_DIR") or str(here / "output")
cache = os.environ.get("JOB_CACHE_DIR") or os.path.join(os.path.dirname(out), "shepard-citations-cache")
prior = os.environ.get("JOB_PRIOR_OUTPUT_DIR") or ""
os.makedirs(out, exist_ok=True)

tables, records, fetch_stats = blm.fetch_tables(
    out, cache, prior, str(here / "data" / "blm_plo_tables.json"),
    max_requests=int(os.environ.get("JOB_MAX_REQUESTS") or 60),
    commit_max_bytes=int(os.environ.get("BLM_COMMIT_MAX_BYTES") or 2_000_000),
    offline=os.environ.get("SHEPARD_OFFLINE") == "1")
with open(os.path.join(out, "SOURCES.jsonl"), "w", encoding="utf-8") as fh:
    for rec in records:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")

limit = int(os.environ["SHEPARD_TEXT_LIMIT"]) if os.environ.get("SHEPARD_TEXT_LIMIT") else None
summary = shepard.run(root, out, tables=[t for t in tables if t.get("pages")], text_limit=limit)
summary["blm_fetch"] = fetch_stats
summary["blm_tables_failed"] = [t["name"] for t in tables if t.get("status") == "failed"]
with open(os.path.join(out, "SUMMARY.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2, sort_keys=True)
    fh.write("\n")
print(json.dumps({k: summary[k] for k in ("edges", "edges_by_evidence_type", "plo_table_rows", "blm_tables_failed",
                                          "land_targets_with_ending_candidate", "seconds")}, indent=2))
# No BLM table read or carried forward: fail only if that would replace a previous PLO_TABLE that had rows (the runner
# then keeps the previous output). On a first run the other sources' leads are still published.
if not any(t.get("pages") for t in tables):
    prior_table = os.path.join(prior, "PLO_TABLE.csv") if prior else ""
    if prior_table and os.path.isfile(prior_table) and sum(1 for _ in open(prior_table, encoding="utf-8")) > 1:
        sys.exit("No BLM Public Land Order table could be read or carried forward; previous output kept.")
    print("WARNING: no BLM Public Land Order table could be read; PLO_TABLE.csv is empty this run.")
