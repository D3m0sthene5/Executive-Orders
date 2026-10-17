"""Regression tests built from real saved texts that the first version got wrong.

Each excerpt is shortened from the real Opus/GovInfo text named in its comment
(executive orders are US government works). No network.
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build  # noqa: E402
import segment as S  # noqa: E402
import sources as SRC  # noqa: E402
from test_build import build_fixture_repo  # noqa: E402

CHROME = (
    "\n\nSkip to main content\n\nThe American Presidency Project\n\nAbout\n Search\n\nToggle navigation\n\n"
    "Documents \nGuidebook\n\nCategories\n\nExecutive Orders (10877)\n\nProclamations (11159)\n\n"
)
FOOTER = (
    "\n\nThe American Presidency Project\nJohn Woolley and Gerhard Peters\nContact\n\nTwitter\n \nFacebook\n\n"
    "Copyright © The American Presidency Project\nTerms of Service\n | \nPrivacy\n"
)


def app_page(title, president_lines, body, citation_name):
    return (f"\n\n{title} | The American Presidency Project" + CHROME + president_lines + f"\n\n{title}\n\n" + body
            + f"\n\n{citation_name}, {title} Online by Gerhard Peters and John T. Woolley, The American Presidency Project "
            "https://www.presidency.ucsb.edu/node/1\n\nFiled Under\n\nCategories\nPresidential\n" + FOOTER)


# reviews/V11_G_EVENT_X3_REV/cache/APP_EO9709.txt (meta http_status 404)
APP_404 = (
    "\n\n404 Page Not Found | The American Presidency Project" + CHROME
    + "Were You Looking for a Document by PID?\n\n404 Page Not Found\n \n\nWe're Sorry!  We did not locate the page "
    "or resource you requested.\n" + FOOTER
)

# reviews/V11_G_EVENT_X3_REV/cache/APP_EO4359.txt: URL says 4359, page is 4359-A
APP_4359A = app_page(
    "Executive Order 4359-A—Citizenship, Passports and Protection",
    "Calvin Coolidge\n\n30th\n\nPresident of the United States:\n\n1923 ‐ 1929",
    "December 19, 1925\n\n"
    "Article X of the Consular Regulations, 1896, entitled \"Citizens, Passports and Protection,\" is hereby "
    "canceled and the following substituted:\n\n"
    "137. NATIVE CITIZENS.—All persons born in the United States and subject to the jurisdiction thereof are "
    "citizens of the United States.\n\n"
    "138. CITIZENSHIP BY NATURALIZATION.—Naturalization is a judicial act, and a certificate of naturalization "
    "will be treated by consular officers as conclusive evidence of citizenship.\n\n"
    "CALVIN COOLIDGE\n\nTHE WHITE HOUSE, \nDecember 19, 1925\n.",
    "Calvin Coolidge",
)

# shards/S11_E_CONT/cache/app_EO2859.txt: page labelled EO 2859 (1918) holds a later
# order that cites "Executive Order No. 2859 of May 11, 1918" in a recital.
APP_2859 = app_page(
    "Executive Order 2859—National Research Council of the National Academy of Sciences",
    "Woodrow Wilson\n\n28th\n\nPresident of the United States:\n\n1913 ‐ 1921",
    "May 11, 1918\n\n"
    "WHEREAS the National Research Council was organized in 1916 at the request of the President by the National "
    "Academy of Sciences; and\n\n"
    "WHEREAS the Council has been perpetuated by the Academy as requested by the President in Executive Order No. "
    "2859 of May 11, 1918; and\n\n"
    "NOW, THEREFORE, by virtue of the authority vested in me as President of the United States, it is ordered as follows:\n\n"
    "1. The functions of the Council shall be to stimulate research in the mathematical, physical, and biological sciences.\n\n"
    "2. The Government shall be represented on the Council by officers designated by the heads of departments.",
    "Woodrow Wilson",
)

# shards/S11_D_REPEAL/cache/app_eo11609.txt: a list of superseded orders in the body
APP_11609 = app_page(
    "Executive Order 11609—Delegating Certain Functions Vested in the President to Other Officers of the Government",
    "Richard Nixon\n\n37th\n\nPresident of the United States:\n\n1969 ‐ 1974",
    "July 22, 1971\n\n"
    "By virtue of the authority vested in me by section 301 of title 3 of the United States Code, and as President "
    "of the United States, it is hereby ordered as follows:\n\n"
    "SECTION 1. General Services Administration. The Administrator of General Services is hereby designated and "
    "empowered to exercise the authority of the President under 5 U.S.C. 4111(b).\n\n\n"
    "SEC. 11. Orders superseded. The following are hereby superseded:\n\n\n"
    "Executive Order No. 10604 of April 22, 1955.\n\n\n"
    "Executive Order No. 11290 of July 21, 1966.\n\n\n"
    "SEC. 12. Taking effect. This order shall be effective immediately.\n\n\n"
    "RICHARD NIXON\n\n\nThe White House\n\n\nJuly 22, 1971\n\n\n"
    "NOTE: Executive Order 11609 was not issued in the form of a White House press release.",
    "Richard Nixon",
)

# shards/S11_C_TEMP_X3/cache/app_eo11269.txt: "SEC. 5. \nExecutive Order No. 10033.\n Section 2 (a) ..."
APP_11269_BODY = (
    "Executive Order 11269—National Advisory Council on International Monetary and Financial Policies\n\n"
    "February 14, 1966\n\n"
    "By virtue of the authority vested in me by Reorganization Plan No. 4 of 1965 (30 F.R. 9353), and as President "
    "of the United States, it is ordered as follows:\n\n"
    "SECTION I. \nEstablishment of Council.\n (a) There is hereby established the National Advisory Council.\n\n"
    "(b) The Council shall be composed of the following members: the Secretary of the Treasury, who shall be the chairman.\n\n"
    "SEC. 2. \nFunctions of the Council.\n The Council shall coordinate the policies of the agencies.\n\n"
    "SEC. 5. \nExecutive Order No. 10033.\n Section 2 (a) of Executive Order No. 10033 of February 8, 1949, is hereby "
    "amended by substituting for the name \"National Advisory Council on International Monetary and Financial Problems\" "
    "the following: \"National Advisory Council on International Monetary and Financial Policies.\"\n\n"
    "SEC. 6. \nEffective date.\n The provisions of this order shall be effective as of January 1, 1966.\n\n"
    "LYNDON B. JOHNSON\n\nThe White House\n\nFebruary 14, 1966"
)

# shards/S11_E_CONT_X10/cache/app_EO10122.txt: "SEC. 2 (a)" with no period after the number
APP_10122_BODY = (
    "Executive Order 10122—Regulations Governing Payment of Disability Retirement Pay\n\nApril 14, 1950\n\n"
    "By virtue of and pursuant to the authority vested in me by section 414(b) of the Career Compensation Act of 1949, "
    "I hereby prescribe the following regulations:\n\n"
    "SECTION 1. The terms \"uniformed services\" and \"Secretary\" shall have the meaning prescribed therefor.\n\n"
    "SEC. 2 (a) Effective as of October 1, 1949, all duties incident to the payment of disability retirement pay shall be "
    "vested in the Secretary concerned.\n\n"
    "(b) Effective July 1, 1950, all functions exercised by the Veterans' Administration pursuant to Executive Order No. "
    "8099 of April 28, 1939, as amended by Executive Order No. 8461 of June 28, 1940, shall be vested in the Secretary "
    "of the Army.\n\n"
    "SEC. 3. Effective as of October 1, 1949, all duties incident to hospitalization shall be vested in the Secretary concerned.\n\n"
    "SEC. 4 The Secretary concerned shall prescribe the necessary regulations.\n\n"
    "SEC. 7. Nothing in this order shall be construed to affect the duties of the Administrator.\n\n"
    "HARRY S. TRUMAN\n\nThe White House,\nApril 14, 1950."
)

# shards/S11_E_CONT_X6/cache/app_EO14168.txt: "Section 1\n. \nPurpose\n. ..."
APP_14168_BODY = (
    "Executive Order 14168—Defending Women From Gender Ideology Extremism\n\nJanuary 20, 2025\n\n"
    "By the authority vested in me as President by the Constitution and the laws of the United States of America, "
    "it is hereby ordered:\n\n"
    "Section 1\n. \nPurpose\n. Across the country, ideologues have used legal means to permit self-identification.\n\n"
    "Sec. 2\n. \nPolicy and Definitions\n. It is the policy of the United States to recognize two sexes, and the "
    "following definitions shall govern:\n\n"
    "(a) \"Sex\" shall refer to an individual's immutable biological classification.\n\n"
    "(b) \"Women\" or \"woman\" shall mean adult human females.\n\n"
    "Sec. 3\n. \nRecognizing Women Are Biologically Distinct From Men\n. (a) Within 30 days of the date of this order, "
    "the Secretary shall provide guidance.\n\n"
    "(b) Each agency shall enforce laws governing sex-based rights.\n\n"
    "Sec. 4\n. \nGeneral Provisions\n. (a) Nothing in this order shall be construed to impair the authority granted by law.\n\n"
    "(b) This order shall be implemented consistent with applicable law.\n\n"
    "THE WHITE HOUSE,\n\nJanuary 20, 2025."
)

# reviews/V11_E_CONT_X3_REV/cache/gi_eo14251.txt: inserted text closes with  .' ''  then " Sec. 3."
GI_14251 = (
    "Executive Order 14251 of March 27, 2025\n\nExclusions From Federal Labor-Management Relations Programs\n\n"
    " By the authority vested in me as President by the Constitution and the \nlaws of the United States of America, "
    "it is hereby ordered:\n\n"
    " Section 1. Determinations. The agencies set forth in section 2 of this \norder are hereby determined to have as a "
    "primary function \nnational security work.\n"
    " Sec. 2. Additional National Security Exclusions. \n Executive Order 12171 of November 19, 1979, as amended, \n is further amended by:\n"
    " (a) In section 1-101, adding ``and Section 1-4'' \n after ``Section 1-2'' in both places that term appears.\n"
    " (b) Adding after section 1-3 a new section 1-4 that \n reads:\n ``1-4. Additional Exclusions.\n"
    "1-401. The Department of State.\n1-402. The Department of Defense, except for subdivisions excluded \n"
    "pursuant to section 4 of the Executive Order entitled \n`Exclusions from Federal Labor-Management \nRelations Programs.' ''\n"
    " Sec. 3. Foreign Service Exclusions. Executive Order \n 12171, as amended, is further amended by:\n"
    " (a) In the first paragraph, adding ``and Title 22'' after ``Title 5''.\n"
    " Sec. 4. General Provisions. (a) Nothing in this order \n shall be construed to impair the authority granted by law.\n"
    "\n THE WHITE HOUSE,\n March 27, 2025.\n\n[FR Doc. 2025-05836 \nFiled 4-2-25; 8:45 am]\n"
)

# stage21 PDF of EO 12974 (60 FR 51875): list of prior amenders; "Execu-\ntive" split over a line.
PDF_12974 = (
    "Executive Order 12974 of September 29, 1995\nContinuance of Certain Federal Advisory Committees\n"
    "By the authority vested in me as President by the Constitution and the laws of the\n"
    "United States of America, it is hereby ordered as follows:\n"
    "Section 1. Each advisory committee listed below is continued until September 30, 1997.\n"
    "(a) President’s Committee of Advisors on Science and Technology; Execu-\n"
    "tive Order No. 12882, as amended (Office of Science and Technology Policy).\n"
    "(b) President’s Committee on the Arts and the Humanities; Executive\n"
    "Order No. 12367, as amended (National Endowment for the Arts).\n"
    "Sec. 3. The following Executive orders or sections thereof, which established\n"
    "committees that have terminated or whose work is completed, are revoked:\n"
    "(a) Executive Order No. 12878, as amended by Executive Order Nos.\n"
    "12887 and 12912, establishing the Bipartisan Commission on Entitlement\nReform; and\n"
    "(b) That portion of section 2 of Executive Order No. 12844 that established\n"
    "the Federal Fleet Conversion Task Force.\n"
    "Sec. 5. This order shall be effective September 30, 1995.\n"
    "THE WHITE HOUSE,\nSeptember 29, 1995.\n"
)

# reviews/V11_G_EVENT_X4_REV/cache/FR-1940-07-04.raw.txt: two interleaved columns, FR masthead in the middle.
OCR_8467 = (
    "\fFEDERAL REGISTER, Thursday, July 4, 1940\n2467\n"
    "EXECUTIVE ORDER\nj. Strontium chemicals\nA mending S ection 7 of E xecutive O rder\nk. Sulphuric acid, fuming\n"
    "No. 7916 of J une 24, 1938, E xtending\n4. Products as follows:\nthe\nC ompetitive C lassified Civil\nS ervice\n"
    "By virtue of the authority vested in\nPublished daily, except Sundays, Mondays, proclamation of May 1, 1937.\n"
    "me by the Constitution, by section 1753\nand days following legal holidays by the\n"
    "Division of the Federal Register, The National in my proclamation of May 1, 1937.\n"
    "United States, section 7 of Executive\nd. Plastics, optically clear.\nOrder No. 7916 of June 24, 1938, extend\xad\n"
    "ing the competitive classified civil serv\xad\nice, is hereby amended to read as\nfollows:\n"
    "Superintendent of Documents directly to the\n“S ec. 7. (a) Effective July 1, 1940, the\n"
    "United States Civil Service Commission is directed to establish a Council.”\n"
    "F ranklin D R oosevelt\nT h e W h it e H o u s e ,\nJune 24, 1940.\n[No. 8467]\n"
    "[F. R. Doc. 40-2602; Filed, July 3, 1940; 11:56 a. m.]\n"
)


def long_regulation():
    """EO 5642 pattern (shards/S11_C_TEMP/cache/app_eo5642.txt): numbered paragraphs
    printed as "1. \\nDefinition.\\n ...", the last one followed by a very long schedule."""
    paras = ["1. \nDefinition.\n \"Foreign Service officer\" shall be deemed to denote permanent officers of the Foreign Service.",
             "2. \nEntry into the Foreign Service.\n Appointments shall be made after examination."]
    long = "3. \nExaminations.\n The board shall formulate rules. " + ("The examinations shall be both written and oral. " * 160)
    return ("Executive Order 5642—Administration of the Foreign Service\n\nJune 08, 1931\n\n"
            "The regulations established in this Executive order shall be effective and binding for the following purposes:\n\n"
            + "\n\n".join(paras + [long]) + "\n\nHERBERT HOOVER\n\nThe White House,\nJune 8, 1931.")


def run(text, number):
    loc = S.locate_order(text, number)
    assert loc is not None, number
    return loc, S.segment(text, loc, "EO:" + number)


def ids(seg):
    return [c["scope_id"].split("#")[1] for c in seg["clauses"]]


class StructureRegressions(unittest.TestCase):
    def test_10122_section_marker_without_period(self):
        loc, seg = run(APP_10122_BODY, "10122")
        self.assertEqual(ids(seg), ["preamble-op", "sec1", "sec2(a)", "sec2(b)", "sec3", "sec4", "sec7"])
        self.assertIn("section_number_gap_4->7", seg["warnings"])
        roles = {r["instrument_id"]: r["role"] for r in seg["clauses"][3]["related_orders"]}
        self.assertEqual(roles, {"EO:8099": "target_candidate", "EO:8461": "mentioned_as_prior_amender"})
        self.assertEqual(len(seg["clauses"][3]["related_orders"]), 2)  # no duplicates

    def test_14168_split_marker_lines(self):
        loc, seg = run(APP_14168_BODY, "14168")
        self.assertEqual(ids(seg), ["sec1", "sec2", "sec2(a)", "sec2(b)", "sec3(a)", "sec3(b)", "sec4(a)", "sec4(b)"])
        by = {c["scope_id"].split("#")[1]: c for c in seg["clauses"]}
        self.assertEqual(by["sec1"]["heading"], "Purpose")
        self.assertEqual(by["sec1"]["clause_kind"], "purpose_or_policy")
        self.assertEqual(by["sec4(a)"]["clause_kind"], "general_provisions")
        self.assertFalse([w for w in seg["warnings"] if w.startswith("incomplete_")])

    def test_11269_roman_section_and_heading_line_that_names_an_order(self):
        self.assertEqual(S.find_headings(APP_11269_BODY), [("11269", 0)])
        loc, seg = run(APP_11269_BODY, "11269")
        self.assertEqual(ids(seg), ["sec1(a)", "sec1(b)", "sec2", "sec5", "sec6"])
        by = {c["scope_id"].split("#")[1]: c for c in seg["clauses"]}
        self.assertEqual(by["sec1(a)"]["label"], "Sec. I(a)")
        self.assertEqual(by["sec5"]["clause_kind"], "amends_other_order")
        self.assertEqual(by["sec5"]["related_orders"], [{"instrument_id": "EO:10033", "role": "target_candidate"}])
        self.assertEqual(by["sec6"]["clause_kind"], "effective_date")

    def test_14251_typed_closing_quotes_end_the_inserted_text(self):
        loc, seg = run(GI_14251, "14251")
        self.assertEqual(ids(seg), ["sec1", "sec2", "sec2(a)", "sec2(b)", "sec3", "sec3(a)", "sec4(a)"])
        b = GI_14251[seg["clauses"][3]["start"]:seg["clauses"][3]["end"]]
        self.assertIn("1-402. The Department of Defense", b)
        self.assertNotIn("Foreign Service Exclusions", b)

    def test_12974_amender_lists_hyphenated_reference_and_effective_date(self):
        loc, seg = run(PDF_12974, "12974")
        by = {c["scope_id"].split("#")[1]: c for c in seg["clauses"]}
        self.assertEqual(by["sec1(a)"]["related_orders"], [{"instrument_id": "EO:12882", "role": "target_candidate"}])
        roles = {r["instrument_id"]: r["role"] for r in by["sec3(a)"]["related_orders"]}
        self.assertEqual(roles, {"EO:12878": "target_candidate", "EO:12887": "mentioned_as_prior_amender",
                                 "EO:12912": "mentioned_as_prior_amender"})
        self.assertEqual(by["sec3(a)"]["clause_kind"], "revokes_or_supersedes_other_order")
        self.assertEqual(by["sec5"]["clause_kind"], "effective_date")

    def test_5642_long_unit_is_flagged(self):
        text = long_regulation()
        loc, seg = run(text, "5642")
        self.assertEqual(ids(seg), ["preamble-op", "para1", "para2", "para3"])
        self.assertTrue(any(w.startswith("incomplete_clause_over_6000_chars_para3") for w in seg["warnings"]))

    def test_unsplit_section_markers_are_flagged(self):
        text = ("Executive Order 13999 of May 1, 2005\nExample\nBy the authority vested in me, it is hereby ordered as follows:\n"
                "Section 1. Policy. The policy is set out here.\n"
                "Sec. 5. Duties. The Secretary shall act and\n"   # a jump the sequence check refuses
                "Sec. 2. Reports. The Secretary shall report.\n"
                "THE WHITE HOUSE,\nMay 1, 2005.\n")
        loc, seg = run(text, "13999")
        self.assertTrue(any(w.startswith("incomplete_section_markers_not_split_") for w in seg["warnings"]))

    def test_8467_ocr_masthead_is_detected(self):
        loc = S.locate_order(OCR_8467, "8467")
        self.assertIsNotNone(loc)
        sig = S.ocr_interleave_signals(OCR_8467, loc.body_start, loc.doc_end)
        self.assertIn("fr_masthead_or_contents_text", sig)

    def test_11609_dated_list_line_is_not_a_heading(self):
        self.assertEqual([n for n, _ in S.find_headings(APP_11609)], ["11609"])
        loc, seg = run(APP_11609, "11609")
        self.assertTrue(loc.signature_found)
        self.assertNotIn("no_signature_block_found", seg["warnings"])
        sec11 = [c for c in seg["clauses"] if c["scope_id"].endswith("#sec11")][0]
        self.assertEqual(sec11["clause_kind"], "revokes_or_supersedes_other_order")
        self.assertEqual([r["instrument_id"] for r in sec11["related_orders"]], ["EO:10604", "EO:11290"])

    def test_2859_identity_doubt(self):
        loc, seg = run(APP_2859, "2859")
        self.assertIn("body_cites_its_own_order_number_identity_doubtful", seg["warnings"])
        ev = S.identity_evidence(APP_2859, loc)
        self.assertEqual(ev["document_year"], 1918)
        # signer / year checks
        self.assertEqual(S.identity_doubts({"signature_line": "DWIGHT D. EISENHOWER", "signer_years": S.signer_years("DWIGHT D. EISENHOWER"),
                                            "document_year": 1956}, 1918),
                         ["identity_doubt_document_dated_1956_expected_1918", "identity_doubt_signer_DWIGHT_D_EISENHOWER_not_president_in_1918"])
        self.assertEqual(S.identity_doubts({"signature_line": "FRANKLIN D ROOSEVELT", "signer_years": S.signer_years("FRANKLIN D ROOSEVELT"),
                                            "document_year": 1941}, 1941), [])

    def test_own_number_in_prescribed_contract_text_is_not_a_doubt(self):
        text = ("Executive Order 11246—Equal Employment Opportunity\n\nSeptember 24, 1965\n\n"
                "By virtue of the authority vested in me, it is ordered as follows:\n\n"
                "SEC. 202. The contractor will send to each labor union a notice advising of the contractor's commitments "
                "under Section 202 of Executive Order No. 11246 of September 24, 1965, and shall post copies of the notice.\n\n"
                "LYNDON B. JOHNSON\n\nThe White House,\nSeptember 24, 1965.")
        loc, seg = run(text, "11246")
        self.assertNotIn("body_cites_its_own_order_number_identity_doubtful", seg["warnings"])

    def test_12957_pronoun_clause_and_inline_first_item(self):
        # stage21 PDF of EO 12957 (60 FR 14615)
        text = ("Executive Order 12957 of March 15, 1995\nProhibiting Certain Transactions\n"
                "By the authority vested in me as President by the Constitution and the laws\n"
                "of the United States of America, including the International Emergency\n"
                "Economic Powers Act (50 U.S.C. 1701 et seq.), the National Emergencies\n"
                "Act (50 U.S.C. 1601 et seq.), and section 301 of title 3, United States\nCode,\n"
                "I, WILLIAM J. CLINTON, President of the United States of America, find\n"
                "that the actions of the Government of Iran constitute a threat, and hereby declare a national emergency.\n"
                "I hereby order:\n"
                "Section 1. The following are prohibited, except to the extent provided in regulations issued\n"
                "pursuant to this order, and notwithstanding any contract entered into before the effective date of this order: (a) the entry\n"
                "into a contract for the development of petroleum resources located in Iran;\n"
                "(b) the entry into a guaranty of another person’s performance under such a contract.\n"
                "Sec. 2. The Secretary of the Treasury is hereby authorized to take such actions as may be necessary.\n"
                "THE WHITE HOUSE,\nMarch 15, 1995.\n")
        loc, seg = run(text, "12957")
        first = text[seg["clauses"][0]["start"]:seg["clauses"][0]["end"]]
        self.assertTrue(first.startswith("I, WILLIAM J. CLINTON, President"), first[:40])
        self.assertTrue(any(w.startswith("incomplete_unsplit_sub_markers_") or w.startswith("incomplete_") for w in seg["warnings"])
                        or "sec1(a)" in ids(seg))

    def test_heading_date_is_the_orders_own(self):
        text = ("Executive Order 9458—Amending Paragraphs 6 and 7 of Executive Order No. 9195 of July 7, 1942\n\n"
                "July 1, 1944\n\nBy virtue of the authority vested in me, it is hereby ordered that paragraph 6 is amended.\n\n"
                "FRANKLIN D ROOSEVELT\n\nThe White House,\nJuly 1, 1944.")
        loc = S.locate_order(text, "9458")
        self.assertEqual(S.identity_evidence(text, loc)["document_year"], 1944)


class SourceRegressions(unittest.TestCase):
    def test_app_page_identity(self):
        self.assertEqual(SRC.app_page_identity(APP_4359A)[:2], ("4359-A", "page_title"))
        self.assertEqual(SRC.app_page_identity(APP_404)[1], "not_an_order_page")
        self.assertEqual(SRC.app_page_identity(APP_11269_BODY)[:2], ("11269", "first_line_heading"))
        self.assertEqual(SRC.app_page_identity("\n\nBy virtue of the authority vested in me ...")[1], "body_only")
        self.assertTrue(SRC.ERROR_PAGE.search(APP_404[:2500]))
        self.assertFalse(SRC.ERROR_PAGE.search(APP_4359A[:2500]))

    def test_app_url_numbers_and_grades(self):
        u = "https://www.presidency.ucsb.edu/documents/executive-order-11669-j-edgar-hoover-retirement"
        self.assertEqual(SRC.app_number_from_url(u, {"EO:11669"}), "11669")
        self.assertEqual(SRC.app_number_from_url("https://www.presidency.ucsb.edu/documents/executive-order-6513-j-amendments",
                                                 {"EO:6513", "EO:6513J"}), "6513-J")
        self.assertEqual(SRC.grade_for_url("https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm"), "official_fr_html_text")
        self.assertEqual(SRC.grade_for_url("https://www.govinfo.gov/content/pkg/FR-2025-04-03/pdf/2025-05836.pdf"), "official_fr_pdf_text_layer")

    def test_ocr_page_map(self):
        pages = []
        for i in range(5):
            num = 2467 + i
            head = f"{num}\nFEDERAL REGISTER, Thursday, July 4, 1940" if i % 2 else f"FEDERAL REGISTER, Thursday, July 4, 1940 {num}"
            pages.append(head + "\nsome text of the page\n" * 5)
        text = "\f".join(pages)
        starts, off = SRC.ocr_page_map(text)
        self.assertEqual(off, 2467)
        a = starts[3] + 10
        self.assertEqual(SRC.ocr_page_label(starts, off, a, a + 5, 1940),
                         "5 FR 2470 (candidate FR page read from OCR page numbers; PDF p. 4)")


def add_members(root: Path, members: dict):
    with zipfile.ZipFile(root / SRC.OPUS_ZIP, "a") as z:
        for name, data in members.items():
            z.writestr("OPUS_STAGE11_FINITE_STATUS_DELTA/evidence/shards/S11_R/cache/" + name, data)


def app_meta(slug, sha_char, status=200, **extra):
    meta = {"url": f"https://www.presidency.ucsb.edu/documents/{slug}", "sha256": sha_char * 64, "http_status": status,
            "retrieved_utc": "2026-10-16T00:00:00Z", "content_type": "text/html; charset=utf-8"}
    meta.update(extra)
    return json.dumps(meta)


class BuildRegressions(unittest.TestCase):
    def build(self, extra_env=None, members=None, universe_extra=()):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "repo"
        build_fixture_repo(root)
        if universe_extra:
            p = root / build.UNIVERSE
            with open(p, "a", encoding="utf-8", newline="") as fh:
                csv.writer(fh).writerows(universe_extra)
        if members:
            add_members(root, members)
        out = Path(tmp.name) / "out"
        env = {"OUTPUT_DIR": str(out), "REPO_ROOT": str(root), "JOB_CACHE_DIR": str(Path(tmp.name) / "cache"),
               "JOB_LIMIT": "", "JOB_IDS": "", "CLAUSE_INPUT_JOBS": "fr-originals", "CLAUSE_ALLOW_PARTIAL_INPUTS": ""}
        env.update(extra_env or {})
        with mock.patch.dict(os.environ, env), mock.patch("sys.stdout", new=io.StringIO()):
            build.main()
        return root, out

    def test_wrong_order_pages_never_reach_fragments(self):
        import hashlib
        members = {
            "APP_EO9709.txt": APP_404,
            "APP_EO9709.meta.json": app_meta("executive-order-9709-air-navigation", "c", 404),
            "APP_EO9710.txt": APP_404,  # error text although the meta says 200
            "APP_EO9710.meta.json": app_meta("executive-order-9710-x", "d", 200),
            "APP_EO4359.txt": APP_4359A,
            "APP_EO4359.meta.json": app_meta("executive-order-4359-citizenship-passports-and-protection", "e", 200,
                                             text_sha256=hashlib.sha256(APP_4359A.encode("utf-8")).hexdigest(), bytes_size=4321),
            "app_EO2859.txt": APP_2859,
            "app_EO2859.meta.json": app_meta("executive-order-2859-national-research-council", "f", "200"),
            "app_eo11609.txt": APP_11609,
            "app_eo11609.meta.json": app_meta("executive-order-11609-delegating-certain-functions", "1", 200),
            "rapp_eo6246.body.txt": "\n\nBy virtue of the authority vested in me, it is hereby ordered that the code is approved.\n\n"
                                    "FRANKLIN D ROOSEVELT\n\nThe White House,\nAugust 19, 1933.\n",
            "rapp_eo6246.meta.json": app_meta("executive-order-6246-code", "2", 200),
        }
        universe = [["EO:9709", "1946", "1937–1989"], ["EO:9710", "1946", "1937–1989"], ["EO:4359", "1925", "1907–1936"],
                    ["EO:4359A", "1925", "1907–1936"], ["EO:2859", "1918", "1907–1936"], ["EO:11609", "1971", "1937–1989"],
                    ["EO:11290", "1966", "1937–1989"], ["EO:10604", "1955", "1937–1989"], ["EO:6246", "1933", "1907–1936"]]
        root, out = self.build(members=members, universe_extra=universe)
        frags = {json.loads(l)["instrument_id"]: json.loads(l) for l in (out / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines()}
        for bad in ("EO:9709", "EO:9710", "EO:4359", "EO:2859", "EO:11290", "EO:10604", "EO:6246"):
            self.assertNotIn(bad, frags, bad)
        self.assertIn("EO:4359A", frags)
        self.assertIn("EO:11609", frags)
        f = frags["EO:4359A"]
        saved = (out / f["data"][0]["text_offsets"]["text_path"]).read_text(encoding="utf-8")
        self.assertTrue(saved.startswith("Executive Order 4359-A—Citizenship"))
        self.assertNotIn("Skip to main content", saved)
        self.assertNotIn("Online by Gerhard Peters", saved)
        with open(out / "IDENTITY_QUARANTINE.csv", encoding="utf-8", newline="") as fh:
            q = {r["instrument_id"]: r for r in csv.DictReader(fh)}
        self.assertIn("body_cites_its_own_order_number_identity_doubtful", q["EO:2859"]["reasons"])
        self.assertIn("no_heading_in_text_identity_from_source_url_only", q["EO:6246"]["reasons"])
        srcs = [json.loads(l) for l in (out / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines()]
        ids_in_sources = {i for s in srcs for i in s["instrument_ids"]}
        self.assertFalse(ids_in_sources & {"EO:2859", "EO:6246", "EO:9709", "EO:4359"})
        s4359 = [s for s in srcs if s["instrument_ids"] == ["EO:4359A"]][0]
        self.assertEqual(s4359["bytes"], 4321)  # from bytes_size
        self.assertIn("sha256 not re-verifiable here", s4359["notes"])
        summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["inputs"]["opus_zip"]["skipped"].get("http_status_404"), 1)
        self.assertEqual(summary["inputs"]["opus_zip"]["skipped"].get("error_or_block_page_text"), 1)
        self.assertGreaterEqual(summary["self_check"]["opus_text_member_sha256_vs_meta_text_hash_for_sources_used"].get("match", 0), 1)
        self.assertEqual(summary["orders_identity_quarantined"], 2)
        self.assertGreaterEqual(summary["source_records_bytes_unknown"], 1)
        with open(out / "CLAUSES.csv", encoding="utf-8", newline="") as fh:
            row = next(csv.DictReader(fh))
        self.assertIn("text_preview", row)
        self.assertNotIn("original_operative_text", row)

    def test_bad_job_limit_and_missing_inputs_stop_the_job(self):
        for bad in ("abc", "0", "-3"):
            with self.assertRaises(SystemExit):
                self.build({"JOB_LIMIT": bad})
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "repo"
        build_fixture_repo(root)
        (root / SRC.OPUS_ZIP).write_text("version https://git-lfs.github.com/spec/v1\noid sha256:00\nsize 1\n", encoding="utf-8")
        out = Path(tmp.name) / "out"
        env = {"OUTPUT_DIR": str(out), "REPO_ROOT": str(root), "JOB_CACHE_DIR": str(Path(tmp.name) / "cache"),
               "JOB_LIMIT": "", "JOB_IDS": "", "CLAUSE_INPUT_JOBS": "fr-originals", "CLAUSE_ALLOW_PARTIAL_INPUTS": ""}
        with mock.patch.dict(os.environ, env), mock.patch("sys.stdout", new=io.StringIO()), \
                mock.patch("sources.subprocess.run", side_effect=RuntimeError("no git lfs in test")):
            with self.assertRaises(SystemExit) as cm:
                build.main()
            self.assertEqual(cm.exception.code, 3)
            self.assertFalse((out / "FRAGMENTS.jsonl").exists())
            env["CLAUSE_ALLOW_PARTIAL_INPUTS"] = "1"
            with mock.patch.dict(os.environ, env):
                build.main()
        summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["inputs"]["availability"]["opus_zip"], "git_lfs_pointer_not_downloaded")
        self.assertEqual(summary["fragments_written"], 2)  # the PDF and the other job's text only


if __name__ == "__main__":
    unittest.main()
