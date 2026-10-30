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

    def test_malformed_association_identity_does_not_crash_job(self):
        self.fragment["instrument_id"] = []
        self.write_inputs()
        result = self.run_it()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["receipts"][0]["state"], "no_matching_cited_replica")
        self.assertFalse((self.repo / self.rel).exists())

    def test_association_hash_normalization_matches_source_adapter(self):
        self.fragment["data"]["sha256"] = " " + self.digest.upper() + " "
        self.write_inputs()
        result = self.run_it()
        self.assertEqual(result["receipts"][0]["state"], "restored_exact_blob")
        self.assertEqual(result["receipts"][0]["sha256"], self.digest)

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

    def test_missing_pinned_object_is_reported_without_writing(self):
        oid = p.git(self.repo, "rev-parse", "HEAD:" + self.rel).decode().strip()
        (self.repo / ".git/objects" / oid[:2] / oid[2:]).unlink()
        result = self.run_it()
        self.assertEqual(result["receipts"][0]["state"], "unavailable:CalledProcessError")
        self.assertTrue(result["artifacts"][0]["git_object_fetch_attempted"])
        self.assertFalse((self.repo / self.rel).exists())

    def test_lfs_pointer_never_counts_as_bytes(self):
        (self.repo / self.rel).write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
        self.assertEqual(self.run_it()["receipts"][0]["state"], "lfs_bytes_not_materialized")

    def test_invocation_bounds_cannot_be_raised(self):
        with self.assertRaises(ValueError):
            p.materialize(self.repo, self.out, max_artifacts=p.MAX_ARTIFACTS + 1)
        with self.assertRaises(ValueError):
            p.materialize(self.repo, self.out, max_total_bytes=p.MAX_TOTAL_BYTES + 1)

    def test_growing_corpus_does_not_exhaust_per_file_bound(self):
        claims = self.repo / "research/readiness/claims"
        # The target is in the last file, after unrelated metadata has already
        # exceeded the individual-file limit. No corpus-wide budget is valid.
        for name in ("a.jsonl", "b.jsonl"):
            (claims / name).write_bytes(json.dumps({
                "instrument_id": "EO:999", "padding": "x" * 650,
                "source": {"sha256": "0" * 64},
            }).encode() + b"\r\n\n")
        with mock.patch.object(p, "MAX_INPUT_BYTES", 1024):
            r = self.run_it()
        self.assertFalse(r["errors"])
        self.assertEqual(r["receipts"][0]["state"], "restored_exact_blob")
        for path in claims.glob("*.jsonl"):
            self.assertEqual(r["input_sha256"][str(path.relative_to(self.repo))],
                             hashlib.sha256(path.read_bytes()).hexdigest())

    def test_oversized_claim_file_fails_before_restoration(self):
        cp = self.repo / "research/readiness/claims/z.jsonl"
        cp.write_text(json.dumps({"instrument_id": "EO:254", "padding": "x" * 1024}))
        with mock.patch.object(p, "MAX_INPUT_BYTES", 1024):
            r = self.run_it()
        self.assertIn("oversized metadata", r["errors"][0])
        self.assertFalse((self.repo / self.rel).exists())

    def test_malformed_claim_file_fails_before_restoration(self):
        (self.repo / "research/readiness/claims/z.jsonl").write_text("{broken\n")
        self.assertTrue(self.run_it()["errors"])
        self.assertFalse((self.repo / self.rel).exists())

    def add_source(self, iid, name):
        rel = "ProQuest Pre-1937 Orders/" + name + ".pdf"
        raw = ("%PDF-1.4\nfixture " + iid + "\n").encode()
        (self.repo / rel).write_bytes(raw)
        subprocess.run(["git", "-C", str(self.repo), "add", rel], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test", "-c",
                        "user.email=test@example.invalid", "commit", "-qm", "additional source"],
                       check=True, capture_output=True)
        (self.repo / rel).unlink()
        digest = p.sha(raw)
        fragment = json.loads(json.dumps(self.fragment))
        fragment["instrument_id"] = iid
        fragment["data"].update(file=rel, sha256=digest)
        with (self.repo / p.FRAGMENTS).open("a") as f:
            f.write(json.dumps(fragment) + "\n")
        (self.repo / "research/readiness/claims" / (name + ".jsonl")).write_text(
            json.dumps({"instrument_id": iid, "source": {"sha256": digest}}) + "\n")
        return rel, raw

    def test_automatic_effective_selection_extends_beyond_three(self):
        for n in range(4):
            self.add_source(f"EO:{n + 100}", f"extra{n}")
        r = p.materialize(self.repo, self.out)
        self.assertFalse(r["errors"])
        self.assertEqual(len(r["artifacts"]), 5)
        self.assertEqual({x["state"] for x in r["receipts"]}, {"restored_exact_blob"})

    def test_explicit_selection_preserves_three_case_compatibility(self):
        rel, _ = self.add_source("EO:1547", "additional")
        r = p.materialize(self.repo, self.out, p.DEFAULT_IDS)
        self.assertEqual(next(x for x in r["receipts"] if x["instrument_id"] == "EO:254")["state"],
                         "restored_exact_blob")
        self.assertFalse((self.repo / rel).exists())

    def test_last_filename_and_physical_line_are_effective(self):
        cp = self.repo / "research/readiness/claims/z.jsonl"
        cp.write_bytes(b"\xef\xbb\xbf\n" + json.dumps({"instrument_id": "EO:254", "source": {"sha256": self.digest}}).encode()
                       + b"\n\n" + json.dumps({"instrument_id": "EO:254", "source": {"sha256": "0" * 64}}).encode())
        self.assertEqual(self.run_it()["receipts"][0]["state"], "no_matching_cited_replica")
        self.assertFalse((self.repo / self.rel).exists())

    def test_confirmations_are_not_source_references(self):
        cp = self.repo / "research/readiness/claims/x.jsonl"
        cp.write_text(json.dumps({"instrument_id": "EO:254", "working_text": {"confirmations": [{"sha256": self.digest}]}}))
        self.assertEqual(self.run_it()["receipts"][0]["state"], "no_matching_cited_replica")

    def test_cross_identity_reference_refused(self):
        cp = self.repo / "research/readiness/claims/x.jsonl"
        cp.write_text(json.dumps({"instrument_id": "EO:254", "source": {"sha256": self.digest, "instrument_id": "EO:999"}}))
        self.assertEqual(self.run_it()["receipts"][0]["state"], "conflicting_identity_path_or_hash")
        self.assertFalse((self.repo / self.rel).exists())

    def test_conflicting_path_hash_association_refused(self):
        fragment = json.loads(json.dumps(self.fragment))
        fragment["instrument_id"] = "EO:999"
        fragment["data"]["sha256"] = "0" * 64
        with (self.repo / p.FRAGMENTS).open("a") as f:
            f.write(json.dumps(fragment) + "\n")
        self.assertEqual(self.run_it()["receipts"][0]["state"], "conflicting_identity_path_or_hash")
        self.assertFalse((self.repo / self.rel).exists())

    def test_shared_pdf_deduplicated_with_every_claim_reference(self):
        fragment = json.loads(json.dumps(self.fragment))
        fragment["instrument_id"] = "EO:255"
        with (self.repo / p.FRAGMENTS).open("a") as f:
            f.write(json.dumps(fragment) + "\n")
        (self.repo / "research/readiness/claims/y.jsonl").write_text(json.dumps({
            "instrument_id": "EO:255", "source": {"sha256": self.digest},
            "sources": [{"sha256": self.digest}]}))
        r = p.materialize(self.repo, self.out, max_artifacts=1)
        self.assertEqual(len(r["artifacts"]), 1)
        self.assertEqual(len(r["receipts"]), 2)
        self.assertEqual(sum(len(x["references"]) for x in r["receipts"]), 3)
        self.assertEqual(r["bytes_read"], len(self.raw))

    def test_batch_deferral_and_resume_do_not_reverify_prefix(self):
        for n in range(4):
            self.add_source(f"EO:{n + 100}", f"extra{n}")
        r = p.materialize(self.repo, self.out, max_artifacts=2)
        self.assertEqual(sum(x["state"] == "restored_exact_blob" for x in r["artifacts"]), 2)
        self.assertEqual(sum(x["state"] == "deferred_batch_bound" for x in r["artifacts"]), 3)
        r2 = p.materialize(self.repo, self.out, max_artifacts=2, resume=r["next_cursor"])
        self.assertEqual(sum(x["state"] == "before_cursor_not_reverified" for x in r2["artifacts"]), 2)
        r3 = p.materialize(self.repo, self.out, max_artifacts=2, resume=r2["next_cursor"])
        self.assertIsNone(r3["next_cursor"])
        self.assertEqual(sum(x["state"] == "restored_exact_blob" for x in r3["artifacts"]), 1)

    def test_byte_budget_deferred_and_resumed(self):
        r = p.materialize(self.repo, self.out, max_total_bytes=len(self.raw) - 1)
        self.assertEqual(r["receipts"][0]["state"], "deferred_byte_budget")
        self.assertFalse((self.repo / self.rel).exists())
        r2 = p.materialize(self.repo, self.out, resume=r["next_cursor"])
        self.assertEqual(r2["receipts"][0]["state"], "restored_exact_blob")

    def test_changed_selection_refuses_resume_before_writes(self):
        r = p.materialize(self.repo, self.out, max_total_bytes=1)
        (self.repo / "research/readiness/claims/other.jsonl").write_text('{"instrument_id":"EO:999"}\n')
        r2 = p.materialize(self.repo, self.out, resume=r["next_cursor"])
        self.assertIn("resume selection changed", r2["errors"][0])
        self.assertFalse((self.repo / self.rel).exists())

    def test_local_matching_hash_must_match_pinned_blob(self):
        changed = b"%PDF-1.4\nlocal uncommitted source\n"
        (self.repo / self.rel).write_bytes(changed)
        self.digest = p.sha(changed)
        self.fragment["data"]["sha256"] = self.digest
        self.write_inputs()
        self.assertEqual(self.run_it()["receipts"][0]["state"], "existing_bytes_not_pinned_blob")
        self.assertEqual((self.repo / self.rel).read_bytes(), changed)

    def test_tracked_lfs_pointer_is_not_materialized_as_pdf(self):
        pointer = b"version https://git-lfs.github.com/spec/v1\noid sha256:" + self.digest.encode() + b"\nsize 99\n"
        (self.repo / self.rel).write_bytes(pointer)
        subprocess.run(["git", "-C", str(self.repo), "add", self.rel], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test", "-c",
                        "user.email=test@example.invalid", "commit", "-qm", "pointer"], check=True, capture_output=True)
        (self.repo / self.rel).unlink()
        self.assertEqual(self.run_it()["receipts"][0]["state"], "lfs_bytes_not_materialized")
        self.assertFalse((self.repo / self.rel).exists())

    def test_evidence_grade_and_association_required(self):
        self.fragment["data"]["acceptable_as_original"] = True
        self.write_inputs()
        self.assertEqual(self.run_it()["receipts"][0]["state"], "no_matching_cited_replica")
        self.assertFalse((self.repo / self.rel).exists())


if __name__ == "__main__":
    unittest.main()
