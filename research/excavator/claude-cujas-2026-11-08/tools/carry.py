"""Cujas: carry the reviewed 2026-11-04 Tribonian rows (adapted from Haloander carry.py) into a fresh Haloander packet (clerical; no legal judgment).

usage: python3 -I carry.py PACKET_DIR TRIBONIAN_DIR
  For each member of the fresh packet, finds its single submitted row in the Theophilus r01-r03 packets
  (research/excavator/claude-theophilus-2026-11-05/rNN/packet/decisions.csv and clauses.csv) and copies the
  decision and clause rows into the fresh packet's sheets, except:
    * dossier_sha256 and working_text are taken from the FRESH sheet (the frozen dossier changed because
      Lachmann's current confirmation record now lists the Photius official printing as a skipped witness);
    * approved is set to false, and in working_text every identity_confirmed / complete_text_confirmed /
      pages_confirmed is set to false, so the producer must inspect and re-confirm before apply.
  Rationale keys referenced by copied rows are copied too. Writes CARRY.json with per-member provenance.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
OLD = Path(sys.argv[2])  # Tribonian packets extracted from origin/claude/tribonian-state 2bc32c6d4


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)


def main(pk):
    pk = Path(pk)
    dfields, drows = rows(pk / "decisions.csv")
    cfields, crows = rows(pk / "clauses.csv")
    rat = json.loads((pk / "RATIONALES.json").read_text())
    old = {}
    for b in ("o02", "o03", "o04", "o05", "o06", "o07", "o08", "o09", "a01"):
        op = OLD / b / "packet"
        _, od = rows(op / "decisions.csv")
        _, oc = rows(op / "clauses.csv")
        orat = json.loads((op / "RATIONALES.json").read_text())
        sha = {f: hashlib.sha256((op / f).read_bytes()).hexdigest() for f in ("decisions.csv", "clauses.csv", "RATIONALES.json")}
        for r in od:
            if r["outcome"] == "submit":
                old.setdefault(r["instrument_id"], []).append((b, r, [c for c in oc if c["instrument_id"] == r["instrument_id"]], orat, sha))
    report, new_clauses, copied = [], {}, set()
    for row in drows:
        iid = row["instrument_id"]
        hits = old.get(iid, [])
        rec = {"instrument_id": iid}
        if len(hits) != 1:
            rec["outcome"] = f"not_carried: {len(hits)} submitted Tribonian rows"
            report.append(rec)
            continue
        b, o, cl, orat, sha = hits[0]
        fresh_wt = row.get("working_text", "")
        fresh_sha = row["dossier_sha256"]
        for k in dfields:
            if k in o and k not in ("dossier_sha256", "working_text"):
                row[k] = o[k]
        row["approved"] = "false"
        if fresh_wt:
            wt = json.loads(fresh_wt)
            for c in wt.get("confirmations", []):
                for k in ("identity_confirmed", "complete_text_confirmed", "pages_confirmed"):
                    c[k] = False
            row["working_text"] = json.dumps(wt, ensure_ascii=False)
        row["dossier_sha256"] = fresh_sha
        new_clauses[iid] = [{k: c.get(k, "") for k in cfields} for c in cl]
        text = json.dumps(o) + json.dumps(cl)
        for key in set(re.findall(r"@rationale:([A-Za-z0-9_.:-]+)", text)):
            if key in rat and rat[key] != orat[key]:
                raise SystemExit(f"rationale key conflict {key}")
            rat[key] = orat[key]
            copied.add(key)
        rec.update(outcome="carried", source_batch=b, source_sha256=sha, prior_dossier_sha256=o["dossier_sha256"],
                   fresh_dossier_sha256=fresh_sha, clause_rows=len(cl))
        report.append(rec)
    out_c = [r for r in crows if r["instrument_id"] not in new_clauses]
    for row in drows:
        out_c += new_clauses.get(row["instrument_id"], [])
    with open(pk / "decisions.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=dfields)
        w.writeheader()
        w.writerows(drows)
    with open(pk / "clauses.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cfields)
        w.writeheader()
        w.writerows(out_c)
    (pk / "RATIONALES.json").write_text(json.dumps(rat, indent=1, ensure_ascii=False) + "\n")
    (pk / "CARRY.json").write_text(json.dumps({"schema": "cujas-carry/v1", "rationale_keys_copied": sorted(copied),
                                               "members": report}, indent=1) + "\n")
    print(json.dumps({"carried": sum(r["outcome"] == "carried" for r in report),
                      "not": [r["instrument_id"] for r in report if r["outcome"] != "carried"]}))


if __name__ == "__main__":
    main(sys.argv[1])
