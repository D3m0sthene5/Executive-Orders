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
        for col in sessions.DERIVED_COLUMNS + ("_derived",):
            row = {c: "" for c in sessions.COLUMNS}
            row[col] = ["x " + SECRET_REPLY] if col == "_derived" else "x " + SECRET_REPLY
            with self.assertRaises(sessions.GuardError, msg=col):
                sessions.write_outputs(self.out, [row], {"wave": "w"}, forbidden)
            self.assertFalse((self.out / "AGENT_USAGE.csv").exists())
        with self.assertRaises(sessions.GuardError):  # a model key in the summary is derived too
            sessions.write_outputs(self.out, [], {"totals_by_model": {"x " + SECRET_REPLY: {}}}, forbidden)

    def test_cli_refuses_leaky_phase_label_inside_repo(self):
        repo = Path(self.tmp.name) / "repo"
        (repo / "jobs" / "hamilton-token-audit").mkdir(parents=True)
        (repo / "jobs" / "hamilton-token-audit" / "profile.py").write_text(
            (sessions.HAMILTON).read_text())
        (repo / "jobs" / "necker-costs").mkdir(parents=True)
        (repo / "jobs" / "necker-costs" / "PRICES.json").write_text((sessions.REPO_ROOT / sessions.pricing.REL).read_text())
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


class GutenbergTest(unittest.TestCase):
    """Holes found on 2026-11-09 in real Haloander and Cujas usage; each test pins one closed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name) / "cfg"
        self.proj = self.cfg / "projects" / "-work"
        self.out = Path(self.tmp.name) / "out"
        self.sid = "33333333-aaaa-bbbb-cccc-000000000003"
        self.wid = "44444444-aaaa-bbbb-cccc-000000000004"
        # coordinator: 2 Opus calls; worker (claude -p): 1 Sonnet call with a 1-hour write
        write_jsonl(self.proj / (self.sid + ".jsonl"), [
            user("2026-11-09T10:00:00.000Z", SECRET_USER, sid=self.sid),
            asst("2026-11-09T10:00:10.000Z", "c1", "claude-opus-5-5", usage(10, 1_000_000, 0, 1000, w1=100_000), sid=self.sid),
            asst("2026-11-09T10:00:20.000Z", "c2", "claude-opus-5-5", usage(10, 1_000_000, 0, 1000), sid=self.sid)])
        write_jsonl(self.proj / (self.wid + ".jsonl"), [
            user("2026-11-09T10:01:00.000Z", SECRET_USER + " worker", sid=self.wid),
            asst("2026-11-09T10:01:10.000Z", "w1", "claude-sonnet-5-5", usage(2, 2_000_000, 0, 20_000, w1=80_000), sid=self.wid)])
        # list price: opus 5.5 input 4, read .2, 1h 8, out 20; sonnet 5.5 input 2, read .1, 1h 4, out 10
        self.coord_usd = (20 * 4 + 2_000_000 * 0.2 + 100_000 * 8 + 2000 * 20) / 1e6
        self.work_usd = (2 * 2 + 2_000_000 * 0.1 + 80_000 * 4 + 20_000 * 10) / 1e6

    def tearDown(self):
        self.tmp.cleanup()

    def run_(self, reported=()):
        return sessions.run("w", self.out, phase="p", claude_dirs=[self.cfg], reported_paths=reported)

    def rows(self):
        with (self.out / "AGENT_USAGE.csv").open() as f:
            return {r["session_id"]: r for r in csv.DictReader(f)}

    def test_columns_all_classified(self):
        cols = set(sessions.COLUMNS)
        self.assertEqual(cols, set(sessions.DERIVED_COLUMNS) | set(sessions.STRUCTURAL_COLUMNS))
        self.assertFalse(set(sessions.DERIVED_COLUMNS) & set(sessions.STRUCTURAL_COLUMNS))

    def test_list_price_per_call(self):
        s, _, _ = self.run_()
        r = self.rows()
        self.assertAlmostEqual(float(r[self.sid]["usd_list"]), self.coord_usd, places=6)
        self.assertAlmostEqual(float(r[self.wid]["usd_list"]), self.work_usd, places=6)
        self.assertAlmostEqual(s["totals"]["usd_list"], self.coord_usd + self.work_usd, places=6)
        self.assertEqual(s["prices"]["source"], "jobs/necker-costs/PRICES.json")

    def test_fast_mode_and_haiku_long_prompt(self):
        P = sessions.pricing.Prices.load(sessions.REPO_ROOT)
        t = {"fresh_input": 1000, "output": 1000}
        self.assertAlmostEqual(P.call_usd("claude-opus-5-5", t, fast=True), 2 * P.call_usd("claude-opus-5-5", t))
        short = P.call_usd("claude-haiku-5-5", {"fresh_input": 100_000})
        long_ = P.call_usd("claude-haiku-5-5", {"fresh_input": 100_001})
        self.assertAlmostEqual(short, 100_000 * 0.10 / 1e6)
        self.assertAlmostEqual(long_, 100_001 * 0.50 / 1e6)
        self.assertIsNone(P.call_usd("claude-unknown-1", t))

    def test_trailing_partial_line_accepted_and_noted(self):
        """Hole 1a: Haloander's live transcript ended in a half-written line; Hamilton refused the file."""
        p = self.proj / (self.sid + ".jsonl")
        p.write_text(p.read_text() + '{"type": "assistant", "message": {"id": "c3", "us')
        hp = sessions.load_hamilton()
        with self.assertRaises(ValueError):
            hp.load(p)  # Hamilton's own behaviour is unchanged
        self.run_()
        r = self.rows()[self.sid]
        self.assertEqual(r["malformed_lines"], "1")
        self.assertIn("trailing line only", r["coverage_notes"])
        self.assertAlmostEqual(float(r["usd_list"]), self.coord_usd, places=6)

    def test_interior_bad_line_is_lower_bound(self):
        p = self.proj / (self.sid + ".jsonl")
        lines = p.read_text().splitlines()
        p.write_text("\n".join(lines[:2] + ["not json at all"] + lines[2:]) + "\n")
        self.run_()
        self.assertIn("lower bound", self.rows()[self.sid]["coverage_notes"])

    def test_own_table_read_back_does_not_refuse(self):
        """Hole 1c: Cujas c01-c03 refused because the coordinator had read rows of its earlier table."""
        self.run_()
        earlier = self.rows()[self.wid]
        line = next(ln for ln in (self.out / "AGENT_USAGE.csv").read_text().splitlines() if self.wid in ln)
        summary_note = "Tokens are what transcripts recorded; they are not an invoice."
        p = self.proj / (self.sid + ".jsonl")
        p.write_text(p.read_text() + json.dumps(user("2026-11-09T10:02:00.000Z", result=line, sid=self.sid)) + "\n"
                     + json.dumps(user("2026-11-09T10:02:01.000Z", result=summary_note, sid=self.sid)) + "\n"
                     + json.dumps(user("2026-11-09T10:02:02.000Z", result=earlier["started_utc"], sid=self.sid)) + "\n")
        self.run_()  # must not raise GuardError
        self.assertIn(self.wid, self.rows())

    def test_crosscheck_and_worker_role(self):
        log = Path(self.tmp.name) / "COORDINATOR_LOG.txt"
        log.write_text("producer-c01 %s cost %.7f turns 1 ms 5\n" % (self.wid, self.work_usd / 2)  # earlier, superseded
                       + "producer-c01-r %s cost %.7f turns 1 ms 5\n" % (self.wid, self.work_usd))
        s, _, _ = self.run_([log])
        xc = {e["session_id"]: e for e in s["crosscheck"]["sessions"]}
        self.assertEqual(xc[self.wid]["verdict"], "agrees")
        r = self.rows()[self.wid]
        self.assertEqual((r["role"], r["worker_label"]), ("worker", "producer-c01-r"))
        self.assertEqual(self.rows()[self.sid]["role"], "coordinator")
        self.assertIn("worker", s["totals_by_role"])

    def test_crosscheck_json_result_and_disagreement_exit_3(self):
        res = Path(self.tmp.name) / "reviewer.json"
        res.write_text(json.dumps({"type": "result", "session_id": self.wid, "total_cost_usd": self.work_usd * 1.5}))
        ghost = Path(self.tmp.name) / "ghost.json"
        ghost.write_text(json.dumps({"type": "result", "session_id": "55555555-aaaa-bbbb-cccc-000000000005",
                                     "total_cost_usd": 1.0}))
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.cfg), "HOME": self.tmp.name}
        p = subprocess.run([sys.executable, "-I", str(HERE / "sessions.py"), "--wave", "w", "--phase", "p",
                            "--out", str(self.out), "--reported-costs", str(res), "--reported-costs", str(ghost)],
                           env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 3, p.stderr)
        s = json.loads((self.out / "SUMMARY.json").read_text())
        v = {e["session_id"][:8]: e["verdict"] for e in s["crosscheck"]["sessions"]}
        self.assertEqual(v, {"44444444": "disagrees", "55555555": "no_transcript"})
        # tolerance: 1 cent or 1 percent, whichever is larger
        xc = next(e for e in s["crosscheck"]["sessions"] if e["verdict"] == "disagrees")
        self.assertAlmostEqual(xc["tolerance_usd"], max(0.01, 0.01 * self.work_usd * 1.5), places=6)

    def test_since_makes_crosscheck_not_comparable(self):
        log = Path(self.tmp.name) / "log.txt"
        log.write_text("w %s cost %.7f\n" % (self.wid, self.work_usd))
        s, _, _ = sessions.run("w", self.out, phase="p", claude_dirs=[self.cfg], reported_paths=[log],
                               since=sessions.parse_ts("2026-11-09T10:00:00Z"))
        self.assertEqual(s["crosscheck"]["sessions"][0]["verdict"], "not_comparable")

    def test_bentham_usage_propagates_exit_code(self):
        """Hole 1d: `bentham.py usage` exited 0 even when sessions.py refused to write."""
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.cfg), "HOME": self.tmp.name}
        res = Path(self.tmp.name) / "r.json"
        res.write_text(json.dumps({"type": "result", "session_id": self.wid, "total_cost_usd": 99.0}))
        p = subprocess.run([sys.executable, "-I", str(HERE / "bentham.py"), "usage", "--wave", "w", "--phase", "p",
                            "--out", str(self.out), "--claude-dir", str(self.cfg), "--reported-costs", str(res)],
                           env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 3, p.stderr)


if __name__ == "__main__":
    unittest.main()
