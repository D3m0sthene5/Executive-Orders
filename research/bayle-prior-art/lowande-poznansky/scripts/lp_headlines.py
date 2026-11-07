"""Recompute Lowande & Poznansky (2024) headline numbers from orders.Rda.

Usage: py -I lp_headlines.py ORDERS_RDA OUT_DIR
Needs pandas, numpy, pyreadr. Writes OUT_DIR/headlines.json.
The Rda is untrusted data: it is only parsed, never executed.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr


def irls_logit(X, y, iters=50):
    """Plain IRLS logistic regression (matches R glm binomial/logit)."""
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = X @ b
        p = 1 / (1 + np.exp(-eta))
        w = p * (1 - p)
        z = eta + (y - p) / w
        XtW = X.T * w
        b_new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(b_new - b)) < 1e-10:
            b = b_new
            break
        b = b_new
    p = 1 / (1 + np.exp(-(X @ b)))
    cov = np.linalg.inv((X.T * (p * (1 - p))) @ X)
    ll = float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))
    return b, np.sqrt(np.diag(cov)), ll


COLS = ["foreign", "war", "election", "inflation", "admchg", "endterm", "trend37",
        "issuing_divgov", "opposing_next", "next_term_divgov", "immutable"]


def design(d, imm_override=None):
    d = d.copy()
    if imm_override is not None:
        d["immutable"] = imm_override
    X = d[COLS].astype(float).copy()
    a, b, c, i = (d["issuing_divgov"], d["opposing_next"], d["next_term_divgov"], d["immutable"])
    X["issuing_divgov:opposing_next"] = a * b
    X["issuing_divgov:next_term_divgov"] = a * c
    X["opposing_next:next_term_divgov"] = b * c
    X["issuing_divgov:immutable"] = a * i
    X["opposing_next:immutable"] = b * i
    X["next_term_divgov:immutable"] = c * i
    X["issuing_divgov:opposing_next:next_term_divgov"] = a * b * c
    X["issuing_divgov:opposing_next:immutable"] = a * b * i
    X["issuing_divgov:next_term_divgov:immutable"] = a * c * i
    X["opposing_next:next_term_divgov:immutable"] = b * c * i
    X["issuing_divgov:opposing_next:next_term_divgov:immutable"] = a * b * c * i
    X.insert(0, "const", 1.0)
    return X


def main(rda, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    dt = pyreadr.read_r(rda)["dt"]
    H = {}
    H["rows"] = int(len(dt))
    H["year_min"], H["year_max"] = int(dt.year.min()), int(dt.year.max())
    H["ceremonial_n"] = int(dt.ceremonial.sum())
    H["ceremonial_share"] = float(dt.ceremonial.mean())
    nc = dt[dt.ceremonial == 0]
    H["non_ceremonial_n"] = int(len(nc))
    H["revoked_next_term_mean_all_rows"] = float(dt.revoked_next_term.mean())
    H["revoked_next_term_mean_non_ceremonial"] = float(nc.revoked_next_term.mean())
    H["revoked_next_term_n_all"] = int(dt.revoked_next_term.sum())
    H["revoked_next_term_n_non_ceremonial"] = int(nc.revoked_next_term.sum())
    H["not_revoked_next_term_share_non_ceremonial"] = 1 - H["revoked_next_term_mean_non_ceremonial"]
    H["immutable_share_all_rows"] = float(dt.immutable.mean())
    H["immutable_share_non_ceremonial"] = float(nc.immutable.mean())
    for name, d in (("all", dt), ("non_ceremonial", nc)):
        g = d.groupby("immutable").revoked_next_term.agg(["mean", "size"])
        H[f"revoked_next_term_by_immutable_{name}"] = {str(int(k)): {"mean": float(v["mean"]), "n": int(v["size"])} for k, v in g.iterrows()}
        g = d.groupby("issuing_divgov").immutable.agg(["mean", "size"])
        H[f"immutable_share_by_issuing_divgov_{name}"] = {str(int(k)): {"mean": float(v["mean"]), "n": int(v["size"])} for k, v in g.iterrows()}
    H["immutable_share_diff_divgov_minus_unified_all_rows_pp"] = 100 * float(
        dt[dt.issuing_divgov == 1].immutable.mean() - dt[dt.issuing_divgov == 0].immutable.mean())
    H["opposing_next_missing_rows"] = int(dt.opposing_next.isna().sum())
    H["missing_rows_years"] = sorted(int(y) for y in dt[dt.opposing_next.isna()].year.unique())
    dt = dt.assign(era=pd.cut(dt.year, [1936, 1952, 1980, 2021], labels=["1937-1952", "1953-1980", "1981-2021"]))
    H["immutable_share_by_era_all_rows"] = {k: float(v) for k, v in dt.groupby("era", observed=True).immutable.mean().items()}
    H["immutable_share_1981_2021_all_rows"] = float(dt[dt.year >= 1981].immutable.mean())

    # Table C.1 column 1 (main: non-ceremonial) and column 3 (including ceremonial) replication
    models = {}
    beta = None
    for label, d in (("main_non_ceremonial", nc), ("including_ceremonial", dt)):
        dd = d.dropna(subset=COLS)
        X = design(dd)
        y = dd.revoked_next_term.to_numpy(float)
        b, se, ll = irls_logit(X.to_numpy(float), y)
        k = X.shape[1]
        models[label] = {"n": int(len(dd)), "aic": -2 * ll + 2 * k,
                         "coef": dict(zip(X.columns, map(float, b))), "se": dict(zip(X.columns, map(float, se)))}
        if label == "main_non_ceremonial":
            beta = b
    H["table_C1_replication"] = models

    # Figure 1, H1: point-estimate marginal effect of immutable 0->1, observed-case, rows as in figures.R
    # (figures.R builds `zero`/`one` from ALL complete-case rows of dt, including ceremonial ones).
    dd = dt.dropna(subset=COLS)
    p0 = 1 / (1 + np.exp(-(design(dd, 0.0).to_numpy(float) @ beta)))
    p1 = 1 / (1 + np.exp(-(design(dd, 1.0).to_numpy(float) @ beta)))
    H["h1_marginal_effect_immutable_pp"] = 100 * float(np.mean(p1 - p0))
    H["h1_marginal_effect_n_rows"] = int(len(dd))

    (out / "headlines.json").write_text(json.dumps(H, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in H.items() if k != "table_C1_replication"}, indent=1, sort_keys=True))
    for label, m in models.items():
        print(label, "n", m["n"], "AIC", round(m["aic"], 3))
        for k in m["coef"]:
            print("  %-60s %8.3f (%.3f)" % (k, m["coef"][k], m["se"][k]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
