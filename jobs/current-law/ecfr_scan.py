"""eCFR part: point-in-time search hits and full-title XML scanning.

Two official routes are used, because robots.txt on www.ecfr.gov forbids
automated use of the full-text XML endpoint (/api/versioner/v1/full/):

1. The eCFR search API (/api/search/v1/results) with ``date=2026-10-14``.
   It is point-in-time: every hit is a section in force on the cutoff date,
   but it returns only a short excerpt of each section.
2. GovInfo's eCFR bulk XML (one file per title, the current text), scanned
   in full. To know whether that current text still equals the text on the
   cutoff date, the eCFR versioner's "versions" list
   (/api/versioner/v1/versions/title-N.json) names every section that changed
   after the cutoff; mentions in those sections are flagged and not given a
   "checked_through" date.
"""

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import eo_refs

SEARCH_URL = "https://www.ecfr.gov/api/search/v1/results"
VERSIONS_URL = "https://www.ecfr.gov/api/versioner/v1/versions/title-{title}.json"
TITLES_URL = "https://www.ecfr.gov/api/versioner/v1/titles.json"
GOVINFO_URL = "https://www.govinfo.gov/bulkdata/ECFR/title-{title}/ECFR-title{title}.xml"
SEARCH_QUERIES = ['"Executive Order"', '"Executive Orders"', '"E.O."', '"Ex. Ord."', '"Exec. Order"']
VERSIONS_LOOKBACK_DAYS = 120

BLOCK = {"P", "FP", "HEAD", "HD1", "HD2", "HD3", "CITA", "AUTH", "SECAUTH", "SOURCE", "NOTE", "EDNOTE", "TR",
         "PSPACE", "HED", "EXTRACT", "EFFDNOT", "APPRO", "FTNT", "DIV", "TABLE", "EXAMPLE"}
CHILD_KIND = {"AUTH": ("part_authority", "cfr_authority_citation"),
              "SECAUTH": ("section_authority", "cfr_authority_citation"),
              "SOURCE": ("part_source", "cfr_source_citation"),
              "CITA": ("section_source_citation", "cfr_source_citation"),
              "EDNOTE": ("editorial_note", "cfr_editorial_note_reference"),
              "NOTE": ("editorial_note", "cfr_editorial_note_reference"),
              "EFFDNOT": ("effective_date_note", "cfr_editorial_note_reference")}


def human_url(title, section=None, part=None, on=eo_refs.LEGAL_CUTOFF):
    base = f"https://www.ecfr.gov/on/{on}/title-{title}"
    if section:
        return f"{base}/section-{section}"
    if part:
        return f"{base}/part-{part}"
    return base


def search_url(query, page, per_page=1000, on=eo_refs.LEGAL_CUTOFF):
    from urllib.parse import urlencode
    return SEARCH_URL + "?" + urlencode({"query": query, "date": on, "per_page": per_page, "page": page})


def versions_url(title, cutoff=eo_refs.LEGAL_CUTOFF, lookback_days=VERSIONS_LOOKBACK_DAYS):
    since = (date.fromisoformat(cutoff) - timedelta(days=lookback_days)).isoformat()
    return VERSIONS_URL.format(title=title) + f"?issue_date%5Bgte%5D={since}"


# ------------------------------------------------------------ search API --
def parse_search_page(raw_bytes):
    """Return (meta, hits) from one search-results JSON page."""
    data = json.loads(raw_bytes.decode("utf-8"))
    hits = []
    for r in data.get("results", []):
        h = r.get("hierarchy") or {}
        heads = r.get("headings") or {}
        excerpt = eo_refs.strip_tags(r.get("full_text_excerpt") or "")
        heading = eo_refs.strip_tags(heads.get("section") or heads.get("appendix") or "")
        hits.append({
            "title": str(h.get("title") or ""), "part": h.get("part") or "", "section": h.get("section") or "",
            "appendix": h.get("appendix") or "", "type": r.get("type") or "", "starts_on": r.get("starts_on"),
            "ends_on": r.get("ends_on"), "removed": bool(r.get("removed")), "reserved": bool(r.get("reserved")),
            "excerpt": excerpt, "heading": heading,
        })
    return data.get("meta") or {}, hits


def search_hit_mentions(hit, on=eo_refs.LEGAL_CUTOFF):
    """Mentions found in a hit's heading + excerpt (excerpts are partial)."""
    text = (hit["heading"] + " | " if hit["heading"] else "") + hit["excerpt"]
    if hit["section"]:
        cit = f"{hit['title']} CFR {hit['section']}"
    elif hit["appendix"]:
        cit = f"{hit['title']} CFR part {hit['part']}, {hit['appendix']}" if hit["part"] else f"{hit['title']} CFR {hit['appendix']}"
    else:
        cit = f"{hit['title']} CFR part {hit['part']}"
    grouped = {}
    refs = eo_refs.find_eo_refs(text)
    ended = eo_refs.ended_subject_keys(text) if refs else set()
    for r in refs:
        key = (r["number"], r["suffix"].upper())
        if key not in grouped:
            grouped[key] = {"title": hit["title"], "part": hit["part"], "section": hit["section"],
                            "citation": cit, "location_kind": "search_excerpt", "container_id": hit["section"] or hit["appendix"],
                            "role": "cfr_search_excerpt_reference", "eo_raw": r["raw"], "eo_number": r["number"],
                            "eo_suffix": r["suffix"], "occurrences": 0,
                            "snippet": eo_refs.snippet(text, r["start"], r["end"]),
                            "caution": _join(eo_refs.caution(text, r["start"], r["end"]),
                                             state_program_part(hit["title"], hit["part"]),
                                             ENDED_CAUTION if key in ended else ""),
                            "human_url": human_url(hit["title"], hit["section"] or None, hit["part"] or None, on)}
        grouped[key]["occurrences"] += 1
    return list(grouped.values())


# ------------------------------------------------------------- versions --
def version_rows(raw_bytes):
    """[(date, identifier, part)] from a versioner "versions" JSON file."""
    data = json.loads(raw_bytes.decode("utf-8"))
    out = []
    for v in data.get("content_versions", []):
        d = v.get("date") or v.get("amendment_date") or ""
        if d:
            out.append((d, str(v.get("identifier") or ""), str(v.get("part") or "")))
    return out


def changed_after(raw_bytes, cutoff=eo_refs.LEGAL_CUTOFF):
    """Sections/parts with a version in force after the cutoff -> (sections, parts, rows)."""
    rows = [r for r in version_rows(raw_bytes) if r[0] > cutoff]
    return {r[1] for r in rows if r[1]}, {r[2] for r in rows if r[2]}, len(rows)


def currency_flag(rec, rows, file_date, cutoff=eo_refs.LEGAL_CUTOFF, window_start=None):
    """How far the bulk-file text of one mention can be trusted for the cutoff date.

    "no"  -> no version of this section dated after the cutoff (and none
             between the file's amendment date and the cutoff): the file text
             should equal the text in force on the cutoff.
    other -> a reason to check the text at the point-in-time URL by hand.
    """
    if rows is None:
        return "unknown (versions list unavailable)"
    key = rec.get("section") or rec.get("appendix") or ""
    after = [r for r in rows if r[0] > cutoff]
    if key and any(r[1] == key for r in after):
        return "yes"
    if file_date and file_date < cutoff:
        if window_start and file_date < window_start:
            return "unknown (bulk file older than the versions window)"
        if key and any(file_date < r[0] <= cutoff and r[1] == key for r in rows):
            return "file_older_than_cutoff_version"
    if not rec.get("section") and rec.get("part") and any(r[2] == rec["part"] for r in after):
        return "part_has_changes"
    return "no"


# ------------------------------------------------------------- bulk XML --
def text_of(elem, skip=()):
    parts = []

    def walk(e):
        if e.tag in skip:
            if e.tail:
                parts.append(e.tail)
            return
        if e.text:
            parts.append(e.text)
        for c in e:
            walk(c)
        if e.tag in BLOCK:
            parts.append("\n")
        if e.tail and e is not elem:
            parts.append(e.tail)

    walk(elem)
    text = "".join(parts)
    text = re.sub(r"[ \t\r\f\v     ]+", " ", text)
    return re.sub(r"\s*\n\s*", "\n", text).strip()


def _sec_id(n):
    return re.sub(r"^[\s§]+", "", html.unescape(n or "")).strip()


def scan_ecfr_xml(stream, title, on=eo_refs.LEGAL_CUTOFF):
    """Yield ("amddate", str) once, then ("mention", dict) for one title file."""
    stack = []
    for ev, elem in ET.iterparse(stream, events=("start", "end")):
        if ev == "start":
            stack.append(elem)
            continue
        stack.pop()
        tag = elem.tag
        if tag == "AMDDATE":
            yield "amddate", eo_refs.parse_date(eo_refs.clean(elem.text or ""))
            continue
        if not tag.startswith("DIV"):
            continue
        part = next((a.get("N") for a in reversed(stack) if a.get("TYPE") == "PART"), None)
        if elem.get("TYPE") == "PART":
            part = elem.get("N")
        node = elem.get("NODE") or ""
        if tag in ("DIV8", "DIV9") or elem.get("TYPE") in ("SECTION", "APPENDIX"):
            is_app = elem.get("TYPE") == "APPENDIX" or tag == "DIV9"
            sec = None if is_app else _sec_id(elem.get("N"))
            app_name = ""
            if is_app:
                head = next((c for c in elem if c.tag == "HEAD"), None)
                head_text = eo_refs.clean("".join(head.itertext())) if head is not None else ""
                app_name = re.split(r"\s*[—–]\s*|\s+-\s+", head_text)[0] if head_text else _sec_id(elem.get("N"))
            if sec:
                cit = f"{title} CFR {sec}"
            elif part:
                cit = f"{title} CFR part {part}, {app_name}"
            else:
                cit = f"{title} CFR {app_name}"
            base = {"title": str(title), "part": part or "", "section": sec or "", "citation": cit,
                    "container_id": node, "human_url": human_url(title, sec, part, on), "appendix": app_name}
            main_role = "cfr_appendix_text_reference" if is_app else "cfr_text_reference"
            body = text_of(elem, skip=("CITA", "SECAUTH"))
            yield from _emit(body, dict(base, location_kind="appendix_text" if is_app else "section_text"), main_role,
                             events=True)
            for child in elem.iter():
                if child.tag in ("CITA", "SECAUTH"):
                    kind, role = CHILD_KIND[child.tag]
                    yield from _emit(text_of(child), dict(base, location_kind=kind), role)
        else:
            # Part / subpart / chapter level: authority, source, editorial notes.
            for child in list(elem):
                if child.tag.startswith("DIV") or child.tag in ("HEAD", "CFRTOC", "PTHD", "CHAPTI"):
                    continue
                kind, role = CHILD_KIND.get(child.tag, ("level_text", "cfr_other_text_reference"))
                cit = f"{title} CFR part {part}" if part else f"{title} CFR {elem.get('TYPE', '').lower()} {elem.get('N', '')}".strip()
                base = {"title": str(title), "part": part or "", "section": "", "citation": cit, "container_id": node,
                        "human_url": human_url(title, None, part, on), "appendix": ""}
                yield from _emit(text_of(child), dict(base, location_kind=kind), role)
        parent = stack[-1] if stack else None
        if parent is not None:
            parent.remove(elem)


ENDED_CAUTION = "text_says_revoked_or_superseded"


def _join(*parts):
    return ";".join(p for p in dict.fromkeys(parts) if p)


def _emit(text, base, role, events=False):
    """Yield ("mention", dict) per order named in ``text``; with ``events``,
    also ("event", dict) for "Executive Order X is revoked/superseded" text.

    An order the text itself says was revoked or superseded gets the caution
    'text_says_revoked_or_superseded', so it is not a 'still operating' lead.
    """
    refs = eo_refs.find_eo_refs(text)
    if not refs:
        return
    passive = eo_refs.editorial_events(text)
    active = eo_refs.active_events(text)
    ended = {(e["subject"]["number"], e["subject"]["suffix"].upper()) for e in passive + active if e["verb"] != "amended"}
    grouped = {}
    for r in refs:
        key = (r["number"], r["suffix"].upper())
        if key not in grouped:
            grouped[key] = dict(base, role=role, eo_raw=r["raw"], eo_number=r["number"], eo_suffix=r["suffix"],
                                occurrences=0, snippet=eo_refs.snippet(text, r["start"], r["end"]),
                                caution=_join(eo_refs.caution(text, r["start"], r["end"]),
                                              state_program_part(base["title"], base["part"]),
                                              ENDED_CAUTION if key in ended else ""))
        grouped[key]["occurrences"] += 1
    for m in grouped.values():
        yield "mention", m
    if not events:
        return
    for e in passive + [a for a in active if a["actor"]]:
        if e["actor"] or e["verb"] in ("revoked", "superseded", "rescinded"):
            yield "event", eo_refs.make_event(e, dict(base, note_role="cfr_text", note_id=""))


def state_program_part(title, part):
    """CFR parts that approve State plans/programs, where "Executive Order"
    usually means a Governor's order: 40 CFR 52 and 62 (air plans), 40 CFR 147
    and 272 (State programs), 30 CFR 900-955 (State mining programs)."""
    try:
        t, p = int(str(title)), int(str(part).split("-")[0].split(".")[0])
    except ValueError:
        return ""
    if (t == 40 and p in (52, 62, 147, 272, 282)) or (t == 30 and 900 <= p <= 955):
        return "state_plan_approval_part"
    return ""
