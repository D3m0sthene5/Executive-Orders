"""COVERAGE: orders in Thrower (1937-2013) missing from the project register, and register orders in that
number range missing from Thrower; also the OFR catalog's view and year disagreements.

usage: py -I coverage.py ARCHIVE_DIR PROJECT_CACHE_DIR OUT_DIR
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from thrower_lib import NUM_MAX, NUM_MIN, base_number, norm_id, read_csv, read_thrower


def main():
    archive, cache, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    t = read_thrower(archive)
    reg = read_csv(cache, "jobs/domesday-register/output/REGISTER.csv")
    reg["raw_id"] = reg["instrument_id"]
    reg["iid"] = reg["instrument_id"].map(norm_id)
    reg["base"] = reg["iid"].map(base_number)
    rr = reg[reg["base"].between(NUM_MIN, NUM_MAX)].copy()
    cat = read_csv(cache, "jobs/later-events/output/CATALOG_INDEX.csv")
    cat["iid"] = cat["id"].map(norm_id)

    tset, rset, cset = set(t["instrument_id"]), set(rr["iid"]), set(cat["iid"])
    t["suffix"] = t["eonumber"].str.extract(r"-([A-Za-z])$")[0].fillna("")
    t["base_number"] = t["eonumber"].str.extract(r"^(\d+)")[0].astype(int)
    res = {"thrower_rows": len(t)}
    res["thrower_plain_numbers"] = int((t["suffix"] == "").sum())
    res["thrower_lettered_suffix_rows"] = int((t["suffix"] != "").sum())
    nums = sorted(t.loc[t["suffix"] == "", "base_number"])
    res["thrower_number_range"] = [min(nums), max(nums)]
    res["thrower_gaps_inside_range"] = [n for n in range(min(nums), max(nums) + 1) if n not in set(nums)]
    res["register_rows_in_number_range_7532_13655"] = len(rr)
    res["register_ids_differing_only_by_case_from_thrower"] = sorted(
        x for x in rr["raw_id"] if x != norm_id(x) and norm_id(x) in tset)

    # ---- Thrower rows missing from the register (after upper-casing the suffix) ----
    miss_reg = t[~t["instrument_id"].isin(rset)]
    rows = []
    for _, r in miss_reg.iterrows():
        rows.append({"instrument_id": r["instrument_id"], "eonumber": r["eonumber"], "year": r["year"],
                     "in_ofr_catalog": r["instrument_id"] in cset,
                     "why": "lettered suffix absent from register" if r["suffix"] else "number absent from register"})
    pd.DataFrame(rows, columns=["instrument_id", "eonumber", "year", "in_ofr_catalog", "why"]).to_csv(
        os.path.join(out, "COVERAGE_thrower_not_in_register.csv"), index=False, lineterminator="\n")
    res["thrower_not_in_register"] = len(rows)

    # ---- register rows in range missing from Thrower ----
    extra = rr[~rr["iid"].isin(tset)]
    rows = []
    for _, r in extra.iterrows():
        base = r["base"]
        suffix = r["iid"][len("EO:" + str(base)):]
        twin = rr[(rr["base"] == base) & (rr["iid"] != r["iid"])]
        twin_info = ""
        why = ""
        if len(twin):
            tw = twin.iloc[0]
            same_date = (tw["date"] == r["date"]) and isinstance(r["date"], str)
            t1 = str(tw["title"]).split("-", 1)[-1][-60:]
            twin_info = f"{tw['iid']} date={tw['date']} title={str(tw['title'])[:70]}"
            if not isinstance(r["date"], str) and not isinstance(r["title"], str):
                why = ("lettered suffix with no date, title or text in the register and no OFR catalog entry; "
                       "only the register's own row names it; probably a phantom identity (register-side lead)")
            elif same_date and str(r["title"]).lower().find(str(tw["title"])[:30].lower()) >= 0:
                why = ("same date and same title as the unsuffixed twin; the APP index heading 'Executive Order N-A' "
                       "probably re-lists the same order (duplicate in register)")
            else:
                why = "lettered suffix in register, absent from Thrower; different title from twin"
        rows.append({"register_id": r["raw_id"], "normalized_id": r["iid"], "date": r["date"], "date_source": r["date_source"],
                     "title": r["title"], "census_class": r["census_class"], "text_files": r["text_files"],
                     "twin_in_register": twin_info, "in_ofr_catalog": r["iid"] in cset, "why": why})
    pd.DataFrame(rows).to_csv(os.path.join(out, "COVERAGE_register_not_in_thrower.csv"), index=False, lineterminator="\n")
    res["register_not_in_thrower"] = len(rows)

    # ---- OFR catalog view ----
    cr = cat[cat["id"].map(base_number).between(NUM_MIN, NUM_MAX)]
    res["ofr_catalog_rows_in_range"] = len(cr)
    res["thrower_not_in_ofr_catalog"] = sorted(tset - cset)
    res["ofr_catalog_not_in_thrower"] = sorted(set(cr["iid"]) - tset)
    res["catalog_labels_with_lowercase_suffix"] = sorted(cr.loc[cr["executive_order_number_raw"].str.contains(r"[a-z]$", na=False), "executive_order_number_raw"])

    # ---- year disagreements ----
    m = t.merge(rr[["iid", "date", "date_source", "title"]].rename(columns={"iid": "instrument_id"}), on="instrument_id", how="left")
    m["register_year"] = m["date"].str[:4]
    bad = m[m["register_year"].notna() & (m["register_year"] != m["year"])].copy()
    bad["thrower_year"] = bad["year"].astype(int)
    bad["register_year"] = bad["register_year"].astype(int)
    bad["register_month"] = bad["date"].str[5:7]
    bad["pattern"] = "other"
    # Thrower year earlier than the signing year, signing in January: the end-of-term pattern
    bad.loc[(bad["register_year"] == bad["thrower_year"] + 1) & (bad["register_month"] == "01"), "pattern"] = "signed_January_coded_previous_year"
    bad.loc[(bad["register_year"] == bad["thrower_year"] + 1) & (bad["register_month"] != "01"), "pattern"] = "thrower_year_one_earlier_not_January"
    bad.loc[bad["register_year"] < bad["thrower_year"], "pattern"] = "thrower_year_later_than_register"
    bad[["instrument_id", "eonumber", "thrower_year", "date", "date_source", "register_year", "pattern", "title"]].to_csv(
        os.path.join(out, "COVERAGE_year_differs.csv"), index=False, lineterminator="\n")
    res["thrower_year_differs_from_register_date_year"] = len(bad)
    res["year_differs_patterns"] = bad["pattern"].value_counts().to_dict()
    res["register_rows_without_date_in_range"] = int(rr["date"].isna().sum())
    with open(os.path.join(out, "COVERAGE_SUMMARY.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(res, indent=1, sort_keys=True))


main()
