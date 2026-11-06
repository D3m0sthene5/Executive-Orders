"""H6 BATCHES.json + Bentham gate (coordinator tool). USD per batch = sessions.py AGENT_USAGE rows of that batch's workers,
priced with jobs/bentham/measure.py usd(); coordinator excluded (it is in telemetry/USD.json)."""
import csv, json, subprocess, sys, re
from pathlib import Path
T = Path(__file__).resolve().parent; H = T.parent; R = H.parents[2]
sys.path.insert(0, str(R / "jobs/bentham")); import measure as M
E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
plan = {w["name"]: w for w in json.loads((T / "plan.json").read_text())}
pm = json.loads((H / "telemetry/PHASE_MAP.json").read_text())
PROJ = Path.home() / ".claude/projects/-tmp-claude-0--home-claude-1b28d9a2-1935-5c00-acfa-76feacb7b775-scratchpad-herschel-H6-run"
s2w = {}
for f in PROJ.glob("*.jsonl"):
    m = re.search(r"(?:worker|You are) (H6-w\d\d)", "".join(l for i, l in zip(range(8), open(f))))
    if m: s2w[f.stem] = m.group(1)
disc_batch = {"H6-w17": "D1", "H6-w18": "D1", "H6-w19": "D2", "H6-w20": "D2", "H6-w21": "U4", "H6-w22": "U4"}
usd = {}
for r in csv.DictReader(open(H / "telemetry/AGENT_USAGE.csv")):
    w = s2w.get(r.get("session_id") or "") or s2w.get(r.get("agent_id") or "")
    if not w: continue
    b = plan[w]["batch"] if w in plan else disc_batch.get(w)
    fam = "opus" if "opus" in (r.get("model") or "").lower() else "sonnet"
    tk = {"fresh_input": int(r["fresh_input"] or 0), "cache_read": int(r["cache_read"] or 0), "output": int(r["output"] or 0),
          "cache_write": sum(int(r.get(k) or 0) for k in ("cache_write_5m", "cache_write_1h", "cache_write_unclassified"))}
    usd[b] = usd.get(b, 0) + M.usd(fam, tk)
B = json.loads((T / "batches.json").read_text()); out = []
for b in ["D1", "D2", "U2", "U3", "U1", "U4"]:
    sk = E / "review" / b / "SET.jsonl"
    sub = sum(1 for l in open(sk) if l.strip()) if sk.exists() else 0
    out.append({"batch": b, "attempted": len(B[b]), "submitted": sub, "filed": 0, "controls_missed": 0, "usd": round(usd.get(b, 0), 2),
                "kind": "herschel-survey", "note": ("no record proposed; no review" if not sub else "submitted = records with a status proposal or submit row sent to paired blind Opus review; filed 0: " +
                ("manual route, the kit holds no dossier, nothing can file" if b in ("U1", "U2", "U3") else "undecided overlay: status proposals need owner adoption; no lifecycle claim files to readiness"))})
(H / "BATCHES.json").write_text(json.dumps(out, indent=1))
args = ["--prior-rate", "0.3", "--cost-per-attempt", "2", "--next-best", "0.5", "--window", "2"]
for k in range(1, len(out) + 1):
    tmp = E / f"batches_upto_{k}.json"; tmp.write_text(json.dumps(out[:k]))
    g = subprocess.run([sys.executable, "-I", str(R / "jobs/bentham/gate.py"), "--batches", str(tmp)] + args + ["--json"], cwd=R, capture_output=True, text=True)
    (H / f"GATE_after_{out[k-1]['batch']}.json").write_text(g.stdout or g.stderr)
    print(out[k - 1]["batch"], (g.stdout or g.stderr)[:300].replace("\n", " "))
