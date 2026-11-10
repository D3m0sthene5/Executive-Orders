"""Regression tests for the clause segmenter's heading pattern on real OCR forms.

Each text is the minimal failing snippet copied from a held FR text layer (EO 11202, 11813,
11575, 12072) plus a synthetic Part-numbering case. They build their own input; no outputs are read.
"""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("excavate", Path(__file__).with_name("excavate.py"))
excavate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(excavate)
SOURCE = {"url": "https://example.test/original.pdf", "sha256": "a" * 64, "page_or_item": "30 FR 1, PDF pages 5-6",
          "text_path": "held/order.txt", "text_sha256": "b" * 64}

EO_11202 = """Executive Order 11202
PERMITTING STUDENT TRAINEES TO BE GIVEN CAREER OR CAREER-
CONDITIONAL APPOINTMENTS
By virtue of the authority vested in me by Section 2 of the Civil
Service Act (22 Stat. 403) and Section 1753 of the Revised Statutes
(5 U.S.C. 631), and as President of the United States, it is hereby
ordered as follows:
S ection  1. The appointment of an employee occupying a Student
Trainee position in a shortage occupation that is excepted from the
competitive service under Schedule B of the Civil Service Rules
shall be converted to a career-conditional o r career appointment if he:
(1) has successfully completed a preprofessional cooperative work-
study program and has satisfied all applicable requirements
leading to the award of a bachelor's degree;
(2) has had a minimum of six months' work experience in the
employing agency as a Student Trainee;
(3) is recommended for such appointment by his employing agency;
and ' .
(4) meets all other requirements and conditions prescribed by the
Commission under Section 3 of this Order.
S e c. 2 . As used in this Order, a cooperative work-study program is
a program involving alternating periods of planned work experience
and related study at an accredited college or university.
S e c. 3 . The Civil Service Commission shall prescribe such regula-
tions as may be necessary to carry out the provisions of this Order.
L yndon  B. J ohnson
T h e W h ite H ouse,
M arch 5, 1965.
[F.R. Doc. 65-2465 ; Filed, Mar. 5,1965 ; 4: 09 p.m.]
"""

EO_11813 = """E X E C U T IV E  O R D E R  11813
Perm itting Cooperative Education Students To Be Given Career or
Career-Conditional Appointments
By virtue of the authority vested in me by sections 1301 and 3301 of
title 5 of the United States Code, and as President of the United States,
it is ?  hereby ordered as follows:
, S ection  1. As used in this order, " cooperative education"  describes
a program which provides for a formally arranged schedule of periods
graduation.
Sec . 2. Under this order, the appointment of a cooperative education
student under Schedule B of the civil service rules may be converted
noncompetitively to a career-conditional or career appointment if the
student:
(1 ) has completed within the preceding 90 days a cooperative educa-
tion program that meets the provisions of this order;
(2 ) has satisfied all requirements leading to the award of a bachelor's
degree.
Sec. 3. The Commission shall prescribe regulations.
G erald R. F ord
T h e W h ite H ouse,
O ctober 7, 1974.
[FR Doc.74-23500 Filed 10-8-74;8:45 am]
"""

EO_11575 = """E X E C U T IV E  O R D E R  11575
Delegating Authority
By virtue of the authority vested in me as President of the United States, it is ordered as follows:
S e c t io n 1. (a) The authorities vested in the President by section 301 of title 3
of the United States Code are delegated to the Director.
(b) The Director shall report to the President.
S e c. 2. The Director of the Office of Emergency Preparedness may redelegate
any of the functions delegated to him by this order.
Sec. 3. Rules, regulations, procedures, and documents issued under prior orders
shall remain in effect.
R ichard N ixon
T h e W h ite H ouse,
December 31, 1970.
[FR Doc.71-1 Filed 1-4-71;8:45 am]
"""

EO_12072 = """Executive Order 12072
FEDERAL SPACE MANAGEMENT
By the authority vested in me as President of the United States of America, it is hereby ordered as follows:
1-1 Space Acquisition.
1-101. Federal facilities and Federal use of space in urban areas shall
serve to strengthen the Nation's cities.
1-102. Procedures for meeting space needs in urban areas shall give
serious consideration to the impact a site selection will have.
1-104. The process of meeting Federal space needs in urban areas shall
be consistent with the policies of this Order and shall include consideration of
the following criteria:
(a) Comparability of the site with State, regional, or local development.
(b) Conformity with the activities and programs of other Federal agencies.
1-105. Procedures for meeting space needs in urban areas shall be con-
sistent with the policies of this Order.
Sec. 1-201. The Administrator shall issue regulations.
Jimmy Carter
The White House,
August 16, 1978.
[FR Doc. 78-23101 Filed 8-17-78; 11:08 am]
"""

PARTS = """Executive Order 12999
IMPLEMENTING SOMETHING
By the authority vested in me as President, it is hereby ordered as follows:
PART 1
Sec. 1. Policy. The policy of the United States is as follows.
Sec. 2. Definitions. For purposes of this order the terms mean the following.
PART 2
Sec. 1. Administration. The Secretary shall administer this order.
Sec. 2. Effective date. This order is effective immediately.
Jimmy Carter
The White House,
August 16, 1978.
[FR Doc. 78-23101 Filed 8-17-78; 11:08 am]
"""


def segment(iid, text):
    return excavate.segment(iid, text, SOURCE)["clauses"]


class HeadingTests(unittest.TestCase):
    def test_eo11202_letter_spaced_sections_and_lead_in(self):
        clauses = segment("EO:11202", EO_11202)
        ids = [c["scope_id"] for c in clauses]
        self.assertEqual(ids, ["EO:11202#sec1", "EO:11202#sec1-1", "EO:11202#sec1-2", "EO:11202#sec1-3", "EO:11202#sec1-4",
                               "EO:11202#sec2", "EO:11202#sec3"])
        lead = clauses[0]["text"]
        self.assertTrue(lead.startswith("S ection  1. The appointment"))
        self.assertTrue(lead.rstrip().endswith("if he:"))  # the command that governs the list is its own clause
        self.assertTrue(clauses[5]["text"].startswith("S e c. 2 ."))
        self.assertNotIn("Johnson", clauses[6]["text"])

    def test_eo11813_leading_comma_and_spaced_sec(self):
        clauses = segment("EO:11813", EO_11813)
        ids = [c["scope_id"] for c in clauses]
        self.assertEqual(ids[0], "EO:11813#sec1")
        self.assertIn("EO:11813#sec2", ids)
        sec2 = next(c for c in clauses if c["scope_id"] == "EO:11813#sec2")
        self.assertTrue(sec2["text"].rstrip().endswith("student:"))  # Sec. 2 lead-in precedes its enumerated list
        self.assertIn("EO:11813#sec3", ids)

    def test_eo11575_sec1_a_is_in_a_clause_and_sec2_is_not_inside_d(self):
        clauses = segment("EO:11575", EO_11575)
        ids = [c["scope_id"] for c in clauses]
        self.assertEqual(ids, ["EO:11575#sec1", "EO:11575#sec1-b", "EO:11575#sec2", "EO:11575#sec3"])
        self.assertIn("section 301 of title 3", clauses[0]["text"])

    def test_eo12072_decimal_sections(self):
        clauses = segment("EO:12072", EO_12072)
        ids = [c["scope_id"] for c in clauses]
        for wanted in ("sec1-101", "sec1-102", "sec1-104", "sec1-104-a", "sec1-104-b", "sec1-105", "sec1-201"):
            self.assertIn("EO:12072#" + wanted, ids)
        self.assertEqual(len(ids), len(set(ids)))  # no "-dup" collisions
        self.assertFalse([i for i in ids if "dup" in i])

    def test_part_numbering_that_restarts_keeps_unique_scope_ids(self):
        clauses = segment("EO:12999", PARTS)
        ids = [c["scope_id"] for c in clauses]
        self.assertEqual(ids, ["EO:12999#part1-sec1", "EO:12999#part1-sec2", "EO:12999#part2-sec1", "EO:12999#part2-sec2"])

    def test_continuous_numbering_across_parts_keeps_plain_ids(self):
        text = PARTS.replace("PART 2\nSec. 1.", "PART 2\nSec. 3.").replace("Sec. 2. Effective", "Sec. 4. Effective")
        ids = [c["scope_id"] for c in segment("EO:12999", text)]
        self.assertEqual(ids, ["EO:12999#sec1", "EO:12999#sec2", "EO:12999#sec3", "EO:12999#sec4"])

    def test_plain_headings_and_wrapped_references_unchanged(self):
        text = ("By the authority vested in me, it is hereby ordered as follows:\n"
                "Sec. 1. The Secretary shall act pursuant to\nsection 5. of the Act and shall report.\n"
                "Section 2. This order is effective immediately.\nTHE WHITE HOUSE\nJune 1, 1940.")
        ids = [c["scope_id"] for c in segment("EO:5", text)]
        self.assertEqual(ids, ["EO:5#sec1", "EO:5#sec2"])


if __name__ == "__main__":
    unittest.main()
