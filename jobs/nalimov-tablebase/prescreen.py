"""Nalimov pre-screen: run the kit's own assembler and the actual claim checker on every draft before any verifier
token is spent. Zero tokens.

For each complete draft: the lifecycle sheet is built exactly as `jobs/claim-kit/batch.py` `_apply_rows` builds it
from a decisions.csv row and its clauses.csv rows; the claim is assembled on the experimental dossier exactly as
`status_overlay.experimental_dossier` builds it (the frozen base dossier with the proposed status), then
`assemble.check_claim` and `jobs/claim-checker/checker.py --claims` run on the result, with downloads off. Only a draft
whose claim assembles, passes check_claim and passes every checker step goes on to verification.

This is a screen, not the filing route: the real claim is assembled again by `overlay-propose` after the status
review, and checked again by `batch-check` and completion. The two must agree; when they do not, the filing route
wins. The kit code is imported from the data checkout (`--data`), so its compiler pins match its outputs.

    python -I jobs/nalimov-tablebase/prescreen.py --data CHECKOUT --evidence SCRATCH/evidence --out SCRATCH/prescreen [--mentions CSV]
"""
from __future__ import annotations

import argparse
import csv
import glob
import importlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drafter as D  # noqa: E402

csv.field_size_limit(1 << 30)


def canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def kit(data):
    sys.path.insert(0, str(Path(data) / "jobs/claim-kit"))
    return (importlib.import_module("assemble"), importlib.import_module("batch"),
            importlib.import_module("fragment_cache"))


def sheet_from_draft(A, B, dossier, dr):
    """The lifecycle sheet batch._apply_rows builds from this draft's row and clause rows."""
    r, shared = dr["row"], {}
    sheet = A.blank_sheet(dossier, r["agent"])
    for k in ("approved", "original_confirmed", "original_pages_confirmed", "inventory_confirmed"):
        sheet[k] = B.boolean(r[k])
    if r.get("working_text"):
        disclosure = B.json_field(r["working_text"], dict)
        if disclosure:
            sheet["working_text"] = disclosure
    checks = {k: B.rationale(r[k], shared) for k in ("earlier_end_check", "scope_check", "independent_command_check",
                                                     "savings_check")}
    sheet["research_rationale"] = B.rationale(r["research_rationale"], shared) + "\nMember checks: " + B.canon(checks)
    sheet["savings"] = {"state": r["savings_state"] or None, "source_id": r["savings_source_id"] or None,
                        "reason": B.rationale(r["savings_reason"], shared)}
    sheet["search_ids"] = B.json_field(r["search_ids"], list)
    sheet["conflict_resolutions"] = B.json_field(r["conflict_resolutions"], dict)
    sheet["unresolved_material_gaps"] = B.json_field(r["unresolved_material_gaps"], list)
    sheet["clauses"] = []
    for c in dr["clauses"]:
        clause = {k: (c[k] or None) for k in ("scope_id", "clause_id", "state", "end_id", "effective_date",
                                              "current_basis_id", "current_legal_basis", "checked_through")}
        if c.get("mechanism"):
            clause["mechanism"] = c["mechanism"]
        clause.update(effective_date_confirmed=B.boolean(c["effective_date_confirmed"] or "false"),
                      later_event_ids=B.json_field(c["later_event_ids"] or "[]", list),
                      later_events=B.json_field(c["later_events"] or "[]", list), reason=B.rationale(c["reason"], shared))
        sheet["clauses"].append(clause)
    sheet["inventory_overrides"] = []
    return sheet


def experimental(A, evidence, status="no"):
    dossier = deepcopy(evidence["base_dossier"])
    dossier["whole_order_status"] = status
    dossier["fingerprint"] = A.canonical_sha(dossier)
    return dossier


def run(data, evidence_dir, out, mentions_csv=None):
    data, out = Path(data).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    A, B, F = kit(data)
    index = D.mentions_index(csv.DictReader(open(mentions_csv, encoding="utf-8"))) if mentions_csv else None
    results, claims = {}, []
    with F.policy_index(data):
        for p in sorted(glob.glob(str(Path(evidence_dir) / "EO_*.json"))):
            ev = json.loads(Path(p).read_text(encoding="utf-8"))
            iid = ev["instrument_id"]
            prow = {"working_text": canon(A.blank_sheet(ev["base_dossier"], D.AGENT).get("working_text", {}))}
            dr = D.draft(ev, prepared_row=prow, mentions=D.mentions_for(index, iid) if index else None)
            if not dr.ok:
                results[iid] = {"stage": "drafter", "errors": dr["blockers"]}
                continue
            dossier = experimental(A, ev)
            sheet = sheet_from_draft(A, B, dossier, dr)
            claim, errors = A.assemble(sheet, dossier, data)
            if errors or claim is None:
                results[iid] = {"stage": "assemble", "errors": errors}
                continue
            gate = A.check_claim(claim, data, dossier)
            if gate:
                results[iid] = {"stage": "check_claim", "errors": [str(g) for g in gate]}
                continue
            results[iid] = {"stage": "checker", "claim_sha256": A.canonical_sha(claim)}
            claims.append(claim)
    if claims:
        (out / "CLAIMS.proposed.jsonl").write_text("".join(canon(c) + "\n" for c in claims), encoding="utf-8")
        target = out / "actual-checker"
        target.mkdir()
        env = dict(os.environ, REPO_ROOT=str(data), OUTPUT_DIR=str(target), JOB_LIMIT="",
                   JOB_CACHE_DIR=str(out / ".validation-cache"), CLAIM_CHECKER_VERIFY_DOWNLOADS="0", PYTHONIOENCODING="utf-8")
        with (out / "CHECKER.log").open("w", encoding="utf-8") as log:
            rc = subprocess.run([sys.executable, "-B", str(data / "jobs/claim-checker/checker.py"), "--claims",
                                 str(out / "CLAIMS.proposed.jsonl")], cwd=data, env=env, stdout=log,
                                stderr=subprocess.STDOUT).returncode
        if rc:
            raise RuntimeError(f"claim-checker failed (exit {rc}); see {out / 'CHECKER.log'}")
        per = json.loads((target / "PER_CLAIM.json").read_text(encoding="utf-8"))["by_instrument"]
        for iid, row in per.items():
            res = results.get(iid) or {}
            if res.get("claim_sha256") != row.get("claim_sha256"):
                res.update(stage="checker", errors=["checker read a different claim hash"])
            elif row.get("all_checks_passed") is True:
                res.update(stage="passed")
            else:
                res.update(stage="checker", errors=[f"{f.get('step')}:{f.get('check')}:{f.get('status')}@{f.get('field')}"
                                                    for f in row.get("failures") or []] or
                           [f"mechanical {row.get('mechanical_result')}; unverified {row.get('unverified')}"])
    summary = {"schema": "nalimov-prescreen/v1", "data": str(data), "drafter": D.DRAFTER_VERSION,
               "stages": {}, "passed": sorted(i for i, r in results.items() if r.get("stage") == "passed"),
               "results": results}
    for r in results.values():
        summary["stages"][r["stage"]] = summary["stages"].get(r["stage"], 0) + 1
    (out / "PRESCREEN.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--evidence", required=True, help="folder of frozen EVIDENCE json files (EO_N.json)")
    ap.add_argument("--out", required=True, help="new folder, outside the repository")
    ap.add_argument("--mentions")
    a = ap.parse_args(argv)
    s = run(a.data, a.evidence, a.out, a.mentions)
    print(json.dumps({"stages": s["stages"], "passed": len(s["passed"])}, indent=1))


if __name__ == "__main__":
    main()
