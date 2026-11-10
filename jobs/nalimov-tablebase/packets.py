"""Nalimov verification packets: one actor text, then every target claim it settles, plus typed planted controls.

A verifier does not research. It reads, for each acting instrument, the decisive held text once (the whole text when
it is short, exact windows around each decisive sentence when it is long), and for each target the claim fields the
drafter filled, each clause's held text with the state assigned to it, the order's own text that lies outside the
clauses, every held act on the order, every catalog entry and U.S. Code note, and the resolved flags. It answers uphold
or reject per entry with defect codes from a fixed list (prompts/verifier.md).

Sessions group several actor blocks (about 12 targets per session, never splitting an actor) so the actor text is
paid for once per session. Sessions run in dependency order (topological: a parent's batch before its amendment-only
children's), largest actor batches first. There are always at least two sessions, so every control can sit apart
from its genuine twin.

Controls are planted inside each session, sealed in a key kept outside the scratch tree the workers can reach: at
least `MIN_CONTROLS` per session and one per 15 genuine entries (rounded up), of at least two kinds, at least one
status-determining (Respondendi RULE.md `status_control_kinds`). Two families:
- mutations of a genuine entry from ANOTHER session (so no session holds both a control and its twin), with its own
  copy of the actor block, edited consistently where the defect is in the text: `date_shift`,
  `ending_source_swapped`, `wrong_order_text` (clauses of an order from a third session), `partial_as_whole` (the
  decisive sentence is qualified in the actor text too);
- decoys, when the census supplies them: real orders the drafter refused only because another instrument acts on them
  or the same actor acts on part of them, drafted with that one blocker ignored (drafter.draft(ignore=...)), so the
  claim is wrong in exactly the way a drafter bug would make it wrong (`later_event_removed`, `partial_as_whole`).
  Their evidence is in `evidence_on_order`, a field every entry carries (genuine entries list their own revoking
  records there). At most one decoy a session.
A control is caught only if the arm rejects it and names a defect code its kind maps to (CATCH).
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import re

MAX_ACTOR_TEXT = 20000      # an actor text up to this many characters is sent whole; a longer one as windows
WINDOW = 1500
SESSION_TARGETS = 12
MIN_CONTROLS = 2
CLAUSE_CAP = 2400
DEFECT_CODES = {
    "wrong_end_date": "the end date, or a clause's first-end date, does not follow from the decisive text",
    "actor_does_not_name_order": "the quoted decisive sentence does not name this order, or is not in the actor text",
    "qualified_or_partial_end": "the decisive sentence ends only part of the order, or is qualified",
    "later_event_omitted": "held evidence shows another instrument acting on the order (or the same one acting on part "
                           "of it) that the claim leaves out",
    "wrong_order_text": "the clause texts are not this order's text (another order's text, or wrong identity)",
    "inventory_incomplete": "an operative command of the order is in no clause, or a clause merges several",
    "clause_state_wrong": "a clause's assigned state, mechanism or date is wrong (e.g. a one-time act dated by the revocation)",
    "savings_missed": "the actor text preserves something done under or continued from the order",
    "witness_contradicts": "a catalog note or U.S. Code note contradicts the claim",
    "other": "any other defect (explain)",
}
CATCH = {"date_shift": {"wrong_end_date"}, "ending_source_swapped": {"actor_does_not_name_order"},
         "wrong_order_text": {"wrong_order_text"},
         "partial_as_whole": {"qualified_or_partial_end", "later_event_omitted"},
         "later_event_removed": {"later_event_omitted"}}
STATUS_DETERMINING = {"ending_source_swapped", "wrong_order_text", "partial_as_whole", "later_event_removed"}
MUTATIONS = ("date_shift", "ending_source_swapped", "wrong_order_text", "partial_as_whole")
QUALIFIER = ", except sections 2 and 3 thereof, which shall remain in effect."


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clip(text, cap):
    text = str(text or "")
    return text if len(text) <= cap else text[:cap] + f" [... {len(text) - cap} more characters; sha256 of the full text given]"


def entry_id(e):
    return "E-" + sha(canon({k: v for k, v in e.items() if k != "entry_id"}))[:12]


def _seal(e):
    e.pop("entry_id", None)
    e["entry_id"] = entry_id(e)
    return e


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
    acts = []
    for k, r in sorted(recs.items()):
        if k.startswith("ACT:"):
            acts.append({"id": k, "actor_id": r.get("actor_id"), "verb": r.get("verb"), "scope": r.get("scope"),
                         "signing_date": r.get("signing_date"),
                         "text": _clip(r.get("provision_text") or r.get("text"), 900),
                         "page_or_item": (r.get("source") or {}).get("page_or_item")})
    claim = {"status": "no",
             "whole_order_end": {"date": f["end_date"], "actor": f["actor_id"], "mechanism": f.get("mechanism"),
                                 "source": f["act_id"], "quote": f["provision_text"],
                                 "quote_sha256": f["provision_sha256"], "locator": f["provision_locator"]},
             "later_events": [], "savings": draft["row"]["savings_reason"],
             "searches": json.loads(draft["row"]["search_ids"]),
             "checks": {k: draft["row"][k] for k in ("earlier_end_check", "scope_check", "independent_command_check")}}
    out = {"instrument_id": f["instrument_id"], "signing_date": f["signing_date"], "actor_id": f["actor_id"],
           "original": {"id": f["original_id"], **f["original_locator"]}, "clauses": clauses,
           "text_outside_clauses": [{"where": u["where"], "text": _clip(u["text"], 1500)}
                                    for u in f.get("unclaimed_text") or []],
           "claim": claim,
           "witnesses": {"ofr_catalog_entries": list(f.get("catalog_entries") or []),
                         "us_code_notes": [{"citation": n.get("citation"), "text": _clip(n.get("snippet"), 600)}
                                           for n in f.get("current_law_notes") or []]},
           "resolved": {**(draft.get("decision") or {}).get("conflict_resolutions", {}),
                        **json.loads(draft["row"].get("conflict_resolutions") or "{}")},
           "conflict_actor_texts": [{"actor_id": x["actor_id"], "page_or_item": x.get("page_or_item"),
                                     "text": _clip(x["text"], 6000)} for x in f.get("conflict_actor_texts") or []],
           "evidence_on_order": acts}
    return _seal(out)


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
        decisive.append({"target": f["instrument_id"], "label": f["provision_label"], "text": f["provision_text"],
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


def sessions(actor_order, batches, size=SESSION_TARGETS, minimum=2):
    """Consecutive actor batches, about `size` targets each, never splitting an actor; at least `minimum` sessions
    when there are at least that many actors."""
    total = sum(len(batches[a]) for a in actor_order)
    if len(actor_order) >= minimum:
        size = min(size, max(1, math.ceil(total / minimum)))
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


def mutate(e, kind, rng, donors, block):
    """(planted entry, its actor block) from genuine entry e and a copy of its actor block, with one typed defect, or
    None when no donor fits. donors: genuine entries of sessions other than e's and the planting session's."""
    p = copy.deepcopy(e)
    b = copy.deepcopy(block)
    p.pop("entry_id", None)
    end = p["claim"]["whole_order_end"]
    others = [o for o in donors if o["instrument_id"] != e["instrument_id"]]
    if kind == "date_shift":
        old, new = end["date"], _shift(end["date"])
        end["date"] = new
        for c in p["clauses"]:
            if c["assigned"]["mechanism"] in ("express_revocation", "express_supersession"):
                c["assigned"]["first_end_date"] = new
        p["claim"]["checks"] = {k: v.replace(old, new) for k, v in p["claim"]["checks"].items()}
    elif kind == "ending_source_swapped":
        pool = [o for o in others if o["claim"]["whole_order_end"]["quote"] != end["quote"]]
        if not pool:
            return None
        d = rng.choice(pool)["claim"]["whole_order_end"]
        end.update(quote=d["quote"], quote_sha256=d["quote_sha256"], locator=copy.deepcopy(d["locator"]))
    elif kind == "wrong_order_text":
        pool = [o for o in others if o["clauses"]]
        if not pool:
            return None
        d = rng.choice(pool)
        assigned = [c["assigned"] for c in e["clauses"]] or [None]
        p["clauses"] = []
        for i, c in enumerate(copy.deepcopy(d["clauses"])):
            c["scope_id"] = re.sub(r"^EO:[^#]+", e["instrument_id"], c["scope_id"])
            c["assigned"] = copy.deepcopy(assigned[min(i, len(assigned) - 1)])
            p["clauses"].append(c)
        p["text_outside_clauses"] = copy.deepcopy(d["text_outside_clauses"])
    elif kind == "partial_as_whole":
        old = end["quote"]
        new = old.rstrip(". ") + QUALIFIER
        end.update(quote=new, quote_sha256=sha(new))
        loc = end.get("locator") or {}
        if isinstance(loc.get("char_end"), int):
            loc["char_end"] += len(new) - len(old)
        for dec in b["decisive"]:
            if dec["text"] == old:
                dec.update(text=new, sha256=sha(new))
        if b.get("text_form") == "whole" and old in b["text"]:
            b["text"] = b["text"].replace(old, new, 1)
        for w in b.get("windows") or []:
            if old in w["text"]:
                w["text"] = w["text"].replace(old, new, 1)
                w["char_end"] += len(new) - len(old)
        # text_sha256 is the held file's hash on every block (genuine ones too), so it is left as it is.
    else:
        raise ValueError(kind)
    b["decisive"] = [x for x in b["decisive"] if x["target"] == e["instrument_id"]]
    return _seal(p), b


def _n_controls(n):
    return max(MIN_CONTROLS, math.ceil(n / 15))


def build(drafted, evidence_by_id, salt, edges=(), decoys=None, size=SESSION_TARGETS):
    """Verification sessions and their sealed key.

    drafted: complete drafts; evidence_by_id: their frozen evidence; salt: a secret (kept with the key, never in a
    packet); edges: (child, parent) dependency pairs; decoys: [(kind, draft, evidence)] real refused orders drafted
    with one blocker ignored. Returns (sessions, key): each session {'session', 'actors', 'entries'}; key
    {'salt_sha256', 'sessions': {name: {'controls': [...], 'genuine': [{entry_id, instrument_id}]}}}.
    Needs at least two acting instruments (a control never shares a session with its twin)."""
    rng = random.Random(sha("nalimov-controls:" + salt))
    batches = {}
    for dr in drafted:
        batches.setdefault(dr["facts"]["actor_id"], []).append(dr)
    if len(batches) < 2:
        raise ValueError("at least two acting instruments are needed, so no control shares a session with its twin")
    order = topological({a: [d["instrument_id"] for d in v] for a, v in batches.items()}, edges)
    groups = sessions(order, {a: batches[a] for a in order}, size)
    genuine = [[entry(dr, evidence_by_id[dr["instrument_id"]]) for a in g for dr in batches[a]] for g in groups]
    blocks = [[actor_block(a, [evidence_by_id[d["instrument_id"]] for d in batches[a]], batches[a]) for a in g]
              for g in groups]
    block_of = {e["instrument_id"]: blk for gi, g in enumerate(groups) for blk in blocks[gi] for e in genuine[gi]
                if e["actor_id"] == blk["actor_id"]}
    pool = [(k, dr, ev) for k, dr, ev in (decoys or []) if any(
        x.startswith(("another_instrument_acts", "same_actor_partial_act")) for x in dr.get("ignored") or [])]
    rng.shuffle(pool)
    out, key = [], {"salt_sha256": sha(salt), "sessions": {}}
    for gi, g in enumerate(groups):
        name = f"s{gi + 1:03d}"
        n = _n_controls(len(genuine[gi]))
        planted, extra_blocks, rows, kinds = [], [], [], []
        if pool:
            kind, dr, ev = pool.pop()
            de = entry(dr, ev)
            planted.append(de)
            extra_blocks.append(actor_block(dr["facts"]["actor_id"], [ev], [dr]))
            rows.append({"entry_id": de["entry_id"], "control_kind": kind, "family": "decoy",
                         "instrument_id": de["instrument_id"], "genuine_entry_id": None, "genuine_session": None,
                         "catch": sorted(CATCH[kind])})
            kinds.append(kind)
        other_sessions = [j for j in range(len(groups)) if j != gi]
        used = {x["instrument_id"] for x in genuine[gi]} | {x["instrument_id"] for x in planted}
        donated = set()
        attempts = 0
        while (len(planted) < n or len(set(kinds)) < 2 or not STATUS_DETERMINING & set(kinds)) and attempts < 40:
            attempts += 1
            todo = [k for k in MUTATIONS if k not in kinds] or list(MUTATIONS)
            if not STATUS_DETERMINING & set(kinds):
                todo = [k for k in todo if k in STATUS_DETERMINING] or todo
            kind = rng.choice(todo)
            tj = rng.choice(other_sessions)
            twins = [x for x in genuine[tj] if x["instrument_id"] not in used]
            if not twins:
                continue
            twin = rng.choice(twins)
            donors = [x for j in range(len(groups)) if j != gi for x in genuine[j]
                      if x["instrument_id"] != twin["instrument_id"] and x["instrument_id"] not in donated]
            got = mutate(twin, kind, rng, donors, block_of[twin["instrument_id"]])
            if got is None:
                continue
            p, b = got
            trial = {"entries": genuine[gi] + planted + [p]}
            if tells(trial):
                continue            # e.g. a donor's clause text already in this session
            donated |= {x["instrument_id"] for x in donors
                        if any(c["text_sha256"] in {k["text_sha256"] for k in p["clauses"]} for c in x["clauses"])}
            planted.append(p)
            extra_blocks.append(b)
            used.add(p["instrument_id"])
            rows.append({"entry_id": p["entry_id"], "control_kind": kind, "family": "mutation",
                         "instrument_id": p["instrument_id"], "genuine_entry_id": twin["entry_id"],
                         "genuine_session": f"s{tj + 1:03d}", "catch": sorted(CATCH[kind])})
            kinds.append(kind)
        if len(planted) < n or len(set(kinds)) < 2 or not STATUS_DETERMINING & set(kinds):
            raise ValueError(f"{name}: could not plant {n} controls of two kinds with one status-determining")
        entries = genuine[gi] + planted
        if tells({"entries": entries}):
            raise ValueError(f"{name}: planted controls leave a mechanical tell: {tells({'entries': entries})[:2]}")
        rng.shuffle(entries)
        acts = blocks[gi] + extra_blocks
        rng.shuffle(acts)
        out.append({"session": name, "actors": acts, "entries": entries})
        key["sessions"][name] = {"controls": rows, "genuine": [{"entry_id": x["entry_id"], "instrument_id": x["instrument_id"]}
                                                              for x in genuine[gi]]}
    return out, key


def tells(session):
    """Mechanical giveaways a verifier could use without reading the law: duplicate order ids, clause texts shared by
    two entries, entries without held acts, decisive sentences absent from their actor block. Empty when clean."""
    out = []
    ids = [e["instrument_id"] for e in session["entries"]]
    if len(ids) != len(set(ids)):
        out.append("duplicate instrument_id")
    seen = {}
    for e in session["entries"]:
        for c in e["clauses"]:
            if len(c["text"]) < 200:
                continue   # short boilerplate ("This order shall take effect immediately.") recurs between orders
            if c["text_sha256"] in seen and seen[c["text_sha256"]] != e["entry_id"]:
                out.append(f"clause text shared by two entries: {c['text_sha256'][:12]}")
            seen[c["text_sha256"]] = e["entry_id"]
        if not e.get("evidence_on_order"):
            out.append(f"entry without held acts: {e['instrument_id']}")
        if sha(e["claim"]["whole_order_end"]["quote"]) != e["claim"]["whole_order_end"]["quote_sha256"]:
            out.append(f"quote hash differs from the quote shown: {e['instrument_id']}")
    return out


def measure(session):
    """Characters and a token estimate (4 characters a token) of one session's packet, and per target."""
    chars = len(canon(session))
    n = len(session["entries"])
    return {"chars": chars, "tokens_est": round(chars / 4), "entries": n,
            "tokens_est_per_entry": round(chars / 4 / max(1, n))}


def review_bundle(drafted, evidence_by_id, edges=()):
    """Reviewer context for the conveyor's blind arms (--producer nalimov): one block per acting instrument, with its
    held text once and the packet entry of every target it settles, in dependency order. No controls: the conveyor
    plants its own typed controls in the claims, and this bundle is built from the genuine drafts only, so it must be
    given to reviewers as context for the claims they review, never as the thing reviewed."""
    batches = {}
    for dr in drafted:
        batches.setdefault(dr["facts"]["actor_id"], []).append(dr)
    order = topological({a: [d["instrument_id"] for d in v] for a, v in batches.items()}, edges)
    out = []
    for a in order:
        evs = [evidence_by_id[d["instrument_id"]] for d in batches[a]]
        block = actor_block(a, evs, batches[a])
        out.append({"actor": block, "targets": [d["instrument_id"] for d in batches[a]]})
    return {"schema": "nalimov-review-bundle/v1", "actors": out}
