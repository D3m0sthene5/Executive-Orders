#!/usr/bin/env python3
"""Carnot handoff: the packet a fresh session needs at a phase boundary, and a per-call context check.

    python3 -I jobs/carnot-coordinator/handoff.py context [--session-id ID] [--threshold N]
    python3 -I jobs/carnot-coordinator/handoff.py write --phase NAME --next TEXT [--note TEXT ...] [--run ID ...]
                                                        [--require-clean] [--out DIR]

`context` reads only the usage numbers of this session's newest model call (Claude Code's transcript under
$CLAUDE_CONFIG_DIR or ~/.claude/projects) and prints the tokens that call carried (fresh input + cache read + cache
write). Above the threshold (default 300,000, the line Rumford measures `revere_phase_handoff` against) it says to
hand off. Exit code 0 under the threshold, 5 above it, 6 when unknown.

`write` builds HANDOFF/packets/<UTC date>-<phase>.md from git and the arguments only, never from transcript text:
branch, HEAD, upstream state, modified and untracked files, the last commits, runs to watch, the newest entry of
HANDOFF/notes-claude.md (its heading), the context check, and what to do next. A fresh session reads it, checks
that HEAD matches, and continues. See PROTOCOL.md section 3.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

THRESHOLD = 300_000
REPO = Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[2])
SLUG = re.compile(r"[^A-Za-z0-9._-]+")


def config_dirs():
    dirs = [Path(os.environ["CLAUDE_CONFIG_DIR"])] if os.environ.get("CLAUDE_CONFIG_DIR") else []
    return dirs + [Path.home() / ".claude"]


def newest_transcript(session_id=None):
    best = None
    for cfg in config_dirs():
        for f in (cfg / "projects").glob("*/*.jsonl"):
            if session_id and not f.stem.startswith(session_id):
                continue
            if f.stem.startswith("agent-"):
                continue
            m = f.stat().st_mtime
            if best is None or m > best[0]:
                best = (m, f)
    return best[1] if best else None


def last_call_context(path):
    """(tokens carried by the newest call with usage, model) or (None, None). Reads usage numbers only."""
    last = None
    with path.open(errors="replace") as fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue  # a live transcript's half-written last line
            msg = r.get("message") if isinstance(r, dict) else None
            u = msg.get("usage") if isinstance(msg, dict) else None
            if r.get("type") == "assistant" and isinstance(u, dict) and msg.get("model") != "<synthetic>":
                last = (u, msg.get("model"))
    if not last:
        return None, None
    u, model = last
    n = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return n, model


def context(session_id=None, threshold=THRESHOLD):
    path = newest_transcript(session_id)
    if path is None:
        return 6, {"tokens_per_call": None, "verdict": "unknown", "why": "no transcript found"}
    n, model = last_call_context(path)
    if n is None:
        return 6, {"tokens_per_call": None, "verdict": "unknown", "why": "no model call with usage yet"}
    over = n > threshold
    return (5 if over else 0), {"tokens_per_call": n, "model": model, "threshold": threshold,
                                "session": path.stem[:8], "verdict": "hand_off" if over else "ok",
                                "advice": ("Over the threshold: finish the current step, write a packet "
                                           "(handoff.py write) and continue in a fresh session.") if over else ""}


def git(*args):
    p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def newest_notes_heading(path=REPO / "HANDOFF/notes-claude.md"):
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                return line[3:].strip()
    except OSError:
        pass
    return "(no notes entry found)"


def packet(phase, next_step, notes=(), runs=(), session_id=None, threshold=THRESHOLD):
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    dirty = [ln for ln in status.splitlines() if ln.strip()]
    code, ctx = context(session_id, threshold)
    when = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines = [f"# Handoff packet: {phase}", "",
             f"Written {when} by `jobs/carnot-coordinator/handoff.py`. Built from git and its arguments only.", "",
             "## Where things stand", "",
             f"- Branch `{git('rev-parse', '--abbrev-ref', 'HEAD')}`, HEAD `{git('rev-parse', 'HEAD')}`. "
             "Check `git rev-parse HEAD` matches before continuing; if not, read the commits since.",
             f"- Upstream: {git('status', '-sb').splitlines()[0] if git('status', '-sb') else 'unknown'}",
             f"- Uncommitted files ({len(dirty)}): " + (", ".join(f"`{d[3:]}` ({d[:2].strip()})" for d in dirty[:40])
                                                         + (" ..." if len(dirty) > 40 else "") if dirty else "none"),
             f"- Newest notes entry: {newest_notes_heading()}",
             f"- Context of the handing-off session: {ctx.get('tokens_per_call') or 'unknown'} tokens per call "
             f"({ctx['verdict']}).", "", "## Recent commits", ""]
    lines += [f"- {c}" for c in git("log", "--oneline", "-8").splitlines()]
    if runs:
        lines += ["", "## Runs to watch", ""] + [
            f"- {r}: `python3 -I jobs/carnot-coordinator/await_run.py --run {r}` in the background, then end the turn"
            for r in runs]
    if notes:
        lines += ["", "## Notes from the coordinator", ""] + [f"- {n}" for n in notes]
    lines += ["", "## Next", "", next_step, ""]
    return "\n".join(lines), dirty, ctx


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("context")
    c.add_argument("--session-id")
    c.add_argument("--threshold", type=int, default=THRESHOLD)
    w = sub.add_parser("write")
    w.add_argument("--phase", required=True)
    w.add_argument("--next", required=True)
    w.add_argument("--note", action="append", default=[])
    w.add_argument("--run", action="append", default=[])
    w.add_argument("--session-id")
    w.add_argument("--threshold", type=int, default=THRESHOLD)
    w.add_argument("--require-clean", action="store_true")
    w.add_argument("--out", default=str(REPO / "HANDOFF/packets"))
    a = ap.parse_args(argv)
    if a.cmd == "context":
        code, ctx = context(a.session_id, a.threshold)
        print(json.dumps(ctx))
        return code
    text, dirty, ctx = packet(a.phase, a.next, a.note, a.run, a.session_id, a.threshold)
    if a.require_clean and dirty:
        print(f"refusing: {len(dirty)} uncommitted file(s); commit them or drop --require-clean", file=sys.stderr)
        return 7
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{time.strftime('%Y-%m-%d', time.gmtime())}-{SLUG.sub('-', a.phase).strip('-')[:60] or 'phase'}.md"
    path.write_text(text, encoding="utf-8")
    print(json.dumps({"wrote": str(path), "uncommitted": len(dirty), "context": ctx}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
