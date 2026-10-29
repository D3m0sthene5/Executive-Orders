"""Offline sparse-checkout restoration tests with real temporary Git objects."""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import proquest_inputs as p


class ProQuestInputsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.out = Path(self.tmp.name) / "out"
        self.rel = "ProQuest Pre-1937 Orders/scan.pdf"
        self.raw = b"%PDF-1.4\nsynthetic fixture only\n"
        self.digest = hashlib.sha256(self.raw).hexdigest()
        (self.repo / self.rel).parent.mkdir()
        (self.repo / self.rel).write_bytes(self.raw)
        for args in [("init", "-q"), ("add", "."), ("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")]:
            subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)
        (self.repo / self.rel).unlink()
        self.fragment = {"instrument_id": "EO:254", "kind": "original_representation", "produced_by": "pinakes-proquest-ingest", "data": {"acceptable_as_original": False, "grade": "archival_replica_scan_pending_codebook", "file": self.rel, "sha256": self.digest}}
        self.write_inputs()

    def write_inputs(self, cited=True):
        fp = self.repo / p.FRAGMENTS
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(json.dumps(self.fragment) + "\n")
        cp = self.repo / "research/readiness/claims/x.jsonl"
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps({"instrument_id": "EO:254", "source": {"sha256": self.digest if cited else "0" * 64}}) + "\n")

    def run_it(self):
        return p.materialize(self.repo, self.out, ("EO:254",))

    def test_restores_exact_cited_blob(self):
        r = self.run_it()
        self.assertEqual(r["receipts"][0]["state"], "restored_exact_blob")
        self.assertEqual((self.repo / self.rel).read_bytes(), self.raw)
        self.assertEqual(self.run_it()["receipts"][0]["state"], "already_held")

    def test_uncited_scan_not_materialized(self):
        self.write_inputs(cited=False)
        self.assertEqual(self.run_it()["receipts"][0]["state"], "no_matching_cited_replica")
        self.assertFalse((self.repo / self.rel).exists())

    def test_existing_wrong_bytes_never_overwritten(self):
        (self.repo / self.rel).write_bytes(b"local work")
        self.assertEqual(self.run_it()["receipts"][0]["state"], "existing_hash_mismatch")
        self.assertEqual((self.repo / self.rel).read_bytes(), b"local work")

    def test_wrong_git_hash_refused(self):
        self.digest = "0" * 64
        self.fragment["data"]["sha256"] = self.digest
        self.write_inputs()
        self.assertEqual(self.run_it()["receipts"][0]["state"], "blob_hash_or_format_mismatch")
        self.assertFalse((self.repo / self.rel).exists())

    def test_path_escape_refused_before_git(self):
        self.fragment["data"]["file"] = "ProQuest Pre-1937 Orders/../../escape.pdf"
        self.write_inputs()
        self.assertTrue(self.run_it()["errors"])

    def test_symlink_refused(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        try:
            (self.repo / self.rel).symlink_to(Path(self.tmp.name) / "outside.pdf")
        except OSError:
            self.skipTest("symlink privilege unavailable")
        self.assertTrue(self.run_it()["errors"])

    def test_budget_refused(self):
        with mock.patch.object(p, "MAX_FILE_BYTES", 4):
            self.assertEqual(self.run_it()["receipts"][0]["state"], "byte_budget_hold")

    def test_untracked_path_refused(self):
        self.fragment["data"]["file"] = "ProQuest Pre-1937 Orders/absent.pdf"
        self.write_inputs()
        self.assertEqual(self.run_it()["receipts"][0]["state"], "not_in_pinned_tree")

    def test_lfs_pointer_never_counts_as_bytes(self):
        (self.repo / self.rel).write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
        self.assertEqual(self.run_it()["receipts"][0]["state"], "lfs_bytes_not_materialized")

    def test_identity_bound(self):
        with self.assertRaises(ValueError):
            p.materialize(self.repo, self.out, ("EO:1", "EO:2", "EO:3", "EO:4"))


if __name__ == "__main__":
    unittest.main()
