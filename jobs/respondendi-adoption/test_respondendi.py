"""Respondendi refuses without the owner's exact rule, adopts only what meets every condition, and can be undone."""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import respondendi as R  # noqa: E402

WAVE = "research/excavator/fixture-wave"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=R.ROW_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in R.ROW_FIELDS})
    return stream.getvalue().encode("utf-8")


def canonical_ids(ids):
    return R.canon(sorted(ids))


class Fixture:
    """A tiny repository: census EO:1-EO:9, EO:1 decided, a wave whose overlay proposals cover EO:2-EO:5."""

    def __init__(self, root, rule_text=None, ids=("EO:2", "EO:3", "EO:4", "EO:5"), control="EO:5"):
        self.root = Path(root)
        self.ids, self.control = list(ids), control
        self.write(R.RULE, (rule_text or (HERE / "RULE.md").read_text(encoding="utf-8")).encode("utf-8"))
        census = [{"id": f"EO:{n}"} for n in range(1, 10)]
        stream = io.StringIO(newline="")
        w = csv.DictWriter(stream, fieldnames=["id"], lineterminator="\n")
        w.writeheader()
        w.writerows(census)
        self.write("census.csv", stream.getvalue().encode("utf-8"))
        base = [{"instrument_id": "EO:1", "provisional_substantive_status": "yes", "human_certified_by_this_release": "no"}]
        base_bytes = csv_bytes(base)
        self.write(R.LEDGER, base_bytes)
        parsed = list(csv.DictReader(io.StringIO(base_bytes.decode("utf-8"), newline="")))
        contract = {
            "schema": "eo-accepted-population-contract/v1",
            "census": {"path": "census.csv", "count": 9, "identity_sha256": canonical_ids([c["id"] for c in census])},
            "historical_status_baseline": {"path": R.LEDGER, "bytes": len(base_bytes), "count": 1,
                                           "sha256": sha(base_bytes), "rows_sha256": R.canon(parsed)},
            "accepted_additions": [],
        }
        self.write(R.CONTRACT, (json.dumps(contract, indent=2) + "\n").encode("utf-8"))
        self.write(R.DECISIONS, b"")
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

    def build_wave(self, batch="u01", *, arm_b_rejects=(), control_missed=False, status="no", checker_fail=(),
                   reviewer_same_as_arm=False, admitted=None, partial=(), gaps=("unresolved_material_gaps:clause 2 end undated",),
                   failed_steps=()):
        u = f"{WAVE}/{batch}"
        COMP = u + "/completion"
        claims, members, outcomes, checks = [], [], [], {}
        for iid in self.ids:
            n = iid.split(":")[1]
            b = f"{u}/overlay/EO_{n}/proposal-v1"
            reviewer = "arm-A" if reviewer_same_as_arm else f"status-reviewer-{n}"
            review = {"schema": "eo-status-overlay-review/v1", "decision": "accept", "independence_confirmed": True,
                      "source_checks_confirmed": True, "instrument_id": iid, "reviewer": reviewer,
                      "reviewer_role": "independent_ai"}
            decision = {"instrument_id": iid, "approved": True, "recommended_provisional_status": status}
            dsha, rsha = R.canon(decision), R.canon(review)
            proposal = {"recommended_provisional_status": status, "decision_sha256": dsha, "review_sha256": rsha}
            for name, value in (("EVIDENCE.json", {"instrument_id": iid}), ("STATUS_DECISION.json", decision),
                                ("STATUS_REVIEW.json", review), ("PROMOTION_PROPOSAL.json", proposal)):
                self.wjson(f"{b}/{name}", value)
            claim = {"instrument_id": iid, "whole_order_status": status, "whole_order_end": {"date": "1950-01-01"},
                     "claim_kit": {"agent": "producer-x", "status_overlay": {"decision_sha256": dsha, "review_sha256": rsha}}}
            claims.append(claim)
            csha = R.canon(claim)
            kind = "partial_research" if iid in partial else "whole_case"
            if kind == "partial_research":
                claim["whole_order_end"]["source"] = {"text_path": "x.txt"}
                csha = R.canon(claim)
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
        planted = copy.deepcopy(next(c for c in claims if c["instrument_id"] == self.control))
        planted["whole_order_end"]["date"] = "1947-01-01"
        psha = R.canon(planted)
        reviews = {}
        for arm in "AB":
            rows = []
            for claim in claims:
                csha = R.canon(claim)
                if claim["instrument_id"] == self.control:
                    continue
                verdict = "rejected" if (arm == "B" and claim["instrument_id"] in arm_b_rejects) else "upheld"
                rows.append({"instrument_id": claim["instrument_id"], "claim_sha256": csha, "reviewer": f"arm-{arm}",
                             "model_family": "Anthropic", "independent": True, "separate_context": True,
                             "scope": "partial_research" if claim["instrument_id"] in partial else "whole_case",
                             "verdict": verdict})
            rows.append({"instrument_id": self.control, "claim_sha256": psha, "reviewer": f"arm-{arm}",
                         "model_family": "Anthropic", "independent": True, "separate_context": True, "scope": "whole_case",
                         "verdict": "upheld" if (control_missed and arm == "B") else "rejected",
                         "defects": [{"field": "whole_order_end.date"}]})
            self.write(f"{u}/reviews/BLIND_REVIEW_{arm}.jsonl", "".join(json.dumps(r) + "\n" for r in rows))
            genuine = next(c for c in claims if c["instrument_id"] == self.control)
            self.write(f"{u}/reviews/AFTER_REVEAL_{arm}.jsonl", json.dumps(
                {"instrument_id": self.control, "claim_sha256": R.canon(genuine), "reviewer": f"arm-{arm}",
                 "model_family": "Anthropic", "independent": True, "separate_context": True, "scope": "whole_case",
                 "verdict": "upheld_after_reveal"}) + "\n")
            reviews[arm] = True
        adj = self.wjson(f"{COMP}/CONTROL_ADJUDICATION_EO_{self.control.split(':')[1]}.json", {"caught": not control_missed})
        manifest = {"schema": "eo-claim-kit-completion/v1", "agent": "producer-x", "members": members,
                    "controls": [{"instrument_id": self.control, "planted_claim_sha256": psha, "adjudication": self.ref(adj)}],
                    "receipts": [self.ref(f"{u}/reviews/{k}_{a}.jsonl") for a in "AB" for k in ("BLIND_REVIEW", "AFTER_REVEAL")]}
        self.wjson(f"{COMP}/COMPLETION.json", manifest)
        cv = COMP + "/complete-v1"
        prop_rel = self.write(f"{u}/overlay/REPLACEMENT_PROPOSAL.jsonl",
                              "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in claims))
        self.wjson(cv + "/INPUTS.json", {"preserved_receipts": {f"{COMP}/COMPLETION.json": sha(self.path(f"{COMP}/COMPLETION.json").read_bytes())}})
        self.wjson(cv + "/PUBLICATION.json", {"mode": "replacement_proposal", "written": True, "path": prop_rel,
                                              "sha256": sha(self.path(prop_rel).read_bytes()),
                                              "independent_human_certifications": 0})
        self.wjson(cv + "/EXCEPTIONS.json", [])
        self.wjson(cv + "/TALLY.json", {"controls": [{"instrument_id": self.control, "caught": not control_missed}],
                                        "outcomes": outcomes})
        self.wjson(cv + "/TRACKER_CHECKER.json", {"by_instrument": checks})
        self.admission = self.wjson(u + "/packet/ADMISSION.json", {
            "schema": "eo-claim-kit-admission/v1", "bentham_action": "status_assignment.undecided", "agent": "producer-x",
            "instrument_ids": sorted(admitted if admitted is not None else self.ids)})
        self.completion = cv

    def approve(self, token_sha=None, kind=R.APPROVE, decision_id="D-20991231-respondendi", ruling_name="respondendi.md"):
        digest = token_sha or R.rule_sha(self.root)
        ruling = self.write(R.RULINGS + ruling_name, f"# Owner ruling\n\nOwner: yes. {kind}{digest}\n")
        with self.path(R.DECISIONS).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": decision_id, "rev": 0, "ruling": f"Owner approves. {kind}{digest}",
                                 "sources": [ruling]}) + "\n")
        return decision_id

    def adopt(self, lot="lot-one", write=True, date="2026-11-10"):
        return R.adopt(self.root, lot, [self.completion], [self.admission], date=date, write=write)


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
            self.fx.adopt()
        self.assertEqual(self.ledger(), before)
        self.assertFalse(self.fx.path(R.LOTS).exists())

    def test_dry_run_reports_without_authorization(self):
        out = self.fx.adopt(write=False)
        self.assertEqual(out["qualifying"], ["EO:2", "EO:3", "EO:4", "EO:5"])
        self.assertIn("no recorded owner decision", out["authorization"])
        self.assertFalse(out["written"])

    def test_decision_without_owner_ruling_file_is_not_enough(self):
        digest = R.rule_sha(self.root)
        self.fx.write(R.DECISIONS, json.dumps({"id": "D-x", "rev": 0, "ruling": R.APPROVE + digest,
                                               "sources": ["HANDOFF/notes-claude.md"]}) + "\n")
        with self.assertRaisesRegex(R.Refused, "no recorded owner decision"):
            self.fx.adopt()

    def test_approval_of_another_rule_text_does_not_carry_over(self):
        self.fx.approve()
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"max_lot_orders": 60', '"max_lot_orders": 600')
        self.fx.write(R.RULE, rule)
        with self.assertRaisesRegex(R.Refused, "no recorded owner decision"):
            self.fx.adopt()

    def test_crlf_checkout_keeps_the_rule_hash(self):
        digest = R.rule_sha(self.root)
        data = self.fx.path(R.RULE).read_bytes().replace(b"\n", b"\r\n")
        self.fx.write(R.RULE, data)
        self.assertEqual(R.rule_sha(self.root), digest)

    def test_suspension_stops_adoption(self):
        self.fx.approve()
        self.fx.approve(kind=R.SUSPEND, decision_id="D-20991231-suspend", ruling_name="suspend.md")
        with self.assertRaisesRegex(R.Refused, "suspended"):
            self.fx.adopt()


class Adoption(Base):
    def setUp(self):
        super().setUp()
        self.decision = self.fx.approve()

    def test_adopts_rows_contract_and_byte_identical_claims(self):
        out = self.fx.adopt()
        self.assertEqual(out["adopted"], 4)
        self.assertEqual((out["decided_before"], out["decided_after"]), (1, 5))
        state = R.population(self.root)
        self.assertEqual(state["statuses"], {"EO:1": "yes", "EO:2": "no", "EO:3": "no", "EO:4": "no", "EO:5": "no"})
        proposal = self.fx.path(WAVE + "/u01/overlay/REPLACEMENT_PROPOSAL.jsonl").read_bytes()
        self.assertEqual(self.fx.path(R.CLAIMS + "/respondendi-lot-one.jsonl").read_bytes(), proposal)
        contract = json.loads(self.fx.path(R.CONTRACT).read_text(encoding="utf-8"))
        entry = contract["accepted_additions"][-1]
        self.assertEqual(entry["standing_rule"]["decision"], self.decision)
        self.assertEqual(entry["count"], 4)
        pinned_paths = {p["path"] for p in entry["authorization_pins"]}
        self.assertTrue({R.LOTS + "/lot-one/RULE_AT_ADOPTION.md", R.RULINGS + "respondendi.md", R.LOTS + "/lot-one/LOT.json"} <= pinned_paths)
        rows = list(csv.DictReader(io.StringIO(self.fx.path(R.LOTS + "/lot-one/ADOPTION_ROWS.csv").read_text(encoding="utf-8"))))
        self.assertTrue(all(r["human_certified_by_this_release"] == "no" for r in rows))
        self.assertTrue(all(self.decision in r["decision_origin"] for r in rows))
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))
        receipt = json.loads(self.fx.path(R.LOTS + "/lot-one/LOT.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["independent_human_certifications"], 0)
        self.assertTrue(receipt["probation"])
        self.assertEqual(len(receipt["audit_sample"]), 2)          # 34% of 4 rounds up to 2, the probation minimum

    def test_sample_is_deterministic_from_the_receipt(self):
        params = R.parameters(self.root)
        a = R.sample_for("abc", ["EO:2", "EO:3", "EO:4", "EO:5"], params, True)
        self.assertEqual(a, R.sample_for("abc", ["EO:5", "EO:4", "EO:3", "EO:2"], params, True))
        self.assertEqual(len(R.sample_for("abc", [f"EO:{n}" for n in range(100)], params, False)), 10)

    def test_one_arm_rejecting_keeps_that_order_out(self):
        self.fx.build_wave(arm_b_rejects=("EO:3",))
        out = self.fx.adopt()
        self.assertEqual(out["qualifying"], ["EO:2", "EO:4", "EO:5"])
        refused = {r["instrument_id"]: r["reasons"] for r in out["refused"]}
        self.assertIn("arm B", refused["EO:3"][0])

    def test_missed_control_refuses_the_whole_completion(self):
        self.fx.build_wave(control_missed=True)
        with self.assertRaisesRegex(R.Refused, "did not reject planted control"):
            self.fx.adopt()

    def test_unadmitted_order_is_refused(self):
        self.fx.build_wave(admitted=["EO:2", "EO:3", "EO:5"])
        out = self.fx.adopt()
        self.assertNotIn("EO:4", out["qualifying"])

    def test_yes_status_needs_a_rule_that_allows_it(self):
        self.fx.build_wave(status="yes")
        with self.assertRaisesRegex(R.Refused, "no proposal meets the rule"):
            self.fx.adopt()

    def test_checker_failure_is_refused(self):
        self.fx.build_wave(checker_fail=("EO:2",))
        out = self.fx.adopt()
        self.assertNotIn("EO:2", out["qualifying"])

    def test_status_reviewer_must_differ_from_the_arms(self):
        self.fx.build_wave(reviewer_same_as_arm=True)
        with self.assertRaisesRegex(R.Refused, "no proposal meets the rule"):
            self.fx.adopt()

    def test_tampered_manifest_is_refused(self):
        rel = WAVE + "/u01/completion/COMPLETION.json"
        data = json.loads(self.fx.path(rel).read_text(encoding="utf-8"))
        data["agent"] = "someone-else"
        self.fx.wjson(rel, data)
        with self.assertRaisesRegex(R.Refused, "differs from the manifest"):
            self.fx.adopt()

    def test_decided_order_is_never_readopted(self):
        self.fx.adopt()
        with self.assertRaisesRegex(R.Refused, "no proposal meets the rule"):
            self.fx.adopt(lot="lot-two")

    def test_lot_size_limit(self):
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"max_lot_orders": 60', '"max_lot_orders": 3')
        self.fx.write(R.RULE, rule)
        self.fx.approve(decision_id="D-20991231-small", ruling_name="small.md")
        with self.assertRaisesRegex(R.Refused, "per lot"):
            self.fx.adopt()

    def test_failed_population_check_rolls_back(self):
        ledger, contract = self.ledger(), self.fx.path(R.CONTRACT).read_bytes()
        original = R.population
        calls = {"n": 0}

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
        out = self.fx.adopt()
        self.assertIn("EO:3", out["qualifying"])
        self.assertEqual(R.population(self.root)["statuses"]["EO:3"], "no")
        filed = self.fx.path(R.CLAIMS + "/respondendi-lot-one.jsonl").read_text(encoding="utf-8")
        self.assertNotIn('"instrument_id": "EO:3"', filed)
        rows = self.fx.path(R.LOTS + "/lot-one/ADOPTION_ROWS.csv").read_text(encoding="utf-8")
        self.assertIn("status only, lifecycle claim not filed", rows)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))
        R.reverse(self.root, "lot-one", "EO:3", "Audit found the revoking order postdates the cutoff.", write=True)
        self.assertNotIn("EO:3", R.population(self.root)["statuses"])
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_status_touching_gap_is_refused(self):
        self.fx.build_wave(partial=("EO:3",), gaps=("whole_order_end_evidence:no source",))
        out = self.fx.adopt()
        self.assertNotIn("EO:3", out["qualifying"])

    def test_failed_status_checker_step_is_refused(self):
        self.fx.build_wave(partial=("EO:3",), failed_steps=("ending_or_current_basis",))
        out = self.fx.adopt()
        self.assertNotIn("EO:3", out["qualifying"])

    def test_rule_without_status_only_refuses_partial_claims(self):
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"status_only": true', '"status_only": false')
        self.fx.write(R.RULE, rule)
        self.fx.approve(decision_id="D-20991231-nostatusonly", ruling_name="nso.md")
        self.fx.build_wave(partial=("EO:3",))
        out = self.fx.adopt()
        self.assertNotIn("EO:3", out["qualifying"])


class AuditsAndReversal(Base):
    def setUp(self):
        super().setUp()
        self.fx.approve()
        self.out = self.fx.adopt()
        self.sample = self.out["audit_sample"]

    def record(self, iid, verdict="agree", found="no", family="OpenAI", role="independent_ai", auditor="auditor-1"):
        return R.audit_record(self.root, "lot-one", iid, auditor, role, family, verdict, found,
                              "Re-read the held revoking order and its effective date; the end date is supported.",
                              date="2026-11-11", write=True)

    def test_ai_auditor_must_be_another_family(self):
        with self.assertRaisesRegex(R.Refused, "different from the reviewers"):
            self.record(self.sample[0], family="Anthropic")

    def test_auditor_must_not_be_a_reviewer(self):
        with self.assertRaisesRegex(R.Refused, "must not be the producer or a reviewer"):
            self.record(self.sample[0], auditor="arm-A")

    def test_agreeing_audits_clear_the_queue(self):
        for iid in self.sample:
            self.record(iid)
        self.assertEqual(R.pending_audits(self.root), [])
        s = R.status(self.root)
        self.assertEqual((s["audits"], s["disagreements"], s["agree_streak"]), (2, 0, 2))
        self.assertTrue(s["probation"])

    def test_disagreement_stops_then_reverse_then_owner_resume(self):
        bad = self.sample[0]
        out = self.record(bad, verdict="disagree", found="yes")
        stop_id = out["stop_id"]
        self.fx.ids = ["EO:6", "EO:7"]
        self.fx.control = "EO:7"
        self.fx.build_wave("u02")
        with self.assertRaisesRegex(R.Refused, "adoption stopped"):
            self.fx.adopt(lot="lot-two")
        R.reverse(self.root, "lot-one", bad, "Audit found the order still in force at the cutoff.", write=True)
        state = R.population(self.root)
        self.assertNotIn(bad, state["statuses"])
        self.assertEqual(len(state["statuses"]), 4)
        claims = self.fx.path(R.CLAIMS + "/respondendi-lot-one.jsonl").read_text(encoding="utf-8")
        self.assertNotIn(f'"instrument_id": "{bad}"', claims)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))
        self.fx.approve(token_sha=stop_id, kind=R.RESUME, decision_id="D-20991231-resume", ruling_name="resume.md")
        self.record(self.sample[1])
        out = self.fx.adopt(lot="lot-two", date="2026-11-12")
        self.assertEqual(out["adopted"], 2)
        self.assertTrue(R.verify(self.root)["ok"], R.verify(self.root))

    def test_audit_debt_blocks_new_lots(self):
        rule = self.fx.path(R.RULE).read_text(encoding="utf-8").replace('"max_pending_audits": 20', '"max_pending_audits": 1')
        self.fx.write(R.RULE, rule)
        self.fx.approve(decision_id="D-20991231-debt", ruling_name="debt.md")
        self.fx.ids, self.fx.control = ["EO:6", "EO:7"], "EO:7"
        self.fx.build_wave("u02")
        with self.assertRaisesRegex(R.Refused, "audit debt"):
            self.fx.adopt(lot="lot-two")

    def test_old_pending_audit_blocks_new_lots(self):
        self.fx.ids, self.fx.control = ["EO:6", "EO:7"], "EO:7"
        self.fx.build_wave("u02")
        with self.assertRaisesRegex(R.Refused, "older than"):
            self.fx.adopt(lot="lot-two", date="2026-12-31")

    def test_verify_catches_a_hand_edited_lot_receipt(self):
        rel = R.LOTS + "/lot-one/LOT.json"
        data = json.loads(self.fx.path(rel).read_text(encoding="utf-8"))
        data["members"][0]["status"] = "yes"
        self.fx.wjson(rel, data)
        self.assertFalse(R.verify(self.root)["ok"])

    def test_report_states_zero_human_certification(self):
        text = R.report_text(self.root)
        self.assertIn("Human-certified whole lifecycles: 0", text)
        self.assertIn("lot-one", text)


class Statistics(unittest.TestCase):
    def test_upper_bound_matches_the_jacquard_rule(self):
        self.assertAlmostEqual(R.upper_bound(0, 59), 1 - 0.05 ** (1 / 59), places=4)
        self.assertLess(R.upper_bound(0, 59), 0.05)
        self.assertGreater(R.upper_bound(1, 59), 0.05)

    def test_shipped_rule_parses(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / R.RULE).parent.mkdir(parents=True)
        shutil.copy(HERE / "RULE.md", root / R.RULE)
        params = R.parameters(root)
        self.assertEqual(params["statuses_allowed"], ["no"])
        self.assertGreaterEqual(params["min_blind_arms"], 2)


if __name__ == "__main__":
    unittest.main()
