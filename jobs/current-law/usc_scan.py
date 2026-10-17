"""U.S. Code part: pick the release point, then stream-read USLM XML.

The Office of the Law Revision Counsel (OLRC) publishes the Code as "release
points" (one per batch of new public laws). Each title is one USLM XML file.
Executive orders appear in three ways:

* the order's text (or a status line about it) printed as a note under a
  section, usually with topic="executiveOrder";
* other notes (editorial, statutory, cross references) naming an order;
* the statute text itself naming an order.

``scan_uslm`` yields plain dicts; mapping to order ids and building claim
fragments happens in build.py.
"""

import re
import urllib.parse
import xml.etree.ElementTree as ET

import eo_refs

BASE = "https://uscode.house.gov/"
H3_RE = re.compile(r"<h3[^>]*>\s*Public Law\s+(\d+)-(\d+)\s*([^<(]*)\((\d{2})/(\d{2})/(\d{4})\)([^<]*)</h3>", re.I)
ZIP_RE = re.compile(r'href="([^"]*releasepoints/us/pl/(\d+)/([0-9a-zA-Z]+)/xml_usc([0-9a-zA-Z]+)@([0-9a-zA-Z-]+)\.zip)"')

EDITORIAL_TOPICS = {"amendments", "codification", "priorProvisions", "dispositionOfSections", "referencesInText",
                    "changeOfName", "editorialNotes", "removalDescription", "transferOfFunctions"}
EXEC_TOPICS = {"executiveOrder", "executiveMemo", "execDoc", "reorganizationPlan", "proclamation",
               "presidentialDocument", "determination"}
BLOCK = {"p", "heading", "num", "chapeau", "continuation", "content", "subsection", "paragraph", "subparagraph",
         "clause", "subclause", "item", "section", "tr", "signature", "note", "quotedContent", "level"}
AMEND_SELF_RE = re.compile(r"\b(?:is|are)\s+(?:hereby\s+)?(?:further\s+)?amended\b", re.I)


# ------------------------------------------------------- release points --
def parse_release_points(page_html, page_url):
    """Return release points listed on a download page, newest first."""
    heads = list(H3_RE.finditer(page_html))
    points = []
    for i, m in enumerate(heads):
        block = page_html[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(page_html)]
        zips = {}
        all_zip = None
        for z in ZIP_RE.finditer(block):
            url = urllib.parse.urljoin(page_url, z.group(1))
            if z.group(4).lower() == "all":
                all_zip = url
            else:
                zips[z.group(4)] = url
        points.append({
            "id": f"{m.group(1)}-{m.group(2)}",
            "label": eo_refs.clean(re.sub(r"<[^>]+>", "", m.group(0))),
            "date": f"{m.group(6)}-{m.group(4)}-{m.group(5)}",
            "all_zip_url": all_zip,
            "title_zip_urls": zips,
            "listed_on": page_url,
        })
    return points


# Release points whose "current through" law date is known without the
# listing page (the OLRC site lists only the newest one or two).
KNOWN_RELEASE_DATES = {"119-121": "2026-10-09", "119-118": "2026-09-30"}
# Title codes published in release point 119-121 (from its download page).
DEFAULT_TITLE_CODES = ["01", "02", "03", "04", "05", "05a", "06", "07", "08", "09", "10", "11", "11a", "12", "13",
                       "14", "15", "16", "17", "18", "18a", "19", "20", "21", "22", "23", "24", "25", "26", "27",
                       "28", "28a", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41",
                       "42", "43", "44", "45", "46", "47", "48", "49", "50", "50a", "51", "52", "54"]
ZIP_PATTERN = BASE + "download/releasepoints/us/pl/{congress}/{law}/xml_usc{code}@{rp}.zip"


def norm_title_code(code):
    """'5' -> '05', '05A' -> '05a', 'All' -> 'all'."""
    c = str(code).strip().lower()
    m = re.match(r"^(\d+)([a-z]?)$", c)
    return f"{int(m.group(1)):02d}{m.group(2)}" if m else c


def _rp_key(rp_id):
    try:
        return [int(x) for x in rp_id.split("-")]
    except ValueError:
        return [0]


def release_point_from_id(rp_id, date=None, title_codes=None):
    """Build a release point from the stable OLRC URL pattern (no listing needed)."""
    m = re.match(r"^(\d+)-(\d+[a-z]*)$", rp_id or "")
    if not m:
        raise ValueError(f"bad release point id {rp_id!r} (expected e.g. 119-121)")
    congress, law = m.groups()
    codes = title_codes or DEFAULT_TITLE_CODES
    return {"id": rp_id, "label": f"Public Law {rp_id}" + (f" ({date})" if date else " (current-through date unknown)"),
            "date": date, "all_zip_url": ZIP_PATTERN.format(congress=congress, law=law, code="All", rp=rp_id),
            "title_zip_urls": {c: ZIP_PATTERN.format(congress=congress, law=law, code=c, rp=rp_id) for c in codes},
            "listed_on": None}


def choose_release(points, cutoff=eo_refs.LEGAL_CUTOFF, override=None, pinned=None):
    """Pick the release point; return (point, why, problems).

    * ``override`` (USC_RELEASE_POINT) or ``pinned`` (job default) names a
      point; it is used even when the listing no longer shows it, with URLs
      built from the stable OLRC pattern. ``override`` may be "id@YYYY-MM-DD"
      to give the current-through date of an unlisted point.
    * "auto" (or neither given) means: latest listed point current through a
      law dated on or before the cutoff; if none is listed, the earliest later
      one, with a problem saying it post-dates the cutoff.
    The listing is also used as a check: a problem is reported when a newer
    point on or before the cutoff exists than the one chosen.
    """
    problems = []
    usable = [p for p in points if p.get("date") and p["date"] <= cutoff and (p["all_zip_url"] or p["title_zip_urls"])]
    best_listed = max(usable, key=lambda p: (p["date"], _rp_key(p["id"]))) if usable else None
    want = override or pinned
    if want and want.lower() != "auto":
        rp_id, _, given_date = want.partition("@")
        listed = next((p for p in points if p["id"] == rp_id), None)
        if listed:
            rp, why = listed, f"{'override (USC_RELEASE_POINT)' if override else 'pinned default'}; listed on {listed['listed_on']}"
        else:
            date = given_date or KNOWN_RELEASE_DATES.get(rp_id)
            rp = release_point_from_id(rp_id, date)
            why = (f"{'override (USC_RELEASE_POINT)' if override else 'pinned default'}; not on the current listing pages, "
                   "so the ZIP URLs were built from the stable OLRC pattern")
            if not date:
                problems.append(f"USC release point {rp_id}: current-through date unknown; U.S. Code entries get checked_through null")
        if best_listed and best_listed["id"] != rp["id"] and (rp.get("date") or "") <= best_listed["date"] \
                and _rp_key(best_listed["id"]) > _rp_key(rp["id"]):
            problems.append(f"A newer U.S. Code release point on or before the cutoff is listed: {best_listed['id']} "
                            f"(current through {best_listed['date']}); consider USC_RELEASE_POINT={best_listed['id']}")
    elif best_listed:
        rp, why = best_listed, "latest listed release point current through a law enacted on or before the cutoff"
    else:
        later = sorted([p for p in points if p["all_zip_url"] or p["title_zip_urls"]], key=lambda p: (p["date"] or "", _rp_key(p["id"])))
        if not later:
            raise ValueError("no release points found")
        rp, why = later[0], "NO release point on/before the cutoff is listed; using the earliest available (post-cutoff) one"
    if rp.get("date") and rp["date"] > cutoff:
        problems.append(f"USC release point {rp['id']} is current through {rp['date']}, AFTER the cutoff {cutoff}: "
                        "its text includes later laws, so U.S. Code entries get checked_through null")
    return rp, why, problems


def usc_checked_through(rp, cutoff=eo_refs.LEGAL_CUTOFF):
    """Date the U.S. Code text is known current through, for claim entries (or None)."""
    d = rp.get("date")
    if not d or d > cutoff:
        return None
    return d


def usc_currency_note(rp, cutoff=eo_refs.LEGAL_CUTOFF):
    d = rp.get("date")
    if not d:
        return f"U.S. Code release point {rp['id']}: its current-through date is unknown, so currency at {cutoff} is not established."
    if d > cutoff:
        return (f"U.S. Code release point {rp['id']} is current through a law of {d}, AFTER the cutoff {cutoff}; "
                "the text may include later changes and is NOT evidence of the text in force on the cutoff.")
    gap = "" if d == cutoff else f"; laws enacted after {d} and on or before {cutoff}, if any, are not reflected"
    return f"U.S. Code release point {rp['id']} is current through Pub. L. {rp['id']} ({d}){gap}."


# ---------------------------------------------------------------- USLM --
def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def text_of(elem):
    """Plain text with line breaks between block elements."""
    parts = []

    def walk(e):
        tag = local(e.tag)
        if tag in ("toc", "layout"):
            return
        if e.text:
            parts.append(e.text)
        for c in e:
            walk(c)
            if c.tail:
                parts.append(c.tail)
        if tag in BLOCK:
            parts.append("\n")

    walk(elem)
    text = "".join(parts)
    text = re.sub(r"[ \t\r\f\v     ]+", " ", text)
    return re.sub(r"\s*\n\s*", "\n", text).strip()


_CITE_KINDS = {"sch": "subch. ", "spt": "subpt. ", "st": "subtitle ", "art": "art. ", "ch": "ch. ", "pt": "pt. ",
               "r": "rule ", "d": "div. ", "s": ""}
_CITE_COMP_RE = re.compile(r"(sch|spt|st|art|ch|pt|r|d|s)(.+)$")  # longest prefixes first


def _cite_one(identifier):
    m = re.match(r"/us/usc/t(\d+)(a?)(?:/(.*))?$", identifier or "") or re.match(r"/us/usc/t(\w+?)()(?:/(.*))?$", identifier or "")
    if not m:
        return None, identifier or ""
    title = m.group(1) + (" App." if m.group(2) else "")
    rest = m.group(3) or ""
    if not rest:
        return title, "(title level)"
    bits = []
    for comp in rest.split("/"):
        cm = _CITE_COMP_RE.match(comp)
        bits.append(_CITE_KINDS[cm.group(1)] + cm.group(2) if cm else comp)
    return title, ", ".join(bits)


def cite(identifier):
    """'/us/usc/t5/s3301' -> '5 U.S.C. 3301'; '/us/usc/t50/ch15' -> '50 U.S.C. ch. 15';
    '/us/usc/t10/stA/ptII/ch57' -> '10 U.S.C. subtitle A, pt. II, ch. 57';
    '/us/usc/t42/s2031 /us/usc/t42/s2032' -> '42 U.S.C. 2031, 2032'."""
    parts = (identifier or "").split()
    if not parts:
        return ""
    out, last_title = [], None
    for p in parts:
        title, rest = _cite_one(p)
        if title is None:
            out.append(rest)
        elif title == last_title:
            out.append(rest)
        else:
            out.append(f"{title} U.S.C. {rest}")
        last_title = title
    return ", ".join(out)


def title_of(identifier):
    m = re.match(r"/us/usc/t(\w+)", identifier or "")
    return m.group(1) if m else ""


ENDED_CAUTION = "text_says_revoked_or_superseded"


def join_caution(*parts):
    return ";".join(p for p in dict.fromkeys(parts) if p)


def _refs_in(text, base_role, **extra):
    """Group references by order number -> one mention per (number, suffix).

    An order the same text says was revoked or superseded gets the caution
    'text_says_revoked_or_superseded' (so it is not a 'still operating' lead).
    """
    grouped = {}
    refs = eo_refs.find_eo_refs(text)
    ended = eo_refs.ended_subject_keys(text) if refs else set()
    for r in refs:
        key = (r["number"], r["suffix"].upper())
        if key not in grouped:
            grouped[key] = dict(extra, role=base_role, eo_raw=r["raw"], eo_number=r["number"], eo_suffix=r["suffix"],
                                occurrences=0, snippet=eo_refs.snippet(text, r["start"], r["end"]),
                                caution=join_caution(eo_refs.caution(text, r["start"], r["end"]),
                                                     ENDED_CAUTION if key in ended else ""))
        grouped[key]["occurrences"] += 1
    return grouped


def _event(e, base, actor_fallback=None):
    return eo_refs.make_event(e, base, actor_fallback)


def _bracket_event(subject_ref, b, base):
    e = {"subject": subject_ref, "verb": b["verb"], "actor": b["actor"], "sentence": b["sentence"]}
    return eo_refs.make_event(e, dict(base, note_role="bracketed_editorial_insert", scope_hint=b["scope_text"]))


def scan_uslm(stream, member_name):
    """Yield ("mention" | "event" | "eo_note", dict) for one USLM title file."""
    stack = []
    cross = []  # current cross-heading for each open <notes> container
    last_subject = {}  # container identifier -> actor dict of the last printed order there
    for ev, elem in ET.iterparse(stream, events=("start", "end")):
        tag = local(elem.tag)
        if ev == "start":
            stack.append(elem)
            if tag == "notes":
                cross.append("")
            continue
        stack.pop()
        if tag == "notes" and cross:
            cross.pop()
            continue
        in_note = any(local(a.tag) == "note" for a in stack)
        in_toc = any(local(a.tag) in ("toc", "quotedContent") for a in stack)
        if tag == "note" and not in_note and not in_toc:
            if elem.get("role") == "crossHeading":
                if cross:
                    cross[-1] = elem.get("topic") or ""
                continue
            ident = next((a.get("identifier") for a in reversed(stack) if a.get("identifier")), "")
            yield from _note(elem, ident, cross[-1] if cross else "", member_name, last_subject)
            parent = stack[-1] if stack else None
            if parent is not None:
                parent.remove(elem)
        elif tag == "section" and not in_note and not in_toc:
            ident = elem.get("identifier") or ""
            body = text_of(elem)
            base = {"member": member_name, "container_id": ident, "title": title_of(ident),
                    "citation": cite(ident), "location_kind": "section_text", "note_topic": "", "note_heading": "",
                    "note_id": "", "crossheading": ""}
            for m in _refs_in(body, "statutory_text_reference", **base).values():
                yield "mention", m
            for e in eo_refs.editorial_events(body):
                yield "event", _event(e, base, {"kind": "statute_text", "text": cite(ident), "date": None, "fr": None,
                                                "scope_text": ""})
            parent = stack[-1] if stack else None
            if parent is not None:
                parent.remove(elem)
        elif tag in ("chapter", "subchapter", "part", "subpart", "title", "subtitle", "division") and not in_note:
            parent = stack[-1] if stack else None
            if parent is not None and tag != "title":
                parent.remove(elem)




STATUS_START_RE = re.compile(r"^(?:Ex\.\s*Ord\.\s*No\.|Executive Order No\.)\s*\d")


def _keep_event(e):
    """Keep an ending statement only if someone acted or the verb is a clear revocation."""
    return bool(e.get("actor")) or e["verb"] in ("revoked", "superseded", "rescinded")


def _note(elem, ident, crossheading, member, last_subject):
    topic = elem.get("topic") or ""
    head_el = next((c for c in elem if local(c.tag) == "heading"), None)
    heading = eo_refs.clean(text_of(head_el)) if head_el is not None else ""
    full = text_of(elem)
    if not eo_refs.find_eo_refs(full):
        return
    base = {"member": member, "container_id": ident, "title": title_of(ident), "citation": cite(ident) + " note",
            "location_kind": "note", "note_topic": topic, "note_heading": heading[:300],
            "note_id": elem.get("id") or "", "crossheading": crossheading}
    first_p = next((c for c in elem if local(c.tag) == "p"), None)
    status = eo_refs.clean(text_of(first_p)) if first_p is not None else ""
    heading_refs = eo_refs.find_eo_refs(heading)
    is_eo_note = (topic == "executiveOrder"
                  or bool(re.match(r"(Ex\.\s*Ord\.|Executive Order)", heading, re.I) and heading_refs)
                  or bool((crossheading == "execDoc" or topic in EXEC_TOPICS) and STATUS_START_RE.match(status)))
    container_actor = last_subject.get(ident)
    if not is_eo_note:
        if topic == "referencesInText":
            role = "references_in_text_note"
        elif topic in EDITORIAL_TOPICS or crossheading == "editorialNotes":
            role = "editorial_note_reference"
        elif topic in EXEC_TOPICS or crossheading == "execDoc":
            role = "executive_document_note_reference"
        elif crossheading == "statutoryNotes":
            role = "statutory_note_reference"
        else:
            role = "other_note_reference"
        for m in _refs_in(full, role, **base).values():
            yield "mention", m
        # The order printed just above acted only when this note continues its
        # text; a note that names a statute (act, Pub. L., Stat., "provided
        # that") gets the statute as actor from editorial_events instead.
        fallback = container_actor if role == "executive_document_note_reference" else None
        for e in eo_refs.editorial_events(full):
            if _keep_event(e) or fallback:
                yield "event", _event(e, dict(base, note_role=role), fallback)
        if container_actor and role == "executive_document_note_reference":
            # A continuation of the order printed just above ("Part I ... [Superseded by ...]").
            for b in eo_refs.bracket_events(full):
                yield "event", _bracket_event(container_actor["ref"], b, base)
        return

    # --- an executive-order note: heading, status line, then (maybe) text --
    subjects = heading_refs or eo_refs.find_eo_refs(status)[:1]
    kind = eo_refs.status_line_kind(status)
    subject_role = {"printed_text": "printed_eo_text", "ended_status_line": "eo_note_ended_status",
                    "status_or_cross_reference": "eo_note_status_or_cross_reference"}[kind]
    subject_keys = set()
    for s in subjects:
        subject_keys.add((s["number"], s["suffix"].upper()))
        yield "mention", dict(base, role=subject_role, eo_raw=s["raw"], eo_number=s["number"], eo_suffix=s["suffix"],
                              occurrences=1, snippet=(heading + " | " + status)[:420])
    acting = set()
    for e in eo_refs.editorial_events(status):
        if not _keep_event(e):
            continue
        yield "event", _event(e, dict(base, note_role=subject_role))
        if e["actor"] and e["actor"].get("kind") == "executive_order":
            acting.add((e["actor"]["ref"]["number"], e["actor"]["ref"]["suffix"].upper()))
    amenders = eo_refs.amendments_listed(status)
    for a in amenders:
        for s in subjects:
            yield "event", _event({"subject": s, "verb": "amended", "actor": a, "sentence": a["segment"]},
                                  dict(base, note_role=subject_role))
    amending = {(a["ref"]["number"], a["ref"]["suffix"].upper()) for a in amenders if a["kind"] == "executive_order"}
    for key, m in _refs_in(status, "status_line_other_reference", **base).items():
        if key in subject_keys:
            continue
        if key in acting:
            m["role"] = "ending_order_in_status_line"
        elif key in amending:
            m["role"] = "amending_order_in_status_line" if kind == "printed_text" else "amending_order_in_ended_status_line"
        yield "mention", m
    # Body = everything after heading and status line.
    body = full
    for part in (heading, status):
        idx = body.find(part[:60]) if part else -1
        if idx >= 0:
            body = body[idx + len(part):]
    body = body.strip()
    for key, m in _refs_in(body, "mentioned_in_printed_eo_text", **base).items():
        if key in subject_keys:
            continue
        yield "mention", m
    if kind == "printed_text" and subjects:
        # The printed order (as amended): it is the actor of revocations in its
        # own text, unless the text was inserted by a later amending order,
        # which build.add_event works out from "amenders".
        self_actor = {"kind": "executive_order", "ref": subjects[0], "date": eo_refs.parse_date(status),
                      "fr": eo_refs.parse_fr(status), "scope_text": "the printed order itself",
                      "amenders": [a for a in amenders if a["kind"] == "executive_order"]}
        last_subject[ident] = self_actor
        body_base = dict(base, note_role="printed_eo_text_body")
        for e in eo_refs.editorial_events(body):
            if (e["subject"]["number"], e["subject"]["suffix"].upper()) in subject_keys:
                continue
            yield "event", _event(e, body_base, self_actor)
        for e in eo_refs.active_events(body):
            # "This order supersedes Executive Order 13560": the printed order acted.
            if (e["subject"]["number"], e["subject"]["suffix"].upper()) in subject_keys:
                continue
            if e["actor"] or e["self_ref"]:
                yield "event", _event(e, dict(body_base, note_role="printed_eo_text_body_active_voice"),
                                      self_actor if e["self_ref"] else None)
        for a, b, sent in eo_refs.sentences(body):
            am = AMEND_SELF_RE.search(sent)
            if am:
                refs = [r for r in eo_refs.find_eo_refs(sent) if (r["number"], r["suffix"].upper()) not in subject_keys]
                if refs and refs[0]["start"] < am.start():
                    yield "event", _event({"subject": refs[0], "verb": "amended", "actor": self_actor,
                                           "sentence": eo_refs.clean(sent)}, body_base)
        for b in eo_refs.bracket_events(body):
            # "[Revoked by ...]" inside the printed order: part of the order ended.
            yield "event", _bracket_event(subjects[0], b, base)
        yield "eo_note", {"member": member, "note_id": base["note_id"], "citation": base["citation"],
                          "heading": heading, "subjects": [eo_refs.normalized(s["number"], s["suffix"]) for s in subjects],
                          "status_line": status, "text": full}
