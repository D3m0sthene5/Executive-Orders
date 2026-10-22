"""Offline tests: python -I jobs/csc-annual-reports/test_csc.py"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import csc  # noqa: E402

PAGE_121 = """EXCEPTIONS FROM EXAMINATION. 121
EXCEPTION OF CERTAIN EMPLOYEES OF FOOD ADMINISTRATION.
September 27; 191%.
One executive secretary may be appointed without examination.
V. ORDERS EXCEPTING PERSONS NAMED FROM THE REQUIREMENTS
OF THE RULES.
September 30, 1916.
Mrs. Lillian M. Watkins may be transferred from the nonapportioned to the apportioned service.
The Civil Service Commission does not concur in the recommendation.
October 10, 1916.
Mrs. Vera A. Hardie may be reinstated as a printer's assistant.
October 17, 1916. :
Mrs. George S. Ferrow may be appointed to an existing vacancy.
"""
PAGE_122 = """122 THIRTY-FOURTH REPORT U. S. CIVIL SERVICE COMMISSION.
of clerk in the Bureau of Navigation.
November 5, 1916.
The year limit upon eligibility for reinstatement is hereby waived.
"""


def wpa(md, year, text="", cites=""):
    return {"id": "EO:1", "month_day": md, "year": year, "text": text, "citations_joined": cites, "family_hint": ""}


class T(unittest.TestCase):
    def test_citations(self):
        rows = [dict(wpa("Oct 10", "1916", cites="1917 CSR 121; IX R 5"), id="EO:2468"),
                dict(wpa("Oct 10", "1916", cites="1917 C8R 121"), id="EO:2468")]
        got = csc.citations(rows)
        self.assertEqual([(c["id"], c["fy"], c["page"]) for c in got], [("EO:2468", 1917, 121)])

    def test_printed_number_and_map(self):
        texts = ["TITLE PAGE", PAGE_121, PAGE_122]
        self.assertEqual(csc.printed_number(PAGE_121), 121)
        self.assertEqual(csc.printed_number(PAGE_122), 122)
        pmap = csc.page_map(texts)
        self.assertEqual((pmap[121], pmap[122]), (1, 2))
        self.assertNotIn(124, pmap)  # would fall past the last PDF page

    def test_segment_stops_at_next_date_and_heading(self):
        texts = ["", PAGE_121, PAGE_122]
        pmap = {121: 1, 122: 2}
        idx, seg, conf, _ = csc.locate(texts, pmap, {"page": 121, "wpa": wpa("Sept 30", "1916")})
        self.assertEqual((idx, conf), (1, "high"))
        self.assertIn("Lillian M. Watkins", seg)
        self.assertNotIn("Hardie", seg)
        idx, seg, conf, _ = csc.locate(texts, pmap, {"page": 121, "wpa": wpa("Oct 17", "1916")})
        self.assertIn("Ferrow", seg)
        self.assertIn("Bureau of Navigation", seg)  # runs onto the next page
        self.assertNotIn("year limit", seg)

    def test_neighbour_page_and_fuzzy_year(self):
        texts = ["", PAGE_121, PAGE_122]
        pmap = {121: 1, 122: 2}
        idx, _, conf, _ = csc.locate(texts, pmap, {"page": 121, "wpa": wpa("Nov 5", "1916")})
        self.assertEqual((idx, conf), (2, "medium"))
        idx, seg, conf, _ = csc.locate(texts, pmap, {"page": 121, "wpa": wpa("Sept 27", "1917")})
        self.assertEqual((idx, conf), (1, "medium"))
        self.assertIn("executive secretary", seg)

    def test_not_found_and_unmapped(self):
        texts = ["", PAGE_121]
        self.assertEqual(csc.locate(texts, {121: 1}, {"page": 121, "wpa": wpa("Jan 3", "1916")})[3],
                         "date_not_found_near_cited_page")
        self.assertEqual(csc.locate(texts, {}, {"page": 121, "wpa": wpa("Jan 3", "1916")})[3], "printed_page_not_mapped")

    def test_report_fy(self):
        self.assertEqual(csc.report_fy("THIRTY-FOURTH ANNUAL REPORT ... FOR THE FISCAL YEAR ENDED JUNE 30 \n 1917"), 1917)
        self.assertEqual(csc.report_fy("Eighteenth Report ... July 1, 1900, to June 30, 1901"), 1901)
        # OCR read 1923 as 1925 on the 40th report's title page; the ordinal decides.
        self.assertEqual(csc.report_fy("FORTIETH ANNUAL REPORT OF THE ... FOR THE FISCAL YEAR ENDED JUNE 30 1925"), 1923)
        self.assertEqual(csc.report_fy("57th Annual Report, United States Civil Service Commission. June 30, 1940"), 1940)
        self.assertEqual(csc.report_number("FIFTY-SIXTH ANNUAL REPORT"), 56)


if __name__ == "__main__":
    unittest.main()
