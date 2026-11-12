"""The shared runner's hard limit, and when a long job must stop starting new work.

Lesson (Kean F-20261112-runner-deadline): on 2026-11-11 a one-shot web pass over 2,251 orders ran into the
workflow's 350-minute limit after 5 h 50 min and published nothing, because it never measured its per-item cost
(about 30 s an order) and had no deadline. Every job that loops over many items calls `deadline()` and stops starting
new items once `past_safe_stop()` is true, then writes its results; the next run continues from the committed state.
"""
import os
import time

RUNNER_LIMIT_SECONDS = 350 * 60        # .github/workflows/run-jobs.yml timeout; Rattle Watch stops silent jobs sooner
SAFE_STOP_SECONDS = int(4.5 * 3600)    # leave about 80 minutes for writing, publishing and the runner's own steps
_START = time.time()


def safe_stop_seconds(env=None):
    env = os.environ if env is None else env
    try:
        return max(60, min(int(env.get("JOB_DEADLINE_SECONDS", SAFE_STOP_SECONDS)), RUNNER_LIMIT_SECONDS - 1800))
    except (TypeError, ValueError):
        return SAFE_STOP_SECONDS


def elapsed(start=None):
    return time.time() - (_START if start is None else start)


def past_safe_stop(start=None, env=None):
    return elapsed(start) > safe_stop_seconds(env)
