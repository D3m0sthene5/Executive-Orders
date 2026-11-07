"""Derive thrower_orders.csv from the CC0 replication deposit and write MANIFEST.json.

usage: py -I build_thrower_table.py ARCHIVE_DIR OUT_DIR

ARCHIVE_DIR is the unpacked Harvard Dataverse ZIP (doi:10.7910/DVN/LZGQOH). Only eo_original_list.csv is
used for the table. Columns are kept exactly as deposited, with three added in front: instrument_id (the
project's id form, 7677-A -> EO:7677A), base_number and suffix. Values are not recoded.
Also cross-checks the order-year file's flags against the order-level file (a deposit self-check).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import pyreadstat
from thrower_lib import read_thrower, sha256_file

ZIP_SHA256 = "c641a12e2dbf8e827999cbb531dabbe7fcc402f20488c93da4847a95eda3f9a2"


def main():
    archive, out = sys.argv[1:3]
    os.makedirs(out, exist_ok=True)
    d = read_thrower(archive)
    d["base_number"] = d["eonumber"].str.extract(r"^(\d+)")[0].astype(int)
    d["suffix"] = d["eonumber"].str.extract(r"-([A-Za-z])$")[0].fillna("")
    cols = ["instrument_id", "base_number", "suffix"] + [c for c in d.columns if c not in ("instrument_id", "base_number", "suffix")]
    d = d[cols]
    # the order-year main .dta (not the CSV) carries revokedbyeo12553; the CSV's revokedbyotherthaneo is a different flag
    df, meta = pyreadstat.read_dta(os.path.join(archive, "thrower_ajps_replication_main.dta"),
                                   usecols=["id", "revoked", "year", "revokedbyeo12553"])
    df = df.dropna(subset=["id"])  # the .dta ends with blank rows
    first = df.drop_duplicates("id").assign(id=lambda x: x["id"].astype(int).astype(str))
    d = d.merge(first[["id", "revokedbyeo12553"]].assign(revokedbyeo12553=lambda x: x["revokedbyeo12553"].astype(int).astype(str)),
                on="id", how="left")
    assert d["revokedbyeo12553"].notna().all()
    cols = [c for c in d.columns if c != "revokedbyeo12553"] + ["revokedbyeo12553"]
    d = d[cols]
    path = os.path.join(out, "thrower_orders.csv")
    d.to_csv(path, index=False, lineterminator="\n", encoding="utf-8")
    size = os.path.getsize(path)
    assert size < 2 * 1024 * 1024, size

    # deposit self-check: the order-year main file should reproduce the order-level flags
    check = {}
    check["main_dta_rows_with_id"] = int(len(df))
    check["main_dta_orders"] = int(first["id"].nunique())
    m = first.merge(d[["id", "revoked", "revokedbyotherthaneo"]], on="id", suffixes=("_dta", "_csv"))
    check["order_level_rows_matched"] = int(len(m))
    check["revoked_flag_mismatch_dta_vs_csv"] = int((m["revoked_dta"].astype(int) != m["revoked_csv"].astype(int)).sum())
    ct = pd.crosstab(d["revokedbyeo12553"], d["revokedbyotherthaneo"])
    check["crosstab_revokedbyeo12553_by_revokedbyotherthaneo"] = {str(i): {str(j): int(ct.loc[i, j]) for j in ct.columns} for i in ct.index}
    check["note"] = ("revokedbyeo12553 (372 orders, from the main .dta, added here as the last column) and the CSV's "
                     "revokedbyotherthaneo (140 orders) are different flags that never overlap.")

    src = []
    for f in sorted(os.listdir(archive)):
        p = os.path.join(archive, f)
        if os.path.isfile(p):
            src.append({"file": f, "bytes": os.path.getsize(p), "sha256": sha256_file(p)})
    man = {
        "dataset": {
            "citation": 'Thrower, Sharece, 2016, "Replication Data for: To Revoke or Not Revoke? The Political Determinants of Executive Order Longevity", https://doi.org/10.7910/DVN/LZGQOH, Harvard Dataverse, V1 (API reports version 1.1, released 2018-12-11), UNF:6:HoWUG8bvlsiqOgxKJ59NUg== [fileUNF]',
            "license": "CC0 (Harvard Dataverse terms: made available under a Creative Commons CC0 license)",
            "zip_sha256_as_downloaded": ZIP_SHA256,
            "zip_bytes": 8080973,
        },
        "article": 'Sharece Thrower, "To Revoke or Not Revoke? The Political Determinants of Executive Order Longevity," American Journal of Political Science 61, no. 3 (2017): 642-656, https://doi.org/10.1111/ajps.12294',
        "source_files": src,
        "derived": {"thrower_orders.csv": {"sha256": sha256_file(path), "bytes": size, "rows": int(len(d)),
                                           "built_from": "eo_original_list.csv",
                                           "added_columns": ["instrument_id", "base_number", "suffix", "revokedbyeo12553 (from thrower_ajps_replication_main.dta)"]}},
        "deposit_self_check": check,
    }
    with open(os.path.join(out, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(len(d), "rows", size, "bytes", json.dumps(check))


main()
