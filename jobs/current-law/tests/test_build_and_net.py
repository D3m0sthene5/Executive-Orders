import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
import urllib.robotparser

import build
import eo_refs
import net
import usc_scan

FIX = pathlib.Path(__file__).parent / "fixtures"
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent.parent / "research" / "stage19" / "code"))


def make_book():
    u = eo_refs.Universe(["EO:10450", "EO:10491", "EO:13526", "EO:12333", "EO:11230", "EO:11609", "EO:9835",
                          "EO:14000", "EO:14100", "EO:11275", "EO:11294"],
                         {"EO:10450": "no", "EO:13526": "yes", "EO:11230": "no", "EO:9835": "no"})
    u.origins = {}
    book = build.Book(u)
    book.ecfr_amddate = {}
    book.usc_currency = "test currency"
    meta = {"url": "https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_usc99@119-121.zip",
            "sha256": "a" * 64, "bytes": 10, "content_type": "application/zip", "retrieved_utc": "2026-10-17T00:00:00Z",
            "route": "usc_release_point_xml_zip", "cache_path": "usc/x.zip"}
    book.add_source("usc:test", meta, page_or_item="zip")
    with open(FIX / "usc_sample.xml", "rb") as f:
        for kind, rec in usc_scan.scan_uslm(f, "usc99.xml"):
            poi = rec.get("citation", "") + "; usc99.xml"
            if kind == "mention":
                book.add_mention(rec, "usc", "usc_release_point_xml_zip", "U.S. Code release point 119-121", "usc:test", poi, "2026-10-09")
            elif kind == "event":
                book.add_event(rec, "usc", "U.S. Code release point 119-121", "usc:test", poi)
    book.dedupe()
    return book


class Build(unittest.TestCase):
    def setUp(self):
        self.book = make_book()
        self.frags = self.book.fragments()

    def test_mentions_mapped(self):
        m = next(m for m in self.book.mentions if m["role"] == "printed_eo_text")
        self.assertEqual(m["instrument_id"], "EO:10450")
        self.assertEqual(m["provisional_status"], "no")
        self.assertEqual(m["is_predicate_lead"], "yes")
        self.assertEqual(len({m["mention_id"] for m in self.book.mentions}), len(self.book.mentions))

    def test_fragment_shapes(self):
        kinds = {(f["instrument_id"], f["kind"]) for f in self.frags}
        self.assertIn(("EO:13526", "current_predicate_candidates"), kinds)
        self.assertIn(("EO:11230", "later_event_candidates"), kinds)
        for f in self.frags:
            self.assertEqual(f["produced_by"], "current-law")
            self.assertTrue(f["sources"])
            for ref in f["sources"]:
                self.assertEqual(set(ref), {"url", "sha256", "page_or_item"})
                self.assertTrue(ref["url"].startswith("https://"))
            for d in f["data"]:
                self.assertIn("source", d)
        pred = next(f for f in self.frags if f["instrument_id"] == "EO:13526")
        d = pred["data"][0]
        self.assertTrue({"legal_basis_candidate", "where", "snippet", "checked_through"} <= set(d))
        self.assertTrue(d["where"].startswith("USC 99 U.S.C. 101"))

    def test_sources_pass_claim_gate_source_check(self):
        try:
            import claim_gate
        except ImportError:
            self.skipTest("research/stage19/code not checked out")
        for f in self.frags:
            for ref in f["sources"]:
                self.assertTrue(claim_gate.source_ok(ref))

    def test_events_after_cutoff_excluded(self):
        late = [e for e in self.book.events if e["subject_instrument_id"] == "EO:14100"]
        self.assertEqual(late[0]["in_scope"], "no_after_cutoff")
        self.assertFalse(any(f["instrument_id"] == "EO:14100" and f["kind"] == "later_event_candidates" for f in self.frags))
        ended = next(f for f in self.frags if f["instrument_id"] == "EO:11230" and f["kind"] == "later_event_candidates")
        sup = [d for d in ended["data"] if d["event_type_candidate"] == "supersession"][0]
        self.assertEqual(sup["date_candidate"], "1971-07-22")
        self.assertEqual(sup["date_basis_code"], "printed_next_to_acting_instrument")
        # nothing in a fragment uses the bare claim field names
        for f in self.frags:
            for d in f["data"]:
                self.assertFalse({"effective_date", "actor", "mechanism", "legal_basis", "date"} & set(d))
        self.assertEqual(sup["acting_instrument_id"], "EO:11609")

    def test_conflicts(self):
        rows, conflicts = build.order_table(self.book)
        ids = {c["instrument_id"]: c for c in conflicts}
        self.assertIn("EO:10450", ids)  # provisional NO but printed as current text
        self.assertEqual(ids["EO:10450"]["signal"], "3_printed_text_but_ending_statement_also_found")
        self.assertNotIn("EO:13526", ids)  # YES orders are never conflicts
        self.assertNotIn("EO:11230", ids)  # only an ended status note: not a predicate lead


class Fetcher(unittest.TestCase):
    def test_cache_reuse_offline(self):
        with tempfile.TemporaryDirectory() as d:
            f = net.Fetcher(d, offline=True)
            target = pathlib.Path(d) / "x" / "a.json"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"{}")
            meta = {"url": "https://example.gov/a.json", "sha256": hashlib.sha256(b"{}").hexdigest(), "bytes": 2,
                    "content_type": "application/json", "retrieved_utc": "2026-10-17T00:00:00Z", "route": "t",
                    "cache_path": "x/a.json"}
            (pathlib.Path(d) / "x" / "a.json.meta.json").write_text(json.dumps(meta), encoding="utf-8")
            got = f.get("https://example.gov/a.json", "x/a.json", route="t")
            self.assertTrue(got["from_cache"])
            self.assertEqual(got["retrieved_utc"], "2026-10-17T00:00:00Z")
            with self.assertRaises(net.FetchFailed):
                f.get("https://example.gov/b.json", "x/b.json", route="t")

    def test_robots_respected(self):
        with tempfile.TemporaryDirectory() as d:
            f = net.Fetcher(d)
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(["User-agent: *", "Disallow: /api/versioner/v1/full/"])
            f._robots["www.ecfr.gov"] = rp
            self.assertFalse(f.allowed("https://www.ecfr.gov/api/versioner/v1/full/2026-10-14/title-5.xml"))
            self.assertTrue(f.allowed("https://www.ecfr.gov/api/search/v1/results?query=x"))
            with self.assertRaises(net.RobotsDisallowed):
                f.get("https://www.ecfr.gov/api/versioner/v1/full/2026-10-14/title-5.xml", "full.xml", route="t")
            self.assertEqual(f.requests_made, 0)


if __name__ == "__main__":
    unittest.main()
