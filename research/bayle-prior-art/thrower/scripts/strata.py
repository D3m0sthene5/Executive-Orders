"""STRATA: do Thrower's covariates predict which orders the project finds hard or cheap?

usage: py -I strata.py ARCHIVE_DIR PROJECT_CACHE_DIR OUT_DIR

Outcomes come from jobs/readiness-tracker/output/READINESS_BY_ORDER.csv (one row per order). Cross-tabs give
counts and rates; Pearson chi-square p-values and a logistic regression with decade dummies (numpy IRLS) say
whether a covariate matters once the decade is held fixed. "Decided" is the project's own provisional status
and is NOT a random sample, so its predictors partly describe how the project chose what to decide.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from thrower_lib import chi2_test, norm_id, read_csv, read_thrower, wilson

BIN_COVS = ["revoked", "partrevoked", "superseded", "ceremonial", "war", "divdgovt", "fds", "nyt", "public_mention",
            "civilservice", "publicland", "economy", "committee", "civilrights", "intelligence", "nationalsecurity",
            "foreignservice", "militaryoperations", "governmentcontracting", "temporaryandemergencyfunctions"]


def logit(X, y, ridge=1e-6, iters=60):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ b, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        W = p * (1 - p)
        H = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1])
        g = X.T @ (y - p) - ridge * b
        step = np.linalg.solve(H, g)
        b += step
        if np.abs(step).max() < 1e-9:
            break
    cov = np.linalg.inv(H)
    return b, np.sqrt(np.diag(cov))


def main():
    archive, cache, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    t = read_thrower(archive)
    rd = read_csv(cache, "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")
    rd["instrument_id"] = rd["instrument_id"].map(norm_id)
    d = t.merge(rd, on="instrument_id", how="left", suffixes=("", "_rd"))
    assert d["steps_done"].notna().all(), "every Thrower order should be in the readiness table"
    d["decade"] = (d["year"].astype(int) // 10 * 10).astype(str) + "s"
    bl = d["blockers"].fillna("")
    d["o_decided"] = d["provisional_status"].notna().astype(int)
    d["o_ready"] = (d["ready_for_human_review"] == "yes").astype(int)
    d["o_claim"] = (d["claim_present"] == "yes").astype(int)
    d["o_text_done"] = (d["step_original_text"] == "done").astype(int)
    d["o_no_official_source"] = bl.str.contains("NO_OFFICIAL_SOURCE_LOCATED").astype(int)
    d["o_first_end_unproved"] = bl.str.contains("FIRST_END_UNPROVED|FIRST_END_UNRESOLVED|CURRENT_BASIS_UNPROVED").astype(int)
    d["o_contrary_lead"] = bl.str.contains("MACHINE_SEARCH_FOUND_CONTRARY_LEAD|QUARANTINED_RELATIONSHIP_CONFLICT").astype(int)
    d["o_steps_frac"] = d["steps_done"].astype(float) / d["steps_applicable"].astype(float)
    d["o_status_yes_among_decided"] = np.where(d["o_decided"] == 1, (d["provisional_status"] == "yes").astype(float), np.nan)
    d["origin_family"] = d["decision_origin"].fillna("undecided").map(
        lambda s: "undecided" if s == "undecided" else ("jacquard" if s.startswith("jacquard") else ("inherited_legacy_v2" if s.startswith("inherited") else ("opus" if s.startswith("opus") else "other_review"))))
    outcomes = ["o_decided", "o_ready", "o_claim", "o_text_done", "o_no_official_source", "o_first_end_unproved", "o_contrary_lead"]
    summary = {"orders": len(d)}
    for o in outcomes:
        summary[o] = {"n": int(d[o].sum()), "rate": round(float(d[o].mean()), 4)}
    summary["status_yes_among_decided"] = {"yes": int(((d["provisional_status"] == "yes")).sum()), "decided": int(d["o_decided"].sum())}
    summary["mean_steps_done_fraction"] = round(float(d["o_steps_frac"].mean()), 4)

    covs = BIN_COVS + ["decade"]
    rows, tests = [], []
    for c in covs:
        for lvl, g in d.groupby(c):
            r = {"covariate": c, "level": lvl, "n": len(g)}
            for o in outcomes:
                k = int(g[o].sum())
                lo, hi = wilson(k, len(g))
                r[o + "_n"] = k
                r[o + "_rate"] = round(k / len(g), 4)
                r[o + "_ci_lo"] = round(lo, 4)
                r[o + "_ci_hi"] = round(hi, 4)
            dg = g[g["o_decided"] == 1]
            r["ready_among_decided_n"] = int(dg["o_ready"].sum())
            r["ready_among_decided_rate"] = round(float(dg["o_ready"].mean()), 4) if len(dg) else None
            r["decided_status_yes_n"] = int((dg["provisional_status"] == "yes").sum())
            r["decided_status_yes_rate"] = round(float((dg["provisional_status"] == "yes").mean()), 4) if len(dg) else None
            r["mean_steps_done_fraction"] = round(float(g["o_steps_frac"].mean()), 4)
            rows.append(r)
        for o in outcomes:
            stat, df, p = chi2_test(pd.crosstab(d[c], d[o]))
            tests.append({"covariate": c, "outcome": o, "chi2": round(stat, 3), "df": df, "p": p})
    X = pd.DataFrame(rows)
    X.to_csv(os.path.join(out, "STRATA_crosstabs.csv"), index=False, lineterminator="\n")
    T = pd.DataFrame(tests)
    T["p_text"] = T["p"].map(lambda v: "<1e-12" if v < 1e-12 else f"{v:.3g}")
    T.drop(columns=["p"]).to_csv(os.path.join(out, "STRATA_chi2.csv"), index=False, lineterminator="\n")

    # decision origin vs revoked / ceremonial
    ct = d.groupby(["origin_family", "revoked"]).size().unstack(fill_value=0)
    ct.to_csv(os.path.join(out, "STRATA_decision_origin_by_revoked.csv"), lineterminator="\n")

    # adjusted logistic: outcome ~ decade dummies + a compact covariate set
    core = ["revoked", "ceremonial", "war", "divdgovt", "fds", "nyt", "public_mention", "civilservice", "publicland", "economy", "committee",
            "civilrights", "intelligence", "nationalsecurity", "foreignservice", "militaryoperations", "governmentcontracting",
            "temporaryandemergencyfunctions"]
    D = pd.get_dummies(d["decade"], drop_first=True, dtype=float)
    cf = d[core].astype(float)
    miss = cf["temporaryandemergencyfunctions"].isna().astype(float).rename("temporaryandemergencyfunctions_missing")
    cf["temporaryandemergencyfunctions"] = cf["temporaryandemergencyfunctions"].fillna(0.0)
    summary["temporaryandemergencyfunctions_missing_n"] = int(miss.sum())
    summary["temporaryandemergencyfunctions_missing_years"] = sorted(set(d.loc[miss.astype(bool), "year"]))
    Xmat = pd.concat([pd.Series(1.0, index=d.index, name="const"), cf, miss, D], axis=1)
    adj = []
    for o in ["o_decided", "o_ready", "o_text_done", "o_first_end_unproved"]:
        b, se = logit(Xmat.values, d[o].values)
        for name, bi, si in zip(Xmat.columns, b, se):
            if name in core:
                sep = bool(si > 20)  # quasi-separation: no events in one cell
                adj.append({"outcome": o, "covariate": name,
                            "odds_ratio": None if sep else round(float(np.exp(bi)), 3),
                            "ci_lo": None if sep else round(float(np.exp(bi - 1.96 * si)), 3),
                            "ci_hi": None if sep else round(float(np.exp(bi + 1.96 * si)), 3),
                            "z": None if sep else round(float(bi / si), 2),
                            "note": "separation (no events in one cell)" if sep else "",
                            "n_with_flag": int(d[name].eq("1").sum())})
    A = pd.DataFrame(adj)
    A.to_csv(os.path.join(out, "STRATA_adjusted_logit.csv"), index=False, lineterminator="\n")

    # decade pattern (the strongest single stratifier) and revoked within decade
    dec = d.groupby("decade").agg(n=("year", "size"), decided=("o_decided", "mean"), ready=("o_ready", "mean"),
                                   text_done=("o_text_done", "mean"), revoked=("revoked", lambda s: (s == "1").mean())).round(4)
    dec.to_csv(os.path.join(out, "STRATA_by_decade.csv"), lineterminator="\n")
    with open(os.path.join(out, "STRATA_SUMMARY.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
        fh.write("\n")

    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 400)
    print(json.dumps(summary, indent=1))
    print(dec)
    print(X[X["covariate"].isin(["revoked", "ceremonial", "war", "divdgovt", "partrevoked", "superseded", "fds"])][
        ["covariate", "level", "n", "o_decided_rate", "o_ready_rate", "o_text_done_rate", "o_first_end_unproved_rate", "o_contrary_lead_rate", "decided_status_yes_rate"]].to_string())
    print(T.sort_values("p").head(25).drop(columns=["p"]).to_string())
    print(A.to_string())
    print(ct)


if __name__ == "__main__":
    main()
