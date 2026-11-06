"""Builds H1's TRACE.jsonl, ORDER_OUTCOMES.csv, BATCHES.json, step data copies and review copies (coordinator tool).

usage: python3 -I research/herschel/H1/tools/finish.py
Reads scratch JOBS.json, DRIVER_LOG.jsonl, LAUNCH_LOG.txt, run/*.json|err, telemetry/AGENT_USAGE.csv and the step
and review files under packets/. Writes only under research/herschel/H1/. No legal judgment: outcomes are copied
from worker files; review outcomes are the two arms' verdicts as recorded.
"""
import csv
import json
import re
import shutil
from pathlib import Path

REPO = Path("/home/claude/executive-orders")
H = REPO / "research/herschel/H1"
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H1")
STEPFILE = {"original_text": "ORIGINAL_TEXT.jsonl", "provisional_status": "STATUS.jsonl",
            "clause_inventory": "INVENTORY.jsonl", "ending_or_current_basis": "ENDING.jsonl",
            "savings_residuals": "SAVINGS.jsonl", "counterevidence": "COUNTER.jsonl",
            "replace_original": "REPLACE_ORIGINAL.jsonl"}
LIMIT = re.compile(r"rate.?limit|usage limit|overloaded|\b429\b|\b529\b|too many requests|quota", re.I)
B = json.load(open(H / "tools/batches.json"))
BATCH_OF = {i: b for b, ids in B.items() for i in ids}
STRATUM = {r["instrument_id"]: r["stratum"] for r in csv.DictReader(open(H.parent / "frame/ORDERS.csv"))}


def rows(p):
    out = {}
    if p.exists():
        for line in p.read_text("utf-8").splitlines():
            if line.strip():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                out.setdefault(r.get("instrument_id"), r)
    return out


def norm(o):
    o = (o or "").strip()
    if o.startswith("blocked") and not o.startswith("blocked:"):
        o = "blocked:" + o[len("blocked"):].lstrip(" -")
    return o or "failed:no_outcome_recorded"


jobs = json.load(open(S / "JOBS.json"))
jobs2 = json.load(open(S / "JOBS2.json")) if (S / "JOBS2.json").exists() else []
SUPERSEDED = {j["supersedes"]: j["name"] for j in jobs2 if j.get("supersedes")}
OOM = {j["name"] for j in jobs2 if j.get("oom_rerun")}
jobs = [j for j in jobs if j["name"] not in OOM] + jobs2
launch = (S / "LAUNCH_LOG.txt").read_text().splitlines() if (S / "LAUNCH_LOG.txt").exists() else []
usage = {}
up = H / "telemetry/AGENT_USAGE.csv"
if up.exists():
    for r in csv.DictReader(open(up)):
        parts = r["phase"].split(":")
        name = parts[2] if len(parts) >= 3 else parts[-1]
        usage.setdefault(name, []).append(r)


def launched(name):
    ts, conc = [], []
    for l in launch:
        mm = re.match(rf"^{re.escape(name)} \S+ (?:resume \S+ )?launched (\S+) concurrent_at_start=(\d+)", l)
        if mm:
            ts.append(mm.group(1)); conc.append(int(mm.group(2)))
    ends = [l.split()[2] for l in launch if l.startswith(name + " done ")]
    return ts, conc, ends


trace = []
for j in jobs:
    if j["kind"] != "worker":
        continue
    name = j["name"]
    ts, conc, ends = launched(name)
    rts, _, rends = launched(name + "-reveal")
    res = {}
    for suffix in ("", "-reveal"):
        p = S / "run" / (name + suffix + ".json")
        if p.exists():
            try:
                res[suffix or "main"] = json.load(open(p))
            except ValueError:
                res[suffix or "main"] = {"error": "unparseable result"}
    events = []
    for suffix in ("", "-reveal"):
        e = S / "run" / (name + suffix + ".err")
        if e.exists():
            events += [l.strip()[:200] for l in e.read_text(errors="replace").splitlines() if LIMIT.search(l)]
    for r in res.values():
        t = str(r.get("result", ""))
        if r.get("is_error") and LIMIT.search(t):
            events.append(t[:200])
    outcomes = {}
    sup = "superseded-v1/" if name in SUPERSEDED else ""
    if j["step"] in STEPFILE:
        got = rows(H / "packets" / j["batch"] / (sup or "steps/").rstrip("/") / ("steps" if sup else "") / STEPFILE[j["step"]]) if sup else rows(H / "packets" / j["batch"] / "steps" / STEPFILE[j["step"]])
        for i in j["orders"]:
            outcomes[i] = norm(got[i]["outcome"]) if i in got else ("not_reached" if not ts else "failed:no_row_written")
    elif j["step"] == "review":
        arm = j["alias"][-1]
        got = rows(H / "packets" / j["batch"] / (sup + "reviews") / f"BLIND_REVIEW_{arm}.jsonl")
        for i in j["orders"]:
            r = got.get(i)
            outcomes[i] = ("not_reached" if not ts else "failed:no_row_written") if r is None else (
                "upheld" if r.get("verdict") == "upheld" else "rejected:" + "; ".join(map(str, r.get("defects") or []))[:300])
    elif j["step"] == "admit":
        got = rows(H / "admission/ADMISSION_RESEARCH.jsonl")
        for i, r in got.items():
            outcomes[i] = str(r.get("classification"))
    u = usage.get(name, [])
    tok = {k: sum(int(r[k] or 0) for r in u) for k in ("fresh_input", "cache_read", "cache_write_5m", "cache_write_1h",
                                                          "cache_write_unclassified", "output")} if u else None
    trace.append({"worker": name, "alias": j.get("alias"), "step": j["step"], "model": j["model"],
                  "stratum": "none.1907-36" if j["step"] != "admit" else "admission_candidates",
                  "batch": j["batch"], "orders": j["orders"] if j["step"] != "admit" else sorted(outcomes),
                  "started_utc": (ts[-1] if (name in OOM or name == "H1-w01") else ts[0]) if ts else None, "ended_utc": (rends or ends or [None])[-1],
                  "concurrent_workers_at_start": (conc[-1] if name in OOM else conc[0]) if conc else None, "limit_events": events,
                  "outcomes": outcomes,
                  "session_id": (res.get("main") or {}).get("session_id"),
                  "turns": sum(int(r.get("num_turns") or 0) for r in res.values()),
                  "cli_cost_usd": round(sum(float(r.get("total_cost_usd") or 0) for r in res.values()), 4),
                  "tokens": tok, "usd_bentham": round(sum(float(r["usd_bentham"]) for r in u), 4) if u else None,
                  "oom_rerun": name in OOM, "superseded_by": SUPERSEDED.get(name),
                  "first_attempt": ({"started_utc": ts[0] if ts else None, "result": "killed by memory-cgroup OOM killer; empty result"}
                                    if name in OOM else None),
                  "reveal": {"started_utc": rts[0] if rts else None, "ended_utc": rends[-1] if rends else None} if j["step"] == "review" else None})
(H / "TRACE.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in trace))

# ORDER_OUTCOMES: one row per assigned order and open step (CELLS.csv), plus review.
cells = [r for r in csv.DictReader(open(H.parent / "frame/CELLS.csv")) if r["instrument_id"] in BATCH_OF]
by_step = {}
for t in trace:
    if t["superseded_by"]:
        continue
    for i, o in t["outcomes"].items():
        by_step.setdefault((i, t["step"]), []).append((o, t["worker"], t.get("alias")))
out = []
for c in cells:
    i, st = c["instrument_id"], c["step"]
    if st == "human_certification":
        out.append([i, STRATUM[i], st, "not_reached", ""]); continue
    v = by_step.get((i, st))
    out.append([i, STRATUM[i], st, v[0][0] if v else "not_reached", v[0][1] if v else ""])
for i in BATCH_OF:
    v = by_step.get((i, "review"), [])
    if not v:
        out.append([i, STRATUM[i], "review", "not_reached", ""]); continue
    up_ = [o for o, _, _ in v if o == "upheld"]
    o = "upheld" if len(up_) == 2 else ("rejected:" + " | ".join(f"{a}: {o[9:]}" for o, _, a in v if o.startswith("rejected"))[:600]
                                       if any(o.startswith("rejected") for o, _, _ in v) else v[0][0])
    out.append([i, STRATUM[i], "review", o, "+".join(w for _, w, _ in v)])
with open(H / "ORDER_OUTCOMES.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["instrument_id", "stratum", "step", "outcome", "worker"])
    w.writerows(sorted(out, key=lambda r: (list(BATCH_OF).index(r[0]), r[2])))

# Copy the small step, proposal, review and control files into the committed folder.
for b in B:
    for sub in ("steps", "reviews"):
        src = H / "packets" / b / sub
        if src.exists():
            dst = H / "data" / b / sub
            dst.mkdir(parents=True, exist_ok=True)
            for p in src.glob("*.jsonl"):
                shutil.copy(p, dst / p.name)
    sv = H / "packets" / b / "superseded-v1"
    if sv.exists():
        for p in sv.rglob("*.jsonl"):
            d = H / "data" / b / "superseded-v1" / p.relative_to(sv).parent
            d.mkdir(parents=True, exist_ok=True); shutil.copy(p, d / p.name)
    if (H / "packets" / b / "PROPOSALS.jsonl").exists():
        shutil.copy(H / "packets" / b / "PROPOSALS.jsonl", H / "data" / b / "PROPOSALS.jsonl")
    cc = S / "review" / b / "CONTROL_CHECK.json"
    if cc.exists():
        shutil.copy(cc, H / "data" / b / "CONTROL_CHECK.json")
print(json.dumps({"trace": len(trace), "order_outcomes": len(out)}))
