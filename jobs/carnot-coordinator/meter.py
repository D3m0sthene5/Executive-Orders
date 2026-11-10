"""Meter: measured agent spend per lane and per verified filed claim, from the agents' own token logs.

Self-reported counts and turn lengths are not enough. On 2026-11-09/10 five Codex lanes reported "producing"
for hours. 910M input tokens (97% cache re-reads) went mostly to coordinators re-sending contexts of up to 447k
tokens on every call, and to 150 auto-review sessions. 12 claims were filed. This module reads what was actually
spent (Codex rollout files) and what was actually filed (the lane's claim files), so a supervisor can stop a lane
on measurements an agent cannot talk around.

Usage units weigh the three token kinds the way API price lists do. A cached input token costs a tenth of an
uncached one, and an output token four times as much:
    units = 0.1 x cached_input + 1 x uncached_input + 4 x output
The weights are an explicit approximation. A plan's real usage meter is not published.

  python -I jobs/carnot-coordinator/meter.py --since 2026-11-10T05:00Z --lane mommsen-1=C:/path/worktree ...
"""

import argparse
import collections
import datetime
import glob
import json
import os
import re
from pathlib import Path

W_CACHED, W_INPUT, W_OUTPUT = 0.1, 1.0, 4.0
REVIEW_MODELS = ("codex-auto-review",)


def units(cached, uncached, output):
    return W_CACHED * cached + W_INPUT * uncached + W_OUTPUT * output


def parse_time(text):
    return datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))


def read_rollout(path):
    """One Codex rollout: cwd mentions, model, call count, final token totals, largest single-call context."""
    s = {"path": str(path), "model": None, "calls": 0, "input": 0, "cached": 0, "output": 0, "max_context": 0,
         "last_context": 0,
         "started": None, "mentions": collections.Counter(), "cwds": []}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if s["started"] is None and '"timestamp"' in line:
                m = re.search(r'"timestamp"\s*:\s*"([^"]+)"', line)
                if m:
                    s["started"] = m.group(1)
            if '"token_count"' in line:
                try:
                    info = json.loads(line)["payload"]["info"]
                except (ValueError, KeyError, TypeError):
                    info = None
                if info:
                    t = info["total_token_usage"]
                    s["calls"] += 1
                    s["input"], s["cached"], s["output"] = t["input_tokens"], t["cached_input_tokens"], t["output_tokens"]
                    s["last_context"] = info["last_token_usage"]["input_tokens"]
                    s["max_context"] = max(s["max_context"], s["last_context"])
                continue
            if s["model"] is None and '"model"' in line:
                m = re.search(r'"model"\s*:\s*"([^"]+)"', line)
                s["model"] = m.group(1) if m else None
            for m in re.finditer(r'"cwd"\s*:\s*"([^"]+)"', line):
                s["cwds"].append(m.group(1))
            for m in re.finditer(r"eo-wt(?:\\\\|\\|/)+([A-Za-z0-9_-]+)", line):
                s["mentions"][m.group(1).lower()] += 1
    return s


def attribute(session, lanes):
    """The lane a session belongs to: its working directory if that is a lane, else the lane it names most."""
    for cwd in reversed(session["cwds"]):
        low = cwd.replace("\\\\", "\\").lower()
        for lane in lanes:
            if re.search(r"eo-wt[\\/]+" + re.escape(lane) + r"(?![A-Za-z0-9_-])", low):
                return lane
    named = [(n, lane) for lane in lanes for n in [session["mentions"].get(lane, 0)] if n]
    return max(named)[1] if named else None


def sessions(since, home=None):
    home = Path(home or os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    cutoff = parse_time(since)
    out = []
    for path in glob.glob(str(home / "sessions" / "*" / "*" / "*" / "rollout-*.jsonl")):
        if datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc) < cutoff:
            continue
        s = read_rollout(path)
        if s["calls"] and s["started"] and parse_time(s["started"]) >= cutoff:
            out.append(s)
    return out


def filed_claims(worktree, lane):
    """Distinct orders in the lane's own claim files (both the amended and the old name form): what it filed."""
    n = lane.split("-")[-1]
    ids = set()
    folder = Path(worktree) / "research/readiness/claims"
    for pattern in (f"{lane}-*.jsonl", f"mommsen{n}-*.jsonl"):
        for path in folder.glob(pattern):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    iid = json.loads(line).get("instrument_id") if line.strip() else None
                except ValueError:
                    iid = None
                if iid:
                    ids.add(iid)
    return ids


def lane_report(lanes, since, home=None, worktrees=None, now=None):
    """{lane: {units, calls, max_context, sessions, reviews, reviews_last_hour, filed}} from measurements only."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    report = {lane: {"units": 0.0, "calls": 0, "max_context": 0, "sessions": 0, "reviews": 0,
                     "reviews_last_hour": 0, "filed": None} for lane in lanes}
    for s in sessions(since, home):
        lane = attribute(s, lanes)
        if lane is None:
            continue
        r = report[lane]
        r["units"] += units(s["cached"], s["input"] - s["cached"], s["output"])
        r["calls"] += s["calls"]
        r["sessions"] += 1
        if s["model"] in REVIEW_MODELS:
            r["reviews"] += 1
            if now - parse_time(s["started"]) <= datetime.timedelta(hours=1):
                r["reviews_last_hour"] += 1
        else:
            r["max_context"] = max(r["max_context"], s["max_context"])
    for lane, tree in (worktrees or {}).items():
        if lane in report and tree:
            report[lane]["filed"] = len(filed_claims(tree, lane))
    for r in report.values():
        r["units"] = round(r["units"])
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", required=True, help="ISO time; sessions started earlier are ignored")
    ap.add_argument("--lane", action="append", default=[], help="NAME or NAME=WORKTREE (repeatable)")
    ap.add_argument("--codex-home")
    a = ap.parse_args(argv)
    lanes, trees = [], {}
    for item in a.lane:
        name, _, tree = item.partition("=")
        lanes.append(name)
        trees[name] = tree or None
    print(json.dumps(lane_report(lanes, a.since, a.codex_home, trees), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
