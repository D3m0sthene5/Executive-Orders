#!/usr/bin/env python3
"""Thin driver: run the project's Hamilton profiler over each agent of the Tribonian run.

Re-runnable; skips agents whose Hamilton output exists unless --force.
Per-agent Hamilton outputs (private, may embed transcript-derived details) go to the
scratchpad; only AGENT_USAGE.csv, SUMMARY.json and sanitized effort receipts are
written beside this script. Transcripts are never copied.
"""
import argparse, csv, json, re, shutil, subprocess, sys
from collections import OrderedDict, defaultdict
from datetime import datetime
from pathlib import Path

SESSION = "113ce3b2-4ba3-50df-9241-eb6576e0f367"
SCRATCH = Path("/tmp/claude-0/-home-claude") / SESSION / "scratchpad"
LOG = SCRATCH / "tribonian/COORDINATOR_LOG.txt"
BATCHES = SCRATCH / "tribonian/batches.json"
HOME = Path("/root/.claude/projects/-home-claude") / SESSION
SUB = HOME / "subagents"
COORD = HOME.with_suffix(".jsonl")
PRIVATE = SCRATCH / "hamilton"
PROFILER = Path("/tmp/claude-0/bv/repo/jobs/hamilton-token-audit/profile.py")
CLAIMS = Path("/home/claude/executive-orders/research/readiness/claims")
OUT = Path(__file__).resolve().parent
ID = r"a[0-9a-f]{16}"
COORD_ID = "coordinator"


def parse_log():
    agents = OrderedDict()
    def get(i):
        return agents.setdefault(i, {"id": i, "role": None, "phase": None, "batches": [], "log_model": None, "notes": []})
    def add(i, role, phase, batch=None):
        a = get(i)
        if a["role"] is None:
            a["role"], a["phase"] = role, phase
        for b in (batch or "").split("+"):
            if b and b not in a["batches"]:
                a["batches"].append(b)
    for line in LOG.read_text().splitlines():
        if line.startswith("NOTE"):
            continue
        m = re.match(rf"correction producer (\w+) ({ID}) (\w+)", line)
        if m:
            add(m[2], "correction_producer", "correction", m[1]); get(m[2])["log_model"] = m[3]; continue
        m = re.match(rf"producer (\w+) ({ID}) (?:(sonnet|opus) )?", line)
        if m:
            add(m[2], "producer", "production", m[1])
            if m[3]: get(m[2])["log_model"] = m[3]
            continue
        m = re.search(rf"(integration|adapter|telemetry) worker ({ID})(?: (sonnet|opus))?", line)
        if m:
            add(m[2], m[1] + "_worker", "integration"); 
            mm = re.search(r"\b(sonnet|opus)\b", line)
            if mm: get(m[2])["log_model"] = mm[1]
            continue
        for m in re.finditer(rf"([\w+-]+) reviewer \(?({ID})\)?", line):
            add(m[2], "reviewer", "review", m[1])
            mm = re.search(r"launched.*?\b", line)
            if "opus launched" in line and m[1] in line.split(m[2])[0]:
                get(m[2])["log_model"] = "opus"
        for m in re.finditer(rf"(\w+) (?:blind )?(?:review )?assigned to ({ID})", line):
            add(m[1] and m[2], "reviewer", "review", m[1])
    return agents


def read_stamps_and_tools(path):
    first = last = None
    tool_ids, bash_ids = set(), set()
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = r.get("timestamp")
        if t:
            first = t if first is None or t < first else first
            last = t if last is None or t > last else last
        if r.get("type") == "assistant":
            c = (r.get("message") or {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tool_ids.add(b.get("id"))
                        if b.get("name") == "Bash":
                            bash_ids.add(b.get("id"))
    return first, last, len(tool_ids), len(bash_ids)


def run(transcript, label, out, metadata=None):
    cmd = ["python3", "-I", str(PROFILER), str(transcript), "--label", label, "--out", str(out)]
    if metadata:
        cmd += ["--production-metadata", str(metadata)]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=PROFILER.parents[2])
    return p.returncode, (p.stderr.strip().splitlines() or [""])[-1] if p.returncode else ""


def profile_agent(a, force, batches):
    d = PRIVATE / a["id"]
    status_file = d / "DRIVER_STATUS.json"
    if status_file.exists() and not force:
        return json.loads(status_file.read_text())
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    # private snapshot without unparsable lines (a transcript still being written can end mid-line)
    t = d / "snapshot.jsonl"
    dropped = synthetic = 0
    with t.open("w") as out:
        for line in a["transcript"].read_text(errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                dropped += 1; continue
            if (rec.get("message") or {}).get("model") == "<synthetic>":
                # client-generated rate-limit/error message with zero usage; not a provider call
                synthetic += 1; continue
            out.write(line + "\n")
    first, last, tools, bashes = read_stamps_and_tools(t)
    ids = []
    for b in a["batches"]:
        for i in batches.get(b, []):
            if i not in ids:
                ids.append(i)
    # pass 1: plain profile to learn the observed model(s)
    rc, err = run(t, a["id"], d / "plain")
    res = {"synthetic_messages": synthetic, "dropped_lines": dropped, "first": first, "last": last, "tools": tools, "bashes": bashes, "instrument_ids": ids}
    if rc:
        res.update(status="refused: " + err, profile=None, effort=False)
        status_file.write_text(json.dumps(res)); return res
    prof = json.loads((d / "plain" / f"PROFILE_{a['id']}.json").read_text())
    models = sorted({r["model"] for r in prof["usage_records"] if r["model"]})
    res["models"] = models
    meta = {"session_id": SESSION, "agents": {"main": {
        "worker_id": a["id"], "role": a["role"], "phase": a["phase"],
        "actual_model": models[0] if len(models) == 1 else (a.get("log_model") or "unknown"),
        "instrument_ids": ids, "started_utc": first, "finished_utc": last,
        "coverage": a["coverage"], "measurement_method": a["method"]}}}
    mpath = d / "METADATA.json"
    mpath.write_text(json.dumps(meta, indent=1))
    rc, err = run(t, a["id"], d / "effort", mpath)
    if rc:
        res.update(status=f"profile ok; PRODUCTION_EFFORT refused: {err}", effort=False)
    else:
        res.update(status="ok", effort=True)
    res["profile"] = str(d / "plain" / f"PROFILE_{a['id']}.json")
    status_file.write_text(json.dumps(res))
    return res


def n(v):
    return "" if v is None else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    batches = json.loads(BATCHES.read_text())
    agents = parse_log()
    for a in agents.values():
        a["transcript"] = SUB / f"agent-{a['id']}.jsonl"
        a["coverage"] = "complete_interval"
        a["method"] = "claude-code subagent transcript first/last record"
    agents[COORD_ID] = {"id": COORD_ID, "role": "coordinator", "phase": "coordination", "batches": [],
        "log_model": "opus", "notes": [], "transcript": COORD, "coverage": "partial",
        "method": "claude-code coordinator transcript first/last record (spans earlier work)"}
    rows, results = [], {}
    for a in agents.values():
        if not a["transcript"].exists():
            results[a["id"]] = None
            rows.append({"agent_id": a["id"], "role": a["role"] or "unknown", "phase": n(a["phase"]),
                         "batch": "+".join(a["batches"]), "hamilton_status": "refused: transcript file not found",
                         "coverage_notes": "no transcript"})
            continue
        r = profile_agent(a, args.force, batches)
        results[a["id"]] = r
        row = {"agent_id": a["id"], "role": a["role"] or "unknown", "phase": n(a["phase"]),
               "batch": "+".join(a["batches"]), "started_utc": n(r["first"]), "finished_utc": n(r["last"]),
               "tool_uses": r["tools"], "bash_calls": r["bashes"], "hamilton_status": r["status"]}
        notes = [a["coverage"]]
        if len(a["batches"]) > 1:
            notes.append("reviewer reused across batches; tokens not separable by batch")
        if a["role"] == "reviewer":
            notes.append("blind review and after-reveal share one transcript; not separable")
        if r.get("dropped_lines"):
            notes.append(f"{r['dropped_lines']} unparsable line(s) dropped before profiling")
        if r.get("synthetic_messages"):
            notes.append(f"{r['synthetic_messages']} zero-usage client-generated '<synthetic>' message(s) (rate-limit error) excluded from calls; wall interval includes any wait")
        if not r.get("effort"):
            notes.append("no PRODUCTION_EFFORT written")
        if a["id"] == "a0ab8841edc53ca1f":
            notes.append("this driver's own worker; transcript still open at measurement time")
        if r["first"] and r["last"]:
            f = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
            row["wall_seconds"] = round((f(r["last"]) - f(r["first"])).total_seconds(), 3)
        if r.get("profile"):
            p = json.loads(Path(r["profile"]).read_text())
            tk = p["tokens"]
            models = r.get("models") or []
            row["model"] = "+".join(models) if models else n(a.get("log_model"))
            if len(models) > 1:
                notes.append("multiple observed models")
            row.update(calls=p["model_calls"], fresh_input=n(tk.get("input")), cache_read=n(tk.get("read")),
                       cache_write_5m=n(tk.get("write5m")), cache_write_1h=n(tk.get("write1h")),
                       cache_write_unclassified=n(p.get("cache_write_unclassified_tokens")), output=n(tk.get("output")))
            miss = {k: v.get("calls_missing_field") for k, v in p["coverage"].items() if v.get("calls_missing_field")}
            if miss:
                notes.append("calls missing fields: " + json.dumps(miss))
            row["_roles"] = a["role"]
        else:
            row["model"] = n(a.get("log_model"))
        row["coverage_notes"] = "; ".join(notes)
        rows.append(row)
        if r.get("effort"):
            (OUT / "effort").mkdir(exist_ok=True)
            eff = PRIVATE / a["id"] / "effort" / "PRODUCTION_EFFORT.json"
            src = json.loads(eff.read_text())
            # sanitize check: receipt holds only counts, ids, roles, timestamps
            allowed = {"schema", "events", "provenance"}
            assert set(src) == allowed
            shutil.copyfile(eff, OUT / "effort" / f"{a['id']}.json")
    cols = ["agent_id", "role", "phase", "batch", "model", "started_utc", "finished_utc", "wall_seconds", "calls",
            "fresh_input", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_unclassified", "output",
            "tool_uses", "bash_calls", "coverage_notes", "hamilton_status"]
    with (OUT / "AGENT_USAGE.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    summarize(rows, agents)


CATS = ["fresh_input", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_unclassified", "output"]


def add_cats(acc, row):
    for c in CATS:
        v = row.get(c)
        if v not in ("", None):
            acc[c] = acc.get(c, 0) + v
            acc.setdefault("_seen", set()).add(c)


def clean(acc):
    return {c: acc.get(c) for c in CATS}  # absent category stays null, never zero


def summarize(rows, agents):
    by_phase, by_model = {}, {}
    for r in rows:
        if r.get("calls") in (None, ""):
            continue
        for key, d in ((r["phase"], by_phase), (r["model"], by_model)):
            e = d.setdefault(key, {"agents": 0, "calls": 0})
            e["agents"] += 1; e["calls"] += r["calls"]; add_cats(e, r)
    fix = lambda d: {k: {"agents": v["agents"], "calls": v["calls"], **clean(v)} for k, v in sorted(d.items())}
    # production batches: union batches that share a reviewer agent
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    prod_batches = set()
    for a in agents.values():
        if a["role"] == "producer":
            prod_batches.update(a["batches"])
    for a in agents.values():
        if a["role"] == "reviewer":
            bs = [b for b in a["batches"] if b in prod_batches]
            for b in bs:
                find(b); parent[find(b)] = find(bs[0])
    for b in prod_batches:
        find(b)
    groups = defaultdict(list)
    for b in sorted(prod_batches):
        groups[find(b)].append(b)
    rowmap = {r["agent_id"]: r for r in rows}
    def filed(b):
        p = CLAIMS / f"claude-2026-11-04-tribonian-{b}.jsonl"
        return sum(1 for l in p.read_text().splitlines() if l.strip()) if p.exists() else 0
    out_groups, excluded = [], []
    for g in sorted(groups.values()):
        acc, members, missing = {}, [], []
        for a in agents.values():
            if a["role"] in ("producer", "reviewer") and any(b in g for b in a["batches"]):
                r = rowmap[a["id"]]
                if r.get("calls") in (None, ""):
                    missing.append(a["id"]); continue
                add_cats(acc, r); members.append({"agent_id": a["id"], "role": a["role"]})
        claims = {b: filed(b) for b in g}
        total = sum(claims.values())
        entry = {"batches": g, "filed_claims_by_batch": claims, "filed_claims_total": total,
                 "includes": members, "tokens_by_category": clean(acc),
                 "observed_tokens_per_filed_claim": {c: (acc[c] / total if total and c in acc else None) for c in CATS},
                 "ratio_label": "observed_tokens_per_filed_claim",
                 "notes": []}
        if not total:
            entry["notes"].append("zero filed claims; ratio undefined, left null")
        if len(g) > 1:
            entry["notes"].append("batches share a reviewer agent; tokens are not separable, so the ratio is for the group")
        if missing:
            entry["notes"].append("agents without profile: " + ",".join(missing))
        if not any(m["role"] == "reviewer" for m in members):
            entry["notes"].append("no reviewer agent found in the log for this batch")
        out_groups.append(entry)
    for a in agents.values():
        if a["role"] not in ("producer", "reviewer") or all(b not in prod_batches for b in a["batches"]):
            excluded.append({"agent_id": a["id"], "role": a["role"], "batch": "+".join(a["batches"]),
                             "reason": "not a production-batch producer/reviewer (re-review, correction, integration, adapter, telemetry, coordinator, or unknown)"})
    summary = {
        "generated_from": "AGENT_USAGE.csv via Hamilton profile.py (jobs/hamilton-token-audit)",
        "token_categories_note": "fresh_input, cache_read, cache_write and output are separate, nonoverlapping categories and are never summed together. Null means no value observed.",
        "totals_by_phase": fix(by_phase), "totals_by_model": fix(by_model),
        "production_batches": out_groups,
        "excluded_from_production_batch_ratios": excluded,
        "notes": ["Coordinator transcript spans earlier work (coverage partial).",
                  "Output tokens may be a streaming lower bound where Hamilton reports calls without final output counts.",
                  "Batches o25-o30 and unfilled claims files count as 0 filed claims; ratios for them are null.",
                  "Filed-claim counts are lines in the claims files present at run time; the completion chain was interrupted by a full disk, so later batches may file more claims and these ratios then fall.",
                  "Re-review, correction, integration, adapter, telemetry and coordinator agents are excluded from batch ratios; see excluded_from_production_batch_ratios.",
                  "Blind review and after-reveal share one reviewer transcript and are included together."]}
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()
