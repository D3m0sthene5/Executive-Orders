"""Narrow, source-bound checks for attributed wording in applied claims.

An absence flag requires a hash-verified, identified whole-order body.  Clause
spans alone can establish presence, but cannot establish absence from recitals.
This module does not inspect review outcomes or maintain order-specific rules.
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import json
import re
import sys
import subprocess
import unicodedata
from pathlib import Path

CLAIM_KIT = Path(__file__).resolve().parents[1] / "claim-kit"
CLAUSE_DRAFTS = Path(__file__).resolve().parents[1] / "clause-drafts"
for directory in (CLAIM_KIT, CLAUSE_DRAFTS):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


def _concept_text(value):
    """Allow OCR spacing and soft hyphens for concepts, preserving word order."""
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = re.sub("\u00ad\\s*", "", value).replace("\u200b", "")
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", value)
    return re.sub(r"\s+", " ", value).casefold()


CONCEPTS = {
    "standstill": re.compile(r"\bstand\s*-?\s*still\b|\b(?:no|not any)\s+change\b|\b(?:shall|will|must)\s+not\s+(?:be\s+)?chang(?:e|ed)\b|\b(?:maintain|preserve)\s+(?:the\s+)?(?:existing|current)\s+(?:conditions|terms)\b|\bexcept\s+by\s+agreement\b.{0,180}\bconditions\s+out\b"),
    "approval_recommended": re.compile(r"\bapproval\s+recommended\b|\brecommend(?:ation|ed|s)?\s+(?:approval|that\s+.{0,45}\s+be\s+approved)\b"),
    "non_derogation": re.compile(r"\bderogat\w*\b|\b(?:nothing|not\s+anything)\s+(?:in\s+this\s+order\s+)?(?:shall\s+)?(?:be\s+)?construed\s+to\s+(?:affect|limit|abridge|impair)\b|\bshall\s+not\s+(?:affect|limit|abridge|impair)\b"),
    "status_quo": re.compile(r"\bstatus\s*-?\s*quo\b|\bno\s+change\b.{0,80}\bshall\s+be\s+made\b|\bexcept\s+by\s+agreement\b.{0,180}\bconditions\s+out\b|\b(?:existing|current)\s+(?:conditions|terms)\b.{0,80}\b(?:remain|continue|maintained|unchanged)\b|\b(?:remain|continue)\b.{0,65}\b(?:unchanged|existing|in\s+force)\b|\bas\s+they\s+(?:now\s+)?are\b"),
    "hearing_recital": re.compile(r"\bhearings?\b"),
    "board_report": re.compile(r"\b(?:board|commission|committee)\b.{0,100}\b(?:report|submit)\b|\b(?:report|submit)\b.{0,70}\b(?:board|commission|committee)\b"),
}
# The three anchors of a printed Railway Labor Act section 10 command can
# survive severe OCR damage to "no change" itself.  A statute citation alone
# never satisfies this check; the report-relative period and agreement clause
# must appear in the same short passage of the bounded order body.
OCR_RLA_STANDSTILL = re.compile(r"\bas\s+provided\s+by\s+section\s+10\b.{0,175}\bfor\s+thirty\s+days\s+after\b.{0,140}\bby\s+agreement\b")
CLAIM_TERMS = {
    "standstill": re.compile(r"\bstand\s*-?\s*still\b", re.I),
    "approval_recommended": re.compile(r"\bapproval recommended\b", re.I),
    "non_derogation": re.compile(r"\bnon\s*-?\s*derogation\b|\bnon\s*-?\s*derogating\b", re.I),
    "status_quo": re.compile(r"\bstatus\s*-?\s*quo\b", re.I),
    "hearing_recital": re.compile(r"\bhearings?\b", re.I),
    "board_report": re.compile(r"\b(?:board|commission|committee)\s+(?:shall|will|must)\s+(?:report|submit)\b", re.I),
}
QUOTE = re.compile(r'(?<!\w)["“]([^"”\n]{5,240})["”]|(?<!\w)\'([^\'\n]{5,240})\'(?!\w)')
ATTRIBUTION = re.compile(r"\b(?:this|the)\s+(?:executive\s+)?order\s+(?:sets?|states?|says?|provides?|directs?|requires?|contains?|includes?|recites?|describes?)\b|\b(?:this|the)\s+order's\s+(?:text|words|recitals?)\b", re.I)
NEGATIVE = re.compile(r"\b(?:no|not|never|without|lacks?|absent|omits?|does\s+not|did\s+not|not\s+contain|not\s+include)\b", re.I)
REASON_KEYS = {"reason", "rationale", "judgment_reason", "research_rationale", "current_legal_basis", "savings_reason"}


def _verified(source, repo, cache):
    path = source.get("text_path") if isinstance(source, dict) else None
    sha = source.get("text_sha256") if isinstance(source, dict) else None
    if not isinstance(path, str) or not isinstance(sha, str):
        return None, "source_reference_missing"
    p = (repo / path).resolve()
    if not p.is_relative_to(repo.resolve()) or not p.is_file():
        return None, "source_file_unavailable"
    key = (str(p), sha)
    # Rehash even with a caller cache: size and mtime can be restored after a
    # same-length mutation, and the held source is the authority for every row.
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        return None, "source_hash_mismatch"
    if key not in cache:
        try:
            cache[key] = (raw.decode("utf-8"), None)
        except UnicodeDecodeError:
            cache[key] = (None, "source_not_utf8")
    return cache[key]


def _records(dossier):
    result = dict(dossier.get("evidence") or {})
    for clause in dossier.get("clauses") or []:
        if isinstance(clause, dict):
            result.setdefault(clause.get("id") or "CLAUSES:" + str(clause.get("scope_id")), clause)
    return result


def _source_id(source):
    ident = source.get("evidence_id") if isinstance(source, dict) else None
    if source.get("evidence_id_encoding") == "base64url-utf8" and isinstance(ident, str):
        try:
            ident = base64.urlsafe_b64decode(ident + "=" * (-len(ident) % 4)).decode("utf-8")
        except (UnicodeError, ValueError):
            return None
    return ident


def _exact(value):
    """Only whitespace normalization is allowed for a verbatim quotation."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _app_listing(source, repo, number, cache):
    """Corroborate an individualized APP item in the publisher listing.

    APP slugs sometimes drop EO suffixes, so the exact URL is matched to the
    listing's *explicit* instrument id, title and date, not parsed as an EO id.
    """
    index_path = repo / "jobs/app-executive-orders/output/INDEX.jsonl"
    try:
        raw = index_path.read_bytes()
        try:
            expected = subprocess.check_output(["git", "rev-parse", "HEAD:jobs/app-executive-orders/output/INDEX.jsonl"], cwd=repo, stderr=subprocess.DEVNULL).decode().strip()
            if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != expected:
                return None
        except (OSError, subprocess.CalledProcessError):
            pass  # Exported fixtures have no Git; the supplied record remains explicit.
        digest = hashlib.sha256(raw).hexdigest()
        key = ("app_index", str(index_path), digest)
        if key not in cache:
            by_url = {}
            for line in raw.decode("utf-8").splitlines():
                row = json.loads(line)
                if isinstance(row, dict) and isinstance(row.get("url"), str):
                    by_url.setdefault(row["url"], []).append(row)
            cache[key] = by_url
        candidates = cache[key].get(source.get("url"), [])
    except (OSError, ValueError, UnicodeError):
        return None
    label = str(source.get("page_or_item") or "")
    title = label.split(";", 1)[0].strip()
    date = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(\d{4})\b", label, re.I)
    if not date:
        return None
    try:
        item_date = datetime.date(int(date.group(3)), datetime.datetime.strptime(date.group(1), "%B").month, int(date.group(2))).isoformat()
    except ValueError:
        return None
    matching = [row for row in candidates if row.get("instrument_id") == source.get("instrument_id")
                and row.get("title") == title and row.get("date") == item_date]
    if len(matching) != 1:
        return None
    return {"index_path": str(index_path.relative_to(repo)), "index_sha256": digest,
            "listing_date": item_date, "listing_instrument_id": matching[0]["instrument_id"],
            "listing_url": matching[0]["url"]}


def _own_body(claim, dossier, repo, cache):
    """Return (body, provenance, gap); never treat a filename as identity."""
    records = _records(dossier)
    parent = records.get(dossier.get("original_source_id"))
    if not isinstance(parent, dict):
        return None, {}, "original_record_missing"
    source = parent.get("source")
    full, issue = _verified(source, repo, cache)
    if issue:
        return None, {}, issue
    start, end = parent.get("char_start"), parent.get("char_end")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(full) or full[start:end] != parent.get("text"):
        return None, {}, "original_record_span_mismatch"
    overrides = (claim.get("claim_kit") or {}).get("inventory_overrides", [])
    clauses = dossier.get("clauses") or []
    if overrides:
        import assemble
        clauses, _, errors = assemble.derive_inventory(dossier, overrides)
        if errors:
            return None, {}, "inventory_override_invalid:" + ",".join(errors)
    spans = [(c.get("char_start"), c.get("char_end")) for c in clauses if isinstance(c, dict)]
    if not spans or any(type(a) is not int or type(b) is not int or not start <= a < b <= end or full[a:b] != c.get("text")
                        for (a, b), c in zip(spans, clauses)):
        return None, {}, "target_clause_span_unverified"
    number = str(dossier.get("instrument_id") or "").removeprefix("EO:")
    try:
        import segment
        loc = segment.locate_order(full, number)
    except ImportError:
        return None, {}, "order_locator_unavailable"
    if loc is None or loc.heading_style == "unnumbered_hint":
        # APP's individual order item can begin with an unnumbered recital.
        # The producer's source record must identify an APP node, this very EO
        # in its item title, and an independently matching publisher URL.  A
        # file path or the dossier instrument id alone never proves identity.
        label = source.get("page_or_item", "")
        url = source.get("url", "")
        listing = _app_listing(source, repo, number, cache)
        item_date = datetime.date.fromisoformat(listing["listing_date"]) if listing else None
        month = item_date.strftime('%B') if item_date else ''
        signature_date = (rf"(?:{month}|{month[:3]}\.?)\s+0?{item_date.day},?\s*{item_date.year}"
                          if item_date else "")
        signature_tail = full[-330:]
        matching_signature_date = bool(signature_date and
            re.search(r"\bThe\s+White\s+House\b.{0,35}" + signature_date + r"\s*\.?\s*$",
                      signature_tail, re.I | re.S))
        app = (isinstance(source.get("archival_id"), str) and source["archival_id"].startswith("app:node/")
               and source.get("instrument_id") == dossier.get("instrument_id")
               and re.search(r"\bExecutive Order\s+" + re.escape(number[:-1]) + r"\s*[-‐–]?\s*" + re.escape(number[-1]) + r"\b" if number[-1:].isalpha() else r"\bExecutive Order\s+" + re.escape(number) + r"\b", label, re.I)
               and listing is not None
               and matching_signature_date
               and start == 0 and end == len(full)
               and all(0 <= a < b <= len(full) for a, b in spans))
        if not app:
            return None, {}, "order_heading_unresolved"
        return full, {"text_path": source["text_path"], "text_sha256": source["text_sha256"],
            "char_start": 0, "char_end": len(full), "boundary": "identified_app_item",
            "source_id": dossier.get("original_source_id"), "publisher_listing": listing}, None
    if not all(loc.doc_start <= b and a < loc.doc_end for a, b in spans):
        return None, {}, "order_boundary_clause_conflict"
    # Some early source inventories include the page header immediately before
    # the heading; permit at most one such leading span when no prior order
    # heading intervenes.  No after-order clause can be silently accepted.
    if any((b > loc.doc_end and full[loc.doc_end:b].strip()) or (a < loc.doc_start and
            (loc.doc_start - a > 150 or segment.find_headings(full[a:loc.doc_start])))
           for a, b in spans):
        return None, {}, "order_boundary_clause_conflict"
    # Reject ambiguous repeated headings, even if the locator chose one.
    headings = [(n, pos) for n, pos in segment.find_headings(full)
                if re.sub(r"[^A-Z0-9]", "", n.upper()) == re.sub(r"[^A-Z0-9]", "", number.upper())]
    if len(headings) > 1 and loc.heading_style == "numbered":
        return None, {}, "repeated_order_headings"
    return full[loc.doc_start:loc.doc_end], {"text_path": source["text_path"], "text_sha256": source["text_sha256"],
        "char_start": loc.doc_start, "char_end": loc.doc_end, "boundary": loc.heading_style,
        "source_id": dossier.get("original_source_id")}, None


def _reasoning(claim):
    def walk(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in REASON_KEYS and isinstance(child, str):
                    if "Member checks:" in child:
                        import json
                        before, _, tail = child.partition("Member checks:")
                        if before.strip():
                            yield f"{path}.{key}.narrative", before
                        try:
                            obj, end = json.JSONDecoder().raw_decode(tail.lstrip())
                            if isinstance(obj, dict):
                                for part, text in obj.items():
                                    if isinstance(text, str):
                                        yield f"{path}.{key}.{part}", text
                                remainder = tail.lstrip()[end:]
                                if remainder.strip():
                                    yield f"{path}.{key}.narrative", remainder
                                continue
                        except ValueError:
                            pass
                    yield f"{path}.{key}", child
                else:
                    yield from walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from walk(child, f"{path}[{index}]")
    yield from walk(claim, "claim")


def _citations(value, path="claim"):
    if isinstance(value, dict):
        if isinstance(value.get("text_path"), str) and isinstance(value.get("quote"), str) and value["quote"]:
            yield path, value
            return
        for key, child in value.items():
            yield from _citations(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _citations(child, f"{path}[{index}]")


def check(claim, dossier, repo, packet_path=None, cache=None):
    """Return deterministic flags and uncertainty for one claim and dossier.

    ``packet_path`` is reserved for an optional caller provenance label.  A
    source defect requires a hash-verified full order body or cited event span.
    """
    repo = Path(repo).resolve()
    cache = cache if cache is not None else {}
    flags, gaps = [], []
    body, provenance, issue = _own_body(claim, dossier, repo, cache)
    if issue:
        gaps.append({"code": "own_order_body_unverified", "reason": issue})
    normalized = _concept_text(body) if body is not None else ""
    seen = set()
    for path, text in _reasoning(claim):
        # Quotes may contain initials, dates and semicolons; scan complete
        # parts before sentence splitting so these do not break attribution.
        for m in QUOTE.finditer(text):
            phrase = m.group(1) or m.group(2)
            prefix = text[max(0, m.start()-180):m.start()]
            if len(phrase.split()) < 3 or body is None:
                continue
            attributed = (re.search(r"\b(?:the|this)\s+(?:executive\s+)?order\s+(?:sets?|states?|says?|provides?|contains?|includes?|recites?|describes?)\b[^.!?;]{0,130}$", prefix, re.I)
                          or re.search(r"\b(?:the|this)\s+order\s+(?:sets?|has)\s+(?:a\s+)?(?:report\s+)?(?:date|deadline)\s*\($", prefix, re.I))
            if not attributed and path.endswith("independent_command_check"):
                attributed = re.search(r"^\s*Approval recommended\b", phrase, re.I)
            if attributed and _exact(phrase) not in _exact(body):
                key = (path, "quotation", phrase)
                if key not in seen:
                    flags.append({"code": "attributed_quote_not_verbatim", "detail": f"{path}: attributed quotation {phrase!r} is absent verbatim from the verified order body", "source": provenance})
                    seen.add(key)
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            # A reviewable source assertion, including a checklist inventory,
            # rather than legal discussion about a later statute or instrument.
            own_scope = bool(re.search(r"(?:scope_check|independent_command_check|judgment_reason|inventory)", path, re.I))
            explicit = bool(ATTRIBUTION.search(sentence) or re.search(r"\b(?:the|this)\s+order\s+(?:consists|has|is)\b", sentence, re.I)
                            or re.search(r"\bInventory:\s*the\s+order\b", sentence, re.I))
            if not (own_scope or explicit):
                continue
            for concept, term in CLAIM_TERMS.items():
                for match in term.finditer(sentence):
                    before = sentence[max(0, match.start() - 60):match.start()]
                    after = sentence[match.end():match.end() + 35]
                    if re.search(r"\b(?:no|without|lacks?|not\s+contain|not\s+include)\s+(?:[\w-]+\s+){0,3}$", before, re.I) or re.match(r"\s+(?:is\s+|was\s+)?(?:absent|missing|not\s+(?:present|in))\b", after, re.I):
                        continue
                    # A statutory period or a discussion of when a command
                    # ended is not an assertion that these words/commands were
                    # in the printed order. Require a concrete textual role.
                    local = sentence[max(0, match.start()-95):min(len(sentence), match.end()+75)]
                    if concept == "hearing_recital" and not re.search(r"\b(?:order|recital|preamble|text)\b.{0,85}\bhearings?\b|\bhearings?\b.{0,80}\b(?:recital|preamble|order(?:'s)?\s+text)\b", local, re.I):
                        continue
                    if not (re.search(r"\b(?:sentence|recital|command|provision|paragraph|order|inventory|text|terms|contains?|includes?|recited|states?|sets?)\b", local, re.I)
                            or concept == "approval_recommended" and path.endswith("independent_command_check")):
                        continue
                    if body is None:
                        continue
                    if CONCEPTS[concept].search(normalized) or concept in {"standstill", "status_quo"} and OCR_RLA_STANDSTILL.search(normalized):
                        continue
                    key = (path, concept)
                    if key not in seen:
                        flags.append({"code": "attributed_stock_phrase_absent", "concept": concept,
                                      "detail": f"{path}: attributed {concept.replace('_', ' ')} is absent from the verified order body",
                                      "source": provenance})
                        seen.add(key)

    # Each quotation is verified against *its own* exact cited source span.
    # In particular, a first-ending actor is never compared to the original.
    verified_quote_paths = set()
    for path, source in _citations(claim):
        full, source_issue = _verified(source, repo, cache)
        if source_issue:
            gaps.append({"code": "cited_quote_source_unverified", "path": path, "reason": source_issue})
            continue
        a, b = source.get("char_start"), source.get("char_end")
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(full):
            gaps.append({"code": "cited_quote_span_unverified", "path": path})
            continue
        if _exact(source["quote"]) not in _exact(full[a:b]):
            if ".later_events[" in path:
                code = "later_event_quote_not_in_cited_source"
            elif ".first_end." in path:
                code = "first_end_quote_not_in_cited_source"
            elif ".original_source" in path or ".original_representation" in path:
                code = "original_quote_not_in_cited_source"
            else:
                code = "citation_quote_not_in_cited_source"
            flags.append({"code": code, "detail": f"{path}: quotation differs from the pinned source span",
                          "source": {"text_path": source["text_path"], "text_sha256": source["text_sha256"],
                                     "char_start": a, "char_end": b, "source_id": _source_id(source)}})
        else:
            verified_quote_paths.add(path)
    for i, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict):
            continue
        original = clause.get("original_source")
        if not isinstance(original, dict) or not isinstance(original.get("quote"), str) or not original["quote"]:
            continue
        operative = clause.get("original_operative_text")
        if (f"claim.operative_clauses[{i}].original_source" in verified_quote_paths
                and isinstance(operative, str) and operative != original["quote"]):
            flags.append({"code": "quotation_not_verbatim", "detail": f"operative_clauses[{i}]: operative text differs from its cited original quotation",
                          "source": {"source_id": _source_id(original), "text_path": original.get("text_path"),
                                     "text_sha256": original.get("text_sha256")}})
    return {"flags": flags, "coverage_gaps": gaps}
