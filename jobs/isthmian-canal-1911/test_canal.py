import csv
import hashlib
import json
import pathlib
import tempfile
import unittest

import canal

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent

CONTENTS = """TABLE OF CONTEI^TS.
Page.
Letter of the President, Mar. 8, 1904, relative to duties of commission 1
Order of tiie President, Mar. 26, 1904, prescribing compensation of commis-
sioners 2
Order of the Secretary of War, Apr. 3, 1905, fixing compensation of commissioners 3
Action of commission, Apr. 3, 1905, in connection with its reorganization 3
Order of the President, Aug. 12, 1V)07, fixing salary of Lieut. Col. AV. C. Gorgas 4
Letter of the Secretary of War, Jan. 5, 1908, transmitting draft of foregoing
order to the President 5
Order of the President, amending civil-service Rule X regarding transfers 6
Order of the President, May 11, 19U, making it a misdemeanor to evade fare 7
■Order of the secretary of W^ar, Mar. 11, 1911, exempting Juan Vampero 8
ni"""

BODY = {
    14: """EXECUTIVE ORDERS
RELATING TO THE
ISTHMIAN CANAL COMMISSION.
White House,
Wasliington, March 8, 1904.
Sirs: I have appointed you as the Commission.
Theodore Roosevelt.
1""",
    15: """"-l EXECUTIVE ORDERS.
The compensation of the members of the Commission shall be as follows.
Theodore Roosevelt.
White House, March 26, 1904.""",
    16: """ISTHMIAN CANAL C0MMI6SI0N. 3
By direction of the President, and in accordance with his order of
April 1, 1905, each member shall be paid a salary.
Wm. H. Taft,
Secretary of IVar.
April 3, 1905.
At a meeting of the Commission, held April 3, 1905, it was resolved:
1. The Commission shall hold quarterly sessions.
.98987—11 2""",
    17: """4 EXECUTIVE OEDEES.
It is hereby ordered that the salary of Lieut. Col. W. C. Gorgas
be fixed at the rate of four-""",
    18: """rSTHMTAK CANAL COMMISSION. 5
teen thousand dollars a year.
Theodore Roosevelt.
The White House, August 12, 1907.
War Department,
Washington, January 5, 1908.
My Dear Mr. President: I enclose herewith a form of Executive Order.
Very sincerely yours, Wm. H. Taft.
The President.""",
    19: """6 EXEGUTlVi: UKDERS.
Rule X of the civil-service rules is amended.
Wm. H. Taft.
The White House, March 23, 1909.""",
    20: """ISTHMIAN CANAL COMMISSION. * 7
Article 1. Evading the fare is a misdemeanor.
Wm. H. Taft.
The White House, May 11, 1911.
I""",
    21: """8
■ EXECUTIVE ORDERS.
Juan Vampero is exempted from the order limiting employment.
Robert Shaw Oliver,
Acting Secretary of War.
War Department,
Washington, D. 0., March 11, 1911.""",
}


def fixture_pages():
    pages = {p: "" for p in range(1, 14)}
    pages[6] = CONTENTS
    pages.update(BODY)
    return pages


class Contents(unittest.TestCase):
    def test_entries_issuers_and_categories(self):
        e = canal.parse_contents(fixture_pages())
        self.assertEqual([x["category"] for x in e],
                         ["presidential_letter", "presidential_order", "secretary_of_war_order", "commission_action",
                          "presidential_order", "secretary_of_war_letter", "presidential_order", "presidential_order",
                          "secretary_of_war_order"])  # 'tiie President', '■Order', 'secretary of W^ar'
        self.assertEqual([x["printed_page"] for x in e], [1, 2, 3, 3, 4, 5, 6, 7, 8])
        self.assertEqual(e[1]["subject"], "prescribing compensation of commissioners")  # hyphen joined, page dropped
        self.assertEqual(e[5]["subject"], "transmitting draft of foregoing order to the President")  # lowercase 'order' continues

    def test_page_number_mid_entry_and_ill(self):
        page = """Order of the Secretary of War, Aug. 15, 1907, appointing Maj. H. F. Hodges,
United States Army, as general purchasing officer of the commission and 119
prescribing approval for vouchers
Order of the Secretary of War, June 22, 1907, amending act No. 24 of the
commission relative to administration of estates of deceased employees on
the Isthmus Ill
Order of the President, Aug. 14, 1908, amending section 344 of the Penal Code
of the Canal Zone, making grand larceny punishable by not exceeding 10
years' imprisonment 154"""
        e = canal.parse_contents({6: page})
        self.assertEqual([x["printed_page"] for x in e], [119, 111, 154])
        self.assertTrue(e[0]["page_mid_entry"])
        self.assertTrue(e[0]["subject"].endswith("commission and prescribing approval for vouchers"))
        self.assertTrue(e[2]["subject"].endswith("not exceeding 10 years' imprisonment"))

    def test_contents_date_misreads(self):
        page = """Letter of the Secretary of War, Mai-. 30, 1905, recommending reorganization 36
Order of the Secretary of War, Dcic. 3, 1904. Importations into the Canal Zone. 17
Order of the President, Feb, 21, 1907, authorizing transfer of John E. Kidwell 83
Order of the President, July 2.5, 1910, empewers commission to establish rules 204
Order of the President, Aug. 20, 19 iO, prescribing method for married women 206
Order of the President, May 11, 19U, making it a misdemeanor 234
Order, of the President, Mar. 14, 1907, refusing permission to aliens 99
Order of tlie President, Mar. 4, 1907, appointing John F. Stevens 88"""
        e = canal.parse_contents({6: page})
        self.assertEqual([x["category"] for x in e[6:]], ["presidential_order", "presidential_order"])
        self.assertEqual([x["category"] for x in e[:2]], ["secretary_of_war_letter", "secretary_of_war_order"])
        got = [(x["month"], x["day"], x["year_candidates"], x["contents_date_ocr_repaired"]) for x in e]
        self.assertEqual(got[:5], [(3, 30, [1905], True), (12, 3, [1904], True), (2, 21, [1907], False),
                                   (7, 25, [1910], True), (8, 20, [1910], True)])
        self.assertEqual(got[5][2], list(range(1904, 1912)))  # '19U': the body decides

    def test_year_candidates_are_clamped(self):
        self.assertEqual(canal.year_candidates("1V)07"), ([1907], True))
        self.assertEqual(canal.year_candidates("1907"), ([1907], False))
        self.assertEqual(canal.year_candidates("1899")[0], [])
        self.assertEqual(canal.year_candidates("19U")[0], list(range(1904, 1912)))


class Pages(unittest.TestCase):
    def test_running_heads_footer_and_title(self):
        lines, info = canal.page_lines(BODY[14], 14)
        self.assertEqual(lines[0], "White House,")          # book title and printed page '1' dropped
        self.assertEqual(lines[-1], "Theodore Roosevelt.")
        lines, info = canal.page_lines(BODY[16], 16)
        self.assertEqual((info["head_number"], info["footer"]), (3, True))
        self.assertNotIn(".98987—11 2", lines)
        for pdf, head in ((17, 4), (18, 5), (20, 7)):
            self.assertEqual(canal.page_lines(BODY[pdf], pdf)[1]["head_number"], head)
        lines, info = canal.page_lines(BODY[19], 19)   # 'EXEGUTlVi: UKDERS', no number
        self.assertEqual((lines[0], info["head_number"]), ("Rule X of the civil-service rules is amended.", 6))
        lines, info = canal.page_lines(BODY[21], 21)   # bare '8' then a second head line
        self.assertEqual(lines[0], "Juan Vampero is exempted from the order limiting employment.")
        lines, _ = canal.page_lines(BODY[20], 20)      # stray 'I' at the foot
        self.assertEqual(lines[-1], "The White House, May 11, 1911.")
        for h in ("16 EXECUTIVE OBDEES.", "2Q4 EXECUTIVE OEDEBS.", "118 • EXECUTIVE OEDERS.", "ISTHMIAN CA.NAL COMMISSION. 177",
                  "TSTHMTAN CANAL COMMTSSTCN. 211", "ISTHMIAN CANAL COMMISSIOl 147", "isthmian canal commission. 53"):
            self.assertTrue(canal.page_lines(h + "\nbody", 30)[1]["head"], h)
        self.assertEqual(canal.page_lines("ISTHMIAN CANAL COMMISSION. 66\nbody", 78)[1]["head_number"], 66)  # misread kept as read

    def test_body_dates(self):
        cases = {
            "The White House, March 26, 1906.": ("1906-03-26", "white_house_strict"),
            "The White House, Septemier 8, 1909.": ("1909-09-08", "white_house_ocr"),
            "The y^HiTE House, March 13, 1907.": ("1907-03-13", "white_house_ocr"),
            "The White House, March I4, 1907.": ("1907-03-14", "white_house_ocr"),
            "The White House, June S, 1905.": ("1905-06-08", "white_house_ocr"),
            "The White House, Decemler 23, 1908.": ("1908-12-23", "white_house_ocr"),
            "The White House, Ajyril 15, 1907.": ("1907-04-15", "white_house_ocr"),
            "The White House, October\n2,1909.": ("1909-10-02", "white_house_strict"),
            "White House,\nWasliington, March 8, 1904.": ("1904-03-08", "white_house_ocr"),
            "White House,\nWashington, D. C, Ajml 1, 1905.": ("1905-04-01", "white_house_ocr"),
            "The White House, August lf>, 1907.": ("1907-08-??", "white_house_ocr"),
            "The White House, March W, 1911.": ("1911-03-??", "white_house_ocr"),
            "CuLEBRA, C. Z., Hay I4, 1909.": ("1909-05-14", "dateline"),
            "Oyster Bay, August 31, 1905.": ("1905-08-31", "dateline"),
            "in accordance with his order of\nApril 1, 1905, each of the seven": ("1905-04-01", "mention"),
        }
        for text, want in cases.items():
            f = canal.body_dates(text)
            self.assertEqual((f[0]["date"], f[0]["where"]), want, text)
        self.assertEqual(canal.date_check("1907-08-15", canal.body_dates("The White House, August lf>, 1907.")), "damaged_day")
        self.assertEqual(canal.date_check("1907-09-13", canal.body_dates("Washington, D. G., September IS, 1907.")),
                         "body_dateline_differs")
        self.assertEqual(canal.date_check("1905-04-01", canal.body_dates("his order of\nApril 1, 1905, each")), "mention_only")


class Documents(unittest.TestCase):
    def setUp(self):
        self.docs, self.stats = canal.build_documents(fixture_pages())

    def test_shared_start_page_is_split_at_the_dateline(self):
        a, b = self.docs[2], self.docs[3]
        self.assertEqual(a["lines"][-1], "April 3, 1905.")
        self.assertTrue(b["lines"][0].startswith("At a meeting"))
        self.assertEqual(a["boundary"], "shared_start_page_split_at_dateline")
        self.assertTrue(a["by_direction_of_president"])
        self.assertEqual(a["category"], "secretary_of_war_order")  # from the contents, not the signer

    def test_tail_on_the_next_documents_first_page(self):
        a, b = self.docs[4], self.docs[5]
        self.assertEqual(a["boundary"], "tail_on_next_documents_first_page")
        self.assertEqual((a["end_page"], a["pdf_pages"]), (5, (17, 18)))
        self.assertEqual(a["lines"][-1], "The White House, August 12, 1907.")
        self.assertEqual(b["lines"][0], "War Department,")
        self.assertEqual((a["date"], a["date_source"], a["date_check"]), ("1907-08-12", "contents_ocr_repaired", "white_house_strict"))
        self.assertEqual(b["signers"], ["William H. Taft (Secretary of War)"])

    def test_document_without_closing_line_is_flagged_not_split(self):
        pages = fixture_pages()
        pages[18] = "rSTHMTAK CANAL COMMISSION. 5\nteen thousand dollars a year.\nNo signature on this page."
        docs, _ = canal.build_documents(pages)
        self.assertEqual(docs[4]["boundary"], "no_closing_line_unsplit")
        self.assertTrue(docs[4]["needs_page_check"] and docs[5]["needs_page_check"])

    def test_dates_from_body_when_contents_has_none_or_a_damaged_year(self):
        g, h = self.docs[6], self.docs[7]
        self.assertEqual((g["date"], g["date_source"], g["date_check"]), ("1909-03-23", "body_only_no_contents_date", "body_only"))
        self.assertTrue(g["needs_page_check"])
        self.assertEqual(g["signers"], ["William H. Taft (President)"])
        self.assertEqual((h["date"], h["date_source"]), ("1911-05-11", "contents_year_from_body"))

    def test_all_dates_and_confidence(self):
        self.assertEqual([d["date"] for d in self.docs],
                         ["1904-03-08", "1904-03-26", "1905-04-03", "1905-04-03", "1907-08-12", "1908-01-05",
                          "1909-03-23", "1911-05-11", "1911-03-11"])
        self.assertEqual([d["confidence"] for d in self.docs][:3], ["high", "high", "high"])
        self.assertEqual(self.docs[8]["signers"], ["Robert Shaw Oliver"])
        self.assertEqual(self.stats["head_number_mismatches"], [])
        self.assertEqual(self.stats["gpo_footers"], [16])

    def test_affected_documents(self):
        docs = [
            {"seq": 1, "date": "1904-06-24", "category": "secretary_of_war_order", "subject": "Establishment and administration of customs service", "lines": []},
            {"seq": 2, "date": "1904-06-24", "category": "secretary_of_war_order", "subject": "establishing postal service", "lines": []},
            {"seq": 3, "date": "1904-12-16", "category": "secretary_of_war_order",
             "subject": "revoking order of June 24, 1904, relative to establishment and administration of customs service", "lines": []},
            {"seq": 4, "date": "1908-02-06", "category": "presidential_order", "subject": "establishing jury trials in the Canal Zone", "lines": []},
            {"seq": 5, "date": "1908-03-31", "category": "presidential_order", "subject": "amending order establishing jury trials in the Canal Zone",
             "lines": ["All orders in conflict herewith are revoked."]},
            {"seq": 6, "date": "1908-08-14", "category": "presidential_order", "subject": "amending section 344 of the Penal Code", "lines": []},
            {"seq": 7, "date": "1909-01-12", "category": "presidential_order", "subject": "providing for appointment",
             "lines": ["The Executive Order of February 20, 1908, prescribing the", "procedure, is hereby amended."]},
            {"seq": 8, "date": "1909-02-01", "category": "presidential_order", "subject": "amending order prescribing procedure in the classified service", "lines": []},
        ]
        rows = canal.affected_rows(docs, {4: ["EO:750"]})
        got = [(r["seq"], r["source"], r["target_resolution"], r["target_seq"]) for r in rows]
        self.assertEqual(got, [(3, "contents", "date_then_subject_words", "1"),
                               (5, "contents", "subject_words_only", "4"),
                               (6, "contents", "target_is_rules_code_or_regulations_not_a_document_here", ""),
                               (7, "body", "referenced_date_not_in_volume", ""),
                               (8, "contents", "unresolved", "")])
        self.assertEqual((rows[1]["target_ids"], rows[1]["revokes_conflicting_orders_clause"]), ("EO:750", "yes"))


class EndToEnd(unittest.TestCase):
    def build(self, td):
        job, out, repo = td / "job", td / "out", td / "repo"
        (job / "data").mkdir(parents=True)
        (repo / "census").mkdir(parents=True)
        pages = fixture_pages()
        text = "".join(json.dumps({"page": p, "text": pages[p]}, ensure_ascii=False) + "\n" for p in sorted(pages))
        (job / "data" / "p.jsonl").write_text(text, encoding="utf-8", newline="\n")
        xw = [["seq", "instrument_id", "lord_seq", "wpa_date", "wpa_citations", "wpa_text", "lord_date", "lord_pairing",
               "lord_summary", "basis"],
              ["2", "EO:100", "", "1904-03-26", "M 20", "Compensation.", "", "", "", "test"],
              ["5", "EO:200½", "", "1907-08-12", "", "Salaries.", "", "", "", "test"],
              ["7", "EO:300", "", "1909", "", "Rule X.", "", "", "", "test"],
              ["8", "EO:400", "", "1911-05-11", "", "Fare.", "", "", "", "test"],
              ["9", "", "1500", "", "", "", "1911-03-11", "paired", "Vampero exempted.", "test"]]
        with open(job / "data" / "xw.csv", "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerows(xw)
        with open(job / "data" / "nv.csv", "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerows([["instrument_id", "wpa_date", "wpa_year", "wpa_citations", "wpa_text"],
                                      ["EO:150", "1905-03-15", "1905", "1905 CSR 86", "Isthmian Canal Service."]])
        with open(repo / "census" / "c.csv", "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerows([["id", "date_effective"], ["EO:100", "1904"], ["EO:200½", ""], ["EO:400", "1910"],
                                      ["EO:150", "1905"], ["EO:UN:x:row:1", ""]])
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        vol = {"key": "T", "title": "t", "short": "T", "published": "p", "digitized_by": "d", "handle_url": "u",
               "pdf": "book.pdf", "pdf_sha256": "0" * 64, "text": "data/p.jsonl", "text_sha256": sha(job / "data" / "p.jsonl"),
               "extractor": "x", "crosswalk": "data/xw.csv", "crosswalk_sha256": sha(job / "data" / "xw.csv"),
               "wpa_not_in_volume": "data/nv.csv", "wpa_not_in_volume_sha256": sha(job / "data" / "nv.csv")}
        prov = {"census": "census/c.csv", "readiness": "none.csv", "volume": vol}
        (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
        return job, out, repo, prov

    def test_run_against_a_small_census(self):
        with tempfile.TemporaryDirectory() as td:
            job, out, repo, prov = self.build(pathlib.Path(td))
            s = canal.run(repo, job, out)
            self.assertEqual((s["contents_entries"], s["pdf_check"]), (9, "pdf_not_checked_out"))
            self.assertEqual(s["census_state_of_eo_ids"], {"NOT_IN_CENSUS": 1, "YEAR_CONFLICT": 1, "census_date_blank": 1,
                                                           "census_year_only": 1})
            with open(out / "CENSUS_LEADS.csv", encoding="utf-8") as fh:
                leads = {(r["lead"], r["instrument_id"] or r["lord_seq"] or r["seq"]) for r in csv.DictReader(fh)}
            self.assertEqual(leads, {("NOT_IN_CENSUS", "1"), ("census_date_blank", "EO:200½"), ("NOT_IN_CENSUS", "EO:300"),
                                     ("YEAR_CONFLICT", "EO:400"), ("LORD_UNNUMBERED_MATCH", "1500"),
                                     ("SECWAR_ORDER_BY_DIRECTION_OF_PRESIDENT_CANDIDATE", "3"),
                                     ("IN_LIST_NOT_IN_VOLUME", "EO:150")})
            with open(out / "FRAGMENTS.jsonl", encoding="utf-8") as fh:
                frags = [json.loads(l) for l in fh]
            self.assertEqual([f["instrument_id"] for f in frags], ["EO:100", "EO:200½", "EO:400"])  # census ids only
            self.assertTrue(all(f["data"]["location_verified"] is False for f in frags))
            self.assertEqual(frags[0]["data"]["route"], "official/ic_compilation_1911")
            body = (out / "texts" / "EO_200-half.txt").read_text(encoding="utf-8").split("\n\n", 1)[1]
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), frags[1]["data"]["text_sha256"])
            self.assertTrue((out / "texts" / "LORD_1500.txt").exists())
            self.assertTrue((out / "texts" / "1904-03-08_presidential_letter_seq001.txt").exists())
            self.assertEqual(s["wpa_date_check"], {"yes": 3, "wpa_partial_year_agrees": 1})
            with open(out / "IC1911_DOCUMENTS.csv", encoding="utf-8") as fh:
                self.assertEqual(sum(1 for _ in csv.DictReader(fh)), 9)

    def test_pdf_and_text_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            job, out, repo, prov = self.build(pathlib.Path(td))
            (repo / "book.pdf").write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1\n")
            self.assertEqual(canal.run(repo, job, out)["pdf_check"], "pdf_is_lfs_pointer_text_layer_hash_verified")
            (repo / "book.pdf").write_bytes(b"%PDF-1.4 not the book")
            with self.assertRaises(SystemExit):
                canal.run(repo, job, out)
            (repo / "book.pdf").unlink()
            prov["volume"]["text_sha256"] = "f" * 64
            (job / "data" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
            with self.assertRaises(SystemExit):
                canal.run(repo, job, out)


class CommittedVolume(unittest.TestCase):
    """Regression guard on the committed text layer and crosswalk."""

    @classmethod
    def setUpClass(cls):
        cls.prov = json.loads((HERE / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
        vol = cls.prov["volume"]
        cls.path = HERE / vol["text"]
        cls.docs, cls.stats = canal.build_documents(canal.load_pages(cls.path))
        cls.by_seq = {d["seq"]: d for d in cls.docs}
        cls.xw = canal.load_csv(HERE / vol["crosswalk"])

    def test_hashes(self):
        vol = self.prov["volume"]
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), vol["text_sha256"])
        self.assertEqual(hashlib.sha256((HERE / vol["crosswalk"]).read_bytes()).hexdigest(), vol["crosswalk_sha256"])

    def test_contents(self):
        cats = {}
        for d in self.docs:
            cats[d["category"]] = cats.get(d["category"], 0) + 1
        self.assertEqual(len(self.docs), 177)
        self.assertEqual(cats, {"presidential_order": 107, "secretary_of_war_order": 62, "presidential_letter": 2,
                                "secretary_of_war_letter": 3, "proclamation": 1, "commission_action": 1,
                                "war_department_circular": 1})
        self.assertTrue(self.stats["pages_monotonic"])
        self.assertEqual(self.by_seq[80]["printed_page"], 119)
        self.assertEqual(self.by_seq[74]["printed_page"], 111)

    def test_page_offset_and_heads(self):
        self.assertEqual(canal.OFFSET, 13)
        self.assertGreaterEqual(self.stats["head_numbers_read"], 200)
        self.assertEqual(self.stats["head_number_mismatches"], [(78, 66), (176, 1153), (193, 130)])
        self.assertEqual(len(self.stats["gpo_footers"]), 15)

    def test_spans_and_boundaries(self):
        spans = [d["end_page"] - d["printed_page"] + 1 for d in self.docs]
        self.assertEqual(spans.count(1), 147)
        self.assertEqual(max(spans), 9)
        self.assertEqual((self.by_seq[3]["printed_page"], self.by_seq[3]["end_page"]), (4, 11))
        self.assertEqual((self.by_seq[29]["printed_page"], self.by_seq[29]["end_page"]), (53, 61))
        b = {d["seq"]: d["boundary"] for d in self.docs if d["boundary"]}
        self.assertEqual(b, {17: "tail_on_next_documents_first_page", 18: "starts_below_previous_documents_tail",
                             19: "shared_start_page_split_at_dateline", 20: "shared_start_page_split_at_dateline",
                             89: "tail_on_next_documents_first_page", 90: "starts_below_previous_documents_tail"})
        self.assertTrue(self.by_seq[6]["lines"][0].startswith("United States Civil Service Commission"))  # wrapper kept
        self.assertEqual(self.by_seq[90]["category"], "secretary_of_war_letter")
        self.assertEqual(self.by_seq[118]["category"], "secretary_of_war_letter")

    def test_dates(self):
        d = self.by_seq
        self.assertEqual([d[s]["date"] for s in (77, 129, 157, 159, 175)],
                         ["1907-08-12", "1909-03-23", "1910-07-25", "1910-08-20", "1911-05-11"])
        self.assertEqual(d[129]["date_source"], "body_only_no_contents_date")
        self.assertEqual(d[175]["date_source"], "contents_year_from_body")
        self.assertEqual([x["seq"] for x in self.docs if x["contents_date_ocr_repaired"]], [7, 18, 77, 157, 159, 175])
        inv = [(self.docs[i]["seq"], self.docs[i + 1]["seq"]) for i in range(176) if self.docs[i + 1]["date"] < self.docs[i]["date"]]
        self.assertEqual(inv, [(10, 11), (17, 18), (89, 90), (117, 118), (148, 149)])
        pres = [x for x in self.docs if x["category"] == "presidential_order"]
        self.assertEqual(sum(1 for x in pres if x["date_check"] == "white_house_strict"), 80)
        self.assertEqual(sum(1 for x in pres if x["date_check"] in canal.CONFIRMED), 103)
        self.assertEqual([x["seq"] for x in pres if x["needs_page_check"]], [6, 78, 129, 171])

    def test_secretary_of_war_orders(self):
        sw = [x for x in self.docs if x["category"] == "secretary_of_war_order"]
        self.assertEqual(sum(1 for x in sw if x["by_direction_of_president"]), 31)
        self.assertTrue(self.by_seq[55]["by_direction_of_president"])  # Lord 1297

    def test_crosswalk(self):
        ids = [x["instrument_id"] for x in self.xw if x["instrument_id"]]
        self.assertEqual((len(ids), len(set(ids))), (105, 105))
        self.assertEqual(len({x["seq"] for x in self.xw if x["instrument_id"]}), 104)
        self.assertEqual([x["instrument_id"] for x in self.xw if x["seq"] == "6"], ["EO:273", "EO:274"])
        self.assertIn("EO:577½", ids)
        self.assertIn("EO:680½", ids)
        lord = {x["seq"]: x["lord_seq"] for x in self.xw if x["lord_seq"]}
        self.assertEqual(lord, {"2": "1269", "14": "1283", "55": "1297", "65": "1298"})
        for x in self.xw:
            doc = self.by_seq[int(x["seq"])]
            if not x["instrument_id"]:
                continue
            self.assertEqual(doc["category"], "presidential_order", x["seq"])
            if x["instrument_id"] == "EO:1345":
                self.assertEqual((x["wpa_date"], doc["date"]), ("1911", "1911-05-02"))  # WPA reads 'Hay 2'
            else:
                self.assertEqual(x["wpa_date"], doc["date"], x["instrument_id"])
        mapped = {int(x["seq"]) for x in self.xw if x["instrument_id"]}
        self.assertEqual([x["seq"] for x in self.docs if x["category"] == "presidential_order" and x["seq"] not in mapped],
                         [2, 14, 65])
        self.assertEqual(len(canal.load_csv(HERE / self.prov["volume"]["wpa_not_in_volume"])), 8)


class CensusSnapshot(unittest.TestCase):
    """Counts against the census and readiness files as they were when the job was built. Skipped
    (not failed) once either file changes; the job then reports the new counts instead."""

    def setUp(self):
        prov = json.loads((HERE / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
        self.snap = prov["test_snapshot"]
        self.census_p, self.ready_p = REPO / prov["census"], REPO / prov["readiness"]
        self.xw = canal.load_csv(HERE / prov["volume"]["crosswalk"])
        self.docs = {d["seq"]: d for d in canal.build_documents(canal.load_pages(HERE / prov["volume"]["text"]))[0]}

    def test_census(self):
        if not self.census_p.exists() or hashlib.sha256(self.census_p.read_bytes()).hexdigest() != self.snap["census_sha256"]:
            self.skipTest("census absent or changed since the snapshot")
        census = {r["id"].upper(): r for r in canal.load_csv(self.census_p)}
        states = {}
        for x in self.xw:
            if x["instrument_id"]:
                st = canal.census_state(census.get(x["instrument_id"].upper()), self.docs[int(x["seq"])]["date"])[0]
                states[st] = states.get(st, 0) + 1
        self.assertEqual(states, {"census_year_only": 102, "census_date_blank": 3})  # all 105 in census, 0 conflicts
        self.assertEqual(sum(1 for k in census if k.startswith("EO:UN")), 19)

    def test_readiness(self):
        if not self.ready_p.exists() or hashlib.sha256(self.ready_p.read_bytes()).hexdigest() != self.snap["readiness_sha256"]:
            self.skipTest("readiness output absent or changed since the snapshot")
        ready = {r["instrument_id"].upper(): r for r in canal.load_csv(self.ready_p)}
        rows = [ready.get(x["instrument_id"].upper(), {}) for x in self.xw if x["instrument_id"]]
        decided_open = sorted(x["instrument_id"] for x, r in zip([x for x in self.xw if x["instrument_id"]], rows)
                              if r.get("provisional_status") and r.get("step_original_text") != "done")
        self.assertEqual(decided_open, ["EO:1153", "EO:283"])


if __name__ == "__main__":
    unittest.main()
