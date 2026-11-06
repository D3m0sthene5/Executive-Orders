"""H6 review-set builder (coordinator tool; no judgment). usage: python3 -I build_set.py BATCH [APPLIED_DIR]
D1/D2: copies APPLIED_DIR/CLAIMS.proposed.jsonl. U4 and HAND U1-U3: one sheet record per order (status decision,
decisions.csv row, clauses.csv rows, original-text record). Writes scratch review/BATCH/SET.jsonl."""
import csv, json, sys
from pathlib import Path
R = Path("/home/claude/executive-orders"); S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
b = sys.argv[1]; B = json.loads((R / "research/herschel/H6/tools/batches.json").read_text())
d = S / "review" / b; d.mkdir(parents=True, exist_ok=True); out = d / "SET.jsonl"
if b in ("D1", "D2"):
    out.write_bytes((Path(sys.argv[2]) / "CLAIMS.proposed.jsonl").read_bytes())
else:
    pk = R / "research/herschel/H6/packets" / (b if b == "U4" else "HAND/" + b)
    dec = {r["instrument_id"]: r for r in csv.DictReader(open(pk / "decisions.csv", newline="", encoding="utf-8"))}
    cl = {}
    for r in csv.DictReader(open(pk / "clauses.csv", newline="", encoding="utf-8")): cl.setdefault(r["instrument_id"], []).append(r)
    lines = []
    for i in B[b]:
        n = i.split(":", 1)[1]
        sp = pk / ("undecided/EO_%s/STATUS_DECISION.json" % n if b == "U4" else "status/EO_%s.json" % n)
        op = pk / "original_text" / f"EO_{n}.json"
        rec = {"instrument_id": i, "status_decision": json.loads(sp.read_text()) if sp.exists() else None,
               "decision_row": dec.get(i), "clause_rows": cl.get(i, []),
               "original_text": json.loads(op.read_text()) if op.exists() else None}
        lines.append(json.dumps(rec, ensure_ascii=False) + "\n")
    out.write_text("".join(lines))
print(out, sum(1 for _ in open(out)))
