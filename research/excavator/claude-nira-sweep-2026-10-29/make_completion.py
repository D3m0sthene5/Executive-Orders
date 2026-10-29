"""Write a batch's kit.py completion manifest from its exact review records (clerical; no judgment).

Usage:
  python3 -I make_completion.py PACKET APPLIED BLIND_REVIEW.jsonl [AFTER_REVEAL.jsonl|-] KEY.json PUBLICATION_PATH \
      ADJUDICATOR "EO:N=caught|RATIONALE" [...] [--planted-review BLIND.jsonl] [--receipt PATH ...]

--planted-review names the blind review file holding the planted-version verdicts when the genuine versions
were attested in a later exact-version review file (passed as BLIND_REVIEW above).

KEY.json is the coordinator's private control key (kept outside the repository); only hashes from it are
copied. Each control needs one "EO:N=caught|rationale" or "EO:N=missed|rationale" argument: that semantic
judgment is the adjudicator's, recorded verbatim. Members follow decisions.csv; a submitted claim whose blind
review is not "upheld" (or whose control lacks an after-reveal "upheld_after_reveal") is recorded as blocked
with the reviewer's defects, so it is retained but never filed.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def fsha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(REPO).as_posix()


def lines(p):
    out = {}
    for i, l in enumerate(open(p, encoding="utf-8"), 1):
        if l.strip():
            r = json.loads(l)
            out[r.get("claim_sha256") or canon(r)] = (i, r)
    return out


def main(a):
    receipts = []
    planted_review = None
    if "--planted-review" in a:
        i = a.index("--planted-review")
        planted_review = a[i + 1]
        a = a[:i] + a[i + 2:]
    if "--receipt" in a:
        i = a.index("--receipt")
        receipts = a[i + 1:]
        a = a[:i]
    packet, applied, blind, after, keyf, pub, adjudicator, *judg = a
    packet, applied = Path(packet), Path(applied)
    key = json.load(open(keyf))["controls"]
    judgments = {}
    for j in judg:
        iid, rest = j.split("=", 1)
        state, why = rest.split("|", 1)
        judgments[iid] = (state == "caught", why)
    claims = {}
    agents = set()
    cpath = applied / "CLAIMS.proposed.jsonl"
    for i, l in enumerate(open(cpath, encoding="utf-8"), 1):
        c = json.loads(l)
        claims[c["instrument_id"]] = (i, canon(c))
        agents.add((c.get("claim_kit") or {}).get("agent"))
    if len(agents) != 1:
        raise SystemExit("claims name more than one producer agent: %s" % sorted(map(str, agents)))
    agent = agents.pop()
    blind_l = lines(blind)
    after_l = lines(after) if after != "-" else {}
    ref = lambda p, line: {"path": rel(p), "sha256": fsha(p), "line": line}
    pk = {"path": rel(packet / "PACKET.json"), "sha256": fsha(packet / "PACKET.json")}
    controls_by_id = {k["instrument_id"]: k for k in key}
    members = []
    for row in csv.DictReader(open(packet / "decisions.csv", encoding="utf-8-sig")):
        iid = row["instrument_id"]
        if row["outcome"] != "submit" or iid not in claims:
            reason = row.get("unresolved_material_gaps") or row.get("research_rationale") or row["outcome"]
            members.append({"instrument_id": iid, "outcome": "blocked", "reason": reason})
            continue
        line, sha = claims[iid]
        m = {"instrument_id": iid, "outcome": "submit", "claim_sha256": sha, "claim": ref(cpath, line),
             "publication_kind": "whole_case", "packet": pk}
        if iid in controls_by_id:
            hit = after_l.get(sha)
            if hit and hit[1].get("verdict") == "upheld_after_reveal":
                m["after_reveal_review"] = ref(after, hit[0])
            else:
                members.append({"instrument_id": iid, "outcome": "blocked",
                                "reason": "Control order without an upheld after-reveal review of the genuine version."})
                continue
        else:
            hit = blind_l.get(sha)
            if hit and hit[1].get("verdict") == "upheld":
                m["review"] = ref(blind, hit[0])
            else:
                why = json.dumps(hit[1].get("defects"), ensure_ascii=False) if hit else "no review record for this exact version"
                members.append({"instrument_id": iid, "outcome": "blocked",
                                "reason": "Independent review did not uphold this version: " + why})
                continue
        members.append(m)
    controls = []
    outdir = packet / "completion"
    outdir.mkdir(exist_ok=True)
    planted_path = planted_review or blind
    planted_l = lines(planted_path)
    for k in key:
        iid = k["instrument_id"]
        hit = planted_l.get(k["planted"])
        caught, why = judgments[iid]
        adj = {"instrument_id": iid, "planted_claim_sha256": k["planted"], "review": ref(planted_path, hit[0]),
               "adjudicator": adjudicator, "caught": caught, "scoring": "strict", "rationale": why}
        ap = outdir / ("CONTROL_ADJUDICATION_" + iid.replace(":", "_") + ".json")
        ap.write_text(json.dumps(adj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        sp = outdir / ("SEED_RECEIPT_" + iid.replace(":", "_") + ".json")
        controls.append({"instrument_id": iid, "planted_claim_sha256": k["planted"],
                         "seed": {"path": rel(sp), "sha256": fsha(sp)}, "review": ref(planted_path, hit[0]),
                         "adjudication": {"path": rel(ap), "sha256": fsha(ap)}})
    manifest = {"schema": "eo-claim-kit-completion/v1", "agent": agent, "producer_model_family": "Anthropic",
                "independence_requirement": "same_family_separate_context",
                "publication": {"mode": "own_claims", "path": pub}, "members": members, "controls": controls,
                "receipts": [{"path": rel(r), "sha256": fsha(r)} for r in receipts]}
    (outdir / "COMPLETION.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"members": len(members), "submit": sum(m["outcome"] == "submit" for m in members),
                      "blocked": sum(m["outcome"] != "submit" for m in members), "controls": len(controls)}))


if __name__ == "__main__":
    main(sys.argv[1:])
