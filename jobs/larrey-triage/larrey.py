#!/usr/bin/env python3
"""Larrey: zero-token triage of every order before any agent is dispatched to it.

Named for Dominique Jean Larrey, Napoleon's chief surgeon, who sorted the wounded on the field by need rather than
by rank and sent ambulances only where treatment could help. Here: before an agent is paid to work an order, check
that the order holds every input its route needs, so that no agent is paid to discover a missing input.

Subcommands (standard library only; run with `python3 -I jobs/larrey-triage/larrey.py ...`):
  triage    every order's verdict per route, from claim-kit's compiled outputs (Llull gates) -> output/
  backtest  replay the gates on the frozen packets of past waves and score them against real outcomes
  project   projected cost per adopted status with the gate against without it (a projection, labelled so)

Larrey decides no status, adopts nothing, changes no count. A kept-out order is deferred, not decided: the reason
says which input is missing, and the reason tally is the acquisition to-do list. Human-certified stays 0.
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LLULL = REPO / "jobs/llull"
OUTPUT = "jobs/larrey-triage/output"
BACKTEST = "jobs/larrey-triage/BACKTEST.json"
SCHEMA = "larrey.triage/v1"
KIT_SUMMARY = "jobs/claim-kit/output/SUMMARY.json"

# Each route lists its gates (names in Llull's GATES registry). Hard gates are what the route itself requires:
# without them the kit cannot accept the result whatever the agent finds. Soft gates are measured predictors,
# chosen from the back-test curve (BACKTEST.json); `LARREY_LEVEL=hard` applies the hard gates only.
ROUTES = {
    "status_only": {
        "title": "undecided order, status-only tier (independent status review; no lifecycle sheet)",
        "hard": ["original_usable", "no_page_check_owed", "status_basis_record"],
        "soft": ["later_order_text_held"],
        "calibrated_on": "jobs/claim-kit/status_overlay.py",
    },
    "undecided_full": {
        "title": "undecided order, status plus whole-lifecycle sheet (Haloander/Papinian overlay route)",
        "hard": ["original_usable", "no_page_check_owed", "status_basis_record", "clause_inventory_present"],
        "soft": ["later_order_text_held"],
        "calibrated_on": "jobs/claim-kit/status_overlay.py",
    },
    "decided_lifecycle": {
        "title": "decided (provisional YES/NO) order, whole-lifecycle dossier",
        "hard": ["original_usable", "no_page_check_owed", "clause_inventory_present"],
        "soft": ["nea_notice_if_emergency"],
        "calibrated_on": "jobs/claim-kit/assemble.py",
    },
}

# reason code, what would admit the order, and the Bentham action that acquires it (if one exists)
REASONS = {
    "original_usable": ("original_not_usable", "an official original, or a working text the route accepts", None),
    "no_page_check_owed": ("page_check_owed", "a page/image check of the official printing",
                           "acquire.ORIGINAL_FOUND_NEEDS_PAGE_CHECK"),
    "clause_inventory_present": ("no_clause_inventory", "a machine clause inventory (segmenter)", None),
    "status_basis_record": ("no_status_basis_record",
                            "a held ending instrument, own-terms text or current-status record (or the Accursius "
                            "F3/F5 route fixes that frame held ones)", None),
    "later_order_text_held": ("no_later_order_text_held", "a held text of a later instrument acting on the order",
                              None),
    "nea_notice_if_emergency": ("nea_continuation_notice_not_held",
                                "the National Emergencies Act continuation notices through 2026-10-14",
                                "acquire.nea_continuation_notices"),
}


def action_route(action):
    """The route a Bentham action's orders take, or None for an action Larrey does not triage."""
    base = action[len("probe."):] if action.startswith("probe.") else action
    if base.startswith("status_assignment."):
        return "status_only" if "status_only" in base else "undecided_full"
    if base.startswith("production.claim_ready."):
        return "decided_lifecycle"
    return None


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path, text):
    """Write text with LF line ends on every platform (the committed outputs are compared byte for byte)."""
    Path(path).write_bytes(text.encode("utf-8"))


def sha_file(path):
    p = Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _llull():
    if str(LLULL) not in sys.path:
        sys.path.insert(0, str(LLULL))
    import llull
    return llull


def level():
    v = os.environ.get("LARREY_LEVEL", "soft").strip().lower() or "soft"
    if v not in ("soft", "hard"):
        raise ValueError("LARREY_LEVEL must be soft (default: hard and soft gates) or hard (hard gates only)")
    return v


def evaluate(row, D, route, G):
    """{'hard': [failed gate...], 'soft': [failed gate...]} for one tracker row on one route."""
    spec = ROUTES[route]
    return {k: [g for g in spec[k] if G[g][1](row, D) not in ("held", "na")] for k in ("hard", "soft")}


def reason_codes(failed, feats):
    out = []
    for g in failed:
        code = REASONS[g][0]
        if g == "original_usable":
            if not feats or not feats.get("has_original"):
                code = "no_held_text"
            else:
                code += ":" + str(feats.get("original_grade"))
        out.append(code)
    return out


# ---------------------------------------------------------------- triage

def triage(repo=REPO, out_dir=None, strata_dir=None, pools=True):
    repo = Path(repo)
    ll = _llull()
    D = ll.Data(repo)
    G = ll.GATES
    feats = D.kit()
    rows = D.tracker()
    out = Path(out_dir) if out_dir else repo / OUTPUT
    out.mkdir(parents=True, exist_ok=True)
    verdicts, tallies = [], {}
    for r in rows:
        iid = r["instrument_id"]
        routes = ["decided_lifecycle"] if r.get("provisional_status") in ("yes", "no") else ["undecided_full", "status_only"]
        for route in routes:
            failed = evaluate(r, D, route, G)
            hard = reason_codes(failed["hard"], feats.get(iid))
            soft = reason_codes(failed["soft"], feats.get(iid))
            verdicts.append({"instrument_id": iid, "provisional_status": r.get("provisional_status") or "",
                             "route": route, "admit": "yes" if not hard and not soft else "no",
                             "admit_hard_only": "yes" if not hard else "no",
                             "reasons": ";".join(hard + ["soft:" + c for c in soft])})
            t = tallies.setdefault(route, {"orders": 0, "admitted": 0, "admitted_hard_only": 0,
                                           "any": Counter(), "sole": Counter(), "detail": Counter()})
            t["orders"] += 1
            t["admitted"] += not hard and not soft
            t["admitted_hard_only"] += not hard
            base = [c.split(":")[0] for c in hard] + ["soft:" + c.split(":")[0] for c in soft]
            t["any"].update(set(base))
            if len(base) == 1:
                t["sole"][base[0]] += 1
            t["detail"].update(c for c in hard if ":" in c)
    with open(out / "VERDICTS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["instrument_id", "provisional_status", "route", "admit", "admit_hard_only",
                                           "reasons"], lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(verdicts, key=lambda v: (v["route"], v["instrument_id"])))
    reasons = {route: {"orders": t["orders"], "admitted": t["admitted"], "admitted_hard_only": t["admitted_hard_only"],
                       "kept_out": t["orders"] - t["admitted"],
                       "reasons_any": dict(t["any"].most_common()), "reasons_sole": dict(t["sole"].most_common()),
                       "original_grades_kept_out": dict(t["detail"].most_common(20))}
               for route, t in sorted(tallies.items())}
    # The job leaves pools to Bentham, which reads these verdicts (reading Bentham's strata here would make each
    # job an input of the other); a local run lists them from the committed strata.
    pools = action_pools(repo, verdicts, strata_dir) if pools else {}
    calib = calibration(repo)
    summary = {"schema": SCHEMA, "generated_at": now(),
               "inputs": {"claim_kit_summary_sha256": sha_file(repo / KIT_SUMMARY),
                          "tracker_sha256": sha_file(repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")},
               "code_sha256": {p: sha_file(repo / p) for p in ("jobs/larrey-triage/larrey.py",
                                                                "jobs/llull/kit_features.py", "jobs/llull/llull.py")},
               "routes": {k: {kk: v[kk] for kk in ("title", "hard", "soft")} for k, v in ROUTES.items()},
               "calibration": calib,
               "orders_with_compiled_inputs": len(feats), "tracker_orders": len(rows),
               "notice": "Deferral, not decision: a kept-out order is open until its missing input is held. "
                         "No status, count or certification changed."}
    _write((out / "SUMMARY.json"), json.dumps(summary, indent=1) + "\n")
    _write((out / "REASONS.json"), json.dumps(reasons, indent=1) + "\n")
    _write((out / "POOLS.json"), json.dumps(pools, indent=1) + "\n")
    _write((out / "TODO.md"), todo_md(reasons, pools, calib))
    return summary, reasons, pools


def calibration(repo):
    """Per route: is the kit code its gates were back-tested on still the code on this checkout?"""
    bt = {}
    p = Path(repo) / BACKTEST
    if not p.exists():
        p = HERE / "BACKTEST.json"   # the code's own back-test when the data checkout is another worktree
    if p.exists():
        bt = json.loads(p.read_text(encoding="utf-8")).get("calibrated_code_sha256", {})
    out = {}
    for route, spec in ROUTES.items():
        rel = spec["calibrated_on"]
        cur = sha_file(Path(repo) / rel)
        out[route] = {"file": rel, "backtested_sha256": bt.get(rel), "current_sha256": cur,
                      "enforced": bool(cur) and bt.get(rel) == cur}
    return out


def _code(reason):
    """A reason without its detail: 'original_not_usable:mirror_transcription' -> 'original_not_usable';
    'soft:no_later_order_text_held' stays as it is."""
    if reason.startswith("soft:"):
        return "soft:" + reason[5:].split(":")[0]
    return reason.split(":")[0]


def action_pools(repo, verdicts, strata_dir=None):
    """Per Bentham action: members, admitted and the top reasons (from Bentham's committed strata)."""
    strata = Path(strata_dir) if strata_dir else Path(repo) / "jobs/bentham/output/strata"
    by = {(v["route"], v["instrument_id"]): v for v in verdicts}
    pools = {}
    for f in sorted(strata.glob("*.txt")) if strata.is_dir() else []:
        action = f.stem
        route = action_route(action)
        ids = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        rec = {"route": route, "members": len(ids)}
        if route:
            vs = [by.get((route, i)) for i in ids]
            missing = sum(1 for v in vs if v is None)
            vs = [v for v in vs if v]
            c = Counter(_code(x) for v in vs if v["admit"] == "no" for x in v["reasons"].split(";") if x)
            missing_ids = [i for i in ids if (route, i) not in by]
            if missing_ids:
                c["no_compiled_inputs"] += len(missing_ids)
            rec.update(admitted=sum(v["admit"] == "yes" for v in vs),
                       admitted_hard_only=sum(v["admit_hard_only"] == "yes" for v in vs),
                       no_verdict_kept_out=missing, top_reasons=dict(c.most_common(8)))
        pools[action] = rec
    return pools


def todo_md(reasons, pools, calib):
    lines = ["# Larrey triage: what is missing before agents can work these orders", "",
             "Generated by `python3 -I jobs/larrey-triage/larrey.py triage`; do not edit by hand. A kept-out order is "
             "deferred, not decided. Counts are orders; one order can lack several inputs.", "",
             "## Pools per Bentham action", "",
             "| Action | Route | Members | Admitted | Admitted (hard gates only) | Top reasons kept out |",
             "|---|---|---:|---:|---:|---|"]
    for a, p in pools.items():
        if p.get("route"):
            top = ", ".join(f"{k} {v}" for k, v in list(p["top_reasons"].items())[:4])
            lines.append(f"| {a} | {p['route']} | {p['members']} | {p['admitted']} | {p['admitted_hard_only']} | {top} |")
        else:
            lines.append(f"| {a} | not triaged | {p['members']} | | | |")
    lines += ["", "## Acquisition to-do list (reasons, all orders)", ""]
    for route, t in reasons.items():
        enforced = calib.get(route, {}).get("enforced")
        lines.append(f"### {route}: {t['kept_out']} of {t['orders']} kept out"
                     + ("" if enforced else " (advisory: kit code changed since the back-test)"))
        lines.append("")
        lines.append("| Reason | Orders (any) | Orders (sole reason) | What admits them | Bentham action |")
        lines.append("|---|---:|---:|---|---|")
        for code, n in t["reasons_any"].items():
            gate = next((g for g, v in REASONS.items() if v[0] == code.replace("soft:", "")
                         or (code == "no_held_text" and g == "original_usable")), None)
            what, act = (REASONS[gate][1], REASONS[gate][2] or "") if gate else ("", "")
            lines.append(f"| {code} | {n} | {t['reasons_sole'].get(code, 0)} | {what} | {act} |")
        lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- admission helper (no Llull import)

def verdicts_for(repo, route):
    path = Path(repo) / OUTPUT / "VERDICTS.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        return {r["instrument_id"]: r for r in csv.DictReader(fh) if r["route"] == route}


def admitted(repo, action):
    """(admitted ids, reasons by kept-out id, receipt) for a Bentham action; (None, {}, receipt) when Larrey does
    not triage it (another route, or a route whose kit code changed since the back-test: advisory only).

    Fail-closed: an order with no verdict on the action's route (no compiled inputs) is not admitted. Raises
    ValueError when the triage output is missing or was computed on other compiled claim-kit outputs.
    """
    repo = Path(repo)
    route = action_route(action or "")
    lv = level()
    receipt = {"larrey_route": route, "larrey_level": lv, "larrey_enforced": False}
    if route is None:
        return None, {}, receipt
    out = repo / OUTPUT
    summary_path = out / "SUMMARY.json"
    rerun = "run: python3 -I jobs/larrey-triage/larrey.py triage (zero tokens, under a minute)"
    if not summary_path.exists() or not (out / "VERDICTS.csv").exists():
        raise ValueError(f"Larrey triage missing ({OUTPUT}); {rerun}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("inputs", {}).get("claim_kit_summary_sha256") != sha_file(repo / KIT_SUMMARY):
        raise ValueError(f"Larrey triage is stale: computed on other claim-kit outputs than {KIT_SUMMARY}; {rerun}")
    receipt["larrey_summary_sha256"] = sha_file(summary_path)
    receipt["larrey_enforced"] = calibration(repo).get(route, {}).get("enforced", False)
    if not receipt["larrey_enforced"]:
        return None, {}, receipt
    key = "admit_hard_only" if lv == "hard" else "admit"
    rows = verdicts_for(repo, route)
    return ({i for i, r in rows.items() if r[key] == "yes"},
            {i: r["reasons"] for i, r in rows.items() if r[key] != "yes"}, receipt)


def refusal(action, ids, ok, why):
    """The ValueError text for ids Larrey keeps out of action (None when all are admitted)."""
    out = sorted(set(ids) - ok)
    if not out:
        return None
    shown = ", ".join(f"{i} ({why.get(i) or 'no_compiled_inputs'})" for i in out[:8]) + (" ..." if len(out) > 8 else "")
    return (f"{len(out)} orders are kept out of {action} by Larrey triage (a missing input, not a decision): {shown}. "
            f"See jobs/larrey-triage/output/TODO.md")


# ---------------------------------------------------------------- back-test

PAPINIAN = "research/excavator/claude-papinian-2026-11-10"
HALOANDER = "research/excavator/claude-haloander-2026-11-07"


class _FeatData:
    def __init__(self, feats):
        self._f = feats

    def kit(self):
        return self._f


def _jl(path):
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for l in fh:
                if l.strip():
                    out.append(json.loads(l))
    return out


def undecided_outcomes(repo):
    """One row per attempted undecided order in Papinian u01b/u02/u03 and Haloander u01-u03, with its frozen
    overlay dossier and its outcome."""
    kf = _kf()
    repo = Path(repo)
    rows = {}
    for wave, base, batches in (("papinian", PAPINIAN, ["u01b", "u02", "u03"]),
                                ("haloander", HALOANDER, ["u01", "u02", "u03"])):
        for b in batches:
            pk = repo / base / b / "packet"
            disp = None
            for f in ("DISPATCH_CHECK.json", "dispatch-v3.json"):
                if (pk / f).exists():
                    disp = set(json.loads((pk / f).read_text(encoding="utf-8"))["dispatchable_ids"])
            for ev in sorted(pk.glob("undecided/*/EVIDENCE.json")):
                e = json.loads(ev.read_text(encoding="utf-8"))
                sd = json.loads((ev.parent / "STATUS_DECISION.json").read_text(encoding="utf-8"))
                iid = e["instrument_id"]
                rows[iid] = {"wave": wave, "batch": b, "dispatched": disp is None or iid in disp,
                             "producer_status": bool(sd.get("approved") is True
                                                     and sd.get("recommended_provisional_status") in ("yes", "no")),
                             "accepted": False, "filed": False,
                             "features": kf.from_dossier(e["base_dossier"], status=None)}
    reviews = (glob.glob(str(repo / PAPINIAN / "u0*/overlay/*/review-v1/STATUS_REVIEW.json"))
               + glob.glob(str(repo / HALOANDER / "u0*/packet/undecided/*/STATUS_REVIEW.json"))
               + glob.glob(str(repo / HALOANDER / "ux/overlay/*/proposal-v1/STATUS_REVIEW.json")))
    for p in reviews:
        r = json.loads(Path(p).read_text(encoding="utf-8"))
        if r.get("instrument_id") in rows and r.get("decision") == "accept":
            rows[r["instrument_id"]]["accepted"] = True
    for p in (glob.glob(str(repo / PAPINIAN / "u0*/overlay/REPLACEMENT_PROPOSAL.jsonl"))
              + glob.glob(str(repo / HALOANDER / "ux/overlay/REPLACEMENT_PROPOSAL.jsonl"))):
        for r in _jl(p):
            iid = r.get("instrument_id") or (r.get("claim") or {}).get("instrument_id")
            if iid in rows:
                rows[iid]["filed"] = True
    for r in rows.values():
        r["outcome"] = ("filed" if r["filed"] else "status_accepted" if r["accepted"] else
                        "producer_status_only" if r["producer_status"] else
                        "failed_after_dispatch" if r["dispatched"] else "dispatch_blocked")
    return rows


def decided_outcomes(repo):
    """One row per order in Papinian's decided lifecycle batches (y01-y14 YES, c01 own-claim corrections)."""
    kf = _kf()
    repo = Path(repo)
    kit_dir = str(repo / "jobs/claim-kit")
    if kit_dir not in sys.path:
        sys.path.insert(0, kit_dir)
    import batch
    rows = {}
    for pk in sorted((repo / PAPINIAN).glob("y*/packet")) + [repo / PAPINIAN / "c01/packet"]:
        if not (pk / "PACKET.json").exists():
            continue
        b = pk.parent.name
        ds = batch.decode(json.loads((pk / "PACKET.json").read_text(encoding="utf-8")))
        ass = {a["id"]: a for a in _jl(pk / "ASSESSMENT.jsonl")}
        filed = set()
        for p in pk.glob("complete-v*/CLAIMS.publishable.jsonl"):
            filed |= {r["instrument_id"] for r in _jl(p)}
        for iid, d in ds.items():
            a = ass.get(iid, {})
            rows[iid] = {"wave": "papinian", "batch": b, "features": kf.from_dossier(d),
                         "outcome": "filed" if iid in filed else
                         "submitted_not_filed" if a.get("outcome") == "submit" else "blocked",
                         "blocker": (a.get("blocker") or "")[:160]}
    return rows


def _kf():
    if str(LLULL) not in sys.path:
        sys.path.insert(0, str(LLULL))
    import kit_features
    return kit_features


def _score(rows, route, gates, G, success, failure):
    """Kept-out counts for the conjunction of gates."""
    D = _FeatData({i: r["features"] for i, r in rows.items()})
    c = Counter()
    kept = []
    for iid, r in rows.items():
        status = r["features"].get("status") or ""
        row = {"instrument_id": iid, "provisional_status": status if status in ("yes", "no") else ""}
        passed = all(G[g][1](row, D) in ("held", "na") for g in gates)
        c[(r["outcome"], passed)] += 1
        if not passed:
            kept.append(iid)
    res = {"gates": list(gates), "admitted": sum(v for (o, p), v in c.items() if p)}
    for o in success + failure:
        res[o] = {"kept_out": c[(o, False)], "of": c[(o, False)] + c[(o, True)]}
    res["failures_kept_out"] = sum(c[(o, False)] for o in failure)
    res["failures"] = sum(c[(o, False)] + c[(o, True)] for o in failure)
    res["successes_lost"] = sum(c[(o, False)] for o in success)
    res["successes"] = sum(c[(o, False)] + c[(o, True)] for o in success)
    return res, kept


UNDECIDED_LADDER = [
    [], ["original_usable"], ["original_usable", "no_page_check_owed"],
    ["original_usable", "no_page_check_owed", "status_basis_record"],
    ["original_usable", "no_page_check_owed", "status_basis_record", "clause_inventory_present"],
    ["original_usable", "no_page_check_owed", "status_basis_record", "clause_inventory_present",
     "later_order_text_held"],
]
DECIDED_LADDER = [
    [], ["original_usable"], ["original_usable", "no_page_check_owed"],
    ["original_usable", "no_page_check_owed", "clause_inventory_present"],
    ["original_usable", "no_page_check_owed", "clause_inventory_present", "nea_notice_if_emergency"],
]


def backtest(repo=REPO, diagnosis=None, write=True):
    repo = Path(repo)
    G = _llull().GATES
    und = undecided_outcomes(repo)
    dec = decided_outcomes(repo)
    succ_u = ["filed", "status_accepted", "producer_status_only"]
    fail_u = ["failed_after_dispatch", "dispatch_blocked"]
    succ_d = ["filed", "submitted_not_filed"]
    fail_d = ["blocked"]
    result = {"schema": "larrey.backtest/v1", "generated_at": now(),
              "sources": {"undecided": [PAPINIAN + "/u01b", PAPINIAN + "/u02", PAPINIAN + "/u03",
                                        HALOANDER + "/u01", HALOANDER + "/u02", HALOANDER + "/u03"],
                          "decided": [PAPINIAN + "/y01..y14", PAPINIAN + "/c01"]},
              "method": "Gates evaluated on each order's frozen dossier (overlay EVIDENCE.json base_dossier, or the "
                        "decoded PACKET.json dossier) as the producer received it; outcomes from the same folders "
                        "(dispatch checks, producer decisions, independent status reviews, both-arm replacement "
                        "proposals, completion publishable claims).",
              "calibrated_code_sha256": {spec["calibrated_on"]: sha_file(repo / spec["calibrated_on"])
                                         for spec in ROUTES.values()},
              "undecided": {"orders": len(und), "outcomes": dict(Counter(r["outcome"] for r in und.values())),
                            "by_wave": {w: dict(Counter(r["outcome"] for r in und.values() if r["wave"] == w))
                                        for w in ("papinian", "haloander")},
                            "curve": [], "by_wave_operating_point": {}, "single_gates": {}},
              "decided": {"orders": len(dec), "outcomes": dict(Counter(r["outcome"] for r in dec.values())),
                          "curve": [], "single_gates": {}}}
    for gates in UNDECIDED_LADDER:
        s, kept = _score(und, "undecided_full", gates, G, succ_u, fail_u)
        result["undecided"]["curve"].append(s)
    for g in ROUTES["undecided_full"]["hard"] + ROUTES["undecided_full"]["soft"]:
        result["undecided"]["single_gates"][g] = _score(und, "undecided_full", [g], G, succ_u, fail_u)[0]
    op = UNDECIDED_LADDER[-1]
    for w in ("papinian", "haloander"):
        sub = {i: r for i, r in und.items() if r["wave"] == w}
        result["undecided"]["by_wave_operating_point"][w] = _score(sub, "undecided_full", op, G, succ_u, fail_u)[0]
    _, kept_u = _score(und, "undecided_full", op, G, succ_u, fail_u)
    for gates in DECIDED_LADDER:
        result["decided"]["curve"].append(_score(dec, "decided_lifecycle", gates, G, succ_d, fail_d)[0])
    for g in ROUTES["decided_lifecycle"]["hard"] + ROUTES["decided_lifecycle"]["soft"]:
        result["decided"]["single_gates"][g] = _score(dec, "decided_lifecycle", [g], G, succ_d, fail_d)[0]
    _, kept_d = _score(dec, "decided_lifecycle", DECIDED_LADDER[-1], G, succ_d, fail_d)
    kept_rows = [{"instrument_id": i, "route": "undecided_full", "wave": und[i]["wave"], "batch": und[i]["batch"],
                  "outcome": und[i]["outcome"]} for i in sorted(kept_u)]
    kept_rows += [{"instrument_id": i, "route": "decided_lifecycle", "wave": "papinian", "batch": dec[i]["batch"],
                   "outcome": dec[i]["outcome"], "blocker": dec[i]["blocker"]} for i in sorted(kept_d)]
    if diagnosis and Path(diagnosis).exists():
        diag = {r["instrument_id"]: r for r in csv.DictReader(open(diagnosis, encoding="utf-8"))}
        c = Counter((diag[i]["final_primary_cause"], diag[i]["final_best_status"] or "unknown")
                    for i in kept_u if i in diag)
        result["undecided"]["kept_out_by_respondendi_diagnosis"] = {
            "source": "Respondendi DIAGNOSIS.csv (PR 270, research/excavator/claude-respondendi-2026-11-10)",
            "diagnosed": sum(c.values()),
            "by_cause_and_best_status": {f"{k[0]}|{k[1]}": v for k, v in c.most_common()}}
        for k in kept_rows:
            if k["instrument_id"] in diag:
                k["respondendi_cause"] = diag[k["instrument_id"]]["final_primary_cause"]
                k["respondendi_best_status"] = diag[k["instrument_id"]]["final_best_status"]
    result["operating_point"] = {"undecided_full": op, "decided_lifecycle": DECIDED_LADDER[-1]}
    result["kept_out"] = kept_rows
    result["costs"] = measured_costs(repo)
    if write:
        _write((repo / BACKTEST), json.dumps(result, indent=1) + "\n")
    return result


COST_LINE = re.compile(r"^(?P<label>\S+) \S+ (?P<role>\S+) \S+ cost (?P<usd>[0-9.]+)")


def measured_costs(repo):
    """Worker dollars per batch and role from Papinian COSTS.log; batch totals from the BATCHES files."""
    repo = Path(repo)
    by = defaultdict(lambda: defaultdict(float))
    log = repo / PAPINIAN / "COSTS.log"
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            m = COST_LINE.match(line)
            if not m:
                continue
            batch = m["label"].rsplit("-", 2)
            b = next((x for x in m["label"].split("-") if re.fullmatch(r"(u\d+b?|u23|u02u03|y\d+|c\d+|r\d+b?)", x)), None)
            if b:
                by[b][m["role"]] += float(m["usd"])
    def batches(rel):
        p = repo / rel
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    return {"papinian_by_batch_role": {b: {r: round(v, 4) for r, v in roles.items()} for b, roles in sorted(by.items())},
            "papinian_undecided_batches": batches(PAPINIAN + "/BATCHES_status_assignment.undecided.json"),
            "papinian_yes_batches": batches(PAPINIAN + "/BATCHES_production.claim_ready.yes.fr.json"),
            "haloander_batches": batches(HALOANDER + "/BATCHES_probe.json"),
            "basis": "list-price worker dollars (jobs/necker-costs/PRICES.json via the waves' own cost tools); "
                     "coordinator dollars excluded"}


# ---------------------------------------------------------------- projection

def project(repo=REPO, bt=None):
    """Projected cost per adopted status with the gate against without it, from the back-test and measured costs.

    Model P (producer-only, primary): the gate removes the producer cost of each kept-out dispatched order; review
    cost is unchanged, because the gate kept out no order that reached review. Model A (all-in per attempt): every
    worker dollar scales with attempted orders. Both are projections, not measurements.
    """
    repo = Path(repo)
    bt = bt or json.loads((repo / BACKTEST).read_text(encoding="utf-8"))
    costs = bt["costs"]
    und = undecided_outcomes(repo)
    G = _llull().GATES
    op = bt["operating_point"]["undecided_full"]
    D = _FeatData({i: r["features"] for i, r in und.items()})

    def admitted(iid):
        st = und[iid]["features"].get("status") or ""
        return all(G[g][1]({"instrument_id": iid, "provisional_status": st}, D) in ("held", "na") for g in op)

    out = {"schema": "larrey.projection/v1", "label": "PROJECTION (not measured): what the measured waves would "
                                                      "have cost had the gate run first", "routes": {}}
    pb = costs["papinian_by_batch_role"]
    prod = sum(pb.get(b, {}).get("producer", 0) for b in ("u01b", "u02", "u03"))
    rev = sum(v for b in ("u01b", "u02", "u03", "u23", "u02u03") for r, v in pb.get(b, {}).items() if r != "producer")
    pu = {i: r for i, r in und.items() if r["wave"] == "papinian"}
    disp = [i for i, r in pu.items() if r["dispatched"]]
    disp_kept = [i for i in disp if not admitted(i)]
    attempted_kept = [i for i in pu if not admitted(i)]
    usd = sum(b["usd"] for b in costs["papinian_undecided_batches"])
    adopted = sum(1 for r in pu.values() if r["outcome"] == "filed")
    accepted = sum(1 for r in pu.values() if r["outcome"] in ("filed", "status_accepted"))
    lost = sum(1 for i, r in pu.items() if r["outcome"] in ("filed", "status_accepted", "producer_status_only")
               and not admitted(i))
    per_prod = prod / len(disp) if disp else 0
    with_p = usd - per_prod * len(disp_kept)
    with_a = usd * (len(pu) - len(attempted_kept)) / len(pu)
    out["routes"]["status_assignment.undecided (Papinian u01b+u02+u03)"] = {
        "attempted": len(pu), "dispatched": len(disp), "kept_out_attempted": len(attempted_kept),
        "kept_out_dispatched": len(disp_kept), "successes_lost": lost,
        "worker_usd_measured": round(usd, 2), "producer_usd_measured": round(prod, 2),
        "review_usd_measured": round(rev, 2),
        "adopted_statuses": adopted, "statuses_accepted": accepted,
        "usd_per_attempt_without": round(usd / len(pu), 3),
        "usd_per_adopted_without": round(usd / adopted, 2) if adopted else None,
        "usd_per_adopted_with_P": round(with_p / adopted, 2) if adopted else None,
        "usd_per_adopted_with_A": round(with_a / adopted, 2) if adopted else None,
        "usd_per_accepted_status_without": round(usd / accepted, 2) if accepted else None,
        "usd_per_accepted_status_with_P": round(with_p / accepted, 2) if accepted else None,
        "usd_per_accepted_status_with_A": round(with_a / accepted, 2) if accepted else None,
    }
    hb = costs["haloander_batches"]
    hu = {i: r for i, r in und.items() if r["wave"] == "haloander"}
    if hb and hu:
        husd = sum(b["usd"] for b in hb)
        hk = [i for i in hu if not admitted(i)]
        hadopt = sum(1 for r in hu.values() if r["outcome"] == "filed")
        hw = husd * (len(hu) - len(hk)) / len(hu)
        out["routes"]["status_assignment.undecided (Haloander probe)"] = {
            "attempted": len(hu), "kept_out_attempted": len(hk), "worker_usd_measured": husd,
            "adopted_statuses": hadopt, "usd_per_adopted_without": round(husd / hadopt, 2) if hadopt else None,
            "usd_per_adopted_with_A": round(hw / hadopt, 2) if hadopt else None,
            "note": "no per-role costs recorded; model A only"}
    dec = decided_outcomes(repo)
    opd = bt["operating_point"]["decided_lifecycle"]
    Dd = _FeatData({i: r["features"] for i, r in dec.items()})
    ys = {i: r for i, r in dec.items() if r["batch"].startswith("y")}

    def admitted_d(iid):
        st = ys[iid]["features"].get("status") or ""
        return all(G[g][1]({"instrument_id": iid, "provisional_status": st}, Dd) in ("held", "na") for g in opd)

    yusd = sum(b["usd"] for b in costs["papinian_yes_batches"])
    yprod = sum(v.get("producer", 0) for b, v in pb.items() if b.startswith("y"))
    yfiled = sum(1 for r in ys.values() if r["outcome"] == "filed")
    yk = [i for i in ys if not admitted_d(i)]
    ylost = sum(1 for i in yk if ys[i]["outcome"] != "blocked")
    y_with_p = yusd - (yprod / len(ys)) * len(yk) if ys else 0
    y_with_a = yusd * (len(ys) - len(yk)) / len(ys) if ys else 0
    out["routes"]["production.claim_ready.yes.fr (Papinian y01-y14)"] = {
        "attempted": len(ys), "kept_out_attempted": len(yk), "successes_lost": ylost,
        "worker_usd_measured": round(yusd, 2), "producer_usd_measured": round(yprod, 2),
        "filed": yfiled, "usd_per_filed_without": round(yusd / yfiled, 2) if yfiled else None,
        "usd_per_filed_with_P": round(y_with_p / yfiled, 2) if yfiled else None,
        "usd_per_filed_with_A": round(y_with_a / yfiled, 2) if yfiled else None}
    return out


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(prog="larrey", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("triage", help="verdicts for every order -> output/")
    t.add_argument("--out")
    t.add_argument("--no-pools", action="store_true", help="skip per-action pools (the job: Bentham counts them)")
    b = sub.add_parser("backtest", help="score the gates on past waves -> BACKTEST.json")
    b.add_argument("--diagnosis", help="Respondendi DIAGNOSIS.csv (PR 270), optional")
    p = sub.add_parser("project", help="projected cost per adopted status, with and without the gate")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    if a.cmd == "triage":
        out_dir = a.out or os.environ.get("OUTPUT_DIR")
        summary, reasons, pools = triage(repo, out_dir, pools=not a.no_pools)
        for route, t in reasons.items():
            print(f"{route}: {t['admitted']} of {t['orders']} admitted ({t['admitted_hard_only']} on hard gates only)")
        for act, pl in pools.items():
            if pl.get("route"):
                print(f"  {act}: {pl['admitted']} of {pl['members']} admitted")
    elif a.cmd == "backtest":
        r = backtest(repo, a.diagnosis)
        for route in ("undecided", "decided"):
            for s in r[route]["curve"]:
                print(f"{route} {'+'.join(s['gates']) or 'none'}: failures kept out {s['failures_kept_out']}/"
                      f"{s['failures']}, successes lost {s['successes_lost']}/{s['successes']}")
    elif a.cmd == "project":
        res = project(repo)
        text = json.dumps(res, indent=1) + "\n"
        if a.out:
            _write(Path(a.out), text)
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
