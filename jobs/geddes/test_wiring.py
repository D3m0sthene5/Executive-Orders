"""Tests for the claim-kit wiring, flag ids, resolution gate, cost comparison and telemetry extractor.

All data is synthetic and lives under temporary directories; nothing touches the network.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "jobs/claim-kit"))
import geddes
import telemetry
from test_geddes import fixture


class AppliedDirCase(unittest.TestCase):
    """A synthetic packet plus an applied directory holding one claim (flagged when bad=True)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.dossier, self.claim, self.packet = fixture(self.repo)
        self.applied = self.packet.parent / "applied-v1"
        self.applied.mkdir()
        self.write_claims([self.bad_claim()])

    def tearDown(self): self.temp.cleanup()

    def bad_claim(self):
        c = copy.deepcopy(self.claim)
        c["operative_clauses"][0]["original_operative_text"] = "Wrong words."
        return c

    def write_claims(self, claims):
        (self.applied / "CLAIMS.proposed.jsonl").write_text("".join(json.dumps(c) + "\n" for c in claims), encoding="utf-8")

    def write_resolutions(self, rows, name=geddes.RESOLUTIONS_NAME):
        path = self.applied / name
        path.write_text(json.dumps({"schema": geddes.RESOLUTIONS_SCHEMA, "resolutions": rows}), encoding="utf-8")
        return path


class FlagIdTests(AppliedDirCase):
    def test_lint_flags_carry_stable_ids_and_new_top_level_counts(self):
        first = geddes.lint(self.applied, self.repo)
        second = geddes.lint(self.applied, self.repo)
        flags = [f for r in first["results"] for f in r["flags"]]
        self.assertTrue(flags)
        for f in flags:
            self.assertRegex(f["flag_id"], r"^[0-9a-f]{16}$")
        self.assertEqual([f["flag_id"] for r in first["results"] for f in r["flags"]],
                         [f["flag_id"] for r in second["results"] for f in r["flags"]])
        self.assertEqual(len({f["flag_id"] for f in flags}), len(flags))
        self.assertGreaterEqual(first["files_read"], 3)  # packet, claims and at least one held text file
        self.assertGreaterEqual(first["file_reads"], first["files_read"])
        self.assertIsInstance(first["seconds"], float)

    def test_id_depends_on_instrument_code_scope_and_text_and_keeps_existing_ids(self):
        base = {"code": "quotation_not_verbatim", "scope_id": "s1", "detail": "text A"}
        ids = {geddes.flag_id_for("EO:1", base), geddes.flag_id_for("EO:2", base),
               geddes.flag_id_for("EO:1", {**base, "code": "other"}), geddes.flag_id_for("EO:1", {**base, "scope_id": "s2"}),
               geddes.flag_id_for("EO:1", {**base, "detail": "text B"}), geddes.flag_id_for("EO:1", {**base, "quote": "span"})}
        self.assertEqual(len(ids), 6)
        self.assertEqual(geddes.flag_id_for("EO:1", base), geddes.flag_id_for("EO:1", dict(base)))
        rows = [{"instrument_id": "EO:1", "flags": [{**base, "flag_id": "keep-me"}, dict(base)]}]
        geddes.stamp_flag_ids(rows)
        self.assertEqual(rows[0]["flags"][0]["flag_id"], "keep-me")
        self.assertEqual(rows[0]["flags"][1]["flag_id"], geddes.flag_id_for("EO:1", base))

    def test_flag_without_any_text_field_still_gets_a_distinct_id(self):
        self.assertNotEqual(geddes.flag_id_for("EO:1", {"code": "c", "source_id": "a"}), geddes.flag_id_for("EO:1", {"code": "c", "source_id": "b"}))


class GateTests(AppliedDirCase):
    def current_flag_ids(self):
        return [f["flag_id"] for r in geddes.lint(self.applied, self.repo)["results"] for f in r["flags"]]

    def test_gate_fails_without_resolutions_and_lists_unresolved_flags(self):
        result = geddes.gate(self.applied, repo=self.repo)
        self.assertFalse(result["passed"])
        self.assertEqual({u["flag_id"] for u in result["unresolved"]}, set(self.current_flag_ids()))
        self.assertIsNone(result["resolutions_path"])

    def test_gate_passes_when_every_flag_has_a_noted_resolution(self):
        rows = [{"flag_id": fid, "instrument_id": "EO:12345", "response": "disputed", "note": "Source wording checked; claim keeps its paraphrase."}
                for fid in self.current_flag_ids()]
        self.write_resolutions(rows)
        result = geddes.gate(self.applied, repo=self.repo)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["resolved"], len(rows))

    def test_empty_note_bad_response_and_wrong_instrument_do_not_resolve(self):
        fid = self.current_flag_ids()[0]
        for row, reason in (({"flag_id": fid, "instrument_id": "EO:12345", "response": "disputed", "note": "   "}, "note_empty"),
                            ({"flag_id": fid, "instrument_id": "EO:12345", "response": "ignored", "note": "x"}, "response_not_one_of"),
                            ({"flag_id": fid, "instrument_id": "EO:99999", "response": "disputed", "note": "x"}, "resolution_instrument_id")):
            self.write_resolutions([row])
            result = geddes.gate(self.applied, repo=self.repo)
            self.assertFalse(result["passed"], row)
            self.assertIn(reason, json.dumps(result))

    def test_every_flag_must_be_resolved_and_stale_resolutions_are_reported(self):
        ids = self.current_flag_ids()
        self.write_resolutions([{"flag_id": "deadbeefdeadbeef", "instrument_id": "EO:12345", "response": "order_blocked", "note": "n"}])
        result = geddes.gate(self.applied, repo=self.repo)
        self.assertFalse(result["passed"])
        self.assertEqual(result["stale_resolutions"], ["deadbeefdeadbeef"])
        self.assertEqual(result["unresolved_count"], len(ids))

    def test_clean_claim_passes_with_no_resolutions_file(self):
        self.write_claims([self.claim])
        self.assertTrue(geddes.gate(self.applied, repo=self.repo)["passed"])

    def test_custom_resolutions_path_must_exist_and_bad_schema_is_an_error(self):
        with self.assertRaises(FileNotFoundError):
            geddes.gate(self.applied, self.applied / "missing.json", self.repo)
        (self.applied / "bad.json").write_text(json.dumps({"schema": "wrong", "resolutions": []}))
        with self.assertRaises(ValueError):
            geddes.gate(self.applied, self.applied / "bad.json", self.repo)

    def test_cli_exit_codes(self):
        argv = ["gate", str(self.applied), "--repo", str(self.repo)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(geddes.main(argv), 1)
            self.assertIn("UNRESOLVED", err.getvalue())
            self.write_resolutions([{"flag_id": f, "instrument_id": "EO:12345", "response": "fixed_in_new_version", "note": "Fixed in v2."}
                                    for f in self.current_flag_ids()])
            self.assertEqual(geddes.main(argv), 0)
            self.assertEqual(geddes.main(argv + ["--resolutions", str(self.applied / "nope.json")]), 2)


class KitWiringTests(AppliedDirCase):
    """claim-kit batch-check runs Geddes after batch.check; batch.check itself is stubbed."""

    def run_kit(self, *extra, geddes_module=None):
        import batch
        import kit
        original = batch.check
        batch.check = lambda repo, packet, applied, actual=True: {"claims_checked": 1, "strict_claim_fail": 0, "counts": {},
                                                                    "actual_claim_checker": {"claims_all_checks_passed": 1}}
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = kit.main(["--repo", str(self.repo), "batch-check", str(self.packet.parent), str(self.applied), *extra])
        finally:
            batch.check = original
        return code, json.loads(out.getvalue())

    def test_summary_is_added_lint_file_written_and_exit_code_unchanged(self):
        code, result = self.run_kit()
        self.assertEqual(code, 0)
        g = result["geddes"]
        self.assertGreaterEqual(g["flags"], 1)
        self.assertEqual(g["flagged_claims"], ["EO:12345"])
        self.assertEqual(g["path"], "GEDDES_LINT.json")
        self.assertIn("coverage_gaps", g); self.assertIn("seconds", g)
        saved = json.loads((self.applied / "GEDDES_LINT.json").read_text())
        self.assertEqual(saved["defect_flags"], g["flags"])
        self.assertNotIn("gate", g)

    def test_strict_fails_until_every_flag_is_resolved(self):
        code, result = self.run_kit("--geddes-strict")
        self.assertEqual(code, 1)
        self.assertFalse(result["geddes"]["gate"]["passed"])
        ids = result["geddes"]["gate"]["unresolved"]
        self.write_resolutions([{"flag_id": f, "instrument_id": "EO:12345", "response": "disputed", "note": "Reviewed."} for f in ids])
        code, result = self.run_kit("--geddes-strict")
        self.assertEqual(code, 0)
        self.assertTrue(result["geddes"]["gate"]["passed"])

    def test_geddes_error_is_recorded_and_does_not_crash(self):
        (self.packet).unlink()  # Geddes cannot find PACKET.json
        code, result = self.run_kit()
        self.assertEqual(code, 0)
        self.assertIn("error", result["geddes"])
        code, result = self.run_kit("--geddes-strict")
        self.assertEqual(code, 1)
        self.assertIn("error", result["geddes"])


class CostCompareTests(unittest.TestCase):
    HEADER = "batch,role,model,input_tokens,output_tokens,cache_creation_input_tokens,cache_read_input_tokens,active_seconds\n"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self): self.temp.cleanup()

    def csv(self, name, body):
        p = self.root / name; p.write_text(self.HEADER + body, encoding="utf-8"); return p

    def filed(self, name, counts):
        p = self.root / name; p.write_text(json.dumps({"filed_claims": counts})); return p

    def row(self, result, track, role):
        return next(r for r in result["rows"] if r["track"] == track and r["role"] == role)

    def test_per_filed_claim_values_ratio_and_verdict(self):
        base = self.csv("b.csv", "n01,producer,m,100,40,300,1000,60\nn02,producer,m,100,60,100,1000,40\nn01,reviewer,m,10,5,10,500,10\n")
        new = self.csv("n.csv", "n01,producer,m,50,20,100,250,30\nn02,producer,m,50,30,50,250,20\nn01,reviewer,m,10,5,10,500,10\n")
        result = geddes.cost_compare(base, new, self.filed("fb.json", {"NRA": 10}), self.filed("fn.json", {"NRA": 20}))
        m = self.row(result, "NRA", "producer")["metrics"]
        self.assertEqual(m["cache_read_input_tokens"]["baseline_per_filed_claim"], 200.0)
        self.assertEqual(m["cache_read_input_tokens"]["new_per_filed_claim"], 25.0)
        self.assertEqual(m["cache_read_input_tokens"]["ratio_new_over_baseline"], 0.125)
        self.assertEqual(m["tokens_total_input"]["baseline_total"], 200 + 400 + 2000)  # input + cache creation + cache read
        self.assertEqual(m["tokens_total_input"]["new_per_filed_claim"], (100 + 150 + 500) / 20)
        self.assertEqual(m["output_tokens"]["baseline_per_filed_claim"], 10.0)
        self.assertEqual(m["active_seconds"]["new_per_filed_claim"], 2.5)
        self.assertEqual(self.row(result, "NRA", "producer")["verdict"],
                         "new run used 87.5% fewer cache-read tokens per filed claim for NRA/producer")
        self.assertEqual(self.row(result, "NRA", "reviewer")["verdict"],  # 500/10 per claim before, 500/20 after
                         "new run used 50% fewer cache-read tokens per filed claim for NRA/reviewer")

    def test_missing_data_is_unknown_never_zero(self):
        base = self.csv("b.csv", "n01,producer,m,100,40,300,,60\ng01,producer,m,1,1,1,1,1\n")
        new = self.csv("n.csv", "n01,producer,m,50,20,100,250,30\n")
        result = geddes.cost_compare(base, new, self.filed("fb.json", {"NRA": 10}), self.filed("fn.json", {"NRA": 10}))
        m = self.row(result, "NRA", "producer")["metrics"]["cache_read_input_tokens"]
        self.assertEqual(m["baseline_total"], "unknown")
        self.assertEqual(m["baseline_per_filed_claim"], "unknown")
        self.assertEqual(m["ratio_new_over_baseline"], "unknown")
        self.assertTrue(m["unknown_because"])
        self.assertIn("unknown", self.row(result, "NRA", "producer")["verdict"])
        # Output tokens were reported in both runs, so they still compare.
        self.assertEqual(self.row(result, "NRA", "producer")["metrics"]["output_tokens"]["ratio_new_over_baseline"], 0.5)
        # A track/role present in only one run, and a track without a filed count, are unknown.
        g = self.row(result, "General", "producer")
        self.assertEqual(g["metrics"]["output_tokens"]["new_per_filed_claim"], "unknown")
        self.assertEqual(g["metrics"]["output_tokens"]["ratio_new_over_baseline"], "unknown")

    def test_no_filed_files_and_invalid_counts_are_unknown(self):
        base = self.csv("b.csv", "n01,producer,m,1,1,1,10,1\n"); new = self.csv("n.csv", "n01,producer,m,1,1,1,5,1\n")
        result = geddes.cost_compare(base, new)
        self.assertEqual(self.row(result, "NRA", "producer")["metrics"]["cache_read_input_tokens"]["ratio_new_over_baseline"], "unknown")
        bad = self.root / "bad.json"; bad.write_text('{"filed_claims":{"NRA":-3}}')
        result = geddes.cost_compare(base, new, bad, bad)
        self.assertEqual(result["errors"][0]["reason"], "invalid_denominator")
        self.assertEqual(self.row(result, "NRA", "producer")["metrics"]["output_tokens"]["ratio_new_over_baseline"], "unknown")

    def test_tokens_total_input_column_is_used_when_present_and_zero_baseline_is_unknown(self):
        (self.root / "b.csv").write_text("batch,role,tokens_total_input,cache_read_input_tokens,output_tokens,active_seconds\nn01,producer,100,0,4,2\n")
        (self.root / "n.csv").write_text("batch,role,tokens_total_input,cache_read_input_tokens,output_tokens,active_seconds\nn01,producer,50,0,2,1\n")
        f = self.filed("f.json", {"NRA": 1})
        result = geddes.cost_compare(self.root / "b.csv", self.root / "n.csv", f, f)
        m = self.row(result, "NRA", "producer")["metrics"]
        self.assertEqual(m["tokens_total_input"]["ratio_new_over_baseline"], 0.5)
        self.assertEqual(m["cache_read_input_tokens"]["baseline_per_filed_claim"], 0.0)
        self.assertEqual(m["cache_read_input_tokens"]["ratio_new_over_baseline"], "unknown")

    def test_cli_compare(self):
        base = self.csv("b.csv", "n01,producer,m,1,1,1,100,1\n"); new = self.csv("n.csv", "n01,producer,m,1,1,1,60,1\n")
        fb, fn = self.filed("fb.json", {"NRA": 1}), self.filed("fn.json", {"NRA": 1})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = geddes.main(["cost", "--compare", str(base), "--filed-baseline", str(fb), str(new), "--filed-new", str(fn)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["verdicts"], ["new run used 40% fewer cache-read tokens per filed claim for NRA/producer"])


class TelemetryTests(unittest.TestCase):
    def transcript(self, path, messages):
        lines = []
        for i, (stamp, mid, usage, tools) in enumerate(messages):
            lines.append(json.dumps({"type": "assistant", "timestamp": stamp, "message": {
                "id": mid, "model": "m1", "usage": usage, "content": [{"type": "tool_use", "name": t} for t in tools]}}))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_roster_extraction_totals_and_gap_dropping(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            u = {"input_tokens": 3, "output_tokens": 5, "cache_creation_input_tokens": 7, "cache_read_input_tokens": 11}
            self.transcript(root / "agentA.output", [
                ("2026-11-01T00:00:00Z", "msg1", u, ["Bash", "Read"]),
                ("2026-11-01T00:00:00Z", "msg1", u, []),  # same API message id: counted once
                ("2026-11-01T00:00:30Z", "msg2", u, ["Bash"]),
                ("2026-11-01T02:00:00Z", "msg3", u, [])])  # a two-hour pause is dropped from active time
            (root / "roster.csv").write_text("agent_id,batch,role,track\nagentA,x01,producer,Alpha\nghost,x02,reviewer,Alpha\n")
            out = str(root / "out")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(telemetry.main([str(root), out, "--roster", str(root / "roster.csv")]), 0)
            import csv
            with (root / "out.csv").open(encoding="utf-8") as f: rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual((r["batch"], r["role"], r["track"], r["model"]), ("x01", "producer", "Alpha", "m1"))
            self.assertEqual((r["api_messages"], r["input_tokens"], r["output_tokens"]), ("3", "9", "15"))
            self.assertEqual(r["tokens_total_input"], str(9 + 21 + 33))
            self.assertEqual((r["tool_calls"], r["bash_calls"], r["read_calls"], r["active_seconds"]), ("3", "2", "1", "30"))
            summary = json.loads((root / "out.json").read_text())
            self.assertEqual(summary["agents_without_transcript"], ["ghost"])
            # The first columns keep the Apollo order, so older readers still work.
            self.assertEqual(list(r)[:15], ["batch", "role", "agent", "model", "api_messages", "input_tokens", "output_tokens",
                                           "cache_creation_input_tokens", "cache_read_input_tokens", "tool_calls", "bash_calls",
                                           "read_calls", "active_seconds", "first_utc", "last_utc"])

    def test_apollo_log_fallback_and_roster_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "log.txt"
            log.write_text("producer n01 a0123456789abcdef x\nn01 reviewer a1123456789abcdef\nnoise\n")
            agents = telemetry.read_apollo_log(log)
            self.assertEqual(agents, [("a0123456789abcdef", "n01", "producer", "NRA"), ("a1123456789abcdef", "n01", "reviewer", "NRA")])
            (root / "dup.csv").write_text("agent_id,batch,role,track\na,b,producer,T\na,b,reviewer,T\n")
            with self.assertRaises(ValueError): telemetry.read_roster(root / "dup.csv")
            (root / "short.csv").write_text("agent_id,batch\na,b\n")
            with self.assertRaises(ValueError): telemetry.read_roster(root / "short.csv")


if __name__ == "__main__": unittest.main()
