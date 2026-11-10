"""Measure F6 (working-text gate) reach on main's compiled kit.

Usage: python -I measure_f6.py REFERENCE_REPO CODE_DIR DIAGNOSIS.csv TRACKER_CSV OUT.json

Proxy, per undecided order (OVERLAY_INPUTS): the frozen ORIGINAL is the compiled selected text. Text gate
before = acceptable_as_original; after = before or status_overlay.working_text_basis. "Some NO basis" = an
ACTING_PROVISIONS row targeting the order, a non-report OWN_TERMS row, or a known actor (ACTOR_TEXT). The
tracker's text tier (READINESS_BY_ORDER.csv) is reported beside each opened order to show agreement.
Machine-lead counts, not findings.
"""
import collections, csv, glob, json, sys
from pathlib import Path

ref, code, diag_path, tracker_path, out_path = map(Path, sys.argv[1:6])
sys.path.insert(0, str(code))
import status_overlay as O
kit = ref / "jobs/claim-kit/output"


def rows(stem):
    for f in sorted(glob.glob(str(kit / (stem + "*.jsonl")))):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                yield json.loads(line)


inputs = {r["instrument_id"]: r for r in rows("OVERLAY_INPUTS")}
ids = set(inputs)
terms = {}
for r in rows("OWN_TERMS"):
    if r["instrument_id"] in ids and r.get("kind") != "report_deadline":
        terms.setdefault(r["instrument_id"], set()).add(r["kind"])
acted = {r["target_id"] for r in rows("ACTING_PROVISIONS") if r.get("target_id") in ids}
with open(tracker_path, encoding="utf-8") as fh:
    tier = {r["instrument_id"]: r.get("text_evidence_tier") for r in csv.DictReader(fh)}
per = {}
for iid, inp in sorted(inputs.items()):
    sel = inp.get("selected") or {}
    original = {"grade": sel.get("grade"), "acceptable_as_original": bool(sel.get("acceptable_as_original")),
                "requires_page_check": bool(sel.get("requires_page_check"))} if sel else None
    dossier = {"original_source_id": "O", "evidence": {"O": original} if original else {}}
    if inp.get("working_text_confirmation") is not None:
        dossier["working_text_confirmation"] = inp["working_text_confirmation"]
    basis = O.working_text_basis(dossier) if original else None
    before = bool(original and original["acceptable_as_original"])
    no_basis = iid in acted or bool(terms.get(iid)) or bool(inp.get("known_actor_ids"))
    per[iid] = {"gate_before": before, "basis": basis, "gate_after": before or basis is not None,
                "page_check_owed": bool(original and original["requires_page_check"]), "no_basis": no_basis,
                "grade": original and original["grade"], "tracker_tier": tier.get(iid)}

opened = {i: r for i, r in per.items() if r["gate_after"] and not r["gate_before"]}
result = {
    "undecided": len(per),
    "text_gate_before": sum(r["gate_before"] for r in per.values()),
    "text_gate_opened": len(opened),
    "opened_by_basis": dict(collections.Counter(r["basis"] for r in opened.values())),
    "opened_by_grade": dict(collections.Counter(r["grade"] for r in opened.values())),
    "opened_page_check_owed": sum(r["page_check_owed"] for r in opened.values()),
    "opened_tracker_tier": dict(collections.Counter(r["tracker_tier"] for r in opened.values())),
    "opened_with_some_no_basis": sum(r["no_basis"] for r in opened.values()),
    "admissible_before": sum(r["gate_before"] and r["no_basis"] for r in per.values()),
    "admissible_after": sum(r["gate_after"] and r["no_basis"] for r in per.values()),
}
result["gain"] = result["admissible_after"] - result["admissible_before"]
diag = []
with open(diag_path, encoding="utf-8") as fh:
    for d in csv.DictReader(fh):
        r = per.get(d["instrument_id"])
        if r is None:
            continue
        diag.append({"instrument_id": d["instrument_id"], "probe": d["probe"], "final_primary_cause": d["final_primary_cause"],
                     "grade": r["grade"], "basis": r["basis"], "gate_opened": r["gate_after"] and not r["gate_before"],
                     "page_check_owed": r["page_check_owed"], "some_no_basis": r["no_basis"]})
result["diagnosed_gate_opened"] = [d["instrument_id"] for d in diag if d["gate_opened"]]
out_path.write_text(json.dumps({"summary": result, "diagnosed_rows": diag}, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
print(json.dumps(result, indent=1, sort_keys=True))
