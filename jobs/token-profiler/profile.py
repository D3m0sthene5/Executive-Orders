"""Where do an agent session's tokens go?

Reads transcript pages saved from the claude-code-remote `list_events` tool
(one JSON page per file, `{"ccr": {"data": [...]}}`), rebuilds every model call
with its usage, and attributes cost to what caused it:

- fresh cost of a call (new input, cache writes, output) goes to the step that
  triggered it: the tool whose result the model was reading, or a user turn;
- re-read cost (cache reads) goes to every item still in context, in
  proportion to its size, so a large tool result pays for every later call
  that re-reads it until the context is compacted.

Cost units use the API's relative prices (input 1, cache read 0.1, 5-minute
cache write 1.25, 1-hour cache write 2, output 5) and are scaled to dollars
with the session's own reported cost when it is given. Sizes of tool results
are characters / 4, an estimate.

usage: python profile.py PAGES_DIR [--cost-usd N] [--label NAME] --out OUT_DIR
"""
import argparse, collections, json, re
from pathlib import Path

W = {"input": 1.0, "read": 0.1, "write5m": 1.25, "write1h": 2.0, "output": 5.0}


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


def profile(events, cost_usd=None, label=""):
    calls = collections.OrderedDict()   # message id -> call record
    tool_meta = {}                       # tool_use_id -> (label, path)
    pending = []                         # items added since the last call
    for ts, kind, body in events:
        msg = (body.get("internal_anthropic_catchall") or {}).get("message") or body.get("message")
        if not isinstance(msg, dict):
            continue
        agent = (body.get("internal_anthropic_catchall") or {}).get("parent_tool_use_id") or "main"
        if kind == "assistant":
            mid = msg.get("id")
            u = msg.get("usage") or {}
            if mid not in calls:
                cc = u.get("cache_creation") or {}
                w1h = cc.get("ephemeral_1h_input_tokens", 0)
                w5m = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) - w1h)
                calls[mid] = {"ts": ts, "agent": agent, "read": u.get("cache_read_input_tokens", 0),
                              "write5m": max(w5m, 0), "write1h": w1h, "input": u.get("input_tokens", 0),
                              "output": u.get("output_tokens", 0), "tools": [], "trigger": list(pending)}
                pending = []
            for b in msg.get("content") or []:
                if b.get("type") == "tool_use":
                    lab = tool_label(b.get("name", ""), b.get("input"))
                    path = (b.get("input") or {}).get("file_path") or ""
                    tool_meta[b.get("id")] = (lab, path)
                    calls[mid]["tools"].append(lab)
        elif kind == "user":
            for b in msg.get("content") or [] if isinstance(msg.get("content"), list) else []:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    size = len(json.dumps(c)) if not isinstance(c, str) else len(c)
                    lab, path = tool_meta.get(b.get("tool_use_id"), ("unknown tool", ""))
                    pending.append({"label": lab, "path": path, "tokens": size / 4, "agent": agent})
            if isinstance(msg.get("content"), str):
                pending.append({"label": "user or system message", "path": "", "tokens": len(msg["content"]) / 4, "agent": agent})

    def units(c):
        return sum(W[k] * c[k] for k in W)

    fresh = collections.Counter()      # label -> cost units (new tokens)
    carry = collections.Counter()      # label -> cost units (re-reads)
    reads_by_path = collections.Counter()
    by_agent = collections.Counter()
    live = collections.defaultdict(list)   # agent -> items in context
    last_read = collections.defaultdict(int)
    rebuilds, polls = [], collections.Counter()
    for mid, c in calls.items():
        a = c["agent"]
        # A sharp drop in cache reads means the context was compacted or a new
        # agent started: forget what was in it.
        if c["read"] < 0.5 * last_read[a]:
            live[a] = []
        last_read[a] = c["read"]
        items = c["trigger"]
        live[a].extend(items)
        u = units(c)
        by_agent[a] += u
        new_u = u - W["read"] * c["read"]
        trig = items[0]["label"] if items else "model continuing"
        fresh[trig] += new_u
        tot = sum(i["tokens"] for i in live[a]) or 1
        base_share = max(c["read"] - tot, 0) / max(c["read"], 1)
        carry["system prompt and instructions"] += W["read"] * c["read"] * base_share
        for it in live[a]:
            carry[it["label"]] += W["read"] * c["read"] * (1 - base_share) * it["tokens"] / tot
        for it in items:
            if it["path"]:
                reads_by_path[it["path"]] += 1
        if c["write1h"] + c["write5m"] > 100_000:
            rebuilds.append({"ts": c["ts"], "tokens_rewritten": c["write1h"] + c["write5m"]})
        if c["read"] > 300_000 and c["output"] < 400 and set(c["tools"]) & {
                "ReadNotifications", "MCP github pull_request_read get", "MCP github pull_request_read get_check_runs",
                "MCP github actions_list list_workflow_runs", "MCP claude-code-remote get_session", "TaskOutput"}:
            polls["status check in a large context"] += u
    total = sum(units(c) for c in calls.values())
    scale = (cost_usd / total) if cost_usd and total else None
    cost = lambda x: round(x * scale, 2) if scale else round(x)
    combined = collections.Counter()
    for k, v in fresh.items():
        combined[k] += v
    for k, v in carry.items():
        combined[k] += v
    return {
        "label": label, "model_calls": len(calls), "cost_units": round(total),
        "usd_per_unit": scale, "unit": "USD" if scale else "input-token equivalents",
        "tokens": {k: sum(c[k] for c in calls.values()) for k in ("input", "read", "write5m", "write1h", "output")},
        "cost_by_cause": [{"cause": k, "cost": cost(v), "share": round(v / total, 4),
                           "fresh": cost(fresh.get(k, 0)), "reread": cost(carry.get(k, 0))}
                          for k, v in combined.most_common(25)],
        "cache_rebuilds": {"count": len(rebuilds), "cost": cost(sum(W["write1h"] * r["tokens_rewritten"] for r in rebuilds)),
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
    ap.add_argument("--label", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ev = load(a.pages)
    res = profile(ev, a.cost_usd, a.label)
    res["events"] = len(ev)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / f"PROFILE_{a.label or 'session'}.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("label", "events", "model_calls", "cost_units", "unit")}, indent=1))
    for r in res["cost_by_cause"][:12]:
        print(f"{r['share']*100:5.1f}%  {r['cost']:>10}  {r['cause']}")
