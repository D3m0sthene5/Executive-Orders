"""Reproduce the received PR #40 projection, before the later code guard patches.

Default is read-only. Use --materialize only in a disposable checkout. Generated
job outputs are never changed; the integration commit also contains guard patches.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = "bd4450ab101cf0c14e736678614cd645c59312f0"
OURS = "cad6e4026e8a3736c3f858c69ad945135b56c1cc"
INCOMING = "874f970f5564b81135e6ff939ff77b56f8972a5a"
MERGED_TREE = "193e061d4c76b9c55145b7fcbe2089d761ed3a19"
ROOT = Path(__file__).resolve().parents[3]
LEDGER = "jobs/llull/ledger/"


def raw(ref, path):
    return subprocess.check_output(["git", "show", ref + ":" + path], cwd=ROOT)


def rows(ref, path):
    return [json.loads(line) for line in raw(ref, path).splitlines() if line.strip()]


def canon(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def remap(value, mapping):
    if isinstance(value, dict):
        return {key: remap(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [remap(item, mapping) for item in value]
    if isinstance(value, str):
        return re.sub(r"\b[LO]-20261020-\d+\b", lambda m: mapping.get(m.group(0), m.group(0)), value)
    return value


def main(materialize=False):
    changed = subprocess.check_output(["git", "diff", "--name-only", OURS, MERGED_TREE], cwd=ROOT, text=True).splitlines()
    assert all("/output/" not in p and not p.startswith("HANDOFF/") for p in changed)
    contents = {path: raw(MERGED_TREE, path) for path in changed}
    mapping = {"L-20261020-65": "L-20261020-78", **{
        f"O-20261020-{i}": f"O-20261020-{i + 10}" for i in range(49, 53)}}
    projections = {}
    merged_rows = {}
    for filename, key in (("forecasts.jsonl", "forecast_id"), ("outcomes.jsonl", "outcome_id")):
        path = LEDGER + filename
        original, incoming, current = rows(BASE, path), rows(INCOMING, path), rows(OURS, path)
        assert incoming[:len(original)] == original, "incoming rewrites existing ledger rows"
        additions = incoming[len(original):]
        occupied = {row[key] for row in current}
        last = max(int(row[key].rsplit("-", 1)[1]) for row in current + incoming)
        assigned = {}
        for row in additions:
            old = row[key]
            if old in occupied:
                last += 1
                assigned[old] = old.rsplit("-", 1)[0] + "-" + str(last)
            occupied.add(assigned.get(old, old))
        mapping.update(assigned)
        projected = []
        for row in additions:
            item = remap(copy.deepcopy(row), mapping)
            if row[key] in assigned:
                item["renumbered_from"] = row[key]
            projected.append(item)
        prefix = raw(OURS, path)
        contents[path] = prefix + b"".join((json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode() for row in projected)
        merged_rows[filename] = current + projected
        assert len({row[key] for row in merged_rows[filename]}) == len(merged_rows[filename])
        projections[filename] = {"added": len(projected), "renumbered": assigned,
            "total": len(merged_rows[filename]), "previous_bytes_preserved_as_prefix": contents[path].startswith(prefix)}
    rates_path = LEDGER + "base_rates.json"
    rates = json.loads(raw(OURS, rates_path))
    existing_keys = {row["key"] for row in rates["rows"]}
    incoming_rates = json.loads(raw(INCOMING, rates_path))
    for row in incoming_rates["rows"]:
        if row["key"] not in existing_keys:
            rates["rows"].append(remap(row, mapping))
    outcome_by_id = {row["outcome_id"]: row for row in merged_rows["outcomes.jsonl"]}
    pointer_repairs = []
    for rate in rates["rows"]:
        source, derived = rate.get("source"), rate.get("derived_from")
        if source in outcome_by_id and isinstance(derived, dict):
            correct = {**derived, "outcome_id": source, "forecast_id": outcome_by_id[source]["forecast_id"]}
            if correct != derived:
                pointer_repairs.append({"key": rate["key"], "before": derived, "after": correct})
                rate["derived_from"] = correct
    contents[rates_path] = (json.dumps(rates, indent=2, ensure_ascii=False) + "\n").encode()
    assert [row for row in rates["rows"] if row["key"] == "hit_rate.plant_catch_mountweazel_sealed_opus_sources"][-1]["value"] == 0.7
    queue = "research/readiness/FETCH_QUEUE.jsonl"
    original_queue = raw(OURS, queue)
    seen = {canon(json.loads(line)) for line in original_queue.splitlines() if line.strip()}
    extra = []
    for line in raw(INCOMING, queue).splitlines(keepends=True):
        if line.strip() and canon(json.loads(line)) not in seen:
            extra.append(line if line.endswith(b"\n") else line + b"\n")
            seen.add(canon(json.loads(line)))
    contents[queue] = original_queue + b"".join(extra)
    # Research artifacts retain their original bytes and source-local identifiers:
    # their pinned hashes must never change because of a ledger projection.
    if materialize:
        for path, data in contents.items():
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    journal = {"schema": "eo-late-production-reconciliation/v1", "base": BASE, "prior_repair": OURS,
        "incoming": INCOMING, "merge_tree": MERGED_TREE, "paths": sorted(contents),
        "ledger_projection": projections, "source_branch_aliases": mapping,
        "base_rate_pointer_repairs": pointer_repairs, "queue_lines_added": len(extra),
        "corrected_plant_rate_preserved": "7/10", "generated_outputs_modified": False,
        "historical_research_identifiers_remain_source_local": True,
        "new_claims_remain_provisional": True, "owner_method_rulings_adopted": False,
        "file_sha256": {p: hashlib.sha256(data).hexdigest() for p, data in contents.items()}}
    if materialize:
        (Path(__file__).parent / "LATE_PRODUCTION_RECONCILIATION.json").write_text(json.dumps(journal, indent=2) + "\n")
    print(json.dumps({k: journal[k] for k in ("ledger_projection", "queue_lines_added", "base_rate_pointer_repairs")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize", action="store_true")
    main(parser.parse_args().materialize)
