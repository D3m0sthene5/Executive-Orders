"""Tests for the Maudslay conveyor: the real state machine, driven by a fake kit and a fake worker command.

No model, no network, no real claim-kit corpus. jobs/claim-kit stages (next, prepare, dispatch-check, apply,
batch-check, complete) are replaced by fakes/fake_kit.py behind the conveyor's tool templates; cruden lookups,
Geddes views and Bentham's gate by fakes/fake_tool.py; workers by fakes/fake_worker.py.

    python -I jobs/maudslay-conveyor/test_conveyor.py
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import conveyor as C  # noqa: E402

FAKES = HERE / "fakes"
PY = sys.executable
CLAUDE_FAKE = [PY, str(FAKES / "fake_worker.py"), "-p", "--model", "{model}", "--output-format", "json",
               "--max-turns", "{max_turns}", "--max-budget-usd", "{item_usd}"]
CODEX_FAKE = [PY, str(FAKES / "fake_worker.py"), "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-C", "{cwd}",
              "-m", "{model}", "-c", "model_auto_compact_token_limit={auto_compact_tokens}",
              "-c", "tool_output_token_limit={tool_output_tokens}", "-c", 'approval_policy="never"']


def jl(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


class ConveyorCase(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        k = tempfile.TemporaryDirectory()
        self.addCleanup(k.cleanup)
        self.repo = Path(t.name) / "repo"
        self.repo.mkdir()
        self.keys = Path(k.name)
        (self.repo / "FAKE_POOL.json").write_text(json.dumps([f"EO:{i}" for i in range(1, 9)]))
        (self.repo / "route_test.txt").write_text("decided, synthetic route for tests.\n")
        tools = {"kit": [PY, str(FAKES / "fake_kit.py"), "--repo", "{repo}"],
                 "lookups": [PY, str(FAKES / "fake_tool.py"), "lookups", "{packet}"],
                 "view": [PY, str(FAKES / "fake_tool.py"), "view", "{packet}/PACKET.json", "{iid}", "--write", "{out}"],
                 "gate": [PY, str(FAKES / "fake_tool.py"), "gate", "--action", "{action}", "--batches", "{batches}"]}
        (self.repo / "tools.json").write_text(json.dumps(tools))
        self.workers(CLAUDE_FAKE)
        self.log = self.repo / "WORKER_LOG.jsonl"
        self.scenario({})
        env = {"MAUDSLAY_FAKE_LOG": str(self.log), "MAUDSLAY_FAKE_SCENARIO": str(self.repo / "SCENARIO.json")}
        p = mock.patch.dict(os.environ, env)
        p.start()
        self.addCleanup(p.stop)
        os.environ.pop("MAUDSLAY_KILL_AT", None)

    def workers(self, producer, reviewer=None, family="claude", rfamily="claude"):
        w = {"producer": {"command": producer, "family": family, "model": "fake-producer", "model_family": "Anthropic"},
             "reviewer": {"command": reviewer or CLAUDE_FAKE, "family": rfamily, "model": "fake-reviewer",
                          "model_family": "Anthropic"}}
        (self.repo / "workers.json").write_text(json.dumps(w))

    def scenario(self, sc):
        (self.repo / "SCENARIO.json").write_text(json.dumps(sc))

    def kit(self, cfg):
        (self.repo / "FAKE_KIT.json").write_text(json.dumps(cfg))

    def args(self, *extra, n=4):
        return ["run", "--repo", str(self.repo), "--run-dir", "research/excavator/maudslay-test", "--batch", "b01",
                "--agent", "testagent", "--action", "production.test", "--n", str(n), "--route", "route_test.txt",
                "--workers", "workers.json", "--tools", "tools.json", "--keys-dir", str(self.keys),
                "--item-usd", "2", "--parallel", "2", "--publication", "research/readiness/claims/testagent-b01.jsonl",
                *extra]

    def run_cli(self, *extra, n=4):
        with contextlib.redirect_stdout(io.StringIO()):
            return C.main(self.args(*extra, n=n))

    def run_proc(self, *extra, kill=None, n=4):
        env = dict(os.environ)
        env.pop("MAUDSLAY_KILL_AT", None)
        if kill:
            env["MAUDSLAY_KILL_AT"] = kill
        p = subprocess.run([PY, "-I", str(HERE / "conveyor.py"), *self.args(*extra, n=n)], env=env,
                           capture_output=True, text=True)
        return p.returncode

    @property
    def bdir(self):
        return self.repo / "research/excavator/maudslay-test/b01"

    def ledger(self):
        return jl(self.bdir / "LEDGER.jsonl")

    def calls(self, cmd=None):
        return [c for c in jl(self.repo / "FAKE_CALLS.jsonl") if cmd is None or c["cmd"] == cmd]

    def worker_calls(self, kind=None):
        return [c for c in jl(self.log) if "kind" in c and (kind is None or c["kind"] == kind)]

    def published(self):
        return jl(self.repo / "research/readiness/claims/testagent-b01.jsonl")


class FullBatchTests(ConveyorCase):
    def test_full_batch_files_reviewed_claims_and_measures(self):
        self.kit({"blocked": ["EO:4"]})
        rc = self.run_cli("--publish")
        self.assertEqual(rc, C.EXIT_DONE)
        self.assertEqual(sorted(c["instrument_id"] for c in self.published()), ["EO:1", "EO:2", "EO:3"])
        self.assertEqual(len(self.worker_calls("producer")), 3)  # EO:4 was source-blocked: no producer
        man = json.loads((self.bdir / "packet/completion/COMPLETION.json").read_text(encoding="utf-8"))
        out = {m["instrument_id"]: m["outcome"] for m in man["members"]}
        self.assertEqual(out, {"EO:1": "submit", "EO:2": "submit", "EO:3": "submit", "EO:4": "blocked"})
        self.assertGreaterEqual(len(man["controls"]), 1)
        self.assertEqual(man["independence_requirement"], "same_family_separate_context")
        m = json.loads((self.bdir / "MEASURES.json").read_text(encoding="utf-8"))
        self.assertEqual(m["stages"]["produce"]["workers"], 3)
        self.assertEqual(m["stages"]["review"]["workers"], 2)
        self.assertEqual(m["stages"]["reveal"]["workers"], 2)
        self.assertAlmostEqual(m["totals"]["usd"], 3.5)
        self.assertEqual(m["totals"]["filed"], 3)
        self.assertEqual(m["human_certified"], 0)
        gate = json.loads((self.repo / "research/excavator/maudslay-test/BATCHES.json").read_text())
        self.assertEqual(gate, [{"batch": "b01", "attempted": 4, "submitted": 3, "filed": 3, "controls_missed": 0,
                                 "usd": 3.5}])
        self.assertEqual(json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"], [])
        costs = (self.bdir / "COSTS.log").read_text()
        self.assertEqual(costs.count(" cost "), 7, costs)
        # The control key is sealed outside the repository; the ledger holds only its hash and counts.
        plant = next(r for r in self.ledger() if r["key"] == "plant" and r["status"] == "done")["data"]
        self.assertEqual(set(plant) - {"wall_seconds"}, {"controls", "key_sha256", "claims", "sets"})
        salt = json.loads((self.keys / "b01.json").read_text())["salt"]
        for p in self.repo.rglob("*"):
            if p.is_file():
                self.assertNotIn(salt, p.read_text(encoding="utf-8", errors="replace"), p)

    def test_rerun_of_a_finished_batch_redoes_nothing(self):
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        before = (len(self.worker_calls()), len(self.calls()))
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertEqual((len(self.worker_calls()), len(self.calls("complete"))), (before[0], 1))


class ResumeTests(ConveyorCase):
    def test_killed_run_resumes_without_redoing_finished_stages(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_2:done"), 137)
        self.assertEqual(len(self.worker_calls("producer")), 2)
        self.assertEqual(self.run_proc("--parallel", "1", kill="plant:done"), 137)
        key_sha = next(r for r in self.ledger() if r["key"] == "plant" and r["status"] == "done")["data"]["key_sha256"]
        self.assertEqual(self.run_proc("--parallel", "1", "--publish"), C.EXIT_DONE)
        self.assertEqual(len(self.calls("next")), 1)
        self.assertEqual(len(self.calls("prepare")), 1)
        per_order = [c["id"] for c in self.worker_calls("producer")]
        self.assertEqual(sorted(per_order), ["EO:1", "EO:2", "EO:3", "EO:4"])  # each order produced exactly once
        self.assertEqual(len(self.worker_calls("reviewer")), 4)  # 2 blind arms + 2 after-reveal, once each
        self.assertEqual(C.fsha(self.keys / "b01.json"), key_sha)  # the planted controls were not re-drawn
        self.assertEqual(len(self.published()), 4)
        # Each restart that still had producers to launch ran its own dispatch check.
        self.assertEqual(len(self.calls("dispatch-check")), 2)

    def test_killed_between_started_and_done_reruns_only_that_item(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_3:started"), 137)
        self.assertEqual(sorted(c["id"] for c in self.worker_calls("producer")), ["EO:1", "EO:2"])
        self.assertEqual(self.run_proc("--parallel", "1"), C.EXIT_DONE)
        self.assertEqual(sorted(c["id"] for c in self.worker_calls("producer")), ["EO:1", "EO:2", "EO:3", "EO:4"])

    def test_fixed_settings_cannot_change_on_resume(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_1:done"), 137)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = C.main([a if a != "production.test" else "production.other" for a in self.args()])
        self.assertEqual(rc, C.EXIT_FAILED)


class PromptCapTests(ConveyorCase):
    def test_prompts_over_the_cap_are_not_dispatched(self):
        rc = self.run_cli("--prompt-cap-chars", "3000")
        self.assertEqual(rc, C.EXIT_STOPPED)
        self.assertEqual(self.worker_calls(), [])
        items = json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"]
        self.assertEqual(sorted(i["instrument_id"] for i in items), ["EO:1", "EO:2", "EO:3", "EO:4"])
        self.assertTrue(all(i["kind"] == "prompt_over_cap" and not i["blocks_completion"] for i in items))

    def test_every_rendered_prompt_is_within_the_cap_and_names_only_its_order(self):
        self.assertEqual(self.run_cli("--prompt-cap-chars", "12000"), C.EXIT_DONE)
        for p in (self.bdir / "prompts").glob("*.txt"):
            self.assertLessEqual(len(p.read_text(encoding="utf-8")), 12000, p.name)
        text = (self.bdir / "prompts/b01-produce-EO_2.txt").read_text(encoding="utf-8")
        self.assertIn("ORDER: EO:2", text)
        for other in ("EO:1", "EO:3", "EO:4"):
            self.assertNotIn(other, text)
        self.assertIn("decided, synthetic route for tests.", text)


class FreshSessionTests(ConveyorCase):
    def test_every_worker_call_is_fresh_and_carries_budget_flags(self):
        self.assertEqual(self.run_cli("--item-usd", "1.25"), C.EXIT_DONE)
        calls = self.worker_calls()
        self.assertEqual(len(calls), 8)
        for c in calls:
            a = c["argv"]
            self.assertFalse(set(a) & (C.RESUME_TOKENS | {"-c", "-r"}), a)
            self.assertEqual(a[a.index("--max-budget-usd") + 1], "1.25")
            self.assertIn("--max-turns", a)
            self.assertEqual(a[a.index("--output-format") + 1], "json")
        sessions = [w["session_id"] for w in C.Ledger(self.bdir / "LEDGER.jsonl").workers()]
        self.assertEqual(len(set(sessions)), 8)

    def test_a_role_can_carry_its_own_item_cap(self):
        w = json.loads((self.repo / "workers.json").read_text())
        w["reviewer"]["item_usd"] = 7.5
        (self.repo / "workers.json").write_text(json.dumps(w))
        self.assertEqual(self.run_cli("--item-usd", "1.25"), C.EXIT_DONE)
        caps = {(c["kind"], c["argv"][c["argv"].index("--max-budget-usd") + 1]) for c in self.worker_calls()}
        self.assertEqual(caps, {("producer", "1.25"), ("reviewer", "7.5")})

    def test_resume_and_unsafe_commands_are_refused(self):
        ok = ["claude", "-p", "--model", "m", "--output-format", "json", "--max-turns", "5", "--max-budget-usd", "1"]
        C.validate_worker_command(ok, "claude")
        for bad in (ok + ["--resume", "abc"], ok + ["-c"], ok + ["--continue"], ok + ["--fork-session"],
                    ok[:6] + ok[8:], ok[:8], ok + ["--dangerously-skip-permissions"]):
            with self.assertRaises(C.Fail, msg=bad):
                C.validate_worker_command(bad, "claude")
        cx = C.render_args(C.CODEX_TEMPLATE, {"cwd": "B", "model": "m", "auto_compact_tokens": 1000,
                                              "tool_output_tokens": 100, "writable_roots": '["B", "G"]',
                                              "network": "false"})
        C.validate_worker_command(cx, "codex")
        for need in ("--ephemeral", "--skip-git-repo-check", "--json", "model_auto_compact_token_limit=1000",
                     "tool_output_token_limit=100", 'approval_policy="never"', 'sandbox_mode="workspace-write"',
                     'sandbox_workspace_write.writable_roots=["B", "G"]', "sandbox_workspace_write.network_access=false"):
            self.assertIn(need, cx)
        self.assertNotIn("resume", cx)
        for bad in (["codex", "exec", "resume", "--last"] + cx[2:], cx + ["-c", "rollout_token_budget=1"],
                    [t for t in cx if t != "--ephemeral"], cx + ["--dangerously-bypass-approvals-and-sandbox"]):
            with self.assertRaises(C.Fail, msg=bad):
                C.validate_worker_command(bad, "codex")

    def test_claude_worker_without_item_cap_is_refused(self):
        args = self.args()
        i = args.index("--item-usd")
        args = args[:i] + args[i + 2:]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(C.main(args), C.EXIT_FAILED)
        self.assertEqual(self.worker_calls(), [])

    def test_codex_usage_is_read_from_its_json_events(self):
        self.workers(CODEX_FAKE, CODEX_FAKE, "codex", "codex")
        self.scenario({"tokens": 1000})
        self.assertEqual(self.run_cli(), C.EXIT_DONE)
        ws = C.Ledger(self.bdir / "LEDGER.jsonl").workers()
        self.assertTrue(all((w["input"], w["cache_read"], w["output"], w["tokens"]) == (1000, 2000, 1000, 4000) for w in ws))
        gate = [r for r in self.ledger() if r["key"].startswith("gate:")][-1]["data"]["verdict"]
        self.assertIn("usd unknown", gate["skipped"])  # no prices given: the gate is not run on a guessed cost


class StopRuleTests(ConveyorCase):
    def test_missed_planted_control_stops_the_batch(self):
        self.scenario({"reviewer": {"B": {"miss_controls": True}}})
        rc = self.run_cli("--publish")
        self.assertEqual(rc, C.EXIT_STOPPED)
        self.assertEqual(self.calls("complete"), [])
        self.assertEqual(self.published(), [])
        self.assertEqual(len(self.worker_calls("reviewer")), 2)  # no after-reveal sessions
        line = json.loads((self.repo / "research/excavator/maudslay-test/BATCHES.json").read_text())[0]
        self.assertGreaterEqual(line["controls_missed"], 1)
        self.assertEqual(line["filed"], 0)
        ctl = json.loads((self.bdir / "CONTROLS.json").read_text())["controls"]
        self.assertTrue(all(c["caught_A"] and not c["caught_B"] for c in ctl))
        run = [r for r in self.ledger() if r["key"] == "run"][-1]
        self.assertEqual(run["status"], "stopped")
        self.assertIn("planted control", run["data"]["reason"])

    def test_batch_budget_stops_launching_and_a_resume_can_continue(self):
        self.scenario({"usd": {"producer": 1.0}})
        rc = self.run_cli("--parallel", "1", "--item-usd", "1", "--batch-usd", "2.5")
        self.assertEqual(rc, C.EXIT_STOPPED)
        self.assertEqual(len(self.worker_calls("producer")), 2)
        self.assertIn("batch_budget", [r for r in self.ledger() if r["key"] == "run"][-1]["data"]["reason"])
        self.assertEqual(self.calls("apply"), [])
        rc = self.run_cli("--parallel", "1", "--item-usd", "1", "--batch-usd", "100")
        self.assertEqual(rc, C.EXIT_DONE)
        self.assertEqual(sorted(c["id"] for c in self.worker_calls("producer")), ["EO:1", "EO:2", "EO:3", "EO:4"])

    def test_zero_submittable_after_producers_stops(self):
        self.scenario({"producer": {f"EO:{i}": "block" for i in range(1, 5)}})
        self.assertEqual(self.run_cli(), C.EXIT_STOPPED)
        self.assertIn("zero orders submittable", [r for r in self.ledger() if r["key"] == "run"][-1]["data"]["reason"])
        self.assertEqual(self.calls("apply"), [])

    def test_item_token_cap_kills_a_worker_in_the_loop(self):
        self.workers(CODEX_FAKE, CLAUDE_FAKE, "codex", "claude")
        self.scenario({"codex_turns": 6, "codex_turn_sleep": 0.4, "tokens": 1000})
        rc = self.run_cli("--item-tokens", "6000", n=2)
        self.assertEqual(rc, C.EXIT_STOPPED)  # both producers killed: zero submittable
        ws = C.Ledger(self.bdir / "LEDGER.jsonl").workers()
        self.assertEqual(len(ws), 2)
        self.assertTrue(all(w["killed"] and "item_token_cap" in w["killed"] for w in ws))
        self.assertTrue(all(w["tokens"] <= 8000 for w in ws))  # killed after 2 of 6 turns
        items = json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"]
        self.assertEqual({i["kind"] for i in items}, {"over_item_cap"})


class AdjudicationTests(ConveyorCase):
    def test_arm_disagreement_goes_to_adjudicate_not_to_a_decision(self):
        self.scenario({"reviewer": {"A": {"reject": ["EO:2"]}}})
        rc = self.run_cli("--publish")
        self.assertEqual(rc, C.EXIT_PAUSED)
        self.assertEqual(self.calls("complete"), [])
        items = json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"]
        self.assertEqual([(i["instrument_id"], i["kind"], i["blocks_completion"]) for i in items],
                         [("EO:2", "arm_disagreement", True)])
        self.assertEqual(items[0]["arm_A"]["verdict"], "rejected")
        self.assertIn(items[0]["arm_B"]["verdict"], ("upheld", "upheld_after_reveal"))
        # The coordinator decides; the conveyor then completes with that decision recorded.
        (self.bdir / "ADJUDICATION.json").write_text(json.dumps({"decisions": [
            {"instrument_id": "EO:2", "decision": "block", "reason": "arm A's defect stands", "adjudicator": "coord"}]}))
        rc = self.run_cli("--publish")
        self.assertEqual(rc, C.EXIT_DONE)
        self.assertEqual(sorted(c["instrument_id"] for c in self.published()), ["EO:1", "EO:3", "EO:4"])
        man = json.loads((self.bdir / "packet/completion/COMPLETION.json").read_text(encoding="utf-8"))
        eo2 = next(m for m in man["members"] if m["instrument_id"] == "EO:2")
        self.assertEqual(eo2["outcome"], "blocked")
        self.assertIn("Coordinator adjudication", eo2["reason"])
        self.assertIn("research/excavator/maudslay-test/b01/ADJUDICATION.json", [r["path"] for r in man["receipts"]])
        self.assertEqual(len(self.worker_calls("reviewer")), 4)  # no review was rerun

    def test_defer_adjudication_completes_and_holds_the_order_unfiled(self):
        self.scenario({"reviewer": {"B": {"reject": ["EO:3"]}}})
        self.assertEqual(self.run_cli("--publish", "--defer-adjudication"), C.EXIT_DONE)
        self.assertNotIn("EO:3", [c["instrument_id"] for c in self.published()])
        self.assertEqual([i["instrument_id"] for i in json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"]],
                         ["EO:3"])

    def test_both_arms_rejecting_blocks_without_adjudication(self):
        self.scenario({"reviewer": {"A": {"reject": ["EO:1"]}, "B": {"reject": ["EO:1"]}}})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertNotIn("EO:1", [c["instrument_id"] for c in self.published()])
        self.assertEqual(json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"], [])


class RepairTests(ConveyorCase):
    def test_mechanical_failure_gets_one_fresh_repair_session_then_demotion(self):
        self.scenario({"producer": {"EO:2": "checkfail", "EO:3": "badclaim"}, "repair_fails": ["EO:3"]})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        rep = sorted(c["id"] for c in self.worker_calls("producer") if c["repair"])
        self.assertEqual(rep, ["EO:2", "EO:3"])
        self.assertEqual(sorted(c["instrument_id"] for c in self.published()), ["EO:1", "EO:2", "EO:4"])
        man = json.loads((self.bdir / "packet/completion/COMPLETION.json").read_text(encoding="utf-8"))
        eo3 = next(m for m in man["members"] if m["instrument_id"] == "EO:3")
        self.assertEqual(eo3["outcome"], "blocked")
        self.assertIn("mechanical checks failed", eo3["reason"])
        self.assertTrue((self.bdir / "packet/maudslay/work/EO_3.round-0").is_dir())  # the pre-repair sheet is kept

    def test_invalid_sheet_is_not_used(self):
        self.scenario({"producer": {"EO:1": "bad_sheet"}})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertNotIn("EO:1", [c["instrument_id"] for c in self.published()])
        _, rows = C.read_csv(self.bdir / "packet/decisions.csv")
        r = next(r for r in rows if r["instrument_id"] == "EO:1")
        self.assertEqual(r["outcome"], "unresolved")
        self.assertIn("producer sheet invalid", r["unresolved_material_gaps"])


KIT_HOME = Path(os.environ.get("MAUDSLAY_KIT_HOME") or C.REPO)
KIT_NEEDS = ("jobs/claim-kit/test_build.py", "jobs/claim-kit/test_dispatch.py", "jobs/norton/model.py",
             "jobs/claim-checker/checker.py", "jobs/later-events/later_events.py", "jobs/geddes/geddes.py",
             "research/stage19/code/claim_gate.py", "jobs/clause-drafts/segment.py", "jobs/status-history/history.py")


@unittest.skipUnless(all((KIT_HOME / p).exists() for p in KIT_NEEDS),
                     f"needs a checkout holding the claim kit and its imports at {KIT_HOME} (set MAUDSLAY_KIT_HOME)")
class RealKitFixtureTests(unittest.TestCase):
    """The committed claim kit end to end on its own synthetic corpus (jobs/claim-kit/test_build.py
    BuildIntegrationTests, with test_dispatch.py's raw-source retention): real kit next, prepare, dispatch-check,
    Geddes views, apply, batch-check with the actual claim checker, and complete --publish. Only the workers are
    fake (they write the kit fixture's own canned decision), and the readiness-tracker replay is stubbed as the
    kit's completion tests stub it."""

    def setUp(self):
        import shutil
        sys.path.insert(0, str(KIT_HOME / "jobs/claim-kit"))
        import test_build as T
        import test_dispatch as TD
        fx = T.BuildIntegrationTests("test_reservations_disjoint_and_respect_existing_claims")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        TD.DispatchTests.retain(fx)
        # The actual checker reads signing dates from any jobs/*/output/*.csv with these columns.
        (fx.repo / "jobs/future-source/output/SIGNING.csv").write_text(
            "instrument_id,signing_date\n" + "".join(f"EO:{i},{'2000-01-01' if i == 5 else '1990-01-01'}\n"
                                                      for i in range(1, 7)))
        fx.run_build()
        for d in ("claim-kit", "claim-checker", "norton"):  # batch-check runs the checker from the fixture repo
            for f in (KIT_HOME / "jobs" / d).glob("*.py"):
                t = fx.repo / "jobs" / d / f.name
                if not t.exists():
                    t.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(f, t)
        self.fx, self.repo = fx, fx.repo
        k = tempfile.TemporaryDirectory()
        self.addCleanup(k.cleanup)
        self.keys = Path(k.name)
        tools = {"kit": [PY, "-X", "utf8", str(FAKES / "kit_shim.py"), str(KIT_HOME), "--repo", "{repo}"],
                 "lookups": [PY, str(FAKES / "fake_tool.py"), "lookups", "{packet}"],
                 "view": [PY, "-X", "utf8", str(KIT_HOME / "jobs/geddes/geddes.py"), "view", "{packet}/PACKET.json",
                          "{iid}", "--write", "{out}", "--repo", "{repo}"],
                 "gate": [PY, str(FAKES / "fake_tool.py"), "gate", "--action", "{action}", "--batches", "{batches}"]}
        (self.repo / "tools.json").write_text(json.dumps(tools))
        (self.repo / "workers.json").write_text(json.dumps({
            "producer": {"command": CLAUDE_FAKE, "family": "claude", "model": "p", "model_family": "Anthropic"},
            "reviewer": {"command": CLAUDE_FAKE, "family": "claude", "model": "r", "model_family": "Anthropic"}}))
        (self.repo / "route.txt").write_text("synthetic route")
        canned = {}
        for iid in ("EO:1", "EO:2"):  # test_batch.BatchTests.fill, as sheet rows
            s = fx.decision(iid)
            dec = dict(outcome="submit", approved="true", original_confirmed="true", inventory_confirmed="true",
                       original_pages_confirmed="false", research_rationale=s["research_rationale"],
                       savings_state=s["savings"]["state"], savings_source_id=s["savings"]["source_id"],
                       savings_reason=s["savings"]["reason"], search_ids=json.dumps(s["search_ids"]),
                       conflict_resolutions="{}", unresolved_material_gaps="[]",
                       **{k: "Explicit synthetic corpus review confirms this target-specific check."
                          for k in ("earlier_end_check", "scope_check", "independent_command_check", "savings_check")})
            cl = {d["scope_id"]: {k: (json.dumps(v) if isinstance(v, (bool, list, dict)) else ("" if v is None else v))
                                  for k, v in d.items()} for d in s["clauses"]}
            canned[iid] = {"decision": dec, "clauses": cl}
        (self.repo / "SCENARIO.json").write_text(json.dumps({"canned": canned}))
        p = mock.patch.dict(os.environ, {"MAUDSLAY_FAKE_SCENARIO": str(self.repo / "SCENARIO.json"),
                                         "MAUDSLAY_FAKE_LOG": str(self.repo / "WORKER_LOG.jsonl")})
        p.start()
        self.addCleanup(p.stop)

    def test_real_kit_reserve_prepare_apply_check_and_complete(self):
        with contextlib.redirect_stdout(io.StringIO()):
            rc = C.main(["run", "--repo", str(self.repo), "--run-dir", "research/excavator/real", "--batch", "r01",
                         "--agent", "producer", "--action", "production.fixture", "--n", "2", "--route", "route.txt",
                         "--workers", "workers.json", "--tools", "tools.json", "--keys-dir", str(self.keys),
                         "--item-usd", "1", "--publish", "--publication", "research/readiness/claims/producer-r01.jsonl"])
        b = self.repo / "research/excavator/real/r01"
        self.assertEqual(rc, C.EXIT_DONE, [r for r in jl(b / "LEDGER.jsonl") if r["key"] == "run"])
        reserved = next(r for r in jl(b / "LEDGER.jsonl") if r["key"] == "reserve" and r["status"] == "done")["data"]
        self.assertEqual((reserved["via"], sorted(reserved["ids"])), ("kit next", ["EO:1", "EO:2"]))
        lock = json.loads((self.repo / "research/readiness/CLAIM_KIT_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual({lock["orders"][i]["agent"] for i in ("EO:1", "EO:2")}, {"producer"})
        summ = json.loads(next(b.glob("packet/applied-v*/CHECK_SUMMARY.json")).read_text(encoding="utf-8"))
        self.assertEqual(summ["actual_claim_checker"]["claims_all_checks_passed"], 2)
        tally = json.loads(next(b.glob("packet/complete-v*/TALLY.json")).read_text(encoding="utf-8"))
        self.assertEqual((tally["exceptions"], tally["claims_published"]), (0, 2))
        self.assertGreaterEqual(tally["plants_caught"], 1)
        filed = jl(self.repo / "research/readiness/claims/producer-r01.jsonl")
        self.assertEqual(sorted(c["instrument_id"] for c in filed), ["EO:1", "EO:2"])
        self.assertTrue(all(c["schema"] == "eo-lifecycle-claim/v1" for c in filed))


class UnitTests(unittest.TestCase):
    def test_plant_moves_dates_back_and_is_never_a_no_op(self):
        c = {"instrument_id": "EO:1", "whole_order_end": {"date": "2000-02-29"},
             "operative_clauses": [{"first_end": {"date": "2000-02-29"}}]}
        rset, ctl = C.plant_controls([c], "salt")
        self.assertEqual(rset[0]["whole_order_end"]["date"], "1997-02-28")
        self.assertEqual(ctl[0]["genuine"], C.canon(c))
        self.assertNotEqual(ctl[0]["planted"], ctl[0]["genuine"])
        many = [dict(c, instrument_id=f"EO:{i}") for i in range(31)]
        self.assertEqual(len(C.plant_controls(many, "s")[1]), 2)

    def test_caught_needs_a_rejection_naming_a_date(self):
        self.assertTrue(C.caught({"verdict": "rejected", "defects": [{"field": "first_end.date"}]}))
        self.assertFalse(C.caught({"verdict": "rejected", "defects": ["quote mismatch"]}))
        self.assertFalse(C.caught({"verdict": "upheld", "defects": []}))
        self.assertFalse(C.caught(None))

    def test_claude_usage_parse(self):
        u = C.parse_usage(json.dumps({"session_id": "s", "total_cost_usd": 0.7, "num_turns": 4, "usage": {
            "input_tokens": 10, "cache_read_input_tokens": 200, "cache_creation_input_tokens": 30, "output_tokens": 5}}))
        self.assertEqual((u["session_id"], u["usd"], C.tokens(u)), ("s", 0.7, 245))


if __name__ == "__main__":
    unittest.main()
