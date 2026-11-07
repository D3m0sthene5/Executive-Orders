"""Finish the Haloander undecided-probe overlay batch 'ux' (coordinator tool; rules fixed in advance, no legal judgment).

usage: python3 -I finish_overlay.py [--publish]
  Reads ux/reviews/BLIND_REVIEW_{A,B}.jsonl and AFTER_REVEAL_{A,B}.jsonl and the private control key. A control is
  caught only if BOTH arms rejected its exact planted hash and named a date defect; any miss stops before completion.
  A member files only if BOTH arms upheld its exact claim hash (upheld_after_reveal for the genuine control). Every
  overlay member is published as an isolated replacement proposal (owner acceptance false; kit COMPLETION.md).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-user-Executive-Orders/b948d1cb-92e5-5ecb-8cbe-fc3fb7b3e2c6/scratchpad/necker")
REPO = Path("/home/user/Executive-Orders")
RUN = REPO / "research/excavator/claude-haloander-2026-11-07"
UX = RUN / "ux"
ADJ = "claude-coordinator-haloander-2026-11-07"
PUB = "research/excavator/claude-haloander-2026-11-07/ux/overlay/REPLACEMENT_PROPOSAL.jsonl"


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def fsha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(REPO).as_posix()


def lineref(p, sha):
    for i, l in enumerate(open(p, encoding="utf-8"), 1):
        if l.strip() and json.loads(l).get("claim_sha256") == sha:
            return {"path": rel(p), "sha256": fsha(p), "line": i}
    return None


def dated(r):
    t = json.dumps(r.get("defects", []), ensure_ascii=False).lower() + str(r.get("reasoning", "")).lower()
    return any(w in t for w in ("date", "first_end", "whole_order_end", "year"))


def main(*flags):
    rv = UX / "reviews"
    key = json.loads((S / "moon-keys" / "ux.json").read_text())
    blindf = {a: rv / f"BLIND_REVIEW_{a}.jsonl" for a in "AB"}
    afterf = {a: rv / f"AFTER_REVEAL_{a}.jsonl" for a in "AB"}
    blind = {a: {r["claim_sha256"]: r for r in jl(blindf[a])} for a in "AB"}
    after = {a: {r["claim_sha256"]: r for r in jl(afterf[a])} for a in "AB"}
    cdir = UX / "completion"
    cdir.mkdir(exist_ok=True)
    controls, missed = [], []
    ctl = {k["instrument_id"] for k in key["controls"]}
    for k in key["controls"]:
        iid = k["instrument_id"]
        res = {a: bool(blind[a].get(k["planted"]) and blind[a][k["planted"]].get("verdict") == "rejected"
                       and dated(blind[a][k["planted"]])) for a in "AB"}
        ok = all(res.values())
        if not ok:
            missed.append(iid)
        seed = {"schema": "eo-claim-kit-control-seed/v1", "instrument_id": iid, "planted_claim_sha256": k["planted"],
                "genuine_claim_sha256": k["genuine"], "seeded_by": ADJ}
        sp = cdir / ("SEED_RECEIPT_" + iid.replace(":", "_") + ".json")
        sp.write_text(json.dumps(seed, indent=1) + "\n")
        ref = lineref(blindf["A"], k["planted"])
        adj = {"instrument_id": iid, "planted_claim_sha256": k["planted"], "review": ref, "adjudicator": ADJ,
               "caught": ok, "scoring": "strict",
               "rationale": f"Planted version: {k['defect']}. Per-arm results {res} (caught = rejected the exact planted "
                            "hash and named the date defect). Rule fixed in advance: caught only if both arms caught it."}
        ap = cdir / ("CONTROL_ADJUDICATION_" + iid.replace(":", "_") + ".json")
        ap.write_text(json.dumps(adj, indent=1) + "\n")
        controls.append({"instrument_id": iid, "planted_claim_sha256": k["planted"],
                         "seed": {"path": rel(sp), "sha256": fsha(sp)}, "review": ref,
                         "adjudication": {"path": rel(ap), "sha256": fsha(ap)}})
    if missed:
        print(json.dumps({"missed_controls": missed, "action": "STOP: not completed"}))
        return 2
    members = []
    for bundle in sorted((UX / "overlay").glob("EO_*/proposal-v1")):
        cpath = bundle / "CLAIMS.working.jsonl"
        c = jl(cpath)[0]
        iid, sha = c["instrument_id"], canon(c)
        src, want = (after, "upheld_after_reveal") if iid in ctl else (blind, "upheld")
        bad = {a: (src[a][sha].get("defects") if sha in src[a] else "no record for this exact version")
               for a in "AB" if src[a].get(sha, {}).get("verdict") != want}
        if bad:
            members.append({"instrument_id": iid, "outcome": "blocked",
                            "reason": ("Not upheld by both independent arms: " + json.dumps(bad, ensure_ascii=False))[:3000]})
            continue
        m = {"instrument_id": iid, "outcome": "submit", "claim_sha256": sha,
             "claim": {"path": rel(cpath), "sha256": fsha(cpath), "line": 1}, "publication_kind": "whole_case",
             "overlay_bundle": {k: {"path": rel(bundle / n), "sha256": fsha(bundle / n)} for k, n in
                                (("evidence", "EVIDENCE.json"), ("decision", "STATUS_DECISION.json"),
                                 ("review", "STATUS_REVIEW.json"), ("proposal", "PROMOTION_PROPOSAL.json"))}}
        m["after_reveal_review" if iid in ctl else "review"] = lineref((afterf if iid in ctl else blindf)["A"], sha)
        members.append(m)
    # MECH_BLOCK (optional ux/completion/MECH_BLOCK.json {iid: reason}): members that passed review but that an earlier
    # dry-run completion's actual checker refused are retained as blocked with that exact reason (Dorotheus precedent).
    mb_path = UX / "completion" / "MECH_BLOCK.json"
    if mb_path.exists():
        mb = json.loads(mb_path.read_text())
        members = [({"instrument_id": m["instrument_id"], "outcome": "blocked", "reason": mb[m["instrument_id"]]}
                    if m["instrument_id"] in mb and m["outcome"] == "submit" else m) for m in members]
    receipts = [{"path": rel(f), "sha256": fsha(f)} for a in "AB" for f in (blindf[a], afterf[a]) if f.exists()]
    manifest = {"schema": "eo-claim-kit-completion/v1", "agent": "claude", "producer_model_family": "Anthropic",
                "independence_requirement": "same_family_separate_context",
                "publication": {"mode": "replacement_proposal", "path": PUB},
                "members": members, "controls": controls, "receipts": receipts}
    (cdir / "COMPLETION.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"members": len(members), "submit": sum(m["outcome"] == "submit" for m in members)}))
    n = 1
    while (cdir / f"complete-v{n}").exists():
        n += 1
    cmd = ["python3", "jobs/claim-kit/kit.py", "complete", str(cdir / "COMPLETION.json"), "--write",
           str(cdir / f"complete-v{n}")] + (["--publish"] if "--publish" in flags else [])
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    (cdir / f"COMPLETE_v{n}.log").write_text(p.stdout + "\n" + p.stderr)
    print(p.stdout[-1500:], p.stderr[-800:], "exit", p.returncode)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
