#!/usr/bin/env python3
"""Junto finder `hamilton`: turns Hamilton's token audit into candidate savers.

Wraps jobs/hamilton-token-audit/profile.py (`load`, `profile`, `tool_label`; that
file supplies the shared usage parser), runs it over saved transcript pages, and emits
one candidate per saver, all `status: "unverified"`. Candidates are triage
material: every dollar figure is an estimate and never counts as a saving. A
saving counts only after a before-and-after test (research/plans/JUNTO_DESIGN.md).

usage (design section 2):
  python3 -I jobs/junto/finders/hamilton.py --data DIR --out FILE.jsonl --run-id R-yyyymmdd-n
                                            [--profiles DIR] [--candidate-start N]

DIR (outside the repository) holds `session_index.json` (get_session totals),
optionally `MANIFEST.json` (which sessions are complete), and
`events/<session_id>/*.json` (saved list_events pages).

Extra numeric pass: profile.profile() returns only per-cause aggregates, so this
file re-reads the same events for per-call usage numbers (tokens, timestamps,
redacted tool labels from `tool_label`). It never keeps or emits any text.

Dollar basis: an observed window can be calibrated only against independently
reported complete session token categories. A manifest claiming complete pages
does not establish complete output usage. No rate is borrowed from another
session. Unpriced sessions remain in the check sidecar; no saving is inferred.

Exit codes: 0 ok; 2 bad or empty input, or a sanity-check failure; 3 privacy
refusal (data inside the repo, or a record failed the redaction check).
"""
import argparse, collections, hashlib, importlib.util, json, re, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FINDER_NAME, FINDER_VERSION = "hamilton", "2"
FINDER_ID = "F-" + FINDER_NAME
WRITTEN_BY = "claude"

# Cause keys this finder is meant to cover (register these in finders.json `targets`).
TARGETS = ["coordinator_context", "fixed_setup", "idle_wait", "narration", "tool_output"]

# Relative prices, copied from profile.W and checked against it at start-up.
W = {"input": 1.0, "read": 0.1, "write5m": 1.25, "write1h": 2.0, "output": 5.0}

# Assumptions used only to rank candidates. None of them is measured.
SHARE_MIN = 0.05           # design: a cause key above 5% of a session's cost gets a saver
MAIN_SHARE_MIN = 0.60      # design: main-agent share above 60% means coordinator_context
REVERE_CAP = 200_000       # Hamilton: coordinators held below about 150-200k tokens
HANDOFF = 20_000           # state file the fresh session starts from (tokens)
HANDOFF_OUT = 8_000        # tokens the old session writes to produce that file
WATCH_CTX = 50_000         # context of a scripted or fresh watcher (tokens)
IDLE_GAP_S = 300           # cache time-to-live: a rebuild after a longer gap is an idle rebuild
SETUP_TRIM = 10_000        # tokens trimmed from each agent's fixed setup (Hamilton's example)
NARRATION_CUT = 0.5        # fraction of narration cost a reply cap removes
TOOL_OUTPUT_CUT = 0.25     # fraction of tool-output cost a 20-line print cap removes
REBUILD_TOKENS = 100_000   # same threshold as profile.py
POLL_TOOLS = {"ReadNotifications", "MCP github pull_request_read get",
              "MCP github pull_request_read get_check_runs",
              "MCP github actions_list list_workflow_runs",
              "MCP claude-code-remote get_session", "TaskOutput"}  # mirrors profile.py


def load_hamilton():
    path = REPO / "jobs" / "hamilton-token-audit" / "profile.py"
    spec = importlib.util.spec_from_file_location("hamilton_profile", path)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(mod)
    if dict(mod.W) != W:
        raise SystemExit("hamilton profile.py prices changed; update W in this finder")
    return mod


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def ctx_of(c):
    return c["read"] + c["write5m"] + c["write1h"] + c["input"]


def units_of(c):
    return sum(W[k] * c[k] for k in W)


def scan_calls(events, tool_label, usage_reader=None):
    """Per-call numbers in transcript order, rebuilt the way profile.profile() does."""
    calls = collections.OrderedDict()
    last_ts = {}
    for ts, kind, body in events:
        if kind != "assistant":
            continue
        msg = (body.get("internal_anthropic_catchall") or {}).get("message") or body.get("message")
        if not isinstance(msg, dict):
            continue
        agent = (body.get("internal_anthropic_catchall") or {}).get("parent_tool_use_id") or "main"
        mid = msg.get("id")
        if mid not in calls:
            u = msg.get("usage") or {}
            cc = u.get("cache_creation") or {}
            w1h = cc.get("ephemeral_1h_input_tokens", 0)
            w5m = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) - w1h)
            t = parse_ts(ts)
            calls[mid] = {"t": t, "agent": agent, "read": u.get("cache_read_input_tokens", 0),
                          "write5m": max(w5m, 0), "write1h": w1h, "input": u.get("input_tokens", 0),
                          "output": u.get("output_tokens", 0), "tools": set(),
                          "gap": (t - last_ts[agent]) if (t is not None and agent in last_ts) else None,
                          "first": agent not in last_ts}
            if usage_reader:
                calls[mid].update({k: v or 0 for k, v in usage_reader(u).items()})
            if t is not None:
                last_ts[agent] = t
            else:
                last_ts.setdefault(agent, 0)
        elif usage_reader:
            for k, value in usage_reader(msg.get("usage") or {}).items():
                if value is not None:
                    calls[mid][k] = max(calls[mid][k], value)
        for b in msg.get("content") or []:
            if b.get("type") == "tool_use":
                calls[mid]["tools"].add(tool_label(b.get("name", ""), b.get("input")))
    return list(calls.values())


def cause_key(label):
    """Hamilton cause label -> Junto cause key (design section 4)."""
    if label.startswith("fixed setup"):
        return "fixed_setup"
    if label == "model wrote: reply or narration":
        return "narration"
    if label.startswith("model wrote:"):
        return "model_writes"
    if label in ("user or system message", "model continuing", "history before the transcript starts"):
        return "unmapped:" + label
    return "tool_output"          # a tool result: Read, Bash cat/sed/ls/..., MCP ..., Artifact, ...


def safe_label(key):
    return "unmapped:redacted_label" if ("=" in key or "@" in key or len(key) > 60) else key


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None


def analyze(ham, sid, events, complete, scale, scale_basis, base_fallback):
    """All per-session numbers. `scale` converts cost units to USD."""
    calls = scan_calls(events, ham.tool_label, ham.usage_counts)
    prof = ham.profile(events, None, sid)              # units, not dollars
    total_units = prof["cost_units"]
    usd = lambda units: units * scale
    out = {"session_id": sid, "complete": complete, "events": len(events), "model_calls": len(calls),
           "scale": scale, "scale_basis": scale_basis, "total_units": total_units,
           "attributed_usd": usd(total_units), "cache_read_tokens": prof["tokens"]["read"]}
    if not calls or not total_units:
        return out

    # cause keys from Hamilton's cost_by_cause (top 25 causes only: a lower bound)
    by_key, by_label = collections.Counter(), {}
    for r in prof["cost_by_cause"]:
        k = safe_label(cause_key(r["cause"]))
        by_key[k] += r["share"]
        by_label[k] = by_label.get(k, 0) + r["cost"]
    out["cause_share"] = {k: round(v, 4) for k, v in sorted(by_key.items())}
    out["cause_usd"] = {k: usd(v) for k, v in by_label.items()}

    main = [c for c in calls if c["agent"] == "main"]
    sub_units = prof["subagents"]["cost"]
    out["main_share"] = 1 - sub_units / total_units
    out["main_usd"] = usd(total_units - sub_units)
    out["median_ctx_all"] = statistics.median(ctx_of(c) for c in calls)
    out["median_ctx_main"] = statistics.median(ctx_of(c) for c in main) if main else None

    # fixed setup: first-call context of each agent (not trustworthy if the start is missing)
    firsts = {}
    for c in calls:
        firsts.setdefault(c["agent"], ctx_of(c))
    out["agents"] = len(firsts)
    out["median_setup_tokens"] = statistics.median(firsts.values())
    base_main = firsts.get("main") if complete else None
    if base_main is None or base_main > 2 * (base_fallback or base_main):
        base_main = base_fallback or firsts.get("main") or 70_000
    out["base_main"] = base_main

    # Revere: hold the coordinator under REVERE_CAP by handing off to a fresh session
    off, resets, saved, prev_read = 0, 0, 0.0, 0
    for c in main:
        if prev_read and c["read"] < 0.5 * prev_read:
            off = 0                                    # the session was compacted anyway
        prev_read = c["read"]
        if ctx_of(c) - off > REVERE_CAP:
            off, resets = ctx_of(c) - (base_main + HANDOFF), resets + 1
        saved += W["read"] * min(c["read"], max(off, 0))
    overhead = resets * (W["write1h"] * (base_main + HANDOFF) + W["output"] * HANDOFF_OUT)
    out["revere"] = {"units": max(saved - overhead, 0.0), "resets": resets}

    # waiting in a large context: status checks and idle cache rebuilds
    polls = [c for c in calls if c["read"] > 300_000 and c["output"] < 400 and c["tools"] & POLL_TOOLS]
    poll_ids = {id(c) for c in polls}
    rebuild = lambda c: c["write5m"] + c["write1h"]
    # what the rebuild actually cost: 5-minute and 1-hour writes are priced separately
    rebuild_units = lambda c: W["write5m"] * c["write5m"] + W["write1h"] * c["write1h"]
    # cost of rewriting only `keep` tokens at the same mix of write prices
    rewrite_units = lambda c, keep: rebuild_units(c) * min(keep, rebuild(c)) / rebuild(c) if rebuild(c) else 0.0
    idle_rebuilds = [c for c in calls if rebuild(c) > REBUILD_TOKENS and not c["first"]
                     and c["gap"] is not None and c["gap"] > IDLE_GAP_S]
    poll_cost = sum(units_of(c) for c in polls)
    poll_rebuild = [c for c in idle_rebuilds if id(c) in poll_ids]
    other_rebuild = [c for c in idle_rebuilds if id(c) not in poll_ids]
    out["profile_status_check_units"] = sum(prof["status_checks_in_large_context"].values())
    out["scan_status_check_units"] = poll_cost
    # Watchman keeps the final check (it is the wake-up), so that poll is not saved
    kept = polls[-1] if polls else None
    wsaved = 0.0
    for c in polls:
        if c is kept:
            continue
        wsaved += W["read"] * max(c["read"] - WATCH_CTX, 0)
        if id(c) in {id(x) for x in poll_rebuild}:
            wsaved += rebuild_units(c) - rewrite_units(c, WATCH_CTX)
    out["watchman"] = {"units": wsaved, "polls": len(polls),
                       "cost_units": poll_cost,
                       "median_ctx": statistics.median(ctx_of(c) for c in polls) if polls else None}
    isaved = sum(max(rebuild_units(c) - rewrite_units(c, base_main + HANDOFF) - W["output"] * HANDOFF_OUT, 0)
                 for c in other_rebuild)
    out["idle_cache"] = {"units": isaved, "rebuilds": len(other_rebuild),
                         "cost_units": sum(rebuild_units(c) for c in other_rebuild),
                         "median_ctx": statistics.median(ctx_of(c) for c in other_rebuild) if other_rebuild else None}

    # Spare setup: SETUP_TRIM tokens off each agent's setup (re-read on every call, written once)
    base_by_agent = {a: min(v, 10**9) for a, v in firsts.items()}
    ssaved = 0.0
    for c in calls:
        ssaved += W["read"] * min(SETUP_TRIM, base_by_agent[c["agent"]], c["read"])
    ssaved += sum(W["write5m"] * min(SETUP_TRIM, v) for v in base_by_agent.values())
    out["spare_setup"] = {"units": ssaved}
    return out


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def build_candidates(rows, profiles_for, run_id, start_n, now_iso):
    """rows: analyzed sessions. Returns candidate dicts, sorted by estimate."""
    day = run_id.split("-")[1] if run_id.count("-") >= 2 else now_iso[:10].replace("-", "")
    specs = []

    def add(saver_key, title, targets, cause, evid, est, proposed_test):
        specs.append(dict(saver_key=saver_key, title=title, targets=targets, cause=cause,
                          evid=evid, est=est, proposed_test=proposed_test))

    def collect(key_fn):
        """key_fn(row) -> (cause_usd, median_ctx, est_units) or None."""
        evid, est = [], {}
        for r in rows:
            got = key_fn(r)
            if not got:
                continue
            cusd, mctx, eunits = got
            evid.append({"session_id": r["session_id"], "profile": profiles_for.get(r["session_id"]),
                         "cause_key": None, "usd": round(cusd, 2),
                         "share": round(cusd / r["attributed_usd"], 4) if r["attributed_usd"] else 0.0,
                         "events": r["events"], "model_calls": r["model_calls"],
                         "median_context_tokens": int(mctx) if mctx is not None else None})
            est[r["session_id"]] = (eunits * r["scale"], eunits, r["complete"])
        return evid, est

    # coordinator_context -> Revere
    def f_coord(r):
        if r.get("main_share", 0) > MAIN_SHARE_MIN and r.get("median_ctx_main"):
            return r["main_usd"], r["median_ctx_main"], r["revere"]["units"]
    e, s = collect(f_coord)
    add("revere_phase_handoff", "Revere: hand off to a fresh session before the coordinator grows",
        ["coordinator_context"], "coordinator_context", e, s,
        "Run one Y1 build phase with handoffs at a 200k-token cap against the audited X1 coordinator; unit completed_phase; measure get_session cost per phase and checker pass.")

    # idle_wait -> Watchman, and idle cache avoidance
    def idle_total(r):
        w, i = r.get("watchman", {}), r.get("idle_cache", {})
        return (w.get("cost_units", 0) + i.get("cost_units", 0)) / r["total_units"] if r.get("total_units") else 0

    def f_watch(r):
        if r.get("watchman") and idle_total(r) >= SHARE_MIN and r["watchman"]["cost_units"] > 0:
            return r["watchman"]["cost_units"] * r["scale"], r["watchman"]["median_ctx"], r["watchman"]["units"]
    e, s = collect(f_watch)
    add("watchman_outside_monitoring", "Watchman: monitor pull requests and CI outside the big session",
        ["idle_wait"], "idle_wait", e, s,
        "Run the next pull-request babysit to merge with a scripted CI watcher that wakes the main session only on change, against the audited PR 31/33 session; unit pr_babysit_to_merge.")

    def f_idle(r):
        if r.get("idle_cache") and idle_total(r) >= SHARE_MIN and r["idle_cache"]["cost_units"] > 0:
            return r["idle_cache"]["cost_units"] * r["scale"], r["idle_cache"]["median_ctx"], r["idle_cache"]["units"]
    e, s = collect(f_idle)
    add("idle_cache_avoidance", "Avoid idle cache rebuilds: resume from a short handoff after waiting",
        ["idle_wait"], "idle_wait", e, s,
        "Before an expected idle longer than 5 minutes write a handoff and resume in a short context; compare the first resumed call's cache write with an audited rebuild; unit resumed_wait.")

    # fixed_setup -> Spare setup (only where the session start is in the data)
    def f_setup(r):
        if r.get("complete") and r.get("cause_share", {}).get("fixed_setup", 0) >= SHARE_MIN:
            return (r["cause_usd"]["fixed_setup"], r["median_setup_tokens"], r["spare_setup"]["units"])
    e, s = collect(f_setup)
    add("spare_setup_trim", "Spare setup: shrink the fixed per-agent setup read on every call",
        ["fixed_setup"], "fixed_setup", e, s,
        "Start one empty session per configuration (connectors off, shorter rules) and read each first-call context in tokens; unit empty_session_first_call.")

    # narration / tool_output -> Quiet protocol
    def f_narr(r):
        if r.get("cause_share", {}).get("narration", 0) >= SHARE_MIN:
            return r["cause_usd"]["narration"], r["median_ctx_all"], NARRATION_CUT * r["cause_usd"]["narration"] / r["scale"]
    e, s = collect(f_narr)
    add("narration_cap", "Quiet protocol: cap replies and move long reasoning into files",
        ["narration"], "narration", e, s,
        "Run the next agent batch with replies capped at a few lines and reports written to files; re-audit against the audited X1 batch; unit accepted_claim.")

    def f_tool(r):
        if r.get("cause_share", {}).get("tool_output", 0) >= SHARE_MIN:
            return r["cause_usd"]["tool_output"], r["median_ctx_all"], TOOL_OUTPUT_CUT * r["cause_usd"]["tool_output"] / r["scale"]
    e, s = collect(f_tool)
    add("tool_output_cap", "Quiet protocol: scripts print twenty lines or fewer",
        ["tool_output"], "tool_output", e, s,
        "Run the next agent batch with scripts printing at most 20 lines and files read by range; re-audit against the audited X1 batch; unit accepted_claim.")

    out = []
    for sp in specs:
        if not sp["evid"]:
            continue
        comp = {k: v for k, v in sp["est"].items() if v[2]} or sp["est"]
        usd_ps = mean(v[0] for v in comp.values())
        tok_ps = mean(v[1] for v in comp.values())
        n_c = sum(1 for v in sp["est"].values() if v[2])
        n_p = len(sp["est"]) - n_c
        basis = {"revere_phase_handoff": "simulated: main context held under 200k with a 20k handoff, net of handoff cost",
                 "watchman_outside_monitoring": "simulated: status checks run in a 50k context, last check kept",
                 "idle_cache_avoidance": "simulated: idle rebuild rewrites a short handoff context instead",
                 "spare_setup_trim": "simulated: 10k tokens off each agent's setup on every call",
                 "narration_cap": "assumed: reply cap removes 50% of narration cost",
                 "tool_output_cap": "assumed: print cap removes 25% of tool-output cost (top-25 causes only)"}[sp["saver_key"]]
        basis += "; mean of %d complete session(s)" % n_c if n_c else "; partial sessions only"
        if n_p and n_c:
            basis += ", %d partial excluded" % n_p
        basis += "; tokens are input-price cost units; overlaps other savers; unmeasured"
        for ev in sp["evid"]:
            ev["cause_key"] = sp["cause"]
        out.append((usd_ps, sp, {"usd_per_session": round(usd_ps, 2), "tokens_per_session": int(tok_ps),
                                 "basis": basis}))
    out.sort(key=lambda x: (-x[0], x[1]["saver_key"]))
    cands = []
    for n, (usd_ps, sp, est) in enumerate(out, start_n):
        cands.append({"schema": "junto.candidate/1", "candidate_id": "C-%s-%d" % (day, n), "rev": 0,
                      "finder_id": FINDER_ID, "run_id": run_id, "saver_key": sp["saver_key"],
                      "title": sp["title"], "targets": sp["targets"],
                      "evidence": sorted(sp["evid"], key=lambda e: e["session_id"]),
                      "estimate": est, "usd_basis": "profile_scaled", "proposed_test": sp["proposed_test"],
                      "status": "unverified", "status_ref": None,
                      "written_at": now_iso, "written_by": WRITTEN_BY})
    return cands


SECRET = re.compile(r"ghp_|github_pat_|\bsk-[A-Za-z0-9_-]{16,}|xox[abprs]-|AKIA[0-9A-Z]{16}|Bearer\s|-----BEGIN"
                    r"|(?:token|key|sig|password|secret)=|@[\w-]+\.\w+|https?://\S*\?|/home/|/tmp/|/root/")


def redaction_ok(records):
    for rec in records:
        for ev in rec.get("evidence", []):
            if len(json.dumps(ev)) > 200 + 160:
                return False
        if SECRET.search(json.dumps(rec)):
            return False
    return True


def main():
    t0 = time.time()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--profiles")
    ap.add_argument("--candidate-start", type=int, default=1)
    a = ap.parse_args()
    data = Path(a.data).resolve()
    try:
        data.relative_to(REPO)
        print("refused: --data is inside the repository"); return 3
    except ValueError:
        pass
    if not re.fullmatch(r"R-\d{8}-\d+", a.run_id):
        print("bad --run-id (expected R-yyyymmdd-n)"); return 2
    idx = load_json(data / "session_index.json")
    if not idx or not (data / "events").is_dir():
        print("bad input: need session_index.json and events/<session_id>/ pages"); return 2
    index = {s["id"]: s for s in idx.get("sessions", [])}
    manifest = load_json(data / "MANIFEST.json") or {}
    complete_of = {s["session_id"]: bool(s.get("complete")) for s in manifest.get("sessions", [])}

    ham = load_hamilton()
    files, sessions = [data / "session_index.json"], {}
    for d in sorted((data / "events").iterdir()):
        pages = sorted(p for p in d.glob("*") if p.is_file())
        if d.is_dir() and pages:
            ev = ham.load(d)
            if ev:
                sessions[d.name] = ev
                files += pages
    if (data / "MANIFEST.json").is_file():
        files.append(data / "MANIFEST.json")
    if not sessions:
        print("bad input: no events"); return 2

    # A manifest saying complete does not make streamed output complete. No
    # cross-session borrowed rate, and no full bill assigned to a partial window.
    def totals(s):
        if isinstance(s.get("token_totals"), dict):
            return s["token_totals"]
        aliases = {"input":"input_tokens", "read":"cache_read_tokens", "write5m":"cache_write_5m_tokens",
                   "write1h":"cache_write_1h_tokens", "output":"output_tokens"}
        return {k:s.get(v) for k,v in aliases.items()}
    probe = {sid: ham.profile(ev, (index.get(sid) or {}).get("cost_usd"), sid,
                             session_totals=totals(index.get(sid) or {})) for sid, ev in sessions.items()}
    bases = []
    for sid, ev in sessions.items():
        if complete_of.get(sid):
            first = next((c for c in scan_calls(ev, ham.tool_label, ham.usage_counts) if c["agent"] == "main"), None)
            if first:
                bases.append(ctx_of(first))
    base_fallback = statistics.median(bases) if bases else None

    rows, skipped = [], []
    for sid in sorted(sessions):
        s = index.get(sid) or {}
        complete = complete_of.get(sid, False) and all(probe[sid]["tokens"][k] == totals(s).get(k) for k in W)
        scale = probe[sid]["usd_per_unit"]
        basis = "observed window calibrated to independent full-session category totals; relative-price assumption"
        if scale is None or scale <= 0:
            skipped.append(sid); continue
        rows.append(analyze(ham, sid, sessions[sid], complete, scale, basis, base_fallback))

    # sanity: attributed cost never exceeds a session's reported total
    check = {"sessions": [], "skipped_no_rate": len(skipped),
             "unpriced_sessions": [{"session_id": sid, "coverage": probe[sid]["coverage"],
                                     "token_value_usd": probe[sid]["session_token_value_usd"],
                                     "reason":"no complete category totals to calibrate observed usage"} for sid in skipped]}
    bad = False
    for r in rows:
        total = (index.get(r["session_id"]) or {}).get("cost_usd")
        rd = (index.get(r["session_id"]) or {}).get("cache_read_tokens")
        ok = total is None or r["attributed_usd"] <= total * 1.0001
        bad |= not ok
        check["sessions"].append({
            "session_id": r["session_id"], "complete": r["complete"], "events": r["events"],
            "reported_cost_usd": total, "attributed_usd": round(r["attributed_usd"], 2),
            "attributed_le_reported": ok, "scale_basis": r["scale_basis"],
            "cache_read_coverage": round(r["cache_read_tokens"] / rd, 4) if rd else None,
            "status_check_units_profile_vs_scan": [r.get("profile_status_check_units"), round(r.get("scan_status_check_units", 0))],
            "cause_share": r.get("cause_share")})

    # committed profiles, matched by model-call count and event count
    profiles_for, nprof = {}, 0
    if a.profiles:
        for pf in sorted(Path(a.profiles).glob("PROFILE_*.json")):
            nprof += 1
            files.append(pf)
            p = load_json(pf) or {}
            try:
                rel = pf.resolve().relative_to(REPO).as_posix()
            except ValueError:
                continue
            for r in rows:
                if p.get("model_calls") == r["model_calls"] and abs(p.get("events", -9) - r["events"]) <= max(2, r["events"] // 100):
                    profiles_for.setdefault(r["session_id"], rel)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cands = build_candidates(rows, profiles_for, a.run_id, a.candidate_start, now_iso)
    for c in cands:   # no estimate may exceed the session it comes from
        for ev in c["evidence"]:
            tot = (index.get(ev["session_id"]) or {}).get("cost_usd")
            if tot is not None and ev["usd"] > tot + 0.005:   # evidence is rounded to cents
                bad = True
    check["sanity_ok"] = not bad
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    Path(str(out) + ".check.json").write_text(json.dumps(check, indent=1) + "\n")
    if bad:
        print("sanity check failed: attributed cost exceeds a session total"); return 2
    if not redaction_ok(cands):
        print("redaction check failed; nothing written"); return 3
    out.write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cands))
    run = {"run_id": a.run_id, "finder_id": FINDER_ID, "finder_version": FINDER_VERSION,
           "wall_seconds": round(time.time() - t0, 2), "data_digest": None,
           "inputs": {"profiles": nprof, "sessions": len(rows), "events": sum(r["events"] for r in rows)},
           "candidates_emitted": [c["candidate_id"] for c in cands],
           "usd_spent": None, "usd_basis": "local_script", "round_id": None}
    dig = hashlib.sha256()
    for f in sorted(files, key=lambda p: (p.parent.name if p.parent != data else "", p.name)):
        dig.update(("%s/%s %d\n" % (f.parent.name if f.parent != data else ".", f.name, f.stat().st_size)).encode())
    run["data_digest"] = dig.hexdigest()
    Path(str(out) + ".run.json").write_text(json.dumps(run, indent=1) + "\n")

    print("finder %s: %d sessions (%d complete), %d events, %d candidates, all unverified"
          % (FINDER_ID, len(rows), sum(r["complete"] for r in rows), run["inputs"]["events"], len(cands)))
    for c in cands[:19]:
        print("%-28s est $%.2f/session (not counted)" % (c["saver_key"], c["estimate"]["usd_per_session"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
