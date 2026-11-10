"""Attributed plain-text extracts of the U.S. Code notes and sections that name orders.

The claim kit cites current law only from an exact slice of a held UTF-8 text
file, never from a JSON/JSONL record or a whitespace-normalized snippet. This
module writes each note (or section) text the scanner read as its own .txt
file and declares it in SOURCES.jsonl by its own identity (sha256 and bytes of
the extract) with the release-point ZIP it was cut from in ``extracted_from``
(url and sha256 of the ZIP; the member XML and its sha256 are in page_or_item).
It points every current-law lead about that note or section at the extract
(text_path, text_sha256 and the exact character span of its quoted words).
The claim kit accepts such a lead only through that declaration: same ZIP,
same page_or_item, matching pins.

Nothing here decides legal status. A lead with an extract is still a lead.

``python usc_extracts.py OUTPUT_DIR`` regenerates the extracts and the
updated FRAGMENTS.jsonl / SOURCES.jsonl / SUMMARY.json offline from the
committed USC_EO_NOTES.jsonl (printed executive-order notes). A network run
of job.py also writes extracts for the other notes and sections that carry a
predicate lead.
"""

import hashlib
import json
import pathlib
import re
import sys

EXTRACT_ROUTE = "usc_release_point_xml_zip_text_extract"
NOTE_DIR = "usc-notes"
SECTION_DIR = "usc-sections"
NOTE_ID_RE = re.compile(r"\[USLM note id ([^\]\s]+)\]")
MEMBER_RE = re.compile(r";\s*([^;]+?\.xml) \(sha256 ([0-9a-f]{64})\) in ([^;]+)$")
_UNSAFE = re.compile(r"[^0-9A-Za-z_.-]")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_name(value):
    name = _UNSAFE.sub("_", str(value or "")).strip("._")
    return name[:120] or "x"


# --- locate: identical copy in jobs/current-law/usc_extracts.py and jobs/claim-kit/current_evidence.py
# (the claim kit must not import producer code: its compiler files are hash-pinned; the copies are kept
# textually identical, checked by jobs/claim-kit/test_current_records.py).
MIN_COLLAPSED_QUOTE = 12


def _unique(hay, needle):
    start = hay.find(needle)
    if start < 0 or hay.find(needle, start + 1) >= 0:
        return None
    return start


def _collapse(text):
    """Text with each whitespace run replaced by one space, and each kept character's index in text."""
    chars, index, space = [], [], False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not space:
                chars.append(" ")
                index.append(i)
            space = True
        else:
            chars.append(ch)
            index.append(i)
            space = False
    return "".join(chars), index


def locate(text, quote, collapsed=None):
    """(start, end) of the one place ``quote`` occurs in ``text``, else None.

    Tried in order: 1. the quote as given; 2. the quote without a leading or
    trailing "..." (snippet ellipses); 3. the quote with each whitespace run
    read as one space and " | " (a heading joined to a status line) read as a
    line break. Every step needs exactly one occurrence both as written and
    with whitespace runs collapsed in the text and the quote, so "1234 5"
    never matches "12345" and an exact hit cannot hide a second, differently
    spaced one. The caller quotes text[start:end], an exact slice of the held
    bytes, never the snippet. ``collapsed`` is _collapse(text), if cached.
    """
    if not isinstance(text, str) or not isinstance(quote, str) or not quote.strip():
        return None
    norm, index = collapsed if collapsed is not None else _collapse(text)

    def once_collapsed(q):
        needle = _collapse(q)[0].strip()
        return bool(needle) and _unique(norm, needle) is not None

    start = _unique(text, quote)
    if start is not None and once_collapsed(quote):
        return start, start + len(quote)
    trimmed = quote.strip()
    if trimmed.startswith("..."):
        trimmed = trimmed[3:]
    if trimmed.endswith("..."):
        trimmed = trimmed[:-3]
    trimmed = trimmed.strip()
    if not trimmed:
        return None
    start = _unique(text, trimmed)
    if start is not None and once_collapsed(trimmed):
        return start, start + len(trimmed)
    needle = _collapse(trimmed.replace(" | ", "\n"))[0].strip()
    if len(needle.replace(" ", "")) < MIN_COLLAPSED_QUOTE:
        return None
    start = _unique(norm, needle)
    if start is None:
        return None
    return index[start], index[start + len(needle) - 1] + 1
# --- end of locate copy


def member_of(page_or_item):
    m = MEMBER_RE.search(page_or_item or "")
    return (m.group(1), m.group(2), m.group(3).strip()) if m else (None, None, None)


def note_id_of(page_or_item):
    m = NOTE_ID_RE.search(page_or_item or "")
    return m.group(1) if m else None


class Extracts:
    """Collects one text per page_or_item (one note or one section of one member XML)."""

    def __init__(self):
        self.items = {}
        self.ambiguous = set()

    def add(self, page_or_item, text, source_id, citation, kind, note_id="", container_id="", printed_ids=()):
        if not page_or_item or not isinstance(text, str) or not text:
            return
        if page_or_item in self.ambiguous:
            return
        old = self.items.get(page_or_item)
        if old is not None:
            if old["text"] != text:
                # Two different texts under one locator: cite neither.
                self.ambiguous.add(page_or_item)
                del self.items[page_or_item]
                return
            old["printed_ids"].update(printed_ids)
            return
        self.items[page_or_item] = {"text": text, "source_id": source_id, "citation": citation, "kind": kind,
                                    "note_id": note_id, "container_id": container_id,
                                    "printed_ids": set(printed_ids)}

    def path_for(self, poi, item):
        if item["kind"] == "note" and item["note_id"]:
            return f"{NOTE_DIR}/{safe_name(item['note_id'])}.txt"
        key = hashlib.sha1(poi.encode("utf-8")).hexdigest()[:10]
        return f"{SECTION_DIR}/{safe_name(item['container_id'] or item['citation'])}-{key}.txt"

    def write(self, out, sources):
        """Write the .txt files; return {page_or_item: (rel_path, text, text_sha256)} and declarations."""
        out = pathlib.Path(out)
        held, declarations, used = {}, [], set()
        for poi in sorted(self.items):
            item = self.items[poi]
            zip_rec = sources.get(item["source_id"])
            if not zip_rec or not zip_rec.get("sha256") or not zip_rec.get("url"):
                continue
            rel = self.path_for(poi, item)
            if rel in used:
                continue  # never let two locators share one file
            used.add(rel)
            raw = item["text"].encode("utf-8")
            path = out / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
            digest = sha256(raw)
            member, member_sha, zip_name = member_of(poi)
            declarations.append({
                "source_id": f"{item['source_id']}:{item['kind']}:{item['note_id'] or item['container_id'] or rel}",
                "instrument_ids": [],
                # The record's own identity is the extract (sha256 and bytes of the .txt), so readers
                # that key held copies by sha256 never take one note for the whole ZIP; the ZIP the
                # text was cut from is extracted_from, which is how the claim kit reaches it.
                "url": zip_rec["url"], "sha256": digest, "bytes": len(raw),
                "extracted_from": {"url": zip_rec["url"], "sha256": zip_rec["sha256"], "bytes": zip_rec.get("bytes")},
                "content_type": "text/plain; charset=utf-8", "retrieved_utc": zip_rec.get("retrieved_utc"),
                "route": EXTRACT_ROUTE, "page_or_item": poi, "text_path": rel, "text_sha256": digest,
                # item_extract names how a lead finds this extract: by its exact page_or_item
                # (one note or section of one member XML), never by citation alone, since many
                # notes share one "N U.S.C. S note" citation.
                "cache_path": None, "item_extract": "page_or_item", "citation": item["citation"],
                "note_id": item["note_id"] or None, "container_id": item["container_id"] or None,
                "member": member, "member_sha256": member_sha, "zip": zip_name,
                "printed_instrument_ids": sorted(item["printed_ids"]),
                "notes": ("Exact plain text of one U.S. Code " + ("note" if item["kind"] == "note" else "section")
                          + " as read from the USLM XML member named in page_or_item (line breaks between block "
                          "elements, spaces collapsed), inside the release-point ZIP named in extracted_from "
                          "(url, sha256); sha256 and bytes here are those of this extract. It is an "
                          "editorial print of the Office of the Law Revision Counsel. instrument_ids is empty: "
                          "this text is not any order's own text; printed_instrument_ids lists orders the note "
                          "prints. No legal finding."),
            })
            held[poi] = (rel, item["text"], digest)
        return held, declarations


def attach(fragments, held):
    """Point U.S. Code current-predicate leads at their extract with an exact span.

    ``held`` must hold only extracts whose bytes match their declaration. Every
    earlier text_path, text_sha256 and span is removed first; a lead whose item
    is not held keeps none. A lead whose item is held gets text_path and
    text_sha256, and text/char_start/char_end only when its snippet is located
    exactly once; without a span the claim kit locates the snippet itself and
    reports a gap when it cannot. Returns counts.
    """
    counts = {"usc_leads": 0, "with_extract": 0, "located": 0}
    for frag in fragments:
        if frag.get("kind") != "current_predicate_candidates":
            continue
        for entry in frag.get("data", []):
            if entry.get("system") != "usc":
                continue
            counts["usc_leads"] += 1
            for key in ("text", "char_start", "char_end", "text_sha256", "text_path"):
                entry.pop(key, None)
            poi = (entry.get("source") or {}).get("page_or_item")
            if poi not in held:
                continue
            rel, text, digest = held[poi]
            counts["with_extract"] += 1
            entry["text_path"] = rel
            entry["text_sha256"] = digest
            span = locate(text, entry.get("snippet"))
            if span:
                start, end = span
                entry.update(text=text[start:end], char_start=start, char_end=end)
                counts["located"] += 1
    return counts


def from_eo_notes(extracts, notes):
    for n in notes:
        extracts.add(n.get("page_or_item"), n.get("text"), n.get("source_id"), n.get("citation", ""), "note",
                     note_id=n.get("note_id", ""), printed_ids=n.get("instrument_ids") or ())


def merge_sources(rows, declarations):
    """Old extract declarations out, new ones in after the record they extract from."""
    kept = [r for r in rows if r.get("route") != EXTRACT_ROUTE]
    return kept + declarations


def _jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")


def regenerate(out):
    """Offline: rebuild extracts, SOURCES.jsonl, FRAGMENTS.jsonl from committed USC_EO_NOTES.jsonl."""
    out = pathlib.Path(out)
    notes = _jsonl(out / "USC_EO_NOTES.jsonl")
    sources = _jsonl(out / "SOURCES.jsonl")
    frags = _jsonl(out / "FRAGMENTS.jsonl")
    by_id = {r["source_id"]: r for r in sources if r.get("route") != EXTRACT_ROUTE}
    ex = Extracts()
    from_eo_notes(ex, notes)
    held, declarations = ex.write(out, by_id)
    # Section and other-note extracts of an earlier network run cannot be
    # rebuilt from USC_EO_NOTES.jsonl: keep each one whose held bytes still
    # match its declaration, drop the rest.
    kept = []
    for r in sources:
        if r.get("route") != EXTRACT_ROUTE or r.get("page_or_item") in held:
            continue
        path = out / str(r.get("text_path") or "")
        if r.get("text_path") and path.is_file() and sha256(path.read_bytes()) == r.get("text_sha256"):
            held[r["page_or_item"]] = (r["text_path"], path.read_bytes().decode("utf-8"), r["text_sha256"])
            kept.append(r)
    declarations = sorted(declarations + kept, key=lambda r: r["page_or_item"])
    counts = attach(frags, held)
    counts.update(extracts=len(declarations), ambiguous_locators=len(ex.ambiguous))
    _write_jsonl(out / "SOURCES.jsonl", merge_sources(sources, declarations))
    _write_jsonl(out / "FRAGMENTS.jsonl", frags)
    summary_path = out / "SUMMARY.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["usc_text_extracts"] = dict(counts, regenerated_offline_from="USC_EO_NOTES.jsonl")
        summary_path.write_bytes(json.dumps(summary, indent=1, ensure_ascii=False).encode("utf-8"))
    return counts


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python usc_extracts.py OUTPUT_DIR")
    print(json.dumps(regenerate(sys.argv[1]), indent=1))
