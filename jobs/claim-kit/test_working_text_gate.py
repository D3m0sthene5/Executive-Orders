"""Accursius F6: the overlay text gate accepts a working text the rulings credit, with the standing note.

Credited: Photius R37 official_printing and P4 archival_replica_checked with no page check owed, or any
working-text grade with a current Lachmann confirmation (2026-10-31 ruling). Everything else stays refused.
Integration tests freeze real overlay evidence from the build fixture. No corpus status is promoted.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import status_overlay as O
import test_status_overlay as S


class _GradedFixture(unittest.TestCase):
    """The overlay fixture with EO:1's held text declared as a non-original working text of GRADE."""
    GRADE = None

    def setUp(self):
        original_init = S.F.BuildIntegrationTests.setUp
        grade = self.GRADE

        def patched(fixture):
            original_init(fixture)
            prov_path = fixture.repo / "jobs/future-source/data/PROVENANCE.json"
            prov = json.loads(prov_path.read_text(encoding="utf-8"))
            for r in prov["representations"]:
                if r["instrument_id"] == "EO:1":
                    r.update(grade=grade, acceptable_as_original=False)
            prov_path.write_text(json.dumps(prov), encoding="utf-8")
        S.F.BuildIntegrationTests.setUp = patched
        try:
            self.base = S.OverlayTests("test_reviewed_proposal_has_no_authority_and_experimental_full_dossier")
            self.base.setUp()
        finally:
            S.F.BuildIntegrationTests.setUp = original_init
        self.addCleanup(self.base.doCleanups)
        self.dossier = self.base.evidence["base_dossier"]
        self.original = self.dossier["evidence"][self.dossier["original_source_id"]]


class OfficialPrintingTests(_GradedFixture):
    GRADE = "official_printing"

    def test_credited_text_carries_a_status_with_the_standing_note(self):
        self.assertEqual((self.original["acceptable_as_original"], self.original["working_text_basis"]),
                         (False, "tracker_original_supported"))
        proposal = self.base.propose()
        self.assertEqual(proposal["recommended_provisional_status"], "no")
        self.assertEqual(proposal["working_text"]["standing_note"], O.W.NOTE)
        self.assertEqual((proposal["working_text"]["basis"], proposal["working_text"]["grade"]),
                         ("tracker_original_supported", "official_printing"))
        self.assertTrue(proposal["working_text"]["replacement_required"])
        self.assertFalse(proposal["owner_acceptance"]["accepted"])

    def test_owed_page_check_withdraws_the_credit(self):
        self.original["requires_page_check"] = True
        self.base.reseal_changed_fixture_evidence()
        self.base.decision["original_pages_confirmed"] = True
        self.base.review = self.base.accepted_review(self.base.decision)
        self.base.assert_rejects("acceptable_original_required_for_status_proposal")

    def test_a_relabelled_basis_is_refused(self):
        self.original["working_text_basis"] = "lachmann_confirmation"
        self.base.reseal_changed_fixture_evidence()
        self.base.assert_rejects("acceptable_original_required_for_status_proposal")

    def test_routes_constant_names_the_live_route(self):
        self.assertIn("working_text", O.UNDECIDED_ROUTES)


class ReplicaCheckedTests(_GradedFixture):
    GRADE = "archival_replica_checked"

    def test_p4_checked_replica_is_credited(self):
        self.assertEqual(self.original["working_text_basis"], "tracker_original_supported")
        working = self.base.propose()["working_text"]
        self.assertEqual(working["grade"], "archival_replica_checked")
        self.assertEqual(working["informational_flags"], ["REPLICA_CHECKED_PROQUEST_BYTES"])


class UncreditedGradeTests(_GradedFixture):
    GRADE = "machine_read_government_printed_copy"

    def test_machine_read_copy_needs_a_lachmann_confirmation(self):
        # Independent F6 review finding 2: the tracker does not credit this grade by itself.
        self.assertNotIn("working_text_basis", self.original)
        self.base.assert_rejects("acceptable_original_required_for_status_proposal")


class BasisRuleTests(unittest.TestCase):
    def dossier(self, grade, confirmation=None, page_check=False, acceptable=False):
        d = {"original_source_id": "ORIGINAL:EO:1",
             "evidence": {"ORIGINAL:EO:1": {"grade": grade, "acceptable_as_original": acceptable,
                                             "requires_page_check": page_check}}}
        if confirmation is not None:
            d["working_text_confirmation"] = confirmation
        return d

    def test_basis_by_grade_page_check_and_confirmation(self):
        cases = [
            (("official_printing",), "tracker_original_supported"),
            (("official_printing", None, True), None),
            (("archival_replica_checked",), "tracker_original_supported"),
            (("government_printed_copy",), None),
            (("machine_read_government_printed_copy",), None),
            (("mirror_transcription",), None),
            (("mirror_transcription", {"record": {}}), "lachmann_confirmation"),
            (("machine_read_government_printed_copy", {"record": {}}, True), "lachmann_confirmation"),
            (("held_text_lead", {"record": {}}), None),
            (("original_representation_unverified", None, False, True), None),
        ]
        for args, expected in cases:
            self.assertEqual(O.working_text_basis(self.dossier(*args)), expected, args)


if __name__ == "__main__":
    unittest.main()
