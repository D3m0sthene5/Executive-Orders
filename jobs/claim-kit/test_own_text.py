"""Accursius F5/F6: own-text status bases and the working-text gate on the undecided route.

Unit tests run the classifier on literal texts copied from held originals named in the Respondendi
diagnosis (research/excavator/claude-respondendi-2026-11-10/DIAGNOSIS.csv). Integration tests freeze
real overlay evidence from the build fixture and run the status gate. No corpus status is promoted.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import excavate as E
import own_text as T
import status_overlay as O
import test_status_overlay as S


def original(text, signing="1982-08-17"):
    digest = hashlib.sha256(text.encode()).hexdigest()
    return {"id": "ORIGINAL:EO:9", "text": text, "char_start": 0, "char_end": len(text), "signing_date": signing,
            "source": {"text_path": "x.txt", "text_sha256": digest, "sha256": digest}}


# EO 12379 (47 FR 36099), sections 1-2 and 24, abridged: every command is self-executing.
REVOKE_ONLY = ("Executive Order 12379 of August 17, 1982\nTermination of Boards, Committees, and Commissions\n"
               "By the authority vested in me as President by the Constitution and laws of the United States of "
               "America, it is hereby ordered as follows:\n"
               "Section 1. Executive Order No. 12071, as amended, establishing the President's  \nCommission on "
               "Pension Policy, is revoked.\n"
               "Sec. 2. Executive Order No. 12042, creating a Board of Inquiry to Report on  \nLabor Disputes, is "
               "revoked.\n"
               "Sec. 24. The Veterans' Federal Coordinating Committee (Weekly Compilation  \nof Presidential "
               "Documents, volume 14, number 41, page 1743) is terminated.\n")
# EO 13013 (61 FR 41483), abridged: amends EO 10163; the inserted sections carry their own "may"/"shall".
AMEND_ONLY = ("Executive Order 13013 of August 6, 1996\nAmending Executive Order No. 10163, the Armed Forces\n"
              "Reserve Medal\nBy the authority vested in me as President by the Constitution and the\nlaws of the "
              "United States, it is hereby ordered that Executive\nOrder No. 10163, as amended, is further amended "
              "by striking out sections\n3 and 4 and inserting in lieu thereof the following new sections 3 and\n4:\n"
              "‘‘3. The Armed Forces Reserve Medal may be awarded to members or\nformer members of the reserve "
              "components.\n4. Not more than one Armed Forces Reserve Medal may be awarded\nto any one person. The member "
              "shall receive the medal with the distinctive\ndesign.’’.\n")
# EO 4720 (1927), as held: the trailing sentence is a further provision (Pothier PD-CS-RULES only-content test).
AMEND_WITH_EFFECT = ("September 12, 1927.\nSchedule A, Subdivision IV, War Department, of positions excepted from\n"
                     "the requirement of examination under the civil-service rules is hereby amended\nby revoking "
                     "paragraph 1, which excepts from examination “All cable engineers” and by striking out "
                     "of paragraph 2 the\nwords “and cable seamen.”\nThe effect of the above amendment is to "
                     "bring the positions named with\ntheir present occupants within the competitive classified service.\n")
# A council order: continuing commands.
STANDING = ("Executive Order 99 of May 1, 1990\nBy the authority vested in me, it is hereby ordered as follows:\n"
            "Section 1. There is hereby established the Council on Example Affairs.\n"
            "Sec. 2. The Council shall report annually to the President.\n")
# EO 13552 (75 FR 60951), abridged: amendments effective 30 days after the order.
DEFERRED_FIXED = ("Section 1. Parts II and IV of the Manual for Courts-Martial, United States, \nare amended as "
                  "described in the Annex attached and made a part of this \norder.\nSec. 2. These amendments shall "
                  "take effect 30 days from the date of this \norder.\n(a) Nothing in these amendments shall be "
                  "construed to make punishable \nany act done or omitted prior to the effective date.\n")
DEFERRED_EVENT = ("By virtue of the authority vested in me, the Executive order of March 31, 1911, withdrawing lands "
                  "for Power Site Reserve No. 178, is hereby revoked, effective upon the approval of the survey "
                  "by the Secretary of the Interior.\n")


class ClassifierTests(unittest.TestCase):
    def test_revocation_only_order_is_spent_on_issue_with_one_record_per_command(self):
        recs = T.records("EO:12379", dict(original(REVOKE_ONLY), id="ORIGINAL:EO:12379"), [])
        self.assertEqual(len(recs), 3)
        for ident, r in recs.items():
            self.assertTrue(ident.startswith("OWN_TEXT:EO:12379#"))
            self.assertEqual((r["own_text_kind"], r["mechanism"], r["actor_id"], r["scope"]), ("spent_on_issue", "spent_on_issue", "EO:12379", "whole"))
            self.assertEqual(REVOKE_ONLY[r["char_start"]:r["char_end"]], r["text"])
            self.assertEqual(r["effective_date"], "1982-08-17")
            self.assertNotIn("parent_id", r)

    def test_amendment_only_order_names_parent_and_ignores_inserted_text(self):
        recs = T.records("EO:13013", original(AMEND_ONLY, "1996-08-06"), [])
        self.assertEqual(len(recs), 1)
        r = next(iter(recs.values()))
        self.assertEqual((r["own_text_kind"], r["mechanism"], r["parent_id"]), ("amends_parent", "spent_on_issue", "EO:10163"))
        self.assertIn("surviving_consequence", r)
        self.assertEqual(r["whole_order_test"]["inserted_sentences"] > 0, True)

    def test_further_provision_or_continuing_command_disqualifies(self):
        self.assertEqual(T.records("EO:4720", original(AMEND_WITH_EFFECT), []), {})
        self.assertEqual(T.records("EO:99", original(STANDING), []), {})

    def test_effective_date_follows_the_order_and_undated_events_disqualify(self):
        r = next(iter(T.records("EO:13552", original(DEFERRED_FIXED, "2010-08-31"), []).values()))
        self.assertEqual((r["own_text_kind"], r["effective_date"], r["effective_date_basis"]),
                         ("amends_parent", "2010-09-30", "relative_to_signing"))
        self.assertEqual(T.records("EO:7066", original(DEFERRED_EVENT, "1935-06-07"), []), {})

    def test_blind_audit_false_positives_stay_out(self):
        # Shapes the 2026-11-10 blind read found continuing (EO 4531, 7489, 1426, 1624).
        standing = ("It is hereby ordered that the following-described lands be, and the same are hereby, withdrawn "
                    "from settlement and held for the use of the Navy Department until this order is revoked.\n")
        refuge = ("The following lands are hereby reserved and set apart for the use of the Department of "
                  "Agriculture as an addition to the Elk Refuge.\n")
        so_as = ("The Executive order of July 31, 1879, is hereby amended so as to withdraw permanently the "
                 "following land for the Pima and Maricopa Indians.\n")
        unquoted = ("Schedule A, Subdivision VII, paragraph 4, of the Civil Service Rules\nis hereby amended to read as "
                    "follows:\nAll employees on star routes in post offices of the fourth class.\nThe regulations governing "
                    "the appointment of postmasters of the\nfourth class shall be amended so as to provide that all "
                    "appointments be made from eligible registers.\n")
        for iid, text in (("EO:4531", standing), ("EO:7489", refuge), ("EO:1426", so_as), ("EO:1624", unquoted)):
            self.assertEqual(T.records(iid, original(text, "1926-01-01"), []), {}, iid)

    def test_records_need_the_full_original_span(self):
        partial = dict(original(REVOKE_ONLY), char_end=40)
        self.assertEqual(T.records("EO:12379", partial, []), {})

    def test_parent_end_requires_whole_named_ending_of_the_parent(self):
        own = T.records("EO:13013", original(AMEND_ONLY, "1996-08-06"), [])
        src = {"text_path": "y.txt", "text_sha256": "0" * 64}
        acts = [
            {"id": "ACT:EO:10163>EO:20000@a", "target_id": "EO:10163", "actor_id": "EO:20000", "verb": "revoke",
             "scope": "whole", "names_target": True, "provision_text": "Executive Order 10163 is revoked.",
             "actor_source": src, "char_start": 0, "char_end": 33, "signing_date": "2020-01-01"},
            {"id": "ACT:EO:10163>EO:20001@b", "target_id": "EO:10163", "actor_id": "EO:20001", "verb": "revoke",
             "scope": "partial", "names_target": True, "provision_text": "Section 3 of Executive Order 10163 is revoked.",
             "actor_source": src, "char_start": 0, "char_end": 10},
            {"id": "ACT:EO:10163>EO:20002@c", "target_id": "EO:10163", "actor_id": "EO:20002", "verb": "amend",
             "scope": "whole", "names_target": True, "provision_text": "amended", "actor_source": src,
             "char_start": 0, "char_end": 7}]
        ends = T.parent_end_records("EO:13013", own, acts)
        self.assertEqual(list(ends), ["PARENT_END:EO:13013>EO:10163>EO:20000"])
        e = ends["PARENT_END:EO:13013>EO:10163>EO:20000"]
        self.assertEqual((e["mechanism"], e["parent_id"], e["actor_id"], e["role"]),
                         ("follows_parent", "EO:10163", "EO:20000", "parent_end"))
        self.assertEqual(T.parent_end_records("EO:12379", T.records("EO:12379", original(REVOKE_ONLY), []), acts), {})


class OwnTermsRetypingTests(unittest.TestCase):
    def terms(self, sentence):
        src = {"signing_date": "1997-10-11"}
        return {t["kind"]: t for t in E.own_terms("EO:13064", sentence, src, [])}

    def test_body_sunset_beside_a_report_is_a_sunset(self):
        # EO 13064 / 13010 wording: previously typed report_deadline only.
        t = self.terms("The Commission shall submit its report, and the Principals Committee, the Steering "
                       "Committee, and the Advisory Committee shall terminate no later than September 30, 1998.")
        self.assertIn("sunset_date", t)
        self.assertEqual((t["sunset_date"]["stated_end_date"], t["sunset_date"]["end_bound"]), ("1998-09-30", "not_later_than"))
        self.assertIn("report_deadline", t)

    def test_enumerated_years_are_a_final_period(self):
        # EO 13116 Part II sec. 1(a).
        t = self.terms("Within 30 days of the submission of the National Trade Estimate Report for 1999, 2000, "
                       "and 2001, the Trade Representative shall submit a report.")
        self.assertEqual(t["enumerated_final_period"]["final_year"], "2001")
        self.assertIsNone(t["enumerated_final_period"]["stated_end_date"])

    def test_a_plain_report_deadline_is_unchanged(self):
        t = self.terms("The Board shall report to the President within 30 days from the date of its creation.")
        self.assertEqual(set(t), {"report_deadline"})


class _OverlayFixture(unittest.TestCase):
    """Freeze real evidence for an undecided order whose held original is TEXT, then run the gate."""
    TEXT = REVOKE_ONLY.replace("12379", "1").replace("12071", "2").replace("12042", "3")
    GRADE = None

    def setUp(self):
        original_init = S.F.BuildIntegrationTests.setUp
        text, grade = self.TEXT, self.GRADE

        def patched(fixture):
            original_init(fixture)
            path = fixture.repo / "jobs/future-source/data/texts/EO_1.txt"
            path.write_bytes(text.encode("utf-8"))
            prov_path = fixture.repo / "jobs/future-source/data/PROVENANCE.json"
            prov = json.loads(prov_path.read_text(encoding="utf-8"))
            for r in prov["representations"]:
                if r["instrument_id"] == "EO:1":
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    r["source"].update(sha256=digest, text_sha256=digest)
                    r["signing_date"] = "1982-08-17"
                    if grade:
                        r.update(grade=grade, acceptable_as_original=False)
            prov_path.write_text(json.dumps(prov), encoding="utf-8")
        S.F.BuildIntegrationTests.setUp = patched
        try:
            self.base = S.OverlayTests("test_reviewed_proposal_has_no_authority_and_experimental_full_dossier")
            self.base.setUp()
        finally:
            S.F.BuildIntegrationTests.setUp = original_init
        self.addCleanup(self.base.doCleanups)
        self.evidence, self.decision = self.base.evidence, self.base.decision
        self.dossier = self.evidence["base_dossier"]

    def use_basis(self, ids):
        self.base.decision["basis_evidence_ids"] = ids
        self.base.ending = ids[0]
        self.base.review = self.base.accepted_review(self.base.decision)


class OverlayRouteTests(_OverlayFixture):
    def test_frozen_evidence_carries_rederivable_own_text_records(self):
        own = self.dossier["own_text_ids"]
        self.assertEqual(len(own), 3)
        self.assertTrue(all(T.verify(self.dossier, i) for i in own))
        O.validate_evidence(self.base.repo, self.evidence)

    def test_own_text_is_a_no_basis_and_reaches_the_proposal(self):
        self.use_basis([self.dossier["own_text_ids"][0]])
        proposal = self.base.propose()
        self.assertEqual(proposal["recommended_provisional_status"], "no")
        self.assertFalse(proposal["owner_acceptance"]["accepted"])
        self.assertNotIn("working_text", proposal)

    def test_hand_written_own_text_record_is_refused(self):
        ident = "OWN_TEXT:EO:1#0"
        fake = deepcopy(self.dossier["evidence"][self.dossier["own_text_ids"][0]])
        fake["id"] = ident
        self.dossier["evidence"][ident] = fake
        self.base.reseal_changed_fixture_evidence()
        self.use_basis([ident])
        self.base.assert_rejects("own_text_basis_not_rederivable")

    def test_parent_end_alone_is_never_a_basis(self):
        ident = "PARENT_END:EO:1>EO:2>EO:5"
        record = deepcopy(self.dossier["evidence"][self.dossier["own_text_ids"][0]])
        record.update(id=ident, role="parent_end", parent_id="EO:2", mechanism="follows_parent")
        self.dossier["evidence"][ident] = record
        self.base.reseal_changed_fixture_evidence()
        self.use_basis([ident])
        self.base.assert_rejects("parent_end_requires_own_text_amends_parent_basis")

    def test_routes_constant_names_the_live_routes(self):
        self.assertEqual(O.UNDECIDED_ROUTES, frozenset({"current", "own_text", "working_text"}))
        self.assertIn("OWN_TEXT:", O.NO_BASIS_PREFIXES)


class WorkingTextGateTests(_OverlayFixture):
    GRADE = "official_printing"

    def test_tracker_credited_working_text_may_carry_a_status_with_the_standing_note(self):
        original = self.dossier["evidence"][self.dossier["original_source_id"]]
        self.assertEqual((original["acceptable_as_original"], original["working_text_basis"]),
                         (False, "tracker_original_supported"))
        self.use_basis([self.dossier["own_text_ids"][0]])
        proposal = self.base.propose()
        self.assertEqual(proposal["working_text"]["standing_note"], O.W.NOTE)
        self.assertEqual(proposal["working_text"]["basis"], "tracker_original_supported")
        self.assertTrue(proposal["working_text"]["replacement_required"])

    def test_a_relabelled_basis_is_refused(self):
        self.dossier["evidence"][self.dossier["original_source_id"]]["working_text_basis"] = "lachmann_confirmation"
        self.base.reseal_changed_fixture_evidence()
        self.use_basis([self.dossier["own_text_ids"][0]])
        self.base.assert_rejects("acceptable_original_required_for_status_proposal")


class UncreditedTranscriptionTests(_OverlayFixture):
    GRADE = "mirror_transcription"

    def test_uncredited_transcription_is_still_refused(self):
        original = self.dossier["evidence"][self.dossier["original_source_id"]]
        self.assertNotIn("working_text_basis", original)
        self.use_basis([self.dossier["own_text_ids"][0]])
        self.base.assert_rejects("acceptable_original_required_for_status_proposal")


if __name__ == "__main__":
    unittest.main()
