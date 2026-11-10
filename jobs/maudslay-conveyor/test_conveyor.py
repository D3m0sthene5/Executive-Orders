"""Tests for the Maudslay conveyor: the real state machine, driven by a fake kit and a fake worker command.

No model, no network. In most tests the jobs/claim-kit stages (next, prepare, dispatch-check, apply, batch-check,
complete) are fakes/fake_kit.py behind the conveyor's tool templates; cruden lookups, Geddes views and Bentham's gate
are fakes/fake_tool.py; workers are fakes/fake_worker.py. RealKitFixtureTests runs the committed kit instead.

    python -I jobs/maudslay-conveyor/test_conveyor.py
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import conveyor as C  # noqa: E402

FAKES = HERE / "fakes"
PY = sys.executable
CLAUDE_FAKE = [PY, str(FAKES / "fake_worker.py"), "-p", "--model", "{model}", "--output-format", "stream-json",
               "--verbose", "--max-turns", "{max_turns}", "--max-budget-usd", "{item_usd}"]
CODEX_FAKE = [PY, str(FAKES / "fake_worker.py"), "exec", "--json", "--skip-git-repo-check", "-C", "{cwd}",
              "-m", "{model}", "--config", "model_auto_compact_token_limit={auto_compact_tokens}",
              "--config", "tool_output_token_limit={tool_output_tokens}", "--config", 'approval_policy="never"']
CODEX_OK = {"item_tokens": 100000, "prices_usd_per_mtok": {"input": 1.0, "cached_input": 0.1, "output": 8.0}}


def load_augur():
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_augur_module", C.REPO / "jobs/augur-launch/augur.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AUGUR = load_augur()


def stub_bentham(repo, action, orders_listed=100, members=()):
    """A minimal Bentham plan, an empty Kean register, and (optionally) the action's strata list."""
    out = Path(repo) / "jobs/bentham/output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "PLAN.json").write_text(json.dumps({"ranked": [{"id": action, "orders": orders_listed, "rate": {"value": 0.6},
                                                           "per_usd": 1.0, "cost_usd": 100.0}], "unranked": []}))
    if members:
        (out / "strata").mkdir(exist_ok=True)
        (out / "strata" / f"{action}.txt").write_text("".join(m + "\n" for m in members))
    reg = Path(repo) / "jobs/kean/register/findings.jsonl"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text("")


def wave_plan(path, action, orders, reviewed=True):
    """A WAVE.json that Augur's real check() passes against stub_bentham."""
    plan = {"wave": "maudslay-test", "author": "claude-opus-5-5", "stage": 0,
            "objective": {"metric": "filed_dossiers_per_unit"},
            "actions": [{"id": action, "orders": orders, "lanes": 1}],
            "configuration": {"orchestrator": "maudslay-conveyor", "coordinator_model": "claude-opus-5-5",
                              "producer_model": "claude-sonnet"},
            "limits": {"chain_budget_units": 1000000, "spend_per_claim_units": 100000, "no_claim_minutes": 40,
                       "context_kill_tokens": 120000, "reviews_per_hour": 6, "coordinator_units_per_hour": 100000},
            "premortem": [{"failure": f"synthetic failure number {i} in the test wave", "guard": f"synthetic guard "
                           f"number {i} that stops it"} for i in range(3)],
            "acknowledged_findings": {}}
    if reviewed:
        plan["review"] = {"reviewer": "gpt-6.1-sol", "verdict": "approve", "plan_sha256": AUGUR.plan_sha(plan)}
    Path(path).write_text(json.dumps(plan))


def jl(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


class ConveyorCase(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        s = tempfile.TemporaryDirectory()
        self.addCleanup(s.cleanup)
        self.repo = Path(t.name) / "repo"
        self.repo.mkdir()
        self.scratch = Path(s.name) / "scratch"
        self.control = self.scratch / "control"
        self.codex_home = Path(s.name) / "codex-home"
        stub_bentham(self.repo, "production.test")
        wave_plan(self.repo / "WAVE.json", "production.test", 8)
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
        env = {"MAUDSLAY_FAKE_LOG": str(self.log), "MAUDSLAY_FAKE_SCENARIO": str(self.repo / "SCENARIO.json"),
               "MAUDSLAY_TEST_ALLOW_TEMP_SCRATCH": "1", "CODEX_HOME": str(self.codex_home)}
        p = mock.patch.dict(os.environ, env)
        p.start()
        self.addCleanup(p.stop)
        for k in ("MAUDSLAY_KILL_AT", "MAUDSLAY_FAKE_GATE"):
            os.environ.pop(k, None)

    def workers(self, producer, reviewer=None, family="claude", rfamily="claude", pextra=None, rextra=None):
        w = {"producer": dict({"command": producer, "family": family, "model": "fake-producer",
                               "model_family": "Anthropic"}, **(pextra or {})),
             "reviewer": dict({"command": reviewer or CLAUDE_FAKE, "family": rfamily, "model": "fake-reviewer",
                               "model_family": "Anthropic"}, **(rextra or {}))}
        (self.repo / "workers.json").write_text(json.dumps(w))

    def scenario(self, sc):
        (self.repo / "SCENARIO.json").write_text(json.dumps(sc))

    def kit(self, cfg):
        (self.repo / "FAKE_KIT.json").write_text(json.dumps(cfg))

    def args(self, *extra, n=4, budget="100"):
        a = ["run", "--repo", str(self.repo), "--run-dir", "research/excavator/maudslay-test", "--batch", "b01",
             "--agent", "testagent", "--action", "production.test", "--n", str(n), "--route", "route_test.txt",
             "--workers", "workers.json", "--tools", "tools.json", "--scratch-root", str(self.scratch),
             "--wave", "WAVE.json",
             "--item-usd", "2", "--parallel", "2", "--publication", "research/readiness/claims/testagent-b01.jsonl"]
        if budget is not None:
            a += ["--batch-usd", budget]
        return a + list(extra)

    def run_cli(self, *extra, n=4, budget="100"):
        with contextlib.redirect_stdout(io.StringIO()):
            return C.main(self.args(*extra, n=n, budget=budget))

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
        return C.read_jsonl(self.bdir / "LEDGER.jsonl")

    def run_state(self):
        return [r for r in self.ledger() if r["key"] == "run"][-1]

    def calls(self, cmd=None):
        return [c for c in jl(self.repo / "FAKE_CALLS.jsonl") if cmd is None or c["cmd"] == cmd]

    def worker_calls(self, kind=None):
        rows = [r for p in sorted(self.log.parent.glob(self.log.name + ".*")) for r in jl(p)]
        return [c for c in rows if "kind" in c and (kind is None or c["kind"] == kind)]

    def published(self):
        return jl(self.repo / "research/readiness/claims/testagent-b01.jsonl")

    def batch_lines(self):
        p = self.repo / "research/excavator/maudslay-test/BATCHES.json"
        return json.loads(p.read_text()) if p.exists() else []

    def research_files(self):
        return [p for p in (self.repo / "research").rglob("*") if p.is_file()]

    def launched(self, key):
        return next(r["data"] for r in self.ledger() if r["key"] == key and r["status"] == "launched")


class FullBatchTests(ConveyorCase):
    def test_full_batch_files_reviewed_claims_and_measures(self):
        self.kit({"blocked": ["EO:4"]})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertEqual(sorted(c["instrument_id"] for c in self.published()), ["EO:1", "EO:2", "EO:3"])
        self.assertEqual(len(self.worker_calls("producer")), 3)  # EO:4 was source-blocked: no producer
        man = json.loads((self.bdir / "packet/completion/COMPLETION.json").read_text(encoding="utf-8"))
        self.assertEqual({m["instrument_id"]: m["outcome"] for m in man["members"]},
                         {"EO:1": "submit", "EO:2": "submit", "EO:3": "submit", "EO:4": "blocked"})
        self.assertGreaterEqual(len(man["controls"]), 1)
        m = json.loads((self.bdir / "MEASURES.json").read_text(encoding="utf-8"))
        self.assertEqual((m["stages"]["produce"]["workers"], m["stages"]["review"]["workers"],
                          m["stages"]["reveal"]["workers"]), (3, 2, 2))
        self.assertAlmostEqual(m["totals"]["usd"], 3.5)
        self.assertEqual((m["totals"]["filed"], m["human_certified"]), (3, 0))
        self.assertEqual(self.batch_lines(), [{"batch": "b01", "attempted": 4, "submitted": 3, "filed": 3,
                                               "controls_missed": 0, "usd": 3.5}])
        self.assertEqual(json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"], [])
        costs = (self.bdir / "COSTS.log").read_text()
        self.assertEqual(costs.count(" cost "), 7, costs)
        plant = next(r for r in self.ledger() if r["key"] == "plant" and r["status"] == "done")["data"]
        self.assertEqual(set(plant) - {"wall_seconds"}, {"controls", "key_sha256", "claims"})

    def test_rerun_of_a_finished_batch_redoes_nothing(self):
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        before = len(self.worker_calls())
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertEqual((len(self.worker_calls()), len(self.calls("complete"))), (before, 1))


class ControlMaterialTests(ConveyorCase):
    def planted(self):
        key = json.loads((self.control / "b01.json").read_text())
        return {k["planted"] for k in key["controls"]}

    def test_planted_claims_never_enter_research(self):
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        allowed = ("packet/reviews/", "packet/completion/", "packet/complete-v")
        for p in self.research_files():
            text = p.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("1997-01-02", text, p)  # the planted (moved) date: no planted claim body anywhere
            rel = p.relative_to(self.bdir).as_posix() if p.is_relative_to(self.bdir) else p.as_posix()
            if any(sha in text for sha in self.planted()):
                self.assertTrue(rel.startswith(allowed), f"planted hash outside the kit's post-reveal records: {rel}")
        self.assertTrue((self.control / "b01.REVIEW_SET.jsonl").exists())
        salt = json.loads((self.control / "b01.json").read_text())["salt"]
        self.assertFalse(any(salt in p.read_text(encoding="utf-8", errors="replace") for p in self.research_files()))

    def test_no_planted_hash_under_research_before_reveal(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="controls:done"), 137)
        planted = self.planted()
        for p in self.research_files():
            text = p.read_text(encoding="utf-8", errors="replace")
            self.assertFalse(any(sha in text for sha in planted), p)
            self.assertNotIn("1997-01-02", text, p)


class IsolationTests(ConveyorCase):
    def test_every_worker_runs_in_its_own_folder_outside_the_repository(self):
        self.assertEqual(self.run_cli(), C.EXIT_DONE)
        calls = self.worker_calls()
        self.assertEqual(len(calls), 8)
        cwds = [Path(c["cwd"]).resolve() for c in calls]
        self.assertEqual(len(set(cwds)), 8)
        for cwd in cwds:
            self.assertFalse(cwd.is_relative_to(self.repo.resolve()), cwd)
            self.assertEqual(cwd.parent, (self.scratch / "workers").resolve())
            for d in [cwd, *cwd.parents]:
                for name in ("CLAUDE.md", "AGENTS.md"):
                    self.assertFalse((d / name).exists(), d / name)
        # The commands built for each role at check time also point outside the repository.
        b = C.Batch(json.loads((self.bdir / "CONFIG.json").read_text()), self.repo)
        for role in ("producer", "reviewer_A", "reviewer_B"):
            self.assertFalse((b.scratch / "workers").is_relative_to(self.repo.resolve()), role)

    def test_reviewer_folders_hold_only_their_prompt_and_set(self):
        self.assertEqual(self.run_cli(), C.EXIT_DONE)
        rev = self.worker_calls("reviewer")
        blind = [c for c in rev if "review-" in Path(c["cwd"]).name]
        reveal = [c for c in rev if "reveal-" in Path(c["cwd"]).name]
        self.assertEqual((len(blind), len(reveal)), (2, 2))
        for c in blind:
            self.assertEqual(c["files"], ["PROMPT.txt", "REVIEW_SET.jsonl"])
        for c in reveal:
            self.assertEqual(c["files"], ["GENUINE.jsonl", "PROMPT.txt"])
        self.assertNotEqual(blind[0]["cwd"], blind[1]["cwd"])

    def blinding_stop(self, arm, touch):
        self.scenario({"reviewer": {arm: {"touch": [touch]}}})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_STOPPED)
        self.assertIn("blinding", self.run_state()["data"]["reason"])
        self.assertEqual(self.calls("complete"), [])
        rec = next(w for w in C.Ledger(self.bdir / "LEDGER.jsonl").workers() if w["label"] == f"b01-review-{arm}0")
        self.assertTrue(rec["blinding_violations"] and rec["killed"].startswith("blinding"))
        self.assertFalse(rec["ok"])

    def test_reviewer_naming_the_control_folder_fails_the_arm(self):
        self.blinding_stop("A", f"cat {(self.control / 'b01.json').as_posix()}")

    def test_reviewer_naming_batch_material_fails_the_arm(self):
        self.blinding_stop("B", "cat research/excavator/maudslay-test/b01/packet/decisions.csv")

    def test_reviewer_naming_the_other_arms_folder_fails_the_arm(self):
        self.blinding_stop("A", str(self.scratch / "workers" / "b01-review-B0" / "REVIEW_SET.jsonl"))

    def test_scan_allows_own_folder_and_the_frozen_packet_only(self):
        rules = [(C.path_forms("C:/s"), C.re.compile(r"^/workers/me(/.*)?$"), "outside"),
                 (["research/x/b01"], C.re.compile(r"^/packet(/packet\.json)?$"), "batch")]
        ok = ["cat C:\\s\\workers\\me\\REVIEW_SET.jsonl", "load_packet('research/x/b01/packet')",
              "open research/x/b01/packet/PACKET.json", "ls research/x/b01x/other", "cat /c/s/workers/me/a"]
        self.assertEqual(C.scan(ok, rules), [])
        for bad in ("cat C:/s/control/key.json", "ls C:/s/workers", "cat /c/s/workers/meX/a",
                    "cat research/x/b01/packet/decisions.csv", "ls research/x/b01", "grep -r EO research/x/b01/"):
            self.assertTrue(C.scan([bad], rules), bad)


class ResumeTests(ConveyorCase):
    def test_killed_run_resumes_without_redoing_finished_stages(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_2:done"), 137)
        self.assertEqual(len(self.worker_calls("producer")), 2)
        self.assertEqual(self.run_proc("--parallel", "1", kill="plant:done"), 137)
        key_sha = next(r for r in self.ledger() if r["key"] == "plant" and r["status"] == "done")["data"]["key_sha256"]
        self.assertEqual(self.run_proc("--parallel", "1", "--publish"), C.EXIT_DONE)
        self.assertEqual((len(self.calls("next")), len(self.calls("prepare"))), (1, 1))
        self.assertEqual(sorted(c["id"] for c in self.worker_calls("producer")), ["EO:1", "EO:2", "EO:3", "EO:4"])
        self.assertEqual(len(self.worker_calls("reviewer")), 4)
        self.assertEqual(C.fsha(self.control / "b01.json"), key_sha)  # the planted controls were not re-drawn
        self.assertEqual(len(self.published()), 4)
        self.assertEqual(len(self.calls("dispatch-check")), 2)

    def test_orphan_worker_still_running_is_killed_on_resume(self):
        self.scenario({"sleep_once": {"EO:1": 60}})
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_1:launched"), 137)
        pid, epoch = self.launched("produce:EO_1")["pid"], self.launched("produce:EO_1")["launched_epoch"]
        self.assertTrue(C.pid_alive(pid, epoch))
        t0 = time.monotonic()
        self.assertEqual(self.run_proc("--parallel", "1"), C.EXIT_DONE)
        self.assertLess(time.monotonic() - t0, 40)
        self.assertFalse(C.pid_alive(pid, epoch))
        orphan = next(r["data"] for r in self.ledger() if r["key"] == "produce:EO_1" and r["status"] == "done")
        self.assertTrue(orphan["orphaned"] and "killed" in orphan["killed"])
        self.assertTrue(C.Ledger(self.bdir / "LEDGER.jsonl").data("produce:EO_1#2")["ok"])
        m = json.loads((self.bdir / "MEASURES.json").read_text())
        self.assertAlmostEqual(m["stages"]["produce"]["usd"], 2 + 4 * 0.5)  # the orphan counts at its $2 cap

    def test_finished_orphan_output_is_adopted_not_relaunched(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_1:launched"), 137)
        for _ in range(100):
            if self.worker_calls("producer"):
                break
            time.sleep(0.1)
        pid = self.launched("produce:EO_1")["pid"]
        for _ in range(50):
            if not C.pid_alive(pid):
                break
            time.sleep(0.1)
        self.assertEqual(self.run_proc("--parallel", "1"), C.EXIT_DONE)
        self.assertEqual([c["id"] for c in self.worker_calls("producer")].count("EO:1"), 1)
        rec = C.Ledger(self.bdir / "LEDGER.jsonl").data("produce:EO_1")
        self.assertTrue(rec["adopted"] and rec["ok"])

    def test_a_batch_failure_kills_running_worker_trees(self):
        self.scenario({"sleep": {"EO:2": 60}})
        orig = C.Batch.record

        def boom(self, label, *a, **k):
            if "EO_1" in label:
                raise C.Fail("injected failure")
            return orig(self, label, *a, **k)
        t0 = time.monotonic()
        with mock.patch.object(C.Batch, "record", boom):
            self.assertEqual(self.run_cli(), C.EXIT_FAILED)
        self.assertLess(time.monotonic() - t0, 40)
        launched = self.launched("produce:EO_2")
        self.assertFalse(C.pid_alive(launched["pid"], launched["launched_epoch"]))

    def test_kit_next_is_never_called_twice(self):
        self.assertEqual(self.run_proc(kill="reserve:started"), 137)
        self.assertEqual(self.run_proc(), C.EXIT_FAILED)
        self.assertEqual(self.calls("next"), [])
        self.assertIn("kit next is not called twice", self.run_state()["data"]["reason"])

    def test_kill_after_publish_adopts_the_publication(self):
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        rows = (self.bdir / "LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
        cut = next(i for i, l in enumerate(rows) if json.loads(l)["key"] == "complete" and json.loads(l)["status"] == "done")
        (self.bdir / "LEDGER.jsonl").write_text("\n".join(rows[:cut]) + "\n", encoding="utf-8")
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertEqual(len(self.calls("complete")), 1)
        self.assertTrue(C.Ledger(self.bdir / "LEDGER.jsonl").data("complete")["adopted"])
        self.assertEqual(len(self.published()), 4)

    def test_a_torn_ledger_line_does_not_swallow_the_next_record(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_2:done"), 137)
        with open(self.bdir / "LEDGER.jsonl", "ab") as fh:
            fh.write(b'{"utc": "x", "key": "torn')
        self.assertEqual(self.run_proc("--parallel", "1"), C.EXIT_DONE)
        bad = 0
        for line in (self.bdir / "LEDGER.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                json.loads(line)
            except ValueError:
                bad += 1
        self.assertEqual(bad, 1)
        self.assertEqual(self.run_state()["status"], "done")

    def test_fixed_settings_cannot_change_on_resume(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_1:done"), 137)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = C.main([a if a != "production.test" else "production.other" for a in self.args()])
        self.assertEqual(rc, C.EXIT_FAILED)


class PromptCapTests(ConveyorCase):
    def test_prompts_over_the_cap_are_not_dispatched(self):
        self.assertEqual(self.run_cli("--prompt-cap-chars", "3000"), C.EXIT_STOPPED)
        self.assertEqual(self.worker_calls(), [])
        items = json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"]
        self.assertEqual(sorted(i["instrument_id"] for i in items), ["EO:1", "EO:2", "EO:3", "EO:4"])
        self.assertTrue(all(i["kind"] == "prompt_over_cap" and not i["blocks_completion"] for i in items))
        self.assertEqual(self.batch_lines()[0]["filed"], 0)

    def test_every_rendered_prompt_is_within_the_cap_and_names_only_its_order(self):
        self.assertEqual(self.run_cli("--prompt-cap-chars", "12000"), C.EXIT_DONE)
        for p in (self.bdir / "prompts").glob("*.txt"):
            self.assertLessEqual(len(p.read_text(encoding="utf-8")), 12000, p.name)
        text = (self.bdir / "prompts/b01-produce-EO_2.txt").read_text(encoding="utf-8")
        self.assertIn("ORDER: EO:2", text)
        for other in ("EO:1", "EO:3", "EO:4"):
            self.assertNotIn(other, text)
        self.assertIn("decided, synthetic route for tests.", text)


class WorkerCommandTests(ConveyorCase):
    def test_every_worker_call_is_fresh_and_carries_budget_flags(self):
        self.assertEqual(self.run_cli("--item-usd", "1.25"), C.EXIT_DONE)
        calls = self.worker_calls()
        self.assertEqual(len(calls), 8)
        for c in calls:
            a = c["argv"]
            self.assertFalse(set(a) & C.REFUSED_TOKENS, a)
            self.assertEqual(a[a.index("--max-budget-usd") + 1], "1.25")
            self.assertIn("--max-turns", a)
            self.assertEqual(a[a.index("--output-format") + 1], "stream-json")
        self.assertEqual(len({w["session_id"] for w in C.Ledger(self.bdir / "LEDGER.jsonl").workers()}), 8)

    def test_a_role_can_carry_its_own_item_cap(self):
        self.workers(CLAUDE_FAKE, rextra={"item_usd": 7.5})
        self.assertEqual(self.run_cli("--item-usd", "1.25"), C.EXIT_DONE)
        caps = {(c["kind"], c["argv"][c["argv"].index("--max-budget-usd") + 1]) for c in self.worker_calls()}
        self.assertEqual(caps, {("producer", "1.25"), ("reviewer", "7.5")})

    def test_refused_commands(self):
        ok = ["claude", "-p", "--model", "m", "--output-format", "stream-json", "--verbose", "--max-turns", "5",
              "--max-budget-usd", "1"]
        C.validate_worker_command(ok, "claude")
        for bad in (ok + ["--resume", "abc"], ok + ["-c"], ok + ["--continue"], ok + ["-r", "x"], ok + ["--fork-session"],
                    [t if t != "stream-json" else "json" for t in ok], [t for t in ok if t != "--verbose"],
                    ok[:7] + ok[9:], ok + ["--dangerously-skip-permissions"]):
            with self.assertRaises(C.Fail, msg=bad):
                C.validate_worker_command(bad, "claude")
        with self.assertRaises(C.Fail):
            C.validate_worker_command(ok, "codex")  # the program is claude
        with self.assertRaises(C.Fail):
            C.validate_worker_command(ok, "generic")
        cx = C.render_args(C.CODEX_TEMPLATE, {"cwd": "W", "model": "m", "auto_compact_tokens": 1000,
                                              "tool_output_tokens": 100, "writable_roots": '["W"]', "network": "false"})
        C.validate_worker_command(cx, "codex")
        self.assertNotIn("--ephemeral", cx)  # its rollout file is the mid-run meter
        for need in ("--skip-git-repo-check", "--json", "model_auto_compact_token_limit=1000",
                     "tool_output_token_limit=100", 'approval_policy="never"', 'sandbox_mode="workspace-write"',
                     'sandbox_workspace_write.writable_roots=["W"]', "sandbox_workspace_write.network_access=false"):
            self.assertIn(need, cx)
        for bad in (["codex", "exec", "resume", "--last"] + cx[2:], [t if t != "--config" else "-c" for t in cx],
                    cx + ["--config", "rollout_token_budget=1"], cx + ["--ephemeral"], [t for t in cx if t != "--json"],
                    cx + ["--dangerously-bypass-approvals-and-sandbox"]):
            with self.assertRaises(C.Fail, msg=bad):
                C.validate_worker_command(bad, "codex")

    def refused_before_any_work(self, *extra, budget="100"):
        self.assertEqual(self.run_cli(*extra, budget=budget), C.EXIT_FAILED)
        self.assertEqual((self.calls(), self.worker_calls()), ([], []))

    def test_generic_family_is_refused(self):
        self.workers(CLAUDE_FAKE, family="generic")
        self.refused_before_any_work()

    def test_codex_without_a_token_cap_or_prices_is_refused(self):
        self.workers(CODEX_FAKE, family="codex", pextra={"prices_usd_per_mtok": CODEX_OK["prices_usd_per_mtok"]})
        self.refused_before_any_work()
        self.workers(CODEX_FAKE, family="codex", pextra={"item_tokens": 1000})
        self.refused_before_any_work()

    def test_batch_usd_is_required(self):
        self.refused_before_any_work(budget=None)

    def test_codex_spend_counts_at_its_item_cap(self):
        self.workers(CODEX_FAKE, family="codex", pextra=CODEX_OK)
        self.assertEqual(self.run_cli(), C.EXIT_DONE)
        ws = [w for w in C.Ledger(self.bdir / "LEDGER.jsonl").workers() if w["role"] == "producer"]
        self.assertTrue(len(ws) == 4 and all(w["usd"] < 0.1 for w in ws))  # priced cheaply ...
        b = C.Batch(json.loads((self.bdir / "CONFIG.json").read_text()), self.repo)
        self.assertGreaterEqual(b.spent()[0], 4 * 2.0)  # ... yet budgeted at the $2 cap each

    def test_codex_usage_is_read_from_its_json_events(self):
        self.workers(CODEX_FAKE, CODEX_FAKE, "codex", "codex", pextra=CODEX_OK, rextra=CODEX_OK)
        self.scenario({"tokens": 1000})
        self.assertEqual(self.run_cli(), C.EXIT_DONE)
        ws = C.Ledger(self.bdir / "LEDGER.jsonl").workers()
        self.assertTrue(all((w["input"], w["cache_read"], w["output"], w["tokens"]) == (1000, 2000, 1000, 4000)
                            for w in ws))
        self.assertTrue(all(abs(w["usd"] - (1000 * 1.0 + 2000 * 0.1 + 1000 * 8.0) / 1e6) < 1e-9 for w in ws))


class StopRuleTests(ConveyorCase):
    def test_missed_planted_control_stops_the_batch(self):
        self.scenario({"reviewer": {"B": {"miss_controls": True}}})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_STOPPED)
        self.assertEqual((self.calls("complete"), self.published()), ([], []))
        self.assertEqual(len(self.worker_calls("reviewer")), 2)  # no after-reveal sessions
        line = self.batch_lines()[0]
        self.assertGreaterEqual(line["controls_missed"], 1)
        self.assertEqual(line["filed"], 0)
        self.assertTrue(all(c["caught_A"] and not c["caught_B"]
                            for c in json.loads((self.bdir / "CONTROLS.json").read_text())["controls"]))
        self.assertIn("planted control", self.run_state()["data"]["reason"])

    def test_budget_stop_is_a_resumable_pause_with_no_bentham_line(self):
        # Each claude fake reports 4,000 tokens; the token budget allows two producers, then pauses.
        self.assertEqual(self.run_cli("--parallel", "1", "--item-tokens", "4000", "--batch-tokens", "9000"),
                         C.EXIT_BUDGET)
        self.assertEqual(len(self.worker_calls("producer")), 2)
        self.assertEqual(self.run_state()["status"], "budget_paused")
        self.assertIn("batch_token_budget", self.run_state()["data"]["reason"])
        self.assertEqual((self.calls("apply"), self.batch_lines()), ([], []))  # no filed=0 line, no gate
        self.assertFalse([r for r in self.ledger() if r["key"].startswith("gate:")])
        self.assertEqual(self.run_cli("--parallel", "1", "--item-tokens", "4000", "--batch-tokens", "100000"),
                         C.EXIT_DONE)
        self.assertEqual(sorted(c["id"] for c in self.worker_calls("producer")), ["EO:1", "EO:2", "EO:3", "EO:4"])
        self.assertEqual(len(self.batch_lines()), 1)

    def test_batch_usd_below_the_minimum_is_refused_and_the_minimum_printed(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = C.main(self.args(budget="20"))
        self.assertEqual(rc, C.EXIT_FAILED)
        # 4 producers + 4 repairs at $2, plus (1 blind chunk + 1 reveal) x 2 arms at $2.
        self.assertIn('"minimum_batch_usd": 24.0', out.getvalue())
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.run_cli(budget="24"), C.EXIT_DONE)

    def test_review_chunk_defaults_to_ten(self):
        self.assertEqual(self.run_cli(n=4), C.EXIT_DONE)
        self.assertEqual(json.loads((self.bdir / "CONFIG.json").read_text())["review_chunk"], 10)
        self.assertEqual(sum("review-" in Path(c["cwd"]).name for c in self.worker_calls("reviewer")), 2)

    def test_review_chunks_split_each_arm(self):
        self.assertEqual(self.run_cli("--review-chunk", "2", n=4), C.EXIT_DONE)
        self.assertEqual(sum("review-" in Path(c["cwd"]).name for c in self.worker_calls("reviewer")), 4)

    def test_zero_submittable_after_producers_stops_and_writes_a_batch_line(self):
        self.scenario({"producer": {f"EO:{i}": "block" for i in range(1, 5)}})
        self.assertEqual(self.run_cli(), C.EXIT_STOPPED)
        self.assertIn("zero orders submittable", self.run_state()["data"]["reason"])
        self.assertEqual(self.calls("apply"), [])
        self.assertEqual(self.batch_lines(), [{"batch": "b01", "attempted": 4, "submitted": 0, "filed": 0,
                                               "controls_missed": 0, "usd": 2.0}])

    def test_codex_token_cap_is_read_from_the_rollout_mid_turn(self):
        # One codex turn of 6 model calls, 4,000 tokens each; --json reports usage only at the end of the turn.
        self.workers(CODEX_FAKE, family="codex", pextra=dict(CODEX_OK, item_tokens=6000))
        self.scenario({"turns": 6, "turn_sleep": 0.5, "tokens": 1000})
        self.assertEqual(self.run_cli(n=2), C.EXIT_STOPPED)  # both producers killed: zero submittable
        ws = C.Ledger(self.bdir / "LEDGER.jsonl").workers()
        self.assertEqual(len(ws), 2)
        for w in ws:
            self.assertIn("(rollout)", w["killed"])
            self.assertFalse(w["result_seen"])  # killed before turn.completed
            self.assertTrue(8000 <= w["tokens"] <= 12000, w["tokens"])  # the spend comes from the rollout
            self.assertTrue(w["rollout"]["path"].startswith(self.codex_home.as_posix()))
        items = json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"]
        self.assertEqual({i["kind"] for i in items}, {"over_item_cap"})

    def test_item_token_cap_kills_a_claude_worker_from_stream_json(self):
        self.scenario({"turns": 6, "turn_sleep": 0.4, "tokens": 1000})
        self.assertEqual(self.run_cli("--item-tokens", "3000", n=2), C.EXIT_STOPPED)
        ws = C.Ledger(self.bdir / "LEDGER.jsonl").workers()
        self.assertTrue(all(w["killed"] and "item_token_cap" in w["killed"] and not w["result_seen"] for w in ws))


class GateTests(ConveyorCase):
    def test_gate_without_a_verdict_is_a_distinct_exit(self):
        os.environ["MAUDSLAY_FAKE_GATE"] = "REFUSE"
        self.assertEqual(self.run_cli("--publish"), C.EXIT_NO_GATE)
        self.assertEqual(len(self.published()), 4)
        gate = [r for r in self.ledger() if r["key"].startswith("gate:")][-1]["data"]["verdict"]
        self.assertIsNone(gate["decision"])
        self.assertIn("not a ranked production action", gate["refused"])

    def test_gate_stop_is_its_own_exit(self):
        os.environ["MAUDSLAY_FAKE_GATE"] = "STOP"
        self.assertEqual(self.run_cli(), C.EXIT_GATE_STOP)


class AdjudicationTests(ConveyorCase):
    def test_arm_disagreement_goes_to_adjudicate_not_to_a_decision(self):
        self.scenario({"reviewer": {"A": {"reject": ["EO:2"]}}})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_PAUSED)
        self.assertEqual(self.calls("complete"), [])
        items = json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"]
        self.assertEqual([(i["instrument_id"], i["kind"], i["blocks_completion"]) for i in items],
                         [("EO:2", "arm_disagreement", True)])
        self.assertEqual(items[0]["arm_A"]["verdict"], "rejected")
        # A decision written where workers could reach it (the batch folder) is not read.
        (self.bdir / "ADJUDICATION.json").write_text(json.dumps({"decisions": [
            {"instrument_id": "EO:2", "claim_sha256": items[0]["claim_sha256"], "decision": "file", "adjudicator": "x"}]}))
        self.assertEqual(self.run_cli("--publish"), C.EXIT_PAUSED)
        time.sleep(0.05)
        (self.control / "ADJUDICATION.json").write_text(json.dumps({"decisions": [
            {"instrument_id": "EO:2", "claim_sha256": items[0]["claim_sha256"], "decision": "block",
             "reason": "arm A's defect stands", "adjudicator": "coord"}]}))
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertEqual(sorted(c["instrument_id"] for c in self.published()), ["EO:1", "EO:3", "EO:4"])
        man = json.loads((self.bdir / "packet/completion/COMPLETION.json").read_text(encoding="utf-8"))
        eo2 = next(m for m in man["members"] if m["instrument_id"] == "EO:2")
        self.assertEqual(eo2["outcome"], "blocked")
        self.assertIn("Coordinator adjudication (coord)", eo2["reason"])
        receipt = json.loads((self.bdir / "ADJUDICATION.json").read_text())
        self.assertEqual(receipt["decisions"][0]["decision"], "block")  # the control copy, pinned as a receipt
        self.assertIn("research/excavator/maudslay-test/b01/ADJUDICATION.json", [r["path"] for r in man["receipts"]])
        self.assertEqual(len(self.worker_calls("reviewer")), 4)  # no review was rerun

    def test_adjudication_must_name_the_claim_hash_and_an_adjudicator(self):
        self.scenario({"reviewer": {"A": {"reject": ["EO:2"]}}})
        self.assertEqual(self.run_cli(), C.EXIT_PAUSED)
        time.sleep(0.05)
        (self.control / "ADJUDICATION.json").write_text(json.dumps({"decisions": [
            {"instrument_id": "EO:2", "decision": "block", "adjudicator": "coord"}]}))
        self.assertEqual(self.run_cli(), C.EXIT_FAILED)
        sha = json.loads((self.bdir / "ADJUDICATE.json").read_text())["items"][0]["claim_sha256"]
        (self.control / "ADJUDICATION.json").write_text(json.dumps({"decisions": [
            {"instrument_id": "EO:2", "claim_sha256": sha, "decision": "block"}]}))
        self.assertEqual(self.run_cli(), C.EXIT_FAILED)

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
        self.assertEqual(sorted(c["id"] for c in self.worker_calls("producer") if c["repair"]), ["EO:2", "EO:3"])
        self.assertEqual(sorted(c["instrument_id"] for c in self.published()), ["EO:1", "EO:2", "EO:4"])
        man = json.loads((self.bdir / "packet/completion/COMPLETION.json").read_text(encoding="utf-8"))
        eo3 = next(m for m in man["members"] if m["instrument_id"] == "EO:3")
        self.assertEqual(eo3["outcome"], "blocked")
        self.assertIn("mechanical checks failed", eo3["reason"])
        # The repair ran in a new folder; the first sheet is kept.
        self.assertTrue((self.scratch / "workers/b01-produce-EO_3/decisions.csv").exists())
        self.assertTrue((self.scratch / "workers/b01-repair1-EO_3/decisions.csv").exists())

    def test_invalid_sheet_is_not_used(self):
        self.scenario({"producer": {"EO:1": "bad_sheet"}})
        self.assertEqual(self.run_cli("--publish"), C.EXIT_DONE)
        self.assertNotIn("EO:1", [c["instrument_id"] for c in self.published()])
        _, rows = C.read_csv(self.bdir / "packet/decisions.csv")
        r = next(r for r in rows if r["instrument_id"] == "EO:1")
        self.assertEqual(r["outcome"], "unresolved")
        self.assertIn("producer sheet invalid", r["unresolved_material_gaps"])


class GuardTests(ConveyorCase):
    def test_a_second_process_on_the_same_batch_is_refused(self):
        holder = subprocess.Popen([PY, "-c", "import time; time.sleep(60)"])
        self.addCleanup(holder.kill)
        self.bdir.mkdir(parents=True)
        (self.bdir / "RUN.lock").write_text(json.dumps({"pid": holder.pid, "epoch": time.time()}))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(C.main(self.args()), C.EXIT_FAILED)
        self.assertIn("another conveyor process", out.getvalue())
        self.assertEqual(self.calls(), [])

    def test_a_stale_lock_of_a_dead_process_is_cleared(self):
        dead = subprocess.Popen([PY, "-c", "pass"])
        dead.wait()
        self.bdir.mkdir(parents=True)
        (self.bdir / "RUN.lock").write_text(json.dumps({"pid": dead.pid, "epoch": time.time()}))
        self.assertEqual(self.run_cli(), C.EXIT_DONE)
        self.assertFalse((self.bdir / "RUN.lock").exists())  # released at the end of the run

    def batch(self):
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(C, "run", lambda cfg, repo: cfg):
            cfg = C.main(self.args())
        return C.Batch(cfg, self.repo)

    def test_lock_is_exclusive_while_a_run_holds_it(self):
        b = self.batch()
        b.lock()
        with self.assertRaises(C.Fail):
            b.lock()  # held by this live test process

    def test_scratch_root_is_required_and_not_in_temp(self):
        args = self.args()
        i = args.index("--scratch-root")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(C.main(args[:i] + args[i + 2:]), C.EXIT_FAILED)
        os.environ.pop("MAUDSLAY_TEST_ALLOW_TEMP_SCRATCH")
        self.assertEqual(self.run_cli(), C.EXIT_FAILED)  # the test scratch root sits in the system temp folder
        self.assertEqual(self.calls(), [])

    def test_lost_producer_folder_is_a_hard_failure_on_resume(self):
        import shutil
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_2:done"), 137)
        shutil.rmtree(self.scratch / "workers" / "b01-produce-EO_1")
        self.assertEqual(self.run_proc("--parallel", "1"), C.EXIT_FAILED)
        self.assertIn("scratch lost", self.run_state()["data"]["reason"])
        self.assertEqual(sorted(c["id"] for c in self.worker_calls("producer")), ["EO:1", "EO:2"])

    def test_missing_control_key_is_a_clear_error(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="plant:done"), 137)
        (self.control / "b01.json").unlink()
        self.assertEqual(self.run_proc("--parallel", "1"), C.EXIT_FAILED)
        self.assertIn("control material missing", self.run_state()["data"]["reason"])

    def test_a_changed_workers_file_is_refused_on_resume(self):
        self.assertEqual(self.run_proc("--parallel", "1", kill="produce:EO_1:done"), 137)
        self.workers(CLAUDE_FAKE, rextra={"model_family": "OpenAI"})
        self.assertEqual(self.run_proc("--parallel", "1"), C.EXIT_FAILED)
        self.assertIn("workers file changed", self.run_state()["data"]["reason"])

    def test_augur_refusal_stops_the_run_before_any_work(self):
        wave_plan(self.repo / "WAVE.json", "production.test", 8, reviewed=False)  # real check(): no review
        self.assertEqual(self.run_cli(), C.EXIT_FAILED)
        self.assertEqual(self.calls(), [])
        receipt = next(r for r in self.ledger() if r["key"] == "augur:1")["data"]
        self.assertEqual(receipt["verdict"], "REFUSE")
        self.assertTrue(any("review" in x for x in receipt["refusals"]))

    def test_batch_must_fit_one_of_the_plans_actions(self):
        wave_plan(self.repo / "WAVE.json", "production.test", 3)  # passes Augur, but only 3 orders
        self.assertEqual(self.run_cli(n=4), C.EXIT_FAILED)
        receipt = next(r for r in self.ledger() if r["key"] == "augur:1")["data"]
        self.assertEqual((receipt["verdict"], receipt["fits"]), ("PASS", False))
        self.assertEqual(self.calls(), [])

    def test_a_substituted_refusing_check_is_obeyed(self):
        with mock.patch.object(C, "check_plan", lambda mod, plan, repo: (["stub refusal"], {"verdict": "REFUSE"})):
            self.assertEqual(self.run_cli(), C.EXIT_FAILED)
        self.assertEqual(self.calls(), [])

    def test_reviewers_may_read_undecided_evidence(self):
        b = self.batch()
        rules = b.rules_for("reviewer_A", b.scratch / "workers" / "b01-review-A0")
        batch = "research/excavator/maudslay-test/b01"
        self.assertEqual(C.scan([f"cat {batch}/packet/undecided/EO_5/EVIDENCE.json", f"ls {batch}/packet/undecided",
                                 f"load_packet('{batch}/packet')"], rules), [])
        self.assertTrue(C.scan([f"cat {batch}/packet/undecided/EO_5/STATUS_DECISION.json"], rules))
        self.assertTrue(C.scan([f"cat {batch}/packet/decisions.csv"], rules))


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
        self.scratch = Path(k.name) / "scratch"
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
        # Bentham's plan and the action's strata (the kit's admission check reads them) and a wave Augur passes.
        stub_bentham(self.repo, "production.fixture", members=[f"EO:{i}" for i in range(1, 7)])
        wave_plan(self.repo / "WAVE.json", "production.fixture", 2)
        p = mock.patch.dict(os.environ, {"MAUDSLAY_FAKE_SCENARIO": str(self.repo / "SCENARIO.json"),
                                         "MAUDSLAY_FAKE_LOG": str(self.repo / "WORKER_LOG.jsonl"),
                                         "MAUDSLAY_TEST_ALLOW_TEMP_SCRATCH": "1"})
        p.start()
        self.addCleanup(p.stop)

    def test_real_kit_reserve_prepare_apply_check_and_complete(self):
        with contextlib.redirect_stdout(io.StringIO()):
            rc = C.main(["run", "--repo", str(self.repo), "--run-dir", "research/excavator/real", "--batch", "r01",
                         "--agent", "producer", "--action", "production.fixture", "--n", "2", "--route", "route.txt",
                         "--workers", "workers.json", "--tools", "tools.json", "--scratch-root", str(self.scratch),
                         "--wave", "WAVE.json", "--item-usd", "1", "--batch-usd", "20", "--publish",
                         "--publication", "research/readiness/claims/producer-r01.jsonl"])
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

    def test_caught_reads_only_whole_words_in_defects(self):
        self.assertTrue(C.caught({"verdict": "rejected", "defects": [{"field": "first_end.date"}]}))
        self.assertTrue(C.caught({"verdict": "rejected", "defects": ["whole_order_end is three years early"]}))
        self.assertTrue(C.caught({"verdict": "rejected", "defects": ["the signing date is wrong"]}))
        for rec in ({"verdict": "rejected", "defects": ["quote mismatch"], "reasons": "the mandate lapsed"},
                    {"verdict": "rejected", "defects": ["quote mismatch"], "reasons": "signing date confirmed"},
                    {"verdict": "rejected", "defects": ["the mandate was updated"]},
                    {"verdict": "upheld", "defects": []}, None):
            self.assertFalse(C.caught(rec), rec)

    def test_stream_json_usage(self):
        events = [{"type": "system", "session_id": "s"},
                  {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 5, "output_tokens": 1}}},
                  {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 5, "output_tokens": 3}}},
                  {"type": "assistant", "message": {"id": "b", "usage": {"input_tokens": 7, "cache_read_input_tokens": 100,
                                                                         "output_tokens": 2}}}]
        u = C.parse_usage("\n".join(json.dumps(e) for e in events))
        self.assertEqual((u["session_id"], C.tokens(u), u["result_seen"]), ("s", 5 + 3 + 7 + 100 + 2, False))
        events.append({"type": "result", "session_id": "s", "total_cost_usd": 0.7, "num_turns": 4, "usage": {
            "input_tokens": 10, "cache_read_input_tokens": 200, "cache_creation_input_tokens": 30, "output_tokens": 5}})
        u = C.parse_usage("\n".join(json.dumps(e) for e in events))
        self.assertEqual((u["usd"], C.tokens(u), u["result_seen"]), (0.7, 245, True))

    def test_move_aside_reports_a_held_folder(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "packet"
            p.mkdir()
            with mock.patch.object(C.os, "replace", side_effect=PermissionError("in use")):
                with self.assertRaises(C.Fail):
                    C.move_aside(p, "packet.incomplete")
            self.assertEqual(C.move_aside(p, "packet.incomplete").name, "packet.incomplete-1")


if __name__ == "__main__":
    unittest.main()
