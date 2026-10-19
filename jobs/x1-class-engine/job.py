"""X1, the lifecycle class engine: type, rule, event, cluster and batch sheets for pre-1937 orders.

Zero-token and offline. Reads committed outputs of other jobs (claim-kit,
readiness-tracker, source-ladder, app-executive-orders) and the WPA lists in
data/. Writes leads only: no claim, status, identity, count or judgment field.
See README.md.
"""
import collections, csv, hashlib, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import classify, cluster, events, sheets, taxonomy  # noqa: E402

REVIEW = "research/production/x1-2026-10-19/TYPE_RULES_REVIEW.json"


def write_csv(path, rows, cols=None):
    cols = cols or (list(rows[0].keys()) if rows else [])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def check_rules(repo):
    """Each type rule: frozen hash against its independent review, exact quote against its held text."""
    review = {}
    rp = repo / REVIEW
    if rp.exists():
        for it in json.load(open(rp)).get("items", []):
            review[it["rule_id"]] = it
    out = {}
    for p in sorted((repo / "research/readiness/type-rules").glob("TR-*.json")):
        rule = json.loads(p.read_text(encoding="utf-8"))
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        q, src = rule.get("quoted_clause", ""), rule.get("source", {})
        quote = "no_quote"
        if q and src.get("text_path"):
            tp = repo / src["text_path"]
            if not tp.exists():
                quote = "text_not_held"
            else:
                raw = tp.read_text(encoding="utf-8", errors="replace")
                ok_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest() == src.get("text_sha256")
                quote = ("exact" if q in raw else "not_found") + ("" if ok_hash else "_text_hash_changed")
        rv = review.get(rule["rule_id"])
        if not rv:
            state = "unreviewed"
        elif rv.get("rule_file_sha256") != sha:
            state = "changed_after_review"
        else:
            state = "reviewed_frozen:" + rv.get("decision", "")
        out[rule["rule_id"]] = {"rule_file_sha256": sha, "quote_check": quote, "review_state": state,
                                "types": rule.get("types", []), "exemplar": (rule.get("exemplar") or {}).get("instrument_id")}
    return out


def main():
    out = Path(os.environ.get("OUTPUT_DIR", HERE / "output"))
    repo = Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows = classify.classify(repo, HERE)
    types = {r["instrument_id"]: r for r in rows}
    write_csv(out / "TYPES.csv", rows)
    project_ids = {r["id"] for r in csv.DictReader(open(repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"))}
    gap = classify.classify_gap(repo, HERE, project_ids)
    write_csv(out / "GAP_TYPES.csv", gap)
    print(f"classified {len(rows)} pre-1937 orders; {len(gap)} census-gap candidate rows")

    rules = check_rules(repo)
    json.dump(rules, open(out / "TYPE_RULES_CHECK.json", "w"), indent=1, sort_keys=True)
    rule_state = {k: v["review_state"] + ("" if v["quote_check"] in ("exact", "no_quote") else "|quote:" + v["quote_check"])
                  for k, v in rules.items()}

    clusters, members, cloned, csum = cluster.build(repo, set(types), types)
    json.dump(clusters, open(out / "CLUSTERS.json", "w"), indent=1)
    write_csv(out / "CLUSTER_MEMBERS.csv", members)
    with open(out / "CLONED_CLAUSES.jsonl", "w") as f:
        for c in cloned:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    fams = cluster.modern_families(repo)
    json.dump(fams, open(out / "MODERN_FAMILIES.json", "w"), indent=1)
    print("clusters:", csum)

    wpa = classify.load_wpa(HERE)
    reg, ev_states, ev_rows = events.map_events(repo, HERE, types, wpa)
    json.dump(ev_states, open(out / "EVENT_SOURCES_STATE.json", "w"), indent=1)
    write_csv(out / "EVENT_CANDIDATES.csv", ev_rows)

    batches = sheets.build(repo, types, members, cloned, ev_rows, rule_state)
    (out / "sheets").mkdir(exist_ok=True)
    for b in batches:
        write_csv(out / "sheets" / f"{b['batch_id']}.csv", b["rows"], sheets.COLUMNS)
    bsum = sheets.summary(batches)
    json.dump(bsum, open(out / "BATCHES.json", "w"), indent=1)

    by_type = collections.Counter(r["type"] for r in rows)
    summ = {
        "schema": "eo-x1-class-engine-summary/v1",
        "lead_only": True,
        "pre1937_orders": len(rows),
        "by_class": dict(collections.Counter(r["class"] for r in rows).most_common()),
        "by_confidence": dict(collections.Counter(r["confidence"] for r in rows).most_common()),
        "by_type": [{"type": t, "class": taxonomy.TYPE_CLASS.get(t, "unknown"), "rule_id": taxonomy.TYPE_RULE.get(t, ""),
                     "orders": n} for t, n in by_type.most_common()],
        "census_gap_rows": {s: dict(collections.Counter(g["class"] for g in gap if g["gap_source"] == s))
                            for s in ("app_index", "lord_1943_unnumbered")},
        "clusters": csum,
        "clone_status": dict(collections.Counter(m["clone_status"] for m in members)),
        "modern_families_5_plus": len(fams),
        "event_candidates": dict(collections.Counter(e["event_id"] for e in ev_rows)),
        "event_sources": {k: [s["state"] for s in v] for k, v in ev_states.items()},
        "type_rules": {k: v["review_state"] + "|" + v["quote_check"] for k, v in rules.items()},
        "batches": len(batches),
        "batch_rows_by_route": dict(collections.Counter(r["route"] for b in batches for r in b["rows"])),
        "risk_tiered_review": "on (UNAPPROVED by the owner)" if sheets.risk_tiered() else "off (default; not approved by the owner)",
    }
    json.dump(summ, open(out / "SUMMARY.json", "w"), indent=1)
    print(json.dumps({k: summ[k] for k in ("pre1937_orders", "by_class", "by_confidence", "batches", "batch_rows_by_route")}, indent=1))


if __name__ == "__main__":
    main()
