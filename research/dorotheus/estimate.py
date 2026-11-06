"""Dorotheus C5: design-based estimate of the operative-force share from the Stage 15 stratified sample.

Usage: python3 -I research/dorotheus/estimate.py SAMPLE.csv DISPOSITION.csv OUT.json

Design (research/stage15/STATISTICS/STRATIFIED_POPULATION_SAMPLE_120_BLIND.csv): 12 strata (era x source class)
with stratum size N_h, sample size n_h and design weight N_h / n_h; the weights sum to the census, 14,972.

Estimand (owner ruling R1, research/justinian/ESTIMAND.md): the share of the census with operative force on
2026-10-14 (y = 1 if at least one operative clause, 0 if none). Formal validity (unrevoked on the books) is a
separate column.

Estimator: the stratified mean. Within each stratum the respondents' mean estimates the stratum share (missing
at random within stratum, the default nonresponse assumption); the census share is sum_h (N_h / N) p_h.
Variance: sum_h (N_h / N)^2 (1 - r_h / N_h) s_h^2 / r_h, with r_h the respondents and s_h^2 the sample variance
of y among them (with finite-population correction; a certainty stratum, N_h = n_h, contributes 0). A stratum
with fewer than 2 respondents and N_h > r_h has no variance estimate; it is collapsed with the largest stratum of
the same era for variance (collapsed-strata estimator), and with the largest stratum overall if its era has no
other. A stratum with no respondents contributes its weight through the collapse partner's mean under MAR.
Intervals: Wald (normal) and Korn-Graubard (Clopper-Pearson on the effective sample size n_eff = p(1-p)/V, with
degrees of freedom = respondents - strata), which behaves better near 0 and 1 and for small n.

Sensitivity: (a) MAR within stratum (above); (b) every nonrespondent y = 0 (all nonresponse NO); (c) for the
formal-validity column, the same two.

A response is a filed, independently AI-reviewed claim (outcome filed or ready_existing). Everything is
provisional, AI-reviewed and uncertified (human-certified count: 0).
"""
import csv
import json
import math
import sys
from collections import defaultdict


def beta_ppf(q, a, b):
    """Inverse regularized incomplete beta by bisection (standard library only)."""
    if a <= 0:
        return 0.0
    if b <= 0:
        return 1.0

    def cdf(x):
        # continued fraction (Numerical Recipes betacf) for the regularized incomplete beta
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
        def cf(a_, b_, x_):
            qab, qap, qam = a_ + b_, a_ + 1, a_ - 1
            c, d = 1.0, 1 - qab * x_ / qap
            d = 1 / (d if abs(d) > 1e-300 else 1e-300)
            h = d
            for m in range(1, 300):
                m2 = 2 * m
                aa = m * (b_ - m) * x_ / ((qam + m2) * (a_ + m2))
                d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
                c = 1 + aa / c if abs(c) > 1e-300 else 1e300
                h *= d * c
                aa = -(a_ + m) * (qab + m) * x_ / ((a_ + m2) * (qap + m2))
                d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
                c = 1 + aa / c if abs(c) > 1e-300 else 1e300
                de = d * c
                h *= de
                if abs(de - 1) < 3e-12:
                    break
            return h
        if x < (a + 1) / (a + b + 2):
            return math.exp(lbt) * cf(a, b, x) / a
        return 1 - math.exp(lbt) * cf(b, a, 1 - x) / b

    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if cdf(mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def t_quantile(df):
    table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
             15: 2.131, 20: 2.086, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}
    if df <= 0:
        return float("nan")
    keys = sorted(table)
    for k in keys:
        if df <= k:
            return table[k]
    return 1.960


def estimate(strata, values, mode):
    """strata: {h: {N, n, era}}; values: {h: [y or None for each sampled unit]}; mode: 'mar' or 'nonresponse_zero'."""
    N = sum(s["N"] for s in strata.values())
    obs = {}
    for h, ys in values.items():
        ys = [(0 if y is None else y) for y in ys] if mode == "nonresponse_zero" else [y for y in ys if y is not None]
        obs[h] = ys
    # collapse partners for strata without a usable variance or mean
    def partner(h):
        era = strata[h]["era"]
        same = [k for k in strata if k != h and strata[k]["era"] == era and len(obs[k]) >= 2]
        pool = same or [k for k in strata if k != h and len(obs[k]) >= 2]
        return max(pool, key=lambda k: strata[k]["N"]) if pool else None
    p, var, notes, used = 0.0, 0.0, [], {}
    for h, s in strata.items():
        ys = obs[h]
        W = s["N"] / N
        if not ys:
            k = partner(h)
            ys_eff = obs[k] if k else []
            notes.append(f"stratum {h}: no respondents; mean borrowed from {k} (MAR across strata)")
        else:
            ys_eff = ys
        if not ys_eff:
            continue
        ph = sum(ys_eff) / len(ys_eff)
        p += W * ph
        used[h] = {"respondents": len(ys), "share": ph, "weight": W}
        r = len(ys)
        if s["N"] == r:
            continue  # certainty stratum: no sampling variance
        if r >= 2:
            s2 = sum((y - ph) ** 2 for y in ys) / (r - 1)
            var += W * W * (1 - r / s["N"]) * s2 / r
        else:
            k = partner(h)
            if k:
                yk = obs[k]
                pk = sum(yk) / len(yk)
                s2 = sum((y - pk) ** 2 for y in yk) / (len(yk) - 1)
                rr = max(r, 1)
                var += W * W * (1 - rr / s["N"]) * s2 / rr
                notes.append(f"stratum {h}: {r} respondent(s); variance collapsed with {k}")
    respondents = sum(len(v) for v in obs.values())
    se = math.sqrt(var)
    wald = (max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se))
    df = max(1, respondents - len(strata))
    if 0 < p < 1 and var > 0:
        n_eff = p * (1 - p) / var
        tq, zq = t_quantile(df), 1.96
        n_star = n_eff * (zq / tq) ** 2
        x = p * n_star
        kg = (beta_ppf(0.025, x, n_star - x + 1) if x > 0 else 0.0,
              beta_ppf(0.975, x + 1, n_star - x) if x < n_star else 1.0)
    else:
        n_eff, kg = None, wald
    return {"mode": mode, "share": p, "se": se, "wald_95": wald, "korn_graubard_95": kg, "n_effective": n_eff,
            "df": df, "respondents": respondents, "population": N, "estimated_count": p * N,
            "count_95_korn_graubard": [kg[0] * N, kg[1] * N], "strata": used, "notes": notes}


def main(sample_path, disposition_path, out_path):
    sample = list(csv.DictReader(open(sample_path, encoding="utf-8")))
    disp = {r["id"]: r for r in csv.DictReader(open(disposition_path, encoding="utf-8"))
            if r.get("wave", "sample") in ("", "sample")}
    strata, op, fv, rows = {}, defaultdict(list), defaultdict(list), []
    for s in sample:
        h = f"{s['era']} | {s['source_class']}"
        strata[h] = {"N": int(s["stratum_N"]), "n": int(s["stratum_sample_n"]), "era": s["era"]}
        d = disp.get(s["id"], {})
        responded = d.get("outcome") in ("filed", "ready_existing")
        status = (d.get("claimed_status") or "").lower()
        y = (1 if status == "yes" else 0 if status == "no" else None) if responded else None
        f = d.get("formal_validity_at_cutoff", "")
        yf = (1 if f == "unrevoked" else 0 if f == "revoked" else None) if responded else None
        op[h].append(y)
        fv[h].append(yf)
        rows.append({"id": s["id"], "stratum": h, "outcome": d.get("outcome", "missing"), "y_operative": y,
                     "y_formal_validity": yf, "first_cause": d.get("first_cause", ""),
                     "formal_revocation_after_earlier_cessation": d.get("formal_revocation_after_earlier_cessation", "")})
    result = {
        "schema": "dorotheus-sample-estimate/v1", "label": "provisional, AI-reviewed, uncertified, n=120",
        "operative_force": {m: estimate(strata, op, m) for m in ("mar", "nonresponse_zero")},
        "formal_validity_unrevoked": {m: estimate(strata, fv, m) for m in ("mar", "nonresponse_zero")},
        "nonresponse_by_stratum": {h: {"n": len(v), "respondents": sum(1 for y in v if y is not None)} for h, v in op.items()},
        "outcomes": dict(sorted(defaultdict(int, {k: sum(1 for r in rows if r["outcome"] == k) for k in {r["outcome"] for r in rows}}).items())),
        "first_cause_among_no": dict(sorted({k: sum(1 for r in rows if r["y_operative"] == 0 and r["first_cause"] == k)
                                             for k in {r["first_cause"] for r in rows if r["y_operative"] == 0}}.items())),
        "formal_revocation_after_earlier_cessation_true_among_no": sum(
            1 for r in rows if r["y_operative"] == 0 and r["formal_revocation_after_earlier_cessation"] == "yes"),
        "rows": rows,
    }
    json.dump(result, open(out_path, "w"), indent=1, default=str)
    m = result["operative_force"]["mar"]
    print(json.dumps({"share": round(m["share"], 4), "kg95": [round(x, 4) for x in m["korn_graubard_95"]],
                      "respondents": m["respondents"]}))


if __name__ == "__main__":
    main(*sys.argv[1:4])
