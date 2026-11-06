"""INHERITED ERRORS: does the project's revocation data derive from the same National Archives / Office of the
Federal Register disposition tables Thrower used, and where do the two agree against a held primary source?

usage: py -I inherited.py ARCHIVE_DIR PROJECT_CACHE_DIR OUT_DIR

Tests (all counts come from the files, nothing is typed in):
  1  lineage: peano lemmas and status-history events are views of later-events edges (edge-id join).
  2  fingerprint: where the 1989 table (an editorial compilation) and the OFR notes disagree, which one does Thrower follow?
  3  dates: where an OFR note's stated date differs in year from the catalog signing date, which year did Thrower use?
  4  flags: Thrower and the OFR notes agree, but a held official text or the 1989 Codification disagrees; and
     omissions shared by Thrower and the OFR notes that a held official text contradicts.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from crosscheck import C89_PATH, EDGES_PATH, REV, build_events, split_window, tfact
from thrower_lib import load_c89, load_edges, load_peano, load_sh_events, read_csv, read_thrower, year_of

PRIMARY_TYPES = {"order_text_fr_originals", "order_text_govinfo_pdf", "order_text_opus_official_copy"}


def main():
    archive, cache, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    t = read_thrower(archive)
    derived = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "thrower_orders.csv"), dtype=str)
    t = t.merge(derived[["instrument_id", "revokedbyeo12553"]], on="instrument_id", how="left").fillna({"revoke_year": "", "supersede_year": ""})
    tix = t.set_index("instrument_id")
    e = load_edges(cache)
    c89 = load_c89(cache)
    cat = read_csv(cache, "jobs/later-events/output/CATALOG_INDEX.csv")
    ev, _ = build_events(t, e, c89, cat)
    S = {}

    # ---- 1 lineage ----
    ids = set(e["edge_id"])
    peano = load_peano(cache)
    inst = peano.drop_duplicates("lemma_id")
    S["lineage_peano"] = {"instance_lemmas": int(len(inst)),
                          "origin_from_later_events": int((inst["origin_from"] == "later-events").sum()),
                          "origin_edge_id_found_in_EDGES_csv": int(inst["edge_id"].isin(ids).sum()),
                          "other_origins": inst.loc[inst["origin_from"] != "later-events", "origin_from"].value_counts().to_dict()}
    sh = load_sh_events(cache)
    S["lineage_status_history"] = {"events": int(len(sh)),
                                   "input_path_EDGES_csv": int((sh["input_path"] == EDGES_PATH).sum()),
                                   "edge_id_found_in_EDGES_csv": int(sh["edge_id"].isin(ids).sum())}
    S["lineage_later_events_evidence_types"] = e["evidence_type"].value_counts().to_dict()
    ofr_rev_edges = e[e["klass"].isin(REV) & e["evidence_type"].str.startswith("ofr_note")]
    S["later_events_revocation_edges"] = {"total": int(e["klass"].isin(REV).sum()), "from_ofr_notes": int(len(ofr_rev_edges)),
                                          "from_order_texts": int((e["klass"].isin(REV) & e["source_group"].eq("order_text")).sum())}
    # does the 1989 table agree with the OFR notes? (both OFR editorial lineage)
    rv = c89[c89["category"] == "revoked"]
    S["c89_revoked_rows_vs_later_events"] = rv["later_events_check"].fillna("blank").str.replace(r"DIFFERENT_acting_order:.*", "DIFFERENT_acting_order", regex=True).value_counts().to_dict()

    # ---- 2 fingerprint: 1989 table vs OFR notes, who does Thrower follow? ----
    rows = []
    for iid, r in tix.iterrows():
        evs = ev.get(iid, [])
        inw, _ = split_window(evs)
        c89_rows = [x for x in inw if x.src == "C89"]
        if not c89_rows:
            continue
        ofr_full = [x for x in inw if x.src == "LE" and x.evtype.startswith("ofr_note") and x.klass == "revoke_full"]
        ofr_part = [x for x in inw if x.src == "LE" and x.evtype.startswith("ofr_note") and x.klass == "revoke_part"]
        c_rev = [x for x in c89_rows if x.klass == "revoke_full"]
        c_inforce = [x for x in c89_rows if x.klass == "in_force_1989"]
        ofr_before_1989 = [x for x in ofr_full if x.year is not None and x.year <= 1988]
        rows.append({"iid": iid, "T_rev": r["revoked"] == "1", "T_part": r["partrevoked"] == "1",
                     "ofr_full": bool(ofr_full), "ofr_any": bool(ofr_full or ofr_part), "c89_revoked": bool(c_rev),
                     "c89_in_force": bool(c_inforce), "ofr_full_before_1989": bool(ofr_before_1989)})
    F = pd.DataFrame(rows)

    def rate(mask, label):
        sub = F[mask]
        return {"orders": int(len(sub)), "thrower_revoked": int(sub["T_rev"].sum()),
                "rate": round(float(sub["T_rev"].mean()), 4) if len(sub) else None}

    S["fingerprint"] = {
        "orders_with_a_1989_table_row": int(len(F)),
        "OFR_notes_say_revoked_and_1989_says_revoked": rate(F.ofr_any & F.c89_revoked, ""),
        "OFR_notes_silent_1989_says_revoked": rate(~F.ofr_any & F.c89_revoked, ""),
        "OFR_notes_say_revoked_1989_not_revoked": rate(F.ofr_any & ~F.c89_revoked, ""),
        "OFR_notes_say_revoked_before_1989_but_1989_codified": rate(F.ofr_full_before_1989 & F.c89_in_force, ""),
        "neither_says_revoked": rate(~F.ofr_any & ~F.c89_revoked, ""),
    }
    S["fingerprint"]["reading"] = ("If Thrower's tables were independent of the OFR notes, her revoked rate in the second row would "
                                   "resemble the first row's. A rate near 0 there and near 1 in the third row means she follows the notes.")

    # ---- 3 dates ----
    pat = re.compile(r"note_states_(\d{4})-\d\d-\d\d_but_catalog_signing_date_is_(\d{4})-\d\d-\d\d")
    drows = []
    for r in e[e["klass"].isin(REV) & e["date_flags"].fillna("").str.contains("note_states_")].itertuples(index=False):
        m = pat.search(r.date_flags)
        if not m or m.group(1) == m.group(2) or r.target not in tix.index:
            continue
        tr = tix.loc[r.target]
        drows.append({"edge_id": r.edge_id, "target": r.target, "acting": r.acting, "note_year": int(m.group(1)), "catalog_year": int(m.group(2)),
                      "thrower_revoked": tr["revoked"], "thrower_revoke_year": tr["revoke_year"], "thrower_part": tr["partrevoked"]})
    D = pd.DataFrame(drows)
    if len(D):
        D = D.drop_duplicates(["target", "acting", "note_year", "catalog_year"])
        D.to_csv(os.path.join(out, "INHERITED_date_flagged_edges.csv"), index=False, lineterminator="\n")
        Dr = D[D["thrower_revoked"] == "1"].copy()
        Dr["ty"] = pd.to_numeric(Dr["thrower_revoke_year"])
        S["dates"] = {"revocation_edges_where_note_year_differs_from_catalog_signing_year": int(len(D)),
                      "of_which_thrower_revoked": int(len(Dr)),
                      "thrower_year_equals_note_year": int((Dr["ty"] == Dr["note_year"]).sum()),
                      "thrower_year_equals_catalog_signing_year": int((Dr["ty"] == Dr["catalog_year"]).sum()),
                      "thrower_year_equals_neither": int(((Dr["ty"] != Dr["note_year"]) & (Dr["ty"] != Dr["catalog_year"])).sum())}
    else:
        S["dates"] = {"revocation_edges_where_note_year_differs_from_catalog_signing_year": 0}

    # ---- 4 flags ----
    flags = []
    # 4a: pairs with an OFR note and a held official text, class differs
    le = e[e["target"].isin(tix.index) & e["klass"].isin(REV) & (e["acting"] != e["target"])]
    pair = {}
    for r in le.itertuples(index=False):
        src = "primary" if r.evidence_type in PRIMARY_TYPES else ("ofr" if r.evidence_type.startswith("ofr_note") else "other")
        pair.setdefault((r.target, r.acting), {}).setdefault(src, []).append(r)
    n_pairs_both = n_class_differs = 0
    for (tg, ac), d in pair.items():
        if "ofr" in d and "primary" in d:
            n_pairs_both += 1
            ofr_k = {x.klass for x in d["ofr"]}
            pri_k = {x.klass for x in d["primary"]}
            if ofr_k != pri_k and not (len(ofr_k) > 1 or len(pri_k) > 1):
                tr = tix.loc[tg]
                n_class_differs += 1
                if "revoke_full" in ofr_k and "revoke_part" in pri_k:
                    flag, agrees = "ofr_whole_primary_text_partial", (tr["revoked"] == "1" and tr["partrevoked"] == "0")
                else:
                    flag, agrees = "ofr_partial_primary_text_whole", (tr["partrevoked"] == "1")
                flags.append({"eo": tg, "flag": flag, "thrower_agrees_with_ofr": bool(agrees), "thrower_fact": tfact(tr),
                              "ofr_fact": f"{ac} {sorted(ofr_k)} " + ";".join(sorted({f'{EDGES_PATH}#{x.edge_id}' for x in d['ofr']})[:3]),
                              "held_official_text_fact": f"{ac} {sorted(pri_k)} quote: " + " | ".join(str(x.quote)[:160] for x in d["primary"][:1]),
                              "source_paths": ";".join(sorted({f'{EDGES_PATH}#{x.edge_id}' for x in d["primary"]})[:3])})
    S["official_text_vs_ofr_note"] = {"pairs_with_both": n_pairs_both, "pairs_whole_vs_partial_differs": n_class_differs}

    # 4b: Thrower + OFR notes revoked before 1989, 1989 Codification lists the order as codified
    for iid, r in tix.iterrows():
        inw, _ = split_window(ev.get(iid, []))
        ofr_full = [x for x in inw if x.src == "LE" and x.evtype.startswith("ofr_note") and x.klass == "revoke_full" and x.year is not None and x.year <= 1988]
        inforce = [x for x in inw if x.klass == "in_force_1989"]
        if r["revoked"] == "1" and ofr_full and inforce:
            flags.append({"eo": iid, "flag": "thrower_and_ofr_revoked_before_1989_but_1989_table_codified", "thrower_agrees_with_ofr": True,
                          "thrower_fact": tfact(r), "ofr_fact": "; ".join(x.text() for x in ofr_full[:3]),
                          "held_official_text_fact": "1989 Codification table: codified (in force 1989-01-20); the Codification prints the order's text; note: an editorial compilation, not a primary original",
                          "source_paths": ";".join([x.ref for x in ofr_full[:2]] + [x.ref for x in inforce[:1]])})
        # 4c: shared omission, held official text states a whole-order revocation of this order
        prim_full = [x for x in inw if x.src == "LE" and x.evtype in PRIMARY_TYPES and x.klass == "revoke_full"]
        ofr_any = [x for x in inw if (x.src == "LE" and x.evtype.startswith("ofr_note") and x.klass in REV) or (x.src == "C89" and x.klass == "revoke_full")]
        if prim_full and not ofr_any and r["revoked"] == "0":
            flags.append({"eo": iid, "flag": "shared_omission_held_official_text_states_revocation", "thrower_agrees_with_ofr": True,
                          "thrower_fact": tfact(r), "ofr_fact": "no revocation in OFR notes or the 1989 table",
                          "held_official_text_fact": "; ".join(x.text() for x in prim_full[:3]),
                          "source_paths": ";".join(x.ref for x in prim_full[:3])})
    Fl = pd.DataFrame(flags)
    Fl.to_csv(os.path.join(out, "INHERITED_flags.csv"), index=False, lineterminator="\n")
    S["flags"] = Fl["flag"].value_counts().to_dict() if len(Fl) else {}
    if len(Fl):
        S["flags_thrower_agrees_with_ofr"] = Fl.groupby("flag")["thrower_agrees_with_ofr"].sum().astype(int).to_dict()
    with open(os.path.join(out, "INHERITED_SUMMARY.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(S, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    print(json.dumps(S, indent=1, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
