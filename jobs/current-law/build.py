"""Turn raw scanner records into MENTIONS.csv, FRAGMENTS.jsonl and friends.

Nothing here decides legal status. Mentions are leads; fragments are draft
claim parts labelled as candidates.
"""

import csv
import hashlib
import json
from collections import Counter, defaultdict

import eo_refs

PRODUCED_BY = "current-law"
MAX_ENTRIES_PER_FRAGMENT = 80

# Roles that suggest something in current law still prints, relies on or
# incorporates the order (leads for "what keeps it operating now").
PREDICATE_ROLES = {
    "printed_eo_text": "The U.S. Code ({edition}) prints this order's text as a note under {where}, and the note's status line does not say it was revoked or superseded. This is an editorial reprint by the Office of the Law Revision Counsel, not a legal basis by itself; it is a lead that the order was treated as in force when the note was last revised.",
    "statutory_text_reference": "Statute text at {where} ({edition}) names this order. A statute that relies on, ratifies or incorporates an order can keep it operating; read the section to see how the order is used.",
    "references_in_text_note": "The 'References in Text' note at {where} ({edition}) says statute text there refers to this order.",
    "statutory_note_reference": "A statutory note (law not classified to a section) at {where} ({edition}) names this order.",
    "amending_order_in_status_line": "This order is listed as an amendment of another order whose text the U.S. Code ({edition}) prints as current under {where}; its amendment is reflected in that printed text.",
    "cfr_text_reference": "Current regulation text at {where} ({edition}) names this order.",
    "cfr_authority_citation": "The authority citation of {where} ({edition}) lists this order as authority for the regulation.",
    "cfr_source_citation": "The source citation of {where} ({edition}) lists this order as a document that issued or amended the regulation text.",
    "cfr_appendix_text_reference": "An appendix at {where} ({edition}) names or reprints this order.",
    "cfr_search_excerpt_reference": "The eCFR point-in-time search for {date} returns {where} as in force, and its excerpt names this order.",
}
BASIS_LABELS = {
    "printed_eo_text": "U.S. Code prints the order's text as a note, with no ending statement",
    "statutory_text_reference": "statute text names the order",
    "references_in_text_note": "References-in-Text note says statute text refers to the order",
    "statutory_note_reference": "statutory note names the order",
    "amending_order_in_status_line": "order amended a printed order (weak lead)",
    "cfr_text_reference": "regulation text names the order",
    "cfr_authority_citation": "regulation authority citation lists the order",
    "cfr_source_citation": "regulation source citation lists the order",
    "cfr_appendix_text_reference": "CFR appendix names or reprints the order",
    "cfr_search_excerpt_reference": "eCFR point-in-time search excerpt names the order",
}
CONFIDENCE_NOTES = {
    "current_predicate_candidates": (
        "Machine-found mentions of this order in current federal law (U.S. Code and/or eCFR; see each entry's system). "
        "Leads only: a mention shows the text names the order, not that the order still has legal effect. Read each cited place. "
        "checked_through is null where the text could have changed after the cutoff, and is the source's own currency date "
        "when that is earlier than the cutoff. basis_code and currency_code are explained in SUMMARY.json fragment_codes."),
    "later_event_candidates": (
        "Statements that this order (or a part of it) was revoked, superseded, repealed or amended, parsed by regex from OLRC "
        "notes and statute text in the U.S. Code and from CFR text. Candidates only: date_candidate is the date printed next "
        "to the acting instrument, not a verified effective date; scope (whole order or part) and the effective date must be "
        "checked in the acting instrument."),
    "whole_order_end_candidates": (
        "The subset of later_event_candidates that read as ending the WHOLE order (no section, paragraph or qualifier named, "
        "an actor is named, no chronology caution). Candidates only: date_candidate is a printed date, not a verified "
        "effective date, and the acting instrument must be read to confirm the scope."),
}
# Events with these cautions are kept in EVENT_CANDIDATES.csv but not put into fragments.
EXCLUDED_CAUTIONS = ("chronology_impossible", "subject_inside_prepositional_phrase")
ENDING_VERBS = {"revoked": "revocation", "superseded": "supersession", "rescinded": "rescission",
                "terminated": "termination", "repealed": "repeal", "annulled": "annulment",
                "cancelled": "cancellation", "canceled": "cancellation", "amended": "amendment"}

MENTION_FIELDS = ["mention_id", "system", "route", "edition", "title", "citation", "location_kind", "container_id",
                  "section_key", "note_topic", "crossheading", "note_heading", "note_id", "role", "is_predicate_lead", "caution", "eo_raw",
                  "eo_normalized", "instrument_id", "mapping", "provisional_status", "occurrences", "snippet",
                  "source_id", "page_or_item", "human_url", "changed_after_cutoff", "checked_through",
                  "confirmed_at_cutoff_by_search"]
EVENT_FIELDS = ["event_id", "system", "edition", "citation", "note_role", "subject_raw", "subject_normalized",
                "subject_instrument_id", "subject_provisional_status", "event_type_candidate", "actor_kind",
                "actor", "acting_instrument_id", "acting_raw", "acting_fr_citation", "acting_scope", "date_candidate",
                "scope_candidate", "scope_hint", "caution", "in_scope", "sentence", "source_id", "page_or_item"]


def short_hash(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]


def load_universe(repo):
    ids = []
    with open(repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            ids.append(row["id"])
    statuses, origins = {}, {}
    with open(repo / "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            statuses[row["instrument_id"]] = row["provisional_substantive_status"].strip().lower()
            origins[row["instrument_id"]] = row.get("decision_origin", "")
    u = eo_refs.Universe(ids, statuses)
    u.origins = origins
    return u


class Book:
    """Collects sources, mentions and events across both systems."""

    def __init__(self, universe):
        self.u = universe
        self.sources = {}
        self.mentions = []
        self.events = []
        self.eo_notes = []
        self.search_hits = []
        self.dropped_events = Counter()

    # -------------------------------------------------------- sources --
    def add_source(self, source_id, meta, instrument_ids=(), page_or_item="", notes="", text_path=None):
        rec = {"source_id": source_id, "instrument_ids": sorted(set(instrument_ids)), "url": meta["url"],
               "sha256": meta["sha256"], "bytes": meta["bytes"], "content_type": meta.get("content_type", ""),
               "retrieved_utc": meta["retrieved_utc"], "route": meta["route"], "page_or_item": page_or_item,
               "text_path": text_path, "cache_path": meta.get("cache_path"), "notes": notes}
        self.sources[source_id] = rec
        return rec

    def ref(self, source_id, page_or_item):
        s = self.sources[source_id]
        return {"url": s["url"], "sha256": s["sha256"], "page_or_item": page_or_item}

    # ------------------------------------------------------- mentions --
    def add_mention(self, rec, system, route, edition, source_id, page_or_item, checked_through,
                    changed_after_cutoff="", human_url=""):
        iid, how = self.u.map(rec["eo_number"], rec.get("eo_suffix", ""))
        norm = eo_refs.normalized(rec["eo_number"], rec.get("eo_suffix", ""))
        role = rec["role"]
        mid = f"{system}:" + short_hash(edition, rec.get("citation"), rec.get("note_id"), rec.get("container_id"),
                                        rec.get("location_kind"), role, norm)
        row = {
            "mention_id": mid, "system": system, "route": route, "edition": edition, "title": rec.get("title", ""),
            "citation": rec.get("citation", ""), "location_kind": rec.get("location_kind", ""),
            "container_id": rec.get("container_id", ""), "note_topic": rec.get("note_topic", ""),
            "crossheading": rec.get("crossheading", ""), "note_heading": rec.get("note_heading", ""),
            "note_id": rec.get("note_id", ""), "role": role, "is_predicate_lead": ("no_caution" if rec.get("caution") else "yes") if role in PREDICATE_ROLES else "no",
            "caution": rec.get("caution", ""),
            "section_key": rec.get("section") or rec.get("appendix") or "",
            "eo_raw": rec.get("eo_raw", ""), "eo_normalized": norm, "instrument_id": iid, "mapping": how,
            "provisional_status": self.u.status(iid) if iid else "", "occurrences": rec.get("occurrences", 1),
            "snippet": rec.get("snippet", ""), "source_id": source_id, "page_or_item": page_or_item,
            "human_url": human_url or rec.get("human_url", ""), "changed_after_cutoff": changed_after_cutoff,
            "checked_through": checked_through or "", "confirmed_at_cutoff_by_search": "",
        }
        self.mentions.append(row)
        return row

    def add_event(self, rec, system, edition, source_id, page_or_item):
        """Add one editorial event; returns the row, or None when it is dropped
        (the acting order is the subject itself)."""
        subj_num, subj_suf = rec["subject_number"], rec.get("subject_suffix", "") or ""
        subj_norm = eo_refs.normalized(subj_num, subj_suf)
        subj_id, _ = self.u.map(subj_num, subj_suf)
        actor = dict(rec.get("actor") or {})
        cautions = [rec["context_caution"]] if rec.get("context_caution") else []
        kind = actor.get("kind", "")
        printed_self = actor.get("scope_text") == "the printed order itself"
        if kind == "executive_order":
            r = actor["ref"]
            if r["number"] == subj_num and (r.get("suffix") or "").upper() == subj_suf.upper():
                self.dropped_events["acting_order_is_the_subject"] += 1
                return None
            if r["number"] < subj_num:
                ab = actor.get("amended_by")
                later = [a for a in actor.get("amenders", []) if a["ref"]["number"] > subj_num]
                if ab and ab["ref"]["number"] > subj_num:
                    # "revoked by Ex. Ord. No. 12333, § 3.6, ..., as amended by Ex. Ord. No. 13470": 13470 did it.
                    actor = dict(ab, scope_text=f"amendment of {r['raw']}" + (f" {actor['scope_text']}" if actor.get("scope_text") else ""))
                    cautions.append("actor_is_amending_order_of_named_order")
                    printed_self = False
                elif printed_self and later:
                    # Text of a printed order that revokes a LATER order was inserted by an amendment.
                    actor = {"kind": "amendment_of_printed_order", "date": None, "fr": None, "scope_text": "",
                             "text": f"an amendment of the printed {r['raw']}; candidates listed in its status line: "
                                     + ", ".join(a["ref"]["raw"] + (f" ({a['date']})" if a.get("date") else "") for a in later)}
                    cautions.append("text_inserted_by_later_amendment_candidate")
                    printed_self = False
                else:
                    cautions.append("chronology_impossible")
        acting_id, acting_raw, actor_text = "", "", ""
        kind = actor.get("kind", "")
        if kind == "executive_order":
            r = actor["ref"]
            acting_id, _ = self.u.map(r["number"], r.get("suffix", ""))
            acting_raw = r["raw"]
            actor_text = f"President, by {r['raw']}" + (" (the printed order itself)" if printed_self else "")
        elif kind == "statute":
            actor_text = f"Congress, by {actor['publ']}" if actor.get("publ") else f"Congress ({actor.get('text', 'an Act')})"
        elif kind == "statute_text":
            actor_text = f"statute text at {actor.get('text')}"
        elif kind in ("other", "amendment_of_printed_order"):
            actor_text = actor.get("text", "")
        when = actor.get("date")
        in_scope = "yes" if (when is None or when <= eo_refs.LEGAL_CUTOFF) else "no_after_cutoff"
        subject_scope = rec.get("subject_scope") or ""
        scope = rec.get("scope_hint") or subject_scope or ""
        acting_scope = actor.get("scope_text") or ""
        if acting_scope == "the printed order itself":
            acting_scope = ""
        verb = rec.get("verb", "")
        if verb == "repealed" and not scope:
            # OLRC says "revoked"/"superseded" for orders; "repealed" is usually about a statute or rule.
            cautions.append("repeal_wording_check_what_ended")
        if verb == "amended":
            scope_candidate = ""
        elif rec.get("note_role") == "bracketed_editorial_insert":
            # "[Superseded by ...]" replaces a part of the printed text, never the whole order.
            scope_candidate = "partial_candidate"
            scope = scope or "bracketed editorial insert inside the order's printed text"
        elif scope or rec.get("qualified"):
            scope_candidate = "partial_candidate"
        else:
            scope_candidate = "whole_order_candidate"
        row = {
            "event_id": f"{system}:ev:" + short_hash(edition, rec.get("citation"), rec.get("note_id"), subj_norm,
                                                       verb, acting_raw or actor_text, rec.get("sentence", "")[:200]),
            "system": system, "edition": edition, "citation": rec.get("citation", ""),
            "note_role": rec.get("note_role", ""), "subject_raw": rec.get("subject_raw", ""),
            "subject_normalized": subj_norm, "subject_instrument_id": subj_id,
            "subject_provisional_status": self.u.status(subj_id) if subj_id else "",
            "event_type_candidate": ENDING_VERBS.get(verb, verb),
            "actor_kind": kind or "unknown", "actor": actor_text, "acting_instrument_id": acting_id,
            "acting_raw": acting_raw, "acting_fr_citation": actor.get("fr") or "",
            "acting_scope": acting_scope[:200],
            "date_candidate": when or "", "scope_candidate": scope_candidate, "scope_hint": scope[:300],
            "caution": ";".join(cautions), "in_scope": in_scope,
            "sentence": eo_refs.clean(rec.get("sentence", ""))[:700], "source_id": source_id, "page_or_item": page_or_item,
        }
        self.events.append(row)
        return row

    # ----------------------------------------------------------- write --
    def dedupe(self):
        seen, out = set(), []
        for m in self.mentions:
            if m["mention_id"] in seen:
                continue
            seen.add(m["mention_id"])
            out.append(m)
        self.mentions = out
        seen, out = set(), []
        for e in self.events:
            if e["event_id"] in seen:
                continue
            seen.add(e["event_id"])
            out.append(e)
        self.events = out

    def mark_search_confirmation(self, search_complete):
        keys = {(h["title"], h["section"] or h["appendix"]) for h in self.search_hits}
        for m in self.mentions:
            if m["system"] != "ecfr" or m["route"] != "govinfo_ecfr_bulk_xml":
                continue
            if (m["title"], m["section_key"]) in keys:
                m["confirmed_at_cutoff_by_search"] = "yes"
            elif search_complete and m["location_kind"] in ("section_text", "appendix_text"):
                m["confirmed_at_cutoff_by_search"] = "no_hit_for_section"
            else:
                m["confirmed_at_cutoff_by_search"] = "not_checked"

    def _frag(self, frags, iid, kind):
        return frags.setdefault((iid, kind), {"instrument_id": iid, "kind": kind, "data": [], "sources": [],
                                              "confidence_note": "", "produced_by": PRODUCED_BY})

    def fragments(self):
        """One fragment per (instrument_id, kind), U.S. Code and eCFR entries merged.

        Field names end in ``_candidate`` on purpose: nothing here is a
        verified claim value, so a merge cannot copy them into claim fields
        (legal_basis, effective_date, date, actor, mechanism) unchecked.
        Long explanations are codes; SUMMARY.json "fragment_codes" spells them out.
        """
        frags = {}
        covered = {(m["title"], m["citation"], m["instrument_id"]) for m in self.mentions
                   if m["route"] == "govinfo_ecfr_bulk_xml" and m["checked_through"]}
        for m in self.mentions:
            if not m["instrument_id"] or m["is_predicate_lead"] != "yes":
                continue
            if m["route"] == "ecfr_search_api_point_in_time" and (m["title"], m["citation"], m["instrument_id"]) in covered:
                continue
            where = ("USC " if m["system"] == "usc" else "CFR ") + m["citation"]
            ref = self.ref(m["source_id"], m["page_or_item"])
            entry = {"system": m["system"], "legal_basis_candidate": f"{BASIS_LABELS[m['role']]} ({m['citation']})",
                     "basis_code": m["role"], "where": where, "edition": m["edition"], "snippet": m["snippet"],
                     "checked_through": m["checked_through"] or None, "currency_code": self.currency_code(m),
                     "mention_id": m["mention_id"], "source": ref}
            if m["role"] == "printed_eo_text" and m.get("note_id"):
                entry["text_path"] = f"USC_EO_NOTES.jsonl#note_id={m['note_id']}"
            frag = self._frag(frags, m["instrument_id"], "current_predicate_candidates")
            frag["data"].append(entry)
        for e in self.events:
            if not e["subject_instrument_id"] or e["in_scope"] != "yes" or any(c in e["caution"] for c in EXCLUDED_CAUTIONS):
                continue
            ref = self.ref(e["source_id"], e["page_or_item"])
            where = ("USC " if e["system"] == "usc" else "CFR ") + e["citation"]
            mechanism = f"{e['event_type_candidate']} (as stated in {'an OLRC note' if e['system'] == 'usc' else 'CFR text'} at {e['citation']})"
            date_code = "printed_next_to_acting_instrument" if e["date_candidate"] else None
            entry = {"system": e["system"], "date_candidate": e["date_candidate"] or None, "date_basis_code": date_code,
                     "actor_candidate": e["actor"] or None, "mechanism_candidate": mechanism,
                     "event_type_candidate": e["event_type_candidate"], "scope_candidate": e["scope_candidate"] or None,
                     "scope_hint": e["scope_hint"] or None, "acting_instrument_id": e["acting_instrument_id"] or None,
                     "acting_raw": e["acting_raw"] or None, "acting_scope": e["acting_scope"] or None,
                     "acting_fr_citation": e["acting_fr_citation"] or None, "caution": e["caution"] or None,
                     "where": where, "snippet": e["sentence"], "event_id": e["event_id"], "source": ref}
            self._frag(frags, e["subject_instrument_id"], "later_event_candidates")["data"].append(entry)
            if (e["event_type_candidate"] != "amendment" and e["scope_candidate"] == "whole_order_candidate"
                    and e["actor"] and e["caution"] in ("", "actor_is_amending_order_of_named_order")):
                w = {"system": e["system"], "date_candidate": e["date_candidate"] or None, "date_basis_code": date_code,
                     "actor_candidate": e["actor"], "mechanism_candidate": mechanism,
                     "acting_instrument_id": e["acting_instrument_id"] or None, "where": where, "snippet": e["sentence"],
                     "event_id": e["event_id"], "source": ref}
                self._frag(frags, e["subject_instrument_id"], "whole_order_end_candidates")["data"].append(w)
        order = {r: i for i, r in enumerate(PREDICATE_ROLES)}
        for (iid, kind), f in frags.items():
            extra = ""
            if kind == "current_predicate_candidates":
                f["data"].sort(key=lambda d: (d["checked_through"] is None, order.get(d["basis_code"], 99), d["system"], d["where"]))
            else:
                f["data"].sort(key=lambda d: (d["date_candidate"] or "9999", d["system"], d["where"]))
            if len(f["data"]) > MAX_ENTRIES_PER_FRAGMENT:
                extra = (f" Only the first {MAX_ENTRIES_PER_FRAGMENT} of {len(f['data'])} entries are kept here; "
                         f"MENTIONS.csv / EVENT_CANDIDATES.csv list them all.")
                f["data"] = f["data"][:MAX_ENTRIES_PER_FRAGMENT]
            for d in f["data"]:
                if d["source"] not in f["sources"]:
                    f["sources"].append(d["source"])
            f["confidence_note"] = CONFIDENCE_NOTES[kind] + extra
        return list(frags.values())

    def currency_code(self, m):
        if m["system"] == "usc":
            return "usc_release_point"
        if m["route"] == "ecfr_search_api_point_in_time":
            return "ecfr_search_point_in_time"
        if m["changed_after_cutoff"] == "no":
            return "ecfr_bulk_no_change_after_cutoff"
        return "ecfr_bulk_changed_or_unknown"

    def fragment_codes(self):
        """Lookup table for the codes used in FRAGMENTS.jsonl (written to SUMMARY.json)."""
        return {
            "basis_code": dict(PREDICATE_ROLES),
            "basis_code_placeholders": "{edition} = entry 'edition', {where} = entry 'where', {date} = " + eo_refs.LEGAL_CUTOFF,
            "currency_code": {
                "usc_release_point": self.usc_currency,
                "ecfr_search_point_in_time": f"eCFR search API queried with date={eo_refs.LEGAL_CUTOFF}: the section was in force on that date; the excerpt is partial.",
                "ecfr_bulk_no_change_after_cutoff": f"GovInfo eCFR bulk text; the eCFR versioner lists no change to this section after {eo_refs.LEGAL_CUTOFF} (title amendment dates in SUMMARY.json ecfr.titles), so the text should equal the cutoff text.",
                "ecfr_bulk_changed_or_unknown": f"GovInfo eCFR bulk text; the section changed after {eo_refs.LEGAL_CUTOFF} or its currency is unknown (MENTIONS.csv changed_after_cutoff); verify at the point-in-time URL in MENTIONS.csv human_url.",
            },
            "date_basis_code": {
                "printed_next_to_acting_instrument": "The date printed next to the acting order or law in the note (normally its signing or approval date). It is NOT a verified effective date.",
            },
            "scope_candidate": {
                "whole_order_candidate": "Nothing in the sentence limits the ending to part of the order. Still check the acting instrument.",
                "partial_candidate": "The sentence names a section, paragraph or provision, is a bracketed '[Revoked by ...]' insert inside the order's text, or is qualified ('insofar as', 'to the extent'); see scope_hint.",
            },
            "caution": {
                "subject_inside_prepositional_phrase": "The order is named inside a phrase such as 'as established by' or 'pursuant to', so the thing that ended is probably a rule, office or statute, not the order. Excluded from fragments; kept in EVENT_CANDIDATES.csv.",
                "repeal_wording_check_what_ended": "The verb is 'repealed', which the OLRC normally uses for statutes or rules; check that the order itself ended. Kept in later_event_candidates, not in whole_order_end_candidates.",
                "chronology_impossible": "The acting order's number is lower than the subject's: the parse is probably wrong. Excluded from fragments; kept in EVENT_CANDIDATES.csv.",
                "actor_is_amending_order_of_named_order": "The note says 'revoked by Ex. Ord. A, as amended by Ex. Ord. B'; B (the later order) is given as the actor.",
                "text_inserted_by_later_amendment_candidate": "The revoking text sits inside a printed order that is older than the subject, so a later amendment inserted it; candidates are named in actor_candidate.",
                "text_says_revoked_or_superseded": "(MENTIONS.csv) The same text says this order was revoked or superseded, so the mention is not a 'still operating' lead.",
                "possible_state_local_or_tribal_order": "(MENTIONS.csv) Words like Governor, State of, County or Tribe are near the reference.",
                "state_plan_approval_part": "(MENTIONS.csv) A CFR part approving State plans or programs, where 'Executive Order' usually means a Governor's order.",
            },
            "snippets": "Snippets are whitespace-normalized excerpts; ' | ' joins a heading to a status line or excerpt. They are not byte-verbatim quotes: quote from the source itself.",
        }

    usc_currency = ""
    ecfr_amddate = {}


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")


def order_table(book):
    """Per-order roll-up and the provisional-NO possible-conflict list."""
    by = defaultdict(lambda: {"usc": Counter(), "ecfr": Counter(), "usc_pred": 0, "ecfr_pred": 0,
                              "strong_roles": set(), "usc_cites": [], "cfr_cites": [], "snip": ""})
    for m in book.mentions:
        if not m["instrument_id"]:
            continue
        d = by[m["instrument_id"]]
        d[m["system"]][m["role"]] += 1
        if m["is_predicate_lead"] == "yes":
            d[m["system"] + "_pred"] += 1
            if m["role"] != "amending_order_in_status_line":
                d["strong_roles"].add(m["role"])
            lst = d["usc_cites" if m["system"] == "usc" else "cfr_cites"]
            if m["citation"] not in lst:
                lst.append(m["citation"])
            if not d["snip"] or (m["role"] != "amending_order_in_status_line" and d.get("snip_weak")):
                d["snip"] = m["snippet"][:300]
                d["snip_weak"] = m["role"] == "amending_order_in_status_line"
    ends = defaultdict(set)
    amends = Counter()
    for e in book.events:
        if e["subject_instrument_id"] and e["in_scope"] == "yes" and not any(c in e["caution"] for c in EXCLUDED_CAUTIONS):
            if e["event_type_candidate"] == "amendment":
                amends[e["subject_instrument_id"]] += 1
            else:
                ends[e["subject_instrument_id"]].add(e["event_type_candidate"])
    rows, conflicts = [], []
    for iid in sorted(set(by) | set(ends) | set(amends)):
        d = by[iid]
        status = book.u.status(iid)
        printed = d["usc"].get("printed_eo_text", 0)
        row = {"instrument_id": iid, "provisional_status": status,
               "usc_mentions": sum(d["usc"].values()), "usc_predicate_leads": d["usc_pred"], "usc_printed_text_notes": printed,
               "ecfr_mentions": sum(d["ecfr"].values()), "ecfr_predicate_leads": d["ecfr_pred"],
               "ending_statements_found": ";".join(sorted(ends[iid])), "amendment_statements_found": amends[iid],
               "usc_predicate_citations": " ; ".join(d["usc_cites"][:6]), "cfr_predicate_citations": " ; ".join(d["cfr_cites"][:6])}
        row["possible_conflict"] = "yes" if status == "no" and (d["usc_pred"] or d["ecfr_pred"]) else ""
        rows.append(row)
        if row["possible_conflict"]:
            if printed and not ends[iid]:
                signal = "1_printed_as_current_text_in_usc"
            elif d["strong_roles"] - {"printed_eo_text"}:
                signal = "2_cited_by_statute_or_regulation"
            elif printed:
                signal = "3_printed_text_but_ending_statement_also_found"
            else:
                signal = "4_only_listed_as_amendment_of_a_printed_order"
            conflicts.append(dict(row, decision_origin=getattr(book.u, "origins", {}).get(iid, ""), signal=signal,
                                  strong_roles=";".join(sorted(d["strong_roles"])), example_snippet=d["snip"],
                                  note="Lead only: the provisional status is NOT changed. A NO order can be cited by current law for historical, definitional or savings reasons."))
    conflicts.sort(key=lambda c: (c["signal"], c["instrument_id"]))
    return rows, conflicts


ORDER_FIELDS = ["instrument_id", "provisional_status", "usc_mentions", "usc_predicate_leads", "usc_printed_text_notes",
                "ecfr_mentions", "ecfr_predicate_leads", "ending_statements_found", "amendment_statements_found",
                "possible_conflict", "usc_predicate_citations", "cfr_predicate_citations"]
CONFLICT_FIELDS = ["instrument_id", "decision_origin", "signal", "strong_roles", "usc_predicate_leads", "usc_printed_text_notes",
                   "ecfr_predicate_leads", "ending_statements_found", "usc_predicate_citations", "cfr_predicate_citations",
                   "example_snippet", "note"]
