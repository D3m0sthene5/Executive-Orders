"""Extract per-agent token and time telemetry from subagent transcripts (deterministic; no judgment).

usage: python3 -I moon_telemetry.py TASKS_DIR COORDINATOR_LOG OUT_PREFIX
  Agents and their roles come from COORDINATOR_LOG lines "producer B ID ..." and "B reviewer ID ...".
  Usage is summed once per API message id. active_seconds sums gaps between consecutive transcript events,
  dropping gaps over 10 minutes (the 2026-10-31 usage-limit pause). Tool calls are counted by tool name.
"""
import collections, csv, json, re, sys
from datetime import datetime
from pathlib import Path

def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def main(tasks, log, out):
    agents = {}
    for line in open(log):
        m = re.match(r"producer (\S+) (a[0-9a-f]{16})", line) or re.match(r"(\S+) reviewer (a[0-9a-f]{16})", line)
        if m:
            agents[m.group(2)] = (m.group(1), "producer" if line.startswith("producer") else "reviewer")
    rows = []
    for aid, (batch, role) in sorted(agents.items(), key=lambda x: (x[1][1], x[1][0])):
        p = Path(tasks) / f"{aid}.output"
        if not p.exists():
            continue
        seen, tok, tools, times, models = set(), collections.Counter(), collections.Counter(), [], collections.Counter()
        for l in open(p, encoding="utf-8"):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("timestamp"):
                times.append(ts(r["timestamp"]))
            msg = r.get("message") or {}
            if r.get("type") == "assistant":
                for c in msg.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        tools[c.get("name")] += 1
                mid = msg.get("id")
                u = msg.get("usage")
                if u and mid not in seen:
                    seen.add(mid)
                    models[msg.get("model")] += 1
                    for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
                        tok[k] += u.get(k) or 0
        times.sort()
        active = sum(min((b - a).total_seconds(), 0) if False else (b - a).total_seconds()
                     for a, b in zip(times, times[1:]) if (b - a).total_seconds() <= 600)
        rows.append({"batch": batch, "role": role, "agent": aid, "model": models.most_common(1)[0][0] if models else "",
                     "api_messages": len(seen), **tok, "tool_calls": sum(tools.values()),
                     "bash_calls": tools.get("Bash", 0), "read_calls": tools.get("Read", 0),
                     "active_seconds": round(active), "first_utc": times[0].isoformat() if times else "",
                     "last_utc": times[-1].isoformat() if times else ""})
    with open(out + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    tot = collections.defaultdict(collections.Counter)
    for r in rows:
        for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
                  "tool_calls", "active_seconds", "api_messages"):
            tot[r["role"]][k] += r[k]
        tot[r["role"]]["agents"] += 1
    Path(out + ".json").write_text(json.dumps({"schema": "eo-swarm-telemetry/v1", "by_role": tot, "rows": len(rows)},
                                              indent=1) + "\n")
    print(json.dumps(tot, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:])
