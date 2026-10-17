"""Stage 21 — acquire OFR's *entire* post-1937 executive-order catalog once.

The Office of the Federal Register's documented public bulk export includes
pre-1994 presidential document records. We preserve the untouched response
bytes, reconcile identifiers conservatively, and publish SOURCE LEADS only.

No editorial disposition note establishes a first substantive cessation.
No PDF link proves that a legal provision is operative or terminated.
All outputs are research inputs; this code never mutates classifications.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "research/stage21/output"
ARCHIVE = ROOT / "research/stage21/sources/OFR_BULK_RESPONSE.json.gz"
ACQUISITION = ROOT / "research/stage21/sources/ACQUISITION.json"
QUEUE = ROOT / "research/stage19/output/CAUSAL_QUEUE.csv"
CONVERSION = ROOT / "research/stage20/output/CONVERSION_INDEX.csv"
FAMILIES = ROOT / "research/stage20/output/SHARED_SOURCE_REFERENCE_QUEUE.csv"
CUTOFF = date(2026, 10, 14)
MAX_BYTES = 35_000_000
FIELDS = (
    "body_html_url", "citation", "disposition_notes", "document_number",
    "end_page", "executive_order_number", "full_text_xml_url", "html_url",
    "json_url", "not_received_for_publication", "pdf_url",
    "publication_date", "signing_date", "start_page", "subtype",
    "title", "type"
)


def official_export_url():
    """Exact public OFR search parameters, including pre-1994 data."""
    pairs = [
        ("conditions[correction]", "0"),
        ("conditions[presidential_document_type]", "executive_order"),
        ("conditions[search_type_id]", "3"),
        ("conditions[type][]", "PRESDOCU"),
    ]
    pairs += [("fields[]", f) for f in FIELDS]
    pairs += [
        ("include_pre_1994_docs", "true"),
        ("maximum_per_page", "10000"),
        ("order", "executive_order"),
        ("per_page", "10000"),
    ]
    return "https://www.federalregister.gov/documents/search.json?" + urllib.parse.urlencode(pairs)


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(rows, columns):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator="\n",
                            extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def normalize_eo_number(value):
    if value is None:
        return None
    raw = str(value).strip().upper()
    found = re.fullmatch(r"0*(\d{1,5})(?:[-\s]?([A-Z]))?", raw)
    if not found:
        return None
    return "EO:" + str(int(found.group(1))) + (found.group(2) or "")


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\d", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def clean_note(value):
    """Retain editorial note wording but do not interpret it as legal proof."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def safe_url(url, domains):
    if not isinstance(url, str) or not url:
        return ""
    parsed = urllib.parse.urlsplit(url)
    return url if parsed.scheme == "https" and parsed.hostname in domains else ""


def load_catalog(raw, minimum_count=3000):
    """Fail closed on incomplete, ambiguous, or substituted bulk responses."""
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("OFR payload missing results array")
    items = payload["results"]
    total = payload.get("count", len(items))
    if isinstance(total, bool) or not isinstance(total, int):
        raise ValueError("OFR total count is not integer")
    if len(items) < minimum_count or total != len(items) or len(items) > 10000:
        raise ValueError("Partial or unexpectedly small OFR bulk export: %s of %s" %
                         (len(items), total))
    if not all(isinstance(x, dict) for x in items):
        raise ValueError("Malformed OFR result object")
    indexed = defaultdict(list)
    post_cutoff = 0
    invalid_numbers = 0
    invalid_dates = 0
    for item in items:
        identifier = normalize_eo_number(item.get("executive_order_number"))
        signing = parse_date(item.get("signing_date"))
        if not identifier:
            invalid_numbers += 1
            continue
        if signing is None:
            invalid_dates += 1
            # Missing signing dates must not be assigned a date or used to
            # certify an original's status. Keep as unresolved catalog leads.
        if signing and signing > CUTOFF:
            post_cutoff += 1
            continue
        indexed[identifier].append(item)
    return indexed, {"bulk_result_rows": len(items),
                     "unique_order_numbers": len(indexed),
                     "post_cutoff_rows_excluded": post_cutoff,
                     "invalid_order_numbers": invalid_numbers,
                     "missing_or_invalid_signing_dates": invalid_dates}


def select_catalog_record(records):
    if not records:
        return "not_in_bulk_catalog", None
    if len(records) != 1:
        return "ambiguous_duplicate_catalog_records", None
    return "unique_catalog_record", records[0]


def make_model(indexed, queue, conversion, families, provenance, source_metrics):
    if len(queue) != 3359 or len(conversion) != 3359 or len(families) != 98:
        raise ValueError("Stage 19/20 frozen cohort changed; stop and reconcile")
    by_id = {}
    for r in queue:
        identifier = r["instrument_id"]
        if not identifier or identifier in by_id:
            raise ValueError("Duplicate or missing research identifier")
        by_id[identifier] = r
    conv = {}
    for r in conversion:
        identifier = r["instrument_id"]
        if identifier in conv:
            raise ValueError("Duplicate conversion identifier")
        conv[identifier] = r
    if set(by_id) != set(conv):
        raise ValueError("Conversion and causal queue disagree on identities")

    def classify(identifier, expected_date=""):
        state, doc = select_catalog_record(indexed.get(identifier, []))
        date_conflict = False
        if doc is not None and expected_date:
            date_str = str(doc.get("signing_date") or "")
            date_conflict = bool(date_str and date_str != expected_date)
        if state == "unique_catalog_record" and date_conflict:
            state = "catalog_signing_date_conflict"
        return state, doc

    crosswalk = []
    for identifier in sorted(by_id):
        q, c = by_id[identifier], conv[identifier]
        if q["legacy_status"] != c["provisional_status"]:
            raise ValueError("Disagreeing legacy status %s" % identifier)
        state, doc = classify(identifier, q.get("issuance_date", ""))
        doc = doc or {}
        crosswalk.append({
            "instrument_id": identifier,
            "provisional_status_UNVERIFIED": q["legacy_status"],
            "legacy_issuance_date": q.get("issuance_date", ""),
            "catalog_match_state": state,
            "catalog_signing_date": doc.get("signing_date") or "",
            "catalog_publication_date": doc.get("publication_date") or "",
            "catalog_document_number": doc.get("document_number") or "",
            "catalog_title": doc.get("title") or "",
            "catalog_FR_citation": doc.get("citation") or "",
            "catalog_source_page_start": doc.get("start_page") or "",
            "official_catalog_record_url": safe_url(doc.get("html_url"),
                {"www.federalregister.gov", "federalregister.gov"}),
            "official_pdf_candidate_url": safe_url(doc.get("pdf_url"),
                {"www.govinfo.gov", "govinfo.gov"}),
            "disposition_note_editorial_NOT_CAUSAL_PROOF": clean_note(
                doc.get("disposition_notes")),
            "original_text_or_clause_inventory_authenticated": "no",
            "source_effect_and_effective_date_proven": "no",
            "independent_human_review": "no",
        })
    families_out = []
    for fam in families:
        if fam.get("reference_type") != "EO":
            continue
        ref = normalize_eo_number(fam.get("reference_as_mentioned"))
        if ref is None:
            raise ValueError("Invalid shared EO authority number")
        state, doc = classify(ref)
        ids = [x.strip() for x in fam["case_ids"].split("|")]
        if len(ids) != int(fam["affected_candidate_count"]) or any(
                x not in by_id for x in ids):
            raise ValueError("Shared source family case mismatch")
        doc = doc or {}
        families_out.append({
            "cited_authority": ref,
            "citation_cooccurrence_case_count": len(ids),
            "citing_case_ids": " | ".join(ids),
            "bulk_catalog_match_state": state,
            "catalog_original_title": doc.get("title") or "",
            "catalog_signing_date": doc.get("signing_date") or "",
            "catalog_FR_citation": doc.get("citation") or "",
            "official_catalog_url": safe_url(doc.get("html_url"),
                {"www.federalregister.gov", "federalregister.gov"}),
            "original_pdf_candidate_url": safe_url(doc.get("pdf_url"),
                {"www.govinfo.gov", "govinfo.gov"}),
            "editorial_disposition_note_NOT_PROOF": clean_note(
                doc.get("disposition_notes")),
            "document_pages_checked": "no",
            "affected_clause_effectively_changed_proven": "no",
            "research_reuse_instruction": ("Acquire and hash the cited source once; "
                                           "adjudicate each EO clause separately"),
        })
    if len(families_out) != 73:
        raise ValueError("Unexpected cited EO family count")
    # One note per original EO record, not one invented terminal event per date.
    notes = []
    for row in crosswalk:
        note = row["disposition_note_editorial_NOT_CAUSAL_PROOF"]
        if note and row["catalog_match_state"] == "unique_catalog_record":
            notes.append({
                "instrument_id": row["instrument_id"],
                "catalog_document_number": row["catalog_document_number"],
                "catalog_url": row["official_catalog_record_url"],
                "editorial_note_reproduced_UNVERIFIED": note,
                "interpretation": "editorial_note_only_no_first_cause_inferred",
            })
    counts = Counter(x["catalog_match_state"] for x in crosswalk)
    family_counts = Counter(x["bulk_catalog_match_state"] for x in families_out)
    metrics = {
        "schema": "eo-stage21-ofr-bulk-custody/v1",
        "historical_cutoff": CUTOFF.isoformat(),
        "source": "Office of the Federal Register executive-order bulk export",
        "source_export_url": official_export_url(),
        "catalog_raw_response_sha256": sha256(provenance["raw"]),
        "input_csv_sha256": {k: sha256(v) for k, v in provenance["inputs"].items()},
        "reconciled_provisional_instruments": len(crosswalk),
        "shared_EO_authority_families": len(families_out),
        "shared_EO_case_source_edges": sum(int(r["citation_cooccurrence_case_count"])
                                           for r in families_out),
        "crosswalk_match_states": dict(sorted(counts.items())),
        "shared_family_match_states": dict(sorted(family_counts.items())),
        "catalog_editorial_notes_for_provisional_instruments": len(notes),
        "bulk_source_integrity_metrics": source_metrics,
        "catalog_matches_are_originals_authenticated": False,
        "catalog_disposition_notes_are_first_cessation_proofs": False,
        "certified_whole_lifecycle_dossiers_added": 0,
    }
    return {"crosswalk": crosswalk, "families": families_out, "notes": notes,
            "metrics": metrics}


def outputs(model):
    out = {}
    specs = [
        ("OFR_PROVISIONAL_CASE_CROSSWALK.csv", "crosswalk"),
        ("OFR_SHARED_EO_FAMILIES.csv", "families"),
        ("OFR_EDITORIAL_DISPOSITION_LEADS.csv", "notes"),
    ]
    for name, key in specs:
        rows = model[key]
        if rows:
            out[name] = write_csv(rows, list(rows[0]))
        else:
            out[name] = b""
    out["METRICS.json"] = (json.dumps(model["metrics"], indent=2,
                           ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    return out


def fetch_source():
    request = urllib.request.Request(official_export_url(),
        headers={"User-Agent": "EO-Lifecycle-Research/Stage21 (archival index)",
                 "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname not in (
                "www.federalregister.gov", "federalregister.gov"):
            raise ValueError("Unexpected OFR export redirect hostname: " + str(final.hostname))
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("OFR response exceeded bounded size")
        if "json" not in (response.headers.get("Content-Type") or ""):
            raise ValueError("OFR bulk response is not JSON")
    load_catalog(data)  # Validation before committing any source bytes.
    return data


def build_from_files(raw, root=ROOT):
    paths = {"queue": root / QUEUE.relative_to(ROOT),
             "conversion": root / CONVERSION.relative_to(ROOT),
             "families": root / FAMILIES.relative_to(ROOT)}
    inputs = {k: p.read_bytes() for k, p in paths.items()}
    indexed, source_metrics = load_catalog(raw)
    model = make_model(indexed,
                       list(csv.DictReader(io.StringIO(inputs["queue"].decode("utf-8")))),
                       list(csv.DictReader(io.StringIO(inputs["conversion"].decode("utf-8")))),
                       list(csv.DictReader(io.StringIO(inputs["families"].decode("utf-8")))),
                       {"raw": raw, "inputs": inputs}, source_metrics)
    return outputs(model)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fetch", action="store_true",
                   help="Fetch once unless an archived response already exists")
    p.add_argument("--check", action="store_true",
                   help="Recompute and byte-compare all derived outputs")
    a = p.parse_args()
    if a.fetch and a.check:
        p.error("--fetch and --check are mutually exclusive")
    if a.fetch and not ARCHIVE.exists():
        source = fetch_source()
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVE.write_bytes(gzip.compress(source, mtime=0))
        ACQUISITION.write_text(json.dumps({
            "schema": "eo-stage21-ofr-custody/v1",
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "bulk_export_url": official_export_url(),
            "raw_sha256": sha256(source),
            "raw_length": len(source),
            "response_archived_losslessly_gzip": True,
        }, indent=2) + "\n", encoding="utf-8")
    if not ARCHIVE.is_file():
        raise SystemExit("No catalog archive: run --fetch")
    raw = gzip.decompress(ARCHIVE.read_bytes())
    if ACQUISITION.is_file():
        custody = json.loads(ACQUISITION.read_text("utf-8"))
        if custody.get("raw_sha256") != sha256(raw) or custody.get(
                "raw_length") != len(raw):
            raise SystemExit("Archived source digest/byte count differs from custody")
    derived = build_from_files(raw)
    if a.check:
        for name, body in derived.items():
            path = OUT / name
            if not path.is_file() or path.read_bytes() != body:
                raise SystemExit("Stale derived artifact: " + name)
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, body in derived.items():
            (OUT / name).write_bytes(body)
    print(json.dumps(json.loads(derived["METRICS.json"]), indent=2))


if __name__ == "__main__":
    main()
