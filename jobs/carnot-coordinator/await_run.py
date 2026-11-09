#!/usr/bin/env python3
"""Carnot await_run: wait on one GitHub Actions run, print one line at its end, exit. Run it in the background and
end your turn; the session is re-invoked when it exits. See PROTOCOL.md section 2.

Exit codes: 0 completed (any conclusion; the line says which), 2 not_found, 3 timeout, 4 error.
Every terminal state prints a line, so silence never means success.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com/repos/{repo}/actions/runs/{run}"
MIN_INTERVAL = 60


def fetch(repo, run, token=None, opener=urllib.request.urlopen):
    req = urllib.request.Request(API.format(repo=repo, run=run), headers={
        "Accept": "application/vnd.github+json", "User-Agent": "carnot-await-run",
        **({"Authorization": "Bearer " + token} if token else {})})
    with opener(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def wait(repo, run, interval=300, max_hours=6.0, token=None, fetch_fn=fetch, sleep=time.sleep, clock=time.monotonic):
    """Return (code, line)."""
    interval = max(MIN_INTERVAL, int(interval))
    deadline = clock() + max_hours * 3600
    errors, delay = 0, interval
    while True:
        try:
            d = fetch_fn(repo, run, token)
            errors, delay = 0, interval
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 2, f"run {run}: not_found in {repo}"
            if e.code in (403, 429):  # rate limited: back off, never hammer
                delay = min(delay * 2, 3600)
            errors += 1
            d = None
            reason = f"HTTP {e.code}"
        except (urllib.error.URLError, OSError, ValueError) as e:
            errors += 1
            d = None
            reason = type(e).__name__
        if d is not None:
            status, conclusion = d.get("status"), d.get("conclusion")
            if status == "completed":
                return 0, (f"run {run} attempt {d.get('run_attempt')}: completed {conclusion} "
                           f"({d.get('name')}, {d.get('head_branch')}, {d.get('html_url')})")
        elif errors >= 10:
            return 4, f"run {run}: error after 10 failed checks in a row ({reason})"
        if clock() + delay > deadline:
            last = f"{d.get('status')}" if d else "unknown"
            return 3, f"run {run}: timeout after {max_hours} h (last status {last}); re-arm or check by hand"
        sleep(delay)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, type=int)
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "D3m0sthene5/Executive-Orders"))
    ap.add_argument("--interval", type=int, default=300, help=f"seconds between checks (minimum {MIN_INTERVAL})")
    ap.add_argument("--max-hours", type=float, default=6.0)
    a = ap.parse_args(argv)
    code, line = wait(a.repo, a.run, a.interval, a.max_hours, os.environ.get("GITHUB_TOKEN") or None)
    print(line, flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
