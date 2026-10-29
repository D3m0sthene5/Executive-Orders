import json
import tempfile
import unittest
from pathlib import Path
import handoff as h


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.p = {"instrument_id": "EO:7543", "step": "original_text", "citation": "2 FR 263", "urls": []}
        self.r = {"instrument_ids": "EO:7543", "step": "original_text", "citation": "2 FR 263", "result": "found", "wanted_id": "x", "url": "https://example.invalid/source", "sha256": "a" * 64}
        self.s = {"wanted_id": "x", "url": self.r["url"], "sha256": self.r["sha256"], "text_path": "texts/t.txt"}

    def result(self, queue=None, results=None, sources=None):
        return h.annotate([self.p], [self.p] if queue is None else queue, [self.r] if results is None else results, [self.s] if sources is None else sources)

    def test_found_receipt_is_review_work_not_a_new_request(self):
        d, remaining = self.result()
        self.assertEqual(remaining, [])
        self.assertEqual(d[0]["route_status"], "retrieval_recorded_needs_review")
        self.assertEqual(d[0]["result_records"][0]["sources"][0]["custody"], "record_only_not_rehashed_by_Lewis")

    def test_not_queued_stays_proposal(self):
        d, remaining = self.result(queue=[])
        self.assertEqual(remaining, [self.p])
        self.assertEqual(d[0]["route_status"], "not_queued")

    def test_missing_result_never_means_unattempted(self):
        d, remaining = self.result(results=[])
        self.assertEqual(d[0]["route_status"], "queued_result_not_published")
        self.assertEqual(remaining, [])

    def test_budget_deferment_preserved(self):
        d, _ = self.result(results=[dict(self.r, result="not_attempted_budget", why="limit")])
        self.assertEqual(d[0]["route_status"], "queued_not_attempted_budget")
        self.assertEqual(d[0]["result_records"][0]["why"], "limit")

    def test_other_target_never_matches(self):
        d, _ = self.result(results=[dict(self.r, instrument_ids="EO:7544")])
        self.assertEqual(d[0]["route_status"], "queued_result_not_published")

    def test_qualified_request_not_conflated(self):
        d, remaining = self.result(queue=[dict(self.p, edition_year=1953)])
        self.assertEqual(remaining, [self.p])

    def test_found_without_current_receipt_needs_revalidation(self):
        d, _ = self.result(sources=[])
        self.assertEqual(d[0]["route_status"], "found_record_needs_revalidation")

    def test_contradictory_results_stay_explicit(self):
        d, _ = self.result(results=[self.r, dict(self.r, result="needs_revalidation")])
        self.assertEqual(d[0]["route_status"], "published_results_conflict")

    def test_shared_result_matches_each_exact_target(self):
        d, _ = self.result(results=[dict(self.r, instrument_ids="EO:7543 | EO:7544")])
        self.assertEqual(d[0]["route_status"], "retrieval_recorded_needs_review")

    def test_native_refresh_is_idempotent_and_preserves_original_proposals(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder); out = repo / "out"; out.mkdir()
            for path, text in [(h.QUEUE, json.dumps(self.p)+"\n"), (h.RESULTS, "instrument_ids,step,citation,result\n"), (h.SOURCES, "")]:
                dest = repo / path; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(text)
            original = json.dumps(self.p)+"\n"
            (out / "PROPOSED_FETCH_REQUESTS.jsonl").write_text(original)
            (out / "ROUTES.csv").write_text("instrument_id,best_route,route_status,next_action,action_owner\nEO:7543,federal_register,fetch_request_proposed,enqueue,machine_job\n")
            (out / "SUMMARY.json").write_text(json.dumps({"proposed_fetch_requests": {"count": 1, "contract_valid": 1}}))
            callback = lambda path, summary, routes: path.write_text(json.dumps(summary))
            first = h.refresh(repo, out, callback); second = h.refresh(repo, out, callback)
            self.assertEqual(first, second)
            self.assertEqual((out / "ALL_FETCH_PROPOSALS.jsonl").read_text(), original)
            self.assertEqual((out / "PROPOSED_FETCH_REQUESTS.jsonl").read_text(), "")
            self.assertIn("handoff_records", (out / "ROUTES.csv").read_text())


if __name__ == "__main__":
    unittest.main()
