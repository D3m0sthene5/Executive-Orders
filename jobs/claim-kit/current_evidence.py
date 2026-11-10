"""Normalize held current-law quote leads without treating JSON as legal text.

No downloads or writes. An unresolved pointer remains a lead with an explicit
``evidence_gap`` and no citable quote fields. This module cannot make a current
predicate or extend its producer's currency date.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

SHA = re.compile(r"[a-fA-F0-9]{64}\Z")
TEXT_SUFFIXES = {".txt", ".xml", ".html", ".htm"}
# Producer manifests whose rows may declare attributed legal-text extracts.
# A row is keyed by its own (url, sha256); an ``item_extract`` row also by the
# (url, sha256) of the official artifact it was cut from (``extracted_from``).
DECLARATION_MANIFESTS = ("jobs/current-law/output/SOURCES.jsonl",
                         "jobs/theophilus-sources/output/SOURCES.jsonl")


def _safe(root, base, name):
    if not isinstance(name, str) or not name or "#" in name:
        return None
    name = name.replace("\\", "/")
    if name.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", name):
        return None
    anchor = root if name.startswith(("jobs/", "research/", "releases/")) else base
    path = (anchor / name).resolve()
    return path if path.is_relative_to(root) else None


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


def _citation(item):
    value = item.get("citation")
    if isinstance(value, str) and value:
        return value
    where = item.get("where")
    if isinstance(where, str):
        for prefix in ("USC ", "CFR "):
            if where.startswith(prefix):
                return where[len(prefix):]
    return None


def _applies(declaration, item, source):
    """Whole-artifact declarations apply to every lead on that artifact (legacy).

    An item extract holds one note, section or part only. It applies when the
    lead names the same item: by exact page_or_item, or (rule "citation") by
    the same citation of the same original artifact.
    """
    rule = declaration.get("item_extract")
    if not rule:
        return True
    poi = declaration.get("page_or_item")
    if isinstance(poi, str) and poi and poi == source.get("page_or_item"):
        return True
    citation = declaration.get("citation")
    return rule == "citation" and isinstance(citation, str) and bool(citation) and citation == _citation(item)


# Producer folders whose files are item extracts: such a file is citable only through a
# SOURCES.jsonl declaration of that file that applies to the lead's own item.
EXTRACT_DIRS = ("jobs/current-law/output/usc-notes/", "jobs/current-law/output/usc-sections/")


def _declarations(root):
    """Declarations by original (url, sha256), and by resolved text path."""
    by_key, by_path = {}, {}
    for rel in DECLARATION_MANIFESTS:
        manifest = root / rel
        if not manifest.is_file():
            continue
        base = manifest.parent
        for line in manifest.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(row, dict):
                continue
            entry = {"row": row, "manifest": rel,
                     "text_path": _safe(root, base, row.get("text_path")),
                     "cache_path": _safe(root, base, row.get("cache_path")),
                     "pin": row.get("text_sha256")}
            origin = row.get("extracted_from")
            if row.get("item_extract") and isinstance(origin, dict):
                # An item extract cut from another artifact declares its own bytes
                # (sha256 = hash of the extract). Its text_sha256, or that sha256,
                # pins it on every route; the origin's (url, sha256) reaches it.
                entry["pin"] = row.get("text_sha256") or row.get("sha256")
                by_key.setdefault((origin.get("url"), origin.get("sha256")), []).append(
                    dict(entry, via_origin=True))
            by_key.setdefault((row.get("url"), row.get("sha256")), []).append(entry)
            if entry["text_path"]:
                by_path.setdefault(entry["text_path"], []).append(entry)
    return by_key, by_path


def _gap(root, path, why):
    return "Held current-law extract " + path.relative_to(root).as_posix() + " " + why


def enrich_current(repo, leads):
    """Return copied leads with verified exact held-text quote spans where possible.

    Supports direct attributed UTF-8 text/XML/HTML pointers and SOURCES.jsonl
    declarations (current-law, theophilus-sources) with the same original
    URL/hash. JSON/JSONL/CSV/search excerpts are never silently promoted to
    legal text. The latter require an upstream producer to publish a properly
    attributed legal-text extract.

    Pins: a text_sha256 on the lead or on its source must equal the held
    bytes, and so must the pin of the declaration used. An unpinned direct
    pointer must match some pin any declaration gives that file. A file that
    is declared as an item extract, or lies in an item-extract folder, is
    citable only through a declaration of that file that applies to the
    lead's own item, even when the lead points at the file directly.
    """
    root = Path(repo).resolve()
    base = root / "jobs/current-law/output"
    declarations, by_path = _declarations(root)
    reads = {}
    result = []
    for lead in leads:
        if not isinstance(lead, dict):
            continue
        item = deepcopy(lead)
        source = item.get("source")
        # Remove unproved quote fields on every unsuccessful branch.
        prior_text = item.pop("text", None)
        prior_start = item.pop("char_start", None)
        prior_end = item.pop("char_end", None)
        item.pop("held_extract", None)
        if not isinstance(source, dict) or not SHA.fullmatch(str(source.get("sha256") or "")):
            item["evidence_gap"] = "Current-law lead lacks an original-source sha256."
            result.append(item)
            continue
        direct_pins = [p for p in (source.get("text_sha256"), item.get("text_sha256")) if p is not None]
        applying = [d for d in declarations.get((source.get("url"), source.get("sha256")), [])
                    if _applies(d["row"], item, source)]
        declaration_gap = None
        candidates = []
        direct = _safe(root, base, source.get("text_path") or item.get("text_path"))
        if direct is not None:
            rel = direct.relative_to(root).as_posix()
            item_only = rel.startswith(EXTRACT_DIRS) or any(d["row"].get("item_extract")
                                                            for d in by_path.get(direct, []))
            if item_only:
                own = [d for d in applying if d["text_path"] == direct]
                if own:
                    candidates.append((direct, False, own[0]["pin"], own[0]))
                else:
                    declaration_gap = _gap(root, direct, (
                        "is not declared for this lead's item (original url/sha256 and page_or_item or citation); "
                        "an undeclared extract, or another item's, is not evidence for it."))
            else:
                candidates.append((direct, False, None, None))
        for declaration in applying:
            candidates.append((declaration["text_path"], False, declaration["pin"], declaration))
            # A cache path is an original artifact, not an attributed text
            # extract. Accept only a matching original-byte hash below.
            if not declaration.get("via_origin"):
                candidates.append((declaration["cache_path"], True, None, declaration))
        found = False
        for path, original_cache, declared_text_sha, declaration in candidates:
            if not path or path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
                continue
            try:
                if path not in reads:
                    raw = path.read_bytes()
                    reads[path] = [hashlib.sha256(raw).hexdigest(), raw, None, None]
                digest, raw = reads[path][0], reads[path][1]
                if original_cache and digest != source["sha256"]:
                    continue
                if any(not isinstance(pin, str) or pin.lower() != digest for pin in direct_pins):
                    declaration_gap = _gap(root, path, "does not match the text_sha256 the lead carries; repair "
                                           "the retained bytes or the lead before citing this extract.")
                    continue
                # An unpinned direct pointer (or legacy fallback) to a declared
                # extraction is not an independent witness: some pin that a
                # declaration gives this file (any manifest, any item) must hold.
                # Explicitly pinned direct text and exact original caches remain
                # separate routes.
                path_pins = [d["pin"] for d in by_path.get(path, []) if d["pin"] is not None]
                if (not original_cache and declared_text_sha is None and not direct_pins and path_pins and
                        not any(isinstance(pin, str) and SHA.fullmatch(pin) and pin.lower() == digest
                                for pin in path_pins)):
                    declaration_gap = _gap(root, path, "does not match its declared text_sha256; repair the "
                                           "retained bytes or declaration before citing this extract.")
                    continue
                # The declaration's original URL/hash selects this extract,
                # but its own text pin must still match the held bytes. An
                # unchanged snippet cannot renew a stale source declaration.
                if declared_text_sha is not None and (not isinstance(declared_text_sha, str) or
                        not SHA.fullmatch(declared_text_sha) or declared_text_sha.lower() != digest):
                    declaration_gap = _gap(root, path, "does not match its declared text_sha256; repair the "
                                           "retained bytes or declaration before citing this extract.")
                    continue
                if reads[path][2] is None:
                    reads[path][2] = raw.decode("utf-8")
                text = reads[path][2]
            except (OSError, ValueError, UnicodeError):
                continue
            if text.startswith("version https://git-lfs.github.com/spec/v1"):
                continue
            quote = prior_text if isinstance(prior_text, str) and prior_text else item.get("snippet")
            if not isinstance(quote, str) or not quote:
                continue
            if reads[path][3] is None:
                reads[path][3] = _collapse(text)
            if (type(prior_start) is int and type(prior_end) is int and
                    0 <= prior_start < prior_end <= len(text) and text[prior_start:prior_end] == quote):
                start, end = prior_start, prior_end
            else:
                span = locate(text, quote, reads[path][3])
                if span is None:
                    continue
                start, end = span
            normalized_source = dict(source, text_path=path.relative_to(root).as_posix(), text_sha256=digest)
            item.update(source=normalized_source, text=text[start:end], char_start=start, char_end=end,
                        evidence_role="current_law_wording_lead")
            if declaration is not None:
                row = declaration["row"]
                item["held_extract"] = {"manifest": declaration["manifest"], "source_id": row.get("source_id"),
                                        "url": row.get("url"), "sha256": row.get("sha256"),
                                        "page_or_item": row.get("page_or_item")}
            item.pop("evidence_gap", None)
            found = True
            break
        if not found:
            item["evidence_gap"] = declaration_gap or (
                "No uniquely located attributed legal-text slice is held for this current-law pointer; "
                "serialized JSON/JSONL, snippets and absent cache artifacts are not legal-text evidence.")
        result.append(item)
    return result
