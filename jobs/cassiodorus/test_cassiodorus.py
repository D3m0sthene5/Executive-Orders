"""Offline tests for Cassiodorus: request discovery and hash discipline. No network."""
import json
import pathlib
import sys
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
