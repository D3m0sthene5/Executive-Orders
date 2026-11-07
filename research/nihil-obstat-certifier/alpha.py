#!/usr/bin/env python3
"""Krippendorff's alpha (nominal metric) for two or more certifiers over exported decisions.

Reads the JSONL files the Nihil obstat page exports (schema eo-nihil-obstat-decision/v1). The coder is
the reviewer name; the unit is the claim (overall decision) or each claim element (--level elements).
Any number of coders, with missing data: a unit counts when at least two coders judged it.

  python alpha.py alice.jsonl bob.jsonl
  python alpha.py *.jsonl --level elements --bootstrap 2000 --seed 1

Method: Krippendorff, K. (2011), "Computing Krippendorff's Alpha-Reliability", Departmental Papers (ASC) 43,
University of Pennsylvania, https://repository.upenn.edu/asc_papers/43 ; and Krippendorff (2004), Content
Analysis, 2nd ed., ch. 11. Interpretation (2004, p. 241): alpha >= 0.800 reliable; 0.667 to 0.800 only
tentative conclusions; below 0.667 discard. Standard library only. Changes no count.
"""

import argparse
import collections
import itertools
import json
import random
import statistics
import sys

VALUES = ("certify", "reject", "needs_more")


def coincidences(units):
    """Coincidence matrix {(c, k): o_ck} from units = iterable of lists of coded values (None = missing)."""
    o = collections.defaultdict(float)
    for values in units:
        vals = [v for v in values if v is not None]
        m = len(vals)
        if m < 2:
            continue                      # an unpairable value carries no information about agreement
        for i, j in itertools.permutations(range(m), 2):
            o[(vals[i], vals[j])] += 1.0 / (m - 1)
    return o


def alpha_nominal(units, detail=False):
    """Krippendorff's alpha with the nominal metric. None when expected disagreement is zero
    (fewer than two pairable values, or every value identical, so there is nothing to agree about)."""
    o = coincidences(units)
    n_c = collections.defaultdict(float)
    for (c, _k), v in o.items():
        n_c[c] += v
    n = sum(n_c.values())
    if n < 2:
        result = {"alpha": None, "n": n, "d_o": None, "d_e": None, "value_counts": dict(n_c)}
        return result if detail else None
    observed = sum(v for (c, k), v in o.items() if c != k)
    expected = sum(n_c[c] * n_c[k] for c in n_c for k in n_c if c != k)
    d_o = observed / n
    d_e = expected / (n * (n - 1))
    a = None if d_e == 0 else 1.0 - d_o / d_e
    if not detail:
        return a
    return {"alpha": a, "n": n, "d_o": d_o, "d_e": d_e, "value_counts": dict(n_c)}


def bootstrap_ci(units, reps, seed, level=0.95):
    """Percentile interval from resampling units with replacement (a simple approximation of
    Krippendorff's bootstrap; use it as a guide with fewer than about 30 coded units)."""
    units = [u for u in units if sum(v is not None for v in u) >= 2]
    rng = random.Random(seed)
    draws = []
    for _ in range(reps):
        a = alpha_nominal([units[rng.randrange(len(units))] for _ in units])
        if a is not None:
            draws.append(a)
    if len(draws) < reps // 2:
        return None
    draws.sort()
    lo = draws[int(((1 - level) / 2) * (len(draws) - 1))]
    hi = draws[int((1 - (1 - level) / 2) * (len(draws) - 1))]
    return lo, hi


def read_records(paths):
    recs = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError as exc:
                    raise SystemExit(f"{path}:{n}: not JSON ({exc})")
                if isinstance(r, dict) and r.get("schema") == "eo-nihil-obstat-decision/v1":
                    r["_where"] = f"{path}:{n}"
                    recs.append(r)
    return recs


def coder_id(rec):
    name = (rec.get("reviewer") or {}).get("name") if isinstance(rec.get("reviewer"), dict) else rec.get("reviewer")
    return " ".join(str(name or "").lower().split())


def build_units(records, level="overall", duplicates="latest"):
    """({unit_key: {coder: value}}, {coder: [active seconds per claim]}, dropped duplicate count)."""
    latest = {}
    dropped = 0
    for r in records:
        key = (coder_id(r), r.get("claim_sha256"))
        if not key[0] or not key[1]:
            continue
        if key in latest:
            if duplicates == "error":
                raise SystemExit(f"{r['_where']}: coder {key[0]!r} decided claim {key[1][:12]} more than once "
                                 f"(also {latest[key]['_where']}); use --duplicates latest to keep the newest")
            dropped += 1
            if (r.get("decided_utc") or "") < (latest[key].get("decided_utc") or ""):
                continue
        latest[key] = r
    units = collections.defaultdict(dict)
    seconds = collections.defaultdict(list)
    for (coder, sha), r in latest.items():
        seconds[coder].append(r.get("active_seconds") or 0)
        if level == "overall":
            if r.get("overall") in VALUES:
                units[sha][coder] = r["overall"]
        else:
            for e in r.get("elements") or []:
                if e.get("decision") in VALUES:
                    units[(sha, e.get("element"))][coder] = e["decision"]
    return units, seconds, dropped


def interpret(a):
    if a is None:
        return "undefined (no variation among the coded values, or fewer than two pairable values)"
    if a >= 0.800:
        return "reliable (>= 0.800, Krippendorff 2004)"
    if a >= 0.667:
        return "tentative conclusions only (0.667 to 0.800, Krippendorff 2004)"
    return "below 0.667: do not rely on these codes"


def report(paths, level="overall", duplicates="latest", bootstrap=0, seed=0):
    records = read_records(paths)
    units, seconds, dropped = build_units(records, level, duplicates)
    coded = [list(u.values()) for u in units.values()]
    multi = [u for u in coded if len(u) >= 2]
    res = alpha_nominal(coded, detail=True)
    coders = sorted({c for u in units.values() for c in u})
    out = {"level": level, "coders": coders, "units_coded": len(coded), "units_with_two_or_more_coders": len(multi),
           "pairable_values": res["n"], "alpha": res["alpha"], "observed_disagreement": res["d_o"],
           "expected_disagreement": res["d_e"], "value_counts": res["value_counts"],
           "interpretation": interpret(res["alpha"]), "duplicate_decisions_superseded": dropped}
    if bootstrap and multi:
        out["alpha_95ci_bootstrap"] = bootstrap_ci(coded, bootstrap, seed)
    if level == "overall" and seconds:
        flat = [s for v in seconds.values() for s in v if s]
        if flat:
            out["active_seconds_per_claim"] = {"median": statistics.median(flat), "mean": round(statistics.mean(flat), 1),
                                               "claims_timed": len(flat),
                                               "claims_per_hour_at_median": round(3600 / statistics.median(flat), 2)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="decision JSONL files exported by the page (one per certifier, or combined)")
    ap.add_argument("--level", choices=("overall", "elements"), default="overall")
    ap.add_argument("--duplicates", choices=("latest", "error"), default="latest")
    ap.add_argument("--bootstrap", type=int, default=0, metavar="N", help="N bootstrap resamples for a 95%% interval")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args(argv)
    rep = report(args.files, args.level, args.duplicates, args.bootstrap, args.seed)
    if args.json:
        print(json.dumps(rep, indent=1))
        return 0
    a = rep["alpha"]
    print(f"Krippendorff's alpha (nominal), level={rep['level']}: " + ("undefined" if a is None else f"{a:.4f}"))
    print(f"  coders: {', '.join(rep['coders']) or '(none)'}")
    print(f"  units coded: {rep['units_coded']}; with two or more coders: {rep['units_with_two_or_more_coders']}; "
          f"pairable values: {rep['pairable_values']:g}")
    if rep.get("alpha_95ci_bootstrap"):
        lo, hi = rep["alpha_95ci_bootstrap"]
        print(f"  bootstrap 95% interval: {lo:.3f} to {hi:.3f}")
    print(f"  value counts: {rep['value_counts']}")
    print(f"  reading: {rep['interpretation']}")
    if "active_seconds_per_claim" in rep:
        t = rep["active_seconds_per_claim"]
        print(f"  page time: median {t['median']:g} s per claim over {t['claims_timed']} claims "
              f"({t['claims_per_hour_at_median']} claims per hour)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
