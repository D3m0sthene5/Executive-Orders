#!/usr/bin/env python3
"""Retrospective comparison, separate from Geddes' review-blind implementation.

The original review labels identify the comparator sets only. No review text,
claim id allowlist, or outcome is supplied to the linter.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
APOLLO = ROOT / "research/excavator/claude-apollo-2026-10-31"
sys.path.insert(0, str(ROOT / "jobs/geddes"))
import geddes as G
IMPL_HASH = hashlib.sha256((ROOT / "jobs/geddes/geddes.py").read_bytes()).hexdigest()
BASE = "40eb4b561ad657413169dae72bc0262efd4b119d"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def claim_at(ref):
    p = ROOT / ref["path"]
    raw = p.read_bytes()
    if sha(raw) != ref.get("file_sha256", ref.get("sha256")):
        raise ValueError(f"changed claim file: {p}")
    line = raw.splitlines()[ref["line"] - 1]
    if ref.get("record_sha256") and sha(line) != ref["record_sha256"]:
        raise ValueError(f"changed claim record: {p}")
    return json.loads(line)


def main():
    manifest = json.loads((HERE / "inventory/MANIFEST.json").read_text())
    cache = {}
    corpus_cache = {}

    def run(claim, packet_path):
        if packet_path not in cache:
            raw = packet_path.read_bytes()
            path = str(packet_path.relative_to(ROOT))
            expected = subprocess.check_output(["git", "rev-parse", BASE + ":" + path], cwd=ROOT).decode().strip()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if actual != expected:
                raise ValueError(f"packet differs from pinned Apollo base: {path}")
            cache[packet_path] = G.batch.decode(json.loads(raw))
        return G.lint_one(1, claim, cache[packet_path], ROOT, packet_path, corpus_cache)

    rejected = []
    for row in manifest["rows"]:
        ref = row["prior_claim"]
        claim = claim_at(ref)
        packet = G.packet_for((ROOT / ref["path"]).parent)
        result = run(claim, packet)
        rejected.append({"instrument_id": row["instrument_id"], "prior_claim": ref,
                         "review_defects": row["defects"], **result})

    # Resolve each actual filed record back to its exact submitted version and
    # packet, rather than treating every producer proposal as filed.
    submitted = {}
    for p in sorted(APOLLO.glob("*/packet/**/completion/COMPLETION.json")):
        data = json.loads(p.read_text())
        for m in data["members"]:
            if m.get("outcome") == "submit":
                submitted[m["instrument_id"]] = m
    filed = []
    for p in sorted((ROOT / "research/readiness/claims").glob("claude-2026-10-31-apollo-*.jsonl")):
        for line in p.read_bytes().splitlines():
            if not line.strip():
                continue
            claim = json.loads(line)
            member = submitted[claim["instrument_id"]]
            proposal = claim_at(member["claim"])
            if claim != proposal:
                raise ValueError(f"filed/proposed claim differs: {claim['instrument_id']}")
            packet = ROOT / member["packet"]["path"]
            if sha(packet.read_bytes()) != member["packet"]["sha256"]:
                raise ValueError(f"packet changed: {packet}")
            result = run(claim, packet)
            filed.append({"filed_path": str(p.relative_to(ROOT)), **result})
    assert len(rejected) == 40 and len(filed) == 254
    report = {
        "schema": "geddes-retrospective-comparison/v1",
        "implementation_sha256": IMPL_HASH,
        "apollo_source_commit": BASE,
        "rejected_versions": len(rejected),
        "rejected_versions_with_flags": sum(bool(r["flags"]) for r in rejected),
        "filed_versions": len(filed),
        "filed_versions_with_flags": sum(bool(r["flags"]) for r in filed),
        "recall_target": 12,
        "filed_flag_target_max": 5,
        "interpretation": "Retrospective, on the known development set; no held-out performance or savings inference. Rejected-version flags need comparison with the exact reviewer defect; unrelated flags do not establish recall. Filed-set flags are comparator false positives, not proof the original filed claim is correct.",
        "rejected": rejected,
        "filed": filed,
    }
    if sha((ROOT / "jobs/geddes/geddes.py").read_bytes()) != IMPL_HASH:
        raise ValueError("Geddes changed during evaluation; rerun after implementation freeze")
    (HERE / "EVALUATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    # A reproducible payload-size experiment on a real old batch. No model run
    # occurred, so this does not manufacture cache-read telemetry for Track B.
    packet = APOLLO / "g03/packet/PACKET.json"
    data = json.loads(packet.read_text())
    old_paths = [packet.parent / f for f in ("READ.md", "LOOKUPS.json", "LOOKUPS.details.json")]
    old_bytes = sum(p.stat().st_size for p in old_paths)
    views = []
    viewdir = HERE / "measurements/views"
    viewdir.mkdir(parents=True, exist_ok=True)
    for iid in sorted(data["dossiers"]):
        payload = (json.dumps(G.view(packet, iid), ensure_ascii=False, indent=2) + "\n").encode()
        path = viewdir / (iid.replace(":", "_") + ".json")
        path.write_bytes(payload)
        views.append({"instrument_id": iid, "path": str(path.relative_to(ROOT)),
                      "sha256": sha(payload), "bytes": len(payload)})
    size = {
        "schema": "geddes-payload-measurement/v1",
        "packet": str(packet.relative_to(ROOT)), "packet_sha256": sha(packet.read_bytes()),
        "baseline_files": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p.read_bytes()),
                            "bytes": p.stat().st_size} for p in old_paths],
        "baseline_bytes_per_full_read": old_bytes, "views": views,
        "view_bytes_for_one_read_each": sum(x["bytes"] for x in views),
        "full_bundle_bytes_if_reread_once_per_order": old_bytes * len(views),
        "actual_cache_read_tokens_saved": None,
        "actual_cache_read_note": "No required Sonnet producer/Opus reviewer runtime or worker transcripts were available. This is a static real-batch payload comparison; it is not measured cache token savings, labor savings, or a completed Track B live test.",
    }
    (HERE / "measurements/PAYLOAD_SIZE.json").write_text(json.dumps(size, indent=2) + "\n")
    (HERE / "measurements/APOLLO_COST.json").write_text(json.dumps(G.cost(APOLLO / "TELEMETRY.csv"), indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("rejected_versions", "rejected_versions_with_flags", "filed_versions", "filed_versions_with_flags")}))


if __name__ == "__main__":
    main()
