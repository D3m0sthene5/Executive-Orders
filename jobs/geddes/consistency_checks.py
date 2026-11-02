"""Internal-consistency checks between a claim's reasoning and its own sources.

Each rule compares words or dates the reasoning attributes to the order, to a
cited row, or to the claim's own end against the claim's structured fields or
the hash-verified held text.  Nothing here reads review outcomes or contains
order-specific rules.  A missing or unverified source yields a coverage gap.
"""
from __future__ import annotations

import base64
import hashlib
import re
from datetime import datetime
from pathlib import Path

import citation_checks as CC
import source_checks as SC

MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
ISO = r"\d{4}-\d{2}-\d{2}"
CONDITIONAL = re.compile(r"\b(?:if|unless|instead|alternative(?:ly)?|would|could|might|whether|reviewer|reading\s+as|were\s+read)\b", re.I)

# "an order whose end is shown in 1986 or earlier"
END_BOUND = re.compile(r"\b(?:end|ending|first\s+end|termination)\s+(?:is\s+|was\s+)?(?:shown\s+|dated\s+|recorded\s+|claimed\s+)?"
                       r"(?:in\s+|as\s+|at\s+)?(\d{4})\s+or\s+(earlier|before|later|after)\b", re.I)
# "the first end is 1935-06-14", "ended on 1958-08-05"
STATED_END = re.compile(r"\b(?:the\s+)?first\s+end\s+(?:is|was|date\s+is|falls\s+on)\s+(" + ISO + r")\b|\bended\s+on\s+(" + ISO + r")\b", re.I)
STATED_WHOLE_END = re.compile(r"\bwhole[- ]order\s+end\s+(?:is|was|date\s+is)\s+(" + ISO + r")\b", re.I)

# Descriptions attributed to a held table row or to the order itself.
ROW_DESC = re.compile(r"\b(?:row|subject\s+line|table\s+entry)\s+(?:describes|reads|says|gives)\s+(?:it\s+as\s+)?['\"“‘]?(?P<desc>[^.;\"”’]{8,220})", re.I)
ORDER_DESC = re.compile(r"\b(?:the|this)\s+order\s+(?:concerns|recites|covers|addresses|involves|is\s+about)\s+['\"“‘]?(?P<desc>[^.;\"”’]{8,220})", re.I)
COUNT_NOUNS = {"dispute": "disputes", "strike": "strikes", "controversy": "controversies"}
ENTITY = {
    "airline": (re.compile(r"\b(?:air\s*lines?|airlines?|air\s+carriers?)\b", re.I),
                re.compile(r"\bair\s*lines?\b|\bairlines?\b|\bair\s+(?:carrier|transport|craft)|\baviation\b|\bairways\b|\baeronautic", re.I)),
    "railroad": (re.compile(r"\brail(?:road|way)s?\b", re.I),
                 re.compile(r"\brail(?:road|way)s?\b(?!\s+labor\s+act)|\brail\s+road", re.I)),
}
STATUTE_ATTRIBUTION = re.compile(r"(?P<cites>(?:\b\d{1,2}\s+U\.?\s?S\.?\s?C\.?\s+)?\d{3,5}(?:\s*\([a-z0-9]{1,3}\))*(?:\s*(?:,|and|or)\s*(?:\b\d{1,2}\s+U\.?\s?S\.?\s?C\.?\s+)?\d{3,5}(?:\s*\([a-z0-9]{1,3}\))*)*)\s*,?\s+(?:which|that)\s+the\s+order\s+cites\b", re.I)
SECTION = re.compile(r"(?<![\d.])(?:\d{1,2}\s+U\.?\s?S\.?\s?C\.?\s+)?(\d{3,5})((?:\s*\([a-z0-9]{1,3}\))*)", re.I)


def _flag(code, scope, field, span, detail, source=None):
    row = {"code": code, "scope_id": scope, "field": field, "span": span, "detail": detail}
    if source:
        row["source"] = source
    return row


def _parts(claim):
    """Reasoning parts plus search-scope text, which also make assertions."""
    yield from CC._reason_parts(claim)
    for i, search in enumerate(claim.get("later_source_search") or []):
        if isinstance(search, dict):
            for key in ("query_or_scope", "repository"):
                if isinstance(search.get(key), str):
                    yield f"claim.later_source_search[{i}].{key}", search[key]


def _sentence(text, start, end):
    a = max(text.rfind(". ", 0, start), text.rfind("; ", 0, start), text.rfind("\n", 0, start)) + 1
    tail = re.search(r"(?<!\bNo)(?<!\bSec)(?<!\bU\.S)\.\s|;\s|\n", text[end:])
    return text[a:end + (tail.start() + 1 if tail else len(text) - end)].strip()


def _verified_claim_source(source, dossier, repo):
    """Return (text, provenance) for a claim source whose pin matches the dossier record."""
    if not isinstance(source, dict):
        return None, None, "source_missing"
    ident = source.get("evidence_id")
    if source.get("evidence_id_encoding") == "base64url-utf8" and isinstance(ident, str):
        try:
            ident = base64.urlsafe_b64decode(ident + "=" * (-len(ident) % 4)).decode("utf-8")
        except (ValueError, UnicodeError):
            return None, None, "evidence_id_undecodable"
    record = SC._records(dossier).get(ident)
    expected = (record.get("actor_source") or record.get("source")) if isinstance(record, dict) else None
    if not isinstance(expected, dict) or expected.get("text_sha256") != source.get("text_sha256") or expected.get("text_path") != source.get("text_path"):
        return None, None, "claim_source_not_bound_to_dossier_record"
    path = (Path(repo).resolve() / str(source.get("text_path"))).resolve()
    if not path.is_relative_to(Path(repo).resolve()) or not path.is_file():
        return None, None, "source_file_unavailable"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source.get("text_sha256"):
        return None, None, "source_hash_mismatch"
    return raw.decode("utf-8", errors="replace"), {"text_path": source["text_path"], "text_sha256": source["text_sha256"], "source_id": ident}, None


def _end_dates(claim):
    whole = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else None
    dates = [c["first_end"]["date"] for c in claim.get("operative_clauses") or []
             if isinstance(c, dict) and isinstance(c.get("first_end"), dict) and isinstance(c["first_end"].get("date"), str)]
    return (whole or {}).get("date") if whole else (max(dates) if dates else None), whole


def _date_checks(claim, dossier):
    flags = []
    end, whole = _end_dates(claim)
    end_source = (whole or {}).get("source") if isinstance((whole or {}).get("source"), dict) else None
    if end and re.match(ISO, end):
        year = int(end[:4])
        for field, text in _parts(claim):
            for m in END_BOUND.finditer(text):
                bound, side = int(m[1]), m[2].lower()
                if (side in ("earlier", "before") and year > bound) or (side in ("later", "after") and year < bound):
                    src = {k: end_source.get(k) for k in ("text_path", "text_sha256", "char_start", "char_end", "quote") if end_source.get(k) is not None} if end_source else None
                    flags.append(_flag("stated_end_bound_contradicts_claimed_end", "whole", field, _sentence(text, m.start(), m.end()),
                                       f"Reasoning bounds the end at {bound} or {side}; the claim's own end is {end}.", src))
    for i, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict):
            continue
        scope = clause.get("scope_id") or f"clause[{i}]"
        first = clause.get("first_end") if isinstance(clause.get("first_end"), dict) else {}
        text = str(clause.get("judgment_reason") or "")
        for m in STATED_END.finditer(text):
            stated = m[1] or m[2]
            sentence = _sentence(text, m.start(), m.end())
            if first.get("date") and stated != first["date"] and not CONDITIONAL.search(sentence):
                flags.append(_flag("stated_end_date_mismatch", scope, f"operative_clauses[{i}].judgment_reason", sentence,
                                   f"Reasoning states the end as {stated}; this clause's first_end.date is {first['date']}."))
    if whole and whole.get("date"):
        for field, text in _parts(claim):
            for m in STATED_WHOLE_END.finditer(text):
                sentence = _sentence(text, m.start(), m.end())
                if m[1] != whole["date"] and not CONDITIONAL.search(sentence):
                    flags.append(_flag("stated_end_date_mismatch", "whole", field, sentence,
                                       f"Reasoning states the whole-order end as {m[1]}; whole_order_end.date is {whole['date']}."))
    signed = dossier.get("signing_date")
    if not signed:
        record = (dossier.get("evidence") or {}).get(dossier.get("original_source_id")) or {}
        signed = (record.get("source") or {}).get("signing_date") if isinstance(record, dict) else None
    if isinstance(signed, str) and re.fullmatch(ISO, signed):
        for i, clause in enumerate(claim.get("operative_clauses") or []):
            if not isinstance(clause, dict):
                continue
            scope = clause.get("scope_id") or f"clause[{i}]"
            events = [("first_end", clause.get("first_end"))] + [(f"later_events[{j}]", e) for j, e in enumerate(clause.get("later_events") or [])]
            for name, event in events:
                date = event.get("date") if isinstance(event, dict) else None
                if isinstance(date, str) and re.fullmatch(ISO, date) and date < signed:
                    flags.append(_flag("event_precedes_order", scope, f"operative_clauses[{i}].{name}.date", date,
                                       f"The recorded date {date} precedes the order's own date {signed}."))
        own = str(claim.get("instrument_id") or "").removeprefix("EO:")
        own_ref = re.compile(r"\b(?:Executive\s+Order|EO)\s*(?:No\.?\s*)?" + re.escape(own[:-1] + ("-?" + own[-1] if own[-1:].isalpha() else own[-1])) + r"(?![\w-])", re.I)
        for field, text in CC._reason_parts(claim):
            for m in own_ref.finditer(text):
                tail = re.match(r",?\s+(?:of|dated|signed(?:\s+on)?|issued(?:\s+on)?)\s+(" + MONTH + "|" + ISO + r")", text[m.end():m.end() + 60], re.I)
                if not tail:
                    continue
                try:
                    stated = tail[1] if re.fullmatch(ISO, tail[1]) else datetime.strptime(re.sub(r"\s+", " ", tail[1]).title(), "%B %d, %Y").date().isoformat()
                except ValueError:
                    continue
                if stated < signed:
                    flags.append(_flag("own_order_date_precedes_signing", "whole", field, text[m.start():m.end() + tail.end()],
                                       f"Reasoning dates this order {stated}; the pinned dossier signing date is {signed}."))
    return flags


def _row_text(text, number):
    """Return a numbered table row and its continuation lines, or None."""
    digits = re.match(r"\d+", number).group()
    suffix = number[len(digits):]
    pat = re.compile(r"(?m)^[ \t]*" + r"[ ]?".join(digits) + (r"[ \t]*-?[ \t]*" + suffix if suffix else r"(?![\d])(?![ \t]*-?[ \t]*[A-Z]\b)") + r"\b[^\n]*")
    hits = list(pat.finditer(text))
    if len(hits) != 1:
        return None, None
    m = hits[0]
    end = m.end()
    for line in re.finditer(r"\n([^\n]*)", text[m.end():m.end() + 600]):
        if re.match(r"[ \t]*\d{3,5}\b", line[1]) or not line[1].strip():
            break
        end = m.end() + line.end()
    return text[m.start():end], (m.start(), end)


def _words_disagree(desc, target):
    """Return a list of count/entity words in desc that the target text contradicts."""
    problems = []
    d, t = desc.casefold(), target.casefold()
    for noun, plural in COUNT_NOUNS.items():
        sing_d = re.search(rf"\b{noun}\b", d)
        plur_d = re.search(rf"\b{plural}\b", d)
        sing_t = re.search(rf"\b{noun}\b", t)
        plur_t = re.search(rf"\b{plural}\b", t)
        if sing_d and not plur_d and plur_t and not sing_t:
            problems.append(f"singular '{noun}' where the source has only '{plural}'")
        if plur_d and not sing_d and sing_t and not plur_t:
            problems.append(f"plural '{plural}' where the source has only '{noun}'")
    for label, (asserted, present) in ENTITY.items():
        if asserted.search(desc) and not present.search(target):
            problems.append(f"'{label}' is not in the source")
    return problems


def _description_checks(claim, dossier, repo, cache):
    flags, gaps = [], []
    own = str(claim.get("instrument_id") or "").removeprefix("EO:")
    body, provenance, body_gap = SC._own_body(claim, dossier, Path(repo).resolve(), cache)
    sources = {}
    for clause in claim.get("operative_clauses") or []:
        for event in ([clause.get("first_end")] if isinstance(clause, dict) else []):
            if isinstance(event, dict) and isinstance(event.get("source"), dict) and event.get("actor"):
                sources.setdefault(str(event["actor"]).upper(), event["source"])
    whole = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else {}
    if whole.get("actor") and isinstance(whole.get("source"), dict):
        sources.setdefault(str(whole["actor"]).upper(), whole["source"])
    seen = set()
    for field, text in CC._reason_parts(claim):
        for m in ROW_DESC.finditer(text):
            sentence = _sentence(text, m.start(), m.end())
            named = [re.sub(r"[- ]", "", x).upper() for x in re.findall(r"\b(?:Executive\s+Order|EO)\s*(?:No\.?\s*)?(\d{3,6}(?:-?[A-Z])?)\b", sentence, re.I)]
            named = ["EO:" + x for x in named if x != own.upper()]
            listed = re.search(r"\b(?:lists|row|entry)\s+(?:for\s+)?(\d{3,6}[A-Z]?)\b", sentence)
            if listed and listed[1] != own:
                continue
            candidates = [a for a in named if a in sources] or ([next(iter(sources))] if len(sources) == 1 and not named else [])
            if len(candidates) != 1:
                gaps.append({"code": "row_description_source_unresolved", "field": field, "span": sentence})
                continue
            held, prov, issue = _verified_claim_source(sources[candidates[0]], dossier, repo)
            if issue:
                gaps.append({"code": "row_description_source_unverified", "field": field, "reason": issue})
                continue
            row, span = _row_text(held, own)
            if row is None:
                gaps.append({"code": "row_description_row_not_located", "field": field, "actor": candidates[0]})
                continue
            problems = _words_disagree(m["desc"], row)
            key = (field, tuple(problems))
            if problems and key not in seen:
                seen.add(key)
                flags.append(_flag("attributed_row_wording_mismatch", "whole", field, sentence,
                                   f"Reasoning describes the {candidates[0]} row as '{m['desc'].strip()}'; " + "; ".join(problems) + f". Held row: {re.sub(r'\s+', ' ', row).strip()!r}.",
                                   {**prov, "char_start": span[0], "char_end": span[1], "quote": row}))
        for m in ORDER_DESC.finditer(text):
            sentence = _sentence(text, m.start(), m.end())
            if body is None:
                gaps.append({"code": "order_description_body_unverified", "field": field, "reason": body_gap})
                continue
            problems = _words_disagree(m["desc"], body)
            key = (field, tuple(problems), "order")
            if problems and key not in seen:
                seen.add(key)
                flags.append(_flag("attributed_order_wording_mismatch", "whole", field, sentence,
                                   f"Reasoning describes the order as '{m['desc'].strip()}'; " + "; ".join(problems) + " in the verified order body.",
                                   {k: provenance.get(k) for k in ("text_path", "text_sha256", "char_start", "char_end", "source_id")}))
        for m in STATUTE_ATTRIBUTION.finditer(text):
            if body is None:
                gaps.append({"code": "order_citation_body_unverified", "field": field, "reason": body_gap})
                continue
            compact = re.sub(r"\s+", "", body)
            missing = [s.group(1) + re.sub(r"\s+", "", s.group(2)) for s in SECTION.finditer(m["cites"])
                       if not re.search(r"(?<![\d.])" + s.group(1) + r"(?!\d)", compact)]
            if missing:
                flags.append(_flag("attributed_order_citation_absent", "whole", field, _sentence(text, m.start(), m.end()),
                                   f"Reasoning says the order cites {', '.join(missing)}; that section number is absent from the verified order body.",
                                   {k: provenance.get(k) for k in ("text_path", "text_sha256", "char_start", "char_end", "source_id")}))
    return flags, gaps


ONLY_MIRROR = re.compile(r"\b(?:dossier|packet)\s+holds\s+only\s+(?:an?\s+)?(?:American\s+Presidency\s+Project|APP|mirror)\s+transcription\s+(?:row|record|text)?s?\s*(?:for|of)\s+(?:EO\s*|Executive\s+Order\s+)?(\d{3,6}(?:-?[A-Z])?)\b", re.I)


def _grade_checks(claim, dossier, repo):
    """A claim saying the dossier holds only a transcription for an instrument
    must not contradict a dossier record that pins an official FR printing."""
    flags = []
    for field, text in CC._reason_parts(claim):
        for m in ONLY_MIRROR.finditer(text):
            actor = "EO:" + re.sub(r"[- ]", "", m.group(1)).upper()
            for ident, record in sorted(SC._records(dossier).items()):
                source = record.get("source") if isinstance(record, dict) else None
                if (not isinstance(source, dict) or record.get("actor_id") != actor or source.get("grade") == "mirror_transcription"
                        or not str(source.get("text_path", "")).startswith("jobs/fr-originals/")):
                    continue
                path = (Path(repo).resolve() / source["text_path"]).resolve()
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source.get("text_sha256"):
                    continue
                flags.append(_flag("dossier_source_grade_misdescribed", "whole", field, _sentence(text, m.start(), m.end()),
                                   f"Reasoning says the dossier holds only a transcription for {actor}; dossier record {ident} pins a Federal Register printing ({source.get('page_or_item')}).",
                                   {"text_path": source["text_path"], "text_sha256": source["text_sha256"], "source_id": ident,
                                    "char_start": record.get("char_start"), "char_end": record.get("char_end")}))
                break
    return flags


HEXRUN = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,80}(?![0-9A-Za-z])")
HASH_LABEL = re.compile(r"(?:sha-?256|SHA-256)[\s:=,)(]{0,4}(?:of\s+[^\s]{1,40}\s+)?(?:is\s+)?$", re.I)
PATH_BEFORE = re.compile(r"((?:jobs|research)/[^\s,;()'\"]+?\.(?:txt|json|jsonl|csv|md))\s*[,(]?\s*(?:text\s+)?(?:sha-?256|SHA-256)[\s:=]{0,3}$", re.I)


def _hash_checks(claim, repo):
    """Stated SHA-256 values: 64 lowercase hex characters, and equal to an adjacent held file's hash."""
    flags = []

    def visit(obj, path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and key.lower().endswith("sha256") and value and not re.fullmatch(r"[0-9a-f]{64}", value):
                    flags.append(_flag("stated_sha256_malformed", "whole", f"{path}.{key}", value,
                                       f"{path}.{key} has {len(value)} characters; a SHA-256 is 64 lowercase hex characters."))
                else:
                    visit(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                visit(value, f"{path}[{i}]")
    visit(claim, "claim")
    for field, text in _parts(claim):
        for m in HEXRUN.finditer(text):
            before = text[max(0, m.start() - 300):m.start()]
            if not HASH_LABEL.search(before):
                continue
            value = m.group()
            span = text[max(0, m.start() - 160):m.end()]
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                flags.append(_flag("stated_sha256_malformed", "whole", field, span,
                                   f"A stated SHA-256 has {len(value)} characters{'' if value == value.lower() else ' and uppercase letters'}; a SHA-256 is 64 lowercase hex characters."))
                continue
            near = PATH_BEFORE.search(before)
            if not near:
                continue
            file = (Path(repo).resolve() / near.group(1)).resolve()
            if not file.is_relative_to(Path(repo).resolve()) or not file.is_file():
                continue
            actual = hashlib.sha256(file.read_bytes()).hexdigest()
            if actual != value:
                flags.append(_flag("stated_sha256_mismatch", "whole", field, span,
                                   f"The claim states sha256 {value} for {near.group(1)}; the held file hashes to {actual}.",
                                   {"text_path": near.group(1), "text_sha256": actual}))
    return flags


def _dedupe(flags):
    """One flag per code and detail; the same discrepancy restated in several fields is one finding."""
    out, seen = [], set()
    for flag in flags:
        key = (flag["code"], flag["detail"])
        if key not in seen:
            seen.add(key)
            out.append(flag)
    return out


def check(claim, dossier, repo, packet_path=None, cache=None):
    cache = {} if cache is None else cache
    flags = _date_checks(claim, dossier) + _grade_checks(claim, dossier, repo) + _hash_checks(claim, repo)
    more, gaps = _description_checks(claim, dossier, repo, cache)
    return {"flags": _dedupe(flags + more), "coverage_gaps": gaps}
