"""Nalimov census: how many orders a script can complete fully, per kind, and what blocks the rest.

Zero tokens. Reads a checkout that holds main's compiled outputs (claim-kit, readiness-tracker, current-law, pothier,
later-events) and runs the real drafter on real frozen evidence:

- express_named_revocation (undecided): every undecided order with an ACT record that passes Respondendi's sentence
  predicate is frozen with the kit's own `status_overlay.prepare_evidence_many` (the code of the data checkout, so
  the compiler pins match its outputs) and drafted. "Complete" means the drafter filled every field and the kit's
  `_decision_errors` gate returns nothing.
- decided_express (decided NO orders with no ready claim): the compiled dossier is drafted on the decided route.
- amendment_only (Pothier P2 'merged into parent on issue', undecided): counted with the parent's state; the kit has
  no OWN_TEXT / PARENT_END records on main (F5, PR #274), so none is scriptable until that route is live.
- own_terms (undecided): Respondendi's own-terms lead predicate; reported with the reasons it blocks.

Output: CENSUS.json (counts, blockers, actor batches, dependency order) and CENSUS.csv (one row per order looked at).

    python -I jobs/nalimov-tablebase/census.py --data C:/Users/danie/eo-wt/accursius --out research/nalimov/census
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import importlib
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drafter as D  # noqa: E402
import predicate as P  # noqa: E402

csv.field_size_limit(1 << 30)
# Orders refused only for one of these reasons make realistic decoy controls (packets.py): the claim the drafter
# would write if it ignored the blocker is wrong in a known, typed way.
DECOY_BLOCKERS = {"another_instrument_acts", "chain_event_by_another_actor", "same_actor_partial_act"}


def jsonl(paths):
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def num(iid):
    m = re.match(r"\D*(\d+)", iid or "")
    return int(m.group(1)) if m else 0


def band(iid):
    return "below_7532" if num(iid) < 7532 else "from_7532"


def load_tracker(data):
    rows = list(csv.DictReader(open(data / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", encoding="utf-8")))
    return {r["instrument_id"]: r for r in rows}


def express_candidates(kit, und, kind):
    """Undecided orders with at least one whole, naming ACT whose provision passes the sentence predicate."""
    hits = collections.defaultdict(set)
    for r in jsonl(sorted(glob.glob(str(kit / "ACTING_PROVISIONS*.jsonl")))):
        t = r.get("target_id")
        if t in und and r.get("scope") == "whole" and r.get("names_target") and not r.get("reaches_target_via") \
                and r.get("verb") in kind["act_verbs"]:
            prov = str(r.get("provision_text") or "")
            if len(prov) <= kind["max_provision_chars"] and P.named_end_in(prov, t, kind):
                hits[t].add(r.get("actor_id"))
    return hits


def kit_module(data):
    sys.path.insert(0, str(data / "jobs/claim-kit"))
    return importlib.import_module("status_overlay")


def _precheck(so, data, iid):
    """The kit's own cheap per-order history check (no shard scan), so a refusing order is found before batching."""
    root = Path(data).resolve()
    if not hasattr(_precheck, "cache"):
        _precheck.cache = (so._history_module(root), so._authority_tables(root))
    history, tables = _precheck.cache
    packet = history.show(root / "jobs/status-history/output", iid)
    got, _, _ = so._precheck(root, packet, lambda i: so._authority_for(tables, i), history)
    if got != iid:
        raise ValueError("history_packet_instrument_mismatch:" + iid)


def freeze_tolerant(so, data, ids, log=print):
    """status_overlay.prepare_evidence_many with one change: an order the kit refuses is recorded with its error
    instead of aborting the batch, so every order costs one shared shard scan. The per-order steps are the kit's own
    functions, called in the same order; the kit's equality test (prepare_evidence_many == prepare_evidence) is what
    makes each evidence identical to a single-order freeze."""
    from copy import deepcopy
    root = Path(data).resolve()
    output = root / "jobs/claim-kit/output"
    result, errors = {}, {}
    shared = so._new_stats()
    tables = so._authority_tables(root)
    history = so._history_module(root)
    packets, authorities = {}, {}
    for iid in ids:
        try:
            packet = history.show(root / "jobs/status-history/output", iid)
            got, authorities[iid], _ = so._precheck(root, packet, lambda i: so._authority_for(tables, i), history)
            if got != iid:
                raise ValueError("history_packet_instrument_mismatch:" + iid)
            packets[iid] = packet
        except Exception as exc:  # noqa: BLE001
            errors[iid] = exc
    ids = [i for i in ids if i in packets]
    out, summary = so._manifest(root, output)
    want = set(ids)
    found = so._collect(out, summary, "OVERLAY_INPUTS", shared, "instrument_id", want)
    inputs, leads, chain = {}, {}, {}
    fl = so._collect(out, summary, "STATUS_LEADS", shared, "instrument_id", want)
    ft = so._collect(out, summary, "OWN_TERMS", shared, "instrument_id", want)
    fa = so._collect(out, summary, "ACTING_PROVISIONS", shared, "target_id", want)
    fc = so._collect(out, summary, "CHAINS", shared, "target_id", want)
    terms = {iid: [row for _, row in ft.get(iid, [])] for iid in ids}
    acts = {iid: [row for _, row in fa.get(iid, [])] for iid in ids}
    actors = {}
    for iid in ids:
        try:
            inputs[iid] = so._unique([r for _, r in found.get(iid, [])], "OVERLAY_INPUTS:" + iid, True)
            if inputs[iid].get("schema") != so.INPUT_SCHEMA:
                raise ValueError("old_overlay_input_record")
            leads[iid] = so._unique([r for _, r in fl.get(iid, [])], "STATUS_LEADS:" + iid, True)
            if leads[iid].get("status") is not None:
                raise ValueError("status_lead_must_be_undecided")
            chain[iid] = so._unique([r for _, r in fc.get(iid, [])], "CHAINS:" + iid, True)
            actors[iid] = so._actor_ids(inputs[iid], acts[iid])
        except Exception as exc:  # noqa: BLE001
            errors[iid] = exc
    ids = [i for i in ids if i in actors]
    wanted = set(ids).union(*[set(a) for a in actors.values()]) if ids else set()
    clauses = so._collect(out, summary, "CLAUSES", shared, "instrument_id", wanted)
    represented = so._collect(out, summary, "TEXT_REPRESENTATIONS", shared, "instrument_id", wanted)
    for iid in ids:
        try:
            clause = so._unique([r for _, r in clauses.get(iid, [])], "CLAUSES:" + iid, False)
            actor_clauses = {a: clauses[a][-1][1] for a in actors[iid] if a in clauses}
            keep = set(actors[iid] + [iid])
            declared = [row for _, row in sorted((pair for k in keep for pair in represented.get(k, [])),
                                                 key=lambda pair: pair[0])]
            result[iid] = so._assemble_evidence(root, out, summary, packets[iid], iid, authorities[iid], *deepcopy((
                inputs[iid], leads[iid], clause, terms[iid], acts[iid], chain[iid], actor_clauses, declared)),
                so._new_stats())
        except Exception as exc:  # noqa: BLE001
            errors[iid] = exc
    log(f"froze {len(result)}, refused {len(errors)}")
    for iid, exc in errors.items():
        result[iid] = f"freeze_refused: {type(exc).__name__}: {str(exc)[:160]}"
    return result


def freeze(so, data, ids, chunk, log=print):
    """{iid: evidence or error string}. Orders the kit refuses are found by its cheap history precheck first; a chunk
    that still fails is bisected (each half is one shard scan), never frozen one order at a time."""
    out = {}
    ids = sorted(ids, key=num)
    ok = []
    for iid in ids:
        try:
            _precheck(so, data, iid)
            ok.append(iid)
        except Exception as exc:  # noqa: BLE001
            out[iid] = f"freeze_refused: {type(exc).__name__}: {str(exc)[:160]}"
    log(f"precheck: {len(ok)} of {len(ids)} pass")

    def go(part):
        try:
            out.update(so.prepare_evidence_many(data, data / "jobs/claim-kit/output", part))
            log(f"froze {len(part)} (total {len(out)})")
        except Exception as exc:  # noqa: BLE001
            if len(part) == 1:
                out[part[0]] = f"freeze_refused: {type(exc).__name__}: {str(exc)[:160]}"
                return
            mid = len(part) // 2
            go(part[:mid])
            go(part[mid:])
    for i in range(0, len(ok), chunk):
        go(ok[i:i + chunk])
    return out


def ending_evidence(dossier):
    """What kind of ending evidence a dossier holds, for the tally: the kind a new drafter tier would need."""
    recs = dossier.get("evidence") or {}
    acts = [r for k, r in recs.items() if k.startswith("ACT:")]
    terms = [r for k, r in recs.items() if k.startswith("TERM:") and r.get("kind") not in ("report_deadline", "condition")]
    if any(r.get("scope") == "whole" and r.get("names_target") for r in acts):
        return "whole_named_act_failing_sentence_test"
    if any(r.get("scope") == "partial" for r in acts):
        return "partial_acts_only"
    if acts:
        return "acts_not_naming_or_not_whole"
    if terms:
        return "own_terms_only"
    if (dossier.get("chain") or {}).get("events"):
        return "chain_events_without_located_provision"
    return "no_later_instrument_or_term_held"


def head(blockers):
    return blockers[0].split(":")[0] if blockers else "complete"


def actor_batches(rows):
    by = collections.defaultdict(list)
    for r in rows:
        by[r["actor_id"]].append(r["instrument_id"])
    sizes = sorted((len(v) for v in by.values()), reverse=True)
    return {"actors": len(by), "targets": sum(sizes), "largest": sizes[:10],
            "singletons": sum(1 for s in sizes if s == 1),
            "targets_in_batches_of_2_or_more": sum(s for s in sizes if s >= 2),
            "by_actor": {a: sorted(v, key=num) for a, v in sorted(by.items(), key=lambda kv: (-len(kv[1]), num(kv[0])))}}


def run(data, out, chunk=150, limit=None, evidence_cache=None, only=None):
    """evidence_cache: a folder (outside the repository) to keep each complete order's frozen evidence, for packet
    measurement and calibration; only: restrict the express kind to these ids."""
    data, out = Path(data).resolve(), Path(out)
    if evidence_cache:
        evidence_cache = Path(evidence_cache)
        evidence_cache.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    kit = data / "jobs/claim-kit/output"
    kind = P.express_kind(data) if (data / "jobs/respondendi-adoption").exists() else dict(P.EXPRESS)
    tracker = load_tracker(data)
    und = {i for i, r in tracker.items() if not r["provisional_status"]}
    mindex = D.mentions_index(csv.DictReader(open(data / "jobs/current-law/output/MENTIONS.csv", encoding="utf-8")))
    so = kit_module(data)
    rows, result = [], {"basis": {}, "kinds": {}}

    # 1. express named revocation, undecided route.
    cands = express_candidates(kit, und, kind)
    ids = sorted(cands, key=num)[:limit] if limit else sorted(cands, key=num)
    if only:
        ids = [i for i in ids if i in set(only)]
    frozen = freeze_tolerant(so, data, ids,
                             log=lambda m: print(time.strftime("%H:%M:%S"), m, file=sys.stderr, flush=True))
    complete, blockers_first, blockers_all = [], collections.Counter(), collections.Counter()
    for iid in ids:
        ev = frozen.get(iid)
        if isinstance(ev, str):
            bl, facts, gate = [ev], {}, None
        else:
            dr = D.draft(ev, mentions=D.mentions_for(mindex, iid))
            bl, facts = dr["blockers"], dr.get("facts") or {}
            gate = so._decision_errors(dr["decision"], ev) if dr.ok else None
            if gate:
                bl = [f"kit_decision_gate: {g}" for g in gate]
        blockers_first[head(bl)] += 1
        for b in {x.split(":")[0] for x in bl}:
            blockers_all[b] += 1
        row = {"kind": "express_named_revocation", "instrument_id": iid, "band": band(iid),
               "actor_id": facts.get("actor_id") or ";".join(sorted(a for a in cands[iid] if a)),
               "complete": not bl, "first_blocker": head(bl), "blockers": " | ".join(b[:160] for b in bl)}
        rows.append(row)
        if not bl:
            complete.append(row)
            if evidence_cache:
                (evidence_cache / (iid.replace(":", "_") + ".json")).write_text(
                    json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        elif evidence_cache and not isinstance(ev, str) and {x.split(":")[0] for x in bl} <= DECOY_BLOCKERS:
            (evidence_cache / ("decoy-" + iid.replace(":", "_") + ".json")).write_text(
                json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    if only:
        (out / "CENSUS_ONLY.json").write_text(json.dumps({"ids": ids, "complete": [r["instrument_id"] for r in complete]},
                                                         indent=1) + "\n", encoding="utf-8")
        return {"kinds": {"express_named_revocation": {"complete": len(complete)}}}
    result["kinds"]["express_named_revocation"] = {
        "route": "undecided (status unset)", "candidates_with_a_predicate_passing_act": len(ids),
        "complete": len(complete), "complete_by_band": dict(collections.Counter(r["band"] for r in complete)),
        "first_blocker": dict(blockers_first.most_common()), "any_blocker": dict(blockers_all.most_common()),
        "batches": actor_batches(complete)}

    # 2. decided NO orders with no ready claim, decided route.
    dec = [i for i, r in tracker.items() if r["provisional_status"] == "no" and r["ready_for_human_review"] != "yes"]
    if limit:
        dec = sorted(dec, key=num)[:limit]
    dfirst, dall, dcomplete = collections.Counter(), collections.Counter(), []
    for iid in sorted(dec, key=num):
        path = kit / "dossiers" / (iid.replace(":", "_") + ".json")
        if not path.exists():
            dfirst["no_compiled_dossier"] += 1
            continue
        dossier = json.loads(path.read_text(encoding="utf-8"))
        dr = D.draft({"instrument_id": iid, "base_dossier": dossier}, mentions=D.mentions_for(mindex, iid),
                     route="decided")
        bl = dr["blockers"]
        dfirst[head(bl)] += 1
        for b in {x.split(":")[0] for x in bl}:
            dall[b] += 1
        row = {"kind": "decided_express", "instrument_id": iid, "band": band(iid),
               "actor_id": (dr.get("facts") or {}).get("actor_id") or "", "complete": not bl,
               "first_blocker": head(bl), "blockers": " | ".join(b[:160] for b in bl),
               "ending_evidence": ending_evidence(dossier)}
        rows.append(row)
        if not bl:
            dcomplete.append(row)
    result["kinds"]["decided_express"] = {
        "route": "decided production (status NO already provisional; lifecycle sheet only)",
        "decided_no_without_ready_claim": len(dec), "complete": len(dcomplete),
        "complete_by_band": dict(collections.Counter(r["band"] for r in dcomplete)),
        "first_blocker": dict(dfirst.most_common()), "any_blocker": dict(dall.most_common()),
        "batches": actor_batches(dcomplete)}

    # 3. amendment-only children (Pothier P2), with the state of the parent.
    express_done = {r["instrument_id"] for r in complete}
    kids, parent_state = [], collections.Counter()
    for r in jsonl([data / "jobs/pothier/output/LEADS.jsonl"]):
        if r.get("lead_kind") != "merged_into_parent_on_issue" or r["instrument_id"] not in und:
            continue
        m = re.search(r"\b(?:into|parent'?s? lead \(|parent,? )\s*(EO \d+[A-Z]?)", r.get("basis") or "")
        parent = "EO:" + m.group(1).split()[1] if m else None
        if parent is None:
            state = "parent_not_named_in_lead"
        elif parent in express_done:
            state = "parent_scriptable_now"
        elif (tracker.get(parent) or {}).get("provisional_status") == "no":
            state = "parent_decided_no"
        elif (tracker.get(parent) or {}).get("provisional_status") == "yes":
            state = "parent_decided_yes"
        else:
            state = "parent_undecided"
        parent_state[state] += 1
        kids.append({"kind": "amendment_only", "instrument_id": r["instrument_id"], "band": band(r["instrument_id"]),
                     "actor_id": parent or "", "complete": False, "first_blocker": "route_own_text_not_on_main",
                     "blockers": f"route_own_text_not_on_main (F5, PR #274) | {state}"})
    rows += kids
    order = collections.defaultdict(list)
    for k in kids:
        order[k["actor_id"] or "?"].append(k["instrument_id"])
    result["kinds"]["amendment_only"] = {
        "route": "undecided, OWN_TEXT basis (mechanism follows_parent / spent_on_issue)",
        "undecided_members": len(kids), "complete": 0, "parent_state": dict(parent_state.most_common()),
        "blocker": "the claim kit on main emits no OWN_TEXT or PARENT_END record (F5, Accursius PR #274); once it does, "
                   "a child whose parent is decided or scriptable is drafted after its parent (dependency order)",
        "children_by_parent": {p: len(v) for p, v in sorted(order.items(), key=lambda kv: -len(kv[1]))}}

    # 4. own terms (Respondendi's lead predicate, for the record).
    own = collections.Counter()
    for r in jsonl(sorted(glob.glob(str(kit / "OWN_TERMS*.jsonl")))):
        if r.get("instrument_id") in und and r.get("kind") in ("fixed_term", "sunset_date") and \
                r.get("scope_id") in (r["instrument_id"], r["instrument_id"] + "#whole"):
            own["whole_scope_dated_term" if P._date(r.get("stated_end_date")) else "whole_scope_term_without_date"] += 1
    result["kinds"]["own_terms"] = {
        "route": "undecided, TERM basis", "complete": 0, "term_records": dict(own),
        "blocker": "Respondendi's own-terms predicate reaches 0 undecided orders on main (KINDS.json); a stated term "
                   "also needs the extension and later-act checks a script cannot close without a held negative search"}

    result["basis"] = {"data_checkout": str(data), "claim_kit_generation": json.loads(
        (kit / "SUMMARY.json").read_text(encoding="utf-8")).get("generated_at"), "undecided": len(und),
        "decided": len(tracker) - len(und), "seconds": round(time.time() - started, 1),
        "drafter": D.DRAFTER_VERSION, "rule_express_kind_sha256": D.sha(D.canon(kind))}
    (out / "CENSUS.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    with open(out / "CENSUS.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "instrument_id", "band", "actor_id", "complete", "first_blocker",
                                          "blockers", "ending_evidence"], lineterminator="\n", restval="")
        w.writeheader()
        w.writerows(rows)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True, help="a checkout holding main's compiled job outputs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunk", type=int, default=150)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--evidence-cache", help="folder outside the repository for complete orders' frozen evidence")
    ap.add_argument("--only", nargs="*", help="restrict the express kind to these ids (with --evidence-cache)")
    a = ap.parse_args(argv)
    res = run(a.data, a.out, a.chunk, a.limit, a.evidence_cache, a.only)
    print(json.dumps({k: {x: v.get(x) for x in ("complete", "candidates_with_a_predicate_passing_act",
                                                 "decided_no_without_ready_claim", "undecided_members")}
                      for k, v in res["kinds"].items()}, indent=1))


if __name__ == "__main__":
    main()
