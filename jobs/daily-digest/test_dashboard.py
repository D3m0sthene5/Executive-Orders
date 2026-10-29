"""Display contract: stale generations and distinct research tiers stay visible."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import dashboard


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name, relative in dashboard.PATHS.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                self.save(name, {})
        self.csv("universe", [{"id": "EO:1"}, {"id": "EO:2"}, {"id": "EO:3"}])
        self.csv("statuses", [
            {"instrument_id": "EO:1", "provisional_substantive_status": "yes", "human_certified_by_this_release": "no"},
            {"instrument_id": "EO:2", "provisional_substantive_status": "no", "human_certified_by_this_release": "no"},
        ])
        self.save("tracker", {"orders_total": 3, "orders_with_provisional_status": 2,
                              "ready_for_human_review": 1,
                              "ready_by_text_evidence_tier": {"original_supported": 0, "transcription_dependent": 1}})
        self.save("tracker_status", {"finished_utc": "2026-10-28T10:00:00Z", "commit_run": "a" * 40})
        self.save("human_review", {"independently_reviewed_whole_lifecycle_complete": 0})
        self.claim_dir = self.root / "research/readiness/claims"
        self.claim_dir.mkdir(parents=True)

    def save(self, name, value):
        (self.root / dashboard.PATHS[name]).write_text(json.dumps(value), encoding="utf-8")

    def csv(self, name, rows):
        with (self.root / dashboard.PATHS[name]).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def claims(self, name, rows):
        (self.claim_dir / name).write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    def receipts(self):
        inventory = dashboard.claims_inventory(self.root)
        self.save("checker", {"claim_files": [Path(p).name for p in inventory["files"]],
                              "claims_checked": inventory["valid_claim_lines"],
                              "orders_with_claim": inventory["unique_orders"]})
        self.save("checker_receipts", {"claims": inventory["records"], "by_instrument": inventory["effective"]})

    def test_new_claims_leave_published_readiness_unchanged_and_flag_staleness(self):
        self.claims("a.jsonl", [{"instrument_id": "EO:1", "analysis": "first"}])
        self.receipts()
        self.claims("b.jsonl", [{"instrument_id": "EO:2", "analysis": "new"}])
        report = dashboard.build(self.root)
        cover = report["freshness"]["claim_receipts"]
        self.assertEqual(report["freshness"]["state"], "stale")
        self.assertEqual(cover["unmatched_current_claim_lines"], 1)
        self.assertEqual(cover["unmatched_effective_orders"], 1)
        self.assertEqual(cover["current_claim_files_absent_from_checker_summary"], ["b.jsonl"])
        self.assertEqual(report["readiness"]["published_ready_for_human_review"], 1)
        self.assertIn("behind the current records", dashboard.render_markdown(report))

    def test_same_filename_changed_content_is_detected(self):
        self.claims("a.jsonl", [{"instrument_id": "EO:1", "analysis": "old"}])
        self.receipts()
        self.claims("a.jsonl", [{"instrument_id": "EO:1", "analysis": "corrected"}])
        cover = dashboard.build(self.root)["freshness"]["claim_receipts"]
        self.assertEqual(cover["current_claim_files_absent_from_checker_summary"], [])
        self.assertEqual(cover["unmatched_current_claim_lines"], 1)
        self.assertEqual(cover["unmatched_effective_orders"], 1)

    def test_duplicate_and_replacement_lines_are_not_distinct_orders(self):
        self.claims("a.jsonl", [{"instrument_id": "EO:1", "analysis": "first"},
                                 {"instrument_id": "EO:1", "analysis": "first"},
                                 {"instrument_id": "EO:2", "analysis": "other"}])
        self.claims("z.jsonl", [{"instrument_id": "EO:1", "analysis": "replacement"}])
        self.receipts()
        report = dashboard.build(self.root)
        self.assertEqual(report["filed_claims"]["valid_claim_lines"], 4)
        self.assertEqual(report["filed_claims"]["unique_orders"], 2)
        self.assertEqual(report["filed_claims"]["superseded_or_repeated_lines"], 2)
        self.assertEqual(report["freshness"]["claim_receipts"]["exact_current_claim_lines"], 4)
        self.assertEqual(report["freshness"]["claim_receipts"]["state"], "claim_versions_match")
        self.assertEqual(report["provisional_status"]["yes"], 1)
        self.assertEqual(report["provisional_status"]["no"], 1)
        self.assertEqual(report["provisional_status"]["without_provisional_status"], 1)

    def test_ai_approval_and_status_flags_never_create_human_certification(self):
        self.claims("a.jsonl", [{"instrument_id": "EO:1", "human_certified": True,
                                 "review": {"approved": True}, "complete": True}])
        self.receipts()
        report = dashboard.build(self.root)
        self.assertEqual(report["human_review"]["published_whole_lifecycle_certifications"], 0)
        self.assertEqual(report["readiness"]["by_text_evidence_tier"]["transcription_dependent"], 1)
        self.assertIn("never inferred from AI passes", dashboard.render_markdown(report))
        (self.root / dashboard.PATHS["human_review"]).unlink()
        self.assertIsNone(dashboard.build(self.root)["human_review"]["published_whole_lifecycle_certifications"])

    def test_missing_claim_directory_and_receipts_remain_unknown(self):
        self.claim_dir.rmdir()
        (self.root / dashboard.PATHS["checker_receipts"]).unlink()
        report = dashboard.build(self.root)
        self.assertIsNone(report["filed_claims"]["valid_claim_lines"])
        self.assertIsNone(report["freshness"]["claim_receipts"]["unmatched_current_claim_lines"])
        self.assertEqual(report["freshness"]["claim_receipts"]["state"], "unknown")
        self.assertTrue(report["unavailable_inputs"])

    def test_matching_receipt_can_contain_a_failed_check(self):
        self.claims("a.jsonl", [{"instrument_id": "EO:1"}])
        self.receipts()
        path = self.root / dashboard.PATHS["checker_receipts"]
        receipts = json.loads(path.read_text())
        receipts["claims"][0]["all_checks_passed"] = False
        receipts["by_instrument"]["EO:1"]["all_checks_passed"] = False
        self.save("checker_receipts", receipts)
        report = dashboard.build(self.root)
        self.assertEqual(report["freshness"]["claim_receipts"]["exact_current_claim_lines"], 1)
        self.assertEqual(report["readiness"]["published_ready_for_human_review"], 1)
        self.assertIn("matching receipt may record a failure", dashboard.render_markdown(report))


if __name__ == "__main__":
    unittest.main()
