"""H6 telemetry (coordinator tool): phase map by worker step, then jobs/bentham/sessions.py; sums only H6 phases."""
import json, re, subprocess, sys
from pathlib import Path
T = Path(__file__).resolve().parent; H = T.parent; R = H.parents[2]
PROJ = Path.home() / ".claude/projects/-tmp-claude-0--home-claude-1b28d9a2-1935-5c00-acfa-76feacb7b775-scratchpad-herschel-H6-run"
plan = {w["name"]: w for w in json.loads((T / "plan.json").read_text())}
disc = {"H6-w17", "H6-w18", "H6-w19", "H6-w20", "H6-w21", "H6-w22"}
pm = {"agent-aa2b8693b021b2138": "coordination", "aa2b8693b021b2138": "coordination", "default": "not_H6"}
names = {}
for f in PROJ.glob("*.jsonl"):
    head = "".join(l for i, l in zip(range(8), open(f)))
    m = re.search(r"(?:worker|You are) (H6-w\d\d)", head)
    if m: names[f.stem] = m.group(1)
for sid, n in names.items():
    w = plan.get(n)
    lab = ("discarded_" + {"H6-w17": "savings_residuals", "H6-w18": "counterevidence", "H6-w19": "ending_or_current_basis", "H6-w20": "savings_residuals", "H6-w21": "ending_or_current_basis", "H6-w22": "savings_residuals"}[n]) if n in disc else \
          ("review" if w["step"] in ("review",) else w["step"] + ("_fix" if w.get("fix") else ""))
    pm["session:" + sid] = lab; pm[sid] = lab
# reveal runs resume the reviewer session: they are in the same transcript and count as review
out = H / "telemetry"; out.mkdir(exist_ok=True)
(out / "PHASE_MAP.json").write_text(json.dumps(pm, indent=1, sort_keys=True))
import os; env = dict(os.environ, HOME="/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6/tele_home"); env.pop("CLAUDE_CONFIG_DIR", None)
r = subprocess.run([sys.executable, "-I", str(R / "jobs/bentham/sessions.py"), "--wave", "herschel-H6", "--phase-map", str(out / "PHASE_MAP.json"),
                    "--out", str(out), "--since", "2026-11-05T23:28:38Z"], cwd=R, capture_output=True, text=True, env=env)
print(r.stdout[-1500:], r.stderr[-1500:])
s = json.loads((out / "SUMMARY.json").read_text())
print(json.dumps({k: v for k, v in s.items() if k != "by_exact_model"}, indent=0)[:3000])
sys.path.insert(0, str(R / "jobs/bentham")); import measure as M
rows, tot = {}, 0.0
for k, v in s["totals_by_phase_and_family"].items():
    ph, fam = k.split("|")
    if ph == "not_H6": continue
    tk = {"fresh_input": v["fresh_input"] or 0, "cache_read": v["cache_read"] or 0, "output": v["output"] or 0,
          "cache_write": sum(v.get(x) or 0 for x in ("cache_write_5m", "cache_write_1h", "cache_write_unclassified"))}
    u = M.usd(fam if fam in M.PRICE_TABLE else "opus", tk); rows[k] = {"agents": v["agents"], "usd": round(u, 4), **tk}; tot += u
(out / "USD.json").write_text(json.dumps({"priced_by": "jobs/bentham/measure.py usd() and PRICE_TABLE", "since": "2026-11-05T23:28:38Z", "total_usd": round(tot, 4), "by_phase_and_family": rows}, indent=1))
print("TOTAL_USD", round(tot, 2)); [print(k, r["agents"], r["usd"]) for k, r in sorted(rows.items())]
