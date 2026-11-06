"""Draw the 15-case hand-check sample from DISAGREEMENTS.csv (seeded, stratified by kind) and dump the project's
evidence record for each (OFR notes on the order and on the acting orders, 1989 table row, edge quotes, register line).

usage: py -I draw_sample.py ARCHIVE_DIR PROJECT_CACHE_DIR OUT_DIR [DUMP_FILE]
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from thrower_lib import load_c89, load_edges, norm_id, read_csv, read_thrower

SEED = 20261106
QUOTA = [("project_revoked_thrower_silent", 3), ("thrower_revoked_project_silent", 2), ("year_differs", 3),
         ("partial_vs_full", 2), ("project_superseded_thrower_silent", 1), ("project_partial_revoked_thrower_silent", 1),
         ("thrower_revoked_project_status_in_effect", 2), ("supersede_year_differs", 1)]


def main():
    archive, cache, out = sys.argv[1:4]
    dump = sys.argv[4] if len(sys.argv) > 4 else None
    D = pd.read_csv(os.path.join(out, "DISAGREEMENTS.csv"), dtype=str, keep_default_na=False)
    rng = random.Random(SEED)
    picks = []
    used = set()
    frozen = os.path.join(out, "SAMPLE15_frozen_draw.csv")
    if os.path.exists(frozen):
        # The 15 cases were drawn (seed above) from the first pipeline version and hand-read; the draw is kept frozen so
        # the reading stays valid when the pipeline changes. Delete the file to redraw from the current DISAGREEMENTS.csv.
        F = pd.read_csv(frozen, dtype=str)
        picks = list(zip(F["kind"], F["eo"]))
        S = pd.DataFrame(picks, columns=["kind_at_draw", "eo"])
        S["kinds_now"] = [";".join(sorted(set(D.loc[D["eo"] == e, "kind"]))) or "(none)" for e in S["eo"]]
        S.to_csv(os.path.join(out, "SAMPLE15_draw.csv"), index=False, lineterminator="\n")
        QUOTA_USED = []
    else:
        QUOTA_USED = QUOTA
    for kind, n in QUOTA_USED:
        pool = sorted(set(D.loc[D["kind"] == kind, "eo"]) - used)
        if kind == "project_revoked_thrower_silent":
            # one each of: 1989 table only, OFR note (no 1989 row), held official text only
            def ev(e):
                return D.loc[(D["eo"] == e) & (D["kind"] == kind), "project_evidence"].iloc[0]
            groups = [[e for e in pool if ev(e) == "C89:c89_table"],
                      [e for e in pool if "ofr_note" in ev(e) and "C89" not in ev(e)],
                      [e for e in pool if "ofr_note" not in ev(e) and "C89" not in ev(e)]]
            chosen = [rng.choice(g) for g in groups if g]
        else:
            chosen = rng.sample(pool, min(n, len(pool)))
        for e in chosen:
            picks.append((kind, e))
            used.add(e)
    if not os.path.exists(frozen):
        S = pd.DataFrame(picks, columns=["kind", "eo"])
        S.to_csv(os.path.join(out, "SAMPLE15_draw.csv"), index=False, lineterminator="\n")
    if not dump:
        print(S)
        return
    t = read_thrower(archive).set_index("instrument_id")
    e = load_edges(cache)
    c89 = load_c89(cache)
    cat = read_csv(cache, "jobs/later-events/output/CATALOG_INDEX.csv").set_index("id")
    reg = read_csv(cache, "jobs/domesday-register/output/REGISTER.csv")
    reg["iid"] = reg["instrument_id"].map(norm_id)
    reg = reg.set_index("iid")
    lines = []
    for kind, eo in picks:
        lines.append("=" * 100)
        lines.append(f"{eo}  [{kind}]")
        tr = t.loc[eo]
        lines.append("THROWER: " + ", ".join(f"{c}={tr[c]}" for c in ["eonumber", "year", "revoked", "revoke_year", "partrevoked", "superseded", "supersede_year", "revokedbyotherthaneo", "reject_revoke_eo", "ceremonial"]))
        if eo in cat.index:
            lines.append(f"CATALOG {eo}: {cat.loc[eo,'signing_date']} | {str(cat.loc[eo,'title'])[:100]} | NOTES: {cat.loc[eo,'disposition_notes']}")
        if eo in reg.index:
            rr = reg.loc[eo]
            lines.append(f"REGISTER: status={rr['provisional_status']} best_held={rr['best_held']} blockers={rr['blockers']}")
        for r in c89[c89["target"] == eo].itertuples():
            lines.append(f"C89 row seq={r.seq} p{r.page}: raw={r.raw} | disp={r.disposition} | cat={r.category} | acting={r.acting_documents} | check={r.later_events_check}")
        sub = e[(e["target"] == eo) & e["klass"].isin(["revoke_full", "revoke_part", "supersede_full", "supersede_part", "other_end"])]
        for r in sub.itertuples():
            lines.append(f"EDGE {r.edge_id} {r.klass} by {r.acting} {r.date_candidate} <{r.evidence_type}> q='{r.qualifier}' flags={r.date_flags}\n     QUOTE: {str(r.quote)[:300]}")
        acts = sorted({a for a in sub["acting"].dropna() if a in cat.index})
        for a in acts[:3]:
            lines.append(f"ACTING CATALOG {a}: {cat.loc[a,'signing_date']} | {str(cat.loc[a,'title'])[:90]} | NOTES: {str(cat.loc[a,'disposition_notes'])[:300]}")
    with open(dump, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(S)


if __name__ == "__main__":
    main()
