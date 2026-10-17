"""Compare the final Opus LFS release with the Stage 17 interim import.

Usage: python research/progress/reconcile_opus_final.py STAGE17.sqlite OPUS_FINAL.zip
"""

import argparse
import hashlib
import json
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("database", type=Path)
parser.add_argument("opus_release", type=Path)
args = parser.parse_args()
db = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
zip_path = args.opus_release
zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
expected_zip_sha = "95b41d81fb3ef7a5b6b5a24db247124f6a6499ba899d7d69a7841192eeaeadf7"
if zip_sha != expected_zip_sha:
    raise SystemExit("Unexpected Opus final ZIP SHA-256")
with zipfile.ZipFile(zip_path) as archive:
    base = "OPUS_STAGE11_FINITE_STATUS_DELTA/"
    accepted = [json.loads(x) for x in archive.read(base + "STAGE11_ACCEPTED.jsonl").splitlines() if x]
    status_records = [json.loads(x) for x in archive.read(base + "STAGE11_STATUS_RECORDS.jsonl").splitlines() if x]
    accounting = json.loads(archive.read(base + "ACCOUNTING.json"))
ids = {x["instrument_id"] for x in accepted}
assert len(ids) == len(accepted) == 597
included = {x[0] for x in db.execute("SELECT id FROM instruments WHERE include_proxy=1")}
prior = {x[0]: x[1] for x in db.execute("SELECT instrument_id, substantive_status FROM opus_checkpoint2_import")}
accepted_map = {x["instrument_id"]: x["final_substantive_effect"] for x in accepted}
missing_from_final = set(prior) - ids
changed_prior = {x: (y, accepted_map[x]) for x, y in prior.items() if x in accepted_map and accepted_map[x] != y}
new = ids - set(prior)
result = {
    "schema": "eo-opus-final-reconciliation/v1",
    "opus_release_path": "releases/opus_stage11/OPUS_STAGE11_FINITE_STATUS_DELTA.zip",
    "opus_release_sha256": zip_sha,
    "stage17_database_sha256": "c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1",
    "final_accepted": len(ids),
    "final_breakdown": dict(Counter(accepted_map.values())),
    "stage17_interim_import": len(prior),
    "interim_missing_from_final": sorted(missing_from_final),
    "interim_verdict_changes": changed_prior,
    "new_final_ids": len(new),
    "new_final_breakdown": dict(Counter(accepted_map[x] for x in new)),
    "final_accepted_not_included_in_stage17": sorted(ids - included),
    "final_accepted_legacy_already_determinate": [
        x for x in sorted(new) if db.execute(
            "SELECT original_legacy_status FROM instruments WHERE id=?", (x,)
        ).fetchone() not in (("indeterminate",),)
    ],
    "final_status_records": len(status_records),
    "first_cause_states": dict(Counter(x.get("historical_causes") for x in status_records if x["instrument_id"] in ids)),
    "accounting_denominator": accounting["denominator"],
    "stage17_denominator": len(included),
    "combined_stage17_working_decisions": 2515 + len(ids),
    "combined_stage17_working_coverage_percent": (2515 + len(ids)) / len(included) * 100,
    "canonical_stage17_database_includes_final_57": False,
    "interpretation": "The final Opus release is retrievable on GitHub, but Stage 17's canonical database contains only the earlier 540 imported decisions. The 57 later decisions are an additive verified overlay, not yet a rebuilt authoritative SQLite release. None of the Opus 597 records establishes a historical first cause."
}
if missing_from_final or changed_prior or len(new) != 57 or ids - included:
    raise SystemExit("Opus release differs from the expected additive 57-decision overlay")
target = Path(__file__).parent / "OPUS_FINAL_RECONCILIATION.json"
target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
