"""Regression tests — Stage 21 OFR bulk index is evidence, not status."""
import gzip
import json
import unittest
from pathlib import Path

from ofr_bulk_excavator import (
    load_catalog, normalize_eo_number, make_model, outputs, sha256, CUTOFF,
    official_export_url
)


def example_docs():
    return [
        {"executive_order_number": "10005", "signing_date": "1948-10-05",
         "document_number": "1948-01", "title": "Original order",
         "disposition_notes": "Revoked by later order (editorial note only)",
         "html_url": "https://www.federalregister.gov/example",
         "pdf_url": "https://www.govinfo.gov/example.pdf"},
        {"executive_order_number": "10033", "signing_date": "1949-02-08",
         "document_number": "1949-02", "title": "Another order",
         "disposition_notes": None, "html_url": "https://www.federalregister.gov/example2"},
        {"executive_order_number": "14499", "signing_date": "2026-11-01",
         "document_number": "2026-99", "title": "Outside cutoff"},
    ]


def fixture():
    # Frozen-cohort invariants: representative accepted legacy records plus
    # synthetic additional identities. Distinctiveness matters; no legal
    # certification is implied.
    queue = [
        {"instrument_id": "EO:10005", "issuance_date": "1948-10-05",
         "legacy_status": "no"},
        {"instrument_id": "EO:10033", "issuance_date": "1949-02-07",
         "legacy_status": "yes"},
    ] + [{"instrument_id": "EO:" + str(50000 + i),
          "issuance_date": "", "legacy_status": "no"} for i in range(3357)]
    conversion = [{"instrument_id": row["instrument_id"],
                   "provisional_status": row["legacy_status"]} for row in queue]
    families = [
        {"reference_type": "EO", "reference_as_mentioned": "10005",
         "case_ids": "EO:10005 | EO:10033", "affected_candidate_count": "2"},
    ] + [{"reference_type": "EO",
          "reference_as_mentioned": str(11000 + i),
          "case_ids": "EO:10005 | EO:10033", "affected_candidate_count": "2"}
         for i in range(72)] + [
        {"reference_type": "USC", "reference_as_mentioned": "31 U.S.C. 1552"}
         for _ in range(25)]
    return queue, conversion, families


class BulkExtractorTests(unittest.TestCase):
    def test_official_source_is_broad_including_pre1994(self):
        url = official_export_url()
        self.assertIn("include_pre_1994_docs=true", url)
        self.assertIn("disposition_notes", url)
        self.assertIn("per_page=10000", url)

    def test_number_aliases_and_invalid(self):
        self.assertEqual(normalize_eo_number("7784-A"), "EO:7784A")
        self.assertEqual(normalize_eo_number("00010033"), "EO:10033")
        self.assertIsNone(normalize_eo_number("exec 10033"))

    def test_bulk_rejects_truncated_or_small(self):
        raw = json.dumps({"count": 4, "results": example_docs()}).encode()
        with self.assertRaises(ValueError):
            load_catalog(raw, minimum_count=1)
        with self.assertRaises(ValueError):
            load_catalog(json.dumps({"results": []}).encode())

    def test_cutoff_duplicates_date_conflicts_and_savings(self):
        raw = json.dumps({"count": 3, "results": example_docs()}).encode()
        records, count = load_catalog(raw, minimum_count=1)
        self.assertEqual(count["post_cutoff_rows_excluded"], 1)
        self.assertEqual(len(records["EO:10005"]), 1)
        q, c, f = fixture()
        model = make_model(records, q, c, f,
                           {"raw": raw, "inputs": {"fixture": b"abc"}}, count)
        one = next(r for r in model["crosswalk"]
                   if r["instrument_id"] == "EO:10005")
        second = next(r for r in model["crosswalk"]
                      if r["instrument_id"] == "EO:10033")
        self.assertEqual(one["catalog_match_state"], "unique_catalog_record")
        self.assertEqual(second["catalog_match_state"],
                         "catalog_signing_date_conflict")
        self.assertEqual(one["source_effect_and_effective_date_proven"], "no")
        self.assertEqual(model["metrics"]["certified_whole_lifecycle_dossiers_added"], 0)
        self.assertIn(b"editorial", outputs(model)["OFR_EDITORIAL_DISPOSITION_LEADS.csv"])
        dup = example_docs()[:2] + [dict(example_docs()[0])]
        records, _ = load_catalog(json.dumps({"count": 3, "results": dup}).encode(),
                                  minimum_count=1)
        model = make_model(records, q, c, f,
                           {"raw": raw, "inputs": {"fixture": b"abc"}}, count)
        row = next(r for r in model["crosswalk"]
                   if r["instrument_id"] == "EO:10005")
        self.assertEqual(row["catalog_match_state"],
                         "ambiguous_duplicate_catalog_records")
        self.assertFalse(row["official_pdf_candidate_url"])


if __name__ == "__main__":
    unittest.main()
