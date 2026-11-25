"""Stratified month-cluster estimate of presidential orders in ProQuest's signed unnumbered collection (1789-1936)
that the census lacks. Per-month counts of missing executive-order-type records come from SAMPLE_ROWS.psv as
adjudicated in MATCH_REVIEW.txt (see REPORT.md). Run: python3 -I estimate.py"""
import math, statistics as st
ERAS = {  # months in era, missing per sampled month (all order types), missing per month (land orders only)
    "1789-1861": (874, [0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 0.5, 0.5, 0, 0, 2], [0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0]),
    "1862-1906": (540, [0, 5, 0, 0, 1, 0, 2, 0], [0, 1, 0, 0, 1, 0, 1, 0]),
    "1907-1936": (360, [29, 9, 3, 2, 1, 4], [28, 6, 2, 2, 1, 3]),
}
def est(N, x):
    n = len(x); m = st.mean(x); s = st.stdev(x)
    return N * m, (N ** 2) * (1 - n / N) * s * s / n
for label, idx in (("all order types", 1), ("land orders only", 2)):
    tot = var = 0
    for era, row in ERAS.items():
        e, v = est(row[0], row[idx]); tot += e; var += v
        print(f"{label:17} {era}: {e:6.0f} (se {math.sqrt(v):5.0f})")
    se = math.sqrt(var)
    print(f"{label:17} TOTAL {tot:6.0f} (se {se:5.0f}; normal 95% {max(0, tot - 1.96 * se):.0f} to {tot + 1.96 * se:.0f})")
