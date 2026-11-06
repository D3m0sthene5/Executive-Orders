"""Finish one Herschel H5 batch reviewed by two independent blind arms (coordinator; scoring rule fixed in advance).

usage: python3 -I finish_pair.py BATCH [--publish]
  Reads PACKET/reviews/BLIND_REVIEW_{A,B}.jsonl and AFTER_REVEAL_{A,B}.jsonl. A planted control is CAUGHT only if
  BOTH arms rejected its exact planted hash and named a date defect (field or text mentions date, first_end,
  whole_order_end or year). Any miss stops the batch before completion. Builds the completion manifest with the
  existing make_completion.py from arm A's records, then applies the both-uphold rule: a submitted member files only
  if arm B also upheld the exact same claim hash (blind, or upheld_after_reveal for a genuine control); otherwise it
  becomes a blocked member whose reason quotes arm B's defects. Arm B's review files are pinned as receipts.
  Then runs kit.py complete into a new complete-vN (with --publish only when asked).
"""
import hashlib
import os
import json
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5")
REPO = Path("/home/claude/executive-orders")
RUN = REPO / "research/herschel/H5/packets"
MAKE = REPO / "research/excavator/claude-nira-sweep-2026-10-29/make_completion.py"
ADJ = "claude-coordinator-herschel-H5-2026-11-05"


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def fsha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def caught(rec):
    if not rec or rec.get("verdict") != "rejected":
        return False
    text = json.dumps(rec.get("defects", []), ensure_ascii=False).lower()
    return any(w in text for w in ("date", "first_end", "whole_order_end", "year"))


def main(batch, *flags):
    packet = RUN / batch / os.environ.get("PK", "packet")
    applied = sorted(packet.glob("applied-v*"), key=lambda p: int(p.name.split("-v")[1]))[-1]
    if (packet / "APPLIED_FOR_REVIEW").exists():
        applied = packet / (packet / "APPLIED_FOR_REVIEW").read_text().strip()
    key = json.loads((S / "moon-keys" / f"{batch}.json").read_text())
    rv = packet / "reviews"
    blind = {a: {r["claim_sha256"]: r for r in load(rv / f"BLIND_REVIEW_{a}.jsonl")} for a in "AB"}
    after = {a: {r["claim_sha256"]: r for r in load(rv / f"AFTER_REVEAL_{a}.jsonl")} for a in "AB"}
    out = packet / "completion"
    out.mkdir(exist_ok=True)
    judg, missed = [], []
    for k in key["controls"]:
        iid = k["instrument_id"]
        seed = {"schema": "eo-claim-kit-control-seed/v1", "instrument_id": iid, "planted_claim_sha256": k["planted"],
                "genuine_claim_sha256": k["genuine"], "seeded_by": ADJ}
        (out / ("SEED_RECEIPT_" + iid.replace(":", "_") + ".json")).write_text(json.dumps(seed, indent=1) + "\n")
        ok = {a: caught(blind[a].get(k["planted"])) for a in "AB"}
        why = ("Planted version moved every end date back three years; both independent blind arms (A and B) rejected "
               "that exact planted hash and named the date defect." if all(ok.values()) else
               "Planted version moved every end date back three years; arm(s) %s did not reject it for the date defect."
               % ",".join(a for a in "AB" if not ok[a]))
        judg.append(f"{iid}={'caught' if all(ok.values()) else 'missed'}|{why}")
        if not all(ok.values()):
            missed.append(iid)
    if missed:
        print(json.dumps({"batch": batch, "missed_controls": missed, "action": "STOP: not completed"}))
        return 2
    pub = f"research/readiness/claims/claude-2026-11-05-herschel-H5-{batch}.jsonl"
    receipts = [str(rv / f) for f in ("BLIND_REVIEW_B.jsonl", "AFTER_REVEAL_B.jsonl") if (rv / f).exists()]
    for extra in ("REAPPLY.json",):
        if (packet / extra).exists():
            receipts.append(str(packet / extra))
    cmd = ["python3", "-I", str(MAKE), str(packet), str(applied), str(rv / "BLIND_REVIEW_A.jsonl"),
           str(rv / "AFTER_REVEAL_A.jsonl") if (rv / "AFTER_REVEAL_A.jsonl").exists() else "-",
           str(S / "moon-keys" / f"{batch}.json"), pub, ADJ, *judg, "--receipt", *receipts]
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[-600:])
    mpath = out / "COMPLETION.json"
    m = json.loads(mpath.read_text())
    ctrl = {k["instrument_id"] for k in key["controls"]}
    demoted = []
    for i, mem in enumerate(m["members"]):
        if mem["outcome"] != "submit":
            continue
        sha = mem["claim_sha256"]
        rec = (after["B"] if mem["instrument_id"] in ctrl else blind["B"]).get(sha)
        need = "upheld_after_reveal" if mem["instrument_id"] in ctrl else "upheld"
        if not rec or rec.get("verdict") != need:
            why = json.dumps(rec.get("defects"), ensure_ascii=False) if rec else "no arm B record for this exact version"
            m["members"][i] = {"instrument_id": mem["instrument_id"], "outcome": "blocked",
                               "reason": "Second independent blind reviewer (arm B) did not uphold this exact version: " + why}
            demoted.append(mem["instrument_id"])
    if os.environ.get("REPLACEMENT"):
        # Filed-claim corrections whose canonical filename would be shadowed by the existing claim file go to an
        # isolated owner-reviewable replacement proposal outside research/readiness (kit COMPLETION.md).
        m["publication"] = {"mode": "replacement_proposal",
                            "path": f"research/herschel/H5/{batch}-REPLACEMENT_PROPOSAL.jsonl"}
    mpath.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"batch": batch, "submit_after_pair_rule": sum(x["outcome"] == "submit" for x in m["members"]),
                      "demoted_by_arm_B": demoted}))
    n = 1
    while (packet / f"complete-v{n}").exists():
        n += 1
    ccmd = ["python3", "jobs/claim-kit/kit.py", "complete", str(mpath), "--write", str(packet / f"complete-v{n}")] + \
        (["--publish"] if "--publish" in flags else [])
    p = subprocess.run(ccmd, cwd=REPO, capture_output=True, text=True)
    (packet / f"COMPLETE_v{n}.log").write_text(p.stdout + "\n" + p.stderr)
    print(p.stdout[-1500:], p.stderr[-800:], "exit", p.returncode)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
