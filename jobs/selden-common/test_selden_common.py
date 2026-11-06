import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import selden_common as S  # noqa: E402

REVOKE = ("Sec. 4. Revocation. Executive Order 13879 of July 10, 2019 (Advancing American Kidney Health), is hereby "
          "revoked. Sec. 5. General Provisions. (a) Nothing in this order shall be construed to impair the authority "
          "granted by law to an executive department.")
AMENDED_BY = ("By the authority vested in me, Executive Order 12345, as amended by Executive Order 12400, is further "
              "amended by striking section 3.")
PLO = ("Public Land Order 4620. Revocation of Executive Order No. 5214 of October 30, 1929. By virtue of the authority "
       "vested in the President, it is ordered as follows: Executive Order No. 5214 of October 30, 1929, which "
       "withdrew public lands for classification, is hereby revoked.")
PURSUANT = ("This rule implements section 8 of E.O. 13879, which directed the Secretary to propose a regulation. "
            "The Department also considered Executive Order 12866.")


class Locate(unittest.TestCase):
    def test_revocation_found_with_date(self):
        hits = S.find_citations(REVOKE, "EO:13879", "2019-07-10")
        b = S.best_hit(hits)
        self.assertEqual(b["mechanism"], "revocation")
        self.assertTrue(S.acting_on_target(b))
        self.assertTrue(b["date_match"])
        self.assertEqual(REVOKE[b["start"]:b["end"]], b["quote"])
        self.assertIn("hereby revoked", b["quote"])

    def test_near_numbers_never_match(self):
        for t in ("EO:1387", "EO:138790", "EO:13880", "EO:3879"):
            self.assertEqual(S.find_citations(REVOKE, t), [], t)

    def test_longer_printed_number_is_not_target(self):
        self.assertEqual(S.find_citations("Executive Order 138790 was cited.", "EO:13879"), [])
        self.assertTrue(S.find_citations("Executive Orders 13879 and 138790 were cited.", "EO:13879"))

    def test_v2_lists_and_ocr(self):
        self.assertTrue(S.find_citations("Amendment of E xecutive O rder No. 8572 of October 21, 1940", "EO:8572"))
        lst = "Executive Orders Numbered 8744 9230 9712 9830 are revoked."
        self.assertTrue(S.find_citations(lst, "EO:9712"))
        self.assertEqual(S.find_citations(lst, "EO:9713"), [])
        cut = "Executive Order No. 12360, establishing" + " x" * 500
        self.assertEqual(S.find_citations(cut, "EO:1236"), [])
        table = "No. Subject\n10919 Creating an emergency board\n1056 THE PRESIDENT\n"
        self.assertTrue(S.find_citations(table, "EO:10919"))
        self.assertEqual(S.find_citations(table, "EO:1056"), [])

    def test_v2_false_forms_rejected(self):
        self.assertEqual(S.find_citations("Executive Order 1 2552, see the Weekly Compilation", "EO:2552"), [])
        self.assertEqual(S.find_citations("Executive Order No. 6980-C approved March 1, 1935", "EO:6980"), [])
        self.assertEqual(S.find_citations("Executive Order 9395B, supra.", "EO:9395"), [])
        self.assertEqual(S.find_citations("Executive Order 13488 of January 16, 2009 Granting", "EO:2009"), [])
        self.assertTrue(S.find_citations("Executive Orders Nos. 4109, 4262, and 4430 of December 8, 1924", "EO:4430"))

    def test_closing_tag_and_year_after_date(self):
        b = S.best_hit(S.find_citations("is hereby revoked.\n[EXECUTIVE ORDER 9346]\nThe White House", "EO:9346"))
        self.assertTrue(b["heading_or_closing_tag"])
        self.assertFalse(S.acting_on_target(b))
        self.assertEqual(S.find_citations("Executive Order 13593 of December 13, 2011\n2011 Amendments", "EO:2011"), [])

    def test_amender_named_is_not_target_acted_on(self):
        hits = S.find_citations(AMENDED_BY, "EO:12400")
        self.assertTrue(hits)
        self.assertFalse(S.acting_on_target(S.best_hit(hits)))
        b = S.best_hit(S.find_citations(AMENDED_BY, "EO:12345"))
        self.assertEqual(b["mechanism_class"], "modifying")

    def test_plo_text_cites_order(self):
        b = S.best_hit(S.find_citations(PLO, "EO:5214", "1929-10-30"))
        self.assertEqual(b["mechanism"], "revocation")
        self.assertTrue(b["date_match"])
        self.assertTrue(S.find_citations(PLO, "PLO:4620"))

    def test_mention_under(self):
        hits = S.find_citations(PURSUANT, "EO:13879")
        b = S.best_hit(hits)
        self.assertEqual(b["mechanism_class"], "mention")
        self.assertTrue(b["under_or_pursuant"])

    def test_fragment_and_source_shape(self):
        b = S.best_hit(S.find_citations(REVOKE, "EO:13879", "2019-07-10"))
        src = S.source_record("fr:doc:2021-01", "EO:14000", ["EO:13879"], "https://x", "a" * 64, 10, "r", "p",
                              "texts/x.txt", "g", "n")
        self.assertEqual(src["instrument_ids"], ["EO:14000", "EO:13879"])
        one = S.source_record("fr:doc:2", "FRDOC:2", [], "https://x", "a" * 64, 1, "r", "p", "t", "g", "n")
        self.assertEqual(len(one["instrument_ids"]), 2)
        f = S.fragment("EO:13879", "EO:14000", "EO 14000", b, src, "t", "2021-01-20", "signing", "e")
        self.assertEqual(f["kind"], "later_event_candidates")
        self.assertEqual(f["data"][0]["mechanism"], "revocation")
        self.assertEqual(f["data"][0]["quote_span"], f"{b['start']}-{b['end']}")

    def test_controls(self):
        texts = {"a": REVOKE, "p": PLO}
        res = S.run_controls([("EO:13879", "EO:14000", "ending", "a"), ("EO:5214", "PLO:4620", "ending", "p")], texts)
        self.assertEqual(res["positives_located"], 2)
        self.assertEqual(res["false_locations"], 0)
        self.assertTrue(res["passed"])
        self.assertGreaterEqual(res["negatives"], 4)


if __name__ == "__main__":
    unittest.main()
