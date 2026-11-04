#!/usr/bin/env python3
"""Read-only retained-packet rendering comparison; outputs only requested JSON."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "jobs/geddes"))
import geddes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixture-root", type=Path, required=True)
    p.add_argument("--baseline-code", type=Path, required=True)
    p.add_argument("--repeat", type=int, default=5)
    p.add_argument("--worker", choices=("baseline", "batch"))
    p.add_argument("--write", type=Path)
    a = p.parse_args()
    root = a.fixture_root.resolve()
    packet_path = root / "research/excavator/claude-apollo-2026-10-31/n01/packet/PACKET.json"
    packet = json.loads(packet_path.read_text())
    iids = list(packet["dossiers"])
    spec = importlib.util.spec_from_file_location("baseline_geddes", a.baseline_code)
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    def run(mode):
        start = time.perf_counter()
        with geddes._count_file_reads() as reads:
            output = ([old.view(packet_path, iid, repo=root) for iid in iids] if mode == "baseline"
                      else geddes.view_many(packet_path, iids, repo=root))
        return output, {"seconds": time.perf_counter() - start,
                        "path_read_calls": reads["calls"], "distinct_path_reads": len(reads["paths"])}
    if a.worker:
        _, record = run(a.worker)
        print(json.dumps(record)); return
    observations = {"baseline": [], "batch": []}
    for n in range(a.repeat):
        outputs = {}
        for mode in (("baseline", "batch") if n % 2 == 0 else ("batch", "baseline")):
            outputs[mode], record = run(mode); observations[mode].append(record)
        assert outputs["baseline"] == outputs["batch"], "ordinary-view parity failed"
    baseline, optimized = outputs["baseline"], outputs["batch"]
    # Also compare complete filed-claim strings, beyond the default view caps.
    assert [old.view(packet_path, iid, repo=root, full_claim=True) for iid in iids] == geddes.view_many(packet_path, iids, repo=root, full_claim=True)
    cold = {}
    for mode in ("baseline", "batch"):
        start = time.perf_counter()
        stdout = subprocess.check_output([sys.executable, "-I", str(Path(__file__).resolve()),
            "--fixture-root", str(root), "--baseline-code", str(a.baseline_code), "--worker", mode])
        cold[mode] = {"process_wall_seconds": time.perf_counter() - start,
                      "worker": json.loads(stdout)}
    setup_start = time.perf_counter()
    context = geddes._ViewContext(packet_path, root, iids)
    setup_seconds = time.perf_counter() - setup_start
    render_start = time.perf_counter()
    [geddes._view_one(context, iid, None, False) for iid in iids]
    member_render_seconds = time.perf_counter() - render_start
    single = {}
    for mode in ("baseline", "batch"):
        start = time.perf_counter()
        output = old.view(packet_path, iids[0], repo=root) if mode == "baseline" else geddes.view_many(packet_path, iids[:1], repo=root)[0]
        single[mode] = time.perf_counter() - start
    pins = packet["held_text_file_pins"]
    verified = sum(hashlib.sha256((root / path).read_bytes()).hexdigest() == sha for path, sha in pins.items())
    result = {"schema": "sol-batch-views-benchmark/v1", "orders": iids,
        "packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
        "packet_bytes": packet_path.stat().st_size,
        "baseline_code_sha256": hashlib.sha256(a.baseline_code.read_bytes()).hexdigest(),
        "source_pins_verified": verified, "source_pins_total": len(pins),
        "claims_fixture_files": len(list((root / "research/readiness/claims").glob("*.jsonl"))),
        "ordinary_and_full_claim_parity": True,
        "output_utf8_bytes": sum(len(json.dumps(v, ensure_ascii=False).encode()) for v in optimized),
        "source_integrity_failures": sum(len(v["source_file_verification"]["integrity_failures"]) for v in optimized),
        "source_unavailable": sum(len(v["source_file_verification"]["unavailable"]) for v in optimized),
        "whole_order_body_verified": sum(v["own_text_boundary"]["verified_whole_order"] for v in optimized),
        "warm_observations": observations, "fresh_process_observations": cold,
        "one_order_warm_seconds": single,
        "shared_setup_seconds": setup_seconds, "all_member_render_seconds": member_render_seconds,
        "median_seconds": {mode: statistics.median(x["seconds"] for x in records) for mode, records in observations.items()},
        "limits": ["No model invocation or measured token/cash saving.",
                   "Fixture has one retained claims file; not all 104 current claim files.",
                   "APP publisher INDEX unavailable in sparse checkout; body boundary gaps remain explicit.",
                   "File read counters cover Path.read_bytes/read_text; CSV open is not counted.",
                   "Cold means fresh Python process; operating-system file cache is not flushed.",
                   "Baseline competently loops existing per-order renderer in one process; no repeated import penalty."]}
    text = json.dumps(result, indent=2) + "\n"
    if a.write: a.write.write_text(text)
    else: print(text)


if __name__ == "__main__": main()
