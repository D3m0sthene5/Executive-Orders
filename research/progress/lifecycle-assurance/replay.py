"""Bounded real-source checker -> tracker replay; never writes canonical outputs.

Run from repository root. Hydrate the exact inputs listed in input_paths() first.
Outputs default to a scratch directory; pass --out to retain an audit receipt.
"""
import argparse
import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

BASE = "f9c6d806ad059dcad7875ab3708715f20ea386df"
IID = "EO:12970"
CLAIMS = "research/readiness/claims/claude-lamm-s04-2026-10-20.jsonl"
PDF = "research/stage21/original_sources/EO_12970.pdf"
SOURCE_SHA = "9997afba89e10f60d9e2364d8d993bd5f441a9c97f4122d506a0414ff9b7e159"
TEXTS = ["jobs/fr-originals/" + p + "/texts/EO_12970.txt" for p in ("data/full_run", "output")]


def module(name, path, raw=None):
    obj = types.ModuleType(name)
    obj.__file__ = str(path)
    sys.modules[name] = obj
    exec(compile(raw if raw is not None else path.read_bytes(), str(path), "exec"), obj.__dict__)
    return obj


def input_paths(tracker):
    return [v for k, v in tracker.P.items() if k not in ("claims", "claim_gate_dir", "exhausted")] + [CLAIMS, PDF] + TEXTS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[3]
    args.out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(repo / "jobs/claim-checker"), str(repo / "jobs/readiness-tracker")]
    import checker as C
    import tracker as repaired
    original_raw = subprocess.check_output(["git", "show", BASE + ":jobs/readiness-tracker/tracker.py"], cwd=repo)
    baseline = module("assurance_baseline_tracker", repo / "jobs/readiness-tracker/tracker.py", original_raw)
    canonical = next(json.loads(l) for l in (repo / CLAIMS).read_text().splitlines()
                     if l.strip() and json.loads(l).get("instrument_id") == IID)
    holds = [json.loads(l) for l in (repo / "research/readiness/SOURCE_AUDIT_HOLDS.jsonl").read_text().splitlines() if l.strip()]
    assert not any(h["instrument_id"] == IID for h in holds), "Choose a control without an existing hold"
    assert hashlib.sha256((repo / PDF).read_bytes()).hexdigest() == SOURCE_SHA
    pinned = {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in input_paths(repaired)}
    source_registry = "jobs/fr-originals/data/full_run/SOURCES.jsonl"
    registry_bytes = subprocess.check_output(["git", "show", BASE + ":" + source_registry], cwd=repo)
    source = next(json.loads(l) for l in registry_bytes.splitlines()
                  if l.strip() and json.loads(l).get("sha256") == SOURCE_SHA)
    assert source["repo_path"] == PDF and source["instrument_ids"] == [IID]
    pinned[source_registry] = hashlib.sha256(registry_bytes).hexdigest()
    record = {"instrument_id":IID,"step":"savings_residuals",
              "searched":["ISOLATED ENGINEERING FIXTURE: asserted definitive govinfo, APP, NARA and presidential-library routes; not new historical search evidence"],
              "recorded_by":"assurance engineering fixture","recorded_on":"2026-10-29"}
    variants = []
    variants.append(("unchanged_retained_claim", copy.deepcopy(canonical), [], False))
    partial = copy.deepcopy(canonical)
    del partial["savings_residuals"]
    variants.append(("undisclosed_exhaustion", copy.deepcopy(partial), [record], False))
    partial["unresolved_material_gaps"] = ["ISOLATED FIXTURE: savings evidence exhausted; no new historical finding"]
    variants.append(("disclosed_exhaustion_control", copy.deepcopy(partial), [record], False))
    variants.append(("weak_ladder_evidence", copy.deepcopy(partial), [{**record,"note":"WEAK: only mirror routes"}], False))
    variants.append(("null_search_route", copy.deepcopy(partial), [{**record,"searched":[None]}], False))
    status = copy.deepcopy(canonical)
    status["unresolved_material_gaps"] = ["ISOLATED FIXTURE: provisional status unadopted"]
    variants.append(("exhausted_status", status, [{**record,"step":"provisional_status"}], True))
    variants.append(("no_claim", None, [{**record,"step":s} for s in ("clause_inventory","ending_or_current_basis","savings_residuals","counterevidence")], False))
    expected = {
        "unchanged_retained_claim": ("yes", "yes", "complete_claim"),
        "undisclosed_exhaustion": ("yes", "no", ""),
        "disclosed_exhaustion_control": ("yes", "yes", "machine_exhausted"),
        "weak_ladder_evidence": ("yes", "no", ""),
        "null_search_route": ("yes", "no", ""),
        "exhausted_status": ("yes", "no", ""),
        "no_claim": ("yes", "no", ""),
    }
    results = []
    with tempfile.TemporaryDirectory(prefix="eo-assurance-real-") as tmp:
        root = Path(tmp)
        for rel in input_paths(repaired):
            dst = root / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(repo / rel, dst)
        shutil.copytree(repo / "research/stage19/code", root / "research/stage19/code", ignore=shutil.ignore_patterns("__pycache__"))
        dst = root / "jobs/fr-originals/output/SOURCES.jsonl"; dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(source)+"\n")
        for name, claim, records, unset_status in variants:
            case_out = args.out / name; case_out.mkdir(exist_ok=True)
            # Restore status after each perturbation; a separate universe copy is
            # unnecessary because checker/tracker both read the true census.
            shutil.copyfile(repo / repaired.P["decided"], root / repaired.P["decided"])
            if unset_status:
                path=root / repaired.P["decided"]
                with path.open(newline="") as f:
                    reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
                with path.open("w",newline="") as f:
                    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(r for r in rows if r["instrument_id"]!=IID)
            claim_path=root / "research/readiness/claims/assurance.jsonl"
            claim_path.parent.mkdir(parents=True, exist_ok=True)
            claim_path.write_text(json.dumps(claim)+"\n" if claim else "")
            # Remove the original copied claim file: exactly the selected variant.
            (root / CLAIMS).unlink(missing_ok=True)
            (root / repaired.P["exhausted"]).write_text("".join(json.dumps(r)+"\n" for r in records))
            env={"REPO_ROOT":str(root),"OUTPUT_DIR":str(root / "jobs/claim-checker/output"),
                 "JOB_CACHE_DIR":str(root / "cache"),"CLAIM_CHECKER_VERIFY_DOWNLOADS":"0"}
            old={k:os.environ.get(k) for k in env};os.environ.update(env)
            try:
                with contextlib.redirect_stdout(io.StringIO()) as log:
                    C.main(["--claims",str(claim_path)])
                (case_out / "checker.log").write_text(log.getvalue())
            finally:
                for k,v in old.items():
                    if v is None:os.environ.pop(k,None)
                    else:os.environ[k]=v
            receipt=json.loads((root / "jobs/claim-checker/output/PER_CLAIM.json").read_text())
            selected=receipt["by_instrument"].get(IID)
            pair={}
            for label, tracker in (("before",baseline),("after",repaired)):
                orders, problems=tracker.build(str(root)); row=next(o for o in orders if o["instrument_id"]==IID)
                pair[label]={"row":row,"input_problems":problems}
            observed = (pair["before"]["row"]["ready_for_human_review"],
                        pair["after"]["row"]["ready_for_human_review"], pair["after"]["row"]["ready_tier"])
            assert observed == expected[name], (name, observed, expected[name])
            if name == "unchanged_retained_claim":
                assert selected["all_checks_passed"] is True
            if name == "disclosed_exhaustion_control":
                assert selected["steps_checker_passed"]["savings_residuals"] is False
            results.append({"case":name,"claim_sha256":C.load_gate(root).claim_sha(claim) if claim else None,
                            "checker":selected,**pair})
            (case_out / "RESULT.json").write_text(json.dumps(results[-1],indent=2)+"\n")
    # Source backing is a mechanical control; no substantive endorsement of the
    # retained 1996 endpoint, search coverage or producer rationale is made.
    report={"baseline":BASE,"source_pdf_sha256":SOURCE_SHA,"input_sha256":pinned,
            "scope":"Seven isolated source-backed checker-to-tracker variants; fixture exhaustion attestations are not research evidence. No canonical decision or count changed.",
            "results":results}
    (args.out / "RESULTS.json").write_text(json.dumps(report,indent=2)+"\n")
    for item in results:
        print(item["case"],item["before"]["row"]["ready_for_human_review"],"->",item["after"]["row"]["ready_for_human_review"],item["after"]["row"]["ready_tier"])

if __name__ == "__main__":
    main()
