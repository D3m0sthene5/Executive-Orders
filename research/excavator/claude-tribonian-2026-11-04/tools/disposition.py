"""Tribonian wave disposition from native receipts (coordinator tool; no legal judgment).

usage: python3 -I disposition.py OUT.json OUT.csv
For each batch folder it reads the newest packet/complete-v*/TALLY.json (all earlier versions stay on disk and are
listed), the claims file under research/readiness/claims, and the review files, and records: attempted, eligible,
blocked (with each blocked order's first reason line), controls and whether caught, after-reveal verdicts, the
claims file line count, and the packet state when no completion exists (prepared-not-started, stale, in-progress).
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/claude/executive-orders")
RUN = ROOT / "research/excavator/claude-tribonian-2026-11-04"
CLAIMS = ROOT / "research/readiness/claims"


def vnum(p):
    m = re.search(r"-v(\d+)", p.name)
    return int(m.group(1)) if m else 0


def jsonl(p):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()] if p.exists() else []


def batch_row(b):
    pk = b / "packet"
    row = {"batch": b.name, "packet": str(pk.relative_to(ROOT)) if pk.exists() else None}
    stale = sorted(x.name for x in b.glob("packet-stale-v*"))
    row["stale_packets_preserved"] = stale
    if not pk.exists():
        row["state"] = "no_packet"
        return row
    prep = json.loads((pk / "PREPARE.json").read_text()) if (pk / "PREPARE.json").exists() else {}
    ids = prep.get("instrument_ids") or prep.get("ids") or []
    row["orders_prepared"] = len(ids) if ids else None
    applied = sorted(pk.glob("applied-v*"), key=vnum)
    completes = sorted(pk.glob("complete-v*"), key=vnum)
    row["applied_versions"] = [a.name for a in applied]
    row["complete_versions"] = [c.name for c in completes]
    claims_file = CLAIMS / f"claude-2026-11-04-tribonian-{b.name}.jsonl"
    row["claims_file"] = str(claims_file.relative_to(ROOT)) if claims_file.exists() else None
    row["claims_filed"] = len(jsonl(claims_file))
    blind = jsonl(pk / "reviews/BLIND_REVIEW.jsonl")
    row["blind_review_verdicts"] = {}
    for r in blind:
        row["blind_review_verdicts"][r.get("verdict")] = row["blind_review_verdicts"].get(r.get("verdict"), 0) + 1
    row["after_reveal"] = {r.get("instrument_id"): r.get("verdict") for r in jsonl(pk / "reviews/AFTER_REVEAL.jsonl")}
    row["blind_review_amended"] = (pk / "reviews/BLIND_REVIEW_AMENDED.jsonl").exists()
    tally = None
    for c in reversed(completes):
        if (c / "TALLY.json").exists():
            tally = json.loads((c / "TALLY.json").read_text())
            row["tally_from"] = c.name
            break
    if tally:
        row["state"] = "completed"
        row["attempted"] = tally.get("attempted")
        row["eligible"] = tally.get("counts", {}).get("eligible")
        row["blocked"] = tally.get("counts", {}).get("blocked")
        row["claims_published_by_completion"] = tally.get("claims_published")
        row["controls"] = [{"instrument_id": c.get("instrument_id"), "caught": c.get("caught")}
                           for c in tally.get("controls", [])]
        reasons = []
        for o in tally.get("outcomes", []):
            if o.get("outcome") != "published" and o.get("outcome") != "eligible":
                r = o.get("reason") or ""
                try:
                    r = json.loads(r)
                    r = r[0] if isinstance(r, list) and r else r
                except (ValueError, TypeError):
                    pass
                reasons.append({"instrument_id": o.get("instrument_id"), "outcome": o.get("outcome"),
                                "reason": str(r)[:300]})
        row["not_filed"] = reasons
    elif applied:
        row["state"] = "applied_not_completed"
    elif (pk / "decisions.csv").exists() and (pk / "PRODUCER_REPORT.md").exists():
        row["state"] = "produced_not_applied"
    else:
        row["state"] = "prepared_not_started"
    return row


def main():
    rows = [batch_row(b) for b in sorted(RUN.iterdir())
            if b.is_dir() and re.fullmatch(r"[a-z]\d\d", b.name)]
    out = {"schema": "tribonian-disposition/v1", "batches": rows,
           "totals": {"claims_filed": sum(r.get("claims_filed", 0) for r in rows),
                      "batches": len(rows)}}
    Path(sys.argv[1]).write_text(json.dumps(out, indent=2) + "\n")
    keys = ["batch", "state", "orders_prepared", "attempted", "eligible", "blocked", "claims_filed",
            "tally_from", "complete_versions", "stale_packets_preserved"]
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.DictWriter(f, keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(r[k]) if isinstance(r.get(k), list) else r.get(k)) for k in keys})
    print(json.dumps(out["totals"]))


if __name__ == "__main__":
    main()
