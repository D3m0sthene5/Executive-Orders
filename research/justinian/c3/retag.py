"""Justinian C3: re-tag claims filed under the 2026-10-21 reading as schema v2 (owner ruling R3).

R3 (2026-11-06): the 2026-10-28 ruling (evidence-not-convenience, point 3: "a later general rule,
rewrite or revocation ends a command only where something shows it extinguished that command; its
date is not a default end") governs where it conflicts with the 2026-10-21 report-deadline,
unnamed-instruments and eo-10449 rulings. Claims filed under the 10-21 reading are NOT re-researched:
they are re-tagged first_cause: unresolved, date_kind: not_later_than, with the instrument that was
recorded as the end moved to formal_disposition. The v1 line is kept (claims files are append-only).

Selection (legal judgment, Justinian): a claim is "filed under the 10-21 reading" when its own text
applies one of those rulings: it records a report-relative provision as "functionally spent", a
"disclosed earlier candidate" end under the unnamed-instruments ruling, a board "never constituted",
or cites one of the three ruling files. A claim whose end is an express revocation naming an order
the evidence shows was still operative (for example EO 13988 revoked by EO 14148) is not under the
10-21 reading and is listed, not re-tagged (NOT_RETAGGED.csv).

Clauses whose recorded first end is the whole-order end's instrument and date become not_later_than /
unresolved. A clause with a different, earlier recorded end keeps it as exact with a first_cause read
from its mechanism text; if the text maps to no cause, the clause is also bounded (conservative).

Usage: python3 -I research/justinian/c3/retag.py REPO_ROOT READINESS_BY_ORDER.csv OUTDIR [GATE_DIR]
"""
import csv
import glob
import hashlib
import json
import os
import re
import sys

MARKERS = re.compile(r"functionally spent|2026-10-21-(report-deadline|unnamed-instruments|eo-10449)|"
                     r"earlier candidate end|never constituted|disclosed earlier candidate", re.I)
CLEANUP = {"EO:12553", "EO:14148", "EO:11490", "EO:12379", "EO:12076", "EO:11708", "EO:9830"}


def canonical(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(v):
    return hashlib.sha256(canonical(v).encode("utf-8")).hexdigest()


def mechanism(text):
    t = (text or "").lower().replace("_", " ")
    for pat, value in ((r"supersed", "express_supersession"), (r"revok|revoc|rescind|rescission", "express_revocation"),
                       (r"amend", "amendment"), (r"abolish", "body_abolished"),
                       (r"expir|own terms|own end date|by its terms|terminat(e|ed|ion) (on|by) its", "expiration_by_own_terms"),
                       (r"court|unconstitutional|invalid", "judicial_invalidation"),
                       (r"statut|act of congress|joint resolution|s\. ?j\. ?res|pub(lic)? ?(law|res)", "statutory_termination")):
        if re.search(pat, t):
            return value
    return "other"


def cause(clause_end):
    t = (str(clause_end.get("mechanism", "")) + " " + str(clause_end.get("actor", ""))).lower().replace("_", " ")
    for pat, value in ((r"own terms|expir|own end date|by its terms|fixed date|until event", "under_original_terms"),
                       (r"court|unconstitutional|schechter", "judicial"),
                       (r"statut|act of congress|joint resolution|s\. ?j\. ?res|pub(lic)? ?(law|res)|stat\.", "legislative"),
                       (r"regulation|cfr", "regulatory"),
                       (r"\beo[: ]|executive order|revok|revoc|supersed|rescind|president", "later_presidential")):
        if re.search(pat, t):
            return value
    return None


def v2_end(old, bounded, first_cause=None):
    end = {"actor": old.get("actor"), "source": old.get("source"), "mechanism": mechanism(old.get("mechanism")),
           "mechanism_note": str(old.get("mechanism") or "")}
    if bounded:
        end.update(date_kind="not_later_than", date=old.get("date"), first_cause="unresolved")
    else:
        end.update(date_kind="exact", date=old.get("date"), first_cause=first_cause)
    return end


def retag(claim, v1_sha):
    whole = claim["whole_order_end"]
    new = json.loads(json.dumps(claim))
    new["schema"] = "eo-lifecycle-claim/v2"
    for clause in new["operative_clauses"]:
        if clause.get("state_at_cutoff") not in ("terminated", "never_activated"):
            continue
        old = clause["first_end"]
        same = old.get("date") == whole.get("date") and old.get("actor") == whole.get("actor")
        c = None if same else cause(old)
        clause["first_end"] = v2_end(old, bounded=same or c is None, first_cause=c)
    latest = max(cl["first_end"]["date"] for cl in new["operative_clauses"]
                 if cl.get("state_at_cutoff") in ("terminated", "never_activated"))
    new["whole_order_end"] = v2_end(dict(whole, date=latest), bounded=True)
    new["formal_disposition"] = {"instrument": whole.get("actor"), "date": whole.get("date"),
                                 "source": whole.get("source")}
    new["retag"] = {"ruling": "D-20261106-justinian-r3", "by": "Justinian (claude), 2026-11-06",
                    "v1_claim_sha256": v1_sha, "researched_again": False,
                    "note": "Filed under the 2026-10-21 reading; the 2026-10-28 ruling point 3 governs (R3). The "
                            "recorded end instrument is the formal disposition; the first end is unresolved and bounded "
                            "no later than it. Not re-researched."}
    return new


def main(root, readiness, outdir, gate_dir=None):
    ready = {r["instrument_id"] for r in csv.DictReader(open(readiness, encoding="utf-8"))
             if r["ready_for_human_review"] == "yes"}
    claims = {}
    for f in sorted(glob.glob(os.path.join(root, "research/readiness/claims/*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                c = json.loads(line)
            except ValueError:
                continue
            if isinstance(c, dict) and isinstance(c.get("instrument_id"), str):
                claims[c["instrument_id"]] = c
    sys.path.insert(0, gate_dir or os.path.join(root, "research/stage19/code"))
    import claim_gate
    out, skipped, report = [], [], []
    for i in sorted(claims, key=lambda x: (len(x), x)):
        c = claims[i]
        if c.get("whole_order_status") != "no" or c.get("schema") != "eo-lifecycle-claim/v1":
            continue
        text = canonical(c)
        marker = sorted({m.group(0).lower() for m in MARKERS.finditer(text)})
        actor = (c.get("whole_order_end") or {}).get("actor", "")
        if not marker:
            if actor in CLEANUP and i in ready:
                skipped.append({"instrument_id": i, "whole_end_actor": actor, "whole_end_date": c["whole_order_end"].get("date"),
                                "reason": "express revocation naming the order; no 10-21 reading applied in the claim"})
            continue
        new = retag(c, claim_gate.claim_sha(c))
        errors = claim_gate.validate_claim(new, expected_status="no")
        report.append({"instrument_id": i, "ready_before": "yes" if i in ready else "no", "whole_end_actor": actor,
                       "formal_disposition_date": new["formal_disposition"]["date"], "markers": "|".join(marker),
                       "bounded_clauses": sum(1 for cl in new["operative_clauses"]
                                              if (cl.get("first_end") or {}).get("date_kind") == "not_later_than"),
                       "exact_clauses_kept": sum(1 for cl in new["operative_clauses"]
                                                 if (cl.get("first_end") or {}).get("date_kind") == "exact"),
                       "v1_claim_sha256": claim_gate.claim_sha(c), "v2_claim_sha256": claim_gate.claim_sha(new),
                       "v2_gate_errors": "|".join(errors)})
        if not errors:
            out.append(new)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "justinian-2026-11-06-r3-retag.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        fh.writelines(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in out)
    for name, rows in (("RETAGGED.csv", report), ("NOT_RETAGGED.csv", skipped)):
        with open(os.path.join(outdir, name), "w", encoding="utf-8", newline="") as fh:
            if rows:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
    print(json.dumps({"retagged": len(out), "gate_failures": sum(1 for r in report if r["v2_gate_errors"]),
                      "retagged_ready_before": sum(1 for r in report if r["ready_before"] == "yes" and not r["v2_gate_errors"]),
                      "cleanup_actor_not_retagged_ready": len(skipped)}))


if __name__ == "__main__":
    main(*sys.argv[1:5])
