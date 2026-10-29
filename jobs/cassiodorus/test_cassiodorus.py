"""Offline tests for Cassiodorus: request discovery and hash discipline. No network."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cassiodorus as C  # noqa: E402

SHA_A = "a" * 64
SHA_B = "b" * 64


class Discovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        claims = self.root / "research/readiness/claims"
        claims.mkdir(parents=True)
        (claims / "x.jsonl").write_text(json.dumps({
            "instrument_id": "EO:1",
            "original_representation": {"url": "https://www.presidency.ucsb.edu/documents/eo-1", "sha256": SHA_A},
            "operative_clauses": [{"original_source": {"url": "https://www.govinfo.gov/x.pdf", "sha256": SHA_B}}]}) + "\n",
            encoding="utf-8")
        packet = self.root / "research/excavator/run-1/packet/applied-v1"
        packet.mkdir(parents=True)
        (packet / "CLAIMS.proposed.jsonl").write_text(json.dumps({
            "savings_residuals": {"source": {"url": "https://www.presidency.ucsb.edu/documents/eo-2", "sha256": SHA_B}}}) + "\n",
            encoding="utf-8")

    def test_only_app_pages_are_collected_from_claims_and_packets(self):
        found = C.cited_app_pages(str(self.root))
        self.assertEqual(found, {SHA_A: "https://www.presidency.ucsb.edu/documents/eo-1",
                                 SHA_B: "https://www.presidency.ucsb.edu/documents/eo-2"})

    def test_explicit_requests_are_bounded_to_valid_hashes(self):
        job = self.root / "job"
        job.mkdir()
        (job / "REQUESTS.json").write_text(json.dumps({"sha256": [SHA_A, "nothex"], "instrument_ids": ["EO:9"]}), encoding="utf-8")
        shas, ids = C.explicit_requests(str(self.root), job)
        self.assertEqual(shas, {SHA_A})
        self.assertEqual(ids, {"EO:9"})


class HashDiscipline(unittest.TestCase):
    def test_sha256_is_hex_of_bytes(self):
        self.assertEqual(C.sha256(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


class ArchiveOnly(unittest.TestCase):
    def test_live_record_is_refused_without_a_request(self):
        import app_mirror as M
        record = {"kind": "live", "row": {"url": "https://www.presidency.ucsb.edu/documents/eo-1"}}
        with mock.patch.object(M, "http_get") as get:
            with self.assertRaisesRegex(C.ArchiveUnavailable, "live APP acquisition is disabled"):
                C.fetch_bytes(record, pathlib.Path("unused"), {})
        get.assert_not_called()

    def test_unavailable_live_records_do_not_block_archive_retention(self):
        import app_mirror as M
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            app = root / C.APP_OUT
            app.mkdir(parents=True)
            job, out, cache = root / "job", root / "out", root / "cache"
            job.mkdir()
            body = b"fixed archive bytes"
            sha = C.sha256(body)
            url = "https://www.presidency.ucsb.edu/documents/eo-archive"
            unavailable = [{"sha256": str(i) * 64, "url": url + str(i)} for i in range(6)]
            self.assertTrue(all(r["sha256"] < sha for r in unavailable))
            (app / "DOCUMENTS.jsonl").write_text("".join(json.dumps(r) + "\n" for r in unavailable))
            row = {"sha256": sha, "url": url, "capture": {"archive": "common-crawl",
                   "warc_filename": "crawl-data/test.warc.gz", "warc_offset": 0, "warc_length": 1}}
            (app / "MIRROR_DOCUMENTS.jsonl").write_text(json.dumps(row) + "\n")
            (job / "REQUESTS.json").write_text(json.dumps({"sha256": [r["sha256"] for r in unavailable] + [sha]}))
            with mock.patch.object(M, "http_get") as get, mock.patch.object(M, "read_cc", return_value=(body, {})):
                summary = C.run(root, job, out, cache)
            get.assert_not_called()
            self.assertEqual(summary["counts"]["no_archive_capture"], 6)
            self.assertEqual(summary["counts"]["skipped_after_failures"], 0)
            self.assertEqual(summary["counts"]["kept"], 1)
            self.assertEqual((out / "raw" / (sha + ".html")).read_bytes(), body)
            results = json.loads((out / "RESULTS.json").read_text())
            self.assertEqual([r["result"] for r in results], ["no_archive_capture"] * 6 + ["kept"])

    def test_previously_retained_live_bytes_are_rehashed_and_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            job, out = root / "job", root / "out"
            job.mkdir()
            (out / "raw").mkdir(parents=True)
            body = b"previously retained live bytes"
            sha = C.sha256(body)
            path = out / "raw" / (sha + ".html")
            path.write_bytes(body)
            (job / "REQUESTS.json").write_text(json.dumps({"sha256": [sha]}))
            with mock.patch.object(C, "fetch_bytes") as fetch:
                summary = C.run(root, job, out, root / "cache")
            fetch.assert_not_called()
            self.assertEqual(summary["counts"]["already_kept"], 1)
            self.assertEqual(path.read_bytes(), body)
            self.assertEqual(json.loads((out / "SOURCES.jsonl").read_text())["sha256"], sha)


if __name__ == "__main__":
    unittest.main()
