"""Pre-review checks: one true positive and one near-miss negative per check, plus lint wiring.

All data is synthetic and lives in temporary directories.
"""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "jobs/claim-kit"))
import geddes
import prereview_checks as P
from test_geddes import fixture


def codes(result, code):
    return [f for f in result["flags"] if f["code"] == code]


def base_claim(**extra):
    claim = {"instrument_id": "EO:13694", "research_rationale": "", "operative_clauses": [],
             "original_representation": {"signing_date": "2015-04-01"}}
    claim.update(extra)
    return claim


def notice(year):
    return {"actor": f"FRDOC:{year}-0001", "effective_date": f"{year}-03-29",
            "mechanism": "continuation_of_national_emergency_nea_notice", "source": {"quote": "continued"}}


def amendment(actor, date):
    return {"actor": actor, "effective_date": date, "mechanism": "amendment", "source": {"quote": "amended"}}


class Counts(unittest.TestCase):
    def run_check(self, reason, events, rationale=""):
        claim = base_claim(research_rationale=rationale, operative_clauses=[
            {"scope_id": "EO:13694#lead", "judgment_reason": reason, "later_events": events}])
        return codes(P.check(claim, {}, Path.cwd()), "count_contradicts_records")

    def test_zero_notices_and_no_amendment_contradict_records(self):
        events = [notice(2016), notice(2017), amendment("EO:13757", "2016-12-29")]
        flags = self.run_check("The 0 held Federal Register notices of continuation () continue the emergency. "
                               "No held later instrument revokes, supersedes or amends this order.", events)
        self.assertEqual(sorted(f["recorded_count"] for f in flags), [1, 2])

    def test_near_misses_are_not_flagged(self):
        events = [notice(2016), notice(2017), amendment("EO:13757", "2016-12-29")]
        # Matching count; another order's history; clause-scoped absence for a clause without amendments;
        # and an event whose mechanism text merely says it is not an amendment.
        self.assertEqual(self.run_check("The 2 held continuation notices continue the emergency. "
                                        "No instrument amends Executive Order 13660.", events), [])
        claim = base_claim(operative_clauses=[
            {"scope_id": "EO:13694#sec2", "judgment_reason": "No held instrument revokes or amends the clause.", "later_events": [notice(2016)]},
            {"scope_id": "EO:13694#sec1", "judgment_reason": "Amended by EO 13757.", "later_events": [amendment("EO:13757", "2016-12-29")]},
            {"scope_id": "EO:13694#sec3", "judgment_reason": "No held instrument amends it.",
             "later_events": [{"actor": "FRDOC:2016-1", "effective_date": "2016-03-29",
                               "mechanism": "continuation of the national emergency; a continuation notice, not an amendment"}]}])
        self.assertEqual(codes(P.check(claim, {}, Path.cwd()), "count_contradicts_records"), [])


class HeldTextCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)

    def tearDown(self): self.temp.cleanup()

    def held(self, name, text):
        (self.repo / name).write_text(text, encoding="utf-8")
        return {"text_path": name, "text_sha256": hashlib.sha256(text.encode()).hexdigest()}


class Emergency(HeldTextCase):
    DECLARES = "I find that this situation constitutes an unusual and extraordinary threat, and I hereby declare a national emergency to deal with that threat."
    EXPANDS = "In order to take additional steps with respect to the national emergency declared in Executive Order 14024, I hereby order:"

    def run_check(self, own_text, basis):
        source = {**self.held("own.txt", own_text), "char_start": 0, "char_end": len(own_text)}
        claim = base_claim(instrument_id="EO:14068", original_representation=source, operative_clauses=[
            {"scope_id": "EO:14068#lead", "judgment_reason": "", "current_predicate": {"legal_basis": basis}, "later_events": []}])
        return codes(P.check(claim, {}, self.repo), "emergency_declaration_unsupported")

    def test_declares_boilerplate_without_declaring_text(self):
        flags = self.run_check(self.EXPANDS, "The national emergency it declares was continued by the notice of March 2026.")
        self.assertEqual(len(flags), 1)

    def test_near_misses(self):
        # The order really declares the emergency (OCR line break inside the phrase).
        self.assertEqual(self.run_check(self.DECLARES.replace("national emergency", "na-\ntional emergency"),
                                        "The national emergency it declares was continued."), [])
        # "it" refers to another named order.
        self.assertEqual(self.run_check(self.EXPANDS, "Its force depends on Executive Order 14024 and the emergency it declared."), [])


class PageLabels(HeldTextCase):
    TEXT = ("Header\n=== PDF page 1 of 3 ===\nREPORT TO THE PRESIDENT\n=== PDF page 2 of 3 ===\nLetter text\n"
            "=== PDF page 3 of 3 ===\nThe time for filing was extended to December 10, 1960.\n")

    def run_check(self, label, quote, text=None):
        text = text or self.TEXT
        a = text.index(quote)
        source = {**self.held("report.txt", text), "page_or_item": label, "char_start": a, "char_end": a + len(quote), "quote": quote}
        claim = base_claim(source_notes=[{"reason": "extension", "source": source}])
        return codes(P.check(claim, {}, self.repo), "page_label_excludes_span")

    def test_cover_label_on_later_page_span(self):
        flags = self.run_check("Report.pdf PDF page 1 (cover)", "The time for filing was extended")
        self.assertEqual(flags[0]["span_pages"], [3])

    def test_near_misses(self):
        self.assertEqual(self.run_check("Report.pdf PDF pages 1-3 (excerpt)", "The time for filing was extended"), [])
        self.assertEqual(self.run_check("Report.pdf PDF page 1 (cover)", "REPORT TO THE PRESIDENT"), [])
        # Form-feed page breaks are recognised too; the span on page 2 matches a page-2 label.
        ff = "Cover page\fSecond page text here\fThird"
        self.assertEqual(self.run_check("PDF page 2", "Second page text", ff), [])
        self.assertEqual(len(self.run_check("PDF page 1", "Second page text", ff)), 1)


class Dates(unittest.TestCase):
    def claim(self, end, event, reason):
        return base_claim(instrument_id="EO:10509", original_representation={"signing_date": "1953-12-16"},
                          whole_order_end={"actor": "EO:10509", "date": end, "mechanism": "expiry_by_own_terms"},
                          research_rationale=f"Whole-order end {'1954-03-19'}.",
                          operative_clauses=[{"scope_id": "EO:10509#board", "judgment_reason": reason,
                                              "first_end": {"actor": "board", "date": end, "mechanism": "completion_of_task"},
                                              "later_events": [amendment("EO:10600", event)]}])

    def test_date_before_signing(self):
        flags = codes(P.check(self.claim("1951-03-19", "1955-01-01", ""), {}, Path.cwd()), "date_before_signing")
        self.assertEqual(flags[0]["field_count"], 2)
        # A dossier signing date takes precedence over the claim's copy.
        self.assertEqual(codes(P.check(self.claim("1951-03-19", "1955-01-01", ""), {"signing_date": "1950-01-01"}, Path.cwd()), "date_before_signing"), [])

    def test_date_on_or_after_signing_not_flagged(self):
        self.assertEqual(codes(P.check(self.claim("1953-12-16", "1955-01-01", ""), {}, Path.cwd()), "date_before_signing"), [])

    def test_end_year_conflicts_reasons(self):
        reason = "The report is dated February 17, 1954; thirty days later is 1954-03-19. Executive Order 10600 of January 1, 1958 amended it."
        flags = codes(P.check(self.claim("1951-03-19", "1955-01-01", reason), {}, Path.cwd()), "end_year_conflicts_reasons")
        self.assertEqual({f["field"] for f in flags}, {"operative_clauses[EO:10509#board].first_end.date", "whole_order_end.date",
                                                      "later_events.effective_date"})

    def test_end_year_near_misses(self):
        # The structured date also appears; an anniversary date for an unnamed notice is not compared.
        reason = "The board reported 1954-02-17, so the end is 1954-03-19; the 1955-03-19 notice is unrelated. Executive Order 10600 of January 1, 1955."
        self.assertEqual(codes(P.check(self.claim("1954-03-19", "1955-01-01", reason), {}, Path.cwd()), "end_year_conflicts_reasons"), [])


class Wiring(unittest.TestCase):
    def test_lint_one_runs_prereview_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            dossier, claim, packet = fixture(repo)
            claim = copy.deepcopy(claim)
            claim["operative_clauses"][0]["later_events"][0].update({"effective_date": "1930-01-01", "mechanism": "amendment"})
            row = geddes.lint_one(1, claim, {"EO:12345": dossier}, repo, packet, {})
            self.assertIn("date_before_signing", [f["code"] for f in row["flags"]])
            geddes.stamp_flag_ids([row])
            self.assertTrue(all(f.get("flag_id") for f in row["flags"]))


if __name__ == "__main__":
    unittest.main()
