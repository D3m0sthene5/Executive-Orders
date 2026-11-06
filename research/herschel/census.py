"""Herschel, step 1: the free census of all remaining work, and the deep-sample draw.

Named for William Herschel's star gauges (1785): he counted stars in 683 sample fields to infer the shape of the whole
galaxy. Herschel does the same for the project's remaining work: a free, complete census of every open order-step
(this script), a probability sample of orders run end to end by instrumented agents, and a projection back to the
whole census.

Inputs are committed files only. The order-step frame and its cost tiers reuse
`research/progress/remaining-work/build_effort.py` (whose minutes are mostly assumed; Herschel replaces them with
measurements). Two kinds of work that model omits are added: replacing a transcription with an official original
(with the quotation recheck it carries), and independent human certification of every dossier.

Outputs (research/herschel/frame/):
  CELLS.csv        one row per open order-step: order, stratum, step, tier, assumed minutes
  ORDERS.csv       one row per order: stratum and cheap features (era, status, text length, clauses, edges...)
  STRATA.json      population, assumed effort and sample allocation per stratum
  SAMPLE.csv       the drawn sample with inclusion weights (orders each sampled order stands for)
  ASSIGNMENTS.json the sample split across coordinators, balanced by assumed effort
Run: python3 -I research/herschel/census.py
"""
from __future__ import annotations

import collections
import csv
import json
import math
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "frame"
sys.path.insert(0, str(REPO / "research/progress/remaining-work"))
csv.field_size_limit(10**9)

SEED = 17850101          # Herschel's "On the Construction of the Heavens" was read to the Royal Society in 1785
ROUND1 = 120             # deep-sample orders in round 1
MIN_PER_STRATUM = 6
COORDINATORS = 4
ERAS = [(0, 1906, "pre1907"), (1907, 1936, "1907-36"), (1937, 1989, "1937-89"), (1990, 9999, "1990on")]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def era_of(date):
    m = re.match(r"(\d{4})", date or "")
    if not m:
        return "undated"
    y = int(m.group(1))
    return next(name for lo, hi, name in ERAS if lo <= y <= hi)


def text_lengths():
    """Characters of the longest held text per order (any class), as a size feature."""
    sys.path.insert(0, str(REPO / "jobs/_lib"))
    import eo_identity as ident
    frags = ident.load_fragments(str(REPO))
    out = {}
    for iid, fs in frags.items():
        best = 0
        for f in fs:
            p = f.get("text_path")
            if p:
                try:
                    best = max(best, Path(p).stat().st_size)
                except OSError:
                    pass
        out[iid] = best
    return out


def counts_by(path, key):
    c = collections.Counter()
    if Path(path).is_file():
        with open(path, encoding="utf-8") as f:
            if str(path).endswith(".jsonl"):
                for line in f:
                    try:
                        c[json.loads(line).get(key)] += 1
                    except ValueError:
                        pass
            else:
                for r in csv.DictReader(f):
                    c[r.get(key)] += 1
    return c


def main():
    import build_effort as BE
    records, model = BE.assign()
    readiness = {r["instrument_id"]: r for r in read_csv(REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")}
    register = {r["instrument_id"]: r for r in read_csv(REPO / "jobs/domesday-register/output/REGISTER.csv")}
    tlen = text_lengths()
    clauses = counts_by(REPO / "jobs/claim-kit/output/CLAUSES.jsonl", "instrument_id")
    edges = counts_by(REPO / "jobs/later-events/output/EDGES.csv", "target_id")

    def stratum(iid):
        r = readiness.get(iid, {})
        if r.get("ready_for_human_review") == "yes":
            return "ready"
        status = r.get("provisional_status") or "none"
        return f"{status}.{era_of(register.get(iid, {}).get('date'))}"

    OUT.mkdir(parents=True, exist_ok=True)
    cells = []
    for rec in records:
        iid = rec["instrument_id"]
        minutes = float(model[rec["tier"]]["minutes"]) * float(rec.get("mult") or 1)
        basis = model[rec["tier"]]["basis"].split(":")[0]
        cells.append({"instrument_id": iid or "", "stratum": stratum(iid) if iid else "not_in_census",
                      "step": rec["step"], "tier": rec["tier"], "count": rec["count"],
                      "assumed_minutes": round(minutes, 2), "basis": basis})
    # Work the effort model omits: replacing a transcription with an official original (and rechecking quotations),
    # and independent human certification of every dossier (human time, not tokens).
    for iid, r in readiness.items():
        if r.get("original_copy_replacement_required") == "yes":
            cells.append({"instrument_id": iid, "stratum": stratum(iid), "step": "replace_original", "tier": "RO",
                          "count": 1, "assumed_minutes": "", "basis": "unmodelled"})
        cells.append({"instrument_id": iid, "stratum": stratum(iid), "step": "human_certification", "tier": "HC",
                      "count": 1, "assumed_minutes": "", "basis": "human time, unmodelled"})
    with open(OUT / "CELLS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cells[0]))
        w.writeheader()
        w.writerows(cells)

    per_order = collections.defaultdict(lambda: {"minutes": 0.0, "steps": []})
    for c in cells:
        if c["instrument_id"] and c["assumed_minutes"] != "":
            per_order[c["instrument_id"]]["minutes"] += float(c["assumed_minutes"])
            per_order[c["instrument_id"]]["steps"].append(c["step"])
    orders = []
    for iid, r in readiness.items():
        g = register.get(iid, {})
        orders.append({"instrument_id": iid, "stratum": stratum(iid), "era": era_of(g.get("date")),
                       "status": r.get("provisional_status") or "none", "ready": r.get("ready_for_human_review"),
                       "date": g.get("date", ""), "best_held": g.get("best_held", ""), "text_chars": tlen.get(iid, 0),
                       "clauses": clauses.get(iid, 0), "later_edges": edges.get(iid, 0),
                       "open_steps": "|".join(per_order[iid]["steps"]),
                       "assumed_minutes": round(per_order[iid]["minutes"], 1),
                       "blockers": r.get("blockers", ""),
                       "transcription_dependent": r.get("original_copy_replacement_required") == "yes"})
    with open(OUT / "ORDERS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(orders[0]))
        w.writeheader()
        w.writerows(orders)

    # Allocation: Neyman allocation n_h proportional to N_h x S_h. Per-order cost spread is unmeasured, so S_h is
    # taken proportional to the stratum's mean assumed minutes (a coefficient of variation of about 1, as in the
    # 2026-10-18 pilot), with a floor so every stratum is measured. Ready orders get a small reading-only sample.
    by = collections.defaultdict(list)
    for o in orders:
        by[o["stratum"]].append(o)
    work = {h: v for h, v in by.items() if h != "ready" and sum(o["assumed_minutes"] for o in v) > 0}
    weight = {h: sum(o["assumed_minutes"] for o in v) for h, v in work.items()}  # N_h x mean_h
    total_w = sum(weight.values())
    alloc = {h: max(MIN_PER_STRATUM, round(ROUND1 * weight[h] / total_w)) for h in work}
    alloc = {h: min(alloc[h], len(work[h])) for h in alloc}
    rnd = random.Random(SEED)
    sample = []
    for h in sorted(work):
        members = sorted(work[h], key=lambda o: (o["text_chars"], o["instrument_id"]))
        n = alloc[h]
        step = len(members) / n
        start = rnd.random() * step
        picks = [members[min(len(members) - 1, int(start + k * step))] for k in range(n)]
        for o in picks:
            sample.append({**o, "weight": round(len(members) / n, 3), "sample_kind": "deep"})
    ready = sorted(by.get("ready", []), key=lambda o: o["text_chars"])
    for o in [ready[int((k + 0.5) * len(ready) / 6)] for k in range(6)] if ready else []:
        sample.append({**o, "weight": round(len(ready) / 6, 3), "sample_kind": "certification_reading"})
    cands = read_csv(REPO / "jobs/domesday-register/output/CANDIDATES_NOT_IN_REGISTER.csv")
    cand_sample = rnd.sample(cands, min(6, len(cands)))

    with open(OUT / "SAMPLE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sample[0]))
        w.writeheader()
        w.writerows(sample)
    (OUT / "ADMISSION_SAMPLE.json").write_text(json.dumps(cand_sample, indent=2) + "\n")

    # Split deep orders across coordinators balanced by assumed minutes. (The committed ASSIGNMENTS.json then dealt the
    # largest stratum, none.1907-36, across all four coordinators one order at a time, so no coordinator holds it alone.)
    deep = [s for s in sample if s["sample_kind"] == "deep"]
    groups = [{"orders": [], "minutes": 0.0, "strata": []} for _ in range(COORDINATORS)]
    for h in sorted({s["stratum"] for s in deep}, key=lambda h: -sum(s["assumed_minutes"] for s in deep if s["stratum"] == h)):
        members = [s for s in deep if s["stratum"] == h]
        g = min(groups, key=lambda g: g["minutes"])
        g["orders"] += [m["instrument_id"] for m in members]
        g["minutes"] += sum(m["assumed_minutes"] for m in members)
        g["strata"].append(h)
    (OUT / "ASSIGNMENTS.json").write_text(json.dumps({
        "coordinators": [{"name": f"H{i + 1}", "concurrency": c, **g}
                         for i, (g, c) in enumerate(zip(groups, (4, 8, 8, 16)))],
        "certification_reading": [s["instrument_id"] for s in sample if s["sample_kind"] == "certification_reading"],
        "admission": [c.get("candidate_id") or c.get("id") or c for c in cand_sample]}, indent=2) + "\n")

    strata = {h: {"population": len(v), "assumed_minutes": round(sum(o["assumed_minutes"] for o in v), 1),
                  "sampled": alloc.get(h, 6 if h == "ready" else 0)} for h, v in sorted(by.items())}
    summary = {"orders": len(orders), "cells": sum(int(c["count"]) for c in cells),
               "cells_by_step": dict(collections.Counter(c["step"] for c in cells for _ in range(int(c["count"])))),
               "assumed_agent_hours": round(sum(float(c["assumed_minutes"] or 0) * int(c["count"]) for c in cells) / 60),
               "tiers_by_basis": dict(collections.Counter(r["basis"].split(":")[0] for r in model.values())),
               "strata": strata, "round1_deep": len(deep), "seed": SEED}
    (OUT / "STRATA.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "strata"}, indent=2))
    for h, s in strata.items():
        print(f"{h:22} N={s['population']:6}  assumed hours={s['assumed_minutes'] / 60:8.0f}  sample={s['sampled']}")


if __name__ == "__main__":
    main()
