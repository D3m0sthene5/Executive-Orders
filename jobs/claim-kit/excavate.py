"""Pure, conservative claim-kit excavators. Every result is a research lead.

Offsets are Python Unicode code-point offsets in the unmodified input. These
functions never read files, resolve legal status, or infer census identities.
"""
from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import re
from functools import lru_cache


FLAGS = re.I | re.M
MONTHS = {name.lower(): n for n, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): n for n, name in enumerate(calendar.month_abbr) if name})
DATE = r"(?:\d{4}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Sept\.?|Oct\.?|Nov\.?|Dec\.?)\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4}|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
EO_NUMBER = r"\d(?:[ \t]*\d){0,4}[A-Z]?(?:½)?"
EO_REF = re.compile(r"\bExecutive\s+Orders?\s*(?:(?:Nos?|Numbers?)\.?\s*)?(" + EO_NUMBER + r")(?![\w-]|,\d|[ \t]+\d)", re.I)
CHANGE = re.compile(r"\b(revok(?:e[ds]?|ing)|supersed(?:e[ds]?|ing)|amend(?:s|ed|ing)?|transfer(?:s|red|ring)?|abolish(?:es|ed|ing)?|terminat(?:e[ds]?|ing)|rescind(?:s|ed|ing)?)\b", re.I)
HEADING = re.compile(r"(?m)^[ \t]*(?:(?P<section>(?:Sec(?:tion)?\.?\s+|SECTION\s+|SEC\.?\s+)(?P<sec>[0-9]+[A-Za-z]?)[ \t]*(?:[.):](?=\s|$)|(?=[ \t]*$)))|(?P<schedule>SCHEDULE(?:\s+[A-Z0-9IVX]+)?\b)|(?P<sub>\(\s*(?P<letter>[a-z])\s*\)(?!\s*[,;]))|(?P<item>(?:\(\s*(?P<number>[0-9]+|[ivx]{2,})\s*\)|(?P<decimal>[0-9]+)\s*\.(?=\s))))")
WHITE_HOUSE = r"(?im)^[ \t]*T[ \t]*H[ \t]*E[ \t]+W[ \t]*H[ \t]*I[ \t]*T[ \t]*E[ \t]+H[ \t]*O[ \t]*U[ \t]*S[ \t]*E[ \t]*[,.;]?[ \t]*$"
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "thirty": 30, "sixty": 60, "ninety": 90}
NUMBERS.update({"eleven": 11, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "forty": 40, "fifty": 50, "seventy": 70, "eighty": 80})
NUMBER = r"(?:(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)[ -](?:one|two|three|four|five|six|seven|eight|nine)|\d+|" + "|".join(NUMBERS) + r")"
TERM = re.compile(r"\b(?:for\s+)?(?:a\s+)?(?:period\s+of\s+)?(" + NUMBER + r")\s+(calendar\s+)?(days?|weeks?|months?|years?)\b", re.I)


def _date(value):
    value = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", value, flags=re.I)
    value = re.sub(r"\s+", " ", value.strip()).replace(",", "").replace(".", "")
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError:
        pass
    parts = value.split()
    try:
        if parts[0].isdigit():
            day, month, year = int(parts[0]), MONTHS[parts[1].lower()], int(parts[2])
        else:
            month, day, year = MONTHS[parts[0].lower()], int(parts[1]), int(parts[2])
        return dt.date(year, month, day).isoformat()
    except (ValueError, KeyError, IndexError):
        return None


def _add_term(base, amount, unit):
    if not base:
        return None
    date = dt.date.fromisoformat(base)
    amount = int(amount) if amount.isdigit() else sum(NUMBERS[n] for n in re.split(r"[ -]", amount.lower()))
    if unit.lower().startswith(("day", "week")):
        try:
            return (date + dt.timedelta(days=amount * (7 if unit.lower().startswith("week") else 1))).isoformat()
        except OverflowError:
            return None
    months = amount * (12 if unit.lower().startswith("year") else 1)
    year, month = divmod(date.year * 12 + date.month - 1 + months, 12)
    if not 1 <= year <= 9999:
        return None
    # Anniversary conventions at month ends need legal confirmation.
    if date.day > calendar.monthrange(year, month + 1)[1]:
        return None
    return dt.date(year, month + 1, date.day).isoformat()


def _trim(text, start, end):
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _page(text, offset, source):
    # Producer page markers carry actual PDF page numbers, not relative page
    # indices. Use the closest preceding marker without modifying the text.
    markers = list(re.finditer(r"(?im)^===\s*PDF\s+page\s+(\d+)\s+of\s+\d+\s*===", text[:offset]))
    if markers:
        return int(markers[-1][1])
    # Form feeds delimit PDF pages when present; otherwise don't invent a page.
    explicit = re.search(r"PDF\s+pages?\s+(\d+)", str(source.get("page_or_item", "")), re.I)
    first = int(explicit[1]) if explicit else None
    return first + text[:offset].count("\f") if first is not None else None


def _signature_start(text, end):
    prior = re.search(r"(?m)^([^\n]{3,75})\n[ \t]*\Z", text[:end])
    if prior:
        letters = re.sub(r"[^A-Za-z]", "", prior[1])
        presidents = ("GeorgeWashington", "JohnAdams", "ThomasJefferson", "JamesMadison", "JamesMonroe", "JohnQuincyAdams", "AndrewJackson", "MartinVanBuren", "WilliamHenryHarrison", "JohnTyler", "JamesKPolk", "ZacharyTaylor", "MillardFillmore", "FranklinPierce", "JamesBuchanan", "AbrahamLincoln", "AndrewJohnson", "USGrant", "UlyssesSGrant", "RutherfordBHayes", "JamesAGarfield", "ChesterAArthur", "GroverCleveland", "BenjaminHarrison", "WilliamMcKinley", "TheodoreRoosevelt", "WilliamHTaft", "WoodrowWilson", "WarrenGHarding", "CalvinCoolidge", "HerbertHoover", "FranklinDRoosevelt", "HarrySTruman", "DwightDEisenhower", "JohnFKennedy", "LyndonBJohnson", "RichardNixon", "RichardMNixon", "GeraldRFord", "JimmyCarter", "RonaldReagan", "GeorgeBush", "GeorgeHWBush", "WilliamJClinton", "GeorgeWBush", "BarackObama", "BarackHObama", "DonaldJTrump", "JosephRBidenJr")
        signature = (letters.lower() in {p.lower() for p in presidents} or
                     bool(letters and letters.isupper() and len(prior[1].split()) <= 6))
        if signature and not re.search(r"[;:()\d]|\b(?:shall|order|unless|hereby|extended)\b", prior[1], re.I):
            return prior.start()
    return end


def _body_end(text, start=0):
    patterns = [r"(?m)^\s*\[\s*(?:FR|F\.\s*R\.)\s+Doc", WHITE_HOUSE, r"(?im)^\s*IN WITNESS WHEREOF\b"]
    found = [m.start() for p in patterns for m in re.finditer(p, text) if m.start() >= start and not re.search(r"(?im)^\s*SCHEDULE\b", text[m.end():])]
    end = min(found, default=len(text))
    # A signature immediately before the White House line is recognizable as
    # a short name line. Keep this bounded to that position, not arbitrary
    # uppercase substantive headings elsewhere in the document.
    if any(m.start() == end for m in re.finditer(WHITE_HOUSE, text)):
        end = _signature_start(text, end)
    return end


def _paragraph_start(text, offset):
    boundary = text.rfind("\n\n", 0, offset)
    return boundary + 2 if boundary >= 0 else 0


@lru_cache(maxsize=32)
def _extent(instrument_id, text):
    """Bound an attributed order before using any signature or legal wording.

    Neighboring pages can begin with a previous order's FR Doc or signature.
    Only a printed heading matching the supplied identity licenses skipping
    those blocks. Space-separated printed digits are read, never repaired.
    """
    heading = re.compile(r"(?im)^[ \t]*(?:[^\n]{0,30}?[-—–][ \t]*)?Executive[ \t]+Order[ \t]+(" + EO_NUMBER + r")(?![\w-]|,\d|[ \t]+\d)(?=\s+(?:of|o[ \t]+f)\b|[ \t]*$)")
    headers = list(heading.finditer(text))
    own = next((h for h in headers if "EO:" + re.sub(r"[ \t]", "", h[1]).upper() == instrument_id), None)
    start = own.start() if own else 0
    next_header = next((h for h in headers if own and h.start() > own.start() and "EO:" + re.sub(r"[ \t]", "", h[1]).upper() != instrument_id), None)
    upper = next_header.start() if next_header else len(text)
    return start, _body_end(text[:upper], start)


def segment(instrument_id, text, source):
    """Build disjoint operative spans, retaining nested heading paths.

    Recital/title heuristics are explicitly flagged; unusual OCR requires review.
    An unnumbered operative lead before numbered sections is always retained.
    """
    notes = ["Machine segmentation lead; compare the inventory with the official original."]
    body_start, end = _extent(instrument_id, text)
    headings = list(HEADING.finditer(text, body_start, end))
    operative = re.compile(r"\b(?:I\s+(?:hereby\s+)?(?:order|direct|extend|establish|revoke|amend)|it\s+is\s+(?:hereby\s+)?ordered|(?:is|are)\s+(?:hereby\s+)?(?:amended|revoked|established)|[A-Za-z]+\s+(?:shall|is hereby))\b", re.I).search(text, body_start, end)
    if headings:
        start = headings[0].start()
        if operative and operative.start() < start:
            # Authority text is excluded only when it has a clear operative tail.
            lead = text[:start]
            para = _paragraph_start(lead, operative.start())
            start = max(body_start, para)
            whereas = re.search(r"\b(?:NOW,?\s+THEREFORE|I\s+hereby)\b", lead[start:], re.I)
            if whereas:
                start += whereas.start()
            # 'It is ordered as follows' concludes an authority preamble; it
            # does not itself establish an additional operative clause. Keep
            # a separate unnumbered command only when it precedes that formula.
            preamble = text[start:headings[0].start()]
            if re.search(r"\b(?:it\s+is\s+|is\s+)?(?:hereby\s+)?ordered\s+as\s+follow\s*s\s*:", preamble, re.I):
                command = re.search(r"\bI\s+(?:hereby\s+)?(?:establish|direct|extend|transfer|revoke|amend|abolish|terminate)\b", preamble, re.I)
                if not command:
                    start = headings[0].start()
    elif operative:
        start = max(body_start, _paragraph_start(text, operative.start()))
    else:
        start = body_start
        notes.append("No confident operative boundary found; unstructured text retained for review.")
    # Exclude authority-only lead paragraphs; retain authority in one-sentence orders.
    if not headings:
        authority = [m for m in re.finditer(r"(?im)^\s*(?:By virtue|By the authority|Pursuant to)\b", text[:end]) if m.start() >= body_start]
        prior_authority = [a for a in authority if operative and a.start() <= operative.start()]
        if prior_authority:
            start = prior_authority[-1].start()
    # FR text products put metadata and printed page headers before the
    # authority paragraph. Never let paragraph whitespace pull those headers
    # into an otherwise unnumbered operative lead.
    metadata = re.search(r"(?m)^Instrument:\s*EO:", text[:end])
    if metadata:
        authorities = [m for m in re.finditer(r"(?im)^[ \t]*(?:By\s+(?:virtue|the\s+authority|authority)|Pursuant\s+to)\b", text[:end]) if m.start() >= body_start]
        first_heading = headings[0].start() if headings else end
        authority = next((m for m in authorities if m.start() < first_heading), None)
        if authority and start < authority.start():
            start = authority.start()
    marks = [h for h in headings if h.start() >= start]
    boundaries = sorted(set([start, end] + [h.start() for h in marks]))
    clauses, section, subsection, schedule, seen = [], "", "", "", {}
    for a, b in zip(boundaries, boundaries[1:]):
        tail = re.search(WHITE_HOUSE + r"|^\s*\[\s*(?:FR|F\.\s*R\.)\s+Doc", text[a:b])
        if tail:
            b = _signature_start(text, a + tail.start())
        a, b = _trim(text, a, b)
        if a == b:
            continue
        h = next((h for h in marks if a <= h.end() and h.start() <= a), None)
        label, kind, scope = "operative lead", "whole", "lead"
        if h:
            label = h.group().strip()
            if h["section"]:
                section, subsection = "sec" + h["sec"].lower(), ""
                kind, scope = "section", "-".join(filter(None, [schedule, section]))
            elif h["schedule"]:
                schedule, section, subsection = re.sub(r"\s+", "-", h["schedule"].lower()), "", ""
                kind, scope = "schedule", schedule
            elif h["sub"]:
                subsection = h["letter"].lower()
                kind, scope = "subsection", "-".join(filter(None, [schedule, section, subsection]))
            else:
                kind, scope = "item", "-".join(filter(None, [schedule, section, subsection, h["number"] or h["decimal"]]))
        value = text[a:b]
        if re.search(r"\bamended\s+by\s+(?:adding|striking|deleting|inserting|substituting|revising|redesignating)", value, re.I):
            kind = "amendment_instruction"
        if len(boundaries) == 2:
            label, scope = "sole paragraph", "whole"
            if kind != "amendment_instruction":
                kind = "whole"
        seen[scope] = seen.get(scope, 0) + 1
        scope += "-dup" + str(seen[scope]) if seen[scope] > 1 else ""
        scope_id = instrument_id + "#" + scope
        clauses.append({"id": "CLAUSES:" + scope_id, "scope_id": scope_id, "kind": kind, "label": label, "text": value, "char_start": a, "char_end": b, "pdf_page": _page(text, a, source)})
    return {"id": "CLAUSES:" + instrument_id, "instrument_id": instrument_id, "source": source, "clauses": clauses, "method": "heading_and_operative_boundary_v2", "confidence": "medium" if notes or not headings else "high", "notes": " ".join(notes)}


def _uncached_sentences(text):
    # Periods in Sec./No./month abbreviations must not break a reference.
    start = 0
    for match in re.finditer(r"[.!?](?=\s+(?:[A-Z(]|$))|\n\s*\n", text):
        before = text[max(start, match.start() - 12):match.start()]
        if re.search(r"\b(?:No|Nos|Sec|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)$", before, re.I):
            continue
        a, b = _trim(text, start, match.end())
        if a < b:
            yield a, b
        start = match.end()
    a, b = _trim(text, start, len(text))
    if a < b:
        yield a, b


@lru_cache(maxsize=32)
def _sentence_spans(text):
    return tuple(_uncached_sentences(text))

def _sentences(text):
    return iter(_sentence_spans(text))


def own_terms(instrument_id, text, source, clauses):
    """Surface own-term wording without treating report deadlines as endings."""
    clauses = clauses.get("clauses", []) if isinstance(clauses, dict) else clauses
    result = []
    windows = [(c["char_start"], c["char_end"]) for c in clauses if isinstance(c, dict) and type(c.get("char_start")) is int and type(c.get("char_end")) is int]
    if not windows:
        windows = [_extent(instrument_id, text)]
    sentence_spans = ((start + a, start + b) for start, end in windows for a, b in _sentences(text[start:end]))
    for a, b in sentence_spans:
        sentence = text[a:b]
        kinds = []
        report = bool(re.search(r"\b(?:report|recommendations?|findings)\b.{0,120}\b(?:within|by|no later|not later|before|days|months|years)\b|\b(?:within|not later|no later)\b.{0,120}\b(?:report|recommendations?|findings)\b", sentence, re.I | re.S))
        term = TERM.search(sentence)
        if report:
            kinds.append("report_deadline")
        if term and not report and re.search(r"\b(?:period|duration|existence|continue[sd]?|extend[sd]?|term|remain[sd]?|effective|expire[sd]?|terminate[sd]?)\b", sentence, re.I):
            kinds.append("fixed_term")
        if not report and re.search(r"\b(?:expire[sd]?|sunset|terminate[sd]?|cease)\b", sentence, re.I) and re.search(DATE, sentence, re.I):
            kinds.append("sunset_date")
        if re.search(r"\buntil\b", sentence, re.I):
            kinds.append("until_event")
        if re.search(r"\btemporary\b.{0,100}\b(?:committee|commission|board|council|body|office)\b|\b(?:committee|commission|board|council|body|office)\b.{0,100}\btemporary\b", sentence, re.I | re.S):
            kinds.append("temporary_body")
        if re.search(r"\b(?:provided\s+that|subject\s+to|unless|if\s+and\s+when|upon\s+(?:completion|approval))\b", sentence, re.I):
            kinds.append("condition")
        if re.search(r"\b(?:duration|continuance|termination|end)\b.{0,70}\b(?:war|emergency|hostilities)\b|\b(?:war|emergency|hostilities)\b.{0,70}\b(?:duration|continues|ends)\b", sentence, re.I | re.S):
            kinds.append("emergency_duration")
        for kind in dict.fromkeys(kinds):
            start_match = re.search(r"\b(?:from|beginning(?:\s+on)?|commencing(?:\s+on)?|starting(?:\s+on)?)\s+(" + DATE + ")", sentence, re.I)
            end_match = re.search(r"\b(?:to|through|until|on)\s+(" + DATE + ")", sentence, re.I)
            start_date = _date(start_match[1]) if start_match else None
            stated_signing_base = bool(kind == "fixed_term" and term and re.search(r"\b(?:from|after|beginning(?:\s+on)?)\s+(?:the\s+)?date\s+of\s+this\s+order\b", sentence, re.I))
            if not start_date and stated_signing_base:
                start_date = _date(str(source.get("signing_date") or ""))
            end_date = _date(end_match[1]) if end_match and kind in {"fixed_term", "sunset_date", "until_event"} else None
            computed = _add_term(start_date, term[1], term[3]) if kind == "fixed_term" and term and start_date else None
            scope = next((c["scope_id"] for c in clauses if c["char_start"] <= a < c["char_end"] or a <= c["char_start"] < b), instrument_id + "#whole")
            digest = hashlib.sha256((scope + "\0" + kind + "\0" + sentence).encode()).hexdigest()[:16]
            result.append({"id": "TERM:" + instrument_id + ":" + digest, "instrument_id": instrument_id, "scope_id": scope, "kind": kind, "text": sentence, "char_start": a, "char_end": b, "start_date": start_date, "stated_end_date": end_date, "computed_end_candidate": computed, "source": source, "confidence": "medium", "notes": "Machine wording lead; no cessation or occurrence inferred." + (" Explicit date-of-this-order base uses the source job's signing-date candidate; confirm the printed signing date." if stated_signing_base else ""), "note": "A report deadline never yields an end candidate; month-end anniversary ambiguity remains unresolved."})
    return result


def _uncached_references(text):
    """Only explicitly printed EO numbers; preserve census-form suffixes."""
    for m in EO_REF.finditer(text):
        yield "EO:" + re.sub(r"[ \t]", "", m[1]).upper(), m.start(), m.end()
        if re.search(r"Orders\b", m[0], re.I):
            # Consume one grammatical continuation at a time. Date commas must
            # never become extra order numbers, and a later unrelated 'No.'
            # outside this list must not inherit the Executive Orders heading.
            continuation = re.compile(
                r"(?:\s+(?:of|dated)\s+" + DATE + r")?"
                r"(?:\s*,?\s*as\s+amended)?"
                r"(?:\s*,\s*(?:(?:and|or)\s+)?|\s+(?:and|or)\s+)"
                r"(?:(?:Nos?|Numbers?)\.?\s*)?"
                r"(?P<number>" + EO_NUMBER + r")(?![\w-]|,\d|[ \t]+\d)", re.I)
            cursor = m.end()
            while True:
                follow = continuation.match(text, cursor)
                if not follow:
                    break
                yield "EO:" + re.sub(r"[ \t]", "", follow["number"]).upper(), follow.start("number"), follow.end("number")
                cursor = follow.end()


@lru_cache(maxsize=32)
def _reference_spans(text):
    return tuple(_uncached_references(text))

def _references(text):
    return iter(_reference_spans(text))


def _changes(text):
    return [m for m in CHANGE.finditer(text) if not re.search(r"\bas\s+$", text[max(0, m.start() - 8):m.start()], re.I)]


def _historical_amender(text, offset):
    return bool(re.search(r"\bas\s+amended\s+by(?:(?!;|\n\s*\(\s*[a-z]\s*\)).){0,150}\Z", text[max(0, offset - 170):offset], re.I | re.S))


def _list_instruction(text, ref, body_start=0, body_end=None):
    """Locate a governing multiline change list, without repairing its text."""
    section = [h for h in HEADING.finditer(text, body_start, ref[1]) if h["section"]]
    start = section[-1].start() if section else max(body_start, _paragraph_start(text, ref[1]))
    before = text[start:ref[1]]
    intro = re.search(r"\bfollowing\b[^:]{0,800}\b(?:are|is)\s+(?:hereby\s+)?(?:revoked|superseded|amended|abolished|terminated)\s*:", before, re.I | re.S)
    if not intro:
        return None
    intro_end = start + intro.end()
    items = [h for h in HEADING.finditer(text, intro_end, body_end or len(text)) if h["sub"] or h["item"] or h["section"]]
    next_item = next((h.start() for h in items if h.start() > ref[1]), body_end or _body_end(text, body_start))
    return start, next_item, intro[0]


def _effective(text, provision, signing_date, filing_date, body_start=0, body_end=None):
    spans = []
    for a, b in ((body_start + a, body_start + b) for a, b in _sentences(text[body_start:body_end])):
        s = text[a:b]
        if re.search(r"\b(?:effective|take\s+effect|takes\s+effect|in\s+effect|upon\s+(?:signing|signature))\b", s, re.I):
            spans.append({"text": s, "char_start": a, "char_end": b})
    if not spans:
        return spans, "on_signing", None, "No express effective wording found; on_signing is an unconfirmed lead assumption; signing date is not asserted as an exact effective date."
    wording = "\n".join(s["text"] for s in spans)
    if re.search(r"\b(?:pay\s+period|with\s+respect\s+to\s+(?:any|each)\s+agency|as\s+(?:the\s+)?(?:Secretary|Director|agency).{0,60}(?:determine|prescribe)|upon\s+(?:approval|publication|completion))\b", wording, re.I | re.S):
        return spans, "agency_variable", None, "Effective date depends on agency, publication or an unstated event."
    relative = re.search(r"(" + NUMBER + r")\s+(?:calendar\s+)?(days?|weeks?|months?|years?)\s+after\s+(?:the\s+)?(" + DATE + r"|date\s+of\s+(?:this\s+order|signing|signature|filing)|signing|signature|filing)", wording, re.I)
    if relative:
        base_word = relative[3]
        base = _date(base_word)
        if not base and re.search(r"filing", base_word, re.I):
            base = filing_date
        elif not base and re.search(r"signing|signature|this\s+order", base_word, re.I):
            base = signing_date
        return spans, "relative", _add_term(base, relative[1], relative[2]) if base else None, "Relative date candidate uses only an expressly named base and term; confirm applicability."
    if re.search(r"\b(?:upon\s+(?:signing|signature)|effective\s+immediately|effective\s+(?:upon|on)\s+(?:the\s+)?date\s+of\s+(?:this\s+order|signing))", wording, re.I):
        return spans, "on_signing", signing_date or None, "Express signing-date wording; supplied signing date still needs source confirmation."
    # An explicitly dated global effectiveness sentence is needed. Multiple or
    # section-specific dates remain unresolved rather than leaking across scopes.
    dates = []
    dated_effect = r"\b(?:effective(?:\s+(?:as\s+of|on(?:\s+and\s+after)?|from))?|take[s]?\s+effect\s+(?:on(?:\s+and\s+after)?|as\s+of)|in\s+effect\s+(?:on|from))\s+(" + DATE + ")"
    for span in spans:
        if re.search(dated_effect, span["text"], re.I):
            match = re.search(dated_effect, span["text"], re.I)
            specific = bool(re.search(r"\b(?:section|subsection|paragraph)\s+[\d(]|\bthis\s+(?:section|subsection|paragraph)\b", span["text"], re.I))
            if not specific or span["text"] == provision:
                dates.append(_date(match[1]))
    if dates and None not in dates and len(set(dates)) == 1:
        return spans, "stated_date", dates[0], "Express effective-date candidate; agent must confirm it reaches this provision."
    return spans, "unknown", None, "Effective wording is ambiguous, section-specific, or has no determinable date."


def acting_provision(target_id, actor_id, text, source, signing_date=None, filing_date=None, parent_id=None):
    """Locate an explicit target or explicitly supplied parent-as-amended lead.

    None means no printed reference. A named reference without a change provision
    remains an incomplete record with empty quote and explicit gap, never a quote
    reconstructed from a disposition table.
    """
    body_start, body_end = _extent(actor_id, text)
    refs = [r for r in _references(text) if body_start <= r[1] < body_end]
    chosen = [r for r in refs if r[0] == target_id and not _historical_amender(text, r[1])]
    via = False
    if not chosen and parent_id:
        chosen = [r for r in refs if r[0] == parent_id and re.search(r"\bas\s+amended\b", text[r[2]:r[2] + 100], re.I)]
        via = bool(chosen)
    if not chosen:
        return None
    sentences = [(body_start + a, body_start + b) for a, b in _sentences(text[body_start:body_end])]
    list_context = next((context for r in chosen if (context := _list_instruction(text, r, body_start, body_end))), None)
    candidates = [(list_context[0], list_context[1])] if list_context else [(a, b) for a, b in sentences if any(a <= r[1] < b for r in chosen) and _changes(text[a:b])]
    # Lists often put the change instruction in the enclosing section header.
    if not candidates:
        for clause in segment(actor_id, text, source)["clauses"]:
            if any(clause["char_start"] <= r[1] < clause["char_end"] for r in chosen) and _changes(clause["text"]):
                candidates.append((clause["char_start"], clause["char_end"]))
    if not candidates:
        # A list can place 'are revoked:' before many sentence-separated items.
        # Quote the instruction and the item as one contiguous source span.
        for ref in chosen:
            before = text[:ref[1]]
            instruction = list(re.finditer(r"(?im)^.*\b(?:following|listed|enumerated)\b[^\n]*\b(?:revoked|superseded|amended|abolished|terminated)\s*:\s*", before))
            instruction = [i for i in instruction if i.start() >= body_start]
            if instruction:
                intro = instruction[-1]
                intervening = before[intro.end():]
                if not re.search(r"(?im)^\s*(?:Sec(?:tion)?\.?\s+\d|THE WHITE HOUSE|EXECUTIVE ORDER\s+\d)", intervening):
                    end = next((y for x, y in sentences if x <= ref[1] < y), ref[2])
                    candidates.append((intro.start(), end))
    a, b = candidates[0] if candidates else (None, None)
    provision = text[a:b] if a is not None else ""
    changes = _changes(provision)
    # Prefer a change verb following the printed target. This avoids picking a
    # historical descriptor ('amended') ahead of 'is revoked'.
    local_ref = next((r for r in chosen if a is not None and a <= r[1] < b), None)
    following = [m for m in changes if local_ref and m.start() + a >= local_ref[2] and not re.search(r"as\s+$", provision[max(0, m.start() - 4):m.start()], re.I)]
    change = (changes[-1] if list_context else (following or changes)[0]) if changes else None
    if list_context:
        # Historical 'as amended by EO...' inside an item must not displace
        # the governing 'are revoked:' instruction.
        governing_end = list_context[2].rfind(":")
        governing = list(CHANGE.finditer(list_context[2][:governing_end]))
        if governing:
            word = governing[-1][0].lower()
        else:
            word = ""
    else:
        word = change[0].lower() if change else ""
    verb = next((name for prefix, name in [("revok", "revoke"), ("rescind", "revoke"), ("supersed", "supersede"), ("amend", "amend"), ("transfer", "transfer"), ("abolish", "abolish"), ("terminat", "terminate")] if word.startswith(prefix)), "other")
    negated = bool(change and re.search(r"\b(?:not|never)\b", provision[max(0, change.start() - 25):change.start()], re.I))
    if negated:
        verb = "other"
    exceptions = [m[0] for m in re.finditer(r"\b(?:except\b[^.;]+|provided\s+(?:that|however)[^.;]+|insofar\s+as[^.;]+|to\s+the\s+extent[^.;]+)", provision, re.I)]
    scope_wording = re.sub(r"^\s*(?:Sec(?:tion)?\.?\s+\d+[A-Za-z]?[.):]\s*)", "", provision, flags=re.I)
    partial = bool(exceptions or re.search(r"\b(?:section|subsection|paragraph|item|part|schedule)\s+(?:\d|\(|[IVX]+\b)", scope_wording, re.I) or verb == "amend")
    savings = [text[x:y] for x, y in sentences if re.search(r"\b(?:shall\s+not\s+(?:affect|impair)|without\s+(?:affecting|prejudice)|pending\s+(?:proceedings|matters|actions)|rights?\s+(?:accrued|vested)|savings?|remain\s+in\s+(?:full\s+)?force|continue\s+in\s+effect)\b", text[x:y], re.I)]
    effective, effective_class, effective_date, date_note = _effective(text, provision, signing_date, filing_date, body_start, body_end)
    notes = ["Machine lead only; no legal ending asserted.", date_note]
    if not candidates:
        notes.append("MISSING_CHANGE_PROVISION: printed reference found, but no change provision located; quote and offsets intentionally empty.")
    if len(candidates) > 1:
        notes.append("MULTIPLE_PROVISIONS: first located provision quoted; additional provisions require review.")
    if via:
        notes.append("Parent-as-amended reach is a lead only; target membership and exceptions require confirmation.")
    if negated:
        notes.append("NEGATED_CHANGE_WORDING: no change event inferred from the negative predicate.")
    return {"id": "ACT:" + target_id + ">" + actor_id, "target_id": target_id, "actor_id": actor_id, "actor_source": source, "provision_label": next((h.group().strip() for h in reversed(list(HEADING.finditer(text[:a or 0]))) if h["section"]), ""), "provision_text": provision, "char_start": a, "char_end": b, "verb": verb, "scope": "partial" if partial else "whole_via_parent" if via else "whole", "names_target": not via, "reaches_target_via": parent_id + " as amended" if via else "", "signing_date": signing_date, "filing_date": filing_date, "effective_wording": effective, "effective_class": effective_class, "effective_date": effective_date, "exceptions_text": exceptions, "savings_phrases": savings, "confidence": "medium" if candidates else "low", "notes": " ".join(notes)}


def discover_mentions(actor_id, text, source, signing_date=None, filing_date=None):
    """One pass over actor text; caller must filter printed IDs to its census."""
    result = []
    start, end = _extent(actor_id, text)
    for target in sorted({r[0] for r in _references(text) if start <= r[1] < end}):
        if target != actor_id:
            record = acting_provision(target, actor_id, text, source, signing_date, filing_date)
            if record and record["provision_text"]:
                result.append(record)
    return result


def generic_reference_count(text):
    """Count unassigned generic change wording, never attach it to a target."""
    iid = re.search(r"(?m)^Instrument:\s*(EO:[^\s]+)", text)
    start, end = _extent(iid[1], text) if iid else (0, len(text))
    return sum(bool(CHANGE.search(text[start + a:start + b]) and re.search(r"\ball\s+(?:prior\s+|previous\s+|executive\s+)?orders?\b|\borders?\s+inconsistent\b", text[start + a:start + b], re.I)) for a, b in _sentences(text[start:end]))


def chain(target_id, acting_records, generic_refs_excluded=0):
    events = []
    records = [r for r in acting_records if r.get("target_id") == target_id and r.get("scope") != "generic" and r.get("provision_text") and r.get("verb") != "other"]
    for r in sorted(records, key=lambda r: (r.get("signing_date") or "9999-99-99", r["actor_id"], r.get("char_start") or 0)):
        sections = [m[0] for m in re.finditer(r"\b(?:sections?|subsections?|paragraphs?|items?|parts?|schedule)\s+[\dIVX]+(?:\([a-z0-9]+\))*", r["provision_text"], re.I)]
        events.append({"id": "CHAIN:" + target_id + "#" + str(len(events) + 1), "actor_id": r["actor_id"], "signing_date": r.get("signing_date"), "verb": r["verb"], "how_named": "direct" if r["names_target"] else "parent_as_amended", "sections_touched": sections or [r["scope"]], "provision_text": r["provision_text"], "char_start": r["char_start"], "char_end": r["char_end"], "source": r["actor_source"], "confidence": r.get("confidence", "medium"), "notes": "Change wording lead; chronology does not decide legal effect."})
    return {"id": "CHAIN:" + target_id, "target_id": target_id, "events": events, "generic_refs_excluded": generic_refs_excluded, "confidence": "medium", "notes": "Named, located change provisions only; missing provisions and unheld texts remain dossier gaps. Undated events sort last."}
