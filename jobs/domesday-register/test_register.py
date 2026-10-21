"""Offline tests for the Domesday register with a synthetic repository."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import register  # noqa: E402


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


class Register(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="domesday-")
        self.out = os.path.join(self.root, "_out")
        r = self.root
        write_csv(os.path.join(r, ident.UNIVERSE), [
            {"id": "EO:5852", "bibliographic_class": "validated_numbered", "included_in_bibliography": "1", "date_effective": "1932", "year_group": "1907–1936"},
            {"id": "EO:7543", "bibliographic_class": "validated_numbered", "included_in_bibliography": "1", "date_effective": "1937", "year_group": "1937–1989"},
            {"id": "EO:9999", "bibliographic_class": "validated_numbered", "included_in_bibliography": "0", "date_effective": "1948", "year_group": "1937–1989"}])
        write_csv(os.path.join(r, ident.READINESS), [
            {"instrument_id": "EO:5852", "provisional_status": "", "ready_for_human_review": "no", "blockers": "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND", "step_original_text": "open"},
            {"instrument_id": "EO:7543", "provisional_status": "no", "ready_for_human_review": "no", "blockers": "", "step_original_text": "done"}])
        os.makedirs(os.path.join(r, "jobs/app-executive-orders/output"))
        with open(os.path.join(r, "jobs/app-executive-orders/output/FRAGMENTS.jsonl"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"instrument_id": "EO:5852", "produced_by": "app-executive-orders", "acceptable_as_original": False,
                                 "sources": [{}], "data": {"app_date": "1932-06-01", "title": "Executive Order 5852—Test"}}) + "\n")
        write_csv(os.path.join(r, ident.OFR_CATALOG), [{"id": "EO:7543", "signing_date": "1937-01-29", "citation": "2 FR 263", "title": "Catalog title",
                                                       "president": "Franklin D. Roosevelt", "html_url": "", "disposition_notes": ""}])
        write_csv(os.path.join(r, register.LEWIS, "ROUTES.csv"), [{"instrument_id": "EO:5852", "best_route": "gpo_bound_volumes", "route_status": "in_volume_range_not_found", "next_action": "check"}])
        write_csv(os.path.join(r, register.CLARK, "NUMBER_GAPS.csv"), [
            {"instrument_id": "EO:5853", "number": "5853", "window_from": "EO:5852 1932-06-01", "window_to": "EO:5857 1932-06-16", "strength": "strong",
             "known_to_index": "app_index", "identity_evidence": "app_index:1932-06-03:Executive Order 5853—Waiver", "cited_plausibly_by": "", "citations_total": "0", "where_to_look": ""}])
        write_csv(os.path.join(r, register.CLARK, "WEB_LISTED_ORDERS.csv"), [
            {"instrument_id": "EO:5899", "in_census": "no", "pages_naming_it": "1", "dates_seen": "1932-07-20", "example_page": "https://lists.test/h", "context": "Executive Order 5899 July 20, 1932"}])
        with open(os.path.join(r, register.LEWIS, "WEB_STATE.json"), "w", encoding="utf-8") as fh:
            json.dump({"targets": {"EO:5852": {"best_score": 75, "best_url": "https://docs.test/5852"}}}, fh)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_register_rows_consolidate_every_source(self):
        s = register.run(self.root, self.out)
        rows = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(self.out, "REGISTER.csv"))}
        self.assertEqual(sorted(rows), ["EO:5852", "EO:7543"], "only orders counted in the census")
        a = rows["EO:5852"]
        self.assertEqual(a["best_held"], "transcription_only")
        self.assertEqual(a["transcription_sources"], "app-executive-orders")
        self.assertEqual(a["date"], "1932-06-01")
        self.assertEqual(a["lewis_route"], "gpo_bound_volumes")
        self.assertEqual(a["lewis_web_best_score"], "75")
        self.assertEqual(a["proquest_link_supplied"], "no")
        b = rows["EO:7543"]
        self.assertEqual(b["best_held"], "official_original_counted")
        self.assertEqual(b["president"], "Franklin D. Roosevelt")
        self.assertEqual(s["orders"], 2)

    def test_candidates_are_kept_out_of_the_register(self):
        s = register.run(self.root, self.out)
        c = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(self.out, "CANDIDATES_NOT_IN_REGISTER.csv"))}
        self.assertEqual(sorted(c), ["EO:5853", "EO:5899"])
        self.assertEqual(c["EO:5853"]["strength"], "strong")
        self.assertIn("number_gap", c["EO:5853"]["named_by"])
        self.assertEqual(c["EO:5899"]["dates_seen"], "1932-07-20")
        self.assertEqual(s["candidates_not_in_register"]["total"], 2)
        rows = {r["instrument_id"] for r in ident.read_csv(os.path.join(self.out, "REGISTER.csv"))}
        self.assertNotIn("EO:5853", rows)

    def test_missing_lewis_and_clark_outputs_are_fine(self):
        shutil.rmtree(os.path.join(self.root, "jobs/lewis-originals"))
        shutil.rmtree(os.path.join(self.root, "jobs/clark-discovery"))
        s = register.run(self.root, self.out)
        self.assertEqual(s["orders"], 2)
        self.assertEqual(s["candidates_not_in_register"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
