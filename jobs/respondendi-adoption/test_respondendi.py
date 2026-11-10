"""Respondendi refuses without the owner's exact rule, adopts only audited lot members that meet every condition,
stops on confirmed errors, and can be undone."""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import respondendi as R  # noqa: E402

WAVE = "research/excavator/fixture-wave"
PROMPT = "research/excavator/fixture-wave/tools/prompts/producer.txt"


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
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)


class Fixture:
    """A tiny git repository: census EO:1-EO:9, EO:1 decided, a wave whose overlay proposals cover four orders."""

    def __init__(self, root, ids=("EO:2", "EO:3", "EO:4", "EO:5"), controls=("EO:4", "EO:5")):
        self.root = Path(root)
        self.ids, self.controls = list(ids), list(controls)
        self.write(R.RULE, (HERE / "RULE.md").read_bytes())
        self.write(R.CHECKLIST, b"checklist\n")
        self.write(PROMPT, b"producer prompt\n")
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
        git(self.root, "init", "-q")
        self.commit()
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

    def build_wave(self, batch="u01", *, arm_b_rejects=(), control_missed=False, status="no", checker_fail=(),
                   reviewer_same_as_arm=False, admitted=None, partial=(), gaps=("unresolved_material_gaps:clause 2 end undated",),
                   failed_steps=(), kinds=("date_shift", "partial_as_whole"), own_terms=(), lot_kinds=None,
                   no_basis=(), working=(), working_ok=True, extra_act=()):
        """lot_kinds: {iid: express|own_terms|spent|parent|yes|outer}; no_basis: orders whose decision cites no
        kind record (an inactive route); working: orders whose original is a working text."""
        u = f"{WAVE}/{batch}"
        comp = u + "/completion"
        lot_kinds = dict(lot_kinds or {})
        for iid in own_terms:
            lot_kinds[iid] = "own_terms_bare"
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
            original = ({"acceptable_as_original": False, "grade": "archival_replica_checked",
                         **({"working_text_basis": "tracker_original_supported"} if working_ok else {})}
                        if iid in working else {"acceptable_as_original": True, "grade": "original_representation_unverified"})
            records = {f"ORIGINAL:{iid}": original}
            revoke = f"Executive Order No. {n} of May 1, 1940, is hereby revoked."
            if lk == "express":
                basis = f"ACT:{iid}>EO:9000"
                records[basis] = {"scope": "whole", "verb": "revoke", "savings_phrases": [], "names_target": True}
                end = {"actor": "EO:9000", "date": "1950-01-01", "mechanism": "express_revocation"}
                quote = revoke
            elif lk in ("own_terms", "own_terms_bare"):
                basis = f"TERM:{iid}:a"
                records[basis] = {"kind": "fixed_term", "stated_end_date": "1950-01-01"}
                end = {"actor": iid, "date": "1950-01-01", "mechanism": "expiration_by_own_terms"}
                quote = "This order shall remain in effect until January 1, 1950."
                if lk == "own_terms_bare":
                    records.pop(basis)
            elif lk == "spent":
                basis = f"OWN_TEXT:{iid}:a"
                records[basis] = {"own_text_kind": "spent_on_issue"}
                end = {"actor": iid, "date": "1940-05-01", "mechanism": "spent_on_issue"}
                quote = "The lands described are hereby restored to the public domain."
            elif lk == "parent":
                basis = f"PARENT_END:{iid}:EO:8000"
                records[basis] = {"parent": "EO:8000"}
                end = {"actor": "EO:9000", "date": "1950-01-01", "mechanism": "follows_parent", "parent": "EO:8000"}
                quote = "Executive Order No. 8000 of May 1, 1939, as amended, is hereby revoked."
            elif lk == "yes":
                basis = f"CURRENT:{iid}:usc"
                records[basis] = {"text": "Ex. Ord. No. %s ... provided:" % n}
                end, quote = None, None
            else:                                                     # outer
                basis = f"OWN_TEXT:{iid}:outer"
                end = {"actor": iid, "date": "1990-01-01", "mechanism": "outer_bound", "bound_rule": "D-x"}
                quote = "Mr. Smith may be appointed without examination."
            for extra in extra_act:
                if extra == iid:
                    records[f"ACT:{iid}>EO:9500"] = {"scope": "whole", "verb": "revoke", "savings_phrases": []}
            if iid in no_basis:
                records.pop(basis, None)
            evidence = {"instrument_id": iid, "base_dossier": {"original_source_id": f"ORIGINAL:{iid}", "evidence": records}}
            decision = {"instrument_id": iid, "approved": True, "recommended_provisional_status": st,
                        "basis_evidence_ids": [basis], "current_predicate_checked_through": "2026-10-14" if st == "yes" else None}
            dsha, rsha = R.canon(decision), R.canon(review)
            proposal = {"recommended_provisional_status": st, "decision_sha256": dsha, "review_sha256": rsha}
            for name, value in (("EVIDENCE.json", evidence), ("STATUS_DECISION.json", decision),
                                ("STATUS_REVIEW.json", review), ("PROMOTION_PROPOSAL.json", proposal)):
                self.wjson(f"{b}/{name}", value)
            if end is not None:
                end["source"] = {"quote": quote, "text_path": "jobs/fr-originals/texts/EO_9000.txt", "sha256": "1" * 64,
                                 "signing_date": "1950-01-01" if end["actor"] != iid else "1940-05-01"}
            claim = {"instrument_id": iid, "whole_order_status": st, "whole_order_end": end,
                     "claim_kit": {"agent": "producer-x", "status_overlay": {"decision_sha256": dsha, "review_sha256": rsha}}}
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
            steps = {s: s not in failed_steps for s in ("original_text", "clause_inventory", "ending_or_current_basis",
                                                         "savings_residuals", "counterevidence")}
            if kind == "partial_research":
                steps["clause_inventory"] = False
            checks[iid] = {"claim_sha256": csha, "all_checks_passed": kind == "whole_case" and iid not in checker_fail,
                           "gate_passed": kind == "whole_case", "mechanical_result": "pass" if kind == "whole_case" else "fail",
                           "steps_checker_passed": steps}
        planted = {}
        for cid in self.controls:
            p = copy.deepcopy(next(c for c in claims if c["instrument_id"] == cid))
            p["whole_order_end"]["date"] = "1947-01-01"
            planted[cid] = R.canon(p)
        for arm in "AB":
            rows = []
            for claim in claims:
                iid = claim["instrument_id"]
                if iid in self.controls:
                    continue
                verdict = "rejected" if (arm == "B" and iid in arm_b_rejects) else "upheld"
                rows.append({"instrument_id": iid, "claim_sha256": R.canon(claim), "reviewer": f"arm-{arm}",
                             "model_family": "Anthropic", "independent": True, "separate_context": True,
                             "scope": "partial_research" if iid in partial else "whole_case", "verdict": verdict})
            after = []
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
                                        "outcomes": outcomes})
        self.wjson(cv + "/TRACKER_CHECKER.json", {"by_instrument": checks})
        self.admission = self.wjson(u + "/packet/ADMISSION.json", {
            "schema": "eo-claim-kit-admission/v1", "bentham_action": "status_assignment.undecided", "agent": "producer-x",
            "instrument_ids": sorted(admitted if admitted is not None else self.ids)})
        self.completion = cv

    def approve(self, token_sha=None, kind=R.APPROVE, decision_id="D-20991231-respondendi", ruling_name="respondendi.md",
                commit=True):
        digest = token_sha or R.rule_sha(self.root)
        ruling = self.write(R.RULINGS + ruling_name, f"# Owner ruling\n\nOwner: yes. {kind}{digest}\n")
        with self.path(R.DECISIONS).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": decision_id, "rev": 0, "ruling": f"Owner approves. {kind}{digest}",
                                 "sources": [ruling]}) + "\n")
        if commit:
            self.commit()
        return decision_id

    def plan(self, lot="lot-one", write=True, date="2026-11-10"):
        return R.plan(self.root, lot, [self.completion], [self.admission], [PROMPT], date=date, write=write)

    def audit_all(self, lot="lot-one", verdict="agree", found="no", only=None, date="2026-11-10"):
        for iid in only or R.plan_of(self.root, lot)["audit_sample"]:
            R.audit_record(self.root, lot, iid, "auditor-gpt", "independent_ai", "OpenAI", verdict, found,
                           "Re-read the held revoking order and its effective date; the end date is supported.",
                           date=date, write=True)

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
        self.fx = Fixture(self.root)

    def ledger(self):
        return self.fx.path(R.LEDGER).read_bytes()


class Authorization(Base):
    def test_refuses_without_owner_decision_and_writes_nothing(self):
        before = self.ledger()
        with self.assertRaisesRegex(R.Refused, "no recorded owner decision"):
            self.fx.plan()
        self.assertEqual(self.ledger(), before)
        self.assertFalse(self.fx.path(R.LOTS).exists())

    def test_dry_run_reports_without_authorization(self):
        out = self.fx.plan(write=False)
        self.assertEqual(out["qualifying"], ["EO:2", "EO:3", "EO:4", "EO:5"])
        self.assertEqual(out["audit_sample"], ["EO:2", "EO:3", "EO:4", "EO:5"])      # probation: every member
        self.assertIn("no recorded owner decision", out["authorization"])
        self.assertFalse(out["written"])

    def test_decision_without_owner_ruling_file_is_not_enough(self):
        digest = R.rule_sha(self.root)
        self.fx.write(R.DECISIONS, json.dumps({"id": "D-x", "rev": 0, "ruling": R.APPROVE + digest,
                                               "sources": ["HANDOFF/notes-claude.md"]}) + "\n")
        self.fx.commit()
        with self.assertRaisesRegex(R.Refused, "no recorded owner decision"):
            self.fx.plan()

    def test_uncommitted_approval_is_not_enough(self):
        self.fx.approve(commit=False)
        with self.assertRaisesRegex(R.Refused, "no recorded owner decision"):
            self.fx.plan()

    def test_approval_of_another_rule_text_does_not_carry_over(self):
        self.fx.approve()
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"max_lot_orders": 60', '"max_lot_orders": 600')
        self.fx.write(R.RULE, rule)
        with self.assertRaisesRegex(R.Refused, "no recorded owner decision"):
            self.fx.plan()

    def test_crlf_checkout_keeps_the_rule_hash(self):
        digest = R.rule_sha(self.root)
        self.fx.write(R.RULE, self.fx.path(R.RULE).read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(R.rule_sha(self.root), digest)

    def test_suspension_stops_adoption(self):
        self.fx.approve()
        self.fx.approve(kind=R.SUSPEND, decision_id="D-20991231-suspend", ruling_name="suspend.md")
        with self.assertRaisesRegex(R.Refused, "suspended"):
            self.fx.plan()


class Adoption(Base):
    def setUp(self):
        super().setUp()
        self.decision = self.fx.approve()

    def test_plan_audit_adopt_writes_rows_contract_and_byte_identical_claims(self):
        out = self.fx.run()
        self.assertEqual(out["adopted"], 4)
        self.assertEqual((out["decided_before"], out["decided_after"]), (1, 5))
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
        self.assertTrue(all(self.decision in r["decision_origin"] for r in rows))
        self.assertEqual(json.loads(self.fx.path(R.LOTS + "/lot-one/LOT.json").read_text(encoding="utf-8"))
                         ["independent_human_certifications"], 0)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_nothing_is_adopted_before_the_audits(self):
        self.fx.plan()
        before = self.ledger()
        with self.assertRaisesRegex(R.Refused, "audits missing"):
            self.fx.adopt()
        self.assertEqual(self.ledger(), before)

    def test_one_arm_rejecting_keeps_that_order_out(self):
        self.fx.build_wave(arm_b_rejects=("EO:3",))
        out = self.fx.plan()
        self.assertEqual(out["qualifying"], ["EO:2", "EO:4", "EO:5"])
        self.assertIn("arm B", " ".join({r["instrument_id"]: r["reasons"] for r in out["refused"]}["EO:3"]))

    def test_own_terms_end_needs_its_term_record(self):
        self.fx.build_wave(own_terms=("EO:3",))
        out = self.fx.plan(write=False)
        self.assertNotIn("EO:3", out["qualifying"])
        reasons = " ".join({r["instrument_id"]: r["reasons"] for r in out["refused"]}["EO:3"])
        self.assertIn("TERM", reasons)

    def test_partial_revocation_quote_is_outside_the_lot(self):
        claim = json.loads(self.fx.path(WAVE + "/u01/overlay/REPLACEMENT_PROPOSAL.jsonl").read_text(encoding="utf-8").splitlines()[0])
        params = R.parameters(self.root)
        self.assertEqual(R.lot_check(claim, params), [])
        for quote in ("Executive Order No. 2 is revoked in part, so far as it relates to the Board.",
                      "Executive Order No. 2 is hereby revoked except section 3 thereof.",
                      "Executive Order No. 2 is amended. Sec. 3. Executive Order No. 9001 is revoked."):
            claim["whole_order_end"]["source"]["quote"] = quote
            self.assertTrue(R.lot_check(claim, params), quote)

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

    def test_unadmitted_order_is_refused(self):
        self.fx.build_wave(admitted=["EO:2", "EO:3", "EO:5"])
        self.assertNotIn("EO:4", self.fx.plan(write=False)["qualifying"])

    def test_yes_status_needs_a_rule_that_allows_it(self):
        self.fx.build_wave(status="yes")
        with self.assertRaisesRegex(R.Refused, "no proposal meets the rule"):
            self.fx.plan()

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


class StatusOnly(Base):
    def setUp(self):
        super().setUp()
        self.fx.approve()

    def test_partial_claim_adopts_status_but_files_no_claim(self):
        self.fx.build_wave(partial=("EO:3",))
        self.assertIn("EO:3", self.fx.run()["adoptable"])
        self.assertEqual(R.population(self.root)["statuses"]["EO:3"], "no")
        filed = self.fx.path(R.CLAIMS + "/respondendi-lot-one.jsonl").read_text(encoding="utf-8")
        self.assertNotIn('"instrument_id": "EO:3"', filed)
        rows = self.fx.path(R.LOTS + "/lot-one/ADOPTION_ROWS.csv").read_text(encoding="utf-8")
        self.assertIn("status only, lifecycle claim not filed", rows)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_status_touching_gap_is_refused(self):
        self.fx.build_wave(partial=("EO:3",), gaps=("whole_order_end_evidence:no source",))
        self.assertNotIn("EO:3", self.fx.plan(write=False)["qualifying"])

    def test_failed_status_checker_step_is_refused(self):
        self.fx.build_wave(partial=("EO:3",), failed_steps=("ending_or_current_basis",))
        self.assertNotIn("EO:3", self.fx.plan(write=False)["qualifying"])

    def test_rule_without_status_only_refuses_partial_claims(self):
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"status_only": true', '"status_only": false')
        self.fx.write(R.RULE, rule)
        self.fx.approve(decision_id="D-20991231-nostatusonly", ruling_name="nso.md")
        self.fx.build_wave(partial=("EO:3",))
        self.assertNotIn("EO:3", self.fx.plan(write=False)["qualifying"])


class Audits(Base):
    def setUp(self):
        super().setUp()
        self.fx.approve()
        self.fx.plan()

    def record(self, iid, verdict="agree", found="no", family="OpenAI", role="independent_ai", auditor="auditor-1"):
        return R.audit_record(self.root, "lot-one", iid, auditor, role, family, verdict, found,
                              "Re-read the held revoking order and its effective date; the end date is supported.",
                              date="2026-11-10", write=True)

    def adjudicate(self, iid, finding, family="Google", adjudicator="adjudicator-1"):
        return R.adjudicate(self.root, "lot-one", iid, adjudicator, "independent_ai", family, finding,
                            "Read the revoking order and the target's text side by side; the finding follows.",
                            date="2026-11-10", write=True)

    def test_ai_auditor_must_be_another_family(self):
        with self.assertRaisesRegex(R.Refused, "different from the reviewers"):
            self.record("EO:2", family="Anthropic")

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
            self.adjudicate("EO:3", "auditor_wrong", family="OpenAI")
        self.adjudicate("EO:3", "auditor_wrong")
        self.assertEqual(self.fx.adopt()["adopted"], 4)

    def test_confirmed_error_is_not_adopted_and_counts(self):
        for iid in ("EO:2", "EO:4", "EO:5"):
            self.record(iid)
        self.record("EO:3", verdict="disagree", found="yes")
        self.adjudicate("EO:3", "confirmed_error")
        out = self.fx.adopt()
        self.assertEqual(out["adopted"], 3)
        self.assertNotIn("EO:3", R.population(self.root)["statuses"])
        state = R.status(self.root)["strata"][0]
        self.assertEqual((state["confirmed_errors"], state["audits_needed"]), (1, 93))
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_two_confirmed_errors_stop_the_stratum_until_the_owner_resumes(self):
        for iid in ("EO:2", "EO:3"):
            self.record(iid, verdict="disagree", found="yes")
            self.adjudicate(iid, "confirmed_error")
        stratum = R.plan_of(self.root, "lot-one")["members"][0]["stratum"]
        for iid in ("EO:4", "EO:5"):
            self.record(iid)
        with self.assertRaisesRegex(R.Refused, "stopped strata"):
            self.fx.adopt()
        self.fx.approve(token_sha=stratum, kind=R.RESUME, decision_id="D-20991231-resume", ruling_name="resume.md")
        self.assertEqual(self.fx.adopt()["adopted"], 2)

    def test_steady_state_samples_after_the_bound_is_met(self):
        stratum = R.plan_of(self.root, "lot-one")["members"][0]["stratum"]
        fake = "".join(json.dumps({"lot": f"old-{i}", "stratum": stratum, "instrument_id": f"EO:{100 + i}",
                                   "verdict": "agree", "date": "2026-11-01"}) + "\n" for i in range(59))
        self.fx.write(R.REGISTER + "/AUDITS.jsonl", fake)
        self.fx.ids, self.fx.controls = ["EO:6", "EO:7", "EO:8"], ["EO:7", "EO:8"]
        self.fx.build_wave("u02")
        out = self.fx.plan(lot="lot-two", write=False)
        self.assertFalse(out["strata"][stratum]["probation"])
        self.assertEqual(len(out["audit_sample"]), 2)                     # 20% of 3 rounds up, at least 2

    def test_reversal_keeps_the_claim_with_a_hold(self):
        for iid in ("EO:2", "EO:3", "EO:4", "EO:5"):
            self.record(iid)
        self.fx.adopt()
        R.reverse(self.root, "lot-one", "EO:3", "Later audit found the revoking order postdates the cutoff.", write=True)
        self.assertNotIn("EO:3", R.population(self.root)["statuses"])
        self.assertIn('"instrument_id": "EO:3"', self.fx.path(R.CLAIMS + "/respondendi-lot-one.jsonl").read_text(encoding="utf-8"))
        holds = [json.loads(l) for l in self.fx.path(R.HOLDS).read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual([h["instrument_id"] for h in holds], ["EO:3"])
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


class LotKinds(Base):
    """Every kind opens on its own probation stratum; a kind whose route is not on main cannot be met."""

    def setUp(self):
        super().setUp()
        self.fx.approve()

    def strata(self, out):
        return {m["instrument_id"]: m["stratum"] for m in R.plan_of(self.root, "lot-one")["members"]} if out.get("written") else {}

    def reasons(self, out, iid):
        return " ".join({r["instrument_id"]: r["reasons"] for r in out["refused"]}.get(iid, []))

    def test_each_active_and_future_kind_qualifies_with_its_records(self):
        self.fx.build_wave(lot_kinds={"EO:2": "own_terms", "EO:3": "spent"}, kinds=("date_shift", "later_event_removed"))
        out = self.fx.plan()
        self.assertEqual(out["qualifying"], ["EO:2", "EO:3", "EO:4", "EO:5"])
        strata = self.strata(out)
        self.assertEqual({s.split(":")[1] for s in strata.values()}, {"own_terms", "spent_on_issue", "express_named_revocation"})
        self.assertEqual(out["audit_sample"], ["EO:2", "EO:3", "EO:4", "EO:5"])          # every new stratum on probation
        self.fx.audit_all()
        self.assertEqual(self.fx.adopt()["adopted"], 4)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_a_route_not_on_main_stays_inactive(self):
        self.fx.build_wave(lot_kinds={"EO:2": "spent", "EO:3": "parent"}, no_basis=("EO:2", "EO:3"))
        out = self.fx.plan(write=False)
        self.assertNotIn("EO:2", out["qualifying"])
        self.assertIn("inactive until: F5", self.reasons(out, "EO:2"))
        self.assertIn("inactive until: F5", self.reasons(out, "EO:3"))

    def test_follows_parent_checks_the_parents_ending_quote(self):
        self.fx.build_wave(lot_kinds={"EO:2": "parent"})
        self.assertIn("EO:2", self.fx.plan(write=False)["qualifying"])

    def test_yes_needs_a_current_record_and_a_later_event_control(self):
        self.fx.build_wave(lot_kinds={"EO:2": "yes"})
        out = self.fx.plan(write=False)
        self.assertIn("later_event_removed", self.reasons(out, "EO:2"))
        self.fx.build_wave(lot_kinds={"EO:2": "yes"}, kinds=("date_shift", "later_event_removed"))
        self.assertIn("EO:2", self.fx.plan(write=False)["qualifying"])
        self.fx.build_wave(lot_kinds={"EO:2": "yes"}, kinds=("date_shift", "later_event_removed"), no_basis=("EO:2",))
        self.assertIn("inactive until: F3", self.reasons(self.fx.plan(write=False), "EO:2"))

    def test_yes_with_a_held_whole_scope_ending_lead_is_refused(self):
        self.fx.build_wave(lot_kinds={"EO:2": "yes"}, kinds=("date_shift", "later_event_removed"), extra_act=("EO:2",))
        self.assertIn("contradicts YES", self.reasons(self.fx.plan(write=False), "EO:2"))

    def test_outer_bound_waits_for_the_owner(self):
        self.fx.build_wave(lot_kinds={"EO:2": "outer"})
        self.assertIn("outer-bound ask", self.reasons(self.fx.plan(write=False), "EO:2"))

    def test_working_text_needs_the_f6_marker_and_is_its_own_stratum(self):
        self.fx.build_wave(working=("EO:2",), working_ok=False)
        self.assertIn("working texts inactive until: F6", self.reasons(self.fx.plan(write=False), "EO:2"))
        self.fx.build_wave(working=("EO:2",))
        out = self.fx.plan()
        strata = self.strata(out)
        self.assertIn(":working:", strata["EO:2"])
        self.assertNotEqual(strata["EO:2"], strata["EO:3"])

    def test_a_stopped_stratum_does_not_stop_the_others(self):
        self.fx.build_wave(lot_kinds={"EO:2": "own_terms", "EO:3": "own_terms"})
        self.fx.plan()
        strata = self.strata({"written": True})
        for iid in ("EO:2", "EO:3"):
            R.audit_record(self.root, "lot-one", iid, "auditor-gpt", "independent_ai", "OpenAI", "disagree", "yes",
                           "The order's term was extended by a later order the claim does not list.", date="2026-11-10", write=True)
            R.adjudicate(self.root, "lot-one", iid, "adjudicator-1", "independent_ai", "Google", "confirmed_error",
                         "Read the extending order; the term did not expire on the claimed date.", date="2026-11-10", write=True)
        self.fx.audit_all(only=["EO:4", "EO:5"])
        self.assertTrue(R.stratum_state(self.root, strata["EO:2"], R.parameters(self.root))["stopped"])
        out = self.fx.adopt()
        self.assertEqual(out["adopted"], 2)
        self.assertEqual(sorted(R.population(self.root)["statuses"]), ["EO:1", "EO:4", "EO:5"])

    def test_yes_stratum_stops_on_one_confirmed_error(self):
        params = R.parameters(self.root)
        self.assertEqual(R.effective(params, "yes_current")["stop_confirmed_errors_in_59"], 1)
        self.assertEqual(R.effective(params, "express_named_revocation")["stop_confirmed_errors_in_59"], 2)


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
        self.assertEqual(params["statuses_allowed"], ["no", "yes"])
        self.assertGreaterEqual(params["min_blind_arms"], 2)
        self.assertEqual(set(params["kinds"]), {"express_named_revocation", "own_terms", "spent_on_issue",
                                                "follows_parent", "yes_current", "outer_bound"})


if __name__ == "__main__":
    unittest.main()
