"""Test whether the rows of Lowande & Poznansky's orders.Rda can be aligned to executive-order numbers.

Usage: py -I lp_alignment.py ORDERS_RDA THROWER_CSV REGISTER_CSV OUT_DIR [--perms N]

Inputs (all treated as untrusted data):
  ORDERS_RDA    L&P replication data (1 data frame `dt`, no EO number, rows ordered by year descending).
  THROWER_CSV   Thrower (2017) eo_original_list.csv (eonumber, year, ceremonial, revoked, revoke_year, ...).
  REGISTER_CSV  the project's master register (jobs/domesday-register/output/REGISTER.csv on origin/main).

Hypotheses, all labelled hypotheses, never facts:
  CAL    L&P `year` is the calendar year of signing, so L&P year counts should equal register year counts.
  DESC   within a year, L&P rows run in descending EO-number order.
  ASC    within a year, L&P rows run in ascending EO-number order.
Signals taken from Thrower (not independent of L&P: its ceremonial values look carried over from Thrower, so
agreement tests row order, not the accuracy of either file), and joined to the register by EO number (and suffix):
  ceremonial     L&P ceremonial vs Thrower ceremonial
  revoked_next   L&P revoked_next_term vs "Thrower revoke_year is by the last year of the following
                 four-year block" (blocks 1937-40, 1941-44, ...; inferred, see README.md)
Writes year_counts.csv, term_definition_check.csv, alignment_by_year.csv, alignment_summary.json and
aligned_orders.csv (only years whose ASC agreement is strong).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

SEED = 20261106
# Article p. 351 says January 18, 2021; SI-2 says the first half of 2021; the data hold 64 rows for 2021
# (register: 11 orders by Jan 18, 65 by Jun 30). The data agree with the SI.
CUTOFF = "2021-06-30"
BLOCK0 = 1937  # four-year blocks 1937-40, 1941-44, ... (inferred from L&P's opposing_next / next_term_divgov by year)
LAST_REVOKE_YEAR_HELD = 2013  # Thrower's data end


def key_of(number, suffix):
    suffix = "" if (suffix is None or (isinstance(suffix, float) and np.isnan(suffix))) else str(suffix).strip().upper()
    return f"{int(float(number))}{('-' + suffix) if suffix else ''}"


def thrower_key(s):
    m = re.fullmatch(r"\s*(\d+)(?:[-\s]*([A-Za-z]+))?\s*", str(s))
    if not m:
        return None
    return f"{int(m.group(1))}{('-' + m.group(2).upper()) if m.group(2) else ''}"


def load(rda, thr, reg):
    dt = pyreadr.read_r(rda)["dt"].reset_index(drop=True)
    dt["row"] = np.arange(1, len(dt) + 1)
    dt["year"] = dt.year.astype(int)
    t = pd.read_csv(thr, dtype={"eonumber": str})
    t["key"] = t.eonumber.map(thrower_key)
    r = pd.read_csv(reg, dtype=str, encoding="utf-8")
    r = r[r.date.notna() & r.number.notna()].copy()
    r["suffix"] = r.suffix.where(r.suffix.str.fullmatch(r"[A-Za-z]+", na=False))
    r["key"] = [key_of(n, s) for n, s in zip(r.number, r.suffix)]
    r["num"] = r.number.astype(float).astype(int)
    r["sfx"] = r.suffix.fillna("")
    r["year"] = r.date.str[:4].astype(int)
    r = r[(r.num >= 7532) & (r.date >= "1937-01-01") & (r.date <= CUTOFF)].copy()
    # Known register defects (coordinator check, 2026-11-07): EO:7700A duplicates EO:7700 (Thrower has only 7700);
    # EO:10276 carries a date typo (1961-07-31) and belongs to 1951 (Thrower year 1951; neighbours 10275, 10277 are 1951).
    r = r[r.key != "7700-A"].copy()
    r.loc[r.key == "10276", "year"] = 1951
    return dt, t, r


def block_of(y):
    return (int(y) - BLOCK0) // 4


def thrower_revoked_next(cal_year, revoke_year, variant):
    """Revocation by the end of the following four-year block (the L&P rule, inferred).
       variant 'A': revoke_year <= last year of the following block (revocations inside the issuing block count)
       variant 'B': revoke_year inside the following block only
       NaN where the end of the following block is after Thrower's data end (2013)."""
    out = []
    for y, ry in zip(cal_year, revoke_year):
        b = block_of(y)
        start1 = BLOCK0 + 4 * (b + 1)
        end1 = start1 + 3
        if end1 > LAST_REVOKE_YEAR_HELD:
            out.append(np.nan)
        elif np.isnan(ry):
            out.append(0.0)
        elif variant == "A":
            out.append(1.0 if ry <= end1 else 0.0)
        else:
            out.append(1.0 if start1 <= ry <= end1 else 0.0)
    return np.array(out)


def agree_score(l_cer, l_rev, t_cer, t_rev):
    """Number of rows on which L&P ceremonial equals Thrower ceremonial and, where Thrower's
    revoked-next-term is defined, L&P revoked_next_term equals it."""
    ok = l_cer == t_cer
    d = ~np.isnan(t_rev)
    ok = ok & np.where(d, l_rev == t_rev, True)
    return int(ok.sum())


def main(rda, thr, reg, out, perms=2000):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    dt, t, r = load(rda, thr, reg)
    rng = np.random.default_rng(SEED)
    t = t.merge(r[["key", "year"]].rename(columns={"year": "cal_year"}), on="key", how="left")
    assert t.cal_year.notna().all(), "Thrower orders missing from the register"

    # 1. year counts
    lp_n = dt.groupby("year").size()
    th_n = t.groupby("year").size()
    rg_n = r.groupby("year").size()
    yc = pd.DataFrame({"lp_rows": lp_n, "thrower_rows": th_n, "register_rows": rg_n})
    yc = yc.loc[(yc.index >= 1937) & (yc.index <= 2021)]
    yc["lp_minus_register"] = yc.lp_rows - yc.register_rows
    yc["lp_minus_thrower"] = yc.lp_rows - yc.thrower_rows
    yc.index.name = "year"
    yc.to_csv(out / "year_counts.csv", lineterminator="\n")

    # 2. term-definition check on year shares, independent of any row alignment
    chk = []
    s_lp = dt.groupby("year").revoked_next_term.mean()
    for variant in ("A", "B"):
        rn = thrower_revoked_next(t.cal_year, t.revoke_year, variant)
        tj = t.assign(rev_next=rn).dropna(subset=["rev_next"])
        s_th = tj.groupby("cal_year").rev_next.mean()
        j = pd.concat([s_th.rename("thrower_share"), s_lp.rename("lp_share")], axis=1).dropna()
        for y, row in j.iterrows():
            chk.append({"variant": variant, "year": int(y), "thrower_share": row.thrower_share, "lp_share": row.lp_share})
    chk = pd.DataFrame(chk)
    chk.to_csv(out / "term_definition_check.csv", index=False, float_format="%.4f", lineterminator="\n")
    defs = {}
    for v, g in chk.groupby("variant"):
        defs[v] = {"years": int(len(g)), "pearson_r": float(np.corrcoef(g.thrower_share, g.lp_share)[0, 1]),
                   "mean_abs_diff_pp": float(100 * (g.thrower_share - g.lp_share).abs().mean())}
    best_variant = max(defs, key=lambda v: defs[v]["pearson_r"])

    # 3. within-year alignment test
    t_rev = t.copy()
    t_rev["rev_next"] = thrower_revoked_next(t_rev.cal_year, t_rev.revoke_year, best_variant)
    tinfo = t_rev.drop_duplicates("key").set_index("key")[["ceremonial", "rev_next"]]
    rows = []
    aligned = []
    summ = {"perms": perms, "seed": SEED, "term_blocks": "four-year blocks 1937-40, 1941-44, ...",
            "best_term_variant": best_variant, "term_variant_check": defs}
    for y in range(1937, 2021):
        L = dt[dt.year == y]
        R = r[r.year == y].sort_values(["num", "sfx"])
        n_l, n_r = len(L), len(R)
        rec = {"year": y, "lp_rows": n_l, "register_rows": n_r, "count_match": n_l == n_r}
        if n_l != n_r:
            rec["status"] = "count_mismatch_not_tested"
            rows.append(rec)
            continue
        Rk = R.key.tolist()
        has = [k in tinfo.index for k in Rk]
        rec["thrower_joined"] = int(sum(has))
        if y > LAST_REVOKE_YEAR_HELD:
            rec["status"] = "after_thrower_data_not_tested"
            rows.append(rec)
            continue
        if sum(has) < n_r:
            rec["status"] = "thrower_missing_for_some_orders_not_tested"
            rows.append(rec)
            continue
        ti = tinfo.loc[Rk]
        t_cer_asc = ti.ceremonial.to_numpy(float)
        t_rev_asc = ti.rev_next.to_numpy(float)
        l_cer = L.ceremonial.to_numpy(float)
        l_rev = L.revoked_next_term.to_numpy(float)
        rec.update({"thrower_ceremonial": int(t_cer_asc.sum()), "lp_ceremonial": int(l_cer.sum()),
                    "thrower_revoked_next_defined": int((~np.isnan(t_rev_asc)).sum()),
                    "thrower_revoked_next_pos": int(np.nansum(t_rev_asc)), "lp_revoked_next_pos": int(l_rev.sum())})
        sc = {}
        for name, tc, tr in (("DESC", t_cer_asc[::-1], t_rev_asc[::-1]), ("ASC", t_cer_asc, t_rev_asc)):
            sc[name] = agree_score(l_cer, l_rev, tc, tr)
        null = np.empty(perms)
        for i in range(perms):
            p = rng.permutation(n_l)
            null[i] = agree_score(l_cer[p], l_rev[p], t_cer_asc, t_rev_asc)
        for name in ("DESC", "ASC"):
            rec[f"score_{name}"] = sc[name]
            rec[f"p_{name}"] = float((1 + (null >= sc[name]).sum()) / (1 + perms))
            rec[f"excess_{name}"] = float((sc[name] - null.mean()) / (n_l - null.mean())) if n_l > null.mean() else np.nan
        rec["null_mean"] = float(null.mean())
        rec["null_p95"] = float(np.quantile(null, 0.95))
        defined = int((~np.isnan(t_rev_asc)).sum())
        rec["informative"] = bool(defined > 0 and (int(t_cer_asc.sum()) + int(np.nansum(t_rev_asc))) >= 3)
        rec["status"] = "tested"
        if not rec["informative"]:
            cls = "UNTESTABLE_too_few_positives"
        elif sc["ASC"] == n_l and rec["p_ASC"] <= 0.01:
            cls = "STRONG_exact"
        elif rec["p_ASC"] <= 0.01 and rec["excess_ASC"] >= 0.5:
            cls = "PARTIAL"
        elif rec["p_ASC"] <= 0.05:
            cls = "WEAK"
        else:
            cls = "NONE"
        rec["asc_class"] = cls
        rec["signal_positives"] = int(t_cer_asc.sum()) + int(np.nansum(t_rev_asc))
        rows.append(rec)
        if cls in ("STRONG_exact", "PARTIAL"):
            # ASC hypothesis: L&P row k within the year <-> k-th smallest EO number of that year
            Rs = R.reset_index(drop=True)
            agree = (l_cer == t_cer_asc) & np.where(np.isnan(t_rev_asc), True, l_rev == t_rev_asc)
            has_pos = (l_cer == 1) | (t_cer_asc == 1) | (l_rev == 1) | (t_rev_asc == 1)
            for k in range(n_l):
                aligned.append({
                    "lp_row": int(L.row.iloc[k]), "year": y, "eo_key": Rs.key[k], "eo_number": int(Rs.num[k]),
                    "eo_suffix": Rs.sfx[k], "eo_date": Rs.date[k],
                    "year_alignment_class": cls, "year_p_ASC": rec["p_ASC"], "year_excess_ASC": round(rec["excess_ASC"], 4),
                    "row_signals_agree": bool(agree[k]),
                    "row_has_positive_signal": bool(has_pos[k]),
                    "lp_ceremonial": int(l_cer[k]), "thrower_ceremonial": int(t_cer_asc[k]),
                    "lp_revoked_next_term": int(l_rev[k]),
                    "thrower_revoked_next_term_derived": ("" if np.isnan(t_rev_asc[k]) else int(t_rev_asc[k])),
                    "lp_immutable": int(L.immutable.iloc[k]), "lp_foreign": int(L.foreign.iloc[k]),
                    "year_null_mean_agreements": round(rec["null_mean"], 2),
                    "hypothesis": "L&P rows within a year run in ascending EO-number order (ASC); a labelled hypothesis, not a fact",
                })
    res = pd.DataFrame(rows)
    res.to_csv(out / "alignment_by_year.csv", index=False, float_format="%.4f", lineterminator="\n")
    tested = res[res.status == "tested"]
    inf = tested[tested.informative == True]  # noqa: E712
    summ["years_total_1937_2020"] = int(len(res))
    summ["asc_class_counts"] = {k: int(v) for k, v in tested.asc_class.value_counts().items()}
    summ["years_equal_ceremonial_counts"] = int((tested.thrower_ceremonial == tested.lp_ceremonial).sum())
    if aligned:
        al = pd.DataFrame(aligned)
        al.to_csv(out / "aligned_orders.csv", index=False, lineterminator="\n")
        summ["aligned_rows"] = int(len(al))
        summ["aligned_rows_signals_agree"] = int(al.row_signals_agree.sum())
        summ["aligned_years"] = int(al.year.nunique())
        pos = al[al.row_has_positive_signal]
        summ["aligned_rows_with_positive_signal"] = int(len(pos))
        summ["aligned_rows_with_positive_signal_agree"] = int(pos.row_signals_agree.sum())
        summ["aligned_rows_expected_agreements_by_chance"] = float(al.groupby("year").year_null_mean_agreements.first().sum())
    summ["years_count_match"] = int(res.count_match.sum())
    summ["years_tested"] = int(len(tested))
    summ["years_informative"] = int(len(inf))
    for name in ("DESC", "ASC"):
        summ[f"informative_years_p_below_0.05_{name}"] = int((inf[f"p_{name}"] < 0.05).sum())
        summ[f"tested_years_p_below_0.05_{name}"] = int((tested[f"p_{name}"] < 0.05).sum())
        summ[f"median_p_informative_{name}"] = float(inf[f"p_{name}"].median()) if len(inf) else None
        summ[f"mean_excess_informative_{name}"] = float(inf[f"excess_{name}"].mean()) if len(inf) else None
    (out / "alignment_summary.json").write_text(json.dumps(summ, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    print(json.dumps(summ, indent=1, sort_keys=True))
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 500)
    print(res.drop(columns=["status"]).to_string())


if __name__ == "__main__":
    a = sys.argv[1:]
    perms = 2000
    if "--perms" in a:
        i = a.index("--perms")
        perms = int(a[i + 1])
        a = a[:i] + a[i + 2:]
    main(a[0], a[1], a[2], a[3], perms)
