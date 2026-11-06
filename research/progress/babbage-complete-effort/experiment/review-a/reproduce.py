#!/usr/bin/env python3
"""Independent mechanical reproduction for the hash-pinned Arm A result."""
import hashlib
import json
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
INPUT = EXP / "inputs/o25-preflight-only.json"
RESULT = EXP / "arm-a/result.json"
EXPECTED = {
    "../CONTRACT.md": "4131f46fbf7976a18460d90231fa576a35c7c532680f89a8975ed8a88c6f8d83",
    "inputs/o25-preflight-only.json": "9293d5f0e75ab4590a607d81a8df3caeb21a87151c9c0f2daf9c33d5a267b27f",
    "arm-a/baseline_route.py": "b5cae494e121ab058b8d73a718f352ff7d93f12c73f2fd62dede511b8fc224d1",
    "arm-a/result.json": "90a49da7d571f92a51a023c06dfa2d5a88ac16b95ebe57802397e574e6f0403a",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

hashes = {
    "../CONTRACT.md": sha(EXP / "CONTRACT.md"),
    "inputs/o25-preflight-only.json": sha(INPUT),
    "arm-a/baseline_route.py": sha(EXP / "arm-a/baseline_route.py"),
    "arm-a/result.json": sha(RESULT),
}
assert hashes == EXPECTED, {"expected": EXPECTED, "actual": hashes}
source = json.loads(INPUT.read_text(encoding="utf-8"))
actual = json.loads(RESULT.read_text(encoding="utf-8"))
preflight = source["preflight"]
expected_members = []
expected_groups = OrderedDict()
for iid, payload in preflight.items():
    matching = [t for t in payload.get("mechanical_tasks", [])
                if t.get("kind") == "operative_current_law"]
    expected_members.append({
        "instrument_id": iid,
        "route": "route_source_preparation" if matching else "no_known_declared_prerequisite",
        "member_tasks": matching,
    })
    for task in matching:
        key = task.get("shared_key")
        gkey = (iid, task.get("kind"), key) if key == "{}" else (task.get("kind"), key)
        if gkey not in expected_groups:
            expected_groups[gkey] = {
                "kind": task.get("kind"), "shared_key": key,
                "grouped_by_shared_key": key != "{}",
                "affected_orders": [], "member_tasks": [],
            }
        group = expected_groups[gkey]
        if iid not in group["affected_orders"]:
            group["affected_orders"].append(iid)
        group["member_tasks"].append(task)

actual_members = actual.get("members", [])
actual_groups = actual.get("groups", [])
member_match = actual_members == expected_members
group_match = actual_groups == list(expected_groups.values())
all_tasks = sum(len(m["member_tasks"]) for m in expected_members)
route_counts = {}
for member in expected_members:
    route_counts[member["route"]] = route_counts.get(member["route"], 0) + 1

# Boundary wording is checked literally in the result, not imputed from the contract.
note = actual.get("scope_note", "")
boundary = {
    "mechanical_prerequisite_only": "Mechanical assignment-prerequisite routing only" in note,
    "groups_not_source_identity_or_shared_legal_question":
        "neither shared source nor shared legal question" in note,
    "explicit_no_source_feasibility_finding": "source-feasibility" in note,
    "explicit_no_legal_inference": "no legal inference" in note.lower(),
    "explicit_no_dispatch_approval": "dispatch approval" in note.lower(),
}

report = {
    "schema": "arm-a-independent-engineering-review/v1",
    "disposition": "REJECT_BOUNDARY_WORDING",
    "hash_pins": hashes,
    "mechanical_check": {
        "input_members": len(preflight),
        "result_members": len(actual_members),
        "member_order_and_route_exact": member_match,
        "expected_matching_task_count": all_tasks,
        "matching_task_count_by_member": {m["instrument_id"]: len(m["member_tasks"]) for m in expected_members},
        "exact_matching_task_payloads_and_per_member_order": member_match,
        "expected_group_count": len(expected_groups),
        "result_group_count": len(actual_groups),
        "exact_literal_key_groups_and_complete_payloads": group_match,
        "empty_key_groups_are_member_scoped": all(
            g["shared_key"] != "{}" or len(g["affected_orders"]) == 1
            for g in actual_groups
        ),
        "route_counts": route_counts,
    },
    "boundary_wording_check": boundary,
    "findings": [
        {
            "severity": "blocking_for_exact_output_acceptance",
            "finding": "The result scope_note says this is mechanical assignment-prerequisite routing and disclaims group implications for shared source/legal question, but it does not explicitly say the output is not a source-feasibility finding or dispatch approval. The contract requires routing never be represented as either.",
            "correction": "Add a concise scope sentence to the result stating that routing is not a source-feasibility/legal-readiness finding and does not approve dispatch or completed dossier work; regenerate the result and update the hash pin."
        },
        {
            "severity": "accounting_limit",
            "finding": "Arm A reports 0.030884 seconds for final reusable-script execution, 4 tool interactions and 4 shell commands, with provider tokens and cash null. Its own scope says earlier bounded input inspection was not timed. The prescribed one-time development/briefing/examiner/setup work is not quantified in these four allowed files, so recurring-cost metadata cannot establish full one-time cost or savings.",
            "correction": "Keep one-time and recurring costs separate; record unmeasured setup/inspection as unmeasured rather than treating the final script runtime as total Arm A cost."
        }
    ],
    "limits": [
        "Engineering comparison only; no legal or scientific source examination or certification.",
        "No claim is made about the truth, sufficiency, currency, custody, identity, or legal effect of any source."
    ],
    "reviewer_accounting": {
        "configured_model": "gpt-6-luna",
        "provider_tokens": None,
        "cash_usage": None,
        "tool_interactions": 8,
        "shell_command_invocations_attempted": 4,
        "shell_commands_executed": 3,
        "elapsed_wall_seconds_approx": 144.0,
        "elapsed_scope": "Reviewer tool wall time, summed from reported exec/wait durations; approximate and includes transport delay."
    },
    "arm_a_reported_accounting": actual.get("accounting"),
    "arm_a_reported_elapsed_seconds_monotonic": actual.get("elapsed_seconds_monotonic"),
    "arm_a_reported_utc_started": actual.get("utc_started"),
    "arm_a_reported_utc_completed": actual.get("utc_completed"),
}
assert len(preflight) == 30
assert member_match
assert group_match
assert report["mechanical_check"]["empty_key_groups_are_member_scoped"]
(HERE / "REVIEW.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "disposition": report["disposition"],
    "members": len(preflight),
    "matching_tasks": all_tasks,
    "groups": len(expected_groups),
    "routes": route_counts,
    "exact_members": member_match,
    "exact_groups": group_match,
    "boundary_wording": boundary,
    "review": str(HERE / "REVIEW.json"),
}, indent=2))
