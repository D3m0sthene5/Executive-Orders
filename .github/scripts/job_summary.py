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
                       "no-results": "No results to commit."}.get(env.get("PUBLICATION"), "Publication disposition unavailable.")
    else:
        publication = {"failure": "Publication step failed.", "cancelled": "Publication step cancelled.",
                       "skipped": "Publication step skipped."}.get(outcome, "Publication outcome unavailable.")
    if env.get("DIAGNOSTIC") == "true" and outcome == "skipped":
        publication = "Diagnostic run: named jobs only; publication disabled."
    lines = ["## Production job summary", "", publication]
    check = read_json(RECEIPTS / "publication-check.json")
    if outcome == "failure" and isinstance(check, dict) and check.get("result") == "rejected":
        for problem in check.get("problems", []):
            job, reason = problem.get("job"), problem.get("reason")
            if isinstance(job, str) and NAME.fullmatch(job) and isinstance(reason, str) and NAME.fullmatch(reason):
                lines.append(f"- Freshness check rejected `{job}`: `{reason}`.")
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
