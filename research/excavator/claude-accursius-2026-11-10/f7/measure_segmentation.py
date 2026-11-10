"""F7 reach measure for the clause-segmenter heading fix.

Usage: python -I measure_segmentation.py REF_REPO OLD_EXCAVATE NEW_EXCAVATE OUT_CSV

For every order in the reference kit's CLAUSES.jsonl whose held text file is on disk, re-run segment()
with the old and the new excavate.py on that same text and compare the scope ids. REF_REPO is the
read-only reference checkout (origin/main with outputs). Undecided = not in DECIDED_CASE_COMPLETENESS_RECONCILED.csv.
Also checks that the OLD code reproduces the recorded inventory (fidelity of the proxy).
"""
import csv
import importlib.util
import json
import sys
from pathlib import Path

ref, old_path, new_path, out_csv = (Path(a) for a in sys.argv[1:5])


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


old, new = load(old_path, "exc_old"), load(new_path, "exc_new")
decided = {r["instrument_id"] for r in csv.DictReader(open(ref / "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv", encoding="utf-8", newline=""))}
rows, stats = [], {"orders": 0, "text_missing": 0, "old_reproduces_recorded": 0, "old_differs_from_recorded": 0}
for line in open(ref / "jobs/claim-kit/output/CLAUSES.jsonl", encoding="utf-8"):
    rec = json.loads(line)
    iid = rec["instrument_id"]
    src = rec.get("source") or {}
    tp = ref / (src.get("text_path") or "-")
    if not src.get("text_path") or not tp.is_file():
        stats["text_missing"] += 1
        continue
    text = tp.read_text(encoding="utf-8")
    stats["orders"] += 1
    recorded = [c["scope_id"] for c in rec["clauses"]]
    try:
        a = [c["scope_id"] for c in old.segment(iid, text, src)["clauses"]]
        b = [c["scope_id"] for c in new.segment(iid, text, src)["clauses"]]
    except Exception as exc:  # report, never hide
        rows.append({"instrument_id": iid, "undecided": iid not in decided, "old_n": "", "new_n": "", "recorded_n": len(recorded), "changed": "ERROR", "detail": repr(exc)[:200]})
        continue
    stats["old_reproduces_recorded" if a == recorded else "old_differs_from_recorded"] += 1
    if a != b:
        rows.append({"instrument_id": iid, "undecided": iid not in decided, "old_n": len(a), "new_n": len(b), "recorded_n": len(recorded),
                     "changed": "yes", "detail": "; ".join(sorted(set(b) - set(a)))[:160]})
# Orders that already have a claim: do the claimed scope ids still exist, and with the same text span?
claimed = {}
for cp in sorted((ref / "research/readiness/claims").glob("*.jsonl")):
    for line in open(cp, encoding="utf-8", errors="replace"):
        try:
            c = json.loads(line)
        except ValueError:
            continue
        iid = c.get("instrument_id")
        for cl in c.get("operative_clauses") or []:
            if isinstance(cl, dict) and cl.get("scope_id"):
                claimed.setdefault(iid, set()).add(cl["scope_id"])
claim_rows = []
for rec in (json.loads(l) for l in open(ref / "jobs/claim-kit/output/CLAUSES.jsonl", encoding="utf-8")):
    iid = rec["instrument_id"]
    if iid not in claimed:
        continue
    src = rec.get("source") or {}
    tp = ref / (src.get("text_path") or "-")
    if not src.get("text_path") or not tp.is_file():
        continue
    text = tp.read_text(encoding="utf-8")
    o = {c["scope_id"]: c["text"] for c in old.segment(iid, text, src)["clauses"]}
    n = {c["scope_id"]: c["text"] for c in new.segment(iid, text, src)["clauses"]}
    gone = sorted(i for i in claimed[iid] if i not in n and i in o)
    moved = sorted(i for i in claimed[iid] if i in n and i in o and n[i] != o[i])
    if gone or moved:
        claim_rows.append({"instrument_id": iid, "claimed_scope_ids": len(claimed[iid]), "ids_that_disappear": "; ".join(gone),
                           "ids_kept_with_different_text": "; ".join(moved)})
with open(out_csv.with_name("claimed_scope_id_changes.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["instrument_id", "claimed_scope_ids", "ids_that_disappear", "ids_kept_with_different_text"])
    w.writeheader()
    w.writerows(claim_rows)
stats["claimed_orders"] = len(claimed)
stats["claimed_orders_with_changed_scope_ids_or_text"] = len(claim_rows)
with open(out_csv, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["instrument_id", "undecided", "old_n", "new_n", "recorded_n", "changed", "detail"])
    w.writeheader()
    w.writerows(rows)
changed = [r for r in rows if r["changed"] == "yes"]
stats.update(changed_total=len(changed), changed_undecided=sum(1 for r in changed if r["undecided"]),
             errors=sum(1 for r in rows if r["changed"] == "ERROR"))
print(json.dumps(stats, indent=1))
