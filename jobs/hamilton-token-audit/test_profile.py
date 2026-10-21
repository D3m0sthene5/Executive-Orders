"""Concrete Hamilton capture/pricing regressions; fixtures contain no real transcripts."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("hamilton", ROOT / "profile.py")
ham = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ham)


def assistant(mid="m1", usage=None, agent="main", final=False):
    usage = usage if usage is not None else {"input_tokens":10, "cache_read_input_tokens":100,
        "cache_creation_input_tokens":0, "output_tokens":1}
    message = {"id":mid, "usage":usage, "content":[], "stop_reason":"end_turn" if final else None}
    body = {"message":message} if agent == "main" else {"internal_anthropic_catchall":{"message":message, "parent_tool_use_id":agent}}
    return ("2000-01-01T00:00:00Z", "assistant", body)


class ProfileRegressionTests(unittest.TestCase):
    def test_partial_transcript_cannot_absorb_full_session_value(self):
        p = ham.profile([assistant()], 100, "partial")
        self.assertEqual(p["session_token_value_usd"], 100)
        self.assertIsNone(p["usd_per_unit"])
        self.assertIsNone(p["observed_window_token_value_usd"])
        self.assertEqual(p["cost_units"], 25)
        self.assertIsNone(p["session_tokens"]["output"])
        self.assertFalse(p["coverage"]["output"]["complete_final_usage_observed"])

    def test_known_full_totals_price_only_observed_window(self):
        totals = {"input":100, "read":1000, "write5m":0, "write1h":0, "output":100}
        p = ham.profile([assistant()], 100, session_totals=totals)
        self.assertAlmostEqual(p["observed_window_token_value_usd"], 100 * 25 / 700)
        self.assertEqual(p["coverage"]["read"]["fraction"], 0.1)
        self.assertLess(p["observed_window_token_value_usd"], p["session_token_value_usd"])

    def test_inconsistent_totals_are_not_valued(self):
        totals = {"input":1, "read":1, "write5m":0, "write1h":0, "output":1}
        self.assertIsNone(ham.profile([assistant()], 100, session_totals=totals)["usd_per_unit"])

    def test_missing_usage_fields_are_explicit(self):
        p = ham.profile([assistant(usage={})])
        self.assertTrue(p["unpriced_or_unclassified_usage"])
        self.assertEqual(p["coverage"]["output"]["calls_missing_field"], 1)
        self.assertIsNone(p["cash_charge_usd"])
        self.assertEqual(set(p["effort_accounting"]["missing_phases"]), set(ham.PHASES))

    def test_cache_ttl_is_not_invented(self):
        p = ham.profile([assistant(usage={"input_tokens":0, "cache_read_input_tokens":0,
            "cache_creation_input_tokens":150000, "output_tokens":0})])
        self.assertEqual(p["cache_write_unclassified_tokens"], 150000)
        self.assertEqual(p["tokens"]["write5m"], 0)
        self.assertEqual(p["coverage"]["write5m"]["calls_missing_field"], 1)

    def test_five_minute_rebuild_is_not_charged_at_one_hour_rate(self):
        p = ham.profile([assistant(usage={"input_tokens":0, "cache_read_input_tokens":0,
            "cache_creation_input_tokens":150000, "cache_creation":{"ephemeral_5m_input_tokens":150000}, "output_tokens":0})])
        self.assertEqual(p["cache_rebuilds"]["cost"], 187500)
        self.assertFalse(p["attribution"]["add_diagnostic_views_to_cause_total"])

    def test_final_usage_update_supersedes_initial_stream_count(self):
        events = [assistant(), assistant(usage={"input_tokens":10, "cache_read_input_tokens":100,
            "cache_creation_input_tokens":0, "output_tokens":100}, final=True)]
        p = ham.profile(events)
        self.assertEqual(p["model_calls"], 1)
        self.assertEqual(p["tokens"]["output"], 100)
        self.assertTrue(p["coverage"]["output"]["complete_final_usage_observed"])

    def test_agent_context_does_not_leak_into_another_agent(self):
        events = [("2000-01-01T00:00:00Z", "user", {"message":{"content":"Main task"}}),
            assistant("helper", {"input_tokens":100, "cache_read_input_tokens":0, "cache_creation_input_tokens":0, "output_tokens":0}, "helper"),
            assistant("main", {"input_tokens":10, "cache_read_input_tokens":0, "cache_creation_input_tokens":0, "output_tokens":0})]
        p = ham.profile(events)
        by_cause = {x["cause"]:x["cost"] for x in p["cost_by_cause"]}
        self.assertEqual(by_cause["user or system message"], 10)
        self.assertEqual(by_cause["model continuing"], 100)

    def test_cash_and_price_valuations_are_distinct(self):
        pricing = {"source":"fixture price schedule", "as_of":"2000-01-01",
            "usd_per_million_tokens":{"input":3, "read":0.3, "write5m":3.75, "write1h":6, "output":15}}
        p = ham.profile([assistant()], 100, pricing=pricing, cash_charge_usd=3)
        self.assertAlmostEqual(p["priced_observed_tokens_usd"], 0.000075)
        self.assertEqual(p["cash_charge_usd"], 3)
        self.assertIsNone(p["observed_window_token_value_usd"])
        self.assertEqual(p["pricing"]["source"], "fixture price schedule")

    def test_invalid_money_is_rejected(self):
        with self.assertRaises(ValueError):
            ham.profile([assistant()], float("nan"))


class FinderIntegration(unittest.TestCase):
    def run_finder(self, with_totals):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / "events/demo"
            d.mkdir(parents=True)
            ts, kind, body = assistant()
            (d / "page.json").write_text(json.dumps({"ccr":{"data":[{"created_at":ts,kind:body}]}}))
            session = {"id":"demo", "model":"fixture", "cost_usd":100}
            if with_totals:
                session["token_totals"] = {"input":100, "read":1000, "write5m":0, "write1h":0, "output":100}
            (root / "session_index.json").write_text(json.dumps({"sessions":[session]}))
            (root / "MANIFEST.json").write_text(json.dumps({"sessions":[{"session_id":"demo", "complete":True}]}))
            out = root / "candidates.jsonl"
            result = subprocess.run([sys.executable,"-I",str(ROOT.parent / "junto/finders/hamilton.py"),
                "--data",str(root),"--out",str(out),"--run-id","R-20000101-1"], capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(Path(str(out)+".check.json").read_text())

    def test_complete_manifest_cannot_override_missing_counts(self):
        check = self.run_finder(False)
        self.assertEqual(check["skipped_no_rate"], 1)
        self.assertEqual(check["sessions"], [])
        self.assertEqual(check["unpriced_sessions"][0]["token_value_usd"], 100)

    def test_complete_manifest_with_partial_output_remains_partial(self):
        check = self.run_finder(True)
        self.assertEqual(check["skipped_no_rate"], 0)
        self.assertFalse(check["sessions"][0]["complete"])
        self.assertLess(check["sessions"][0]["attributed_usd"], 4)


if __name__ == "__main__":
    unittest.main()
