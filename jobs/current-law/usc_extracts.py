"""Attributed plain-text extracts of the U.S. Code notes and sections that name orders.

The claim kit cites current law only from an exact slice of a held UTF-8 text
file, never from a JSON/JSONL record or a whitespace-normalized snippet. This
module writes each note (or section) text the scanner read as its own .txt
file, declares it in SOURCES.jsonl under the release-point ZIP it came from
(url and sha256 of the ZIP, plus the member XML and its sha256 in
page_or_item), and points every current-law lead about that note or section
at the extract with the exact character span of its quoted words.

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


def _compact(text):
    """Text without whitespace, and for each kept character its index in text."""
    chars, index = [], []
    for i, ch in enumerate(text):
        if not ch.isspace():
            chars.append(ch)
            index.append(i)
    return "".join(chars), index


def _unique(hay, needle):
    start = hay.find(needle)
    if start < 0 or hay.find(needle, start + 1) >= 0:
        return None
    return start


def locate(text, quote):
    """(start, end) of the one place ``quote`` occurs in ``text``, else None.

    Tried in order, each requiring exactly one occurrence:
    1. the quote as given;
    2. the quote without a leading or trailing "..." (snippet ellipses);
    3. the same characters ignoring whitespace (snippets collapse line breaks
       and join a heading to a status line with " | ").
    The returned span always slices the held text itself; the caller quotes
    ``text[start:end]``, never the snippet.
    """
    if not isinstance(text, str) or not isinstance(quote, str) or not quote.strip():
        return None
    start = _unique(text, quote)
    if start is not None:
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
    if start is not None:
        return start, start + len(trimmed)
    needle, _ = _compact(trimmed.replace(" | ", " "))
    if len(needle) < 12:
        return None  # too short to identify one place without whitespace
    hay, index = _compact(text)
    start = _unique(hay, needle)
    if start is None:
        return None
    return index[start], index[start + len(needle) - 1] + 1


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
                "url": zip_rec["url"], "sha256": zip_rec["sha256"], "bytes": zip_rec.get("bytes"),
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
                          "elements, spaces collapsed), inside the release-point ZIP at url/sha256. It is an "
                          "editorial print of the Office of the Law Revision Counsel. instrument_ids is empty: "
                          "this text is not any order's own text; printed_instrument_ids lists orders the note "
                          "prints. No legal finding."),
            })
            held[poi] = (rel, item["text"], digest)
        return held, declarations


def attach(fragments, held):
    """Point U.S. Code current-predicate leads at their extract with an exact span.

    Returns counts. A lead whose quote cannot be located exactly once keeps
    text_path (so the claim kit reports the gap) but gets no text or span.
    """
    counts = {"usc_leads": 0, "with_extract": 0, "located": 0}
    for frag in fragments:
        if frag.get("kind") != "current_predicate_candidates":
            continue
        for entry in frag.get("data", []):
            if entry.get("system") != "usc":
                continue
            counts["usc_leads"] += 1
            for key in ("text", "char_start", "char_end", "text_sha256"):
                entry.pop(key, None)
            if str(entry.get("text_path") or "").startswith("USC_EO_NOTES.jsonl#"):
                entry.pop("text_path")
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
