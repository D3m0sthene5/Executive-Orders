import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trajectory as T  # noqa: E402

HEAD = ("instrument_id,provisional_status,ready_for_human_review,claim_present,blockers,step_provisional_status,"
        "step_original_text,step_clause_inventory,step_ending_or_current_basis,step_savings_residuals,"
        "step_counterevidence,step_shared_sources,step_opus_media\n")


class Units(unittest.TestCase):
    def test_credit(self):
        self.assertEqual(T.credit("original_text", "done", []), 1.0)
        self.assertEqual(T.credit("original_text", "provisional", []), T.PROVISIONAL)
        self.assertEqual(T.credit("original_text", "open", ["ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK"]), 0.4)
        self.assertEqual(T.credit("clause_inventory", "open", ["CLAIM_NOT_YET_CHECKED"]), 0.8)
        self.assertEqual(T.credit("clause_inventory", "open", ["CLAIM_INCOMPLETE:clause_inventory"]), 0.4)
        self.assertEqual(T.credit("provisional_status", "open", ["CLAIM_NOT_YET_CHECKED"]), 0.0)
        self.assertLessEqual(T.credit("clause_inventory", "open", ["CLAIM_NOT_YET_CHECKED"], "high"), 0.95)

    def test_classify(self):
        self.assertEqual(T.classify("Merge pull request #164 from D3m0sthene5/claude/mabillon-register")[:3],
                         ("merge", "claude", "Mabillon"))
        self.assertEqual(T.classify("Merge #174 COUNT-CHANGING (Justinian C3, R3/R8): x [Dorotheus]")[2], "Justinian")
        self.assertEqual(T.classify("Integrate PRs 131-137 and the Tribonian production run (#138)")[2], "Tribonian")
        self.assertEqual(T.classify("Results of job(s): later-events kean")[0], "machine")
        self.assertEqual(T.classify("Niebuhr: results b06")[:3], ("commit", "", "Niebuhr"))

    def test_mission_clock(self):
        self.assertEqual(T.mission(0.0), (0.0, "Earth orbit"))
        self.assertEqual(T.mission(0.3645)[1], "Translunar coast")
        self.assertEqual(T.mission(1.0)[1], "First step")


class EndToEnd(unittest.TestCase):
    def git(self, root, *a):
        subprocess.run(["git", "-C", root, *a], check=True, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t"})

    def write(self, root, rel, text):
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(text)

    def test_history_credit_and_order(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as out:
            self.git(root, "init", "-q", "-b", "main")
            self.write(root, T.PATH, HEAD + "EO:1,,no,no,NO_OFFICIAL_SOURCE_LOCATED,open,open,open,open,open,open,n/a,n/a\n")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-q", "-m", "Results of job(s): readiness-tracker")
            # a merge that adds a claim file, then the tracker reading it produced
            self.git(root, "checkout", "-q", "-b", "claude/gratian-wiring")
            self.write(root, "research/readiness/claims/c.jsonl", "{}\n")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-q", "-m", "claims")
            self.git(root, "checkout", "-q", "main")
            self.git(root, "merge", "-q", "--no-ff", "-m", "Merge pull request #5 from o/claude/gratian-wiring", "claude/gratian-wiring")
            self.write(root, T.PATH, HEAD + "EO:1,no,no,yes,CLAIM_NOT_YET_CHECKED,done,open,open,open,open,open,n/a,n/a\n")
            self.git(root, "add", "-A")
            self.git(root, "commit", "-q", "-m", "Results of job(s): claim-checker readiness-tracker")
            T.build(root, out)
            with open(os.path.join(out, "GENERATION_POINTS.csv")) as fh:
                pts = list(csv.DictReader(fh))
            self.assertEqual(len(pts), 2)
            self.assertLess(float(pts[0]["W_hours"]), float(pts[1]["W_hours"]))
            with open(os.path.join(out, "CAMPAIGNS.csv")) as fh:
                camp = {r["credited_to"]: r for r in csv.DictReader(fh)}
            self.assertIn("Gratian", camp)  # claim steps credited to the merge that touched claims
            self.assertTrue(any(k.startswith("Launch pad") for k in camp))
            self.assertNotIn("machine:readiness-tracker", camp)  # an instrument is never credited
            s = json.load(open(os.path.join(out, "SUMMARY.json")))
            self.assertEqual(s["generations"], 2)


if __name__ == "__main__":
    unittest.main()
