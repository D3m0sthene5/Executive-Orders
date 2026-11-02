import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import event_checks as E
import name_checks as N


class EventRoles(unittest.TestCase):
    def check(self, text, events=None):
        claim = {"instrument_id": "EO:12345", "operative_clauses": [{"scope_id": "whole", "judgment_reason": text,
                 "first_end": {"actor": "EO:15000", "source": {"quote": "revoked"}}, "later_events": events or []}]}
        return E.check(claim, {"evidence": {}}, Path.cwd())

    def test_grammatical_subject_and_revoked_object(self):
        row = self.check("The later order EO 15000 revoked EO 12000.")
        self.assertEqual(row["flags"], [])
        row = self.check("Executive Order 14000 amended this order.")
        self.assertEqual([f["actor"] for f in row["flags"]], ["EO:14000"])

    def test_explicit_later_list_and_missing_source(self):
        row = self.check("EO 14000 and EO 14001 amend the code and are later events, not ends.")
        self.assertEqual({f["actor"] for f in row["flags"]}, {"EO:14000", "EO:14001"})
        row = self.check("Proclamation No. 2416 renamed this refuge.", [{"actor": "PROC:2416"}])
        self.assertTrue(any(f["code"] == "recorded_later_event_source_missing" for f in row["flags"]))

    def test_other_section_discussion_is_not_own_event(self):
        for text in ("EO 14000 amended other sections of the parent order.",
                     "EO 14000 amended section 9, so subsection (h) was not changed by it.",
                     "Later orders amended the parent but did not amend section 4; EO 14000 does not name section 4."):
            self.assertEqual(self.check(text)["flags"], [])


class NameInventory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.textpath = "jobs/app-executive-orders/output/texts/other.txt"
        path = self.repo / self.textpath
        path.parent.mkdir(parents=True)
        self.text = "Executive Order 14000. The Cotton Textile Industry is named here."
        path.write_text(self.text)
        self.index = self.repo / "jobs/app-executive-orders/output/INDEX.jsonl"
        self.index.write_text(json.dumps({"instrument_id": "EO:14000", "date": "1934-12-27",
            "title": "Executive Order 14000—Cotton Textile Industry", "path": "/documents/other", "url": "https://www.presidency.ucsb.edu/documents/other"}) + "\n")
        for args in (("init", "-q"), ("add", "."), ("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")):
            subprocess.run(["git", *args], cwd=self.repo, capture_output=True, check=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_proper_name_positive_is_source_bound(self):
        claim = {"instrument_id": "EO:12345", "research_rationale": "No other held order names Cotton Textile Industry."}
        row = N.check(claim, {}, self.repo)
        flag = row["flags"][0]
        self.assertEqual(flag["code"], "literal_name_counterexample")
        self.assertEqual(flag["counterexamples"][0]["text_sha256"], hashlib.sha256(self.text.encode()).hexdigest())
        self.assertTrue(row["coverage_gaps"][0]["full_discovered_corpus_covered"])

    def test_deictic_phrase_is_not_a_name(self):
        claim = {"instrument_id": "EO:12345", "research_rationale": "No other held order names this code."}
        row = N.check(claim, {}, self.repo)
        self.assertFalse(row["flags"])
        self.assertEqual(row["coverage_gaps"][0]["code"], "literal_name_unresolved")

    def test_industry_alias_requires_code_context(self):
        claim = {"instrument_id": "EO:12345", "research_rationale": "No other held order names Cotton Textile Code."}
        row = N.check(claim, {}, self.repo)
        self.assertFalse(row["flags"])
        self.assertTrue(any(g["code"] == "name_alias_entity_unverified" for g in row["coverage_gaps"]))
        (self.repo / self.textpath).write_text("Executive Order 14000. Under the Codes of Fair Competition for the Cotton Textile Industry.")
        subprocess.run(["git", "add", "."], cwd=self.repo, capture_output=True, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "code context"], cwd=self.repo, capture_output=True, check=True)
        self.assertEqual(N.check(claim, {}, self.repo)["flags"][0]["code"], "literal_name_counterexample")

    def test_changed_source_with_restored_stat_cannot_use_cache(self):
        cache = {}
        N.scan_names(None, ["Cotton Textile"], self.repo, cache)
        path = self.repo / self.textpath; stat = path.stat()
        path.write_text(self.text.replace("Cotton", "Xotton"))
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        hits, failures, count, scope = N.scan_names(None, ["Cotton Textile"], self.repo, cache)
        self.assertFalse(hits["Cotton Textile"])
        self.assertFalse(scope["full_discovered_corpus_covered"])
        self.assertTrue(failures)

    def test_snapshot_refuses_changed_bytes_at_exit(self):
        with self.assertRaisesRegex(ValueError, "changed during"):
            with N.Snapshot(self.repo) as cache:
                N.scan_names(None, ["Cotton Textile"], self.repo, cache)
                (self.repo / self.textpath).write_text(self.text.replace("Cotton", "Xotton"))

    def test_missing_member_prevents_negative_even_with_equal_counts(self):
        (self.repo / self.textpath).unlink()
        hits, failures, count, scope = N.scan_names(None, ["Cotton Textile"], self.repo)
        self.assertFalse(scope["full_discovered_corpus_covered"])
        self.assertEqual(scope["missing_files"], 1)


if __name__ == "__main__":
    unittest.main()
