#!/usr/bin/env python3 -I
"""Bentham candidates: list the work an agent swarm or a machine job could do next, from committed files.

Output is CANDIDATES.json (shape in jobs/bentham/CONTRACT.md). Nothing here is typed in by hand: counts are
computed from the readiness tracker's per-order table, the Tribonian disposition receipt, the tracker's
"do these first" table and Polya's reach counts.

What the numbers mean
- "orders" is the number of orders the action can be dispatched on today.
- An "unlock" is a count of orders that cannot be drafted today but would join a claim-ready stratum if this
  one action finished. An order is counted only when every blocker that holds it back (apart from steps the
  stratum itself leaves open) is one this action clears. Each order is assigned to at most one acquisition
  action, so unlock counts can be added across actions. Orders that need two acquisitions are not counted.
- A count is a count of orders, never a forecast of filed dossiers; yield comes from MEASURED.json.
- Polya reach counts are upper bounds on one-step advances and are used only as cited evidence, never added.
Standard library only; reads committed files; writes only jobs/bentham/output/ (and --out).
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

FR_START = 7532  # first EO number in the Federal Register index era
TRACKER_CSV = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
TRACKER_MD = "jobs/readiness-tracker/output/TRACKER.md"
SHARED_CSV = "jobs/readiness-tracker/output/SHARED_UNLOCKS.csv"
POLYA_ACTIONS = "jobs/polya/output/CANDIDATE_ACTIONS.json"
POLYA_COMPARE = "jobs/polya/output/COMPARE.json"
DISPOSITION = "research/excavator/claude-tribonian-2026-11-04/evidence/DISPOSITION.json"
TRIBONIAN_REPORT = "research/excavator/claude-tribonian-2026-11-04/REPORT.md"

# Blockers that describe steps the claim-ready stratum leaves open on purpose, or the Opus-media step, which
# the stratum definition does not gate on. They never stop an order from joining the stratum.
NON_GATING = ("NO_CLAUSE_INVENTORY", "FIRST_END_UNPROVED", "SAVINGS_RESIDUALS_NOT_CLOSED",
              "CURRENT_BASIS_UNPROVED", "NO_PROVISIONAL_STATUS", "OPUS_MEDIA_")
# Blockers that make an order un-draftable even when its text and counterevidence steps are done.
HOLD_PREFIXES = ("SHARED_SOURCE_NOT_RETRIEVED", "QUARANTINED_RELATIONSHIP_CONFLICT", "OPEN_SOURCE_AUDIT")
ORIGINAL_BLOCKERS = {"NO_OFFICIAL_SOURCE_LOCATED", "ONLY_COMPILED_TRANSCRIPTION_FOUND",
                     "ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK", "ORIGINAL_FOUND_NEEDS_PAGE_CHECK"}


def era(eo_number):
    return "fr" if eo_number >= FR_START else "prefr"


def eo_number(instrument_id):
    m = re.match(r"EO:(\d+)", instrument_id)
    return int(m.group(1)) if m else -1


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(repo, rel):
    with open(Path(repo) / rel, encoding="utf-8") as fh:
        return fh.read()


def quote_in(repo, rel, quote):
    """Return an evidence row only if the quote is verbatim in the file; else None."""
    try:
        return {"quote": quote, "source": rel} if quote in read_text(repo, rel) else None
    except OSError:
        return None


def evidence(repo, pairs):
    return [e for e in (quote_in(repo, rel, q) for rel, q in pairs) if e]


def load_orders(repo):
    """Decided (provisional YES/NO), not-yet-ready orders with parsed steps and blockers."""
    rows = []
    with open(Path(repo) / TRACKER_CSV, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["provisional_status"] not in ("yes", "no") or r["ready_for_human_review"] != "no":
                continue
            steps = {k[5:]: v for k, v in r.items() if k.startswith("step_")}
            r["_steps"] = steps
            r["_blockers"] = [b for b in r["blockers"].split("|") if b]
            r["_era"] = era(eo_number(r["instrument_id"]))
            rows.append(r)
    return rows


def gating(blockers):
    return {b for b in blockers if not b.startswith(NON_GATING)}


def is_hold(b):
    return b.startswith(HOLD_PREFIXES)


def in_claim_ready_stratum(o):
    s = o["_steps"]
    return (s["original_text"] in ("done", "provisional") and s["counterevidence"] == "done"
            and all(s[k] == "open" for k in ("clause_inventory", "ending_or_current_basis", "savings_residuals"))
            and not any(is_hold(b) for b in o["_blockers"]))


def one_step_away(o):
    applicable = [v for v in o["_steps"].values() if v != "n/a"]
    return o["claim_present"] == "yes" and applicable.count("open") == 1


def recovery_ids(repo):
    d = json.loads(read_text(repo, DISPOSITION))
    ids = []
    for b in d.get("batches", []):
        for n in b.get("not_filed", []):
            if n.get("outcome") == "rejected_mechanical" and n["instrument_id"] not in ids:
                ids.append(n["instrument_id"])
    return ids


def tracker_rows(repo):
    """Rows of the tracker's 'Do these first' table joined to SHARED_UNLOCKS.csv for the blocker code."""
    md = read_text(repo, TRACKER_MD).splitlines()
    table = {}
    for line in md:
        m = re.match(r"\|\s*([\d,]+)\s*\|\s*([a-z ]+?)\s*\|\s*(.+?)\s*\|$", line)
        if m:
            table[m.group(3)] = (int(m.group(1).replace(",", "")), m.group(2), line)
    out = []
    with open(Path(repo) / SHARED_CSV, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            line = table.get(r["action"])
            out.append({"orders_reach": int(r["orders_unblocked"]), "kind": r["kind"], "action": r["action"],
                        "blocker": r["blocker"], "md_line": line[2] if line else None})
    return out


# Each acquisition: the blockers it clears, the one headline blocker an order must carry, an era filter, and an
# estimated delay. Order matters: an order covered by several is assigned to the first.
def acquisition_specs(shared_rows):
    specs = []
    for r in shared_rows:
        b = r["blocker"]
        if b.startswith("SHARED_SOURCE_NOT_RETRIEVED:"):
            specs.append({"key": "shared." + b.split(":", 1)[1], "row": r, "clears": {b}, "headline": b,
                          "eras": ("fr", "prefr"), "delay": 2,
                          "delay_basis": "estimate: one machine fetch of a single source plus a tracker re-run (no measured run time)"})
    for b, clears, eras, delay, why in (
        ("ORIGINAL_FOUND_NEEDS_PAGE_CHECK", {"ORIGINAL_FOUND_NEEDS_PAGE_CHECK", "ONLY_COMPILED_TRANSCRIPTION_FOUND"},
         ("fr", "prefr"), 2, "estimate: agent page check of a located original, then tracker re-run"),
        ("ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK", {"ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK", "NO_OFFICIAL_SOURCE_LOCATED"},
         ("fr", "prefr"), 3, "estimate: agent page comparison against the ProQuest scan under the 2026-10-21 owner rulings"),
        ("ONLY_COMPILED_TRANSCRIPTION_FOUND", {"ONLY_COMPILED_TRANSCRIPTION_FOUND", "NO_OFFICIAL_SOURCE_LOCATED"},
         ("fr",), 3, "estimate: GitHub Actions fetch job (fr-originals route) and tracker re-run; era fr only because the "
                    "tracker text says orders from 1936 on were printed in the Federal Register"),
    ):
        row = next((r for r in shared_rows if r["blocker"] == b), None)
        if row:
            specs.append({"key": b, "row": row, "clears": clears, "headline": b, "eras": eras, "delay": delay, "delay_basis": why})
    return specs


def assign_unlocks(orders, specs, excluded):
    """Assign each non-stratum order to at most one acquisition. Returns (assigned, coverage) where coverage maps
    spec key -> set of every order that spec alone could cover (before the one-assignment rule)."""
    assigned = defaultdict(list)
    coverage = {s["key"]: set() for s in specs}
    for o in orders:
        if o["instrument_id"] in excluded or in_claim_ready_stratum(o):
            continue
        s = o["_steps"]
        if not all(s[k] == "open" for k in ("clause_inventory", "ending_or_current_basis", "savings_residuals")):
            continue  # would not land in the claim-ready stratum
        g = gating(o["_blockers"])
        if not g:
            continue
        # consistency: an open original_text step must be explained by an original-text blocker in g
        if s["original_text"] == "open" and not (g & ORIGINAL_BLOCKERS):
            continue
        for sp in specs:
            if g <= sp["clears"] and sp["headline"] in g and o["_era"] in sp["eras"]:
                coverage[sp["key"]].add(o["instrument_id"])
                if o["instrument_id"] not in {i for lst in assigned.values() for i, _ in lst}:
                    assigned[sp["key"]].append((o["instrument_id"], (o["provisional_status"], o["_era"])))
    return assigned, coverage


def build(repo, write_ids=True):
    repo = Path(repo)
    orders = load_orders(repo)
    rec_ids = recovery_ids(repo)
    rec_set = set(rec_ids)
    actions = []
    strata_dir = repo / "jobs/bentham/output/strata"

    def save_ids(action_id, ids):
        if not write_ids:
            return None
        strata_dir.mkdir(parents=True, exist_ok=True)
        (strata_dir / (action_id + ".txt")).write_text("\n".join(sorted(ids)) + ("\n" if ids else ""), encoding="utf-8")
        return "jobs/bentham/output/strata/%s.txt" % action_id

    # A. production strata
    strata = defaultdict(list)
    held = 0
    recovered_overlap = 0
    for o in orders:
        if o["instrument_id"] in rec_set:
            if in_claim_ready_stratum(o):
                recovered_overlap += 1
            continue
        if in_claim_ready_stratum(o):
            strata[(o["provisional_status"], o["_era"])].append(o["instrument_id"])
        elif (o["_steps"]["original_text"] in ("done", "provisional") and o["_steps"]["counterevidence"] == "done"
              and any(is_hold(b) for b in o["_blockers"])
              and all(o["_steps"][k] == "open" for k in ("clause_inventory", "ending_or_current_basis", "savings_residuals"))):
            held += 1
    csv_ev = evidence(repo, [(TRACKER_CSV, "instrument_id,provisional_status,decision_origin,steps_applicable")])
    stratum_ids = {}
    for (status, e), ids in sorted(strata.items()):
        aid = "production.claim_ready.%s.%s" % (status, e)
        stratum_ids[(status, e)] = aid
        actions.append({
            "id": aid, "kind": "production",
            "description": ("Draft whole-lifecycle dossiers for provisional-%s, %s-era orders whose original text (done or provisional) and "
                            "counterevidence are done and whose clause inventory, ending/current basis and savings/residuals are open. "
                            "Excludes orders held by an unretrieved shared source, a quarantined relationship or an open source audit, and "
                            "the custody-stranded recovery orders." % (status.upper(), "Federal Register" if e == "fr" else "pre-Federal-Register")),
            "orders": len(ids), "order_ids_path": save_ids(aid, ids),
            "rate_key": "filed_per_attempt.%s.%s" % (status, e), "cost_key": "wave.per_attempt",
            "unlocks": [], "prerequisites": [],
            "basis": "Computed from %s: provisional_status=%s, ready_for_human_review=no, EO number %s %d, rule in_claim_ready_stratum." % (
                TRACKER_CSV, status, ">=" if e == "fr" else "<", FR_START),
            "evidence": csv_ev})
    # one step away
    one = [o["instrument_id"] for o in orders if one_step_away(o) and o["instrument_id"] not in rec_set]
    aid = "production.one_step_away"
    actions.append({
        "id": aid, "kind": "production",
        "description": "Close the single open step of orders that already have a claim and exactly one applicable step open. Excludes recovery orders.",
        "orders": len(one), "order_ids_path": save_ids(aid, one),
        "rate_key": "filed_per_attempt.correction", "cost_key": "wave.per_attempt",
        "unlocks": [], "prerequisites": [],
        "basis": "Computed from %s: claim_present=yes and exactly one step_* column equal to open (n/a steps ignored)." % TRACKER_CSV,
        "evidence": csv_ev})

    # B. recovery
    aid = "recovery.custody_stranded"
    actions.append({
        "id": aid, "kind": "recovery",
        "description": ("Reviewed claims that passed blind review but failed the checker at completion, almost always because a cited source "
                        "was held only as a hash (custody_record_only). They need re-preparation and fresh review, not new drafting, so the "
                        "cost is review.per_submitted. DISPOSITION.json lists %d distinct orders with outcome rejected_mechanical; the "
                        "REPORT text says 47 (a one-order difference left unexplained)." % len(rec_ids)),
        "orders": len(rec_ids), "order_ids_path": save_ids(aid, rec_ids),
        "rate_key": "filed_per_attempt.correction", "cost_key": "review.per_submitted",
        "unlocks": [],
        "prerequisites": ["source bytes held for the cited sources (jobs/cotton-capture-custody, jobs/astra-source-retention)",
                          "kit.py prepare for exactly these ids, then fresh blind review or owner-approved reuse"],
        "basis": "Computed from %s: orders with outcome rejected_mechanical, de-duplicated. %d of them also sit in a claim-ready stratum and were removed from it." % (DISPOSITION, recovered_overlap),
        "evidence": evidence(repo, [(DISPOSITION, '"outcome": "rejected_mechanical"'),
                                    (TRIBONIAN_REPORT, "47 reviewed claims are blocked by source custody")])})

    # C/D. acquisitions and zero-agent actions from the tracker table
    rows = tracker_rows(repo)
    specs = acquisition_specs(rows)
    assigned, coverage = assign_unlocks(orders, specs, rec_set)
    for sp in specs:
        key = sp["key"]
        r = sp["row"]
        by_group = Counter(g for _, g in assigned.get(key, []))
        unlocks = [{"orders": n, "rate_key": "filed_per_attempt.%s.%s" % g, "delay_days": sp["delay"],
                    "delay_basis": sp["delay_basis"],
                    "basis": "%s: decided orders whose only gating blocker(s) are in {%s}, with clause inventory, ending and savings open; assigned to this action only." % (
                        TRACKER_CSV, ", ".join(sorted(sp["clears"])))}
                   for g, n in sorted(by_group.items())]
        overlaps = sorted(o for o, cov in ((s2["key"], coverage[s2["key"]] & coverage[key]) for s2 in specs if s2["key"] != key) if cov)
        machine = r["kind"] in ("machine_job", "one_source") 
        actions.append({
            "id": "acquire." + re.sub(r"[^A-Za-z0-9_.]+", "_", key).strip("_"),
            "kind": "acquisition",
            "description": r["action"] + (" (tracker reach %d includes undecided orders, which unlock nothing until they have a provisional status)" % r["orders_reach"]),
            "orders": 0, "rate_key": "filed_per_attempt.correction",
            "cost_key": None if machine else "production.per_attempt", "cost_override_usd": 0 if machine else None,
            "cost_units": None if machine else sum(by_group.values()),
            "unlocks": unlocks, "overlaps_with": ["acquire." + re.sub(r"[^A-Za-z0-9_.]+", "_", k).strip("_") for k in overlaps],
            "prerequisites": [] if machine else ["agent time to check pages, one order at a time (cost_units orders)"],
            "tracker_reach_orders": r["orders_reach"], "tracker_kind": r["kind"],
            "basis": "Tracker reach from %s; unlock counts computed from %s under the one-assignment rule." % (SHARED_CSV, TRACKER_CSV),
            "evidence": [e for e in (quote_in(repo, TRACKER_MD, r["md_line"]) if r["md_line"] else None,
                                     quote_in(repo, SHARED_CSV, r["blocker"])) if e]})

    # zero-agent: Opus media refetch (the stratum does not gate on opus media, so it unlocks no stratum membership)
    for r in rows:
        if r["blocker"] == "OPUS_MEDIA_REFETCH_NEEDED":
            n_stratum = sum(1 for o in orders if "OPUS_MEDIA_REFETCH_NEEDED" in o["_blockers"])
            actions.append({
                "id": "zero_agent.opus_media_refetch", "kind": "zero_agent", "description": r["action"],
                "orders": 0, "rate_key": "filed_per_attempt.correction", "cost_key": None, "cost_override_usd": 0,
                "unlocks": [], "prerequisites": [],
                "note": "Clears the Opus-media step, which the claim-ready stratum does not gate on, so no unlock is counted. %d decided orders carry this blocker." % n_stratum,
                "basis": "Tracker reach %d from %s; decided count computed from %s." % (r["orders_reach"], SHARED_CSV, TRACKER_CSV),
                "evidence": [e for e in (quote_in(repo, TRACKER_MD, r["md_line"]) if r["md_line"] else None,) if e]})

    # yield-lift acquisitions: no stratum membership changes, so no unlock is counted (counting them would repeat
    # orders already in the production strata)
    yes_strata = [aid for (st, _), aid in stratum_ids.items() if st == "yes"]
    cb = [o for o in orders if o["provisional_status"] == "yes" and in_claim_ready_stratum(o) and "CURRENT_BASIS_UNPROVED" in o["_blockers"]
          and o["instrument_id"] not in rec_set]
    try:
        f7 = json.loads(read_text(repo, POLYA_COMPARE))
        f7_reach = next(f["decided_not_ready_reachable"] for f in f7["frames"] if f["frame"].startswith("F7"))
    except (OSError, ValueError, StopIteration):
        f7_reach = None
    nea_ev = evidence(repo, [(TRIBONIAN_REPORT, "Emergency-dependent YES orders lack the yearly National Emergencies Act continuation notices"),
                             (TRIBONIAN_REPORT, "The current texts of parent orders and statutes are not held")])
    actions.append({
        "id": "acquire.nea_continuation_notices", "kind": "acquisition",
        "description": "Fetch the yearly National Emergencies Act continuation notices for emergency-dependent YES orders, so their current basis can be cited.",
        "orders": 0, "rate_key": "filed_per_attempt.yes.fr", "cost_key": None, "cost_override_usd": 0, "unlocks": [],
        "overlaps_with": yes_strata + ["acquire.current_law_sections"],
        "yield_lift_not_counted": {"orders": len(cb), "applies_to": yes_strata,
                                   "why": "These YES orders are already in the claim-ready strata; the action raises their yield but moves no order into a stratum, and no measured yield change exists."},
        "prerequisites": [], "basis": "Orders counted from %s: YES, in a claim-ready stratum, blockers include CURRENT_BASIS_UNPROVED." % TRACKER_CSV,
        "evidence": nea_ev[:1]})
    actions.append({
        "id": "acquire.current_law_sections", "kind": "acquisition",
        "description": "Retrieve current text of the U.S. Code and CFR sections and parent orders that YES orders cite for their current basis.",
        "orders": 0, "rate_key": "filed_per_attempt.yes.fr", "cost_key": None, "cost_override_usd": 0, "unlocks": [],
        "overlaps_with": yes_strata + ["acquire.nea_continuation_notices"],
        "yield_lift_not_counted": {"orders": f7_reach, "applies_to": yes_strata,
                                   "why": "Polya F7 reach (upper bound, counts one-step advances not yield) and it overlaps the NEA action; Polya reports 0 orders whose only open steps this frame advances."},
        "prerequisites": [],
        "basis": "Polya reach from %s (frame F7_aux_current_predicate_table, decided_not_ready_reachable); see jobs/polya/README.md: reach is not yield." % POLYA_COMPARE,
        "evidence": evidence(repo, [(POLYA_COMPARE, '"frame": "F7_aux_current_predicate_table"'),
                                    (TRIBONIAN_REPORT, "The current texts of parent orders and statutes are not held")])})

    inputs = [TRACKER_CSV, TRACKER_MD, SHARED_CSV, POLYA_ACTIONS, POLYA_COMPARE, DISPOSITION, TRIBONIAN_REPORT]
    gen = {p: sha256(repo / p) for p in inputs if (repo / p).exists()}
    return {"generated_from": gen,
            "pool": {"decided_not_ready_orders": len(orders), "held_by_unretrieved_source_or_quarantine": held},
            "notes": ["Unlock counts are additive across acquisition actions (one assignment per order); orders needing two acquisitions are uncounted.",
                      "NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE (orders absent from the OFR catalog) has no tracker action, so no acquisition is proposed for it.",
                      "Polya counts reach, not yield; they are cited, never added."],
            "actions": actions}


def candidates(repo, write_ids=True):
    return build(repo, write_ids)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=None)
    ap.add_argument("--repo", default=os.environ.get("REPO_ROOT"))
    a = ap.parse_args(argv)
    repo = Path(a.repo) if a.repo else Path(__file__).resolve().parents[2]
    result = candidates(repo)
    out = Path(a.out) if a.out else repo / "jobs/bentham/output/CANDIDATES.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for x in result["actions"]:
        print("%-45s %-12s orders=%-6d unlocks=%d" % (x["id"], x["kind"], x["orders"], sum(u["orders"] for u in x["unlocks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
