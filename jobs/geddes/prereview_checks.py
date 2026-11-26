"""Zero-token pre-review checks for defect classes that blind reviewers rejected.

Each check compares a claim with itself or with its own hash-pinned held text.
Flags are advisory, like every other Geddes flag: a producer resolves each one
as fixed or disputed. No check decides a legal question.

Flag codes:
  count_contradicts_records       prose says no (or N) continuation notices or no
                                  amendment, while later_events record them
  emergency_declaration_unsupported  prose says the order declares a national
                                  emergency, but its held text has no declaring words
  page_label_excludes_span        a cited source's PDF page label does not contain
                                  the page on which its cited character span lies
  date_before_signing             an end or later-event date precedes the signing date
  end_year_conflicts_reasons      the reasons give the structured end's month and day
                                  in a different year, and never the structured date
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

NUMBER_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
NUM = r"(\d{1,2}|" + "|".join(NUMBER_WORDS) + r")"
ADJ = r"(?:(?:held|annual|Federal\s+Register|later|presidential|NEA|separate)\s+)*"
NOTICE_NOUN = r"(?:continuation\s+notices?|notices?\s+(?:of\s+)?continu\w*|notices?\s+continuing)"
NOTICE_ZERO = re.compile(rf"\b(?:0|zero|no)\s+{ADJ}{NOTICE_NOUN}", re.I)
NOTICE_COUNT = re.compile(rf"\b{NUM}\s+{ADJ}{NOTICE_NOUN}", re.I)
ENDING_VERBS = r"(?:revokes?|supersedes?|rescinds?|terminates?|modifies|ends|repeals?|replaces?)"
AMEND_ABSENT = [
    re.compile(rf"\bno\s+(?:held\s+|later\s+|subsequent\s+|other\s+)*(?:instrument|order|executive\s+order|proclamation|text)s?\s+"
               rf"(?:(?:{ENDING_VERBS})\s*,?\s*(?:or\s+|and\s+)?)*amends?\b", re.I),
    re.compile(r"\bno\s+(?:held\s+|later\s+)?(?:amendments?|amending\s+instruments?)\b(?:\s*(?:,|or|and)\s*\w+){0,3}\s+"
               r"(?:is|are|was|were|has\s+been|have\s+been)\s+(?:held|found|recorded)\b", re.I),
    re.compile(r"\bnothing\b[^.;]{0,30}\bamends\b", re.I),
    re.compile(r"\bunamended\b", re.I),
]
# Wording that limits an absence statement to part of the history or another
# instrument; such sentences are not compared with the recorded events.
EXCEPTION_RE = re.compile(r"\b(?:other\s+than|except|besides|apart\s+from|aside\s+from|beyond|further|after|since|before|prior\s+to|until|"
                          r"at\s+the\s+time|originally|as\s+(?:first\s+)?(?:signed|issued|printed)|if|whether)\b", re.I)
PART_RE = re.compile(r"\b(?:sections?|sec\.|subsections?|paragraphs?|clauses?|provisions?|items?|§)\s*[\w(]", re.I)
CLAUSE_REF = re.compile(r"\b(?:this|the|that)\s+(?:clause|provision|section|subsection|paragraph|definition|sentence|command)\b", re.I)
EO_NUM = re.compile(r"\b(?:Executive\s+Orders?\s+(?:No\.?\s*)?|E\.\s?O\.\s*|EO\s*:?\s*)(\d{3,6}[A-Z]?)\b", re.I)

DATE_ISO = re.compile(r"\b(1[6-9]\d\d|20\d\d)-(\d\d)-(\d\d)\b")
MONTHS = {m: i for i, m in enumerate("january february march april may june july august september october november december".split(), 1)}
DATE_LONG = re.compile(r"\b(" + "|".join(MONTHS) + r")\.?\s+(\d{1,2}),?\s+(1[6-9]\d\d|20\d\d)\b", re.I)

PAGE_LABEL = re.compile(r"\bPDF\s+pages?\s+(\d+(?:\s*(?:-|–|,|and|to)\s*\d+)*)", re.I)
PAGE_MARK = re.compile(r"^=== PDF page (\d+) of \d+ ===[ \t]*$", re.M)

DECLARES_CLAIM = [
    r"\bemergency\s+(?:that\s+|which\s+)?(?:it|this\s+order|the\s+order)\s+(?:itself\s+)?declare[sd]\b",
    r"\bdeclared\s+(?:in|by)\s+this\s+order\b",
    r"\b(?:this|the)\s+order(?:'s\s+own\s+text)?\s+(?:itself\s+)?declares\s+(?:a|the|its)\s+(?:own\s+)?(?:national\s+)?emergency\b",
    r"\b(?:this|the)\s+order'?s?\s+own\s+(?:declaration|declared)\s+(?:of\s+)?(?:the\s+|a\s+)?(?:national\s+)?emergency\b",
]
DECLARING_TEXT = [
    re.compile(r"\b(?:hereby|do|I)\s+(?:\w+\s+){0,3}declare\b[^.]{0,250}?\bemergenc", re.I),
    re.compile(r"\bemergency\b[^.]{0,120}\b(?:is|are)\s+hereby\s+declared\b", re.I),
    re.compile(r"\bdeclare\s+(?:a|an|the)\s+(?:\w+\s+){0,2}(?:national\s+)?emergency\b", re.I),
]


def _sentences(text):
    return [s for s in re.split(r"(?<=[!?;])\s+|(?<=[a-z0-9)\"'”])\.\s+(?=[A-Z(\"'“])|\n+", str(text or "")) if s.strip()]


def _own_number(claim):
    m = re.search(r"(\d{3,6}[A-Z]?)", str(claim.get("instrument_id") or ""))
    return m.group(1).upper() if m else None


def _rationale_parts(text):
    """Split an embedded 'Member checks: {json}' block into its strings."""
    text = str(text or "")
    marker = re.search(r"Member checks:\s*", text, re.I)
    if marker:
        try:
            obj, end = json.JSONDecoder().raw_decode(text[marker.end():])
            if isinstance(obj, dict):
                return ([("research_rationale", text[:marker.start()])]
                        + [(f"research_rationale.{k}", v) for k, v in obj.items() if isinstance(v, str)]
                        + [("research_rationale", text[marker.end() + end:])])
        except ValueError:
            pass
    return [("research_rationale", text)]


def _strings(value, path):
    if isinstance(value, str): yield path, value
    elif isinstance(value, list):
        for i, v in enumerate(value): yield from _strings(v, f"{path}[{i}]")
    elif isinstance(value, dict):
        for k, v in value.items():
            if k not in ("source", "quote", "text"): yield from _strings(v, f"{path}.{k}")


def prose(claim):
    """(field, scope_id or None, text) for every producer-written explanatory field."""
    out = list((f, None, t) for f, t in _rationale_parts(claim.get("research_rationale")))
    savings = claim.get("savings_residuals")
    if isinstance(savings, dict) and isinstance(savings.get("reason"), str):
        out.append(("savings_residuals.reason", None, savings["reason"]))
    for key in ("unresolved_material_gaps", "source_notes"):
        out.extend((f, None, t) for f, t in _strings(claim.get(key), key))
    end = claim.get("whole_order_end")
    if isinstance(end, dict):
        out.extend((f, None, t) for f, t in _strings({k: v for k, v in end.items() if k not in ("actor", "date", "mechanism")}, "whole_order_end"))
    for pos, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict): continue
        scope = clause.get("scope_id") or f"clause[{pos}]"
        if isinstance(clause.get("judgment_reason"), str):
            out.append((f"operative_clauses[{scope}].judgment_reason", scope, clause["judgment_reason"]))
        pred = clause.get("current_predicate")
        if isinstance(pred, dict) and isinstance(pred.get("legal_basis"), str):
            out.append((f"operative_clauses[{scope}].current_predicate.legal_basis", scope, pred["legal_basis"]))
    return out


def _events(claim):
    for pos, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict): continue
        scope = clause.get("scope_id") or f"clause[{pos}]"
        for event in clause.get("later_events") or []:
            if isinstance(event, dict): yield scope, event


def _kind(event):
    """Classify by the mechanism's leading term only; free-text tails often say what an event is not."""
    mech = re.sub(r"[_\s]+", " ", str(event.get("mechanism") or "").lower()).strip()
    if re.match(r"(?:annual )?continuation (?:of (?:the )?(?:a )?national emergency|notice)|national emergency continuation notice", mech): return "notice"
    if re.match(r"amend(?:ment|ed|s)?\b", mech) and not re.search(r"\bnot (?:of )?this order\b|\bof (?:executive )?order \d", mech): return "amendment"
    return None


def _num(token):
    token = token.lower()
    return int(token) if token.isdigit() else NUMBER_WORDS.get(token)


# ---------------------------------------------------------------- check 1
def check_counts(claim):
    flags, seen = [], set()
    own = _own_number(claim)
    recorded = {"notice": {}, "amendment": {}}
    for scope, event in _events(claim):
        kind = _kind(event)
        if kind: recorded[kind].setdefault(scope, set()).add(str(event.get("actor")))
    union = {k: set().union(*v.values()) if v else set() for k, v in recorded.items()}
    for field, scope, text in prose(claim):
        for sentence in _sentences(text):
            others = {n.upper() for n in EO_NUM.findall(sentence)} - {own}
            if EXCEPTION_RE.search(sentence):
                continue
            notices = union["notice"]
            if notices:
                stated = None
                if NOTICE_ZERO.search(sentence) and not others:
                    stated = 0
                else:
                    m = NOTICE_COUNT.search(sentence)
                    if m and not others and not re.search(r"\b(?:first|last|latest|earliest|remaining|other)\s+" + re.escape(m.group(1)) + r"\b", sentence, re.I):
                        stated = _num(m.group(1))
                if stated is not None and stated != len(notices):
                    key = ("notice", field, stated)
                    if key not in seen:
                        seen.add(key)
                        flags.append({"code": "count_contradicts_records", "scope_id": scope, "field": field,
                                      "reasoning_sentence": sentence.strip()[:400], "stated_count": stated,
                                      "recorded_count": len(notices),
                                      "detail": f"Prose states {stated} continuation notices, but later_events record {len(notices)} distinct continuation notices."})
            if not union["amendment"] or not any(p.search(sentence) for p in AMEND_ABSENT):
                continue
            names_order = bool(re.search(r"\b(?:the|this)\s+order\b", sentence, re.I)) or bool(own and re.search(rf"\b{re.escape(own)}\b", sentence))
            whole = names_order and not PART_RE.search(sentence) and not CLAUSE_REF.search(sentence)
            if scope is None and not whole:
                continue  # claim-level text about a part of the order cannot be mapped to one clause
            if others:
                continue  # sentence is about another instrument's amendment history
            target = union["amendment"] if (scope is None or whole) else recorded["amendment"].get(scope, set())
            if target:
                key = ("amendment", field)
                if key not in seen:
                    seen.add(key)
                    flags.append({"code": "count_contradicts_records", "scope_id": scope, "field": field,
                                  "reasoning_sentence": sentence.strip()[:400], "stated_count": 0,
                                  "recorded_count": len(target),
                                  "detail": f"Prose says no amendment is held, but later_events record {len(target)} amending instrument(s): {', '.join(sorted(target)[:6])}."})
    return flags


# ---------------------------------------------------------------- held text
def _held_text(source, repo, cache):
    """Return the whole verified file text for a cited source, or (None, reason)."""
    if not isinstance(source, dict): return None, "no_source"
    path, sha = source.get("text_path"), source.get("text_sha256")
    if not path or not sha: return None, "source_text_reference_missing"
    key = (path, sha)
    if key in cache: return cache[key]
    p = (Path(repo) / path).resolve()
    if not p.is_relative_to(Path(repo).resolve()) or not p.is_file():
        result = (None, "source_text_file_unavailable")
    else:
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha: result = (None, "source_text_hash_mismatch")
        else:
            try: result = (raw.decode("utf-8"), None)
            except UnicodeDecodeError: result = (None, "source_text_not_utf8")
    cache[key] = result
    return result


def _normal(text):
    text = re.sub(r"-\s*\n\s*", "", str(text or ""))
    return re.sub(r"\s+", " ", text.replace("­", "")).strip()


# ---------------------------------------------------------------- check 2
def check_emergency(claim, repo, cache):
    own = _own_number(claim)
    patterns = DECLARES_CLAIM + ([rf"\bemergency\s+declared\s+(?:in|by)\s+(?:Executive\s+Order|E\.\s?O\.|EO)\s*:?\s*{re.escape(own)}\b"] if own else [])
    hits = []
    for field, scope, text in prose(claim):
        for sentence in _sentences(text):
            if re.search(r"\b(?:does|did)\s+not\s+declare|\bdeclares\s+no\b|\bdeclares\s+none\b", sentence, re.I):
                continue
            others = {n.upper() for n in EO_NUM.findall(sentence)} - {own}
            # "the emergency it declared" after naming another order refers to that order.
            usable = patterns[1:] if others else patterns
            if any(re.search(p, sentence, re.I) for p in usable):
                hits.append((field, scope, sentence.strip()))
    if not hits: return [], []
    source = claim.get("original_representation")
    full, why = _held_text(source, repo, cache)
    if full is None:
        return [], [{"code": "emergency_declaration_text_unavailable", "reason": why}]
    a, b = source.get("char_start"), source.get("char_end")
    own_text = full[a:b] if type(a) is int and type(b) is int and 0 <= a < b <= len(full) else full
    body = _normal(own_text)
    if any(p.search(body) for p in DECLARING_TEXT):
        return [], []
    fields = sorted({h[0] for h in hits})
    return [{"code": "emergency_declaration_unsupported", "scope_id": hits[0][1], "reasoning_sentence": hits[0][2][:400],
             "fields": fields[:12], "field_count": len(fields),
             "detail": "Prose says this order declares a national emergency, but its held original text has no declaring words "
                       "(such as 'hereby declare a national emergency'). Check whether the order declares the emergency or acts under one declared elsewhere."}], []


# ---------------------------------------------------------------- check 3
def _label_pages(label):
    pages = set()
    for m in PAGE_LABEL.finditer(str(label or "")):
        for part in re.split(r"\s*(?:,|and)\s*", m.group(1)):
            r = re.split(r"\s*(?:-|–|to)\s*", part.strip())
            if len(r) == 2 and r[0].isdigit() and r[1].isdigit() and int(r[0]) <= int(r[1]) <= int(r[0]) + 2000:
                pages.update(range(int(r[0]), int(r[1]) + 1))
            elif len(r) == 1 and r[0].isdigit():
                pages.add(int(r[0]))
    return pages


def _span_pages(full, a, b):
    """Pages holding non-blank characters of full[a:b]; None when the text has no page boundaries."""
    marks = [(m.start(), m.end(), int(m.group(1))) for m in PAGE_MARK.finditer(full)]
    if marks:
        pages = set()
        for i, (start, end, page) in enumerate(marks):
            stop = marks[i + 1][0] if i + 1 < len(marks) else len(full)
            lo, hi = max(a, end), min(b, stop)
            if lo < hi and full[lo:hi].strip(): pages.add(page)
        return pages
    if "\f" in full:
        pages, offset = set(), 0
        for n, chunk in enumerate(full.split("\f"), 1):
            lo, hi = max(a, offset), min(b, offset + len(chunk))
            if lo < hi and full[lo:hi].strip(): pages.add(n)
            offset += len(chunk) + 1
        return pages
    return None


def _cited_sources(claim):
    def walk(value, path):
        if isinstance(value, dict):
            if isinstance(value.get("text_path"), str) and "page_or_item" in value and "char_start" in value:
                yield path, value
            for k, v in value.items():
                if k not in ("quote", "text"): yield from walk(v, f"{path}.{k}" if path else k)
        elif isinstance(value, list):
            for i, v in enumerate(value): yield from walk(v, f"{path}[{i}]")
    yield from walk(claim, "")


def check_pages(claim, repo, cache):
    flags, gaps, seen = [], [], {}
    for path, source in _cited_sources(claim):
        label = source.get("page_or_item")
        wanted = _label_pages(label)
        a, b = source.get("char_start"), source.get("char_end")
        if not wanted or type(a) is not int or type(b) is not int or a >= b: continue
        key = (source.get("text_path"), a, b, label)
        if key in seen:
            if seen[key] is not None: seen[key]["field_count"] += 1
            continue
        seen[key] = None
        full, why = _held_text(source, repo, cache)
        if full is None or b > len(full):
            gaps.append({"code": "page_label_text_unavailable", "field": path, "reason": why or "span_outside_text"}); continue
        quote = source.get("quote")
        if isinstance(quote, str) and quote and _normal(quote) != _normal(full[a:b]):
            gaps.append({"code": "page_label_span_unverified", "field": path, "reason": "quote does not match the cited span"}); continue
        pages = _span_pages(full, a, b)
        if not pages: continue
        outside = sorted(pages - wanted)
        if outside:
            flag = {"code": "page_label_excludes_span", "field": path, "flagged_text": f"{label} @ {source.get('text_path')}:{a}-{b}",
                    "label_pages": sorted(wanted), "span_pages": sorted(pages), "field_count": 1,
                    "detail": f"page_or_item '{label}' names PDF page(s) {sorted(wanted)}, but the cited span (chars {a}-{b}) lies on PDF page(s) {sorted(pages)}."}
            seen[key] = flag
            flags.append(flag)
    return flags, gaps


# ---------------------------------------------------------------- checks 4 and 5
def _iso(value):
    m = DATE_ISO.fullmatch(str(value or "").strip())
    return m.group(0) if m else None


def _signing_date(claim, dossier):
    for value in ((dossier or {}).get("signing_date"), (claim.get("original_representation") or {}).get("signing_date")):
        if _iso(value): return _iso(value)
    return None


def _structured_dates(claim):
    for pos, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict): continue
        scope = clause.get("scope_id") or f"clause[{pos}]"
        end = clause.get("first_end")
        if isinstance(end, dict) and _iso(end.get("date")):
            yield f"operative_clauses[{scope}].first_end.date", scope, _iso(end["date"])
        for i, event in enumerate(clause.get("later_events") or []):
            if isinstance(event, dict) and _iso(event.get("effective_date")):
                yield f"operative_clauses[{scope}].later_events[{event.get('actor') or i}].effective_date", scope, _iso(event["effective_date"])
    end = claim.get("whole_order_end")
    if isinstance(end, dict) and _iso(end.get("date")):
        yield "whole_order_end.date", None, _iso(end["date"])


def check_signing(claim, dossier):
    signed = _signing_date(claim, dossier)
    if not signed: return [], [{"code": "signing_date_unknown"}]
    early = [(f, s, d) for f, s, d in _structured_dates(claim) if d < signed]
    if not early: return [], []
    return [{"code": "date_before_signing", "scope_id": early[0][1], "signing_date": signed,
             "examples": [{"field": f, "date": d} for f, _, d in early[:8]], "field_count": len(early),
             "detail": f"{len(early)} end or later-event date(s) precede the order's signing date {signed}, e.g. {early[0][0]} = {early[0][2]}."}], []


def _text_dates(text):
    out = {m.group(0) for m in DATE_ISO.finditer(text)}
    for m in DATE_LONG.finditer(text):
        try: out.add(f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}")
        except (KeyError, ValueError): pass
    return out


def check_end_years(claim):
    flags = []
    rationale = " ".join(t for f, s, t in prose(claim) if s is None)
    ends = []
    for pos, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict): continue
        end = clause.get("first_end")
        if isinstance(end, dict) and _iso(end.get("date")):
            scope = clause.get("scope_id") or f"clause[{pos}]"
            ends.append((f"operative_clauses[{scope}].first_end.date", scope, _iso(end["date"]), str(clause.get("judgment_reason") or "")))
    end = claim.get("whole_order_end")
    if isinstance(end, dict) and _iso(end.get("date")):
        ends.append(("whole_order_end.date", None, _iso(end["date"]), rationale))
    def clash(date, reasons):
        stated = _text_dates(reasons)
        if not stated or date in stated: return None
        other = sorted(d for d in stated if d[5:] == date[5:] and d[:4] != date[:4])
        return other[0] if other else None
    for field, scope, date, reasons in ends:
        other = clash(date, reasons)
        if other:
            flags.append({"code": "end_year_conflicts_reasons", "scope_id": scope, "field": field, "date": date, "reasons_date": other,
                          "detail": f"{field} is {date}, but the reasons give {other} (same month and day, different year) and never {date}."})
    # Later-event dates get one aggregated flag per claim: one event is often attached to many clauses.
    # A date counts only from sentences of the clause's reasons that name the event's instrument.
    events = []
    for pos, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict): continue
        scope = clause.get("scope_id") or f"clause[{pos}]"
        sentences = _sentences(clause.get("judgment_reason"))
        for event in clause.get("later_events") or []:
            date = _iso(event.get("effective_date")) if isinstance(event, dict) else None
            number = re.fullmatch(r"(?:EO|PROC|PL|PLO):(\d{3,6}[A-Z]?)", str(event.get("actor") or "")) if date else None
            if not number: continue  # bind only to sentences that name the acting instrument by number
            # Annual notices share month and day by design, so only the sentences naming this actor count.
            named = " ".join(t for t in sentences if re.search(rf"\b{re.escape(number.group(1))}\b", t))
            other = clash(date, named) if named else None
            if other: events.append({"field": f"operative_clauses[{scope}].later_events[{event.get('actor')}].effective_date", "date": date, "reasons_date": other})
    if events:
        flags.append({"code": "end_year_conflicts_reasons", "scope_id": None, "field": "later_events.effective_date",
                      "examples": events[:8], "field_count": len(events),
                      "detail": f"{len(events)} later-event date(s) differ in year from the same month and day in their clause's reasons, "
                                f"e.g. {events[0]['field']} = {events[0]['date']} but the reasons give {events[0]['reasons_date']}."})
    return flags


def check(claim, dossier, repo, packet_path=None, cache=None):
    cache = {} if cache is None else cache
    flags, gaps = check_counts(claim), []
    for fl, gp in (check_emergency(claim, repo, cache), check_pages(claim, repo, cache), check_signing(claim, dossier)):
        flags.extend(fl); gaps.extend(gp)
    flags.extend(check_end_years(claim))
    return {"flags": flags, "coverage_gaps": gaps}
