"""Own-text status bases for undecided orders (Accursius F5). Machine leads only.

An order whose every operative command is a self-executing act (a revocation, a
restoration, an abolition, an amendment of another order) exhausts that command
when it takes effect: nothing remains for it to command afterwards. The kit had
no record type for that case, so such an order could never receive a NO status
basis, however plain its held text (Respondendi F5;
``research/excavator/claude-respondendi-2026-11-10/REPORT.md``).

Rulings applied (no new policy):
- D-20261028-evidence-decides: separate an exhausted command from its surviving
  consequences.
- Owner answer to A-20261106-pothier (2026-11-09) point 2, ruling P2 as applied:
  an amendment-only order's own command is spent on issue. The inserted text
  continues inside the parent until the parent ends
  (D-20261021-strike-and-insert). Each claim records both.

Records (frozen into the overlay dossier by ``status_overlay``):
- ``OWN_TEXT:{iid}#{char_start}``: one record per operative sentence, each an
  exact span of the dossier original. ``own_text_kind`` is ``spent_on_issue`` or
  ``amends_parent``; ``mechanism`` is always ``spent_on_issue``.
- ``PARENT_END:{iid}>{parent}>{ender}``: a later held provision that ends an
  amended parent with an ending verb, names the parent, and has whole scope.
  ``mechanism`` is ``follows_parent``. It is the source for the surviving
  consequence (``savings_residuals``), not the order's own end, and it is never
  required for a status.

The classifier is conservative. Any sentence carrying a continuing command
(``shall``, ``is hereby established``, ``withdrawn``, ``directed``, ...) outside
recognised effective-date, construction and inserted-text wording disqualifies
the whole order. A record is a lead: the producer must confirm that every
operative command is of the stated kind, and the reviewer must check it against
the held original. ``verify`` re-derives the records from the frozen original,
so a hand-written ``OWN_TEXT:`` record cannot become a basis.
"""
from __future__ import annotations

import re

from excavate import DATE, EO_REF, TERM, _add_term, _date, _extent, _sentence_spans

ROLE = "own_text"
PARENT_ROLE = "parent_end"
KINDS = ("spent_on_issue", "amends_parent")
MECHANISM = "spent_on_issue"
PARENT_MECHANISM = "follows_parent"
ENDING_VERBS = frozenset({"revoke", "supersede", "terminate", "abolish", "rescind"})
RULINGS = ("D-20261028-evidence-decides", "A-20261106-pothier (answered 2026-11-09, point 2: ruling P2)",
           "D-20261021-strike-and-insert")

_I = re.I | re.S
AMEND = re.compile(
    r"\b(?:is|are)\s+(?:hereby\s+)?(?:further\s+)?(?:amended|modified|revised)\b"
    r"|\bhereby\s+(?:further\s+)?(?:amend|modify)\b"
    # "shall be amended by deleting ..." is this order's instruction; a bare "regulations shall be amended"
    # directs someone to amend later (a continuing command; EO 1624).
    r"|\bshall\s+be\s+(?:further\s+)?(?:amended|modified|revised)\s+(?:by|to\s+read|as\s+follows)\b"
    r"|\bshall\s+be\s+(?:inserted|added|renumbered|redesignated|deleted|struck)\b"
    r"|\bto\s+read\s+as\s+follows\b", _I)
# Standing land, custody and tenure commands that the blind audit (2026-11-10, 40 positives) found the
# first classifier missed: "be, and the same are hereby, withdrawn" (EO 4531), "reserved and set apart"
# (EO 7489), "so as to withdraw permanently" (EO 1426), "does not terminate the tenure" (EO 10668).
STANDING = (r"\b(?:is|are|be)\b[\s,]*(?:and\s+the\s+same\s+(?:is|are)[\s,]+)?hereby[\s,]+(?:temporarily\s+|"
            r"permanently\s+)?(?:withdrawn|reserved|set\s+apart|held)\b"
            r"|\b(?:reserved|withdrawn)\s+and\s+(?:set\s+apart|reserved|held)\b"
            r"|\buntil\s+(?:this\s+order\s+is|otherwise)\s+(?:revoked|modified)\b|\buntil\s+further\s+(?:order|notice)\b"
            r"|\bso\s+as\s+to\s+(?:permanently\s+|temporarily\s+)?(?:withdraw|reserve|set\s+apart|include)\b"
            r"|\btenure\b|\bpersons\s+(?:already|heretofore)\s+(?:designated|appointed)\b")
SPENT = re.compile(
    r"\b(?:is|are)\s+(?:hereby\s+)?(?:revoked|rescinded|superseded|abolished|terminated|vacated|restored|"
    r"excluded|eliminated|annulled|canceled|cancelled)\b"
    r"|\bhereby\s+(?:revoke|rescind|restore|abolish|terminate|vacate|exclude|annul|cancel)\b"
    r"|\b(?:this|the\s+present)\s+order\s+(?:hereby\s+)?(?:revokes|supersedes|rescinds|abolishes|terminates)\b"
    r"|\b(?:restored|returned)\s+to\s+the\s+public\s+domain\b", _I)
# Continuing commands. "shall" is the main one; recognised neutral uses of it are removed first.
CONTINUING = re.compile(
    r"\bshall\b|\bmust\b|\bwill\b"
    r"|\b(?:is|are)\s+(?:hereby\s+)?(?:withdrawn|reserved|established|created|constituted|designated|set\s+apart|"
    r"directed|authorized|empowered|delegated|assigned|required|prohibited|requested|continued|extended|"
    r"prescribed|promulgated|approved|appointed|ordered\s+to|exempted|placed)\b"
    r"|\bhereby\s+(?:withdraw|reserve|establish|create|constitute|designate|direct|authorize|empower|delegate|"
    r"assign|require|prohibit|request|continue|extend|prescribe|promulgate|approve|appoint|exempt|place)\b"
    r"|\bmay\b"
    # Pothier's further-provision markers for amending orders (PD-CS-RULES only-content test).
    r"|\bthe\s+effect\s+of\s+(?:this|the\s+above|these|such)\s+(?:amendments?|order)\b"
    r"|\b(?:present|existing)\s+(?:incumbents?|occupants?)\b|\bpersons\s+now\s+(?:holding|serving|employed)\b"
    r"|\bit\s+is\s+further\s+ordered\b|\bincumbents?\b|" + STANDING, _I)
CONTINUING_IN_INSTRUCTION = re.compile(STANDING + r"|"
    r"\bshall\b|\bmust\b|\b(?:is|are)\s+hereby\s+(?:established|created|directed|authorized|withdrawn|reserved|"
    r"designated|delegated|assigned|required|prohibited)\b"
    # "is hereby modified to the extent of authorizing the Secretary to approve ...": a grant of
    # continuing power, not a pure change of the parent's words.
    r"|\b(?:to\s+the\s+extent\s+of\s+)?authoriz(?:e|es|ing)\b", _I)
NEUTRAL_SHALL = re.compile(
    r"\b(?:shall|will)\s+(?:take\s+effect|become\s+effective|be\s+effective)\b"
    r"|\bshall\s+(?:not\s+)?be\s+construed\b|\bshall\s+not\s+(?:affect|impair)\b"
    r"|\bshall\s+be\s+implemented\s+consistent(?:ly)?\s+with\b"
    r"|\bmay\s+be\s+cited\b", _I)
CONSTRUCTION = re.compile(
    r"\bNothing\s+in\s+(?:this|these)\b|\bnot\s+intended\s+to,?\s+and\s+does\s+not,?\s+create\b"
    r"|\bshall\s+be\s+implemented\s+consistent(?:ly)?\s+with\b|\bsubject\s+to\s+the\s+availability\s+of\s+appropriations\b"
    r"|\bshall\s+(?:not\s+)?be\s+construed\b", _I)
EFFECTIVE = re.compile(
    r"\b(?:shall|will)\s+(?:take\s+effect|become\s+effective|be\s+effective)\b|\b(?:is|are)\s+effective\b"
    r"|\beffective\s+(?:immediately|on|as\s+of|upon|at)\b", _I)
PREAMBLE = re.compile(r"(?m)^\W*(?:By\s+(?:virtue\s+of|the\s+authority)|Pursuant\s+to|Under\s+(?:and\s+by\s+virtue|the\s+authority))", re.I)
# "... it is hereby ordered as follows: Section 1." (the splitter keeps the first heading with the preamble)
ORDERED = re.compile(r"\bit\s+is\s+(?:hereby\s+)?ordered(?:\s+as\s+follows)?\s*[:.,]?\s*"
                     r"(?:(?:Section|Sec\.?|SECTION)\s*\d+[A-Za-z]?\.?)?\s*$", _I)
COMMANDISH = re.compile(r"\b(?:shall|must|may|will|hereby|is|are|be|directed|authorized|ordered)\b", _I)
QUOTED = re.compile(r"[\"“][^\"”]*[\"”]|‘[^’]*’")
TOP_HEADING = re.compile(r"^\W*(?:Sec(?:tion)?\.?|SECTION|SEC\.?)\s*\d", _I)
DEFERRED = re.compile(r"\b(?:take\s+effect|become\s+effective|be\s+effective|effective)\b", _I)


def _normal_quotes(text):
    """FR and GPO texts print double quotes as paired single quotes or backticks."""
    for pair, mark in (("‘‘", "“"), ("’’", "”"), ("``", "“"), ("''", "”"), ("��", '"')):
        text = text.replace(pair, mark)
    return text


FOLLOWS = r"(?:as\s+follows|the\s+following(?:\s+[\w-]+){0,6})"


def _strip_quotes(sentence):
    return QUOTED.sub(" ", _normal_quotes(sentence))


def _classify(sentence):
    """One sentence outside inserted text: amend, spent, effective, construction, neutral or continuing."""
    # Producer preambles and page markers are not the order's words.
    plain = _strip_quotes("\n".join(line for line in sentence.splitlines() if not HEADER.search(line)))
    if not plain.strip():
        return "neutral"
    head = _instruction(plain)
    if AMEND.search(head):
        rest = NEUTRAL_SHALL.sub(" ", AMEND.sub(" ", head))
        return "continuing" if CONTINUING_IN_INSTRUCTION.search(rest) else "amend"
    if SPENT.search(plain):
        rest = NEUTRAL_SHALL.sub(" ", SPENT.sub(" ", plain))
        return "continuing" if CONTINUING.search(rest) else "spent"
    if CONSTRUCTION.search(plain):
        return "construction"
    if EFFECTIVE.search(plain):
        return "continuing" if CONTINUING.search(NEUTRAL_SHALL.sub(" ", plain)) else "effective"
    if ORDERED.search(plain) or (PREAMBLE.search(plain) and not CONTINUING.search(NEUTRAL_SHALL.sub(" ", plain))):
        return "neutral"
    if not COMMANDISH.search(plain):
        return "neutral"
    return "continuing"


STRONG = re.compile(r"\bshall\b|\bmust\b|\b(?:is|are)\s+(?:hereby\s+)?(?:established|created|directed|authorized|"
                    r"withdrawn|reserved|designated|delegated|empowered)\b|" + STANDING, _I)
RECITAL = re.compile(r"(?m)^\W*Whereas\b", re.I)


def _strong_command(sentence):
    """A plain continuing command in text the clause inventory left out (headers, recitals and
    amending instructions excluded)."""
    plain = _strip_quotes("\n".join(line for line in sentence.splitlines() if not HEADER.search(line)))
    if RECITAL.search(plain) or AMEND.search(_instruction(plain)):
        return False
    return bool(STRONG.search(NEUTRAL_SHALL.sub(" ", plain)))


def _instruction(sentence):
    """The amending instruction before any 'as follows:' / 'the following:' text it introduces."""
    return re.split(FOLLOWS + r"\s*:", sentence, maxsplit=1, flags=_I)[0]


def _quote_balance(fragment):
    """Open minus closed double quotation marks (curly pairs; straight quotes by parity)."""
    fragment = _normal_quotes(fragment)
    return fragment.count("“") - fragment.count("”") + fragment.count('"') % 2


def _windows(iid, text, clauses):
    """The clause inventory's operative spans, or the printed extent when there is none."""
    spans = [(c["char_start"], c["char_end"]) for c in clauses
             if isinstance(c, dict) and type(c.get("char_start")) is int and type(c.get("char_end")) is int]
    return sorted(spans) if spans else [_extent(iid, text)]


# Further-provision wording that a clause inventory can leave outside its spans
# (a trailing "The effect of the above amendment is ..."). Any of it in the order's
# printed extent disqualifies the order, wherever the segmenter put it.
FURTHER = re.compile(
    r"\bthe\s+effect\s+of\s+(?:this|the\s+above|these|such)\s+(?:amendments?|order)\b"
    r"|\b(?:present|existing)\s+(?:incumbents?|occupants?)\b|\bpersons\s+now\s+(?:holding|serving|employed)\b"
    r"|\bit\s+is\s+further\s+ordered\b|\bincumbents?\b|\bhereafter\b", _I)
HEADER = re.compile(r"^\W*(?:#|Instrument:|Source:|Location:|SHA-256|Wanted:|Cited by:|Machine text layer|"
                    r"May contain recognition errors|Not an authenticated transcription|=== PDF page)", _I)


def _parents(sentence):
    plain = _strip_quotes(_instruction(sentence))
    found = []
    for m in EO_REF.finditer(plain):
        ident = "EO:" + re.sub(r"[ \t]", "", m[1]).upper()
        if ident not in found:
            found.append(ident)
    return found


def _effective_date(sentences, signing):
    """Signing date unless the order's own wording defers or fixes its effect."""
    for sentence in sentences:
        found = DEFERRED.search(sentence)
        if not found:
            continue
        after = sentence[found.start():]
        term = TERM.search(after)
        if term and re.search(r"\b(?:from|after)\s+(?:the\s+)?date\s+(?:of\s+(?:this|the)\s+order|hereof)\b", after, _I):
            return _add_term(signing, term[1], term[3]), "relative_to_signing", sentence
        if re.search(r"^\S+(?:\s+\S+)?\s+(?:immediately|upon\s+(?:its\s+)?(?:signing|issuance)|"
                     r"(?:on|from)\s+(?:and\s+after\s+)?(?:the\s+)?date\s+(?:of\s+(?:this|the)\s+order|hereof))", after, _I):
            return signing, "immediately", sentence
        stated = re.match(r"\S+(?:\s+effect)?\s+(?:on\s+|as\s+of\s+|at\s+[^,;.]{0,40}?\s+on\s+)?(" + DATE + ")", after, re.I)
        if stated and _date(stated[1]):
            return _date(stated[1]), "stated", sentence
        # Effect deferred to an event the text does not date: whether the command was ever
        # carried out needs evidence of that event (D-20261028-evidence-decides).
        return None, "deferred_to_undated_event", sentence
    return signing, "signing_date", None


def classify(iid, text, clauses, signing_date=None):
    """Return (kind or None, sentence rows) for the order's own operative text.

    Text an amending instruction introduces ("to read as follows:", "the following
    new section:") is the parent's text, not this order's command: it is labelled
    ``inserted`` until its quotation closes or, when unquoted, until a top-level
    section heading of this order carries another instruction."""
    rows, inserted, quoted, depth = [], False, False, 0
    for start, end in _windows(iid, text, clauses):
        for a, b in _sentence_spans(text[start:end]):
            a, b = start + a, start + b
            sentence = text[a:b]
            if inserted:
                if quoted:
                    depth += _quote_balance(sentence)
                    rows.append({"char_start": a, "char_end": b, "label": "inserted"})
                    if depth <= 0:
                        inserted, quoted, depth = False, False, 0
                    continue
                plain = _strip_quotes(sentence)
                if not (TOP_HEADING.search(sentence) and (AMEND.search(_instruction(plain)) or SPENT.search(plain)
                                                          or EFFECTIVE.search(plain) or CONSTRUCTION.search(plain))):
                    # Unquoted inserted text has no reliable end. A command in it may be this order's own
                    # (EO 1624: "the regulations ... shall be amended so as to provide"), so it is ambiguous
                    # and the order does not qualify (blind audit 2026-11-10).
                    rows.append({"char_start": a, "char_end": b,
                                 "label": "ambiguous" if _strong_command(sentence) else "inserted"})
                    continue
                inserted = False
            label = _classify(sentence)
            rows.append({"char_start": a, "char_end": b, "label": label})
            if label != "amend":
                continue
            head = _instruction(sentence)
            tail = sentence[len(head):]
            opens = bool(tail) or sentence.rstrip().endswith(":") or bool(re.search(
                FOLLOWS + r"\s*\W*$", sentence, _I))
            if not opens:
                continue
            balance = _quote_balance(tail)
            if balance > 0:
                inserted, quoted, depth = True, True, balance
            elif "“" in _normal_quotes(tail) or '"' in tail:
                continue  # the inserted words opened and closed inside this sentence
            elif _normal_quotes(text[b:b + 8].lstrip())[:1] in "“\"":
                inserted, quoted, depth = True, True, 0
            else:
                inserted, quoted, depth = True, False, 0
    windows = _windows(iid, text, clauses)
    # Further-provision wording anywhere in the order (inside or outside the clause spans, inside
    # unquoted inserted text) disqualifies it: an inserted-text boundary is a guess.
    extent = _extent(iid, text)
    lo, hi = min([extent[0]] + [a for a, _ in windows]), max([extent[1]] + [b for _, b in windows])
    for found in FURTHER.finditer(text, lo, hi):
        if _quote_balance(text[lo:found.start()]) > 0:
            continue  # inside a quotation: the parent's inserted words
        rows.append({"char_start": found.start(), "char_end": found.end(), "label": "continuing"})
        break
    # Sentences of the printed order that the clause inventory left out (a segmenter that kept only
    # "Sec. 3" of EO 10917) are read too: a continuing command there disqualifies the order. Gap text
    # after an unquoted insertion may be the parent's words; that only costs reach.
    cursor = extent[0]
    gaps = []
    for s, e in sorted(windows):
        if s > cursor:
            gaps.append((cursor, min(s, extent[1])))
        cursor = max(cursor, e)
    if cursor < extent[1]:
        gaps.append((cursor, extent[1]))
    for gs, ge in gaps:
        if gs >= ge:
            continue
        for a, b in _sentence_spans(text[gs:ge]):
            if _strong_command(text[gs + a:gs + b]) and not _quote_balance(text[lo:gs + a]) > 0:
                rows.append({"char_start": gs + a, "char_end": gs + b, "label": "continuing", "outside_clauses": True})
                break
    labels = {r["label"] for r in rows}
    operative = [r for r in rows if r["label"] in {"amend", "spent"}]
    if not operative or "continuing" in labels or "ambiguous" in labels:
        return None, rows
    kind = "amends_parent" if all(r["label"] == "amend" for r in operative) else "spent_on_issue"
    return kind, rows


def records(iid, original, clauses):
    """OWN_TEXT records for the dossier original, or {} when the order does not qualify.

    ``original`` is the dossier's ``ORIGINAL:`` evidence record (exact text and source).
    """
    if not isinstance(original, dict) or not original.get("text") or not isinstance(original.get("source"), dict):
        return {}
    text = original["text"]
    if original.get("char_start") != 0 or original.get("char_end") != len(text):
        return {}
    kind, rows = classify(iid, text, clauses or [], original.get("signing_date"))
    if kind is None:
        return {}
    operative = [r for r in rows if r["label"] in {"amend", "spent"}]
    effective_sentences = [text[r["char_start"]:r["char_end"]] for r in rows if r["label"] in {"effective", "spent", "amend"}]
    effective, basis, wording = _effective_date(effective_sentences, original.get("signing_date"))
    if basis == "deferred_to_undated_event":
        return {}
    parents = []
    for r in operative:
        if r["label"] == "amend":
            for p in _parents(text[r["char_start"]:r["char_end"]]):
                if p != iid and p not in parents:
                    parents.append(p)
    ids = ["OWN_TEXT:" + iid + "#" + str(r["char_start"]) for r in operative]
    test = {"operative_sentences": len(operative),
            "inserted_sentences": sum(r["label"] == "inserted" for r in rows),
            "neutral_sentences": sum(r["label"] in {"neutral", "construction", "effective"} for r in rows),
            "continuing_sentences": 0, "classifier": "own_text_v1"}
    result = {}
    for ident, r in zip(ids, operative):
        sentence = text[r["char_start"]:r["char_end"]]
        record = {"id": ident, "role": ROLE, "instrument_id": iid, "actor_id": iid,
                  "own_text_kind": kind, "mechanism": MECHANISM, "sentence_kind": r["label"],
                  # Records exist only when no sentence of the order (clause spans, their gaps, the
                  # printed extent) carries a continuing command: every record is whole-order.
                  "scope": "whole",
                  "source": original["source"], "text": sentence,
                  "char_start": r["char_start"], "char_end": r["char_end"],
                  "signing_date": original.get("signing_date"), "effective_date": effective,
                  "effective_date_basis": basis, "operative_sentence_ids": ids, "whole_order_test": test,
                  "rulings": list(RULINGS),
                  "notes": ("Machine own-text lead: every operative sentence the classifier found is a self-executing "
                            "act and none carries a continuing command. Confirm against the held original that every "
                            "command is of this kind before citing it; confirm the effective date.")}
        if wording is not None:
            record["effective_wording"] = wording
        if kind == "amends_parent" or parents:
            record["parent_ids"] = parents
        if kind == "amends_parent":
            record["parent_id"] = parents[0] if parents else None
            record["surviving_consequence"] = ("The inserted text continues inside the amended instrument until it "
                                               "ends (D-20261021-strike-and-insert); record it under savings_residuals, "
                                               "citing a PARENT_END record when one is held.")
        result[ident] = record
    return result


def parent_candidates(iid, text):
    """Every order number printed in the text: a superset of the parents ``records`` can name."""
    found = set()
    for m in EO_REF.finditer(text or ""):
        ident = "EO:" + re.sub(r"[ \t]", "", m[1]).upper()
        if ident != iid:
            found.add(ident)
    return found


def parent_end_records(iid, own, parent_acts):
    """PARENT_END records from held ACT rows that end a parent named by an amends_parent record."""
    parents = []
    for record in own.values():
        if record.get("own_text_kind") == "amends_parent":
            for p in record.get("parent_ids") or []:
                if p not in parents:
                    parents.append(p)
    result = {}
    for parent in parents:
        chosen = {}
        for act in parent_acts or []:
            if (act.get("target_id") != parent or act.get("actor_id") in (iid, parent)
                    or act.get("verb") not in ENDING_VERBS or act.get("scope") != "whole"
                    or act.get("names_target") is not True or not act.get("provision_text")
                    or not isinstance(act.get("actor_source"), dict)
                    or type(act.get("char_start")) is not int or type(act.get("char_end")) is not int):
                continue
            key = act["actor_id"]
            if key not in chosen or str(act.get("id")) < str(chosen[key].get("id")):
                chosen[key] = act
        for actor, act in sorted(chosen.items()):
            ident = "PARENT_END:" + iid + ">" + parent + ">" + actor
            result[ident] = {
                "id": ident, "role": PARENT_ROLE, "mechanism": PARENT_MECHANISM, "instrument_id": iid,
                "target_id": iid, "parent_id": parent, "actor_id": actor, "parent_act_id": act.get("id"),
                "verb": act.get("verb"), "scope": act.get("scope"), "names_parent": True,
                "source": act["actor_source"], "text": act["provision_text"],
                "char_start": act["char_start"], "char_end": act["char_end"],
                "signing_date": act.get("signing_date"), "effective_date": act.get("effective_date"),
                "notes": ("Machine lead: a held provision ends the amended parent. It is evidence for the surviving "
                          "consequence (the inserted text), not for the amending order's own end, which is spent on "
                          "issue (owner answer to A-20261106-pothier point 2).")}
    return result


def attach(dossier, iid, parent_acts=()):
    """Add OWN_TEXT and PARENT_END records to an overlay dossier in place; return their ids."""
    original = dossier.get("evidence", {}).get(dossier.get("original_source_id"))
    own = records(iid, original, dossier.get("clauses", []))
    ends = parent_end_records(iid, own, parent_acts)
    dossier["evidence"].update(own)
    dossier["evidence"].update(ends)
    dossier["own_text_ids"] = sorted(own)
    dossier["parent_end_ids"] = sorted(ends)
    return sorted(own) + sorted(ends)


def verify(dossier, ident):
    """True when the dossier's OWN_TEXT record is exactly what ``records`` derives from its frozen original."""
    original = dossier.get("evidence", {}).get(dossier.get("original_source_id"))
    expected = records(dossier.get("instrument_id"), original, dossier.get("clauses", []))
    return ident in expected and dossier.get("evidence", {}).get(ident) == expected[ident]
