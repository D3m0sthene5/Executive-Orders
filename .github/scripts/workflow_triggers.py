"""Workflow trigger policy (owner, 2026-11-09, Kean D-20261109-no-push-runs).

Over 2026-11-06..09 most runner time went to runs started by pushes that raced each other and
the bots' result commits, and to legacy workflows that every pergamon-* tag push started. These
rules keep that from coming back:

1. Run jobs starts only on its schedule or by hand (workflow_dispatch), never on a push, pull
   request, workflow_run or workflow_call.
2. Every push trigger names literal branches, so tag pushes never start a workflow, and names
   no tags.
3. The retired legacy workflows start only by hand.
4. No workflow that a push, pull request or workflow_run starts may start Run jobs.

The checker reads the `on:` block itself, without a YAML library, and fails closed: a trigger
written in a form it cannot read with certainty (inline `on: push`, flow mappings, anchors) is
an error, not a pass. Run `python .github/scripts/workflow_triggers.py` to check the repository.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
RUN_JOBS = "run-jobs.yml"
RUN_JOBS_EVENTS = {"schedule", "workflow_dispatch"}
RETIRED = {"stage20-causal-cues.yml", "stage20-opus-recovery.yml", "stage20-shared-source-check.yml",
           "stage20-shared-statutes.yml", "stage21-batchforge.yml", "stage21-ofr-bulk.yml",
           "stage21-original-pdfs.yml", "stage21-reuse-sources.yml", "tribonian-finalization.yml",
           "r1-materializer-proof.yml"}
PUSH_KEYS = {"branches", "paths", "paths-ignore"}
# Events GitHub raises for tags (a pergamon-* release creates a tag); no workflow may listen to them.
TAG_EVENTS = {"create", "delete", "release", "registry_package"}
ON_KEY = re.compile(r"""^(?:on|"on"|'on'|true|"true"|'true')[ \t]*:(.*)$""")
KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)[ \t]*:(.*)$")
TOP_KEY = re.compile(r"""^(?:[A-Za-z_][A-Za-z0-9_-]*|"[^"]+"|'[^']+')[ \t]*:(?:[ \t]|$)""")
# Line breaks a YAML parser honours but str.split("\n") does not, and other invisible structure.
ODD_BREAKS = re.compile("[  \u0085\x0b\x0c﻿]")
BRANCH_PATTERN = re.compile(r"[*?+\[\]!]")
STARTS_RUN_JOBS = re.compile(r"run-jobs|['\"]?Run jobs['\"]?")
# Any way a workflow step can start another workflow run.
DISPATCH = re.compile(r"gh\s+workflow\s+run|/dispatches|createWorkflowDispatch|repository_dispatch"
                      r"|uses:\s*\.?/?\.github/workflows/|arsenale\.py\s+requeue")
# Picking jobs belongs to run-jobs.yml only; executing and committing a fixed set of jobs also to the
# progress refresh and to manual-only workflows.
PICKER = re.compile(r"pick_jobs\.py|arsenale\.py\s+(?:plan|publish)\b")
EXECUTOR = re.compile(r"run_jobs\.(?:py|sh)|commit_results\.sh")
EXECUTOR_ALLOWED = {RUN_JOBS, "refresh-readiness.yml"}


class PolicyError(ValueError):
    pass


def _strip(value):
    """Drop a trailing comment; refuse anything that is not empty."""
    value = value.split(" #", 1)[0].strip() if not value.lstrip().startswith("#") else ""
    return value


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def triggers(text):
    """Return {event: {key: [values]}} for a workflow's `on:` block, or raise PolicyError."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\t" in text:
        raise PolicyError("tabs in the workflow; YAML indentation must be spaces")
    if ODD_BREAKS.search(text):
        raise PolicyError("unusual line-break or invisible characters (U+2028, U+2029, U+0085, form feed, BOM)")
    lines = text.split("\n")
    for line in lines:
        # Every column-0 line is a comment or a top-level key. A quoted or folded value that runs on at
        # column 0 could end the `on:` block early for this reader but not for GitHub's.
        if line.strip() and not line.startswith(" ") and not line.startswith("#") and not TOP_KEY.match(line):
            raise PolicyError(f"column-0 line is not a top-level key: {line[:60]!r}")
    starts = [i for i, line in enumerate(lines) if ON_KEY.match(line)]
    if len(starts) != 1:
        raise PolicyError(f"expected exactly one top-level `on:` key, found {len(starts)}")
    start = starts[0]
    if _strip(ON_KEY.match(lines[start]).group(1)):
        raise PolicyError("write `on:` as a block, one event per line, not inline")
    body = []
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith(" ") and not line.lstrip().startswith("#"):
            break
        body.append(line)
    content = [line for line in body if line.strip() and not line.lstrip().startswith("#")]
    if not content:
        raise PolicyError("the `on:` block is empty")
    events, base = {}, _indent(content[0])
    event = key = None
    for line in content:
        depth, stripped = _indent(line), line.strip()
        if depth < base:
            raise PolicyError(f"unexpected indentation in `on:`: {stripped!r}")
        if depth == base:
            m = KEY.match(stripped)
            if not m:
                raise PolicyError(f"cannot read trigger line {stripped!r}")
            event, rest = m.group(1), _strip(m.group(2))
            if rest not in ("", "{}", "null", "~"):
                raise PolicyError(f"write the `{event}` trigger as a block, not inline ({rest!r})")
            if event in events:
                raise PolicyError(f"`{event}` appears twice in `on:`")
            events[event], key, sub = {}, None, None
            continue
        if event is None:
            raise PolicyError(f"cannot read trigger line {stripped!r}")
        if re.search(r"(^|[\s\[,])[&*][A-Za-z]|<<\s*:", stripped):
            raise PolicyError(f"YAML anchors, aliases and merge keys are not allowed in `on:` ({stripped!r})")
        if stripped.startswith("- "):
            if key is None:
                if event == "schedule":
                    continue
                raise PolicyError(f"a list item under `{event}` has no key: {stripped!r}")
            events[event][key].append(stripped[2:].strip().strip("'\""))
            continue
        m = KEY.match(stripped)
        if not m:
            raise PolicyError(f"cannot read line under `{event}`: {stripped!r}")
        if sub is not None and depth > sub:
            continue  # deeper detail, such as workflow_dispatch input fields
        sub, key, rest = depth, m.group(1), _strip(m.group(2))
        if rest.startswith("[") and rest.endswith("]"):
            events[event][key] = [v.strip().strip("'\"") for v in rest[1:-1].split(",") if v.strip()]
        elif rest.startswith(("[", "{")):
            raise PolicyError(f"cannot read `{event}.{key}`: {rest!r}")
        else:
            events[event][key] = [rest.strip("'\"")] if rest else []
    return events


def check(name, text):
    """Return a list of policy violations for one workflow file."""
    try:
        events = triggers(text)
    except PolicyError as exc:
        return [f"{name}: {exc}"]
    problems = []
    if set(events) & TAG_EVENTS:
        problems.append(f"{name}: no workflow may start on tag events {sorted(set(events) & TAG_EVENTS)}")
    if "push" in events:
        push = events["push"]
        branches = push.get("branches") or []
        if not branches:
            problems.append(f"{name}: a push trigger must name branches (a tag push matches every path)")
        if any(BRANCH_PATTERN.search(b) for b in branches):
            problems.append(f"{name}: push branches must be literal names, not patterns: {branches}")
        extra = set(push) - PUSH_KEYS
        if extra:
            problems.append(f"{name}: push may not use {sorted(extra)} (tags start nothing)")
    if name == RUN_JOBS and set(events) - RUN_JOBS_EVENTS:
        problems.append(f"{name}: Run jobs may start only on {sorted(RUN_JOBS_EVENTS)}, "
                        f"not {sorted(set(events) - RUN_JOBS_EVENTS)}")
    if name == RUN_JOBS and "schedule" not in events:
        problems.append(f"{name}: the scheduled sweep is missing")
    if name in RETIRED and set(events) != {"workflow_dispatch"}:
        problems.append(f"{name}: retired workflows start only by hand (workflow_dispatch), not {sorted(events)}")
    lines = text.replace("\r\n", "\n").split("\n")
    start = next(i for i, line in enumerate(lines) if ON_KEY.match(line))
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].strip() and not lines[i].startswith(" ") and not lines[i].startswith("#")), len(lines))
    # Everything outside the `on:` block, without comments (a workflow_run may name 'Run jobs' to listen).
    code = "\n".join(line for i, line in enumerate(lines)
                     if not (start <= i < end) and not line.lstrip().startswith("#"))
    title = re.search(r"""(?m)^name:[ \t]*['"]?([^'"\n#]*?)['"]?[ \t]*(?:#.*)?$""", text.replace("\r\n", "\n"))
    if name != RUN_JOBS and ((title and title.group(1).strip().lower() == "run jobs") or PICKER.search(code)):
        problems.append(f"{name}: only {RUN_JOBS} may be Run jobs or pick jobs")
    if name not in EXECUTOR_ALLOWED and set(events) != {"workflow_dispatch"} and EXECUTOR.search(code):
        problems.append(f"{name}: only {sorted(EXECUTOR_ALLOWED)} or a manual-only workflow may execute jobs")
    if name != RUN_JOBS and set(events) != {"workflow_dispatch"}:
        allowed = f"python .github/scripts/arsenale.py requeue --workflow {name}"
        for line in code.split("\n"):
            if DISPATCH.search(line) and re.sub(r"^(?:-\s+)?(?:run:\s*)?", "", line.strip()) != allowed:
                problems.append(f"{name}: a workflow that starts on {sorted(events)} may start no other "
                                f"workflow run (only `{allowed}`): {line.strip()[:80]!r}")
        if STARTS_RUN_JOBS.search(code):
            problems.append(f"{name}: a workflow that starts on {sorted(events)} may not start Run jobs")
    return problems


def check_repository(root=ROOT):
    folder = Path(root) / ".github/workflows"
    files = sorted(list(folder.glob("*.yml")) + list(folder.glob("*.yaml")))
    problems = [p for path in files for p in check(path.name, path.read_text(encoding="utf-8"))]
    if not any(path.name == RUN_JOBS for path in files):
        problems.append(f"{RUN_JOBS} is missing")
    return problems


if __name__ == "__main__":
    found = check_repository()
    for problem in found:
        print("::error::" + problem)
    print("Workflow trigger policy:", "FAILED" if found else "ok")
    sys.exit(1 if found else 0)
