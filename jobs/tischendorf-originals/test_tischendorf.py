import datetime as dt
import io
import json
import unittest
from collections import Counter

import fingerprint as fp
import tischendorf as t

ORDER = ("It is hereby ordered that the lands in township twelve north of range four east of the Willamette "
         "meridian in Oregon be withdrawn from settlement and reserved for use by the Bureau of Fisheries as a "
         "hatchery site at Bonneville pending legislation by Congress.")
OTHER = ("It is hereby ordered that Guy Emerson be made eligible for appointment as special agent in the "
         "Treasury Department without regard to the requirements of the civil service rules.")
BOILER = "By virtue of the authority vested in me as President of the United States it is hereby ordered that "


def corpus():
    texts = {f"EO:{n}": BOILER + f"filler words number {n} about routine matters of the service" for n in range(60)}
    texts["EO:1000"], texts["EO:1001"] = BOILER + ORDER, BOILER + OTHER
    return texts


class FingerprintTests(unittest.TestCase):
    def setUp(self):
        self.texts = corpus()
        self.df, self.n = fp.document_frequency(self.texts)

    def test_same_order_scores_high_despite_ocr_noise(self):
        F = fp.Fingerprint(self.texts["EO:1000"], self.df, self.n)
        self.assertTrue(F.distinctive)
        noisy = ORDER.replace("township", "towusliip").replace("Willamette", "Wi11amette")
        self.assertGreater(F.score("EXECUTIVE ORDER 1000\n" + noisy), t.STRONG_SCORE)

    def test_boilerplate_and_other_orders_score_low(self):
        F = fp.Fingerprint(self.texts["EO:1000"], self.df, self.n)
        self.assertLess(F.score(BOILER + OTHER), 0.1)

    def test_phrases_are_rare_runs(self):
        F = fp.Fingerprint(self.texts["EO:1000"], self.df, self.n)
        phrases = F.phrases(k=2, source_text=self.texts["EO:1000"])
        self.assertEqual(len(phrases), 2)
        self.assertTrue(all("authority vested" not in p for p in phrases))


class VerdictTests(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(t.verdict(0.8, "heading", False, True, True), "strong")
        self.assertEqual(t.verdict(0.8, "heading", False, True, False), "lead")       # not government printed
        self.assertEqual(t.verdict(0.8, "heading", False, False, True), "lead")       # generic transcription
        self.assertEqual(t.verdict(0.8, "heading", False, True, True, controls_ok=False), "lead")
        self.assertEqual(t.verdict(0.4, "heading", False, True, True), "lead")
        self.assertEqual(t.verdict(0.55, "heading_ocr_damaged", False, True, True), "lead")
        self.assertEqual(t.verdict(0.65, "heading_ocr_damaged", False, True, True), "strong")
        self.assertEqual(t.verdict(0.8, None, True, True, True), "lead")              # numbers printed, none seen
        self.assertEqual(t.verdict(0.8, None, True, True, True, numbers_printed=False), "strong")
        self.assertIsNone(t.verdict(0.2, "heading", True, True, True))

    def test_dates(self):
        self.assertTrue(t.date_on("Done this 30th day ... July 30, 1914.", "1914-07-30"))
        self.assertFalse(t.date_on("July 31, 1914", "1914-07-30"))
        days = t.fr_issue_days("1937-01-02")
        self.assertEqual(days[0], dt.date(1937, 1, 4))  # Sunday skipped
        self.assertNotIn(dt.date(1937, 1, 3), days)

    def test_header_stripped(self):
        self.assertEqual(t.body_of("Instrument: EO:5\nSource: x\n\nEXECUTIVE ORDER 5"), "EXECUTIVE ORDER 5")
        self.assertEqual(t.body_of("EXECUTIVE ORDER 5\n\nmore"), "EXECUTIVE ORDER 5\n\nmore")


class FakePool:
    def __init__(self, routes):
        self.routes, self.requests, self.bytes_downloaded = routes, 0, 0

    def fetch(self, url):
        self.requests += 1
        for key, body in self.routes.items():
            if key in url:
                raw = body if isinstance(body, bytes) else json.dumps(body).encode()
                return {"url": url, "final_url": url, "sha256": "f" * 64, "bytes": len(raw), "body": raw}
        raise RuntimeError("HTTP 404")


def djvu(pages):
    objs = "".join("<OBJECT>" + "".join(f"<WORD>{w}</WORD>" for w in p.split()) + "</OBJECT>" for p in pages)
    return f"<DjVuXML><BODY>{objs}</BODY></DjVuXML>".encode()


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.texts = corpus()
        self.df, self.n = fp.document_frequency(self.texts)
        self.F = fp.Fingerprint(self.texts["EO:1000"], self.df, self.n)
        self.target = {"instrument_id": "EO:1000", "number": "1000", "date": "1908-11-05", "title": "Hatchery",
                       "_text": self.texts["EO:1000"], "flagged_finds": []}

    def test_ia_fulltext_finds_compilation_page(self):
        pages = ["Title page", "EXECUTIVE ORDER 999\n" + OTHER,
                 "EXECUTIVE ORDER 1000\n" + ORDER + " November 5, 1908. THEODORE ROOSEVELT", "Index"]
        pool = FakePool({
            "page_production": {"response": {"body": {"hits": {"hits": [{"fields": {"identifier": "eocomp1908"}}]}}}},
            "/metadata/eocomp1908": {"metadata": {"title": "Executive orders relating to fisheries",
                                                  "publisher": "Government Printing Office", "collection": ["americana"]},
                                     "files": [{"name": "eocomp1908_djvu.xml", "size": "1000"}]},
            "eocomp1908_djvu.xml": djvu(pages),
        })
        tried = {"phrases": [], "items": []}
        res, complete = t.ia_fulltext(self.target, self.F, t.Archive(pool), tried, lambda: True)
        self.assertTrue(complete)
        self.assertEqual(res["verdict"], "strong")
        self.assertIn("leaves 3-3", res["page_or_item"])
        self.assertEqual(res["route"], "official/ia_fulltext")

    def test_ia_restricted_and_non_government_are_not_strong(self):
        pool = FakePool({
            "page_production": {"response": {"body": {"hits": {"hits": [{"fields": {"identifier": "a"}},
                                                                         {"fields": {"identifier": "b"}}]}}}},
            "/metadata/a": {"metadata": {"title": "Executive orders", "publisher": "Gov't Printing Office",
                                         "collection": ["inlibrary"]}, "files": [{"name": "a_djvu.xml", "size": "9"}]},
            "/metadata/b": {"metadata": {"title": "Oregon history", "publisher": "Binfords & Mort",
                                         "collection": ["americana"]}, "files": [{"name": "b_djvu.xml", "size": "9"}]},
            "b_djvu.xml": djvu(["EXECUTIVE ORDER 1000 " + ORDER]),
        })
        res, _ = t.ia_fulltext(self.target, self.F, t.Archive(pool), {"phrases": [], "items": []}, lambda: True)
        self.assertEqual(res["verdict"], "lead")
        self.assertEqual(res["route"], "lead/ia_fulltext")

    def test_fr_by_date_uses_issue_pages(self):
        target = dict(self.target, date="1937-01-02")

        class Issues:
            def get(self, day):
                if day == dt.date(1937, 1, 5):
                    return {"url": "u", "sha256": "a" * 64,
                            "pages": ["FEDERAL REGISTER 12", "EXECUTIVE ORDER 1000\n" + ORDER + "\n[F. R. Doc. 37-1]"]}
                return {"url": "u", "error": "HTTP 404"}

        tried = []
        res, complete = t.fr_by_date(target, self.F, Issues(), tried)
        self.assertTrue(complete)
        self.assertEqual(res["verdict"], "strong")
        self.assertIn("1937-01-04", tried)
        self.assertNotIn("1937-01-06", tried)  # stops at the first strong find

    def test_fr_by_date_stops_on_transient_error(self):
        class Issues:
            def get(self, day):
                return {"url": "u", "error": "timed out"}

        tried = []
        res, complete = t.fr_by_date(dict(self.target, date="1937-01-02"), self.F, Issues(), tried)
        self.assertFalse(complete)
        self.assertEqual(tried, [])

    def test_fragment_schema(self):
        res = {"verdict": "strong", "route": "official/ia_fulltext", "score": 0.9, "marker": "heading",
               "url": "https://archive.org/details/x/page/n2", "sha256": "f" * 64, "page_or_item": "p",
               "source_kind": "government-printed compilation of executive orders", "text": "x"}
        frag, path = t.fragment(self.target, res)
        self.assertFalse(frag["acceptable_as_original"])
        self.assertFalse(frag["data"]["needs_page_check"])
        self.assertEqual(frag["produced_by"], "tischendorf-originals")
        self.assertTrue(path.startswith("texts/"))
        lead, _ = t.fragment(self.target, dict(res, verdict="lead"))
        self.assertTrue(lead["data"]["needs_page_check"])


if __name__ == "__main__":
    unittest.main()
