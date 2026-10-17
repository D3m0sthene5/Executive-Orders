"""Audit the released Stage 17 database without changing legal conclusions.

Usage: python research/progress/build_decision_completeness.py PATH_TO_STAGE17.sqlite
"""

import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    database = Path(sys.argv[1])
    if not database.is_file():
        raise SystemExit(f"Database not found: {database}")
    sha = hashlib.sha256()
    with database.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            sha.update(block)
    expected_sha = "c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1"
    if sha.hexdigest() != expected_sha:
        raise SystemExit("Unexpected Stage 17 database SHA-256")
    out = Path(__file__).resolve().parent
    conn = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)

    opus = {r[0]: r for r in conn.execute(
        "SELECT instrument_id, substantive_status, any_effect_status, "
        "source_text_obtained, footprint_complete, historical_first_cause_status, "
        "evidence_originals_in_supplied_opus_zip FROM opus_checkpoint2_import"
    )}
    episodes = defaultdict(list)
    for instrument, cause, proven in conn.execute(
        "SELECT instrument_id, cessation_mechanism, first_cessation_proven FROM legal_episode"
    ):
        episodes[instrument].append((cause, proven))
    provisions = Counter(r[0] for r in conn.execute("SELECT instrument_id FROM stage17_provision"))
    transitions = Counter(r[0] for r in conn.execute(
        "SELECT p.instrument_id FROM stage17_transition t "
        "JOIN stage17_provision p ON p.provision_id=t.affected_provision_id"
    ))
    first_sunsets = Counter(r[0] for r in conn.execute(
        "SELECT p.instrument_id FROM stage17_transition t "
        "JOIN stage17_provision p ON p.provision_id=t.affected_provision_id "
        "WHERE t.first_cause_inference='FIRST_NORMATIVE_SUNSET'"
    ))
    legal_events = Counter(r[0] for r in conn.execute(
        "SELECT affected_instrument FROM legal_event"
    ))
    stage17_assessments = {r[0]: r[1] for r in conn.execute(
        "SELECT instrument_id, normative_status FROM stage17_assessment"
    )}
    v3_assessments = {r[0]: r[1] for r in conn.execute(
        "SELECT id, normative_status FROM v3_effect_assessments"
    )}
    review_count = conn.execute("SELECT COUNT(*) FROM stage17_review WHERE test_only=0").fetchone()[0]

    rows = []
    for instrument, legacy_status in conn.execute(
        "SELECT id, original_legacy_status FROM instruments WHERE include_proxy=1 ORDER BY id"
    ):
        o = opus.get(instrument)
        status = o[1] if o else legacy_status
        if status not in ("yes", "no"):
            continue
        row = {
            "instrument_id": instrument,
            "provisional_substantive_status": status,
            "decision_origin": "opus_checkpoint2" if o else "inherited_legacy_v2",
            "opus_any_effect_status": o[2] if o else "not_recorded_in_opus_overlay",
            "opus_source_text_obtained": o[3] if o else "not_applicable",
            "opus_footprint_complete_claim": o[4] if o else "not_applicable",
            "opus_first_cause_status": o[5] if o else "not_applicable",
            "opus_original_images_in_supplied_zip": o[6] if o else "not_applicable",
            "stage16_structured_episode_count": len(episodes[instrument]),
            "stage16_scoped_first_cause_proven_count": sum(x[1] == 1 for x in episodes[instrument]),
            "stage17_provision_count": provisions[instrument],
            "stage17_transition_count": transitions[instrument],
            "stage17_scoped_first_sunset_count": first_sunsets[instrument],
            "recorded_legal_event_count": legal_events[instrument],
            "stage17_assessment": stage17_assessments.get(instrument, "none"),
            "stage16_v3_assessment": v3_assessments.get(instrument, "none"),
            "whole_order_first_cessation_verified_by_this_audit": "no",
            "human_certified_by_this_release": "no",
            "audit_next_step": (
                "inspect_original_images_and_full_provision_footprint; reconstruct first causal history"
                if o else
                "inspect original and full provision footprint; reconstruct first causal history"
            ),
        }
        rows.append(row)

    target = out / "DECIDED_CASE_COMPLETENESS_STAGE17.csv"
    with target.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(r["provisional_substantive_status"] for r in rows)
    origins = Counter(r["decision_origin"] for r in rows)
    summary = {
        "schema": "eo-decision-completeness-audit/v1",
        "source_database": database.name,
        "source_stage17_database_sha256": sha.hexdigest(),
        "working_identities": 14972,
        "provisional_decisions": len(rows),
        "provisional_yes": counts["yes"],
        "provisional_no": counts["no"],
        "provisional_unknown": 14972 - len(rows),
        "decision_origins": dict(origins),
        "decided_with_stage16_structured_episode": sum(int(r["stage16_structured_episode_count"]) > 0 for r in rows),
        "decided_with_stage17_structured_provision": sum(int(r["stage17_provision_count"]) > 0 for r in rows),
        "decided_with_any_scoped_structured_history": sum(
            int(r["stage16_structured_episode_count"]) > 0 or int(r["stage17_provision_count"]) > 0
            for r in rows
        ),
        "opus_decisions_without_supplied_original_images": sum(
            r["decision_origin"] == "opus_checkpoint2" and r["opus_original_images_in_supplied_zip"] == 0
            for r in rows
        ),
        "opus_decisions_with_first_cause_unknown": sum(
            r["decision_origin"] == "opus_checkpoint2" and str(r["opus_first_cause_status"]).startswith("UNKNOWN")
            for r in rows
        ),
        "production_human_review_rows": review_count,
        "stage17_scoped_first_sunset_assertions": sum(first_sunsets.values()),
        "whole_order_first_cessation_verified_by_this_audit": 0,
        "interpretation": (
            "The audit inventories structured fields. A blank structured history does not prove "
            "that no narrative appears in original raw records. A scoped sunset or legal-event "
            "reference does not establish whole-order first cessation. No legal conclusion is "
            "changed by this audit."
        ),
    }
    if (len(rows), counts["yes"], counts["no"], origins["opus_checkpoint2"]) != (3055, 268, 2787, 540):
        raise SystemExit("Unexpected Stage 17 counts; inspect the database before publishing results")
    (out / "DECISION_COMPLETENESS_SUMMARY_STAGE17.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
