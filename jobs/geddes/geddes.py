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
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "jobs/claim-kit"))
import batch  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_checks as SC
import citation_checks as CC
import event_checks as EC
import name_checks as NC
import consistency_checks as CON
import citing_checks as CIT

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
    if "char_start" in source or "char_end" in source:
        return None, "source_span_invalid"
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


def held_corpus_search(packet_path, names, repo, corpus_cache=None):
    return NC.scan_names(packet_path, names, repo, corpus_cache)


def lint_one(line, claim, dossiers, repo: Path, packet_path=None, corpus_cache=None):
    repo = Path(repo).resolve()
    iid = claim.get("instrument_id", "")
    dossier = dossiers.get(iid)
    if dossier is None:
        return {"line": line, "instrument_id": iid, "flags": [],
                "coverage_gaps": [{"code": "packet_member_missing"}]}
    cache = {} if corpus_cache is None else corpus_cache
    flags, gaps = [], []
    for name, module in (("source", SC), ("citation", CC), ("event", EC), ("name", NC), ("consistency", CON), ("citing", CIT)):
        # Citing checks share the name module's snapshot-verified corpus cache.
        result = module.check(claim, dossier, repo, packet_path, cache.setdefault("name" if module is CIT else name, {}))
        flags.extend(result["flags"])
        gaps.extend(result["coverage_gaps"])
    original = claim.get("original_representation") or {}
    pinned_original = (dossier.get("evidence") or {}).get(dossier.get("original_source_id"), {}).get("source")
    if isinstance(original, dict) and pinned_original and CC._verified(pinned_original, repo):
        flags.extend(_metadata_issue(pinned_original, original, dossier.get("original_source_id")))
    for clause in claim.get("operative_clauses") or []:
        if not isinstance(clause, dict):
            continue
        events = [clause.get("first_end")] + (clause.get("later_events") or [])
        for event in events:
            if not isinstance(event, dict) or not isinstance(event.get("source"), dict):
                continue
            source = event["source"]
            evidence_id, expected = _source_record(dossier, source)
            if not expected or not CC._verified(expected, repo):
                continue
            flags.extend(_metadata_issue(expected, source, evidence_id))
            record = (dossier.get("evidence") or {}).get(evidence_id, {})
            expected_actor = _eo_label(record.get("actor_id")) or _eo_label(expected.get("instrument_id")) or _eo_label(_source_metadata(expected))
            actual_actor = _eo_label(event.get("actor"))
            if actual_actor and expected_actor and actual_actor != expected_actor:
                code = "suffix_dropped" if actual_actor == expected_actor.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ") else "later_actor_source_mismatch"
                flags.append({"code": code, "detail": f"Claim actor EO {actual_actor} differs from the verified actor record EO {expected_actor}.", "source_id": evidence_id})
    # A row reports exact source defects and incomplete checks separately.
    # Nothing here changes a producer's claim, status, review or publication.
    return {"line": line, "instrument_id": iid, "flags": flags,
            "coverage_gaps": gaps,
            "held_text_integrity_failures": sum("hash" in str(g) or "integrity" in str(g) for g in gaps)}


SPAN_KEYS = ("span", "flagged_text", "quote", "phrase", "assertion", "reasoning_sentence")


def flag_id_for(instrument_id, flag):
    """Deterministic 16-hex id over instrument, code, scope and the flagged text or detail."""
    span = next((flag[k] for k in SPAN_KEYS if isinstance(flag.get(k), str) and flag[k].strip()), "")
    detail = flag.get("detail") if isinstance(flag.get("detail"), str) else ""
    if not span and not detail:
        # No text field at all: bind the id to the whole flag so distinct flags stay distinct.
        detail = json.dumps({k: v for k, v in flag.items() if k != "flag_id"}, sort_keys=True, ensure_ascii=False, default=str)
    material = "\x1f".join([str(instrument_id or ""), str(flag.get("code") or ""), str(flag.get("scope_id") or ""), span, detail])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def stamp_flag_ids(rows):
    """Give every flag a stable flag_id, keeping any id a check already supplied."""
    for row in rows:
        for flag in row.get("flags", []):
            if isinstance(flag, dict) and not flag.get("flag_id"):
                flag["flag_id"] = flag_id_for(row.get("instrument_id"), flag)
    return rows


@contextmanager
def _count_file_reads():
    """Count the distinct files, and total reads, made through Path.read_bytes/read_text."""
    state = {"paths": set(), "calls": 0}
    original_bytes, original_text = Path.read_bytes, Path.read_text

    def read_bytes(self):
        state["paths"].add(str(self.absolute())); state["calls"] += 1
        return original_bytes(self)

    def read_text(self, *args, **kwargs):
        state["paths"].add(str(self.absolute())); state["calls"] += 1
        return original_text(self, *args, **kwargs)
    Path.read_bytes, Path.read_text = read_bytes, read_text
    try:
        yield state
    finally:
        Path.read_bytes, Path.read_text = original_bytes, original_text


def lint(applied: Path, repo=REPO):
    started = time.monotonic()
    with _count_file_reads() as reads:
        packet_path, packet, dossiers, claims = load_context(applied)
        with NC.Snapshot(repo) as name_cache:
            corpus_cache = {"name": name_cache}
            rows = [lint_one(n, c, dossiers, Path(repo).resolve(), packet_path, corpus_cache) for n, c in claims]
    stamp_flag_ids(rows)
    result = {"schema": SCHEMA, "mode": "advisory_source_comparison", "packet": str(packet_path),
              "seconds": round(time.monotonic() - started, 3),
              "files_read": len(reads["paths"]), "file_reads": reads["calls"],
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


VIEW_CAPS = {"machine_searches": 12, "chain_events": 25, "citable_evidence": 40, "clause_inventory": 40,
             "draft_clause_rows": 40, "questions_per_clause": 6, "text_chars": 600, "reason_chars": 2000,
             "claim_bytes": 20000, "claim_string_chars": 400}


def _cap_list(items, limit):
    """Return (items shown, bound report); a long list keeps its true total and says it was cut."""
    items = list(items)
    return items[:limit], {"total": len(items), "shown": min(len(items), limit), "truncated": len(items) > limit}


def _cap_text(value, limit):
    if not isinstance(value, str) or len(value) <= limit: return value
    return value[:limit] + f"... [truncated; {len(value)} characters in all]"


def _source_brief(source):
    source = source if isinstance(source, dict) else {}
    return {k: source.get(k) for k in ("page_or_item", "signing_date", "url", "text_path") if source.get(k) is not None}


def _machine_searches_view(dossier):
    rows = []
    for m in dossier.get("machine_searches") or []:
        if not isinstance(m, dict): continue
        entry = m.get("entry") if isinstance(m.get("entry"), dict) else {}
        search_id = m.get("search_id")
        rows.append({"search_id": search_id,
                     "kind": str(search_id).split(":", 1)[0] if search_id else None,
                     "searched_by": entry.get("searched_by"), "checked_on": entry.get("checked_on"),
                     "complete": m.get("complete"),
                     "machine_hits_for_this_order": m.get("machine_hits_for_this_order"),
                     "coverage": {"repository": _cap_text(entry.get("repository"), VIEW_CAPS["text_chars"]),
                                  "query_or_scope": _cap_text(entry.get("query_or_scope"), VIEW_CAPS["text_chars"]),
                                  "scope_note": _cap_text(m.get("scope_note"), VIEW_CAPS["text_chars"])}})
    shown, bound = _cap_list(rows, VIEW_CAPS["machine_searches"])
    hits = [r["machine_hits_for_this_order"] for r in rows]
    bound["hit_total"] = sum(hits) if hits and all(type(h) is int for h in hits) else "unknown"
    bound["incomplete_searches"] = sum(r["complete"] is not True for r in rows)
    return {"searches": shown, "bound": bound,
            "note": "Machine searches are leads and coverage statements run before this packet was frozen; they are not independent review."}


def _later_events_view(dossier):
    chain = dossier.get("chain") if isinstance(dossier.get("chain"), dict) else {}
    evidence = dossier.get("evidence") if isinstance(dossier.get("evidence"), dict) else {}
    by_actor = defaultdict(list)
    citable = []
    for ident, record in sorted(evidence.items()):
        if not isinstance(record, dict) or ident.startswith(("CLAUSES:", "TERM:", "ORIGINAL:")): continue
        if record.get("role") == "reviewed_occurrence_interval": continue
        actor = record.get("actor_id")
        by_actor[actor].append(ident)
        source = record.get("actor_source") or record.get("source")
        citable.append({"evidence_id": ident, "role": record.get("role"), "actor_id": actor, **_source_brief(source)})
    events = []
    for event in chain.get("events") or []:
        if not isinstance(event, dict): continue
        events.append({"id": event.get("id"), "actor_id": event.get("actor_id"), "signing_date": event.get("signing_date"),
                       "verb": event.get("verb"), "how_named": event.get("how_named"), "confidence": event.get("confidence"),
                       "sections_touched": event.get("sections_touched"), "notes": _cap_text(event.get("notes"), VIEW_CAPS["text_chars"]),
                       "provision_text": _cap_text(event.get("provision_text"), VIEW_CAPS["text_chars"]),
                       "source": _source_brief(event.get("source")),
                       "citable_evidence_ids": by_actor.get(event.get("actor_id"), [])})
    shown_events, event_bound = _cap_list(events, VIEW_CAPS["chain_events"])
    shown_evidence, evidence_bound = _cap_list(citable, VIEW_CAPS["citable_evidence"])
    return {"chain": {"id": chain.get("id"), "confidence": chain.get("confidence"), "notes": chain.get("notes"),
                      "generic_refs_excluded": chain.get("generic_refs_excluded"), "events": shown_events, "bound": event_bound},
            "citable_evidence": {"records": shown_evidence, "bound": evidence_bound,
                                 "note": "Evidence ids a later_events entry may cite from this packet (actor texts and actor provisions). A later instrument absent from this list is not citable from the packet."},
            "actor_contexts": [c for c in (dossier.get("actor_contexts") or []) if isinstance(c, dict)][:VIEW_CAPS["citable_evidence"]]}


def _packet_side_file(packet_path, name):
    folder = Path(packet_path).resolve().parent
    for candidate in (folder / name, folder.parent / name):
        if candidate.is_file(): return candidate
    return None


def _clause_inventory_view(dossier, iid, packet_path, context=None):
    obligations = {o.get("scope_id"): o for o in dossier.get("lifecycle_obligations") or [] if isinstance(o, dict)}
    rows = []
    for clause in dossier.get("clauses") or []:
        if not isinstance(clause, dict): continue
        ob = obligations.get(clause.get("scope_id"), {})
        questions, q_bound = _cap_list(ob.get("questions") or [], VIEW_CAPS["questions_per_clause"])
        rows.append({"id": clause.get("id"), "scope_id": clause.get("scope_id"), "kind": clause.get("kind"), "label": clause.get("label"),
                     "pdf_page": clause.get("pdf_page"), "char_start": clause.get("char_start"), "char_end": clause.get("char_end"),
                     "lifecycle_state": ob.get("state"), "established_ending": ob.get("established_ending"),
                     "wording_features": ob.get("wording_features"), "own_term_evidence_ids": ob.get("own_term_evidence_ids"),
                     "later_actor_evidence_ids": ob.get("later_actor_evidence_ids"),
                     "questions": [_cap_text(q, VIEW_CAPS["text_chars"]) for q in questions], "questions_bound": q_bound})
    inventory, inventory_bound = _cap_list(rows, VIEW_CAPS["clause_inventory"])
    out = {"clauses": inventory, "bound": inventory_bound,
           "dossier_draft_gate_errors": dossier.get("draft_gate_errors"), "dossier_draft_material_gaps": dossier.get("draft_material_gaps")}
    sheet = _packet_side_file(packet_path, "clauses.csv")
    if sheet is None:
        out["draft_sheet"] = {"present": False}
        return out
    shared = {}
    rationales = _packet_side_file(packet_path, "RATIONALES.json")
    if rationales:
        try: shared = context.json(rationales) if context else read_json(rationales)
        except (OSError, ValueError): shared = {}
    def resolve(value):
        if isinstance(value, str) and value.startswith("@rationale:") and isinstance(shared.get(value.split(":", 1)[1]), str):
            return shared[value.split(":", 1)[1]]
        return value
    if context:
        mine = context.clause_rows(sheet, iid)
    else:
        with sheet.open(encoding="utf-8-sig", newline="") as f:
            mine = [r for r in csv.DictReader(f) if r.get("instrument_id") == iid]
    known = {c.get("scope_id") for c in dossier.get("clauses") or [] if isinstance(c, dict)}
    drafts = [{"scope_id": r.get("scope_id"), "in_dossier_inventory": r.get("scope_id") in known, "state": r.get("state"),
               "end_id": r.get("end_id"), "effective_date": r.get("effective_date"), "mechanism": r.get("mechanism"),
               "reason": _cap_text(resolve(r.get("reason")), VIEW_CAPS["reason_chars"]),
               "inventory_source_id": r.get("inventory_source_id"),
               "inventory_char_start": r.get("inventory_char_start"), "inventory_char_end": r.get("inventory_char_end"),
               "inventory_reason": _cap_text(resolve(r.get("inventory_reason")), VIEW_CAPS["reason_chars"])} for r in mine]
    shown, bound = _cap_list(drafts, VIEW_CAPS["draft_clause_rows"])
    out["draft_sheet"] = {"present": True, "path": str(sheet), "rows": shown, "bound": bound,
                          "note": "Working draft sheet from the packet folder (state, ending and reason as last written by whoever filled it). It is a prior draft, not evidence."}
    return out


def _shrink_strings(value, limit):
    if isinstance(value, str): return _cap_text(value, limit)
    if isinstance(value, list): return [_shrink_strings(v, limit) for v in value]
    if isinstance(value, dict): return {k: _shrink_strings(v, limit) for k, v in value.items()}
    return value


def _claim_records(repo, iids):
    """One ordered scan, preserving the single-order filename/physical-line rule."""
    found = {}
    selected = set(iids)
    needles = tuple(json.dumps(iid) for iid in selected)
    folder = Path(repo) / "research/readiness/claims"
    for path in sorted(folder.glob("*.jsonl")) if folder.is_dir() else []:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not any(needle in line for needle in needles): continue
            try: claim = json.loads(line)
            except ValueError: continue
            if isinstance(claim, dict) and isinstance(claim.get("instrument_id"), str) and claim["instrument_id"] in selected:
                found[claim["instrument_id"]] = (path, n, claim)
    return found


class _ViewContext:
    """Invocation-local shared presentation inputs; never a source-verification cache.

    Source checks still read and hash the actual held file for every order.
    Side sheets and current claims describe a single invocation's snapshot.
    """
    def __init__(self, packet_path, repo, iids):
        self.packet_path = Path(packet_path)
        self.repo = Path(repo).resolve()
        self.packet = read_json(self.packet_path)
        native = self.packet.get("schema") == batch.SCHEMA or bool(re.fullmatch(r"[0-9a-f]{64}", str(self.packet.get("fingerprint", ""))))
        if native:
            if self.packet.get("schema") != batch.SCHEMA:
                raise ValueError("changed work package: native schema missing")
            # Native frozen-envelope integrity, without pretending that a slim
            # source view has rerun every current preparation/review gate.
            unsigned = {k: v for k, v in self.packet.items() if k != "fingerprint"}
            if (self.packet.get("fingerprint") != batch.canonical_sha(unsigned)
                    or any(not isinstance(self.packet.get(k), dict) for k in
                           ("dossiers", "sources", "text_blocks", "shared_objects", "held_text_file_pins"))):
                raise ValueError("changed work package")
        self.dossiers = batch.decode(self.packet)
        for iid in iids:
            if iid not in self.dossiers: raise KeyError(f"{iid} is not in packet")
        if self.packet.get("reviewed_histories") is not None:
            from history_context import verify
            from assemble import CUTOFF
            if self.packet.get("legal_cutoff") != CUTOFF:
                raise ValueError("reviewed history cutoff differs from project cutoff")
            verify(self.repo, list(self.dossiers), self.packet["reviewed_histories"], CUTOFF)
        self.claims = _claim_records(self.repo, iids)
        self.packet_bytes = self.packet_path.stat().st_size
        self.jsons, self.sheets, self.memos = {}, {}, {}
        self.body_cache = {}  # SC._verified always rehashes, even on cache hits.

    def json(self, path):
        if path not in self.jsons: self.jsons[path] = read_json(path)
        return self.jsons[path]

    def clause_rows(self, path, iid):
        if path not in self.sheets:
            rows = defaultdict(list)
            with path.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f): rows[row.get("instrument_id")].append(row)
            self.sheets[path] = rows
        return self.sheets[path].get(iid, [])

    def memo(self, path):
        if path not in self.memos:
            raw = path.read_bytes()
            self.memos[path] = (_markdown_sections(raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")), hashlib.sha256(raw).hexdigest())
        return self.memos[path]


def _canonical_claim_view(iid, repo, full_claim=False, claims=None):
    """Latest claim for the order across research/readiness/claims, resolved as batch.owners does (last file, last line)."""
    found = (claims if claims is not None else _claim_records(repo, [iid])).get(iid)
    if found is None:
        return {"found": False, "note": "No filed claim for this order under research/readiness/claims."}
    path, n, claim = found
    full_bytes = len(json.dumps(claim, ensure_ascii=False).encode("utf-8"))
    shrunk = not full_claim and full_bytes > VIEW_CAPS["claim_bytes"]
    return {"found": True, "path": path.relative_to(Path(repo)).as_posix(), "line": n, "owner": path.stem,
            "claim_sha256": batch.canonical_sha(claim), "claim_full_bytes": full_bytes,
            "claim_strings_truncated": shrunk,
            "claim": _shrink_strings(claim, VIEW_CAPS["claim_string_chars"]) if shrunk else claim,
            "status": "prior draft",
            "note": "The current filed claim for this order, shown as a prior draft. It is not evidence; re-derive each point from the sources."
                    + (f" Strings longer than {VIEW_CAPS['claim_string_chars']} characters are cut because the whole claim is {full_bytes} bytes; read the line at path/line, or rerun with --full-claim, for the complete text." if shrunk else "")}


def view_summary(compact):
    """Short stdout summary used with --write, so the full view is not printed twice."""
    counts = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in compact.items()
              if k in ("clauses", "source_catalogue", "lookup_leads", "bounded_name_search")}
    return {"instrument_id": compact.get("instrument_id"), "written_to": compact.get("written_to"),
            "view_bytes": compact.get("view_bytes"), "approx_view_tokens": compact.get("approx_view_tokens"),
            "approx_full_packet_tokens": compact.get("approx_full_packet_tokens"),
            "own_text_boundary": compact.get("own_text_boundary"),
            "machine_searches": (compact.get("machine_searches") or {}).get("bound"),
            "later_event_chain": ((compact.get("later_events_chain") or {}).get("chain") or {}).get("bound"),
            "citable_evidence": ((compact.get("later_events_chain") or {}).get("citable_evidence") or {}).get("bound"),
            "clause_inventory": (compact.get("clause_inventory") or {}).get("bound"),
            "current_canonical_claim": {k: (compact.get("current_canonical_claim") or {}).get(k) for k in ("found", "path", "line")},
            "section_counts": counts}


def view(packet_path: Path, eo: str, write: Path | None = None, repo: Path | None = None, full_claim: bool = False):
    iid = eo if eo.startswith("EO:") else "EO:" + eo
    context = _ViewContext(packet_path, repo or REPO, [iid])
    return _view_one(context, iid, write, full_claim)


def view_many(packet_path: Path, eos, write_dir: Path | None = None, repo: Path | None = None, full_claim: bool = False):
    """Render exact ordinary views with shared setup, in the requested order.

    No cross-invocation state, model-facing deduplication or additional caps.
    Validate all members and filenames before creating any output.
    """
    iids = [eo if eo.startswith("EO:") else "EO:" + eo for eo in eos]
    if not iids: raise ValueError("at least one order is required")
    if len(set(iids)) != len(iids): raise ValueError("duplicate order in view request")
    destinations = [None] * len(iids)
    if write_dir is not None:
        # Match build.filename for ordinary EO identifiers; reject path syntax.
        if any(not re.fullmatch(r"EO:[0-9]+[A-Za-z0-9_-]*", iid) for iid in iids):
            raise ValueError("unsafe order identifier for view filename")
        destinations = [Path(write_dir) / (iid.replace(":", "_") + ".view.json") for iid in iids]
        if any(destination.exists() or destination.is_symlink() for destination in destinations):
            raise ValueError("view destination exists; refusing overwrite")
    context = _ViewContext(packet_path, repo or REPO, iids)
    return [_view_one(context, iid, destination, full_claim) for iid, destination in zip(iids, destinations)]


def _view_one(context, iid, write, full_claim):
    packet_path, repo = context.packet_path, context.repo
    packet, dossier = context.packet, context.dossiers[iid]
    keep = {"instrument_id", "title", "signing_date", "whole_order_status", "original_source_id", "clauses", "missing", "fingerprint"}
    compact = {k: dossier[k] for k in keep if k in dossier}
    evidence = dossier.get("evidence", {})
    compact["source_catalogue"] = {k: v.get("source", {}) for k, v in evidence.items() if isinstance(v, dict) and isinstance(v.get("source"), dict)}
    original_meta = evidence.get(dossier.get("original_source_id"), {}).get("source", {})
    compact["target_source_metadata"] = {k: original_meta.get(k) for k in ("instrument_id", "page_or_item", "signing_date", "filing_date", "grade", "url") if k in original_meta}
    original = evidence.get(dossier.get("original_source_id"), {})
    body, body_source, body_gap = SC._own_body({"instrument_id": iid, "claim_kit": {}}, dossier, repo, context.body_cache)
    if body is None:
        compact["own_original_text"], partial_scope = bounded_own_text(dossier)
        compact["own_text_boundary"] = {"verified_whole_order": False, "scope": partial_scope, "coverage_gap": body_gap}
    else:
        compact["own_original_text"] = body
        compact["own_text_boundary"] = {"verified_whole_order": True, "source": body_source}
    compact["mechanical_shared_tasks"] = [t for t in packet.get("shared_tasks", []) if iid in t.get("affected_orders", [])]
    compact["prior_research_for_order"] = packet.get("prior_research", {}).get("orders", {}).get(iid, {})
    verified_texts, missing_texts, bad_texts = instrument_texts(dossier, repo)
    compact["source_file_verification"] = {"text_sources_checked": len(verified_texts),
        "unavailable": missing_texts, "integrity_failures": bad_texts,
        "embedded_packet_text_used": True}
    packet_dir = Path(packet_path).resolve().parent
    lookup_path = packet_dir / "LOOKUPS.json"
    if not lookup_path.is_file(): lookup_path = packet_dir.parent / "LOOKUPS.json"
    if lookup_path.is_file():
        lookup = context.json(lookup_path)
        compact["lookup_leads"] = lookup.get("members", {}).get(iid, {})
    details_path = packet_dir / "LOOKUPS.details.json"
    if not details_path.is_file(): details_path = packet_dir.parent / "LOOKUPS.details.json"
    if details_path.is_file():
        details = context.json(details_path)
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
        memo = repo / "research/excavator/claude-nira-sweep-2026-10-29/SHARED_ANALYSIS.md"
        if memo.is_file():
            sections, memo_sha = context.memo(memo)
            selected = ["Conclusion", "Events that do not end a code approval", "What each order still needs"]
            title = str(dossier.get("title", ""))
            if re.search(r"\b(?:denial|denies|dismiss|exemption)\b", title, re.I):
                selected.append("Denials of exemption and other one-time determinations")
            compact["shared_analysis_memo"] = {"path": str(memo.relative_to(repo)), "sha256": memo_sha,
                "sections": {h: sections[h] for h in selected if h in sections},
                "scope_note": "Batch-level shared context. It makes no order-specific determination; read this order's own text and sources."}
        else:
            compact["shared_analysis_memo"] = {"missing": "SHARED_ANALYSIS.md not available", "coverage_gap": True}
    compact["machine_searches"] = _machine_searches_view(dossier)
    compact["later_events_chain"] = _later_events_view(dossier)
    compact["clause_inventory"] = _clause_inventory_view(dossier, iid, packet_path, context)
    compact["current_canonical_claim"] = _canonical_claim_view(iid, repo, full_claim, context.claims)
    if packet.get("reviewed_histories") is not None:
        from history_context import for_order
        compact["reviewed_histories"] = for_order(packet["reviewed_histories"], iid)
    if dossier.get("factual_interval_ids") or any(isinstance(e, dict) and e.get("role") == "reviewed_occurrence_interval" for e in evidence.values()):
        import factual_events as F
        compact["reviewed_occurrence_intervals"] = {
            "records": {eid: e for eid, e in evidence.items() if isinstance(e, dict) and e.get("role") == "reviewed_occurrence_interval"},
            "observations": F.observations_at(dossier, packet.get("legal_cutoff", F.MODEL.CUTOFF), repo=repo),
            "notice": "Reviewed factual occurrence intervals only; no text-version, legal-effect or whole-order approval. Event dates and legal endings remain separate."}
    compact["view_caps"] = dict(VIEW_CAPS)
    compact["packet_fingerprint"] = packet.get("fingerprint")
    compact_bytes = len(json.dumps(compact, ensure_ascii=False).encode("utf-8"))
    packet_bytes = context.packet_bytes
    compact["view_bytes"] = compact_bytes
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
        track = _track_of(row)
        key = (track, row.get("role", ""), row.get("model", ""))
        g = groups.setdefault(key, {"rows": 0, "sums": defaultdict(Decimal), "reported": Counter(), "errors": []})
        g["rows"] += 1
        for col in columns:
            raw = row.get(col)
            if raw is None or not str(raw).strip(): continue
            try:
                value = Decimal(str(raw).strip())
                if not value.is_finite() or value < 0: raise InvalidOperation
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
                value = Decimal(str(v))
                if isinstance(v, bool) or not value.is_finite() or value < 0 or value != value.to_integral_value(): raise ValueError
                filed[str(k)] = int(value)
            except (TypeError, ValueError, InvalidOperation): errors.append({"filed_manifest": str(k), "value": v, "reason": "invalid_denominator"})
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


UNKNOWN = "unknown"
COMPARE_SCHEMA = "geddes-cost-compare/v1"
# tokens_total_input is derived (input + cache creation + cache read) when the CSV lacks that column.
COMPARE_METRICS = ("tokens_total_input", "cache_read_input_tokens", "output_tokens", "active_seconds")
COMPARE_LABELS = {"tokens_total_input": "input tokens (total)", "cache_read_input_tokens": "cache-read tokens",
                  "output_tokens": "output tokens", "active_seconds": "active seconds"}


def _track_of(row):
    batch_id = (row.get("batch") or "").lower()
    return row.get("track") or ("NRA" if batch_id.startswith("n") else "General" if batch_id.startswith("g") else "unknown")


def _clean_number(raw, integer):
    """Return a non-negative Decimal, None when blank, or raise InvalidOperation."""
    if raw is None or not str(raw).strip(): return None
    value = Decimal(str(raw).strip())
    if not value.is_finite() or value < 0: raise InvalidOperation
    if integer and value != value.to_integral_value(): raise InvalidOperation
    return value


def _row_metrics(row):
    """Per-row values for the compared metrics; None means unknown, never zero."""
    out = {}
    for col in ("tokens_total_input", "cache_read_input_tokens", "output_tokens", "active_seconds",
                "input_tokens", "cache_creation_input_tokens"):
        try: out[col] = _clean_number(row.get(col), col != "active_seconds")
        except InvalidOperation: out[col] = None
    if out["tokens_total_input"] is None:
        parts = [out["input_tokens"], out["cache_creation_input_tokens"], out["cache_read_input_tokens"]]
        out["tokens_total_input"] = None if any(v is None for v in parts) else sum(parts)
    return out


def _run_totals(path):
    """Sum compared metrics per (track, role); a metric is unknown if any agent row lacks it."""
    with Path(path).open(encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f))
    groups = {}
    for row in rows:
        g = groups.setdefault((_track_of(row), row.get("role", "")), {"agents": 0, "sums": {m: Decimal(0) for m in COMPARE_METRICS}, "missing": Counter()})
        g["agents"] += 1
        values = _row_metrics(row)
        for m in COMPARE_METRICS:
            if values[m] is None: g["missing"][m] += 1
            else: g["sums"][m] += values[m]
    return groups


def _load_filed(path):
    """Read a filed-claims JSON map such as {"filed_claims": {"NRA": 127}} into track -> int."""
    filed, errors = {}, []
    if not path: return filed, errors
    manifest = read_json(path)
    if not isinstance(manifest, dict): raise ValueError(f"{path}: filed-claims JSON must be an object")
    for k, v in manifest.get("filed_claims", manifest).items():
        try:
            value = Decimal(str(v))
            if isinstance(v, bool) or not value.is_finite() or value < 0 or value != value.to_integral_value(): raise ValueError
            filed[str(k)] = int(value)
        except (TypeError, ValueError, InvalidOperation): errors.append({"filed_manifest": str(k), "value": v, "reason": "invalid_denominator"})
    return filed, errors


def _num(value):
    return int(value) if value == value.to_integral_value() else float(value)


def _per_claim(group, metric, denominator):
    """Return (value, reason); value is UNKNOWN when any input to it is missing."""
    if group is None: return UNKNOWN, "track/role absent from this run"
    if group["missing"][metric]: return UNKNOWN, f"{group['missing'][metric]} of {group['agents']} agent rows lack {metric}"
    if not denominator: return UNKNOWN, "no filed-claim count for this track"
    return round(float(group["sums"][metric]) / denominator, 2), None


def cost_compare(baseline: Path, new: Path, filed_baseline: Path | None = None, filed_new: Path | None = None):
    base_groups, new_groups = _run_totals(baseline), _run_totals(new)
    base_filed, e1 = _load_filed(filed_baseline)
    new_filed, e2 = _load_filed(filed_new)
    rows, verdicts = [], []
    for track, role in sorted(set(base_groups) | set(new_groups)):
        bg, ng = base_groups.get((track, role)), new_groups.get((track, role))
        entry = {"track": track, "role": role, "agents": {"baseline": bg["agents"] if bg else UNKNOWN, "new": ng["agents"] if ng else UNKNOWN},
                 "filed_claims": {"baseline": base_filed.get(track, UNKNOWN), "new": new_filed.get(track, UNKNOWN)}, "metrics": {}}
        for metric in COMPARE_METRICS:
            b, why_b = _per_claim(bg, metric, base_filed.get(track))
            n, why_n = _per_claim(ng, metric, new_filed.get(track))
            m = {"baseline_total": _num(bg["sums"][metric]) if bg and not bg["missing"][metric] else UNKNOWN,
                 "new_total": _num(ng["sums"][metric]) if ng and not ng["missing"][metric] else UNKNOWN,
                 "baseline_per_filed_claim": b, "new_per_filed_claim": n}
            reasons = [f"baseline: {why_b}" if why_b else None, f"new: {why_n}" if why_n else None]
            if UNKNOWN in (b, n): ratio = UNKNOWN
            elif b == 0: ratio, reasons = UNKNOWN, reasons + ["baseline value is zero, so the ratio is undefined"]
            else: ratio = round(n / b, 4)
            m["ratio_new_over_baseline"] = ratio
            m["unknown_because"] = [r for r in reasons if r] if ratio == UNKNOWN else []
            entry["metrics"][metric] = m
        label, cache = f"{track}/{role}", entry["metrics"]["cache_read_input_tokens"]
        r = cache["ratio_new_over_baseline"]
        if r == UNKNOWN:
            line = f"cache-read tokens per filed claim for {label}: unknown ({'; '.join(cache['unknown_because'])})"
        else:
            pct = round(abs(1 - r) * 100, 1)
            line = (f"new run used the same number of cache-read tokens per filed claim for {label}" if pct == 0 else
                    f"new run used {pct:g}% {'fewer' if r < 1 else 'more'} cache-read tokens per filed claim for {label}")
        entry["verdict"] = line
        verdicts.append(line)
        rows.append(entry)
    return {"schema": COMPARE_SCHEMA, "baseline": {"source": str(baseline), "filed_claims": base_filed},
            "new": {"source": str(new), "filed_claims": new_filed}, "rows": rows, "verdicts": verdicts,
            "errors": e1 + e2,
            "note": "Per filed claim = track/role total divided by that track's filed-claim count. Ratio = new / baseline. "
                    "'unknown' means an input was missing; it is never treated as zero. Active seconds retain fractions."}


RESOLUTIONS_SCHEMA = "geddes-resolutions/v1"
RESOLUTIONS_NAME = "GEDDES_RESOLUTIONS.json"
RESPONSES = ("fixed_in_new_version", "disputed", "order_blocked")


def load_resolutions(path: Path, required: bool = False):
    """Return the parsed resolutions document, or None when an optional file is absent."""
    path = Path(path)
    if not path.is_file():
        if required: raise FileNotFoundError(f"resolutions file not found: {path}")
        return None
    doc = read_json(path)
    if not isinstance(doc, dict) or doc.get("schema") != RESOLUTIONS_SCHEMA or not isinstance(doc.get("resolutions"), list):
        raise ValueError(f"{path}: expected an object with schema {RESOLUTIONS_SCHEMA!r} and a resolutions list")
    return doc


def gate_check(lint_result, resolutions_doc):
    """Pure gate: passes only when every current flag has a valid resolution with a non-empty note."""
    stamp_flag_ids(lint_result.get("results", []))
    valid, invalid = {}, []
    for i, entry in enumerate((resolutions_doc or {}).get("resolutions", [])):
        problems = []
        if not isinstance(entry, dict): invalid.append({"index": i, "reason": "entry_not_an_object"}); continue
        if not isinstance(entry.get("flag_id"), str) or not entry["flag_id"].strip(): problems.append("flag_id_missing")
        if entry.get("response") not in RESPONSES: problems.append(f"response_not_one_of_{'|'.join(RESPONSES)}")
        if not isinstance(entry.get("note"), str) or not entry["note"].strip(): problems.append("note_empty")
        if problems: invalid.append({"index": i, "flag_id": entry.get("flag_id"), "reason": ",".join(problems)}); continue
        valid.setdefault(entry["flag_id"], []).append(entry)
    resolved, unresolved, current = [], [], set()
    for row in lint_result.get("results", []):
        for flag in row.get("flags", []):
            fid = flag.get("flag_id"); current.add(fid)
            matches = [e for e in valid.get(fid, []) if e.get("instrument_id") in (None, row.get("instrument_id"))]
            if matches:
                resolved.append({"flag_id": fid, "instrument_id": row.get("instrument_id"), "response": matches[0]["response"]})
                continue
            item = {"flag_id": fid, "instrument_id": row.get("instrument_id"), "line": row.get("line"), "code": flag.get("code"),
                    "scope_id": flag.get("scope_id"), "detail": flag.get("detail")}
            if fid in valid: item["reason"] = "resolution_instrument_id_does_not_match"
            else: item["reason"] = "no_valid_resolution"
            unresolved.append(item)
    return {"schema": "geddes-gate/v1", "passed": not unresolved, "flags": len(resolved) + len(unresolved),
            "resolved": len(resolved), "unresolved_count": len(unresolved), "unresolved": unresolved,
            "resolved_flags": resolved, "invalid_resolutions": invalid,
            "stale_resolutions": sorted(set(valid) - current),
            "note": "Coverage gaps are reported by lint and are not gated here. A gate pass shows only that every flag has a documented response; it is not a legal or review conclusion."}


def gate(applied: Path, resolutions: Path | None = None, repo=REPO):
    """Re-lint the applied directory so the flags are current, then apply the resolutions file."""
    applied = Path(applied)
    path = Path(resolutions) if resolutions else applied / RESOLUTIONS_NAME
    doc = load_resolutions(path, required=resolutions is not None)
    result = gate_check(lint(applied, repo), doc)
    result["resolutions_path"] = str(path) if doc is not None else None
    return result


def lint_for_kit(applied: Path, repo=REPO, strict: bool = False):
    """Lint for claim-kit batch-check: write GEDDES_LINT.json and return the compact summary."""
    started = time.monotonic()
    applied = Path(applied).resolve()
    result = lint(applied, repo)
    (applied / "GEDDES_LINT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    flagged = []
    for row in result["results"]:
        if row["flags"] and row["instrument_id"] not in flagged: flagged.append(row["instrument_id"])
    summary = {"flags": result["defect_flags"], "flagged_claims": flagged, "coverage_gaps": result["coverage_gaps"],
               "path": "GEDDES_LINT.json", "seconds": 0}
    if strict:
        try:
            outcome = gate_check(result, load_resolutions(applied / RESOLUTIONS_NAME))
            summary["gate"] = {"passed": outcome["passed"], "unresolved": [u["flag_id"] for u in outcome["unresolved"]],
                               "resolutions_path": RESOLUTIONS_NAME}
        except (OSError, ValueError) as exc:
            summary["gate"] = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
    summary["seconds"] = round(time.monotonic() - started, 3)
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("lint"); x.add_argument("applied", type=Path); x.add_argument("--repo", type=Path, default=REPO)
    x = sub.add_parser("gate", help="exit 0 only when every current lint flag has a resolution with a note")
    x.add_argument("applied", type=Path); x.add_argument("--resolutions", type=Path); x.add_argument("--repo", type=Path, default=REPO)
    x = sub.add_parser("view"); x.add_argument("packet", type=Path); x.add_argument("eo"); x.add_argument("--write", type=Path); x.add_argument("--repo", type=Path, default=REPO)
    x.add_argument("--full-claim", action="store_true", help="include the current filed claim without shortening long strings")
    x = sub.add_parser("views", help="render several ordinary order views with one shared setup")
    x.add_argument("packet", type=Path); x.add_argument("eos", nargs="+")
    x.add_argument("--write-dir", type=Path); x.add_argument("--repo", type=Path, default=REPO)
    x.add_argument("--full-claim", action="store_true")
    x = sub.add_parser("cost", help="summarize one telemetry CSV, or compare it (as NEW) against --compare BASELINE")
    x.add_argument("telemetry", type=Path, metavar="TELEMETRY_OR_NEW.csv"); x.add_argument("--filed-manifest", type=Path)
    x.add_argument("--compare", type=Path, metavar="BASELINE.csv"); x.add_argument("--filed-baseline", type=Path); x.add_argument("--filed-new", type=Path)
    a = p.parse_args(argv)
    if a.cmd == "cost" and not a.compare and (a.filed_baseline or a.filed_new):
        p.error("--filed-baseline and --filed-new require --compare")
    try:
        code = 0
        if a.cmd == "lint": result = lint(a.applied, a.repo)
        elif a.cmd == "gate":
            result = gate(a.applied, a.resolutions, a.repo)
            if not result["passed"]:
                code = 1
                for u in result["unresolved"]:
                    print(f"UNRESOLVED {u['flag_id']} {u['instrument_id']} {u['code']}: {u['detail']}", file=sys.stderr)
        elif a.cmd == "view": result = view(a.packet, a.eo, a.write, a.repo, a.full_claim)
        elif a.cmd == "views": result = view_many(a.packet, a.eos, a.write_dir, a.repo, a.full_claim)
        elif a.compare: result = cost_compare(a.compare, a.telemetry, a.filed_baseline, a.filed_new)
        else: result = cost(a.telemetry, a.filed_manifest)
        printed = view_summary(result) if a.cmd == "view" and a.write else result
        if a.cmd == "views" and a.write_dir: printed = [view_summary(v) for v in result]
        print(json.dumps(printed, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2

if __name__ == "__main__": raise SystemExit(main())
