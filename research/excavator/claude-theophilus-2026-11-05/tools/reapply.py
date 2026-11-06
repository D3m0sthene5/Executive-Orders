"""Reapply reviewed 2026-11-04 decision rows unchanged into a fresh Theophilus packet (clerical; no judgment).

usage: python3 -I reapply.py BATCH
  For each member of BATCH (from the coordinator's batches.json), finds the Tribonian batch whose completion
  receipt held the exact reviewed claim (precheck/meta.json), reads that batch's decisions.csv and clauses.csv
  from the preserved branch origin/claude/tribonian-state, and copies the member's rows byte-for-byte into the
  new packet's sheets, provided the new dossier fingerprint equals the old one. A member whose fingerprint
  changed is left untouched (unresolved) and reported, because a changed dossier needs new production.
  Shared RATIONALES keys referenced by copied rows are copied too, and must not conflict with existing keys.
  Writes REAPPLY.json in the packet with per-member outcome and source hashes.
"""
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/claude/executive-orders")
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/theophilus")
REF = "origin/claude/tribonian-state"
OLD = "research/excavator/claude-tribonian-2026-11-04/{b}/packet/{f}"


def show(path):
    r = subprocess.run(["git", "show", f"{REF}:{path}"], cwd=REPO, capture_output=True)
    if r.returncode:
        raise SystemExit(f"cannot read {REF}:{path}")
    return r.stdout


def rows(text):
    rd = csv.DictReader(io.StringIO(text.decode("utf-8-sig")))
    return rd.fieldnames, list(rd)


def main(batch):
    ids = json.loads((S / "batches.json").read_text())[batch]
    meta = json.loads((S / "precheck/meta.json").read_text())
    pk = REPO / f"research/excavator/claude-theophilus-2026-11-05/{batch}/packet"
    dfields, drows = rows((pk / "decisions.csv").read_bytes())
    cfields, crows = rows((pk / "clauses.csv").read_bytes())
    rat = json.loads((pk / "RATIONALES.json").read_text())
    by_new = {r["instrument_id"]: r for r in drows}
    report, new_clauses, copied = [], {}, set()
    old_cache = {}
    for iid in ids:
        ob = meta[iid]["batch"]
        if ob not in old_cache:
            raw_d, raw_c, raw_r = (show(OLD.format(b=ob, f=f)) for f in ("decisions.csv", "clauses.csv", "RATIONALES.json"))
            old_cache[ob] = (rows(raw_d), rows(raw_c), json.loads(raw_r),
                             {f: hashlib.sha256(x).hexdigest() for f, x in
                              (("decisions.csv", raw_d), ("clauses.csv", raw_c), ("RATIONALES.json", raw_r))})
        (odf, odr), (ocf, ocr), orat, shas = old_cache[ob]
        old = [r for r in odr if r["instrument_id"] == iid]
        rec = {"instrument_id": iid, "source_batch": ob, "source_ref": REF, "source_sha256": shas}
        if len(old) != 1 or old[0]["outcome"] != "submit":
            rec["outcome"] = "not_reapplied: no single submitted reviewed row"
        elif old[0]["dossier_sha256"] != by_new[iid]["dossier_sha256"]:
            rec["outcome"] = "not_reapplied: dossier fingerprint changed"
        else:
            o = old[0]
            row = {k: o.get(k, "") for k in dfields}
            missing = [k for k in dfields if k not in o]
            row["publication_kind"] = row.get("publication_kind") or ("whole_case" if "publication_kind" in missing else "")
            by_new[iid].clear(); by_new[iid].update(row)
            cl = [{k: r.get(k, "") for k in cfields} for r in ocr if r["instrument_id"] == iid]
            new_clauses[iid] = cl
            text = json.dumps(o) + json.dumps(cl)
            for key in set(re.findall(r"@rationale:([A-Za-z0-9_.:-]+)", text)):
                if key in rat and rat[key] != orat[key]:
                    raise SystemExit(f"rationale key conflict {key}")
                rat[key] = orat[key]; copied.add(key)
            rec["outcome"] = "reapplied_unchanged"
            rec["new_fields_defaulted"] = missing
            rec["clause_rows"] = len(cl)
        report.append(rec)
    out_c = [r for r in crows if r["instrument_id"] not in new_clauses]
    for iid in ids:
        out_c += new_clauses.get(iid, [])
    with open(pk / "decisions.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=dfields); w.writeheader(); w.writerows(drows)
    with open(pk / "clauses.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cfields); w.writeheader(); w.writerows(out_c)
    (pk / "RATIONALES.json").write_text(json.dumps(rat, indent=1, ensure_ascii=False) + "\n")
    (pk / "REAPPLY.json").write_text(json.dumps({"schema": "theophilus-reapply/v1", "batch": batch,
                                                  "rationale_keys_copied": sorted(copied), "members": report}, indent=1) + "\n")
    print(json.dumps({"batch": batch, "reapplied": sum(r["outcome"] == "reapplied_unchanged" for r in report),
                      "not": [r["instrument_id"] for r in report if r["outcome"] != "reapplied_unchanged"],
                      "defaulted": sorted({k for r in report for k in r.get("new_fields_defaulted", [])})}))


if __name__ == "__main__":
    main(sys.argv[1])
