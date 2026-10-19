"""X1 step 5: batch review sheets of up to 50 rows per type or look-alike cluster.

A sheet is a work list, not a decision. Each row says what the machines hold for
the order (type and its evidence, rule, cluster and clone, event candidates,
text, provisional status) and which existing path it takes:

  claim_kit_prepare  the order has a provisional status and a claim-kit dossier:
                     `kit.py prepare` the batch (it accepts 1-50 identities),
                     decide every row in decisions.csv / clauses.csv, `apply`,
                     `batch-check`, independent AI review, then commit accepted
                     lines to research/readiness/claims/<agent>-<date>.jsonl.
  status_first       no provisional status yet: `kit.py history` and the
                     overlay path in jobs/claim-kit/BATCH.md come first.
  text_first         no held text: request the source through FETCH_QUEUE.jsonl.

The judgment columns are left blank for the agent. Review tier is "full" unless
X1_RISK_TIERED_REVIEW=1 is set; the owner has NOT approved risk-tiered review.
"""
import csv, hashlib, json, os

BATCH_MAX = 50
AUDIT_RATE = 0.20
COLUMNS = ["batch_id", "row", "instrument_id", "type", "type_confidence", "type_evidence", "rule_id", "rule_state",
           "cluster_id", "cluster_role", "clone_status", "cloned_clauses", "clone_dropout_reason", "event_candidates",
           "provisional_status", "has_dossier", "text_grade", "route", "review_tier",
           "agent_decision", "agent_reason", "reviewer_decision", "reviewer_reason"]


def risk_tiered():
    return os.environ.get("X1_RISK_TIERED_REVIEW", "0") == "1"


def review_tier(row):
    if not risk_tiered():
        return "full"
    # Experimental, off by default: only clean clones of a cluster get a 20% audit sample.
    if row["clone_status"] != "cloned":
        return "full"
    h = int(hashlib.sha256(row["instrument_id"].encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "audit_sample" if h < AUDIT_RATE else "skip_independent_review_UNAPPROVED"


def build(repo, types, members, cloned, events, rule_state):
    status = {r["instrument_id"]: r["provisional_status"]
              for r in csv.DictReader(open(repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"))}
    dossiers = {"EO:" + p.stem[3:] for p in (repo / "jobs/claim-kit/output/dossiers").glob("EO_*.json")}
    mem = {m["instrument_id"]: m for m in members}
    ncl = {}
    for c in cloned:
        ncl[c["instrument_id"]] = ncl.get(c["instrument_id"], 0) + 1
    ev = {}
    for e in events:
        ev.setdefault(e["instrument_id"], []).append(e["event_id"])

    def row(iid):
        t = types[iid]
        m = mem.get(iid, {})
        st = status.get(iid, "")
        has_d = iid in dossiers
        route = ("claim_kit_prepare" if st and has_d and t["text_path"] else
                 "status_first" if not st else "text_first")
        r = {"instrument_id": iid, "type": t["type"], "type_confidence": t["confidence"],
             "type_evidence": f"{t['evidence_source']}:{t['evidence_match']}"[:80],
             "rule_id": t["rule_id"], "rule_state": rule_state.get(t["rule_id"], ""),
             "cluster_id": m.get("cluster_id", ""), "cluster_role": m.get("role", ""),
             "clone_status": m.get("clone_status", ""), "cloned_clauses": ncl.get(iid, 0),
             "clone_dropout_reason": m.get("dropout_reason", ""), "event_candidates": "|".join(ev.get(iid, [])),
             "provisional_status": st, "has_dossier": "yes" if has_d else "no", "text_grade": t["text_grade"],
             "route": route, "agent_decision": "", "agent_reason": "", "reviewer_decision": "", "reviewer_reason": ""}
        r["review_tier"] = review_tier(r)
        return r

    route_rank = {"claim_kit_prepare": 0, "status_first": 1, "text_first": 2}
    conf_rank = {"high": 0, "medium": 1, "low": 2}
    groups = {}
    for iid, t in types.items():
        if t["class"] in ("spent", "land", "swept") and t["confidence"] in ("high", "medium"):
            groups.setdefault(("type", t["type"]), []).append(iid)
    batches = []
    for (kind, key), ids in sorted(groups.items()):
        rows = sorted((row(i) for i in ids),
                      key=lambda r: (route_rank[r["route"]], r["cluster_id"] == "", r["cluster_id"],
                                     conf_rank.get(r["type_confidence"], 3), r["instrument_id"]))
        for n in range(0, len(rows), BATCH_MAX):
            bid = f"X1-{key}-{n // BATCH_MAX + 1:03d}"
            chunk = rows[n:n + BATCH_MAX]
            for k, r in enumerate(chunk, 1):
                r["batch_id"], r["row"] = bid, k
            batches.append({"batch_id": bid, "kind": kind, "key": key, "rows": chunk})
    return batches


def summary(batches):
    out = []
    for b in batches:
        routes = {}
        for r in b["rows"]:
            routes[r["route"]] = routes.get(r["route"], 0) + 1
        ready = [r["instrument_id"] for r in b["rows"] if r["route"] == "claim_kit_prepare"]
        out.append({"batch_id": b["batch_id"], "type": b["key"], "rows": len(b["rows"]), "routes": routes,
                    "prepare_command": ("python jobs/claim-kit/kit.py prepare " + " ".join(ready) +
                                        " --agent NAME --write research/excavator/RUN/" + b["batch_id"]) if ready else ""})
    return out
