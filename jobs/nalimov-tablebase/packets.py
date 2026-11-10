"""Nalimov verification packets: one actor text, then every target claim it settles, plus typed planted controls.

A verifier does not research. It reads, for each acting instrument, the decisive held text once (the whole text when
it is short, exact windows around each decisive sentence when it is long), and for each target the claim fields the
drafter filled, each clause's held text with the state assigned to it, the witnesses and the resolved flags. It
answers uphold or reject per entry with defect codes from a fixed list (prompts/verifier.md).

Sessions group several actor blocks (about 12 targets per session, never splitting an actor) so the actor text is
paid for once per session. Sessions run in dependency order (topological: a parent's batch before its amendment-only
children's), largest actor batches first.

Controls are planted inside each session, sealed in a key outside the packet folder: at least `MIN_CONTROLS` per
session, of at least two kinds, at least one status-determining (Respondendi RULE.md `status_control_kinds`). Two
families:
- mutations of a genuine entry: `date_shift`, `ending_source_swapped`, `wrong_order_text`, `partial_as_whole`;
- decoys, when the census supplies them: real orders the drafter refused for a real reason (another instrument amends
  the order; the same actor acts on only part of it), drafted with that one blocker ignored (drafter.draft(ignore=...)),
  so the claim is wrong in exactly the way a drafter bug would make it wrong (`later_event_removed`,
  `partial_as_whole`). At most one decoy a session, so decoys never outnumber the mutations around them.
A control is caught only if the arm rejects it and names the defect code its kind maps to (CATCH).
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
import re

import drafter as D

MAX_ACTOR_TEXT = 20000      # an actor text up to this many characters is sent whole; a longer one as windows
WINDOW = 1500
SESSION_TARGETS = 12
MIN_CONTROLS = 2
CLAUSE_CAP = 2400
DEFECT_CODES = {
    "wrong_end_date": "the end date, or a clause's first-end date, does not follow from the decisive text",
    "actor_does_not_name_order": "the quoted decisive sentence does not name this order, or is not in the actor text",
    "qualified_or_partial_end": "the decisive sentence ends only part of the order, or is qualified",
    "later_event_omitted": "held evidence shows another instrument acting on the order that the claim leaves out",
    "wrong_order_text": "the clause texts are not this order's text (another order's text, or wrong identity)",
    "inventory_incomplete": "an operative command of the order is in no clause, or a clause merges several",
    "clause_state_wrong": "a clause's assigned state, mechanism or date is wrong (e.g. a one-time act dated by the revocation)",
    "savings_missed": "the actor text preserves something done under or continued from the order",
    "witness_contradicts": "a catalog note or U.S. Code note contradicts the claim",
    "other": "any other defect (explain)",
}
CATCH = {"date_shift": {"wrong_end_date"}, "ending_source_swapped": {"actor_does_not_name_order"},
         "wrong_order_text": {"wrong_order_text"}, "partial_as_whole": {"qualified_or_partial_end"},
         "later_event_removed": {"later_event_omitted"}}
STATUS_DETERMINING = {"ending_source_swapped", "wrong_order_text", "partial_as_whole", "later_event_removed"}
MUTATIONS = ("date_shift", "ending_source_swapped", "wrong_order_text", "partial_as_whole")


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clip(text, cap):
    text = str(text or "")
    return text if len(text) <= cap else text[:cap] + f" [... {len(text) - cap} more characters; sha256 of the full clause given]"


def entry(draft, evidence):
    """The verification packet entry for one drafted order: claim fields and the held text they rest on."""
    f = draft["facts"]
    recs = (evidence.get("base_dossier") or {}).get("evidence") or {}
    rows = {c["scope_id"]: c for c in draft["clauses"]}
    clauses = []
    for c in (evidence.get("base_dossier") or {}).get("clauses") or []:
        text = str(c.get("text") or (recs.get(c.get("id")) or {}).get("text") or "")
        r = rows.get(c["scope_id"]) or {}
        clauses.append({"scope_id": c["scope_id"], "label": c.get("label"), "chars": [c.get("char_start"), c.get("char_end")],
                        "text": _clip(text, CLAUSE_CAP), "text_sha256": sha(text),
                        "assigned": {"state": r.get("state"), "first_end_date": r.get("effective_date"),
                                     "mechanism": r.get("mechanism"), "end_source": r.get("end_id")}})
    others = []
    for k, r in sorted(recs.items()):
        if k.startswith("ACT:") and (r.get("actor_id") != f["actor_id"] or r.get("scope") == "partial"):
            others.append({"id": k, "actor_id": r.get("actor_id"), "verb": r.get("verb"), "scope": r.get("scope"),
                           "signing_date": r.get("signing_date"), "text": _clip(r.get("provision_text") or r.get("text"), 900),
                           "page_or_item": (r.get("source") or {}).get("page_or_item")})
    claim = {"status": "no",
             "whole_order_end": {"date": f["end_date"], "actor": f["actor_id"], "mechanism": "express_revocation",
                                 "source": f["act_id"], "quote": f["provision_text"].strip(),
                                 "quote_sha256": f["provision_sha256"], "locator": f["provision_locator"]},
             "later_events": [], "savings": draft["row"]["savings_reason"],
             "searches": json.loads(draft["row"]["search_ids"]),
             "checks": {k: draft["row"][k] for k in ("earlier_end_check", "scope_check", "independent_command_check")}}
    out = {"instrument_id": f["instrument_id"], "signing_date": f["signing_date"], "actor_id": f["actor_id"],
           "original": {"id": f["original_id"], **f["original_locator"]}, "clauses": clauses, "claim": claim,
           "witnesses": {"ofr_catalog": f.get("witness"), "us_code_notes": [
               {"citation": n.get("citation"), "text": _clip(n.get("snippet"), 600)} for n in f.get("current_law_notes") or []]},
           "resolved": {**(draft.get("decision") or {}).get("conflict_resolutions", {}),
                        **json.loads(draft["row"].get("conflict_resolutions") or "{}")},
           "other_acts_on_order": others}
    return _seal(out)


def entry_id(e):
    return "E-" + sha(canon({k: v for k, v in e.items() if k != "entry_id"}))[:12]


def _seal(e):
    e.pop("entry_id", None)
    e["entry_id"] = entry_id(e)
    return e


def actor_block(actor_id, evidence_list, drafts):
    """The actor's held text, once: whole when short, else exact windows around each decisive sentence."""
    recs = {}
    for ev in evidence_list:
        recs.update((ev.get("base_dossier") or {}).get("evidence") or {})
    at = recs.get(f"ACTOR_TEXT:{actor_id}") or {}
    text = str(at.get("text") or "")
    src = at.get("source") or {}
    decisive = []
    for dr in drafts:
        f = dr["facts"]
        decisive.append({"target": f["instrument_id"], "label": f["provision_label"], "text": f["provision_text"].strip(),
                         "sha256": f["provision_sha256"], **f["provision_locator"]})
    signed = next((dr["facts"]["actor_signing_date"] for dr in drafts), None)
    block = {"actor_id": actor_id, "signing_date": signed, "page_or_item": src.get("page_or_item"),
             "text_path": src.get("text_path"), "text_sha256": src.get("text_sha256"), "decisive": decisive}
    if text and len(text) <= MAX_ACTOR_TEXT:
        block.update(text=text, text_form="whole")
    elif text:
        spans = []
        for d in decisive:
            i = text.find(d["text"])
            if i >= 0:
                spans.append((max(0, i - WINDOW), min(len(text), i + len(d["text"]) + WINDOW)))
        merged = []
        for a, b in sorted(spans):
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
            else:
                merged.append((a, b))
        block.update(text_form="windows", windows=[{"char_start": a, "char_end": b, "text": text[a:b]} for a, b in merged],
                     text_chars=len(text))
    else:
        block.update(text_form="decisive_sentences_only")
    return block


def topological(batches, edges):
    """Order actor batches so that every parent's batch comes before a child's (edges: child -> parent ids);
    otherwise largest batches first. A cycle is refused."""
    where = {t: a for a, ts in batches.items() for t in ts}
    deps = {a: set() for a in batches}
    for child, parent in edges:
        if child in where and parent in where and where[child] != where[parent]:
            deps[where[child]].add(where[parent])
    order, done = [], set()
    pending = sorted(batches, key=lambda a: (-len(batches[a]), a))
    while pending:
        ready = [a for a in pending if deps[a] <= done]
        if not ready:
            raise ValueError("dependency cycle among actor batches: " + ", ".join(pending[:5]))
        a = ready[0]
        order.append(a)
        done.add(a)
        pending.remove(a)
    return order


def sessions(actor_order, batches, size=SESSION_TARGETS):
    out, cur, n = [], [], 0
    for a in actor_order:
        k = len(batches[a])
        if cur and n + k > size:
            out.append(cur)
            cur, n = [], 0
        cur.append(a)
        n += k
    if cur:
        out.append(cur)
    return out


def _shift(d):
    if not isinstance(d, str) or len(d) < 10:
        return d
    md = "-02-28" if d[4:10] == "-02-29" else d[4:10]
    return f"{int(d[:4]) - 3:04d}{md}"


def mutate(e, kind, rng, pool):
    """A planted copy of genuine entry e with one typed defect, or None when the session cannot supply it.
    pool: the session's genuine entries (donors for swaps)."""
    p = copy.deepcopy(e)
    p.pop("entry_id", None)
    end = p["claim"]["whole_order_end"]
    others = [o for o in pool if o["instrument_id"] != e["instrument_id"]]
    if kind == "date_shift":
        old, new = end["date"], _shift(end["date"])
        end["date"] = new
        for c in p["clauses"]:
            if c["assigned"]["mechanism"] == "express_revocation":
                c["assigned"]["first_end_date"] = new
        p["claim"]["checks"] = {k: v.replace(old, new) for k, v in p["claim"]["checks"].items()}
    elif kind == "ending_source_swapped":
        donors = [o for o in others if o["claim"]["whole_order_end"]["quote"] != end["quote"]]
        if not donors:
            return None
        d = rng.choice(donors)["claim"]["whole_order_end"]
        end.update(quote=d["quote"], quote_sha256=d["quote_sha256"], locator=copy.deepcopy(d["locator"]))
    elif kind == "wrong_order_text":
        donors = [o for o in others if o["clauses"]]
        if not donors:
            return None
        d = rng.choice(donors)
        assigned = [c["assigned"] for c in e["clauses"]] or [None]
        p["clauses"] = []
        for i, c in enumerate(copy.deepcopy(d["clauses"])):
            c["scope_id"] = re.sub(r"^EO:[^#]+", e["instrument_id"], c["scope_id"])
            c["assigned"] = copy.deepcopy(assigned[min(i, len(assigned) - 1)])
            p["clauses"].append(c)
    elif kind == "partial_as_whole":
        end["quote"] = end["quote"].rstrip(". ") + ", except sections 2 and 3 thereof, which shall remain in effect."
        end["quote_sha256"] = sha(end["quote"])
    else:
        raise ValueError(kind)
    return _seal(p)


def plant(session_entries, rng, decoys=()):
    """(controls, key rows) for one session. decoys: (kind, entry) pairs of real refused orders drafted with one
    blocker ignored. At least MIN_CONTROLS (and one per 15 genuine entries), of at least two kinds, at least one
    status-determining."""
    n = max(MIN_CONTROLS, round(len(session_entries) / 15))
    planted, key, kinds = [], [], []
    for kind, dec in list(decoys)[:n]:
        planted.append(dec)
        key.append({"entry_id": dec["entry_id"], "control_kind": kind, "family": "decoy",
                    "instrument_id": dec["instrument_id"], "genuine_entry_id": None, "catch": sorted(CATCH[kind])})
        kinds.append(kind)
    order = list(MUTATIONS)
    rng.shuffle(order)
    order.sort(key=lambda k: (k in kinds, k not in STATUS_DETERMINING if not STATUS_DETERMINING & set(kinds) else 0))
    for kind in order:
        if len(planted) >= n and len(set(kinds)) >= 2 and STATUS_DETERMINING & set(kinds):
            break
        base = rng.choice(session_entries)
        p = mutate(base, kind, rng, session_entries)
        if p is None:
            continue
        planted.append(p)
        key.append({"entry_id": p["entry_id"], "control_kind": kind, "family": "mutation",
                    "instrument_id": p["instrument_id"], "genuine_entry_id": base["entry_id"], "catch": sorted(CATCH[kind])})
        kinds.append(kind)
    if len(set(kinds)) < 2 or not STATUS_DETERMINING & set(kinds):
        raise ValueError("could not plant two control kinds with one status-determining (session too small?)")
    return planted, key


def build(drafted, evidence_by_id, salt, edges=(), decoys=None, size=SESSION_TARGETS):
    """Verification sessions and their sealed key.

    drafted: complete drafts; evidence_by_id: their frozen evidence; salt: a secret (kept with the key, never in a
    packet); edges: (child, parent) dependency pairs; decoys: [(kind, draft, evidence)] real refused orders drafted
    with one blocker ignored. Returns (sessions, key): each session {'session', 'actors', 'entries'}; key
    {'salt_sha256', 'sessions': {name: {'controls': [...], 'genuine': [{entry_id, instrument_id}]}}}."""
    rng = random.Random(sha("nalimov-controls:" + salt))
    batches = {}
    for dr in drafted:
        batches.setdefault(dr["facts"]["actor_id"], []).append(dr)
    order = topological({a: [d["instrument_id"] for d in v] for a, v in batches.items()}, edges)
    pool = list(decoys or [])
    rng.shuffle(pool)
    out, key = [], {"salt_sha256": sha(salt), "sessions": {}}
    for i, actors in enumerate(sessions(order, {a: batches[a] for a in order}, size), 1):
        name = f"s{i:03d}"
        genuine = [entry(dr, evidence_by_id[dr["instrument_id"]]) for a in actors for dr in batches[a]]
        mine = [pool.pop() for _ in range(min(1, len(pool)))]      # at most one decoy a session; mutations fill the rest
        dec_entries = [(kind, entry(dr, ev)) for kind, dr, ev in mine]
        planted, k = plant(genuine, rng, dec_entries)
        blocks = [actor_block(a, [evidence_by_id[d["instrument_id"]] for d in batches[a]], batches[a]) for a in actors]
        for kind, dr, ev in mine:
            if dr["facts"]["actor_id"] not in actors:
                blocks.append(actor_block(dr["facts"]["actor_id"], [ev], [dr]))
        rng.shuffle(blocks)
        entries = genuine + planted
        rng.shuffle(entries)
        out.append({"session": name, "actors": blocks, "entries": entries})
        key["sessions"][name] = {"controls": k, "genuine": [{"entry_id": g["entry_id"], "instrument_id": g["instrument_id"]}
                                                           for g in genuine]}
    return out, key


def measure(session):
    """Characters and a token estimate (4 characters a token) of one session's packet, and per target."""
    chars = len(canon(session))
    n = len(session["entries"])
    return {"chars": chars, "tokens_est": round(chars / 4), "entries": n,
            "tokens_est_per_entry": round(chars / 4 / max(1, n))}
