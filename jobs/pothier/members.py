"""Pothier, step 1: the member table of the undecided orders that have no dated status history.

Named for Robert-Joseph Pothier (1699-1772), who reduced French law to treatises by subject, so that one
treatise settled what had been argued case by case. Pothier writes one doctrine per family of orders and
applies it to every member. This module builds the members and the facts the doctrines may read.

A member is an order that the readiness tracker counts as undecided (no provisional status) and for which
`jobs/status-history` located no dated history (INDEX.json `history` is null). On main of 2026-11-05 that is
5,918 of 10,681 undecided orders.

Every field is read from committed outputs of other jobs; nothing here is a finding. Texts are read from the
project's held fragments (jobs/_lib/eo_identity.load_fragments) and from X1's TYPES.csv text path. Feature
extraction is literal pattern matching on the held text, the WPA 1944 summary and the APP title.

Standard library only. Zero tokens. Deterministic: rows are sorted by instrument id and every list is sorted.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "jobs/_lib"))
import eo_identity  # noqa: E402

csv.field_size_limit(10**9)

TRACKER = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
HISTORY_INDEX = "jobs/status-history/output/INDEX.json"
WPA = "jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv"
TYPES = "jobs/x1-class-engine/output/TYPES.csv"
LATER_EDGES = "jobs/later-events/output/EDGES.csv"
SHEPARD_EDGES = "jobs/shepard-citations/output/EDGES.csv"
NAMIER_LINKS = "jobs/namier/output/NAME_LINKS.jsonl"
NAMIER_EDGES = "jobs/namier/output/EDGES.csv"
CURRENT_LAW = "jobs/current-law/output/ORDERS_CURRENT_LAW.csv"
TEXT_CHARS = 12000
PARTIAL_QUALIFIER = re.compile(r"\bpart\b|in so far|insofar|so far as|^as to |^sections? |with respect to|following-described|^paragraphs? ", re.I)
GRADE_RANK = {"official": 0, "archival_replica": 1, "transcription": 2}

# --- literal feature patterns (compacted text: WPA OCR joins and splits words) ---------------------
STAT_RE = re.compile(r"(\d{1,3})\s*Stat\.?\s*(?:L\.?\s*)?,?\s*(?:p\.?\s*)?(\d{1,4})", re.I)
ACT_DATE_RE = re.compile(r"act\s+(?:of\s+Congress\s+)?(?:approved|of)\s+(" + eo_identity._MONTH +
                         r"\s+\d{1,2},?\s+\d{4})", re.I)
PLSS_RE = re.compile(r"\b(?:T(?:ownship)?\.?\s*\d{1,3}\s*(?:N|S|north|south)\b|R(?:ange)?\.?\s*\d{1,3}\s*(?:E|W|east|west)\b|"
                     r"township\s+[a-z\-]+\s+(?:north|south)|range\s+[a-z\-]+\s+(?:east|west)|meridian)", re.I)
TERMS = {
    "temporary": r"temporar(?:y|ily)",
    "pending": r"pending\s+(?:resurvey|survey|classification|legislation|determination|examination|the\s+determination)",
    "until": r"\buntil\b",
    "for_period_years": r"for\s+(?:a|an\s+additional|a\s+further)?\s*period\s+of\s+(?:\w+\s+){0,2}\(?\d*\)?\s*years?",
    "trust_period": r"trust\s+period|period\s+of\s+trust|restrictions?\s+(?:against|on)\s+alienation",
    "revokes_other": r"(?:is|are)\s+hereby\s+(?:revoked|rescinded|vacated)|revocation\s+of|revoking",
    "amends_other": r"(?:is|are)\s+hereby\s+amended|amending|amendment\s+of",
    "restores": r"restored\s+to\s+(?:the\s+)?public\s+domain|restore[sd]?\s+to\s+entry|open(?:ed)?\s+to\s+(?:settlement|entry)",
    "waiver": r"without\s+regard\s+to\s+the\s+(?:civil[\s-]+service\s+)?rules?|civil[\s-]+service\s+rules?.{0,80}waived|"
              r"exempt(?:ed)?\s+from\s+(?:the\s+)?(?:provisions|operation)",
    "retirement": r"retire(?:ment)?\s+(?:act|age)|compulsory\s+retirement|act\s+of\s+May\s+22,?\s+1920",
    "emergency": r"\bemergency\b|\bwar\b",
    "fiscal_year": r"fiscal\s+year",
    "boundary": r"boundar(?:y|ies)",
    "transfer_forest": r"(?:transferred|added|eliminated|excluded)\s+(?:to|from)\s+(?:the\s+)?[A-Z][a-z]+\s+National\s+Forest|"
                       r"National\s+Forest",
}
TERM_RES = {k: re.compile(v, re.I) for k, v in TERMS.items()}
STATE_NAMES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
               "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
               "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
               "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
               "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
               "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
               "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "Puerto Rico", "Philippine",
               "Canal Zone", "Porto Rico", "Guam", "Samoa"]
STATE_RE = re.compile(r"\b(" + "|".join(re.escape(s) for s in STATE_NAMES) + r")\b")


def read_csv(rel):
    with open(REPO / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_jsonl(rel):
    out = []
    p = REPO / rel
    if not p.exists():
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def member_ids():
    """Undecided tracker orders whose status-history index entry has no history."""
    tracker = {r["instrument_id"]: r for r in read_csv(TRACKER)}
    with open(REPO / HISTORY_INDEX, encoding="utf-8") as f:
        index = {d["instrument_id"]: d for d in json.load(f)}
    return sorted(i for i, r in tracker.items()
                  if not r.get("provisional_status") and not (index.get(i) or {}).get("history")), tracker


def rel(path):
    if not path:
        return ""
    p = Path(path)
    if not p.is_absolute():
        p = (REPO / p).resolve()
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(path)


def best_texts(iid, fragments, types_row):
    """All held text files for the order, best grade first. Returns list of dicts with path, sha, grade."""
    seen, out = set(), []
    for f in fragments.get(iid, []):
        p = rel(f.get("text_path"))
        if p and p not in seen and (REPO / p).is_file():
            seen.add(p)
            out.append({"path": p, "class": f["class"], "grade": f.get("grade") or f["class"],
                        "produced_by": f.get("produced_by", ""), "acceptable_as_original": bool(f.get("acceptable_as_original")),
                        "url": f.get("url", "")})
    tp = rel((types_row or {}).get("text_path"))
    if tp and tp not in seen and (REPO / tp).is_file():
        out.append({"path": tp, "class": "transcription", "grade": types_row.get("text_grade") or "transcription",
                    "produced_by": "x1_types_text_path", "acceptable_as_original": False, "url": ""})
    out.sort(key=lambda t: (0 if t["acceptable_as_original"] else 1, GRADE_RANK.get(t["class"], 3), t["path"]))
    return out


def read_text(path, limit=TEXT_CHARS):
    with open(REPO / path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    return raw[:limit], hashlib.sha256(raw.encode("utf-8")).hexdigest()


def features(text):
    flat = re.sub(r"\s+", " ", text or "")
    out = {k: bool(r.search(flat)) for k, r in TERM_RES.items()}
    out["stat_cites"] = sorted({f"{a} Stat. {b}" for a, b in STAT_RE.findall(flat)})
    out["act_dates"] = sorted({re.sub(r"\s+", " ", d) for d in ACT_DATE_RE.findall(flat)})
    out["plss"] = bool(PLSS_RE.search(flat))
    out["states"] = sorted(set(STATE_RE.findall(flat)))
    mentions = set()
    for m in eo_identity.MENTION_RE.finditer(flat):
        for n in eo_identity._NUM_RE.finditer(m.group("run")):
            mentions.add(eo_identity.canon_id(n.group(1).replace(",", ""), n.group(2) or ""))
    out["eo_mentions"] = sorted(mentions)  # may include the order itself and neighbours in compiled texts
    return out


def build():
    ids, tracker = member_ids()
    idset = set(ids)
    wpa = {}
    for r in read_csv(WPA):
        wpa.setdefault(r["id"], []).append(r)
    types = {r["instrument_id"]: r for r in read_csv(TYPES)}
    fragments = eo_identity.load_fragments(str(REPO))
    dates = eo_identity.load_dates(str(REPO), fragments)
    edges_on = {}
    shepard = read_csv(SHEPARD_EDGES) if (REPO / SHEPARD_EDGES).exists() else []
    for e in shepard:
        # Shepard rows marked "in part" act on part of the order only: keep them apart from whole-order mechanisms.
        if (e.get("qualifier") or "").strip().lower() == "in part" and e.get("mechanism"):
            e["mechanism"] = "partial_" + e["mechanism"]
    later = read_csv(LATER_EDGES)
    for e in later:
        # A later-events qualifier that confines the act to part of the order (tracts, sections, a country) marks it partial.
        if e.get("mechanism") and PARTIAL_QUALIFIER.search(e.get("qualifier") or ""):
            e["mechanism"] = "partial_" + e["mechanism"]
    for e in later + shepard:
        if e.get("target_id") in idset:
            edges_on.setdefault(e["target_id"], []).append(
                {k: e.get(k, "") for k in ("edge_id", "acting_id", "mechanism", "qualifier", "date_candidate",
                                          "evidence_type", "source_url", "quote")})
    names = {r["instrument_id"]: r for r in read_jsonl(NAMIER_LINKS) if r.get("instrument_id") in idset}
    name_edges = {}
    for e in read_csv(NAMIER_EDGES):
        if e.get("target_id") in idset:
            name_edges.setdefault(e["target_id"], []).append(
                {k: e.get(k, "") for k in ("edge_id", "acting_id", "qualifier", "date_candidate")})
    cl = {r["instrument_id"]: r for r in read_csv(CURRENT_LAW) if r["instrument_id"] in idset}
    rows = []
    for iid in ids:
        w = wpa.get(iid) or []
        t = types.get(iid) or {}
        texts = best_texts(iid, fragments, t)
        text, text_sha = ("", "")
        if texts:
            text, text_sha = read_text(texts[0]["path"])
        summary = " ".join(x.get("text", "") for x in w)
        f_text = features(text)
        f_sum = features(summary + " " + (t.get("app_title") or ""))
        n = names.get(iid) or {}
        c = cl.get(iid) or {}
        rows.append({
            "instrument_id": iid,
            "number": (w[0]["number"] if w else ""),
            "date": (dates.get(iid) or {}).get("date", ""),
            "date_source": (dates.get(iid) or {}).get("date_source", ""),
            "title": (dates.get(iid) or {}).get("title", "") or t.get("app_title", ""),
            "wpa_family_hint": (w[0]["family_hint"] if w else ""),
            "wpa_entries": len(w),
            "wpa_summary": summary,
            "wpa_citations": " | ".join(x.get("citations_joined", "") for x in w if x.get("citations_joined")),
            "x1_type": t.get("type", ""),
            "x1_class": t.get("class", ""),
            "x1_rule": t.get("rule_id", ""),
            "x1_confidence": t.get("confidence", ""),
            "texts": texts,
            "primary_text_path": texts[0]["path"] if texts else "",
            "primary_text_sha256": text_sha,
            "primary_text_grade": texts[0]["grade"] if texts else "",
            "text_features": f_text,
            "summary_features": f_sum,
            "named_persons": n.get("names", []),
            "name_later_hits": sorted(name_edges.get(iid, []), key=lambda e: e["edge_id"]),
            "later_edges": sorted(edges_on.get(iid, []), key=lambda e: e["edge_id"]),
            "current_law": {k: c.get(k, "") for k in ("usc_mentions", "usc_predicate_leads", "ecfr_mentions",
                                                     "ecfr_predicate_leads", "ending_statements_found",
                                                     "usc_predicate_citations", "cfr_predicate_citations")} if c else {},
            "tracker_blockers": (tracker.get(iid) or {}).get("blockers", ""),
        })
    return rows


def main(argv=None):
    out_dir = Path(os.environ.get("OUTPUT_DIR") or HERE / "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = build()
    with open(out_dir / "MEMBERS.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"members: {len(rows)} -> {out_dir / 'MEMBERS.jsonl'}")
    return rows


if __name__ == "__main__":
    main()
