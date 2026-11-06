"""Gratian: the ranked NEXT-DOSSIER queue, from the ablation's final tracker rows (offline, no tokens).

Tier 1 is every order with a claim and exactly one open step, plus orders whose steps are all done but whose claim
still carries a claim-level error: the population Bentham's production.one_step_away action reads. Each row names
the single blocker and what closes it (a machine rerun, a producer correction, a reviewer reconciliation or a
person), cheapest first. Tier 2 is the orders that enter the claim-ready group only when PR #164 registers Mabillon's
held printings: their text and counterevidence steps are done and they need a drafted claim.

Writes NEXT_DOSSIER.csv (both tiers, with reasons) and NEXT_DOSSIER.txt (tier 1 ids in rank order, one per line,
the format of jobs/bentham/output/strata/production.one_step_away.txt). Nothing here is a status or a review.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FINAL = HERE / "ablation/FINAL_ORDERS.csv"
CONTRIB = HERE / "ablation/CONTRIBUTIONS.json"
CHECKER = ROOT / "jobs/claim-checker/output/PER_CLAIM.json"
PTOLEMY = ROOT / "jobs/ptolemy-custody/output/SOURCES.jsonl"
COST = {"machine": 1, "producer": 2, "reviewer": 3, "person": 4}


def claims_by_id():
    out = {}
    for path in sorted((ROOT / "research/readiness/claims").glob("*.jsonl")):
        for line in path.read_text("utf-8").splitlines():
            if line.strip():
                c = json.loads(line)
                if isinstance(c.get("instrument_id"), str):
                    out[c["instrument_id"]] = c
    return out


def field(obj, path):
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if part.startswith("["):
            obj = obj[int(part[1:-1])] if isinstance(obj, list) and int(part[1:-1]) < len(obj) else None
        else:
            obj = obj.get(part) if isinstance(obj, dict) else None
        if obj is None:
            return None
    return obj


def closer(o, checks, claims, kept):
    b = o["blockers"].split("|")[0] if o["blockers"] else ""
    code = b.split(":", 1)[0]
    if not o["open_steps"]:
        return ("producer", "claim-level error " + o["claim_record_errors"],
                "Close or disclose the listed material gaps in the claim (or record the step in EXHAUSTED.jsonl), then rerun claim-checker")
    if code == "CLAIM_CHECK_FAILED":
        chk = checks.get(o["instrument_id"], {})
        unv = [u for u in chk.get("unverified", []) if "custody_record_only" in u]
        if unv and not chk.get("failures"):
            refs = [field(claims.get(o["instrument_id"], {}), u.split("@", 1)[1]) or {} for u in unv]
            shas = {r.get("sha256") for r in refs if isinstance(r, dict)}
            if shas and shas <= kept:
                return ("machine", b, "Ptolemy now holds the cited bytes; the next claim-checker run passes the step (no tokens)")
            urls = sorted({r.get("url", "") for r in refs if isinstance(r, dict) and r.get("sha256") not in kept})
            return ("machine", b, "Add the cited source to Ptolemy's request list or FETCH_QUEUE.jsonl, then rerun claim-checker: "
                    + "; ".join(urls))
        return ("producer", b, "Producer corrects the failing quotations against the held text (kit.py prepare "
                "--replacement-proposal), then fresh review: " + ", ".join(chk.get("failures", [])[:3]))
    if code == "CLAIM_INCOMPLETE":
        return ("producer", b, "Producer research of the open first-end or current basis named in the claim's material gaps; "
                "if searched to the end, an EXHAUSTED.jsonl line with the gap disclosed (machine_exhausted tier)")
    if code == "OPEN_SOURCE_AUDIT":
        return ("reviewer", b, "Reviewer reconciles the open source audit (research/readiness/SOURCE_AUDIT_HOLDS.jsonl) "
                "with the exact claim; a corrected claim needs a fresh audit")
    if code == "QUARANTINED_RELATIONSHIP_CONFLICT":
        return ("person", b, "A person settles the quarantined relationship in the Stage 19 causal queue")
    if code == "OPUS_MEDIA_REFETCH_NEEDED":
        return ("machine", b, "Queue the Opus file (left out of the release as too large) in FETCH_QUEUE.jsonl by its recorded hash; neither source-ladder nor Ptolemy holds or has requested it")
    if code.startswith("OPUS_MEDIA"):
        return ("producer", b, "Agent settles the remaining Opus media matches (opus-media-match MATCHES.csv)")
    return ("producer", b, "See blockers")


def main():
    final = [r for r in csv.DictReader(open(FINAL, encoding="utf-8")) if r["ready_for_human_review"] != "yes"]
    checks = {c["instrument_id"]: c for c in json.loads(CHECKER.read_text("utf-8"))["claims"]
              if c.get("effective_for_tracker")}
    claims = claims_by_id()
    kept = {json.loads(l)["sha256"] for l in PTOLEMY.read_text("utf-8").splitlines() if l.strip()}
    tier1 = []
    for o in final:
        open_ = [s for s in o["open_steps"].split("|") if s]
        if o["claim_present"] == "yes" and len(open_) <= 1:
            kind, blocker, step = closer(o, checks, claims, kept)
            tier1.append({"tier": 1, "instrument_id": o["instrument_id"], "provisional_status": o["provisional_status"],
                          "open_step": o["open_steps"] or "(none; claim-level error)", "blocker": blocker,
                          "closer_kind": kind, "closes_it": step})
    tier1.sort(key=lambda r: (COST[r["closer_kind"]], int(re.sub(r"\D.*", "", r["instrument_id"][3:]) or 0),
                              r["instrument_id"]))
    contrib = json.loads(CONTRIB.read_text("utf-8"))
    gained = contrib.get("mabillon", {}).get("claim_ready_stratum", {}).get("gained", [])
    status = {o["instrument_id"]: o["provisional_status"] for o in final}
    tier2 = [{"tier": 2, "instrument_id": i, "provisional_status": status.get(i, ""),
              "open_step": "clause_inventory|ending_or_current_basis|savings_residuals",
              "blocker": "NO_CLAIM_YET", "closer_kind": "producer",
              "closes_it": "Enters production.claim_ready when PR #164 registers Mabillon's held printings; draft the claim from jobs/claim-drafts"}
             for i in gained]
    rows = [dict(r, rank=n) for n, r in enumerate(tier1 + tier2, 1)]
    fields = ["rank", "tier", "instrument_id", "provisional_status", "open_step", "blocker", "closer_kind", "closes_it"]
    with open(HERE / "NEXT_DOSSIER.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (HERE / "NEXT_DOSSIER.txt").write_text("".join(r["instrument_id"] + "\n" for r in tier1), encoding="utf-8")
    counts = {}
    for r in tier1:
        counts[r["closer_kind"]] = counts.get(r["closer_kind"], 0) + 1
    print(json.dumps({"tier1": len(tier1), "tier1_by_closer": counts, "tier2": len(tier2)}))


if __name__ == "__main__":
    main()
