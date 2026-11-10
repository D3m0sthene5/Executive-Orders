"""Nalimov drafter: complete a claim by script from held, hashed records, or say exactly why it cannot.

Named for Eugene Nalimov, whose endgame tablebases (1998) computed each chess endgame once so that every later game
only looks the answer up. Here the kind of order is the endgame: for an order whose only end is an express, named,
unqualified revocation by a later order, every field of the claim follows from records the claim kit already holds.
The drafter fills them, and a model only verifies a small packet (see packets.py); it never researches.

Input: one order's frozen claim-kit evidence (packet/undecided/EO_N/EVIDENCE.json, schema of
jobs/claim-kit/status_overlay.py) and, when there is one, the packet's prepared decisions.csv / clauses.csv rows.
Output: the same files a Maudslay producer writes (one decisions.csv row, its clauses.csv rows, RATIONALES.json,
and the filled STATUS_DECISION.json), so the kit's own `apply`, `batch-check`, status review and `overlay-propose`
assemble the claim in the exact format the checker and the filing route accept (prescreen.py runs the kit's
assembler and the actual checker on every draft before any verifier is paid). Nothing here writes a claim, a status,
a ledger row or a review.

Every condition is a blocker, never a guess: an order that fails one goes to the ordinary producer route with the
blocker as its first note. A script cannot judge an earlier end, a partial scope, a saving or an inventory gap; it can
only show that none is held, so every test is written to block when in doubt (a false block costs one producer run; a
missed defect is a wrong claim). v2 follows the independent review of v1 (Fable 5.2, 2026-11-10): OCR letter-spacing
is collapsed before any wording test, a clause is a standing command only on a positive pattern, the inventory is
anchored on the order's own number line, and the savings, delayed-effect, catalog and same-actor tests are wider.
"""
from __future__ import annotations

import hashlib
import json
import re

import predicate as P

AGENT = "nalimov-script"
KIND = "express_named_revocation"
DRAFTER_VERSION = "nalimov-drafter/v2"
# Own-term kinds that are never an end of a standing command by themselves (D-20261021-report-deadline; a 'condition'
# record is a clause's internal condition). Every other kind needs a reading unless its stated date is after the end.
HARMLESS_TERM_KINDS = {"report_deadline", "condition"}
REQUIRED_SEARCHES = ("current-law:usc", "current-law:ecfr", "later-events:ofr_catalog")
# History flags whose resolution is mechanical when the status rests on an exact held revoking provision. Any other
# flag is a blocker (PARTIAL_OR_QUALIFIED_CHANGE_REQUIRES_CLAUSE_CHECK needs a clause-level reading).
FLAG_RESOLUTIONS = {
    "EMPTY_CATALOG_NOTE_DOES_NOT_ESTABLISH_CURRENT_EFFECT":
        "Not relied on. The empty catalog note establishes nothing either way; the status rests on the exact held "
        "provision of {actor} ({label}) that revokes {target} by number, read against its hashed source text.",
    "EMPTY_HISTORY_STARTED_UNDER_OWNER_RULING_2026_11_05":
        "The empty status history is not evidence of force or of an end; the status rests on the exact held provision "
        "of {actor} ({label}) that revokes {target} by number, read against its hashed source text.",
    "NO_STATUS_OBSERVATION_LOCATED":
        "No dated observation is relied on; the status rests on the exact held provision of {actor} ({label}) that "
        "revokes {target} by number, read against its hashed source text.",
}
# Missing-list lines that do not bear on an express whole revocation (matched in full); anything else blocks.
BENIGN_MISSING = (
    re.compile(r"^Current-law lead lacks an original-source sha256\.$"),
    re.compile(r"^No uniquely located attributed legal-text slice is held for this current-law pointer"),
    re.compile(r"^Machine segmentation lead; compare the inventory with the official original\.(?! *No confident)"),
)
NAMED_MISSING = re.compile(r"^(target provision not located)[^:]*:\s*(\S+)$")
ENDED_ROLES = {"eo_note_ended_status", "ending_order_in_status_line", "amending_order_in_ended_status_line"}

# --- wording tests, all applied to text after despace() and P._norm() ------------------------------------------
REVOKE_WORD = r"(?:revok\w*|supersed\w*|rescind\w*|repeal\w*)"
INSTRUMENT = r"(?:executive\s+orders?|ex\s+ord\w*|e\s+o|proclamations?|orders?\s+nos?)"
OTHER_INSTRUMENT_REVOKED = re.compile(r"\b" + INSTRUMENT + r"\b[^;]{0,500}?\b" + REVOKE_WORD + r"\b|\b" + REVOKE_WORD
                                      + r"\b[^;]{0,80}?\b" + INSTRUMENT + r"\b")
ONE_TIME_VERBS = (r"abolished|transferred|amended|terminated|restored|vacated|redesignated|ratified|confirmed|validated|"
                  r"exempted|excepted|discontinued|closed|revested|returned|released|relieved|dismissed|retired|reinstated")
ONE_TIME = re.compile(
    # done by the order itself: "is/are (hereby) transferred", "be, and they are hereby, transferred", "is hereby
    # appointed"; not a structure for the future ("members shall be appointed", "to be appointed by the President")
    r"\b(?:is|are)[\s,]+(?:hereby[\s,]+)?(?:" + ONE_TIME_VERBS + r")\b|\bbe[\s,]+(?:and\s+\w+\s+(?:is|are)[\s,]+)?hereby[\s,]+"
    r"(?:" + ONE_TIME_VERBS + r"|appointed)\b|\b(?:is|are)[\s,]+hereby[\s,]+appointed\b|\bhereby\W{0,3}(?:abolish|transfer|"
    r"amend|appoint|restor|vacat|ratif|confirm|exempt|revest|return|releas|reinstat)\w*|\bto read as follows\b|"
    r"\bstrik(?:e|ing)\s+out\b|\bshall be closed\b")
STANDING = re.compile(
    r"\bshall\b|\bmay\b|\bit is (?:hereby )?ordered\b|\b(?:is|are|be)[\s,]+(?:hereby[\s,]+)?(?:established|created|"
    r"constituted|designated|authorized|empowered|directed|delegated|prescribed|withdrawn|reserved|set apart|assigned|"
    r"vested|continued|required|prohibited|forbidden|placed|suspended)\b|\bhereby\W{0,3}(?:establish|creat|constitut|"
    r"designat|authoriz|empower|direct|delegat|prescrib|withdraw|reserv|assign|requir|prohibit|suspend)\w*|"
    r"\bthere is (?:hereby )?established\b")
# Non-operative parts that end with the order: statements of purpose or policy, findings and definitions.
STATEMENT = re.compile(r"^\s*(?:sec(?:tion)?\s*[\d-]+[a-z]?\s*[.:]\s*)?(?:purpose|policy|findings?|definitions?|"
                       r"background)\b|\bit is (?:the|hereby declared to be the) policy of\b|\bfor (?:the )?purposes? of "
                       r"this order,? the terms?\b|\bas used in this order\b")
# A section heading at a line start, including OCR letter-spacing ("S e c . 2 .", "S ection 1."). Capital S and a
# period after the number, so "section 301 of title 3" in running text is not one. Applied to raw text.
SECTION_HEAD = re.compile(r"(?m)^[ \t]*S[ \t]*(?:e[ \t]*c[ \t]*(?:t[ \t]*i[ \t]*o[ \t]*n)?|E[ \t]*C)[ \t]*\.?[ \t]*\d+[a-z]?[ \t]*\.")
COMMAND = re.compile(r"\b(?:shall|hereby|is directed|are directed|is authorized|are authorized|may)\b")
SIGNATURE = re.compile(r"(?i)the\s+white\s+house|\[f\.?\s?r\.?\s?doc|filed\s+\d|billing\s+code")
# Savings: a preserving word, and something done under or continued from the revoked instruments.
PRESERVE = re.compile(r"\b(?:remain\w*|continue\w*|preserv\w*|saved?|shall not (?:be construed to )?(?:affect|impair)|"
                      r"not be affected|(?:be )?construed to affect|until (?:modified|superseded|revoked|amended|rescinded))\b")
ABOUT_DONE = re.compile(r"\b(?:issued|taken|made|prescribed|granted|done|promulgated|acquired|accrued|incurred|pending)\s+"
                        r"(?:under|pursuant\s+to)\b|\bheretofore\b|\b(?:revoked|superseded|rescinded)\s+(?:orders?|"
                        r"provisions?)\b|\borders?\s+(?:hereby\s+)?(?:revoked|superseded)\b")
# A delayed or dated effect anywhere in the actor's text (blocks unless the ACT record carries a parsed date).
MONTH = r"(?:january|february|march|april|may(?=\s+\d)|june|july|august|september|october|november|december)"
DELAYED = re.compile(r"\b(?:effective|in\s+(?:force|effect)|into\s+effect|operative|take\s+effect|apply)\b[^.;]{0,80}?"
                     r"(?:\b" + MONTH + r"\b|\b\d+\s+days\b|\bdays\s+after\b|\bon\s+and\s+after\b|\bfrom\s+and\s+after\b|"
                     r"\bupon\s+(?:the\s+)?(?:date|expiration|termination|enactment|appointment)\b)"
                     r"|\b(?:on\s+and\s+after|from\s+and\s+after)\b")
SUPERSEDE = re.compile(r"\bsupersed\w*\b")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def despace(text):
    """Collapse OCR letter-spacing: "Executive O rder" -> "Executive Order", "R evocation" -> "Revocation",
    "e x c e p t" -> "except". The articles A and I are left alone."""
    t = str(text or "")
    t = re.sub(r"\b([B-HJ-Z]) (?=[a-z]{2,})", r"\1", t)
    t = re.sub(r"\b(?:[A-Za-z] ){2,}[A-Za-z]\b", lambda m: m.group(0).replace(" ", ""), t)
    return t


def flat(text):
    return P._norm(despace(text))


def _sentences(text):
    return [s for s in re.split(r"(?<=[.;])\s+", flat(text)) if s.strip()]


def _clause_body(text):
    """A clause's normalized text without its leading label."""
    t = flat(text).strip()
    return re.sub(r"^(?:sec(?:tion)?\s*[\d-]+[a-z]?|\([a-z0-9]+\)|[a-z0-9-]+\.)\s*[.:]?\s*(?:[a-z ]{3,40}\.\s+)?", "", t)


def classify_clause(text, target_num=None):
    """'revokes_other' (only revokes other instruments: performed on signing), 'continuing' (a standing command,
    ended by the revocation of the whole order), or 'needs_judgment' (a one-time command of another kind, a revocation
    folded into a standing clause, or a clause with no recognizable standing command). Only a positive pattern makes
    a clause 'continuing'."""
    body = _clause_body(text)
    nums = [n for n in re.findall(r"(?<!\d)(\d{2,5})(?!\d)", body) if n != (target_num or "")]
    sentences = [s for s in re.split(r"(?<=[.;])\s+", body) if len(s.strip()) > 12]
    revoking = [s for s in sentences if re.search(r"\b" + REVOKE_WORD + r"\b", s) and re.search(r"\b" + INSTRUMENT + r"\b", s)]
    if (sentences and len(revoking) == len(sentences) and nums
            and not re.search(r"\b(?:shall|except|insofar|so far as|in part|to the extent)\b", body)
            and not re.search(r"\bamend\w*\b", re.sub(r"\bas amended\b", "", body))):
        return "revokes_other"
    if revoking or OTHER_INSTRUMENT_REVOKED.search(body) and nums:
        return "needs_judgment"
    if ONE_TIME.search(body):
        return "needs_judgment"
    if STANDING.search(body) or STATEMENT.search(flat(text)):
        return "continuing"
    return "unrecognized"   # no standing verb of its own: continuing only as an item of a standing lead-in


def mentions_index(rows):
    """Index jobs/current-law/output/MENTIONS.csv rows by order and by note."""
    by_id, by_note = {}, {}
    for r in rows:
        by_id.setdefault(r.get("instrument_id"), []).append(r)
        if r.get("note_id"):
            by_note.setdefault(r["note_id"], []).append(r)
    return by_id, by_note


def mentions_for(index, iid):
    """The order's own rows, plus every row of a note printed under the order's own heading (its status line names
    the ending order under that order's id). Rows are returned once, in file order of the index."""
    by_id, by_note = index
    own = list(by_id.get(iid) or [])
    notes = {r.get("note_id") for r in own if r.get("note_id") and r.get("role") in ("eo_note_ended_status",
                                                                                     "printed_eo_text")}
    seen = {id(r) for r in own}
    for n in sorted(x for x in notes if x):
        for r in by_note.get(n) or []:
            if id(r) not in seen:
                own.append(r)
                seen.add(id(r))
    return own


class Draft(dict):
    @property
    def ok(self):
        return not self["blockers"]

    @property
    def decoy(self):
        return bool(self.get("ignored"))


def _ok_act(record, iid, kind):
    return (record.get("target_id") == iid and record.get("scope") == "whole" and record.get("names_target") is True
            and not record.get("reaches_target_via") and record.get("verb") in kind["act_verbs"]
            and isinstance(record.get("source"), dict) and record["source"].get("text_path")
            and record.get("text") and not record.get("exceptions_text"))


def _actor_names(text, iid):
    pattern = P._id_pattern(iid)
    return bool(pattern and re.search(pattern, flat(text)))


def _header_end(text):
    """End of the kit's own file header ("Instrument: ...\\nSource: ...\\n...\\n\\n"), or 0."""
    if not text.startswith("Instrument:"):
        return 0
    i = text.find("\n\n")
    return i + 2 if i >= 0 else 0


def _number_line(text, num):
    """Positions of the order's own closing number line ("[No. 8455]"), OCR spacing allowed."""
    spaced = r"\s*".join(num)
    return [m.start() for m in re.finditer(r"\[\s*N\s*o\s*\.?\s*" + spaced + r"\s*\]", text)]


def _catalog_date(segment):
    m = re.search(r"\b(" + MONTH + r")\s+(\d{1,2}),?\s+(\d{4})\b", segment)
    if not m:
        return None
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
              "november", "december"]
    return f"{m.group(3)}-{months.index(m.group(1)) + 1:02d}-{int(m.group(2)):02d}"


def draft(evidence, prepared_row=None, prepared_clauses=None, blank_decision=None, kind=None, agent=AGENT, mentions=None,
          route="undecided", ignore=()):
    """Draft one order. Returns a Draft with 'blockers' (empty when complete), and when complete 'decision',
    'row', 'clauses', 'rationales' and 'facts' (the structured content of its verification packet entry).

    `mentions`: the order's rows of jobs/current-law/output/MENTIONS.csv (mentions_for). A U.S. Code or eCFR hit
    blocks unless every such row is an ended-status note that names the same actor as the end; those notes then go
    into the packet as a further witness.

    `route`: "undecided" (status unset; fills STATUS_DECISION.json and needs Respondendi's second witness) or
    "decided" (the order's provisional status is already NO; only the lifecycle sheet is filled; there is no history
    packet, so the catalog tests are not run and the witness is not required).

    `ignore`: blocker names to record under 'ignored' instead of 'blockers'. Only for decoy controls (packets.py);
    a draft with anything ignored is a planted control and is never filed."""
    kind = kind or P.EXPRESS
    d = evidence.get("base_dossier") or {}
    iid = evidence.get("instrument_id") or d.get("instrument_id")
    recs = d.get("evidence") or {}
    out = Draft(instrument_id=iid, kind=KIND, drafter=DRAFTER_VERSION, blockers=[], ignored=[])
    ignore = frozenset(ignore or ())

    def block(message):
        (out["ignored"] if message.split(":")[0] in ignore else out["blockers"]).append(message)

    if route not in ("undecided", "decided"):
        raise ValueError("route must be undecided or decided")
    if route == "undecided" and d.get("whole_order_status") is not None:
        block("decided_order: the undecided route needs status unset")
    if route == "decided" and d.get("whole_order_status") != "no":
        block(f"decided_status_not_no: {d.get('whole_order_status')}")
    original = recs.get(d.get("original_source_id")) or {}
    if original.get("acceptable_as_original") is not True:
        block("original_not_acceptable: the frozen original is not acceptable as an original")
    if original.get("requires_page_check"):
        block("page_check_owed: the original requires an official page check")
    signed = P._date(original.get("signing_date"))
    if not signed:
        block("target_signing_date_missing")
    target_num = re.sub(r"\D", "", iid or "")

    # The prepared row's working-text disclosure (the kit's blank_sheet value) lists every non-original record held in
    # the dossier, cited or not, so it is carried through unchanged: the kit's assembler, run by prescreen.py before
    # any verifier is paid, refuses a claim that cites a working text without its confirmations.

    # The ending provision: exactly one actor, every Respondendi condition, an official copy.
    acts = {k: r for k, r in recs.items() if k.startswith("ACT:")}
    good = {k: r for k, r in acts.items() if _ok_act(r, iid, kind)
            and len(str(r.get("provision_text") or r.get("text"))) <= kind["max_provision_chars"]
            and P.named_end_in(str(r.get("provision_text") or r.get("text")), iid, kind)}
    actors = sorted({r["actor_id"] for r in good.values()})
    if not actors:
        block("no_express_named_whole_revocation: no ACT record passes the zero-token predicate")
        return out
    if len(actors) > 1:
        block("several_ending_actors: " + ", ".join(actors))
        return out
    actor = actors[0]
    base_id = f"ACT:{iid}>{actor}"
    # A source marked acceptable_as_original False (a mirror transcription, a held-text lead) needs the working-text
    # confirmations of the 2026-10-21 ruling, which a script cannot give; the kit's assembler rejects it otherwise.
    official = {k: r for k, r in good.items() if (r.get("source") or {}).get("acceptable_as_original") is not False}
    if not official:
        block("ending_source_is_working_text: every held copy of the ending provision is a transcription or lead")
        official = good
    act_id = base_id if base_id in official else sorted(official)[0]
    act = official[act_id]
    provision = str(act.get("provision_text") or act.get("text"))
    for phrase in act.get("savings_phrases") or []:
        f = flat(phrase)
        if f and (f[:80] in flat(provision) or re.search(r"(?<!\d)" + re.escape(target_num) + r"(?!\d)", f)):
            block(f"savings_phrase_in_provision: {phrase[:80]}")
    mechanism = "express_supersession" if SUPERSEDE.search(flat(provision)) else "express_revocation"
    actor_signed = P._date(act.get("signing_date"))
    parsed_end = P._date(act.get("effective_date"))
    end = parsed_end or actor_signed
    if act.get("effective_class") not in ("on_signing", "unknown", None) and not parsed_end:
        block(f"effective_class_needs_reading: {act.get('effective_class')}")
    for w in act.get("effective_wording") or []:
        if DELAYED.search(flat(w.get("text") if isinstance(w, dict) else w)) and not parsed_end:
            block("effective_wording_unparsed: the actor states a delayed or dated effect without a parsed date")
            break
    if not end:
        block("end_date_not_derivable")
    elif not (signed and actor_signed and signed < actor_signed <= end < P.CUTOFF):
        block(f"dates_out_of_order: order {signed}, actor {actor_signed}, end {end}")

    good_ids = set(good)
    for k, r in acts.items():
        if r.get("verb") in ("reinstate", "continue"):
            block(f"reinstatement_or_continuation_lead: {k}")
        if r.get("actor_id") != actor:
            block(f"another_instrument_acts: {r.get('actor_id')} ({r.get('verb')}, {r.get('scope')})")
        elif r.get("scope") == "partial":
            block(f"same_actor_partial_act: {k}")
        elif k not in good_ids and not k.startswith(tuple(g + ":" for g in good_ids)):
            block(f"same_actor_other_act: {k} ({r.get('verb')}, {r.get('scope')})")
    for ev in ((d.get("chain") or {}).get("events") or []):
        if ev.get("actor_id") not in (actor, None):
            block(f"chain_event_by_another_actor: {ev.get('actor_id')}")

    actor_text_id = f"ACTOR_TEXT:{actor}"
    actor_text = recs.get(actor_text_id) or {}
    if not (actor_text.get("text") and isinstance(actor_text.get("source"), dict) and actor_text["source"].get("text_path")):
        block("actor_text_not_held: the acting order's held text is not in the dossier")
        actor_text_id, actor_text = None, {}
    elif actor_text["source"].get("acceptable_as_original") is False:
        actor_text_id = None  # still scanned below for savings and effective dates, never cited as a status basis
    atext = str(actor_text.get("text") or "")
    if not parsed_end:
        for s_ in _sentences(atext):
            if DELAYED.search(s_):
                block(f"actor_effective_sentence_needs_reading: {s_[:160]}")
                break
    for s_ in _sentences(atext or provision):
        about = re.search(P._id_pattern(iid) or r"(?!x)x", s_) or ABOUT_DONE.search(s_)
        if PRESERVE.search(s_) and about:
            block(f"actor_savings_sentence: {s_[:200]}")

    for k, r in recs.items():
        if k.startswith("TERM:") and r.get("kind") not in HARMLESS_TERM_KINDS:
            stated = P._date(r.get("stated_end_date"))
            if not (stated and end and stated > end):
                block(f"own_term_needs_reading: {k} ({r.get('kind')})")

    # Conflicts: an actor disagreement is resolved only where the other actor's held text is in the packet and the
    # order's number is not found in it; the verifier sees that text.
    sheet_resolutions, conflict_texts = {}, []
    for c in d.get("conflicts") or []:
        code = c.get("code") if isinstance(c, dict) else str(c)
        others = [a.strip() for a in str((c or {}).get("detail", "")).split(",") if a.strip() and a.strip() != actor]
        if code != "WHOLE_END_ACTOR_DISAGREEMENT" or not others:
            block(f"dossier_conflict_needs_reading: {code}")
            continue
        notes = []
        for other in others:
            rec = recs.get(f"ACTOR_TEXT:{other}") or {}
            text = rec.get("text")
            if not text or len(text) > 20000:
                block(f"conflict_actor_text_not_held_or_too_long: {other}")
            elif _actor_names(text, iid):
                block(f"conflict_actor_prints_the_number: {other}")
            else:
                conflict_texts.append({"actor_id": other, "text": text,
                                       "page_or_item": (rec.get("source") or {}).get("page_or_item")})
                notes.append(f"The number {target_num} is not found in the held text of {other} (pattern search of the "
                             f"held OCR text, letter-spacing collapsed); an instrument that does not name the target does "
                             f"not end it (owner ruling D-20261021-unnamed-instruments).")
        if notes:
            sheet_resolutions[code] = (" ".join(notes) + f" The whole-order end rests on {actor}, whose held text "
                                       f"states: \"{provision.strip()}\"")
    resolved_others = {x["actor_id"] for x in conflict_texts}
    for m in d.get("missing") or []:
        m = str(m)
        if any(p.match(m) for p in BENIGN_MISSING):
            continue
        named = NAMED_MISSING.match(m)
        if named and named.group(2) in resolved_others:
            continue
        block(f"missing_item: {m[:140]}")

    for lead in d.get("current_law_leads") or []:
        code = ((lead or {}).get("meta") or {}).get("basis_code") or (lead or {}).get("basis_code")
        if code != "ofr_codification_1989_in_force":
            block(f"current_law_lead_needs_reading: {code}")
    searches = {s.get("search_id"): s for s in d.get("machine_searches") or [] if isinstance(s, dict)}
    for sid in REQUIRED_SEARCHES:
        s = searches.get(sid) or {}
        if not s.get("complete"):
            block(f"search_incomplete: {sid}")
        elif sid.startswith("current-law") and s.get("machine_hits_for_this_order") and mentions is None:
            block(f"current_law_mentions_order: {sid} has {s.get('machine_hits_for_this_order')} hits (MENTIONS.csv rows not supplied)")
    usc_notes = []
    hits = max([int((searches.get(x) or {}).get("machine_hits_for_this_order") or 0)
                for x in ("current-law:usc", "current-law:ecfr")] or [0])
    if mentions is not None and hits:
        anum = re.sub(r"\D", "", actor)
        if not mentions:
            block("current_law_mentions_order: the searches report hits but no MENTIONS.csv row was found")
        for m in mentions:
            snippet = flat(m.get("snippet"))
            if m.get("instrument_id") == iid and m.get("role") == "ending_order_in_status_line":
                continue  # a note about another order, naming this one as that order's end: not about this order
            if m.get("instrument_id") == iid and "amending_order" in str(m.get("role")):
                block(f"usc_note_says_this_order_amended_another: {m.get('citation')}")
                continue
            if (m.get("role") in ENDED_ROLES and re.search(r"\b(?:revoked|superseded)\b[^.]{0,40}?\b(?:ex\s+ord|executive\s+order|e\s+o)"
                                                          r"\s*(?:no\s*)?" + anum + r"\b", snippet)):
                usc_notes.append({"citation": m.get("citation"), "role": m.get("role"), "snippet": m.get("snippet"),
                                  "page_or_item": m.get("page_or_item")})
            else:
                block(f"current_law_mention_needs_reading: {m.get('citation')} ({m.get('role')})")

    hp = evidence.get("history_packet") or {}
    h = hp.get("history") or {}
    history = [P._norm(o.get("text")) for o in hp.get("observations") or [] if isinstance(o, dict) and o.get("text")]
    segments = P._segments(history)
    witness = P.second_witness(segments, actor)
    if route == "undecided":
        if not witness:
            block("no_second_witness: no catalog note entry names the same actor as ending the order")
        else:
            wdate = _catalog_date(witness[0])
            if wdate and actor_signed and wdate != actor_signed:
                block(f"witness_date_differs: catalog {wdate}, actor signed {actor_signed}")
        for seg in segments:
            if re.match(r"[a-z ]+ by:", seg) and seg not in witness:
                block(f"catalog_entry_acts_on_order: {seg[:120]}")
        if any(("reinstat" in t or "revived" in t) for t in history):
            block("catalog_reinstatement")
    label = str(act.get("provision_label") or "its revoking provision").strip()
    flag_resolutions = {}
    for flag in h.get("flags") or []:
        if flag not in FLAG_RESOLUTIONS:
            block(f"history_flag_needs_reading: {flag}")
        else:
            flag_resolutions[flag] = FLAG_RESOLUTIONS[flag].format(actor=actor, label=label, target=iid)

    # Clause inventory: every clause is a standing command or a pure revocation of other instruments, and nothing
    # of the order's own text lies outside the clauses. The order's text is anchored on its own heading or closing
    # "[No. N]" line, never on the first filing line on the page (that may be a neighbouring document's).
    clauses = [c for c in d.get("clauses") or [] if isinstance(c, dict)]
    if not clauses:
        block("no_clause_inventory")
    otext = str(original.get("text") or "")
    obase = int(original.get("char_start") or 0)
    spans = sorted((int(c.get("char_start") or 0) - obase, int(c.get("char_end") or 0) - obase) for c in clauses)
    unclaimed = []
    if spans and otext:
        hend = _header_end(otext)
        if spans[0][0] < hend:
            block("clause_starts_in_file_header: a clause holds the kit's own file header")
        numbers = _number_line(otext, target_num)
        if numbers and numbers[-1] < spans[-1][1]:
            block("order_number_line_outside_inventory: the order's own [No. N] line comes before its last clause "
                  "(a clause belongs to the next document on the page)")
        heads = list(re.finditer(r"(?i)(?:executive\s+order|e\.\s?o\.)[^\n]{0,20}?(?<!\d)" + r"\s*".join(target_num)
                                 + r"(?!\d)[^\n]*\n", otext[:spans[0][0]]))
        start = heads[-1].end() if heads else max(hend, spans[0][0] - 800)
        head = otext[start:spans[0][0]]
        if SECTION_HEAD.search(head) or (COMMAND.search(flat(head)) and not re.search(
                r"(ordered|follows|directed|prescribed)\s*[:.,]?\s*$", flat(head).strip())):
            block("inventory_gap: operative words or a section heading before the first clause")
        unclaimed.append({"where": "before the first clause", "text": head[-1500:]})
        for (a0, a1), (b0, _) in zip(spans, spans[1:]):
            gap = otext[a1:b0]
            if (len(gap.strip()) > 40 and COMMAND.search(flat(gap))) or SECTION_HEAD.search(gap):
                block(f"inventory_gap: operative words or a section heading between clauses at chars {a1}-{b0}")
            if gap.strip():
                unclaimed.append({"where": f"between clauses, chars {a1 + obase}-{b0 + obase}", "text": gap[:1500]})
        after = [n for n in numbers if n >= spans[-1][1]]
        stop = after[0] if after else None
        if stop is None:
            sig = SIGNATURE.search(otext, spans[-1][1])
            stop = sig.start() if sig else min(len(otext), spans[-1][1] + 600)
        tail = otext[spans[-1][1]:stop]
        if (len(tail.strip()) > 40 and COMMAND.search(flat(tail))) or SECTION_HEAD.search(tail):
            block("inventory_gap: operative words or a section heading after the last clause")
        unclaimed.append({"where": "after the last clause", "text": tail[:1500]})
    states = {}
    lead_in = None   # the last standing clause ending with ":" ("shall perform ... including the following:")
    for c in sorted(clauses, key=lambda c: int(c.get("char_start") or 0)):
        text = str(c.get("text") or (recs.get(c.get("id")) or {}).get("text") or "")
        if not text.strip():
            block(f"clause_text_missing: {c.get('scope_id')}")
            continue
        states[c["scope_id"]] = classify_clause(text, target_num)
        is_item = re.match(r"\s*\(?(?:[a-z]|\d{1,2}|[ivx]{1,4})\)\s", text)
        if states[c["scope_id"]] == "unrecognized":
            states[c["scope_id"]] = "continuing" if (is_item and lead_in) else "needs_judgment"
        if states[c["scope_id"]] == "continuing" and flat(text).rstrip().endswith(":"):
            lead_in = c["scope_id"]
        elif not is_item:
            lead_in = None
        inner = [m for m in SECTION_HEAD.finditer(text) if text[:m.start()].strip()]
        if inner:
            block(f"clause_spans_several_sections: {c.get('scope_id')} holds the heading {inner[0].group(0).strip()!r}")
        if states[c["scope_id"]] == "needs_judgment":
            block(f"clause_needs_judgment: {c.get('scope_id')} (not a recognizable standing command or pure revocation)")
    if clauses and states and all(v == "revokes_other" for v in states.values()):
        block("no_continuing_command: every clause only revokes other orders (spent on issue, not this kind)")

    out["facts"] = {
        "instrument_id": iid, "signing_date": signed, "actor_id": actor, "actor_signing_date": actor_signed,
        "end_date": end, "act_id": act_id, "actor_text_id": actor_text_id, "provision_label": label,
        "provision_text": provision.strip(), "provision_sha256": sha(provision.strip()), "mechanism": mechanism,
        "provision_locator": {"page_or_item": (act.get("source") or {}).get("page_or_item"),
                              "text_path": (act.get("source") or {}).get("text_path"),
                              "text_sha256": (act.get("source") or {}).get("text_sha256"),
                              "char_start": act.get("char_start"), "char_end": act.get("char_end")},
        "original_id": d.get("original_source_id"),
        "original_locator": {"page_or_item": (original.get("source") or {}).get("page_or_item"),
                             "text_path": (original.get("source") or {}).get("text_path"),
                             "text_sha256": (original.get("source") or {}).get("text_sha256")},
        "witness": witness[0] if witness else None, "catalog_entries": segments, "current_law_notes": usc_notes,
        "history_flags": list(h.get("flags") or []), "conflict_actor_texts": conflict_texts,
        "conflicts": [c.get("code") if isinstance(c, dict) else str(c) for c in d.get("conflicts") or []],
        "clause_states": states, "unclaimed_text": unclaimed,
    }
    if out["blockers"]:
        return out

    # Every field, from the records above.
    searches_used = list(REQUIRED_SEARCHES)
    cont = [s for s, v in states.items() if v == "continuing"]
    spent = [s for s, v in states.items() if v == "revokes_other"]
    verb = "superseded" if mechanism == "express_supersession" else "revoked"
    rationale = (
        f"Drafted by script ({DRAFTER_VERSION}, kind {KIND}) from held records only; the producer confirmations below "
        f"are the script's mechanical checks, and the source review is by blind verifiers. {iid} (signed {signed}) is "
        f"{verb} in whole by {actor} (signed {actor_signed}), whose {label} states: \"{provision.strip()}\" "
        f"({act['source'].get('page_or_item')}). The provision names the order, carries an ending verb and no "
        f"qualifier, " + (f"the OFR catalog independently records \"{witness[0]}\", " if witness else "")
        + f"no other held instrument acts on the order, and the bounded U.S. Code and eCFR searches found no citation "
        f"of it other than ended-status notes naming the same actor. Status NO; whole-order end {end}.")
    savings_reason = (
        f"The revoking provision of {actor} carries no exception or savings phrase, and no sentence of the held text of "
        f"{actor} pairs a preserving word (remain, continue, preserve, saved, shall not affect, construed to affect, "
        f"until modified) with this order's number or with things issued, taken, made or acquired under the revoked "
        f"orders. The bounded searches {', '.join(searches_used)} found no held citation of the order in the U.S. Code "
        f"or eCFR other than ended-status notes naming {actor}.")
    checks = {
        "earlier_end_check": (
            f"No earlier end is held: the order has no own term other than report deadlines or conditions ending "
            f"before {end} (report deadlines are not ends, D-20261021-report-deadline); no instrument other than "
            f"{actor} acts on it in the dossier's acting provisions or chain, and no catalog entry other than the "
            f"witness names an acting instrument."),
        "scope_check": (
            f"The {verb[:-1]}ion in {label} of {actor} is of the whole of {iid} (no in-part qualifier, no excepted "
            f"section; zero-token Respondendi predicate), so it reaches every clause."),
        "independent_command_check": (
            (f"Standing commands ended on {end}: {', '.join(cont)}. " if cont else "")
            + (f"Self-executing revocations of other orders, performed on signing ({signed}) and dated by "
               f"performance, not by the later end: {', '.join(spent)}." if spent else
               "No clause is a one-time command.")),
        "savings_check": savings_reason,
    }
    row = {k: "" for k in (prepared_row or {})}
    row.update(prepared_row or {})
    row.update({
        "instrument_id": iid, "dossier_sha256": d.get("fingerprint"), "agent": agent, "outcome": "submit",
        "approved": "true", "original_confirmed": "true", "original_pages_confirmed": "false",
        "inventory_confirmed": "true", "research_rationale": rationale, "savings_state": "none_after_bounded_search",
        "savings_source_id": act_id, "savings_reason": savings_reason, "search_ids": canon(searches_used),
        "conflict_resolutions": canon(sheet_resolutions), "unresolved_material_gaps": "[]",
        "publication_kind": "whole_case", **checks})
    if not row.get("working_text"):
        row["working_text"] = "{}"
    prepared = {c.get("scope_id"): c for c in prepared_clauses or []}
    clause_rows = []
    for c in clauses:
        scope = c["scope_id"]
        base = dict(prepared.get(scope) or {})
        if states[scope] == "revokes_other":
            state = dict(end_id=d.get("original_source_id"), effective_date=signed, mechanism="task_completed",
                         reason=(f"{scope} only revokes other instruments; that revocation was performed when {iid} was "
                                 f"signed on {signed} (no delayed effective date is held), so its first end is the "
                                 f"signing date by performance, not the later end of {iid}. Source: the held original, "
                                 f"which contains the clause."))
        else:
            state = dict(end_id=act_id, effective_date=end, mechanism=mechanism,
                         reason=(f"{scope} is a standing command with no own-terms end held. It remained operative until "
                                 f"{actor} of {actor_signed}, whose {label} states \"{provision.strip()}\" "
                                 f"({act['source'].get('page_or_item')}); " + (
                                     f"its stated effective date is {end}." if parsed_end else
                                     "no delayed effective date is held, so that is its first end.")))
        base.update({"instrument_id": iid, "scope_id": scope, "clause_id": base.get("clause_id") or c.get("id"),
                     "state": "terminated", "effective_date_confirmed": "true", "current_basis_id": "",
                     "current_legal_basis": "", "checked_through": "", "later_event_ids": "[]", "later_events": "[]",
                     "inventory_source_id": "", "inventory_char_start": "", "inventory_char_end": "",
                     "inventory_reason": "", **state})
        clause_rows.append(base)
    if route == "decided":
        out.update(decision=None, row=row, clauses=clause_rows, rationales={})
        return out
    decision = dict(blank_decision or {})
    decision.update({
        "schema": "eo-status-history-decision/v1", "instrument_id": iid,
        "history_sha256": evidence.get("history_sha256") or h.get("fingerprint"),
        "evidence_sha256": evidence.get("fingerprint"), "agent": agent, "approved": True, "identity_confirmed": True,
        "observations_reviewed": list(h.get("observation_ids") or []), "proposed_intervals": [],
        "conflict_resolutions": flag_resolutions, "recommended_provisional_status": "no", "rationale": rationale,
        "material_gaps": [], "basis_evidence_ids": [act_id] + ([actor_text_id] if actor_text_id else []),
        "basis_review_confirmed": True, "earlier_endings_checked": True, "partial_scope_checked": True,
        "savings_checked": True, "current_predicate_checked_through": None, "original_pages_confirmed": False,
        "notice": "Producer research decision only. Independent review and owner adoption remain separate.",
    })
    out.update(decision=decision, row=row, clauses=clause_rows, rationales={})
    return out
