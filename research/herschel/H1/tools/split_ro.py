"""Copies replace_original rows (written by one worker into packets/b3/steps) into each order's own batch steps folder."""
import json
from pathlib import Path
H = Path("/home/claude/executive-orders/research/herschel/H1")
B = json.load(open(H / "tools/batches.json"))
src = H / "packets/b3/steps/REPLACE_ORIGINAL.jsonl"
rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()] if src.exists() else []
for b, ids in B.items():
    if b == "b3":
        continue
    mine = [r for r in rows if r.get("instrument_id") in ids]
    if mine:
        (H / "packets" / b / "steps").mkdir(parents=True, exist_ok=True)
        (H / "packets" / b / "steps/REPLACE_ORIGINAL.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in mine))
