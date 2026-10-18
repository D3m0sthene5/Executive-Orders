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


def _safe(root, base, name):
    if not isinstance(name, str) or not name or "#" in name:
        return None
    name = name.replace("\\", "/")
    if name.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", name):
        return None
    anchor = root if name.startswith(("jobs/", "research/", "releases/")) else base
    path = (anchor / name).resolve()
    return path if path.is_relative_to(root) else None


def enrich_current(repo, leads):
    """Return copied leads with verified exact held-text quote spans where possible.

    Supports direct attributed UTF-8 text/XML/HTML pointers and SOURCES.jsonl
    declarations with the same original URL/hash. JSON/JSONL/CSV/search excerpts
    are never silently promoted to legal text. The latter require an upstream
    producer to publish a properly attributed legal-text extract.
    """
    root = Path(repo).resolve()
    base = root / "jobs/current-law/output"
    declarations = {}
    manifest = base / "SOURCES.jsonl"
    if manifest.is_file():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(row, dict):
                declarations.setdefault((row.get("url"), row.get("sha256")), []).append(row)
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
        if not isinstance(source, dict) or not SHA.fullmatch(str(source.get("sha256") or "")):
            item["evidence_gap"] = "Current-law lead lacks an original-source sha256."
            result.append(item)
            continue
        declarations_for_source = declarations.get((source.get("url"), source.get("sha256")), [])
        candidates = [(source.get("text_path") or item.get("text_path"), False)]
        for declaration in declarations_for_source:
            candidates.append((declaration.get("text_path"), False))
            # A cache path is an original artifact, not an attributed text
            # extract. Accept only a matching original-byte hash below.
            candidates.append((declaration.get("cache_path"), True))
        found = False
        for name, original_cache in candidates:
            path = _safe(root, base, name)
            if not path or path.suffix.lower() not in {".txt", ".xml", ".html", ".htm"} or not path.is_file():
                continue
            try:
                raw = path.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                if original_cache and digest != source["sha256"]:
                    continue
                if source.get("text_sha256") and source["text_sha256"].lower() != digest:
                    continue
                text = raw.decode("utf-8")
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
                start = text.find(quote)
                if start < 0 or text.find(quote, start + 1) >= 0:
                    continue
                end = start + len(quote)
            normalized_source = dict(source, text_path=path.relative_to(root).as_posix(), text_sha256=digest)
            item.update(source=normalized_source, text=quote, char_start=start, char_end=end,
                        evidence_role="current_law_wording_lead")
            item.pop("evidence_gap", None)
            found = True
            break
        if not found:
            item["evidence_gap"] = ("No uniquely located attributed legal-text slice is held for this current-law pointer; "
                                    "serialized JSON/JSONL, snippets and absent cache artifacts are not legal-text evidence.")
        result.append(item)
    return result
