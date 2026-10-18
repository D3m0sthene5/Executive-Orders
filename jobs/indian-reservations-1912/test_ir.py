import csv
import hashlib
import json
import os
import pathlib
import tempfile
import unittest

import ir

HERE = pathlib.Path(__file__).resolve().parent
# The repo holding the census: REPO_ROOT when set (job.py passes it on), else the usual layout.
REPO = pathlib.Path(os.environ.get("REPO_ROOT") or HERE.parent.parent).resolve()
GROVER, TAFT, GRANT, PIERCE, ROOSEVELT = (ir.TERMS[p] for p in ("CLEVELAND", "TAFT", "GRANT", "PIERCE", "ROOSEVELT"))


class Lines(unittest.TestCase):
    def test_running_head_ocr_forms(self):
        for head in ("4 BXECTJTIVE OKDEKS BELATING TO INDIAN RESERVATIONS.",
                     "EXECUTIVE OEDEES EELATING TO INDIAN EESEEVATIONS. 5",
                     "executive obdebs relating to indian besebvations. 531",
                     "EXECUTIVE OEDEES EELATING TO INDIAN EESEEVATIONS. ^5",
                     "■EXEbXTIIVB OEDEES' REtA:TING TO INDIAN EESBEVATI6NS. 47",
                     "EXECUTIVE QEDBES BELATING TOiJM-DIAN KESBEVATIONS. 59"):
            self.assertTrue(ir.is_running_head(head), head)
        for line in ("CAMP VERDE RESERVATION.", "Executive Mansion, April 28, 1875.",
                     "the provisions of the act of Congress approved August 23, 1894"):
            self.assertFalse(ir.is_running_head(line), line)

    def test_signatures(self):
        cases = {"U. S. Grant.": "GRANT", "IT. S. Grant.": "GRANT", "Theodore Eoosbvelt.": "ROOSEVELT",
                 "CiiES'rEE A. Arthur.": "ARTHUR", "GrOVER Cl-EVEIiAND.": "CLEVELAND", "R. B. Hates.": "HAYES",
                 "Wm. H. Taft.": "TAFT", "[seal.] Wm. H. Taft.": "TAFT", "Andrew Johnson, President.": "JOHNSON",
                 "Benj. Harrison.": "HARRISON", "Franklin Pierce,": "PIERCE",
                 "Secretalt of the Interior in letter of 8th instant..'.'.•'■ Franklin Pierce.": "PIERCE"}
        for line, pres in cases.items():
            sig = ir.is_signature(line)
            self.assertIsNotNone(sig, line)
            self.assertEqual(sig[0], pres, line)
        pres, tail, _ = ir.is_signature("A. Lincoln.April 16, 1864.")
        self.assertEqual((pres, tail), ("LINCOLN", "April 16, 1864."))
        for line in ("Robert T. Lincoln,", "Messrs. Smith and Johnson.",
                     "lands to the said Grant and others as stated."):
            self.assertIsNone(ir.is_signature(line), line)

    def test_headers(self):
        for line in ("Executive Mansion, April 28, 1875.", "ExECUTH'E Mansion, March 16, 1877.",
                     "g . Executive MAijfsiON, Decemher ^7, 187^5.", "The White House, February 2, 1911.",
                     "Thu White House, October 20, 1910.", ", The White House, /^(S5'fwar^ 17, JPi^.",
                     "ExECT7Tr\\'B Mansion, July 13, 1880.", "White House, September 15, 1903."):
            self.assertTrue(ir.is_header(line), line)
        for line in ("Chief Moses and other Indians of the Columbia and Colville Reserva-",
                     "Executive action necessary, may be forwarded to the President for his",
                     "28, 1856, which he refers to, premising that the proceedings of his",
                     "Executive order of November 9, 1871, see White Mountain."):
            self.assertFalse(ir.is_header(line), line)

    def test_state_and_reservation_headings(self):
        lines = ["ARIZONA.", "CAMP GEANT RESERVATION.", "Nevada:", "WALKER RIVER RESERVATION.", "Utah.", "text"]
        self.assertEqual(ir.state_heading(lines, 0), "ARIZONA")
        self.assertEqual(ir.state_heading(lines, 2), "NEVADA")
        self.assertIsNone(ir.state_heading(lines, 4))      # not followed by an uppercase line
        self.assertEqual(ir.reservation_heading("ZTJNI PUEBLO RESERVATION."), "ZTJNI PUEBLO RESERVATION")
        self.assertEqual(ir.reservation_heading("YAKAMA RESERVATION (FISHERY)."), "YAKAMA RESERVATION (FISHERY)")
        self.assertEqual(ir.reservation_heading("CAMP McDOWEIL RESERVATION."), "CAMP MCDOWEIL RESERVATION")
        self.assertEqual(ir.reservation_heading("rORT HAH RESERVATION\".")[1:], "ORT HAH RESERVATION")
        self.assertIsNone(ir.reservation_heading("Board of Indian Commissioners, reservation"))
        self.assertIsNone(ir.reservation_heading("[Partly in California.]"))
        self.assertEqual(ir.reservation_heading("GEEENVILLE INDIAN SCHOOL."), "GEEENVILLE INDIAN SCHOOL")


class Dates(unittest.TestCase):
    def test_damaged_digits_resolved_by_term(self):
        y, mo, d, _, repaired = ir.read_date("December 1^, 1872", GRANT)
        self.assertEqual((y, mo, d, repaired), ("1872", 12, "", True))   # several days possible: day left blank
        self.assertEqual(ir.read_date("Decemler SO, 190fl.", ROOSEVELT)[:3], ("1908", 12, "30"))
        self.assertEqual(ir.read_date("D,ec. 13, 1910", TAFT)[:3], ("1910", 12, "13"))
        self.assertEqual(ir.read_date("AtJGTTST 9, 1&55.", PIERCE)[:3], ("1855", 8, "9"))
        # "1375" is 1873 on the page: an italic 8 read as 3, and the last digit is no safer. Only the decade
        # is trusted, so Grant's 1870-1877 leaves the year open; a short term can still settle it.
        self.assertIsNone(ir.read_date("Noveml>er 22, 1375.", GRANT))
        y, mo, d, _, repaired = ir.read_date("June 3, 1381.", ir.TERMS["GARFIELD"])
        self.assertEqual((y, mo, d, repaired), ("1881", 6, "3", True))
        self.assertEqual(ir.read_date("The White House, February 11\n., 1912.", TAFT)[:3], ("1912", 2, "11"))
        self.assertIsNone(ir.read_date("Executive Mansion, June 3, 188^.", ir.TERMS["ARTHUR"]))   # 1882-1884 all fit

    def test_proclamation_clause(self):
        text = ("Done at the city of Washington this 29th day of May, in the year of our Lord one thousand\n"
                "nine hundred and two, and of the independence of the United States the one hundred and twenty-sixth.")
        self.assertEqual(ir.proclamation_date(text)[:3], ("1902", 5, "29"))
        text = "this fifteenth day of February,\nin the year of our Lord one thousand nine hundred and twelve, and"
        self.assertEqual(ir.proclamation_date(text)[:3], ("1912", 2, "15"))

    def test_header_date_never_borrows_from_the_text(self):
        hayes = ir.TERMS["HAYES"]
        self.assertIsNone(ir.header_date("Executive Mansion, /wne ^4, 1879.",
                                         "In lieu of an Executive order dated January 10, 1879, setting apart", hayes))
        self.assertEqual(ir.header_date("Executive Mansion, August", "9,1879.", hayes)[:3], ("1879", 8, "9"))
        self.assertEqual(ir.header_date("The White House,", "February 20, 1912.", TAFT)[:3], ("1912", 2, "20"))
        self.assertEqual(ir.header_date("ExECtTTn^E Mansion,", "Washington, D. C, May 17, 1884.", ir.TERMS["ARTHUR"])[:3],
                         ("1884", 5, "17"))


def page(n, body):
    return {"page": n, "text": f"{n - 13} EXECUTIVE OEDEES EELATING TO INDIAN EESEEVATIONS.\n" + body}


VOLUME = [
    page(16, """ARIZONA.
CAMP VERDE RESERVATION.
Department of the Interior,
Washington, D. C, October 3, 1871.
Sir: I recommend that the tract be set apart.
C. Delano, Secretary.
Executive Mansion, April 28, 1875.
All orders establishing the Camp Verde Indian Reservation are hereby
revoked; and the tract is restored to the public domain. See Executive order of November 22, 1873.
U. S. Grant.
(See act of Congress approved
June 7, 1897, 30 Stats., p. 64.)
57643°—12 2"""),
    page(17, """Executive Mansion, May 15, 1876.
It is hereby ordered that the tract be set apart for the Indians, in lieu of the
Executive order of April 28, 1875.
U. S. Grant.
It is hereby ordered that the following-described lands be withdrawn,
approved June 25,1910:
Wm. H. Taft.
April 15, 1911.
Referred to the Commissioner of the General Land Office for action.
Walter L. Fisher,
Secretary of the Interior.
WASHINGTON.
PUYALLUP RESERVATION.
Department of the Interior,
January 19, 1857.
I recommend the approval of the reservations.
R. McClelland, Secretary.
Approved.
Franklin Pierce,
January 20, 1857."""),
    page(18, """Executive Mansion, Novemher ^4, 187^.
the provisions of the act of Congress approved August 23, 1894, be set aside.
U. S. Grant.
Whereas the lands are reserved;
In witness whereof I have hereunto set my hand.
Done at the city of Washington this 29th day of May, in the year of our Lord one thousand
nine hundred and two, and of the independence the one hundred and twenty-sixth.
[seal.] Theodore Roosevelt.
By the President:
John Hay,
Secretary of State.
218"""),
]


class Parsing(unittest.TestCase):
    def setUp(self):
        self.st, self.heads_removed = ir.stream(VOLUME)
        self.acts, self.heads = ir.parse(self.st)
        ir.lead_ids(self.acts)

    def test_stream_drops_heads_page_numbers_and_gpo_marks(self):
        lines = [x[2] for x in self.st]
        self.assertEqual(self.heads_removed, 3)
        self.assertNotIn("218", lines)
        self.assertFalse(any("57643" in l for l in lines))
        self.assertEqual(self.st[0][:2], (16, 3))   # printed page = PDF page - 13

    def test_acts_kinds_dates_and_boundaries(self):
        got = [(a["kind"], a["signer"], a["date"], a["date_source"]) for a in self.acts]
        self.assertEqual(got, [
            ("order", "GRANT", "1875-04-28", "header"),
            ("order", "GRANT", "1876-05-15", "header"),
            ("indorsement_or_approval", "TAFT", "", ""),           # the referral's date is not the order's
            ("indorsement_or_approval", "PIERCE", "1857-01-20", "date_after_signature"),
            ("order", "GRANT", "", ""),                             # unreadable header: no fallback to 1894
            ("proclamation", "ROOSEVELT", "1902-05-29", "proclamation_done_clause")])
        a, _, taft, pierce, grant, procl = self.acts
        self.assertEqual(a["trailer"], "note")                     # the "(See act ...)" note stays with its act
        self.assertIsNotNone(a["papers"])                          # the Secretary's letter is a related paper
        self.assertEqual(taft["trailer"], "referral")
        self.assertEqual(taft["referral_date"], "1911-04-15")
        self.assertEqual(pierce["state"], "WASHINGTON")
        self.assertEqual(pierce["reservation"], "PUYALLUP RESERVATION")
        self.assertEqual(grant["decade"], "187x")
        self.assertEqual(procl["trailer"], "countersignature")
        self.assertEqual([x["lead_id"] for x in self.acts],
                         ["IR1912:p3:1", "IR1912:p4:1", "IR1912:p4:2", "IR1912:p4:3", "IR1912:p5:1", "IR1912:p5:2"])

    def test_ending_leads_link_the_cited_order(self):
        rows = ir.ending_leads(self.acts, [x[2] for x in self.st])
        second = [r for r in rows if r["lead_id"] == "IR1912:p4:1"][0]
        self.assertIn("supersedes", second["signals"])
        self.assertEqual((second["cited_order_date"], second["target_resolution"], second["target_lead_ids"]),
                         ("1875-04-28", "same_section", "IR1912:p3:1"))
        first = [r for r in rows if r["lead_id"] == "IR1912:p3:1"][0]
        self.assertEqual((first["cited_order_date"], first["target_resolution"]), ("1873-11-22", "not_in_volume_or_unread"))


def act(seq, date, pages, state="ARIZONA", reservation="NAVAJO RESERVATION", signer="TAFT", decade=""):
    return {"seq": seq, "date": date, "printed_start": pages[0], "printed_end": pages[1], "state": state,
            "reservation": reservation, "signer": signer, "decade": decade, "lead_id": f"IR1912:p{pages[0]}:{seq}"}


def wpa(i, year, md, text):
    return {"id": f"EO:{i}", "year": year, "month_day": md, "text": text}


class Matching(unittest.TestCase):
    def test_same_day_cluster_assigned_globally(self):
        acts = [act(1, "1912-02-17", (11, 11), reservation="FORT APACHE RESERVATION"),
                act(2, "1912-02-17", (124, 124), state="NEW MEXICO", reservation="JICARILLA APACHE RESERVATION")]
        numbered = [wpa(1475, "1912", "Feb 17", "Apache National Forest, Ariz., restored to the White Mountain Apache Indian Reservation. IR 11"),
                    wpa(1476, "1912", "Feb 17", "Carson National Forest, N. Mex., restored to the Jicarilla Apache Indian Reservation. IR 124"),
                    wpa(1474, "1912", "Feb 16", "Malachite Administrative Site, Colo.")]
        texts = {1: "the Apache National Forest", 2: "the Carson National Forest"}
        got, ties = ir.match_numbered(acts, numbered, texts)
        self.assertEqual({s: r["id"] for s, (r, _, _) in got.items()}, {1: "EO:1475", 2: "EO:1476"})
        self.assertEqual(ties, {})

    def test_forest_named_in_the_list_must_be_in_the_act(self):
        acts = [act(1, "", (37, 37), reservation="WHITE MOUNTAIN RESERVATION")]
        numbered = [wpa(1477, "1912", "Feb 17", "Crook National Forest, Ariz., restored to the Indian Reservation. IR 37"),
                    wpa(1479, "1912", "Feb 17", "Sitgreaves National Forest, Ariz., restored to the Indian Reservation. IR 37")]
        got, ties = ir.match_numbered(acts, numbered, {1: "the boundaries of the Crooir National Forest"})
        self.assertEqual((got[1][0]["id"], got[1][2]), ("EO:1477", "undated_IR_page_in_term"))

    def test_ties_are_not_paired(self):
        acts = [act(1, "", (37, 37), reservation="WHITE MOUNTAIN RESERVATION"),
                act(2, "", (37, 37), reservation="WHITE MOUNTAIN RESERVATION")]
        numbered = [wpa(1477, "1912", "Feb 17", "Lands restored to the Indian Reservation, Ariz. IR 37"),
                    wpa(1479, "1912", "Feb 17", "Lands restored to the Indian Reservation, Ariz. IR 37")]
        got, ties = ir.match_numbered(acts, numbered, {1: "", 2: ""})
        self.assertEqual(got, {})
        both = {"entries": ["EO:1477", "EO:1479"], "acts": [1, 2]}
        self.assertEqual(ties, {1: both, 2: both})

    def test_two_acts_tied_for_one_entry_is_a_tie(self):
        # the other side of a tie: one entry, two acts at the same score. Neither is paired.
        acts = [act(12, "1912-02-17", (11, 11), reservation="FORT APACHE RESERVATION"),
                act(13, "1912-02-17", (11, 11), reservation="FORT APACHE RESERVATION")]
        numbered = [wpa(1475, "1912", "Feb 17", "Lands restored to the White Mountain Apache Indian Reservation, Ariz. IR 11")]
        got, ties = ir.match_numbered(acts, numbered, {12: "", 13: ""})
        self.assertEqual(got, {})
        both = {"entries": ["EO:1475"], "acts": [12, 13]}
        self.assertEqual(ties, {12: both, 13: both})

    def test_forest_orders_of_one_day_pair_by_the_forest_acted_on(self):
        # IR p. 11 prints the Sitgreaves order, then the Apache order; p. 37 the Crook order. 'Apache' is
        # also in the reservation's name, and the Apache order mentions the Crook forest in passing.
        sitgreaves = ("the boundaries of the Sitgreaves National Forest, Arizona, be further modified by excluding "
                      "therefrom all that part of the White Mountain Apache Indian Reservation included in the said "
                      "Sitgreaves National Forest")
        apache = ("the boundaries of the Apache National Forest, Arizona, be further modified by excluding therefrom "
                  "all that part of the White Mountain Apache Indian Reservation included in said Apache National "
                  "Forest and not transferred to the Crook National Forest, Arizona")
        crook = ("the boundaries of the Crooir National Forest, Arizona, be modified by excluding therefrom that part "
                 "of the White Mountain Apache Indian Reservation included in the Apache National Forest and "
                 "transferred to this, the said Crook National Forest")
        acts = [act(12, "1912-02-17", (11, 11), reservation="FORT APACHE RESERVATION"),
                act(13, "1912-02-17", (11, 11), reservation="FORT APACHE RESERVATION"),
                act(70, "", (37, 37), reservation="WHITE MOUNTAIN OR SAN CARIOS RESERVATION")]
        numbered = [
            wpa(1475, "1912", "Feb 17", "Apache National Forest, Ariz.,diminished, and the excluded lands restored to the "
                                        "White Mountain Apache Indian Reservation. IR 11 ; III K 671."),
            wpa(1477, "1912", "Feb 17", "Crook National Forest, Ariz., diminished, and the excluded lands restored to the "
                                        "White Mountain Apache Indian Reservation. IR 37 ; III K 672."),
            wpa(1479, "1912", "Feb 17", "SitgreavesNational Forest,Ariz.,diminished,and the excluded lands restored to the "
                                        "White Mountain Apache Indian Reservation. IR 37 ; III K 672.")]
        got, ties = ir.match_numbered(acts, numbered, {12: sitgreaves, 13: apache, 70: crook})
        self.assertEqual({s: r["id"] for s, (r, _, _) in got.items()}, {12: "EO:1479", 13: "EO:1475", 70: "EO:1477"})
        self.assertEqual(ties, {})
        self.assertEqual(ir.act_forests(apache), ["Apache", "Apache", "Crook"])

    def test_printings_of_one_order_compete_as_one(self):
        # the same order printed under two reservations; the WPA entry cites neither page
        acts = [act(1, "1912-02-17", (22, 22), reservation="NAVAJO RESERVATION"),
                act(2, "1912-02-17", (130, 130), reservation="ZUNI PUEBLO RESERVATION")]
        numbered = [wpa(1482, "1912", "Feb 17", "Lands restored to the Navajo and Zuni Indian Reservations, Ariz.")]
        got, ties = ir.match_numbered(acts, numbered, {1: "", 2: ""})
        self.assertEqual((got, sorted(ties)), ({}, [1, 2]))                    # as two orders: a tie
        got, ties = ir.match_numbered(acts, numbered, {1: "", 2: ""}, {1: 1, 2: 1})
        self.assertEqual(({s: r["id"] for s, (r, _, _) in got.items()}, ties), ({1: "EO:1482"}, {}))

    def test_month_match_needs_the_ir_page_and_other_states_cost(self):
        acts = [act(1, "1902-12", (37, 37), reservation="WHITE MOUNTAIN RESERVATION", signer="ROOSEVELT"),
                act(2, "1905-07", (127, 127), state="NEW MEXICO", reservation="SANTA CLARA PUEBLO RESERVATION", signer="ROOSEVELT")]
        numbered = [wpa(196, "1902", "Dec 27", "Physician at the Western Navajo Indian Agency, Arizona. 1903 CSR 74."),
                    wpa(344, "1905", "July 29", "Lands in New Mexico reserved for Santa Clara Pueblo Indians. 1R 127 ; III K 687.")]
        got, _ = ir.match_numbered(acts, numbered)
        self.assertEqual({s: r["id"] for s, (r, _, _) in got.items()}, {2: "EO:344"})   # "1R" is OCR for "IR"
        acts = [act(1, "1911-03-22", (29, 29), reservation="SALT RIVER RESERVATION")]
        got, _ = ir.match_numbered(acts, [wpa(9, "1911", "Mar 22", "Lands in California and Oregon withdrawn.")])
        self.assertEqual(got, {})   # same day, but another state and no IR page

    def test_lord_crosswalk_never_forces(self):
        acts = [act(1, "1873-11-22", (6, 6), signer="GRANT"), act(2, "1874-11-16", (6, 6), signer="GRANT"),
                act(3, "1874-05-01", (6, 6), signer="GRANT")]
        lord = [{"seq": "1", "year": "1873", "date": "Nov 22", "pairing": "paired", "summary": "Colorado River. I IR 6", "citation_text": ""},
                {"seq": "2", "year": "1874", "date": "", "pairing": "uncertain", "summary": "I IR 6, 7", "citation_text": ""},
                {"seq": "3", "year": "1874", "date": "Nov 16", "pairing": "paired", "summary": "", "citation_text": "1 IR 6"},
                {"seq": "4", "year": "1880", "date": "", "pairing": "uncertain", "summary": "I IR 6", "citation_text": ""}]
        rows = ir.lord_crosswalk(acts, lord)
        got = [(r["lord_seq"], r["ir_page"], r["resolution"], r["acts"]) for r in rows]
        self.assertEqual(got, [("1", 6, "match", "IR1912:p6:1"), ("2", 6, "ambiguous", "IR1912:p6:2|IR1912:p6:3"),
                               ("2", 7, "ambiguous", "IR1912:p6:2|IR1912:p6:3"), ("3", 6, "match", "IR1912:p6:2"),
                               ("4", 6, "unmatched", "")])


def printing(seq, signer, date, body, decade=""):
    return {"seq": seq, "signer": signer, "date": date, "decade": decade or (date[:3] + "x" if date else ""),
            "lead_id": f"IR1912:p{seq}:1"}, body


SIOUX = ("Executive Mansion, January 11, {y}.\nIt is hereby ordered that the tract of country in the Territory of\n"
         "Dakota lying within the following-described boundaries, viz: Commencing on the east bank of the Missouri\n"
         "River where the forty-sixth parallel of north latitude crosses the same; thence east with said parallel\n"
         "of latitude to the ninety-ninth degree of west longitude; thence south with said degree of longitude to\n"
         "the east bank of the Missouri River; thence up and with the east bank of said river to the place of\n"
         "beginning, be, and the same hereby is, withdrawn from sale and set apart for the use of the several\n"
         "tribes of Sioux Indians as an addition to their present reservation in said Territory.\nU. S. Grant.")
MILITARY = ("Executive Mansion, Washington, {d}.\nThe within request is approved, and the reservation is made and\n"
            "proclaimed accordingly.\nThe Secretary of the Interior will cause the same to be noted in\n"
            "the General Land Office.\nChester A. Arthur.")
FOREST = ("The White House, February 17, 1912.\nUnder authority of the act of Congress of June 4, 1897 (30 Stat.,\n"
          "11 at 34 and 36), and upon recommendation of the Secretary of Agriculture, it is hereby ordered that on\n"
          "and after March 1, 1912, the boundaries of the {f} National Forest, Arizona, as proclaimed March 2, 1909,\n"
          "be further modified by excluding therefrom all that part of the White Mountain Apache Indian Reservation\n"
          "included in said National Forest by said proclamation of March 2, 1909. The purpose of this exclusion\n"
          "is to restore the White Mountain Apache Indian Reservation in all respects to the status existing prior\n"
          "to the said proclamation of March 2, 1909, and said Indian reservation is hereby fully re-created and\n"
          "restored to that status.\nWm. H. Taft.")


class Printings(unittest.TestCase):
    def test_reprints_are_one_order_and_lookalikes_are_not(self):
        pairs = [printing(1, "GRANT", "1875-01-11", SIOUX.format(y=1875)),       # Standing Rock
                 printing(2, "GRANT", "1875-01-11", SIOUX.format(y=1875)),       # Crow Creek: a reprint
                 printing(3, "GRANT", "1876-01-11", SIOUX.format(y=1876)),       # Rosebud: the page reads 1875
                 printing(4, "ARTHUR", "1883-07-17", MILITARY.format(d="July 17, 1883")),    # Fort Reno
                 printing(5, "ARTHUR", "1882-04-18", MILITARY.format(d="April 18, 1882")),   # Fort Supply: same words
                 printing(6, "TAFT", "1912-02-17", FOREST.format(f="Sitgreaves")),
                 printing(7, "TAFT", "1912-02-17", FOREST.format(f="Apache"))]
        acts = [a for a, _ in pairs]
        body = {a["seq"]: b for a, b in pairs}
        group, links = ir.reprint_groups(acts, body)
        self.assertEqual(group, {1: 1, 2: 1, 3: 1, 4: 4, 5: 5, 6: 6, 7: 7})
        # what keeps the lookalikes apart is the date and the forest, not the wording
        for x, y in ((4, 5), (6, 7)):
            r = ir.difflib.SequenceMatcher(None, ir.norm_text(body[x]), ir.norm_text(body[y]), autojunk=False).ratio()
            self.assertGreater(r, ir.REPRINT_MIN, (x, y))

    def test_dates_compatible(self):
        def a(date, decade=""):
            return {"date": date, "decade": decade}
        ok = [("1882-08", "1882-08-04"), ("1912-02-17", "1912-02-11"), ("1875-01-11", "1876-01-11"),
              ("", "1874"), ("1879", "1879-06")]
        for x, y in ok:
            self.assertTrue(ir.dates_compatible(a(x), a(y)), (x, y))
        for x, y in (("1883-07-17", "1882-04-18"), ("1887-09-01", "1887-05"), ("1875-01-11", "1885-01-11")):
            self.assertFalse(ir.dates_compatible(a(x), a(y)), (x, y))
        self.assertFalse(ir.dates_compatible(a("", "188x"), a("1875-01-11")))

    def test_order_date(self):
        five = [{"seq": i, "date": d} for i, d in enumerate(["1875-01-11"] * 4 + ["1876-01-11"])]
        self.assertEqual(ir.order_date(five), ("1875-01-11", "most_printings"))
        two = [{"seq": 13, "date": "1912-02-17"}, {"seq": 71, "date": "1912-02-11"}]
        self.assertEqual(ir.order_date(list(reversed(two)), "1912-02-17"), ("1912-02-17", "printings_tie_wpa_date_agrees"))
        self.assertEqual(ir.order_date(list(reversed(two))), ("1912-02-17", "printings_tie_first_printing"))
        self.assertEqual(ir.order_date([{"seq": 1, "date": "1879-06"}, {"seq": 2, "date": "1879"}]), ("1879-06", "only_partial_dates"))


SECOND = [page(16, """ARIZONA.
WHITE MOUNTAIN RESERVATION.
Executive Mansion, May 15, 1876.
It is hereby ordered that the tract be set apart.
U. S. Grant.
CALIFORNIA.
GEEENVILLE INDIAN SCHOOL.
White House, November 26, 1902.
It is hereby ordered that the quarter section be reserved for Indian school purposes.
T. Roosevelt.
MORONGO BAND.
The White House,
J^dy 7, 1910.
It is hereby ordered that Executive order dated August 25 1877 be revoked in part.
Wm. H. Taft.
COLORADO RIVER RESERVATION.
ExECUTn'E Mansion, Noveml>er 22, 1375.
It is hereby ordered that the tract be withdrawn from sale.
U. S. Grant.""")]


class HeadingsAndHeaders(unittest.TestCase):
    def test_new_state_school_heading_year_on_next_line_and_1375(self):
        acts, _ = ir.parse(ir.stream(SECOND)[0])
        got = [(a["state"], a["reservation"], a["date"], a["decade"], a["date_source"]) for a in acts]
        self.assertEqual(got, [
            ("ARIZONA", "WHITE MOUNTAIN RESERVATION", "1876-05-15", "187x", "header"),
            ("CALIFORNIA", "GEEENVILLE INDIAN SCHOOL", "1902-11-26", "190x", "header"),   # not the Arizona heading
            ("CALIFORNIA", "MORONGO BAND", "1910", "191x", "header_year_only"),           # year on the line below
            ("CALIFORNIA", "COLORADO RIVER RESERVATION", "", "187x", "")])                # 1375: decade only
        self.assertIn("1375", acts[3]["header_unread"])


# The book prints an order again under each reservation it touches: p. 6 here reprints p. 3 and p. 4.
REPRINT_PAGE = page(19, """NEW MEXICO.
SAN JUAN RESERVATION.
Executive Mansion, April 28, 1875.
All orders establishing the Camp Verde Indian Reservation are hereby
revoked; and the tract is restored to the public domain. See Executive order of November 22, 1873.
U. S. Grant.
Executive Mansion, May 15, 1876.
It is hereby ordered that the tract be set apart for the Indians, in lieu of the
Executive order of April 28, 1875.
U. S. Grant.""")


class EndToEnd(unittest.TestCase):
    def build(self, td, pdf_bytes=None, pages=VOLUME):
        job, repo = td / "job", td / "repo"
        (job / "data").mkdir(parents=True)
        (repo / "census").mkdir(parents=True)
        (repo / "wpa").mkdir()
        text = "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pages)
        (job / "data" / "v.jsonl").write_text(text, encoding="utf-8", newline="\n")
        with open(repo / "census" / "c.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "date_effective"])
            w.writerows([["EO:100", "1876"], ["EO:200", "1902"]])
        with open(repo / "wpa" / "NUMBERED_ENTRIES.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "year", "month_day", "text"])
            w.writerows([["EO:100", "1876", "May 15", "Lands set apart for the Indians, Ariz. IR 4"],
                         ["EO:300", "1911", "Apr 14", "Lands withdrawn for a reservoir, San Pasqual Indian Reservation, Calif. IR 9"]])
        with open(repo / "wpa" / "UNNUMBERED_ENTRIES.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["seq", "year", "date", "pairing", "summary", "citation_text"])
            w.writerow(["7", "1875", "Apr 28", "paired", "Camp Verde reservation revoked. I IR 3", ""])
        pdf = "book.pdf"
        if pdf_bytes is not None:
            (repo / pdf).write_bytes(pdf_bytes)
        vol = {"key": "T", "title": "t", "short": "t", "published": "p", "digitized_by": "d", "handle_url": "u",
               "pdf": pdf, "pdf_sha256": hashlib.sha256(b"%PDF real").hexdigest(), "text": "data/v.jsonl",
               "text_sha256": hashlib.sha256((job / "data" / "v.jsonl").read_bytes()).hexdigest(), "extractor": "x",
               "body_pdf_pages": [16, 237], "printed_page_offset": 13}
        prov = {"census": "census/c.csv", "readiness": "none.csv", "wpa_lists": "wpa", "volumes": [vol]}
        (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
        return job, repo, prov

    def test_small_volume_against_small_census(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            job, repo, prov = self.build(td)
            out = td / "out"
            s = ir.run(repo, job, out)
            self.assertEqual((s["acts"], s["numbered_matches"], s["pdf_check"]), (6, 1, "pdf_not_checked_out"))
            with open(out / "CENSUS_LEADS.csv", encoding="utf-8") as fh:
                leads = {(r["lead"], r["lead_id"] or r["instrument_id"]) for r in csv.DictReader(fh)}
            self.assertIn(("BOOK_EXACT_DATE_FOR_YEAR_ONLY", "IR1912:p4:1"), leads)
            self.assertIn(("UNNUMBERED_NOT_IN_CENSUS", "IR1912:p3:1"), leads)
            self.assertIn(("UNDATED_ACT", "IR1912:p5:1"), leads)
            self.assertIn(("WPA_CITATION_MISMATCH", "EO:300"), leads)   # cites IR 9: no act there
            with open(out / "FRAGMENTS.jsonl", encoding="utf-8") as fh:
                frags = [json.loads(l) for l in fh]
            self.assertEqual([f["instrument_id"] for f in frags], ["EO:100"])   # census orders only
            f = frags[0]
            self.assertEqual((f["data"]["location_verified"], f["data"]["needs_page_check"]), (False, False))
            body = (out / f["data"]["text_path"]).read_text(encoding="utf-8").split("\n\n", 1)[1]
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), f["data"]["text_sha256"])
            self.assertTrue(body.startswith("Executive Mansion, May 15, 1876."))
            with open(out / "LORD_IR_CROSSWALK.csv", encoding="utf-8") as fh:
                lord = list(csv.DictReader(fh))
            self.assertEqual((lord[0]["resolution"], lord[0]["acts"]), ("match", "IR1912:p3:1"))
            with open(out / "T_ACTS.csv", encoding="utf-8") as fh:
                acts = list(csv.DictReader(fh))
            self.assertEqual(acts[0]["lord_seqs"], "7")
            self.assertTrue((out / acts[0]["papers_path"]).exists())

    def test_a_reprinted_order_is_one_order(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            job, repo, prov = self.build(td, pages=VOLUME + [REPRINT_PAGE])
            out = td / "out"
            s = ir.run(repo, job, out)
            self.assertEqual((s["acts"], s["orders"], s["reprints"], s["numbered_matches"]), (8, 6, 2, 1))
            with open(out / "CENSUS_LEADS.csv", encoding="utf-8") as fh:
                leads = list(csv.DictReader(fh))
            unnumbered = [l for l in leads if l["lead"] == "UNNUMBERED_NOT_IN_CENSUS"]
            # p. 6:1 reprints the unnumbered p. 3:1: one lead, not two; p. 6:2 reprints EO 100: no lead at all
            ids = [l["lead_id"] for l in unnumbered]
            self.assertEqual(len(ids), 5)                       # 6 orders, one of them EO 100
            self.assertNotIn("IR1912:p6:1", ids)
            self.assertNotIn("IR1912:p6:2", ids)
            camp_verde = unnumbered[ids.index("IR1912:p3:1")]
            self.assertEqual(camp_verde["other_printings"], "IR1912:p6:1")
            self.assertIn("one order, not 2", camp_verde["note"])
            self.assertEqual([l["lead_id"] for l in leads if l["lead"] == "BOOK_EXACT_DATE_FOR_YEAR_ONLY"], ["IR1912:p4:1"])
            with open(out / "FRAGMENTS.jsonl", encoding="utf-8") as fh:
                frags = [json.loads(l) for l in fh]
            self.assertEqual([f["instrument_id"] for f in frags], ["EO:100"])
            self.assertIn("IR1912:p6:2", frags[0]["confidence_note"])
            with open(out / "T_ACTS.csv", encoding="utf-8") as fh:
                rows = {r["lead_id"]: r for r in csv.DictReader(fh)}
            self.assertEqual((rows["IR1912:p6:2"]["numbered_eo"], rows["IR1912:p6:2"]["paired_printing"]), ("EO:100", "IR1912:p4:1"))
            self.assertEqual((rows["IR1912:p6:1"]["order_lead_id"], rows["IR1912:p6:1"]["census"]),
                             ("IR1912:p3:1", "UNNUMBERED_NOT_IN_CENSUS"))
            with open(out / "ENDING_LEADS.csv", encoding="utf-8") as fh:
                endings = list(csv.DictReader(fh))
            self.assertFalse(any(r["lead_id"].startswith("IR1912:p6") for r in endings))   # reprints add no ending rows

    def test_pdf_checks_and_text_hash(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            job, repo, prov = self.build(td, b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1\n")
            self.assertEqual(ir.run(repo, job, td / "o1")["pdf_check"], "pdf_is_lfs_pointer_text_layer_hash_verified")
            (repo / "book.pdf").write_bytes(b"%PDF real")
            self.assertEqual(ir.run(repo, job, td / "o2")["pdf_check"], "match")
            (repo / "book.pdf").write_bytes(b"%PDF other")
            with self.assertRaises(SystemExit):
                ir.run(repo, job, td / "o3")
            (repo / "book.pdf").unlink()
            prov["volumes"][0]["text_sha256"] = "f" * 64
            (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
            with self.assertRaises(SystemExit):
                ir.run(repo, job, td / "o4")

    def test_runs_without_wpa_lists(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            job, repo, prov = self.build(td)
            s = ir.run(repo, job, td / "o", wpa_dir=td / "missing")
            self.assertEqual((s["wpa_lists_read"], s["numbered_matches"], s["acts"]), (False, 0, 6))
            self.assertNotIn("UNNUMBERED_NOT_IN_CENSUS", s["census_leads"])
            self.assertEqual(s["acts_by_census_state"], {"not_compared_wpa_lists_missing": 6})


PROV = json.loads((HERE / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
VOL = PROV["volumes"][0]
WPA_DIR = pathlib.Path(os.environ.get("WPA_DIR") or REPO / PROV["wpa_lists"])
# The pinned counts below were measured with these exact inputs; with other inputs the matching tests are skipped.
PINNED_INPUTS = {
    "NUMBERED_ENTRIES.csv": "5c85b1282914232be6b46e3e5d32823fe1e6203f2e252360d90a8c7a43249e64",
    "UNNUMBERED_ENTRIES.csv": "c0fd09487366f6394594a89d0dff546499904a69c39447d6e89550ee72f43833",
}


def pinned_wpa():
    try:
        return all(hashlib.sha256((WPA_DIR / n).read_bytes()).hexdigest() == h for n, h in PINNED_INPUTS.items())
    except OSError:
        return False


class CommittedVolume(unittest.TestCase):
    """Regression guard on the committed text layer of the 1912 volume."""

    @classmethod
    def setUpClass(cls):
        path = HERE / VOL["text"]
        cls.sha = hashlib.sha256(path.read_bytes()).hexdigest()
        cls.st, cls.heads_removed = ir.stream(ir.load_pages(path), tuple(VOL["body_pdf_pages"]), VOL["printed_page_offset"])
        cls.acts, cls.heads = ir.parse(cls.st)
        ir.lead_ids(cls.acts)

    def test_text_layer_hash(self):
        self.assertEqual(self.sha, VOL["text_sha256"])

    def test_acts_and_headings(self):
        from collections import Counter
        self.assertEqual(len(self.acts), 308)
        self.assertEqual(dict(Counter(a["kind"] for a in self.acts)),
                         {"order": 277, "indorsement_or_approval": 27, "proclamation": 4})
        self.assertEqual(sum(1 for h in self.heads if h["kind"] == "state"), 19)
        self.assertEqual(len({a["lead_id"] for a in self.acts}), 308)
        self.assertEqual(sum(1 for a in self.acts if not a["date"]), 22)
        self.assertEqual(sum(1 for a in self.acts if a["year_in_term"] == "NO"), 2)
        self.assertEqual(sum(1 for a in self.acts if a["date"] and a["date"] < "1900"), 213)
        self.assertEqual(sum(1 for h in self.heads if h["kind"] == "reservation"), 132)

    def test_reprints(self):
        lines = [x[2] for x in self.st]
        body = {a["seq"]: "\n".join(lines[a["act_lines"][0]:a["act_lines"][1] + 1]) for a in self.acts}
        group, _ = ir.reprint_groups(self.acts, body)
        by = {a["lead_id"]: a for a in self.acts}
        orders = {}
        for a in self.acts:
            orders.setdefault(group[a["seq"]], []).append(a["lead_id"])
        self.assertEqual((len(orders), len(self.acts) - len(orders)), (275, 33))
        of = {lid: sorted(orders[group[by[lid]["seq"]]]) for lid in by}
        self.assertEqual(of["IR1912:p37:3"], ["IR1912:p11:3", "IR1912:p37:3"])          # Apache, Feb 17, 1912
        self.assertEqual(of["IR1912:p130:2"], ["IR1912:p130:2", "IR1912:p22:3"])        # Zuni
        self.assertEqual(of["IR1912:p11:2"], ["IR1912:p11:2"])                          # Sitgreaves: its own order
        self.assertEqual(len(of["IR1912:p162:3"]), 5)                                   # Jan 11, 1875 (one copy OCR'd 1876)
        self.assertEqual(len(of["IR1912:p166:1"]), 5)                                   # Aug 9, 1879
        self.assertEqual(of["IR1912:p141:2"], ["IR1912:p141:2"])                        # same words, other date
        self.assertEqual(of["IR1912:p120:1"], ["IR1912:p120:1"])                        # same day, other forest

    def test_every_header_reaches_a_signature(self):
        sig = sorted(a["act_lines"][1] for a in self.acts)
        hdr = [i for i, x in enumerate(self.st) if ir.is_header(x[2].strip())]
        self.assertEqual(len(hdr), 277)
        for a, b in zip(hdr, hdr[1:] + [len(self.st)]):
            self.assertTrue(any(a <= s < b for s in sig), self.st[a])

    def test_known_acts(self):
        by = {a["lead_id"]: a for a in self.acts}
        self.assertEqual((by["IR1912:p5:2"]["date"], by["IR1912:p5:2"]["signer"]), ("1872-12", "GRANT"))
        self.assertEqual(by["IR1912:p81:2"]["date"], "1855-08-09")       # "AtJGTTST 9, 1&55."
        self.assertEqual((by["IR1912:p45:1"]["date"], by["IR1912:p45:1"]["referral_date"]), ("", "1911-04-15"))
        self.assertEqual(by["IR1912:p28:3"]["date"], "1879")              # header month unreadable; not the cited 1879-01-10
        self.assertEqual(by["IR1912:p51:1"]["date"], "1902-05-29")       # proclamation clause
        self.assertEqual((by["IR1912:p6:2"]["date"], by["IR1912:p6:2"]["decade"]), ("", "187x"))   # "1375": the page reads 1873
        self.assertEqual(by["IR1912:p52:1"]["date"], "1910")             # 'The White House,' / 'J^dy 7, 1910.'
        self.assertEqual((by["IR1912:p38:1"]["state"], by["IR1912:p38:1"]["reservation"]),
                         ("CALIFORNIA", "GEEENVILLE INDIAN SCHOOL"))
        longest = max(self.acts, key=lambda a: a["pdf_end"] - a["pdf_start"])
        self.assertEqual((longest["signer"], longest["pdf_start"], longest["pdf_end"]), ("CLEVELAND", 189, 200))

    # Skipped only when the WPA lists are absent or another version. When WPA_DIR is set and pinned but the
    # census cannot be found, the test fails instead of skipping (set REPO_ROOT).
    @unittest.skipUnless(pinned_wpa() and (os.environ.get("WPA_DIR") or (REPO / PROV["census"]).exists()),
                         "WPA lists or census not present, or WPA lists not the pinned version")
    def test_matching_against_the_wpa_lists(self):
        self.assertTrue((REPO / PROV["census"]).exists(), f"census not found under REPO_ROOT={REPO}")
        with tempfile.TemporaryDirectory() as td:
            s = ir.run(REPO, HERE, td, WPA_DIR)
            with open(pathlib.Path(td) / "IR1912_ACTS.csv", encoding="utf-8") as fh:
                rows = {r["lead_id"]: r for r in csv.DictReader(fh)}
        self.assertEqual(s["numbered_matches"], 53)
        self.assertEqual(s["numbered_match_level"], {"exact_date": 42, "same_month_and_IR_page": 10, "undated_IR_page_in_term": 1})
        self.assertEqual(s["numbered_ties_not_paired"], {})
        self.assertEqual(s["wpa_ir_citations"], 45)
        self.assertEqual(s["wpa_ir_citation_resolution"], {"matched_act_on_page": 43, "MATCHED_ACT_ELSEWHERE": 2})
        self.assertEqual((s["lord_ir_citations"], s["lord_rows_citing_ir"]), (249, 178))
        self.assertEqual(s["lord_resolution"], {"match": 182, "ambiguous": 52, "unmatched": 15})
        self.assertEqual(s["census_leads"]["BOOK_EXACT_DATE_FOR_YEAR_ONLY"], 42)
        self.assertEqual(s["census_leads"]["UNNUMBERED_NOT_IN_CENSUS"], 222)      # orders, not printings
        self.assertEqual(s["census_leads"]["REPRINT_DATE_CONFLICT"], 2)
        self.assertEqual(s["fragments"], 53)
        # the Feb 17, 1912 forest orders: each paired with its own forest; reprints inherit, never lead
        got = {k: (rows[k]["numbered_eo"], rows[k]["paired_printing"]) for k in
               ("IR1912:p11:2", "IR1912:p11:3", "IR1912:p37:2", "IR1912:p37:3", "IR1912:p22:3", "IR1912:p130:2")}
        self.assertEqual(got, {"IR1912:p11:2": ("EO:1479", "IR1912:p11:2"), "IR1912:p11:3": ("EO:1475", "IR1912:p11:3"),
                               "IR1912:p37:2": ("EO:1477", "IR1912:p37:2"), "IR1912:p37:3": ("EO:1475", "IR1912:p11:3"),
                               "IR1912:p22:3": ("EO:1482", "IR1912:p22:3"), "IR1912:p130:2": ("EO:1482", "IR1912:p22:3")})
        self.assertEqual((rows["IR1912:p37:3"]["order_date"], rows["IR1912:p37:3"]["confidence"]), ("1912-02-17", "medium"))


if __name__ == "__main__":
    unittest.main()
