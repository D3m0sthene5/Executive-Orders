"""Stage 21 reuse of literal official EO links from the frozen Stage 14 export.

A source URL is an acquisition lead, never evidence that its exact original
pages or substantive legal outcome have been independently authenticated.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / "research/stage14/QUEUES/OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv"
CASES = ROOT / "research/stage20/output/CONVERSION_INDEX.csv"
OUT = ROOT / "research/stage21/sources_index"
KINDS = {"pdf_url": 0, "full_text_xml_url": 1, "html_url": 2}
HOSTS = {"www.govinfo.gov", "www.federalregister.gov"}

def csv_from(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))

def csv_to(rows):
    b = io.StringIO(newline="")
    w = csv.DictWriter(b, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return b.getvalue().encode("utf-8")

def safe_source(row):
    p = urlsplit(row.get("url") or "")
    return (row.get("field") in KINDS and p.scheme == "https"
            and p.hostname in HOSTS
            and ("/content/pkg/" in p.path or "/documents/" in p.path))

def crosswalk(manifest, cases, hashes, strict=True):
    if strict and (len(manifest), len(cases)) != (4331, 3359):
        raise ValueError("Frozen Stage 14/20 cohort changed")
    by_id = {}
    for r in cases:
        id_ = r.get("instrument_id")
        if not id_ or id_ in by_id:
            raise ValueError("Duplicate or missing EO case")
        if r.get("whole_lifecycle_completed") != "no":
            raise ValueError("Previous completion gate has changed")
        by_id[id_] = r
    evidence = defaultdict(list)
    seen = set()
    for s in manifest:
        if not safe_source(s):
            raise ValueError("Invalid purported original URL")
        key = (s.get("instrument_id"), s.get("field"), s.get("url"))
        if not key[0] or key in seen:
            raise ValueError("Duplicate/missing source identity")
        seen.add(key)
        evidence[key[0]].append(s)
    if strict and len(evidence) != 1546:
        raise ValueError("Frozen Stage 14 source identity count changed")
    joins, requests = [], []
    for id_ in sorted(by_id):
        case = by_id[id_]
        links = sorted(evidence.get(id_, []),
            key=lambda r: (KINDS[r["field"]], r["url"]))
        def by_field(k):
            return next((r for r in links if r["field"] == k), None)
        pdf,xml,htm = (by_field(k) for k in
            ("pdf_url","full_text_xml_url","html_url"))
        chosen = pdf or xml or htm
        joins.append({
            "instrument_id": id_, "provisional_status_UNVERIFIED":
                case["provisional_status"],
            "literal_official_URL_candidates": len(links),
            "PDF_candidate": pdf["url"] if pdf else "",
            "XML_candidate": xml["url"] if xml else "",
            "HTML_candidate": htm["url"] if htm else "",
            "signing_date_from_cached_index": chosen.get("signing_date", "") if chosen else "",
            "FR_citation_from_cached_index": chosen.get("citation", "") if chosen else "",
            "selected_literal_URL": chosen["url"] if chosen else "",
            "selected_format": chosen["field"] if chosen else "",
            "index_only_NOT_RETRIEVED": "yes",
            "document_identity_authenticated": "no",
            "operative_clause_legal_effect_verified": "no",
            "independent_human_review": "no"
        })
        if chosen:
            requests.append({
                "instrument_id": id_, "format": chosen["field"],
                "literal_url": chosen["url"],
                "triage_NOT_confidence": int(
                    case.get("research_triage_not_confidence") or 0),
                "input_URL_is_from_official_metadata": "yes",
                "retrieval_attempted_in_this_stage": "no",
                "bytes_sha256": "", "original_EO_verified": "no"
            })
    requests.sort(key=lambda r: (-r["triage_NOT_confidence"],
                                 KINDS[r["format"]],r["instrument_id"]))
    stats = {
        "schema":"eo-stage21-frozen-official-source-reuse/v1",
        "stage14_literal_URL_records":len(manifest),
        "stage14_distinct_source_instruments":len(evidence),
        "reconciled_provisional_cases":len(by_id),
        "provisional_cases_with_direct_OFFICIAL_URLs":len(requests),
        "provisional_cases_with_PDF_URL":sum(bool(x["PDF_candidate"]) for x in joins),
        "selected_format_counts":dict(sorted(Counter(
            x["selected_format"] or "no_url" for x in joins).items())),
        "input_sha256":hashes,
        "actual_downloads_this_stage":0,
        "new_legal_findings":0,
        "human_certified_dossiers":0
    }
    return joins, requests, stats

def generate():
    a,b = ORIGINAL.read_bytes(), CASES.read_bytes()
    joined,requests,stats = crosswalk(csv_from(a),csv_from(b),{
        "Stage14":hashlib.sha256(a).hexdigest(),
        "Stage20":hashlib.sha256(b).hexdigest()
    })
    return {
        "OFFICIAL_SOURCE_CASE_CROSSWALK.csv":csv_to(joined),
        "ORIGINAL_SOURCE_RETRIEVAL_QUEUE.csv":csv_to(requests),
        "METRICS.json":(json.dumps(stats,sort_keys=True,indent=2)+"\n").encode("utf-8")
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true")
    args=p.parse_args()
    data=generate()
    OUT.mkdir(parents=True,exist_ok=True)
    for name,payload in data.items():
        target=OUT/name
        if args.check:
            if target.read_bytes()!=payload:
                raise SystemExit("Source index drift: "+name)
        else:
            target.write_bytes(payload)
    print(data["METRICS.json"].decode())

if __name__=="__main__":
    main()
