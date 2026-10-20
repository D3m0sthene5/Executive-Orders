"""Regressions for false checker acceptance and the exact-source network bound."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import job


def passing():
    summary = {"claims_checked": 6, "claims_parse_errors": 0, "claims_checker_errors": 0,
               "claims_all_checks_passed": 6, "claims_mechanical_pass": 6, "claims_gate_passed": 6}
    claims = [{"instrument_id": iid, "mechanical_result": "pass", "gate_passed": True,
               "all_checks_passed": True} for iid in job.CHECKED]
    return summary, claims


class CheckerAcceptance(unittest.TestCase):
    def test_all_six_required(self):
        self.assertEqual(job.checker_errors(*passing()), [])

    def test_zero_internal_errors_does_not_accept_six_mechanical_failures(self):
        summary, claims = passing()
        summary.update(claims_all_checks_passed=0, claims_mechanical_pass=0)
        for claim in claims:
            claim.update(mechanical_result="fail", all_checks_passed=False)
        errors = job.checker_errors(summary, claims)
        for iid in job.CHECKED:
            self.assertTrue(any(error.startswith(iid + ":") for error in errors), iid)

    def test_positive_control_cannot_hide_unverified_status(self):
        summary, claims = passing()
        claims[-1].update(mechanical_result="pass_with_unverified", all_checks_passed=False)
        self.assertTrue(any(error.startswith(job.POSITIVE + ":") for error in job.checker_errors(summary, claims)))

    def test_duplicate_or_missing_case_rejected_despite_passing_counts(self):
        summary, claims = passing()
        claims[-1] = copy.deepcopy(claims[0])
        self.assertTrue(job.checker_errors(summary, claims))


class BoundedVerification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.out = Path(self.tmp.name) / "repo", Path(self.tmp.name) / "out"
        self.repo.mkdir()
        self.out.mkdir()
        self.checker = job.load("fixture_actual_checker", job.HERE.parent / "claim-checker/checker.py")
        self.data = {f"https://www.govinfo.gov/content/pkg/fixture-{i}.pdf": f"fixture {i}".encode() for i in range(10)}
        self.sources = [{"sha256": job.sha(raw), "url": url} for url, raw in self.data.items()]
        self.manifest = {"sources": self.sources}
        self.claims = [{"sources": self.sources}]

    def response(self, request, timeout):
        self.assertEqual(timeout, 120)
        url = request.full_url
        raw = self.data[url]
        if isinstance(raw, Exception):
            raise raw
        owner = self

        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def geturl(self):
                return url
            def read(self, limit):
                owner.assertLessEqual(limit, 5_000_001)
                return raw[:limit]
        return Response()

    def test_existing_verifier_records_cache_mismatch_and_transport_failure(self):
        cached = self.sources[0]
        path = self.repo / ".job-cache/claim-checker/verified" / cached["sha256"][:2] / (cached["sha256"] + ".bin")
        path.parent.mkdir(parents=True)
        path.write_bytes(self.data[cached["url"]])
        self.data[self.sources[1]["url"]] = b"wrong bytes"
        self.data[self.sources[2]["url"]] = OSError("fixture transport failure")
        with mock.patch("urllib.request.urlopen", side_effect=self.response) as network, mock.patch("time.sleep"):
            result = job.verify_sources(self.checker, self.repo, self.out, self.claims, self.manifest, True)
        self.assertEqual(network.call_count, 9)
        self.assertEqual(result["verified_count"], 8)
        self.assertEqual(result["cache_reused_count"], 1)
        self.assertEqual(result["sources"][1]["result"], "hash_mismatch")
        self.assertEqual(result["sources"][2]["error"]["type"], "OSError")
        self.assertEqual(self.checker._VERIFY["left"], 0)
        self.assertEqual(len(list((self.out / "checker-cache").rglob("*.bin"))), 8)

    def test_offline_phase_never_fetches_missing_bytes(self):
        with mock.patch("urllib.request.urlopen") as network:
            result = job.verify_sources(self.checker, self.repo, self.out, self.claims, self.manifest, False)
        network.assert_not_called()
        self.assertEqual(result["download_attempts"], 0)
        self.assertEqual(result["verified_count"], 0)

    def test_unlisted_source_rejected_before_network(self):
        claims = copy.deepcopy(self.claims)
        claims[0]["sources"][0]["url"] += "?changed=1"
        with mock.patch("urllib.request.urlopen") as network, self.assertRaises(ValueError):
            job.verify_sources(self.checker, self.repo, self.out, claims, self.manifest, True)
        network.assert_not_called()

    def test_oversize_response_fails_before_hash_acceptance(self):
        self.data[self.sources[0]["url"]] = b"x" * 5_000_001
        with mock.patch("urllib.request.urlopen", side_effect=self.response), mock.patch("time.sleep"):
            result = job.verify_sources(self.checker, self.repo, self.out, self.claims, self.manifest, True)
        record = result["sources"][0]
        self.assertFalse(record["verified"])
        self.assertEqual(record["bytes_returned_by_read"], 5_000_001)
        self.assertEqual(record["error"]["type"], "ValueError")
        self.assertEqual(result["declared_bounds"]["maximum_response_bytes_read"], 50_000_010)


if __name__ == "__main__":
    unittest.main()
