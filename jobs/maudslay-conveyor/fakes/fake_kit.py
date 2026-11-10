"""A stand-in for jobs/claim-kit/kit.py used only by test_conveyor.py: same subcommands, arguments and output files
the conveyor reads (next, prepare, dispatch-check, apply, batch-check, complete), with no corpus, no checker and no
legal content. Every call is appended to REPO/FAKE_CALLS.jsonl. REPO/FAKE_KIT.json may hold {"blocked": [ids]}."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROW_FIELDS = ['instrument_id', 'dossier_sha256', 'agent', 'outcome', 'approved', 'original_confirmed',
              'original_pages_confirmed', 'inventory_confirmed', 'research_rationale', 'savings_state', 'savings_source_id',
              'savings_reason', 'search_ids', 'conflict_resolutions', 'unresolved_material_gaps', 'earlier_end_check',
              'scope_check', 'independent_command_check', 'savings_check', 'working_text', 'source_notes', 'publication_kind']
CLAUSE_FIELDS = ['instrument_id', 'scope_id', 'clause_id', 'state', 'end_id', 'effective_date', 'mechanism',
                 'effective_date_confirmed', 'current_basis_id', 'current_legal_basis', 'checked_through',
                 'later_event_ids', 'later_events', 'reason', 'inventory_source_id', 'inventory_char_start',
                 'inventory_char_end', 'inventory_reason']


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(o):
    return hashlib.sha256(canon(o).encode()).hexdigest()


def rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(p, fields, rs):
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rs)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("next"); s.add_argument("--agent"); s.add_argument("--action"); s.add_argument("--n", type=int)
    s = sub.add_parser("prepare"); s.add_argument("ids", nargs="+"); s.add_argument("--agent"); s.add_argument("--action")
    s.add_argument("--write", type=Path); s.add_argument("--replacement-proposal", action="store_true")
    s = sub.add_parser("dispatch-check"); s.add_argument("packet", type=Path); s.add_argument("--order", action="append")
    s.add_argument("--write", type=Path)
    s = sub.add_parser("apply"); s.add_argument("packet", type=Path); s.add_argument("--write", type=Path)
    s = sub.add_parser("batch-check"); s.add_argument("packet", type=Path); s.add_argument("applied", type=Path)
    s = sub.add_parser("complete"); s.add_argument("manifest", type=Path); s.add_argument("--write", type=Path)
    s.add_argument("--publish", action="store_true")
    a = ap.parse_args(argv)
    repo = a.repo
    with open(repo / "FAKE_CALLS.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"cmd": a.cmd, "argv": argv}) + "\n")
    cfg = json.loads((repo / "FAKE_KIT.json").read_text()) if (repo / "FAKE_KIT.json").exists() else {}
    if a.cmd == "next":
        pool = json.loads((repo / "FAKE_POOL.json").read_text())
        lock = repo / "FAKE_LOCK.json"
        taken = json.loads(lock.read_text()) if lock.exists() else {}
        pick = [i for i in pool if i not in taken][:a.n]
        taken.update({i: a.agent for i in pick})
        lock.write_text(json.dumps(taken))
        print(json.dumps([{"instrument_id": i, "agent": a.agent, "action": a.action} for i in pick]))
        return 0
    if a.cmd == "prepare":
        if a.write.exists():
            print("prepare destination exists", file=sys.stderr); return 1
        a.write.mkdir(parents=True)
        blocked = [i for i in a.ids if i in cfg.get("blocked", [])]
        (a.write / "PACKET.json").write_text(json.dumps({"agent": a.agent, "members": a.ids, "fingerprint": "fp"}))
        write_csv(a.write / "decisions.csv", ROW_FIELDS, [dict({k: "" for k in ROW_FIELDS}, instrument_id=i,
                  dossier_sha256="d-" + i, agent=a.agent, outcome="unresolved", approved="false",
                  unresolved_material_gaps="[]") for i in a.ids])
        write_csv(a.write / "clauses.csv", CLAUSE_FIELDS, [dict({k: "" for k in CLAUSE_FIELDS}, instrument_id=i,
                  scope_id=i + "#1", clause_id=i + "#1") for i in a.ids])
        (a.write / "RATIONALES.json").write_text("{}\n")
        dc = {"ok": not blocked, "dispatchable_ids": [i for i in a.ids if i not in blocked], "source_blocked_ids": blocked}
        (a.write / "DISPATCH_CHECK.json").write_text(json.dumps(dc))
        print(json.dumps({"members": len(a.ids)}))
        return int(bool(blocked))
    if a.cmd == "dispatch-check":
        ids = a.order or []
        bad = [i for i in ids if i in cfg.get("blocked", [])] or (["stale"] if cfg.get("dispatch_fails") else [])
        a.write.write_text(json.dumps({"ok": not bad, "dispatchable_ids": [i for i in ids if i not in bad],
                                       "source_blocked_ids": bad}))
        return int(bool(bad))
    if a.cmd == "apply":
        if a.write.exists():
            return 1
        a.write.mkdir(parents=True)
        rat = json.loads((a.packet / "RATIONALES.json").read_text())
        cl = rows(a.packet / "clauses.csv")
        audit, claims = [], []
        for r in rows(a.packet / "decisions.csv"):
            iid = r["instrument_id"]
            if r["outcome"] != "submit":
                audit.append({"instrument_id": iid, "outcome": r["outcome"], "errors": []}); continue
            text = r["research_rationale"]
            if text.startswith("@rationale:"):
                text = rat[text.split(":", 1)[1]]
            if "BADCLAIM" in text:
                audit.append({"instrument_id": iid, "outcome": "rejected", "errors": ["ValueError: synthetic failure"]})
                continue
            cs = [c for c in cl if c["instrument_id"] == iid]
            end = cs[0]["effective_date"]
            claim = {"schema": "eo-lifecycle-claim/v1", "instrument_id": iid, "whole_order_status": "no",
                     "whole_order_end": {"date": end},
                     "operative_clauses": [{"scope_id": c["scope_id"], "first_end": {"date": c["effective_date"]}}
                                           for c in cs],
                     "research_rationale": text, "claim_kit": {"agent": r["agent"], "dossier_sha256": r["dossier_sha256"]}}
            claims.append(claim)
            audit.append({"instrument_id": iid, "outcome": "assembled_proposal", "errors": [], "claim_sha256": sha(claim)})
        (a.write / "CLAIMS.proposed.jsonl").write_text("".join(canon(c) + "\n" for c in claims), encoding="utf-8")
        (a.write / "AUDIT.json").write_text(json.dumps(audit))
        return int(any(x["outcome"] == "rejected" for x in audit))
    if a.cmd == "batch-check":
        claims = [json.loads(l) for l in (a.applied / "CLAIMS.proposed.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        fails = [{"instrument_id": c["instrument_id"], "errors": ["checker: synthetic custody failure"]}
                 for c in claims if "CHECKFAIL" in c.get("research_rationale", "")]
        (a.applied / "CHECK_SUMMARY.json").write_text(json.dumps({"claims_checked": len(claims), "actionable_failures": fails}))
        return int(bool(fails))
    if a.cmd == "complete":
        m = json.loads(a.manifest.read_text(encoding="utf-8"))
        a.write.mkdir(parents=True)
        exceptions = []
        lines = []
        for mem in m["members"]:
            if mem["outcome"] != "submit":
                continue
            ref = mem["claim"]
            p = repo / ref["path"]
            if hashlib.sha256(p.read_bytes()).hexdigest() != ref["sha256"]:
                exceptions.append("claim file hash")
            line = p.read_text(encoding="utf-8").splitlines()[ref["line"] - 1]
            if sha(json.loads(line)) != mem["claim_sha256"]:
                exceptions.append("claim sha")
            rv = mem.get("review") or mem.get("after_reveal_review")
            rec = json.loads((repo / rv["path"]).read_text(encoding="utf-8").splitlines()[rv["line"] - 1])
            want = "upheld_after_reveal" if "after_reveal_review" in mem else "upheld"
            if rec.get("claim_sha256") != mem["claim_sha256"] or rec.get("verdict") != want or not rec.get("independent"):
                exceptions.append("review " + mem["instrument_id"])
            lines.append(line)
        for c in m["controls"]:
            adj = json.loads((repo / c["adjudication"]["path"]).read_text(encoding="utf-8"))
            if adj["review"] != c["review"]:
                exceptions.append("control review pin")
        published = 0
        if a.publish and not exceptions and lines:
            target = repo / m["publication"]["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as f:
                f.write("".join(l + "\n" for l in lines).encode())
            published = len(lines)
        (a.write / "PUBLICATION.json").write_text(json.dumps({"path": m["publication"]["path"],
                                                             "written": bool(published)}))
        (a.write / "TALLY.json").write_text(json.dumps({"exceptions": len(exceptions), "exception_list": exceptions,
                                                         "eligible": [json.loads(l)["instrument_id"] for l in lines],
                                                         "claims_published": published}))
        print(json.dumps({"exceptions": len(exceptions)}))
        return int(bool(exceptions))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
