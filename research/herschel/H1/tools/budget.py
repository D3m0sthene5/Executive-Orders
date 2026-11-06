"""H1 spend so far, priced as jobs/bentham/measure.py prices tokens (coordinator tool).

usage: python3 -I research/herschel/H1/tools/budget.py [--write]
Runs jobs/bentham/sessions.py --since the H1 start over all transcripts, keeps the H1 coordinator agent
(a579cbbaa7e8c66fe) and the sessions of H1 workers (the H1 scratch run project), labels each by step from
JOBS.json, and prices tokens with measure.usd. --write copies the sanitized output to research/herschel/H1/telemetry/.
"""
import csv
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/claude/executive-orders")
H = REPO / "research/herschel/H1"
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H1")
SINCE = "2026-11-05T23:24:00Z"
ME = "a579cbbaa7e8c66fe"
spec = importlib.util.spec_from_file_location("measure", REPO / "jobs/bentham/measure.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

jobs = {j["name"]: j for j in json.load(open(S / "JOBS.json"))}
if (S / "JOBS2.json").exists():
    jobs.update({j["name"]: j for j in json.load(open(S / "JOBS2.json"))})
sess = {}
for p in (S / "run").glob("*.json"):
    try:
        d = json.load(open(p))
    except ValueError:
        continue
    if d.get("session_id"):
        name = p.stem
        base = name[:-7] if name.endswith("-reveal") else name
        sess.setdefault(d["session_id"], base)
pm = {ME: "coordination", "default": "not_h1"}
for sid, name in sess.items():
    j = jobs.get(name, {})
    pm["session:" + sid] = j.get("step", "unknown") + ("" if j.get("batch") in (None, "admission") else ":" + j["batch"]) + ":" + name
if (S / "oom_sessions.json").exists():
    for sid, name in json.load(open(S / "oom_sessions.json")).items():
        j = jobs.get(name, {})
        pm["session:" + sid] = j.get("step", "unknown") + ":" + j.get("batch", "") + ":" + name + ":oom_attempt1"
(S / "phase_map.json").write_text(json.dumps(pm, indent=1))
out = S / "telemetry"
# Snapshot only H1's transcripts (the coordinator agent and the H1 worker project) into a private HOME, dropping a
# trailing partial line of any transcript still being written: other sessions' live transcripts make Hamilton refuse.
import os
snap = S / "snaphome"
shutil.rmtree(snap, ignore_errors=True)
src_root = Path("/root/.claude/projects")
pairs = [(src_root / "-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/subagents" / f"agent-{ME}.jsonl",
          snap / ".claude/projects/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/subagents" / f"agent-{ME}.jsonl")]
meta = src_root / "-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/subagents" / f"agent-{ME}.meta.json"
wproj = "-tmp-claude-0--home-claude-1b28d9a2-1935-5c00-acfa-76feacb7b775-scratchpad-herschel-H1-run"
for f in (src_root / wproj).glob("*.jsonl"):
    pairs.append((f, snap / ".claude/projects" / wproj / f.name))
for a, b in pairs:
    b.parent.mkdir(parents=True, exist_ok=True)
    data = a.read_bytes()
    if not data.endswith(b"\n"):
        data = data[:data.rfind(b"\n") + 1]
    b.write_bytes(data)
if meta.exists():
    shutil.copy(meta, snap / ".claude/projects/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/subagents" / meta.name)
env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
env["HOME"] = str(snap)
r = subprocess.run([sys.executable, "-I", str(REPO / "jobs/bentham/sessions.py"), "--wave", "herschel-H1",
                    "--phase-map", str(S / "phase_map.json"), "--out", str(out), "--since", SINCE],
                   capture_output=True, text=True, env=env)
if r.returncode:
    sys.exit(r.stderr[-1500:])
rows = [r for r in csv.DictReader(open(out / "AGENT_USAGE.csv")) if r["phase"] != "not_h1"]
tot = 0.0
by = {}
for r in rows:
    fam = "opus" if "opus" in r["model"] else "sonnet" if "sonnet" in r["model"] else "opus"
    cw = sum(int(r[k] or 0) for k in ("cache_write_5m", "cache_write_1h", "cache_write_unclassified"))
    tok = {"fresh_input": int(r["fresh_input"] or 0), "cache_read": int(r["cache_read"] or 0), "cache_write": cw,
           "output": int(r["output"] or 0)}
    u = m.usd(fam, tok)
    tot += u
    by[r["phase"]] = by.get(r["phase"], 0) + u
print(json.dumps({"usd_total": round(tot, 2), "agents": len(rows), "by_phase": {k: round(v, 2) for k, v in sorted(by.items())}}, indent=1))
if "--write" in sys.argv:
    (H / "telemetry").mkdir(exist_ok=True)
    with open(out / "AGENT_USAGE.csv") as f, open(H / "telemetry/AGENT_USAGE.csv", "w", newline="") as g:
        rd = csv.DictReader(f); w = csv.DictWriter(g, fieldnames=rd.fieldnames + ["usd_bentham"])
        w.writeheader()
        for r in rd:
            if r["phase"] == "not_h1":
                continue
            fam = "opus" if "opus" in r["model"] else "sonnet" if "sonnet" in r["model"] else "opus"
            cw = sum(int(r[k] or 0) for k in ("cache_write_5m", "cache_write_1h", "cache_write_unclassified"))
            r["usd_bentham"] = round(m.usd(fam, {"fresh_input": int(r["fresh_input"] or 0), "cache_read": int(r["cache_read"] or 0),
                                                  "cache_write": cw, "output": int(r["output"] or 0)}), 4)
            w.writerow(r)
    shutil.copy(S / "phase_map.json", H / "telemetry/phase_map.json")
    (H / "telemetry/SPEND.json").write_text(json.dumps({"usd_total": round(tot, 2), "by_phase": by, "since": SINCE,
                                                        "price_table": m.PRICE_TABLE}, indent=1))
