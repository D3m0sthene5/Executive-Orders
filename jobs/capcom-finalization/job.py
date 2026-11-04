"""One-off exact accounting and the existing Capcom builder; no research rerun."""
import collections
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

START = time.monotonic()
BASELINE = "a3bfac64b3e1c43400a8ed8c744419eb17f6e2e6"
ROOT = Path(os.environ["REPO_ROOT"]).resolve()
OUT = Path(os.environ["OUTPUT_DIR"]).resolve()
SOURCE = ROOT / "research/progress/remaining-work"
TRACKER = "jobs/readiness-tracker/output/"
CHECKER = "jobs/claim-checker/output/"
PINS = {}
OUT.mkdir(parents=True, exist_ok=True)

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def read(rel):
    data = (ROOT / rel).read_bytes()
    PINS[rel] = hashlib.sha256(data).hexdigest()
    return data.decode("utf-8-sig")

def document(rel):
    return json.loads(read(rel))

def table(text):
    return list(csv.DictReader(io.StringIO(text)))

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

head = git("rev-parse", "HEAD")
require(git("rev-parse", "--is-shallow-repository") == "false",
        "Complete first-parent history is required")
git("merge-base", "--is-ancestor", BASELINE, head)
tracker_status = document(TRACKER + "STATUS.json")
checker_status = document(CHECKER + "STATUS.json")
for name, status in (("readiness-tracker", tracker_status), ("claim-checker", checker_status)):
    require(status.get("job") == name and status.get("result") == "succeeded"
            and status.get("exit_code") == 0, name + " receipt is not successful")
require(instant(tracker_status["started_utc"]) >= instant(checker_status["finished_utc"]),
        "Tracker predates the available checker generation")
require(instant(tracker_status["finished_utc"]).date().isoformat() >= "2026-11-04",
        "Tracker still predates Tribonian")

csv_path = TRACKER + "READINESS_BY_ORDER.csv"
rows = table(read(csv_path))
baseline = table(git("show", BASELINE + ":" + csv_path))
summary = document(TRACKER + "SUMMARY.json")
current = {r["instrument_id"]: r for r in rows}
require(len(current) == len(rows) == summary["orders_total"], "Tracker row count or uniqueness mismatch")
ready = {i for i, r in current.items() if r["ready_for_human_review"] == "yes"}
before = {r["instrument_id"] for r in baseline if r["ready_for_human_review"] == "yes"}
require(len(ready) == summary["ready_for_human_review"], "Tracker CSV and summary readiness disagree")
require(sum(r["provisional_status"] in ("yes", "no") for r in rows)
        == summary["orders_with_provisional_status"], "Tracker CSV and summary status counts disagree")

gate_rel = "research/stage19/code/claim_gate.py"
read(gate_rel)
gate = load_module("retained_stage19_gate", ROOT / gate_rel)
checker = document(CHECKER + "PER_CLAIM.json")
receipts = collections.defaultdict(list)
for receipt in checker["claims"]:
    key = (receipt.get("file"), receipt.get("line"), receipt.get("instrument_id"), receipt.get("claim_sha256"))
    receipts[key].append(receipt)

campaign = []
files = sorted((ROOT / "research/readiness/claims").glob("claude-2026-11-04-tribonian-*.jsonl"))
require(files, "No published Tribonian files")
for path in files:
    rel = path.relative_to(ROOT).as_posix()
    for number, line in enumerate(read(rel).splitlines(), 1):
        if not line.strip():
            continue
        claim = json.loads(line)
        iid = claim["instrument_id"]
        sha = gate.claim_sha(claim)
        matches = receipts[(rel, number, iid, sha)]
        receipt = matches[0] if len(matches) == 1 else {}
        campaign.append({
            "file": rel, "line": number, "instrument_id": iid, "claim_sha256": sha,
            "exact_receipt_matches": len(matches),
            "checker_all_passed": receipt.get("all_checks_passed"),
            "effective_for_tracker": receipt.get("effective_for_tracker"),
            "text_evidence_tier": receipt.get("text_evidence_tier"),
            "gate_errors": receipt.get("gate_errors", []),
            "checker_failures": receipt.get("failures", []),
            "ready_before": iid in before, "ready_now": iid in ready,
            "tracker_blockers": current.get(iid, {}).get("blockers"),
        })
ids = {r["instrument_id"] for r in campaign}
require(ids <= current.keys(), "Published campaign orders absent from tracker")
require(campaign, "No published Tribonian claim lines")
# Missing or failing members are reported; they do not suppress the verified majority.
for row in campaign:
    require(not row["ready_now"] or (
        row["exact_receipt_matches"] == 1
        and row["checker_all_passed"] is True
        and row["effective_for_tracker"] is True),
        "Ready campaign member lacks an exact effective passing receipt: " + row["instrument_id"])

gained, lost = ready - before, before - ready
report = {
    "head": head, "baseline": BASELINE, "before_ready": len(before), "after_ready": len(ready),
    "net_change": len(ready) - len(before), "campaign_files": len(files),
    "campaign_claim_lines": len(campaign), "campaign_distinct_orders": len(ids),
    "campaign_exact_receipt_lines": sum(r["exact_receipt_matches"] == 1 for r in campaign),
    "campaign_already_ready": sorted(ids & before), "campaign_newly_ready": sorted(ids & gained),
    "campaign_ready_now": sorted(ids & ready),
    "campaign_blocked": [r for r in campaign if not r["ready_now"]],
    "campaign_checker_passed_lines": sum(r["checker_all_passed"] is True for r in campaign),
    "campaign_text_tiers": dict(collections.Counter(r["text_evidence_tier"] for r in campaign)),
    "previously_ready_lost": sorted(lost), "unrelated_gains": sorted(gained - ids),
    "unrelated_losses": sorted(lost - ids),
    "tracker_status": tracker_status, "checker_status": checker_status,
}
(OUT / "CAMPAIGN_ROWS.json").write_text(json.dumps(campaign, indent=2) + "\n", encoding="utf-8")

# Existing source/weights are retained and pinned, never refrozen.
for name in ("MISSION_WEIGHTS.csv", "APOLLO11_MILESTONES.csv", "REMAINING_WORK.json"):
    rel = "research/progress/remaining-work/" + name
    read(rel)
    shutil.copyfile(ROOT / rel, OUT / name)
for name in ("build_mission_log.py", "build_remaining_work.py"):
    read("research/progress/remaining-work/" + name)
sys.path.insert(0, str(SOURCE))
capcom = load_module("retained_capcom", SOURCE / "build_mission_log.py")
capcom.HERE = OUT
capcom.WEIGHTS = OUT / "MISSION_WEIGHTS.csv"
capcom.MILESTONES = OUT / "APOLLO11_MILESTONES.csv"
capcom.REF = head
capcom.main()

mission = table((OUT / "MISSION_LOG.csv").read_text(encoding="utf-8"))
last = mission[-1]
latest_commit = git("log", "--first-parent", "-1", "--format=%H", head, "--", csv_path)
require(last["commit"] == latest_commit[:10], "Mission omitted the latest tracker checkpoint")
require(int(last["ready_for_human_review"]) == len(ready)
        and int(last["orders_in_census"]) == len(rows), "Mission and current tracker disagree")
historical = table(read("research/progress/remaining-work/snapshots/2026-10-30/MISSION_LOG.csv"))
by_date = {r["date"]: r for r in mission}
require(all(by_date.get(r["date"]) == r for r in historical),
        "A retained historical Mission checkpoint changed")
human_progress = document("research/stage19/output/PROGRESS.json")
report.update({
    "latest_tracker_commit": latest_commit, "mission_last_row": last,
    "historical_checkpoints_preserved": len(historical), "input_sha256": PINS,
    "stage19_progress_separate": human_progress,
    "mission_log_sha256": hashlib.sha256((OUT / "MISSION_LOG.csv").read_bytes()).hexdigest(),
    "finished_utc": datetime.now(timezone.utc).isoformat(),
    "elapsed_seconds": round(time.monotonic() - START, 3), "model_tokens": None,
    "scope": "Exact accounting and existing Capcom builder; no scientific production",
})
(OUT / "RECONCILIATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
