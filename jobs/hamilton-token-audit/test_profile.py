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
    def test_load_keeps_final_revision_with_same_event_uuid(self):
        with tempfile.TemporaryDirectory() as td:
            first = assistant(); final = assistant(usage={"input_tokens":10, "cache_read_input_tokens":100,
                "cache_creation_input_tokens":0, "output_tokens":100}, final=True)
            records = [{"created_at":ts, kind:dict(body, uuid="same-event")} for ts,kind,body in [first,final,final]]
            Path(td,"page.json").write_text(json.dumps({"ccr":{"data":records}}))
            events = ham.load(td)
            self.assertEqual(len(events), 2)
            self.assertEqual(ham.profile(events)["tokens"]["output"], 100)

    def test_geddes_jsonl_input_and_reasoning_subset(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td,"worker.output")
            usage = {"input_tokens":3,"cache_read_input_tokens":5,"cache_creation_input_tokens":7,
                "output_tokens":11,"output_tokens_details":{"reasoning_tokens":4}}
            msg = assistant(usage=usage, final=True)[2]["message"]
            path.write_text(json.dumps({"type":"assistant","timestamp":"2000-01-01T00:00:00Z","message":msg})+"\n")
            p = ham.profile(ham.load(path))
            self.assertEqual(p["tokens"], {"input":3,"read":5,"write5m":0,"write1h":0,"output":11})
            self.assertEqual(p["cache_write_unclassified_tokens"],7)
            self.assertEqual(p["usage_records"][0]["reasoning_tokens_included_in_output"],4)
            self.assertEqual(p["cost_units"],58)  # reasoning is not added again

    def test_call_identity_is_scoped_to_agent(self):
        p=ham.profile([assistant(agent="a"),assistant(agent="b")])
        self.assertEqual(p["model_calls"],2)
        self.assertEqual(p["tokens"]["output"],2)

    def test_missing_call_id_refuses_instead_of_merging_calls(self):
        with self.assertRaisesRegex(ValueError,"stable message id"):
            ham.profile([assistant(mid=None)])

    def test_final_without_output_does_not_certify_stream_output(self):
        p=ham.profile([assistant(),assistant(usage={},final=True)])
        self.assertFalse(p["coverage"]["output"]["complete_final_usage_observed"])

    def test_conflicting_final_usage_refuses(self):
        with self.assertRaises(ValueError):
            ham.profile([assistant(final=True),assistant(usage={"output_tokens":2},final=True)])

    def test_cache_contradiction_invalid_counts_and_reasoning_refuse(self):
        for usage in [{"cache_creation_input_tokens":0,"cache_creation":{"ephemeral_5m_input_tokens":1}},
                {"input_tokens":True},{"input_tokens":1.5},{"output_tokens":1,"reasoning_tokens":2}]:
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                ham.profile([assistant(usage=usage)])

    def test_aggregate_reasoning_and_later_stream_conflicts_refuse(self):
        for first,last in [({"cache_creation_input_tokens":5},{"cache_creation_input_tokens":10}),
                ({"output_tokens":5,"reasoning_tokens":1},{"output_tokens":5,"reasoning_tokens":4})]:
            with self.subTest(first=first),self.assertRaises(ValueError):
                ham.profile([assistant(usage=first,final=True),assistant(usage=last,final=True)])
        with self.assertRaises(ValueError):
            ham.profile([assistant(usage={"output_tokens":5},final=True),assistant(usage={"output_tokens":10})])

    def test_explicit_wrong_model_price_schedule_refuses(self):
        event=assistant();event[2]["message"]["model"]="actual-model"
        with self.assertRaisesRegex(ValueError,"pricing model"):
            ham.profile([event],pricing={"model":"another-model"})

    def test_invalid_pricing_date_and_mixed_or_unknown_models_refuse(self):
        pricing={"source":"synthetic","as_of":"2000-01-01","usd_per_million_tokens":dict.fromkeys(ham.W,1)}
        first=assistant("first");first[2]["message"]["model"]="model-a"
        second=assistant("second");second[2]["message"]["model"]="model-b"
        with self.assertRaisesRegex(ValueError,"one observed model"):
            ham.profile([first,second],pricing=pricing)
        with self.assertRaisesRegex(ValueError,"one observed model"):
            ham.profile([assistant()],pricing=pricing)
        with self.assertRaisesRegex(ValueError,"ISO calendar date"):
            ham.profile([first],pricing=dict(pricing,as_of="not-a-date"))

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
        event=assistant();event[2]["message"]["model"]="fixture-model"
        p = ham.profile([event], 100, pricing=pricing, cash_charge_usd=3)
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


class ProductionEffortIntegration(unittest.TestCase):
    def metadata(self):
        return {"session_id":"fixture-session","agents":{"main":{
            "worker_id":"fixture-worker","role":"producer","phase":"production","actual_model":"fixture-model",
            "instrument_ids":["EO:1","EO:2"],"started_utc":"2000-01-01T00:00:00Z",
            "finished_utc":"2000-01-01T00:01:00Z","coverage":"partial",
            "measurement_method":"explicit caller recorded occupation; active reasoning unavailable"}}}

    def load_consumer(self):
        old=list(sys.path)
        try:
            sys.path.insert(0,str(ROOT.parent/"neyman"))
            spec=importlib.util.spec_from_file_location("neyman_diagnose",ROOT.parent/"neyman/diagnose.py")
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            return module
        finally:
            sys.path[:]=old

    def test_shared_calls_enter_real_consumer_once_with_separate_session_total(self):
        diagnostic=self.load_consumer()
        events=[assistant(final=True),assistant("m2",final=True)]
        result=ham.profile(events,session_totals={"input":1000,"read":1000,"write5m":0,"write1h":0,"output":1000})
        receipt=ham.production_effort(result,self.metadata())
        self.assertEqual(receipt["events"][0]["instrument_ids"],["EO:1","EO:2"])
        self.assertNotEqual(receipt["events"][0]["usage_id"],receipt["events"][1]["usage_id"])
        class Reader:
            def value(self,ref):return receipt
        actual=diagnostic.effort(Reader(),[{},{}],{"EO:1","EO:2"})
        self.assertEqual(actual["token_usage_records"],2)
        self.assertEqual(actual["observed_token_lower_bounds"]["input_uncached"],20)
        self.assertEqual(actual["observed_seconds_by_kind"]["worker_elapsed"],60)
        self.assertIsNone(actual["observed_seconds_by_kind"]["active"])
        self.assertIsNone(actual["complete_session_cost"])
        self.assertFalse(receipt["provenance"]["session_totals_exported"])

    def test_missing_interval_membership_and_wrong_model_refuse(self):
        p=ham.profile([assistant()])
        for key,value in [("started_utc","2000-01-01T00:00:00"),("instrument_ids",[]),("phase","unknown"),("actual_model","")]:
            metadata=self.metadata();metadata["agents"]["main"][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):ham.production_effort(p,metadata)
        wrong=self.metadata();wrong["agents"]["main"].update(started_utc="2000-02-01T00:00:00Z",finished_utc="2000-02-01T00:01:00Z")
        with self.assertRaisesRegex(ValueError,"outside"):
            ham.production_effort(p,wrong)
        late=list(assistant(usage={"output_tokens":3},final=True));late[0]="2000-02-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"outside"):
            ham.production_effort(ham.profile([assistant(),tuple(late)]),self.metadata())
        event=assistant();event[2]["message"]["model"]="observed-model"
        with self.assertRaisesRegex(ValueError,"disagrees"):
            ham.production_effort(ham.profile([event]),self.metadata())

    def test_unknown_cache_ttl_exports_only_known_aggregate(self):
        p=ham.profile([assistant(usage={"input_tokens":2,"cache_creation_input_tokens":7,"output_tokens":3})])
        e=ham.production_effort(p,self.metadata())["events"][0]
        self.assertEqual(e["tokens"]["cache_write"],7)
        self.assertIsNone(e["tokens"]["cache_read"])
        self.assertIsNone(e["tokens"]["reasoning"])
        self.assertIsNone(e["cash_charge_usd"])

    def test_failed_unfinished_cohort_keeps_effort_in_actual_diagnosis(self):
        diagnostic=self.load_consumer()
        receipt=ham.production_effort(ham.profile([assistant(final=True)]),self.metadata())
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            def write(name,value):
                p=root/name;p.write_text(json.dumps(value));return diagnostic.Reader(root).ref(name)
            effort_ref=write("effort.json",receipt)
            selection=write("selection.json",[{"instrument_id":i} for i in ("EO:1","EO:2")])
            attempts=[]
            for iid in ("EO:1","EO:2"):
                attempts.append(write(iid.replace(":","-")+".json",{"schema":"neyman.research-attempt/1",
                    "instrument_id":iid,"attempt_id":iid,"assessor":"synthetic engineering fixture",
                    "question":"test unsuccessful-attempt accounting","outcome":"blocked",
                    "started_utc":"2000-01-01T00:00:00Z","finished_utc":"2000-01-01T00:01:00Z",
                    "basis":[effort_ref]}))
            d=diagnostic.diagnose(diagnostic.Reader(root),{"schema":"neyman.production-import/1",
                "base_commit":"0"*40,"cohort_kind":"ordinary_production","selection":selection,
                "research_attempts":attempts,"effort_receipts":[effort_ref]})
            self.assertEqual(d["summary"]["ready_in_isolated_replay"],0)
            self.assertEqual(d["summary"]["research_attempts"],2)
            self.assertEqual(d["effort"]["observed_token_lower_bounds"]["output"],1)
            self.assertIsNone(d["effort"]["complete_session_cost"])
            self.assertFalse(d["summary"]["verified_savings"])


if __name__ == "__main__":
    unittest.main()
