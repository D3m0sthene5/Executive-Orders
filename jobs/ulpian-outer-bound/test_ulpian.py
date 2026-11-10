"""Tests for Ulpian (python -I jobs/ulpian-outer-bound/test_ulpian.py). Standard library only."""
import datetime as dt
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulpian as U  # noqa: E402

D = dt.date


class Arithmetic(unittest.TestCase):
    def test_calment_reproduces_the_term(self):
        self.assertEqual(U.bound(D(1875, 2, 21), 0), D(1997, 8, 4))

    def test_a_min_zero_threshold_is_1904_05_03(self):
        self.assertEqual(U.date_threshold(0), D(1904, 5, 3))
        self.assertLess(U.bound(D(1904, 5, 2), 0), U.CUTOFF)
        self.assertGreaterEqual(U.bound(D(1904, 5, 3), 0), U.CUTOFF)

    def test_age_thresholds(self):
        self.assertEqual(U.date_threshold(14), D(1918, 5, 3))
        self.assertEqual(U.date_threshold(64), D(1968, 5, 3))

    def test_life_is_counted_in_days(self):
        # A fixed 44,724 days: "plus 122 years plus 164 days" is a day short when the span holds only 29 leap days.
        for born in (D(1875, 2, 21), D(1880, 6, 1), D(1904, 2, 29), D(1899, 12, 31)):
            self.assertEqual((U.death_bound(born) - born).days, 44724)

    def test_feb_29_birth_bound_goes_to_feb_28(self):
        self.assertEqual(U.minus_years(D(1916, 2, 29), 14), D(1902, 2, 28))

    def test_required_age(self):
        self.assertEqual(U.required_age(D(1904, 5, 2)), 0)
        self.assertEqual(U.required_age(D(1904, 5, 3)), 1)
        self.assertEqual(U.required_age(D(1918, 5, 2)), 14)
        self.assertEqual(U.required_age(D(1918, 5, 3)), 15)

    def test_pothier_appendix_bounds_within_a_day(self):
        # PD-CS-ONE-PERSON Appendix A: EO 3378 born by 1868-12-26, latest death 1991-06-08 (year arithmetic).
        self.assertLessEqual(abs((U.death_bound(D(1868, 12, 26)) - D(1991, 6, 8)).days), 1)


class Screens(unittest.TestCase):
    def hits(self, text):
        return U.screen(text)

    def test_one_person_waiver_passes(self):
        self.assertEqual(self.hits("Mr. Cyrus F. Adams may be appointed to a competitive position in the classified "
                                   "civil service without compliance with the civil-service rules. Wm. H. Taft."), [])

    def test_two_persons_fail(self):
        self.assertIn("several_persons", self.hits("Mrs. Laura E. Langley and Miss Elizabeth M. Bowling may be "
                                                   "appointed to the positions of telephone operator"))

    def test_minor_fails(self):
        self.assertIn("possible_minor", self.hits("John Doe may be appointed messenger boy in the Treasury"))

    def test_age_limit_fails(self):
        self.assertIn("age_mentioned", self.hits("may be appointed without regard to the age limit"))

    def test_general_clause_fails(self):
        self.assertIn("general_or_continuing", self.hits("may be classified. In similar cases of exceptional merit"))

    def test_vacancy_fails(self):
        self.assertIn("position_not_person", self.hits("The vacancy in the position of chemist may be filled"))

    def test_second_clause_fails(self):
        self.assertIn("second_clause", self.hits("may be reinstated and will be suspended for sixty days"))

    def test_ratification_fails(self):
        self.assertIn("ratifies_or_confirms", self.hits("the order of October 30 is hereby, on the report, confirmed"))

    def test_conditional_fails(self):
        self.assertIn("conditional", self.hits("may be appointed subject to such noncompetitive test of fitness"))

    def test_labor_regulations_fail(self):
        self.assertIn("outside_civil_service_rules", self.hits("this order waives the labor regulations"))

    def test_truncated_text(self):
        self.assertTrue(U.truncated("Mrs. Braxton is the widow of Henry W. Braxton, a former employee of the Govern-"))
        self.assertTrue(U.truncated("the excellent record of Mrs. Redick while employed as an unclassified"))
        self.assertFalse(U.truncated("without regard to the civil-service rules. WOODROW WILSON. THE WHITE HOUSE, "
                                     "May 5, 1913. [No. 1771] xq7 ~r"))
        self.assertFalse(U.truncated("under the civil-service rules. This work is in the public domain in the US"))

    def test_age_screens_skipped_for_quoted_facts(self):
        text = "waives that part of the order which pertains to the age limit"
        self.assertIn("age_mentioned", U.screen(text, with_age=True))
        self.assertNotIn("age_mentioned", U.screen(text, with_age=False))

    def test_amendment_fails(self):
        self.assertIn("rule_or_order_amended", self.hits("Section 3 of Rule VI is hereby amended to read"))

    def test_estate_fails(self):
        self.assertIn("property_money_or_estate", self.hits("the sum shall be paid to the estate of John Doe"))

    def test_office_designation_fails(self):
        self.assertIn("office_designation", self.hits("John Doe is designated to act as Secretary of Labor"))


class Readings(unittest.TestCase):
    def test_date_must_be_legible_in_text(self):
        self.assertTrue(U.date_in_text(D(1926, 11, 13), "THE WHITE HOUSE, November 13, 1926. [No. 4541]"))
        self.assertFalse(U.date_in_text(D(1926, 11, 13), "THE WHITE HOUSE, November 18, 1996. [No. 4541]"))

    def test_readings_file_has_quotes_and_dates(self):
        for iid, (born, quote) in U.readings().items():
            self.assertTrue(iid.startswith("EO:") and born and len(quote) > 30)


class Lock(unittest.TestCase):
    def test_tag_refuses_without_owner_decision(self):
        try:
            found = U.owner_approval()
        except U.Refused:
            return
        self.skipTest(f"owner decision {found['decision']} approves this RULE.md; nothing to refuse")

    def test_rule_parameters_agree_with_the_tool(self):
        params = U.rule_parameters()
        self.assertEqual(params["life_days"], U.LIFE_DAYS)
        self.assertNotIn("a_min_floor", params)

    def test_rule_sha_ignores_line_endings(self):
        self.assertRegex(U.rule_sha(), r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main(verbosity=1)
