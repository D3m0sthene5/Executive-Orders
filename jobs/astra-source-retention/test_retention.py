import contextlib
import importlib.util
import io
import json
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from pypdf import PdfWriter

spec = importlib.util.spec_from_file_location("retention", Path(__file__).with_name("job.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RequestBoundary(unittest.TestCase):
    def setUp(self):
        self.item = {"url":"https://www.govinfo.gov/example.pdf", "instrument_ids":["EO:1"], "pages":[1,2], "expected_sha256":"a"*64}
        self.queue = [{"instrument_id":"EO:1", "urls":[self.item["url"]]}]

    def test_exact_queue_pair_required(self):
        module.validate_manifest([self.item], self.queue)
        with self.assertRaises(ValueError):
            module.validate_manifest([{**self.item, "instrument_ids":["EO:2"]}], self.queue)

    def test_https_and_duplicate_boundary(self):
        with self.assertRaises(ValueError):
            module.validate_manifest([{**self.item, "url":"http://www.govinfo.gov/example.pdf"}], self.queue)
        with self.assertRaises(ValueError):
            module.validate_manifest([self.item, self.item], self.queue)

    def test_page_and_hash_boundary(self):
        for pages in ([0], [True], [1.5], list(range(1,42))):
            with self.assertRaises(ValueError):
                module.validate_manifest([{**self.item, "pages":pages}], self.queue)
        with self.assertRaises(ValueError):
            module.validate_manifest([{**self.item, "expected_sha256":"not-a-hash"}], self.queue)

    def test_run_bound(self):
        with self.assertRaises(ValueError):
            module.validate_manifest([self.item]*31, self.queue)


class RetainedGeneration(unittest.TestCase):
    """Exercise durable retention across runner generations with network disabled."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.job = self.root / "jobs/astra-source-retention"
        self.job.mkdir(parents=True)
        self.prior = self.job / "output"
        self.pdf = self.root / "held.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_blank_page(width=200, height=200)
        writer.write(self.pdf)
        self.digest = module.sha(self.pdf)
        self.item = {"url": "https://www.govinfo.gov/test.pdf", "instrument_ids": ["EO:1"],
                     "pages": [1, 2], "expected_sha256": self.digest, "retained_path": "held.pdf"}
        queue = self.root / "research/readiness/FETCH_QUEUE.jsonl"
        queue.parent.mkdir(parents=True)
        queue.write_text(json.dumps({"instrument_id": "EO:1", "urls": [self.item["url"]]}) + "\n")
        self.fetcher = Mock(requests=0, bytes_downloaded=0)
        self.fetcher.fetch.side_effect = AssertionError("Unexpected network request")

    def run_generation(self, out, item=None, prior=None, reader=None):
        (self.job / "REQUESTS.json").write_text(json.dumps([item or self.item]))
        env = {"OUTPUT_DIR": str(out), "JOB_CACHE_DIR": str(self.root / "cache"),
               "JOB_PRIOR_OUTPUT_DIR": str(prior or self.prior),
               "RETENTION_MANIFEST": str(self.job / "REQUESTS.json"), "RETENTION_RENDER_PAGES": "0"}
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(module, "ROOT", self.root))
            stack.enter_context(patch.object(module, "JOB", self.job))
            stack.enter_context(patch.object(module, "Fetcher", return_value=self.fetcher))
            stack.enter_context(patch.dict(os.environ, env))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if reader is not None:
                stack.enter_context(patch.object(module, "PdfReader", return_value=reader))
            module.main()
        return (json.loads((out / "SUMMARY.json").read_text()),
                [json.loads(s) for s in (out / "SOURCES.jsonl").read_text().splitlines()],
                json.loads((out / "RESULTS.json").read_text()))

    def test_import_requires_exact_hash_and_repository_path(self):
        queue = [{"instrument_id": "EO:1", "urls": [self.item["url"]]}]
        for changes in ({"expected_sha256": None}, {"retained_path": "../held.pdf"},
                        {"retained_path": str(self.pdf)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                module.validate_manifest([{**self.item, **changes}], queue)
        with self.assertRaises(ValueError):
            module.retained_import(self.root, {**self.item, "expected_sha256": "0" * 64})
        with self.assertRaises(FileNotFoundError):
            module.retained_import(self.root, {**self.item, "retained_path": "missing.pdf"})

    def test_import_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "source.pdf"
            target.write_bytes(self.pdf.read_bytes())
            link = self.root / "escape.pdf"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlinks unavailable on this runner: {exc}")
            with self.assertRaises(ValueError):
                module.retained_import(self.root, {**self.item, "retained_path": "escape.pdf"})

    def test_prior_metadata_is_detached_and_runner_receipts_not_copied(self):
        self.prior.mkdir()
        names = ("RESULTS.json", "SOURCES.jsonl", "SUMMARY.json")
        for name in names:
            (self.prior / name).write_text("prior contents")
        (self.prior / "held.bin").write_bytes(b"immutable evidence")
        (self.prior / "STATUS.json").write_text("old execution status")
        out = self.root / "next"
        out.mkdir()
        module.preserve_previous(out, self.prior)
        for name in names:
            (out / name).write_text("new contents")
            self.assertEqual((self.prior / name).read_text(), "prior contents")
        self.assertEqual((out / "held.bin").read_bytes(), b"immutable evidence")
        self.assertFalse((out / "STATUS.json").exists())

    def test_exact_import_reaches_existing_source_catalogue_without_fetch(self):
        summary, sources, records = self.run_generation(self.prior)
        self.fetcher.fetch.assert_not_called()
        self.assertEqual(summary["imported_objects"], 1)
        self.assertEqual(summary["extractions_completed"], 1)
        self.assertEqual(module.sha(self.prior / sources[0]["cache_path"]), self.digest)
        self.assertEqual(module.sha(self.prior / sources[0]["text_path"]), sources[0]["text_sha256"])
        self.assertEqual(sources[0]["instrument_ids"], [])
        self.assertEqual(sources[0]["requested_for_instrument_ids"], ["EO:1"])
        self.assertNotIn("acceptable_as_original", sources[0])
        self.assertIn("no new page review", records[-1]["pages"][0]["render_error"])

    def test_narrower_extraction_keeps_prior_complete_representation(self):
        _, before, _ = self.run_generation(self.prior)
        old_text = (self.prior / before[0]["text_path"]).read_bytes()
        out = self.root / "narrower"
        _, after, _ = self.run_generation(out, {**self.item, "pages": [1]})
        self.assertEqual(len(after), 2)
        self.assertIn(before[0], after)
        self.assertEqual((out / before[0]["text_path"]).read_bytes(), old_text)
        self.assertEqual((self.prior / before[0]["text_path"]).read_bytes(), old_text)
        self.assertEqual(module.sha(out / before[0]["cache_path"]), self.digest)
        self.fetcher.fetch.assert_not_called()

    def test_failed_reextraction_preserves_pdf_text_and_source_mapping(self):
        _, before, _ = self.run_generation(self.prior)
        held_text = (self.prior / before[0]["text_path"]).read_bytes()
        pages = [Mock(), Mock()]
        pages[0].extract_text.return_value = "partially staged text"
        pages[1].extract_text.side_effect = ValueError("test extraction failed")
        out = self.root / "failed"
        summary, after, records = self.run_generation(out, reader=Mock(pages=pages))
        self.assertEqual(after, before)
        self.assertEqual(summary["extractions_completed"], 0)
        self.assertIn("test extraction failed", records[-1]["error"])
        self.assertEqual((out / before[0]["text_path"]).read_bytes(), held_text)
        self.assertEqual(module.sha(out / before[0]["cache_path"]), self.digest)
        self.assertFalse(list(out.glob(".retention-*")))
        self.fetcher.fetch.assert_not_called()

    def test_different_download_is_preserved_without_relabeling(self):
        self.fetcher.fetch.side_effect = None
        self.fetcher.fetch.return_value = {"accepted": True, "path": str(self.pdf),
                                          "sha256": self.digest, "final_url": self.item["url"]}
        item = {k: v for k, v in self.item.items() if k != "retained_path"}
        item["expected_sha256"] = "0" * 64
        out = self.root / "different"
        summary, sources, records = self.run_generation(out, item)
        self.assertEqual(sources, [])
        self.assertEqual(summary["retained"], 0)
        self.assertEqual((out / "quarantine" / (self.digest + ".pdf")).read_bytes(), self.pdf.read_bytes())
        self.assertFalse((out / "pdf" / (item["expected_sha256"] + ".pdf")).exists())
        self.assertIn("hash_mismatch", records[-1]["error"])

    def test_corrupt_extraction_is_quarantined_and_repaired(self):
        _, before, _ = self.run_generation(self.prior)
        text_path = self.prior / before[0]["text_path"]
        expected = text_path.read_bytes()
        text_path.write_text("corrupted extraction")
        out = self.root / "repaired"
        _, sources, records = self.run_generation(out)
        self.assertEqual((out / sources[-1]["text_path"]).read_bytes(), expected)
        self.assertEqual(text_path.read_text(), "corrupted extraction")
        quarantine = out / records[-1]["repaired_corrupt_extraction"]
        self.assertEqual((quarantine / text_path.name).read_text(), "corrupted extraction")
        self.fetcher.fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
