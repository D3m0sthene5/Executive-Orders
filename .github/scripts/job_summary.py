"""Render current runner receipts for the GitHub Actions summary."""
import json
import os
import re
from datetime import datetime
from pathlib import Path

RECEIPTS = Path("oversized/runner-freshness")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def execution(job, record, env):
    state, duration = "No current receipt", "—"
    if record and isinstance(record.get("exit_code"), int) and isinstance(record.get("publish_output"), bool):
        success = record.get("publish_output") is True
        state = "Succeeded" if success else "Failed"
        if record.get("exit_code") == 125:
            state = "Blocked or failed (125)"
        token = env["GITHUB_RUN_ID"] + "-" + env["GITHUB_RUN_ATTEMPT"]
        directory = Path("jobs", job, "output") if success else Path("jobs/_attempts", job, token)
        status = read_json(directory / "STATUS.json")
        if (isinstance(status, dict) and status.get("job") == job
                and status.get("commit_run") == env.get("GITHUB_SHA")
                and str(status.get("run_url", "")).endswith("/actions/runs/" + env["GITHUB_RUN_ID"])
                and status.get("exit_code") == record.get("exit_code")):
            result = status.get("result")
            if result in ("blocked", "failed", "succeeded"):
                state = result.capitalize()
            dependencies = status.get("blocked_by")
            if result == "blocked" and isinstance(dependencies, list):
                blockers = [x for x in dependencies if isinstance(x, str) and NAME.fullmatch(x)]
                if blockers:
                    state += " by " + ", ".join(blockers)
            try:
                start = datetime.fromisoformat(status["started_utc"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(status["finished_utc"].replace("Z", "+00:00"))
                seconds = int((end - start).total_seconds())
                if seconds >= 0:
                    minutes, remaining = divmod(seconds, 60)
                    duration = f"{minutes}m {remaining:02d}s"
            except (KeyError, AttributeError, ValueError, TypeError):
                pass
    return state, duration


def render(env):
    jobs = [job for job in env.get("JOBS", "").split() if NAME.fullmatch(job)]
    direct = set(env.get("DIRECT_JOBS", "").split())
    rows = read_json(RECEIPTS / "ATTEMPTS.json")
    attempts = {r["job"]: r for r in rows if isinstance(r, dict) and isinstance(r.get("job"), str)} if isinstance(rows, list) else {}
    outcome = env.get("PUBLISH_OUTCOME")
    if outcome == "success":
        publication = {"pushed": "Results pushed.", "unchanged": "Outputs unchanged; no commit needed.",
                       "records-only": "Only run records changed; no commit needed.",
                       "no-results": "No results to commit.",
                       "push-failed": "Push failed after every retry."}.get(env.get("PUBLICATION"), "Publication disposition unavailable.")
    else:
        publication = {"failure": "Publication step failed.", "cancelled": "Publication step cancelled.",
                       "skipped": "Publication step skipped."}.get(outcome, "Publication outcome unavailable.")
    if env.get("DIAGNOSTIC") == "true" and outcome == "skipped":
        publication = "Diagnostic run: named jobs only; publication disabled."
    lines = ["## Production job summary", "", publication]
    arsenale = read_json(RECEIPTS / "ARSENALE.json")
    arsenale = arsenale if isinstance(arsenale, dict) else {}
    record = arsenale.get("publication") if isinstance(arsenale.get("publication"), dict) else {}
    refused = record.get("refused") if isinstance(record.get("refused"), dict) else None
    if refused is not None:
        published = [j for j in record.get("published", []) if isinstance(j, str) and NAME.fullmatch(j)]
        if published:
            lines.append("Published: " + ", ".join(f"`{j}`" for j in published) + ".")
        for job, problems in refused.items():
            reasons = sorted({p.get("reason") for p in problems if isinstance(p, dict)
                              and isinstance(p.get("reason"), str) and NAME.fullmatch(p["reason"])})
            producers = sorted({j for p in problems if isinstance(p, dict) for j in p.get("because_refused", [])
                                if isinstance(j, str) and NAME.fullmatch(j)})
            if isinstance(job, str) and NAME.fullmatch(job):
                note = f" (it read a refused candidate of {', '.join(producers)})" if producers else ""
                lines.append(f"- Freshness check refused `{job}`: " + ", ".join(f"`{r}`" for r in reasons) + note + ".")
    else:
        check = read_json(RECEIPTS / "publication-check.json")
        if outcome == "failure" and isinstance(check, dict) and check.get("result") == "rejected":
            for problem in check.get("problems", []):
                job, reason = problem.get("job"), problem.get("reason")
                if isinstance(job, str) and NAME.fullmatch(job) and isinstance(reason, str) and NAME.fullmatch(reason):
                    lines.append(f"- Freshness check rejected `{job}`: `{reason}`.")
    requeue = arsenale.get("requeue") if isinstance(arsenale.get("requeue"), dict) else {}
    queued = [j for j in requeue.get("jobs", []) if isinstance(j, str) and NAME.fullmatch(j)]
    if requeue.get("dispatch") and queued:
        state = "dispatched" if requeue.get("returncode") == 0 else "dispatch failed"
        lines.append(f"- Re-queued {', '.join(f'`{j}`' for j in queued)} at depth {requeue.get('depth')} "
                     f"of {requeue.get('limit')} ({state}).")
    elif requeue.get("reason") == "requeue_limit_reached" and queued:
        lines.append(f"- Not re-queued (limit {requeue.get('limit')} reached): {', '.join(f'`{j}`' for j in queued)}.")
    stations = [s for s in arsenale.get("stations", []) if isinstance(s, dict)]
    if stations:
        lines.extend(["", "| Station | Jobs | Executed (UTC) |", "|---:|---|---|"])
        for station in stations:
            jobs = [j for j in station.get("jobs", []) if isinstance(j, str) and NAME.fullmatch(j)]
            span = f"{station.get('started_utc') or '?'} to {station.get('finished_utc') or '?'}"
            if re.fullmatch(r"[0-9TZ:\- ?to]+", span):
                lines.append(f"| {station.get('station')} | {', '.join(f'`{j}`' for j in jobs)} | {span} |")
        lock = arsenale.get("lock_acquired_utc")
        if isinstance(lock, str) and re.fullmatch(r"[0-9TZ:-]+", lock):
            lines.append("")
            lines.append(f"Writer lock acquired at {lock}; it was not held while the stations executed.")
    missing = [j for j in arsenale.get("not_executed", []) if isinstance(j, str) and NAME.fullmatch(j)]
    if missing:
        lines.append("- No station delivered results for: " + ", ".join(f"`{j}`" for j in missing) + ".")
    if not jobs:
        message = "No production jobs selected." if env.get("PICK_OUTCOME") == "success" else "Job selection unavailable."
        return "\n".join([*lines, "", message, ""])
    lines.extend(["", "| Job | Why it ran | Execution | Elapsed |", "|---|---|---|---:|"])
    for job in jobs:
        why = "Direct selection" if job in direct else "Downstream consumer" if direct else "Unknown"
        record = attempts.get(job)
        state, duration = execution(job, record, env)
        lines.append(f"| `{job}` | {why} | {state} | {duration} |")
    return "\n".join([*lines, ""])


if __name__ == "__main__":
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
        stream.write(render(os.environ))
