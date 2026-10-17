"""Check the published Stage 18 source bundle and structured research crosswalk."""

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def check_file(relative, digest):
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing source {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        raise AssertionError(f"SHA mismatch: {relative}")
    return path


def main():
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    eo_set = set()
    for row in manifest["federal_register"]:
        path = check_file(row["local_excerpt"], row["local_excerpt_sha256"])
        if len(PdfReader(path).pages) != len(row["issue_pdf_page_indexes_zero_based"]):
            raise AssertionError(f"page count mismatch {path}")
        eo_set.update(f"EO:{n}" for n in row["executive_orders"])
    for row in manifest["library_of_congress"]:
        path = check_file(row["local_file"], row["sha256"])
        with Image.open(path) as im:
            im.verify()
    asp = manifest["american_state_papers"]
    if len(PdfReader(check_file(asp["local_excerpt"], asp["local_excerpt_sha256"])).pages) != 2:
        raise AssertionError("St. Clair source must have both printed pages")
    statute = manifest["statute_1789"]
    check_file(statute["local_file"], statute["sha256"])
    if statute["enactment_date"] != "1789-09-29":
        raise AssertionError("1789 pension statute date conflict missing")
    court = manifest["supreme_court"]
    if len(PdfReader(check_file(court["local_file"], court["sha256"])).pages) != court["pages"]:
        raise AssertionError("Court source page count mismatch")

    audit = json.loads((ROOT / "data" / "PRIMARY_SOURCE_CASE_AUDIT.json").read_text(encoding="utf-8"))
    cases = audit["cases"]
    if {row["instrument_id"] for row in cases} != eo_set or len(cases) != 14:
        raise AssertionError("case/source identity crosswalk incomplete")
    if sum(len(row["stage17_provision_records"]) for row in cases) != 13:
        raise AssertionError("provision count mismatch")
    transitions = [t for row in cases for t in row["stage17_transition_records_with_actor_scan"]]
    if len(transitions) != 26 or len({t["transition_id"] for t in transitions}) != 26:
        raise AssertionError("transition count or identity mismatch")
    for transition in transitions:
        if not (ROOT / transition["actor_publication_scan"]).is_file():
            raise AssertionError("unbacked transition actor")
    for row in cases:
        if row["original_signed_instrument_locally_preserved"] or (ROOT / row["publication_scan"]).is_file() is False:
            raise AssertionError("case source grade/path mismatch")

    early = list(csv.DictReader((ROOT / "data" / "EARLY_SOURCE_CANDIDATES.csv").open(encoding="utf-8", newline="")))
    if len(early) != 6 or any(row["inclusion_state"] not in ("candidate_not_counted", "held_not_counted") for row in early):
        raise AssertionError("early candidates must remain outside denominator")
    for row in early:
        if not (ROOT / row["local_source"]).is_file():
            raise AssertionError(f"missing early source {row['candidate_id']}")
    eo1 = json.loads((ROOT / "data" / "EO1_CAUSAL_HISTORY.json").read_text(encoding="utf-8"))
    if eo1["human_certified"] or sum(bool(e.get("first_actual_institutional_cessation")) for e in eo1["clauses_and_events"]) != 1:
        raise AssertionError("EO 1 evidence state or event chain mismatch")
    print("Stage 18 verified: 14 orders, 13 clauses, 26 transitions, 6 uncounted early candidates, EO 1 event chain")


if __name__ == "__main__":
    main()
