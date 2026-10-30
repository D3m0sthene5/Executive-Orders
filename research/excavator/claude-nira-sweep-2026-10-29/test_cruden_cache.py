"""Focused source/cache invariants; synthetic fixtures, no legal assertions."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cruden_test_target", HERE / "cruden.py")
cruden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cruden)
from cruden_cache import Snapshot, SnapshotChanged, normalized, original_span  # noqa: E402


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cruden-cache-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.folder = self.repo / "jobs/held/output/texts"
        self.folder.mkdir(parents=True)
        self.a = self.folder / "a.txt"
        self.b = self.folder / "b.txt"
        self.a.write_bytes(b"Executive Order No. 6242-C\r\n")
        self.b.write_text("Unrelated 1970", encoding="utf-8")
        self.env = patch.dict(os.environ, {"CRUDEN_CACHE_DIR": str(self.root / "cache")})
        self.env.start()
        self.addCleanup(self.env.stop)

    def discover(self):
        return iter(sorted(self.folder.rglob("*.txt")))

    def snapshot(self):
        return Snapshot(self.repo, self.discover)

    def test_warm_reuses_only_features_and_hashes_all_bytes_twice(self):
        first = self.snapshot()
        first.verify()
        second = self.snapshot()
        second.verify()
        self.assertEqual(second.stats["reused_sources"], 2)
        self.assertEqual(second.stats["recomputed_sources"], 0)
        byte_count = self.a.stat().st_size + self.b.stat().st_size
        self.assertEqual(second.stats["bytes_read"], byte_count)
        self.assertEqual(second.stats["validation_bytes_read"], byte_count)
        self.assertEqual(second.snapshot_sha256, first.snapshot_sha256)

    def test_same_size_preserved_mtime_edit_add_delete(self):
        first = self.snapshot()
        first.verify()
        old_stat = self.b.stat()
        self.b.write_text("Unrelated 6242", encoding="utf-8")
        os.utime(self.b, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
        self.a.unlink()
        added = self.folder / "nested/new.txt"
        added.parent.mkdir()
        added.write_text("Executive Order No. 6242", encoding="utf-8")
        second = self.snapshot()
        second.verify()
        self.assertEqual(second.stats["recomputed_sources"], 2)
        self.assertEqual(len(list(second.candidates(["6242"]))), 2)
        self.assertNotEqual(second.snapshot_sha256, first.snapshot_sha256)

    def test_corrupt_valid_json_posting_omission_rebuilds(self):
        first = self.snapshot()
        first.verify()
        envelope = json.loads(first.cache_path.read_text())
        envelope["payload"]["sources"][0]["digits"] = []
        first.cache_path.write_text(json.dumps(envelope))
        second = self.snapshot()
        self.assertEqual(second.stats["cache_state"], "rebuild")
        self.assertEqual(second.stats["recomputed_sources"], 2)
        self.assertEqual(len(list(second.candidates(["6242"]))), 1)

    def test_corrupt_prefix_omission_rebuilds(self):
        self.a.write_text("Code of Fair Competition for the Widget Industry", encoding="utf-8")
        first = self.snapshot()
        first.verify()
        envelope = json.loads(first.cache_path.read_text())
        envelope["payload"]["sources"][0]["code_prefix"] = False
        first.cache_path.write_text(json.dumps(envelope))
        second = self.snapshot()
        self.assertEqual(second.stats["cache_state"], "rebuild")
        self.assertEqual(len(list(second.candidates(codes=True))), 1)

    def test_non_candidate_mutation_during_scan_refuses(self):
        snapshot = self.snapshot()
        old_stat = self.b.stat()
        self.b.write_text("Unrelated 6242", encoding="utf-8")
        os.utime(self.b, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
        with self.assertRaises(SnapshotChanged):
            snapshot.verify()
        self.assertFalse(snapshot.cache_path.exists())

    def test_inventory_mutation_refuses(self):
        snapshot = self.snapshot()
        (self.folder / "new.txt").write_text("new")
        with self.assertRaises(SnapshotChanged):
            snapshot.verify()

    def test_candidate_mutation_refuses(self):
        snapshot = self.snapshot()
        self.a.write_text("Executive Order No. 6242-D", encoding="utf-8")
        with self.assertRaises(SnapshotChanged):
            snapshot.read_source(next(snapshot.candidates(["6242"])))

    def test_unreadability_is_not_cached_away(self):
        original = Snapshot.read_raw
        def unreadable(obj, path):
            if path == self.b:
                raise PermissionError("fixture unreadable")
            return original(obj, path)
        with patch.object(Snapshot, "read_raw", unreadable):
            snapshot = self.snapshot()
            snapshot.verify()
            self.assertEqual(snapshot.coverage["readable_count"], 1)
            self.assertEqual(len(snapshot.coverage["unreadable_sources"]), 1)
        second = self.snapshot()
        second.verify()
        self.assertEqual(second.coverage["readable_count"], 2)
        self.assertEqual(second.stats["recomputed_sources"], 1)

    def test_cache_write_failure_keeps_sources(self):
        blocker = self.root / "blocked"
        blocker.write_text("file, not directory")
        with patch.dict(os.environ, {"CRUDEN_CACHE_DIR": str(blocker)}):
            snapshot = self.snapshot()
            snapshot.verify()
        self.assertEqual(len(list(snapshot.candidates(["6242"]))), 1)
        self.assertTrue(snapshot.stats["cache_errors"])

    def test_normalization_and_unicode_lower_expansion_spans(self):
        self.assertEqual(normalized(b"a\r\nb\rc\n\xff"), "a\nb\nc\n\ufffd")
        text = "\u0130 before Code of Fair Competition for the Widget Industry"
        lower = text.lower()
        needle = "code of fair competition for the widget"
        start = lower.index(needle)
        a, b = original_span(text, lower, start, start + len(needle))
        self.assertEqual(text[a:b], "Code of Fair Competition for the Widget")

    def test_general_number_and_literal_match_source_spans(self):
        old_repo = cruden.REPO
        cruden.REPO = self.repo
        self.addCleanup(setattr, cruden, "REPO", old_repo)
        self.b.write_text("\u0130 Fitness of American Youth\rFitness of American Youth", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            number = cruden.source_search("number", ["EO:6242C", "EO:6242", "EO:6242C", "EO:6242C\n"])
            literal = cruden.source_search("literal", ["Fitness of American Youth", "Fitness of American Youth"])
        self.assertEqual(number["queries"]["EO:6242C"]["matches"], 1)
        self.assertEqual(number["queries"]["EO:6242"]["matches"], 0)
        self.assertEqual(number["queries"]["EO:6242C\n"]["matches"], 1)
        entry = literal["queries"]["Fitness of American Youth"]
        self.assertEqual(entry["matches"], 2)
        text = self.b.read_text(encoding="utf-8")
        for hit in entry["hits"]:
            self.assertEqual(text[hit["char_start"]:hit["char_end"]], hit["match"])


if __name__ == "__main__":
    unittest.main()
