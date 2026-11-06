"""Build H5 TRACE.jsonl, ORDER_OUTCOMES.csv and the telemetry phase map from the run folder (coordinator tool).
usage: python3 -I trace.py   (reads scratch WORKERS.tsv, run/*.json, LIMITS.jsonl, OUTCOMES.json; writes under research/herschel/H5)"""
import csv, json, re
from datetime import datetime
from pathlib import Path
E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5")
H = Path("/home/claude/executive-orders/research/herschel/H5")
log = (H / "COORDINATOR_LOG.txt").read_text()
def ts(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
starts, ends = {}, {}
for m in re.finditer(r"^(H5-w\d+) (sonnet|opus) launched (\S+)", log, re.M): starts.setdefault(m[1], []).append(m[3])
for m in re.finditer(r"^(H5-w\d+) done (\S+)", log, re.M): ends.setdefault(m[1], []).append(m[2])
limits = {}
for l in (E / "run/LIMITS.jsonl").read_text().splitlines() if (E / "run/LIMITS.jsonl").exists() else []:
    d = json.loads(l); limits.setdefault(d["worker"], []).append({"utc": d["utc"], "message": d["message"]})
for m in re.finditer(r"^KILLED (H5-w\d+(?: H5-w\d+)*) (\S+): (.*)$", log, re.M):
    for w in m[1].split():
        limits.setdefault(w, []).append({"utc": m[2], "message": m[3][:200]})
outcomes = json.loads((E / "OUTCOMES.json").read_text())
usd = json.loads((H / "telemetry/USD.json").read_text())["by_worker_usd"]
follow = {}
for m in re.finditer(r"^(H5-w\d+)-(reveal|fix|resume) \S+ resume \S+ launched (\S+)", log, re.M): follow.setdefault(m[1], []).append(m[2] + "@" + m[3])   # coordinator-assembled {worker: {EO:n: outcome}}
strata = {r["instrument_id"]: r["stratum"] for r in csv.DictReader(open(H.parent / "frame/SAMPLE_R2.csv"))}
rows = [r for r in csv.DictReader(open(E / "WORKERS.tsv"), delimiter="\t")]
import os
for w in starts:
    f = E / "run" / f"{w}.json"
    if f.exists() and f.stat().st_size:
        mt = datetime.utcfromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ")
        if w not in ends or mt > ends[w][-1]: ends.setdefault(w, []).append(mt)
iv = {w: (ts(starts[w][-1]), ts(ends[w][-1])) for w in starts if w in ends}
trace = []
for r in rows:
    w = r["worker"]; orders = r["orders"].split()
    s = starts.get(w, [None])[0]; s_last = starts.get(w, [None])[-1]; e = ends.get(w, [None])[-1]
    conc = sum(1 for o, (a, b) in iv.items() if o != w and s_last and a <= ts(s_last) < b)
    st = sorted({strata.get(o, "?") for o in orders})
    trace.append({"worker": w, "step": r["step"].replace("clause_inventory_carry", "clause_inventory"), "model": r["model"], "stratum": "+".join(st), "batch": r["batch"], "orders": orders,
                  "started_utc": s, "ended_utc": e, "attempts": len(starts.get(w, [])), "oom_rerun": any("OOM" in x["message"] or "killed" in x["message"].lower() for x in limits.get(w, [])), "concurrent_workers_at_start": conc,
                  "limit_events": limits.get(w, []), "follow_ups": follow.get(w, []), "usd": usd.get(w), "outcomes": outcomes.get(w, {o: "not_reached" for o in orders})})
with open(H / "TRACE.jsonl", "w") as f:
    for t in trace: f.write(json.dumps(t, ensure_ascii=False) + "\n")
peak = max((sum(1 for a, b in iv.values() if a <= t0 < b) for t0, _ in iv.values()), default=0)
json.dump({w: r["step"] for r in rows for w in [r["worker"]]} | {"default": "coordinator"}, open(H / "telemetry/PHASE_MAP_BY_WORKER.json", "w"), indent=1)
print(json.dumps({"workers": len(trace), "peak_concurrency": peak}))
