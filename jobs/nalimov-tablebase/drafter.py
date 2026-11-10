"""Nalimov drafter: complete a claim by script from held, hashed records, or say exactly why it cannot.

Named for Eugene Nalimov, whose endgame tablebases (1998) computed each chess endgame once so that every later game
only looks the answer up. Here the kind of order is the endgame: for an order whose only end is an express, named,
unqualified revocation by a later order, every field of the claim follows from records the claim kit already holds.
The drafter fills them, and a model only verifies a small packet (see packets.py); it never researches.

Input: one order's frozen claim-kit evidence (packet/undecided/EO_N/EVIDENCE.json, schema of
jobs/claim-kit/status_overlay.py) and, when there is one, the packet's prepared decisions.csv / clauses.csv rows.
Output: the same files a Maudslay producer writes (one decisions.csv row, its clauses.csv rows, RATIONALES.json,
and the filled STATUS_DECISION.json), so the kit's own `apply`, `batch-check`, status review and `overlay-propose`
assemble the claim in the exact format the checker and the filing route accept. Nothing here writes a claim,
a status, a ledger row or a review.

Every condition is a blocker, never a guess: an order that fails one goes to the ordinary producer route with the
blocker as its first note. The conditions are deliberately narrower than Respondendi's lot, because a script cannot
judge an earlier end, a partial scope, a saving or an inventory gap; it can only show that none is held.
"""
from __future__ import annotations

import hashlib
import json
import re

import predicate as P

AGENT = "nalimov-script"
KIND = "express_named_revocation"
DRAFTER_VERSION = "nalimov-drafter/v1"
ENDING_TERM_KINDS = {"fixed_term", "sunset_date", "until_event", "emergency_duration", "temporary_body"}
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
# Missing-list lines that do not bear on an express whole revocation; anything else blocks.
BENIGN_MISSING = (
    re.compile(r"^Current-law lead lacks an original-source sha256\.$"),
    re.compile(r"^No uniquely located attributed legal-text slice is held for this current-law pointer"),
    re.compile(r"^Machine segmentation lead; compare the inventory with the official original\."),
)
NAMED_MISSING = re.compile(r"^(target provision not located|cited by number, no change provision located|"
                           r"Large actor context must be read at|No compiled selected actor text located|"
                           r"Acting identity absent from census)[^:]*:\s*(\S+)")
REVOKES_OTHER = re.compile(
    r"^(?:(?:sec|section)\s*\d+[a-z]?\s*[.:]\s*)?(?:the\s+following\s+)?(?:executive orders?|ex ord|e o|proclamations?)\b"
    r"[^;]{0,600}?\b(?:is|are)\s+(?:hereby\s+)?(?:revoked|superseded|rescinded)\s*[.;]?\s*$")
ONE_TIME = re.compile(r"\b(?:is|are)\s+(?:hereby\s+)?(?:abolished|transferred|amended|terminated)\b|\bhereby\s+"
                      r"(?:abolish|transfer|amend)\b|\bto read as follows\b|\bstrik(?:e|ing)\s+out\b|\bis\s+redesignated\b")
# A section heading at a line start, including OCR letter-spacing ("S e c . 2 .", "S ection 1."). Capital S and a
# period after the number, so "section 301 of title 3" in running text is not one.
SECTION_HEAD = re.compile(r"(?m)^[ \t]*S[ \t]*(?:e[ \t]*c[ \t]*(?:t[ \t]*i[ \t]*o[ \t]*n)?|E[ \t]*C)[ \t]*\.?[ \t]*\d+[a-z]?[ \t]*\.")
OTHER_REVOKED = re.compile(r"\b(?:executive orders?|ex ord|e o|proclamations?)\b[^;]{0,400}?\b(?:is|are)\s+(?:hereby\s+)?"
                           r"(?:revoked|superseded|rescinded)\b")
COMMAND = re.compile(r"\b(?:shall|hereby|is directed|are directed|is authorized|are authorized)\b")
SAVINGS = re.compile(r"\b(?:remain|continue|continued|shall not affect|not be affected|preserv\w*|until (?:modified|"
                     r"superseded|revoked|amended))\b")
ENDWORD = re.compile(r"\b(?:revoked|superseded|rescinded)\b")
SIGNATURE = re.compile(r"(?i)the white house|\[f\. ?r\. doc|\[fr doc|filed \d|billing code")
# A sentence that sets a date or delay for the actor's effect. An extractor's 'effective_wording' list also catches
# words like "effective use"; only this pattern blocks an on-signing end.
DELAYED = re.compile(r"\b(?:shall|will|to)\s+(?:take effect|become effective|be effective)\b(?!\s+(?:immediately|"
                     r"upon (?:its )?signing|on (?:the date of )?(?:its )?signing))|\beffective\s+(?:on|upon|"
                     r"as of|at|\d|january|february|march|april|may|june|july|august|september|october|"
                     r"november|december|\w+ days)\b|\bdays after\b")
ENDED_ROLES = {"eo_note_ended_status", "ending_order_in_status_line", "amending_order_in_ended_status_line"}


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sentences(text):
    return [s for s in re.split(r"(?<=[.;])\s+", P._norm(text)) if s.strip()]


def _clause_body(text):
    """A clause's normalized text without its leading label."""
    t = P._norm(text).strip()
    return re.sub(r"^(?:sec(?:tion)?\s*\d+[a-z]?|\([a-z0-9]+\)|[a-z0-9]+\.)\s*[.:]?\s*", "", t)


def classify_clause(text):
    """'revokes_other' (a self-executing revocation of other instruments, performed on signing), 'continuing'
    (a standing command, ended by the revocation of the whole order) or 'needs_judgment' (a one-time command of another
    kind: abolition, transfer, amendment of another order; a script cannot date its performance)."""
    body = _clause_body(text)
    if REVOKES_OTHER.match(body) and not re.search(r"\b(?:shall|amend\w*|except|insofar|so far as|in part)\b", body):
        return "revokes_other"
    if ONE_TIME.search(body) or OTHER_REVOKED.search(body):
        return "needs_judgment"  # a one-time command, or a revocation of another order folded into a standing clause
    return "continuing"


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
    return bool(pattern and re.search(pattern, P._norm(text)))


def draft(evidence, prepared_row=None, prepared_clauses=None, blank_decision=None, kind=None, agent=AGENT, mentions=None,
          route="undecided", ignore=()):
    """Draft one order. Returns a Draft with 'blockers' (empty when complete), and when complete 'decision',
    'row', 'clauses', 'rationales' and 'facts' (the structured content of its verification packet entry).

    `mentions`: the order's rows of jobs/current-law/output/MENTIONS.csv (rows whose instrument_id is the order or
    whose snippet prints its number). A U.S. Code or eCFR hit blocks unless every such row is an ended-status note
    that names the same actor as the end; those notes then go into the packet as a further witness.

    `route`: "undecided" (status unset; fills STATUS_DECISION.json and needs Respondendi's second witness) or
    "decided" (the order's provisional status is already NO; only the lifecycle sheet is filled, for the decided
    production route, and the catalog witness is recorded when held but not required)."""
    kind = kind or P.EXPRESS
    d = evidence.get("base_dossier") or {}
    iid = evidence.get("instrument_id") or d.get("instrument_id")
    recs = d.get("evidence") or {}
    out = Draft(instrument_id=iid, kind=KIND, drafter=DRAFTER_VERSION, blockers=[], ignored=[])
    ignore = frozenset(ignore or ())

    def block(message):
        # `ignore` exists only to build decoy controls (packets.py): a real refused order drafted as if one blocker
        # were absent. A draft with anything in 'ignored' is a planted control and is never filed.
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

    # The ending provision: exactly one actor, one base ACT record, every Respondendi condition.
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
    act_id = base_id if base_id in good else sorted(good)[0]
    act = good[act_id]
    provision = str(act.get("provision_text") or act.get("text"))
    target_num = re.sub(r"\D", "", iid)
    for phrase in act.get("savings_phrases") or []:
        flat = P._norm(phrase)
        if flat and (flat[:80] in P._norm(provision) or re.search(r"(?<!\d)" + re.escape(target_num) + r"(?!\d)", flat)):
            block(f"savings_phrase_in_provision: {phrase[:80]}")
    actor_signed = P._date(act.get("signing_date"))
    end = P._date(act.get("effective_date")) or (actor_signed if act.get("effective_class") == "on_signing" else None)
    delayed = [w for w in act.get("effective_wording") or []
               if DELAYED.search(P._norm(w.get("text") if isinstance(w, dict) else w))]
    if delayed and not P._date(act.get("effective_date")):
        block("effective_wording_unparsed: the actor states a delayed or dated effect without a parsed date")
    if not end and not delayed and act.get("effective_class") in ("unknown", None) and actor_signed:
        end = actor_signed  # no delayed or dated effect anywhere in the extracted wording: effective on signing
    if not end:
        block("end_date_not_derivable")
    elif not (signed and actor_signed and signed < actor_signed <= end < P.CUTOFF):
        block(f"dates_out_of_order: order {signed}, actor {actor_signed}, end {end}")

    for k, r in acts.items():
        if r.get("actor_id") == actor and r.get("scope") == "partial":
            block(f"same_actor_partial_act: {k}")
        if r.get("verb") in ("reinstate", "continue"):
            block(f"reinstatement_or_continuation_lead: {k}")
        if r.get("actor_id") != actor:
            block(f"another_instrument_acts: {r.get('actor_id')} ({r.get('verb')}, {r.get('scope')})")
    for ev in ((d.get("chain") or {}).get("events") or []):
        if ev.get("actor_id") not in (actor, None):
            block(f"chain_event_by_another_actor: {ev.get('actor_id')}")

    actor_text_id = f"ACTOR_TEXT:{actor}"
    actor_text = recs.get(actor_text_id) or {}
    if not (actor_text.get("text") and isinstance(actor_text.get("source"), dict) and actor_text["source"].get("text_path")):
        actor_text_id, actor_text = None, {}
    for s_ in _sentences(actor_text.get("text") or ""):
        if DELAYED.search(s_) and re.search(r"\b(?:this order|it)\b", s_) and not P._date(act.get("effective_date")):
            block(f"actor_effective_sentence_needs_reading: {s_[:160]}")
            break
    savings_hits = []
    scan = actor_text.get("text") or provision
    for s in _sentences(scan):
        # A saving preserves something done under, or continued from, the revoked instruments: the sentence names the
        # order, or speaks of what was issued, taken or made under orders it revokes. "This order shall remain in force
        # until revoked" is the actor's own term, not a saving.
        about_revoked = (re.search(P._id_pattern(iid) or r"(?!x)x", s)
                         or re.search(r"\b(?:issued|taken|made|prescribed|granted|done|promulgated)\s+(?:under|pursuant"
                                      r"\s+to|by)\b", s) or re.search(r"\b(?:revoked|superseded)\s+(?:orders?|provisions?)", s))
        if ENDWORD.search(s) and SAVINGS.search(s) and about_revoked and "nothing in this order" not in s:
            savings_hits.append(s[:200])
    for s in savings_hits:
        block(f"actor_savings_sentence: {s}")

    # Own terms: report deadlines are not ends (D-20261021-report-deadline); an ending kind needs a reading unless
    # its stated date is after the revocation.
    for k, r in recs.items():
        if k.startswith("TERM:") and r.get("kind") in ENDING_TERM_KINDS:
            stated = P._date(r.get("stated_end_date"))
            if not (stated and end and stated > end):
                block(f"own_term_needs_reading: {k} ({r.get('kind')})")

    # Conflicts in the dossier: resolvable only where the other named actor's held text does not print the number.
    sheet_resolutions = {}
    for c in d.get("conflicts") or []:
        code = c.get("code") if isinstance(c, dict) else str(c)
        others = [a.strip() for a in str((c or {}).get("detail", "")).split(",") if a.strip() and a.strip() != actor]
        if code != "WHOLE_END_ACTOR_DISAGREEMENT" or not others:
            block(f"dossier_conflict_needs_reading: {code}")
            continue
        notes = []
        for other in others:
            text = (recs.get(f"ACTOR_TEXT:{other}") or {}).get("text")
            if not text:
                block(f"conflict_actor_text_not_held: {other}")
            elif _actor_names(text, iid):
                block(f"conflict_actor_prints_the_number: {other}")
            else:
                notes.append(f"The held text of {other} does not print the number {target_num}, so it cannot end the "
                             f"order (owner ruling D-20261021-unnamed-instruments: an instrument that does not name the "
                             f"target does not end it); the catalog note attaching it to {iid} is an editorial error.")
        if notes:
            sheet_resolutions[code] = (" ".join(notes) + f" The whole-order end rests on {actor} alone, whose held "
                                       f"text states: \"{provision.strip()}\"")
    resolved_others = {a.strip() for c in d.get("conflicts") or [] if isinstance(c, dict)
                       for a in str(c.get("detail", "")).split(",")}
    for m in d.get("missing") or []:
        m = str(m)
        if any(p.match(m) for p in BENIGN_MISSING):
            continue
        named = NAMED_MISSING.match(m)
        if named and named.group(2) in resolved_others and named.group(2) != actor and named.group(1).startswith("target"):
            continue
        if named and named.group(2) == actor and named.group(1).startswith("Large actor context") and act.get("text"):
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
            snippet = P._norm(m.get("snippet"))
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
    if not witness and route == "undecided":
        block("no_second_witness: no catalog note entry names the same actor as ending the order")
    later = P._later_acts(history, end, skip=witness[0] if witness else None)
    if later:
        block(f"catalog_act_after_end: {later[0][:120]}")
    if any(("reinstat" in t or "revived" in t) for t in history):
        block("catalog_reinstatement")
    label = str(act.get("provision_label") or "its revoking provision").strip()
    flag_resolutions = {}
    for flag in h.get("flags") or []:
        if flag not in FLAG_RESOLUTIONS:
            block(f"history_flag_needs_reading: {flag}")
        else:
            flag_resolutions[flag] = FLAG_RESOLUTIONS[flag].format(actor=actor, label=label, target=iid)

    # Clause inventory: every clause is either a standing command (ended by the revocation) or a self-executing
    # revocation of other instruments (performed on signing); nothing operative may sit outside the clauses.
    clauses = [c for c in d.get("clauses") or [] if isinstance(c, dict)]
    if not clauses:
        block("no_clause_inventory")
    otext = str(original.get("text") or "")
    obase = int(original.get("char_start") or 0)
    spans = sorted((int(c.get("char_start") or 0), int(c.get("char_end") or 0)) for c in clauses)
    for (a0, a1), (b0, _) in zip(spans, spans[1:]):
        gap = otext[a1 - obase:b0 - obase]
        if (len(gap.strip()) > 40 and COMMAND.search(P._norm(gap))) or SECTION_HEAD.search(gap):
            block(f"inventory_gap: operative words or a section heading between clauses at chars {a1}-{b0}")
    if spans and otext:
        tail = otext[spans[-1][1] - obase:]
        stop = SIGNATURE.search(tail)
        tail = tail[:stop.start()] if stop else tail[:600]
        if (len(tail.strip()) > 40 and COMMAND.search(P._norm(tail))) or SECTION_HEAD.search(tail):
            block("inventory_gap: operative words or a section heading after the last clause")
        head = otext[:spans[0][0] - obase]
        heads = list(re.finditer(r"(?i)(?:executive\s+order|e\.\s?o\.)[^\n]{0,20}?(?<!\d)" + re.escape(target_num)
                                 + r"(?!\d)[^\n]*\n", head))
        head = head[heads[-1].end():] if heads else head[-800:]
        if SECTION_HEAD.search(head) or (COMMAND.search(P._norm(head)) and not re.search(
                r"(ordered|follows|directed|prescribed)\s*[:.,]?\s*$", P._norm(head).strip())):
            block("inventory_gap: operative words or a section heading before the first clause")
    states = {}
    for c in clauses:
        text = str(c.get("text") or (recs.get(c.get("id")) or {}).get("text") or "")
        if not text.strip():
            block(f"clause_text_missing: {c.get('scope_id')}")
            continue
        states[c["scope_id"]] = classify_clause(text)
        inner = [m for m in SECTION_HEAD.finditer(text) if text[:m.start()].strip()]
        if inner:
            block(f"clause_spans_several_sections: {c.get('scope_id')} holds the heading {inner[0].group(0).strip()!r}")
        if states[c["scope_id"]] == "needs_judgment":
            block(f"clause_needs_judgment: {c.get('scope_id')} (abolition, transfer or amendment of another order)")
    if clauses and states and all(v == "revokes_other" for v in states.values()):
        block("no_continuing_command: every clause only revokes other orders (spent on issue, not this kind)")

    out["facts"] = {
        "instrument_id": iid, "signing_date": signed, "actor_id": actor, "actor_signing_date": actor_signed,
        "end_date": end, "act_id": act_id, "actor_text_id": actor_text_id, "provision_label": label,
        "provision_text": provision, "provision_sha256": sha(provision),
        "provision_locator": {"page_or_item": (act.get("source") or {}).get("page_or_item"),
                              "text_path": (act.get("source") or {}).get("text_path"),
                              "text_sha256": (act.get("source") or {}).get("text_sha256"),
                              "char_start": act.get("char_start"), "char_end": act.get("char_end")},
        "original_id": d.get("original_source_id"),
        "original_locator": {"page_or_item": (original.get("source") or {}).get("page_or_item"),
                             "text_path": (original.get("source") or {}).get("text_path"),
                             "text_sha256": (original.get("source") or {}).get("text_sha256")},
        "witness": witness[0] if witness else None, "current_law_notes": usc_notes, "history_flags": list(h.get("flags") or []),
        "conflicts": [c.get("code") if isinstance(c, dict) else str(c) for c in d.get("conflicts") or []],
        "clause_states": states,
    }
    if out["blockers"]:
        return out

    # Every field, from the records above.
    searches_used = list(REQUIRED_SEARCHES)
    cont = [s for s, v in states.items() if v == "continuing"]
    spent = [s for s, v in states.items() if v == "revokes_other"]
    rationale = (
        f"Drafted by script ({DRAFTER_VERSION}, kind {KIND}) from held records only; two blind verifiers check it. "
        f"{iid} (signed {signed}) is revoked in whole by {actor} (signed {actor_signed}), whose {label} states: "
        f"\"{provision.strip()}\" ({act['source'].get('page_or_item')}). The provision names the order, carries an "
        f"ending verb and no qualifier, " + (f"the OFR catalog independently records \"{witness[0]}\", " if witness else "")
        + f"no other held "
        f"instrument acts on the order, and the bounded U.S. Code and eCFR searches found no citation of it. "
        f"Status NO; whole-order end {end}.")
    savings_reason = (
        f"The revoking provision of {actor} carries no exception or savings phrase, and no sentence of the held text of "
        f"{actor} preserves anything done under or continued from {iid} (sentence scan for 'revoked', 'superseded' or "
        f"'rescinded' together with remain, continue, preserve or shall not affect: none). The bounded searches "
        f"{', '.join(searches_used)} found no held citation of the order in the U.S. Code or eCFR.")
    checks = {
        "earlier_end_check": (
            f"No earlier end is held: the order's text has no own term of an ending kind dated before {end} (report "
            f"deadlines are not ends, D-20261021-report-deadline), and no instrument other than {actor} acts on it in "
            f"the dossier's acting provisions, chain or catalog notes."),
        "scope_check": (
            f"The revocation in {label} of {actor} is of the whole of {iid} (no in-part qualifier, no excepted section; "
            f"zero-token Respondendi predicate), so it reaches every clause."),
        "independent_command_check": (
            (f"Standing commands ended by the revocation on {end}: {', '.join(cont)}. " if cont else "")
            + (f"Self-executing revocations of other orders, performed on signing ({signed}) and dated by "
               f"performance, not by the later revocation: {', '.join(spent)}." if spent else
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
                                 f"signing date by performance, not the later revocation of {iid}. Source: the held "
                                 f"original, which contains the clause."))
        else:
            state = dict(end_id=act_id, effective_date=end, mechanism="express_revocation",
                         reason=(f"{scope} is a standing command with no own-terms end held. It remained operative until "
                                 f"{actor} of {actor_signed}, whose {label} states \"{provision.strip()}\" "
                                 f"({act['source'].get('page_or_item')}); no delayed effective date is held, so the "
                                 f"revocation is its first end."))
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
