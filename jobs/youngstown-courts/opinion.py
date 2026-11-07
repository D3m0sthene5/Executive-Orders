"""Opinion-level class: carry an order's identity forward to "the Order", "the Executive Order", "Section 2(c) of the
Order", "this seizure order" and classify the holding sentences found there. Standard library only.

The sentence-level class (scan.classify_mention) looks only at the sentence that prints the number. A court usually
states what it did about an order in sentences that say "the Order" (Reich: "the Order conflicts with the National
Labor Relations Act, and therefore we reverse"). This module binds those references to the order, then classifies them
with the same cue rules, and records the sentence and span that decided the class. Still a lead, never a status.

Binding rule. Walk the opinion in text order. A printed order number makes that order "active"; a list or range of
numbers leaves none active. A reference binds to the active order. Another order number rebinds, and another instrument
(a Proclamation, Public Law, a numbered "Exclusion Order No. 34", a Memorandum, a Reorganization Plan) deactivates, so
a reference after either never belongs to the first order.
"""
from __future__ import annotations

import re
from collections import defaultdict

import scan

OPINION_VERSION = "youngstown-opinion-1"

_BLACK = re.compile(r"court|judge|stay|restrain|injunct|remand|schedul|dismiss|mandate|trial|circuit|panel|magistrate|"
                    r"\bTRO\b|board|commission|agency|clerk|arbitrat|bankruptcy", re.I)
ANAPHOR_RE = re.compile(r"\b(?:[Tt]he|[Tt]his|[Tt]hat|[Ss]aid|[Ss]uch)\s+((?:[\w'’-]+\s+){0,2}?)"
                        r"(Executive\s+[Oo]rder|executive\s+order|Order|order)\b(?!\s+(?:No|Nos)\.?\s*\d)")
FORWARD_CHARS = 6000  # a reference before the order's number binds forward only this far
OTHER_RE = re.compile(r"\b(?:Civilian\s+)?Exclusion\s+Order\s+(?:No|Nos)\.?\s*\d+|\bProclamations?\s+(?:No|Nos)?\.?\s*\d+|"
                      r"\bPub(?:lic|\.)?\s*L(?:aw|\.)\s*(?:No\.?\s*)?\d|\bPublic\s+Land\s+Order|\bPresidential\s+Memorand(?:um|a)\b|"
                      r"\bReorganization\s+Plan\b|\bPresident\s+[A-Z][a-z]+['\u2019]s\s+(?:[Ee]xecutive\s+[Oo]rder|order)|\b(?:[A-Z][a-z]+\s+){1,3}Order\s+(?:No|Nos)\.?\s*\d+")


def _anaphors(text):
    """[(start, end)] of references that can stand for an executive order."""
    out = []
    for m in ANAPHOR_RE.finditer(text):
        mods, head = m.group(1), m.group(2)
        if _BLACK.search(mods) or re.search(r"(?i)\bexecutive\b", mods):
            continue
        if head == "order" and not mods.strip():
            continue  # a bare "the order" is usually a court's order
        if head == "order" and re.search(r"(?i)\b(?:of|in|by|to|and|or|that|which|whose)\b", mods):
            continue
        out.append((m.start(), m.end()))
    return out


def references(text, mentions):
    """{(number, suffix): [(start, end)]} of references bound to each order, from scan.eo_mentions(text)."""
    events = []
    spans = [(m["start"], m["end"]) for m in mentions]
    for i, m in enumerate(mentions):
        events.append((m["start"], 0, i, "eo", m))
    others = []
    for m in OTHER_RE.finditer(text):
        if not any(a <= m.start() < b for a, b in spans):
            events.append((m.start(), 0, 0, "other", None))
            others.append((m.start(), m.end()))
    for a, b in _anaphors(text):
        if not any(sa <= a < sb for sa, sb in spans) and not any(a < ob and oa < b for oa, ob in others):
            events.append((a, 1, 0, "ref", (a, b)))
    events.sort(key=lambda e: (e[0], e[1], e[2]))
    active, out = None, defaultdict(list)
    pending, first_seen = [], False  # references before the first printed number ("the Order ... Executive Order No. N")
    for pos, _, _, kind, payload in events:
        if kind == "eo":
            if payload["in_list"] or payload["range"]:
                active, pending = None, []
            else:
                active = (payload["number"], payload["suffix"])
                if not first_seen and pending and pos - pending[0][0] <= FORWARD_CHARS:
                    out[active].extend(pending)
                pending = []
            first_seen = True
        elif kind == "other":
            active, pending = None, []
        elif active is not None:
            out[active].append(payload)
        elif not first_seen:
            pending.append(payload)
    return out


# Cues that name a court's act (enjoined, vacated, upheld) count on their own. Cues that only describe the order
# (unlawful, invalid, conflicts with, valid) are often a party's claim or a statement of law, so at opinion level they
# count only in a sentence that has the court speaking (we hold, the court concluded, ...) and no argument frame anywhere.
WEAK_CUES = {"unlawful", "invalid", "exceeds_authority", "conflicts", "valid", "within_authority", "meaning_scope", "applies_to"}
WEAK_INTERPRETIVE = {"meaning_scope", "applies_to"}
_FRAME = re.compile(r"\b(?:we|the\s+court|this\s+court|the\s+majority|the\s+panel|(?:justice|judge)\s+\w+)\b[^.;]{0,120}?"
                    r"\b(?:hold|held|holds|conclude|concluded|concludes|find|found|reverse|reversed|affirm|affirmed|vacate|vacated|"
                    r"enjoin|enjoined|uphold|upheld|sustain|sustained|rule|ruled|decide|decided|determine|determined)\b"
                    r"|\b(?:we|court)\s+(?:therefore|accordingly|thus|also)?\s*(?:hold|conclude|reverse|affirm|vacate)\b", re.I)
_ARG_SENT = re.compile(r"\b(?:argu(?:e|es|ed|ing|ment|ments)|contend(?:s|ed|ing)?|claimed|claiming|alleg(?:e|es|ed|ing|ation|ations)|"
                       r"assert(?:s|ed|ing)?|attack(?:s|ed|ing)?|challeng(?:e|es|ed|ing)|whether|seek(?:s|ing)?|sought|urg(?:e|es|ed)|"
                       r"request(?:s|ed|ing)?|motions?|moved|petition(?:s|ed|ing)?|fear|suggest(?:s|ed)?|maintain(?:s|ed)?)\b", re.I)
# Holding verbs the sentence-level rules leave out because they are common in plain description; counted only with the frame.
_EXTRA_UPHELD = re.compile(r"\b(?:was|were|is|are)\s+(?:fully\s+|clearly\s+)?(?:authorized|empowered)\s+(?:to|by|under)\b|"
                           r"\bhad\s+(?:the\s+)?(?:power|authority)\s+to\b|\bacted\s+(?:lawfully|within)\b", re.I)


def adjust(text, r, a, b):
    """Opinion-level reading of one sentence-level result r: a descriptive cue needs the court speaking and no argument
    words in the sentence; a frame plus an authority phrase is upheld. Returns (class, cue, cue_text, flag)."""
    lo, hi = r["sentence_span"]
    sent = text[lo:hi]
    framed = bool(_FRAME.search(sent))
    cls, cue, cue_text = r["class"], r["cue"], r["cue_text"]
    if cls in ("enjoined_vacated_invalidated", "upheld") and cue in WEAK_CUES:
        if not framed or _ARG_SENT.search(sent):
            return "mentioned", cue, cue_text, "weak_cue_without_court_voice"
    if cls == "interpreted" and cue in WEAK_INTERPRETIVE and (not framed):
        return "mentioned", cue, cue_text, "interpretive_cue_without_court_voice"
    if cls == "interpreted" and _ARG_SENT.search(sent):
        return "mentioned", cue, cue_text, "interpretive_cue_in_argument"
    if cls in ("mentioned", "interpreted") and framed and not _ARG_SENT.search(sent):
        m = _EXTRA_UPHELD.search(sent)
        if m:
            return "upheld", "authorized", m.group(0), "authority_phrase_with_court_voice"
    return cls, cue, cue_text, ""


def opinion_class(text, mention_pairs, ref_spans):
    """Class of one (order, opinion) pair. mention_pairs: [(mention, classify_mention result)] for the order's printed
    numbers; ref_spans: its bound references. The strongest class among all of them decides (holding words beat
    interpretive ones); ties go to a printed number, then to the earlier sentence. Returns the decider's sentence span
    and cue, how many references were bound, and whether enjoin/vacate/invalid and uphold cues both appear."""
    cands = []
    for m, r in mention_pairs:
        cands.append(("mention", m["start"], m["end"], r))
    for a, b in ref_spans:
        cands.append(("reference", a, b, scan.classify_mention(text, a, b)))
    best, best_key = None, None
    families = set()
    for via, a, b, r in cands:
        cls, cue, cue_text, flag = adjust(text, r, a, b)
        if cls in ("enjoined_vacated_invalidated", "upheld"):
            families.add(cls)
        key = (scan.RANK[cls], via == "mention", -a)
        if best_key is None or key > best_key:
            best, best_key = (via, a, b, dict(r, **{"class": cls, "cue": cue, "cue_text": cue_text})), key
    if best is None:
        return {"class": "mentioned", "via": "", "a": -1, "b": -1, "sent": [0, 0], "cue": "", "cue_text": "",
                "references": len(ref_spans), "conflict": False, "version": OPINION_VERSION}
    via, a, b, r = best
    return {"class": r["class"], "via": via, "a": a, "b": b, "sent": list(r["sentence_span"]), "cue": r["cue"],
            "cue_text": r["cue_text"], "references": len(ref_spans), "conflict": len(families) == 2,
            "version": OPINION_VERSION}


def classify_opinion(text):
    """{(number, suffix): opinion_class dict} for every order number printed in the text (registered or not).
    Used by the controls on opinion skeletons and by tests; the job calls the pieces from analyze.analyze_text."""
    ments = scan.eo_mentions(text)
    refs = references(text, ments)
    by = defaultdict(list)
    for m in ments:
        by[(m["number"], m["suffix"])].append(m)
    out = {}
    for key, ms in by.items():
        pairs = [(m, scan.classify_mention(text, m["start"], m["end"])) for m in ms[:40]]
        out[key] = opinion_class(text, pairs, refs.get(key, []))
    return out


def skeleton(text):
    """The opinion cut down to the sentences that matter to the binding rule, in order, one paragraph each: every
    sentence with an order number, another instrument, or a possible reference. The job's result on the skeleton
    equals its result on the whole text (checked when a fixture is built), so a control can be committed without
    committing the opinion."""
    ments = scan.eo_mentions(text)
    marks = [(m["start"], m["end"]) for m in ments]
    marks += [(m.start(), m.end()) for m in OTHER_RE.finditer(text)]
    marks += _anaphors(text)
    seen, out = set(), []
    for a, b in sorted(marks):
        lo, hi = scan.sentence_bounds(text, a, b)
        if (lo, hi) not in seen:
            seen.add((lo, hi))
            out.append(re.sub(r"[ \t]*\n[ \t]*", " ", text[lo:hi]).strip())
    return "\n\n".join(x for x in out if x)
