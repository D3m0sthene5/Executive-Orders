"""Owner decision D-20261125-fr-capture-later-events.

A federalregister.gov full-text capture whose FR citation matches may be the held source of a later event, disclosed
under grade fr_fulltext_capture; it is never an order's own original, an end or a current basis, and every other
refusal stays (citation or document-number mismatch, bytes not held, census identity, undisclosed use).
"""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import working_text as W
import test_assemble as TA

SELDEN_GRADE = ("fr_document_full_text (federalregister.gov full text of a Federal Register document, built from "
                "GPO's XML; the govinfo PDF is the official edition)")
NOTICE = ("<html>\n<head>\n<title>Federal Register, Volume 80 Issue 43 (Thursday, March 5, 2015)</title>\n</head>\n"
          "<body><pre>\n[Federal Register Volume 80, Number 43 (Thursday, March 5, 2015)]\n"
          "[Presidential Documents]\n[Pages 12067-12068]\nFrom the Federal Register Online via the Government "
          "Publishing Office [<a href=\"http://www.gpo.gov\">www.gpo.gov</a>]\n[FR Doc No: 2015-05337]\n\n"
          "Notice of March 3, 2015\n\nContinuation of the National Emergency With Respect to Ukraine\n\n"
          "On March 6, 2014, by Executive Order 13660, I declared a national emergency. The national emergency "
          "declared in Executive Order 13660 must continue in effect beyond March 6, 2015.\n</pre></body>\n</html>\n")
QUOTE = "The national emergency declared in Executive Order 13660 must continue in effect beyond March 6, 2015."


def capture_ref(repo, text=NOTICE, name="fr-2015-05337.txt", **changes):
    path = Path(repo) / "jobs/selden-fr-citers/output/texts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    start = text.index(QUOTE) if QUOTE in text else 0
    ref = {"acceptable_as_original": False, "filing_date": None, "grade": SELDEN_GRADE,
           "instrument_id": "FRDOC:2015-05337",
           "page_or_item": "80 FR 12067; FR Doc. 2015-05337; Presidential Document: Continuation of the National "
                           "Emergency With Respect to Ukraine",
           "requires_page_check": False, "role": "acting_instrument_text", "sha256": digest, "signing_date": None,
           "text_path": path.relative_to(repo).as_posix(), "text_sha256": digest,
           "url": "https://www.federalregister.gov/documents/full_text/text/2015/03/05/2015-05337.txt",
           "quote": QUOTE, "char_start": start, "char_end": start + len(QUOTE)}
    ref.update(changes)
    return ref


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.index = W.Index(self.repo)
        self.ref = capture_ref(self.repo)

    def claim(self, ref=None, path="later", disclose=True):
        ref = deepcopy(self.ref if ref is None else ref)
        clause = {"scope_id": "EO:13660#sec1", "later_events": []}
        claim = {"instrument_id": "EO:13660", "operative_clauses": [clause]}
        if path == "later":
            clause["later_events"].append({"effective_date": "2015-03-03", "actor": ref["instrument_id"],
                                           "mechanism": "continuation", "source": ref})
        elif path == "original":
            claim["original_representation"] = ref
        elif path == "end":
            clause["first_end"] = {"date": "2015-03-03", "source": ref}
        elif path == "basis":
            clause["current_predicate"] = {"legal_basis": "x", "source": ref, "checked_through": "2026-10-14"}
        if disclose:
            claim["fr_fulltext_captures"] = W.fr_capture_disclosure([ref])
        return claim

    def policy(self, claim):
        captures = []
        errors, dependent = W.policy(claim, self.repo, self.index, captures=captures)
        return errors, dependent, captures

    def test_matching_capture_is_accepted_as_a_disclosed_later_event(self):
        errors, dependent, captures = self.policy(self.claim())
        self.assertEqual((errors, dependent), ([], []))
        self.assertEqual([p for p, _ in captures], ["operative_clauses[0].later_events[0].source"])
        disclosure = self.claim()["fr_fulltext_captures"]
        self.assertEqual((disclosure["grade"], disclosure["decision"]),
                         ("fr_fulltext_capture", "D-20261125-fr-capture-later-events"))
        self.assertEqual(disclosure["captures"][0]["fr_citation"], "80 FR 12067")

    def test_a_pin_cite_inside_the_printed_page_range_matches(self):
        ref = dict(self.ref, page_or_item="80 FR 12068; FR Doc. 2015-05337")
        self.assertEqual(self.policy(self.claim(ref))[0], [])

    def test_undisclosed_or_altered_disclosure_is_refused(self):
        self.assertIn("fr_fulltext_capture:disclosure_required", self.policy(self.claim(disclose=False))[0])
        claim = self.claim()
        claim["fr_fulltext_captures"]["grade"] = "official_printing"
        self.assertIn("fr_fulltext_capture:disclosure_required", self.policy(claim)[0])

    def test_disclosure_without_capture_is_refused(self):
        claim = self.claim(path="none")
        claim["fr_fulltext_captures"] = W.fr_capture_disclosure([self.ref])
        self.assertIn("fr_fulltext_capture:disclosure_without_capture", self.policy(claim)[0])

    def assertRefused(self, claim, reason=None):
        errors, _, captures = self.policy(claim)
        self.assertEqual(captures, [])
        self.assertIn("working_text_exact_grade_and_false_flag_required", " ".join(errors))
        if reason:
            self.assertIn("fr_fulltext_capture_" + reason, " ".join(errors))
        return errors

    def test_never_an_original_an_end_or_a_current_basis(self):
        for path in ("original", "end", "basis"):
            with self.subTest(path=path):
                errors = self.assertRefused(self.claim(path=path, disclose=False))
                self.assertNotIn("fr_fulltext_capture_", " ".join(errors))

    def test_cited_volume_or_page_mismatch_is_refused(self):
        for poi in ("81 FR 12067; FR Doc. 2015-05337", "80 FR 12069; FR Doc. 2015-05337",
                    "80 FR 1206; FR Doc. 2015-05337"):
            with self.subTest(poi=poi):
                self.assertRefused(self.claim(dict(self.ref, page_or_item=poi)), "fr_citation_mismatch")

    def test_no_fr_citation_is_refused(self):
        self.assertRefused(self.claim(dict(self.ref, page_or_item="; FR Doc. 2015-05337; Notice")),
                           "no_fr_citation_in_reference")

    def test_capture_whose_header_is_another_document_is_refused(self):
        other = capture_ref(self.repo, NOTICE.replace("[FR Doc No: 2015-05337]", "[FR Doc No: 2015-05338]"),
                            name="other.txt")
        self.assertRefused(self.claim(other), "fr_document_number_mismatch")
        headless = capture_ref(self.repo, NOTICE.replace("[Pages 12067-12068]", ""), name="headless.txt")
        self.assertRefused(self.claim(headless), "fr_citation_mismatch")

    def test_bytes_not_held_or_not_pinned_are_refused(self):
        missing = dict(self.ref, text_path="jobs/selden-fr-citers/output/texts/absent.txt")
        self.assertRefused(self.claim(missing), "capture_bytes_not_held")
        changed = dict(self.ref, text_sha256="0" * 64, sha256="0" * 64)
        self.assertRefused(self.claim(changed), "capture_bytes_not_held")
        pdf_pin = dict(self.ref, sha256="1" * 64)
        self.assertRefused(self.claim(pdf_pin), "capture_bytes_not_pinned")

    def test_census_identity_or_own_order_is_refused(self):
        self.assertRefused(self.claim(dict(self.ref, instrument_id="EO:13660")), "identity_not_a_later_fr_document")
        self.assertRefused(self.claim(dict(self.ref, instrument_id="EO:13685")), "identity_not_a_later_fr_document")
        self.assertRefused(self.claim(dict(self.ref, role="original_representation")),
                           "identity_not_a_later_fr_document")

    def test_other_url_or_grade_is_refused(self):
        self.assertRefused(self.claim(dict(self.ref, url="https://example.org/2015-05337.txt")),
                           "url_not_the_documents_federalregister_full_text")
        self.assertRefused(self.claim(dict(self.ref, url=self.ref["url"].replace("2015-05337", "2015-05338"))),
                           "url_not_the_documents_federalregister_full_text")
        # A different producer grade is not this decision's capture: the existing refusals apply unchanged.
        errors, _, captures = self.policy(self.claim(dict(self.ref, grade="held_text_lead"), disclose=False))
        self.assertEqual(captures, [])
        self.assertIn("working_text_exact_grade_and_false_flag_required", " ".join(errors))
        self.assertTrue(W.fr_capture_source(self.ref))
        self.assertFalse(W.fr_capture_source(dict(self.ref, acceptable_as_original=True)))
        self.assertFalse(W.fr_capture_source(dict(self.ref, grade="fr_document_full_textual")))

    def test_quote_must_be_the_exact_held_span(self):
        errors = self.policy(self.claim(dict(self.ref, quote="continue in effect")))[0]
        self.assertIn("operative_clauses[0].later_events[0].source:working_text_quote_mismatch", errors)

    def test_hash_declared_as_an_order_representation_is_refused(self):
        self.index.by_sha[self.ref["sha256"]] = [{"instrument_id": "EO:13660", "grade": "compiled_transcription",
                                                  "sha256": self.ref["sha256"], "text_path": self.ref["text_path"],
                                                  "text_sha256": self.ref["text_sha256"], "url": None,
                                                  "requires_page_check": False, "complete_text": True}]
        self.assertRefused(self.claim(), "hash_declared_as_an_order_representation")


class AssemblyTests(unittest.TestCase):
    """The real assembler discloses the capture and its check accepts the claim; refusals stay."""

    def setUp(self):
        self.base = TA.AssemblyTests("test_inputs_are_immutable")
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.repo, self.dossier, self.sheet = self.base.repo, self.base.dossier, self.base.sheet
        self.ref = capture_ref(self.repo)
        record = {"id": "ACTOR_TEXT:FRDOC:2015-05337", "actor_id": "FRDOC:2015-05337",
                  "actor_kind": "non_census_instrument", "basis_eligible": False, "official_printing": False,
                  "grade": SELDEN_GRADE, "acceptable_as_original": False, "role": "actor_context",
                  "source": {k: v for k, v in self.ref.items() if k not in ("quote", "char_start", "char_end")},
                  "text": QUOTE, "char_start": self.ref["char_start"], "char_end": self.ref["char_end"]}
        self.dossier["evidence"][record["id"]] = record
        self.refresh()
        self.assertNotIn("working_text", TA.A.blank_sheet(self.dossier, "test producer"))
        self.sheet["clauses"][0]["later_events"] = [{"id": record["id"], "effective_date": "2015-03-03",
                                                     "effective_date_confirmed": True,
                                                     "mechanism": "continuation"}]

    def refresh(self):
        self.base.refresh()
        self.sheet["dossier_sha256"] = self.dossier["fingerprint"]

    def test_capture_later_event_is_assembled_disclosed_and_checked(self):
        claim, errors = self.base.assemble()
        self.assertEqual(errors, [])
        self.assertEqual(claim["fr_fulltext_captures"]["grade"], "fr_fulltext_capture")
        self.assertEqual(claim["fr_fulltext_captures"]["captures"][0]["instrument_id"], "FRDOC:2015-05337")
        self.assertNotIn("working_text", claim)
        self.assertEqual(TA.A._gate(self.repo).validate_claim(claim, "no"), [])
        self.assertEqual(TA.A.check_claim(claim, self.repo, self.dossier), [])
        claim.pop("fr_fulltext_captures")
        self.assertIn("fr_fulltext_capture:disclosure_required", TA.A.check_claim(claim, self.repo, self.dossier))

    def test_capture_as_an_end_is_refused(self):
        self.sheet["clauses"][0]["later_events"] = []
        self.sheet["clauses"][0]["end_id"] = "ACTOR_TEXT:FRDOC:2015-05337"
        self.base.assertFails("working_text_exact_grade_and_false_flag_required")

    def test_citation_mismatch_is_refused_in_assembly(self):
        record = self.dossier["evidence"]["ACTOR_TEXT:FRDOC:2015-05337"]
        record["source"]["page_or_item"] = "80 FR 12100; FR Doc. 2015-05337"
        self.refresh()
        self.base.assertFails("fr_fulltext_capture_fr_citation_mismatch")


if __name__ == "__main__":
    unittest.main()
