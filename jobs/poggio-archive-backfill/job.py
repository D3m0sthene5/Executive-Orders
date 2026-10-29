#!/usr/bin/env python3
"""Poggio: archive captures for American Presidency Project pages that were only harvested live.

Named for Poggio Bracciolini (1380-1459), who recovered classical texts by finding the copies that monastery
libraries had kept. Details, request counts and risks: jobs/app-executive-orders/CHANGE_NOTES.md.

Runs ONLY the archive lane of jobs/app-executive-orders/app_mirror.py (Common Crawl index and WARC ranges,
Wayback CDX and raw captures) for the orders in data/LIVE_ONLY_IDS.txt. It never requests APP: app_mirror's
http_get refuses every host but the three archive hosts, including on redirects, and lock_to_archives()
makes DNS lookups of any other host fail for this whole process before any network code runs.

jobs/app-executive-orders/output is only read. New rows go to OUTPUT_DIR (MIRROR_INDEX, MIRROR_DOCUMENTS,
MIRROR_SOURCES, MIRROR_FRAGMENTS, MIRROR_ATTEMPTS, MIRROR_FAILURES, texts/<slug>.capture.txt,
BACKFILL_STATE.json). `app_mirror.py merge --from jobs/poggio-archive-backfill/output` appends them to the
app-executive-orders output, offline and append-only.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
APP = REPO / "jobs/app-executive-orders"
CRAWLS = int(os.environ.get("POGGIO_CRAWLS", "48"))  # newest Common Crawl crawls to consider (back to about 2018)

for test in ("test_app_harvest.py", "test_app_mirror_backfill.py"):
    run = subprocess.run([sys.executable, "-I", str(APP / test)], capture_output=True, text=True)
    print(run.stdout[-1500:], run.stderr[-1500:], sep="\n")
    if run.returncode:
        sys.exit("Offline tests failed: " + test)

sys.path.insert(0, str(APP))
import app_mirror  # noqa: E402

app_mirror.lock_to_archives()
base = APP / "output"
out = Path(os.environ.get("OUTPUT_DIR", HERE / "output"))
cache = Path(os.environ.get("JOB_CACHE_DIR") or REPO / ".job-cache/poggio-archive-backfill")
out.mkdir(parents=True, exist_ok=True)
cache.mkdir(parents=True, exist_ok=True)

# Resume: rows an earlier, not yet merged run published are carried forward, so a rerun only appends.
prior = Path(os.environ.get("JOB_PRIOR_OUTPUT_DIR", ""))
if str(prior) not in ("", ".") and prior.is_dir() and prior.resolve() != out.resolve():
    for name in app_mirror.MIRROR_FILES + ("MIRROR_INDEX.jsonl",):
        if (prior / name).is_file():
            shutil.copyfile(prior / name, out / name)
    if (prior / "texts").is_dir():
        shutil.copytree(prior / "texts", out / "texts", dirs_exist_ok=True)

ids = app_mirror.read_ids(HERE / "data/LIVE_ONLY_IDS.txt")
now = set(app_mirror.live_only_ids(base))
print(json.dumps({"seed_ids": len(ids), "live_only_now": len(now), "seed_already_mirrored": len(ids - now),
                  "live_only_not_in_seed": sorted(now - ids)[:20]}), flush=True)

index = app_mirror.run_backfill_index(base, out, ids, lambda: app_mirror.cc_collections(CRAWLS),
                                      app_mirror.Throttle(1.0), app_mirror.Throttle(1.5))
state = app_mirror.run_backfill_documents(base, out, cache, ids, workers=4, interval=0.25,
                                          archives={"common-crawl", "wayback"})
state["index"] = index
app_mirror.live.write_json(out / "BACKFILL_STATE.json", state)
print(json.dumps({"saved": state["this_run"], "still_without_capture": len(state["still_without_capture"])}))
