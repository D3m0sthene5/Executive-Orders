"""A stand-in for jobs/claim-kit/kit.py used only by test_conveyor.py: same subcommands, arguments and output files
the conveyor reads (next, prepare, dispatch-check, apply, batch-check, complete, and the status-overlay commands
overlay-review-sheet, overlay-propose, overlay-assemble, overlay-check), with no corpus, no checker and no legal content.
Every call is appended to REPO/FAKE_CALLS.jsonl. REPO/FAKE_KIT.json may hold {"blocked": [ids]} and
{"undecided": {id: repo-relative EVIDENCE.json}}: such an order is prepared as undecided (packet/undecided/EO_N/ with
its evidence and a blank STATUS_DECISION.json), and apply leaves it awaiting_status_review. A working claim carries a
"fake_seal" (sha of the rest of the claim), so a fake reviewer can tell any planted change, typed or dated."""
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


def dump(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def blank_decision(ev, agent):
    """As status_overlay.extend_decision: every judgment blank."""
    h = ev["history_packet"]["history"]
    return {"schema": "eo-status-history-decision/v1", "instrument_id": ev["instrument_id"],
            "history_sha256": ev["history_sha256"], "evidence_sha256": ev["fingerprint"], "agent": agent,
            "approved": False, "identity_confirmed": False, "observations_reviewed": [], "proposed_intervals": [],
            "conflict_resolutions": {}, "recommended_provisional_status": None, "rationale": "",
            "material_gaps": list(h.get("flags", [])), "basis_evidence_ids": [], "basis_review_confirmed": False,
            "earlier_endings_checked": False, "partial_scope_checked": False, "savings_checked": False,
            "current_predicate_checked_through": None, "original_pages_confirmed": False}


def overlay(repo, a):
    """The four overlay commands, with the kit's file contracts (status_overlay.py) and stand-in content."""
    if a.cmd == "overlay-review-sheet":
        if a.write.exists():
            print("Review sheet exists; refusing overwrite", file=sys.stderr)
            return 1
        ev, dec = load(a.evidence), load(a.decision)
        dump(a.write, {"schema": "eo-status-overlay-review/v1", "instrument_id": ev["instrument_id"],
                       "decision_sha256": sha(dec), "evidence_sha256": ev["fingerprint"],
                       "history_sha256": ev["history_sha256"], "reviewer": a.reviewer, "reviewer_role": "independent_ai",
                       "independence_confirmed": False, "decision": None, "source_checks_confirmed": False,
                       "checked_evidence_ids": [], "rationale": ""})
        print(str(a.write))
        return 0
    if a.cmd == "overlay-propose":
        ev, dec, rev = load(a.evidence), load(a.decision), load(a.review)
        if "overlay" not in a.write.resolve().parts:
            print("ValueError: research_overlay_destination_requires_overlay_directory", file=sys.stderr)
            return 1
        if a.write.exists():
            print("ValueError: overlay_bundle_exists; use a new versioned destination", file=sys.stderr)
            return 1
        if rev.get("decision") != "accept" or rev.get("decision_sha256") != sha(dec):
            print("ValueError: status_proposal_rejected:independent_review_accept_required", file=sys.stderr)
            return 1
        proposal = {"schema": "eo-status-promotion-proposal/v1", "instrument_id": ev["instrument_id"],
                    "recommended_provisional_status": dec["recommended_provisional_status"], "producer": dec["agent"],
                    "decision_sha256": sha(dec), "reviewer": rev["reviewer"], "review_sha256": sha(rev),
                    "evidence_sha256": ev["fingerprint"], "owner_acceptance": {"accepted": False}}
        proposal["fingerprint"] = sha(proposal)
        # As status_overlay.experimental_dossier: the base dossier with the reviewed status envelope only (a YES also
        # gains a 'missing' line, which the conveyor's reconfirmation must refuse).
        dossier = dict(ev.get("base_dossier") or {"instrument_id": ev["instrument_id"]})
        dossier.update(whole_order_status=dec.get("recommended_provisional_status"),
                       status_overlay={"proposal_sha256": proposal["fingerprint"], "experimental_only": True},
                       notice="EXPERIMENTAL STATUS OVERLAY; " + str(dossier.get("notice", "")))
        if dossier["whole_order_status"] == "yes":
            dossier["missing"] = sorted(set((dossier.get("missing") or []) + [
                "Current legal predicate and coverage through 2026-10-14 require judgment."]))
        dossier["fingerprint"] = sha(dossier)
        files = {"EVIDENCE.json": ev, "STATUS_DECISION.json": dec, "STATUS_REVIEW.json": rev,
                 "PROMOTION_PROPOSAL.json": proposal, "DOSSIER.json": dossier}
        if a.lifecycle_sheet:
            src = load(a.lifecycle_sheet)
            if src.get("instrument_id") != ev["instrument_id"]:
                print("ValueError: lifecycle_sheet_must_match_frozen_base_dossier", file=sys.stderr)
                return 1
            work = dict(src, approved=False, dossier_sha256="overlay-" + proposal["fingerprint"][:16])
            files.update({"LIFECYCLE_DECISION.json": work, "LIFECYCLE_SOURCE_DECISION.json": src,
                          "LIFECYCLE_CONTINUITY.json": {"producer_reconfirmation_required": True}})
        a.write.mkdir(parents=True)
        for name, value in files.items():
            dump(a.write / name, value)
        dump(a.write / "TELEMETRY.json", {"authoritative_files_unchanged": True})
        print(json.dumps({"proposal_fingerprint": proposal["fingerprint"], "statuses_published": 0}))
        return 0
    bundle = a.bundle.resolve()
    proposal = load(bundle / "PROMOTION_PROPOSAL.json")
    label = {"proposal_sha256": proposal["fingerprint"], "decision_sha256": proposal["decision_sha256"],
             "review_sha256": proposal["review_sha256"], "owner_accepted": False, "experimental_only": True}
    if a.cmd == "overlay-assemble":
        dest = a.write.resolve()
        if dest.exists() or not dest.is_relative_to(bundle):
            print("ValueError: new working claim must stay under isolated overlay bundle", file=sys.stderr)
            return 1
        sheet = load(a.sheet)
        if sheet.get("approved") is not True:
            print(json.dumps({"errors": ["producer approval required"], "claims_published": 0}))
            return 1
        iid = proposal["instrument_id"]
        cs = sheet.get("clauses") or []
        src = {"text_path": f"jobs/x/{iid.replace(':', '_')}.txt", "quote": f"Executive Order {iid[3:]} is hereby revoked.",
               "evidence_id": "ACT:" + iid}
        end = max(c.get("effective_date") or "" for c in cs) if cs else ""
        claim = {"schema": "eo-lifecycle-claim/v1", "instrument_id": iid,
                 "whole_order_status": proposal["recommended_provisional_status"],
                 "whole_order_end": {"date": end, "actor": "EO:fake", "source": dict(src)},
                 "operative_clauses": [{"scope_id": c["scope_id"], "first_end": {"date": c.get("effective_date"),
                                                                                "source": dict(src)},
                                        "original_operative_text": f"Clause {c['scope_id']} of {iid}.",
                                        "original_source": {"quote": f"Clause {c['scope_id']} of {iid}."},
                                        "later_events": []} for c in cs],
                 "research_rationale": sheet.get("research_rationale", ""),
                 "claim_kit": {"agent": sheet.get("agent"), "dossier_sha256": sheet.get("dossier_sha256"),
                               "status_overlay": label}}
        claim["fake_seal"] = sha(claim)
        dest.write_text(json.dumps(claim, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"working_claim": str(dest), "experimental_only": True, "claims_published": 0}))
        return 0
    if a.cmd == "overlay-check":
        rows = [json.loads(l) for l in a.claims.read_text(encoding="utf-8").splitlines() if l.strip()]
        fails = []
        for i, c in enumerate(rows, 1):
            body = {k: v for k, v in c.items() if k != "fake_seal"}
            if c.get("claim_kit", {}).get("status_overlay") != label or c.get("fake_seal") != sha(body):
                fails.append({"line": i, "errors": ["working_claim_status_overlay_label_required"]})
        print(json.dumps({"checked": len(rows), "failures": fails, "claims_published": 0}))
        return int(not rows or bool(fails))
    return 2


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
    s = sub.add_parser("overlay-review-sheet"); s.add_argument("--evidence", type=Path); s.add_argument("--decision", type=Path)
    s.add_argument("--reviewer"); s.add_argument("--write", type=Path)
    s = sub.add_parser("overlay-propose"); s.add_argument("--evidence", type=Path); s.add_argument("--decision", type=Path)
    s.add_argument("--review", type=Path); s.add_argument("--lifecycle-sheet", type=Path); s.add_argument("--write", type=Path)
    s = sub.add_parser("overlay-assemble"); s.add_argument("bundle", type=Path); s.add_argument("--sheet", type=Path)
    s.add_argument("--write", type=Path)
    s = sub.add_parser("overlay-check"); s.add_argument("bundle", type=Path); s.add_argument("claims", type=Path)
    a = ap.parse_args(argv)
    repo = a.repo
    with open(repo / "FAKE_CALLS.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"cmd": a.cmd, "argv": argv}) + "\n")
    cfg = json.loads((repo / "FAKE_KIT.json").read_text()) if (repo / "FAKE_KIT.json").exists() else {}
    if a.cmd.startswith("overlay-"):
        return overlay(repo, a)
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
        undecided = {i: load(repo / p) for i, p in (cfg.get("undecided") or {}).items() if i in a.ids}
        (a.write / "PACKET.json").write_text(json.dumps({"agent": a.agent, "members": a.ids, "fingerprint": "fp"}))
        for i, ev in undecided.items():
            d = a.write / "undecided" / i.replace(":", "_")
            dump(d / "EVIDENCE.json", ev)
            dump(d / "STATUS_DECISION.json", blank_decision(ev, a.agent))
        write_csv(a.write / "decisions.csv", ROW_FIELDS, [dict({k: "" for k in ROW_FIELDS}, instrument_id=i,
                  dossier_sha256=undecided[i]["base_dossier"]["fingerprint"] if i in undecided else "d-" + i,
                  agent=a.agent, outcome="unresolved", approved="false",
                  unresolved_material_gaps="[]") for i in a.ids])
        clause_rows = []
        for i in a.ids:
            scopes = ([(c["scope_id"], c["id"]) for c in undecided[i]["base_dossier"]["clauses"]] if i in undecided
                      else [(i + "#1", i + "#1")])
            clause_rows += [dict({k: "" for k in CLAUSE_FIELDS}, instrument_id=i, scope_id=sc, clause_id=cl)
                            for sc, cl in scopes]
        write_csv(a.write / "clauses.csv", CLAUSE_FIELDS, clause_rows)
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
            sheet = {"schema": "eo-claim-kit-decision/v1", "instrument_id": iid, "dossier_sha256": r["dossier_sha256"],
                     "agent": r["agent"], "approved": r["approved"] == "true", "research_rationale": text,
                     "clauses": [{"scope_id": c["scope_id"], "state": c["state"], "effective_date": c["effective_date"]}
                                 for c in cs]}
            dump(a.write / "decisions" / (iid.replace(":", "_") + ".json"), sheet)
            if (a.packet / "undecided" / iid.replace(":", "_") / "EVIDENCE.json").exists():
                audit.append({"instrument_id": iid, "outcome": "awaiting_status_review", "errors": [], "claim_sha256": None})
                continue
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
            ob = mem.get("overlay_bundle")
            if ob is not None:
                names = {"evidence": "EVIDENCE.json", "decision": "STATUS_DECISION.json", "review": "STATUS_REVIEW.json",
                         "proposal": "PROMOTION_PROPOSAL.json"}
                if m["publication"]["mode"] != "replacement_proposal":
                    exceptions.append("overlay requires replacement_proposal " + mem["instrument_id"])
                if set(ob) != set(names) or len({Path(ob[k]["path"]).parent for k in ob}) != 1 or any(
                        Path(ob[k]["path"]).name != n or hashlib.sha256((repo / ob[k]["path"]).read_bytes()).hexdigest()
                        != ob[k]["sha256"] for k, n in names.items()):
                    exceptions.append("overlay bundle refs " + mem["instrument_id"])
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
