"""Measure F5 (OWN_TEXT basis, TERM retyping) and F6 (working-text gate) reach on main's compiled kit.

Usage: python -I measure_f5_f6.py REFERENCE_REPO CODE_DIR DIAGNOSIS.csv OUT.json

REFERENCE_REPO is a checkout of origin/main with jobs/claim-kit/output (the compiled kit) and every held
text; CODE_DIR is this branch's jobs/claim-kit. Proxy, per undecided order (OVERLAY_INPUTS):
- text gate: before = selected text acceptable_as_original; after = before or status_overlay.working_text_basis.
- NO basis: before = an ACTING_PROVISIONS row targeting the order, a non-report OWN_TERMS row, or a known actor
  (its ACTOR_TEXT id); after adds OWN_TEXT records and the retyped TERM kinds (own_terms rerun on the text).
- YES basis (CURRENT) is F3's, not counted here.
- admissible = text gate passes and some NO basis exists. A machine lead count, not a finding.
"""
import csv, glob, json, sys
from pathlib import Path

ref, code, diag_path, out_path = map(Path, sys.argv[1:5])
sys.path.insert(0, str(code))
import excavate as E, own_text as T, status_overlay as O
kit = ref / "jobs/claim-kit/output"

def rows(stem):
    for f in sorted(glob.glob(str(kit / (stem + "*.jsonl")))):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                yield json.loads(line)

inputs = {r["instrument_id"]: r for r in rows("OVERLAY_INPUTS")}
ids = set(inputs)
clauses = {r["instrument_id"]: r["clauses"] for r in rows("CLAUSES") if r["instrument_id"] in ids}
terms = {}
for r in rows("OWN_TERMS"):
    if r["instrument_id"] in ids:
        terms.setdefault(r["instrument_id"], set()).add(r["kind"])
acted = {r["target_id"] for r in rows("ACTING_PROVISIONS") if r.get("target_id") in ids}
result, per = {"undecided": len(ids)}, {}
for iid, inp in sorted(inputs.items()):
    sel = inp.get("selected")
    rec = {"has_text": bool(sel)}
    if sel:
        try:
            text = (ref / sel["text_path"]).read_bytes().decode("utf-8")
        except OSError:
            text = None
        original = {"text": text, "char_start": 0, "char_end": len(text or ""), "source": sel["source"],
                    "signing_date": sel.get("signing_date"),
                    "acceptable_as_original": bool(sel.get("acceptable_as_original")), "grade": sel.get("grade")}
        dossier = {"original_source_id": "O", "evidence": {"O": original}}
        if inp.get("working_text_confirmation") is not None:
            dossier["working_text_confirmation"] = inp["working_text_confirmation"]
        rec["gate_before"] = original["acceptable_as_original"]
        rec["working_text_basis"] = O.working_text_basis(dossier)
        rec["gate_after"] = rec["gate_before"] or rec["working_text_basis"] is not None
        rec["page_check_owed"] = bool(sel.get("requires_page_check"))
        own = T.records(iid, original, clauses.get(iid, [])) if text else {}
        rec["own_text_kind"] = next(iter(own.values()))["own_text_kind"] if own else None
        new_terms = {t["kind"] for t in E.own_terms(iid, text, dict(sel["source"], signing_date=sel.get("signing_date")), clauses.get(iid, []))} if text else set()
    else:
        rec.update(gate_before=False, gate_after=False, own_text_kind=None, working_text_basis=None)
        new_terms = set()
    old_terms = {k for k in terms.get(iid, set()) if k != "report_deadline"}
    rec["no_basis_before"] = iid in acted or bool(old_terms) or bool(inp.get("known_actor_ids"))
    rec["retyped_term"] = bool((new_terms - {"report_deadline"}) - old_terms) and not old_terms
    rec["no_basis_f5"] = rec["no_basis_before"] or bool(rec["own_text_kind"]) or rec["retyped_term"]
    rec["admissible_before"] = rec["gate_before"] and rec["no_basis_before"]
    rec["admissible_f5"] = rec["gate_before"] and rec["no_basis_f5"]
    rec["admissible_f6"] = rec["gate_after"] and rec["no_basis_before"]
    rec["admissible_f5_f6"] = rec["gate_after"] and rec["no_basis_f5"]
    per[iid] = rec

def count(pred):
    return sum(1 for r in per.values() if pred(r))
result.update(
    own_text_orders=count(lambda r: r["own_text_kind"]),
    own_text_spent_on_issue=count(lambda r: r["own_text_kind"] == "spent_on_issue"),
    own_text_amends_parent=count(lambda r: r["own_text_kind"] == "amends_parent"),
    own_text_without_prior_no_basis=count(lambda r: r["own_text_kind"] and not r["no_basis_before"]),
    retyped_term_only=count(lambda r: r["retyped_term"] and not r["no_basis_before"] and not r["own_text_kind"]),
    text_gate_opened_by_f6=count(lambda r: r["gate_after"] and not r["gate_before"]),
    text_gate_opened_by_basis={b: count(lambda r, b=b: r["working_text_basis"] == b and not r["gate_before"])
                               for b in ("tracker_original_supported", "lachmann_confirmation")},
    text_gate_opened_page_check_owed=count(lambda r: r["gate_after"] and not r["gate_before"] and r.get("page_check_owed")),
    admissible_before=count(lambda r: r["admissible_before"]),
    gain_f5_alone=count(lambda r: r["admissible_f5"] and not r["admissible_before"]),
    gain_f6_alone=count(lambda r: r["admissible_f6"] and not r["admissible_before"]),
    gain_f5_and_f6=count(lambda r: r["admissible_f5_f6"] and not r["admissible_before"]),
    admissible_after_f5_f6=count(lambda r: r["admissible_f5_f6"]))
diag = []
with open(diag_path, encoding="utf-8") as fh:
    for d in csv.DictReader(fh):
        r = per.get(d["instrument_id"])
        if r is None:
            diag.append({"instrument_id": d["instrument_id"], "probe": d["probe"], "note": "not undecided on main now"})
            continue
        diag.append({"instrument_id": d["instrument_id"], "probe": d["probe"], "final_primary_cause": d["final_primary_cause"],
                     "final_best_status": d["final_best_status"], "own_text_kind": r["own_text_kind"],
                     "working_text_basis": r["working_text_basis"], "admissible_before": r["admissible_before"],
                     "admissible_after_f5_f6": r["admissible_f5_f6"],
                     "gained": r["admissible_f5_f6"] and not r["admissible_before"]})
result["diagnosed"] = {"rows": len(diag),
                       "gained_admissible_basis": [d["instrument_id"] for d in diag if d.get("gained")],
                       "own_text": [d["instrument_id"] for d in diag if d.get("own_text_kind")],
                       "working_text_opened": [d["instrument_id"] for d in diag if d.get("working_text_basis")]}
for probe in sorted({d["probe"] for d in diag}):
    sub = [d for d in diag if d["probe"] == probe]
    result["diagnosed"]["gained_" + probe] = sum(bool(d.get("gained")) for d in sub)
out_path.write_text(json.dumps({"summary": result, "diagnosed_rows": diag}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=1, sort_keys=True))
