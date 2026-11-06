"""Finish the yes or noA packet after the rl2 control round, under the two-reviewer rule (coordinator; no legal judgment).

usage: python3 -I finish_rl2.py PACKET_NAME APPLIED_VERSION [--publish]
  Same fixed scoring and two-reviewer rule as finish_h2.py. Review selectors (arm A): the rl1 blind records
  (reviews/BLIND_REVIEW_A.kit.jsonl) plus the rl2 control-round blind records (reviews/rl2/BLIND_REVIEW_A.jsonl);
  the genuine version of the planted control is selected by reviews/rl2/AFTER_REVEAL_A.jsonl. Arm B's matching files
  are pinned receipts and every member arm B did not uphold is blocked. Control key: scratch keys/rl2<PACKET_NAME>.json.
  Publication: research/readiness/claims/claude-2026-11-05-herschel-H2-rl2-PACKET_NAME.jsonl
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


def load(*ps):
    out = {}
    for p in ps:
        if Path(p).exists():
            for l in open(p, encoding="utf-8"):
                if l.strip():
                    r = json.loads(l); out[r.get("claim_sha256")] = r
    return out


def fsha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(pname, version, *flags):
    packet = H / "packets" / pname / "packet"
    applied = packet / version
    rv = packet / "reviews"
    blind = {a: [rv / f"BLIND_REVIEW_{a}.kit.jsonl", rv / "rl2" / f"BLIND_REVIEW_{a}.jsonl"] for a in "AB"}
    after = {a: rv / "rl2" / f"AFTER_REVEAL_{a}.jsonl" for a in "AB"}
    keyf = S / "keys" / f"rl2{pname}.json"
    key = json.loads(keyf.read_text())
    arms = {a: load(*blind[a]) for a in "AB"}
    aft = {a: load(after[a]) for a in "AB"}
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
            res[a] = bool(r) and r.get("verdict") == "rejected" and any(w in text for w in ("date", "first_end", "whole_order_end", "year"))
        caught = res["A"] and res["B"]
        why = ("Planted version moved every end date back three years; both independent blind reviewers (arms A and B) "
               "rejected it and named the date defect." if caught else "Planted version not caught by both arms: %s." % res)
        judg.append(f"{iid}={'caught' if caught else 'missed'}|{why}")
        if not caught:
            missed.append(iid)
    pub = f"research/readiness/claims/claude-2026-11-05-herschel-H2-rl2-{pname}.jsonl"
    cmd = ["python3", "-I", str(MAKE), str(packet), str(applied), ",".join(str(p) for p in blind["A"] if p.exists()),
           str(after["A"]), str(keyf), pub, ADJ, *judg, "--planted-review", str(blind["A"][1]),
           "--receipt", *[str(p) for p in blind["B"] + [after["B"]] if p.exists()]]
    print(subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=True).stdout.strip())
    if missed:
        print(json.dumps({"missed_controls": missed})); return 2
    mpath = out / "COMPLETION.json"
    m = json.loads(mpath.read_text())
    controls = {k["instrument_id"] for k in key["controls"]}
    two = {"two_reviewer_rule": "a claim files only if both independent blind reviewers uphold it", "arm_b_blocked": []}
    for i, mem in enumerate(m["members"]):
        if mem["outcome"] != "submit":
            continue
        rb = (aft if mem["instrument_id"] in controls else arms)["B"].get(mem["claim_sha256"])
        want = "upheld_after_reveal" if mem["instrument_id"] in controls else "upheld"
        if not rb or rb.get("verdict") != want:
            m["members"][i] = {"instrument_id": mem["instrument_id"], "outcome": "blocked",
                               "reason": "Second independent reviewer (arm B) did not uphold this version: " +
                                         (json.dumps(rb.get("defects"), ensure_ascii=False) if rb else "no arm B record")}
            two["arm_b_blocked"].append(mem["instrument_id"])
    (out / "TWO_REVIEWER_RULE.json").write_text(json.dumps(two, indent=1) + "\n")
    m["receipts"].append({"path": str((out / "TWO_REVIEWER_RULE.json").relative_to(REPO)), "sha256": fsha(out / "TWO_REVIEWER_RULE.json")})
    mpath.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n")
    n = 1
    while (packet / f"complete-v{n}").exists():
        n += 1
    p = subprocess.run(["python3", "jobs/claim-kit/kit.py", "complete", str(mpath), "--write", str(packet / f"complete-v{n}")] +
                       (["--publish"] if "--publish" in flags else []), cwd=REPO, capture_output=True, text=True)
    (packet / f"COMPLETE_v{n}.log").write_text(p.stdout + "\n" + p.stderr)
    print(json.dumps(two), p.stdout[-1200:], p.stderr[-600:], "exit", p.returncode)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
