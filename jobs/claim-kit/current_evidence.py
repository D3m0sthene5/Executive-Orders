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
MIN_COMPACT_QUOTE = 12


def _safe(root, base, name):
    if not isinstance(name, str) or not name or "#" in name:
        return None
    name = name.replace("\\", "/")
    if name.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", name):
        return None
    anchor = root if name.startswith(("jobs/", "research/", "releases/")) else base
    path = (anchor / name).resolve()
    return path if path.is_relative_to(root) else None


def _unique(hay, needle):
    start = hay.find(needle)
    if start < 0 or hay.find(needle, start + 1) >= 0:
        return None
    return start


def _compact(text):
    chars, index = [], []
    for i, ch in enumerate(text):
        if not ch.isspace():
            chars.append(ch)
            index.append(i)
    return "".join(chars), index


def locate(text, quote, compact=None):
    """(start, end) of the one place ``quote`` occurs in ``text``, else None.

    1. the quote as given; 2. without a leading/trailing "..." (snippet
    ellipses); 3. the same non-space characters, ignoring whitespace (snippets
    collapse line breaks and join a heading to a status line with " | ").
    Each step needs exactly one occurrence. The caller quotes text[start:end],
    an exact slice of the held bytes, never the snippet itself.
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
    if len(needle) < MIN_COMPACT_QUOTE:
        return None
    hay, index = compact if compact is not None else _compact(text)
    start = _unique(hay, needle)
    if start is None:
        return None
    return index[start], index[start + len(needle) - 1] + 1


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


def _declarations(root):
    by_key = {}
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
            by_key.setdefault((row.get("url"), row.get("sha256")), []).append(entry)
            origin = row.get("extracted_from")
            if row.get("item_extract") and isinstance(origin, dict):
                # The extract's own sha256 pins its bytes when it was cut from
                # another artifact and declares no separate text_sha256.
                by_key.setdefault((origin.get("url"), origin.get("sha256")), []).append(
                    dict(entry, pin=row.get("text_sha256") or row.get("sha256"), via_origin=True))
    return by_key


def enrich_current(repo, leads):
    """Return copied leads with verified exact held-text quote spans where possible.

    Supports direct attributed UTF-8 text/XML/HTML pointers and SOURCES.jsonl
    declarations (current-law, theophilus-sources) with the same original
    URL/hash. JSON/JSONL/CSV/search excerpts are never silently promoted to
    legal text. The latter require an upstream producer to publish a properly
    attributed legal-text extract.
    """
    root = Path(repo).resolve()
    base = root / "jobs/current-law/output"
    declarations = _declarations(root)
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
        declarations_for_source = [d for d in declarations.get((source.get("url"), source.get("sha256")), [])
                                   if _applies(d["row"], item, source)]
        declared_pins = {}
        for declaration in declarations_for_source:
            if declaration["text_path"] and declaration["pin"] is not None:
                declared_pins.setdefault(declaration["text_path"], []).append(declaration["pin"])
        candidates = [(_safe(root, base, source.get("text_path") or item.get("text_path")), False, None, None)]
        for declaration in declarations_for_source:
            candidates.append((declaration["text_path"], False, declaration["pin"], declaration))
            # A cache path is an original artifact, not an attributed text
            # extract. Accept only a matching original-byte hash below.
            if not declaration.get("via_origin"):
                candidates.append((declaration["cache_path"], True, None, declaration))
        found = False
        declaration_gap = None
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
                if source.get("text_sha256") and source["text_sha256"].lower() != digest:
                    continue
                # An unpinned direct pointer (or legacy fallback) to the same
                # declared extraction is not an independent witness. Honor the
                # supplied pins for that path instead of bypassing them merely
                # because the lead also names the path. Explicitly source-pinned
                # direct text and exact original caches remain separate routes.
                same_path_pins = declared_pins.get(path, [])
                if (not original_cache and declared_text_sha is None and
                        not source.get("text_sha256") and same_path_pins and
                        not any(isinstance(pin, str) and SHA.fullmatch(pin) and pin.lower() == digest
                                for pin in same_path_pins)):
                    declaration_gap = ("Held current-law extract does not match its declared text_sha256: "
                                       + path.relative_to(root).as_posix()
                                       + "; repair the retained bytes or declaration before citing this extract.")
                    continue
                # The declaration's original URL/hash selects this extract,
                # but its own text pin must still match the held bytes. An
                # unchanged snippet cannot renew a stale source declaration.
                if declared_text_sha is not None and (not isinstance(declared_text_sha, str) or
                        not SHA.fullmatch(declared_text_sha) or declared_text_sha.lower() != digest):
                    declaration_gap = ("Held current-law extract does not match its declared text_sha256: "
                                       + path.relative_to(root).as_posix()
                                       + "; repair the retained bytes or declaration before citing this extract.")
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
            if (type(prior_start) is int and type(prior_end) is int and
                    0 <= prior_start < prior_end <= len(text) and text[prior_start:prior_end] == quote):
                start, end = prior_start, prior_end
            else:
                if reads[path][3] is None:
                    reads[path][3] = _compact(text)
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
