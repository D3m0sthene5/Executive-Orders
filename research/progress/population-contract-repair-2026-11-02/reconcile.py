"""Reproduce the failed refresh and check the already-merged PR119 delta.

Read-only engineering audit; this does not adopt statuses or review legal claims.
Run from any directory with Python 3.10+; all inputs are retained Git records.
"""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
BASE = "f07b023133640f288fd44c10c5176888c49f23e2"
MERGE = "c469d94d796a65a2779ef857156903774b0fbda9"
CONTRACT_PATH = "jobs/claim-kit/population_contract.json"
spec = importlib.util.spec_from_file_location("population", REPO / "jobs/claim-kit/population.py")
population = importlib.util.module_from_spec(spec)
spec.loader.exec_module(population)


def git_bytes(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=REPO)


def main():
    old = json.loads(git_bytes(BASE, CONTRACT_PATH))
    try:
        population.validate_inputs(REPO, old)
    except ValueError as exc:
        assert str(exc) == "Current status rows differ from independently pinned accepted inputs"
        failure = str(exc)
    else:
        raise AssertionError("Original production failure no longer reproduced")
    current = json.loads((REPO / CONTRACT_PATH).read_text())
    assert current["historical_status_baseline"] == old["historical_status_baseline"]
    assert current["census"] == old["census"]
    assert current["accepted_additions"][:2] == old["accepted_additions"]
    assert len(current["accepted_additions"]) == 4
    checks = []
    adopted = set()
    for entry, expected_count in zip(current["accepted_additions"][2:], (174, 714)):
        assert entry["accepted_in_main"] == MERGE and entry["adoption_pr"] == 119
        for pin in [entry["rows"], *entry["authorization_pins"]]:
            data = (REPO / pin["path"]).read_bytes()
            assert data == git_bytes(MERGE, pin["path"]), pin["path"]
            assert population.sha(data) == pin["sha256"], pin["path"]
        row_path = REPO / entry["rows"]["path"]
        rows = list(csv.DictReader(row_path.open(encoding="utf-8", newline="")))
        ids = {row["instrument_id"] for row in rows}
        assert len(rows) == len(ids) == entry["count"] == expected_count
        assert not ids & adopted
        adopted.update(ids)
        verification = json.loads(row_path.with_name("VERIFICATION.json").read_text())
        upheld = {row["instrument_id"] for lot in verification["lots"].values()
                  for row in lot["upheld"]}
        assert ids <= upheld
        held_path = row_path.with_name("COORDINATOR_HOLDS.json")
        holds = json.loads(held_path.read_text()) if held_path.exists() else []
        assert not ids & {row["instrument_id"] for row in holds}
        assert not ids & {"EO:370", "EO:3031"}
        checks.append({"rows": entry["rows"]["path"], "count": len(rows),
                       "exact_merged_bytes": True, "individually_upheld": True,
                       "coordinator_holds_excluded": len(holds)})
    checked = population.validate_inputs(REPO)
    assert checked["historical_decided"] == 3359
    assert checked["authorized_additions"] == 932
    assert checked["decided"] == 4291
    print(json.dumps({"schema": "eo-population-contract-repair-audit/v1",
                      "failed_generation": BASE, "adoption_merge": MERGE,
                      "original_error": failure, "waves": checks,
                      "validated": {k: v for k, v in checked.items() if k != "statuses"},
                      "scientific_adoptions": 0, "canonical_rows_changed": 0}, indent=2))


if __name__ == "__main__":
    main()
