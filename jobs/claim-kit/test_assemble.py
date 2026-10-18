"""Strict assembly checks, independent of any live downloads or legal judgments."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("kit_assemble_tested", HERE / "assemble.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
REPO = HERE.parents[1]


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        gate = self.repo / "research/stage19/code/claim_gate.py"
        gate.parent.mkdir(parents=True)
        gate.write_bytes((REPO / "research/stage19/code/claim_gate.py").read_bytes())
        text = ("Executive Order 1. The Board shall perform the specified duties.\r\n"
                "Executive Order 2. Executive Order 1 is revoked effective January 2, 2000.\n"
                "Rights and liabilities accrued before revocation are preserved.\n")
        path = self.repo / "held.txt"
        path.write_bytes(text.encode("utf-8"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        source = {"url": "https://example.gov/orders", "sha256": digest,
                  "page_or_item": "1", "text_path": "held.txt", "text_sha256": digest,
                  "local_path": "held.txt"}

        def record(ident, quote, **extra):
            start = text.index(quote)
            return {"id": ident, "source": deepcopy(source), "text": quote,
                    "char_start": start, "char_end": start + len(quote), **extra}

        clause = record("CLAUSES:EO:1#whole", "The Board shall perform the specified duties.",
                        scope_id="EO:1#whole")
        original = record("ORIGINAL:EO:1", text.split("Executive Order 2")[0],
                          acceptable_as_original=True)
        ending = record("ACT:EO:1>EO:2", "Executive Order 1 is revoked effective January 2, 2000.",
                        actor_id="EO:2", verb="revoke", effective_date="2000-01-02")
        self.dossier = {"schema": A.DOSSIER_SCHEMA, "instrument_id": "EO:1",
                        "whole_order_status": "no", "original_source_id": "ORIGINAL:EO:1",
                        "clauses": [clause],
                        "evidence": {"ORIGINAL:EO:1": original, ending["id"]: ending},
                        "machine_searches": [{"search_id": "all", "entry": {
                            "repository": "held complete corpus", "query_or_scope": "EO:1 through cutoff",
                            "checked_on": "2026-10-18"}}],
                        "conflicts": [], "missing": []}
        self.refresh()
        self.sheet = A.blank_sheet(self.dossier, "test producer")
        self.sheet.update({"approved": True, "original_confirmed": True, "inventory_confirmed": True,
                           "research_rationale": "The cited original and revocation have been read, including earlier terms and savings.",
                           "search_ids": ["all"], "savings": {
                               "state": "transferred_or_accrued", "source_id": "ACT:EO:1>EO:2",
                               "reason": "The acting provision preserves accrued rights."}})
        self.sheet["clauses"][0].update({"state": "terminated", "end_id": "ACT:EO:1>EO:2",
                                          "effective_date": "2000-01-02", "effective_date_confirmed": True,
                                          "reason": "All duties ended under the express revocation; earlier provisions have been checked."})

    def refresh(self):
        self.dossier["fingerprint"] = A.canonical_sha(self.dossier)

    def assemble(self):
        return A.assemble(self.sheet, self.dossier, self.repo)

    def assertFails(self, substring):
        claim, errors = self.assemble()
        self.assertIsNone(claim)
        self.assertTrue(any(substring in error for error in errors), errors)

    def test_complete_claim_passes_real_gate_and_strict_check(self):
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        self.assertEqual(A._gate(self.repo).validate_claim(claim, "no"), [])
        self.assertEqual(A.check_claim(claim, self.repo, self.dossier), [])
        self.assertEqual(claim["whole_order_end"]["date"], "2000-01-02")
        self.assertEqual(claim["operative_clauses"][0]["original_operative_text"],
                         "The Board shall perform the specified duties.")
        self.assertNotIn("reviewer", json.dumps(claim))

    def test_inputs_are_immutable(self):
        before = deepcopy((self.sheet, self.dossier))
        self.assemble()
        self.assertEqual((self.sheet, self.dossier), before)

    def test_blank_sheet_has_no_legal_decisions_or_approval(self):
        blank = A.blank_sheet(self.dossier, "any model")
        self.assertFalse(blank["approved"])
        self.assertFalse(blank["original_confirmed"])
        self.assertIsNone(blank["clauses"][0]["state"])
        self.assertEqual(blank["search_ids"], [])
        self.assertEqual(blank["savings"]["state"], None)
        claim, errors = A.assemble(blank, self.dossier, self.repo)
        self.assertIsNone(claim)
        self.assertIn("approved_required", errors)

    def test_status_never_inferred_or_changed(self):
        self.dossier["whole_order_status"] = ""
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("missing_provisional_status")

    def test_stale_sheet(self):
        self.dossier["missing"] = ["new source arrived"]
        self.refresh()
        self.assertFails("stale_dossier_fingerprint")

    def test_stale_dossier_self_hash(self):
        self.dossier["missing"] = ["new source arrived"]
        self.assertFails("dossier_fingerprint_mismatch")

    def test_exact_quote_rejects_case_changes_even_rehashed(self):
        self.dossier["clauses"][0]["text"] = "the Board shall perform the specified duties."
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("quote_not_exact_slice")

    def test_source_text_changed(self):
        (self.repo / "held.txt").write_text("edited source", encoding="utf-8")
        self.assertFails("text_hash_mismatch")

    def test_source_original_hash_changed(self):
        self.dossier["evidence"]["ORIGINAL:EO:1"]["source"]["sha256"] = "0" * 64
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("original_hash_mismatch")

    def test_offline_archival_source_uses_local_scan_hash(self):
        for record in list(self.dossier["evidence"].values()) + self.dossier["clauses"]:
            source = record["source"]
            source["archival_id"] = "TEST-ARCHIVE:BOX-1:ITEM-1"
            source["local_file_sha256"] = source.pop("sha256")
            source.pop("url")
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertEqual(self.assemble()[1], [])

    def test_flat_machine_search_record_is_supported(self):
        nested = self.dossier["machine_searches"][0]
        self.dossier["machine_searches"] = [{"search_id": nested["search_id"], **nested["entry"]}]
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertEqual(self.assemble()[1], [])

    def test_no_free_sources(self):
        self.sheet["clauses"][0]["end_id"] = "my invented source"
        self.assertFails("unknown_evidence_id")

    def test_empty_or_placeholder_inventory(self):
        original = deepcopy(self.sheet["clauses"])
        self.sheet["clauses"] = []
        self.assertFails("operative_clauses_empty")
        self.sheet["clauses"] = original
        self.sheet["clauses"][0]["scope_id"] = "DRAFT-PLACEHOLDER-no-clause-inventory"
        self.assertFails("placeholder")

    def test_no_silent_missing_clause(self):
        clause = deepcopy(self.dossier["clauses"][0])
        clause["id"], clause["scope_id"] = "CLAUSES:EO:1#second", "EO:1#second"
        self.dossier["clauses"].append(clause)
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("clause_inventory_mismatch")

    def test_effective_date_requires_explicit_producer_confirmation(self):
        self.sheet["clauses"][0]["effective_date_confirmed"] = False
        self.assertFails("effective_date_confirmation_required")

    def test_original_lead_cannot_pass(self):
        original = self.dossier["evidence"]["ORIGINAL:EO:1"]
        original["acceptable_as_original"] = False
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("lead_is_not_original")

    def test_richardson_cannot_pass_even_if_marked_acceptable(self):
        self.dossier["evidence"]["ORIGINAL:EO:1"]["source_grade"] = "Richardson transcription"
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("lead_is_not_original")

    def test_conflict_search_guard(self):
        self.dossier["conflicts"] = [{"id": "earlier-end", "reason": "own term"}]
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("conflicts_with_later_source_search")
        self.sheet["conflict_resolutions"]["earlier-end"] = "The term governs a reporting duty and does not end this Board."
        self.assertEqual(self.assemble()[1], [])

    def test_later_event_needs_individual_date_confirmation(self):
        clause = self.sheet["clauses"][0]
        clause["later_event_ids"] = ["ACT:EO:1>EO:2"]
        self.assertFails("later_event_confirmation_required")
        clause["later_events"] = [{"id": "ACT:EO:1>EO:2", "effective_date": "2000-01-02",
                                   "effective_date_confirmed": True}]
        self.assertEqual(self.assemble()[1], [])

    def test_yes_requires_current_basis_and_cutoff(self):
        self.dossier["whole_order_status"] = "yes"
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.sheet["clauses"][0].update({"state": "operative", "end_id": None,
                                          "current_basis_id": "CLAUSES:EO:1#whole",
                                          "current_legal_basis": "The original duties continue under the cited provision.",
                                          "checked_through": "2026-10-14"})
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        self.assertIsNone(claim["whole_order_end"])
        self.sheet["clauses"][0]["checked_through"] = "1989-01-20"
        self.assertFails("current_predicate")

    def test_never_activated_is_explicit_judgment(self):
        self.sheet["clauses"][0]["state"] = "never_activated"
        self.assertEqual(self.assemble()[1], [])

    def test_unknown_search_and_unresolved_gap(self):
        self.sheet["search_ids"] = ["unknown search"]
        self.assertFails("unknown_search_id")
        self.sheet["unresolved_material_gaps"] = ["earlier term has not been checked"]
        self.assertFails("unresolved_material_gaps")

    def test_edited_claim_cannot_substitute_source(self):
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        claim["original_representation"]["page_or_item"] = "invented page"
        self.assertIn("original_representation:not_dossier_evidence",
                      A.check_claim(claim, self.repo, self.dossier))

    def test_path_escape_fails(self):
        self.dossier["evidence"]["ORIGINAL:EO:1"]["source"]["text_path"] = "../outside.txt"
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("text_unavailable_or_unsafe")

    def test_report_deadline_cannot_supply_end(self):
        self.dossier["evidence"]["ACT:EO:1>EO:2"]["kind"] = "report_deadline"
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("report_deadline_is_not_end")

    def test_warning_search_is_not_sufficient_alone(self):
        self.dossier["machine_searches"][0]["coverage_warning"] = "Pre-1937 absent"
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.assertFails("search_coverage_incomplete")

    def test_claim_original_text_is_bound_to_exact_source_quote(self):
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        claim["operative_clauses"][0]["original_operative_text"] = "Invented operative text."
        self.assertIn("clause_0_original_text_not_source_quote", A.check_claim(claim, self.repo, self.dossier))

    def test_malformed_json_shapes_fail_closed(self):
        for field in ("agent", "clauses", "savings", "conflict_resolutions", "search_ids", "instrument_id"):
            for value in (None, 123, [], {}, [None], [[[]]]):
                if field == "conflict_resolutions" and value == {}:
                    continue  # An empty map is valid when there are no conflicts.
                sheet = deepcopy(self.sheet)
                sheet[field] = value
                claim, errors = A.assemble(sheet, self.dossier, self.repo)
                self.assertIsNone(claim, (field, value))
                self.assertTrue(errors, (field, value))
        for field in ("scope_id", "clause_id", "end_id", "later_event_ids", "later_events"):
            sheet = deepcopy(self.sheet)
            sheet["clauses"][0][field] = [[[]]]
            claim, errors = A.assemble(sheet, self.dossier, self.repo)
            self.assertIsNone(claim, field)
            self.assertTrue(errors, field)

    def test_all_four_contract_examples_round_trip(self):
        fixture_dir = REPO / "research/plans/claim_kit_contract/fixtures"
        paths = sorted(fixture_dir.glob("*.example.jsonl"))
        self.assertEqual(len(paths), 4)
        for path in paths:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    value = json.loads(line)
                    self.assertEqual(json.loads(json.dumps(value, ensure_ascii=False)), value)


if __name__ == "__main__":
    unittest.main()
