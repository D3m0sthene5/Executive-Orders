"""Unit tests for the clause segmenter, with realistic excerpts from several eras.

No network, no repo files. Run: python -m unittest -v test_segment
"""

import unittest

import segment as S

# 1900s: one-paragraph order, web transcription layout (blank-line paragraphs).
ERA_1900S = """Executive Order 365—Withdrawal of Lands for Lighthouse Purposes

June 1, 1905

It is hereby ordered that the following-described lands in the Territory of Arizona be, and they are hereby, withdrawn from settlement, entry, sale, or other disposition, and reserved for use as a site for a lighthouse.

THEODORE ROOSEVELT.

THE WHITE HOUSE, June 1, 1905.
"""

# 1930s-40s: numbered paragraphs with Whereas recitals (EO 8802, abridged).
ERA_1940S = """Executive Order 8802—Reaffirming Policy of Full Participation in the Defense Program

June 25, 1941

Whereas it is the policy of the United States to encourage full participation in the national defense program by all citizens of the United States, regardless of race, creed, color, or national origin; and

Whereas there is evidence that available and needed workers have been barred from employment in industries engaged in defense production:

Now, Therefore, by virtue of the authority vested in me by the Constitution and the statutes, I do hereby reaffirm the policy of the United States that there shall be no discrimination in the employment of workers in defense industries or government because of race, creed, color, or national origin;

And it is hereby ordered as follows:

1. All departments and agencies of the Government of the United States concerned with vocational and training programs for defense production shall take special measures appropriate to assure that such programs are administered without discrimination;

2. All contracting agencies of the Government of the United States shall include in all defense contracts hereafter negotiated by them a provision obligating the contractor not to discriminate against any worker;

3. There is established in the Office of Production Management a Committee on Fair Employment Practice, which shall consist of a Chairman and four other members to be appointed by the President.

FRANKLIN D ROOSEVELT

The White House,
June 25, 1941.
"""

# 1937 Federal Register OCR: no number in the heading, "[No. 7595]" after the signature.
ERA_1937_OCR = """F E D E R A L R E G IS T E R , April 2, 1937
E x e c u t iv e O rder
ESTABLISHING MATIA ISLAND MIGRATORY BIRD REFUGE

Washington
By virtue of and pursuant to the authority vested in me
as President of the United States and by the act of June
25, 1910, ch. 421, 36 Stat. 847, it is ordered that all that area of
unsurveyed land known as Matia Island is hereby reserved and set apart
for the use of the Department of Agriculture as a refuge for migratory birds.
This refuge shall be known as the Matia Island Migratory
Bird Refuge.
F r a n k l in D R o o se v e lt
T h e W h it e H o u s e ,

Mar. 30, 1937.
[No. 7595]
[F . R. Doc. 37-933; Filed, March 31,1937; 1:37 p. m .]

BY THE PRESIDENT OF THE UNITED STATES OF AMERICA
A PROCLAMATION
WHEREAS the tonnage duties are suspended:
NOW, THEREFORE, I do hereby proclaim the suspension.
F r a n k l in D R o o se v e lt
[No. 2429]
"""

# 1950s: "SECTION 1." / "SEC. 2." with subsections, Federal Register print (EO 10450, abridged).
ERA_1950S = """EXECUTIVE ORDER 10450
SECURITY REQUIREMENTS FOR GOVERNMENT EMPLOYMENT
WHEREAS the interests of the national security require that all persons
privileged to be employed in the departments and agencies of the Government
shall be reliable, trustworthy, of good conduct and character; and
WHEREAS the American tradition requires that persons be adjudged by
appropriate standards:
NOW, THEREFORE, by virtue of the authority vested in me by the Constitution
and statutes of the United States, it is hereby ordered as follows:
SECTION 1. In addition to the departments and agencies specified in the
said act of August 26, 1950, the provisions of that act shall apply to all other
departments and agencies of the Government.
SEC. 2. The head of each department and agency of the Government shall
be responsible for establishing and maintaining within his department or
agency an effective program to insure that the employment of any civilian
officer or employee is clearly consistent with the interests of the national security.
SEC. 3. (a) The appointment of each civilian officer or employee in any
department or agency of the Government shall be made subject to investigation.
(b) The head of any department or agency shall designate, or cause to be
designated, any position within his department or agency the occupant of which
could bring about a material adverse effect on the national security as a
sensitive position.
SEC. 4. Executive Order No. 9835 of March 21, 1947, as amended, is hereby
revoked.
DWIGHT D. EISENHOWER
THE WHITE HOUSE,
April 27, 1953.
[F. R. Doc. 53-3800; Filed, Apr. 28, 1953; 10:20 a. m.]
"""

# 2000s/2020s: GovInfo PDF text layer with Sec./(a)/(i), a quoted amendment,
# a running page header in the middle, and a general-provisions section.
ERA_2020S = """Presidential Documents
104857
Federal Register
Vol. 89, No. 247
Thursday, December 26, 2024
Title 3—
The President
Executive Order 14999 of December 18, 2024
Improving the Coordination of Federal Advisory Boards
By the authority vested in me as President by the Constitution and the
laws of the United States of America, it is hereby ordered as follows:
Section 1. Purpose. This order improves the coordination of advisory
boards across the executive branch.
Sec. 2. Amendments to Executive Order 13000. Executive Order 13000 of
April 24, 1996, is amended as follows:
(a) Section 3 is amended to read as follows:
‘‘Sec. 3. Duties. (a) The Board shall advise the Secretary on
coordination.
(b) The Board shall report annually to the President.’’.
(b) Section 4 is revoked.
Sec. 3. Implementation. (a) The heads of executive departments and agencies
shall:
(i) designate a senior official responsible for advisory boards; and
(ii) report to the Director within 90 days of the date of this order.
(b) The Director of the Office of Management and Budget shall issue guidance
104858 Federal Register / Vol. 89, No. 247 / Thursday, December 26, 2024 / Presidential Documents
to implement this order.
Sec. 4. General Provisions. (a) Nothing in this order shall be construed
to impair or otherwise affect:
(i) the authority granted by law to an executive department or agency,
or the head thereof; or
(ii) the functions of the Director of the Office of Management and Budget
relating to budgetary, administrative, or legislative proposals.
(b) This order shall be implemented consistent with applicable law and
subject to the availability of appropriations.
(c) This order is not intended to, and does not, create any right or benefit,
substantive or procedural, enforceable at law or in equity by any party.
THE WHITE HOUSE,
December 18, 2024.
[FR Doc. 2024–31999
Filed 12–23–24; 8:45 am]
Billing code 3395–F4–P
"""

# 1990s: one fused sentence: recital + amendment of another order (EO 13065 style).
ERA_1990S_FUSED = """Executive Order 13065 of October 22, 1997
Further Amendment to Executive Order 13038
By the authority vested in me as President by the Constitution and the
laws of the United States of America, and in order to add up to three
more members to the Advisory Committee, it is hereby ordered that the second
sentence of section 1 of Executive Order 13038, as amended by section
5 of Executive Order 13062, is further amended by deleting ‘‘not more
than 22’’ and inserting ‘‘up to 25’’ in lieu thereof.
THE WHITE HOUSE,
October 22, 1997.
[FR Doc. 97–28427
Filed 10–23–97; 8:45 am]
"""

# 1970s Carter numbering.
ERA_1970S_CARTER = """Executive Order 12999
President's Council on Example Matters
By the authority vested in me as President of the United States of America,
it is hereby ordered as follows:
1-1. Establishment.
1-101. There is established the President's Council on Example Matters.
1-102. The Council shall be composed of not more than nine members.
1-2. Functions.
1-201. The Council shall advise the President on example matters.
JIMMY CARTER
The White House,
May 2, 1979.
"""


def run(text, number):
    loc = S.locate_order(text, number)
    assert loc is not None, number
    return loc, S.segment(text, loc, "EO:" + number)


def texts(text, seg):
    return [text[c["start"]:c["end"]] for c in seg["clauses"]]


class EraTests(unittest.TestCase):
    def check_common(self, text, seg):
        ids = [c["scope_id"] for c in seg["clauses"]]
        self.assertEqual(len(ids), len(set(ids)), "scope ids must be unique")
        for t in texts(text, seg):
            self.assertIn(t, text)
            self.assertNotIn("WHITE HOUSE", t.upper().replace("WHITE HOUSE OFFICE", ""))
            self.assertEqual(t, t.strip())

    def test_1900s_one_paragraph(self):
        loc, seg = run(ERA_1900S, "365")
        self.check_common(ERA_1900S, seg)
        self.assertEqual(seg["structure"], "single_operative_paragraph")
        self.assertEqual([c["scope_id"] for c in seg["clauses"]], ["EO:365#whole"])
        t = texts(ERA_1900S, seg)[0]
        self.assertTrue(t.startswith("It is hereby ordered that"))
        self.assertTrue(t.endswith("site for a lighthouse."))
        self.assertTrue(loc.signature_found)

    def test_1940s_numbered_paragraphs_and_recitals(self):
        loc, seg = run(ERA_1940S, "8802")
        self.check_common(ERA_1940S, seg)
        self.assertEqual(seg["structure"], "numbered_paragraphs")
        ids = [c["scope_id"].split("#")[1] for c in seg["clauses"]]
        self.assertEqual(ids, ["preamble-op", "para1", "para2", "para3"])
        self.assertTrue(texts(ERA_1940S, seg)[0].startswith("I do hereby reaffirm the policy"))
        self.assertEqual(seg["clauses"][0]["clause_kind"], "operative_in_preamble")
        recitals = [ERA_1940S[r["start"]:r["end"]] for r in seg["recitals"]]
        self.assertEqual(len(recitals), 4)
        self.assertTrue(recitals[0].startswith("Whereas"))
        self.assertTrue(recitals[-1].startswith("And it is hereby ordered as follows"))
        self.assertTrue(texts(ERA_1940S, seg)[-1].endswith("appointed by the President."))

    def test_1937_ocr_trailing_number(self):
        loc = S.locate_order(ERA_1937_OCR, "7595")
        self.assertIsNotNone(loc)
        self.assertEqual(loc.heading_style, "trailing_number")
        seg = S.segment(ERA_1937_OCR, loc, "EO:7595")
        self.check_common(ERA_1937_OCR, seg)
        t = texts(ERA_1937_OCR, seg)
        self.assertEqual(len(t), 1)
        self.assertTrue(t[0].startswith("it is ordered that all that area"))
        self.assertTrue(t[0].endswith("Bird Refuge."))
        # the proclamation's "[No. 2429]" must not be taken for an executive order
        self.assertIsNone(S.locate_order(ERA_1937_OCR, "2429"))
        self.assertEqual([n for n, _ in S.find_headings(ERA_1937_OCR)], ["7595"])

    def test_1950s_sections_with_subsections(self):
        loc, seg = run(ERA_1950S, "10450")
        self.check_common(ERA_1950S, seg)
        self.assertEqual(seg["structure"], "sections")
        ids = [c["scope_id"].split("#")[1] for c in seg["clauses"]]
        self.assertEqual(ids, ["sec1", "sec2", "sec3(a)", "sec3(b)", "sec4"])
        sec4 = seg["clauses"][-1]
        self.assertEqual(sec4["clause_kind"], "revokes_or_supersedes_other_order")
        self.assertEqual([r["instrument_id"] for r in sec4["related_orders"]], ["EO:9835"])
        self.assertEqual(len(seg["recitals"]), 3)
        self.assertTrue(ERA_1950S[loc.body_end:loc.doc_end].startswith("DWIGHT D. EISENHOWER"))
        self.assertTrue(ERA_1950S[:loc.doc_end].endswith("10:20 a. m.]"))

    def test_2020s_sections_quotes_furniture_general_provisions(self):
        loc, seg = run(ERA_2020S, "14999")
        self.check_common(ERA_2020S, seg)
        by = {c["scope_id"].split("#")[1]: c for c in seg["clauses"]}
        self.assertEqual(list(by), ["sec1", "sec2", "sec2(a)", "sec2(b)", "sec3(a)", "sec3(b)", "sec4(a)", "sec4(b)", "sec4(c)"])
        self.assertEqual(by["sec1"]["clause_kind"], "purpose_or_policy")
        self.assertEqual(by["sec2"]["clause_kind"], "amends_other_order")
        self.assertEqual(by["sec2"]["related_orders"][0]["instrument_id"], "EO:13000")
        # the quoted "Sec. 3." and "(b) The Board" stay inside sec2(a)
        a = ERA_2020S[by["sec2(a)"]["start"]:by["sec2(a)"]["end"]]
        self.assertIn("‘‘Sec. 3. Duties.", a)
        self.assertIn("(b) The Board shall report annually", a)
        self.assertIn("(ii) report to the Director", ERA_2020S[by["sec3(a)"]["start"]:by["sec3(a)"]["end"]])
        self.assertTrue(by["sec3(b)"]["contains_page_furniture"])
        self.assertNotIn("Federal Register /", S.reading_text(ERA_2020S, by["sec3(b)"]["start"], by["sec3(b)"]["end"]))
        for k in ("sec4(a)", "sec4(b)", "sec4(c)"):
            self.assertEqual(by[k]["clause_kind"], "general_provisions")
        self.assertEqual(len(seg["recitals"]), 1)
        self.assertIn("[FR Doc. 2024–31999", ERA_2020S[loc.body_end:loc.doc_end])

    def test_1990s_fused_recital_and_amendment(self):
        loc, seg = run(ERA_1990S_FUSED, "13065")
        self.check_common(ERA_1990S_FUSED, seg)
        self.assertEqual(seg["structure"], "single_operative_paragraph")
        c = seg["clauses"][0]
        self.assertTrue(ERA_1990S_FUSED[c["start"]:c["end"]].startswith("it is hereby ordered that the second"))
        self.assertEqual(c["clause_kind"], "amends_other_order")
        roles = {r["instrument_id"]: r["role"] for r in c["related_orders"]}
        self.assertEqual(roles, {"EO:13038": "target_candidate", "EO:13062": "mentioned_as_prior_amender"})
        rec = ERA_1990S_FUSED[seg["recitals"][0]["start"]:seg["recitals"][0]["end"]]
        self.assertTrue(rec.startswith("By the authority vested in me"))
        self.assertTrue(rec.endswith("Advisory Committee,"))

    def test_1970s_carter_dash_numbering(self):
        loc, seg = run(ERA_1970S_CARTER, "12999")
        self.check_common(ERA_1970S_CARTER, seg)
        ids = [c["scope_id"].split("#")[1] for c in seg["clauses"]]
        self.assertEqual(ids, ["sec1-101", "sec1-102", "sec1-201"])


class HelperTests(unittest.TestCase):
    def test_number_boundaries(self):
        self.assertIsNone(S.locate_order(ERA_2020S, "1499"))
        self.assertIsNone(S.locate_order(ERA_2020S, "149990"))

    def test_wrapped_reference_is_not_a_heading(self):
        text = "Sec. 3. December 24 shall be considered as falling within the scope\nExecutive Order 11582 of February 11, 1971, and of 5 U.S.C. 5546.\n"
        self.assertEqual(S.find_headings(text), [])

    def test_recital_split_variants(self):
        def split(p):
            rec, op = S.split_recital(p, 0, len(p))
            return (p[rec[0]:rec[1]] if rec else None), (p[op[0]:op[1]] if op else None)

        self.assertEqual(split("By the authority vested in me, it is hereby ordered as follows:"),
                         ("By the authority vested in me, it is hereby ordered as follows:", None))
        rec, op = split("Under and pursuant to the act of June 25, 1910, the sum of $100,000 is hereby allocated for relief.")
        self.assertEqual(op, "the sum of $100,000 is hereby allocated for relief.")
        rec, op = split("By virtue of the authority vested in me, Executive Order No. 9805 of November 1946, as amended, is hereby amended as follows:")
        self.assertEqual(op, "Executive Order No. 9805 of November 1946, as amended, is hereby amended as follows:")
        rec, op = split("Whereas the Council exists; and")
        self.assertIsNone(op)
        rec, op = split("The Secretary of War shall take charge of the property.")
        self.assertIsNone(rec)
        rec, op = split("I, WILLIAM J. CLINTON, President of the United States of America, in order to take steps, hereby order:")
        self.assertIsNone(op)

    def test_signature_lines(self):
        for line in ("FRANKLIN D ROOSEVELT", "F r a n k l in D R o o se v e lt", "THEODORE ROOSEVELT.", "JOSEPH R. BIDEN JR.", "WM. H. TAFT"):
            self.assertTrue(S.is_signature_line(line), line)
        for line in ("The Secretary of the Treasury shall", "PART II—GENERAL PROVISIONS"):
            self.assertFalse(S.is_signature_line(line), line)

    def test_furniture(self):
        self.assertTrue(S.is_furniture("310 Federal Register / Vol. 60, No. 1 / Tuesday, January 3, 1995 / Presidential Documents"))
        self.assertTrue(S.is_furniture("VerDate Sep<11>2014 15:48 Dec 23, 2024 Jkt 265001 PO 00000 Frm 00001 Fmt 4705"))
        self.assertTrue(S.is_furniture("[[Page 4078]]"))
        self.assertFalse(S.is_furniture("Sec. 2. The heads of executive departments"))

    def test_unnumbered_multi_paragraph_and_quoted_insertion(self):
        text = (
            "Executive Order 6128—Amending Rule 54\n\nMay 1, 1933\n\n"
            "By virtue of the authority vested in me, I do hereby amend rule 54 of Executive Order No. 4314 to read as follows:\n\n"
            "\"Rule 54. Authorized Speed of Transit: The following speeds shall not be exceeded:\n\n"
            "Gatun Lake channels............ 15\n\n"
            "Gaillard Cut................... 6\"\n\n"
            "This order shall take effect immediately.\n\n"
            "FRANKLIN D ROOSEVELT\n\nThe White House,\nMay 1, 1933.\n"
        )
        loc, seg = run(text, "6128")
        ids = [c["scope_id"].split("#")[1] for c in seg["clauses"]]
        self.assertEqual(ids, ["p1", "p2"])
        first = text[seg["clauses"][0]["start"]:seg["clauses"][0]["end"]]
        self.assertTrue(first.startswith("I do hereby amend rule 54"))
        self.assertTrue(first.endswith("6\""))
        self.assertEqual(seg["clauses"][0]["clause_kind"], "amends_other_order")
        self.assertEqual(seg["clauses"][1]["clause_kind"], "effective_date")

    def test_body_only_and_identity_warning(self):
        text = "\n\nMay 11, 1918\n\nWHEREAS the Council was perpetuated as requested in Executive Order No. 2859 of May 11, 1918:\n\nNOW, THEREFORE, it is ordered as follows:\n\n1. The functions of the Council shall be to stimulate research.\n\n2. The Government shall be represented on the Council.\n\nDWIGHT D. EISENHOWER\n\nThe White House,\nMay 10, 1956.\n"
        loc = S.locate_body_only(text)
        seg = S.segment(text, loc, "EO:2859")
        self.assertIn("body_cites_its_own_order_number_identity_doubtful", seg["warnings"])
        self.assertEqual([c["scope_id"].split("#")[1] for c in seg["clauses"]], ["para1", "para2"])

    def test_revocation_list_items_inherit_lead_in_verb(self):
        text = (
            "Executive Order 14148 of January 20, 2025\nInitial Rescissions of Example Orders\n"
            "By the authority vested in me as President by the Constitution and the laws of the\n"
            "United States of America, it is hereby ordered as follows:\n"
            "Section 1. Purpose. This order rescinds certain earlier orders.\n"
            "Sec. 2. Revocation of Orders. The following executive actions are hereby revoked:\n"
            "(a) Executive Order 13985 of January 20, 2021 (Advancing Racial Equity);\n"
            "(b) National Security Memorandum 3 of February 4, 2021; and\n"
            "(c) Executive Order 13986 of January 20, 2021 (Ensuring a Lawful Census).\n"
            "THE WHITE HOUSE,\nJanuary 20, 2025.\n"
        )
        loc, seg = run(text, "14148")
        by = {c["scope_id"].split("#")[1]: c for c in seg["clauses"]}
        self.assertEqual(by["sec2"]["clause_kind"], "lead_in")
        self.assertEqual(by["sec2(a)"]["clause_kind"], "revokes_or_supersedes_other_order")
        self.assertEqual(by["sec2(a)"]["related_orders"], [{"instrument_id": "EO:13985", "role": "target_candidate"}])
        self.assertEqual(by["sec2(b)"]["clause_kind"], "operative")  # a memorandum, no order number
        self.assertEqual(by["sec2(c)"]["related_orders"][0]["instrument_id"], "EO:13986")

    def test_placeholder_text_is_not_a_clause(self):
        text = "\n\n(this executive order was not published)\n\n"
        loc = S.locate_body_only(text)
        seg = S.segment(text, loc, "EO:9754")
        self.assertEqual(seg["clauses"], [])
        self.assertIn("source_says_order_text_not_published", seg["warnings"])

    def test_ocr_spaced_section_markers_run_on(self):
        text = (
            "Executive Order 11513\nESTABLISHING THE COMMISSION\n"
            "B y virtue o f the authority vested in me, it is ordered as follow s :\n"
            "S ection 1. Establishment o f the Commission, (a ) There is hereby\nestablished the Commission.\n"
            "(b ) The Commission shall be composed o f sixteen members. S ec . 2. Functions. I t shall\nreport to the President.\n"
            "T h e W hite H ouse,\nM a rch 3,1970.\n[F.R. Doc. 70-2764; Filed, Mar. 3, 1970 ; 5:03 p.m.]\n"
        )
        loc, seg = run(text, "11513")
        ids = [c["scope_id"].split("#")[1] for c in seg["clauses"]]
        self.assertEqual(ids, ["sec1(a)", "sec1(b)", "sec2"])


if __name__ == "__main__":
    unittest.main()
