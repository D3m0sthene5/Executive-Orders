"""Youngstown scan rules: find executive-order citations in a court opinion's text and classify the context.

Named for Youngstown Sheet & Tube Co. v. Sawyer, 343 U.S. 579 (1952), where the Supreme Court held EO 10340 unlawful.

Everything here is a transparent, versioned rule set (regular expressions, no model). A class is a LEAD for a
person to read, never a legal status of the order: "enjoined_vacated_invalidated" means the sentence near the
citation holds a word such as enjoin or vacate, not that a court held the order invalid.

Standard library only.
"""
from __future__ import annotations

import html
import re

DERIVE_VERSION = "derive-1"
SCAN_VERSION = "youngstown-scan-1"
CLASS_VERSION = "youngstown-class-1"

CLASSES = ("enjoined_vacated_invalidated", "upheld", "interpreted", "mentioned")
RANK = {"enjoined_vacated_invalidated": 3, "upheld": 2, "interpreted": 1, "mentioned": 0}

# ---- text derivation ----------------------------------------------------------------------------------------------

# CourtListener's opinion row carries up to eight text columns; the first non-empty one in this order is used.
TEXT_COLUMNS = ("plain_text", "html_with_citations", "html_lawbox", "html_columbia", "html_anon_2020", "html",
                "xml_harvard", "xml_scan")
_TAG = re.compile(r"<[^>]+>")
_BLOCK = re.compile(r"(?i)</?(?:p|div|br|li|ul|ol|h[1-6]|blockquote|tr|footnote|opinion|author|page-number)\b[^>]*>")
_SPACES = re.compile(r"[ \t\xa0  ]+")
_NEWLINES = re.compile(r"\n[ \t]*(?:\n[ \t]*)+")


def derive_text(raw: str, column: str) -> str:
    """The text the spans refer to. Plain text is kept; markup columns lose tags (block tags become newlines) and
    entities. Spaces collapse, three or more newlines become two. Deterministic, so a span can be re-found."""
    if column != "plain_text":
        raw = _BLOCK.sub("\n", raw)
        raw = _TAG.sub("", raw)
        raw = html.unescape(raw)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = _SPACES.sub(" ", raw)
    raw = _NEWLINES.sub("\n\n", raw)
    return raw.strip()


def pick_text(row: dict):
    """(column, raw_value) of the first non-empty text column of a CourtListener opinion row, else (None, '')."""
    for col in TEXT_COLUMNS:
        v = row.get(col)
        if v and v.strip():
            return col, v
    return None, ""


# ---- executive-order citations ------------------------------------------------------------------------------------

_NUM = r"(?:\d{1,2},\d{3}|\d{1,5})"
_NUMS = _NUM + r"(?:-?[A-Z](?![A-Za-z0-9]))?"
LEAD_RE = re.compile(
    r"(?:\b(?:Executive|Exec\.?|Ex\.?)\s+Ord(?:ers?|\.)(?=[\s,.(\d])|(?<![A-Za-z])E\.\s?O\.s?(?![A-Za-z])|(?<![A-Za-z])EOs?(?![A-Za-z]))",
    re.I)
# After the lead: optional "No./Nos./Number(s)/Numbered", then the first number.
_AFTER_LEAD = re.compile(r"\s*(?:,\s*)?(?:(?:Nos?|Numbers?|Numbered)\.?\s*)?(?P<first>" + _NUMS + r")")
# Continuation of a list: a separator and another number; short numbers after a bare comma are citation volumes
# ("12,954, 60 Fed. Reg. 13,023"), so a comma-only separator needs three or more digits.
_SEP = re.compile(r"\s*(?:(?P<rng>[-–—])|,\s*(?:(?P<and1>and|or)\s+)?|(?P<and2>\band\b|\bor\b|&)\s*(?:Nos?\.?\s*)?)\s*")
_CITE_WORD = re.compile(r"\s*(?:Fed\.?\s?Reg|F\.\s?R\.|FR\b|C\.\s?F\.\s?R|CFR\b|U\.\s?S\.|Stat\.|F\.\s?\d|F\.\s?Supp|S\.\s?Ct|L\.\s?Ed|"
                        r"Cal\.|Comp\.|Compilation|\(|\d{4}\b)", re.I)
MAX_RANGE = 30


def _to_int(tok: str) -> int:
    return int(tok.replace(",", ""))


def _split_suffix(tok: str):
    m = re.fullmatch(r"(\d{1,2},\d{3}|\d{1,5})(?:-?([A-Z]))?", tok)
    return (_to_int(m.group(1)), m.group(2) or "") if m else (None, "")


def eo_mentions(text: str):
    """[{start, end, number (int), suffix, form, in_list, range}] for each order number cited after an
    executive-order lead word ('Executive Order No. 10340', 'Exec. Order 12,954', 'E.O. 11246',
    'Executive Orders 10925 and 11246', 'Exec. Orders Nos. 12276-12285'). The span covers lead through number."""
    out = []
    for lead in LEAD_RE.finditer(text):
        m = _AFTER_LEAD.match(text, lead.end())
        if not m:
            continue
        form = "eo_abbrev" if re.match(r"(?i)E\.\s?O|EO", lead.group(0)) else (
            "executive_order" if lead.group(0).lower().startswith("executive") else "exec_order")
        n, suf = _split_suffix(m.group("first"))
        if n is None or n < 1:
            continue
        items = [(m.start("first"), m.end("first"), n, suf, False, False)]
        pos, prev = m.end("first"), n
        while True:
            s = _SEP.match(text, pos)
            if not s:
                break
            nxt = _AFTER_NUM(text, s.end())
            if not nxt:
                break
            tok_s, tok_e = nxt
            tok = text[tok_s:tok_e]
            n2, suf2 = _split_suffix(tok)
            if n2 is None or n2 < 1:
                break
            digits = len(tok.replace(",", "").rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ-"))
            if s.group("rng"):
                if suf or not (prev < n2 <= prev + MAX_RANGE):
                    break
                for k in range(prev + 1, n2 + 1):
                    items.append((tok_s, tok_e, k, "", True, True))
            else:
                bare_comma = not (s.group("and1") or s.group("and2"))
                if digits < (3 if bare_comma else 2) or _CITE_WORD.match(text, tok_e):
                    break
                items.append((tok_s, tok_e, n2, suf2, True, False))
            pos, prev, suf = tok_e, n2, suf2
        for (a, b, num, sf, in_list, is_range) in items:
            out.append({"start": lead.start(), "end": b, "number": num, "suffix": sf, "form": form,
                        "in_list": in_list, "range": is_range})
    return out


def _AFTER_NUM(text, pos):
    m = re.compile(_NUMS).match(text, pos)
    return (m.start(), m.end()) if m else None


# ---- signals and sentence bounds ----------------------------------------------------------------------------------

FEDERAL_RE = re.compile(r"\bPresident(?:ial|'s|s')?\b|\bFed\.?\s?Reg|\bF\.\s?R\.\s?\d|\b\d+\s*F\.\s?R\.\b|\bC\.\s?F\.\s?R\b|\bCFR\b|"
                        r"\bU\.\s?S\.\s?C\b|\bStat\.\s|\bProclamation\b|\bFederal\s+Register\b|\bSecretary\s+of\b", re.I)
STATE_RE = re.compile(r"\bGovernor\b|\bGubernatorial\b|\bMayor\b|\bLt\.?\s+Gov|\bLieutenant\s+Governor\b|\bCounty\s+Executive\b", re.I)
_ABBR = {"no", "nos", "sec", "secs", "fed", "reg", "regs", "v", "vs", "co", "corp", "inc", "ltd", "mr", "mrs", "ms", "dr", "st", "ed",
         "cir", "ct", "supp", "app", "stat", "cong", "sess", "dept", "gov", "gen", "sen", "rep", "pub", "pl", "ex", "rel", "al",
         "cf", "ibid", "id", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sept", "sep", "oct", "nov", "dec", "u", "s", "c", "f", "r", "d", "e", "o",
         "ch", "art", "cl", "para", "p", "pp", "vol", "div", "dist", "am", "pa", "ill", "cal", "mass", "wash", "tex", "mich", "ala"}
_TERM = re.compile(r"([.?!])[\"'”’)\]]*\s+(?=[\"'“‘(\[]*[A-Z])|(?<=[.?!:;\"”’)\]])[ \t]*\n\s*\n")


def _is_abbrev(text, dot_index):
    m = re.search(r"([A-Za-z]+)$", text[max(0, dot_index - 12):dot_index])
    return bool(m) and (m.group(1).lower() in _ABBR or len(m.group(1)) == 1)


def sentence_bounds(text: str, start: int, end: int, limit: int = 700):
    """(lo, hi) of the sentence holding text[start:end]; abbreviation periods (No., Fed. Reg., v., U.S.) do not end
    one, a blank line does."""
    lo, hi = max(0, start - limit), min(len(text), end + limit)
    s = lo
    for m in _TERM.finditer(text, lo, min(len(text), start + 1)):
        if m.end() <= start and not (m.group(1) and _is_abbrev(text, m.start())):
            s = m.end()
    e = hi
    for m in _TERM.finditer(text, end, hi):
        if not (m.group(1) and _is_abbrev(text, m.start())):
            e = m.start() + (1 if m.group(1) else 0)
            break
    return s, e


# ---- context classification ---------------------------------------------------------------------------------------

def _rx(p):
    return re.compile(p, re.I)


INVALIDATE = [
    ("enjoin", _rx(r"\benjoin(?:s|ed|ing|ment)?\b")),
    ("restrain", _rx(r"\brestrain(?:s|ed|ing)?\b(?!\s+of\s+trade)|\btemporary\s+restraining\s+order\b")),
    ("injunction", _rx(r"\binjunct(?:ion|ions|ive)\b")),
    ("vacate", _rx(r"\bvacat(?:e|es|ed|ing|ur)\b")),
    ("set_aside", _rx(r"\bset(?:s|ting)?\s+aside\b")),
    ("invalid", _rx(r"\binvalid(?:ate|ated|ates|ating|ity)?\b|\bnull\s+and\s+void\b|\bvoid\b|\bunenforceable\b")),
    ("unlawful", _rx(r"\bun(?:lawful|constitutional)(?:ly)?\b|\billegal(?:ly)?\b|\bultra\s+vires\b")),
    ("exceeds_authority", _rx(r"\bexceed(?:s|ed|ing)?\s+(?:the\s+|his\s+|its\s+)?(?:president'?s?\s+|statutory\s+|legal\s+|constitutional\s+|delegated\s+)?(?:\w+\s+)?(?:authority|power|powers)\b|"
                              r"\bbeyond\s+(?:the\s+)?(?:president'?s?|his)\s+(?:\w+\s+)?(?:power|authority)|"
                              r"\bwithout\s+(?:statutory\s+|legal\s+|constitutional\s+|congressional\s+)?authority|\bnot\s+authorized\b|"
                              r"\bunauthorized\b|\blacked?\s+(?:the\s+)?authority")),
    ("conflicts", _rx(r"\bconflict(?:s|ed)?\s+with\b|\bpreempt(?:s|ed|ion)?\b|\bcontrary\s+to\s+(?:law|the\s+statute)\b")),
]
UPHOLD = [
    ("uphold", _rx(r"\bupheld\b|\bupholds?\b|\bupholding\b|\bsustain(?:s|ed|ing)?\b")),
    ("valid", _rx(r"\bvalid(?:ly)?\b|\bconstitutional(?:ly)?\b|\blawful(?:ly)?\b")),
    ("within_authority", _rx(r"\bwithin\s+(?:the\s+|his\s+|its\s+)?(?:president'?s?\s+|statutory\s+|delegated\s+|constitutional\s+)?(?:\w+\s+)?(?:power|authority)\b|"
                             r"\bdid\s+not\s+exceed\b|\bproper\s+exercise\b")),
    ("affirm", _rx(r"\baffirm(?:s|ed|ing)?\b")),
    ("survives", _rx(r"\bsurviv(?:e|es|ed|ing)\s+(?:our\s+|judicial\s+)?(?:review|scrutiny|challenge)\b|\bpass(?:es|ed)?\s+(?:constitutional\s+)?muster\b")),
]
INTERPRET = [
    ("construe", _rx(r"\bconstru(?:e|es|ed|ing)\b|\bconstruction\s+of\b")),
    ("interpret", _rx(r"\binterpret(?:s|ed|ing|ation|ations)?\b")),
    ("meaning_scope", _rx(r"\bmeaning\s+of\b|\bscope\s+of\b|\bdefinition\s+of\b")),
    ("no_authority", _rx(r"\b(?:does|did|do)\s+not\s+(?:authorize|confer|permit|grant|require|provide)\b|\boffers?\s+no\s+support\b|\bnothing\s+in\b")),
    ("applies_to", _rx(r"\bappl(?:y|ies|ied|icable|ication)\s+to\b|\bdoes\s+not\s+(?:apply|cover)\b|\bextend(?:s|ed)?\s+to\b")),
]
FAMILIES = (("enjoined_vacated_invalidated", INVALIDATE), ("upheld", UPHOLD), ("interpreted", INTERPRET))
ARGUMENT_RE = _rx(r"\bargu(?:e|es|ed|ing|ment|ments)\b|\bcontend(?:s|ed|ing)?\b|\bclaim(?:s|ed|ing)?\b|\balleg(?:e|es|ed|ing|ation|ations)\b|"
                  r"\bassert(?:s|ed|ing)?\b|\bchalleng(?:e|es|ed|ing)\b|\bwhether\b|\bseek(?:s|ing)?\b|\burg(?:e|es|ed)\b|\brequest(?:s|ed|ing)?\b|"
                  r"\bif\b|\bcould\b|\bwould\b|\bmight\b|\bmotions?\b|\bmov(?:e|ed|ing)\b|\bsought\b|\bpetition(?:s|ed|ing)?\b|"
                  r"\bapplication\s+for\b")
NEGATION_RE = _rx(r"(?:\bnot|\bno|\bnever|\bneither|\bnor|\bcannot|\bdeclin\w*\s+to|\bden(?:y|ied|ies|ying)|\brefus\w*\s+to|\bfail\w*\s+to|\bunable\s+to)\s+(?:\w+\s+){0,2}$")
LOWER_COURT_RE = _rx(r"\b(?:district\s+court|trial\s+court|court\s+of\s+appeals|lower\s+court|circuit|magistrate|court\s+below)\b")
# Cues that carry their own negation ("not authorized") are never flipped by a nearby "not".
SELF_NEGATED = {"exceeds_authority"}


def _cues(text, lo, hi, anchor):
    """[(family, cue, distance, start, end, negated)] cues in text[lo:hi], distance from the anchor span."""
    out = []
    seg = text[lo:hi]
    for family, rules in FAMILIES:
        for name, rx in rules:
            for m in rx.finditer(seg):
                a, b = lo + m.start(), lo + m.end()
                dist = anchor[0] - b if b <= anchor[0] else (a - anchor[1] if a >= anchor[1] else 0)
                before = text[max(lo, a - 40):a]
                neg = bool(NEGATION_RE.search(before)) and name not in SELF_NEGATED
                out.append((family, name, abs(dist), a, b, neg))
    return out


STRONG_ADJACENT = {"enjoin", "restrain", "injunction", "vacate", "set_aside", "invalid", "unlawful", "uphold"}


def classify_mention(text: str, start: int, end: int):
    """Rule class of one citation at text[start:end]. The class comes only from cues in the citation's own
    sentence; the cue nearest the citation wins, and holding words (enjoin, uphold) beat interpretive ones
    (construe, scope). When the sentence has no cue, the previous and next sentences are searched for a strong cue
    only (enjoin, vacate, invalid, unlawful, uphold) and reported as adjacent_class, never as the class.
    Returns class, cue, cue_family, cue_text, negated, argument_frame, reports_lower_court, federal_signal,
    state_signal, sentence_span, adjacent_class, adjacent_cue."""
    s0, e0 = sentence_bounds(text, start, end)
    cues = _cues(text, s0, e0, (start, end))
    window = text[max(0, start - 250):min(len(text), end + 250)]
    base = {"federal_signal": bool(FEDERAL_RE.search(window)), "state_signal": bool(STATE_RE.search(window)),
            "sentence_span": (s0, e0), "adjacent_class": "", "adjacent_cue": ""}
    holding = [c for c in cues if c[0] != "interpreted"]
    pick = min(holding, key=lambda c: (c[2], c[3])) if holding else (min(cues, key=lambda c: (c[2], c[3])) if cues else None)
    if pick is None:
        pl = sentence_bounds(text, s0 - 2, s0 - 1) if s0 > 2 else (s0, s0)
        nx = sentence_bounds(text, e0 + 1, e0 + 2) if e0 < len(text) - 2 else (e0, e0)
        adj = [c for c in _cues(text, pl[0], pl[1], (start, end)) + _cues(text, nx[0], nx[1], (start, end))
               if c[1] in STRONG_ADJACENT and not c[5]]
        if adj:
            c = min(adj, key=lambda c: (c[2], c[3]))
            base["adjacent_class"], base["adjacent_cue"] = c[0], c[1]
        return {"class": "mentioned", "cue": "", "cue_family": "", "cue_text": "", "negated": False,
                "argument_frame": False, "reports_lower_court": False, **base}
    family, name, dist, a, b, neg = pick
    cls = family
    if neg:
        # "did not enjoin" is a mention; "not valid" / "not lawful" reads as the opposite family.
        cls = "enjoined_vacated_invalidated" if (family == "upheld" and name in ("valid", "within_authority")) else "mentioned"
    argument = False
    if cls in ("enjoined_vacated_invalidated", "upheld"):
        argument = bool(ARGUMENT_RE.search(text[max(s0, a - 140):a]))
        if argument:
            cls = "mentioned"  # a party's request or contention, not a holding; the cue stays in cue/cue_family
    lower = bool(LOWER_COURT_RE.search(text[max(s0, a - 140):a]))
    return {"class": cls, "cue": name, "cue_family": family, "cue_text": text[a:b], "negated": neg,
            "argument_frame": argument, "reports_lower_court": lower, **base}


def pair_class(mention_results):
    """Class of one (order, opinion) pair from its mentions' results: the strongest class among mentions (a cue in
    a party's argument or request is already demoted to 'mentioned' by classify_mention). Also returns the index of
    the mention that decided it; with no cue anywhere, the first mention that carries a federal signal."""
    best, idx, best_rank = "mentioned", -1, 0
    for i, r in enumerate(mention_results):
        if RANK[r["class"]] > best_rank:
            best, idx, best_rank = r["class"], i, RANK[r["class"]]
    if idx < 0 and mention_results:
        idx = next((i for i, r in enumerate(mention_results) if r["federal_signal"]), 0)
    return best, idx
