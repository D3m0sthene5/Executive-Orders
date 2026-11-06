"""Append one review batch to BATCHES.json and run the Bentham gate (coordinator tool).
usage: python3 -I add_batch.py BATCH ATTEMPTED SUBMITTED FILED CONTROLS_MISSED USD KIND NOTE"""
import json, subprocess, sys
from pathlib import Path
H = Path("/home/claude/executive-orders/research/herschel/H2")
b, att, sub, fil, miss, usd, kind, note = sys.argv[1:9]
p = H / "BATCHES.json"
rows = json.loads(p.read_text()) if p.exists() else []
rows = [r for r in rows if r["batch"] != b] + [{"batch": b, "attempted": int(att), "submitted": int(sub), "filed": int(fil),
        "controls_missed": int(miss), "usd": float(usd), "kind": kind, "note": note}]
p.write_text(json.dumps(rows, indent=1) + "\n")
r = subprocess.run([sys.executable, "-I", "/home/claude/executive-orders/jobs/bentham/gate.py", "--batches", str(p), "--prior-rate", "0.3",
                    "--cost-per-attempt", "2", "--next-best", "0.5", "--window", "2", "--json"], capture_output=True, text=True)
(H / "gate").mkdir(exist_ok=True)
(H / "gate" / f"GATE_after_{b}.json").write_text(r.stdout)
print(r.stdout[-800:], r.stderr[-400:])
