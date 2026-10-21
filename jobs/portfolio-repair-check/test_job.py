"""Regressions for false checker acceptance and the exact-source network bound."""
import copy
import json
import os
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


class FixtureIsolation(unittest.TestCase):
    def test_in_repo_output_and_inherited_tmpdir_do_not_put_fixtures_in_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "checkout"
            out = repo / "jobs/portfolio-repair-check/output"
            inherited = out / "tmp"
            inherited.mkdir(parents=True)
            observed = []

            class Probe(unittest.TestCase):
                def runTest(self):
                    with tempfile.TemporaryDirectory() as fixture:
                        path = Path(fixture).resolve()
                        observed.append(path.parent)
                        self.assertFalse(path.is_relative_to(repo.resolve()), "synthetic fixture entered checkout")
                        self.assertEqual(Path(os.environ["TMPDIR"]).resolve(), path.parent)

            suite = unittest.TestSuite([Probe()])
            with mock.patch.dict(os.environ, {"OUTPUT_DIR": str(out), "TMPDIR": str(inherited),
                                              "TEMP": str(inherited), "TMP": str(inherited)}), \
                    mock.patch.object(tempfile, "tempdir", str(inherited)), \
                    mock.patch.object(unittest.defaultTestLoader, "loadTestsFromNames", return_value=suite):
                code = job.test_worker(repo, out, "hamilton-token-audit")
                self.assertEqual(os.environ["TMPDIR"], str(inherited))
                self.assertEqual(tempfile.tempdir, str(inherited))
            self.assertEqual(code, 0)
            self.assertTrue(observed)
            self.assertFalse(observed[0].exists(), "external fixture directory was not cleaned up")
            receipt = json.loads((out / "tests/hamilton-token-audit.json").read_text())
            self.assertTrue(receipt["passed"])


class HistoricalGateEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "checkout"
        self.current = self.repo / job.HISTORICAL_LEDGER
        self.current.parent.mkdir(parents=True)
        self.current.write_text("new merged ledger; preserve this generation\n")
        self.snapshot = self.repo / job.HISTORICAL_LEDGER_COPY
        self.snapshot.parent.mkdir(parents=True)
        self.historical = (job.HERE / "historical-gate/forecasts.jsonl").read_bytes()
        self.snapshot.write_bytes(self.historical)
        self.observation = {"evidence": [{"path": job.HISTORICAL_LEDGER,
                                         "sha256": job.HISTORICAL_LEDGER_SHA256}]}
        self.destination = Path(self.tmp.name) / "replay"

    def test_merged_ledger_replays_exact_history_without_rewriting_current(self):
        inputs = job.Inputs(self.repo)
        before = self.current.read_bytes()
        records = job.historical_gate_evidence(inputs, self.observation, self.destination)
        self.assertEqual((self.destination / job.HISTORICAL_LEDGER).read_bytes(), self.historical)
        self.assertEqual(self.current.read_bytes(), before)
        self.assertFalse(records[0]["current_matches_historical"])
        self.assertEqual(records[0]["snapshot_commit"], job.HISTORICAL_LEDGER_COMMIT)
        self.assertEqual(set(inputs.pins), {job.HISTORICAL_LEDGER, job.HISTORICAL_LEDGER_COPY})
        inputs.unchanged()

    def test_tampered_snapshot_and_unregistered_changed_evidence_fail_closed(self):
        self.snapshot.write_text("tampered")
        with self.assertRaisesRegex(ValueError, "historical snapshot hash mismatch"):
            job.historical_gate_evidence(job.Inputs(self.repo), self.observation, self.destination)
        other = self.repo / "other.json"
        other.write_text("changed")
        with self.assertRaisesRegex(ValueError, "without a pinned snapshot"):
            job.historical_gate_evidence(job.Inputs(self.repo),
                {"evidence": [{"path": "other.json", "sha256": "0" * 64}]}, self.destination)


class TrackerFreshness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.source = self.repo / "held-input.txt"
        self.source.write_text("held evidence at the successful run")
        self.scope = {"roots": ["held-input.txt"], "patterns": [],
                      "exclude": "jobs/readiness-tracker/output"}
        self.freshness = job.load("fixture_runner_freshness",
            job.HERE.parents[1] / ".github/scripts/result_freshness.py")
        self.status = {"job": "readiness-tracker", "result": "succeeded", "exit_code": 0, "commit_run": "1" * 40}
        self.manifest_path = self.repo / "jobs/readiness-tracker/output/RUNNER_INPUTS.json"
        current = self.current(self.scope)
        self.manifest = {"schema": 1, "job": "readiness-tracker", "base_commit": "1" * 40,
                         "scope": self.scope, "inputs": current, "inputs_sha256": self.freshness.digest(current)}
        job.write(self.manifest_path, self.manifest)
        self.csv_path = self.manifest_path.with_name("READINESS_BY_ORDER.csv")
        self.csv_path.write_text("instrument_id,ready_for_human_review\nEO:1,no\n")

    def current(self, scope):
        self.assertEqual(scope, self.scope)
        return {"held-input.txt": "100644:" + job.sha(self.source.read_bytes())} if self.source.exists() else {}

    def observe(self, commit="2" * 40, status=None):
        inputs = job.Inputs(self.repo)
        prior_cwd = Path.cwd()

        def working(scope):
            self.assertEqual(Path.cwd(), self.repo)
            return self.current(scope)

        with mock.patch.object(self.freshness, "scope", return_value=self.scope), \
                mock.patch.object(self.freshness, "working", side_effect=working):
            result = job.tracker_freshness(inputs, self.status if status is None else status, commit, self.freshness)
        self.assertEqual(Path.cwd(), prior_cwd)
        return result, inputs

    def test_older_identical_inputs_are_reused_and_provenance_and_csv_pinned(self):
        result, inputs = self.observe()
        self.assertTrue(result["passed"])
        self.assertEqual(result["mode"], "reused_identical_inputs")
        self.assertEqual(result["captured_inputs_sha256"], result["current_inputs_sha256"])
        self.assertIn(self.manifest_path.relative_to(self.repo).as_posix(), inputs.pins)
        self.assertIn(self.csv_path.relative_to(self.repo).as_posix(), inputs.pins)

    def test_same_execution_checks_working_bytes(self):
        result, _ = self.observe(commit=self.status["commit_run"])
        self.assertTrue(result["passed"])
        self.assertEqual(result["mode"], "same_execution")
        # Commit identities and saved provenance remain unchanged; only the working file changes.
        self.source.write_text("different uncommitted evidence")
        result, _ = self.observe(commit=self.status["commit_run"])
        self.assertFalse(result["passed"])
        self.assertEqual(result["changed_paths"], ["held-input.txt"])
        self.assertIn("rerun readiness-tracker", result["errors"][0])

    def test_missing_current_input_is_not_equivalent(self):
        self.source.unlink()
        result, _ = self.observe()
        self.assertFalse(result["passed"])
        self.assertEqual(result["changed_paths"], ["held-input.txt"])

    def test_missing_manifest_fails_closed(self):
        self.manifest_path.unlink()
        result, _ = self.observe()
        self.assertFalse(result["passed"])
        self.assertIn("rerun readiness-tracker", result["errors"][0])

    def test_malformed_or_mismatched_provenance_fails_closed(self):
        for mutation in ({"schema": 2}, {"job": "different-job"}, {"inputs_sha256": "0" * 64},
                         {"base_commit": "2" * 40}, {"base_commit": "x" * 40},
                         {"scope": {**self.scope, "patterns": ["new-input"]}}):
            with self.subTest(mutation=mutation):
                job.write(self.manifest_path, {**self.manifest, **mutation})
                result, _ = self.observe()
                self.assertFalse(result["passed"])
                self.assertIn("rerun readiness-tracker", result["errors"][0])

    def test_failed_or_malformed_status_cannot_reuse_inputs(self):
        for status in ({**self.status, "result": "failed"}, {**self.status, "exit_code": 1}, "invalid status"):
            with self.subTest(status=status):
                result, _ = self.observe(status=status)
                self.assertFalse(result["passed"])
                self.assertIn("rerun readiness-tracker", result["errors"][0])


    def test_missing_or_invalid_validation_execution_is_rejected(self):
        for commit in (None, "", "z" * 40, "1" * 41):
            with self.subTest(commit=commit):
                result, _ = self.observe(commit=commit)
                self.assertFalse(result["passed"])
                self.assertIn("validation execution commit is missing or invalid", result["errors"][0])


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
