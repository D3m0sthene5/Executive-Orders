"""Regression tests for multi-order page spans and OCR-damaged closing tags.

Each fixture is the real failing text (condensed) from a held FR scan; nothing here reads
committed outputs. EO 7573/8332 (closing tag misread), 8109 and 8494 (order continues across a
page break behind a neighbour's filing line), 11905 (long order printed in separate parts),
11728/13294 (a PDF that bundles two orders), 8965 (closing tag inside a neighbour's page file).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fr_pages  # noqa: E402


def tag(number):
    return dict(fr_pages.marker_patterns(number))["closing_number_tag"]


class ClosingTagOcr(unittest.TestCase):
    def test_eo7573_spaced_abbreviation_and_digit_for_bracket(self):
        # EO 7573: "[No. 7573]" printed, OCR layer reads "[N o .75731"
        self.assertTrue(tag("7573").search("act\n[N o .75731\n[F. R. Doc. 37-700; Filed]"))
        self.assertTrue(tag("7573").search("[No. 7573]"))
        self.assertTrue(tag("7573").search("[No. 75731"))

    def test_neighbour_tag_is_not_this_order(self):
        # the same page prints EO 7572's tag as "[No. 75721"
        self.assertFalse(tag("7573").search("[No. 75721"))

    def test_digit_read_for_bracket_needs_no_real_bracket(self):
        # "[No. 13571]" is order 13571; it must never identify order 1357
        self.assertFalse(tag("1357").search("[No. 13571]"))
        self.assertTrue(tag("13571").search("[No. 13571]"))

    def test_eo7573_locates_order_not_low(self):
        pages = ["2 FEDERAL REGISTER\nEXECUTIVE ORDER\nDesignating a judge\nBy virtue of the authority\n"
                 "[N o .75731\n[F. R. Doc. 37-701; Filed, March 11, 1937;\n12:11 p. m.]"]
        r = fr_pages.locate_order(pages, "7573", None, page_hint=1)
        self.assertEqual((r["marker_kind"], r["confidence"]), ("closing_number_tag", "high"))

    def test_number_tag_with_spaced_abbreviation(self):
        self.assertTrue(dict(fr_pages.marker_patterns("8332"))["number_tag"].search("\nN o . 8332\n"))


PAGE_8109_1 = """FEDERAL REGISTER
Washington, Friday, May 5, 1939
The President
EXECUTIVE ORDER
Amendment of Executive Order No. 7293 of February 14, 1936
By virtue of and pursuant to the authority vested in me by section 11 of the Act
Franklin D Roosevelt
The White House,
May 3+1939
[Na^81071 )  .
[P. R.  Doc. 39-1521; Filed, May 4, 1939;
11:37 a. m.]
EXECUTIVE ORDER
Revocation of Executive Order No. 6644 of March 14, 1934, Withdrawing Public Lands
COLORADO
Franklin D Roosevelt
The White House,
May 3, 1939.
[No. 81081
[P. R. Doc. 39-1520; Filed, May 4, 1939;
11:37 a. m.]
EXECUTIVE ORDER
Correcting the Description of the Waianae-Kai Military Reservation
WHEREAS by Executive Order No.
2900 of July 2, 1918, certain lands at Waianae-Kai were withdrawn:
CONTENTS
THE PRESIDENT
Executive Orders: Page
Colorado, revocation of public land withdrawal ____ 1903
Hawaii, correcting description of Waianae-Kai ____ 1903
(Continued on next page)
"""
PAGE_8109_2 = """1904 FEDERAL REGISTER
NOW, THEREFORE, I hereby order as follows:
I. The lands are restored to the Territory of Hawaii.
Franklin D Roosevelt
The White House,
May 3, 1939.
[No. 8l09]
[P. R. Doc. 39-1519; Filed, May 4, 1939;
11:37 a. m.]
Notice about something else
"""


class ContinuedAcrossPageBreak(unittest.TestCase):
    def test_eo8109_runs_past_the_neighbours_filing_line(self):
        r = fr_pages.locate_order([PAGE_8109_1, PAGE_8109_2, "1905 more\n[F. R. Doc. 39-1500; Filed]"], "8109", None, page_hint=1)
        self.assertTrue(r["found"])
        self.assertEqual((r["first_page"], r["last_page"], r["confidence"]), (1, 2, "low"))
        self.assertIn("Continued on next page", " ".join(r["notes"]))

    def test_first_order_on_the_page_keeps_its_own_end(self):
        # EO 8107 (the first order on the page, tag unreadable): the old rule still applies
        r = fr_pages.locate_order([PAGE_8109_1, PAGE_8109_2], "8107", None, page_hint=1)
        self.assertEqual((r["first_page"], r["last_page"]), (1, 1))

    def test_order_below_a_certain_tag_is_not_moved(self):
        # a closing tag on the page certainly above the wanted number vetoes the later-heading rule
        page = PAGE_8109_1.replace("[No. 81081", "[No. 9999]")
        self.assertIsNone(fr_pages.continued_anchor([page], 0, "8109"))
        self.assertIsNotNone(fr_pages.continued_anchor([PAGE_8109_1], 0, "8109"))

    def test_contents_box_heading_is_not_an_order_heading(self):
        text = "[F. R. Doc. 1; Filed]\nCONTENTS\nExecutive Orders: Page\nx"
        self.assertIsNone(fr_pages.continued_anchor([text], 0, "8109"))


class LongOrderInParts(unittest.TestCase):
    def test_eo11905_span_is_not_cut_at_three_pages(self):
        pages = ["7703 THE PRESIDENT\nExecutive Order 11905 of February 18, 1976\nUnited States Foreign Intelligence Activities"]
        pages += [f"{7704 + i} FEDERAL REGISTER, VOL. 41, NO. 34\nSec. {i}. text of the order" for i in range(35)]
        pages += ["7739 FEDERAL REGISTER\nGerald R. Ford\n[FR Doc. 76-5003 Filed 2-18-76; 11:31 am]", "Reader Aids"]
        r = fr_pages.locate_order(pages, "11905", 7703)
        self.assertEqual((r["first_page"], r["last_page"]), (1, 37))
        self.assertTrue(r["notes"])
        self.assertEqual(r["confidence"], "medium")

    def test_order_with_no_filing_line_is_flagged(self):
        pages = ["7703 THE PRESIDENT\nExecutive Order 11905 of February 18, 1976\nbody"] + [f"{7704 + i} x" for i in range(5)]
        r = fr_pages.locate_order(pages, "11905", 7703)
        self.assertTrue(r.get("ends_without_filing_line"))
        self.assertEqual(r["confidence"], "medium")


def pdf_13294():
    return [
        "15917 Federal Register / Vol. 68, No. 61 / Monday, March 31, 2003 / Presidential Documents\n"
        "Executive Order 13293 of March 28, 2003\nSupporting the Interim Administration\nSec. 1. text\n"
        "[FR Doc. 03-7900 Filed 3-28-03; 3:56 pm]\nBilling code 3195-01-P",
        "15918 Federal Register / Vol. 68, No. 61 / Monday, March 31, 2003 / Presidential Documents\nunrelated",
        "15919 Federal Register / Vol. 68, No. 61 / Monday, March 31, 2003 / Presidential Documents\n"
        "Executive Order 13294 of March 28, 2003\nDesignating Certain Officials\nSec. 2. text\n"
        "[FR Doc. 03-7901 Filed 3-28-03; 3:56 pm]\nBilling code 3195-01-P",
    ]


class BundledPdf(unittest.TestCase):
    def test_eo13294_starts_on_its_own_page(self):
        r = fr_pages.locate_order(pdf_13294(), "13294", 15917, single_document=True)
        self.assertEqual((r["first_page"], r["last_page"]), (3, 3))
        self.assertEqual(r["start_printed_page"], 15919)
        self.assertTrue(r["shares_file_with_other_order"])
        self.assertEqual(r["confidence"], "medium")
        self.assertEqual(fr_pages.start_citation(r, "68 FR 15917"), "68 FR 15919")

    def test_first_order_in_the_pdf_keeps_the_pdf_start(self):
        r = fr_pages.locate_order(pdf_13294(), "13293", 15917, single_document=True)
        self.assertEqual(r["first_page"], 1)
        self.assertEqual(r["confidence"], "high")
        self.assertEqual(fr_pages.start_citation(r, "68 FR 15917"), "68 FR 15917")

    def test_single_order_pdf_unchanged(self):
        r = fr_pages.locate_order(pdf_13294()[2:], "13294", None, single_document=True)
        self.assertEqual((r["first_page"], r["last_page"], r["confidence"]), (1, 1, "high"))


EO_8964_FILE = """Instrument: EO:8964
=== PDF page 2 of 6 ===
6368 FEDERAL REGISTER, Friday, December 12, 1941
EXECUTIVE ORDER 8964
Amending the Rules
By virtue of the authority vested in me
Franklin D Roosevelt
The White House,
December 11, 1941.
[No. 8964]
[F. R. Doc. 41-9100; Filed, December 11, 1941;
3:44 p. m.]
EXECUTIVE ORDER
Withdrawing Public Lands
By virtue of and pursuant to the authority vested in me
Franklin D Roosevelt
The White House,
December 11, 1941.
[No. 8965]
[F. R. Doc. 41-9101; Filed, December 11, 1941;
3:45 p. m.]
EXECUTIVE ORDER
Another order
"""


class NeighbourPageFile(unittest.TestCase):
    def test_eo8965_span_is_its_own_body(self):
        start, end, complete = fr_pages.neighbour_span(EO_8964_FILE, "8965")
        body = EO_8964_FILE[start:end]
        self.assertTrue(complete)
        self.assertIn("Withdrawing Public Lands", body)
        self.assertIn("[No. 8965]", body)
        self.assertNotIn("Amending the Rules", body)
        self.assertNotIn("Another order", body)
        self.assertTrue(body.rstrip().endswith("3:45 p. m.]"))

    def test_absent_tag(self):
        self.assertIsNone(fr_pages.neighbour_span(EO_8964_FILE, "8966"))


class CatalogPageTwoPagesOff(unittest.TestCase):
    @staticmethod
    def pages(tag_page_body):
        # page-ending lines carry no digits, as in the real scans, so the printed page numbers read cleanly
        return ["313 FEDERAL REGISTER, Saturday, January 27, 1940@PROCLAMATION@regulation text@[F. R. Doc. 40-1; Filed, January 26, 1940]@trailing words@".replace("@", chr(10)),
                "314 FEDERAL REGISTER, Saturday, January 27, 1940@more of the neighbour@[F. R. Doc. 40-2; Filed, January 26, 1940]@trailing words@".replace("@", chr(10)),
                ("315 FEDERAL REGISTER, Saturday, January 27, 1940@" + tag_page_body + "@trailing words@").replace("@", chr(10))]

    def test_eo8332_closing_tag_two_pages_after_the_cited_page(self):
        # OFR catalog cites 5 FR 313; the order is on 315, behind another order's filing line
        pages = self.pages("EXECUTIVE ORDER@Establishing a withdrawal@By virtue of the authority@[No. 8332]@[F. R. Doc. 40-3; Filed, January 26, 1940]")
        r = fr_pages.locate_order(pages, "8332", 313)
        self.assertEqual((r["first_page"], r["last_page"], r["marker_kind"]), (3, 3, "closing_number_tag"))
        self.assertEqual(r["confidence"], "medium")

    def test_eo8332_with_no_heading_after_the_filing_line_is_still_skipped(self):
        pages = self.pages("text without a heading@[No. 8332]@[F. R. Doc. 40-3; Filed, January 26, 1940]")
        r = fr_pages.locate_order(pages, "8332", 313)
        self.assertEqual(r["confidence"], "low")


if __name__ == "__main__":
    unittest.main()
