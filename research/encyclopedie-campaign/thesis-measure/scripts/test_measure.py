"""Offline checks of the measure's text rules. Run: py -I test_measure.py (no repository access needed)."""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure  # noqa: E402

M = measure.Measure


def scan(text):
    out = []
    span = re.sub(r"\s+", " ", text)
    for route, pat in M.SCAN:
        for m in re.finditer(pat + M.DATE_RE, span, re.I):
            out.append((route, m.group(m.lastindex - 2), m.group(m.lastindex - 1), m.group(m.lastindex)))
    flat = re.sub(r"\s+", "", span).lower()
    for route, pat in M.SCAN_FLAT:
        for m in re.finditer(pat + M.DATE_FLAT, flat):
            out.append((route + ":flat", m.group("mon"), m.group("d"), m.group("y")))
    return out


class Mechanisms(unittest.TestCase):
    def test_negation_is_not_a_revocation(self):
        self.assertEqual(measure.classify_mechanism(
            "EO 9618 appoints a successor (not a revocation or supersession of EO 9278)"), "other")

    def test_routes(self):
        c = measure.classify_mechanism
        self.assertEqual(c("express_revocation_by_number_in_table"), "formal")
        self.assertEqual(c("express_supersession"), "formal")
        self.assertEqual(c("own_terms_fixed_sunset"), "own_terms")
        self.assertEqual(c("expiry_of_stated_exemption_period_own_terms"), "own_terms")
        self.assertEqual(c("exhausted_by_performance_on_issuance"), "exhaustion")
        self.assertEqual(c("implied_supersession_by_later_rate_adjustment"), "implied_supersession")
        self.assertEqual(c("statutory_repeal_of_code_approval_and_enforcement_provisions"), "statutory")
        self.assertEqual(c("Rule VI is hereby further amended to read as follows"), "amendment_treated_as_end")
        self.assertEqual(c("EO 11542 deletes this item (10) from EO 11248 sec. 2"), "amendment_treated_as_end")

    def test_eo_ids(self):
        self.assertEqual(measure.eo_ids("EO:12553 and Executive Order No. 9973"), ["EO:12553", "EO:9973"])


class Scan(unittest.TestCase):
    def test_effective_date_is_not_an_end(self):
        self.assertEqual(scan("This Order shall be effective on October 1, 1984."), [])
        self.assertEqual(scan("This order will be effective on and after July 28, 1933."), [])

    def test_member_terms_are_not_a_sunset(self):
        self.assertEqual(scan("The Board shall be governed by the following: (1) The terms of those first "
                              "appointed hereunder shall expire on July 1, 1969."), [])

    def test_sunsets_and_until_dates(self):
        self.assertEqual(scan("1-105. The Board shall terminate on December 31, 1981, unless sooner extended.")[0][0],
                         "own_terms_body_sunset")
        self.assertEqual(scan("exempt Arthur Snow from the provisions thereof and continue him in the service "
                              "until December 1, 1938.")[0][0], "own_terms_until_date")
        self.assertEqual(scan("This order shall cease to be effective at the close of May 31, 1940.")[0][0],
                         "own_terms_order_expiry")

    def test_ocr_split_words(self):
        hits = scan("(b) The Council shall term inate on Decem ber 31,1983, unless sooner extended.")
        self.assertIn(("own_terms_body_sunset:flat", "december", "31", "1983"), hits)


def claim(end_mech, end_date, events, iid="EO:100"):
    return {"instrument_id": iid, "schema": "eo-lifecycle-claim/v1",
            "whole_order_end": {"mechanism": end_mech, "date": end_date, "actor": iid},
            "operative_clauses": [{"later_events": events}, {"later_events": events}]}


class TrackerRule(unittest.TestCase):
    def test_cleanup_after_sunset_is_yes(self):
        ev = [{"actor": "EO:200", "effective_date": "1986-02-25", "mechanism": "express_revocation_by_number_in_table"}]
        self.assertIs(measure.v1_formal_after_cessation(claim("own_terms_fixed_sunset", "1981-12-31", ev)), True)

    def test_revocation_as_end_is_no(self):
        self.assertIs(measure.v1_formal_after_cessation(claim("express_revocation", "2025-01-20", [])), False)

    def test_same_day_is_no(self):
        ev = [{"actor": "EO:200", "effective_date": "1977-09-30", "mechanism": "express_revocation"}]
        self.assertIs(measure.v1_formal_after_cessation(claim("own_terms_fixed_term", "1977-09-30", ev)), False)

    def test_parent_as_amended_is_blank(self):
        ev = [{"actor": "EO:12258", "effective_date": "1980-12-31",
               "mechanism": "revocation of EO 12103 'as amended' by EO 12258 Sec. 1-103(g)"}]
        self.assertIsNone(measure.v1_formal_after_cessation(claim("own_terms_sunset", "1980-03-15", ev, "EO:12176")))

    def test_open_routes_stay_blank(self):
        ev = [{"actor": "EO:200", "effective_date": "1986-02-25", "mechanism": "express_revocation"}]
        self.assertIsNone(measure.v1_formal_after_cessation(
            claim("statutory_repeal_of_code_approval_and_enforcement_provisions", "1935-06-14", ev)))


if __name__ == "__main__":
    unittest.main(verbosity=1)
