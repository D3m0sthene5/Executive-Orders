"""Offline tests; every PDF-like file and audit event is a temporary fixture.

Run from the package: python -m unittest discover -s tests -v
Before the source is packaged, PROQUEST_TEST_SOURCE may point at the attachment.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("PROQUEST_TEST_SOURCE", ROOT / "_resume" / "proquest_download_links.html"))


class PortableProgressTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOURCE.is_file():
            raise unittest.SkipTest("The original source attachment must be present")
        cls.source_bytes = SOURCE.read_bytes()
        text = cls.source_bytes.decode("utf-8")
        cls.rows, _ = json.JSONDecoder().raw_decode(text.split("const ROWS=", 1)[1])
        cls.by_id = {r["id"]: r for r in cls.rows}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="proquest-portable-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.package = self.base / "portable project"
        resume = self.package / "_resume"
        scripts = self.package / "scripts"
        resume.mkdir(parents=True)
        scripts.mkdir()
        self.script = scripts / "proquest_progress.py"
        shutil.copyfile(ROOT / "scripts" / "proquest_progress.py", self.script)
        (resume / "proquest_download_links.html").write_bytes(self.source_bytes)
        self.checkpoint = resume / "checkpoint.json"
        self.checkpoint.write_text(json.dumps({"downloaded_files_verified": [
            {"eo": eo_id, "evidence": "TEST ONLY screenshot fixture"}
            for eo_id in ("EO:4", "EO:7", "EO:12")
        ]}), encoding="utf-8")
        self.log = resume / "progress.jsonl"
        events = [self.event(eo_id, "saved_requested") for eo_id in (
            "EO:10", "EO:13", "EO:14", "EO:15", "EO:17", "EO:23", "EO:26", "EO:28"
        )]
        events += [self.event("EO:28A", "error_unresolved", terminal=False),
                   self.event("EO:28A", "link_unavailable", terminal=True,
                              evidence="TEST ONLY: Access is denied")]
        self.log.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
        self.outside = self.base / "unrelated working directory"
        self.outside.mkdir()
        self.folder = self.base / "ProQuest Pre-1937 Orders"
        self.folder.mkdir()

    def event(self, eo_id, status, **extra):
        return {
            "id": eo_id, "status": status,
            "source_url": self.by_id[eo_id]["rec"],
            "timestamp": "2026-10-19T00:00:00Z",
            "evidence": "TEST ONLY synthetic audit event",
            **extra,
        }

    def run_cli(self, *args, event=None, expected=0):
        result = subprocess.run(
            [sys.executable, str(self.script), *map(str, args)],
            cwd=self.outside, text=True, capture_output=True,
            input=None if event is None else json.dumps(event),
        )
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout if expected == 0 else result.stderr)

    def make_pdf_fixtures(self):
        first = b"%PDF-1.7\nTEST ONLY synthetic bytes\n%%EOF\n"
        other = b"%PDF-1.4\nTEST ONLY other synthetic bytes\n%%EOF\n"
        contents = {
            "PT1-1865-EO-4.pdf": first,
            "PT1-1865-EO-4 (1).pdf": first,
            "1873-EO-10.pdf": first,
            "1873-EO-10 (2).pdf": other,
            "PT1-1874-EO-13.pdf": b"<!doctype html>TEST ONLY error response",
            "PT1-1900-EO-125A.pdf": first,
            "PT1-1872-EO-10.pdf": first,
            "unrelated.pdf": first,
            "PT1-1874-EO-14.pdf.crdownload": first,
            "unrelated.txt": b"ignored",
        }
        for name, data in contents.items():
            (self.folder / name).write_bytes(data)
        nested = self.folder / "nested"
        nested.mkdir()
        (nested / "PT1-1874-EO-14.pdf").write_bytes(first)
        return first

    def test_portable_defaults_pause_state_and_exact_source_validation(self):
        status = self.run_cli("status")
        self.assertEqual(status["saved_requested"], 8)
        self.assertEqual(status["verified_screenshot"], 3)
        self.assertEqual(status["link_unavailable"], 31)
        self.assertEqual(status["linked_unavailable"], 1)
        self.assertEqual(status["source_rows_without_links"], 30)
        self.assertEqual(status["remaining"], 2723)
        first = self.run_cli("next", "--limit", 1)
        self.assertEqual(first, [self.by_id["EO:29"]])
        before = self.log.read_bytes()
        bad = self.event("EO:29", "saved_requested",
                         source_url=self.by_id["EO:29"]["rec"] + "?altered=1")
        self.run_cli("record", event=bad, expected=2)
        self.assertEqual(self.log.read_bytes(), before)

    def test_read_only_inventory_and_explicit_reconcile(self):
        first_bytes = self.make_pdf_fixtures()
        log_before = self.log.read_bytes()
        checkpoint_before = self.checkpoint.read_bytes()
        inventory = self.run_cli("inventory", "--folder", self.folder)
        self.assertEqual(self.log.read_bytes(), log_before)
        self.assertEqual(self.checkpoint.read_bytes(), checkpoint_before)
        self.assertEqual(inventory["summary"]["pdf_files"], 8)
        self.assertEqual(inventory["summary"]["recognized_pdf_files"], 4)
        self.assertEqual(inventory["summary"]["unique_orders"], 2)
        self.assertEqual(inventory["summary"]["duplicate_files"], 2)
        self.assertEqual(inventory["summary"]["invalid_pdf_signatures"], 1)
        files = {f["filename"]: f for f in inventory["files"]}
        self.assertEqual(files["PT1-1865-EO-4.pdf"]["sha256"], hashlib.sha256(first_bytes).hexdigest())
        self.assertEqual(files["1873-EO-10.pdf"]["eo_id"], "EO:10")
        self.assertFalse(files["PT1-1900-EO-125A.pdf"]["eligible_for_reconcile"])
        self.assertFalse(files["PT1-1872-EO-10.pdf"]["eligible_for_reconcile"])
        self.assertFalse(files["PT1-1874-EO-13.pdf"]["eligible_for_reconcile"])
        result = self.run_cli("reconcile", "--folder", self.folder)
        self.assertEqual(result["audit_events_added"], 2)
        self.assertEqual(result["status"]["verified_local_pdf"], 2)
        self.assertEqual(result["status"]["saved_requested"], 7)
        self.assertEqual(result["status"]["linked_unavailable"], 1)
        self.assertEqual(result["status"]["source_rows_without_links"], 30)
        self.assertTrue(self.log.read_bytes().startswith(log_before))
        events = [json.loads(line) for line in self.log.read_text().splitlines()]
        latest_denied = [e for e in events if e["id"] == "EO:28A"][-1]
        self.assertEqual(latest_denied["status"], "link_unavailable")
        self.assertTrue(latest_denied["terminal"])
        self.assertFalse(any(e["id"] == "EO:125A" for e in events))
        after_first = self.log.read_bytes()
        repeat = self.run_cli("reconcile", "--folder", self.folder)
        self.assertEqual(repeat["audit_events_added"], 0)
        self.assertEqual(self.log.read_bytes(), after_first)

    def test_repository_evidence_survives_empty_local_folder(self):
        repo_event = self.event(
            "EO:29", "verified_repository",
            repository_path="pdfs/PT1-1893-EO-29.pdf",
            repository_url="https://github.com/example/test-fixture/blob/test/pdfs/PT1-1893-EO-29.pdf",
            repository_blob_sha="a" * 40,
            evidence="TEST ONLY synthetic confirmed repository file",
        )
        recorded = self.run_cli("record", event=repo_event)["recorded"]
        self.assertFalse(recorded["filesystem_verified"])
        self.assertTrue(recorded["repository_verified"])
        self.assertEqual(self.run_cli("next", "--limit", 1), [self.by_id["EO:99"]])
        result = self.run_cli("reconcile", "--folder", self.folder)
        self.assertEqual(result["audit_events_added"], 0)
        self.assertEqual(result["status"]["verified_repository"], 1)
        self.assertEqual(result["repository_verified_without_matching_file_here"], ["EO:29"])
        self.assertEqual(result["status"]["linked_unavailable"], 1)


if __name__ == "__main__":
    unittest.main()
