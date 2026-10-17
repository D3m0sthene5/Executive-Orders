"""Find executive-order references in plain legal text (no network, no I/O).

Everything here is pure text handling so it can be unit tested with small
strings. The results are LEADS: a regex hit is not proof that a law relies on
an order, only that the text names it.
"""

import html
import re
from datetime import date

LEGAL_CUTOFF = "2026-10-14"

# ---------------------------------------------------------------- patterns --
# Words that introduce an executive-order number. Order matters only for
# readability; all are tried at every position.
_PREFIX = r"""(?:
      Ex\.\s*Ords?\.\s*(?:Nos?\.|Numbered|Numbers?)?
    | Exec(?:utive|\.)\s+Orders?\s*(?:Nos?\.|Numbered|Numbers?)?
    | E\.\s?O\.s?(?:\s*Nos?\.)?
    | \bEOs?(?:\s*Nos?\.)?
)"""
# One order number, optionally with a letter suffix written 10026-A / 10026A.
_NUM = r"(\d{1,5})(?!\d)(?![-–—/.]\d)(?:\s?[-–—]\s?([A-Z])\b|([A-Za-z])(?![A-Za-z]))?(?![\d,]\d)(?!\s*\(\d{4}\))"
# Later numbers in a list ("Nos. 10450 and 10491", "12866, 13563, and 13771").
# A list item needs 3+ digits and must not be a page/volume/year citation.
_LIST_ITEM = r"(?:\s*,\s*(?:and\s+|or\s+)?|\s+(?:and|or|through|to)\s+)(\d{3,5})(?!\d)(?:\s?[-–]\s?([A-Z])\b)?(?![\d,]\d)(?![-–—/.]\d)(?!\s*(?:Comp\b|F\.?\s?R\b|FR\b|Stat\b|U\.S\.C|CFR\b|C\.F\.R|Reorg|Plan\b|ed\.|edition))"

PREFIX_RE = re.compile(_PREFIX + r"\s*", re.VERBOSE | re.IGNORECASE)
FIRST_RE = re.compile(_NUM)
LIST_RE = re.compile(_LIST_ITEM, re.IGNORECASE)
# "E.O." / "EO" only count when written in capitals (avoid "eo" inside words);
# "Executive Order" may be any case.
_CAPS_ONLY = re.compile(r"^(?:E\.\s?O|EO)", re.IGNORECASE)

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "june": 6, "jun": 6,
    "july": 7, "jul": 7, "aug": 8, "sept": 9, "sep": 9, "oct": 10, "nov": 11,
    "dec": 12, "january": 1, "february": 2, "march": 3, "april": 4,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
DATE_RE = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(\d{1,2}),\s+(\d{4})\b"
)
FR_RE = re.compile(r"\b(\d{1,3})\s+F\.?\s?R\.?\s+(\d{1,6})\b")
PUBL_RE = re.compile(r"Pub\.\s*L\.\s*(\d{2,3})\s*[-–—]\s*(\d{1,4})")

# Editorial verbs that mean "this order stopped or changed".
END_VERBS = r"(revoked|superseded|rescinded|terminated|repealed|annulled|cancell?ed)"
END_RE = re.compile(r"\b(?:was|were|is|are|has\s+been|have\s+been|been)\s+(?:(?:\w+|\w+,)\s+){0,4}?" + END_VERBS + r"\b", re.IGNORECASE)
AMENDED_BY_RE = re.compile(r"\bas\s+amended\s+by\b", re.IGNORECASE)


def clean(text):
    """Collapse whitespace and unescape HTML entities."""
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def strip_tags(text):
    return clean(re.sub(r"<[^>]+>", " ", text or ""))


def find_eo_refs(text):
    """Return [{start, end, raw, number, suffix}] for every order number named.

    A list such as "Ex. Ord. Nos. 10450 and 10491" gives two hits that share
    the same prefix. Positions index into ``text``.
    """
    hits = []
    for pm in PREFIX_RE.finditer(text):
        word = pm.group(0)
        if _CAPS_ONLY.match(word) and not word.lower().startswith("ex"):
            if not re.match(r"E\.?\s?O", word):
                continue  # lower-case "e.o." / "eo": not a citation
            if pm.start() > 0 and (text[pm.start() - 1].isalnum() or text[pm.start() - 1] == "."):
                continue  # inside a word or another abbreviation ("GEO", "U.S.E.O")
        m = FIRST_RE.match(text, pm.end())
        if not m:
            continue
        suffix = (m.group(2) or m.group(3) or "")
        hits.append({"start": pm.start(), "end": m.end(), "raw": text[pm.start():m.end()],
                     "number": int(m.group(1)), "suffix": suffix})
        pos = m.end()
        while True:
            lm = LIST_RE.match(text, pos)
            if not lm:
                break
            hits.append({"start": lm.start(1), "end": lm.end(), "raw": text[lm.start(1):lm.end()].strip(),
                         "number": int(lm.group(1)), "suffix": lm.group(2) or ""})
            pos = lm.end()
    # A prefix can match twice ("Executive Order No." and "No."); keep first.
    seen, out = set(), []
    for h in sorted(hits, key=lambda h: h["start"]):
        key = (h["start"], h["number"])
        if key in seen or any(o["start"] <= h["start"] < o["end"] and o["number"] == h["number"] for o in out):
            continue
        seen.add(key)
        out.append(h)
    return out


class Universe:
    """Maps a cited number (+suffix) to an order id in the 14,972-order universe."""

    def __init__(self, ids, statuses=None):
        self.ids = set(ids)
        self.statuses = statuses or {}

    def map(self, number, suffix=""):
        """Return (instrument_id or "", how) where how explains the mapping."""
        base = f"EO:{number}"
        if suffix:
            for cand in (base + suffix.upper(), base + suffix.lower()):
                if cand in self.ids:
                    return cand, "exact_with_suffix"
            return "", f"suffix_not_in_universe(base {base}{' exists' if base in self.ids else ' absent'})"
        if base in self.ids:
            return base, "exact"
        return "", "number_not_in_universe"

    def status(self, instrument_id):
        return self.statuses.get(instrument_id, "")


def normalized(number, suffix=""):
    return f"{number}{suffix.upper()}" if suffix else str(number)


def parse_date(text):
    """First "Mon. D, YYYY" date in text -> ISO string, or None."""
    m = DATE_RE.search(text or "")
    if not m:
        return None
    month = MONTHS.get(m.group(1).lower().rstrip("."))
    try:
        return date(int(m.group(3)), month, int(m.group(2))).isoformat()
    except (TypeError, ValueError):
        return None


def parse_fr(text):
    m = FR_RE.search(text or "")
    return f"{m.group(1)} F.R. {m.group(2)}" if m else None


STATE_CONTEXT_RE = re.compile(r"\bGovernor\b|\bState of [A-Z]|\bCommonwealth\b|\bCounty\b|\bMayor\b|\bTrib(?:e|al)\b|\bParish\b")


def caution(text, start, end, width=150):
    """Flag a hit that is probably a State, local or tribal executive order."""
    window = text[max(0, start - width): end + width]
    if STATE_CONTEXT_RE.search(window):
        return "possible_state_local_or_tribal_order"
    return ""


def snippet(text, start, end, width=160):
    a, b = max(0, start - width), min(len(text), end + width)
    return ("..." if a else "") + clean(text[a:b]) + ("..." if b < len(text) else "")


# ------------------------------------------------------ sentence handling --
_ABBREV = re.compile(
    r"\b(?:Ex|Ord|Ords|No|Nos|Pub|L|Stat|F|R|U|S|C|Sec|Secs|Sept|div|Div|subdiv|Subdiv|tit|subd|subtit|Jan|Feb|Mar|Apr|Aug|Oct|Nov|Dec|Reorg|Proc|Comp|App|ch|Ch|pt|subch|E|O|Exec|Cong|Dept|Gen|Admin|Corp|Co|Inc|Mr|Dr|St|vol|par|cl|subpar|subsec|subsecs|pars|cls|v|Jr|Sr|Mt|Ft|Gov|Atty|Ass|Assn)\.",
)


def sentences(text):
    """Split on sentence ends, not on the dots of legal abbreviations."""
    protected = _ABBREV.sub(lambda m: m.group(0)[:-1] + "\x00", text)
    parts, pos = [], 0
    for m in re.finditer(r"(?:(?<=\.)|(?<=\.[”\"’)\]]))\s+(?=[A-Z\[(\"“])", protected):
        parts.append((pos, m.start()))
        pos = m.end()
    parts.append((pos, len(protected)))
    return [(a, b, text[a:b]) for a, b in parts if text[a:b].strip()]


STATUTE_WORDS_RE = re.compile(r"\b[Aa]ct\b|Pub\.\s*L\.|\bStat\.|\bprovided\s+that\b|\bCongress\b")
# "until they are superseded", "unless revoked", "if ... is terminated": a condition, not an event.
CONDITIONAL_RE = re.compile(r"\b(?:until|unless|if|whether|when|whenever)\s+(?:[\w,]+\s+){0,4}$", re.IGNORECASE)
REMAIN_RE = re.compile(r"\b(?:remains?|continues?)\s+in\s+(?:full\s+)?(?:force|effect)\b", re.IGNORECASE)
RELATIVE_RE = re.compile(r",?\s*\b(?:which|that)\s+(?:(?:in\s+turn|also|later|subsequently|itself),?\s+)?$", re.IGNORECASE)
# "... Executive Order 13519 and that order is hereby revoked": the order itself is the subject.
BACKREF_RE = re.compile(r"\b(?:(?:that|such|this|said)\s+(?:Executive\s+)?order|which)\b", re.IGNORECASE)
_SCOPE_WORDS = (r"(?:sections?|secs?\.|§§?|par(?:agraph)?s?\.?|parts?|provisions?|subsections?|subsecs?\.|clauses?|"
                r"subpar(?:agraph)?s?\.?)")
# "Ex. Ord. No. 13047, ..., sections 1 to 7 of which were revoked by ..."
OF_WHICH_RE = re.compile(r",?\s*(" + _SCOPE_WORDS + r"\s[^,;]{0,40}?\s+of\s+which)\s+$", re.IGNORECASE)
# Words just before a subject reference that make the event a partial one:
# "Section 3 of Executive Order 13492", "The fifth and sixth paragraphs of Ex. Ord. No. 6073".
SUBJECT_SCOPE_RE = re.compile(r"(" + _SCOPE_WORDS + r"\s*[^;:\[\]]{0,70}?\s+of\s+(?:this\s+)?)$", re.IGNORECASE)
# "Executive Order No. 12163 is amended as follows: (a) Section 1-201(a)(14) is revoked.":
# a section label (or "is amended") between the order and the verb makes the ending partial.
VERB_SUBJECT_SCOPE_RE = re.compile(r"((?:\(\w+\)\s*)?\b" + _SCOPE_WORDS + r"\s*[\w().\-–]+(?:\s*(?:,|and|through|to)\s*[\w().\-–]+){0,3})"
                                   r"\s*,?\s*$", re.IGNORECASE)
AMENDED_AS_FOLLOWS_RE = re.compile(r"\bis\s+(?:hereby\s+)?(?:further\s+)?amended\b", re.IGNORECASE)
_SCOPE_LEAD_RE = re.compile(r"(?:(?:[Tt]he|and|or|first|second|third|last|\w+th|\(\w\))[,]?\s+){0,6}$")
QUALIFIED_RE = re.compile(r"^[^.;]{0,40}?\b(?:insofar\s+as|to\s+the\s+extent|in\s+part|except\b|so\s+far\s+as)",
                          re.IGNORECASE)
# "Civil Service Rule 9, as established by Executive Order No. 11315, ..., is revoked": the
# rule ended, not the order. Words right before the subject that make it the object of a phrase.
PREPOSITIONAL_RE = re.compile(
    r"\b(?:(?:established|created|issued|prescribed|designated|specified|authorized|provided|blocked|described|"
    r"set\s+aside|transferred|delegated)\s+(?:by|in|under|pursuant\s+to)|pursuant\s+to|under|by\s+means\s+of(?:\s+and\s+under)?|"
    r"in\s+compliance\s+with|in\s+accordance\s+with|implementing|referred\s+to\s+in|purposes\s+of)\s+"
    r"(?:(?:section|sec\.|§)\s*\S+\s+of\s+)?$", re.IGNORECASE)
ACTIVE_RE = re.compile(r"\b(?:hereby\s+)?(revokes|supersedes|rescinds|revoked|superseded|rescinded)\s+", re.IGNORECASE)


def subject_scope(text, ref):
    """Scope words right before a subject reference ("Section 3 of"), or ""."""
    pre = text[max(0, ref["start"] - 90):ref["start"]]
    m = SUBJECT_SCOPE_RE.search(pre)
    if not m:
        return ""
    lead = _SCOPE_LEAD_RE.search(pre[:m.start(1)])
    start = lead.start() if lead else m.start(1)
    return clean(pre[start:])


def _list_chain(refs, first):
    """The subject plus numbers listed with it ("Executive Orders 13354 and 13355")."""
    out, prev = [first], first
    for r in refs:
        if r["start"] <= prev["start"]:
            continue
        if r["raw"][:1].isdigit() and r["start"] - prev["end"] <= 12:
            out.append(r)
            prev = r
        else:
            break
    return out


def _actor_after(text, pos, refs):
    """Who acted, from the words after "... by": an order, a statute, or text."""
    tail = text[pos:pos + 160]
    m = re.match(r"\s*(?:\w+\s+){0,2}?by\b", tail)
    if not m:
        return None
    start = pos + m.end()
    for i, r in enumerate(refs):
        if start <= r["start"] <= start + 70:
            after = text[r["end"]:r["end"] + 90]
            actor = {"kind": "executive_order", "ref": r, "date": parse_date(after), "fr": parse_fr(after),
                     "scope_text": clean(text[start:r["start"]])}
            # "... by Ex. Ord. No. 12333, § 3.6, Dec. 4, 1981, ..., as amended by Ex. Ord. No. 13470, ..."
            seg = re.split(r";|\bset out\b", text[r["end"]:r["end"] + 140])[0]
            am = AMENDED_BY_RE.search(seg)
            if am:
                abs_pos = r["end"] + am.end()
                nxt = next((x for x in refs[i + 1:] if abs_pos <= x["start"] <= abs_pos + 30), None)
                if nxt:
                    a2 = text[nxt["end"]:nxt["end"] + 90]
                    actor["amended_by"] = {"kind": "executive_order", "ref": nxt, "date": parse_date(a2),
                                           "fr": parse_fr(a2), "scope_text": ""}
            return actor
    pm = PUBL_RE.search(text, start, start + 90)
    if pm:
        after = text[pm.end():pm.end() + 90]
        return {"kind": "statute", "publ": f"Pub. L. {pm.group(1)}-{pm.group(2)}", "date": parse_date(after),
                "fr": None, "scope_text": clean(text[start:pm.start()])}
    rest = clean(text[start:start + 90])
    if re.match(r"(?:an?\s+|the\s+)?[Aa]ct\b", rest):
        return {"kind": "statute", "publ": None, "text": rest, "date": None, "fr": None, "scope_text": ""}
    return {"kind": "other", "text": rest, "date": None, "fr": None, "scope_text": ""}


def _statute_before(sent, end):
    """'Pub. L. 105-277 ... provided that ... Ex. Ord. No. X ... were repealed': a statute acted."""
    head = sent[:end]
    if not STATUTE_WORDS_RE.search(head):
        return None
    pubs = list(PUBL_RE.finditer(head))
    if pubs:
        pm = pubs[-1]
        return {"kind": "statute", "publ": f"Pub. L. {pm.group(1)}-{pm.group(2)}",
                "date": parse_date(head[pm.end():pm.end() + 90]), "fr": None, "scope_text": "",
                "basis": "statute named earlier in the sentence"}
    return {"kind": "statute", "publ": None, "text": "an Act of Congress described in the sentence",
            "date": None, "fr": None, "scope_text": "", "basis": "statute named earlier in the sentence"}


def editorial_events(text):
    """Find "Ex. Ord. No. X ... was revoked by Ex. Ord. No. Y" style statements.

    Returns [{subject, verb, actor, sentence, subject_scope, qualified}].
    The subject is normally the first order named in the sentence before the
    verb (that is how the Office of the Law Revision Counsel writes these
    lines); after "..., which was revoked" it is the order nearest before
    "which". ``actor`` describes who acted (an order, a statute, other text),
    or is None when nobody is named. Conditions such as "shall remain in
    effect until they are superseded" are skipped. A list subject
    ("Executive Orders 13354 and 13355 ... are revoked") gives one event each.
    """
    out = []
    for a, b, sent in sentences(text):
        refs = find_eo_refs(sent)
        if not refs:
            continue
        for vm in END_RE.finditer(sent):
            before = [r for r in refs if r["end"] <= vm.start()]
            if not before:
                continue
            pre = sent[:vm.start()]
            if CONDITIONAL_RE.search(pre[-60:]) or REMAIN_RE.search(pre[-160:]):
                continue
            scope_extra, context = "", ""
            ow = OF_WHICH_RE.search(pre)
            if ow:
                cands = [r for r in before if r["end"] <= ow.start()]
                subject = cands[-1] if cands else before[0]
                scope_extra = clean(ow.group(1))
            elif RELATIVE_RE.search(pre):
                subject = before[-1]
            else:
                subject = before[0]
                between = sent[subject["end"]:vm.start()]
                later_refs = [r for r in before if r["start"] > subject["start"] and not r["raw"][:1].isdigit()]
                if (PREPOSITIONAL_RE.search(sent[max(0, subject["start"] - 60):subject["start"]])
                        and not (BACKREF_RE.search(between) and not later_refs)):
                    context = "subject_inside_prepositional_phrase"
            actor = _actor_after(sent, vm.end(), [r for r in refs if r["start"] >= vm.end()])
            if actor is None:
                actor = _statute_before(sent, vm.start())
            qualified = bool(QUALIFIED_RE.search(sent[vm.end():vm.end() + 120]))
            if not scope_extra and not RELATIVE_RE.search(pre):
                between = sent[subject["end"]:vm.start()]
                vs = VERB_SUBJECT_SCOPE_RE.search(between[-70:])
                if vs and not [r for r in before if r["start"] > subject["end"] and not r["raw"][:1].isdigit()]:
                    scope_extra = clean(vs.group(1))
                elif AMENDED_AS_FOLLOWS_RE.search(between):
                    scope_extra = "part of the order (the sentence amends the order)"
            for s in _list_chain(before, subject):
                out.append({"subject": s, "verb": vm.group(1).lower(), "actor": actor, "sentence": clean(sent),
                            "subject_scope": scope_extra or subject_scope(sent, subject), "qualified": qualified,
                            "context": context})
    return out


def active_events(text):
    """Active-voice endings: "Executive Order 12356, which superseded E.O. 12065"
    and "This order supersedes Executive Order 13560 ...".

    Returns [{subject, verb, actor, self_ref, sentence, subject_scope, qualified}];
    ``actor`` is the order named just before "which"/"that", else None;
    ``self_ref`` is True when the sentence says "this order" does it.
    """
    out = []
    for a, b, sent in sentences(text):
        refs = find_eo_refs(sent)
        if not refs:
            continue
        for vm in ACTIVE_RE.finditer(sent):
            first = next((r for r in refs if vm.end() <= r["start"] <= vm.end() + 4), None)
            if not first:
                continue
            pre = sent[:vm.start()]
            if CONDITIONAL_RE.search(pre[-60:]) or re.search(r"\b(?:is|are|was|were|be|been)\s+$", pre):
                continue
            actor, self_ref = None, False
            if re.search(r"\b(?:which|that)\s+(?:also\s+|has\s+|had\s+)?$", pre, re.IGNORECASE):
                prior = [r for r in refs if r["end"] <= vm.start()]
                if prior:
                    r = prior[-1]
                    after = sent[r["end"]:r["end"] + 90]
                    actor = {"kind": "executive_order", "ref": r, "date": parse_date(after), "fr": parse_fr(after),
                             "scope_text": ""}
            elif re.search(r"\b[Tt]his\s+(?:order|Order)\b[^.;]{0,40}$", pre):
                self_ref = True
            qualified = bool(QUALIFIED_RE.search(sent[vm.end():vm.end() + 160]))
            verb = vm.group(1).lower()
            verb = {"revokes": "revoked", "supersedes": "superseded", "rescinds": "rescinded"}.get(verb, verb)
            for s in _list_chain(refs, first):
                out.append({"subject": s, "verb": verb, "actor": actor, "self_ref": self_ref, "sentence": clean(sent),
                            "subject_scope": "", "qualified": qualified})
    return out


def ended_subject_keys(text):
    """(number, SUFFIX) of every order the text says was revoked, superseded, etc."""
    return {(e["subject"]["number"], e["subject"]["suffix"].upper())
            for e in editorial_events(text) + active_events(text)
            if e["verb"] != "amended" and not e.get("context")}


def make_event(e, base, actor_fallback=None):
    """Scanner event record (consumed by build.Book.add_event)."""
    actor = e.get("actor") or actor_fallback
    rec = dict(base, subject_number=e["subject"]["number"], subject_suffix=e["subject"]["suffix"],
               subject_raw=e["subject"]["raw"], verb=e["verb"], actor=actor, sentence=e["sentence"])
    if e.get("subject_scope"):
        rec["subject_scope"] = e["subject_scope"]
    if e.get("qualified"):
        rec["qualified"] = True
    if e.get("context"):
        rec["context_caution"] = e["context"]
    return rec


BRACKET_RE = re.compile(r"\[\s*(Revoked|Superseded|Rescinded|Terminated)\s+by\s([^\]]{0,260})\]", re.IGNORECASE)


def bracket_events(text):
    """Editorial inserts such as "Sec. 3. [Revoked by Ex. Ord. No. 12345, ...]".

    Returns [{verb, actor, scope_text, sentence}]; the subject is the order
    whose text contains the bracket, which only the caller knows.
    """
    out = []
    for m in BRACKET_RE.finditer(text):
        inner = m.group(2)
        refs = find_eo_refs(inner)
        actor = None
        if refs:
            r = refs[0]
            after = inner[r["end"]:]
            actor = {"kind": "executive_order", "ref": r, "date": parse_date(after), "fr": parse_fr(after),
                     "scope_text": clean(inner[:r["start"]])}
        else:
            pm = PUBL_RE.search(inner)
            if pm:
                actor = {"kind": "statute", "publ": f"Pub. L. {pm.group(1)}-{pm.group(2)}",
                         "date": parse_date(inner[pm.end():]), "fr": None, "scope_text": ""}
        line_start = text.rfind(chr(10), 0, m.start()) + 1
        out.append({"verb": m.group(1).lower(), "actor": actor,
                    "scope_text": clean(text[max(line_start, m.start() - 120):m.start()]),
                    "sentence": clean(text[max(line_start, m.start() - 120):m.end()])})
    return out


def amendments_listed(status_line):
    """From "Ex. Ord. No. X, date, FR, as amended by A, date, FR; B, ..., provided:"
    return [{actor: {...}, segment}] for each amending instrument.

    Only the part before an ending verb counts: in "X ... was revoked by Y,
    as amended by Z" the amendment is of Y, not of X."""
    end = END_RE.search(status_line)
    if end:
        status_line = status_line[:end.start()]
    m = AMENDED_BY_RE.search(status_line)
    if not m:
        return []
    rest = status_line[m.end():]
    stop = re.search(r",\s*(?:provided|which|delegating|establishing|relating|related|was|were|is|are|set out|formerly)\b", rest)
    span = rest[:stop.start()] if stop else rest
    out = []
    for seg in re.split(r";", span):
        refs = find_eo_refs(seg)
        if refs:
            r = refs[0]
            after = seg[r["end"]:]
            out.append({"kind": "executive_order", "ref": r, "date": parse_date(after), "fr": parse_fr(after),
                        "segment": clean(seg)})
            continue
        pm = PUBL_RE.search(seg)
        if pm:
            out.append({"kind": "statute", "publ": f"Pub. L. {pm.group(1)}-{pm.group(2)}",
                        "date": parse_date(seg[pm.end():]), "fr": None, "segment": clean(seg)})
    return out


def status_line_kind(status_line):
    """Classify the first paragraph of an OLRC executive-order note."""
    low = status_line.lower()
    printed = bool(re.search(r"\bprovided\s*:", low))
    ended = bool(END_RE.search(status_line))
    if printed and not ended:
        return "printed_text"
    if ended:
        return "ended_status_line"
    return "status_or_cross_reference"
