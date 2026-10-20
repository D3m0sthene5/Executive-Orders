"""Clausewitz: the friction miner, a Junto finder (finder id F-friction).

Named for Carl von Clausewitz, whose "On War" gave friction its name: the many small
things that go wrong and make the simplest plan hard to carry out. This finder counts
the friction in saved agent transcripts and prices it.

What it counts, per session (never any transcript text):
  permission  commands or tools that were denied or blocked (classifier, harness block)
  merge_conflict  git merge conflicts and rejected pushes
  oversize    tool results the harness refused as too large (the model must ask again)
  tool_error  tool calls that failed (nonzero exit, tool error); also how many were retried
  reread      the same file read again, unchanged, while the first read was still in context
  stale_poll  a status check repeated with an identical answer
  duplicate_run  the same command, search or job trigger repeated with the same result

Pricing (Hamilton's model, jobs/hamilton-token-audit/profile.py): every model call is split
into its fresh input, the fixed setup it re-reads, the history it re-reads (shared out over the
items in context by size) and its own output. A friction event is charged for
  - the fresh and re-read cost of the text it put in context (the tool call and its result),
  - plus its share of the issuing call's fixed-setup re-read and output (the wasted round).
Each piece of each call is charged to at most one event, so the total can never exceed the
session total. Dollars use the session's own get_session cost_usd when the transcript is
complete; a partly saved session is priced at the median dollars-per-unit of the complete ones.

Everything emitted is status "unverified". Estimates rank work and never count as savings.

usage (the Junto finder interface):
  python3 -I jobs/junto/finders/friction.py --data DIR --out FILE --run-id R-yyyymmdd-n [--profiles DIR]
FILE ending in .json gets one JSON document (candidates plus per-session figures and the
sanity check); any other name gets one candidate per line (JSON Lines). FILE.run.json gets the
run record. Exit codes: 0 ok, 2 bad or empty input (or a failed sanity check), 3 privacy refusal.
"""
import argparse
import collections
import datetime
import difflib
import hashlib
import importlib.util
import json
import re
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
HAMILTON = HERE.parents[2] / "hamilton-token-audit" / "profile.py"

FINDER_ID = "F-friction"
VERSION = "1"
MIN_USD = 0.25          # emit a candidate only when its attributed cost reaches this
RETRY_WINDOW = 3        # a failed call counts as retried if a similar call follows within 3 calls

# category -> (cause key, saver key, title, proposed test)
CATS = {
    "permission": ("friction_permission", "permission_preapproval",
                   "Letter of Marque: pre-approve safe commands, no blocked waits",
                   "Same task twice, once with an allowlist and Monitor-style waits; measure denials and usd per accepted unit."),
    "merge_conflict": ("friction_merge_conflict", "conflict_guard",
                       "Mason-Dixon: one owner per branch, fetch and rebase before push",
                       "Two parallel-agent runs on one task, with and without the branch rule; measure conflicts and usd per merged PR."),
    "oversize": ("friction_oversize", "quiet_protocol",
                 "Quiet protocol: cap tool output before it enters context",
                 "Same agent batch with and without an output cap; measure oversize errors, tool_output cost and usd per unit."),
    "tool_error": ("friction_tool_error", "preflight_checks",
                   "Sentinel: check inputs and paths before long scripts run",
                   "Same job with a preflight step (paths, tools, network, schema); measure failed calls and usd per unit."),
    "reread": ("friction_reread", "reading_ledger",
               "Madison's Notes: keep a short file digest, do not re-read",
               "Same task with a read ledger rule; measure repeated reads of unchanged files and usd per unit."),
    "stale_poll": ("friction_stale_poll", "watchman_external_monitoring",
                   "Watchman: monitor jobs and PRs outside the large session",
                   "Next pull-request babysit with an external check that wakes the session on change; measure polls and usd."),
    "duplicate_run": ("friction_duplicate_run", "job_dedupe_guard",
                      "Treasury ledger: skip a run whose inputs and result are known",
                      "Same task with a run ledger (command, inputs, result hash); measure repeated runs and usd per unit."),
}
ORDER = ["permission", "merge_conflict", "oversize", "tool_error", "reread", "stale_poll", "duplicate_run"]

PERM_RE = re.compile(
    r"^(<tool_use_error>)?(Permission for (this|the) \w+ was denied|Blocked:|Permission to use .{0,80} has been denied|"
    r"The user doesn't want to proceed|User rejected|.{0,80}requested permissions? to use .{0,80}haven't granted)", re.S)
GIT_RE = re.compile(r"^\s*(CONFLICT \([^)]*\):|Automatic merge failed|error: failed to push some refs|"
                    r"! \[(remote )?rejected\]|error: could not apply)", re.M)
OVERSIZE_RE = re.compile(r"^Error: result \([\d,]+ characters")
POLLISH = ("MCP github actions_", "MCP github pull_request_read", "MCP claude-code-remote get_session",
           "TaskOutput", "ReadNotifications", "Bash gh", "Bash git fetch", "Bash git status", "Bash git log")
READ_BASH = {"Bash cat", "Bash head", "Bash tail", "Bash sed", "Bash nl"}
DUP_OK_PREFIX = ("Bash", "MCP", "WebFetch", "WebSearch", "Grep", "Glob", "ToolSearch")


def load_hamilton():
    spec = importlib.util.spec_from_file_location("hamilton_profile", str(HAMILTON))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def short_hash(obj):
    s = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True)
    return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:16]


def result_text(c):
    return c if isinstance(c, str) else json.dumps(c)


def is_trigger(label, cmd):
    return "actions_run_trigger" in label or (label == "Bash gh" and bool(re.search(r"\b(workflow run|run rerun)\b", cmd)))


# ---------------------------------------------------------------------------------------
# Pass 1: rebuild calls, items, tool uses and results from the transcript events
# ---------------------------------------------------------------------------------------
def rebuild(H, events):
    calls = collections.OrderedDict()   # message id -> call
    items = {}                           # item id -> dict
    uses = {}                            # tool_use_id -> dict
    results = []                         # in event order
    pending = []
    seq = 0

    def new_item(tokens, agent):
        nonlocal seq
        seq += 1
        items[seq] = {"tokens": tokens, "agent": agent}
        return seq

    for ts, kind, body in events:
        cat = body.get("internal_anthropic_catchall") or {}
        msg = cat.get("message") or body.get("message")
        if not isinstance(msg, dict):
            continue
        agent = cat.get("parent_tool_use_id") or "main"
        if kind == "assistant":
            mid = msg.get("id")
            u = msg.get("usage") or {}
            if mid not in calls:
                cc = u.get("cache_creation") or {}
                w1h = cc.get("ephemeral_1h_input_tokens", 0)
                w5m = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) - w1h)
                calls[mid] = {"idx": len(calls), "ts": ts, "agent": agent, "read": u.get("cache_read_input_tokens", 0),
                              "write5m": max(w5m, 0), "write1h": w1h, "input": u.get("input_tokens", 0),
                              "output": u.get("output_tokens", 0), "triggers": list(pending), "n_uses": 0}
                pending = []
            call = calls[mid]
            for b in msg.get("content") or []:
                if b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    label = H.tool_label(b.get("name", ""), inp)
                    iid = new_item(len(json.dumps(inp)) / 4, agent)
                    cmd = inp.get("command", "") if b.get("name") == "Bash" else ""
                    uses[b.get("id")] = {"item": iid, "call": call["idx"], "agent": agent, "name": b.get("name", ""),
                                         "label": label, "ihash": short_hash(inp), "cmd": cmd}
                    call["n_uses"] += 1
                    pending.append(iid)
                elif b.get("type") == "text":
                    pending.append(new_item(len(b.get("text") or "") / 4, agent))
        elif kind == "user":
            content = msg.get("content")
            if isinstance(content, list):
                for b in content:
                    if b.get("type") != "tool_result":
                        continue
                    text = result_text(b.get("content"))
                    iid = new_item(len(text) / 4, agent)
                    results.append({"use_id": b.get("tool_use_id"), "item": iid, "agent": agent,
                                    "is_error": bool(b.get("is_error")), "head": text[:400],
                                    "text": text[:30000], "rhash": short_hash(text)})
                    pending.append(iid)
            elif isinstance(content, str):
                pending.append(new_item(len(content) / 4, agent))
    return list(calls.values()), items, uses, results


# ---------------------------------------------------------------------------------------
# Pass 2: price every call, piece by piece (Hamilton's model)
# ---------------------------------------------------------------------------------------
def price(H, calls, items):
    W = H.W
    last_read = collections.defaultdict(int)
    base_ctx = {}
    live = collections.defaultdict(list)
    epoch = collections.defaultdict(int)
    fresh, carry = collections.Counter(), collections.Counter()
    overhead = {}            # call idx -> fixed-setup re-read + output units
    total = 0.0
    for c in calls:
        a = c["agent"]
        if c["read"] < 0.5 * last_read[a]:      # context compacted, or a new agent started
            live[a] = []
            base_ctx.pop(a, None)
            epoch[a] += 1
        last_read[a] = c["read"]
        c["epoch"] = epoch[a]
        trig = c["triggers"]
        live[a].extend(trig)
        fresh_in = W["input"] * c["input"] + W["write5m"] * c["write5m"] + W["write1h"] * c["write1h"]
        out_u = W["output"] * c["output"]
        ctx = c["read"] + c["write5m"] + c["write1h"] + c["input"]
        base_ctx.setdefault(a, ctx)
        base = min(base_ctx[a], c["read"])
        fixed_u = W["read"] * base
        hist_u = W["read"] * (c["read"] - base)
        c["ctx_tokens"] = ctx
        total += fresh_in + out_u + W["read"] * c["read"]
        overhead[c["idx"]] = fixed_u + out_u
        tok = sum(items[i]["tokens"] for i in trig)
        for i in trig:
            fresh[i] += fresh_in * ((items[i]["tokens"] / tok) if tok else 1.0 / len(trig))
        live_tok = sum(items[i]["tokens"] for i in live[a])
        if live_tok:
            for i in live[a]:
                carry[i] += hist_u * items[i]["tokens"] / live_tok
    return {"fresh": fresh, "carry": carry, "overhead": overhead, "total": total}


# ---------------------------------------------------------------------------------------
# Pass 3: classify friction events
# ---------------------------------------------------------------------------------------
def classify(calls, uses, results):
    seen_calls = {}      # (agent, name, input hash) -> (result hash, context epoch)
    events, errors = [], []
    for r in results:
        u = uses.get(r["use_id"])
        if not u:
            continue
        label, head, text = u["label"], r["head"], r["text"]
        cat = sub = None
        if PERM_RE.search(head):
            cat = "permission"
            sub = "blocked_wait" if head.startswith("<tool_use_error>Blocked") else "denied"
        elif GIT_RE.search(text):
            cat = "merge_conflict"
            sub = "rejected_push" if re.search(r"failed to push|rejected\]", text) else "conflict"
        elif OVERSIZE_RE.match(head):
            cat = "oversize"
        elif r["is_error"] or head.startswith(("Exit code", "<tool_use_error>")):
            cat = "tool_error"
        else:
            key = (u["agent"], u["name"], u["ihash"])
            prev = seen_calls.get(key)
            issue_epoch = calls[u["call"]]["epoch"]
            is_read = label == "Read" or label in READ_BASH
            if prev and is_trigger(label, u["cmd"]):
                cat, sub = "duplicate_run", "job_trigger"
            elif prev and prev[0] == r["rhash"]:
                if is_read:
                    if prev[1] == issue_epoch:
                        cat = "reread"
                elif label.startswith(POLLISH):
                    cat = "stale_poll"
                elif label.startswith(DUP_OK_PREFIX):
                    cat = "duplicate_run"
            seen_calls[key] = (r["rhash"], issue_epoch)
        if cat:
            events.append({"cat": cat, "sub": sub, "use": u, "res": r, "retried": False})
            if cat == "tool_error":
                errors.append(len(events) - 1)
    # retry: a later call by the same agent, within a few calls, repeating the tool with the same
    # or a very similar input
    by_agent = collections.defaultdict(list)
    for u in uses.values():
        by_agent[u["agent"]].append(u)
    for lst in by_agent.values():
        lst.sort(key=lambda x: x["item"])
    for ei in errors:
        u = events[ei]["use"]
        lst = by_agent[u["agent"]]
        pos = next((k for k, x in enumerate(lst) if x["item"] == u["item"]), None)
        if pos is None:
            continue
        for x in lst[pos + 1: pos + 1 + RETRY_WINDOW]:
            if x["label"] != u["label"]:
                continue
            a, b = u["cmd"][:1500], x["cmd"][:1500]
            if x["ihash"] == u["ihash"] or (a and b and difflib.SequenceMatcher(None, a, b).ratio() >= 0.6):
                events[ei]["retried"] = True
                break
    return events


def summarize_session(sid, label, n_events, calls, items, uses, results, H):
    pr = price(H, calls, items)
    evs = classify(calls, uses, results)
    cats = {k: {"events": 0, "units": 0.0, "junk_tokens": 0.0, "ctx": [], "retried": 0, "subs": collections.Counter()}
            for k in ORDER}
    for e in evs:
        u, r = e["use"], e["res"]
        issue = calls[u["call"]]
        units = (pr["fresh"][u["item"]] + pr["fresh"][r["item"]] + pr["carry"][u["item"]] + pr["carry"][r["item"]]
                 + pr["overhead"][u["call"]] / max(issue["n_uses"], 1))
        c = cats[e["cat"]]
        c["events"] += 1
        c["units"] += units
        c["junk_tokens"] += items[u["item"]]["tokens"] + items[r["item"]]["tokens"]
        c["ctx"].append(issue["ctx_tokens"])
        c["retried"] += 1 if e["retried"] else 0
        if e["sub"]:
            c["subs"][e["sub"]] += 1
    return {"session_id": sid, "label": label, "events": n_events, "model_calls": len(calls),
            "replay_units": round(pr["total"]), "_total_units": pr["total"], "_cats": cats,
            "tokens": {k: sum(c[k] for c in calls) for k in ("input", "read", "write5m", "write1h", "output")}}


def build(args):
    H = load_hamilton()
    data = Path(args.data).resolve()
    idx = {}
    if (data / "session_index.json").exists():
        for s in json.loads((data / "session_index.json").read_text()).get("sessions", []):
            idx[s["id"]] = s
    labels, manifest_complete = {}, {}
    if (data / "MANIFEST.json").exists():
        for s in json.loads((data / "MANIFEST.json").read_text()).get("sessions", []):
            labels[s["session_id"]] = s.get("label", "")
            manifest_complete[s["session_id"]] = bool(s.get("complete", True))
    edir = data / "events"
    sdirs = sorted(p for p in edir.iterdir() if p.is_dir())
    sessions, n_events = [], 0
    for sd in sdirs:
        ev = H.load(sd)
        if not ev:
            continue
        n_events += len(ev)
        calls, items, uses, results = rebuild(H, ev)
        if not calls:
            continue
        s = summarize_session(sd.name, labels.get(sd.name, ""), len(ev), calls, items, uses, results, H)
        s["permission_denials_in_result_events"] = sum(
            len(((b.get("internal_anthropic_catchall") or {}).get("permission_denials")) or [])
            for _, k, b in ev if k == "result")
        row = idx.get(sd.name) or {}
        read_idx = row.get("cache_read_tokens")
        s["coverage_cache_read"] = round(s["tokens"]["read"] / read_idx, 4) if read_idx else None
        # the manifest's word wins; without one, a transcript that covers under 98% of the
        # session's cache reads is treated as partial
        s["complete"] = (manifest_complete[sd.name] if sd.name in manifest_complete else
                         (s["coverage_cache_read"] is None or s["coverage_cache_read"] >= 0.98))
        s["session_cost_usd"] = row.get("cost_usd")
        sessions.append(s)
    if not sessions:
        return None
    # dollars per unit: the session's own cost when the transcript is complete, else the median of those
    rates = [s["session_cost_usd"] / s["replay_units"] for s in sessions
             if s["complete"] and s["session_cost_usd"] and s["replay_units"]]
    median_rate = statistics.median(rates) if rates else None
    for s in sessions:
        if s["complete"] and s["session_cost_usd"]:
            s["usd_per_unit"], s["usd_basis"] = s["session_cost_usd"] / s["replay_units"], "get_session.cost_usd"
        else:
            s["usd_per_unit"], s["usd_basis"] = median_rate, "profile_scaled"
        s["replay_usd"] = round(s["replay_units"] * s["usd_per_unit"], 2) if s["usd_per_unit"] else None
    return sessions, n_events, median_rate


def make_output(sessions, args, run_date):
    n_sessions = len(sessions)
    profile_map = {}
    if args.profiles:
        names = {"X1": "PROFILE_x1.json", "treemap parent": "PROFILE_treemap.json", "PRs 33 and 31": "PROFILE_prmerge.json",
                 "ProQuest": "PROFILE_proquest.json", "blocked-copy session": "PROFILE_upload_partial.json"}
        pdir = Path(args.profiles).resolve()
        for s in sessions:
            f = names.get(s["label"])
            if f and (pdir / f).exists():
                try:
                    profile_map[s["session_id"]] = str((pdir / f).relative_to(REPO))
                except ValueError:
                    pass
    session_docs, sanity = [], []
    by_cat = {k: [] for k in ORDER}
    for s in sessions:
        rate = s["usd_per_unit"]
        usd = (lambda x, r=rate: round(x * r, 2)) if rate else (lambda x: None)
        cat_docs, fr_units = {}, 0.0
        for k in ORDER:
            c = s["_cats"][k]
            fr_units += c["units"]
            share = round(c["units"] / s["_total_units"], 4) if s["_total_units"] else 0.0
            doc = {"events": c["events"], "usd": usd(c["units"]), "units": round(c["units"]),
                   "junk_tokens": round(c["junk_tokens"]), "share_of_replay": share}
            if k == "tool_error":
                doc["retried"] = c["retried"]
            if c["subs"]:
                doc["kinds"] = dict(sorted(c["subs"].items()))
            cat_docs[k] = doc
            if c["events"]:
                e = {"session_id": s["session_id"]}
                if s["session_id"] in profile_map:
                    e["profile"] = profile_map[s["session_id"]]
                e.update({"cause_key": CATS[k][0], "usd": usd(c["units"]), "share": share, "events": c["events"],
                          "model_calls": s["model_calls"],
                          "median_context_tokens": int(statistics.median(c["ctx"])) if c["ctx"] else 0})
                by_cat[k].append((e, c["units"]))
        fr_usd = usd(fr_units)
        cost = s["session_cost_usd"]
        bounds = [x for x in (cost, s["replay_usd"]) if x is not None]
        ok = bool(bounds) and fr_usd is not None and fr_usd <= min(bounds) + 1e-9 and fr_units <= s["_total_units"] + 1e-6
        fr_share = round(fr_units / s["_total_units"], 4) if s["_total_units"] else 0.0
        sanity.append({"session_id": s["session_id"], "friction_usd": fr_usd, "replay_usd": s["replay_usd"],
                       "session_cost_usd": cost, "friction_share_of_replay": fr_share, "within_session_total": ok})
        session_docs.append({
            "session_id": s["session_id"], "label": s["label"], "complete": s["complete"],
            "coverage_cache_read": s["coverage_cache_read"], "events": s["events"], "model_calls": s["model_calls"],
            "usd_basis": s["usd_basis"], "session_cost_usd": cost, "replay_usd": s["replay_usd"],
            "friction_usd": fr_usd, "friction_share_of_replay": fr_share,
            "permission_denials_in_result_events": s["permission_denials_in_result_events"],
            "by_category": cat_docs})
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cands, n = [], 0
    for k in ORDER:
        ev = by_cat[k]
        usd_total = sum(e["usd"] or 0.0 for e, _ in ev)
        if not ev or usd_total < MIN_USD:
            continue
        cause, saver, title, test = CATS[k]
        units_total = sum(u for _, u in ev)
        cands.append({
            "schema": "junto.candidate/1", "candidate_id": "", "rev": 0, "finder_id": FINDER_ID,
            "run_id": args.run_id, "saver_key": saver, "title": title, "targets": [cause],
            "evidence": [e for e, _ in sorted(ev, key=lambda x: -(x[0]["usd"] or 0))],
            "estimate": {"usd_per_session": round(usd_total / n_sessions, 2),
                         "tokens_per_session": round(units_total / n_sessions),
                         "usd_attributed_total": round(usd_total, 2),
                         "events_total": sum(e["events"] for e, _ in ev),
                         "basis": f"upper bound: friction cost attributed in {n_sessions} audited sessions, divided by {n_sessions}; "
                                  "assumes the saver removes all of it; tokens are input-price cost units; "
                                  "an incomplete session counts only its saved part"},
            "proposed_test": test, "status": "unverified", "status_ref": None,
            "usd_basis": "get_session.cost_usd" if all(s["usd_basis"] == "get_session.cost_usd" for s in sessions) else "profile_scaled",
            "written_at": now, "written_by": "claude"})
    cands.sort(key=lambda c: (-c["estimate"]["usd_attributed_total"], c["saver_key"]))
    for n, c in enumerate(cands, 1):
        c["candidate_id"] = f"C-{run_date}-{n}"
    return cands, session_docs, sanity, now


# ---------------------------------------------------------------------------------------
# Redaction check (Junto design, section 5)
# ---------------------------------------------------------------------------------------
BAD = re.compile(r"(ghp_|github_pat_|sk-|xox|AKIA|Bearer |-----BEGIN|token=|key=|sig=|@[A-Za-z0-9-]+\.[A-Za-z]|https?://\S*\?|/home/|/tmp/|/root/|scratchpad)")


def redaction_failures(obj, path="", out=None):
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            redaction_failures(str(k), path + "/key", out)
            redaction_failures(v, path + "/" + str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            redaction_failures(v, path + f"/{i}", out)
    elif isinstance(obj, str) and (BAD.search(obj) or len(obj) > 300):
        out.append(path)
    return out


def main():
    t0 = time.time()
    ap = argparse.ArgumentParser(description="Clausewitz friction miner (Junto finder)")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--profiles")
    args = ap.parse_args()
    data = Path(args.data).resolve()
    try:
        data.relative_to(REPO)
        print("refused: --data is inside the repository", file=sys.stderr)
        return 3
    except ValueError:
        pass
    if not (data / "events").is_dir():
        print("bad input: no events/ directory under --data", file=sys.stderr)
        return 2
    built = build(args)
    if built is None:
        print("bad input: no usable transcript events", file=sys.stderr)
        return 2
    sessions, n_events, median_rate = built
    m = re.match(r"R-(\d{8})-\d+$", args.run_id)
    run_date = m.group(1) if m else datetime.date.today().strftime("%Y%m%d")
    cands, session_docs, sanity, now = make_output(sessions, args, run_date)
    doc = {"schema": "junto.finder_output/1", "finder_id": FINDER_ID, "finder_version": VERSION, "run_id": args.run_id,
           "written_at": now, "written_by": "claude",
           "note": "Everything here is unverified. Estimates rank work and are never counted as savings.",
           "median_usd_per_unit_complete_sessions": median_rate,
           "sanity": {"all_within_session_total": all(x["within_session_total"] for x in sanity), "sessions": sanity},
           "sessions": session_docs, "candidates": cands}
    bad = redaction_failures(doc)
    if bad:
        print("privacy refusal: redaction check failed at " + ", ".join(bad[:5]), file=sys.stderr)
        return 3
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix == ".json":
        out.write_text(json.dumps(doc, indent=1) + "\n")
    else:
        out.write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cands))
    digest_src = sorted((p.name, p.stat().st_size) for p in (data / "events").rglob("*") if p.is_file())
    run = {"schema": "junto.run/1", "run_id": args.run_id, "finder_id": FINDER_ID, "finder_version": VERSION,
           "wall_seconds": round(time.time() - t0, 2),
           "data_digest": hashlib.sha256(json.dumps(digest_src).encode()).hexdigest(),
           "inputs": {"profiles": 0, "sessions": len(sessions), "events": n_events},
           "candidates_emitted": [c["candidate_id"] for c in cands], "usd_spent": None, "usd_basis": "local_script"}
    Path(str(out) + ".run.json").write_text(json.dumps(run, indent=1) + "\n")
    ok = doc["sanity"]["all_within_session_total"]
    lines = [f"friction: {len(sessions)} sessions, {n_events} events, {len(cands)} candidates (all unverified); sanity {'ok' if ok else 'FAILED'}"]
    for c in cands[:8]:
        e = c["estimate"]
        lines.append(f"  {c['saver_key']}: est ${e['usd_per_session']}/session, ${e['usd_attributed_total']} total, {e['events_total']} events")
    print("\n".join(lines[:20]))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
