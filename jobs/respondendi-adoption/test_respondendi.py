"""Respondendi refuses without the owner's exact rule on main, adopts only audited members of active lot kinds that
meet every condition, stops a kind on confirmed errors, and can be undone."""
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import respondendi as R  # noqa: E402

R.ALLOW_DATES = True                                    # the suite runs on fixed dates
WAVE = "research/excavator/fixture-wave"
PROMPT = "research/excavator/fixture-wave/tools/prompts/producer.txt"
ALL_ROUTES = ("own_text", "current", "working_text")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_bytes(rows, fields=R.ROW_FIELDS):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fields})
    return stream.getvalue().encode("utf-8")


def git(root, *args):
    out = subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                          "-c", "commit.gpgsign=false", *args], capture_output=True, text=True)
    if out.returncode:
        raise AssertionError(f"git {args[0]} failed: {out.stderr[-600:]}")
    return out


class Fixture:
    """A tiny git repository with an origin/main ref: census EO:1-EO:9, EO:1 decided, a wave of overlay proposals."""

    def __init__(self, root, ids=("EO:2", "EO:3", "EO:4", "EO:5"), controls=("EO:4", "EO:5"), routes=ALL_ROUTES):
        self.root = Path(root)
        self.ids, self.controls = list(ids), list(controls)
        self.write(R.RULE, (HERE / "RULE.md").read_bytes())
        self.write(R.CHECKLIST, b"checklist\n")
        self.write(PROMPT, b"producer prompt\n")
        self.set_routes(routes, commit=False)
        census = [{"id": f"EO:{n}"} for n in range(1, 10)]
        self.write("census.csv", csv_bytes(census, ["id"]))
        base_bytes = csv_bytes([{"instrument_id": "EO:1", "provisional_substantive_status": "yes",
                                 "human_certified_by_this_release": "no"}])
        self.write(R.LEDGER, base_bytes)
        parsed = list(csv.DictReader(io.StringIO(base_bytes.decode("utf-8"), newline="")))
        contract = {
            "schema": "eo-accepted-population-contract/v1",
            "census": {"path": "census.csv", "count": 9, "identity_sha256": R.canon(sorted(c["id"] for c in census))},
            "historical_status_baseline": {"path": R.LEDGER, "bytes": len(base_bytes), "count": 1,
                                           "sha256": sha(base_bytes), "rows_sha256": R.canon(parsed)},
            "accepted_additions": [],
        }
        self.write(R.CONTRACT, json.dumps(contract, indent=2) + "\n")
        self.write(R.DECISIONS, b"")
        self.write(R.HOLDS, b"")
        self.remote = self.root.parent / (self.root.name + "-remote.git")
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)], check=True, capture_output=True)
        git(self.root, "init", "-q")
        git(self.root, "remote", "add", "origin", str(self.remote))
        self.merge()
        self.build_wave()

    # -- helpers
    def path(self, rel):
        return self.root / rel

    def write(self, rel, data):
        full = self.path(rel)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return rel

    def wjson(self, rel, value):
        return self.write(rel, json.dumps(value, indent=1) + "\n")

    def ref(self, rel):
        return {"path": rel, "sha256": sha(self.path(rel).read_bytes())}

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "--allow-empty", "-m", "fixture")

    def merge(self):
        """Commit, push to the remote's main and fetch it (an owner merge)."""
        self.commit()
        git(self.root, "push", "-q", "origin", "HEAD:refs/heads/main")
        git(self.root, "fetch", "-q", "origin")

    def set_routes(self, routes, commit=True):
        self.write(R.KIT_OVERLAY, "UNDECIDED_ROUTES = frozenset({%s})\n" % ", ".join(repr(r) for r in routes))
        if commit:
            self.merge()

    def build_wave(self, batch="u01", *, arm_b_rejects=(), control_missed=False, status="no", checker_fail=(),
                   reviewer_same_as_arm=False, admitted=None, partial=(), gaps=("unresolved_material_gaps:clause 2 end undated",),
                   failed_steps=(), kinds=("date_shift", "partial_as_whole"), lot_kinds=None, no_basis=(), working=(),
                   working_ok=True, extra_act=(), quote=None, no_witness=(), finished="2026-11-10T09:00:00Z", notes=None):
        """lot_kinds: {iid: express|own_terms|spent|amends|yes}; no_basis: the decision cites no kind record."""
        u = f"{WAVE}/{batch}"
        comp = u + "/completion"
        lot_kinds = dict(lot_kinds or {})
        notes = dict(notes or {})
        claims, members, outcomes, checks = [], [], [], {}
        for iid in self.ids:
            n = iid.split(":")[1]
            b = f"{u}/overlay/EO_{n}/proposal-v1"
            lk = lot_kinds.get(iid, "express")
            st = "yes" if lk == "yes" else status
            reviewer = "arm-A" if reviewer_same_as_arm else f"status-reviewer-{n}"
            review = {"schema": "eo-status-overlay-review/v1", "decision": "accept", "independence_confirmed": True,
                      "source_checks_confirmed": True, "instrument_id": iid, "reviewer": reviewer,
                      "reviewer_role": "independent_ai"}
            original = ({"acceptable_as_original": False, "grade": "archival_replica_checked", "signing_date": "1940-05-01",
                         **({"working_text_basis": "tracker_original_supported"} if working_ok else {})}
                        if iid in working else
                        {"acceptable_as_original": True, "grade": "original_representation_unverified", "signing_date": "1940-05-01"})
            records = {f"ORIGINAL:{iid}": original}
            observations = []
            savings = None
            provision = (quote or f"Executive Order No. {n} of May 1, 1940, is hereby revoked.")
            if lk == "express":
                basis = [f"ACT:{iid}>EO:9000"]
                records[basis[0]] = {"actor_id": "EO:9000", "scope": "whole", "verb": "revoke", "savings_phrases": [],
                                     "names_target": True, "reaches_target_via": "", "signing_date": "1950-01-01",
                                     "provision_text": provision}
                if iid not in no_witness:
                    observations.append({"text": "Revoked by: EO 9000, January 1, 1950" + notes.get(iid, "")})
                end = {"actor": "EO:9000", "date": "1950-01-01", "mechanism": "express_revocation", "quote": provision}
            elif lk == "own_terms":
                basis = [f"TERM:{iid}:a"]
                records[basis[0]] = {"kind": "fixed_term", "stated_end_date": "1950-01-01", "scope_id": f"{iid}#whole",
                                     "text": "This order shall remain in effect until January 1, 1950."}
                end = {"actor": iid, "date": "1950-01-01", "mechanism": "own_terms_fixed_term",
                       "quote": "This order shall remain in effect until January 1, 1950."}
            elif lk == "ulpian":
                basis = [f"ORIGINAL:{iid}"]
                end = {"actor": iid, "date": "2025-07-22", "date_kind": "not_later_than", "first_cause": "unresolved",
                       "mechanism": "life_of_named_person",
                       "quote": "Mr. Smith, born before February 9, 1903, may be appointed without examination."}
                rationale = "Birth no later than 1903-02-09 (born_by); end not later than 2025-07-22; use of the permission unknown."
            elif lk in ("spent", "amends"):
                basis = [f"OWN_TEXT:{iid}#1"]
                records[basis[0]] = {"own_text_kind": "spent_on_issue" if lk == "spent" else "amends_parent",
                                     "mechanism": "spent_on_issue", "actor_id": iid, "scope": "whole",
                                     "whole_order_test": {"continuing_sentences": 0, "classifier": "own_text_v1"},
                                     "text": "The lands described are hereby restored to the public domain."}
                if lk == "amends":
                    records[f"PARENT_END:{iid}>EO:8000>EO:9000"] = {"mechanism": "follows_parent", "parent_id": "EO:8000",
                                                                  "actor_id": "EO:9000", "text": "Executive Order No. 8000 is revoked."}
                    savings = [{"source": {"evidence_id": f"PARENT_END:{iid}>EO:8000>EO:9000"}}]
                end = {"actor": iid, "date": "1940-05-01", "mechanism": "spent_on_issue",
                       "quote": "The lands described are hereby restored to the public domain."}
            else:                                                     # yes
                basis = [f"CURRENT:{iid}#1"]
                records[basis[0]] = {"text": "Ex. Ord. No. %s, May 1, 1940, 5 F.R. 1, provided:" % n}
                end = None
                if notes.get(iid):
                    observations.append({"text": notes[iid].lstrip(" |")})
            for extra in extra_act:
                if extra == iid:
                    records[f"ACT:{iid}>EO:9500"] = {"actor_id": "EO:9500", "scope": "whole", "verb": "revoke", "savings_phrases": []}
            if iid in no_basis:
                for x in basis:
                    records.pop(x, None)
            dossier = {"original_source_id": f"ORIGINAL:{iid}", "evidence": records, "missing": [],
                       "machine_searches": [{"search_id": s_, "complete": True} for s_ in
                                            ("current-law:usc", "current-law:ecfr", "later-events:ofr_catalog")]}
            evidence = {"instrument_id": iid, "base_dossier": dossier, "history_packet": {"observations": observations}}
            decision = {"instrument_id": iid, "approved": True, "recommended_provisional_status": st, "basis_evidence_ids": basis,
                        "current_predicate_checked_through": "2026-10-14" if st == "yes" else None}
            review["decision_sha256"] = R.canon(decision)
            dsha, rsha = R.canon(decision), R.canon(review)
            proposal = {"recommended_provisional_status": st, "decision_sha256": dsha, "review_sha256": rsha}
            for name, value in (("EVIDENCE.json", evidence), ("STATUS_DECISION.json", decision),
                                ("STATUS_REVIEW.json", review), ("PROMOTION_PROPOSAL.json", proposal)):
                self.wjson(f"{b}/{name}", value)
            if end is not None and lk == "ulpian":
                end["source"] = {"quote": end.pop("quote"), "text_path": f"jobs/csc-annual-reports/output/texts/EO_{n}.txt",
                                 "sha256": "2" * 64, "signing_date": "1940-05-01"}
            elif end is not None:
                end["source"] = {"quote": end.pop("quote"), "text_path": "jobs/fr-originals/texts/EO_9000.txt",
                                 "sha256": "1" * 64, "signing_date": "1950-01-01" if end["actor"] != iid else "1940-05-01"}
            claim = {"instrument_id": iid, "whole_order_status": st, "whole_order_end": end,
                     "claim_kit": {"agent": "producer-x", "status_overlay": {"decision_sha256": dsha, "review_sha256": rsha}}}
            if savings:
                claim["savings_residuals"] = savings
            if lk == "ulpian":
                claim["research_rationale"] = rationale
            claims.append(claim)
            csha = R.canon(claim)
            kind = "partial_research" if iid in partial else "whole_case"
            members.append({"instrument_id": iid, "outcome": "submit", "claim_sha256": csha, "publication_kind": kind,
                            "overlay_bundle": {k: self.ref(f"{b}/{f}") for k, f in
                                               (("evidence", "EVIDENCE.json"), ("decision", "STATUS_DECISION.json"),
                                                ("review", "STATUS_REVIEW.json"), ("proposal", "PROMOTION_PROPOSAL.json"))}})
            outcomes.append({"instrument_id": iid, "outcome": "eligible", "claim_sha256": csha,
                             "gate_errors": list(gaps) if kind == "partial_research" else [],
                             "source_review_upheld": True, "publication_kind": kind})
            steps = {s_: s_ not in failed_steps for s_ in ("original_text", "clause_inventory", "ending_or_current_basis",
                                                           "savings_residuals", "counterevidence")}
            if kind == "partial_research":
                steps["clause_inventory"] = False
            checks[iid] = {"claim_sha256": csha, "all_checks_passed": kind == "whole_case" and iid not in checker_fail,
                           "gate_passed": kind == "whole_case", "mechanical_result": "pass" if kind == "whole_case" else "fail",
                           "steps_checker_passed": steps}
        planted = {}
        for cid in self.controls:
            p = copy.deepcopy(next(c for c in claims if c["instrument_id"] == cid))
            if p.get("whole_order_end"):
                p["whole_order_end"]["date"] = "1947-01-01"
            else:
                p["planted_later_event_removed"] = True
            planted[cid] = R.canon(p)
        for arm in "AB":
            rows, after = [], []
            for claim in claims:
                iid = claim["instrument_id"]
                if iid in self.controls:
                    continue
                verdict = "rejected" if (arm == "B" and iid in arm_b_rejects) else "upheld"
                rows.append({"instrument_id": iid, "claim_sha256": R.canon(claim), "reviewer": f"arm-{arm}",
                             "model_family": "Anthropic", "independent": True, "separate_context": True,
                             "scope": "partial_research" if iid in partial else "whole_case", "verdict": verdict})
            for cid in self.controls:
                missed = control_missed and arm == "B" and cid == self.controls[0]
                rows.append({"instrument_id": cid, "claim_sha256": planted[cid], "reviewer": f"arm-{arm}",
                             "model_family": "Anthropic", "independent": True, "separate_context": True,
                             "scope": "whole_case", "verdict": "upheld" if missed else "rejected"})
                genuine = next(c for c in claims if c["instrument_id"] == cid)
                after.append({"instrument_id": cid, "claim_sha256": R.canon(genuine), "reviewer": f"arm-{arm}",
                              "model_family": "Anthropic", "independent": True, "separate_context": True,
                              "scope": "whole_case", "verdict": "upheld_after_reveal"})
            self.write(f"{u}/reviews/BLIND_REVIEW_{arm}.jsonl", "".join(json.dumps(r) + "\n" for r in rows))
            self.write(f"{u}/reviews/AFTER_REVEAL_{arm}.jsonl", "".join(json.dumps(r) + "\n" for r in after))
        ctl = []
        for cid, kind in zip(self.controls, kinds):
            adj = self.wjson(f"{comp}/CONTROL_ADJUDICATION_EO_{cid.split(':')[1]}.json",
                             {"caught": not control_missed, "control_kind": kind})
            ctl.append({"instrument_id": cid, "planted_claim_sha256": planted[cid], "adjudication": self.ref(adj)})
        manifest = {"schema": "eo-claim-kit-completion/v1", "agent": "producer-x", "producer_model_family": "Anthropic",
                    "members": members, "controls": ctl,
                    "receipts": [self.ref(f"{u}/reviews/{k}_{a}.jsonl") for a in "AB" for k in ("BLIND_REVIEW", "AFTER_REVEAL")]}
        self.wjson(f"{comp}/COMPLETION.json", manifest)
        cv = comp + "/complete-v1"
        prop_rel = self.write(f"{u}/overlay/REPLACEMENT_PROPOSAL.jsonl",
                              "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in claims))
        self.wjson(cv + "/INPUTS.json", {"preserved_receipts": {f"{comp}/COMPLETION.json": sha(self.path(f"{comp}/COMPLETION.json").read_bytes())}})
        self.wjson(cv + "/PUBLICATION.json", {"mode": "replacement_proposal", "written": True, "path": prop_rel,
                                              "sha256": sha(self.path(prop_rel).read_bytes()),
                                              "independent_human_certifications": 0})
        self.wjson(cv + "/EXCEPTIONS.json", [])
        self.wjson(cv + "/TALLY.json", {"controls": [{"instrument_id": c, "caught": not control_missed} for c in self.controls],
                                        "outcomes": outcomes, "finished_utc": finished})
        self.wjson(cv + "/TRACKER_CHECKER.json", {"by_instrument": checks})
        self.admission = self.wjson(u + "/packet/ADMISSION.json", {
            "schema": "eo-claim-kit-admission/v1", "bentham_action": "status_assignment.undecided", "agent": "producer-x",
            "instrument_ids": sorted(admitted if admitted is not None else self.ids)})
        self.completion = cv

    def approve(self, token=None, decision_id="D-20991231-respondendi", ruling_name="respondendi.md", merge=True, verb=None):
        token = token or (R.APPROVE + R.rule_sha(self.root))
        verb = verb or R.VERBS[next(k for k in R.VERBS if token.startswith(k))]
        line = f"Owner {verb} {token}"
        ruling = self.write(R.RULINGS + ruling_name, f"# Owner ruling\n\n{line}\n")
        with self.path(R.DECISIONS).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": decision_id, "rev": 0, "ruling": line, "sources": [ruling]}) + "\n")
        if merge:
            self.merge()
        else:
            self.commit()
        return decision_id

    def plan(self, lot="lot-one", write=True, date="2026-11-10"):
        return R.plan(self.root, lot, [self.completion], [self.admission], [PROMPT], date=date, write=write)

    def evidence(self, lot, iid, tag, model="gpt-6.1"):
        member = next(m for m in R.plan_of(self.root, lot)["members"] if m["instrument_id"] == iid)
        return self.wjson(f"{R.LOTS}/{lot}/audit-evidence/{tag}-{iid.replace(':', '')}.json",
                          {"model": model, "instrument_id": iid, "claim_sha256": member["claim_sha256"], "tag": tag})

    def audit_all(self, lot="lot-one", verdict="agree", found="no", only=None, date="2026-11-10"):
        members = R.plan_of(self.root, lot)["members"]
        for iid in only or R.plan_of(self.root, lot)["audit_sample"]:
            st = next(m["status"] for m in members if m["instrument_id"] == iid)
            R.audit_record(self.root, lot, iid, "auditor-gpt", "independent_ai", "OpenAI", verdict,
                           st if verdict == "agree" else found,
                           "Re-read the held revoking order and its effective date; the end date is supported.",
                           evidence=self.evidence(lot, iid, "audit"), date=date, write=True)

    def adopt(self, lot="lot-one", write=True, date="2026-11-10"):
        return R.adopt(self.root, lot, date=date, write=write)

    def run(self, lot="lot-one", date="2026-11-10"):
        self.plan(lot, date=date)
        self.audit_all(lot, date=date)
        return self.adopt(lot, date=date)


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        original = R.kit_checks
        R.kit_checks = lambda *a: []                       # the fixture has no claim kit; its gates are tested apart
        self.addCleanup(setattr, R, "kit_checks", original)
        self.fx = Fixture(self.root)

    def ledger(self):
        return self.fx.path(R.LEDGER).read_bytes()

    def reasons(self, out, iid):
        return " ".join({r["instrument_id"]: r["reasons"] for r in out["refused"]}.get(iid, []))


class Authorization(Base):
    def test_refuses_without_owner_decision_and_writes_nothing(self):
        before = self.ledger()
        with self.assertRaisesRegex(R.Refused, "no owner decision on origin/main"):
            self.fx.plan()
        self.assertEqual(self.ledger(), before)
        self.assertFalse(self.fx.path(R.LOTS).exists())

    def test_dry_run_reports_without_authorization(self):
        out = self.fx.plan(write=False)
        self.assertEqual(out["qualifying"], ["EO:2", "EO:3", "EO:4", "EO:5"])
        self.assertEqual(out["audit_sample"], ["EO:2", "EO:3", "EO:4", "EO:5"])
        self.assertIn("no owner decision", out["authorization"])

    def test_approval_on_a_branch_only_is_not_enough(self):
        self.fx.approve(merge=False)
        with self.assertRaisesRegex(R.Refused, "no owner decision on origin/main"):
            self.fx.plan()

    def test_a_declining_decision_that_cites_the_hash_is_not_approval(self):
        self.fx.approve(verb="declines")
        with self.assertRaisesRegex(R.Refused, "no owner decision on origin/main"):
            self.fx.plan()

    def test_decision_without_owner_ruling_file_is_not_enough(self):
        line = f"Owner approves {R.APPROVE}{R.rule_sha(self.root)}"
        self.fx.write(R.DECISIONS, json.dumps({"id": "D-x", "rev": 0, "ruling": line, "sources": ["HANDOFF/notes-claude.md"]}) + "\n")
        self.fx.merge()
        with self.assertRaisesRegex(R.Refused, "no owner decision"):
            self.fx.plan()

    def test_approval_of_another_rule_text_does_not_carry_over(self):
        self.fx.approve()
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"max_lot_orders": 60', '"max_lot_orders": 600')
        self.fx.write(R.RULE, rule)
        with self.assertRaisesRegex(R.Refused, "no owner decision"):
            self.fx.plan()

    def test_crlf_checkout_keeps_the_rule_hash(self):
        digest = R.rule_sha(self.root)
        self.fx.write(R.RULE, self.fx.path(R.RULE).read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(R.rule_sha(self.root), digest)

    def test_suspension_stops_adoption(self):
        self.fx.approve()
        self.fx.approve(token=R.SUSPEND + R.rule_sha(self.root), decision_id="D-20991231-suspend", ruling_name="suspend.md")
        with self.assertRaisesRegex(R.Refused, "suspended"):
            self.fx.plan()

    def test_dates_come_from_the_clock(self):
        R.ALLOW_DATES = False
        try:
            with self.assertRaisesRegex(R.Refused, "clock"):
                self.fx.plan(date="2001-01-01", write=False)
        finally:
            R.ALLOW_DATES = True

    def test_a_conditional_approval_is_no_approval(self):
        token = R.APPROVE + R.rule_sha(self.root)
        ruling = self.fx.write(R.RULINGS + "cond.md", f"Owner approves {token} for the express kind only\n")
        self.fx.write(R.DECISIONS, json.dumps({"id": "D-c", "rev": 0, "ruling": f"Owner approves {token} for the express kind only",
                                               "sources": [ruling]}) + "\n")
        self.fx.merge()
        with self.assertRaisesRegex(R.Refused, "no owner decision"):
            self.fx.plan()

    def test_a_hand_moved_main_ref_is_refused(self):
        self.fx.approve(merge=False)
        git(self.fx.root, "update-ref", R.MAIN, "HEAD")
        with self.assertRaisesRegex(R.Refused, "not GitHub's main"):
            self.fx.plan()


class Adoption(Base):
    def setUp(self):
        super().setUp()
        self.decision = self.fx.approve()

    def test_plan_audit_adopt_writes_rows_contract_and_byte_identical_claims(self):
        out = self.fx.run()
        self.assertEqual(out["adopted"], 4)
        self.assertEqual(R.population(self.root)["statuses"],
                         {"EO:1": "yes", "EO:2": "no", "EO:3": "no", "EO:4": "no", "EO:5": "no"})
        proposal = self.fx.path(WAVE + "/u01/overlay/REPLACEMENT_PROPOSAL.jsonl").read_bytes()
        self.assertEqual(self.fx.path(R.CLAIMS + "/respondendi-lot-one.jsonl").read_bytes(), proposal)
        entry = json.loads(self.fx.path(R.CONTRACT).read_text(encoding="utf-8"))["accepted_additions"][-1]
        self.assertEqual(entry["standing_rule"]["decision"], self.decision)
        pins = {p["path"] for p in entry["authorization_pins"]}
        self.assertTrue({R.LOTS + "/lot-one/RULE_AT_ADOPTION.md", R.RULINGS + "respondendi.md",
                         R.LOTS + "/lot-one/LOT.json", R.LOTS + "/lot-one/PLAN.json", R.LOTS + "/lot-one/AUDITS.jsonl"} <= pins)
        rows = list(csv.DictReader(io.StringIO(self.fx.path(R.LOTS + "/lot-one/ADOPTION_ROWS.csv").read_text(encoding="utf-8"))))
        self.assertTrue(all(r["human_certified_by_this_release"] == "no" for r in rows))
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_nothing_is_adopted_before_the_audits(self):
        self.fx.plan()
        before = self.ledger()
        with self.assertRaisesRegex(R.Refused, "audits missing"):
            self.fx.adopt()
        self.assertEqual(self.ledger(), before)

    def test_kit_gate_errors_refuse(self):
        R.kit_checks = lambda *a: ["producer_identity_confirmed_required"]
        out = self.fx.plan(write=False)
        self.assertEqual(out["qualifying"], [])
        self.assertIn("claim-kit gate", self.reasons(out, "EO:2"))

    def test_one_arm_rejecting_keeps_that_order_out(self):
        self.fx.build_wave(arm_b_rejects=("EO:3",))
        out = self.fx.plan()
        self.assertEqual(out["qualifying"], ["EO:2", "EO:4", "EO:5"])
        self.assertIn("arm B", self.reasons(out, "EO:3"))

    def test_express_quotes_that_are_not_express_named_unqualified(self):
        kind = R.parameters(self.root)["kinds"]["express_named_revocation"]
        good = ["Executive Order No. 2 of May 1, 1940, is hereby revoked.",
                "This order supersedes Executive Order No. 2 of September 20, 1956.",
                "Executive Order No. 10479 of August 13, 1953, together with Executive Orders Nos. 10482 of August 15, 1953 "
                "(18 F.R. 4944), and 2 of October 10, 1957 (22 F.R. 8135), amending that order, are hereby revoked."]
        bad = ["Section 2 of Executive Order No. 2 is revoked.", "So much of Executive Order No. 2 as relates to Utah is revoked.",
               "Executive Order No. 2 is revoked as to the following lands.", "Executive Order No. 2 (other than section 4) is revoked.",
               "Nothing in this order shall be construed to revoke Executive Order No. 2.", "Executive Order No. 2 is not revoked.",
               "Executive Order No. 7999 is revoked. Executive Order No. 2 is amended to read as follows.",
               "Executive Order No. 2 is revoked: Provided, That section 3 shall remain in force.",
               "Executive Order No. 2 shall be revoked on January 1, 2027.",
               "Executive Order No. 9000, which revoked Executive Order No. 2, is rescinded and Executive Order No. 2 is reinstated.",
               "Executive Order No. 2 is revoked in part.", "Executive Order No. 2 is hereby revoked except section 3 thereof.",
               "The 2 offices are revoked.", "Executive Order No. 2A is revoked."]
        for q in good:
            self.assertTrue(R.named_end_in(q, "EO:2", kind), q)
        for q in bad:
            self.assertFalse(R.named_end_in(q, "EO:2", kind), q)
        self.assertFalse(R.named_end_in("Executive Order No. 341 is revoked.", "EO:341A", kind))
        self.assertTrue(R.named_end_in("Executive Order No. 341-A is revoked.", "EO:341A", kind))

    def test_express_refuses_a_later_catalog_act(self):
        self.fx.build_wave(notes={"EO:3": " | Amended by: EO 9900, May 1, 1960"})
        self.assertIn("after the claimed end", self.reasons(self.fx.plan(write=False), "EO:3"))

    def test_express_needs_a_second_witness(self):
        self.fx.build_wave(no_witness=("EO:3",))
        self.assertIn("second witness", self.reasons(self.fx.plan(write=False), "EO:3"))

    def test_express_refuses_a_partial_provision_in_the_basis_record(self):
        self.fx.build_wave(quote="Section 2 of Executive Order No. 3 is hereby revoked.")
        self.assertIn("not one sentence naming the order", self.reasons(self.fx.plan(write=False), "EO:3"))

    def test_missed_control_refuses_the_whole_completion(self):
        self.fx.build_wave(control_missed=True)
        with self.assertRaisesRegex(R.Refused, "did not reject planted control"):
            self.fx.plan()

    def test_controls_must_include_a_status_determining_kind(self):
        self.fx.build_wave(kinds=("date_shift", "date_shift"))
        with self.assertRaisesRegex(R.Refused, "status-determining"):
            self.fx.plan()

    def test_untyped_control_is_refused(self):
        self.fx.build_wave(kinds=("date_shift", None))
        with self.assertRaisesRegex(R.Refused, "control_kind"):
            self.fx.plan()

    def test_stale_completion_is_refused(self):
        self.fx.build_wave(finished="2026-09-01T00:00:00Z")
        with self.assertRaisesRegex(R.Refused, "older than"):
            self.fx.plan(write=False)

    def test_unadmitted_order_is_refused(self):
        self.fx.build_wave(admitted=["EO:2", "EO:3", "EO:5"])
        self.assertNotIn("EO:4", self.fx.plan(write=False)["qualifying"])

    def test_checker_failure_is_refused(self):
        self.fx.build_wave(checker_fail=("EO:2",))
        self.assertNotIn("EO:2", self.fx.plan(write=False)["qualifying"])

    def test_status_reviewer_must_differ_from_the_arms(self):
        self.fx.build_wave(reviewer_same_as_arm=True)
        with self.assertRaisesRegex(R.Refused, "no proposal meets the rule"):
            self.fx.plan()

    def test_tampered_manifest_is_refused(self):
        rel = WAVE + "/u01/completion/COMPLETION.json"
        data = json.loads(self.fx.path(rel).read_text(encoding="utf-8"))
        data["agent"] = "someone-else"
        self.fx.wjson(rel, data)
        with self.assertRaisesRegex(R.Refused, "differs from the manifest"):
            self.fx.plan()

    def test_decided_order_is_never_readopted(self):
        self.fx.run()
        with self.assertRaisesRegex(R.Refused, "no proposal meets the rule"):
            self.fx.plan(lot="lot-two", date="2026-11-11")

    def test_an_order_is_planned_in_one_open_lot_only(self):
        self.fx.plan()
        with self.assertRaisesRegex(R.Refused, "already planned"):
            self.fx.plan(lot="lot-two")

    def test_an_expired_plan_can_be_replanned(self):
        self.fx.plan()
        self.fx.build_wave(finished="2026-11-20T00:00:00Z")
        self.assertTrue(self.fx.plan(lot="lot-two", date="2026-11-30")["written"])

    def test_lot_size_limit(self):
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"max_lot_orders": 60', '"max_lot_orders": 3')
        self.fx.write(R.RULE, rule)
        self.fx.approve(decision_id="D-20991231-small", ruling_name="small.md")
        with self.assertRaisesRegex(R.Refused, "per lot"):
            self.fx.plan()

    def test_one_lot_a_day(self):
        self.fx.run()
        self.fx.ids, self.fx.controls = ["EO:6", "EO:7", "EO:8"], ["EO:7", "EO:8"]
        self.fx.build_wave("u02")
        self.fx.plan(lot="lot-two")
        self.fx.audit_all("lot-two")
        with self.assertRaisesRegex(R.Refused, "cadence"):
            self.fx.adopt("lot-two")
        self.assertEqual(self.fx.adopt("lot-two", date="2026-11-11")["adopted"], 3)

    def test_old_plan_must_be_redone(self):
        self.fx.plan()
        self.fx.audit_all()
        with self.assertRaisesRegex(R.Refused, "older than"):
            self.fx.adopt(date="2026-12-31")

    def test_changed_rule_needs_a_new_plan(self):
        self.fx.plan()
        self.fx.audit_all()
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"max_lot_orders": 60', '"max_lot_orders": 59')
        self.fx.write(R.RULE, rule)
        with self.assertRaisesRegex(R.Refused, "RULE.md changed"):
            self.fx.adopt()

    def test_failed_population_check_rolls_back(self):
        self.fx.plan()
        self.fx.audit_all()
        ledger, contract = self.ledger(), self.fx.path(R.CONTRACT).read_bytes()
        original, calls = R.population, {"n": 0}

        def flaky(repo, contract_text=None):
            calls["n"] += 1
            if calls["n"] > 1:
                raise R.Refused("simulated population failure")
            return original(repo, contract_text)
        R.population = flaky
        try:
            with self.assertRaisesRegex(R.Refused, "simulated"):
                self.fx.adopt()
        finally:
            R.population = original
        self.assertEqual(self.ledger(), ledger)
        self.assertEqual(self.fx.path(R.CONTRACT).read_bytes(), contract)
        self.assertFalse(self.fx.path(R.LOTS + "/lot-one/LOT.json").exists())


class LotKinds(Base):
    def setUp(self):
        super().setUp()
        self.fx.approve()

    def strata(self):
        return {m["instrument_id"]: m["stratum"] for m in R.plan_of(self.root, "lot-one")["members"]}

    def test_each_kind_qualifies_with_its_records_and_opens_on_probation(self):
        self.fx.build_wave(lot_kinds={"EO:2": "own_terms", "EO:3": "spent", "EO:4": "own_terms"},
                           kinds=("later_event_removed", "partial_as_whole"))
        out = self.fx.plan()
        self.assertEqual(out["qualifying"], ["EO:2", "EO:3", "EO:4", "EO:5"])
        self.assertEqual({s_.split(":")[1] for s_ in self.strata().values()}, {"own_terms", "spent_on_issue", "express_named_revocation"})
        self.assertEqual(out["audit_sample"], ["EO:2", "EO:3", "EO:4", "EO:5"])
        self.fx.audit_all()
        self.assertEqual(self.fx.adopt()["adopted"], 4)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_a_route_not_declared_on_main_stays_inactive(self):
        self.fx.set_routes(("current",))
        self.fx.build_wave(lot_kinds={"EO:2": "spent"})
        self.assertIn("inactive until: F5", self.reasons(self.fx.plan(write=False), "EO:2"))

    def test_hand_written_records_without_the_route_do_not_open_it(self):
        self.fx.set_routes(())
        self.fx.build_wave(lot_kinds={"EO:2": "yes", "EO:3": "spent"}, kinds=("date_shift", "later_event_removed"))
        out = self.fx.plan(write=False)
        self.assertIn("inactive until: F3", self.reasons(out, "EO:2"))
        self.assertIn("inactive until: F5", self.reasons(out, "EO:3"))

    def test_own_terms_needs_a_later_event_control_and_no_later_instrument(self):
        self.fx.build_wave(lot_kinds={"EO:2": "own_terms"})
        self.assertIn("later_event_removed", self.reasons(self.fx.plan(write=False), "EO:2"))
        self.fx.build_wave(lot_kinds={"EO:2": "own_terms", "EO:4": "own_terms"}, kinds=("later_event_removed", "partial_as_whole"),
                           extra_act=("EO:2",))
        self.assertIn("later instrument acts", self.reasons(self.fx.plan(write=False), "EO:2"))
        self.fx.build_wave(lot_kinds={"EO:2": "own_terms", "EO:4": "own_terms"}, kinds=("date_shift", "later_event_removed"))
        self.assertIn("planted on claims of that kind", self.reasons(self.fx.plan(write=False), "EO:2"))

    def test_amending_order_records_its_surviving_text(self):
        self.fx.build_wave(lot_kinds={"EO:2": "amends"})
        self.assertIn("EO:2", self.fx.plan(write=False)["qualifying"])

    def test_yes_needs_a_current_record_a_later_event_control_and_clean_screens(self):
        self.fx.build_wave(lot_kinds={"EO:2": "yes"})
        self.assertIn("later_event_removed", self.reasons(self.fx.plan(write=False), "EO:2"))
        yes = {"EO:2": "yes", "EO:4": "yes"}
        self.fx.build_wave(lot_kinds=yes, kinds=("later_event_removed", "partial_as_whole"))
        self.assertIn("EO:2", self.fx.plan(write=False)["qualifying"])
        self.fx.build_wave(lot_kinds=yes, kinds=("later_event_removed", "partial_as_whole"), extra_act=("EO:2",))
        self.assertIn("later instrument acts", self.reasons(self.fx.plan(write=False), "EO:2"))
        self.fx.build_wave(lot_kinds=yes, kinds=("later_event_removed", "partial_as_whole"), notes={"EO:2": " | Suspended by: EO 9100, 1950"})
        self.assertIn("allow-list", self.reasons(self.fx.plan(write=False), "EO:2"))

    def test_yes_is_always_fully_audited_and_stops_on_one_error(self):
        params = R.parameters(self.root)
        self.assertEqual(R.effective(params, "yes_current")["stop_confirmed_errors_in_59"], 1)
        self.assertEqual(R.effective(params, "yes_current")["audit_rate_steady"], 1.0)

    def test_working_text_needs_the_route_and_its_marker_and_is_its_own_stratum(self):
        self.fx.build_wave(working=("EO:2",), working_ok=False)
        self.assertIn("working texts inactive until: F6", self.reasons(self.fx.plan(write=False), "EO:2"))
        self.fx.build_wave(working=("EO:2",))
        self.fx.plan()
        strata = self.strata()
        self.assertIn(":working:", strata["EO:2"])
        self.assertNotEqual(strata["EO:2"], strata["EO:3"])

    def test_a_stopped_kind_does_not_stop_the_others(self):
        self.fx.build_wave(lot_kinds={"EO:2": "own_terms", "EO:3": "own_terms", "EO:4": "own_terms"},
                           kinds=("later_event_removed", "partial_as_whole"))
        self.fx.plan()
        strata = self.strata()
        for iid in ("EO:2", "EO:3"):
            R.audit_record(self.root, "lot-one", iid, "auditor-gpt", "independent_ai", "OpenAI", "disagree", "yes",
                           "The order's term was extended by a later order the claim does not list.",
                           evidence=self.fx.evidence("lot-one", iid, "audit"), date="2026-11-10", write=True)
            R.adjudicate(self.root, "lot-one", iid, "adjudicator-1", "independent_ai", "Google", "confirmed_error",
                         "Read the extending order; the term did not expire on the claimed date.", date="2026-11-10",
                         write=True, evidence=self.fx.evidence("lot-one", iid, "adj", model="gemini-3"))
        self.fx.audit_all(only=["EO:4", "EO:5"])
        self.assertTrue(R.stratum_state(self.root, strata["EO:2"], R.parameters(self.root))["stopped"])
        self.assertEqual(self.fx.adopt()["adopted"], 1)                 # EO:4 shares the stopped own-terms kind
        self.assertEqual(sorted(R.population(self.root)["statuses"]), ["EO:1", "EO:5"])


class UlpianLot(Base):
    """The owner-approved Ulpian bound rule, read from main, opens the life-bound kind."""

    def setUp(self):
        super().setUp()
        self.fx.approve()

    def ulpian_on_main(self, bound="2025-07-22"):
        body = b"# Ulpian bound rule (fixture)\n"
        digest = hashlib.sha256(body).hexdigest()
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace(
            "57a95ba0c11e7207c27de317d7f522c24d05b9aedda91eea261ea2f9c0f64699", digest)
        self.fx.write(R.RULE, rule)
        self.fx.write("jobs/ulpian-outer-bound/RULE.md", body)
        rows = [{"instrument_id": "EO:2", "tier": "quoted_fact", "status": "undecided", "born_by": "1903-02-09",
                 "bound": bound, "text_path": "jobs/csc-annual-reports/output/texts/EO_2.txt"}]
        self.fx.write("research/ulpian/CLASS.csv", csv_bytes(rows, list(rows[0])))
        ruling = self.fx.write(R.RULINGS + "ulpian.md", f"1. Approve. ulpian-rule-sha256:{digest}\n")
        with self.fx.path(R.DECISIONS).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": "D-20261110-ulpian-life-bound", "rev": 0,
                                 "ruling": f"Approve the Ulpian lot. ulpian-rule-sha256:{digest}", "sources": [ruling]}) + "\n")
        self.fx.approve(decision_id="D-20991231-respondendi-ulpian", ruling_name="respondendi-ulpian.md")

    def test_the_lot_waits_for_the_owner_rule_on_main(self):
        self.fx.build_wave(lot_kinds={"EO:2": "ulpian", "EO:4": "ulpian"}, kinds=("second_person_hidden", "partial_as_whole"))
        self.assertIn("inactive until: PR #271", self.reasons(self.fx.plan(write=False), "EO:2"))

    def test_a_class_member_qualifies_with_its_bound_and_disclosure(self):
        self.ulpian_on_main()
        self.fx.build_wave(lot_kinds={"EO:2": "ulpian", "EO:4": "ulpian"}, kinds=("second_person_hidden", "partial_as_whole"))
        out = self.fx.plan(write=False)
        self.assertIn("EO:2", out["qualifying"])
        self.assertIn("not a quoted-fact member", self.reasons(out, "EO:4"))

    def test_a_wrong_bound_or_missing_control_is_refused(self):
        self.ulpian_on_main(bound="2024-01-01")
        self.fx.build_wave(lot_kinds={"EO:2": "ulpian", "EO:4": "ulpian"}, kinds=("second_person_hidden", "partial_as_whole"))
        self.assertIn("not_later_than the Ulpian bound", self.reasons(self.fx.plan(write=False), "EO:2"))
        self.ulpian_on_main()
        self.fx.build_wave(lot_kinds={"EO:2": "ulpian"}, kinds=("date_shift", "partial_as_whole"))
        self.assertIn("planted on claims of that kind", self.reasons(self.fx.plan(write=False), "EO:2"))


class StatusOnly(Base):
    def setUp(self):
        super().setUp()
        self.fx.approve()

    def test_a_gap_about_another_instrument_is_refused(self):
        self.fx.build_wave(partial=("EO:3",), gaps=("unresolved_material_gaps:whether EO 9900 later reinstated it",))
        self.assertIn("may not concern", self.reasons(self.fx.plan(write=False), "EO:3"))

    def test_partial_claim_adopts_status_but_files_no_claim(self):
        self.fx.build_wave(partial=("EO:3",))
        self.assertIn("EO:3", self.fx.run()["adoptable"])
        self.assertEqual(R.population(self.root)["statuses"]["EO:3"], "no")
        filed = self.fx.path(R.CLAIMS + "/respondendi-lot-one.jsonl").read_text(encoding="utf-8")
        self.assertNotIn('"instrument_id": "EO:3"', filed)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_status_touching_gap_is_refused(self):
        self.fx.build_wave(partial=("EO:3",), gaps=("whole_order_end_evidence:no source",))
        self.assertNotIn("EO:3", self.fx.plan(write=False)["qualifying"])

    def test_failed_status_checker_step_is_refused(self):
        self.fx.build_wave(partial=("EO:3",), failed_steps=("ending_or_current_basis",))
        self.assertNotIn("EO:3", self.fx.plan(write=False)["qualifying"])


class Audits(Base):
    def setUp(self):
        super().setUp()
        self.fx.approve()
        self.fx.plan()

    def record(self, iid, verdict="agree", found="no", family="OpenAI", role="independent_ai", auditor="auditor-1",
               evidence=True):
        model = {"OpenAI": "gpt-6.1", "anthropic": "claude-opus-5-5"}.get(family, "gpt-6.1")
        return R.audit_record(self.root, "lot-one", iid, auditor, role, family, verdict, found,
                              "Re-read the held revoking order and its effective date; the end date is supported.",
                              evidence=self.fx.evidence("lot-one", iid, "audit", model=model) if evidence is True else evidence,
                              date="2026-11-10", write=True)

    def adjudicate(self, iid, finding, family="Google", adjudicator="adjudicator-1"):
        return R.adjudicate(self.root, "lot-one", iid, adjudicator, "independent_ai", family, finding,
                            "Read the revoking order and the target's text side by side; the finding follows.",
                            date="2026-11-10", write=True,
                            evidence=self.fx.evidence("lot-one", iid, "adj", model={"Google": "gemini-3", "openai": "gpt-6.1"}[family]))

    def test_ai_auditor_must_be_another_family_in_any_case(self):
        with self.assertRaisesRegex(R.Refused, "different from the reviewers"):
            self.record("EO:2", family="anthropic")

    def test_an_audit_needs_evidence(self):
        with self.assertRaisesRegex(R.Refused, "evidence"):
            self.record("EO:2", evidence=None)

    def test_evidence_must_be_its_own_file_naming_the_claim(self):
        with self.assertRaisesRegex(R.Refused, "under"):
            self.record("EO:2", evidence=R.RULE)
        other = self.fx.write(f"{R.LOTS}/lot-one/audit-evidence/blank.json", '{"model": "gpt-6.1"}')
        with self.assertRaisesRegex(R.Refused, "claim hash"):
            self.record("EO:2", evidence=other)
        used = self.fx.evidence("lot-one", "EO:2", "audit")
        self.record("EO:2", evidence=used)
        with self.assertRaisesRegex(R.Refused, "claim hash|already backs"):
            self.record("EO:3", evidence=used)

    def test_the_run_receipt_must_show_the_family(self):
        wrong = self.fx.evidence("lot-one", "EO:2", "audit", model="claude-opus-5-5")
        with self.assertRaisesRegex(R.Refused, "does not show family"):
            self.record("EO:2", evidence=wrong)

    def test_a_person_must_be_on_the_rules_list(self):
        with self.assertRaisesRegex(R.Refused, "rule names"):
            self.record("EO:2", role="human", auditor="a person")
        self.record("EO:2", role="human", auditor="owner")

    def test_an_order_with_a_confirmed_error_never_returns(self):
        self.record("EO:3", verdict="disagree", found="yes")
        self.adjudicate("EO:3", "confirmed_error")
        for iid in ("EO:2", "EO:4", "EO:5"):
            self.record(iid)
        self.fx.adopt()
        self.fx.build_wave("u01")
        out = self.fx.plan(lot="lot-two", date="2026-11-11", write=False)
        self.assertIn("confirmed error or a reversal is on record", self.reasons(out, "EO:3"))

    def test_an_inflated_resume_count_resumes_nothing(self):
        for iid in ("EO:2", "EO:3"):
            self.record(iid, verdict="disagree", found="yes")
            self.adjudicate(iid, "confirmed_error")
        stratum = R.plan_of(self.root, "lot-one")["members"][0]["stratum"]
        token = R.stratum_state(self.root, stratum, R.parameters(self.root))["resume_token"].rsplit("@", 1)[0] + "@9999"
        self.fx.approve(token=token, decision_id="D-20991231-resume", ruling_name="resume.md")
        self.assertTrue(R.stratum_state(self.root, stratum, R.parameters(self.root))["stopped"])

    def test_auditor_must_not_be_a_reviewer(self):
        with self.assertRaisesRegex(R.Refused, "must not be the producer or a reviewer"):
            self.record("EO:2", auditor="arm-A")

    def test_open_disagreement_blocks_until_adjudicated(self):
        for iid in ("EO:2", "EO:4", "EO:5"):
            self.record(iid)
        self.record("EO:3", verdict="disagree", found="yes")
        with self.assertRaisesRegex(R.Refused, "adjudicate"):
            self.fx.adopt()
        with self.assertRaisesRegex(R.Refused, "other than the auditor"):
            self.adjudicate("EO:3", "auditor_wrong", family="openai")
        self.adjudicate("EO:3", "auditor_wrong")
        self.assertEqual(self.fx.adopt()["adopted"], 4)

    def test_confirmed_error_is_not_adopted_and_counts(self):
        for iid in ("EO:2", "EO:4", "EO:5"):
            self.record(iid)
        self.record("EO:3", verdict="disagree", found="yes")
        self.adjudicate("EO:3", "confirmed_error")
        self.assertEqual(self.fx.adopt()["adopted"], 3)
        self.assertNotIn("EO:3", R.population(self.root)["statuses"])
        state = R.status(self.root)["strata"][0]
        self.assertEqual((state["confirmed_errors"], state["audits_needed"]), (1, 93))
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_two_confirmed_errors_stop_the_kind_until_the_owner_resumes_at_a_count(self):
        for iid in ("EO:2", "EO:3"):
            self.record(iid, verdict="disagree", found="yes")
            self.adjudicate(iid, "confirmed_error")
        for iid in ("EO:4", "EO:5"):
            self.record(iid)
        with self.assertRaisesRegex(R.Refused, "stopped strata"):
            self.fx.adopt()
        stratum = R.plan_of(self.root, "lot-one")["members"][0]["stratum"]
        token = R.stratum_state(self.root, stratum, R.parameters(self.root))["resume_token"]
        self.fx.approve(token=token, decision_id="D-20991231-resume", ruling_name="resume.md")
        self.assertEqual(self.fx.adopt()["adopted"], 2)

    def test_a_new_prompt_does_not_escape_a_stop(self):
        for iid in ("EO:2", "EO:3"):
            self.record(iid, verdict="disagree", found="yes")
            self.adjudicate(iid, "confirmed_error")
        self.fx.write(PROMPT, b"producer prompt, one byte changed\n")
        self.fx.ids, self.fx.controls = ["EO:6", "EO:7", "EO:8"], ["EO:7", "EO:8"]
        self.fx.build_wave("u02")
        self.assertIn("stopped", self.reasons(self.fx.plan(lot="lot-two", write=False), "EO:6"))

    def test_agreeing_audits_of_unadopted_plans_do_not_count(self):
        stratum = R.plan_of(self.root, "lot-one")["members"][0]["stratum"]
        fake = "".join(json.dumps({"lot": f"never-{i}", "stratum": stratum, "instrument_id": f"EO:{100 + i}",
                                   "verdict": "agree", "in_sample": True, "date": "2026-11-01"}) + "\n" for i in range(59))
        self.fx.write(R.REGISTER + "/AUDITS.jsonl", fake)
        self.assertTrue(R.stratum_state(self.root, stratum, R.parameters(self.root))["probation"])

    def test_steady_state_samples_after_the_bound_is_met(self):
        stratum = R.plan_of(self.root, "lot-one")["members"][0]["stratum"]
        lots = "".join(json.dumps({"lot": f"old-{i}", "date": "2026-10-01", "count": 1}) + "\n" for i in range(59))
        fake = "".join(json.dumps({"lot": f"old-{i}", "stratum": stratum, "instrument_id": f"EO:{100 + i}",
                                   "verdict": "agree", "in_sample": True, "date": "2026-10-01"}) + "\n" for i in range(59))
        self.fx.write(R.REGISTER + "/LOTS.jsonl", lots)
        self.fx.write(R.REGISTER + "/AUDITS.jsonl", fake)
        self.fx.ids, self.fx.controls = ["EO:6", "EO:7", "EO:8"], ["EO:7", "EO:8"]
        self.fx.build_wave("u02")
        out = self.fx.plan(lot="lot-two", write=False)
        self.assertFalse(out["strata"][stratum]["probation"])
        self.assertEqual(len(out["audit_sample"]), 2)

    def test_two_reversals_in_one_lot_and_each_counts_as_an_error(self):
        for iid in ("EO:2", "EO:3", "EO:4", "EO:5"):
            self.record(iid)
        self.fx.adopt()
        for iid in ("EO:3", "EO:4"):
            R.reverse(self.root, "lot-one", iid, "Later audit found the revoking order postdates the cutoff.", write=True)
        self.assertEqual(sorted(R.population(self.root)["statuses"]), ["EO:1", "EO:2", "EO:5"])
        holds = [json.loads(l) for l in self.fx.path(R.HOLDS).read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual([h["instrument_id"] for h in holds], ["EO:3", "EO:4"])
        stratum = R.plan_of(self.root, "lot-one")["members"][0]["stratum"]
        self.assertTrue(R.stratum_state(self.root, stratum, R.parameters(self.root))["stopped"])
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_verify_catches_a_hand_edited_lot_receipt(self):
        for iid in ("EO:2", "EO:3", "EO:4", "EO:5"):
            self.record(iid)
        self.fx.adopt()
        rel = R.LOTS + "/lot-one/LOT.json"
        data = json.loads(self.fx.path(rel).read_text(encoding="utf-8"))
        data["members"][0]["status"] = "yes"
        self.fx.wjson(rel, data)
        self.assertFalse(R.verify(self.root)["ok"])

    def test_report_is_current_and_states_zero_certification(self):
        self.record("EO:2")
        text = self.fx.path(R.REPORT).read_text(encoding="utf-8")
        self.assertIn("Human-certified whole lifecycles: 0", text)
        self.assertIn("Open plans: lot-one", text)


class Statistics(unittest.TestCase):
    def test_bounds_match_the_jacquard_rule(self):
        self.assertAlmostEqual(R.upper_bound(0, 59), 1 - 0.05 ** (1 / 59), places=4)
        self.assertEqual(R.audits_needed(0, 0.05), 59)
        self.assertEqual(R.audits_needed(1, 0.05), 93)
        self.assertEqual(R.audits_needed(2, 0.05), 124)

    def test_shipped_rule_parses(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / R.RULE).parent.mkdir(parents=True)
        shutil.copy(HERE / "RULE.md", root / R.RULE)
        params = R.parameters(root)
        self.assertEqual(set(params["kinds"]), {"express_named_revocation", "own_terms", "spent_on_issue", "yes_current",
                                                "ulpian_life_bound"})
        self.assertEqual(params["kinds"]["yes_current"]["route"], "current")


if __name__ == "__main__":
    unittest.main()
