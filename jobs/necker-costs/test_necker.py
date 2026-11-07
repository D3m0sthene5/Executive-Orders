"""Offline tests for necker.py with synthetic transcripts. Run: python3 -I -m unittest jobs/necker-costs/test_necker.py"""
import csv
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import necker as N  # noqa: E402

P = N.Prices()


def usage(inp=0, out=0, read=0, w5=0, w1=0, speed="standard"):
    return {"input_tokens": inp, "output_tokens": out, "cache_read_input_tokens": read,
            "cache_creation_input_tokens": w5 + w1,
            "cache_creation": {"ephemeral_5m_input_tokens": w5, "ephemeral_1h_input_tokens": w1}, "speed": speed}


def rec(mid, model, u, ts="2026-11-06T10:00:00.000Z", session="S1", agent=None, stop="end_turn", content=None):
    r = {"type": "assistant", "sessionId": session, "timestamp": ts, "uuid": mid + ts,
         "message": {"id": mid, "model": model, "usage": u, "stop_reason": stop,
                     "content": content if content is not None else [{"type": "text", "text": "ok"}]}}
    if agent:
        r["agentId"] = agent
        r["isSidechain"] = True
    return r


def user(text, session="S1", agent=None, ts="2026-11-06T09:59:00.000Z"):
    r = {"type": "user", "sessionId": session, "timestamp": ts, "message": {"role": "user", "content": text}}
    if agent:
        r["agentId"] = agent
        r["isSidechain"] = True
    return r


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf8")


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name) / "proj"
        self.addCleanup(self.td.cleanup)

    def sub(self, agent, records, meta=None, session="S1"):
        d = self.root / session / "subagents"
        write(d / f"agent-{agent}.jsonl", records)
        if meta is not None:
            (d / f"agent-{agent}.meta.json").write_text(json.dumps(meta))


class TestPricing(unittest.TestCase):
    def test_opus_55_each_category(self):
        tok = {"input": 1_000_000, "output": 1_000_000, "cache_read": 1_000_000, "cache_write_5m": 1_000_000,
               "cache_write_1h": 1_000_000}
        self.assertAlmostEqual(P.cost("claude-opus-5-5", tok), 4 + 20 + 0.20 + 5 + 8)

    def test_models_and_cache_read_ratio(self):
        one = {"input": 0, "output": 0, "cache_read": 1_000_000, "cache_write_5m": 0, "cache_write_1h": 0}
        self.assertAlmostEqual(P.cost("claude-sonnet-5-5", one), 0.10)
        self.assertAlmostEqual(P.cost("claude-fable-5-1", one), 0.25)
        self.assertAlmostEqual(P.cost("claude-opus-5", one), 0.50)
        self.assertAlmostEqual(P.cost("claude-opus-4-1", one), 1.50)
        self.assertAlmostEqual(P.cost("claude-sonnet-4-6", one), 0.30)

    def test_unknown_model_is_unpriced_not_free(self):
        self.assertIsNone(P.cost("claude-mystery-9", {"input": 5, "output": 5, "cache_read": 5, "cache_write_5m": 0,
                                                       "cache_write_1h": 0}))

    def test_fast_mode_doubles_opus_55(self):
        tok = {"input": 1_000_000, "output": 1_000_000, "cache_read": 0, "cache_write_5m": 0, "cache_write_1h": 0}
        self.assertAlmostEqual(P.cost("claude-opus-5-5", tok, fast=True), 2 * (4 + 20))
        self.assertAlmostEqual(P.cost("claude-sonnet-5-5", tok, fast=True), 2 + 10)  # no fast tier

    def test_haiku_long_prompt_tier(self):
        short = {"input": 50_000, "output": 1000, "cache_read": 0, "cache_write_5m": 0, "cache_write_1h": 0}
        long = {"input": 50_000, "output": 1000, "cache_read": 60_000, "cache_write_5m": 0, "cache_write_1h": 0}
        self.assertAlmostEqual(P.cost("claude-haiku-5-5", short), 50_000 * 0.10 / 1e6 + 1000 * 0.50 / 1e6)
        self.assertAlmostEqual(P.cost("claude-haiku-5-5", long), 50_000 * 0.50 / 1e6 + 60_000 * 0.05 / 1e6 + 1000 * 2.5 / 1e6)

    def test_web_search(self):
        tok = {c: 0 for c in N.CATS}
        self.assertAlmostEqual(P.cost("claude-opus-5-5", tok, web_searches=3), 0.03)


class TestTranscripts(Base):
    def test_streaming_duplicates_counted_once_with_max(self):
        mid = "msg_1"
        write(self.root / "S1.jsonl", [
            rec(mid, "claude-opus-5-5", usage(inp=10, out=5, read=1000, w1=200), stop=None),
            rec(mid, "claude-opus-5-5", usage(inp=10, out=700, read=1000, w1=200), ts="2026-11-06T10:00:01.000Z"),
            rec(mid, "claude-opus-5-5", usage(inp=10, out=700, read=1000, w1=200), ts="2026-11-06T10:00:02.000Z")])
        res = N.analyze([self.root], P)
        acc = res["by_model"]["claude-opus-5-5"]
        self.assertEqual((acc["messages"], acc["output"], acc["cache_read"], acc["cache_write_1h"]), (1, 700, 1000, 200))
        self.assertEqual(res["duplicate_records_collapsed"], 2)
        want = (10 * 4 + 700 * 20 + 1000 * 0.20 + 200 * 8) / 1e6
        self.assertAlmostEqual(acc["usd"], want)

    def test_cache_heavy_call(self):
        # 800k tokens of context re-read from cache, 2k new output: the shape of a Bentham production worker.
        write(self.root / "S1.jsonl", [rec("m", "claude-sonnet-5-5", usage(inp=30, out=2000, read=800_000, w1=5_000))])
        acc = N.analyze([self.root], P)["by_model"]["claude-sonnet-5-5"]
        want = (30 * 2 + 2000 * 10 + 800_000 * 0.10 + 5_000 * 4) / 1e6
        self.assertAlmostEqual(acc["usd"], want)
        self.assertAlmostEqual(acc["usd_by_cat"]["cache_read"], 0.08)
        lumped = (30 + 800_000 + 5_000) * 2 / 1e6 + 2000 * 10 / 1e6
        self.assertAlmostEqual(acc["usd_no_cache_discount"], lumped)
        self.assertGreater(acc["usd_no_cache_discount"] / acc["usd"], 7)  # lumping overstates a cache-heavy call ~10x
        eff = N.cache_effect(acc)
        self.assertAlmostEqual(eff["cache_reads_share_of_priced_usd"], 0.08 / want, places=3)

    def test_unclassified_cache_write_priced_at_5m(self):
        u = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 1_000_000}
        write(self.root / "S1.jsonl", [rec("m", "claude-opus-5-5", u)])
        acc = N.analyze([self.root], P)["by_model"]["claude-opus-5-5"]
        self.assertAlmostEqual(acc["usd"], 5.0)
        self.assertEqual(acc["unclassified_cache_write"], 1_000_000)

    def test_five_minute_and_one_hour_writes_priced_apart(self):
        write(self.root / "S1.jsonl", [rec("m", "claude-opus-5-5", usage(w5=1_000_000, w1=1_000_000))])
        acc = N.analyze([self.root], P)["by_model"]["claude-opus-5-5"]
        self.assertAlmostEqual(acc["usd_by_cat"]["cache_write_5m"], 5.0)
        self.assertAlmostEqual(acc["usd_by_cat"]["cache_write_1h"], 8.0)

    def test_by_day_model_session_and_worker(self):
        write(self.root / "S1.jsonl", [rec("a", "claude-opus-5-5", usage(out=1000), ts="2026-11-05T23:59:00Z"),
                                       rec("b", "claude-sonnet-5-5", usage(out=1000), ts="2026-11-06T00:01:00Z")])
        self.sub("w1", [user("hello", agent="w1"), rec("c", "claude-sonnet-5-5", usage(out=1000), agent="w1")],
                 {"agentType": "general-purpose", "description": "x", "model": "sonnet"})
        res = N.analyze([self.root], P)
        self.assertEqual(sorted(res["by_day"]), ["2026-11-05", "2026-11-06"])
        self.assertAlmostEqual(res["by_day"]["2026-11-06"]["usd"], 2 * 1000 * 10 / 1e6)
        self.assertEqual(len(res["by_session"]), 1)
        self.assertEqual({k[1] for k in res["workers"]}, {"main", "w1"})
        self.assertEqual(res["workers"][(N.sha12("S1"), "w1")]["role"], "worker:general-purpose")

    def test_synthetic_messages_and_until_filter(self):
        write(self.root / "S1.jsonl", [rec("z", "<synthetic>", usage(out=9999)),
                                       rec("a", "claude-opus-5-5", usage(out=1000), ts="2026-11-06T10:00:00Z"),
                                       rec("b", "claude-opus-5-5", usage(out=1000), ts="2026-11-06T12:00:00Z")])
        self.assertEqual(N.analyze([self.root], P)["by_model"]["claude-opus-5-5"]["messages"], 2)
        res = N.analyze([self.root], P, until=N.parse_ts("2026-11-06T11:00:00Z"))
        self.assertEqual(res["by_model"]["claude-opus-5-5"]["messages"], 1)
        self.assertNotIn("<synthetic>", res["by_model"])

    def test_output_repair_only_for_non_final_messages(self):
        big = "x" * 4000
        final = rec("f", "claude-opus-5-5", usage(out=1000), content=[{"type": "text", "text": big}], stop="end_turn")
        partial = rec("p", "claude-opus-5-5", usage(out=3), content=[{"type": "text", "text": big}], stop=None)
        write(self.root / "S1.jsonl", [final, partial])
        res = N.analyze([self.root], P)
        self.assertAlmostEqual(res["tokens_per_char"], 1000 / 4000)
        acc = res["by_model"]["claude-opus-5-5"]
        self.assertEqual(acc["messages_output_not_final"], 1)
        self.assertEqual(acc["output_repair_tokens"], 997)
        self.assertAlmostEqual(acc["usd_repair"], 997 * 20 / 1e6)
        self.assertAlmostEqual(acc["usd"], (1000 + 3) * 20 / 1e6)  # the base figure is never altered


class TestAttribution(Base):
    def test_description_labels(self):
        self.assertEqual(N.attribute({"description": "produce:b3"}, "", [])[:2], ("b3", "description:produce"))
        self.assertEqual(N.attribute({"description": "review:b3"}, "", [])[:2], ("b3", "description:review"))
        self.assertEqual(N.attribute({"description": "Lane 4 replica check p055"}, "", [])[:2],
                         ("lane4.replica.p055", "description:lane"))
        self.assertEqual(N.attribute({"description": "Lane 1 GPO page check g010 rerun"}, "", [])[0], "lane1.gpo.g010")

    def test_single_packet_path_only(self):
        one = "Read research/production/codex-swarm-20261021/producer/BRIEF.md and write"
        self.assertEqual(N.attribute({}, one, [])[:2], ("codex-swarm-20261021/producer", "weak:packet_path_mention"))
        two = one + " and research/production/other-wave/b02/PACKET.json"
        label, kind, why = N.attribute({}, two, [])
        self.assertIsNone(label)
        self.assertIn("several", why)

    def test_action_id_only_from_a_gate_call(self):
        ids = ["production.one_step_away", "production.claim_ready.yes.fr"]
        cmd = "python3 -I jobs/bentham/bentham.py gate --action production.claim_ready.yes.fr --batches b.json"
        self.assertEqual(N.attribute({}, "", [cmd], ids)[:2], ("production.claim_ready.yes.fr", "gate_call"))
        self.assertIsNone(N.attribute({}, "", ["bentham.py gate --action ID --batches FILE"], ids)[0])
        self.assertIsNone(N.attribute({}, "", [cmd, "bentham.py gate --action production.one_step_away"], ids)[0])
        # naming an action in the first message is a question about it, not a run: weak, never counted
        self.assertEqual(N.attribute({}, "How is production.one_step_away costed?", [], ids)[:2],
                         ("production.one_step_away", "weak:action_id_mention"))

    def test_weak_labels_are_not_attributed_cost(self):
        self.sub("w1", [user("Read research/production/wave-x/b01/BRIEF.md", agent="w1"),
                        rec("b", "claude-sonnet-5-5", usage(out=1000), agent="w1")], {"description": "look"})
        res = N.analyze([self.root], P)
        s = N.attribution_summary(res["workers"])
        self.assertEqual(s["usd"]["attributed"], 0)
        self.assertAlmostEqual(s["weak_label_usd_not_counted"], 1000 * 10 / 1e6)
        self.assertEqual(N.batch_table(res["workers"]), [])

    def test_unlabelled_worker_and_coordinator_are_not_attributed(self):
        write(self.root / "S1.jsonl", [user("do things"), rec("a", "claude-opus-5-5", usage(out=1000))])
        self.sub("w1", [user("plain task", agent="w1"), rec("b", "claude-sonnet-5-5", usage(out=1000), agent="w1")],
                 {"description": "something"})
        self.sub("w2", [user("go", agent="w2"), rec("c", "claude-sonnet-5-5", usage(out=3000), agent="w2")],
                 {"description": "produce:b9"})
        res = N.analyze([self.root], P)
        s = N.attribution_summary(res["workers"])
        self.assertAlmostEqual(s["usd"]["attributed"], 3000 * 10 / 1e6)
        self.assertAlmostEqual(s["usd"]["unattributed_worker"], 1000 * 10 / 1e6)
        self.assertAlmostEqual(s["usd"]["coordinator"], 1000 * 20 / 1e6)
        self.assertAlmostEqual(s["attributed_share_of_worker_cost"], 0.75)
        rows = N.batch_table(res["workers"])
        self.assertEqual([r["batch"] for r in rows], ["b9"])


class TestCommandsAndPrivacy(Base):
    def run_cmd(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = N.main(argv)
        return rc, buf.getvalue()

    def test_transcripts_command_writes_sanitized_outputs(self):
        secret = "THE-SECRET-PROMPT-TEXT-THAT-MUST-NOT-LEAK-9871"
        write(self.root / "S1.jsonl", [user(secret), rec("a", "claude-opus-5-5", usage(inp=5, out=100, read=1000, w1=10),
                                                           content=[{"type": "text", "text": secret + " reply"}])])
        self.sub("w1", [user("Please do the thing " + secret, agent="w1"),
                        rec("b", "claude-sonnet-5-5", usage(out=100), agent="w1")], {"description": "produce:b1"})
        out = Path(self.td.name) / "out"
        rc, _ = self.run_cmd(["transcripts", str(self.root), "--out", str(out)])
        self.assertEqual(rc, 0)
        allout = "".join(p.read_text() for p in out.iterdir())
        self.assertNotIn(secret, allout)
        self.assertNotIn("Please do the thing", allout)
        summary = json.loads((out / "SUMMARY.json").read_text())
        self.assertIn("claude-opus-5-5", summary["by_model"])
        self.assertEqual(summary["attribution"]["transcripts"]["attributed"], 1)
        self.assertTrue((out / "BATCH_COSTS.csv").read_text().startswith("wave,batch"))
        self.assertLess(json.loads((out / "BUDGET.json").read_text())["total_bytes"], 5 * 1024 * 1024)

    def test_guard_refuses_leak(self):
        with self.assertRaises(N.GuardError):
            N.write_files(Path(self.td.name) / "o", {"A.txt": "xx some private sentence that is long enough yy"},
                          {"some private sentence that is long enough"})

    def test_validate_reproduces_cli_cost_state(self):
        # The CLI's own total for 1,000 output / 100k reads / 10k 1h-writes of Opus 5.5.
        cli = (1000 * 20 + 100_000 * 0.20 + 10_000 * 8) / 1e6
        cs = {"type": "cost-state", "sessionId": "S1", "totalCostUSD": cli,
              "modelUsage": {"claude-opus-5-5": {"inputTokens": 0, "outputTokens": 1000, "cacheReadInputTokens": 100_000,
                                                 "cacheCreationInputTokens": 10_000, "webSearchRequests": 0, "costUSD": cli}}}
        write(self.root / "S1.jsonl", [rec("a", "claude-opus-5-5", usage(out=1000, read=100_000, w1=10_000)), cs])
        out = Path(self.td.name) / "v"
        rc, _ = self.run_cmd(["validate", str(self.root), "--out", str(out)])
        v = json.loads((out / "VALIDATION.json").read_text())
        self.assertEqual(rc, 0)
        self.assertAlmostEqual(v["by_model"]["claude-opus-5-5"]["ratio_all_1h_over_reported"], 1.0, places=5)
        self.assertAlmostEqual(v["per_session_vs_cli"]["rows"][0]["ratio"], 1.0, places=4)

    def test_telemetry_reprice_and_gate_file(self):
        hdr = "agent_id,role,phase,batch,model,started_utc,finished_utc,wall_seconds,calls,fresh_input,cache_read," \
              "cache_write_5m,cache_write_1h,cache_write_unclassified,output,tool_uses,bash_calls,coverage_notes,hamilton_status\n"
        rows = ["p1,producer,production,b01,claude-sonnet-5-5,2026-11-04T01:00:00Z,2026-11-04T01:10:00Z,600,10,100,10000000,500000,0,0,50000,1,1,,ok",
                "r1,reviewer,review,b01,claude-opus-5-5,2026-11-04T01:11:00Z,2026-11-04T01:20:00Z,540,5,10,2000000,0,100000,0,20000,1,1,,ok",
                "c1,producer,production,b01+b02,claude-sonnet-5-5,2026-11-04T02:00:00Z,2026-11-04T02:10:00Z,600,10,1,1,1,0,0,1,1,1,,ok"]
        csvp = Path(self.td.name) / "u.csv"
        csvp.write_text(hdr + "\n".join(rows) + "\n")
        disp = Path(self.td.name) / "d.json"
        disp.write_text(json.dumps({"batches": [{"batch": "b01", "attempted": 20, "claims_filed": 7,
                                                  "blind_review_verdicts": {"upheld": 6, "rejected": 2},
                                                  "controls": [{"caught": True}, {"caught": False}]}]}))
        out = Path(self.td.name) / "t"
        rc, _ = self.run_cmd(["telemetry", str(csvp), "--wave", "w", "--disposition", str(disp), "--out", str(out)])
        self.assertEqual(rc, 0)
        b = {r["batch"]: r for r in csv.DictReader(io.StringIO((out / "BATCH_COSTS.csv").read_text()))}
        prod = (100 * 2 + 50000 * 10 + 10_000_000 * 0.10 + 500_000 * 2.5) / 1e6
        rev = (10 * 4 + 20000 * 20 + 2_000_000 * 0.20 + 100_000 * 8) / 1e6
        self.assertAlmostEqual(float(b["b01"]["usd"]), prod + rev, places=4)
        self.assertEqual((b["b01"]["attempted"], b["b01"]["submitted"], b["b01"]["filed"], b["b01"]["controls_missed"]),
                         ("20", "8", "7", "1"))
        self.assertEqual(b["b01+b02"]["composite"], "1")
        gate = list(csv.DictReader(io.StringIO((out / "gate_w.csv").read_text())))
        self.assertEqual([g["batch"] for g in gate], ["b01"])  # composites are never offered to the gate
        self.assertEqual(list(gate[0].keys()), N.GATE_COLS)

    def test_compare_shows_cache_effect(self):
        hdr = "agent_id,role,phase,batch,model,started_utc,finished_utc,wall_seconds,calls,fresh_input,cache_read," \
              "cache_write_5m,cache_write_1h,cache_write_unclassified,output\n"
        csvp = Path(self.td.name) / "u.csv"
        csvp.write_text(hdr + "p1,producer,production,b01,claude-sonnet-5-5,t,t,1,1,100,10000000,500000,0,0,50000\n")
        out = Path(self.td.name) / "c"
        rc, _ = self.run_cmd(["compare", "w=" + str(csvp), "--out", str(out)])
        res = json.loads((out / "COMPARISON.json").read_text())["waves"][0]
        self.assertEqual(rc, 0)
        self.assertGreater(res["usd_bentham"], res["usd_necker"])      # Sonnet 5.5 lists below Bentham's table
        self.assertGreater(res["usd_lumped"], 5 * res["usd_necker"])   # lumping cache reads in is far off
        self.assertGreater(res["cache_read_share_of_tokens"], 0.9)


if __name__ == "__main__":
    unittest.main()
