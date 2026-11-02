"""Extract per-agent token and time telemetry from subagent transcripts (deterministic; no judgment).

usage:
  python3 -I jobs/geddes/telemetry.py TASKS_DIR OUT_PREFIX --roster ROSTER.csv
  python3 -I jobs/geddes/telemetry.py TASKS_DIR OUT_PREFIX --apollo-log COORDINATOR_LOG.txt

The roster is a CSV with the columns agent_id,batch,role,track. Each agent's transcript is
TASKS_DIR/<agent_id>.output. The Apollo fallback reads agents and roles from coordinator log lines of
the form "producer B ID ..." and "B reviewer ID ..." (as in
research/excavator/claude-apollo-2026-10-31/tools/moon_telemetry.py, which this module replaces); the
track is then taken from the batch prefix (n = NRA, g = General).

Usage is summed once per API message id. active_seconds sums the gaps between consecutive transcript
events and drops any gap longer than --max-gap-seconds (default 600, the length of the 2026-10-31
usage-limit pause). Tool calls are counted by tool name. tokens_total_input is input_tokens plus
cache_creation_input_tokens plus cache_read_input_tokens. Writes OUT_PREFIX.csv and OUT_PREFIX.json.
"""
import argparse
import collections
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

TOKEN_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
# The first 15 columns match the Apollo TELEMETRY.csv; the last two are new.
COLUMNS = ["batch", "role", "agent", "model", "api_messages", *TOKEN_KEYS, "tool_calls", "bash_calls",
           "read_calls", "active_seconds", "first_utc", "last_utc", "tokens_total_input", "track"]
ROSTER_COLUMNS = ("agent_id", "batch", "role", "track")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def track_from_batch(batch):
    b = (batch or "").lower()
    return "NRA" if b.startswith("n") else "General" if b.startswith("g") else "unknown"


def read_roster(path):
    """Return [(agent_id, batch, role, track)] from a roster CSV; reject missing columns or duplicate ids."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in ROSTER_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: roster lacks columns {missing}; expected {list(ROSTER_COLUMNS)}")
        agents, seen = [], set()
        for n, row in enumerate(reader, 2):
            if not any((v or "").strip() for v in row.values()):
                continue
            aid = (row["agent_id"] or "").strip()
            if not aid:
                raise ValueError(f"{path}:{n}: empty agent_id")
            if aid in seen:
                raise ValueError(f"{path}:{n}: duplicate agent_id {aid}")
            seen.add(aid)
            batch = (row["batch"] or "").strip()
            agents.append((aid, batch, (row["role"] or "").strip(), (row["track"] or "").strip() or track_from_batch(batch)))
    return agents


def read_apollo_log(path):
    """Return [(agent_id, batch, role, track)] from the Apollo coordinator log format."""
    agents = {}
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        m = re.match(r"producer (\S+) (a[0-9a-f]{16})", line) or re.match(r"(\S+) reviewer (a[0-9a-f]{16})", line)
        if m:
            agents[m.group(2)] = (m.group(1), "producer" if line.startswith("producer") else "reviewer")
    return [(aid, batch, role, track_from_batch(batch))
            for aid, (batch, role) in sorted(agents.items(), key=lambda x: (x[1][1], x[1][0]))]


def read_transcript(path, max_gap=600):
    """Summarize one transcript file. Messages are deduplicated by API message id, as in Apollo."""
    seen, tok, tools, times, models = set(), collections.Counter(), collections.Counter(), [], collections.Counter()
    with open(path, encoding="utf-8") as f:
        raw_lines = f.read().splitlines()
    for l in raw_lines:
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if not isinstance(r, dict):
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
                for k in TOKEN_KEYS:
                    tok[k] += u.get(k) or 0
    times.sort()
    active = sum((b - a).total_seconds() for a, b in zip(times, times[1:]) if (b - a).total_seconds() <= max_gap)
    return {"model": models.most_common(1)[0][0] if models else "", "api_messages": len(seen),
            **{k: tok[k] for k in TOKEN_KEYS}, "tool_calls": sum(tools.values()),
            "bash_calls": tools.get("Bash", 0), "read_calls": tools.get("Read", 0),
            "active_seconds": round(active), "first_utc": times[0].isoformat() if times else "",
            "last_utc": times[-1].isoformat() if times else "",
            "tokens_total_input": tok["input_tokens"] + tok["cache_creation_input_tokens"] + tok["cache_read_input_tokens"]}


def extract(tasks, agents, max_gap=600):
    """Return (rows, missing_agent_ids). Agents without a transcript are listed, never zero-filled."""
    rows, missing = [], []
    for aid, batch, role, track in agents:
        p = Path(tasks) / f"{aid}.output"
        if not p.exists():
            missing.append(aid)
            continue
        rows.append({"batch": batch, "role": role, "agent": aid, "track": track, **read_transcript(p, max_gap)})
    return rows, missing


def write_outputs(rows, missing, out):
    with open(out + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    tot = collections.defaultdict(collections.Counter)
    for r in rows:
        for k in (*TOKEN_KEYS, "tokens_total_input", "tool_calls", "active_seconds", "api_messages"):
            tot[r["role"]][k] += r[k]
        tot[r["role"]]["agents"] += 1
    Path(out + ".json").write_text(json.dumps({"schema": "eo-swarm-telemetry/v1", "by_role": tot, "rows": len(rows),
                                               "agents_without_transcript": missing}, indent=1) + "\n", encoding="utf-8")
    return tot


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tasks", type=Path, help="directory holding <agent_id>.output transcripts")
    p.add_argument("out", help="output path prefix; writes OUT.csv and OUT.json")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--roster", type=Path, help="CSV with columns agent_id,batch,role,track")
    g.add_argument("--apollo-log", type=Path, help="Apollo coordinator log (fallback format)")
    p.add_argument("--max-gap-seconds", type=float, default=600)
    a = p.parse_args(argv)
    try:
        agents = read_roster(a.roster) if a.roster else read_apollo_log(a.apollo_log)
        rows, missing = extract(a.tasks, agents, a.max_gap_seconds)
        tot = write_outputs(rows, missing, a.out)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2
    print(json.dumps({"by_role": tot, "agents_without_transcript": missing}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
