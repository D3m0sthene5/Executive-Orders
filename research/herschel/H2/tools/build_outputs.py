"""Build H2 TRACE.jsonl and ORDER_OUTCOMES.csv from the recorded worker files (coordinator tool; no legal judgment).

usage: python3 -I build_outputs.py
Inputs: tools/WORKERS.json (worker registry), scratch run/*.meta.json (start/end/concurrency/session), steps/*/RESULT.jsonl,
packet decisions.csv + final applied AUDIT.json, reviews/*/BLIND_REVIEW_*.jsonl and AFTER_REVEAL_*.jsonl, scratch keys
(control ids only), tools/LIMIT_EVENTS.json, tools/DISPATCH_BLOCKS.json, tools/FINAL.json (final applied dir per
lifecycle worker and filed ids). Every outcome string is copied or mechanically derived from those files.
"""
import csv
import json
import re
from pathlib import Path

H = Path("/home/claude/executive-orders/research/herschel/H2")
REPO = H.parents[2]
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2")
W = json.loads((H / "tools/WORKERS.json").read_text())
FINAL = json.loads((H / "tools/FINAL.json").read_text())
LIMITS = json.loads((H / "tools/LIMIT_EVENTS.json").read_text())
DISPATCH = json.loads((H / "tools/DISPATCH_BLOCKS.json").read_text())
ORDERS = {r["instrument_id"]: r for r in csv.DictReader(open(H.parent / "frame/ORDERS.csv", encoding="utf-8"))}
ASSIGNED = [c for c in json.loads((H.parent / "frame/ASSIGNMENTS.json").read_text())["coordinators"] if c["name"] == "H2"][0]["orders"]
LIFE = ("clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def metas(worker):
    out = []
    for mp in sorted((S / "run").glob("*.meta.json")):
        m = json.loads(mp.read_text())
        if re.match(r"H2-w\d+", m["worker"]).group(0) == worker:
            out.append(m)
    return sorted(out, key=lambda m: m["started_utc"])


def short(s, n=160):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + "…"


def lifecycle_outcomes(worker):
    info = W[worker]
    fin = FINAL.get(worker, {})
    pk = H / info["packet"]
    gaps = {}
    if (pk / "decisions.csv").exists():
        for r in csv.DictReader(open(pk / "decisions.csv", encoding="utf-8")):
            g = r.get("unresolved_material_gaps") or "[]"
            try:
                g = json.loads(g)
            except ValueError:
                g = [g]
            gaps[r["instrument_id"]] = short("; ".join(map(str, g)) or "no gap stated")
    audit = {a["instrument_id"]: a for a in json.load(open(pk / fin["applied"] / "AUDIT.json"))} if fin.get("applied") else {}
    out = {}
    for o in info["orders"]:
        a = audit.get(o)
        if a and a["outcome"] == "assembled_proposal":
            out[o] = "done"
        elif a:
            out[o] = "blocked:" + gaps.get(o, a["outcome"])
        else:
            out[o] = "failed:" + fin.get("failure", "no applied result")
    return out


def review_outcomes(worker):
    info = W[worker]
    rdir = H / info["review"]
    arm = info["arm"]
    key = json.loads((S / "keys" / (Path(info["review"]).name + ".json")).read_text())
    controls = {c["instrument_id"] for c in key["controls"]}
    out = {}
    for r in jl(rdir / f"BLIND_REVIEW_{arm}.jsonl"):
        v = r["verdict"]
        if r["instrument_id"] in controls:
            v = "control_caught" if v == "rejected" else "control_missed"
        elif v == "rejected":
            v = "rejected:" + short("; ".join(d.get("problem", "") for d in r.get("defects", [])), 140)
        out[r["instrument_id"]] = v
    for r in jl(rdir / f"AFTER_REVEAL_{arm}.jsonl"):
        v = r["verdict"]
        out[r["instrument_id"]] += "; genuine " + ("upheld" if v == "upheld_after_reveal" else "rejected:" + short(
            "; ".join(d.get("problem", "") for d in r.get("defects", [])), 120))
    return out


def main():
    trace, rows = [], []
    by_order_step = {}
    for w, info in sorted(W.items(), key=lambda kv: int(kv[0].split("w")[1])):
        ms = metas(w)
        if info["step"] == "lifecycle":
            outc = lifecycle_outcomes(w)
        elif info["step"].startswith("review"):
            outc = review_outcomes(w)
        else:
            outc = {r["instrument_id"]: r["outcome"] for r in jl(H / info["result"])}
        trace.append({"worker": w, "step": info["step"], "model": info["model"], "stratum": info["stratum"],
                      "orders": sorted(outc), "started_utc": ms[0]["started_utc"] if ms else None,
                      "ended_utc": ms[-1]["ended_utc"] if ms else None,
                      "concurrent_workers_at_start": ms[0]["concurrent_workers_at_start"] if ms else None,
                      "passes": [{"name": m["worker"], "started_utc": m["started_utc"], "ended_utc": m["ended_utc"],
                                  "concurrent_workers_at_start": m["concurrent_workers_at_start"], "session_id": m["session_id"],
                                  "cli_cost_usd": m["cost_reported"], "turns": m["turns"],
                                  "oom_rerun": bool(re.fullmatch(r"H2-w\d+r\d*", m["worker"])),  # passes named ...r / ...r2 are OOM re-runs
                                  "killed_by_oom": any(e.get("event") == "oom_kill" and e.get("pass") == m["worker"] for e in LIMITS.get(w, []))}
                                 for m in ms],
                      "limit_events": LIMITS.get(w, []), "outcomes": outc, **({"note": info["note"]} if info.get("note") else {})})
        steps = LIFE if info["step"] == "lifecycle" else (info["step"],)
        for o, v in outc.items():
            for st in steps:
                by_order_step.setdefault((o, st), []).append((w, v))
    for o in ASSIGNED:
        od = ORDERS[o]
        need = [s for s in od["open_steps"].split("|") if s and s != "human_certification"]
        if od["transcription_dependent"] == "True":
            need.append("replace_original")
        for st in need + ["review"]:
            if st == "review":
                revs = [(s, w, v) for (oo, s), lst in by_order_step.items() if oo == o and s.startswith("review") for w, v in lst]
                if not revs:
                    rows.append({"instrument_id": o, "stratum": od["stratum"], "step": "review",
                                 "outcome": "not_applicable:no proposal or claim produced to review", "worker": ""})
                for s, w, v in sorted(revs):
                    rows.append({"instrument_id": o, "stratum": od["stratum"], "step": s, "outcome": v, "worker": w})
                continue
            lst = by_order_step.get((o, st))
            if lst:
                w, v = lst[-1]  # the last worker to attempt the step holds the current outcome; earlier attempts are in TRACE
                rows.append({"instrument_id": o, "stratum": od["stratum"], "step": st, "outcome": v,
                             "worker": "+".join(x for x, _ in lst)})
            elif st in DISPATCH.get(o, {}):
                rows.append({"instrument_id": o, "stratum": od["stratum"], "step": st, "outcome": DISPATCH[o][st]["outcome"],
                             "worker": DISPATCH[o][st]["worker"]})
            else:
                rows.append({"instrument_id": o, "stratum": od["stratum"], "step": st, "outcome": "not_reached", "worker": ""})
    with open(H / "TRACE.jsonl", "w", encoding="utf-8") as f:
        for t in trace:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    with open(H / "ORDER_OUTCOMES.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["instrument_id", "stratum", "step", "outcome", "worker"])
        wr.writeheader(); wr.writerows(rows)
    print(len(trace), "workers;", len(rows), "order-step rows")


if __name__ == "__main__":
    main()
