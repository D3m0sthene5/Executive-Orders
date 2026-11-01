"""Advisory checks of explicitly described later events, preserving actor roles."""
from __future__ import annotations

import re

EO = re.compile(r"\b(?:Executive\s+Orders?\s+(?:No\.?\s*)?|EO\s*:?[ \t]*)(\d{1,6}(?:[- ]?[A-Z])?)\b", re.I)
OTHER = re.compile(r"\b(Proclamation|Public\s+Land\s+Order|Public\s+Law)\s+(?:No\.?\s*)?(\d+(?:-\d+|[- ]?[A-Z])?)\b", re.I)
ACTION = r"(?:amend(?:s|ed)?|revok(?:e[sd]?|ing)|rescind(?:s|ed)?|supersed(?:e[sd]?|ing)|terminat(?:e[sd]?|ing)|abolish(?:es|ed)?|transfer(?:s|red)?|replac(?:e[sd]?|ing)|extend(?:s|ed)?|modif(?:ies|ied)|renam(?:e[sd]?)|substitut(?:e[sd]?)|rewrit(?:es|ten)|rewrote)"


def label(value):
    m = EO.search(str(value or ""))
    return "EO:" + re.sub(r"[- ]", "", m[1]).upper() if m else str(value or "").upper().replace(" ", "")


def _sentences(text):
    # Preserve 'No. 123' and numbered section labels rather than splitting on
    # every period in a legal citation.
    return re.split(r"(?<=[!?])\s+|(?<=[a-z0-9\"'])\.\s+(?=[A-Z])", text)


def _is_actor(sentence, match):
    before, after = sentence[:match.start()], sentence[match.end():]
    if re.search(rf"\b{ACTION}\s+(?:(?:the|parent)\s+)?$|\b(?:revocation|amendment|repeal)\s+of\s+(?:the\s+)?$", before, re.I):
        return False
    if re.search(r"\b(?:amended|revoked|rescinded|superseded|terminated|abolished|transferred|replaced|extended|modified|renamed)\s+by\s*$", before, re.I):
        return True
    if re.match(rf"\s*(?:\([^)]{{0,100}}\)\s*)?(?:,?\s*(?:section|sec\.|§)\s+[\w().-]+\s*,?\s*)?(?:expressly\s+)?{ACTION}\b(?!\s+by\b)", after, re.I):
        return True
    # A plural list is a useful cue only when the sentence expressly treats
    # its named instruments as events/amendments, not merely as historical
    # objects of an ending actor.
    return bool(re.search(r"\b(?:are|as|recorded as|recorded them as)\s+later events\b|\bLater amendments\b", sentence, re.I))


def check(claim, dossier, repo, packet_path=None, cache=None):
    flags, gaps, seen = [], [], set()
    own = label(claim.get("instrument_id"))
    for pos, clause in enumerate(claim.get("operative_clauses") or []):
        if not isinstance(clause, dict):
            continue
        scope = clause.get("scope_id") or f"clause[{pos}]"
        events = clause.get("later_events") or []
        recorded = {label(e.get("actor")) for e in events if isinstance(e, dict) and e.get("source")}
        ending = clause.get("first_end") or {}
        sourced_end = label(ending.get("actor")) if isinstance(ending, dict) and ending.get("source") else None
        for event in events:
            if isinstance(event, dict) and event.get("actor") and not event.get("source"):
                flags.append({"code": "recorded_later_event_source_missing", "scope_id": scope,
                              "actor": event["actor"], "detail": "The recorded later event has no source."})
                gaps.append({"code": "later_event_source_missing", "scope_id": scope, "actor": event["actor"]})
        reason = str(clause.get("judgment_reason") or "")
        for sentence in _sentences(reason):
            explicit = bool(re.search(r"\blater (?:events?|amendments|instruments|orders)\b", sentence, re.I))
            for match in EO.finditer(sentence):
                actor = "EO:" + re.sub(r"[- ]", "", match[1]).upper()
                if actor in {own, sourced_end} or actor in recorded or not _is_actor(sentence, match):
                    continue
                # A source may discuss an older parent. Only a positive source
                # relationship to this target, or express later-event wording,
                # licenses the missing-event assertion.
                relationship = any(isinstance(ev, dict) and ev.get("actor_id") == actor
                                   and (ev.get("target_id") == own or str(key).startswith(f"ACT:{own}>{actor}"))
                                   for key, ev in (dossier.get("evidence") or {}).items())
                direct_target = bool(re.match(rf"\s*(?:\([^)]{{0,100}}\)\s*)?{ACTION}\s+(?:this|the present)\s+(?:order|clause|provision)\b", sentence[match.end():], re.I))
                if re.search(r"\b(?:other|different|unaffected)\s+(?:sections?|provisions?|clauses?)\b|\b(?:does|did)\s+not\s+(?:amend|affect|change|name)\b|\b(?:subsection|section|clause|provision)\b.{0,40}\bwas not changed\b", sentence, re.I):
                    gaps.append({"code": "other_scope_instrument_mention", "scope_id": scope, "actor": actor,
                                 "detail": "Reasoning treats this instrument as acting on another scope; independent source examination must verify that distinction."})
                    continue
                if not (explicit or relationship or direct_target):
                    gaps.append({"code": "unclassified_instrument_mention", "scope_id": scope, "actor": actor,
                                 "detail": "Acting versus prior-parent context requires source examination."})
                    continue
                key = (scope, actor)
                if key not in seen:
                    seen.add(key)
                    flags.append({"code": "later_instrument_named_without_event_source", "scope_id": scope,
                                  "actor": actor, "reasoning_sentence": sentence,
                                  "detail": f"Reasoning describes {actor} as a later actor but this clause has no source-backed later_events entry for it."})
            for match in OTHER.finditer(sentence):
                if not _is_actor(sentence, match):
                    continue
                aliases = {"PROCLAMATION": "PROC", "PUBLICLANDORDER": "PLO", "PUBLICLAW": "PL"}
                actor = aliases[match[1].upper().replace(" ", "")] + ":" + match[2].replace(" ", "")
                if actor in recorded or actor == sourced_end:
                    continue
                key = (scope, actor)
                if key not in seen:
                    seen.add(key)
                    flags.append({"code": "later_instrument_named_without_event_source", "scope_id": scope,
                                  "actor": actor, "reasoning_sentence": sentence,
                                  "detail": "An expressly acting instrument in this clause's reasoning lacks a source-backed later_events entry."})
    return {"flags": flags, "coverage_gaps": gaps}
