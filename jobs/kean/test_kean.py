"""Offline tests for Kean. Each test builds a throwaway git repository."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_newest_and_asks_pages(self):
        # Justinian B1/B2: NEWEST.md holds each notes file's first "## " block; the brief lists ask ids only.
        self.write("HANDOFF/notes-claude.md", "# notes\n\n## 2026-11-06: newest\n\n- done\n\n## 2026-11-05: older\n\n- old\n")
        self.run_cli("add-ask", "--question", "May we freeze merges for four hours?", "--why", "one chain publishes",
                     "--asked-by", "t", "--id", "A-20261106-test-freeze")
        self.run_cli("brief")
        self.commit()
        root = self.root
        newest = open(os.path.join(root, kean.NEWEST_PAGE), encoding="utf-8").read()
        self.assertIn("2026-11-06: newest", newest)
        self.assertNotIn("2026-11-05: older", newest)
        brief = open(os.path.join(root, kean.BRIEF), encoding="utf-8").read()
        self.assertIn("A-20261106-test-freeze", brief)
        self.assertNotIn("May we freeze", brief)
        asks = open(os.path.join(root, kean.ASKS_PAGE), encoding="utf-8").read()
        self.assertIn("May we freeze merges for four hours?", asks)
        errors, warnings = self.errors()
        self.assertEqual(errors, [])
        self.write(kean.ASKS_PAGE, "edited\n")
        errors, _ = self.errors()
        self.assertTrue(any("KEAN_ASKS.md is out of date" in e for e in errors))
        self.assertEqual(kean.BRIEF_MAX_BYTES, 16384)

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


class ChainHealthTest(unittest.TestCase):
    """Gutenberg item 4: Davy's verdict appears at the top of the brief; absent or malformed files show nothing."""

    def test_line(self):
        import tempfile, json as _j
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import kean as K
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(K.chain_health(t))
            p = Path(t) / K.HEALTH
            p.parent.mkdir(parents=True)
            p.write_text("{bad")
            self.assertIsNone(K.chain_health(t))
            p.write_text(_j.dumps({"verdict": "fail", "summary": "FAIL in drafts - Draft summary population stale",
                                   "checked_utc": "2026-11-09T06:00:00Z", "input_commit": "abc"}))
            line = K.chain_health(t)
            self.assertIn("Chain health (FAIL", line)
            self.assertIn("Draft summary population stale", line)
            self.assertIn("before preparing a paid batch", line)


class MeasuresTest(unittest.TestCase):
    """Gutenberg item 5: optional structured numbers on findings; old findings stay valid."""

    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import kean as K
        self.K = K
        self.ok = {"wave": "cujas-2026-11-08",
                   "usd": {"total": 23.27, "by_role": {"coordinator": 7.83, "worker": 15.44},
                           "by_model": {"claude-opus-5-5": 20.22, "claude-sonnet-5-5": 3.05}, "basis": "mixed"},
                   "orders": {"attempted": 75, "submitted": 73, "filed": 68}, "controls": {"planted": 6, "missed": 0}}

    def test_absent_and_valid(self):
        self.assertEqual(self.K.validate_measures(None), [])
        self.assertEqual(self.K.validate_measures(self.ok), [])
        self.assertEqual(self.K.validate_measures({"wave": "w1", "usd": {"total": 1, "basis": "list_price"}}), [])

    def test_each_refusal(self):
        import copy
        cases = [
            (lambda m: m.update(extra=1), "unknown key extra"),
            (lambda m: m.update(wave="Cujas wave"), "slug"),
            (lambda m: m["usd"].update(basis="guess"), "basis"),
            (lambda m: m["usd"].update(total=-1), "nonnegative"),
            (lambda m: m["usd"]["by_role"].update(coordinator=99), "sums to"),
            (lambda m: m["orders"].update(filed=80), "attempted >= submitted >= filed"),
            (lambda m: m["controls"].update(missed=7), "planted >= missed"),
            (lambda m: m["orders"].update(filed=1.5), "integers"),
            (lambda m: m["usd"].pop("total") and m["usd"].pop("by_role") and m["usd"].pop("by_model"), "needs total"),
        ]
        for mutate, needle in cases:
            m = copy.deepcopy(self.ok)
            mutate(m)
            errs = self.K.validate_measures(m)
            self.assertTrue(any(needle in e for e in errs), (needle, errs))

    def test_wave_measures_newest_valid_revision(self):
        rows = [{"id": "F-1", "rev": 0, "date": "2026-11-08", "measures": dict(self.ok)},
                {"id": "F-1", "rev": 1, "date": "2026-11-08", "measures": dict(self.ok, note="revised")},
                {"id": "F-2", "rev": 0, "date": "2026-11-09", "measures": {"wave": "bad wave"}},
                {"id": "F-3", "rev": 0, "date": "2026-11-09"}]
        w = self.K.wave_measures(rows)
        self.assertEqual(list(w), ["cujas-2026-11-08"])
        self.assertEqual(w["cujas-2026-11-08"]["note"], "revised")
        self.assertEqual(w["cujas-2026-11-08"]["finding"], "F-1")

    def test_real_register_checks_clean(self):
        root = Path(__file__).resolve().parents[2]
        errors, _ = self.K.check(self.K.Repo(str(root)))
        self.assertEqual([e for e in errors if "measures" in e], [])


if __name__ == "__main__":
    unittest.main()


class AskIdPattern(unittest.TestCase):
    def test_numbered_and_session_named_ids(self):
        import kean as k
        line = "@Owner: see A-20261105-1, A-20261106-mabillon-register and A-20261105-niebuhr-admit."
        self.assertEqual(k.ASK_ID_RE.findall(line), ["A-20261105-1", "A-20261106-mabillon-register", "A-20261105-niebuhr-admit"])
        self.assertEqual(k.ASK_ID_RE.findall("D-20261105-brave-paid-search F-20261105-x"), [])
