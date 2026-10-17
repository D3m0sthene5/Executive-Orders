"""Content step for executive-order originals, shared by both jobs.

Given a fetched document for an EO, decide whether it really holds that
order and pull out only the order's own pages:

- a govinfo Federal Register issue PDF (1936-1994 scans): find the cited FR
  page and the order's number with fr_pages.locate_order;
- a per-document PDF (1994 on): the whole file is the order;
- an HTML/XML copy (federalregister.gov, a mirror): accept only if the
  order's number appears in the text.

PDF text is cached in memory per file, so several orders printed in the same
issue parse it once.
"""
from __future__ import annotations

import re
import urllib.parse
from collections import OrderedDict
from pathlib import Path

import fetch_ladder
import fr_pages

_TEXT_CACHE: "OrderedDict[str, list]" = OrderedDict()
_TEXT_CACHE_MAX = 3


def issue_pdf(url: str) -> bool:
    """True for a whole daily issue, e.g. .../FR-1937-01-12/pdf/FR-1937-01-12.pdf."""
    return bool(re.search(r"/pdf/FR-\d{4}-\d\d-\d\d\.pdf$", urllib.parse.urlsplit(url).path))


def pdf_texts(path, sha256):
    key = sha256 or str(path)
    if key in _TEXT_CACHE:
        _TEXT_CACHE.move_to_end(key)
        return _TEXT_CACHE[key]
    _, pages = fetch_ladder.pdf_pages_text(path)
    texts = [t for _, t in pages]
    _TEXT_CACHE[key] = texts
    while len(_TEXT_CACHE) > _TEXT_CACHE_MAX:
        _TEXT_CACHE.popitem(last=False)
    return texts


def number_of(wanted) -> str:
    kind, p = fetch_ladder.parse_citation(wanted.citation)
    if kind == "EO":
        return p["number"]
    m = re.search(r"(\d+[A-Z]?)$", wanted.wanted_id)
    return m.group(1) if m else ""


def fr_citation(wanted):
    rec = wanted.eo_record or {}
    return rec.get("citation") or ""


def eo_extract(wanted, route, att, fetcher, accept_low=True):
    """Ladder content step for an executive order. See module docstring."""
    path = att.get("path")
    if not path or not Path(path).exists():
        return {"ok": False, "reason": "document body not available in cache"}
    number = number_of(wanted)
    citation = fr_citation(wanted)
    vol, page = (None, None)
    m = re.fullmatch(r"\s*(\d+)\s*FR\s*(\d+)\s*", citation)
    if m:
        vol, page = int(m.group(1)), int(m.group(2))
    final = att.get("final_url") or att["url"]
    original = final.split("id_/", 1)[1] if "web.archive.org/web/" in final and "id_/" in final else final
    with open(path, "rb") as fh:
        is_pdf = fh.read(8).lstrip()[:5] == b"%PDF-"
    name = urllib.parse.urlsplit(original).path.rsplit("/", 1)[-1]
    if is_pdf:
        texts = pdf_texts(path, att.get("sha256"))
        single = not issue_pdf(original)
        loc = fr_pages.locate_order(texts, number, page, att.get("page_hint"), single_document=single)
        if not loc["found"]:
            return {"ok": False, "reason": "; ".join(loc["notes"]) or "order not located in PDF", "location": loc}
        if loc["confidence"] == "low" and not accept_low:
            return {"ok": False, "reason": "only a low-confidence location", "location": loc}
        a, b = loc["first_page"], loc["last_page"]
        body = "\n".join(f"=== PDF page {i} of {len(texts)} ===\n{texts[i - 1]}" for i in range(a, b + 1))
        cite = citation or wanted.citation
        page_or_item = f"{cite}, PDF pages {a}-{b}"
        notes = (f"{name}: {len(texts)} PDF pages; located by {loc['method']}"
                 f"{', marker ' + loc['marker_kind'] if loc['marker_kind'] else ''}; confidence {loc['confidence']}")
        if loc["notes"]:
            notes += "; " + "; ".join(loc["notes"])
        return {"ok": True, "text": body, "page_or_item": page_or_item, "notes": notes, "location": loc,
                "pdf_pages_total": len(texts)}
    text, _ = fetch_ladder.extract_text(path, att.get("content_type", ""), route.expect)
    if not text:
        return {"ok": False, "reason": "no text in document"}
    if number and not re.search(rf"(?<!\d){fr_pages.digits_pattern(number)}(?!\d)", text):
        return {"ok": False, "reason": f"order number {number} not found in the text"}
    loc = {"found": True, "confidence": "medium", "method": "number_found_in_html_or_xml_text",
           "first_page": None, "last_page": None, "marker_kind": None, "notes": []}
    return {"ok": True, "text": text, "page_or_item": f"{citation or wanted.citation}, {name or original} (whole document)",
            "notes": f"{name}: non-PDF copy ({route.route}); not the official PDF edition", "location": loc}
