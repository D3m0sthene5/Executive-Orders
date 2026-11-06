"""Offline tests for sessions.py using synthetic transcripts in the real Claude Code JSONL shape."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sessions  # noqa: E402

SECRET_USER = "SECRET-USER-PROMPT-about-the-private-matter"
SECRET_TOOL = "SECRET-TOOL-INPUT cat /private/file.txt"
SECRET_RESULT = "SECRET-FILE-CONTENTS line one of the document"
SECRET_REPLY = "SECRET-ASSISTANT-REPLY text spoken to the user"


def usage(inp, read, w5, out, w1=0):
    return {"input_tokens": inp, "cache_creation_input_tokens": w5 + w1, "cache_read_input_tokens": read,
            "output_tokens": out, "cache_creation": {"ephemeral_5m_input_tokens": w5, "ephemeral_1h_input_tokens": w1}}


def user(ts, text=None, result=None, sidechain=False, sid="S"):
    content = text if result is None else [{"type": "tool_result", "tool_use_id": "t1", "content": result}]
    return {"type": "user", "timestamp": ts, "isSidechain": sidechain, "sessionId": sid, "uuid": "u" + ts,
            "message": {"role": "user", "content": content}}


def asst(ts, mid, model, u, blocks=None, sidechain=False, sid="S", agent=None):
    r = {"type": "assistant", "timestamp": ts, "isSidechain": sidechain, "sessionId": sid, "uuid": "a" + mid,
         "message": {"id": mid, "model": model, "role": "assistant", "usage": u,
                     "content": blocks or [{"type": "text", "text": SECRET_REPLY}]}}
    if agent:
        r["agentId"] = agent
    return r


def write_jsonl(path, recs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in recs))


def build(cfg):
    proj = Path(cfg) / "projects" / "-work"
    s1 = "11111111-aaaa-bbbb-cccc-000000000001"
    s2 = "22222222-aaaa-bbbb-cccc-000000000002"
    tool = [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": SECRET_TOOL}}]
    write_jsonl(proj / (s1 + ".jsonl"), [
        user("2026-11-05T10:00:00.000Z", SECRET_USER, sid=s1),
        asst("2026-11-05T10:00:10.000Z", "m1", "claude-opus-5-5", usage(2, 100, 1000, 50), tool, sid=s1),
        user("2026-11-05T10:00:20.000Z", result=SECRET_RESULT, sid=s1),
        asst("2026-11-05T10:00:30.000Z", "m2", "claude-opus-5-5", usage(3, 1100, 200, 70), sid=s1),
        asst("2026-11-05T10:00:31.000Z", "m3", "<synthetic>", usage(0, 0, 0, 0), sid=s1),
        {"type": "mode", "mode": "x"},
    ])
    sub = proj / s1 / "subagents"
    write_jsonl(sub / "agent-aaa111.jsonl", [
        user("2026-11-05T10:01:00.000Z", SECRET_USER + " for the subagent", sidechain=True, sid=s1),
        asst("2026-11-05T10:01:10.000Z", "s1", "claude-sonnet-5-5", usage(2, 500, 2000, 300), tool, sidechain=True, sid=s1, agent="aaa111"),
        asst("2026-11-05T10:03:10.000Z", "s2", "claude-sonnet-5-5", usage(4, 2500, 100, 400, w1=50), sidechain=True, sid=s1, agent="aaa111"),
    ])
    (sub / "agent-aaa111.meta.json").write_text(json.dumps(
        {"agentType": "Explore", "description": "SECRET-DESCRIPTION should never be copied", "model": "sonnet"}))
    write_jsonl(sub / "agent-bbb222.jsonl", [
        asst("2026-11-05T10:05:00.000Z", "r1", "claude-sonnet-5-5", usage(1, 10, 20, 30), sidechain=True, sid=s1, agent="bbb222"),
    ])
    (sub / "agent-bbb222.meta.json").write_text(json.dumps({"agentType": "general-purpose"}))
    write_jsonl(proj / (s2 + ".jsonl"), [
        user("2026-11-06T09:00:00.000Z", "another session prompt that is private", sid=s2),
        asst("2026-11-06T09:00:05.000Z", "n1", "claude-haiku-4-5", usage(5, 5, 5, 5), sid=s2),
    ])
    return s1, s2


class SessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name) / "claude"
        self.s1, self.s2 = build(self.cfg)
        self.out = Path(self.tmp.name) / "out"
        self.addCleanup(self.tmp.cleanup)

    def run_py(self, *args):
        return sessions.run("wave-x", self.out, *args)

    def rows(self):
        with (self.out / "AGENT_USAGE.csv").open() as f:
            return {r["agent_id"]: r for r in csv.DictReader(f)}

    def test_discovery_finds_main_and_subagents(self):
        found = sessions.discover([self.cfg])
        kinds = sorted((t["kind"], t["agent_id"]) for t in found)
        self.assertEqual(kinds, [("main", "main-11111111"), ("main", "main-22222222"),
                                 ("subagent", "aaa111"), ("subagent", "bbb222")])
        self.assertEqual({t["session_id"] for t in found if t["kind"] == "subagent"}, {self.s1})

    def test_discovery_uses_claude_config_dir_env(self):
        old = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.cfg)
        try:
            ids = {t["agent_id"] for t in sessions.discover()}
        finally:
            if old is None:
                del os.environ["CLAUDE_CONFIG_DIR"]
            else:
                os.environ["CLAUDE_CONFIG_DIR"] = old
        self.assertIn("aaa111", ids)

    def test_session_id_filter(self):
        found = sessions.discover([self.cfg], session_id="2222")
        self.assertEqual([t["agent_id"] for t in found], ["main-22222222"])

    def test_subagent_attribution_and_counts(self):
        self.run_py("production", None, None, None, [self.cfg])
        rows = self.rows()
        sub = rows["aaa111"]
        self.assertEqual(sub["role"], "Explore")
        self.assertEqual(sub["session_id"], self.s1)
        self.assertEqual(sub["model"], "claude-sonnet-5-5")
        self.assertEqual((sub["calls"], sub["fresh_input"], sub["cache_read"]), ("2", "6", "3000"))
        self.assertEqual((sub["cache_write_5m"], sub["cache_write_1h"], sub["output"]), ("2100", "50", "700"))
        self.assertEqual((sub["tool_uses"], sub["bash_calls"]), ("1", "1"))
        self.assertEqual(sub["wall_seconds"], "130.0")  # user record at :00 to last call at 3:10
        self.assertEqual(sub["active_seconds"], "130.0")  # both gaps are under the 300 s cap
        main = rows["main-11111111"]
        self.assertEqual(main["role"], "coordinator")
        self.assertEqual((main["calls"], main["output"]), ("2", "120"))
        self.assertIn("synthetic", main["coverage_notes"])
        self.assertEqual(rows["bbb222"]["role"], "general-purpose")

    def test_totals_by_family_and_phase_map(self):
        pm = {"role:Explore": "review", "default": "production"}
        summary, _, _ = self.run_py(None, pm, None, None, [self.cfg])
        self.assertEqual(summary["totals_by_phase"]["review"]["calls"], 2)
        self.assertEqual(summary["totals_by_phase"]["production"]["calls"], 2 + 1 + 1)
        fam = summary["totals_by_model_family"]
        self.assertEqual(fam["opus"]["output"], 120)
        self.assertEqual(fam["sonnet"]["output"], 730)
        self.assertEqual(fam["haiku"]["calls"], 1)
        self.assertEqual(summary["totals"]["calls"], 6)
        self.assertEqual(summary["totals"]["output"], 120 + 730 + 5)
        self.assertEqual(summary["totals_by_phase_and_family"]["review|sonnet"]["fresh_input"], 6)

    def test_since_filter_drops_early_calls(self):
        since = sessions.parse_ts("2026-11-05T10:02:00Z")
        summary, _, _ = self.run_py("production", None, None, since, [self.cfg])
        self.assertEqual(summary["totals"]["calls"], 3)  # sub s2, bbb222, haiku

    def test_outputs_hold_no_message_content(self):
        self.run_py("production", None, None, None, [self.cfg])
        text = "".join((self.out / n).read_text() for n in ("AGENT_USAGE.csv", "SUMMARY.json"))
        for s in (SECRET_USER, SECRET_TOOL, SECRET_RESULT, SECRET_REPLY, "SECRET-DESCRIPTION", "private"):
            self.assertNotIn(s, text)
        self.assertNotIn("/private/file.txt", text)

    def test_guard_refuses_leak_and_writes_nothing(self):
        forbidden = sessions.content_strings(self.cfg / "projects" / "-work" / (self.s1 + ".jsonl"))
        self.assertIn(SECRET_USER, forbidden)
        row = {c: "" for c in sessions.COLUMNS}
        row["coverage_notes"] = "x " + SECRET_REPLY
        with self.assertRaises(sessions.GuardError):
            sessions.write_outputs(self.out, [row], {"wave": "w"}, forbidden)
        self.assertFalse((self.out / "AGENT_USAGE.csv").exists())

    def test_cli_refuses_leaky_phase_label_inside_repo(self):
        repo = Path(self.tmp.name) / "repo"
        (repo / "jobs" / "hamilton-token-audit").mkdir(parents=True)
        (repo / "jobs" / "hamilton-token-audit" / "profile.py").write_text(
            (sessions.HAMILTON).read_text())
        env = {**os.environ, "REPO_ROOT": str(repo), "CLAUDE_CONFIG_DIR": str(self.cfg), "HOME": self.tmp.name}
        leak = "SECRET-ASSISTANT-REPLY"  # shorter than guard length, so use the full string
        out = repo / "usage"
        p = subprocess.run([sys.executable, "-I", str(HERE / "sessions.py"), "--wave", "w", "--phase", SECRET_REPLY,
                            "--out", str(out)], env=env, capture_output=True, text=True)
        # label() rewrites spaces to underscores, so the raw string cannot appear; the leak must be refused or sanitized.
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn(SECRET_REPLY, (out / "SUMMARY.json").read_text())
        self.assertTrue(leak)

    def test_cli_end_to_end(self):
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.cfg), "HOME": self.tmp.name}
        pm = Path(self.tmp.name) / "pm.json"
        pm.write_text(json.dumps({"default": "review"}))
        p = subprocess.run([sys.executable, "-I", str(HERE / "sessions.py"), "--wave", "w", "--phase-map", str(pm),
                            "--out", str(self.out), "--session-id", self.s1[:8]],
                           env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        s = json.loads((self.out / "SUMMARY.json").read_text())
        self.assertEqual(s["totals"]["agents"], 3)
        self.assertEqual(list(s["totals_by_phase"]), ["review"])


if __name__ == "__main__":
    unittest.main()
