"""Finish one ice-core batch under the two-reviewer rule (coordinator; scoring rule fixed in advance, no legal judgment).

usage: python3 -I finish2.py BATCH APPLIED_VERSION [--publish]
  A planted control is CAUGHT only if BOTH arms' blind reviews of its exact planted hash are "rejected" and name a
  date defect. Any miss stops the batch (no completion). A genuine claim files only if both arms uphold it: blind
  "upheld" for ordinary claims, "upheld_after_reveal" for genuine control versions. Arm A's records are the
  manifest's review selectors; arm B's file is pinned as a receipt and every member that arm B did not uphold is
  turned into a blocked member carrying arm B's defects. Then kit.py complete runs (publish only when asked).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/icecore")
REPO = Path("/home/claude/executive-orders")
RUN = REPO / "research/excavator/claude-icecore-2026-11-05"
MAKE = REPO / "research/excavator/claude-nira-sweep-2026-10-29/make_completion.py"


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def fsha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(batch, version, *flags):
    packet = RUN / batch / "packet"
    applied = packet / version
    rv = packet / "reviews"
    key = json.loads((S / "moon-keys" / f"{batch}.json").read_text())
    arms = {a: {r.get("claim_sha256"): r for r in load(rv / f"BLIND_REVIEW_{a}.jsonl")} for a in "AB"}
    after = {a: {r.get("claim_sha256"): r for r in load(rv / f"AFTER_REVEAL_{a}.jsonl")} for a in "AB"}
    out = packet / "completion"
    out.mkdir(exist_ok=True)
    judg, missed = [], []
    for k in key["controls"]:
        iid = k["instrument_id"]
        seed = {"schema": "eo-claim-kit-control-seed/v1", "instrument_id": iid, "planted_claim_sha256": k["planted"],
                "genuine_claim_sha256": k["genuine"], "seeded_by": "claude-coordinator-icecore-2026-11-05"}
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
    pub = f"research/readiness/claims/claude-2026-11-05-icecore-{batch}.jsonl"
    cmd = ["python3", "-I", str(MAKE), str(packet), str(applied), str(rv / "BLIND_REVIEW_A.jsonl"),
           str(rv / "AFTER_REVEAL_A.jsonl") if (rv / "AFTER_REVEAL_A.jsonl").exists() else "-",
           str(S / "moon-keys" / f"{batch}.json"), pub, "claude-coordinator-icecore-2026-11-05", *judg]
    receipts = [p for p in (rv / "BLIND_REVIEW_B.jsonl", rv / "AFTER_REVEAL_B.jsonl") if p.exists()]
    if receipts:
        cmd += ["--receipt", *map(str, receipts)]
    print(subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=True).stdout.strip())
    if missed:
        print(json.dumps({"batch": batch, "missed_controls": missed, "action": "probe stops; not completed"}))
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
