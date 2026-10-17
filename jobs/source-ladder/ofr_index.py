"""Read the frozen Office of the Federal Register executive-order index.

The snapshot lives in jobs/fr-originals/data/ofr_index/ (exact API response
bytes, gzip-compressed; PROVENANCE.json gives the sha256 of each original).
Each record has: executive_order_number, citation ("2 FR 63"),
publication_date, signing_date, title, pdf_url, document_number,
full_text_xml_url, html_url, disposition_notes, not_received_for_publication.
Everything here is catalog metadata (a lead), not an authenticated original.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path

LEGAL_CUTOFF = "2026-10-14"


def default_dir(repo_root) -> Path:
    return Path(repo_root) / "jobs" / "fr-originals" / "data" / "ofr_index"


def load_raw(index_dir, verify=True):
    """All raw records, in file order. Checks sha256 against PROVENANCE.json."""
    index_dir = Path(index_dir)
    prov = json.loads((index_dir / "PROVENANCE.json").read_text(encoding="utf-8"))
    rows = []
    for f in prov["files"]:
        data = gzip.decompress((index_dir / f["file"]).read_bytes())
        if verify and hashlib.sha256(data).hexdigest() != f["uncompressed_sha256"]:
            raise ValueError(f"OFR index file {f['file']} does not match its recorded sha256")
        rows.extend(json.loads(data.decode("utf-8"))["results"])
    return rows


def normalize_number(raw, title=""):
    """'7933-a' -> '7933A'; '10571' with title '-A ...' -> '10571A'."""
    text = str(raw or "").strip().replace(" ", "").upper()
    m = re.fullmatch(r"0*(\d{1,5})-?([A-Z]?)", text)
    if not m:
        return None
    suffix = m.group(2)
    if not suffix:
        t = re.match(r"^-([A-Z])\s", title or "")
        if t:
            suffix = t.group(1)
    return str(int(m.group(1))) + suffix


def resolve_id(number, universe_ids=None):
    """Map an index number to the project's id (the universe spells 7933a in lower case)."""
    eo = "EO:" + number
    if not universe_ids or eo in universe_ids:
        return eo
    lower = {u.lower(): u for u in universe_ids}
    return lower.get(eo.lower(), eo)


def parse_fr_citation(citation):
    m = re.fullmatch(r"\s*(\d{1,3})\s*FR\s*(\d{1,6})\s*", citation or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def build_index(rows, universe_ids=None):
    """{instrument_id: {"primary": record, "others": [records]}}.

    The primary record is the non-correction one with an FR citation; OFR
    'Correction' entries and duplicates are kept in 'others' for the notes.
    Orders signed after the legal cutoff are dropped.
    """
    by_id = {}
    for r in rows:
        num = normalize_number(r.get("executive_order_number"), r.get("title"))
        if not num:
            continue
        if (r.get("signing_date") or "") > LEGAL_CUTOFF:
            continue
        rec = dict(r)
        rec["_number"] = num
        by_id.setdefault(resolve_id(num, universe_ids), []).append(rec)
    out = {}
    for i, recs in by_id.items():
        def rank(r):
            return (r.get("title", "").strip().lower() == "correction", not r.get("citation"),
                    r.get("publication_date") or "9999")
        recs = sorted(recs, key=rank)
        out[i] = {"primary": recs[0], "others": recs[1:]}
    return out


def load_index(repo_root=None, index_dir=None, universe_ids=None):
    return build_index(load_raw(index_dir or default_dir(repo_root)), universe_ids)
