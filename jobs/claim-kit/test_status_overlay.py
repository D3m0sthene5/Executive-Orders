"""Real compiler/assembler handoff fixtures; no corpus statuses are promoted."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import assemble as A
import status_overlay as O
import test_build as F

write_json, write_jsonl = F.write_json, F.write_jsonl

REPO = HERE.parents[1]


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = F.BuildIntegrationTests("test_whole_population_including_yes_no_undecided_and_missing")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo, self.out = self.fixture.repo, self.fixture.out
        # This is an isolated six-identity fixture. EO:1 is explicitly undecided.
        self.fixture.status.write_text("instrument_id,provisional_substantive_status\nEO:2,no\nEO:3,yes\nEO:5,no\nEO:6,no\n", encoding="utf-8")
        code = self.repo / "jobs/claim-kit"
        code.mkdir(parents=True)
        for name in O.CODE_FILES:
            (code / name).write_bytes((HERE / name).read_bytes())
        history = self.repo / "jobs/status-history/history.py"
        history.parent.mkdir(parents=True)
        history.write_bytes((REPO / "jobs/status-history/history.py").read_bytes())
        self.fixture.run_build()
        self.packet = self.history_packet()
        self.telemetry = {}
        self.evidence = O.freeze_evidence(self.repo, self.out, self.packet, self.telemetry)
        self.decision = O.extend_decision(self.packet, self.evidence, "synthetic-producer")
        self.ending = next(i for i in self.evidence["base_dossier"]["actor_provisions"]
                           if self.evidence["base_dossier"]["evidence"][i]["actor_id"] == "EO:5")
        self.decision.update(approved=True, identity_confirmed=True, basis_review_confirmed=True,
                             earlier_endings_checked=True, partial_scope_checked=True, savings_checked=True,
                             recommended_provisional_status="no", material_gaps=[],
                             observations_reviewed=["OBS:synthetic-1"], basis_evidence_ids=[self.ending],
                             rationale="The synthetic original and exact acting provision were read; this fixture expressly ends every continuing duty.")
        self.review = self.accepted_review(self.decision)

    def history_packet(self):
        row = {"executive_order_number": "1", "title": "Synthetic research fixture",
               "disposition_notes": "Revoked by Executive Order 5."}
        raw = json.dumps({"results": [row]}, sort_keys=True).encode()
        compressed = gzip.compress(raw, mtime=0)
        rel = "jobs/synthetic-history/data/held.json.gz"
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(compressed)
        obs = {"id": "OBS:synthetic-1", "instrument_id": "EO:1", "kind": "api_observation",
               "text": row["disposition_notes"], "source": {
                   "compressed_path": rel, "compressed_sha256": O._sha(compressed),
                   "sha256": O._sha(raw), "json_pointer": "/results/0",
                   "record_sha256": A.canonical_sha(row),
                   "text_sha256": O._sha(row["disposition_notes"].encode())}}
        h = {"schema": "eo-status-history/v1", "instrument_id": "EO:1", "legal_cutoff": O.CUTOFF,
             "provisional_status": None, "observation_ids": [obs["id"]], "event_ids": [],
             "observation_fingerprints": {obs["id"]: A.canonical_sha(obs)},
             "event_fingerprints": {}, "flags": [], "temporal_constraints_LEADS_ONLY": [],
             "accepted_legal_intervals": [], "current_legal_status": None, "human_certified": False}
        O._seal(h)
        out = self.repo / "jobs/status-history/output"
        name = "histories/EO_1.json"
        write_json(out / name, h)
        write_json(out / "INDEX.json", [{"instrument_id": "EO:1", "history": name,
                                         "fingerprint": h["fingerprint"]}])
        shard = O._sha(obs["id"].encode())[:2]
        write_jsonl(out / "observations" / (shard + ".jsonl"), [obs])
        return {"history": h, "observations": [obs], "events": [], "supporting_observations": []}

    def accepted_review(self, decision):
        review = O.blank_review(decision, self.evidence, "synthetic-independent-reviewer")
        review.update(independence_confirmed=True, source_checks_confirmed=True, decision="accept",
                      checked_evidence_ids=[self.ending, self.evidence["base_dossier"]["original_source_id"]],
                      rationale="The independent synthetic review checked the frozen original and exact acting passage, including scope and earlier endings.")
        return review

    def propose(self):
        return O.propose(self.repo, self.decision, self.review, self.evidence)

    def assert_rejects(self, message):
        with self.assertRaisesRegex(ValueError, message):
            self.propose()

    def reseal_changed_fixture_evidence(self):
        dossier = self.evidence["base_dossier"]
        dossier["fingerprint"] = A.canonical_sha(dossier)
        O._seal(self.evidence)
        self.decision["evidence_sha256"] = self.evidence["fingerprint"]
        self.review = self.accepted_review(self.decision)

    def test_reviewed_proposal_has_no_authority_and_experimental_full_dossier(self):
        protected = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        proposal = self.propose()
        self.assertEqual(proposal["schema"], O.PROPOSAL_SCHEMA)
        self.assertFalse(proposal["owner_acceptance"]["accepted"])
        self.assertFalse(proposal["canonical_status_written"])
        dossier = O.experimental_dossier(self.repo, proposal, self.decision, self.review, self.evidence)
        self.assertEqual(dossier["whole_order_status"], "no")
        self.assertEqual(dossier["fingerprint"], A.canonical_sha(dossier))
        self.assertTrue(dossier["clauses"])
        self.assertTrue(dossier["actor_provisions"])
        self.assertTrue(dossier["chain"]["events"])
        self.assertTrue(dossier["machine_searches"])
        self.assertFalse(dossier["status_overlay"]["owner_accepted"])
        self.assertEqual({p: p.read_bytes() for p in protected}, protected)
        self.assertIsNone(self.evidence["base_dossier"]["whole_order_status"])

    def test_blank_decision_and_review_cannot_promote(self):
        blank = O.extend_decision(self.packet, self.evidence, "producer")
        self.assertFalse(blank["approved"])
        self.assertIsNone(blank["recommended_provisional_status"])
        with self.assertRaisesRegex(ValueError, "producer_approved_required"):
            O.propose(self.repo, blank, {}, self.evidence)
        self.review = O.blank_review(self.decision, self.evidence, "reviewer")
        self.assert_rejects("independent_review_accept_required")

    def test_missing_and_rejected_reviews_fail(self):
        self.review = None
        self.assert_rejects("independently_pinned_review_required")
        self.review = self.accepted_review(self.decision)
        self.review["decision"] = "reject"
        self.assert_rejects("independent_review_accept_required")

    def test_same_reviewer_is_not_independent(self):
        self.review["reviewer"] = " SYNTHETIC-PRODUCER "
        self.assert_rejects("different_independent_reviewer_required")

    def test_review_pins_exact_producer_decision(self):
        self.decision["rationale"] += " Changed legal scope."
        self.assert_rejects("stale_review_decision")

    def test_review_pins_evidence_and_history(self):
        for key, error in (("evidence_sha256", "stale_review_evidence"),
                           ("history_sha256", "stale_review_history")):
            with self.subTest(key=key):
                review = deepcopy(self.review)
                review[key] = "0" * 64
                with self.assertRaisesRegex(ValueError, error):
                    O.propose(self.repo, self.decision, review, self.evidence)

    def test_wrong_identity_is_rejected_at_each_boundary(self):
        self.decision["instrument_id"] = "EO:999"
        self.assert_rejects("decision_identity_mismatch")
        self.decision["instrument_id"] = "EO:1"
        self.review["instrument_id"] = "EO:2"
        self.assert_rejects("review_identity_mismatch")

    def test_snapshot_only_status_cannot_be_proposed(self):
        self.decision["basis_evidence_ids"] = ["OBS:synthetic-1"]
        self.review = self.accepted_review(self.decision)
        self.assert_rejects("snapshot_only_or_missing_ending_basis")
        self.decision["basis_evidence_ids"] = ["ORIGINAL:EO:1"]
        self.review = self.accepted_review(self.decision)
        self.assert_rejects("snapshot_only_or_missing_ending_basis")

    def test_yes_snapshot_cannot_replace_current_predicate(self):
        self.decision["recommended_provisional_status"] = "yes"
        self.decision["current_predicate_checked_through"] = O.CUTOFF
        self.review = self.accepted_review(self.decision)
        self.assert_rejects("snapshot_only_or_missing_current_predicate")

    def test_historical_snapshot_cannot_hide_under_current_evidence_id(self):
        record = deepcopy(self.evidence["base_dossier"]["evidence"]["ORIGINAL:EO:1"])
        ident = "CURRENT:EO:1#snapshot"
        record.update(id=ident, meta={"basis_code": "ofr_codification_1989_in_force"})
        self.evidence["base_dossier"]["evidence"][ident] = record
        self.decision.update(recommended_provisional_status="yes", basis_evidence_ids=[ident],
                             current_predicate_checked_through=O.CUTOFF)
        self.reseal_changed_fixture_evidence()
        self.assert_rejects("historical_editorial_snapshot_cannot_establish_status")

    def test_report_deadline_cannot_establish_status(self):
        record = deepcopy(self.evidence["base_dossier"]["evidence"][self.ending])
        ident = "TERM:EO:1#report"
        record.update(id=ident, kind="report_deadline")
        self.evidence["base_dossier"]["evidence"][ident] = record
        self.decision["basis_evidence_ids"] = [ident]
        self.reseal_changed_fixture_evidence()
        self.assert_rejects("report_deadline_cannot_establish_status")

    def test_held_actor_context_can_support_manual_review_of_ocr_missed_provision(self):
        self.decision["basis_evidence_ids"] = ["ACTOR_TEXT:EO:5"]
        self.review = self.accepted_review(self.decision)
        self.review["checked_evidence_ids"].append("ACTOR_TEXT:EO:5")
        proposal = self.propose()
        self.assertEqual(proposal["recommended_provisional_status"], "no")
        self.assertFalse(proposal["owner_acceptance"]["accepted"])

    def test_resealed_evidence_cannot_fabricate_a_quote(self):
        self.evidence["base_dossier"]["evidence"][self.ending]["text"] += " fabricated words"
        self.reseal_changed_fixture_evidence()
        self.assert_rejects("frozen_source_span_mismatch")

    def test_explicit_legal_checks_and_empty_status_gaps_are_required(self):
        for key in ("identity_confirmed", "basis_review_confirmed", "earlier_endings_checked",
                    "partial_scope_checked", "savings_checked"):
            with self.subTest(key=key):
                decision = deepcopy(self.decision)
                decision[key] = False
                with self.assertRaisesRegex(ValueError, key + "_required"):
                    O.propose(self.repo, decision, self.accepted_review(decision), self.evidence)
        self.decision["material_gaps"] = ["The original savings clause remains unread."]
        self.assert_rejects("unresolved_status_material_gaps")

    def test_review_must_pin_original_and_every_selected_basis(self):
        self.review["checked_evidence_ids"] = [self.ending]
        self.assert_rejects("review_must_check_original_and_selected_basis")

    def test_stale_source_bytes_are_rejected(self):
        rel = next(iter(self.evidence["source_fingerprints"]))
        with (self.repo / rel).open("ab") as fh:
            fh.write(b"changed")
        self.assert_rejects("stale_held_source")

    def test_stale_history_is_rejected(self):
        h = deepcopy(self.packet["history"])
        h["flags"] = ["NEW_MATERIAL_CONFLICT"]
        O._seal(h)
        out = self.repo / "jobs/status-history/output"
        write_json(out / "histories/EO_1.json", h)
        write_json(out / "INDEX.json", [{"instrument_id": "EO:1", "history": "histories/EO_1.json", "fingerprint": h["fingerprint"]}])
        self.assert_rejects("stale_status_history")

    def test_authority_change_invalidates_proposal(self):
        with self.fixture.status.open("a", encoding="utf-8") as fh:
            fh.write("EO:1,no\n")
        self.assert_rejects("already_has_authoritative_provisional_status")

    def test_census_change_invalidates_frozen_snapshot(self):
        with (self.repo / O.UNIVERSE).open("a", encoding="utf-8") as fh:
            fh.write("EO:999,1\n")
        self.assert_rejects("stale_authority_snapshot")

    def test_old_compiler_format_is_rejected(self):
        path = self.out / "SUMMARY.json"
        summary = json.loads(path.read_bytes())
        summary.pop("overlay_input_schema")
        write_json(path, summary)
        with self.assertRaisesRegex(ValueError, "old_compiled_outputs:overlay_input_schema"):
            O.freeze_evidence(self.repo, self.out, self.packet)

    def test_changed_compiler_code_is_rejected(self):
        with (self.repo / "jobs/claim-kit/excavate.py").open("a", encoding="utf-8") as fh:
            fh.write("\n# new compiler\n")
        with self.assertRaisesRegex(ValueError, "code_fingerprint"):
            O.freeze_evidence(self.repo, self.out, self.packet)
        self.assert_rejects("stale_compiler_code")

    def test_missing_or_extra_shards_are_rejected(self):
        (self.out / "CLAUSES.jsonl").unlink()
        with self.assertRaisesRegex(ValueError, "missing_or_unlisted_compiled_shards"):
            O.freeze_evidence(self.repo, self.out, self.packet)

    def test_changed_lifecycle_obligations_invalidates_frozen_snapshot(self):
        with (self.repo / "jobs/claim-kit/lifecycle_obligations.py").open("a", encoding="utf-8") as fh:
            fh.write("\n# changed lifecycle compiler\n")
        with self.assertRaisesRegex(ValueError, "code_fingerprint"):
            O.freeze_evidence(self.repo, self.out, self.packet)
        self.assert_rejects("stale_compiler_code")

    def test_extra_unlisted_shard_is_rejected(self):
        write_jsonl(self.out / "CLAUSES.part0001.jsonl", [])
        with self.assertRaisesRegex(ValueError, "missing_or_unlisted_compiled_shards"):
            O.freeze_evidence(self.repo, self.out, self.packet)

    def test_noncontiguous_listed_shard_is_rejected(self):
        path = self.out / "CLAUSES.part0002.jsonl"
        write_jsonl(path, [])
        summary = json.loads((self.out / "SUMMARY.json").read_bytes())
        summary["jsonl_shards"].append(path.name)
        summary["jsonl_shard_sha256"][path.name] = O._sha(path.read_bytes())
        write_json(self.out / "SUMMARY.json", summary)
        with self.assertRaisesRegex(ValueError, "compiled_shard_sequence_invalid"):
            O.freeze_evidence(self.repo, self.out, self.packet)

    def test_shard_tampering_is_rejected_before_freeze(self):
        path = self.out / "CHAINS.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n")
        with self.assertRaisesRegex(ValueError, "compiled_shard_hash_mismatch:CHAINS"):
            O.freeze_evidence(self.repo, self.out, self.packet)

    def test_large_actor_context_pointer_is_qualified_and_pinned_for_isolated_bundle(self):
        path = self.repo / "jobs/future-source/data/texts/EO_5.txt"
        with path.open("a", encoding="utf-8") as fh:
            fh.write("Additional context retained.\n" * 2200)
        digest = O._sha(path.read_bytes())
        provenance = self.repo / "jobs/future-source/data/PROVENANCE.json"
        data = json.loads(provenance.read_bytes())
        actor = next(r for r in data["representations"] if r["instrument_id"] == "EO:5")
        actor["source"].update(sha256=digest, text_sha256=digest)
        write_json(provenance, data)
        self.fixture.run_build()
        evidence = O.freeze_evidence(self.repo, self.out, self.packet)
        context = next(c for c in evidence["base_dossier"]["actor_contexts"] if c["actor_id"] == "EO:5")
        self.assertEqual(context["overflow"], "jobs/claim-kit/output/actor-texts/EO_5.json")
        self.assertEqual(context["held_text_path"], "jobs/future-source/data/texts/EO_5.txt")
        self.assertIn(context["overflow"], evidence["source_fingerprints"])
        self.assertTrue(O.validate_evidence(self.repo, evidence))

    def test_decision_edits_reuse_frozen_evidence_without_corpus_build_or_shard_scan(self):
        self.decision["rationale"] += " A second version explains the same evidence more fully."
        self.review = self.accepted_review(self.decision)
        with patch.object(O, "_read_records", side_effect=AssertionError("must reuse frozen records")), \
                patch("build.build", side_effect=AssertionError("no corpus rebuild")):
            proposal = self.propose()
            dossier = O.experimental_dossier(self.repo, proposal, self.decision, self.review, self.evidence)
        self.assertTrue(dossier["status_overlay"]["experimental_only"])
        self.assertEqual(self.telemetry["corpus_rebuilds"], 0)
        self.assertGreater(self.telemetry["compiled_bytes_read"], 0)

    def test_runner_receipt_only_change_reuses_same_frozen_records(self):
        original_proposal = self.propose()
        path = self.out / "SUMMARY.json"
        summary = json.loads(path.read_bytes())
        summary.update(input_commit="new-run-commit", elapsed_seconds=10.5)
        write_json(path, summary)
        original_open = Path.open

        def bounded_open(path, *args, **kwargs):
            if path.parent == self.out and path.suffix == ".jsonl":
                raise AssertionError("no compiled shard bytes may be reopened")
            return original_open(path, *args, **kwargs)

        with patch.object(O, "_read_records", side_effect=AssertionError("no shard reread")), \
                patch.object(Path, "open", bounded_open):
            self.assertTrue(O.validate_evidence(self.repo, self.evidence))
            self.assertEqual(self.propose(), original_proposal)

    def test_changed_consumed_manifest_requires_new_evidence_and_review(self):
        path = self.out / "SUMMARY.json"
        summary = json.loads(path.read_bytes())
        summary["jsonl_shard_sha256"]["CLAUSES.jsonl"] = "a" * 64
        write_json(path, summary)
        self.assert_rejects("stale_compiled_generation")

    def test_changed_unconsumed_manifest_does_not_change_frozen_status_proposal(self):
        original_proposal = self.propose()
        path = self.out / "SUMMARY.json"
        summary = json.loads(path.read_bytes())
        self.assertNotIn("ACTING_REPRESENTATIONS.jsonl", self.evidence["compiled"]["consumed_shard_sha256"])
        summary["jsonl_shard_sha256"]["ACTING_REPRESENTATIONS.jsonl"] = "b" * 64
        write_json(path, summary)
        self.assertEqual(self.propose(), original_proposal)

    def test_receipt_reuse_does_not_accept_new_failure_or_missing_consumed_shard(self):
        path = self.out / "SUMMARY.json"
        summary = json.loads(path.read_bytes())
        summary.update(input_commit="new-run-commit")
        write_json(path, summary)
        write_json(self.out / "STATUS.json", {"result": "failed"})
        self.assert_rejects("compiled_runner_did_not_succeed")
        write_json(self.out / "STATUS.json", {"result": "succeeded"})
        (self.out / "CLAUSES.jsonl").unlink()
        self.assert_rejects("missing_or_unlisted_compiled_shards")

    def test_owner_acceptance_cannot_be_forged_in_experimental_dossier(self):
        proposal = self.propose()
        proposal["owner_acceptance"]["accepted"] = True
        O._seal(proposal)
        with self.assertRaisesRegex(ValueError, "proposal_does_not_match"):
            O.experimental_dossier(self.repo, proposal, self.decision, self.review, self.evidence)

    def test_bundle_is_new_version_and_protected_destinations_are_rejected(self):
        protected = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        proposal = self.propose()
        folder = self.repo / "research/excavator/synthetic/overlay/v1"
        result = O.write_bundle(self.repo, folder, proposal, self.decision, self.review, self.evidence, self.telemetry)
        self.assertFalse(result["owner_accepted"])
        self.assertTrue(result["authoritative_files_unchanged"])
        self.assertEqual({p: p.read_bytes() for p in protected}, protected)
        with self.assertRaisesRegex(ValueError, "overlay_bundle_exists"):
            O.write_bundle(self.repo, folder, proposal, self.decision, self.review, self.evidence)
        for forbidden in (self.repo / O.STATUSES, self.repo / "research/readiness/claims/new",
                          self.out / "dossiers/EO_1.json", self.repo / "HANDOFF/new"):
            with self.subTest(destination=forbidden):
                with self.assertRaisesRegex(ValueError, "overlay_destination_must_be_isolated"):
                    O.write_bundle(self.repo, forbidden, proposal, self.decision, self.review, self.evidence)

    def lifecycle_sheet(self, dossier):
        sheet = A.blank_sheet(dossier, "synthetic-producer")
        sheet.update(approved=True, original_confirmed=True, inventory_confirmed=True,
                     unresolved_material_gaps=[], search_ids=["complete"],
                     research_rationale="The synthetic original and acting order were read, including all earlier terms, effective wording and savings.",
                     savings={"state": "none_after_bounded_search", "source_id": self.ending,
                              "reason": "The synthetic complete corpus contains no savings provision."})
        for clause in sheet["clauses"]:
            clause.update(state="terminated", end_id=self.ending, effective_date="2000-01-02",
                          effective_date_confirmed=True,
                          reason="The synthetic exact revocation ends the complete original duty; prior terms and savings were checked.")
        return sheet

    def test_full_overlay_dossier_runs_existing_assembler(self):
        proposal = self.propose()
        dossier = O.experimental_dossier(self.repo, proposal, self.decision, self.review, self.evidence)
        sheet = self.lifecycle_sheet(dossier)
        claim, errors = A.assemble(sheet, dossier, self.repo)
        self.assertEqual(errors, [])
        self.assertEqual(claim["whole_order_status"], "no")
        self.assertEqual(A.check_claim(claim, self.repo, dossier), [])
        working, errors = O.assemble_working(self.repo, sheet, proposal, self.decision, self.review, self.evidence)
        self.assertEqual(errors, [])
        self.assertTrue(working["claim_kit"]["status_overlay"]["experimental_only"])
        self.assertEqual(O.check_working_claim(self.repo, working, proposal, self.decision, self.review, self.evidence), [])
        working["claim_kit"].pop("status_overlay")
        self.assertEqual(O.check_working_claim(self.repo, working, proposal, self.decision, self.review, self.evidence),
                         ["working_claim_status_overlay_label_required"])
        self.assertFalse((self.repo / "research/readiness/claims").exists())

    def test_overlay_cli_assemble_check_stays_isolated_and_preserves_labels(self):
        proposal = self.propose()
        bundle = self.repo / "research/excavator/synthetic/overlay/cli-v1"
        O.write_bundle(self.repo, bundle, proposal, self.decision, self.review, self.evidence)
        dossier = json.loads((bundle / "DOSSIER.json").read_bytes())
        sheet_path = bundle / "SYNTHETIC_LIFECYCLE_DECISION.json"
        write_json(sheet_path, self.lifecycle_sheet(dossier))
        protected = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        claim_path = bundle / "working-claims.jsonl"
        prefix = ["--repo", str(self.repo), "--output", str(self.out)]
        with redirect_stdout(io.StringIO()) as output:
            result = F.K.main(prefix + ["overlay-assemble", str(bundle), "--sheet", str(sheet_path),
                                        "--write", str(claim_path)])
        self.assertEqual(result, 0, output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["claims_published"], 0)
        claim = json.loads(claim_path.read_bytes())
        self.assertTrue(claim["claim_kit"]["status_overlay"]["experimental_only"])
        self.assertFalse(claim["claim_kit"]["status_overlay"]["owner_accepted"])
        with redirect_stdout(io.StringIO()) as output:
            result = F.K.main(prefix + ["overlay-check", str(bundle), str(claim_path)])
        self.assertEqual(result, 0, output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["checked"], 1)
        self.assertEqual(json.loads(output.getvalue())["failures"], [])
        self.assertEqual({p: p.read_bytes() for p in protected}, protected)
        self.assertFalse((self.repo / "research/readiness/claims").exists())

        # Canonical destinations, overwrites, blank producer sheets and stripped
        # experimental labels all fail without a published claim.
        forbidden = self.repo / "research/readiness/claims/synthetic.jsonl"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = F.K.main(prefix + ["overlay-assemble", str(bundle), "--sheet", str(sheet_path),
                                        "--write", str(forbidden)])
        self.assertEqual(result, 2)
        self.assertFalse(forbidden.exists())
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = F.K.main(prefix + ["overlay-assemble", str(bundle), "--sheet", str(sheet_path),
                                        "--write", str(claim_path)])
        self.assertEqual(result, 2)
        blank_output = bundle / "rejected-blank.jsonl"
        with redirect_stdout(io.StringIO()):
            result = F.K.main(prefix + ["overlay-assemble", str(bundle), "--sheet", str(bundle / "LIFECYCLE_DECISION.json"),
                                        "--write", str(blank_output)])
        self.assertEqual(result, 1)
        self.assertFalse(blank_output.exists())
        claim["claim_kit"].pop("status_overlay")
        stripped = bundle / "stripped-label.jsonl"
        write_jsonl(stripped, [claim])
        with redirect_stdout(io.StringIO()) as output:
            result = F.K.main(prefix + ["overlay-check", str(bundle), str(stripped)])
        self.assertEqual(result, 1)
        self.assertIn("working_claim_status_overlay_label_required", output.getvalue())


if __name__ == "__main__":
    unittest.main()
