"""Verify and reconcile the complete Opus LFS release with Stage 17.

Usage: python research/progress/reconcile_opus_complete.py STAGE17.sqlite COMPLETE_OPUS.zip INTERIM_OPUS.zip
"""

import argparse
import csv
import hashlib
import json
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("database", type=Path)
parser.add_argument("complete_release", type=Path)
parser.add_argument("interim_release", type=Path)
args = parser.parse_args()

complete_sha = hashlib.sha256(args.complete_release.read_bytes()).hexdigest()
expected = "1fbbd45e9a8846a955cbdcaa5bba2b0f138c10c80049c5bb6063197f6ac62d47"
if complete_sha != expected:
    raise SystemExit("Complete Opus LFS payload SHA-256 mismatch")
conn = sqlite3.connect(f"file:{args.database.resolve().as_posix()}?mode=ro", uri=True)
included = {x[0] for x in conn.execute("SELECT id FROM instruments WHERE include_proxy=1")}
stage17_import = {x[0]: x[1] for x in conn.execute(
    "SELECT instrument_id, substantive_status FROM opus_checkpoint2_import"
)}

prefix = "OPUS_STAGE11_FINITE_STATUS_DELTA/"
with zipfile.ZipFile(args.complete_release) as z:
    if z.testzip() is not None:
        raise SystemExit("Complete Opus ZIP CRC test failed")
    manifest = json.loads(z.read(prefix + "MANIFEST.json"))
    accounting = json.loads(z.read(prefix + "ACCOUNTING.json"))
    complete = [json.loads(x) for x in z.read(prefix + "STAGE11_ACCEPTED.jsonl").splitlines() if x]
    records = [json.loads(x) for x in z.read(prefix + "STAGE11_STATUS_RECORDS.jsonl").splitlines() if x]
    listed = {x["path"]: x for x in manifest["files"]}
    zip_files = [x for x in z.namelist() if x.startswith(prefix) and not x.endswith("/") and x != prefix + "MANIFEST.json"]
    actual_paths = {x[len(prefix):] for x in zip_files}
    omitted = set(listed) - actual_paths
    unusual = actual_paths - set(listed)
    omitted_media = {x for x in omitted if x.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))}
    omitted_text = omitted - omitted_media
    renamed = {x: x.replace("ΓÇô", "–") for x in unusual}
    if {v for v in renamed.values()} != omitted_text:
        raise SystemExit("Unexpected unlisted or missing non-media entries")
    hash_failures = []
    for rel in actual_paths:
        target = renamed.get(rel, rel)
        entry = listed.get(target)
        if entry is None:
            hash_failures.append(rel + ": no manifest entry")
            continue
        data = z.read(prefix + rel)
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            hash_failures.append(rel + ": size or SHA-256 mismatch")
    if hash_failures:
        raise SystemExit("Included file hash failures: " + repr(hash_failures[:10]))

with zipfile.ZipFile(args.interim_release) as z:
    interim = [json.loads(x) for x in z.read(prefix + "STAGE11_ACCEPTED.jsonl").splitlines() if x]

complete_map = {x["instrument_id"]: x["final_substantive_effect"] for x in complete}
interim_map = {x["instrument_id"]: x["final_substantive_effect"] for x in interim}
if len(complete_map) != len(complete) or len(interim_map) != len(interim):
    raise SystemExit("Duplicate accepted IDs")
changed_interim = {x: (status, complete_map.get(x)) for x, status in interim_map.items() if complete_map.get(x) != status}
changed_stage17 = {x: (status, complete_map.get(x)) for x, status in stage17_import.items() if complete_map.get(x) != status}
new_since_interim = set(complete_map) - set(interim_map)
new_since_stage17 = set(complete_map) - set(stage17_import)
not_included = set(complete_map) - included
prior_determinate = [x for x in new_since_stage17 if conn.execute(
    "SELECT original_legacy_status FROM instruments WHERE id=?", (x,)
).fetchone() != ("indeterminate",)]
record_map = {x["instrument_id"]: x for x in records}
causes = Counter(record_map[x].get("historical_causes") for x in complete_map)
new_with_stage16_episode = sorted(x for x in new_since_stage17 if conn.execute(
    "SELECT 1 FROM legal_episode WHERE instrument_id=? LIMIT 1", (x,)
).fetchone())
new_with_stage17_provision = sorted(x for x in new_since_stage17 if conn.execute(
    "SELECT 1 FROM stage17_provision WHERE instrument_id=? LIMIT 1", (x,)
).fetchone())
v3 = {x[0]: x[1] for x in conn.execute("SELECT id, normative_status FROM v3_effect_assessments")}
stage17_assessment = {x[0]: x[1] for x in conn.execute(
    "SELECT instrument_id, normative_status FROM stage17_assessment"
)}
v3_overlap = {x: v3[x] for x in sorted(set(complete_map) & set(v3))}
stage17_overlap = {x: stage17_assessment[x] for x in sorted(set(complete_map) & set(stage17_assessment))}

if (len(complete), len(interim), len(stage17_import), len(new_since_interim),
        len(new_since_stage17)) != (844, 597, 540, 247, 304):
    raise SystemExit("Unexpected Opus acceptance counts")
if changed_interim or changed_stage17 or not_included or prior_determinate:
    raise SystemExit("Unexpected overlap, status change, or excluded identity")
if accounting["newly_accepted"] != 844 or accounting["patched_rows"] != 844:
    raise SystemExit("Accounting disagreement")

result = {
    "schema": "eo-opus-complete-reconciliation/v1",
    "date": "2026-10-17",
    "git_path": "releases/opus_stage11_complete/OPUS_STAGE11_FINITE_STATUS_DELTA_COMPLETE.zip",
    "complete_zip_bytes": args.complete_release.stat().st_size,
    "complete_zip_sha256": complete_sha,
    "zip_crc_test": "passed",
    "zip_file_entries_including_manifest": len(actual_paths) + 1,
    "manifest_file_entries": len(listed),
    "included_manifest_files_sha256_verified": len(actual_paths),
    "manifest_media_entries_not_in_zip": len(omitted_media),
    "manifest_media_extensions": dict(sorted(Counter(Path(x).suffix.lower() for x in omitted_media).items())),
    "zip_filename_encoding_aliases_resolved": len(renamed),
    "included_file_hash_failures": 0,
    "original_media_companion_on_github": False,
    "complete_accepted": len(complete_map),
    "complete_status_records": len(records),
    "complete_status_record_decision_states": dict(Counter(x.get("decision_state") for x in records)),
    "complete_status_records_with_text_obtained": sum(x.get("text_obtained") is True for x in records),
    "complete_yes_no": dict(sorted(Counter(complete_map.values()).items())),
    "interim_accepted": len(interim_map),
    "stage17_interim_import": len(stage17_import),
    "new_vs_interim": len(new_since_interim),
    "new_vs_stage17_canonical": len(new_since_stage17),
    "new_vs_stage17_yes_no": dict(sorted(Counter(complete_map[x] for x in new_since_stage17).items())),
    "new_with_stage16_structured_episode": new_with_stage16_episode,
    "new_with_stage17_structured_provision": new_with_stage17_provision,
    "interim_verdict_changes": changed_interim,
    "stage17_verdict_changes": changed_stage17,
    "accepted_not_in_stage17_working_bibliography": sorted(not_included),
    "accepted_historical_causes": dict(causes),
    "stage16_v3_assessment_overlap_retained_separately": v3_overlap,
    "stage17_assessment_overlap_retained_separately": stage17_overlap,
    "opus_denominator": accounting["denominator"],
    "stage17_denominator": len(included),
    "reconciled_yes_no_unknown": {
        "yes": 193 + Counter(complete_map.values())["yes"],
        "no": 2322 + Counter(complete_map.values())["no"],
        "unknown": len(included) - 2515 - len(complete_map),
    },
    "reconciled_decisions": 2515 + len(complete_map),
    "reconciled_status_coverage_pct": (2515 + len(complete_map)) / len(included) * 100,
    "additional_decisions_to_25pct_current_bibliography": 3743 - (2515 + len(complete_map)),
    "canonical_stage17_database_includes_complete_new_304": False,
    "interpretation": (
        "The complete Opus LFS package is intact and its included files match their manifest. "
        "The 496 manifest media files are in a separately named original-image companion, "
        "not in this ZIP or GitHub. Seven included ZIP filenames have an en-dash encoding alias; "
        "their bytes match the manifest paths. The 844 labels include all 540 in Stage 17 and "
        "all 597 in the earlier final Opus release. These remain provisional AI decisions with "
        "historical first causes unknown."
    ),
}
out = Path(__file__).resolve().parent
(out / "OPUS_COMPLETE_RECONCILIATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
fields = [
    "instrument_id", "final_substantive_effect", "final_any_operative_EO_effect",
    "ledger_signing_date", "ledger_title", "lane", "text_obtained", "text_source_grade",
    "footprint_complete", "historical_causes", "review_verdict", "review_problems",
    "what_remains_inferential", "evidence_dir", "review_dir",
]
with (out / "OPUS_COMPLETE_304_PENDING_CANONICAL_INTEGRATION.csv").open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for instrument in sorted(new_since_stage17):
        writer.writerow({field: record_map[instrument].get(field) for field in fields})

canonical_csv = out / "DECIDED_CASE_COMPLETENESS_STAGE17.csv"
with canonical_csv.open(encoding="utf-8", newline="") as fh:
    canonical = list(csv.DictReader(fh))
if len(canonical) != 3055 or {x["instrument_id"] for x in canonical} & new_since_stage17:
    raise SystemExit("Unexpected canonical completeness CSV")
fieldnames = list(canonical[0])
combined = {x["instrument_id"]: x for x in canonical}
for instrument in new_since_stage17:
    rec = record_map[instrument]
    episode_rows = list(conn.execute(
        "SELECT first_cessation_proven FROM legal_episode WHERE instrument_id=?", (instrument,)
    ))
    provision_count = conn.execute(
        "SELECT COUNT(*) FROM stage17_provision WHERE instrument_id=?", (instrument,)
    ).fetchone()[0]
    transition_count = conn.execute(
        "SELECT COUNT(*) FROM stage17_transition t JOIN stage17_provision p "
        "ON p.provision_id=t.affected_provision_id WHERE p.instrument_id=?", (instrument,)
    ).fetchone()[0]
    first_sunset_count = conn.execute(
        "SELECT COUNT(*) FROM stage17_transition t JOIN stage17_provision p "
        "ON p.provision_id=t.affected_provision_id WHERE p.instrument_id=? "
        "AND t.first_cause_inference='FIRST_NORMATIVE_SUNSET'", (instrument,)
    ).fetchone()[0]
    legal_event_count = conn.execute(
        "SELECT COUNT(*) FROM legal_event WHERE affected_instrument=?", (instrument,)
    ).fetchone()[0]
    combined[instrument] = {
        "instrument_id": instrument,
        "provisional_substantive_status": complete_map[instrument],
        "decision_origin": "opus_complete_addition",
        "opus_any_effect_status": rec.get("final_any_operative_EO_effect"),
        "opus_source_text_obtained": rec.get("text_obtained"),
        "opus_footprint_complete_claim": rec.get("footprint_complete"),
        "opus_first_cause_status": rec.get("historical_causes"),
        "opus_original_images_in_supplied_zip": 0,
        "stage16_structured_episode_count": len(episode_rows),
        "stage16_scoped_first_cause_proven_count": sum(x[0] == 1 for x in episode_rows),
        "stage17_provision_count": provision_count,
        "stage17_transition_count": transition_count,
        "stage17_scoped_first_sunset_count": first_sunset_count,
        "recorded_legal_event_count": legal_event_count,
        "stage17_assessment": stage17_assessment.get(instrument, "none"),
        "stage16_v3_assessment": v3.get(instrument, "none"),
        "whole_order_first_cessation_verified_by_this_audit": "no",
        "human_certified_by_this_release": "no",
        "audit_next_step": "inspect original images and full provision footprint; reconstruct first causal history",
    }
with (out / "DECIDED_CASE_COMPLETENESS_RECONCILED.csv").open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(combined[x] for x in sorted(combined))
if len(combined) != result["reconciled_decisions"]:
    raise SystemExit("Combined decided-case count mismatch")
print(json.dumps(result, indent=2))
