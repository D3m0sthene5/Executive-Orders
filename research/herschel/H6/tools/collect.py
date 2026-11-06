"""H6 evidence collector (coordinator tool; no judgment): writes ../TRACE.jsonl and ../ORDER_OUTCOMES.csv from the plan,
launch records, limit records, discarded attempts, step outcome files and blind-review files."""
import csv, json
from pathlib import Path
T = Path(__file__).resolve().parent; H = T.parent; R = H.parents[2]
E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
plan = json.loads((T / "plan.json").read_text()); B = json.loads((T / "batches.json").read_text())
sample = {r["instrument_id"]: r for r in csv.DictReader(open(R / "research/herschel/frame/SAMPLE_R2.csv"))}
L = [json.loads(l) for l in open(E / "run/LAUNCHES.jsonl")]
LIM = [json.loads(l) for l in open(E / "run/LIMITS.jsonl")] if (E / "run/LIMITS.jsonl").exists() else []
DISC = json.loads((E / "DISCARDED.json").read_text()) if (E / "DISCARDED.json").exists() else []
COORD = json.loads((H / "COORDINATOR_OUTCOMES.json").read_text()) if (H / "COORDINATOR_OUTCOMES.json").exists() else {}
pk = lambda b: R / "research/herschel/H6/packets" / (b if b in ("D1", "D2", "U4") else "HAND/" + b)
trace, cell = [], {}
def oc_file(w):
    f = pk(w["batch"]) / "outcomes" / f"{w['step']}.{w['name']}.json"
    if not f.exists(): f = pk(w["batch"]) / "outcomes" / f"{w['step']}.json"
    if w["step"] in ("review",): return {}
    try: return json.loads(f.read_text()).get("outcomes", {})
    except Exception: return {}
for w in plan:
    runs = [x for x in L if x["worker"] == w["name"]]
    if not runs: oc = {i: "not_reached" for i in w["orders"]}
    elif w["step"] in ("review", "reveal"): oc = w.get("outcomes", {})
    else: oc = {i: oc_file(w).get(i, "failed:no_outcome_recorded") for i in w["orders"]}
    t = {"worker": w["name"], "step": w["step"], "model": w["model"], "batch": w["batch"],
         "stratum": sorted({sample[i]["stratum"] for i in w["orders"]}), "orders": w["orders"],
         "started_utc": runs[0]["started_utc"] if runs else None, "ended_utc": runs[-1]["ended_utc"] if runs else None,
         "concurrent_workers_at_start": runs[0].get("concurrent_at_start") if runs else None,
         "limit_events": [x for x in LIM if x["worker"] == w["name"]], "attempts": len(runs),
         "oom_rerun": any(x.get("oom_rerun") for x in runs) or bool(w.get("attempts")),
         "session_ids": sorted({x["session_id"] for x in runs if x.get("session_id")} | {a["session_id"] for a in w.get("attempts", []) if a.get("session_id")}),
         "reported_cost_usd_last_attempt": runs[-1].get("cost") if runs else None, "outcomes": oc}
    trace.append(t)
    if w["step"] not in ("review", "reveal"):
        for i, o in oc.items(): cell[(i, w["step"])] = (o, w["name"])

for d in DISC:
    trace.append({"worker": d["worker"], "step": d["step"], "model": "sonnet", "batch": d["batch"],
                  "stratum": sorted({sample[i]["stratum"] for i in d["orders"]}), "orders": d["orders"], "discarded": True,
                  "limit_events": [x for x in LIM if x["worker"] == d["worker"]], "outcomes": {i: d["outcome"] for i in d["orders"]}})
for (i, s), o in COORD.items() if isinstance(COORD, dict) and False else []: pass
RO = json.loads((H / "REVIEW_OUTCOMES.json").read_text())["orders"] if (H / "REVIEW_OUTCOMES.json").exists() else {}
revw = {}
for w in plan:
    if w["step"] == "review":
        for i in w["orders"]: revw.setdefault(i, []).append(w["name"])
for i, v in RO.items(): cell[(i, "review")] = (v, "+".join(revw.get(i, [])) or "coordinator")
for k, v in COORD.items():
    i, s = k.split("|"); cell[(i, s)] = (v, "coordinator")
with open(H / "TRACE.jsonl", "w") as f:
    for t in trace: f.write(json.dumps(t, ensure_ascii=False) + "\n")
order = []
for b in ["D1", "D2", "U4", "U1", "U2", "U3"]: order += B[b]
with open(H / "ORDER_OUTCOMES.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["instrument_id", "stratum", "step", "outcome", "worker"])
    for i in order:
        for s in sample[i]["open_steps"].split("|") + ["review"]:
            o, wk = cell.get((i, s), ("not_reached", ""))
            w.writerow([i, sample[i]["stratum"], s, o, wk])
print(len(trace), "trace lines;", sum(1 for _ in open(H / "ORDER_OUTCOMES.csv")) - 1, "cells")
