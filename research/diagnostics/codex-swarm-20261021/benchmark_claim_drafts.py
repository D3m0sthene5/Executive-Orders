"""Offline comparison worker: source.py repo output cache [limit].

Runs cProfile, forbids urllib URL calls, and writes a normalized summary for
byte comparison. Use a fresh cache for cold runs and that same cache for warm
runs. The regular unit suite must be run separately. All outputs belong in
scratch folders, never the canonical jobs/claim-drafts/output directory.
"""
import cProfile
import importlib.util
import json
import os
import pathlib
import pstats
import sys
import time
from unittest import mock

source, repo, output, cache = map(pathlib.Path, sys.argv[1:5])
os.environ.update(REPO_ROOT=str(repo.resolve()), OUTPUT_DIR=str(output.resolve()),
                  JOB_CACHE_DIR=str(cache.resolve()), CLAIM_CHECKER_VERIFY_DOWNLOADS="0")
if len(sys.argv) > 5:
    os.environ["JOB_LIMIT"] = sys.argv[5]
else:
    os.environ.pop("JOB_LIMIT", None)
spec = importlib.util.spec_from_file_location("bench_drafts", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
profile = cProfile.Profile()
start = time.perf_counter()
with mock.patch("urllib.request.urlopen", side_effect=AssertionError("benchmark is offline")) as network:
    summary = profile.runcall(module.main)
    assert network.call_count == 0, network.call_count
elapsed = time.perf_counter() - start
profile.dump_stats(str(output) + ".prof")
summary.pop("elapsed_seconds", None)
(output / "BENCHMARK_SUMMARY.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
print("BENCHMARK", json.dumps({"elapsed_seconds": elapsed, "drafts": summary["orders_with_draft"],
                                "network_calls": network.call_count}))
pstats.Stats(profile).sort_stats("cumulative").print_stats(25)
