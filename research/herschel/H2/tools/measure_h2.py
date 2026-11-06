"""Measure H2 spend (coordinator tool; no legal judgment).

usage: python3 -I measure_h2.py [--write]
  Builds a phase map from the scratch run/*.meta.json files (session:ID -> step label, batch = worker name) plus the
  coordinator's own agent id, runs jobs/bentham/sessions.py --since the H2 start, and prices every H2 row with
  jobs/bentham/measure.py's PRICE_TABLE and usd(). Rows of other coordinators fall to the default phase "not_H2" and
  are excluded from the totals. sessions.py reads only a mirror config dir (scratch cfg/: symlinks to the H2 worker
  project and the coordinator transcript), because another coordinator's OOM-truncated transcript makes Hamilton refuse
  the machine-wide scan. With --write the sessions.py output goes to research/herschel/H2/telemetry/ and
  COSTS.json is written there; otherwise to scratch.
"""
import csv
import re
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/claude/executive-orders")
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2")
START = "2026-11-05T23:24:00Z"
COORD_AGENT = "ac2628c47a86a4dc2"
STEP = json.loads((REPO / "research/herschel/H2/tools/WORKER_STEPS.json").read_text())

spec = importlib.util.spec_from_file_location("measure", REPO / "jobs/bentham/measure.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)


def main(write=False):
    pmap = {"default": "not_H2", COORD_AGENT: "coordination"}
    batch_of = {}
    for mp in sorted((S / "run").glob("*.meta.json")):
        m = json.loads(mp.read_text())
        if m.get("session_id"):
            base = re.match(r"H2-w\d+", m["worker"]).group(0)  # resumed passes (p2) and reveals (rv) count to their worker
            pmap["session:" + m["session_id"]] = STEP.get(base, "unlabeled")
            batch_of[m["session_id"]] = base
    out = (REPO / "research/herschel/H2/telemetry") if write else (S / "telemetry")
    out.mkdir(parents=True, exist_ok=True)
    (out / "PHASE_MAP.json").write_text(json.dumps(pmap, indent=1) + "\n")
    r = subprocess.run([sys.executable, "-I", str(REPO / "jobs/bentham/sessions.py"), "--wave", "herschel-H2",
                        "--phase-map", str(out / "PHASE_MAP.json"), "--out", str(out), "--since", START, "--claude-dir", str(S / "cfg")],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(r.returncode)
    rows = list(csv.DictReader(open(out / "AGENT_USAGE.csv", encoding="utf-8")))
    per_worker, per_step, total = {}, {}, 0.0
    for x in rows:
        if x["phase"] == "not_H2":
            continue
        fam = "opus" if "opus" in (x["model"] or "").lower() else "sonnet" if "sonnet" in (x["model"] or "").lower() else (
            "opus" if x["phase"] in ("coordination",) or x["phase"].startswith("review") else "sonnet")
        cw = sum(int(x.get(k) or 0) for k in ("cache_write_5m", "cache_write_1h", "cache_write_unclassified"))
        tok = {"fresh_input": int(x["fresh_input"] or 0), "cache_read": int(x["cache_read"] or 0), "cache_write": cw,
               "output": int(x["output"] or 0)}
        usd = M.usd(fam, tok)
        total += usd
        w = batch_of.get(x.get("session_id"), "coordinator" if x["phase"] == "coordination" else x["agent_id"])
        pw = per_worker.setdefault(w, {"step": x["phase"], "family": fam, "usd": 0.0, "active_seconds": 0, "wall_seconds": 0,
                                       **{k: 0 for k in tok}})
        pw["usd"] += usd
        pw["active_seconds"] += int(float(x.get("active_seconds") or 0)); pw["wall_seconds"] += int(float(x.get("wall_seconds") or 0))
        for k in tok:
            pw[k] += tok[k]
        ps = per_step.setdefault(x["phase"], {"usd": 0.0, "workers": set(), **{k: 0 for k in tok}})
        ps["usd"] += usd; ps["workers"].add(w)
        for k in tok:
            ps[k] += tok[k]
    for v in per_step.values():
        v["workers"] = sorted(v["workers"])
    doc = {"schema": "herschel-H2-costs/v1", "since": START, "price_table": M.PRICE_TABLE, "total_usd": round(total, 4),
           "per_step": {k: {**v, "usd": round(v["usd"], 4)} for k, v in sorted(per_step.items())},
           "per_worker": {k: {**v, "usd": round(v["usd"], 4)} for k, v in sorted(per_worker.items())}}
    (out / "COSTS.json").write_text(json.dumps(doc, indent=1) + "\n")
    print(json.dumps({"total_usd": doc["total_usd"], "per_step": {k: v["usd"] for k, v in doc["per_step"].items()}}))


if __name__ == "__main__":
    main("--write" in sys.argv)
