"""Publish the existing Capcom model from a validated native tracker generation.

This display adapter never runs a gate, changes readiness, or refreezes weights.
The shared runner publishes its output transactionally with the digest. Refusal
leaves the previous successful generation available, including its original date.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys

SOURCE = "research/progress/remaining-work/"
TRACKER = "jobs/readiness-tracker/output/"
CHECKER = "jobs/claim-checker/output/"
FROZEN_WEIGHTS = {1: 15.0, 2: 6.216, 3: 6.19, 4: 4.992,
                  5: 20.643, 6: 9.606, 7: 10.027, 8: 1.409}
FROZEN_GAP = 1314


def require(condition, message):
    if not condition:
        raise ValueError("Mission refresh refused: " + message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def instant(value):
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "generation time has no timezone")
    return result.astimezone(dt.timezone.utc)


def load_capcom(root):
    folder = root / SOURCE
    sys.path.insert(0, str(folder))
    try:
        spec = importlib.util.spec_from_file_location("daily_digest_capcom", folder / "build_mission_log.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    module.ROOT = root
    return module


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode().strip()


def readiness_witness(root, captured=None, producer="tracker"):
    """Bind committed canonical inputs using scoped Git metadata, not a corpus scan."""
    path = "research/readiness"
    tree = git(root, "rev-parse", "HEAD:" + path)
    require(re.fullmatch(r"[0-9a-f]{40,64}", tree)
            and git(root, "cat-file", "-t", tree) == "tree", "canonical readiness tree is unavailable")
    # Native producer jobs change their output folders, never these scientific
    # inputs. A dirty readiness checkout cannot be described by a committed tree.
    require(not git(root, "diff", "--name-only", "HEAD", "--", path)
            and not git(root, "ls-files", "--others", "--exclude-standard", "--", path),
            "canonical readiness inputs contain uncommitted changes")
    if captured is not None:
        current = {}
        for record in git(root, "ls-tree", "-r", "-z", "HEAD", "--", path).split("\0"):
            if record:
                header, relative = record.split("\t", 1)
                mode, kind, oid = header.split()
                require(kind == "blob", "unsupported canonical readiness entry")
                current[relative] = mode + ":" + oid
        consumed = {p: value for p, value in captured.items() if p == path or p.startswith(path + "/")}
        require(current == consumed, producer + " did not consume the current canonical readiness tree")
    return {"path": path, "git_tree": tree}


def validate_generation(status, manifest, name):
    require(status.get("job") == name and status.get("result") == "succeeded"
            and status.get("exit_code") == 0, name + " receipt is not successful")
    require(not status.get("oversized_files_moved_to_run_download"), name + " generation is incomplete")
    require(re.fullmatch(r"[0-9a-f]{40,64}", status.get("commit_run") or ""), name + " input commit is missing")
    require(instant(status["finished_utc"]) >= instant(status["started_utc"]), name + " generation times are reversed")
    require(manifest.get("schema") == 1 and manifest.get("job") == name
            and isinstance(manifest.get("inputs"), dict), name + " provenance is missing or invalid")
    require(digest(manifest["inputs"]) == manifest.get("inputs_sha256"), name + " provenance digest differs")
    require(manifest.get("base_commit") == status["commit_run"]
            and manifest.get("run_url") == status.get("run_url"), name + " receipt and provenance disagree")


def validate_rows(rows, summary, steps):
    ids = [r.get("instrument_id") for r in rows]
    require(rows and all(ids) and len(set(ids)) == len(ids), "tracker identities are empty or duplicated")
    require(len(rows) == summary.get("orders_total"), "tracker CSV and summary census disagree")
    require(sum(r.get("ready_for_human_review") == "yes" for r in rows)
            == summary.get("ready_for_human_review"), "tracker CSV and summary readiness disagree")
    require(sum(r.get("provisional_status") in ("yes", "no") for r in rows)
            == summary.get("orders_with_provisional_status"), "tracker CSV and summary statuses disagree")
    require(not summary.get("input_problems"), "tracker reports input problems")
    for row in rows:
        require(row.get("ready_for_human_review") in ("yes", "no")
                and row.get("provisional_status") in ("", "yes", "no"), "unknown readiness/status value")
        for step in steps:
            allowed = {"done", "open"}
            if step == "original_text":
                allowed.add("provisional")  # Retained Capcom semantics; not silently promoted to done.
            if step in ("shared_sources", "opus_media"):
                allowed.add("n/a")
            require(row.get("step_" + step) in allowed, "unknown or missing tracker step " + step)
        if row["ready_for_human_review"] == "yes":
            require(all(row["step_" + step] in ("done", "n/a", "provisional") for step in steps),
                    "ready tracker row has an open step")
    by_tier = collections.Counter(r.get("text_evidence_tier") for r in rows if r["ready_for_human_review"] == "yes")
    require(dict(by_tier) == summary.get("ready_by_text_evidence_tier"), "ready text-evidence tiers disagree")


def build(root, dashboard, capcom=None):
    root = Path(root).resolve()
    sources = {}

    def read(name, relative):
        raw = (root / relative).read_bytes()
        sources[name] = {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}
        return raw

    def document(name, relative):
        value = json.loads(read(name, relative))
        require(isinstance(value, dict), relative + " is not an object")
        return value

    status = document("tracker_status", TRACKER + "STATUS.json")
    manifest = document("tracker_manifest", TRACKER + "RUNNER_INPUTS.json")
    checker_status = document("checker_status", CHECKER + "STATUS.json")
    checker_manifest = document("checker_manifest", CHECKER + "RUNNER_INPUTS.json")
    validate_generation(status, manifest, "readiness-tracker")
    validate_generation(checker_status, checker_manifest, "claim-checker")
    require(instant(status["started_utc"]) >= instant(checker_status["finished_utc"]),
            "tracker predates the available checker generation")
    # The exact checker generation captured by the tracker must still be the one
    # available to this adapter, including same-run uncommitted output files.
    for filename in ("STATUS.json", "RUNNER_INPUTS.json", "PER_CLAIM.json", "SUMMARY.json"):
        relative = CHECKER + filename
        actual = git(root, "hash-object", "--no-filters", "--", relative)
        require(manifest["inputs"].get(relative) == "100644:" + actual,
                "tracker captured a different checker generation: " + filename)
    readiness_inputs = readiness_witness(root, manifest["inputs"])
    readiness_witness(root, checker_manifest["inputs"], "checker")
    freshness = dashboard.get("freshness", {})
    require(freshness.get("claim_receipts", {}).get("state") == "claim_versions_match"
            and not freshness.get("discrepancies"), "current records require a checker/tracker refresh")
    for key, expected in (("tracker_generation", status), ("checker_generation", checker_status)):
        require(freshness.get(key) == expected, "dashboard and Mission generations differ")
    summary = document("tracker_summary", TRACKER + "SUMMARY.json")
    rows = list(csv.DictReader(io.StringIO(read("tracker", TRACKER + "READINESS_BY_ORDER.csv").decode("utf-8-sig"))))
    capcom = capcom or load_capcom(root)
    validate_rows(rows, summary, capcom.brw.STEPS[1:])
    universe = list(csv.DictReader(io.StringIO(read("universe", "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv").decode("utf-8-sig"))))
    require({r["instrument_id"] for r in rows} == {r["id"] for r in universe}, "tracker and identity register differ")
    read("weights", SOURCE + "MISSION_WEIGHTS.csv")  # Require the frozen file before calling weights().
    read("milestones", SOURCE + "APOLLO11_MILESTONES.csv")
    remaining = document("remaining_work", SOURCE + "REMAINING_WORK.json")
    require(remaining.get("not_yet_in_project") == FROZEN_GAP, "frozen census-gap policy changed")
    weights = capcom.weights()
    require(weights == FROZEN_WEIGHTS, "frozen effort weights changed")
    milestones, end = capcom.milestones(), capcom.first_step_hours()
    require(end == 109 + 24 / 60 + 15 / 3600, "Apollo mission endpoint changed")
    require(git(root, "rev-parse", "--is-shallow-repository") == "false", "complete tracker history is required")
    head = git(root, "rev-parse", "HEAD")
    history = capcom.history(head)
    # Retained checkpoints are a regression gate, not a new history inferred
    # from campaign receipt unions or ready-count deltas.
    archived = list(csv.DictReader(io.StringIO(read("historical_baseline", SOURCE + "snapshots/2026-10-30/MISSION_LOG.csv").decode("utf-8-sig"))))
    by_date = {r["date"]: {k: str(v) for k, v in r.items()} for r in history}
    require(all(by_date.get(r["date"]) == r for r in archived), "retained historical Mission checkpoints changed")
    when = status["finished_utc"]
    day = instant(when).date().isoformat()
    latest = capcom.snapshot(rows, weights, FROZEN_GAP, end, milestones, day, status["commit_run"], when)
    require(not history or history[-1]["date"] <= day, "tracker generation predates committed Mission history")
    history = [r for r in history if r["date"] < day] + [latest]
    human = document("human_review", "research/stage19/output/PROGRESS.json")
    human_count = human.get("independently_reviewed_whole_lifecycle_complete")
    require(human_count is None or (isinstance(human_count, int) and not isinstance(human_count, bool) and human_count >= 0),
            "human-review register count is invalid")
    require(0 <= latest["progress"] <= 1 and 0 <= latest["met_hours"] <= end, "modeled progress is outside its domain")
    return {
        "schema": "eo-mission/v1", "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "repository_input_commit": head, "tracker_generation": status, "checker_generation": checker_status,
        "sources": sources, "readiness_inputs": readiness_inputs,
        "model": {"version": "capcom-frozen-weights-v1", "denominator_version": "current-census-plus-frozen-gap-v1",
                  "weights_sha256": sources["weights"]["sha256"], "census_gap": FROZEN_GAP,
                  "orders_goal": latest["orders_goal"], "first_step_hours": end, "history_compatible": True,
                  "interpretation": "Existing frozen model minutes weight done/open tracker steps. The goal is current census plus the frozen 1,314-order modeled gap; the retained APP total is a different measure."},
        "freshness": {"state": "generation_reported", "claim_receipts": "claim_versions_match",
                      "interpretation": "Validated published generation and exact current claim-receipt coverage; this is not verification of every scientific source or legal conclusion."},
        "latest": latest, "history": history, "milestones": milestones,
        "latest_provenance": {"time_field": "tracker finished_utc", "commit_field": "tracker commit_run (input commit)",
                              "history_time_field": "tracker-output first-parent commit time"},
        "human_review": {"published_whole_lifecycle_certifications": human_count, "source": sources["human_review"]["path"],
                         "interpretation": "Separate human-review register; Capcom's legacy human_certified=0 is never an inferred certification count."},
        "limits": ["Modeled work completion is not ready dossiers divided by identities, measured labor, or scientific approval.",
                   "Provisional text steps retain the existing Capcom treatment and never become original-supported evidence.",
                   "Failures preserve the prior successful output; its generation date remains authoritative."]}


def write(root, output, dashboard):
    report = build(root, dashboard)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(report["latest"]))
    writer.writeheader()
    writer.writerows(report["history"])
    (output / "MISSION_LOG.csv").write_text(stream.getvalue(), encoding="utf-8", newline="")
    (output / "MISSION.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def refresh(root, output, dashboard, prior=None):
    """Retain the last good Mission on refusal while the digest reports the hold."""
    import shutil
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    attempted = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        report = write(root, output, dashboard)
        receipt = {"schema": "eo-mission-refresh/v1", "state": "ready", "attempted_utc": attempted,
                   "reason": None, "tracker_generation": report["tracker_generation"],
                   "readiness_inputs": report["readiness_inputs"]}
    except (OSError, ValueError, KeyError, TypeError, csv.Error, subprocess.CalledProcessError) as exc:
        # The runner supplies its immutable prior-output backup. Copying these
        # exact bytes retains the old generation and its provenance/date.
        if prior is not None:
            for name in ("MISSION.json", "MISSION_LOG.csv"):
                source = Path(prior) / name
                if source.is_file() and source.resolve() != (output / name).resolve():
                    shutil.copyfile(source, output / name)
        receipt = {"schema": "eo-mission-refresh/v1", "state": "pending", "attempted_utc": attempted,
                   "reason": str(exc), "tracker_generation": dashboard.get("freshness", {}).get("tracker_generation"),
                   "readiness_inputs": None}
    (output / "MISSION_REFRESH.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt
