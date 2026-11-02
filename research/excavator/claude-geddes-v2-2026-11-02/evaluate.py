#!/usr/bin/env python3
"""Retrospective comparison for the Geddes consistency and citing checks.

A copy of claude-geddes-2026-11-01/repair/evaluate.py reduced to the lint
comparison.  It reuses that folder's input pins and manifest, never writes
there, and compares each row's flags with the 2026-11-01 EVALUATION.json.
Review labels identify the comparator sets only; the linter receives no review
text, claim allowlist or outcome.
"""
from __future__ import annotations
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT / "research/excavator/claude-geddes-2026-11-01"
APOLLO = ROOT / "research/excavator/claude-apollo-2026-10-31"
sys.path.insert(0, str(ROOT / "jobs/geddes"))
import geddes as G  # noqa: E402
MODULES = ["geddes.py", "source_checks.py", "citation_checks.py", "event_checks.py", "name_checks.py",
           "consistency_checks.py", "citing_checks.py"]
NEW_CODES = {"stated_end_bound_contradicts_claimed_end", "stated_end_date_mismatch", "event_precedes_order",
             "own_order_date_precedes_signing", "attributed_row_wording_mismatch", "attributed_order_wording_mismatch",
             "attributed_order_citation_absent", "unaddressed_citing_instrument", "held_board_report_unaddressed",
             "created_name_changed_by_later_instrument", "reference_instrument_does_not_cite_order",
             "held_source_left_unpinned", "reasoning_order_suffix_sibling_mismatch",
             "dossier_source_grade_misdescribed", "stated_sha256_malformed", "stated_sha256_mismatch",
             "reported_empty_search_has_hit"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pins():
    return {f: sha((ROOT / "jobs/geddes" / f).read_bytes()) for f in MODULES}


def claim_at(ref):
    raw = (ROOT / ref["path"]).read_bytes()
    if sha(raw) != ref.get("file_sha256", ref.get("sha256")):
        raise ValueError("changed claim file: " + ref["path"])
    line = raw.splitlines()[ref["line"] - 1]
    if ref.get("record_sha256") and sha(line) != ref["record_sha256"]:
        raise ValueError("changed claim record: " + ref["path"])
    return json.loads(line)


def main():
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    code_pins = pins()
    input_pins = json.loads((OLD / "repair/INPUT_PINS.json").read_text())["sha256"]
    for rel, digest in input_pins.items():
        if sha((ROOT / rel).read_bytes()) != digest:
            raise ValueError("input changed: " + rel)
    manifest = json.loads((OLD / "inventory/MANIFEST.json").read_text())
    old = json.loads((OLD / "repair/EVALUATION.json").read_text())
    old_flags = {("rejected", r["instrument_id"]): r["flags"] for r in old["rejected"]}
    old_flags.update({("filed", r["instrument_id"]): r["flags"] for r in old["filed"]})
    decoded = {}

    def run(claim, packet_path, cache):
        if packet_path not in decoded:
            decoded[packet_path] = G.batch.decode(json.loads(packet_path.read_bytes()))
        return G.lint_one(1, claim, decoded[packet_path], ROOT, packet_path, cache)

    rows = {"rejected": [], "filed": []}
    with G.NC.Snapshot(ROOT) as name_cache:
        cache = {"name": name_cache}
        for row in manifest["rows"]:
            ref = row["prior_claim"]
            claim = claim_at(ref)
            result = run(claim, G.packet_for((ROOT / ref["path"]).parent), cache)
            rows["rejected"].append({"instrument_id": row["instrument_id"], "prior_claim": ref, **result})
        submitted = {}
        for p in sorted(APOLLO.glob("*/packet/**/completion/COMPLETION.json")):
            for m in json.loads(p.read_text())["members"]:
                if m.get("outcome") == "submit":
                    submitted[m["instrument_id"]] = m
        for p in sorted((ROOT / "research/readiness/claims").glob("claude-2026-10-31-apollo-*.jsonl")):
            for line in p.read_bytes().splitlines():
                if line.strip():
                    claim = json.loads(line)
                    member = submitted[claim["instrument_id"]]
                    if claim != claim_at(member["claim"]):
                        raise ValueError("filed/proposed claim differs: " + claim["instrument_id"])
                    packet = ROOT / member["packet"]["path"]
                    if sha(packet.read_bytes()) != member["packet"]["sha256"]:
                        raise ValueError("packet changed: " + str(packet))
                    rows["filed"].append({"filed_path": str(p.relative_to(ROOT)), **run(claim, packet, cache)})
    assert len(rows["rejected"]) == 40 and len(rows["filed"]) == 254
    if pins() != code_pins:
        raise ValueError("Geddes changed during evaluation; rerun after implementation freeze")

    def strip(flag):
        return {k: v for k, v in flag.items() if k != "flag_id"}

    def summary(kind):
        out = []
        for r in rows[kind]:
            new = [strip(f) for f in r["flags"] if f.get("code") in NEW_CODES]
            before = [strip(f) for f in old_flags.get((kind, r["instrument_id"]), [])]
            other = [strip(f) for f in r["flags"] if f.get("code") not in NEW_CODES]
            out.append({"instrument_id": r["instrument_id"], "new_check_flags": new,
                        "prior_module_flags_now": len(other), "prior_module_flags_2026_11_01": len(before),
                        "prior_module_flags_unchanged": other == before})
        return out

    rejected, filed = summary("rejected"), summary("filed")
    report = {
        "schema": "geddes-retrospective-comparison/v2",
        "started_utc": started, "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "module_sha256": code_pins,
        "input_pins": str((OLD / "repair/INPUT_PINS.json").relative_to(ROOT)),
        "comparator": str((OLD / "repair/EVALUATION.json").relative_to(ROOT)),
        "rejected_versions": 40, "filed_versions": 254,
        "rejected_with_any_flag": sum(bool(r["flags"]) for r in rows["rejected"]),
        "filed_with_any_flag": sum(bool(r["flags"]) for r in rows["filed"]),
        "rejected_with_new_check_flags": sum(bool(r["new_check_flags"]) for r in rejected),
        "filed_with_new_check_flags": sum(bool(r["new_check_flags"]) for r in filed),
        "prior_module_flags_unchanged_all": all(r["prior_module_flags_unchanged"] for r in rejected + filed),
        "interpretation": "Known development set, not held-out validation. Exact recall credit requires matching a new flag to the reviewer's recorded defect; see REPORT.md.",
        "rejected": rejected,
        "filed": [r for r in filed if r["new_check_flags"] or not r["prior_module_flags_unchanged"]],
        "coverage_gap_codes_new_modules": sorted({g.get("code") for r in rows["rejected"] + rows["filed"] for g in r["coverage_gaps"]
                                                  if str(g.get("code", "")).startswith(("citing_", "created_name", "reference_", "unpinned_", "row_description", "order_", "reasoning_order_not", "reasoning_order_sibling", "search_output"))}),
    }
    (HERE / "EVALUATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("rejected_with_any_flag", "filed_with_any_flag", "rejected_with_new_check_flags",
                                              "filed_with_new_check_flags", "prior_module_flags_unchanged_all")}))


if __name__ == "__main__":
    main()
