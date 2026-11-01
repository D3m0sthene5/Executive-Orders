#!/usr/bin/env python3
"""Deterministic, source-based advisory checks for claim-kit applied proposals.

Geddes never reads or scores review verdicts. Defect flags are reproducible
comparisons against frozen packet data and held text; missing inputs/coverage
are reported separately and are not defects.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "jobs/claim-kit"))
import batch  # noqa: E402

SCHEMA = "geddes-lint/v1"
FR_RE = re.compile(r"(?<!\w)(\d{1,3})\s+F\.?\s*R\.?\s+(\d+)(?!\d)", re.I)
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
NO_ORDER_RE = re.compile(r"\b(?:no|not any|none)\s+(?:other\s+)?(?:(?:held|saved|current|executive)\s+){0,2}orders?\b", re.I)
QUOTED_RE = re.compile(r'["“](.{5,240}?)["”]|(?<![\w])\'([^\'\n]{5,240})\'(?![\w])')
EO_RE = re.compile(r"\b(?:Executive\s+Orders?\s+(?:No\.?\s*)?|EO\s*:?[ \t]*)(\d{1,6}(?:[- ]?[A-Z])?)\b", re.I)
OTHER_INSTRUMENT_RE = re.compile(r"\b(Proclamation|Public\s+Law|Statute)\s+(?:No\.?\s*)?(\d{1,6}(?:[- ]?[A-Z])?)\b", re.I)
STOCK_PHRASES = {
    "standstill": re.compile(r"\bstand[- ]?still\b", re.I),
    "approval_recommended": re.compile(r"\bapproval recommended\b", re.I),
    "hearing_recital": re.compile(r"\bhearings?\b", re.I),
    "non_derogation": re.compile(r"\bnon[- ]derogation\b|\bnot(?:hing)? (?:in this order )?shall (?:be )?construed to (?:limit|affect|abridge)|\bwithout derogating\b|\bshall not derogate\b", re.I),
    "status_quo": re.compile(r"\bstatus quo\b|\bexisting conditions? (?:shall|will) (?:remain|continue)\b", re.I),
    "board_report": re.compile(r"\b(?:board|commission|committee) (?:shall|will) (?:report|submit)\b", re.I),
}
# Reasoning often uses a conventional description rather than the literal
# words of a command. Test the narrow source concept, not that description.
SOURCE_CONCEPTS = {
    **STOCK_PHRASES,
    "standstill": re.compile(r"\bstand[- ]?still\b|\bno change\b|\bshall not (?:be )?change", re.I),
    "non_derogation": re.compile(r"derogat|\bnothing\b.{0,150}\b(?:construed|affect|limit|abridge)|\bshall not\b.{0,100}\b(?:affect|limit|abridge)", re.I | re.S),
    "status_quo": re.compile(r"\bstatus quo\b|\bno change\b|\b(?:remain|continue)\b.{0,60}\b(?:unchanged|in force|existing)|\bas they (?:now )?are\b", re.I | re.S),
    "board_report": re.compile(r"\breport\b|\bsubmit\b", re.I),
}
NEGATION_RE = re.compile(r"\b(?:no|not|never|without|does not|did not|lacks?|absent|omits?|not contain|not include)\b", re.I)


def reasoning_parts(text):
    """Decode the existing producer's embedded checklist without quoting keys."""
    marker = re.search(r"Member checks:\s*", text, re.I)
    if marker:
        try:
            obj, end = json.JSONDecoder().raw_decode(text[marker.end():])
            if isinstance(obj, dict):
                return [("narrative", text[:marker.start()])] + [
                    (key, value) for key, value in obj.items() if isinstance(value, str)
                ] + [("narrative", text[marker.end() + end:])]
        except ValueError:
            pass
    return [("narrative", text)]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def packet_for(applied: Path) -> Path:
    for parent in (applied, *applied.parents):
        candidate = parent / "PACKET.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("could not locate PACKET.json in applied directory or its parents")


def load_context(applied: Path):
    packet_path = packet_for(applied)
    packet = read_json(packet_path)
    dossiers = batch.decode(packet)
    claims_path = applied / "CLAIMS.proposed.jsonl"
    if not claims_path.is_file():
        raise FileNotFoundError(f"missing {claims_path}")
    claims = []
    for n, raw in enumerate(claims_path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip():
            claims.append((n, json.loads(raw)))
    return packet_path, packet, dossiers, claims


def instrument_texts(dossier, repo: Path):
    """Load exact pinned text for this order; preserve missing/hash failures."""
    texts, missing, bad = [], [], []
    records = dossier.get("evidence", {})
    candidates = []
    original_id = dossier.get("original_source_id")
    if original_id and original_id in records: candidates.append((original_id, records[original_id]))
    for clause in dossier.get("clauses", []):
        if isinstance(clause, dict):
            ident = clause.get("id") or "CLAUSES:" + str(clause.get("scope_id", ""))
            candidates.append((ident, clause))
    seen = set()
    for ident, record in candidates:
        if ident in seen: continue
        seen.add(ident)
        source = record.get("source") or record.get("actor_source") or {}
        path = source.get("text_path")
        if not path:
            missing.append({"source_id": ident, "reason": "no_text_path"}); continue
        p = (repo / path).resolve()
        if not p.is_relative_to(repo.resolve()) or not p.is_file():
            missing.append({"source_id": ident, "text_path": path, "reason": "text_file_unavailable"}); continue
        raw = p.read_bytes()
        import hashlib
        if hashlib.sha256(raw).hexdigest() != source.get("text_sha256"):
            bad.append({"source_id": ident, "text_path": path, "reason": "text_hash_mismatch"}); continue
        try: text = raw.decode("utf-8")
        except UnicodeDecodeError:
            missing.append({"source_id": ident, "text_path": path, "reason": "text_not_utf8"}); continue
        a, b = record.get("char_start"), record.get("char_end")
        embedded = record.get("text")
        if type(a) is int and type(b) is int and 0 <= a < b <= len(text):
            text = text[a:b]
        if isinstance(embedded, str) and text != embedded:
            bad.append({"source_id": ident, "text_path": path, "reason": "embedded_span_mismatch"}); continue
        texts.append((ident, source, embedded if isinstance(embedded, str) else text))
    return texts, missing, bad


def bounded_own_text(dossier):
    """Return only the proven target-clause span; never trust the file name."""
    records = _evidence_records(dossier)
    ident = dossier.get("original_source_id")
    record = records.get(ident, {})
    text = record.get("text") if isinstance(record, dict) else None
    source = record.get("source", {}) if isinstance(record, dict) else {}
    if not isinstance(text, str) or not isinstance(source, dict): return "", "original_text_missing"
    start = record.get("char_start", 0)
    spans = [(c.get("char_start"), c.get("char_end"), c.get("text")) for c in dossier.get("clauses", [])
             if isinstance(c, dict) and type(c.get("char_start")) is int and type(c.get("char_end")) is int
             and isinstance(c.get("source"), dict) and c["source"].get("text_path") == source.get("text_path")]
    if spans:
        abs_start = min(a for a, _, _ in spans); abs_end = max(b for _, b, _ in spans)
        lo = abs_start - (start if type(start) is int else 0)
        hi = abs_end - (start if type(start) is int else 0)
        if 0 <= lo < hi <= len(text): return text[lo:hi], "bounded_to_target_clause_envelope"
    return "", "target_text_boundary_unknown"


def _source_metadata(source):
    if not isinstance(source, dict): return {}
    return " ".join(str(source.get(k) or "") for k in ("page_or_item", "url", "citation", "title"))


def _normal_ws(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().casefold()


def _normal_ws_exact(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _quoted_strings(text):
    return [a or b for a, b in QUOTED_RE.findall(str(text or ""))]


def _event_source_text(source, repo: Path):
    """Return exact pinned source slice or a separate missing/integrity reason."""
    path = source.get("text_path") if isinstance(source, dict) else None
    sha = source.get("text_sha256") if isinstance(source, dict) else None
    if not path or not sha:
        return None, "source_text_reference_missing"
    p = (repo / path).resolve()
    if not p.is_relative_to(repo.resolve()) or not p.is_file():
        return None, "source_text_file_unavailable"
    import hashlib
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        return None, "source_text_hash_mismatch"
    try: full = raw.decode("utf-8")
    except UnicodeDecodeError: return None, "source_text_not_utf8"
    a, b = source.get("char_start"), source.get("char_end")
    if type(a) is int and type(b) is int and 0 <= a < b <= len(full):
        return full[a:b], None
    quote = source.get("quote")
    if isinstance(quote, str) and quote and _normal_ws_exact(quote) in _normal_ws_exact(full):
        return full, None
    return None, "source_span_unavailable"


def _later_events(claim):
    for clause in claim.get("operative_clauses", []) if isinstance(claim.get("operative_clauses"), list) else []:
        if isinstance(clause, dict):
            for event in clause.get("later_events", []) if isinstance(clause.get("later_events"), list) else []:
                if isinstance(event, dict): yield clause, event


def _evidence_records(dossier):
    records = dict(dossier.get("evidence", {}))
    for clause in dossier.get("clauses", []) if isinstance(dossier.get("clauses"), list) else []:
        if isinstance(clause, dict):
            ident = clause.get("id") or "CLAUSES:" + str(clause.get("scope_id", ""))
            records.setdefault(ident, clause)
    return records


def _source_record(dossier, source):
    if not isinstance(source, dict): return None, None
    ident = source.get("evidence_id")
    if source.get("evidence_id_encoding") == "base64url-utf8" and isinstance(ident, str):
        try: ident = base64.urlsafe_b64decode(ident + "=" * (-len(ident) % 4)).decode("utf-8")
        except (ValueError, UnicodeDecodeError): return None, None
    record = _evidence_records(dossier).get(ident)
    if not isinstance(record, dict): return ident, None
    expected = record.get("actor_source") or record.get("source")
    return ident, expected if isinstance(expected, dict) else None


def _eo_label(value):
    m = re.search(r"(?:EO\s*:?\s*|Executive\s+Order\s+(?:No\.?\s*)?)(\d{1,6}(?:[- ]?[A-Z])?)", str(value or ""), re.I)
    if not m: return None
    return re.sub(r"[- ]", "", m.group(1)).upper()


def _metadata_issue(expected, actual, evidence_id):
    flags = []
    if not isinstance(expected, dict) or not isinstance(actual, dict): return flags
    exp_fr = set(FR_RE.findall(_source_metadata(expected)))
    act_fr = set(FR_RE.findall(_source_metadata(actual)))
    if exp_fr != act_fr and (exp_fr or act_fr):
        flags.append({"code": "fr_citation_mismatch", "detail": f"source citation {sorted(act_fr)} differs from pinned citation {sorted(exp_fr)}", "source_id": evidence_id})
    exp_date = re.search(r"/FR-(\d{4}-\d{2}-\d{2})/", str(expected.get("url") or ""))
    act_date = re.search(r"/FR-(\d{4}-\d{2}-\d{2})/", str(actual.get("url") or ""))
    if exp_date and act_date and exp_date.group(1) != act_date.group(1):
        flags.append({"code": "fr_issue_date_mismatch", "detail": f"source issue date {act_date.group(1)} differs from pinned issue date {exp_date.group(1)}", "source_id": evidence_id})
    page_issue = re.search(r"\b(?:issue|published|publication|issued)\s+(?:of\s+)?(\d{4}-\d{2}-\d{2})\b", str(actual.get("page_or_item") or ""), re.I)
    if exp_date and page_issue and exp_date.group(1) != page_issue.group(1):
        flags.append({"code": "fr_issue_date_mismatch", "detail": f"page metadata issue date {page_issue.group(1)} differs from pinned PDF issue date {exp_date.group(1)}", "source_id": evidence_id})
    exp_label = _eo_label(expected.get("page_or_item") or expected.get("title"))
    act_label = _eo_label(actual.get("page_or_item") or actual.get("title"))
    if exp_label and act_label and exp_label != act_label:
        code = "suffix_dropped" if exp_label.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ").isdigit() and act_label == exp_label.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ") else "app_register_number_mismatch"
        flags.append({"code": code, "detail": f"cited source label identifies EO {act_label}; pinned source identifies EO {exp_label}", "source_id": evidence_id})
    return flags


def held_corpus_search(packet_path: Path, names, repo: Path, corpus_cache=None):
    """Search exact literal names in the union of Apollo-pinned held-text files."""
    root = next((p for p in packet_path.resolve().parents if (p / "REPORT.md").is_file() and (p / "TELEMETRY.csv").is_file()), packet_path.resolve().parents[2])
    cache_key = (str(root), str(repo.resolve()))
    if corpus_cache is None: corpus_cache = {}
    cached = corpus_cache.get(cache_key)
    if cached is not None:
        for rel, snapshot in cached[4].items():
            path = (repo / rel).resolve()
            try:
                stat = path.stat(); current = (stat.st_size, stat.st_mtime_ns)
            except OSError:
                current = None
            if current != snapshot:
                cached = None
                break
    if cached is None:
        pinned = {}
        conflicts = {}
        for packet_file in root.rglob("PACKET.json"):
            try: pkt = read_json(packet_file)
            except (OSError, ValueError): continue
            for rel, sha in pkt.get("held_text_file_pins", {}).items():
                if rel in pinned and pinned[rel] != sha:
                    conflicts[rel] = sorted({pinned[rel], sha})
                else: pinned[rel] = sha
        texts = {}; missing = []; snapshots = {}; import hashlib
        missing.extend({"path": rel, "reason": "conflicting_packet_pins", "sha256_values": hashes} for rel, hashes in sorted(conflicts.items()))
        for rel, sha in sorted(pinned.items()):
            if rel in conflicts: continue
            path = (repo / rel).resolve()
            if not path.is_relative_to(repo.resolve()) or not path.is_file():
                snapshots[rel] = None
                missing.append({"path": rel, "reason": "file_unavailable"}); continue
            stat = path.stat(); snapshots[rel] = (stat.st_size, stat.st_mtime_ns)
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != sha:
                missing.append({"path": rel, "reason": "sha256_mismatch"}); continue
            texts[rel] = (sha, _normal_ws(raw.decode("utf-8", errors="replace")))
        postings = defaultdict(set)
        for rel, (_, text) in texts.items():
            for word in set(re.findall(r"[a-z0-9]+", text)):
                postings[word].add(rel)
        corpus_cache[cache_key] = (texts, missing, len(pinned), postings, snapshots)
    texts, missing, indexed, postings, _ = corpus_cache[cache_key]
    hits = {n: [] for n in names}
    for name in names:
        needle = _normal_ws(name)
        words = re.findall(r"[a-z0-9]+", needle)
        candidates = set(texts)
        if words:
            words.sort(key=lambda w: len(postings.get(w, ())))
            candidates = set(postings.get(words[0], ()))
            for word in words[1:]: candidates.intersection_update(postings.get(word, ()))
        for rel in candidates:
            sha, text = texts[rel]
            if needle and needle in text:
                hits[name].append({"path": rel, "sha256": sha})
    scope = {}
    detail_paths = [packet_path.resolve().parent / "LOOKUPS.details.json",
                    packet_path.resolve().parent.parent / "LOOKUPS.details.json"]
    if not any(p.is_file() for p in detail_paths):
        detail_paths.extend(sorted(root.glob("*/packet/LOOKUPS.details.json"))[:1])
    for detail_path in detail_paths:
        if detail_path.is_file():
            try:
                cov = read_json(detail_path).get("corpus", {}).get("coverage", {})
                scope = {k: cov.get(k) for k in ("scope", "discovered_count", "readable_count", "excluded_clause_drafts", "source_bytes") if k in cov}
                break
            except (OSError, ValueError): pass
    return hits, missing, indexed, scope


def lint_one(line, claim, dossiers, repo: Path, packet_path: Path | None = None, corpus_cache=None):
    iid = claim.get("instrument_id", "")
    dossier = dossiers.get(iid)
    flags, coverage = [], []
    def flag(code, detail, source_id=None):
        flags.append({"code": code, "detail": detail, **({"source_id": source_id} if source_id else {})})
    if dossier is None:
        return {"line": line, "instrument_id": iid, "flags": [],
                "coverage_gaps": [{"code": "packet_member_missing", "detail": "claim instrument is not in packet"}]}
    texts, missing, bad = instrument_texts(dossier, repo)
    coverage.extend({"code": "held_text_unavailable", **m} for m in missing)
    coverage.extend({"code": "held_text_integrity_failure", **m} for m in bad)
    original_text, boundary_status = bounded_own_text(dossier)
    original_verified = any(i == dossier.get("original_source_id") for i, _, _ in texts)
    if not original_verified: original_text = ""
    if boundary_status == "target_text_boundary_unknown" or not original_verified:
        coverage.append({"code": "own_order_text_boundary_unknown", "detail": "pinned source could contain neighboring text or its hash/boundary was not verified"})
    elif boundary_status == "bounded_to_target_clause_envelope":
        coverage.append({"code": "own_order_recitals_outside_envelope", "detail": "text is limited to the min/max pinned target-clause spans; recitals outside that envelope are not verified"})
    own_text = original_text
    normalized = re.sub(r"\s+", " ", own_text).casefold()

    # Quoted original operative text is tested against this order's own exact
    # evidence span. Later-source quotations are tested against their own source below.
    for i, clause in enumerate(claim.get("operative_clauses", []) if isinstance(claim.get("operative_clauses"), list) else []):
        if not isinstance(clause, dict): continue
        src = clause.get("original_source", {})
        quote = src.get("quote", "") if isinstance(src, dict) else ""
        operative = clause.get("original_operative_text", "")
        if quote and operative != quote:
            flag("quotation_not_verbatim", f"operative_clauses[{i}]: operative quotation differs from cited source quote", src.get("evidence_id"))
        if quote and texts and _normal_ws_exact(quote) not in _normal_ws_exact(own_text):
            flag("quotation_not_in_held_text", f"operative_clauses[{i}]: cited quotation absent from this order's exact held-text span", src.get("evidence_id"))

    # Attributed quotations and known template phrases must occur in this
    # order's own operative text. A nearby negation protects explicit absence.
    reasoning_keys = {"reason", "rationale", "judgment_reason", "research_rationale", "current_legal_basis", "savings_reason"}
    def phrasewalk(v, path="claim"):
        if isinstance(v, dict):
            for k, child in v.items():
                if k in reasoning_keys and isinstance(child, str):
                    for part_key, part in reasoning_parts(child):
                        for qm in QUOTED_RE.finditer(part):
                            phrase = qm.group(1) or qm.group(2)
                            prefix = part[max(0, qm.start()-140):qm.start()]
                            attributed = re.search(r"\b(?:this|the) order\s+(?:sets?|states?|says?|provides?|directs?|requires?|contains?|includes?)\b[^.!?;]{0,115}$", prefix, re.I)
                            recommendation = part_key == "independent_command_check" and re.match(r"Approval recommended\b", phrase, re.I)
                            if not (attributed or recommendation) or len(phrase.split()) < 3 or not texts:
                                continue
                            if attributed and (EO_RE.search(attributed.group(0)) or re.search(r"\b(?:resolution|statute|repeal)\b", attributed.group(0), re.I)):
                                continue
                            if _normal_ws_exact(phrase) in _normal_ws_exact(own_text):
                                continue
                            full_original = next((t for ident, _, t in texts if ident == dossier.get("original_source_id")), "")
                            if _normal_ws_exact(phrase) in _normal_ws_exact(full_original):
                                flag("attributed_phrase_absent", f"{path}.{k}.{part_key}: quoted wording is outside the verified target envelope; it occurs elsewhere in the file and may be a recital or neighboring order, requiring inspection")
                            else:
                                flag("attributed_phrase_absent", f"{path}.{k}.{part_key}: {phrase!r} is absent from the verified cited order text")
                        for kind, pattern in STOCK_PHRASES.items():
                            for match in pattern.finditer(part):
                                before = part[max(0, match.start()-80):match.start()]
                                after = part[match.end():match.end()+45]
                                # Negation must attach to this noun phrase;
                                # 'no earlier end' in a preceding clause does
                                # not negate a subsequently asserted standstill.
                                if re.search(r"\b(?:no|without|lacks?|not contain|not include)\s+(?:[\w-]+\s+){0,2}$", before, re.I):
                                    continue
                                if re.match(r"\s+(?:is |was |does |did )?(?:not present|not appear|absent|missing|not in)\b", after, re.I):
                                    continue
                                own_scope = part_key in {"scope_check", "independent_command_check"} or k == "judgment_reason"
                                explicit = re.search(r"\b(?:this|the) order\s+(?:expressly\s+)?(?:says|states|provides|contains|includes|directs|requires)\b|\bthe order's (?:operative )?text\b", before, re.I)
                                if not (own_scope or explicit) or not texts:
                                    continue
                                source_pattern = SOURCE_CONCEPTS[kind]
                                if source_pattern.search(own_text):
                                    continue
                                full_original = next((t for ident, _, t in texts if ident == dossier.get("original_source_id")), "")
                                if source_pattern.search(full_original):
                                    coverage.append({"code": "stock_concept_outside_target_envelope", "concept": kind,
                                                     "detail": "concept appears elsewhere in the verified source; recital versus neighboring-order attribution requires inspection"})
                                else:
                                    flag("attributed_stock_phrase_absent", f"{path}.{k}.{part_key}: attributed {kind.replace('_', ' ')} has no corresponding wording in the verified held order source")
                    # Explicit unquoted content attribution is a candidate for
                    # direct source comparison. Keep the pattern narrow and
                    # suppress negated statements such as "does not direct".
                    for sentence in re.split(r"(?<=[.!?])\s+", child):
                        explicit = re.search(r"\bthis order\s+(?:directs|states|says|provides|contains|includes|requires)\s+(?:that\s+)?(.{24,240})", sentence, re.I)
                        if explicit and not NEGATION_RE.search(sentence[:explicit.start(1)]):
                            predicate = explicit.group(1).strip(" .;:'\"“”")
                            if len(predicate.split()) >= 5 and _normal_ws_exact(predicate) not in _normal_ws_exact(own_text):
                                coverage.append({"code": "ambiguous_attributed_content", "field": f"{path}.{k}", "detail": "explicit order-content paraphrase is not an exact held-text match; human interpretation required"})
                phrasewalk(child, f"{path}.{k}")
        elif isinstance(v, list):
            for n, x in enumerate(v): phrasewalk(x, f"{path}[{n}]")
    phrasewalk(claim)

    # Target identity must retain the packet's literal suffix. Compare the
    # claim field and its own cited APP/register metadata; do not scan unrelated
    # order numbers in rationale text, which creates false positives.
    claim_json = json.dumps(claim, ensure_ascii=False)
    expected_id = dossier.get("instrument_id", "")
    original_rep = claim.get("original_representation", {})
    if isinstance(original_rep, dict) and expected_id:
        cited_id = str(original_rep.get("instrument_id") or "")
        if cited_id and cited_id.casefold() != expected_id.casefold():
            code = "suffix_dropped" if expected_id[-1:].isalpha() and cited_id == expected_id[:-1] else "app_register_number_mismatch"
            flag(code, f"original representation identifies {cited_id}; packet/register identifies {expected_id}", original_rep.get("evidence_id"))
        suffix_match = re.fullmatch(r"EO:(\d+)([A-Z])", expected_id, re.I)
        page_item = str(original_rep.get("page_or_item") or "")
        if suffix_match and page_item and re.search(rf"\b{suffix_match.group(1)}\s*[- ]\s*{suffix_match.group(2)}\b", page_item, re.I) is None:
            if re.search(rf"\b{suffix_match.group(1)}\b", page_item):
                flag("app_title_suffix_mismatch", f"APP/register title omits the target suffix {suffix_match.group(2)}", original_rep.get("evidence_id"))
        expected_record = _evidence_records(dossier).get(dossier.get("original_source_id"), {})
        expected_source = expected_record.get("source", {}) if isinstance(expected_record, dict) else {}
        for item in _metadata_issue(expected_source, original_rep, dossier.get("original_source_id")):
            flags.append(item)

    # Event actor identities and later-event quotations must match the exact
    # cited event source, not the target order's original text.
    named_events = set()
    sourced_first_ends = set()
    event_rows = []
    for clause in claim.get("operative_clauses", []) if isinstance(claim.get("operative_clauses"), list) else []:
        if not isinstance(clause, dict): continue
        if isinstance(clause.get("first_end"), dict): event_rows.append((clause, clause["first_end"], "first_end"))
        for event in clause.get("later_events", []) if isinstance(clause.get("later_events"), list) else []:
            if isinstance(event, dict): event_rows.append((clause, event, "later_event"))
    for clause, event, event_kind in event_rows:
        source = event.get("source", {})
        ident, expected_source = _source_record(dossier, source)
        actor = event.get("actor") or ""
        actor_label = _eo_label(actor)
        source_label = _eo_label(_source_metadata(source))
        if actor_label:
            if source_label and actor_label != source_label:
                code = "suffix_dropped" if source_label.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ").isdigit() and actor_label == source_label.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ") else "later_actor_source_mismatch"
                flag(code, f"later-event actor {actor} does not preserve source label EO {source_label}", ident)
        if not source:
            coverage.append({"code": event_kind + "_source_missing", "actor": actor, "scope_id": clause.get("scope_id")})
            continue
        if expected_source is None:
            coverage.append({"code": "later_event_source_not_in_dossier", "actor": actor, "evidence_id": source.get("evidence_id")})
        else:
            if actor_label and event_kind == "later_event": named_events.add(actor_label)
            if actor_label and event_kind == "first_end": sourced_first_ends.add(actor_label)
            for item in _metadata_issue(expected_source, source, ident): flags.append(item)
        event_text, source_issue = _event_source_text(source, repo)
        if source_issue:
            coverage.append({"code": "later_event_source_text_unavailable", "reason": source_issue, "evidence_id": source.get("evidence_id")})
        else:
            quoted = source.get("quote")
            if quoted and _normal_ws_exact(quoted) not in _normal_ws_exact(event_text):
                flag("later_event_quote_not_in_cited_source", "later-event quotation is absent from its exact cited source span", ident)
            for key in ("reason", "rationale", "judgment_reason"):
                reason = event.get(key)
                if not isinstance(reason, str): continue
                for q in _quoted_strings(reason):
                    if _normal_ws_exact(q) and _normal_ws_exact(q) not in _normal_ws_exact(event_text):
                        flag("later_event_reason_quote_not_in_source", f"later-event {key} quotation {q!r} absent from cited event source", ident)
        if expected_source is not None:
            local_reason = " ".join(str(event.get(k) or "") for k in ("reason", "rationale", "judgment_reason"))
            refs = set(FR_RE.findall(local_reason)); expected_refs = set(FR_RE.findall(_source_metadata(expected_source)))
            if refs and expected_refs and not refs.issubset(expected_refs):
                flag("fr_citation_mismatch", f"event reason cites FR page(s) {sorted(refs)} outside its pinned source {sorted(expected_refs)}", ident)
            issue_dates = set(re.findall(r"\b(?:issue|published|publication|issued)\s+(?:on|of)?\s*(\d{4}-\d{2}-\d{2})", local_reason, re.I))
            source_issue_date = re.search(r"/FR-(\d{4}-\d{2}-\d{2})/", str(expected_source.get("url") or ""))
            if issue_dates and source_issue_date and issue_dates != {source_issue_date.group(1)}:
                flag("fr_issue_date_mismatch", f"event reason issue date(s) {sorted(issue_dates)} differ from its pinned source {source_issue_date.group(1)}", ident)

    # Instruments named as agents of an ending/change in reasoning need a
    # corresponding source-backed later-event record.
    event_texts = []
    for clause in claim.get("operative_clauses", []) if isinstance(claim.get("operative_clauses"), list) else []:
        if isinstance(clause, dict): event_texts.append(str(clause.get("judgment_reason") or ""))
    value = claim.get("whole_order_end")
    if isinstance(value, dict): event_texts.extend(str(v) for v in value.values() if isinstance(v, str))
    elif isinstance(value, str): event_texts.append(value)
    sentences = [s for text in event_texts for s in re.split(r"(?<=[!?])\s+|(?<=[a-z0-9\"'])\.\s+(?=[A-Z])", text)]
    def actor_context(sentence, match):
        # The object of 'EO A revoked EO B' is not an assertion that B was a
        # later actor. A positive rule must preserve that grammatical role.
        tail = sentence[match.end():]
        head = sentence[:match.start()]
        object_of_action = re.search(r"\b(?:amend\w*|revok\w*|rescind\w*|supersed\w*|terminat\w*|abolish\w*|replac\w*|extend\w*|modif\w*|renam\w*)\s+(?:(?:the|parent)\s+)?$|\b(?:revocation|amendment|repeal)\s+of\s+(?:the\s+)?$", head, re.I)
        if object_of_action:
            return False
        active = re.match(r"\s*(?:\([^)]{0,100}\)\s*)?(?:,?\s*(?:section|sec\.|§)\s+[\w().-]+\s*,?\s*)?(?:expressly\s+)?(?:amends?|amended|revokes?|revoked|rescinds?|rescinded|supersedes?|superseded|terminates?|terminated|abolishes|abolished|transfers?|transferred|replaces?|replaced|extends?|extended|modifies|modified|renames?|renamed|substitutes?|substituted|rewrites?|rewrote)\b(?!\s+by\b)", tail, re.I)
        passive_by = re.search(r"\b(?:amended|revoked|rescinded|superseded|terminated|abolished|transferred|replaced|extended|modified|renamed)\s+(?:expressly\s+)?by\s*$", head, re.I)
        explicit_list = re.search(r"\b(?:later|subsequent)\s+(?:events|amendments|instruments|orders)\b", sentence, re.I)
        return bool(active or passive_by or explicit_list)
    for sentence in sentences:
        for match in EO_RE.finditer(sentence):
            label = re.sub(r"[- ]", "", match.group(1)).upper()
            if label == _eo_label(expected_id) or not actor_context(sentence, match):
                continue
            if label not in named_events and label not in sourced_first_ends:
                flag("later_instrument_named_without_event_source", f"reasoning names EO {label} as an actor/change without a matching later_events source")
        for match in OTHER_INSTRUMENT_RE.finditer(sentence):
            label = match.group(1).split()[0].upper() + ":" + re.sub(r"[- ]", "", match.group(2)).upper()
            if actor_context(sentence, match):
                sourced = any(str(event.get("actor", "")).upper().replace(" ", "") == label.replace(" ", "") and bool(event.get("source")) for _, event in _later_events(claim))
                if not sourced:
                    flag("later_instrument_named_without_event_source", f"reasoning names {label} as an actor/change without a matching later_events source")

    # Later-event coverage: explicit search declarations with empty/no events
    # remain a coverage gap, never a legal defect finding.
    clauses = claim.get("operative_clauses", [])
    if not isinstance(clauses, list): clauses = []
    expected_clause_ids = {c.get("scope_id") for c in dossier.get("clauses", []) if c.get("scope_id")}
    claim_scope_ids = {c.get("scope_id") for c in clauses if isinstance(c, dict) and c.get("scope_id")}
    for absent in sorted(expected_clause_ids - claim_scope_ids):
        coverage.append({"code": "operative_clause_not_covered", "scope_id": absent})
    for i, clause in enumerate(clauses):
        if not isinstance(clause, dict): continue
        search = clause.get("later_source_search") or claim.get("later_source_search")
        if not search:
            coverage.append({"code": "later_event_search_not_recorded", "clause": i})
        elif not clause.get("later_events") and not clause.get("later_event_ids"):
            coverage.append({"code": "later_events_none_recorded", "clause": i})

    # For no-other-order assertions, search literal names (not numeric IDs) and
    # disclose the bounded corpus. A negative hit is expected evidence, not a
    # defect flag. The producer's search scope must itself name the literal.
    rationale_texts = []
    for key in ("research_rationale", "savings_residuals"):
        val = claim.get(key)
        if isinstance(val, str): rationale_texts.append(val)
        elif isinstance(val, dict): rationale_texts.extend(str(x) for x in val.values() if isinstance(x, str))
    for clause in claim.get("operative_clauses", []) if isinstance(claim.get("operative_clauses"), list) else []:
        if isinstance(clause, dict): rationale_texts.append(str(clause.get("judgment_reason") or ""))
    searches = claim.get("later_source_search", [])
    search_text = " ".join(str(x.get("query_or_scope") or "") for x in searches if isinstance(x, dict)) if isinstance(searches, list) else str(searches or "")
    for text in rationale_texts:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            if not NO_ORDER_RE.search(sentence): continue
            names = []
            for q in _quoted_strings(sentence):
                if len(q.split()) >= 2 and not EO_RE.search(q): names.append(q)
            named = re.search(r"\bnames?\s+(?:the\s+)?([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){1,5})", sentence)
            if named: names.append(named.group(1).strip(" .,:;"))
            names = list(dict.fromkeys(n for n in names if len(n.split()) >= 2))
            if not names:
                coverage.append({"code": "literal_name_not_extractable", "assertion": sentence[:240]})
                continue
            for name in names:
                query_has_name = _normal_ws(name) in _normal_ws(search_text)
                if not query_has_name:
                    coverage.append({"code": "literal_name_search_missing", "name": name, "assertion": sentence[:240]})
                if packet_path:
                    hits, absent, indexed, scope = held_corpus_search(packet_path, [name], repo, corpus_cache)
                    coverage.append({"code": "literal_name_corpus_search", "name": name,
                                     "matched_file_count": len(hits[name]), "matches": hits[name][:10],
                                     "matches_truncated": len(hits[name]) > 10,
                                     "corpus_kind": "hash_pinned_Apollo_packet_held_texts",
                                     "indexed_files": indexed, "unavailable_files": len(absent),
                                     "available_pins_hash_verified": not absent,
                                     "all_indexed_files_verified": not absent,
                                     "known_full_scope": scope,
                                     "full_discovered_corpus_covered": bool(scope.get("discovered_count") == indexed and not absent)})
                    if scope.get("discovered_count") and indexed < scope["discovered_count"]:
                        coverage.append({"code": "literal_name_corpus_scope_incomplete", "indexed_files": indexed,
                                         "known_discovered_files": scope["discovered_count"],
                                         "excluded_files": scope.get("excluded_clause_drafts"),
                                         "detail": "search is restricted to packet-pinned texts; it does not establish the all-held-text negative"})
                else:
                    coverage.append({"code": "literal_name_corpus_search_unavailable", "name": name})
    return {"line": line, "instrument_id": iid, "flags": flags, "coverage_gaps": coverage,
            "held_text_sources_checked": len(texts), "held_text_sources_missing": len(missing),
            "held_text_integrity_failures": len(bad)}


def lint(applied: Path, repo=REPO):
    packet_path, packet, dossiers, claims = load_context(applied)
    corpus_cache = {}
    rows = [lint_one(n, c, dossiers, Path(repo).resolve(), packet_path, corpus_cache) for n, c in claims]
    result = {"schema": SCHEMA, "mode": "advisory_source_comparison", "packet": str(packet_path),
              "packet_fingerprint": packet.get("fingerprint"), "claims_checked": len(rows),
              "defect_flags": sum(len(r["flags"]) for r in rows),
              "coverage_gaps": sum(len(r["coverage_gaps"]) for r in rows),
              "claims_with_flags": sum(bool(r["flags"]) for r in rows),
              "claims_with_coverage_gaps": sum(bool(r["coverage_gaps"]) for r in rows),
              "results": rows,
              "limitations": ["advisory only; not a legal conclusion or review verdict", "does not establish source authenticity", "heuristic scans can miss paraphrases and produce false positives"]}
    return result


def _markdown_sections(text):
    sections = {}
    current = None
    body = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None: sections[current] = "\n".join(body).strip()
            current, body = m.group(1), []
        elif current is not None:
            body.append(line)
    if current is not None: sections[current] = "\n".join(body).strip()
    return sections


def view(packet_path: Path, eo: str, write: Path | None = None):
    packet = read_json(packet_path); dossiers = batch.decode(packet)
    iid = eo if eo.startswith("EO:") else "EO:" + eo
    dossier = dossiers.get(iid)
    if dossier is None: raise KeyError(f"{iid} is not in packet")
    keep = {"instrument_id", "title", "signing_date", "whole_order_status", "original_source_id", "clauses", "missing", "fingerprint"}
    compact = {k: dossier[k] for k in keep if k in dossier}
    evidence = dossier.get("evidence", {})
    compact["source_catalogue"] = {k: v.get("source", {}) for k, v in evidence.items() if isinstance(v, dict) and isinstance(v.get("source"), dict)}
    original_meta = evidence.get(dossier.get("original_source_id"), {}).get("source", {})
    compact["target_source_metadata"] = {k: original_meta.get(k) for k in ("instrument_id", "page_or_item", "signing_date", "filing_date", "grade", "url") if k in original_meta}
    original = evidence.get(dossier.get("original_source_id"), {})
    compact["own_original_text"], compact["own_text_boundary"] = bounded_own_text(dossier)
    compact["mechanical_shared_tasks"] = [t for t in packet.get("shared_tasks", []) if iid in t.get("affected_orders", [])]
    compact["prior_research_for_order"] = packet.get("prior_research", {}).get("orders", {}).get(iid, {})
    verified_texts, missing_texts, bad_texts = instrument_texts(dossier, REPO)
    compact["source_file_verification"] = {"text_sources_checked": len(verified_texts),
        "unavailable": missing_texts, "integrity_failures": bad_texts,
        "embedded_packet_text_used": True}
    packet_dir = Path(packet_path).resolve().parent
    lookup_path = packet_dir / "LOOKUPS.json"
    if not lookup_path.is_file(): lookup_path = packet_dir.parent / "LOOKUPS.json"
    if lookup_path.is_file():
        lookup = read_json(lookup_path)
        compact["lookup_leads"] = lookup.get("members", {}).get(iid, {})
    details_path = packet_dir / "LOOKUPS.details.json"
    if not details_path.is_file(): details_path = packet_dir.parent / "LOOKUPS.details.json"
    if details_path.is_file():
        details = read_json(details_path)
        compact["bounded_name_search"] = details.get("members", {}).get(iid, {})
        cov = details.get("corpus", {}).get("coverage", {})
        compact["lookup_corpus_scope"] = {k: (len(cov[k]) if isinstance(cov.get(k), (list, dict)) else cov.get(k)) for k in (
            "scope", "tracked_inventory_status", "tracked_not_discovered", "excluded_clause_drafts",
            "directory_errors", "unreadable_sources", "discovered_count", "readable_count", "source_bytes") if k in cov}
    # NRA batches carry a shared NIRA analysis. Include only the broadly
    # applicable sections, with exact source and hash; this is context, not a
    # per-order finding or approval.
    batch_name = next((part for part in packet_path.resolve().parts if re.fullmatch(r"n\d{2}", part, re.I)), None)
    if batch_name:
        memo = REPO / "research/excavator/claude-nira-sweep-2026-10-29/SHARED_ANALYSIS.md"
        if memo.is_file():
            sections = _markdown_sections(memo.read_text(encoding="utf-8"))
            selected = ["Conclusion", "Events that do not end a code approval", "What each order still needs"]
            title = str(dossier.get("title", ""))
            if re.search(r"\b(?:denial|denies|dismiss|exemption)\b", title, re.I):
                selected.append("Denials of exemption and other one-time determinations")
            compact["shared_analysis_memo"] = {"path": str(memo.relative_to(REPO)), "sha256": hashlib.sha256(memo.read_bytes()).hexdigest(),
                "sections": {h: sections[h] for h in selected if h in sections},
                "scope_note": "Batch-level shared context. It makes no order-specific determination; read this order's own text and sources."}
        else:
            compact["shared_analysis_memo"] = {"missing": "SHARED_ANALYSIS.md not available", "coverage_gap": True}
    compact["packet_fingerprint"] = packet.get("fingerprint")
    compact_bytes = len(json.dumps(compact, ensure_ascii=False).encode("utf-8"))
    packet_bytes = Path(packet_path).stat().st_size
    compact["approx_view_tokens"] = (compact_bytes + 3) // 4
    compact["approx_full_packet_tokens"] = (packet_bytes + 3) // 4
    compact["approx_size_reduction_tokens"] = max(0, (packet_bytes - compact_bytes) // 4)
    compact["token_estimate_note"] = "Approximate UTF-8 bytes/4. Size reduction is a token-count proxy only; actual prompt/cache tokens and cost savings were not observed."
    if write:
        destination = Path(write)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        compact["written_to"] = str(destination)
    return compact


def cost(path: Path, filed_manifest: Path | None = None):
    with path.open(encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f))
    columns = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "tool_calls", "active_seconds")
    groups = {}
    errors = []
    for row in rows:
        batch_id = row.get("batch", "")
        track = row.get("track") or ("NRA" if batch_id.lower().startswith("n") else "General" if batch_id.lower().startswith("g") else "unknown")
        key = (track, row.get("role", ""), row.get("model", ""))
        g = groups.setdefault(key, {"rows": 0, "sums": defaultdict(Decimal), "reported": Counter(), "errors": []})
        g["rows"] += 1
        for col in columns:
            raw = row.get(col)
            if raw is None or not str(raw).strip(): continue
            try:
                value = Decimal(str(raw).strip())
                if not value.is_finite(): raise InvalidOperation
                if col != "active_seconds" and value != value.to_integral_value(): raise InvalidOperation
            except InvalidOperation:
                issue = {"row": row.get("batch"), "column": col, "value": raw, "reason": "invalid_numeric_value"}
                errors.append(issue); g["errors"].append(issue); continue
            g["sums"][col] += value; g["reported"][col] += 1
    grouped = []
    for key, g in sorted(groups.items()):
        out = {"track": key[0], "role": key[1], "model": key[2], "agents": g["rows"], "field_coverage": {}}
        for col in columns:
            complete = g["reported"][col] == g["rows"] and not any(e["column"] == col for e in g["errors"])
            total = g["sums"].get(col, Decimal(0))
            out[col] = (int(total) if total == total.to_integral_value() else float(total)) if complete else None
            out["field_coverage"][col] = {"rows_reported": g["reported"][col], "rows_total": g["rows"], "complete": complete}
        out["errors"] = list(g["errors"])
        grouped.append(out)
    # Denominators come from an explicit JSON sidecar or the sibling report's
    # result table. No batch subtotal is divided by a track-wide denominator.
    filed = {}
    report = Path(path).resolve().with_name("REPORT.md")
    denominator_source = None
    if filed_manifest:
        manifest = read_json(filed_manifest)
        for k, v in manifest.get("filed_claims", manifest).items():
            try:
                value = int(v)
                if value < 0: raise ValueError
                filed[str(k)] = value
            except (TypeError, ValueError): errors.append({"filed_manifest": str(k), "value": v, "reason": "invalid_denominator"})
        denominator_source = str(filed_manifest)
    elif report.is_file():
        for line in report.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and (cells[0].startswith("NRA (") or cells[0].startswith("General (")) and len(cells) >= 2:
                filed["NRA" if cells[0].startswith("NRA (") else "General"] = int(cells[-1])
        denominator_source = str(report)
    for g in grouped:
        denominator = filed.get(g["track"])
        if denominator:
            g["filed_claims_denominator"] = denominator
            g["denominator_source"] = "sibling Apollo REPORT.md track table"
            for col in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "active_seconds"):
                g[col + "_per_filed_claim"] = round(g[col] / denominator, 2) if g[col] is not None else None
    return {"schema": "geddes-cost/v1", "source": str(path), "telemetry_rows": len(rows),
            "filed_claims_denominators": filed, "denominator_source": denominator_source,
            "groups": grouped, "errors": errors,
            "note": "blank telemetry stays unknown; active seconds retain fractions; actual token cost savings are unknown"}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("lint"); x.add_argument("applied", type=Path); x.add_argument("--repo", type=Path, default=REPO)
    x = sub.add_parser("view"); x.add_argument("packet", type=Path); x.add_argument("eo"); x.add_argument("--write", type=Path)
    x = sub.add_parser("cost"); x.add_argument("telemetry", type=Path); x.add_argument("--filed-manifest", type=Path)
    a = p.parse_args(argv)
    try:
        result = lint(a.applied, a.repo) if a.cmd == "lint" else view(a.packet, a.eo, a.write) if a.cmd == "view" else cost(a.telemetry, a.filed_manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2

if __name__ == "__main__": raise SystemExit(main())
