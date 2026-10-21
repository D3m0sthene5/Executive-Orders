import csv
import hashlib
import json
import pathlib
import tempfile
import unittest

import ofr

HERE = pathlib.Path(__file__).resolve().parent

PAGE_A = """Herbert Hoover , 1929-1933 EO 5550
Executive Order 5550. February 6, 1931
Executive Order
Withdrawal of Public Lands for Classification
Executive Order No. 5327 of April 15, 1930 , withdrawing lands is hereby revoked.
HERBERT HOOVER
[No. 5550]
Executive Order 6022 -A . February 10 , 1933
Executive Order
CLASSIFICATION OF MR. HARRY A. MCBRIDE
Harry A. McBride may be classified
781"""
PAGE_B = """ΕΟ 6022-A Executive Orders
as a Foreign Service officer.
HERBERT HOOVER
[No. 6022-A ]
Executive Order 6023. February 11, 1933
Executive Order
WAIVER OF AGE LIMIT
The age limit is waived.
782"""
PAGE_C = """Executive Order 6024. February
12, 1933
Executive Order
No closing tag on this one.
783"""
PAGE_D = """HERBERT HOOVER
[No. 5634
]
Executive Order 5635. June
2, 1931
Executive Order
Appointment.
[No. 5635]
784"""


class Parsing(unittest.TestCase):
    def test_headings_and_closing_tags(self):
        m = ofr.HEADING.match("Executive Order 6022 -A . February 10 , 1933")
        self.assertEqual(ofr.order_id(m.group(1), m.group(2)), "EO:6022A")
        self.assertEqual(m.group(3), "February")
        self.assertIsNone(ofr.HEADING.match("Executive Order No. 5327 of April 15, 1930 , withdrawing"))
        tags = [ofr.order_id(c.group(1), c.group(2)) for c in ofr.CLOSING.finditer("[No. 5555 ] [No. 5855-A] [No 6070]")]
        self.assertEqual(tags, ["EO:5555", "EO:5855A", "EO:6070"])

    def test_page_lines_drop_running_head_and_page_number(self):
        lines, printed = ofr.page_lines(PAGE_B)
        self.assertEqual(printed, "782")
        self.assertEqual(lines[0], "as a Foreign Service officer.")
        lines, printed = ofr.page_lines(PAGE_A)
        self.assertTrue(lines[0].startswith("Executive Order 5550."))

    def test_orders_split_across_pages(self):
        orders = ofr.find_orders([(10, PAGE_A), (11, PAGE_B), (12, PAGE_C)])
        ids = [o["instrument_id"] for o in orders]
        self.assertEqual(ids, ["EO:5550", "EO:6022A", "EO:6023", "EO:6024"])
        a, b, c, d = orders
        self.assertEqual((a["date"], a["confidence"], a["pdf_pages"]), ("1931-02-06", "high", (10, 10)))
        self.assertIn("Executive Order No. 5327", "\n".join(a["lines"]))  # a reference, not a new order
        self.assertEqual((b["pdf_pages"], b["printed_pages"], b["closing_tag"]), ((10, 11), ("781", "782"), "match"))
        self.assertNotIn("Executive Order 6023.", "\n".join(b["lines"]))
        self.assertEqual(c["confidence"], "medium")  # runs into the next heading without its own tag
        self.assertNotIn("6024", "\n".join(c["lines"]))
        self.assertEqual((d["closing_tag"], d["confidence"], d["date"]), ("missing", "medium", "1933-02-12"))

    def test_wrapped_heading_date_and_closing_tag(self):
        page = "Executive Order 5634. June 1, 1931\nExecutive Order\nText.\n" + PAGE_D
        a, b = ofr.find_orders([(92, page)])
        self.assertEqual((a["instrument_id"], a["closing_tag"], a["lines"][-1]), ("EO:5634", "match", "]"))
        self.assertEqual((b["instrument_id"], b["date"], b["confidence"]), ("EO:5635", "1931-06-02", "high"))

    def test_table2_year_lines_and_split_columns(self):
        page = """Table 2-EXECUTIVE ORDERS
1929
5076 Mar. 7
5077 Mar. 7 Mrs. Viola B. Pugh, designation to sign land patents
1931
5605 -A Apr. 21 Lighthouse Service, rules
6070 Mar. 3 Something"""
        rows = ofr.parse_table2([(697, page)], 5076, 6070)
        self.assertEqual(sorted(rows), ["EO:5076", "EO:5077", "EO:5605A", "EO:6070"])
        self.assertEqual(rows["EO:5076"]["year_from_table"], 1929)
        self.assertEqual(rows["EO:5076"]["subject_same_line"], "")
        self.assertTrue(rows["EO:5077"]["subject_same_line"].startswith("Mrs. Viola"))
        self.assertEqual((rows["EO:5605A"]["year_from_table"], rows["EO:5605A"]["month"]), (1931, 4))

    def test_table3_pairs_only_same_line(self):
        page = """Table 3-PRESIDENTIAL DOCUMENTS AFFECTED BY
PROCLAMATIONS
1113 . Amended by EO 5925
EXECUTIVE ORDERS
709- Revoked by EO 5800, 5801
1626-
1642-
See Proc . 1886, 1919"""
        rows, unpaired = ofr.parse_table3([(736, page)])
        self.assertEqual([(r["section"], r["affected"], r["action"]) for r in rows],
                         [("proclamation", "1113", "amended"), ("executive_order", "709", "revoked")])
        self.assertEqual(rows[1]["by"], "EO 5800")
        self.assertEqual(unpaired, 2)


class EndToEnd(unittest.TestCase):
    def test_volume_against_a_small_census(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            job, out, repo = td / "job", td / "out", td / "repo"
            (job / "data").mkdir(parents=True)
            (repo / "census").mkdir(parents=True)
            pages = [(i, "front matter") for i in range(1, 22)] + [(22, PAGE_A), (23, PAGE_B), (24, PAGE_C),
                                                                   (25, "TABLES OF\nPRESIDENTIAL DOCUMENTS")]
            text = "".join(json.dumps({"page": p, "text": t}, ensure_ascii=False) + "\n" for p, t in pages)
            (job / "data" / "v.jsonl").write_text(text, encoding="utf-8", newline="\n")
            with open(repo / "census" / "c.csv", "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["id", "date_effective"])
                w.writerows([["EO:5550", "1931"], ["EO:6022a", ""], ["EO:6025", "1933"]])
            vol = {"key": "T", "title": "t", "short": "t", "published": "p", "digitized_by": "d", "handle_url": "u",
                   "pdf": "missing.pdf", "pdf_sha256": "0" * 64, "text": "data/v.jsonl",
                   "text_sha256": hashlib.sha256((job / "data" / "v.jsonl").read_bytes()).hexdigest(),
                   "extractor": "x", "eo_range": [5550, 6025], "table2_range": [5550, 6025]}
            (job / "data" / "PROVENANCE.json").write_text(json.dumps(
                {"census": "census/c.csv", "readiness": "none.csv", "volumes": [vol]}), encoding="utf-8")
            s = ofr.run(repo, job, out)["volumes"][0]
            self.assertEqual(s["orders_printed"], 4)
            with open(out / "CENSUS_LEADS.csv", encoding="utf-8") as fh:
                leads = {(r["instrument_id"], r["lead"]) for r in csv.DictReader(fh)}
            self.assertEqual(leads, {("EO:6022A", "census_date_blank"), ("EO:6023", "NOT_IN_CENSUS"),
                                     ("EO:6024", "NOT_IN_CENSUS"), ("EO:6025", "IN_CENSUS_NOT_FOUND_IN_VOLUME")})
            with open(out / "FRAGMENTS.jsonl", encoding="utf-8") as fh:
                frags = [json.loads(l) for l in fh]
            self.assertEqual([f["instrument_id"] for f in frags], ["EO:5550", "EO:6022A"])  # census ids only
            self.assertFalse(frags[0]["data"]["location_verified"])
            body = (out / "texts" / "EO_6022A.txt").read_text(encoding="utf-8").split("\n\n", 1)[1]
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), frags[1]["data"]["body_sha256"])
            self.assertEqual(hashlib.sha256((out / frags[1]["data"]["text_path"]).read_bytes()).hexdigest(), frags[1]["data"]["text_sha256"])
            vol["text_sha256"] = "f" * 64
            (job / "data" / "PROVENANCE.json").write_text(json.dumps(
                {"census": "census/c.csv", "readiness": "none.csv", "volumes": [vol]}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                ofr.run(repo, job, out)


class CommittedVolume(unittest.TestCase):
    """Regression guard on the committed Hoover vol. II text layer."""

    def test_hoover_v2_is_complete(self):
        prov = json.loads((HERE / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
        vol = prov["volumes"][0]
        path = HERE / vol["text"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), vol["text_sha256"])
        body, tables = ofr.body_and_tables(ofr.load_pages(path))
        orders = ofr.find_orders(body)
        ids = [o["instrument_id"] for o in orders]
        self.assertEqual(len(ids), len(set(ids)))
        plain = {o["number"] for o in orders if not o["suffix"]}
        self.assertEqual(plain, set(range(5550, 6071)))
        self.assertEqual(sorted(i for i in ids if not i[3:].isdigit()),
                         ["EO:5605A", "EO:5638A", "EO:5855A", "EO:6005A", "EO:6022A"])
        self.assertEqual([o["date"] for o in orders if o["instrument_id"] in ("EO:5550", "EO:6070")],
                         ["1931-02-06", "1933-03-03"])
        nums = [o["number"] for o in orders]
        self.assertEqual(nums, sorted(nums))
        self.assertGreater(len(ofr.parse_table2(tables, 5076, 6070)), 990)


if __name__ == "__main__":
    unittest.main()
