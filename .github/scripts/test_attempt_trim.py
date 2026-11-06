"""Failed-attempt receipts stay small: big files move to the run download with their size and SHA-256."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_jobs  # noqa: E402


class AttemptTrimTest(unittest.TestCase):
    def test_small_kept_big_moved_and_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt, over = Path(tmp) / "jobs/_attempts/x/1", Path(tmp) / "oversized/x/attempt/1"
            (attempt / "sub").mkdir(parents=True)
            (attempt / "log.txt").write_text("boom\n")
            (attempt / "STATUS.json").write_text("{}")
            big = b"z" * (run_jobs.ATTEMPT_FILE_BYTES + 1)
            (attempt / "sub/BIG.jsonl").write_bytes(big)
            for i in range(12):        # 12 x 0.9 MiB: only some fit under the 8 MiB total
                (attempt / f"part{i:02d}.jsonl").write_bytes(b"a" * 900_000)
            moved = run_jobs.trim_attempt(attempt, over)
            kept = sum(f.stat().st_size for f in attempt.rglob("*") if f.is_file() and f.name != "ATTEMPT_TRIMMED.json")
            self.assertLessEqual(kept, run_jobs.ATTEMPT_TOTAL_BYTES)
            self.assertTrue((attempt / "log.txt").exists() and (attempt / "STATUS.json").exists())
            self.assertFalse((attempt / "sub/BIG.jsonl").exists())
            self.assertEqual((over / "sub/BIG.jsonl").read_bytes(), big)
            listed = json.loads((attempt / "ATTEMPT_TRIMMED.json").read_text())["moved_to_run_download"]
            self.assertEqual(len(listed), len(moved))
            row = [r for r in listed if r["path"] == "sub/BIG.jsonl"][0]
            self.assertEqual(row["sha256"], hashlib.sha256(big).hexdigest())
            self.assertEqual(row["bytes"], len(big))
            self.assertGreater(len(moved), 1)

    def test_small_attempt_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = Path(tmp) / "a"
            attempt.mkdir()
            (attempt / "log.txt").write_text("x")
            self.assertEqual(run_jobs.trim_attempt(attempt, Path(tmp) / "o"), [])
            self.assertFalse((attempt / "ATTEMPT_TRIMMED.json").exists())


if __name__ == "__main__":
    unittest.main()
