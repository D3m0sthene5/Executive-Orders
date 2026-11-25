import json
import unittest

import ofr_catalog_search as S

CSV = ("instrument_id,blockers\n"
       "EO:1048,NO_CLAUSE_INVENTORY|NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE\n"
       "EO:6204A,NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE|OPUS_MEDIA_REFETCH_NEEDED\n"
       "EO:7532,NO_CLAUSE_INVENTORY\n"
       "EO:7600,NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE\n")
INDEX = ("<html><body><p>The tables list status from:<br>January 8, 1937 - January 19, 2017 "
         "and begin with orders signed by Franklin D. Roosevelt.</p></body></html>")


def page(nums, total):
    res = [{"executive_order_number": n, "signing_date": "1937-01-08", "title": "T" + n,
            "citation": "2 FR 63", "disposition_notes": "Amended by: EO 8184", "html_url": "https://x/" + n}
           for n in nums]
    return json.dumps({"total_pages": total, "results": res}).encode()


def fake(pages):
    calls = []

    def fetch(url):
        calls.append(url)
        if url == S.INDEX_URL:
            return INDEX.encode(), url
        import urllib.parse as u
        return pages[int(u.parse_qs(u.urlsplit(url).query)["page"][0]) - 1], url
    fetch.calls = calls
    return fetch


class T(unittest.TestCase):
    def test_targets_only_exact_blocker(self):
        self.assertEqual(S.target_ids(CSV), ["EO:1048", "EO:6204A", "EO:7600"])

    def test_coverage_quote(self):
        q = S.parse_index(INDEX)
        self.assertIn("January 8, 1937", q)
        self.assertIsNone(S.parse_index("<p>nothing</p>"))

    def test_found_and_absent(self):
        f = fake([page(["7532", "7600"], 1)])
        recs, info = S.run_search(["EO:1048", "EO:6204A", "EO:7600"], fetch=f, sleep=lambda s: None)
        by = {r["instrument_id"]: r for r in recs}
        self.assertTrue(info["complete"])
        self.assertEqual(by["EO:7600"]["outcome"], "entry_found")
        self.assertIn("Amended by: EO 8184", by["EO:7600"]["entry_text"])
        self.assertEqual(len(by["EO:7600"]["page_sha256"]), 64)
        self.assertEqual(by["EO:1048"]["outcome"], "searched_complete_no_entry")
        self.assertEqual(by["EO:6204A"]["catalog_lowest_number"], 7532)
        self.assertIn("1937", by["EO:1048"]["coverage_quote"])

    def test_suffix_letter_matches_exactly(self):
        recs, _ = S.run_search(["EO:7677A", "EO:7677"], fetch=fake([page(["7677A"], 1)]), sleep=lambda s: None)
        self.assertEqual([r["outcome"] for r in recs], ["entry_found", "searched_complete_no_entry"])

    def test_multi_page_and_state_written_each_page(self):
        seen = []
        f = fake([page(["7532"], 2), page(["7600"], 2)])
        recs, info = S.run_search(["EO:7600"], fetch=f, sleep=lambda s: None, state_cb=seen.append)
        self.assertEqual([s["pages_fetched"] for s in seen], [1, 2])
        self.assertEqual(recs[0]["outcome"], "entry_found")

    def test_deadline_gives_incomplete_never_absent(self):
        recs, info = S.run_search(["EO:1048"], fetch=fake([page(["7532"], 3)]), past_stop=lambda: True,
                                  sleep=lambda s: None)
        self.assertFalse(info["complete"])
        self.assertEqual(recs[0]["outcome"], "search_incomplete")

    def test_missing_coverage_statement_is_incomplete(self):
        f = fake([page(["7532"], 1)])
        orig = S.INDEX_URL
        recs = S.build_records(["EO:1048"], {}, [{"url": "u", "sha256": "h"}], None, {}, True)
        self.assertEqual(recs[0]["outcome"], "search_incomplete")
        self.assertEqual(orig, S.INDEX_URL)

    def test_non_catalog_answer_raises(self):
        with self.assertRaises(ValueError):
            S.parse_api_page(b'{"error": "bot check"}')


if __name__ == "__main__":
    unittest.main()
