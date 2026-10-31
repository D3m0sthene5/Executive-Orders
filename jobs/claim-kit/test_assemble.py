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

    def test_weak_original_requires_separate_page_confirmation(self):
        self.dossier['evidence']['ORIGINAL:EO:1']['requires_page_check']=True
        self.refresh();self.sheet['dossier_sha256']=self.dossier['fingerprint']
        self.assertFails('original_page_check_confirmation_required')
        self.sheet['original_pages_confirmed']=True
        claim,errors=self.assemble();self.assertEqual(errors,[])
        claim['claim_kit']['original_pages_confirmed']=False
        self.assertIn('original_page_check_confirmation_required',A.check_claim(claim,self.repo,self.dossier))

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

    def override(self):
        original = self.dossier["evidence"][self.dossier["original_source_id"]]
        quote = "The Board shall perform the specified duties."
        start = original["char_start"] + original["text"].index(quote)
        return {"scope_id": "EO:1#operative-corrected", "source_id": self.dossier["original_source_id"],
                "char_start": start, "char_end": start + len(quote),
                "reason": "Remove printed document metadata; this exact sentence contains the operative command."}

    def apply_override(self, overrides=None):
        overrides = [self.override()] if overrides is None else overrides
        self.sheet["inventory_overrides"] = deepcopy(overrides)
        row = deepcopy(self.sheet["clauses"][0])
        self.sheet["clauses"] = []
        for override in overrides:
            decision = deepcopy(row)
            decision["scope_id"] = override.get("scope_id")
            decision.pop("clause_id", None)  # The assembler selects the derived id.
            self.sheet["clauses"].append(decision)

    def test_inventory_correction_roundtrip_removes_metadata_and_bad_headings(self):
        original = self.dossier["evidence"][self.dossier["original_source_id"]]
        # Represent an OCR parser's metadata clause and false crossref heading.
        self.dossier["clauses"] = [
            {"id": "CLAUSES:EO:1#lead", "scope_id": "EO:1#lead", "source": deepcopy(original["source"]),
             "text": "Executive Order 1. ", "char_start": 0, "char_end": 19},
            {"id": "CLAUSES:EO:1#false-heading", "scope_id": "EO:1#false-heading", "source": deepcopy(original["source"]),
             "text": original["text"][19:], "char_start": 19, "char_end": original["char_end"]}]
        self.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]
        self.apply_override()
        before = deepcopy((self.dossier, self.sheet))
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        self.assertEqual(A.check_claim(claim, self.repo, self.dossier), [])
        self.assertEqual(A._gate(self.repo).validate_claim(claim, "no"), [])
        self.assertEqual(claim["operative_clauses"][0]["scope_id"], "EO:1#operative-corrected")
        self.assertEqual(claim["operative_clauses"][0]["original_operative_text"], "The Board shall perform the specified duties.")
        self.assertTrue(A.decode_evidence_id(claim["operative_clauses"][0]["original_source"]).startswith("OVERRIDE:ORIGINAL:EO:1#"))
        self.assertEqual(claim["claim_kit"]["inventory_overrides"], self.sheet["inventory_overrides"])
        self.assertEqual((self.dossier, self.sheet), before)

    def test_inventory_correction_rejects_hostile_or_malformed_spans(self):
        changes = [{"char_start": -1}, {"char_end": 100000}, {"char_end": 0},
                   {"char_start": True}, {"source_id": "ACT:EO:1>EO:2"},
                   {"scope_id": "EO:999#whole"}, {"reason": ""},
                   {"quote": "a free quote is prohibited"}, {"source": {"url": "https://invented.gov"}}]
        for change in changes:
            with self.subTest(change=change):
                override = {**self.override(), **change}
                self.apply_override([override])
                self.assertFails("inventory_override")

    def test_inventory_correction_rejects_overlap_and_duplicate_scopes(self):
        first = self.override()
        second = {**first, "scope_id": "EO:1#second", "char_start": first["char_start"] + 1}
        self.apply_override([first, second])
        self.assertFails("overlapping_spans")
        second = {**first}
        self.apply_override([first, second])
        self.assertFails("duplicate_scope")

    def test_inventory_correction_requires_complete_explicit_clause_decisions(self):
        self.apply_override()
        saved = deepcopy(self.sheet["clauses"])
        self.sheet["clauses"] = []
        self.assertFails("clause_inventory_mismatch")
        self.sheet["clauses"] = saved
        self.sheet["inventory_confirmed"] = False
        self.assertFails("inventory_confirmed_required")

    def test_inventory_correction_claim_metadata_cannot_be_edited_or_removed(self):
        self.apply_override()
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        changed = deepcopy(claim)
        changed["claim_kit"]["inventory_overrides"][0]["char_start"] += 1
        self.assertTrue(A.check_claim(changed, self.repo, self.dossier))
        changed = deepcopy(claim)
        del changed["claim_kit"]["inventory_overrides"]
        self.assertTrue(A.check_claim(changed, self.repo, self.dossier))
        changed = deepcopy(claim)
        changed["operative_clauses"][0]["original_source"]["quote"] = "invented"
        self.assertTrue(A.check_claim(changed, self.repo, self.dossier))

    def test_inventory_correction_cannot_reuse_old_clause_pointer(self):
        self.apply_override()
        self.sheet["clauses"][0]["clause_id"] = "CLAUSES:EO:1#whole"
        self.assertFails("corrected_evidence_id_mismatch")

    def test_source_evidence_ids_are_canonical_encoded_and_lookup_strictly(self):
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        source = claim["operative_clauses"][0]["first_end"]["source"]
        self.assertEqual(source["evidence_id_encoding"], "base64url-utf8")
        self.assertNotIn("EO:", source["evidence_id"])
        self.assertEqual(A.decode_evidence_id(source), "ACT:EO:1>EO:2")
        self.assertEqual(source["quote"], self.dossier["evidence"]["ACT:EO:1>EO:2"]["text"])
        self.assertEqual(self.sheet["clauses"][0]["end_id"], "ACT:EO:1>EO:2")
        self.assertEqual(A.check_claim(claim, self.repo, self.dossier), [])
        for change in ({"evidence_id": "ACT:EO:1>EO:2"},
                       {"evidence_id_encoding": "unrecognized"},
                       {"evidence_id": source["evidence_id"] + "="},
                       {"evidence_id": "_w"},
                       {"evidence_id": A.encode_evidence_id("ACT:EO:1>EO:999")},
                       {"evidence_id": ""}):
            with self.subTest(change=change):
                changed = deepcopy(claim)
                changed["operative_clauses"][0]["first_end"]["source"].update(change)
                self.assertTrue(A.check_claim(changed, self.repo, self.dossier))

    def test_encoded_evidence_id_unicode_roundtrip_requires_marker(self):
        ident = "TERM:EO:123½:café:effective#1"
        encoded = A.encode_evidence_id(ident)
        self.assertEqual(A.decode_evidence_id({"evidence_id": encoded, "evidence_id_encoding": "base64url-utf8"}), ident)
        with self.assertRaises(ValueError):
            A.decode_evidence_id({"evidence_id": encoded})

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


    def working_fixture(self):
        import working_text as W
        original = self.dossier['evidence']['ORIGINAL:EO:1']
        text = original['text']
        p = self.repo / 'transcription.txt'
        p.write_bytes(text.encode('utf-8'))
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        ref = dict(original['source'], url='https://example.org/transcription', sha256=digest,
                   text_sha256=digest, text_path='transcription.txt', local_path='transcription.txt',
                   instrument_id='EO:1', grade='mirror_transcription', acceptable_as_original=False)
        original.update(source=ref, acceptable_as_original=False, grade='mirror_transcription')
        for clause in self.dossier['clauses']:
            clause['source'] = deepcopy(ref)
        self.fragment = self.repo / 'jobs/app-executive-orders/output/FRAGMENTS.jsonl'
        self.fragment.parent.mkdir(parents=True)
        self.fragment_record = {'kind':'original_representation', 'instrument_id':'EO:1',
                                'data': deepcopy(ref)}
        self.fragment.write_text(json.dumps(self.fragment_record)+'\n')
        self.refresh()
        self.sheet['dossier_sha256'] = self.dossier['fingerprint']
        self.sheet['original_confirmed'] = False
        self.sheet['working_text'] = W.blank([ref])
        self.sheet['working_text']['confirmations'][0].update(identity_confirmed=True, complete_text_confirmed=True)
        return ref

    def test_working_text_is_provisional_labeled_and_keeps_replacement_obligation(self):
        import working_text as W
        ref = self.working_fixture()
        claim, errors = self.assemble()
        self.assertEqual(errors, [])
        self.assertFalse(claim['original_representation']['acceptable_as_original'])
        self.assertEqual(claim['original_representation']['grade'], ref['grade'])
        self.assertEqual(claim['working_text']['standing_note'], W.NOTE)
        self.assertTrue(claim['working_text']['replacement_required'])
        self.assertEqual(A.check_claim(claim, self.repo, self.dossier), [])
        # The official ending source is still official; the ruling does not relabel it.
        self.assertNotIn('acceptable_as_original', claim['whole_order_end']['source'])

    def test_working_text_requires_identity_completeness_and_note(self):
        self.working_fixture()
        for field in ('identity_confirmed', 'complete_text_confirmed'):
            self.sheet['working_text']['confirmations'][0][field] = False
            self.assertFails('identity_and_complete_text_confirmation_required')
            self.sheet['working_text']['confirmations'][0][field] = True
        self.sheet['working_text']['standing_note'] = 'Original someday'
        self.assertFails('replacement_and_recheck_note_required')

    def test_working_text_rejects_missing_bytes_wrong_order_and_wrong_grade(self):
        self.working_fixture()
        data = deepcopy(self.fragment_record)
        for field, value in [('instrument_id','EO:999'), ('grade','government_printed_copy')]:
            changed = deepcopy(data)
            if field == 'instrument_id': changed[field] = value
            else: changed['data'][field] = value
            self.fragment.write_text(json.dumps(changed)+'\n')
            self.assertFails('working_text_fragment_identity_or_grade_mismatch')
        self.fragment.write_text(json.dumps(data)+'\n')
        (self.repo / 'transcription.txt').unlink()
        self.assertFails('working_text_missing_bytes')

    def test_working_text_rejects_known_incomplete_and_shortened_original(self):
        self.working_fixture()
        self.fragment_record['data']['complete_text'] = False
        self.fragment.write_text(json.dumps(self.fragment_record)+'\n')
        self.assertFails('working_text_known_incomplete')
        del self.fragment_record['data']['complete_text']
        self.fragment.write_text(json.dumps(self.fragment_record)+'\n')
        original = self.dossier['evidence']['ORIGINAL:EO:1']
        original['text'] = original['text'][:-1]
        original['char_end'] -= 1
        self.refresh(); self.sheet['dossier_sha256'] = self.dossier['fingerprint']
        self.assertFails('working_text_incomplete_representation_span')

    def test_working_text_rejects_hash_quote_edits_and_unlabeled_claim(self):
        self.working_fixture()
        claim, errors = self.assemble(); self.assertEqual(errors, [])
        for field, value in [('text_sha256','f'*64), ('quote','invented'), ('acceptable_as_original',True), ('grade','official_original')]:
            changed = deepcopy(claim)
            changed['original_representation'][field] = value
            self.assertTrue(A.check_claim(changed, self.repo, self.dossier), field)
        changed = deepcopy(claim); del changed['working_text']
        self.assertIn('working_text:disclosure_required', A.check_claim(changed, self.repo, self.dossier))

    def test_working_text_requires_declared_text_hash_not_self_asserted_claim_hash(self):
        self.working_fixture()
        del self.fragment_record['data']['text_sha256']
        self.fragment.write_text(json.dumps(self.fragment_record)+'\n')
        self.assertFails('working_text_fragment_identity_or_grade_mismatch')

    def test_working_text_cannot_launder_grade_via_identical_text_path_alias(self):
        self.working_fixture()
        claim, errors = self.assemble(); self.assertEqual(errors, [])
        (self.repo/'alias.txt').write_bytes((self.repo/'transcription.txt').read_bytes())
        for _, ref in A.W.references(claim):
            if ref.get('acceptable_as_original') is False:
                ref.update(text_path='alias.txt', acceptable_as_original=True)
                ref.pop('grade')
        claim.pop('working_text')
        errors, dependent = A.W.policy(claim, self.repo)
        self.assertTrue(dependent)
        self.assertIn('working_text:disclosure_required', errors)
        self.assertTrue(any('fragment_identity_or_grade_mismatch' in e for e in errors))

    def test_existing_exact_official_representation_is_not_tainted_by_shared_pdf_hash(self):
        ref = self.working_fixture()
        claim, errors = self.assemble(); self.assertEqual(errors, [])
        official = self.repo/'jobs/fr-originals/output/official.txt'
        official.parent.mkdir(parents=True)
        official.write_bytes((self.repo/'transcription.txt').read_bytes())
        data = dict(ref, acceptable_as_original=True, grade='official_printing',
                    needs_page_check=False, text_path='official.txt', url='https://example.gov/official')
        fragment = {'kind':'original_representation','instrument_id':'EO:1','produced_by':'fr-originals','data':data}
        (official.parent/'FRAGMENTS.jsonl').write_text(json.dumps(fragment)+'\n')
        for _, source in A.W.references(claim):
            if source.get('acceptable_as_original') is False:
                source.update(text_path=official.relative_to(self.repo).as_posix(), url=data['url'], acceptable_as_original=True)
                source.pop('grade')
        claim.pop('working_text')
        errors, dependent = A.W.policy(claim, self.repo)
        self.assertEqual(errors, [])
        self.assertEqual(dependent, [])

    def test_working_text_page_warning_is_not_waived(self):
        self.working_fixture()
        self.fragment_record['data']['needs_page_check'] = True
        self.fragment.write_text(json.dumps(self.fragment_record)+'\n')
        self.assertFails('working_text:page_confirmation_required')
        self.sheet['working_text']['confirmations'][0]['pages_confirmed'] = True
        self.assertEqual(self.assemble()[1], [])

    def test_working_text_mixed_ending_cannot_hide_undeclared_derivative(self):
        self.working_fixture()
        end = self.dossier['evidence']['ACT:EO:1>EO:2']
        end['source'].update(grade='mirror_transcription', acceptable_as_original=False, instrument_id='EO:2')
        self.refresh(); self.sheet['dossier_sha256'] = self.dossier['fingerprint']
        self.assertFails('working_text_fragment_identity_or_grade_mismatch')

    def test_working_text_official_arrival_reopens_claim_until_rechecked(self):
        self.working_fixture()
        claim, errors = self.assemble(); self.assertEqual(errors, [])
        path = self.repo / 'jobs/fr-originals/output/official.txt'
        path.parent.mkdir(parents=True)
        path.write_text('Executive Order 1. Official copy newly acquired.')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        fragment = {'kind':'original_representation', 'instrument_id':'EO:1', 'produced_by':'fr-originals',
                    'data':{'acceptable_as_original':True, 'sha256':digest, 'text_sha256':digest,
                            'text_path':'official.txt', 'needs_page_check':False}}
        (path.parent/'FRAGMENTS.jsonl').write_text(json.dumps(fragment)+'\n')
        errors = A.check_claim(claim, self.repo, self.dossier)
        self.assertIn('working_text:official_copy_available_recheck_required', errors)
        self.assertTrue(claim['working_text']['replacement_required'])
        self.assertFalse(claim['original_representation']['acceptable_as_original'])

    def test_working_text_new_official_copy_requires_a_new_sheet(self):
        self.working_fixture()
        self.assertEqual(self.assemble()[1], [])
        self.dossier['evidence']['ORIGINAL:EO:1']['source']['url'] = 'https://example.gov/new-official-copy'
        self.dossier['evidence']['ORIGINAL:EO:1']['acceptable_as_original'] = True
        self.refresh()
        self.assertFails('stale_dossier_fingerprint')


if __name__ == "__main__":
    unittest.main()
