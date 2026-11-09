#!/usr/bin/env python3
"""Carnot worker: run one bounded task in a fresh headless Claude Code session and log its cost.

    python3 -I jobs/carnot-coordinator/worker.py LABEL MODEL PROMPT_FILE --log RUN/COSTS.log --out RUN/ [--resume SID]

Writes RUN/LABEL.json (the `claude -p --output-format json` result) and appends to COSTS.log:

    LABEL launched UTC
    LABEL SESSION-ID cost USD turns N ms N
    LABEL done UTC            (or: LABEL failed UTC reason)

That cost line is what `bentham.py usage --reported-costs COSTS.log` reads: it cross-checks the session's computed
list price against it and labels the session `worker`. The coordinator reads only RUN/LABEL.json's `result`.
Exit code: the worker's own, or 1 when the result has no session id or reports an error.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run(label, model, prompt_file, log, out, resume=None, claude="claude", runner=subprocess.run):
    if not LABEL.match(label):
        raise SystemExit("label must be letters, digits, '.', '_' or '-'")
    out, log = Path(out), Path(log)
    out.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    cmd = [claude, "-p", "--model", model, "--output-format", "json"] + (["--resume", resume] if resume else []) + [prompt]
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"{label} {'resume ' + resume + ' ' if resume else ''}{model} launched {now()}\n")
    p = runner(cmd, capture_output=True, text=True)
    (out / f"{label}.json").write_text(p.stdout or "", encoding="utf-8")
    (out / f"{label}.err").write_text(p.stderr or "", encoding="utf-8")
    try:
        d = json.loads(p.stdout or "")
    except ValueError:
        d = {}
    sid, cost = d.get("session_id"), d.get("total_cost_usd")
    with log.open("a", encoding="utf-8") as fh:
        if isinstance(sid, str) and isinstance(cost, (int, float)):
            fh.write(f"{label} {sid} cost {cost} turns {d.get('num_turns')} ms {d.get('duration_ms')}\n")
        if p.returncode or not sid or d.get("is_error"):
            fh.write(f"{label} failed {now()} exit {p.returncode} error {bool(d.get('is_error'))}\n")
            return p.returncode or 1
        fh.write(f"{label} done {now()}\n")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("label")
    ap.add_argument("model")
    ap.add_argument("prompt_file")
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--resume")
    a = ap.parse_args(argv)
    if not shutil.which("claude"):
        raise SystemExit("claude CLI not found")
    return run(a.label, a.model, a.prompt_file, a.log, a.out, a.resume)


if __name__ == "__main__":
    sys.exit(main())
