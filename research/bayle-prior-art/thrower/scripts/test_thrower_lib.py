"""Offline sanity tests: py -I test_thrower_lib.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from thrower_lib import chi2_sf, chi2_test, classify_edge, iid_from_thrower, norm_id, wilson

# chi-square survival values from standard tables
assert abs(chi2_sf(3.841, 1) - 0.05) < 1e-3
assert abs(chi2_sf(5.991, 2) - 0.05) < 1e-3
assert abs(chi2_sf(15.507, 8) - 0.05) < 1e-3
# 2x2 with a known statistic: [[10,20],[30,40]] -> chi2 = 0.7937 (no continuity correction)
st, df, p = chi2_test(pd.DataFrame([[10, 20], [30, 40]]))
assert df == 1 and abs(st - 0.7937) < 1e-3, st
lo, hi = wilson(50, 100)
assert 0.40 < lo < 0.41 and 0.59 < hi < 0.60
assert iid_from_thrower("7677-A") == "EO:7677A" and iid_from_thrower("9395-B") == "EO:9395B" and iid_from_thrower("7532") == "EO:7532"
assert norm_id("EO:7933a") == "EO:7933A" and norm_id("PL:94-412") == "PL:94-412"
assert classify_edge("revocation", "") == "revoke_full"
assert classify_edge("revocation", "in part") == "revoke_part"
assert classify_edge("rescission", "Section 3") == "revoke_part"
assert classify_edge("supersession", "") == "supersede_full"
assert classify_edge("termination", "") == "other_end"
assert classify_edge("amendment", "") == "other"
print("ok")
