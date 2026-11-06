"""Summaries of Thrower (2017) eo_original_list.csv that bear on the project's cleanup thesis.

Usage: py -I thrower_summary.py THROWER_CSV OUT_DIR
Writes OUT_DIR/thrower_summary.json. Counts only; no legal status is asserted.
Thrower's `revoke_year` is the year the disposition tables record a revocation, not an operative end date.
"""
import json
import sys
from pathlib import Path

import pandas as pd


def main(csv, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(csv, dtype={"eonumber": str})
    S = {"rows": int(len(t)), "year_min": int(t.year.min()), "year_max": int(t.year.max())}
    S["revoked_n"] = int(t.revoked.sum())
    S["revoked_share"] = float(t.revoked.mean())
    S["never_revoked_share"] = 1 - S["revoked_share"]
    S["ceremonial_n"] = int(t.ceremonial.sum())
    nc = t[t.ceremonial == 0]
    S["non_ceremonial_never_revoked_share"] = float(1 - nc.revoked.mean())
    S["superseded_n"] = int(t.superseded.sum())
    S["partrevoked_n"] = int(t.partrevoked.sum())
    S["revoked_and_superseded_n"] = int(((t.revoked == 1) & (t.superseded == 1)).sum())
    S["superseded_not_revoked_n"] = int(((t.revoked == 0) & (t.superseded == 1)).sum())
    S["substantive_amended_n"] = int(t.substantive_amended.sum())
    rv = t[t.revoked == 1].copy()
    rv["lag"] = rv.revoke_year - rv.year
    S["revoke_year_missing_among_revoked"] = int(rv.revoke_year.isna().sum())
    S["lag_years_quantiles_revoked"] = {str(q): float(rv.lag.quantile(q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}
    S["revoked_lag_ge_10_years_n"] = int((rv.lag >= 10).sum())
    S["revoked_lag_ge_10_years_share_of_revoked"] = float((rv.lag >= 10).mean())
    S["revoked_lag_ge_20_years_n"] = int((rv.lag >= 20).sum())
    S["revoked_lag_ge_20_years_share_of_revoked"] = float((rv.lag >= 20).mean())
    y86 = rv[rv.revoke_year == 1986]
    S["revoked_in_1986_n"] = int(len(y86))
    S["revoked_in_1986_share_of_revoked"] = float(len(y86) / len(rv))
    S["revoked_in_1986_median_lag_years"] = float(y86.lag.median())
    S["revoked_in_1986_lag_ge_20_share"] = float((y86.lag >= 20).mean())
    S["revoked_excluding_1986_n"] = int(len(rv) - len(y86))
    S["revokedbyotherthaneo_n"] = int(t.revokedbyotherthaneo.sum())
    S["revokedbyotherthaneo_among_1986_revoked_n"] = int(y86.revokedbyotherthaneo.sum())
    S["columns"] = list(t.columns)
    (out / "thrower_summary.json").write_text(json.dumps(S, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    print(json.dumps(S, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
