"""Decide which jobs/<name>/ folders the runner should run.

No push starts the runner (owner, 2026-11-09, Kean D-20261109-no-push-runs): push-started runs raced
each other and the bots' own result commits, and most of their results were refused as stale.
.github/scripts/test_workflow_triggers.py keeps it that way. The push branch of main() below is kept
only for a manual replay of old events.
- The sweep (every scheduled run) runs every job whose own folder changed outside output/, or
  whose triggers.txt has a pattern (fnmatch, e.g. "research/readiness/claims/*") matching a path
  changed on the default branch, plus every job that reads their outputs (after.txt). "Changed"
  means every first-parent commit after the input commit of the previous sweep whose plan
  succeeded, read from GitHub's run history, so a sweep GitHub starts late, or a commit dated
  earlier than its push, is still seen. Only if that history is unavailable does the sweep fall
  back to the last SWEEP_WINDOW, with a warning.
- The daily scheduled run (09:17 UTC) is a sweep that also runs every job whose folder contains a
  file named DAILY, with their consumers at full strength. GitHub has delivered only the 3-hour
  cron since a second cron was added on 2026-10-28, so every sweep also runs each DAILY job whose
  newest committed receipt (output/STATUS.json or jobs/_attempts/<name>/) is older than
  DAILY_STALE_HOURS (Justinian, 2026-11-06; this replaces .github/workflows/daily-dispatch.yml).
  Receipt ages come from Git history, not from output files, which the picker's checkout omits.
- A manual run runs the named job(s), separated by spaces or commas, plus their consumers; with
  only=true it runs exactly the named jobs, as a push used to.
  Manual diagnostics run only the requested jobs; the workflow retains receipts without publishing.
  An Arsenale re-queue (a manual run with requeue_depth > 0) or a Riquet continuation (continuation > 0)
  runs exactly the jobs it names, and
  marks the names in its downstream input as downstream-only, as the refused run had them.
Picked jobs are ordered so that any job listed in a job's after.txt runs before it. Folders
starting with "_" (the template) are never run. The result goes to the step output "jobs" as a
space-separated list; jobs a sweep runs only as consumers go to "downstream".

The runner's initial sparse checkout contains job code/data but omits outputs.
The picker reads root entrypoints and selector manifests. The selected-job
materializer runs afterward; do not add reads of output generations here.
"""

import fnmatch
import hashlib
import json
from pathlib import Path
import os
import re
import subprocess
import sys
import urllib.request

NAME =re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ZERO = "0" * 40
RUNNER_FILES = {".github/workflows/run-jobs.yml"}
SMOKE_TEST = "example-hello"
DAILY_CRON = "17 9 * * *"
# Fallback only, when GitHub's run history cannot name the previous sweep: look back a little further
# than the 3-hour interval; a file changed twice in the overlap only reruns the same jobs once more.
SWEEP_WINDOW = "3 hours 20 minutes ago"
SHA = re.compile(r"^[0-9a-f]{40}$")
DAILY_STALE_HOURS = 20


# Audited at bc65c165 / Opus 71b06f9f. Include every COMPILER_FILES entry,
# entrypoint, conservative local imports and literal dynamic imports. Unknown
# versions rebuild; adding a compiler import invalidates its importing file pin.
CLAIM_KIT_COMPILER_SHA256 = {
    'jobs/claim-kit/act_overrides.py': ('8683c33052f0604e07e790bede2fa6fed1c985707b45a12e14a7eb27f7c09280',),
    'jobs/claim-kit/assemble.py': ('3f6b92ec04cfb07d4d561db5e482bc74c16f14c7ef095666b715f3c7505c7bdb',),
    'jobs/claim-kit/build.py': ('e662bc493ce6bb07d5b550e05c0af2843d82ae61311ae416e7191f1ce074d281',),
    'jobs/claim-kit/current_evidence.py': ('b31d106f84c63736952ee3641a7f5809e804ecd85ae87d1687d5733591d1a93c',),
    'jobs/claim-kit/excavate.py': ('d869e4086c121e33da551ebbe17e678d945d1424d223c1cd1d891d0f2ca5347d',),
    'jobs/claim-kit/factual_events.py': ('f8ba8ad809e5b0c845cb6a3b2946b1d33c0e4e88b916d126c3e58d2ee1c79659',),
    'jobs/claim-kit/inputs.py': ('6ca64e4c65479bd1f363386981e25f390e38295eb3b5a38f9ca316deca60f2dd',),
    'jobs/claim-kit/job.py': ('67a39c213771ffc5a6a4a3fdec7e94b7f2aeed45b38f3a7ef63747503ed04c37',),
    'jobs/claim-kit/lifecycle_obligations.py': ('61448e4f640b76312df4d47f9f5c000468d1ce7e24d0c5df1115a273e13bf5ab',),
    'jobs/claim-kit/population.py': ('299596047de00d2849d26800f63ce1289412170f6b443445f05bf2d11a0d4859',),
    'jobs/claim-kit/prior_research.py': ('3c6fd78ad67bf8a906f41d20e96def99acc08b89a4912bc3db9d2787c26f473b', '971946c180a91015c46904c030ad513e76d81671a6dc9cb49d0788cab3a7cc14'),
    'jobs/claim-kit/working_text.py': ('81de05d41220a7db6fe43a774a13ffd8ab00353573b16ef9ea15ce1088d06bb9',),
    'jobs/clause-drafts/segment.py': ('0ea7afd1bfd6e5776068d32bda1b58efcc367db3055740ee64709da0caef6573',),
    'jobs/norton/model.py': ('abb91bf8c851d051f49a745b2706e0d26b929cc16d3159e1cbd7e22b2957de12',),
    'research/stage19/code/claim_gate.py': ('709c7af8973037cb25cc22e2777a6201afe8863f899d5c2651ebd6959c693875',),
}
# Exact runtime files and their tests only. In particular prior_research.py is
# conservatively compiler code (lifecycle_obligations imports it inside main).
CLAIM_KIT_RUNTIME_ONLY = frozenset('jobs/claim-kit/' + name for name in (
    'batch.py', 'completion.py', 'fragment_cache.py', 'source_supplement.py',
    'status_overlay.py', 'kit.py', 'test_batch.py', 'test_completion.py',
    'test_source_supplement.py', 'test_status_overlay.py',
    'test_overlay_completion.py', 'test_continuous_route.py',
    'test_working_text_index.py',
))


def claim_kit_runtime_only(changed):
    """A push exemption, never an assertion that generated outputs are fresh.

    The sparse bootstrap omits research code. Read its committed blob without
    expanding checkout; missing files/blobs or any changed compiler pin rebuild.
    """
    if not changed or not set(changed) <= CLAIM_KIT_RUNTIME_ONLY:
        return False
    for path, expected in CLAIM_KIT_COMPILER_SHA256.items():
        try:
            if Path(path).is_file():
                raw = Path(path).read_bytes()
            else:
                result = subprocess.run(['git', 'show', 'HEAD:' + path], capture_output=True)
                if result.returncode:
                    return False
                raw = result.stdout
            if hashlib.sha256(raw).hexdigest() not in expected:
                return False
        except OSError:
            return False
    return True


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def runnable(name):
    folder = os.path.join("jobs", name)
    return NAME.match(name) and any(
        os.path.isfile(os.path.join(folder, f)) for f in ("job.sh", "job.py")
    )


def changed_files(before, after):
    if before and before != ZERO and git("cat-file", "-e", before).returncode == 0:
        base = before
    else:
        # New branch: compare with where it left the default branch.
        default = os.environ.get("DEFAULT_BRANCH") or "main"
        base = git("merge-base", f"origin/{default}", after).stdout.strip()
        if not base or base == after:
            base = f"{after}~1"
    out = git("diff", "--name-only", base, after)
    if out.returncode != 0:
        sys.exit(f"Could not list changed files: {out.stderr}")
    return out.stdout.splitlines()


def job_list(name, filename):
    """Non-comment lines of jobs/<name>/<filename>, or [] if it does not exist."""
    path = os.path.join("jobs", name, filename)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [l.split("#", 1)[0].strip() for l in fh if l.split("#", 1)[0].strip()]


def all_jobs():
    # The non-cone runner bootstrap includes these root entrypoints for every
    # job, but omits nested data and output generations until after selection.
    return sorted(n for n in os.listdir("jobs") if not n.startswith("_") and runnable(n))


def ordered(picked):
    """Stable order in which every job's after.txt predecessors (if picked) come first."""
    picked, done, out = list(dict.fromkeys(picked)), set(), []

    def visit(name, path=()):
        if name in path:
            raise ValueError("Job dependency cycle: " + " -> ".join((*path, name)))
        if name in done:
            return
        for before in job_list(name, "after.txt"):
            if before in picked:
                visit(before, path + (name,))
        done.add(name)
        out.append(name)

    for name in picked:
        visit(name)
    return out


def with_consumers(picked):
    """Include downstream jobs because output-only bot commits trigger no workflow."""
    selected=set(picked)
    while True:
        more={name for name in all_jobs() if any(dep in selected for dep in job_list(name,'after.txt'))}
        if more <= selected:return sorted(selected)
        selected |= more


def recent_changes(since=SWEEP_WINDOW):
    """Paths changed on this branch's first-parent history since a time (merge commits count in full)."""
    out = git("log", "--first-parent", "-m", "--name-only", "--format=", f"--since={since}", "HEAD")
    if out.returncode != 0:
        sys.exit(f"Could not list recent changes: {out.stderr}")
    return sorted({line for line in out.stdout.splitlines() if line.strip()})


def github(path):
    """GET a GitHub REST path with the run's token; raises OSError/ValueError on any failure."""
    api = os.environ.get("GITHUB_API_URL") or "https://api.github.com"
    request = urllib.request.Request(api + path, headers={
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "pick_jobs"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def previous_sweep_commit():
    """Input commit of the newest earlier scheduled run whose plan succeeded, or None if unknown.

    A run that GitHub started but whose plan failed (or that was cancelled) never picked its jobs,
    so its commits stay in the next sweep's range. Its head_sha is the commit that triggered it,
    at or before the tip its plan read, so a range starting there can overlap, never skip.
    """
    repo, run_id = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_RUN_ID") or ""
    branch = os.environ.get("DEFAULT_BRANCH") or "main"
    if not (repo and os.environ.get("GITHUB_TOKEN")):
        return None
    try:
        runs = github(f"/repos/{repo}/actions/workflows/run-jobs.yml/runs"
                      f"?event=schedule&branch={branch}&per_page=50")["workflow_runs"]
        mine = next((r["created_at"] for r in runs if str(r["id"]) == run_id), None)
        for run in sorted(runs, key=lambda r: r["created_at"], reverse=True):
            if str(run["id"]) == run_id or (mine and run["created_at"] >= mine):
                continue
            if run.get("status") != "completed" or run.get("conclusion") not in ("success", "failure"):
                continue
            jobs = github(f"/repos/{repo}/actions/runs/{run['id']}/jobs?filter=latest&per_page=100")["jobs"]
            if any(j.get("name") == "plan" and j.get("conclusion") == "success" for j in jobs):
                sha = run.get("head_sha") or ""
                return sha if SHA.match(sha) else None
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"::warning::Could not read the previous sweep from GitHub: {exc}")
    return None


def sweep_changes():
    """Paths changed on first-parent history since the previous sweep's input commit."""
    base = previous_sweep_commit()
    if base and git("merge-base", "--is-ancestor", base, "HEAD").returncode == 0:
        out = git("log", "--first-parent", "-m", "--name-only", "--format=", f"{base}..HEAD")
        if out.returncode == 0:
            print(f"Sweep range: commits after {base[:12]}, the previous sweep's input.")
            return sorted({line for line in out.stdout.splitlines() if line.strip()})
    print(f"::warning::The previous sweep's input commit is unknown or not on this branch; "
          f"the sweep falls back to changes since {SWEEP_WINDOW}.")
    return recent_changes()


def for_changes(changed, triggers=True, runtime_push=False):
    """Select direct consumers of code/data edits; outputs never start feedback loops.

    Shared-library consumers declare exact files in triggers.txt, including
    transitive imports. This keeps docs/test-only library edits from refetching
    the corpus and makes non-Python or dynamic dependencies explicit too.
    """
    skip_claim_kit = runtime_push and claim_kit_runtime_only(changed)
    picked = []
    for path in changed:
        # A change to the runner itself reruns the smoke test.
        if path in RUNNER_FILES or path.startswith(".github/scripts/"):
            if SMOKE_TEST not in picked and runnable(SMOKE_TEST):
                picked.append(SMOKE_TEST)
            continue
        parts = path.split("/")
        if len(parts) < 3 or parts[0] != "jobs" or parts[2] == "output":
            continue
        name = parts[1]
        if name == "claim-kit" and skip_claim_kit:
            continue
        if name.startswith("_") or name in picked or not runnable(name):
            continue
        picked.append(name)
    if not triggers:
        return picked
    # Jobs that asked to rerun when these paths change (job outputs never count).
    inputs = [p for p in changed if not re.match(r"^jobs/[^/]+/output/", p)]
    for name in all_jobs():
        patterns = job_list(name, "triggers.txt")
        if name not in picked and any(fnmatch.fnmatch(p, pat) for p in inputs for pat in patterns):
            picked.append(name)
    return picked


def downstream_only(direct, picked):
    """Jobs selected only as consumers of a selected job, not by a change to their own folder or triggers."""
    return [name for name in picked if name not in set(direct)]


def requeue_depth():
    """Arsenale re-queue generation of a manual run (0 for an ordinary run)."""
    value = (os.environ.get("REQUEUE_DEPTH") or "0").strip()
    if not re.fullmatch(r"[0-9]{1,2}", value):
        sys.exit(f"Invalid requeue_depth: {value!r}")
    return int(value)


def continuation():
    """Riquet continuation number of a manual run (0 for an ordinary run)."""
    value = (os.environ.get("CONTINUATION") or "0").strip()
    if not re.fullmatch(r"[0-9]{1,2}", value):
        sys.exit(f"Invalid continuation: {value!r}")
    return int(value)


def daily_jobs():
    return sorted(name for name in os.listdir("jobs")
                  if not name.startswith("_") and runnable(name) and os.path.isfile(os.path.join("jobs", name, "DAILY")))


def receipt_age_hours(name, now=None):
    """Hours since the newest commit touching the job's STATUS.json or its retained attempts; None if never."""
    out = git("log", "-1", "--format=%ct", "HEAD", "--", f"jobs/{name}/output/STATUS.json", f"jobs/_attempts/{name}")
    stamp = out.stdout.strip() if out.returncode == 0 else ""
    if not stamp.isdigit():
        return None
    import time
    return ((now if now is not None else time.time()) - int(stamp)) / 3600


def stale_daily_jobs(hours=DAILY_STALE_HOURS, now=None):
    """DAILY jobs with no receipt, or whose newest receipt is older than `hours`."""
    stale = []
    for name in daily_jobs():
        age = receipt_age_hours(name, now)
        if age is None or age > hours:
            stale.append(name)
    return stale


def main():
    event, schedule = os.environ.get("EVENT"), os.environ.get("SCHEDULE") or ""
    # Every scheduled run is a sweep, so "the previous sweep" is simply the previous scheduled run.
    sweep = event == "schedule"
    consumers = True
    runtime_tests = False
    daily_due = []
    full_strength = set()
    if sweep:
        picked = for_changes(sweep_changes())
        due = daily_jobs() if schedule == DAILY_CRON else stale_daily_jobs()
        daily_due = [name for name in due if name not in picked]
        picked += daily_due
        if schedule == DAILY_CRON:
            # The daily run keeps its DAILY jobs' consumers at full strength.
            full_strength = set(with_consumers(due))
    elif os.environ.get("EVENT") == "workflow_dispatch":
        # An Arsenale re-queue (requeue_depth > 0) reruns exactly the refused jobs, and a Riquet
        # continuation (continuation > 0) runs exactly the jobs an earlier run deferred. With only=true
        # a manual run runs exactly the named jobs, as a push used to.
        consumers = (os.environ.get("DIAGNOSTIC") != "true" and os.environ.get("ONLY") != "true"
                     and not requeue_depth() and not continuation())
        picked = []
        for name in re.split(r"[\s,]+", os.environ.get("INPUT_JOB") or ""):
            name = name.strip().strip("/").removeprefix("jobs/")
            if not name:
                continue
            if not runnable(name):
                if requeue_depth() or continuation():
                    # A job renamed or removed since the earlier run queued it: skip it, keep the rest.
                    print(f"::warning::Skipping '{name}': it is no longer a runnable job.")
                    continue
                sys.exit(f"There is no job called '{name}'. It needs jobs/{name}/job.sh or job.py.")
            picked.append(name)
        if not picked and not (requeue_depth() or continuation()):
            sys.exit("Type at least one job name.")
    else:
        # A push: only jobs whose own code changed, nothing downstream. The next sweep does the rest.
        changed = changed_files(os.environ.get("BEFORE"), os.environ["AFTER"])
        runtime_tests = claim_kit_runtime_only(changed)
        picked = for_changes(changed, triggers=False, runtime_push=runtime_tests)
        consumers = False

    direct = list(picked)
    try:
        picked = ordered(with_consumers(picked) if consumers else picked)
    except ValueError as exc:
        sys.exit(str(exc))
    if sweep:
        # A DAILY job due by age runs at full strength, never as a downstream-only consumer.
        downstream = [name for name in downstream_only(direct, picked)
                      if name not in daily_due and name not in full_strength]
    elif event == "workflow_dispatch":
        # A re-queued sweep consumer keeps the small web-search budget it ran with.
        named = set(re.split(r"[\s,]+", os.environ.get("INPUT_DOWNSTREAM") or ""))
        downstream = [name for name in picked if name in named]
    else:
        downstream = []
    print("Jobs to run:", ", ".join(picked) or "none")
    if runtime_tests:
        print("Claim-kit runtime-only push: running unit tests; compiler refresh remains scheduled/manual.")
    if daily_due:
        print(f"DAILY jobs with no receipt in {DAILY_STALE_HOURS} hours:", ", ".join(daily_due))
    if downstream:
        print("Running only because a job they read changed:", ", ".join(downstream))
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"jobs={' '.join(picked)}\n")
        fh.write(f"direct={' '.join(dict.fromkeys(direct))}\n")
        if runtime_tests:
            fh.write("runtime_tests=claim-kit\n")
        if downstream:
            fh.write(f"downstream={' '.join(downstream)}\n")


if __name__ == "__main__":
    main()
