"""Niebuhr rows become typed leads only; nothing low-confidence, undated or contradicted gets through."""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import eo_identity as ident  # noqa: E402
import leads  # noqa: E402

HEADER = ["batch", "target_id", "group", "outcome", "date", "title_or_subject", "president", "resolved_to",
          "confidence", "sources", "official_sources", "verbatim_quotes", "first_url", "wpa_check", "wpa_excerpt"]


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})


class LeadTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        write_csv(self.repo / ident.UNIVERSE, ["id", "included_in_bibliography", "date_effective"],
                  [{"id": "EO:1182½", "included_in_bibliography": "1", "date_effective": "1910"},
                   {"id": "EO:3290", "included_in_bibliography": "1", "date_effective": "1920"}])
        rows = [
            {"target_id": "EO:1182½", "group": "in_census_number_only", "outcome": "identified_no_text",
             "date": "1910-03-02", "title_or_subject": "Land withdrawal", "confidence": "high", "wpa_check": "agrees"},
            {"target_id": "EO:36", "group": "number_gap", "outcome": "identified_with_text", "date": "1894-11-02",
             "confidence": "medium", "wpa_check": "silent"},
            {"target_id": "EO:37", "group": "number_gap", "outcome": "identified_with_text", "date": "1894-11-02",
             "confidence": "low"},
            {"target_id": "EO:38", "group": "number_gap", "outcome": "identified_no_text", "date": "1894",
             "confidence": "high"},
            {"target_id": "EO:39", "group": "number_gap", "outcome": "identified_no_text", "date": "1894-11-02",
             "confidence": "high", "wpa_check": "disagrees"},
            {"target_id": "EO:40", "group": "number_gap", "outcome": "not_found", "confidence": "high"},
            {"target_id": "REF:1920-06-05", "group": "dated_unnumbered_reference",
             "outcome": "reference_resolved_to_known_order", "resolved_to": "EO:3290 (probable; check the subject)", "date": "1920-06-05",
             "confidence": "medium"},
            {"target_id": "REF:1921-01-01", "group": "dated_unnumbered_reference", "outcome": "identified_no_text",
             "date": "1921-01-01", "confidence": "high"},
        ]
        write_csv(self.repo / leads.SOURCE, HEADER, rows)

    def test_only_confident_dated_uncontradicted_numbered_rows_become_date_leads(self):
        dates, refs, summary = leads.build(self.repo)
        self.assertEqual([d["instrument_id"] for d in dates], ["EO:36", "EO:1182½"])
        self.assertEqual({d["in_census"] for d in dates if d["instrument_id"] == "EO:1182½"}, {"yes"})
        self.assertTrue(all(d["lead_grade"] == leads.LEAD_GRADE for d in dates))
        self.assertEqual(summary["skipped"], {"low_confidence": 1, "no_full_date": 1, "not_identified:not_found": 1,
                                              "unnumbered_reference_group": 1, "wpa_disagrees": 1})
        self.assertEqual([(r["resolved_to"], r["resolved_in_census"]) for r in refs], [("EO:3290", "yes")])

    def test_load_dates_uses_a_lead_only_where_no_better_source_has_a_date(self):
        dates, refs, summary = leads.build(self.repo)
        leads.write(self.repo / "jobs/gratian-niebuhr-leads/output", dates, refs, summary)
        got = ident.load_dates(str(self.repo), fragments={})
        # The census has only the year 1910; the lead's full date agrees with it and refines it.
        self.assertEqual(got["EO:1182½"]["date"], "1910-03-02")
        self.assertEqual(got["EO:1182½"]["date_source"], "niebuhr_identification_lead")
        # A lead that disagrees with a bare census year does not replace it.
        write_csv(self.repo / leads.SOURCE, HEADER, [
            {"target_id": "EO:3290", "group": "in_census_number_only", "outcome": "identified_no_text",
             "date": "1921-06-05", "confidence": "high"}])
        dates, refs, summary = leads.build(self.repo)
        leads.write(self.repo / "jobs/gratian-niebuhr-leads/output", dates, refs, summary)
        got = ident.load_dates(str(self.repo), fragments={})
        self.assertEqual(got["EO:3290"]["date"], "1920")

    def test_missing_lead_file_changes_nothing(self):
        got = ident.load_dates(str(self.repo), fragments={})
        self.assertEqual(got["EO:1182½"]["date"], "1910")


if __name__ == "__main__":
    unittest.main()
