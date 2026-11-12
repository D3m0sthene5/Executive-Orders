"""Lind fix reach: after a claim-kit rebuild, how many of the 87 back-test failures now hold the input their diagnosis
says was missing? Zero tokens; reads committed outputs only.

For each failed order in the Larrey back-test (Papinian u01b/u02/u03, Haloander u01-u03) it compares the dossier the
producer received (frozen) with the current claim-kit features (jobs/llull/kit_features.load) and the current gates,
then tallies by the Respondendi diagnosis (final_primary_cause) and by the Accursius fix that targeted the order.

A gained record is a lead, not a success: a producer must still use it and two blind reviewers uphold it. The output
bounds how much yield the rebuild can recover; the stage 0 batch measures how much it does.

Usage: python3 -I research/lind/stage0/fix_reach.py [--out FIX_REACH.json]
"""

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "jobs/larrey-triage"))
sys.path.insert(0, str(REPO / "jobs/llull"))
import kit_features as kf  # noqa: E402
import larrey  # noqa: E402

DIAGNOSIS = REPO / "research/excavator/claude-respondendi-2026-11-10/DIAGNOSIS.csv"
GATES = REPO / "jobs/larrey-triage/output/GATES.jsonl"
FAILED = ("failed_after_dispatch", "dispatch_blocked")
# Orders each Accursius fix names as reached (research/excavator/claude-accursius-2026-11-10/REPORT.md); F7 fixed
# artifacts that alone supply no basis, and EO 13204's F4 records are leads only.
ACCURSIUS = {
    "F3": "10624 11225 12661 13329 13505 13647 13748 14051 14191 14233 14318",
    "F4": "8790 8649 13354 14231", "F5": "12178 12378 12379 13013 13552 7621 10816 11728 11816 13024 13820",
    "F5_term": "13116 13064", "F6": "4770 2145 3761 4041",
    "F7_artifact_only": "7573 8109 9446 10195 11202 11575 11813 12072 13294", "F4_lead_only": "13204",
}


def gained(old, new):
    out = sorted(set(new.get("basis_kinds", [])) - set(old.get("basis_kinds", [])))
    if new.get("current_leads", 0) > old.get("current_leads", 0):
        out.append("more_current_leads")
    for k in ("working_text_basis", "original_acceptable", "actor_text"):
        if new.get(k) and not old.get(k):
            out.append(k)
    if old.get("page_check_owed") and not new.get("page_check_owed"):
        out.append("page_check_cleared")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent / "FIX_REACH.json"))
    a = ap.parse_args(argv)
    und = larrey.undecided_outcomes(REPO)
    cur = kf.load(REPO)
    gates = {}
    for line in GATES.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("route") == "undecided_full":
            gates[r["instrument_id"]] = r
    diag = {r["instrument_id"]: r for r in csv.DictReader(DIAGNOSIS.open(encoding="utf-8"))}
    fix = {f"EO:{n}": k for k, v in ACCURSIUS.items() for n in v.split()}
    rows, tally = [], collections.Counter()
    for iid, o in sorted(und.items()):
        if o["outcome"] not in FAILED:
            continue
        g = gained(o["features"], cur.get(iid, {}))
        gate = gates.get(iid, {})
        row = {"instrument_id": iid, "wave": o["wave"], "outcome": o["outcome"],
               "cause": diag.get(iid, {}).get("final_primary_cause", "undiagnosed"),
               "accursius_fix": fix.get(iid, ""), "gained": g,
               "now_pass": bool(gate.get("pass")), "now_pass_hard": bool(gate.get("pass_hard"))}
        rows.append(row)
        tally[(row["cause"], bool(g))] += 1
    summary = {
        "claim_kit_finished_utc": json.loads((REPO / "jobs/claim-kit/output/STATUS.json").read_text())["finished_utc"],
        "failures": len(rows), "with_any_gained_record": sum(1 for r in rows if r["gained"]),
        "by_cause": {f"{c}|{'gained' if g else 'none'}": n for (c, g), n in sorted(tally.items())},
        "named_by_an_accursius_fix": sum(1 for r in rows if r["accursius_fix"]),
        "named_and_gained": sum(1 for r in rows if r["accursius_fix"] and r["gained"]),
    }
    Path(a.out).write_text(json.dumps({"summary": summary, "orders": rows}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
