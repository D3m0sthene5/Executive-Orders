"""Offline provider wiring tests; no acquisition or legal classification."""
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
import event_sources as e

compact = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


class EventSourcesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.spec = [{"event_id": "test-event", "sources": [{"url": "https://example.invalid/source", "citation": "test only", "verify_phrases": ["required phrase"]}]}]

    def source(self, provider, text="required phrase", raw=b"source", **changes):
        base = self.repo / "jobs" / provider / "output"
        base.mkdir(parents=True, exist_ok=True)
        (base / "text.txt").write_text(text, encoding="utf-8")
        (base / "raw.bin").write_bytes(raw)
        row = {"url": self.spec[0]["sources"][0]["url"], "sha256": hashlib.sha256(raw).hexdigest(), "cache_path": "raw.bin", "text_path": "text.txt", "text_sha256": hashlib.sha256(text.encode()).hexdigest()}
        row.update(changes)
        (base / "SOURCES.jsonl").write_text(json.dumps(row) + "\n")
        return base

    def result(self):
        return e.evaluate(self.repo, self.spec, compact)["test-event"][0]

    def test_retention_is_consumed(self):
        self.source("astra-source-retention")
        r = self.result()
        self.assertEqual(r["state"], "held_phrases_found")
        self.assertEqual(r["selected"]["provider"], "astra-source-retention")
        self.assertEqual(r["selected"]["raw_custody"], "bytes_rehashed")

    def test_narrow_excerpt_cannot_overwrite_passing_panizzi(self):
        self.source("source-ladder")
        self.source("astra-source-retention", text="narrow excerpt")
        r = self.result()
        self.assertEqual(r["state"], "held_phrases_found")
        self.assertEqual(r["selected"]["provider"], "source-ladder")
        self.assertEqual(len(r["representations"]), 2)
        self.assertEqual(next(x for x in r["representations"] if x["provider"] == "astra-source-retention")["state"], "held_phrases_missing")

    def test_phrase_failure_remains(self):
        self.source("astra-source-retention", text="different wording")
        self.assertEqual(self.result()["state"], "held_phrases_missing")

    def test_text_hash_mismatch_refused(self):
        self.source("astra-source-retention", text_sha256="0" * 64)
        self.assertEqual(self.result()["state"], "held_invalid")

    def test_missing_text_is_explicit(self):
        base = self.source("astra-source-retention")
        (base / "text.txt").unlink()
        self.assertEqual(self.result()["state"], "held_invalid")

    def test_conflicting_raw_versions_refused(self):
        self.source("source-ladder")
        self.source("astra-source-retention", raw=b"different source")
        self.assertEqual(self.result()["state"], "held_conflicting_versions")
        self.assertIsNone(self.result()["selected"])

    def test_raw_hash_mismatch_refused(self):
        self.source("astra-source-retention", sha256="0" * 64)
        self.assertEqual(self.result()["state"], "held_invalid")

    def test_absent_raw_bytes_never_reported_verified(self):
        base = self.source("astra-source-retention")
        (base / "raw.bin").unlink()
        self.assertEqual(self.result()["selected"]["raw_custody"], "not_rehashed_here")

    def test_unsafe_path_refused(self):
        self.source("astra-source-retention", text_path="../outside.txt")
        self.assertEqual(self.result()["state"], "held_invalid")

    def test_missing_provider_is_pending(self):
        self.assertEqual(self.result()["state"], "source_pending")


class SheetHandoffTests(unittest.TestCase):
    def test_sheet_preserves_source_state_role_and_blank_judgments(self):
        import sheets
        from unittest import mock
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            p = repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
            p.parent.mkdir(parents=True)
            p.write_text("instrument_id,provisional_status\nEO:1,no\n")
            types = {"EO:1": {"type": "land_withdrawal_general", "class": "land", "confidence": "high", "text_path": "t", "text_grade": "working", "evidence_source": "fixture", "evidence_match": "x", "rule_id": ""}}
            ev = [{"instrument_id": "EO:1", "event_id": "FLPMA", "role": "not_an_end_authority_repeal", "sources_state": "all_held_phrases_found", "source_records": json.dumps([{"source_record": "jobs/astra-source-retention/output/SOURCES.jsonl:1"}])}]
            with mock.patch.dict("os.environ", {"X1_RISK_TIERED_REVIEW": "0"}):
                row = sheets.build(repo, types, [], [], ev, {})[0]["rows"][0]
            detail = json.loads(row["event_source_details"])[0]
            self.assertEqual(detail["role"], "not_an_end_authority_repeal")
            self.assertTrue(detail["records"][0]["source_record"].endswith(":1"))
            self.assertEqual(row["provisional_status"], "no")
            self.assertEqual((row["review_tier"], row["agent_decision"], row["reviewer_decision"]), ("full", "", ""))
            self.assertIn("event_source_details", sheets.COLUMNS)


if __name__ == "__main__":
    unittest.main()
