"""Eumenes: joins the store manifest to source-ladder's records and refuses locators the store does not hold."""
import unittest

import job


MANIFEST = [{"sha256": "a" * 64, "bytes": 10, "ext": ".pdf", "backend": "release",
             "locator": "https://github.com/x/y/releases/download/pergamon-aa/" + "a" * 64 + ".pdf",
             "stored_utc": "2026-11-10T11:00:00Z"},
            {"sha256": "b" * 64, "bytes": 20, "ext": ".pdf", "backend": "release", "locator": "L2"}]
LADDER = [{"sha256": "a" * 64, "url": "https://nmb.gov/r1.pdf", "instrument_ids": ["EO:10010"], "page_or_item": "p1",
           "citation": "report"},
          {"sha256": "a" * 64, "url": "https://nmb.gov/r1.pdf", "instrument_ids": ["EO:10015", "EO:10010"]},
          {"sha256": "c" * 64, "url": "https://example.org/other.pdf", "instrument_ids": ["EO:1"]}]


class EumenesTests(unittest.TestCase):
    def test_joins_manifest_to_source_ladder_and_carries_the_locator(self):
        records, summary = job.build(MANIFEST, LADDER, lambda m: True)
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r["instrument_ids"], ["EO:10010", "EO:10015"])
        self.assertEqual(r["pergamon"]["sha256"], r["sha256"])
        self.assertTrue(r["pergamon"]["locator"].endswith(".pdf"))
        self.assertEqual(summary["no_source_ladder_record"], ["b" * 64])
        self.assertEqual(summary["orders_covered"], 2)

    def test_a_record_the_store_does_not_hold_is_never_published(self):
        records, summary = job.build(MANIFEST, LADDER, lambda m: m["sha256"] != "a" * 64)
        self.assertEqual(records, [])
        self.assertEqual(summary["missing_in_store"], ["a" * 64])

    def test_only_nmb_gov_ladder_records_are_joined(self):
        manifest = [dict(MANIFEST[0], sha256="c" * 64)]
        records, _ = job.build(manifest, LADDER, lambda m: True)
        self.assertEqual(records, [])


if __name__ == "__main__":
    unittest.main()
