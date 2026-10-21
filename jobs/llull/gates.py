#!/usr/bin/env python3
"""Fail-closed execution gate for a preregistered, counted research probe.

This checks the recorded test contract. It does not decide legal propositions,
review quality, status, or authorization. Missing tests remain untested.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


class GateStopped(RuntimeError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__("gate %s: %s" % (receipt.get("gate_id"), receipt["status"]))


def number(value, integer=False):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value >= 0 and (not integer or int(value) == value))


def evaluate_gate(contract, observation):
    conditions = []
    raw_contract, raw_observation = contract, observation

    def record(name, state, reason, observed=None, required=None):
        conditions.append({"condition": name, "status": state, "reason": reason,
                           "observed": observed, "required": required})

    if not isinstance(contract, dict) or not isinstance(observation, dict):
        record("shape", "untested", "contract and observation must be objects")
        contract = contract if isinstance(contract, dict) else {}
        observation = observation if isinstance(observation, dict) else {}
    if contract.get("schema") != "llull.gate-contract/v1" or observation.get("schema") != "llull.gate-observation/v1":
        record("schema", "untested", "unknown or missing contract/observation schema")
    if not contract.get("gate_id") or contract.get("gate_id") != observation.get("gate_id"):
        record("identity", "untested", "observation must name this exact gate")
    plants = contract.get("planted_defects")
    if plants is not None:
        p = observation.get("planted_defects") or {}
        if not isinstance(plants, dict) or not isinstance(p, dict):
            record("plant_shape", "untested", "planted-defect counts must be objects")
            plants = plants if isinstance(plants, dict) else {}
            p = p if isinstance(p, dict) else {}
        required, minimum = plants.get("required"), plants.get("minimum_caught")
        present, reviewed, caught = p.get("present"), p.get("reviewed"), p.get("caught")
        valid_contract = all(number(x, integer=True) for x in (required, minimum)) and 0 < required and minimum <= required
        valid_counts = all(number(x, integer=True) for x in (present, reviewed, caught))
        if not valid_contract or not valid_counts or not 0 <= caught <= reviewed <= present:
            record("planted_defects", "untested", "invalid or missing planted-defect counts", p, plants)
        elif present != required or reviewed != required:
            record("planted_defects", "untested", "the exact planned plant cohort was not planted and reviewed", p, plants)
        else:
            record("planted_defects", "pass" if caught >= minimum else "fail", "minimum catch count on the required test", p, plants)
    metrics = observation.get("metrics", {})
    if not isinstance(metrics, dict):
        record("metric_shape", "untested", "metrics must be an object")
        metrics = {}
    for key, comparison in (("minimums", lambda x, y: x >= y), ("maximums", lambda x, y: x <= y)):
        limits = contract.get(key, {})
        if not isinstance(limits, dict):
            record(key, "untested", "thresholds must be an object")
            continue
        for metric, threshold in limits.items():
            value = metrics.get(metric)
            if not number(threshold) or not number(value):
                record(metric, "untested", "missing or invalid measured value/threshold", value, threshold)
            else:
                record(metric, "pass" if comparison(value, threshold) else "fail", key, value, threshold)
    if not conditions:
        record("contract", "untested", "an empty contract cannot pass")
    status = "untested" if any(c["status"] == "untested" for c in conditions) else (
        "fail" if any(c["status"] == "fail" for c in conditions) else "pass")
    return {"schema": "llull.gate-receipt/v1", "gate_id": contract.get("gate_id"), "status": status,
            "may_continue": status == "pass", "conditions": conditions,
            "contract_sha256": digest(raw_contract), "observation_sha256": digest(raw_observation)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_evidence(observation, repo):
    """Verify bounded repository-relative evidence files; never fetch or follow outside links."""
    root, errors = Path(repo).resolve(), []
    if not isinstance(observation, dict):
        return ["observation must be an object"]
    evidence = observation.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return ["observation needs at least one pinned evidence file"]
    for entry in evidence:
        if not isinstance(entry, dict):
            errors.append("invalid evidence record")
            continue
        path = entry.get("path", "")
        if not isinstance(path, str):
            errors.append("evidence path must be a string")
            continue
        full = (root / path).resolve()
        if not path or Path(path).is_absolute() or ".." in Path(path).parts or not full.is_relative_to(root):
            errors.append("evidence path must stay inside the repository")
        elif not full.is_file():
            errors.append("evidence file missing: " + path)
        elif hashlib.sha256(full.read_bytes()).hexdigest() != entry.get("sha256"):
            errors.append("evidence hash mismatch: " + path)
    return errors


def require_gate(contract, observation):
    receipt = evaluate_gate(contract, observation)
    if not receipt["may_continue"]:
        raise GateStopped(receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--contract", required=True)
    parser.add_argument("--observation", required=True)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--out")
    parser.add_argument("--run", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        contract = json.loads(Path(args.contract).read_text())
        observation = json.loads(Path(args.observation).read_text())
        receipt = evaluate_gate(contract, observation)
        errors = verify_evidence(observation, args.repo)
        receipt["evidence_errors"] = errors
        if errors:
            receipt.update(status="untested", may_continue=False)
        text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(text)
        print(text, end="")
        if not receipt["may_continue"]:
            return 5
        return subprocess.run(args.run, check=False).returncode if args.run else 0
    except (OSError, ValueError, TypeError) as exc:
        print("gate untested: " + str(exc), file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
