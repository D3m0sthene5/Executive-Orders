"""Finish one packet's share of an H2 lifecycle review batch under the two-reviewer rule (coordinator; no legal judgment).

usage: python3 -I finish_h2.py BATCH PACKET_NAME APPLIED_VERSION [--publish]
  Scoring rule fixed in advance (as icecore finish2.py): a planted control in this packet is CAUGHT only if BOTH arms'
  blind reviews of its exact planted hash are "rejected" and name a date defect; any miss stops (no completion). A
  genuine claim files only if both arms uphold it (blind "upheld", or "upheld_after_reveal" for a control's genuine
  version). Arm A's records are the manifest's review selectors; arm B's files are pinned receipts, and every member
  arm B did not uphold becomes blocked with arm B's defects. Then kit.py complete runs (publish only when asked).
  Publication path: research/readiness/claims/claude-2026-11-05-herschel-H2-BATCH-PACKET_NAME.jsonl
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2")
REPO = Path("/home/claude/executive-orders")
H = REPO / "research/herschel/H2"
MAKE = REPO / "research/excavator/claude-nira-sweep-2026-10-29/make_completion.py"
ADJ = "claude-coordinator-herschel-H2-2026-11-05"


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def fsha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(batch, pname, version, *flags):
    packet = H / "packets" / pname / "packet"
    applied = packet / version
    rv = packet / "reviews"  # the kit excludes only the packet folder from prior research
    members = {json.loads(l)["instrument_id"] for l in open(applied / "CLAIMS.proposed.jsonl") if l.strip()}
    key = json.loads((S / "keys" / f"{batch}.json").read_text())
    key["controls"] = [k for k in key["controls"] if k["instrument_id"] in members]
    keyf = S / "keys" / f"{batch}-{pname}.json"
    keyf.write_text(json.dumps(key, indent=1))
    arms = {a: {r.get("claim_sha256"): r for r in load(rv / f"BLIND_REVIEW_{a}.kit.jsonl")} for a in "AB"}
    after = {a: {r.get("claim_sha256"): r for r in load(rv / f"AFTER_REVEAL_{a}.kit.jsonl")} for a in "AB"}
    out = packet / "completion"
    out.mkdir(exist_ok=True)
    judg, missed = [], []
    for k in key["controls"]:
        iid = k["instrument_id"]
        seed = {"schema": "eo-claim-kit-control-seed/v1", "instrument_id": iid, "planted_claim_sha256": k["planted"],
                "genuine_claim_sha256": k["genuine"], "seeded_by": ADJ}
        (out / ("SEED_RECEIPT_" + iid.replace(":", "_") + ".json")).write_text(json.dumps(seed, indent=1) + "\n")
        res = {}
        for a in "AB":
            r = arms[a].get(k["planted"])
            text = json.dumps(r.get("defects", []), ensure_ascii=False).lower() if r else ""
            res[a] = bool(r) and r.get("verdict") == "rejected" and any(
                w in text for w in ("date", "first_end", "whole_order_end", "year"))
        caught = res["A"] and res["B"]
        why = ("Planted version moved every end date back three years; both independent blind reviewers (arms A and B) "
               "rejected it and named the date defect." if caught else
               "Planted version moved every end date back three years; arm results %s: not caught by both." % res)
        judg.append(f"{iid}={'caught' if caught else 'missed'}|{why}")
        if not caught:
            missed.append(iid)
    pub = f"research/readiness/claims/claude-2026-11-05-herschel-H2-{batch}-{pname}.jsonl"
    cmd = ["python3", "-I", str(MAKE), str(packet), str(applied), str(rv / "BLIND_REVIEW_A.kit.jsonl"),
           str(rv / "AFTER_REVEAL_A.kit.jsonl") if (rv / "AFTER_REVEAL_A.kit.jsonl").exists() else "-",
           str(keyf), pub, ADJ, *judg]
    receipts = [p for p in (rv / "BLIND_REVIEW_B.kit.jsonl", rv / "AFTER_REVEAL_B.kit.jsonl") if p.exists()]
    if receipts:
        cmd += ["--receipt", *map(str, receipts)]
    print(subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=True).stdout.strip())
    if missed:
        print(json.dumps({"batch": batch, "missed_controls": missed, "action": "production stops; not completed"}))
        return 2
    mpath = out / "COMPLETION.json"
    m = json.loads(mpath.read_text())
    controls = {k["instrument_id"] for k in key["controls"]}
    two = {"two_reviewer_rule": "a claim files only if both independent blind reviewers uphold it", "arm_b_blocked": []}
    for i, mem in enumerate(m["members"]):
        if mem["outcome"] != "submit":
            continue
        sha = mem["claim_sha256"]
        rb = (after if mem["instrument_id"] in controls else arms)["B"].get(sha)
        want = "upheld_after_reveal" if mem["instrument_id"] in controls else "upheld"
        if not rb or rb.get("verdict") != want:
            why = json.dumps(rb.get("defects"), ensure_ascii=False) if rb else "no arm B record for this exact version"
            m["members"][i] = {"instrument_id": mem["instrument_id"], "outcome": "blocked",
                               "reason": "Second independent reviewer (arm B) did not uphold this version: " + why}
            two["arm_b_blocked"].append(mem["instrument_id"])
    (out / "TWO_REVIEWER_RULE.json").write_text(json.dumps(two, indent=1) + "\n")
    m["receipts"].append({"path": str((out / "TWO_REVIEWER_RULE.json").relative_to(REPO)),
                          "sha256": fsha(out / "TWO_REVIEWER_RULE.json")})
    mpath.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n")
    if "--manifest-only" in flags:
        print(json.dumps(two), "manifest only:", mpath)
        return 0
    n = 1
    while (packet / f"complete-v{n}").exists():
        n += 1
    ccmd = ["python3", "jobs/claim-kit/kit.py", "complete", str(mpath), "--write", str(packet / f"complete-v{n}")] + \
        (["--publish"] if "--publish" in flags else [])
    p = subprocess.run(ccmd, cwd=REPO, capture_output=True, text=True)
    (packet / f"COMPLETE_v{n}.log").write_text(p.stdout + "\n" + p.stderr)
    print(json.dumps(two), p.stdout[-1500:], p.stderr[-800:], "exit", p.returncode)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
