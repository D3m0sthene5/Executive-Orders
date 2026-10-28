"""Offline tests for Kean. Each test builds a throwaway git repository."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kean  # noqa: E402


class KeanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.write("HANDOFF/notes-claude.md", "# notes\n")
        self.write(f"{kean.REGISTER}/legacy_reports.txt", "")
        self.write("jobs/x/tool.py", "msg = 'owner must decide the grade'\n")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *a):
        subprocess.run(["git", *a], cwd=self.root, check=True, capture_output=True)

    def write(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "x", "--allow-empty")

    def run_cli(self, *args):
        return kean.main(["--root", self.root, *args])

    def errors(self):
        return kean.check(kean.Repo(self.root))

    def test_clean_repository_passes_after_brief(self):
        self.run_cli("brief")
        self.commit()
        errors, _ = self.errors()
        self.assertEqual(errors, [])

    def test_stale_brief_fails(self):
        self.run_cli("brief")
        self.write(kean.BRIEF, "edited by hand\n")
        self.commit()
        errors, _ = self.errors()
        self.assertTrue(any("out of date" in e for e in errors))

    def test_ruling_without_decision_fails_until_recorded(self):
        self.write("research/readiness/owner_rulings/2026-10-29-x.md", "# ruling\n")
        self.run_cli("brief")
        self.commit()
        errors, _ = self.errors()
        self.assertTrue(any("owner ruling with no Kean decision" in e for e in errors))
        self.run_cli("add-decision", "--title", "X", "--ruling", "Do X.", "--source",
                     "research/readiness/owner_rulings/2026-10-29-x.md", "--date", "2026-10-29")
        self.commit()
        errors, _ = self.errors()
        self.assertEqual(errors, [])

    def test_report_needs_finding_unless_legacy(self):
        self.write("research/excavator/pilot-1/REPORT.md", "# r\n")
        self.write("research/excavator/pilot-1/packet/REPORT.md", "# nested, not an experiment report\n")
        self.run_cli("brief")
        self.commit()
        errors, _ = self.errors()
        self.assertEqual([e for e in errors if "report with no Kean finding" in e],
                         ["report with no Kean finding: research/excavator/pilot-1/REPORT.md "
                          "(python3 -I jobs/kean/kean.py add-finding ...)"])
        self.write(f"{kean.REGISTER}/legacy_reports.txt", "research/excavator/pilot-1/REPORT.md\n")
        self.run_cli("brief")
        self.commit()
        errors, _ = self.errors()
        self.assertEqual(errors, [])

    def test_owner_ask_in_notes_needs_registered_id(self):
        self.write("HANDOFF/notes-claude.md", "# n\n\n## 2026-10-29 ET: x\n\n- **Asks:** `@Owner`: decide Y.\n")
        self.run_cli("brief")
        self.commit()
        errors, _ = self.errors()
        self.assertTrue(any("without a Kean ask id" in e for e in errors))
        self.run_cli("add-ask", "--question", "Decide Y?", "--why", "Blocks Z.", "--asked-by", "Claude",
                     "--date", "2026-10-29")
        self.write("HANDOFF/notes-claude.md",
                   "# n\n\n## 2026-10-29 ET: x\n\n- **Asks:** `@Owner`: decide Y (A-20261029-1).\n")
        self.commit()
        errors, _ = self.errors()
        self.assertEqual(errors, [])

    def test_old_notes_and_explicit_no_ask_are_exempt(self):
        self.write("HANDOFF/notes-claude.md",
                   "# n\n\n## 2026-10-29: a\n- **Asks:** @Owner: none\n\n## 2026-10-20: b\n- **Asks:** @Owner: old\n")
        self.run_cli("brief")
        self.commit()
        errors, _ = self.errors()
        self.assertEqual(errors, [])

    def test_contradicting_text_is_shown_until_removed(self):
        self.write("research/readiness/owner_rulings/r.md", "# r\n")
        self.run_cli("add-decision", "--title", "Grade", "--ruling", "Scans count provisionally.", "--source",
                     "research/readiness/owner_rulings/r.md", "--wiring", "partly_wired",
                     "--stale-text", "jobs/x/tool.py::owner must decide the grade", "--date", "2026-10-21")
        self.commit()
        brief = open(os.path.join(self.root, kean.BRIEF), encoding="utf-8").read()
        self.assertIn("`jobs/x/tool.py` (D-20261021-1)", brief)
        _, warnings = self.errors()
        self.assertTrue(any("contradicting text" in w for w in warnings))
        # Fixing the wording elsewhere must not fail an unrelated pull request over the brief.
        self.write("jobs/x/tool.py", "msg = 'scans count provisionally'\n")
        self.commit()
        errors, warnings = self.errors()
        self.assertEqual(errors, [])
        self.assertFalse(any("contradicting text" in w for w in warnings))

    def test_answer_moves_question_out_of_open_list(self):
        self.run_cli("add-ask", "--question", "Admit EO 5853?", "--why", "Census gap.", "--asked-by", "Claude",
                     "--date", "2026-10-21")
        brief = open(os.path.join(self.root, kean.BRIEF), encoding="utf-8").read()
        self.assertIn("Waiting for the owner (1)", brief)
        self.run_cli("answer", "--id", "A-20261021-1", "--answer", "Yes.", "--date", "2026-10-29")
        brief = open(os.path.join(self.root, kean.BRIEF), encoding="utf-8").read()
        self.assertIn("Waiting for the owner (0)", brief)
        self.assertIn("1 answered questions", brief)
        rows = [json.loads(l) for l in open(os.path.join(self.root, kean.REGISTER, "asks.jsonl"), encoding="utf-8")]
        self.assertEqual([r["rev"] for r in rows], [0, 1])  # append-only

    def test_missing_source_and_bad_values_fail(self):
        self.run_cli("add-finding", "--tried", "t", "--expected", "e", "--result", "r", "--verdict", "failed",
                     "--lesson", "l", "--by", "Claude", "--source", "research/nowhere.md", "--date", "2026-10-28")
        self.commit()
        errors, _ = self.errors()
        self.assertTrue(any("source not in the repository" in e for e in errors))

    def test_search_finds_register_and_notes(self):
        self.run_cli("add-finding", "--tried", "OCR of handwritten scans with tesseract", "--expected", "text",
                     "--result", "noise", "--verdict", "failed", "--lesson", "use vision reading", "--by", "Claude",
                     "--source", "https://example.com", "--date", "2026-10-28")
        self.write("HANDOFF/notes-astra.md", "Tried handwritten OCR bake-off here.\n")
        self.commit()
        hits, _ = kean.search(kean.Repo(self.root), ["handwritten", "ocr"])
        where = [h[1] for h in hits]
        self.assertEqual(where[0], "[findings] F-20261028-1")
        self.assertIn("HANDOFF/notes-astra.md", where)

    def test_brief_stays_small_as_results_accumulate(self):
        for k in range(60):
            kean.append(kean.Repo(self.root), "findings", {
                "id": f"F-20261028-{k + 1}", "rev": 0, "date": "2026-10-28", "by": "Claude", "tried": "t " * 40,
                "expected": "e", "result": "r " * 40, "verdict": "failed", "lesson": "lesson " * 60,
                "sources": ["https://example.com"]})
        self.run_cli("brief")
        self.commit()
        size = os.path.getsize(os.path.join(self.root, kean.BRIEF))
        self.assertLess(size, kean.BRIEF_MAX_BYTES)
        errors, _ = self.errors()
        self.assertEqual(errors, [])
        hits, _ = kean.search(kean.Repo(self.root), ["lesson"])
        self.assertEqual(len(hits), 8)  # search output is capped too

    def test_pinned_requirements_appear_in_every_brief(self):
        self.write("research/readiness/owner_rulings/r.md", "# r\n")
        self.run_cli("add-decision", "--title", "Standing requirements", "--ruling", "Never count a label as a history.",
                     "--source", "research/readiness/owner_rulings/r.md", "--wiring", "no_wiring_needed", "--pinned",
                     "--date", "2026-10-28")
        brief = open(os.path.join(self.root, kean.BRIEF), encoding="utf-8").read()
        self.assertIn("## Standing owner requirements", brief)
        self.assertIn("Never count a label as a history.", brief)

    def test_ids_increment_per_day(self):
        for q in ("a", "b"):
            self.run_cli("add-ask", "--question", q, "--why", "w", "--asked-by", "Claude", "--date", "2026-10-28")
        ids = [r["id"] for r in kean.current(kean.load(kean.Repo(self.root), "asks"))]
        self.assertEqual(ids, ["A-20261028-1", "A-20261028-2"])


if __name__ == "__main__":
    unittest.main()
