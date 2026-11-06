"""Herschel, round 2: an independent replicate draw from the same census.

A second probability sample, drawn with a new seed from the orders round 1 did not take, gives each stratum more
measured orders and, more usefully, a replicate: the projection is computed from each round alone and from both
together, and the gap between the two rounds is a direct, assumption-light check on the projection's uncertainty
(the method of interpenetrating subsamples, P. C. Mahalanobis, Indian Statistical Institute, 1940s).

Inputs: frame/ORDERS.csv and frame/SAMPLE.csv written by census.py. Outputs: frame/SAMPLE_R2.csv and
frame/ASSIGNMENTS_R2.json. Run: python3 -I research/herschel/replicate.py
"""
from __future__ import annotations

import collections
import csv
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAME = HERE / "frame"
csv.field_size_limit(10**9)

SEED = 19400101          # Mahalanobis's interpenetrating subsamples, Bengal crop surveys of the 1940s
ROUND2 = 72
MIN_PER_STRATUM = 3
COORDINATORS = (("H5", 12), ("H6", 12))


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    orders = read_csv(FRAME / "ORDERS.csv")
    round1 = {r["instrument_id"] for r in read_csv(FRAME / "SAMPLE.csv")}
    by = collections.defaultdict(list)
    for o in orders:
        o["assumed_minutes"] = float(o["assumed_minutes"] or 0)
        by[o["stratum"]].append(o)
    work = {h: v for h, v in by.items() if h != "ready" and sum(o["assumed_minutes"] for o in v) > 0}
    weight = {h: sum(o["assumed_minutes"] for o in v) for h, v in work.items()}
    total_w = sum(weight.values())
    rnd = random.Random(SEED)
    sample = []
    for h in sorted(work):
        left = sorted((o for o in work[h] if o["instrument_id"] not in round1),
                      key=lambda o: (int(o["text_chars"] or 0), o["instrument_id"]))
        if not left:
            continue
        n = min(len(left), max(MIN_PER_STRATUM, round(ROUND2 * weight[h] / total_w)))
        step = len(left) / n
        start = rnd.random() * step
        for k in range(n):
            o = left[min(len(left) - 1, int(start + k * step))]
            sample.append({**o, "round": 2, "sample_kind": "deep"})
    with open(FRAME / "SAMPLE_R2.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sample[0]))
        w.writeheader()
        w.writerows(sample)
    # Deal orders across the two coordinators one at a time within each stratum, so both see every stratum.
    groups = {name: {"orders": [], "minutes": 0.0, "strata": set()} for name, _ in COORDINATORS}
    names = [n for n, _ in COORDINATORS]
    i = 0
    for h in sorted({s["stratum"] for s in sample}):
        for s in (s for s in sample if s["stratum"] == h):
            g = groups[names[i % len(names)]]
            g["orders"].append(s["instrument_id"])
            g["minutes"] += s["assumed_minutes"]
            g["strata"].add(h)
            i += 1
    (FRAME / "ASSIGNMENTS_R2.json").write_text(json.dumps({"round": 2, "seed": SEED, "coordinators": [
        {"name": n, "concurrency": c, "orders": groups[n]["orders"], "minutes": round(groups[n]["minutes"], 1),
         "strata": sorted(groups[n]["strata"])} for n, c in COORDINATORS]}, indent=2) + "\n")
    counts = collections.Counter(s["stratum"] for s in sample)
    print(json.dumps({"round2": len(sample), "by_stratum": dict(sorted(counts.items())),
                      "per_coordinator": {n: len(groups[n]["orders"]) for n in names}}, indent=2))


if __name__ == "__main__":
    main()
