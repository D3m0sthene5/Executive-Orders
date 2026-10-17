"""Crosswalk Stage 17 case claims to locally preserved official FR pages.

This is an additive audit, not a relabeling or canonical database migration.
"""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "research" / "stage18"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((STAGE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    facts_path = ROOT / "research" / "stage17" / "sources" / "adjudicated_legal_facts.json"
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    refs = json.loads((ROOT / "research" / "stage17" / "sources" / "verified_web_source_references.json").read_text(encoding="utf-8"))
    refs_by_id = {row["subject_id"]: row for row in refs}
    by_order = {}
    for source in manifest["federal_register"]:
        for order in source["executive_orders"]:
            key = f"EO:{order}"
            if key in by_order:
                raise ValueError(f"duplicate source for {key}")
            by_order[key] = source
    expected = {"EO:9896", "EO:10035", "EO:10084", "EO:10097", "EO:10098", "EO:10118", "EO:10136", "EO:10158", "EO:10174", "EO:10188", "EO:10310", "EO:10517", "EO:10599", "EO:11481"}
    if set(by_order) != expected:
        raise ValueError("Stage 18 primary-source order set differs from Stage 17 pilot")

    rows = []
    for order in sorted(expected, key=lambda x: int(x.split(":")[1])):
        source = by_order[order]
        ref = refs_by_id.get(order)
        provisions = [p for p in facts["provisions"] if p["instrument_id"] == order]
        transitions = [t for t in facts["transitions"] if t["affected_provision_id"] in {p["provision_id"] for p in provisions}]
        signing_date = ref["document_date"] if ref else None
        if order == "EO:10599":
            signing_date = "1955-03-14"  # The next order on the same printed page is dated March 15.
        for t in transitions:
            actor = t["actor_id"]
            if actor not in by_order:
                raise ValueError(f"unmapped transition actor {actor}")
        rows.append({
            "instrument_id": order,
            "signing_date_as_printed": signing_date,
            "issue_date": source["issue_date"],
            "printed_pages": source["printed_register_pages"],
            "publication_scan": source["local_excerpt"],
            "publication_scan_sha256": source["local_excerpt_sha256"],
            "original_signed_instrument_locally_preserved": False,
            "source_representation": "contemporaneous official Federal Register page scan",
            "stage17_provision_records": provisions,
            "stage17_transition_records_with_actor_scan": [
                {**t, "actor_publication_scan": by_order[t["actor_id"]]["local_excerpt"]}
                for t in transitions
            ],
            "stage18_audit_limits": "This crosswalk confirms the printed text and identifies the direct source for each scoped event. It does not prove absence of later unlocated amendments, exercise, accrued rights, or ongoing independent authority. It is AI research, not human certification.",
        })

    if sum(len(row["stage17_provision_records"]) for row in rows) != 13:
        raise ValueError("provision count changed")
    if sum(len(row["stage17_transition_records_with_actor_scan"]) for row in rows) != 26:
        raise ValueError("transition count changed")
    out = {
        "release": "stage18",
        "status": "additive AI source crosswalk; no new human certification",
        "stage17_facts_sha256": sha256(facts_path),
        "case_count": len(rows),
        "provision_count": 13,
        "transition_count": 26,
        "date_resolution": {
            "EO:10599": "The March 16, 1955 Federal Register page 1569 image dates EO 10599 March 14; March 15 belongs to adjacent EO 10600. Filing date was March 15. Retire the unresolved signing-date conflict from the Stage 17 source metadata in a future canonical migration."
        },
        "text_extraction_correction": {
            "EO:10158": "The September 1, 1950 Federal Register page 5927 image cites EO 10118, not EO 10113, in its predecessor chain."
        },
        "cases": rows,
    }
    target = STAGE / "data" / "PRIMARY_SOURCE_CASE_AUDIT.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Crosswalked {len(rows)} cases, 13 provisions, 26 transitions")


if __name__ == "__main__":
    main()
