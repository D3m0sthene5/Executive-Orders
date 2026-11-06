"""REVOCATION CROSS-CHECK: Thrower's revoked / revoke_year / superseded / partrevoked against the project's
formal-revocation facts (later-events edges, 1989 Codification table; peano lemmas and status-history events
are looked up as derived views). Every row of DISAGREEMENTS.csv is a lead, never a fact.

usage: py -I crosscheck.py ARCHIVE_DIR PROJECT_CACHE_DIR OUT_DIR
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from thrower_lib import (WINDOW_LAST_YEAR, load_c89, load_edges, load_peano, load_sh_events, norm_id, read_csv,
                         read_thrower, year_of)

EDGES_PATH = "jobs/later-events/output/EDGES.csv"
C89_PATH = "jobs/ofr-codification-1989/output/DISPOSITION_1989.csv"
REV = {"revoke_full", "revoke_part"}
SUP = {"supersede_full", "supersede_part"}
C89_FORMAL_OTHER = {"authority", "nullified", "terminated", "eliminated", "abolished", "expired"}


class Ev:
    __slots__ = ("src", "klass", "acting", "year", "ref", "evtype", "mechanism", "qualifier", "date")

    def __init__(self, src, klass, acting, year, ref, evtype, mechanism="", qualifier="", date=""):
        self.src, self.klass, self.acting, self.year, self.ref, self.evtype = src, klass, acting, year, ref, evtype
        self.mechanism, self.qualifier, self.date = mechanism, qualifier, date

    def text(self):
        q = f" [{self.qualifier[:40]}]" if self.qualifier else ""
        return f"{self.klass}{q} by {self.acting if isinstance(self.acting, str) else chr(63)} ({self.date or 'no date'}) <{self.evtype}>"


def build_events(t, e, c89, cat):
    tset = set(t["instrument_id"])
    cat_date = dict(zip(cat["id"].map(norm_id), cat["signing_date"]))
    ev = defaultdict(list)
    ed = e[e["target"].isin(tset) & (e["acting"] != e["target"]) & e["klass"].isin(REV | SUP | {"other_end"})]
    self_edges = int(((e["acting"] == e["target"]) & e["target"].isin(tset)).sum())
    # later-events' own rule: a whole-order end needs that no other evidence for the same acting order and target says "partial"
    pairs_part = {(a, b) for a, b, k in zip(ed["target"], ed["acting"], ed["klass"]) if k == "revoke_part"}
    downgraded = 0
    for r in ed.itertuples(index=False):
        klass, qual = r.klass, r.qualifier
        if klass == "revoke_full" and (r.target, r.acting) in pairs_part:
            klass, qual, downgraded = "revoke_part", "conflict: other evidence for this pair says partial", downgraded + 1
        ev[r.target].append(Ev("LE", klass, r.acting, r.event_year, f"{EDGES_PATH}#{r.edge_id}", r.evidence_type,
                               r.mechanism, qual, r.date_candidate if isinstance(r.date_candidate, str) else ""))
    n89 = 0
    for r in c89[c89["target"].isin(tset)].itertuples(index=False):
        cat_ = r.category
        if cat_ == "revoked":
            k = "revoke_full"
        elif cat_ in ("superseded", "replaced"):
            k = "supersede_full"
        elif cat_ in C89_FORMAL_OTHER:
            k = "other_end"
        elif r.group == "in_force_1989":
            k = "in_force_1989"
        else:
            k = "c89_other:" + str(cat_)
        acts = [a for a in str(r.acting_documents).split("|") if a and a != "nan"]
        dates = [cat_date.get(norm_id(a)) for a in acts if a.startswith("EO:")]
        dates = [d for d in dates if isinstance(d, str)]
        ev[r.target].append(Ev("C89", k, "|".join(acts) or "none", year_of(dates[0]) if dates else None,
                               f"{C89_PATH}#seq={r.seq}", "c89_table", cat_, "", dates[0] if dates else ""))
        n89 += 1
    return ev, {"self_edges_dropped": self_edges, "c89_rows_joined_to_thrower": n89, "whole_edges_downgraded_to_partial_by_conflict": downgraded}


def split_window(evs):
    inw = [x for x in evs if x.year is None or x.year <= WINDOW_LAST_YEAR]
    post = [x for x in evs if x.year is not None and x.year > WINDOW_LAST_YEAR]
    return inw, post


def yrs(evs, klasses):
    return sorted({x.year for x in evs if x.klass in klasses and x.year is not None})


def has(evs, klasses):
    return [x for x in evs if x.klass in klasses]


def tfact(r):
    return (f"revoked={r['revoked']} revoke_year={r['revoke_year'] or ''} partrevoked={r['partrevoked']} "
            f"superseded={r['superseded']} supersede_year={r['supersede_year'] or ''} "
            f"revokedbyotherthaneo={r['revokedbyotherthaneo']} revokedbyeo12553={r['revokedbyeo12553']}")


def pfact(evs):
    if not evs:
        return "no revocation, supersession or other-end event"
    return "; ".join(x.text() for x in evs[:6]) + (f"; +{len(evs) - 6} more" if len(evs) > 6 else "")


def pref(evs, extra=""):
    refs = []
    for x in evs[:6]:
        if x.ref not in refs:
            refs.append(x.ref)
    return ";".join(refs) if refs else (extra or f"{EDGES_PATH} (none for this order);{C89_PATH} (none for this order)")


def mindiff(y, ys):
    return min(abs(y - z) for z in ys) if ys else None


def main():
    archive, cache, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    t = read_thrower(archive)
    # revokedbyeo12553 comes from the deposit's main .dta; the derived table holds it
    derived = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "thrower_orders.csv"), dtype=str)
    t = t.merge(derived[["instrument_id", "revokedbyeo12553"]], on="instrument_id", how="left")
    t = t.fillna({"revoke_year": "", "supersede_year": ""})
    e = load_edges(cache)
    c89 = load_c89(cache)
    cat = read_csv(cache, "jobs/later-events/output/CATALOG_INDEX.csv")
    ev, dropinfo = build_events(t, e, c89, cat)
    rd = read_csv(cache, "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")
    rd["instrument_id"] = rd["instrument_id"].map(norm_id)
    status = dict(zip(rd["instrument_id"], rd["provisional_status"]))
    origin = dict(zip(rd["instrument_id"], rd["decision_origin"]))

    peano = load_peano(cache)
    sh = load_sh_events(cache)
    peano_rev = peano[peano["relation"].isin(["revokes", "supersedes", "terminates", "abolishes_agency", "repeals_authority", "holds_invalid", "supersession_or_revocation"])]
    p_proved = peano_rev[peano_rev["status"] == "proved"].groupby("target").size().to_dict()
    p_sorry = peano_rev[peano_rev["status"] != "proved"].groupby("target").size().to_dict()
    sh_rev = sh[sh["mechanism"].isin(["revocation", "rescission", "supersession", "supersession_or_revocation", "termination", "abolition", "authority_repeal", "nullification"])]
    sh_n = sh_rev.groupby("target").size().to_dict()

    # other (non-ending) later-events edges per target, for the reason text
    other_edges = e[e["target"].isin(set(t["instrument_id"])) & (e["acting"] != e["target"]) & ~e["klass"].isin(REV | SUP | {"other_end"})]
    other_n = other_edges[other_edges["mechanism"] != "cross_reference"].groupby("target").size().to_dict()
    xref_n = other_edges[other_edges["mechanism"] == "cross_reference"].groupby("target").size().to_dict()

    rows, after_rows, order_rows = [], [], []
    stat = defaultdict(int)

    def add(r, kind, reason, evs, extra=""):
        iid = r["instrument_id"]
        kinds_ev = sorted({x.src + ":" + x.evtype for x in evs})
        rows.append({"eo": iid, "thrower_fact": tfact(r), "project_fact": pfact(evs),
                     "project_source_path": pref(evs, extra), "kind": kind, "reason": reason,
                     "thrower_eonumber": r["eonumber"], "thrower_year": r["year"],
                     "project_evidence": "|".join(kinds_ev),
                     "peano_end_lemmas_proved": p_proved.get(iid, 0), "peano_end_lemmas_sorry": p_sorry.get(iid, 0),
                     "status_history_end_events": sh_n.get(iid, 0)})

    for _, r in t.iterrows():
        iid = r["instrument_id"]
        evs_all = ev.get(iid, [])
        inw, post = split_window(evs_all)
        T_rev, T_sup, T_part = r["revoked"] == "1", r["superseded"] == "1", r["partrevoked"] == "1"
        T_ry = int(r["revoke_year"]) if r["revoke_year"] else None
        T_sy = int(r["supersede_year"]) if r["supersede_year"] else None
        Rf, Rp = has(inw, {"revoke_full"}), has(inw, {"revoke_part"})
        Sf, Sp = has(inw, {"supersede_full"}), has(inw, {"supersede_part"})
        Eo = has(inw, {"other_end"})
        inforce89 = has(inw, {"in_force_1989"})
        P_rev = Rf + Rp
        P_sup = Sf + Sp
        P_end = P_rev + P_sup + Eo
        Y_rev = yrs(inw, REV)
        Y_sup = yrs(inw, SUP)
        order_rows.append({"instrument_id": iid, "T_revoked": int(T_rev), "T_superseded": int(T_sup), "T_part": int(T_part),
                           "P_rev_full": int(bool(Rf)), "P_rev_part": int(bool(Rp)), "P_sup": int(bool(P_sup)),
                           "P_other_end": int(bool(Eo)), "P_any_end": int(bool(P_end)), "P_post2013_end": int(bool(has(post, REV | SUP | {"other_end"}))),
                           "year": int(r["year"]), "T_revoke_year": T_ry, "P_rev_min_year": Y_rev[0] if Y_rev else None,
                           "P_rev_max_year": Y_rev[-1] if Y_rev else None, "in_force_1989": int(bool(inforce89)),
                           "year_min_diff": mindiff(T_ry, Y_rev) if (T_rev and T_ry is not None and Y_rev) else None})

        # ---- revoked ----
        if T_rev and not P_end:
            late = has(post, REV | SUP | {"other_end"})
            bits = []
            if inforce89:
                bits.append("the 1989 Codification table lists it as codified (in force on 1989-01-20)")
            if other_n.get(iid):
                bits.append(f"later-events holds {other_n[iid]} amendment/continuation/other edges but no ending")
            if xref_n.get(iid):
                bits.append(f"{xref_n[iid]} 'See' cross-references")
            if not (other_n.get(iid) or xref_n.get(iid) or inforce89):
                bits.append("no later-events edge of any kind and no 1989 row")
            if late:
                bits.append("a project ending dated after 2013 exists")
            add(r, "thrower_revoked_project_silent",
                "Thrower revoked in %s; project has no revocation, supersession or other ending dated by 2013: %s" % (T_ry, "; ".join(bits)),
                inforce89 + late)
        elif T_rev and not P_rev and (P_sup or Eo):
            add(r, "revoked_vs_superseded" if P_sup else "revoked_vs_other_end",
                "Thrower codes revoked; the project records only a %s" % ("supersession" if P_sup else "termination/abolition/authority-repeal/other-ending"),
                P_sup + Eo)
        if (not T_rev) and (not T_sup) and Rf:
            basis = "OFR note or 1989 table" if any(x.src == "C89" or x.evtype.startswith("ofr_note") for x in Rf) else "order text only (text_only_unverified under later-events' rules)"
            add(r, "project_revoked_thrower_silent",
                "project records a whole-order revocation dated %s (basis: %s); Thrower has revoked=0 and superseded=0" % (Y_rev[0] if Y_rev else "(undated)", basis), Rf)
        elif (not T_rev) and (not T_sup) and (not Rf) and Rp:
            add(r, "project_partial_revoked_thrower_silent",
                "project records only partial/qualified revocation(s); Thrower codes partial revocations as revoked=1 but has 0 here", Rp)
        if T_sup and not T_rev and Rf and not P_sup:
            add(r, "thrower_superseded_project_revoked",
                "Thrower codes superseded; the project records a whole-order revocation and no supersession", Rf)

        # ---- year ----
        if T_rev and P_rev and T_ry is not None and Y_rev:
            d = mindiff(T_ry, Y_rev)
            if d == 1:
                add(r, "year_differs_by_one", "Thrower revoke_year %d; nearest project revocation year differs by 1 (project years %s)" % (T_ry, Y_rev), P_rev)
            elif d is not None and d >= 2:
                add(r, "year_differs", "Thrower revoke_year %d; no project revocation year within 1 year (project years %s)" % (T_ry, Y_rev), P_rev)

        # ---- partial vs full ----
        if T_part and Rf and not Rp:
            add(r, "partial_vs_full", "Thrower partrevoked=1; the project records only unqualified whole-order revocation(s)", Rf)
        elif T_rev and not T_part and Rp and not Rf:
            add(r, "partial_vs_full", "Thrower revoked in full (partrevoked=0); the project records only qualified (partial) revocation(s)", Rp)

        # ---- superseded ----
        if T_sup and not P_sup:
            if not (P_rev or Eo):
                add(r, "thrower_superseded_project_silent", "Thrower superseded in %s; project has no supersession, revocation or ending by 2013" % T_sy, [])
            elif not Rf:
                add(r, "thrower_superseded_project_silent", "Thrower superseded in %s; project has no supersession edge (only qualified revocation or other ending)" % T_sy, P_rev + Eo)
        if (not T_sup) and (not T_rev) and Sf and not Rf:
            add(r, "project_superseded_thrower_silent",
                "project records a whole-order supersession dated %s; Thrower has superseded=0 and revoked=0" % (Y_sup[0] if Y_sup else "(undated)"), Sf)
        if T_sup and T_sy and P_sup and Y_sup:
            d = mindiff(T_sy, Y_sup)
            if d is not None and d >= 2:
                add(r, "supersede_year_differs", "Thrower supersede_year %d; no project supersession year within 1 year (project years %s)" % (T_sy, Y_sup), P_sup)

        # ---- 1989 table says in force, Thrower says revoked earlier ----
        if T_rev and T_ry is not None and T_ry <= 1988 and inforce89 and not Rf and not (T_part and Rp):
            add(r, "thrower_revoked_c89_in_force",
                "Thrower revoked in %d; the 1989 Codification lists the order as codified (in force on 1989-01-20) and the project has no whole-order revocation by then" % T_ry, inforce89)

        # ---- project provisional status says "in effect" (YES) for an order Thrower coded revoked ----
        if T_rev and not T_part and status.get(iid) == "yes":
            add(r, "thrower_revoked_project_status_in_effect",
                "project provisional status is YES (still in effect, AI or inherited status hypothesis, not certified); Thrower revoked in %s; project formal events by 2013: %s; decision_origin: %s"
                % (T_ry, "present" if P_end else "none", str(origin.get(iid))[:60]), P_end,
                extra="jobs/readiness-tracker/output/READINESS_BY_ORDER.csv (provisional_status=yes)")

        # ---- after the window: expected differences, listed apart ----
        if (not T_rev) and (not P_end):
            late = has(post, REV | SUP | {"other_end"})
            if late:
                after_rows.append({"eo": iid, "thrower_fact": tfact(r), "project_fact": pfact(late),
                                   "project_source_path": pref(late), "kind": "project_ending_after_thrower_window",
                                   "reason": "project ending is dated after 2013, outside Thrower's observation window; expected, not a disagreement"})

    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(out, "DISAGREEMENTS.csv"), index=False, lineterminator="\n")
    pd.DataFrame(after_rows).to_csv(os.path.join(out, "EXPECTED_AFTER_WINDOW.csv"), index=False, lineterminator="\n")
    O = pd.DataFrame(order_rows)
    O.to_csv(os.path.join(out, "ORDER_FACTS.csv"), index=False, lineterminator="\n")

    # ---- agreement tables ----
    def two_by_two(a, b):
        return {"both": int(((a == 1) & (b == 1)).sum()), "thrower_only": int(((a == 1) & (b == 0)).sum()),
                "project_only": int(((a == 0) & (b == 1)).sum()), "neither": int(((a == 0) & (b == 0)).sum())}

    S = {"orders": len(O), "drop_info": dropinfo}
    P_rev_any = ((O["P_rev_full"] == 1) | (O["P_rev_part"] == 1)).astype(int)
    S["revoked_vs_project_any_revocation"] = two_by_two(O["T_revoked"], P_rev_any)
    S["revoked_vs_project_any_end"] = two_by_two(O["T_revoked"], O["P_any_end"])
    S["superseded_vs_project_supersession"] = two_by_two(O["T_superseded"], O["P_sup"])
    S["part_vs_project_part_only"] = two_by_two(O["T_part"], ((O["P_rev_part"] == 1) & (O["P_rev_full"] == 0)).astype(int))
    both = O[(O["T_revoked"] == 1) & (P_rev_any == 1) & O["T_revoke_year"].notna()].copy()
    both["T_revoke_year"] = both["T_revoke_year"].astype(int)
    S["revoke_year_among_both_revoked"] = {
        "n": len(both),
        "equals_project_min_year": int((both["T_revoke_year"] == both["P_rev_min_year"]).sum()),
        "equals_project_max_year": int((both["T_revoke_year"] == both["P_rev_max_year"]).sum()),
        "within_project_min_max": int(((both["T_revoke_year"] >= both["P_rev_min_year"] - 0) & (both["T_revoke_year"] <= both["P_rev_max_year"])).sum()),
        "within_1_of_project_min": int(((both["T_revoke_year"] - both["P_rev_min_year"]).abs() <= 1).sum()),
        "exact_some_project_year": int((both["year_min_diff"] == 0).sum()),
        "off_by_one_from_nearest_project_year": int((both["year_min_diff"] == 1).sum()),
        "off_by_two_or_more": int((both["year_min_diff"] >= 2).sum()),
    }
    S["thrower_revoked_by_project_status"] = (t.assign(st=t["instrument_id"].map(status).fillna("undecided"))
                                              .groupby(["revoked", "st"]).size().unstack(fill_value=0).to_dict("index"))
    same = t[(t["revoked"] == "1") & (t["revoke_year"] == t["year"])]
    O2 = O.set_index("instrument_id")
    S["thrower_revoke_year_equals_issue_year"] = {
        "orders": int(len(same)),
        "project_revocation_in_that_year": int(sum(1 for i in same["instrument_id"] if O2.loc[i, "year_min_diff"] == 0)),
        "project_revocation_only_in_other_years": int(sum(1 for i in same["instrument_id"] if pd.notna(O2.loc[i, "year_min_diff"]) and O2.loc[i, "year_min_diff"] > 0)),
        "project_no_revocation": int(sum(1 for i in same["instrument_id"] if pd.isna(O2.loc[i, "year_min_diff"])))}
    S["thrower_revoked_partial_and_project_status_in_effect"] = int(((t["revoked"] == "1") & (t["partrevoked"] == "1") & (t["instrument_id"].map(status) == "yes")).sum())
    S["disagreement_counts_by_kind"] = D["kind"].value_counts().to_dict()
    pq = D[D["kind"] == "partial_vs_full"]
    pq = pq[pq["reason"].str.contains("Thrower revoked in full")]["project_fact"].str.extract(r"\[([^\]]*)\]")[0].fillna("")
    def qcat(q):
        q = q.lower()
        if q.startswith("conflict"):
            return "whole in one source, partial in another (downgraded)"
        if q.startswith("in part"):
            return "in part"
        if q.startswith("with respect to"):
            return "with respect to ... (clause may qualify a different verb)"
        if q.startswith("section") or q.startswith("partial wording"):
            return "section or provision named"
        return "other qualifier"
    S["thrower_full_project_partial_qualifier_types"] = pq.map(qcat).value_counts().to_dict()
    S["disagreement_rows"] = len(D)
    S["disagreement_distinct_orders"] = int(D["eo"].nunique())
    S["expected_after_window_rows"] = len(after_rows)

    # EO 12553 and "other than EO" flags
    rbe = t[t["revokedbyeo12553"] == "1"]
    acts12553 = {x for x in e[(e["acting"] == "EO:12553") & e["klass"].isin(REV)]["target"]}
    c12553 = {r.target for r in c89[c89["acting_documents"].fillna("").str.contains(r"EO:12553\b")].itertuples()}
    S["revokedbyeo12553"] = {"thrower_flagged": len(rbe),
                             "project_later_events_has_EO12553_revocation_edge": int(rbe["instrument_id"].isin(acts12553).sum()),
                             "project_1989_table_names_EO12553": int(rbe["instrument_id"].isin(c12553).sum()),
                             "project_orders_with_EO12553_edge_in_thrower_range_but_not_flagged": int(len((acts12553 & set(t["instrument_id"])) - set(rbe["instrument_id"])))}
    rbo = t[t["revokedbyotherthaneo"] == "1"]
    acting_kinds = defaultdict(int)
    for iid in rbo["instrument_id"]:
        ks = {(x.acting.split(":")[0] if isinstance(x.acting, str) else "unidentified") for x in ev.get(iid, []) if x.klass in REV and x.src == "LE"}
        acting_kinds["|".join(sorted(ks)) or "none"] += 1
    S["revokedbyotherthaneo"] = {"thrower_flagged": len(rbo), "project_acting_instrument_types_of_revocation_edges": dict(acting_kinds)}

    dec = O.copy()
    dec["decade"] = (dec["year"] // 10 * 10).astype(str) + "s"
    dec["P_rev_any"] = P_rev_any
    g = dec.groupby("decade").apply(lambda x: pd.Series({
        "orders": len(x), "T_revoked": int(x["T_revoked"].sum()), "P_rev_any": int(x["P_rev_any"].sum()),
        "both": int(((x["T_revoked"] == 1) & (x["P_rev_any"] == 1)).sum()),
        "thrower_only": int(((x["T_revoked"] == 1) & (x["P_rev_any"] == 0)).sum()),
        "project_only": int(((x["T_revoked"] == 0) & (x["P_rev_any"] == 1)).sum())}), include_groups=False).reset_index()
    g.to_csv(os.path.join(out, "AGREEMENT_BY_DECADE.csv"), index=False, lineterminator="\n")
    with open(os.path.join(out, "CROSSCHECK_SUMMARY.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(S, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(S, indent=1, sort_keys=True))
    print(g.to_string())


if __name__ == "__main__":
    main()
