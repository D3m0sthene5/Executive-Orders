"""Arsenale: execute jobs in parallel stations, publish them under one short lock.

Named for the Venetian Arsenal, which built galleys in parallel stations and
assembled them at the end. The runner has three stages:

plan     (no lock)  Pick jobs, pin one execution input commit, and split the
                    ordered selection into stations (groups). Jobs joined by an
                    after.txt edge share a station and run there in order, so a
                    consumer still reads its predecessor's same-run candidate.
execute  (no lock)  Each station checks out the pinned commit, materializes only
                    its jobs' inputs, runs them with run_jobs.py and uploads one
                    bundle: outputs, failed attempts, receipts, oversized files.
publish  (lock)     Check out the latest branch tip, unpack every bundle, decide
                    with result_freshness.check which jobs are still fresh, commit
                    only those (one commit, unchanged message format) and push
                    with a bounded retry. Stale jobs are refused, recorded, and
                    re-queued by a bounded workflow_dispatch of exactly those jobs.

Freshness is decided by the existing guard (result_freshness.py), unchanged.
Two declared reads across stations are possible without an after.txt edge (for
example daily-digest reads jobs/*/output/STATUS.json). Such a reader sees the
producer's base generation, which the guard accepts only when the producer comes
later in the check order. The plan therefore orders readers before those
producers, and merges stations when no such order exists. This is the same
condition a serial run satisfied; no new acceptance rule is introduced.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import result_freshness as freshness  # noqa: E402

RECEIPTS = Path("oversized/runner-freshness")
REPORT = RECEIPTS / "ARSENALE.json"
BUNDLE = "bundle.tar"
STATION = "STATION.json"
MAX_REQUEUE_DEPTH = 2           # an original run plus at most two re-queued generations
PUSH_ATTEMPTS = 5
RECORD_ONLY = re.compile(r"/output/(STATUS\.json|log\.txt|install-log\.txt|RUNNER_INPUTS\.json)$")
TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")
SHA = re.compile(r"^[0-9a-f]{40,64}$")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def git(*args, check=True, input=None):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check, input=input)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def names_from(value):
    names = [n for n in (value or "").split() if n]
    for name in names:
        if not freshness.NAME.fullmatch(name):
            raise ValueError(f"Invalid job name: {name!r}")
    return list(dict.fromkeys(names))


def output_github(**values):
    target = os.environ.get("GITHUB_OUTPUT")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as fh:
        for key, value in values.items():
            fh.write(f"{key}={value}\n")


def step_summary(text):
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(text)


# ------------------------------------------------------------------ planning
def reads_output(declared, producer):
    """True when a declared read scope can select any path below producer's output.

    Conservative by design: a wildcard whose literal prefix is compatible with the
    producer's output folder counts as a read (``jobs/*/output/STATUS.json`` reads
    every job; ``*`` reads everything). Over-reporting only costs parallelism.
    """
    target = f"jobs/{producer}/output"
    if freshness.under(target, declared.get("exclude", "\0")):
        return False
    for root in declared.get("roots", []):
        if root in ("", ".") or freshness.under(root, target) or freshness.under(target, root):
            return True
    for pattern in declared.get("patterns", []):
        wildcard = re.search(r"[*?\[]", pattern)
        if not wildcard:
            if freshness.under(pattern, target) or freshness.under(target, pattern):
                return True
            continue
        literal = pattern[:wildcard.start()]
        if literal.startswith(target + "/") or (target + "/").startswith(literal):
            return True
    return False


def after(name):
    return freshness.lines(Path("jobs") / name / "after.txt")


def declared_scope(name):
    try:
        return freshness.scope(name)
    except Exception as exc:  # the job will fail the same way when it runs
        print(f"::warning::Arsenale: cannot read declared inputs of {name} ({exc}); treating it as reading every job.")
        return {"roots": ["."], "patterns": ["*"], "exclude": f"jobs/{name}/output"}


def plan(order, scopes=None, after_of=None):
    """Return stations and a check order for an already dependency-ordered selection.

    ``order`` is pick_jobs' order (after.txt predecessors first). Stations are the
    connected components of after.txt edges among selected jobs; each runs its
    members in ``order``. A cross-station declared read (reader R of producer P,
    no after.txt edge) requires R before P in the check order, so that R's captured
    base generation of P is accepted exactly as in a serial run where P came later.
    If no check order satisfies every constraint, the stations involved merge.
    """
    order = list(dict.fromkeys(order))
    position = {name: i for i, name in enumerate(order)}
    after_of = after_of or after
    scopes = scopes if scopes is not None else {name: declared_scope(name) for name in order}
    parent = {name: name for name in order}

    def find(name):
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb, key=position.get)] = min(ra, rb, key=position.get)

    hard = set()
    for name in order:
        for dep in after_of(name):
            if dep in position and dep != name:
                hard.add((dep, name))
                union(dep, name)
    soft = sorted((producer, reader) for reader in order for producer in order
                  if producer != reader and (producer, reader) not in hard
                  and reads_output(scopes[reader], producer))
    merges = []
    while True:
        stations = {}
        for name in order:
            stations.setdefault(find(name), []).append(name)
        edges = {name: set() for name in order}
        for members in stations.values():
            for a, b in zip(members, members[1:]):
                edges[a].add(b)
        for producer, reader in soft:
            if find(producer) != find(reader):
                edges[reader].add(producer)
        indegree = {name: 0 for name in order}
        for targets in edges.values():
            for target in targets:
                indegree[target] += 1
        ready = sorted((n for n in order if not indegree[n]), key=position.get)
        check = []
        while ready:
            name = ready.pop(0)
            check.append(name)
            for target in edges[name]:
                indegree[target] -= 1
                if not indegree[target]:
                    ready.append(target)
            ready.sort(key=position.get)
        if len(check) == len(order):
            break
        stuck = {find(n) for n in order if n not in check}
        merges.append(sorted(stuck, key=position.get))
        first = min(stuck, key=position.get)
        for root in stuck:
            union(first, root)
    station_list = sorted(stations.values(), key=lambda members: position[members[0]])
    return {"order": order, "check_order": check,
            "stations": [{"station": i + 1, "jobs": members,
                          "cache": hashlib.sha256(" ".join(sorted(members)).encode()).hexdigest()[:12]}
                         for i, members in enumerate(station_list)],
            "after_edges": sorted(hard),
            "cross_station_reads": sorted((p, r) for p, r in soft if find(p) != find(r)),
            "merged_for_order": merges}


def command_plan(args):
    order = names_from(os.environ.get("JOBS"))
    commit = git("rev-parse", "HEAD").stdout.strip()
    result = plan(order)
    result.update(schema=1, input_commit=commit, planned_utc=now())
    write_json(RECEIPTS / "ARSENALE_PLAN.json", result)
    matrix = {"include": [{"station": s["station"], "jobs": " ".join(s["jobs"]), "cache": s["cache"]}
                          for s in result["stations"]]}
    output_github(input_commit=commit, check_order=" ".join(result["check_order"]),
                  matrix=json.dumps(matrix, separators=(",", ":")), stations=len(result["stations"]))
    lines = [f"Arsenale plan at `{commit[:12]}`: {len(order)} job(s) in {len(result['stations'])} station(s)."]
    for station in result["stations"]:
        lines.append(f"- Station {station['station']}: " + " -> ".join(f"`{j}`" for j in station["jobs"]))
    for producer, reader in result["cross_station_reads"]:
        lines.append(f"- `{reader}` reads `{producer}`'s base output; it is checked before `{producer}`.")
    for merged in result["merged_for_order"]:
        lines.append("- Merged stations to keep a valid check order: " + ", ".join(f"`{j}`" for j in merged))
    print("\n".join(lines))
    step_summary("\n".join(["## Arsenale plan", "", *lines, ""]))
    return 0


# ----------------------------------------------------------------- execution
def bundle_members(names, token, attempts):
    succeeded = {r["job"] for r in attempts if r.get("publish_output") is True}
    paths = []
    for name in names:
        if name in succeeded and Path("jobs", name, "output").is_dir():
            paths.append(f"jobs/{name}/output")
        attempt = Path("jobs/_attempts", name, token)
        if attempt.is_dir():
            paths.append(attempt.as_posix())
    if Path("oversized").is_dir():
        paths.append("oversized")
    return paths


def command_bundle(args):
    """Pack one station's results after run_jobs.py; never fails the station itself."""
    names = names_from(os.environ.get("JOBS"))
    token = "-".join((os.environ.get("GITHUB_RUN_ID", "local"), os.environ.get("GITHUB_RUN_ATTEMPT", "1")))
    attempts = read_json(RECEIPTS / "ATTEMPTS.json", [])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out / BUNDLE, "w") as tar:
        for path in bundle_members(names, token, attempts):
            tar.add(path, arcname=path, recursive=True)
    station = {"schema": 1, "station": args.station, "jobs": names, "token": token,
               "input_commit": git("rev-parse", "HEAD").stdout.strip(),
               "expected_input_commit": os.environ.get("ARSENALE_INPUT_COMMIT", ""),
               "started_utc": os.environ.get("ARSENALE_STARTED_UTC", ""), "finished_utc": now(),
               "runner": os.environ.get("RUNNER_NAME", ""), "attempts": attempts}
    write_json(out / STATION, station)
    print(f"Station {args.station}: bundled {len(attempts)} attempt record(s) for {' '.join(names)}.")
    return 0


# ------------------------------------------------------------------ collecting
def safe_member(member, allowed):
    name = member.name
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or not path.parts:
        return False
    if not (member.isfile() or member.isdir() or member.issym()):
        return False
    if member.isdir() and any(root.startswith(name.rstrip("/") + "/") for root in allowed):
        return True  # an ancestor folder such as oversized/
    return any(name == root or name.startswith(root + "/") for root in allowed)


def sparse_add(paths):
    sparse = git("config", "--bool", "core.sparseCheckout", check=False).stdout.strip()
    if sparse != "true" or not paths:
        return
    patterns = sorted({"/" + p.rstrip("/") + "/**" for p in paths})
    git("sparse-checkout", "add", "--stdin", input="\n".join(patterns) + "\n")


def replace_tree(source, target):
    target = Path(target)
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    if source is not None and Path(source).exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, symlinks=True)


def command_collect(args):
    """Unpack station bundles into the publish checkout and merge receipts in check order."""
    order = names_from(os.environ.get("JOBS"))
    expected = os.environ.get("ARSENALE_INPUT_COMMIT", "")
    token = "-".join((os.environ.get("GITHUB_RUN_ID", "local"), os.environ.get("GITHUB_RUN_ATTEMPT", "1")))
    source = Path(args.artifacts)
    stations, problems, attempts, checkout, seen = [], [], {}, {}, set()
    folders = sorted({p.parent for p in source.rglob(STATION)}) if source.exists() else []
    staged = Path(tempfile.mkdtemp(prefix="arsenale-"))
    for folder in folders:
        info = read_json(folder / STATION)
        try:
            if not isinstance(info, dict) or info.get("schema") != 1:
                raise ValueError("invalid station receipt")
            names = names_from(" ".join(info.get("jobs", [])))
            if not names or not set(names) <= set(order) or set(names) & seen:
                raise ValueError("station jobs are not a disjoint part of the plan")
            if info.get("token") != token or not TOKEN.fullmatch(token):
                raise ValueError("station belongs to another run attempt")
            if not SHA.fullmatch(str(info.get("input_commit"))) or (expected and info["input_commit"] != expected):
                raise ValueError("station executed a different input commit than the plan pinned")
            records = [r for r in info.get("attempts", []) if isinstance(r, dict) and r.get("job") in names]
            if len({r["job"] for r in records}) != len(records):
                raise ValueError("duplicate attempt records")
            succeeded = {r["job"] for r in records if r.get("publish_output") is True}
            allowed = [f"jobs/{n}/output" for n in succeeded] + [f"jobs/_attempts/{n}/{token}" for n in names]
            allowed += [f"oversized/{n}" for n in names] + ["oversized/runner-freshness"]
            target = staged / str(info["station"])
            target.mkdir(parents=True)
            with tarfile.open(folder / BUNDLE) as tar:
                members = tar.getmembers()
                refused = [m.name for m in members if not safe_member(m, allowed)]
                if refused:
                    raise ValueError(f"bundle holds paths outside its jobs: {refused[:5]}")
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(target, filter="data")
                else:
                    if any(m.issym() for m in members):
                        raise ValueError("this Python cannot safely unpack symlinks")
                    tar.extractall(target)
        except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
            problems.append({"station_folder": folder.name, "reason": "invalid_bundle", "detail": str(exc)})
            print(f"::error::Arsenale refused station bundle {folder.name}: {exc}")
            continue
        seen.update(names)
        for record in records:
            attempts[record["job"]] = record
        checkout[str(info["station"])] = read_json(target / RECEIPTS / "CHECKOUT_INPUTS.json")
        stations.append({key: info.get(key) for key in
                         ("station", "jobs", "input_commit", "started_utc", "finished_utc", "runner")}
                        | {"target": str(target), "succeeded": sorted(succeeded)})
    # Materialize the tip's copy of every output the publisher may stage, so
    # deletions are visible to Git and to the freshness guard.
    sparse_add([f"jobs/{n}/output" for n in attempts] + [f"jobs/_attempts/{n}" for n in attempts])
    for station in stations:
        target = Path(station.pop("target"))
        for name in station["jobs"]:
            if name in station["succeeded"]:
                replace_tree(target / "jobs" / name / "output", Path("jobs", name, "output"))
            attempt = target / "jobs/_attempts" / name / token
            if attempt.exists():
                replace_tree(attempt, Path("jobs/_attempts", name, token))
            if (target / "oversized" / name).exists():
                replace_tree(target / "oversized" / name, Path("oversized", name))
        receipts = target / RECEIPTS
        if receipts.exists():
            replace_tree(receipts, RECEIPTS / "stations" / str(station["station"]))
            for manifest in receipts.glob("*-inputs.json"):
                shutil.copyfile(manifest, RECEIPTS / manifest.name)
    shutil.rmtree(staged, ignore_errors=True)
    merged = [attempts[name] for name in order if name in attempts]
    missing = [name for name in order if name not in attempts]
    for name in missing:
        print(f"::error::Arsenale: no execution receipt for {name}; its station did not finish. Nothing is published for it.")
    write_json(RECEIPTS / "ATTEMPTS.json", merged)
    write_json(RECEIPTS / "CHECKOUT_INPUTS.json", {"schema": 1, "stations": checkout})
    if "valla" in {r["job"] for r in merged if r.get("publish_output")}:
        # Valla's freshness check rereads its dynamic closure from the worktree.
        import materialize_job_inputs
        materialize_job_inputs.materialize(["valla"], RECEIPTS / "PUBLISH_CHECKOUT_INPUTS.json")
    report = read_json(REPORT, {}) or {}
    report.update(schema=1, collected_utc=now(), lock_acquired_utc=os.environ.get("ARSENALE_LOCK_UTC") or now(),
                  input_commit=expected, check_order=order, stations=stations,
                  not_executed=missing, bundle_problems=problems)
    write_json(REPORT, report)
    print(f"Collected {len(stations)} station bundle(s); {len(merged)} receipt(s); missing {missing or 'none'}.")
    return 0


def command_verdict(args):
    """Fail the run, after publication, when a station delivered nothing usable."""
    report = read_json(REPORT, {}) or {}
    bad = report.get("not_executed") or report.get("bundle_problems")
    if bad:
        print("::error::Arsenale: stations missing or refused: " + json.dumps(bad))
        return 1
    return 0


# ----------------------------------------------------------------- publishing
def fresh_subset(ref, names, report_path):
    """Fresh subset: drop refused jobs and recheck the rest until the check passes.

    The final check over exactly the published set passes, which is the same
    acceptance condition the serial runner applied to its whole selection.
    """
    remaining, refused, rounds, final = list(names), {}, 0, None
    while remaining:
        rounds += 1
        buffer = io.StringIO()
        saved_summary = os.environ.pop("GITHUB_STEP_SUMMARY", None)
        try:
            with contextlib.redirect_stdout(buffer):
                code = freshness.check(ref, remaining, report_path)
        finally:
            if saved_summary is not None:
                os.environ["GITHUB_STEP_SUMMARY"] = saved_summary
        final = read_json(report_path)
        if code == 0:
            break
        bad = {p.get("job") for p in final.get("problems", [])} & set(remaining)
        if not bad:
            raise RuntimeError("freshness check rejected without naming a job")
        for problem in final["problems"]:
            if problem.get("job") in bad:
                refused.setdefault(problem["job"], []).append(problem)
        remaining = [n for n in remaining if n not in bad]
    for name, problems in refused.items():
        # A consumer refused only because a refused producer's candidate it read
        # is no longer what will be published: name that producer.
        paths = [c["path"] for p in problems for c in p.get("changed_paths", []) if isinstance(c, dict)]
        owners = {p.split("/")[1] for p in paths if re.match(r"^jobs/[^/]+/output/", p)}
        if (paths and all(p.get("reason") == "inputs_changed" for p in problems)
                and len(owners) and all(re.match(r"^jobs/[^/]+/output/", p) for p in paths)
                and owners <= set(refused) - {name}):
            problems[-1]["because_refused"] = sorted(owners)
    return remaining, refused, rounds, final


def candidate_paths(fresh, all_jobs):
    paths = [f"jobs/{n}/output" for n in fresh if Path("jobs", n, "output").is_dir()]
    paths += [f"jobs/_attempts/{n}" for n in all_jobs if Path("jobs/_attempts", n).is_dir()]
    digest = Path("jobs/daily-digest/output/DIGEST.md")
    if "daily-digest" in fresh and digest.is_file():
        if len(digest.read_text(encoding="utf-8").splitlines()) >= 150:
            raise SystemExit("Digest exceeds 149 lines")
        Path("HANDOFF/DIGEST.md").write_bytes(digest.read_bytes())
        paths.append("HANDOFF/DIGEST.md")
    return paths


def revert_to_head(path):
    """Put one path back to the checked-out branch tip (or remove it if untracked there)."""
    replace_tree(None, Path(path))
    if git("cat-file", "-e", f"HEAD:{path}", check=False).returncode == 0:
        git("checkout", "-q", "HEAD", "--", path)


def staged_names():
    return [p for p in git("diff", "--cached", "--name-only").stdout.splitlines() if p]


def report_publication(value):
    output_github(publication=value)


def restore(saved, paths):
    for path in paths:
        replace_tree(saved / path if (saved / path).exists() else None, Path(path))


def reset_to(ref, saved, keep):
    git("reset", "-q", "--hard", ref)
    restore(saved, keep)


def render_refusal(refused, check_report):
    rendered = json.dumps({"schema": 1, "result": "rejected", "jobs": sorted(refused),
                           "problems": [p for problems in refused.values() for p in problems],
                           "action": "Refused jobs were not published; they are re-queued on the current branch."},
                          indent=2)
    print("::error::Runner results rejected as stale for: " + ", ".join(sorted(refused)))
    print(rendered)
    step_summary("\n### Runner freshness rejection\n\n```json\n" + rendered + "\n```\n")


def command_publish(args):
    branch = os.environ["BRANCH"]
    run_url = os.environ.get("RUN_URL", "")
    event = os.environ.get("EVENT", "")
    all_jobs = names_from(os.environ.get("JOBS"))
    attempts = read_json(RECEIPTS / "ATTEMPTS.json")
    if attempts is None:
        candidates = list(all_jobs)
    else:
        succeeded = {r["job"] for r in attempts if r.get("publish_output")}
        candidates = [n for n in all_jobs if n in succeeded]
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    keep = [f"jobs/{n}/output" for n in candidates] + [f"jobs/_attempts/{n}" for n in all_jobs]
    saved = Path(tempfile.mkdtemp(prefix="arsenale-publish-"))
    for path in keep:
        if Path(path).exists():
            (saved / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(path, saved / path, symlinks=True)
    check_report = RECEIPTS / "publication-check.json"
    record = {"started_utc": now(), "candidates": candidates, "push_attempts": 0}
    refused, fresh, outcome = {}, [], None
    pool = list(candidates)
    remote = f"origin/{branch}"
    for attempt in range(1, PUSH_ATTEMPTS + 1):
        git("fetch", "-q", "origin", branch)
        reset_to(remote, saved, keep)
        if attempt == 1:
            # The serial runner's no-op rules apply to the whole selection first.
            paths = candidate_paths(candidates, all_jobs)
            if paths:
                git("add", "-A", "--", *paths)
            changed = staged_names() if paths else []
            git("reset", "-q")
            revert_to_head("HANDOFF/DIGEST.md")
            if not paths:
                outcome = "no-results"
                break
            if not changed:
                outcome = "unchanged"
                break
            if event == "schedule" and all(RECORD_ONLY.search(p) for p in changed):
                outcome = "records-only"
                break
        # Each push attempt rechecks against the newest tip; the set only shrinks.
        fresh, newly, rounds, _ = fresh_subset(remote, pool, check_report)
        refused.update(newly)
        pool = list(fresh)
        record["freshness_rounds"] = record.get("freshness_rounds", 0) + rounds
        for name in candidates:
            if name not in fresh:
                revert_to_head(f"jobs/{name}/output")
        paths = candidate_paths(fresh, all_jobs)
        if not paths:
            outcome = "no-results"
            break
        git("add", "-A", "--", *paths)
        if not staged_names():
            outcome = "unchanged"
            break
        git("commit", "-q", "-m", "Results of job(s): " + " ".join(fresh), "-m", "Run: " + run_url)
        record["push_attempts"] = attempt
        push = git("push", "-q", "origin", f"HEAD:{branch}", check=False)
        if push.returncode == 0:
            outcome = "pushed"
            record["commit"] = git("rev-parse", "HEAD").stdout.strip()
            print(f"Results pushed to {branch}.")
            break
        print(f"Push rejected (attempt {attempt}); taking the newer commits and retrying.")
        print(push.stderr.strip())
        time.sleep(attempt * int(os.environ.get("ARSENALE_RETRY_SECONDS", "5")))
    else:
        outcome = "push-failed"
        for name in fresh:
            refused.setdefault(name, []).append({"job": name, "reason": "push_retries_exhausted"})
    if outcome != "pushed":
        print({"no-results": "No results to commit.", "unchanged": "Results are unchanged; nothing to commit.",
               "records-only": "Only the run record changed; nothing new to commit."}.get(outcome, ""))
    published = fresh if outcome == "pushed" else []
    record.update(finished_utc=now(), outcome=outcome, published=published,
                  refused={name: problems for name, problems in refused.items()})
    report = read_json(REPORT, {}) or {}
    report["publication"] = record
    write_json(REPORT, report)
    report_publication(outcome)
    output_github(refused=" ".join(n for n in candidates if n in refused))
    if refused:
        # Keep the refused generations for inspection with the run's downloads.
        for name in refused:
            if (saved / "jobs" / name / "output").exists():
                replace_tree(saved / "jobs" / name / "output", Path("oversized/refused", name))
        render_refusal(refused, check_report)
    shutil.rmtree(saved, ignore_errors=True)
    if outcome == "push-failed":
        print(f"::error::Could not push results after {PUSH_ATTEMPTS} attempts.")
        return 1
    return 3 if refused else 0


# ------------------------------------------------------------------ requeueing
def requeue_plan(refused, depth, downstream, workflow, ref, limit=MAX_REQUEUE_DEPTH):
    """Return the exact dispatch for refused jobs, or why there is none (bounded)."""
    refused = names_from(" ".join(refused))
    if not refused:
        return {"dispatch": False, "reason": "nothing_refused"}
    if depth >= limit:
        return {"dispatch": False, "reason": "requeue_limit_reached", "depth": depth, "limit": limit, "jobs": refused}
    fields = {"job": " ".join(refused), "requeue_depth": str(depth + 1)}
    if workflow == "run-jobs.yml":
        fields["downstream"] = " ".join(n for n in refused if n in set(downstream))
    args = ["gh", "workflow", "run", workflow, "--ref", ref]
    for key, value in fields.items():
        if key == "job" and workflow != "run-jobs.yml":
            continue
        args += ["-f", f"{key}={value}"]
    return {"dispatch": True, "depth": depth + 1, "limit": limit, "jobs": refused, "command": args}


def command_requeue(args):
    report = read_json(REPORT, {}) or {}
    publication = report.get("publication") or {}
    refused = sorted((publication.get("refused") or {}).keys())
    try:
        depth = int(os.environ.get("REQUEUE_DEPTH") or 0)
    except ValueError:
        depth = MAX_REQUEUE_DEPTH
    decision = requeue_plan(refused, depth, names_from(os.environ.get("DOWNSTREAM_ONLY")),
                            args.workflow, os.environ.get("REQUEUE_REF") or os.environ.get("BRANCH", ""))
    if decision["dispatch"]:
        result = subprocess.run(decision["command"], capture_output=True, text=True)
        decision.update(returncode=result.returncode, stderr=result.stderr.strip()[-500:], dispatched_utc=now())
        if result.returncode:
            print(f"::error::Re-queue dispatch failed: {result.stderr.strip()}")
        else:
            print(f"Re-queued {' '.join(decision['jobs'])} at depth {decision['depth']} of {decision['limit']}.")
    elif decision["reason"] == "requeue_limit_reached":
        print(f"::warning::Refused jobs {' '.join(decision['jobs'])} were not re-queued: the re-queue limit "
              f"({decision['limit']}) is reached. Their next scheduled or manual run publishes them.")
    report["requeue"] = decision
    write_json(REPORT, report)
    return 1 if decision.get("returncode") else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    bundle = sub.add_parser("bundle")
    bundle.add_argument("--station", type=int, required=True)
    bundle.add_argument("--out", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--artifacts", required=True)
    sub.add_parser("publish")
    sub.add_parser("verdict")
    requeue = sub.add_parser("requeue")
    requeue.add_argument("--workflow", required=True)
    args = parser.parse_args(argv)
    return {"plan": command_plan, "bundle": command_bundle, "collect": command_collect,
            "publish": command_publish, "requeue": command_requeue, "verdict": command_verdict}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
