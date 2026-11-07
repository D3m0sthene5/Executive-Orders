#!/usr/bin/env python3
"""Offline tests for driver.py using the dry runner. Run: python3 -I research/hollerith-drivers/test_driver.py"""
import ast
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import driver as D  # noqa: E402

ROW_FIELDS = ['instrument_id', 'dossier_sha256', 'agent', 'outcome', 'approved', 'original_confirmed',
              'original_pages_confirmed', 'inventory_confirmed', 'research_rationale', 'savings_state', 'savings_source_id',
              'savings_reason', 'search_ids', 'conflict_resolutions', 'unresolved_material_gaps', 'earlier_end_check',
              'scope_check', 'independent_command_check', 'savings_check', 'working_text', 'source_notes', 'publication_kind']
CLAUSE_FIELDS = ['instrument_id', 'scope_id', 'clause_id', 'state', 'end_id', 'effective_date', 'mechanism',
                 'effective_date_confirmed', 'current_basis_id', 'current_legal_basis', 'checked_through',
                 'later_event_ids', 'later_events', 'reason', 'inventory_source_id', 'inventory_char_start',
                 'inventory_char_end', 'inventory_reason']
NOW = datetime(2026, 11, 6, 12, 0, 0, tzinfo=timezone.utc)


def clock():
    return NOW


def good_review(**over):
    out = {"decision": "accept", "locus": "operative_clauses[0].first_end.source.quote",
           "reason": "The quoted span is present at the offsets and revokes the order outright.", "confidence": 0.8}
    out.update(over)
    return out


def good_draft(ids=("EO:100",), state="terminated"):
    decisions, clauses = [], []
    for iid in ids:
        decisions.append({"instrument_id": iid, "outcome": "submit", "approved": True, "original_confirmed": True,
                          "original_pages_confirmed": True, "inventory_confirmed": True,
                          "research_rationale": "Read the original and the revoking order.", "savings_state": "none_after_bounded_search",
                          "savings_source_id": "SAV:1", "savings_reason": "@rationale:SAV", "search_ids": ["S1"],
                          "conflict_resolutions": {}, "unresolved_material_gaps": [],
                          "earlier_end_check": "No earlier end.", "scope_check": "One clause.",
                          "independent_command_check": "None.", "savings_check": "@rationale:SAV", "publication_kind": "whole_case"})
        row = {"instrument_id": iid, "scope_id": iid + "#1", "state": state, "end_id": "EV:1", "effective_date": "1990-01-02",
               "effective_date_confirmed": True, "current_basis_id": None, "current_legal_basis": "", "checked_through": None,
               "later_event_ids": [], "later_events": [], "reason": "Revoked in terms."}
        if state == "operative":
            row.update(end_id=None, effective_date=None, current_basis_id="CUR:1", current_legal_basis="Still in force.",
                       checked_through=D.LEGAL_CUTOFF)
        clauses.append(row)
    return {"decisions": decisions, "clauses": clauses, "rationales": {"SAV": "Searched; nothing found."}}


def make_packet(root, ids=("EO:100",)):
    root.mkdir(parents=True)
    (root / "PACKET.json").write_text(json.dumps({"fingerprint": "f" * 64, "legal_cutoff": D.LEGAL_CUTOFF}), encoding="utf-8")
    (root / "READ.md").write_text("# packet\nEO:100 text\n", encoding="utf-8")
    drows = [{**{k: "" for k in ROW_FIELDS}, "instrument_id": i, "dossier_sha256": "a" * 64, "agent": "prod", "outcome": "unresolved",
              "approved": "false", "original_confirmed": "false", "original_pages_confirmed": "false", "working_text": "{}",
              "inventory_confirmed": "false", "search_ids": "[]", "conflict_resolutions": "{}", "unresolved_material_gaps": "[]"}
             for i in ids]
    crows = [{**{k: "" for k in CLAUSE_FIELDS}, "instrument_id": i, "scope_id": i + "#1", "clause_id": "CLAUSES:" + i + "#1"} for i in ids]
    D.write_csv(root / "decisions.csv", ROW_FIELDS, drows)
    D.write_csv(root / "clauses.csv", CLAUSE_FIELDS, crows)
    (root / "RATIONALES.json").write_text("{}", encoding="utf-8")


def make_args(tmp, **over):
    ns = type("A", (), {})()
    ns.repo = str(tmp)
    ns.kit = None
    ns.model = "claude-sonnet-5-5"
    ns.model_family = "Anthropic"
    ns.cost_log = str(tmp / "cost.jsonl")
    ns.timeout = 60
    ns.packet_label = None
    ns.no_dispatch_check = True
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


def write_log(path, rows):
    for r in rows:
        D.append_log(path, r)


def write_card(tmp, claim_extra=None, card_dir="cards", item_key=True):
    root = tmp / "src"
    (root / "texts").mkdir(parents=True)
    text = "Executive Order 100. The order is hereby revoked.\r\n"
    (root / "texts" / "eo100.txt").write_bytes(text.encode())
    claim = {"instrument_id": "EO:100", "whole_order_status": "NO",
             "operative_clauses": [{"scope_id": "EO:100#1", "first_end": {"date": "1990-01-02", "source": {
                 "text_path": "texts/eo100.txt", "text_sha256": D.sha256_bytes(text.encode()), "quote": "hereby revoked",
                 "char_start": 30, "char_end": 44}}}]}
    claim.update(claim_extra or {})
    d = tmp / card_dir
    d.mkdir(exist_ok=True)
    path = d / "card.json"
    path.write_text(json.dumps({"item_id": "item-7", "track": "C", "claim": claim} if item_key else claim), encoding="utf-8")
    return path, root


class SchemaTests(unittest.TestCase):
    def test_review_rejects_unknown_missing_and_bad_values(self):
        self.assertEqual(D.validate(good_review(), D.REVIEW_SCHEMA), [])
        self.assertTrue(any("unknown field" in e for e in D.validate(good_review(verdict="upheld"), D.REVIEW_SCHEMA)))
        self.assertTrue(any("missing locus" in e for e in D.validate({"decision": "accept", "reason": "x" * 50, "confidence": 1}, D.REVIEW_SCHEMA)))
        self.assertTrue(D.validate(good_review(decision="maybe"), D.REVIEW_SCHEMA))
        self.assertTrue(D.validate(good_review(confidence=1.5), D.REVIEW_SCHEMA))
        self.assertTrue(D.validate(good_review(reason="short"), D.REVIEW_SCHEMA))
        self.assertTrue(D.validate(good_review(confidence=True), D.REVIEW_SCHEMA))

    def test_draft_schema_matches_claim_kit_columns(self):
        """Every model-supplied draft field is a real claim-kit CSV column (when batch.py is in the checkout)."""
        batch = HERE.parents[1] / "jobs/claim-kit/batch.py"
        if not batch.exists():
            self.skipTest("batch.py not in this checkout")
        tree = ast.parse(batch.read_text(encoding="utf-8"))
        cols = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("ROW_FIELDS", "CLAUSE_FIELDS"):
                cols[node.targets[0].id] = set(ast.literal_eval(node.value))
        self.assertLessEqual(set(D.DECISION_SCHEMA["properties"]), cols["ROW_FIELDS"])
        self.assertLessEqual(set(D.CLAUSE_SCHEMA["properties"]), cols["CLAUSE_FIELDS"])
        self.assertEqual(cols["ROW_FIELDS"] - set(D.DECISION_SCHEMA["properties"]), {"dossier_sha256", "agent"})
        self.assertEqual(cols["CLAUSE_FIELDS"] - set(D.CLAUSE_SCHEMA["properties"]), set())

    def test_draft_schema_accepts_good_and_rejects_bad_state(self):
        self.assertEqual(D.validate(good_draft(), D.DRAFT_SCHEMA), [])
        bad = good_draft()
        bad["clauses"][0]["state"] = "revoked"
        self.assertTrue(D.validate(bad, D.DRAFT_SCHEMA))
        bad = good_draft()
        bad["decisions"][0]["savings_state"] = "maybe"
        self.assertTrue(D.validate(bad, D.DRAFT_SCHEMA))


class RetryAndLogTests(unittest.TestCase):
    def test_schema_rejection_retries_once_then_fails_and_logs_both_attempts(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            runner = D.DryRunner([{"decision": "nope"}, {"decision": "still nope"}, good_review()])
            with self.assertRaises(D.StageFailed):
                D.run_stage(stage="review", packet="EO:1", role="r1", prompt="P", system="S", schema=D.REVIEW_SCHEMA,
                            semantic=lambda o: [], runner=runner, model="m", policy=D.CapPolicy(), log_path=tmp / "c.jsonl", clock=clock)
            self.assertEqual(len(runner.calls), 2)                     # one retry only, never a third call
            rows = D.read_log(tmp / "c.jsonl")
            self.assertEqual([r["outcome"] for r in rows], ["schema_invalid", "schema_invalid"])
            self.assertEqual([r["attempt"] for r in rows], [1, 2])
            self.assertIn("rejected for these format", runner.calls[1].prompt)   # the retry carries the validation errors

    def test_retry_can_succeed(self):
        with tempfile.TemporaryDirectory() as t:
            runner = D.DryRunner(["ERROR: timeout", good_review()])
            res = D.run_stage(stage="review", packet="EO:1", role="r1", prompt="P", system="S", schema=D.REVIEW_SCHEMA,
                              semantic=lambda o: [], runner=runner, model="m", policy=D.CapPolicy(), log_path=Path(t) / "c.jsonl", clock=clock)
            self.assertEqual(res["attempts"], 2)
            self.assertEqual([r["outcome"] for r in D.read_log(Path(t) / "c.jsonl")], ["runner_error", "ok"])

    def test_cost_log_fields_and_tokens_by_type(self):
        with tempfile.TemporaryDirectory() as t:
            tokens = {"input": 100, "output": 20, "cache_creation": 300, "cache_read": 4000}
            runner = D.DryRunner([good_review()], cost_usd=0.0123, tokens=tokens)
            D.run_stage(stage="review", packet="EO:7", role="rev-a", prompt="P", system="S", schema=D.REVIEW_SCHEMA,
                        semantic=lambda o: [], runner=runner, model="claude-opus-5-5", policy=D.CapPolicy(), log_path=Path(t) / "c.jsonl", clock=clock)
            row = D.read_log(Path(t) / "c.jsonl")[0]
            for key in ("ts", "stage", "packet", "model", "tokens", "total_cost_usd", "wall_seconds", "auth_basis", "outcome"):
                self.assertIn(key, row)
            self.assertEqual((row["stage"], row["packet"], row["model"]), ("review", "EO:7", "claude-opus-5-5"))
            self.assertEqual(row["tokens"], tokens)
            self.assertEqual(row["total_cost_usd"], 0.0123)
            self.assertFalse(row["cost_assumed"])
            self.assertEqual(row["ts"], "2026-11-06T12:00:00Z")
            summary = D.summarize(D.read_log(Path(t) / "c.jsonl"), "2026-11-06")
            self.assertEqual(summary["today_counted_usd"], 0.0123)
            self.assertEqual(summary["by_stage"]["review"]["cache_read"], 4000)

    def test_unreported_cost_counts_as_the_granted_budget(self):
        with tempfile.TemporaryDirectory() as t:
            runner = D.DryRunner([good_review()], cost_usd=None)
            D.run_stage(stage="review", packet="p", role="r", prompt="P", system="S", schema=D.REVIEW_SCHEMA, semantic=lambda o: [],
                        runner=runner, model="m", policy=D.CapPolicy(run=1.5), log_path=Path(t) / "c.jsonl", clock=clock)
            row = D.read_log(Path(t) / "c.jsonl")[0]
            self.assertTrue(row["cost_assumed"])
            self.assertIsNone(row["total_cost_usd"])
            self.assertEqual(row["cost_counted_usd"], 1.5)


class CapTests(unittest.TestCase):
    def test_daily_cap_refuses_before_any_call(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / "c.jsonl"
            write_log(log, [{"ts": "2026-11-06T01:00:00Z", "cost_counted_usd": 10.0}])
            runner = D.DryRunner([good_review()])
            with self.assertRaises(D.CapReached):
                D.run_stage(stage="review", packet="p", role="r", prompt="P", system="S", schema=D.REVIEW_SCHEMA, semantic=lambda o: [],
                            runner=runner, model="m", policy=D.CapPolicy(run=2, day=10, total=100), log_path=log, clock=clock)
            self.assertEqual(runner.calls, [])

    def test_yesterdays_spend_does_not_count_against_today(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / "c.jsonl"
            write_log(log, [{"ts": "2026-11-05T23:59:00Z", "cost_counted_usd": 9.99}])
            res = D.run_stage(stage="review", packet="p", role="r", prompt="P", system="S", schema=D.REVIEW_SCHEMA, semantic=lambda o: [],
                              runner=D.DryRunner([good_review()]), model="m", policy=D.CapPolicy(day=10), log_path=log, clock=clock)
            self.assertEqual(res["attempts"], 1)

    def test_campaign_total_cap(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / "c.jsonl"
            write_log(log, [{"ts": "2026-10-01T00:00:00Z", "cost_counted_usd": 60.0}, {"ts": "2026-10-02T00:00:00Z", "cost_counted_usd": 40.0}])
            with self.assertRaises(D.CapReached):
                D.run_stage(stage="review", packet="p", role="r", prompt="P", system="S", schema=D.REVIEW_SCHEMA, semantic=lambda o: [],
                            runner=D.DryRunner([good_review()]), model="m", policy=D.CapPolicy(total=100), log_path=log, clock=clock)

    def test_per_run_cap_blocks_the_retry(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / "c.jsonl"
            runner = D.DryRunner([{"decision": "bad"}, good_review()], cost_usd=1.2)
            with self.assertRaises(D.StageFailed):
                D.run_stage(stage="review", packet="p", role="r", prompt="P", system="S", schema=D.REVIEW_SCHEMA, semantic=lambda o: [],
                            runner=runner, model="m", policy=D.CapPolicy(run=1.0), log_path=log, clock=clock)
            self.assertEqual(len(runner.calls), 1)              # the cap stopped the retry
            self.assertEqual(len(D.read_log(log)), 1)

    def test_budget_granted_to_each_attempt_is_the_smallest_remaining_cap(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / "c.jsonl"
            write_log(log, [{"ts": "2026-11-06T01:00:00Z", "cost_counted_usd": 9.0}])
            runner = D.DryRunner([good_review()])
            D.run_stage(stage="review", packet="p", role="r", prompt="P", system="S", schema=D.REVIEW_SCHEMA, semantic=lambda o: [],
                        runner=runner, model="m", policy=D.CapPolicy(run=2, day=10, total=100), log_path=log, clock=clock)
            self.assertAlmostEqual(runner.calls[0].budget_usd, 1.0)

    def test_cli_exits_3_and_calls_nothing_when_cap_reached(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp)
            log = tmp / "cost.jsonl"
            write_log(log, [{"ts": "2026-11-06T00:00:00Z", "cost_counted_usd": 5.0}])
            runner = D.DryRunner([good_review()])
            code = D.main(["review", "--runner", "dry", "--repo", str(tmp), "--card", str(card), "--source-root", str(root),
                           "--allow-source-root", "texts", "--reviewer", "r1", "--scope", "whole_case", "--out", str(tmp / "out.json"),
                           "--cost-log", str(log), "--max-day-usd", "5"], runner=runner, clock=clock)
            self.assertEqual(code, 3)
            self.assertEqual(runner.calls, [])
            self.assertFalse((tmp / "out.json").exists())


class BlindingTests(unittest.TestCase):
    def run_review(self, tmp, card, root, runner=None, scope="whole_case", extra=()):
        runner = runner or D.DryRunner([good_review()])
        code = D.main(["review", "--runner", "dry", "--repo", str(tmp), "--card", str(card), "--source-root", str(root),
                       "--allow-source-root", "texts", "--reviewer", "rev-a", "--scope", scope, "--out", str(tmp / "out.json"),
                       "--cost-log", str(tmp / "cost.jsonl"), *extra], runner=runner, clock=clock)
        return code, runner

    def test_reviewer_prompt_has_only_card_and_sources(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp)
            # a genuine counterpart, a key and another review sit in the repo; none may reach the prompt
            (tmp / "key").mkdir()
            (tmp / "key" / "KEY.sealed.json").write_text(json.dumps({"item-7": {"defect": "D3", "genuine_claim_sha256": "z" * 64}}), encoding="utf-8")
            (tmp / "other-review.json").write_text(json.dumps({"verdict": "rejected", "reason": "UNIQUE-OTHER-REVIEW-TEXT"}), encoding="utf-8")
            code, runner = self.run_review(tmp, card, root)
            self.assertEqual(code, 0)
            prompt = runner.calls[0].prompt
            self.assertIn("hereby revoked", prompt)
            self.assertIn("The order is hereby revoked.", prompt)
            for forbidden in ("UNIQUE-OTHER-REVIEW-TEXT", "genuine_claim_sha256", "KEY.sealed", "SEEDED", "defect"):
                self.assertNotIn(forbidden, prompt)
            self.assertNotIn(str(tmp), prompt)                          # no repository paths
            record = json.loads((tmp / "out.json").read_text(encoding="utf-8"))
            self.assertEqual(record["claim_sha256"], D.sha256_text(D.canon(json.loads(card.read_text(encoding="utf-8"))["claim"])))
            self.assertEqual((record["verdict"], record["scope"], record["independent"], record["separate_context"],
                              record["reviewer"], record["instrument_id"]), ("upheld", "whole_case", True, True, "rev-a", "EO:100"))
            receipt = json.loads((tmp / "out.json.receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["sources"][0]["path"], "texts/eo100.txt")

    def test_refuses_card_with_seeding_marker(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp, {"instrument_id": "SEEDED:EO:100"})
            code, runner = self.run_review(tmp, card, root)
            self.assertEqual(code, 4)
            self.assertEqual(runner.calls, [])

    def test_refuses_card_carrying_a_review_or_verdict_field(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp, {"review": {"verdict": "upheld"}})
            code, runner = self.run_review(tmp, card, root)
            self.assertEqual(code, 4)
            self.assertEqual(runner.calls, [])

    def test_refuses_card_in_a_key_directory(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp, card_dir="key")
            code, runner = self.run_review(tmp, card, root)
            self.assertEqual(code, 4)
            self.assertEqual(runner.calls, [])

    def test_source_outside_allowed_root_or_with_wrong_hash_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp)
            (root / "texts" / "eo100.txt").write_bytes(b"tampered")
            code, runner = self.run_review(tmp, card, root)
            self.assertEqual(code, 2)
            self.assertEqual(runner.calls, [])
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp)
            code = D.main(["review", "--runner", "dry", "--repo", str(tmp), "--card", str(card), "--source-root", str(root),
                           "--allow-source-root", "elsewhere", "--reviewer", "r", "--scope", "whole_case", "--out", str(tmp / "o.json"),
                           "--cost-log", str(tmp / "c.jsonl")], runner=D.DryRunner([good_review()]), clock=clock)
            self.assertEqual(code, 2)

    def test_no_option_exists_to_show_a_reviewer_another_review_or_key(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp)
            with self.assertRaises(SystemExit):
                D.main(["review", "--runner", "dry", "--card", str(card), "--source-root", str(root), "--allow-source-root", "texts",
                        "--reviewer", "r", "--scope", "whole_case", "--out", str(tmp / "o.json"), "--other-review", "x.json"])

    def test_claude_review_runs_isolated_with_no_tools(self):
        calls = {}

        class Proc:
            returncode = 0
            stdout = json.dumps({"type": "result", "structured_output": good_review(), "total_cost_usd": 0.05,
                                 "usage": {"input_tokens": 1, "output_tokens": 2, "cache_creation_input_tokens": 3, "cache_read_input_tokens": 4}}).encode()

        def fake_run(cmd, input, capture_output, cwd, env, timeout):
            calls.update(cmd=cmd, input=input, cwd=cwd, env=env, listing=sorted(p.name for p in Path(cwd).iterdir()))
            return Proc()
        env = {"ANTHROPIC_API_KEY": "sk-test", "CLAUDE_CODE_OAUTH_TOKEN": "tok", "HOME": "/h", "CLAUDE_CODE_USE_BEDROCK": "1"}
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp)
            runner = D.ClaudeRunner("api-key", environ=env, runner=fake_run)
            code, _ = self.run_review(tmp, card, root, runner=runner)
            self.assertEqual(code, 0)
            row = D.read_log(tmp / "cost.jsonl")[0]
            self.assertEqual((row["auth_basis"], row["total_cost_usd"], row["tokens"]["cache_read"]), ("metered_api", 0.05, 4))
        cmd = calls["cmd"]
        self.assertIn("--bare", cmd)
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")            # no tools: the model cannot read the repository
        self.assertIn("--no-session-persistence", cmd)
        self.assertIn("--max-budget-usd", cmd)
        self.assertEqual(calls["listing"], [])                          # empty working directory
        self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", calls["env"])       # only the chosen credential is present
        self.assertNotIn("CLAUDE_CODE_USE_BEDROCK", calls["env"])
        self.assertTrue(calls["env"]["CLAUDE_CONFIG_DIR"])
        self.assertIn(b"hereby revoked", calls["input"])


class AuthTests(unittest.TestCase):
    def req(self):
        return D.Request("review", "r", "p", "s", D.REVIEW_SCHEMA, "claude-sonnet-5-5", 0.5, 4, 60)

    def test_subscription_drops_api_key_and_never_uses_bare(self):
        env = D.build_env("subscription", {"ANTHROPIC_API_KEY": "k", "CLAUDE_CODE_OAUTH_TOKEN": "t"})
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertIn("CLAUDE_CODE_OAUTH_TOKEN", env)
        cmd = D.build_command("claude", "subscription", self.req())
        self.assertNotIn("--bare", cmd)
        self.assertIn("--strict-mcp-config", cmd)

    def test_api_key_mode_uses_bare_and_drops_the_subscription_token(self):
        env = D.build_env("api-key", {"ANTHROPIC_API_KEY": "k", "CLAUDE_CODE_OAUTH_TOKEN": "t"})
        self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", env)
        self.assertIn("--bare", D.build_command("claude", "api-key", self.req()))

    def test_missing_credentials_refused(self):
        with self.assertRaises(D.InputError):
            D.build_env("api-key", {})
        with self.assertRaises(D.InputError):
            D.build_env("subscription", {"ANTHROPIC_API_KEY": "k"})

    def test_parse_claude_json(self):
        good = json.dumps({"type": "result", "structured_output": {"a": 1}, "total_cost_usd": 0.2,
                           "usage": {"input_tokens": 5}, "modelUsage": {"m1": {"inputTokens": 7, "outputTokens": 3, "cacheReadInputTokens": 9, "cacheCreationInputTokens": 2}}})
        out, tokens, cost, err = D.parse_claude_json(good)
        self.assertEqual((out, cost, err), ({"a": 1}, 0.2, None))
        self.assertEqual(tokens, {"input": 7, "output": 3, "cache_creation": 2, "cache_read": 9})
        out, _, cost, err = D.parse_claude_json(json.dumps({"type": "result", "result": "```json\n{\"b\": 2}\n```"}))
        self.assertEqual((out, cost, err), ({"b": 2}, None, None))
        self.assertIsNotNone(D.parse_claude_json(json.dumps({"type": "result", "result": "no json here"}))[3])
        self.assertIn("error", D.parse_claude_json(json.dumps({"is_error": True, "subtype": "error_max_budget_usd"}))[3])
        self.assertIsNotNone(D.parse_claude_json("not json")[3])


class DraftTests(unittest.TestCase):
    def test_draft_writes_csvs_that_keep_identity_columns(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            make_packet(tmp / "packet")
            args = make_args(tmp, packet=str(tmp / "packet"), out=str(tmp / "draft"))
            runner = D.DryRunner([good_draft()])
            policy = D.CapPolicy()
            D.do_draft(args, runner, policy, clock)
            rows = D.read_csv(tmp / "draft" / "decisions.csv")
            self.assertEqual(rows[0]["dossier_sha256"], "a" * 64)
            self.assertEqual((rows[0]["outcome"], rows[0]["approved"], rows[0]["search_ids"]), ("submit", "true", '["S1"]'))
            clauses = D.read_csv(tmp / "draft" / "clauses.csv")
            self.assertEqual((clauses[0]["state"], clauses[0]["effective_date_confirmed"], clauses[0]["later_events"]), ("terminated", "true", "[]"))
            self.assertEqual(json.loads((tmp / "draft" / "RATIONALES.json").read_text(encoding="utf-8")), {"SAV": "Searched; nothing found."})
            self.assertEqual(json.loads((tmp / "draft" / "DRAFT_RECEIPT.json").read_text(encoding="utf-8"))["attempts"], 1)
            self.assertIn("EO:100 text", runner.calls[0].prompt)
            self.assertEqual(D.read_log(tmp / "cost.jsonl")[0]["stage"], "draft")
            with self.assertRaises(D.InputError):                       # never overwrites
                D.do_draft(args, D.DryRunner([good_draft()]), policy, clock)

    def test_semantic_checks_mirror_apply_and_assemble(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            make_packet(tmp / "packet", ids=("EO:100", "EO:101"))
            _, decisions, clauses, _, _ = D.load_packet_inputs(tmp / "packet")
            check = D.draft_semantic(decisions, clauses)
            self.assertEqual(check(good_draft(("EO:100", "EO:101"))), [])
            self.assertTrue(any("exactly once" in e for e in check(good_draft(("EO:100",)))))     # missing member
            bad = good_draft(("EO:100", "EO:101"))
            bad["decisions"][0]["savings_check"] = "@rationale:MISSING"
            self.assertTrue(any("undefined @rationale" in e for e in check(bad)))
            bad = good_draft(("EO:100", "EO:101"))
            bad["clauses"][0]["effective_date"] = "Jan 2 1990"
            self.assertTrue(any("YYYY-MM-DD" in e for e in check(bad)))
            bad = good_draft(("EO:100", "EO:101"), state="operative")
            bad["clauses"][0]["checked_through"] = "2026-01-01"
            self.assertTrue(any("checked_through" in e for e in check(bad)))
            bad = good_draft(("EO:100", "EO:101"))
            bad["clauses"][1]["scope_id"] = "EO:101#9"
            self.assertTrue(any("inventory" in e for e in check(bad)))

    def test_bad_drafts_exhaust_the_single_retry(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            make_packet(tmp / "packet")
            args = make_args(tmp, packet=str(tmp / "packet"), out=str(tmp / "draft"))
            bad = good_draft()
            bad["decisions"][0]["outcome"] = "approved"
            runner = D.DryRunner([bad, bad, good_draft()])
            with self.assertRaises(D.StageFailed):
                D.do_draft(args, runner, D.CapPolicy(), clock)
            self.assertEqual(len(runner.calls), 2)
            self.assertFalse((tmp / "draft").exists())

    def test_install_keeps_blank_sheets_and_checks_fingerprint(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            make_packet(tmp / "packet")
            args = make_args(tmp, packet=str(tmp / "packet"), out=str(tmp / "draft"))
            D.do_draft(args, D.DryRunner([good_draft()]), D.CapPolicy(), clock)
            D.do_install(tmp / "draft", tmp / "packet")
            self.assertTrue((tmp / "packet" / "decisions.csv.blank").exists())
            self.assertEqual(D.read_csv(tmp / "packet" / "decisions.csv")[0]["outcome"], "submit")
            with self.assertRaises(D.InputError):
                D.do_install(tmp / "draft", tmp / "packet")


class KitTests(unittest.TestCase):
    def fake_kit(self, tmp, code):
        kit = tmp / "kit.py"
        kit.write_text("import sys, json\nopen(sys.argv[0] + '.argv', 'w').write(json.dumps(sys.argv[1:]))\nsys.exit(%d)\n" % code, encoding="utf-8")
        return kit

    def test_failed_dispatch_check_blocks_the_draft_and_no_model_runs(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            make_packet(tmp / "packet")
            args = make_args(tmp, packet=str(tmp / "packet"), out=str(tmp / "draft"), no_dispatch_check=False, kit=str(self.fake_kit(tmp, 1)))
            runner = D.DryRunner([good_draft()])
            with self.assertRaises(D.InputError):
                D.do_draft(args, runner, D.CapPolicy(), clock)
            self.assertEqual(runner.calls, [])
            self.assertEqual(json.loads((tmp / "kit.py.argv").read_text())[-2:], ["dispatch-check", str(tmp / "packet")])

    def test_passing_dispatch_check_lets_the_draft_run(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            make_packet(tmp / "packet")
            args = make_args(tmp, packet=str(tmp / "packet"), out=str(tmp / "draft"), no_dispatch_check=False, kit=str(self.fake_kit(tmp, 0)))
            D.do_draft(args, D.DryRunner([good_draft()]), D.CapPolicy(), clock)
            self.assertTrue((tmp / "draft" / "decisions.csv").exists())

    def test_kit_passthrough_logs_zero_cost_and_returns_exit_code(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            kit = self.fake_kit(tmp, 3)
            code = D.main(["kit", "--repo", str(tmp), "--kit", str(kit), "--cost-log", str(tmp / "c.jsonl"), "--packet-label", "pk",
                           "apply", "--", "PACKET", "--write", "OUT"], clock=clock)
            self.assertEqual(code, 3)
            row = D.read_log(tmp / "c.jsonl")[0]
            self.assertEqual((row["stage"], row["cost_counted_usd"], row["outcome"], row["exit_code"]), ("apply", 0.0, "failed", 3))
            self.assertEqual(json.loads((tmp / "kit.py.argv").read_text())[2:], ["apply", "PACKET", "--write", "OUT"])
            self.assertEqual(D.main(["kit", "--repo", str(tmp), "--cost-log", str(tmp / "c.jsonl"), "bogus"], clock=clock), 2)


class ReviewScopeTests(unittest.TestCase):
    def test_partial_research_acceptance_needs_expected_gate_errors(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp)
            args = make_args(tmp, card=str(card), line=None, source_root=str(root), allow_source_root=["texts"], reviewer="r",
                             scope="partial_research", out=str(tmp / "o.json"), reveal_note=None)
            runner = D.DryRunner([good_review(), good_review(expected_gate_errors=["clause_0_current_predicate"])])
            res = D.do_review(args, runner, D.CapPolicy(), clock)
            self.assertEqual(res["attempts"], 2)                         # first rejected by the semantic check, retried
            record = json.loads((tmp / "o.json").read_text(encoding="utf-8"))
            self.assertEqual(record["expected_gate_errors"], ["clause_0_current_predicate"])
            self.assertEqual(record["scope"], "partial_research")

    def test_after_reveal_verdict_and_note(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            card, root = write_card(tmp, {"instrument_id": "EO:100"})
            note = tmp / "note.txt"
            note.write_text("A control was planted on another order and was caught.", encoding="utf-8")
            args = make_args(tmp, card=str(card), line=None, source_root=str(root), allow_source_root=["texts"], reviewer="r",
                             scope="whole_case", out=str(tmp / "o.json"), reveal_note=str(note))
            runner = D.DryRunner([good_review()])
            D.do_review(args, runner, D.CapPolicy(), clock, after_reveal=True)
            self.assertEqual(json.loads((tmp / "o.json").read_text(encoding="utf-8"))["verdict"], "upheld_after_reveal")
            self.assertIn("planted on another order", runner.calls[0].prompt)
            self.assertEqual(D.read_log(tmp / "cost.jsonl")[0]["stage"], "after-reveal")


if __name__ == "__main__":
    unittest.main(verbosity=1)
