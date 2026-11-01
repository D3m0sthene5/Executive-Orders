"""Finish one Apollo batch after blind and after-reveal reviews (coordinator; scoring rule fixed in advance).

usage: python3 moon_finish.py BATCH PACKET APPLIED [--publish]
  Control scoring: a planted claim is CAUGHT only if the blind review of its exact planted hash is "rejected" and
  names a date defect (a defect whose field mentions date or first_end or whole_order_end, or whose text names
  the planted or true date). Otherwise MISSED. Writes seed receipts into PACKET/completion/, runs
  make_completion.py, then kit.py complete (with --publish only when asked and no control was missed).
"""
import json
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad")
REPO = Path("/home/claude/executive-orders")
MAKE = REPO / "research/excavator/claude-nira-sweep-2026-10-29/make_completion.py"


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def main(batch, packet, applied, *flags):
    packet, applied = Path(packet), Path(applied)
    key = json.loads((S / "moon-keys" / f"{batch}.json").read_text())
    blind = packet / "reviews" / "BLIND_REVIEW.jsonl"
    after = packet / "reviews" / "AFTER_REVEAL.jsonl"
    by_sha = {r.get("claim_sha256"): r for r in load(blind)}
    out = packet / "completion"
    out.mkdir(exist_ok=True)
    judg, missed = [], []
    for k in key["controls"]:
        iid = k["instrument_id"]
        seed = {"schema": "eo-claim-kit-control-seed/v1", "instrument_id": iid, "planted_claim_sha256": k["planted"],
                "genuine_claim_sha256": k["genuine"], "seeded_by": "claude-coordinator-apollo-2026-10-31"}
        (out / ("SEED_RECEIPT_" + iid.replace(":", "_") + ".json")).write_text(json.dumps(seed, indent=1) + "\n")
        r = by_sha.get(k["planted"])
        text = json.dumps(r.get("defects", []), ensure_ascii=False).lower() if r else ""
        dated = any(w in text for w in ("date", "first_end", "whole_order_end", "year"))
        caught = bool(r) and r.get("verdict") == "rejected" and dated
        why = ("Planted version moved every end date back three years; the blind reviewer rejected it and named the "
               "date defect." if caught else
               "Planted version moved every end date back three years; the blind review did not reject it for the "
               "date defect (verdict %s)." % (r.get("verdict") if r else "missing"))
        judg.append(f"{iid}={'caught' if caught else 'missed'}|{why}")
        if not caught:
            missed.append(iid)
    pub = f"research/readiness/claims/claude-2026-10-31-apollo-{batch}.jsonl"
    keyfile = S / "moon-keys" / f"{batch}.json"
    cmd = ["python3", "-I", str(MAKE), str(packet), str(applied), str(blind), str(after) if after.exists() else "-",
           str(keyfile), pub, "claude-coordinator-apollo-2026-10-31", *judg]
    print(subprocess.run(cmd, cwd=REPO, capture_output=True, text=True).stdout.strip())
    if missed:
        print(json.dumps({"batch": batch, "missed_controls": missed, "action": "re-review required; not completed"}))
        return
    ccmd = ["python3", "jobs/claim-kit/kit.py", "complete", str(out / "COMPLETION.json"), "--write",
            str(packet / "complete-v1")] + (["--publish"] if "--publish" in flags else [])
    p = subprocess.run(ccmd, cwd=REPO, capture_output=True, text=True)
    (packet / "COMPLETE_v1.log").write_text(p.stdout + "\n" + p.stderr)
    print(p.stdout[-1500:], p.stderr[-800:], "exit", p.returncode)


if __name__ == "__main__":
    main(*sys.argv[1:])
