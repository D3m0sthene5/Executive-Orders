"""Hamilton: an audit of where an agent session's tokens go.

Reads transcript pages saved from the claude-code-remote `list_events` tool
(one JSON page per file, `{"ccr": {"data": [...]}}`), rebuilds every model call
with its usage, and attributes cost to what caused it:

- fresh cost of a call (new input, cache writes, output) goes to the step that
  triggered it: the tool whose result the model was reading, or a user turn;
- re-read cost (cache reads) goes to every item still in context, in
  proportion to its size, so a large tool result pays for every later call
  that re-reads it until the context is compacted.

The model's own writing (commands, scripts, file bodies, replies) is
counted as context too. Transcripts record output tokens only at the start of
streaming, so output cost is understated here; session totals from
get_session are the reference.

Cost units retain explicit relative-price assumptions (input 1, cache read 0.1,
5-minute cache write 1.25, 1-hour cache write 2, output 5). Optional full-session
category totals calibrate only the observed window. A partial transcript never
absorbs the complete session value. Cash charges and price schedules are separate
observations. Sizes of tool results are characters / 4, an attribution estimate.

usage: python profile.py PAGES_DIR [--cost-usd N --session-totals TOTALS.json] --out OUT_DIR
"""
import argparse, collections, json, math, re
from pathlib import Path

W = {"input": 1.0, "read": 0.1, "write5m": 1.25, "write1h": 2.0, "output": 5.0}
PHASES = ("production", "build", "coordination", "monitoring", "review", "rework", "integration")


def finite_count(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def usage_counts(usage):
    """Unknown usage and unknown cache TTL stay unknown, rather than becoming free."""
    cc = usage.get("cache_creation") or {}
    writes = usage.get("cache_creation_input_tokens")
    result = {"input": usage.get("input_tokens"), "read": usage.get("cache_read_input_tokens"),
              "write5m": cc.get("ephemeral_5m_input_tokens"), "write1h": cc.get("ephemeral_1h_input_tokens"),
              "output": usage.get("output_tokens")}
    result = {k: v if finite_count(v) else None for k, v in result.items()}
    if writes == 0:
        result["write5m"] = result["write1h"] = 0
    elif finite_count(writes):
        known = sum(result[k] or 0 for k in ("write5m", "write1h"))
        if known == writes:
            result["write5m"] = result["write5m"] or 0
            result["write1h"] = result["write1h"] or 0
    return result


def valuation_scale(observed, session_totals, cost_usd):
    """Calibrate only with independently reported full-session category totals.

    A complete-pages flag is insufficient: streamed output can still be partial.
    The numerator is observed work and never expanded to fill a missing window.
    """
    if not finite_count(cost_usd) or not isinstance(session_totals, dict) or any(not finite_count(session_totals.get(k)) for k in W):
        return None
    if any(observed[k] > session_totals[k] for k in W):
        return None
    total = sum(W[k] * session_totals[k] for k in W)
    return cost_usd / total if total > 0 else None


def load(pages_dir):
    events, seen = [], set()
    for f in sorted(Path(pages_dir).glob("*")):
        s = f.read_text(errors="replace")
        i = s.find('{"ccr"')
        if i < 0:
            continue
        j = s.rfind("}")
        try:
            page = json.loads(s[i:j + 1])["ccr"]
        except json.JSONDecodeError:
            continue
        for e in page.get("data", []):
            kind = next((k for k in e if k != "created_at"), None)
            body = e.get(kind) or {}
            uid = body.get("uuid") or json.dumps(e, sort_keys=True)[:200]
            if uid in seen:
                continue
            seen.add(uid)
            events.append((e.get("created_at", ""), kind, body))
    events.sort(key=lambda x: x[0])
    return events


def tool_label(name, inp):
    """A short, groupable description of a tool call."""
    inp = inp or {}
    if name == "Bash":
        c = re.sub(r"^\s*cd [^&;]+(&&|;)\s*", "", inp.get("command", ""))
        c = re.sub(r"^(timeout \d+\s+)", "", c.strip())
        w = c.split()
        if not w:
            return "Bash"
        if "=" in w[0] or w[0] in ("export", "env"):
            # Never echo assignments: they can carry tokens or passwords.
            return "Bash (sets variables, then runs a script)"
        if w[0] == "git":
            return "Bash git " + (w[1] if len(w) > 1 else "")
        if w[0] in ("python", "python3"):
            m = re.search(r"([\w./-]+\.py)", c)
            return "Bash python " + (Path(m.group(1)).name if m else "-c/heredoc")
        return "Bash " + w[0]
    if name in ("Read", "Edit", "Write"):
        return name
    if name.startswith("mcp__"):
        parts = name.split("__")
        meth = inp.get("method") or ""
        return "MCP " + parts[1] + " " + parts[-1] + (" " + meth if meth else "")
    return name


def profile(events, cost_usd=None, label="", session_totals=None, pricing=None, cash_charge_usd=None, effort=None):
    if any(v is not None and not finite_count(v) for v in (cost_usd, cash_charge_usd)):
        raise ValueError("monetary totals must be finite and nonnegative; missing totals are null")
    calls = collections.OrderedDict()   # message id -> call record
    tool_meta = {}                       # tool_use_id -> (label, path)
    pending = collections.defaultdict(list)  # each agent retains its own pending context
    seen_content = set()
    for ts, kind, body in events:
        msg = (body.get("internal_anthropic_catchall") or {}).get("message") or body.get("message")
        if not isinstance(msg, dict):
            continue
        agent = (body.get("internal_anthropic_catchall") or {}).get("parent_tool_use_id") or "main"
        if kind == "assistant":
            mid = msg.get("id")
            u = msg.get("usage") or {}
            if mid not in calls:
                counts = usage_counts(u)
                calls[mid] = {"ts": ts, "agent": agent, **{k: v or 0 for k, v in counts.items()},
                              "observed": counts, "output_final": False, "cache_creation_total": None,
                              "tools": [], "trigger": list(pending[agent])}
                pending[agent] = []
            else:
                for k, value in usage_counts(u).items():
                    if value is not None:
                        calls[mid]["observed"][k] = max(calls[mid]["observed"].get(k) or 0, value)
                        calls[mid][k] = calls[mid]["observed"][k]
            calls[mid]["output_final"] |= bool(msg.get("stop_reason"))
            if finite_count(u.get("cache_creation_input_tokens")):
                calls[mid]["cache_creation_total"] = u["cache_creation_input_tokens"]
            for b in msg.get("content") or []:
                content_key = (mid, json.dumps(b, sort_keys=True))
                if content_key in seen_content:
                    continue
                seen_content.add(content_key)
                if b.get("type") == "tool_use":
                    lab = tool_label(b.get("name", ""), b.get("input"))
                    path = (b.get("input") or {}).get("file_path") or ""
                    tool_meta[b.get("id")] = (lab, path)
                    calls[mid]["tools"].append(lab)
                    # What the model writes (commands, scripts, file bodies) stays in
                    # context and is re-read like a tool result.
                    pending[agent].append({"label": "model wrote: " + lab, "path": "",
                                    "tokens": len(json.dumps(b.get("input") or {})) / 4, "agent": agent})
                elif b.get("type") == "text":
                    pending[agent].append({"label": "model wrote: reply or narration", "path": "",
                                    "tokens": len(b.get("text") or "") / 4, "agent": agent})
        elif kind == "user":
            for b in msg.get("content") or [] if isinstance(msg.get("content"), list) else []:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    size = len(json.dumps(c)) if not isinstance(c, str) else len(c)
                    lab, path = tool_meta.get(b.get("tool_use_id"), ("unknown tool", ""))
                    pending[agent].append({"label": lab, "path": path, "tokens": size / 4, "agent": agent})
            if isinstance(msg.get("content"), str):
                pending[agent].append({"label": "user or system message", "path": "", "tokens": len(msg["content"]) / 4, "agent": agent})

    def units(c):
        return sum(W[k] * c[k] for k in W)

    fresh = collections.Counter()      # label -> cost units (new tokens)
    carry = collections.Counter()      # label -> cost units (re-reads)
    reads_by_path = collections.Counter()
    by_agent = collections.Counter()
    live = collections.defaultdict(list)   # agent -> items in context
    last_read = collections.defaultdict(int)
    base_ctx = {}
    rebuilds, polls = [], collections.Counter()
    for mid, c in calls.items():
        a = c["agent"]
        # A sharp drop in cache reads means the context was compacted or a new
        # agent started: forget what was in it.
        if c["read"] < 0.5 * last_read[a]:
            live[a] = []
            base_ctx.pop(a, None)
        last_read[a] = c["read"]
        items = c["trigger"]
        live[a].extend(items)
        u = units(c)
        by_agent[a] += u
        new_u = u - W["read"] * c["read"]
        trig = items[0]["label"] if items else "model continuing"
        fresh[trig] += new_u
        # The agent's fixed setup (system prompt, tool definitions, rules) is
        # measured as the context of its first call; everything above that is
        # history, shared out in proportion to the estimated size of each item.
        ctx = c["read"] + c["write5m"] + c["write1h"] + c["input"]
        base_ctx.setdefault(a, ctx)
        base = min(base_ctx[a], c["read"])
        carry["fixed setup (system prompt, tools, rules)"] += W["read"] * base
        tot = sum(i["tokens"] for i in live[a])
        hist = c["read"] - base
        if tot:
            for it in live[a]:
                carry[it["label"]] += W["read"] * hist * it["tokens"] / tot
        elif hist > 0:
            carry["history before the transcript starts"] += W["read"] * hist
        for it in items:
            if it["path"]:
                reads_by_path[it["path"]] += 1
        if c["write1h"] + c["write5m"] > 100_000:
            rebuilds.append({"ts": c["ts"], "tokens_rewritten": c["write1h"] + c["write5m"],
                             "cost_units": W["write5m"] * c["write5m"] + W["write1h"] * c["write1h"]})
        if c["read"] > 300_000 and c["output"] < 400 and set(c["tools"]) & {
                "ReadNotifications", "MCP github pull_request_read get", "MCP github pull_request_read get_check_runs",
                "MCP github actions_list list_workflow_runs", "MCP claude-code-remote get_session", "TaskOutput"}:
            polls["status check in a large context"] += u
    total = sum(units(c) for c in calls.values())
    observed = {k: sum(c[k] for c in calls.values()) for k in W}
    missing = {k: sum(c["observed"][k] is None for c in calls.values()) for k in W}
    unclassified_writes = sum(max(0, (c["cache_creation_total"] or 0) - c["write5m"] - c["write1h"]) for c in calls.values())
    scale = valuation_scale(observed, session_totals, cost_usd)
    cost = lambda x: round(x * scale, 6) if scale is not None else round(x, 6)
    coverage = {k: {"observed_tokens": observed[k], "calls_missing_field": missing[k],
                   "session_total": (session_totals or {}).get(k),
                   "fraction": observed[k] / session_totals[k] if finite_count((session_totals or {}).get(k)) and session_totals[k] > 0 else None}
                for k in W}
    coverage["output"]["complete_final_usage_observed"] = bool(calls) and all(c["output_final"] and c["observed"]["output"] is not None for c in calls.values())
    rates = (pricing or {}).get("usd_per_million_tokens") or {}
    priced_observed = None
    if pricing and pricing.get("source") and pricing.get("as_of") and all(finite_count(rates.get(k)) for k in W):
        priced_observed = sum(observed[k] * rates[k] / 1_000_000 for k in W)
    combined = collections.Counter()
    for k, v in fresh.items():
        combined[k] += v
    for k, v in carry.items():
        combined[k] += v
    return {
        "schema": "hamilton.profile/2",
        "label": label, "model_calls": len(calls), "cost_units": round(total),
        "usd_per_unit": scale, "unit": "estimated API token value USD for observed window" if scale is not None else "input-token equivalents",
        "tokens": observed, "coverage": coverage,
        "cache_write_unclassified_tokens": unclassified_writes,
        "unpriced_or_unclassified_usage": bool(unclassified_writes or any(missing.values()) or not coverage["output"]["complete_final_usage_observed"]),
        "session_tokens": {k: (session_totals or {}).get(k) for k in W},
        "session_token_value_usd": cost_usd, "cash_charge_usd": cash_charge_usd,
        "observed_window_token_value_usd": total * scale if scale is not None else None,
        "priced_observed_tokens_usd": priced_observed,
        "pricing": pricing or {"basis": "relative price assumptions retained from the original Hamilton audit", "weights": W,
                               "absolute_rates": None, "model": None, "as_of": None},
        "valuation_note": "Session token value is separate from cash charges. Unknown or partial capture is never scaled to the full session. Output may be a streaming lower bound.",
        "attribution": {"method": "characters/4 context-size estimate and first-call setup proxy",
                        "scope": "observed usage only", "causal_identification": False,
                        "diagnostic_views_overlap": ["cache_rebuilds", "status_checks_in_large_context", "subagents"],
                        "add_diagnostic_views_to_cause_total": False},
        "effort_accounting": {"phases": {phase: (effort or {}).get(phase) for phase in PHASES},
                              "missing_phases": [phase for phase in PHASES if (effort or {}).get(phase) is None],
                              "note": "Phase values annotate session totals; do not add them again. Complete campaign cost requires build, coordination, monitoring, review, rework and integration."},
        "cost_by_cause": [{"cause": k, "cost": cost(v), "share": round(v / total, 4) if total else None,
                           "fresh": cost(fresh.get(k, 0)), "reread": cost(carry.get(k, 0))}
                          for k, v in combined.most_common(25)],
        "cache_rebuilds": {"count": len(rebuilds), "cost": cost(sum(r["cost_units"] for r in rebuilds)),
                           "examples": rebuilds[:5]},
        "status_checks_in_large_context": {k: cost(v) for k, v in polls.items()},
        "subagents": {"count": len(by_agent) - ("main" in by_agent),
                      "cost": cost(sum(v for k, v in by_agent.items() if k != "main"))},
        "files_read_more_than_twice": [{"path": p, "reads": n} for p, n in reads_by_path.most_common(15) if n > 2],
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pages")
    ap.add_argument("--cost-usd", type=float)
    ap.add_argument("--session-totals", help="aggregate JSON with full-session input/read/write5m/write1h/output token totals")
    ap.add_argument("--pricing", help="JSON with source, as_of and usd_per_million_tokens by category")
    ap.add_argument("--cash-charge-usd", type=float, help="actual invoice charge if observed; omitted stays unknown")
    ap.add_argument("--effort", help="aggregate JSON annotating phase costs already included in session totals")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ev = load(a.pages)
    read_json = lambda p: json.loads(Path(p).read_text()) if p else None
    res = profile(ev, a.cost_usd, a.label, read_json(a.session_totals), read_json(a.pricing), a.cash_charge_usd, read_json(a.effort))
    res["events"] = len(ev)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / f"PROFILE_{a.label or 'session'}.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("label", "events", "model_calls", "cost_units", "unit")}, indent=1))
    for r in res["cost_by_cause"][:12]:
        print(f"{(r['share'] or 0)*100:5.1f}%  {r['cost']:>10}  {r['cause']}")
