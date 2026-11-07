"""Offline sanity tests: py -I test_thrower_lib.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from thrower_lib import chi2_sf, chi2_test, classify_edge, iid_from_thrower, is_savings, norm_id, wilson, year_of

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
assert is_savings("To the extent not heretofore rendered inapplicable, the following are hereby revoked: (1) Executive Order No")
assert is_savings("except that, to the extent consistent with this order")
assert is_savings("to the extent that they are inconsistent with this order")
assert not is_savings("Sections 501 and 503") and not is_savings("in part") and not is_savings("with respect to Haiti")
assert year_of("1947-02-24") == 1947 and year_of(float("nan")) is None and year_of(None) is None
# the event-year column must keep a missing year as None (a float NaN compares False both ways)
ser = pd.Series([year_of(x) for x in ["1947-02-24", None, "2001-01-01"]], dtype=object)
assert ser.iloc[1] is None and ser.iloc[0] == 1947
print("ok")
