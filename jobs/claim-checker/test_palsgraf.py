"""Planted controls for Palsgraf impact selection (palsgraf.py). No network.

Each test builds the claim-checker fixture repo, runs the checker in full to write a trace, plants one
change, and requires that (1) the claims the change can reach are rechecked, (2) the others are reused,
and (3) every output file is byte-identical to a fresh untraced full run on the changed state.
"""

import datetime as dt
import gzip
import json
import os
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

import test_checker as T

C, S = T.C, T.S
PG = C.PG
OUTPUTS = ("PER_CLAIM.json", "CLAIM_CHECKS.csv", "SUMMARY.json", "REPORT.md")


@unittest.skipUnless(T.REAL_GATE.is_file(), "research/stage19/code/claim_gate.py not checked out")
class PalsgrafTests(unittest.TestCase):
    def setUp(self):
        clean = {k: v for k, v in os.environ.items()
                 if not k.startswith("CLAIM_CHECKER_") and k not in ("JOB_LIMIT", "JOB_CACHE_DIR",
                                                                     "JOB_PRIOR_OUTPUT_DIR")}
        clean["CLAIM_CHECKER_VERIFY_DOWNLOADS"] = "0"
        patcher = mock.patch.dict(os.environ, clean, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        C._VERIFY.update(left=None, last=0.0)
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="palsgraf-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo, self.jobdir = T.build_repo(self.tmp)
        self.claims = self.repo / "research/readiness/claims"
        self.runs = 0
        self.lines = [T.good_claim(),                                            # EO:90001: text originals
                      dict(T.good_claim(), instrument_id="EO:90004",              # EO:90004: PDF original
                           original_representation=T.ref("https://www.govinfo.gov/x/EO_90004.pdf", "x")),
                      self.savings_only_claim()]
        self.lines[1]["original_representation"]["sha256"] = T.sha(
            (self.repo / "research/stage21/original_sources/EO_90004.pdf").read_bytes())
        # Quotations make the checker read these texts (a source nobody quotes is never read).
        self.lines[1]["original_representation"]["quote"] = "The Council shall continue to meet under section 5"
        for c in self.lines:
            c["savings_residuals"] = dict(c["savings_residuals"], quote=T.SAVINGS_TEXT)
        self.write_claims(self.lines)

    # ------------------------------------------------------------- helpers
    def savings_only_claim(self):
        c = T.good_claim()
        c["instrument_id"] = "EO:90004"
        c["research_rationale"] = "only the savings source differs from the first claim"
        return c

    def write_claims(self, lines, name="a.jsonl"):
        (self.claims / name).write_text("".join(json.dumps(x) + "\n" for x in lines), "utf-8")

    def go(self, prior=None, **env):
        self.runs += 1
        out = self.tmp / f"out{self.runs}"
        e = {"REPO_ROOT": str(self.repo), "OUTPUT_DIR": str(out), "JOB_CACHE_DIR": str(self.tmp / "cache")}
        if prior is not None:
            e["CLAIM_CHECKER_PRIOR_OUTPUT_DIR"] = str(prior)
        e.update(env)
        with mock.patch.dict(os.environ, e), mock.patch.object(C, "HERE", self.jobdir):
            C.main([])
        sel = json.loads((out / PG.SELECTION_FILE).read_text("utf-8"))
        return out, sel

    def reference(self):
        out, sel = self.go(CLAIM_CHECKER_PALSGRAF="off")
        self.assertEqual(sel["reason"], "disabled_by_CLAIM_CHECKER_PALSGRAF")
        self.assertFalse((out / PG.TRACE_FILE).exists())
        return out

    def assert_same_outputs(self, a, b):
        for name in OUTPUTS:
            self.assertEqual((a / name).read_bytes(), (b / name).read_bytes(), name)

    def keys(self, sel):
        return sorted(k.rsplit(":", 1)[1] for k in sel["rechecked_claim_keys"])

    def baseline(self):
        out, sel = self.go()
        self.assertEqual((sel["mode"], sel["reason"]), ("full", "no_previous_trace"))
        self.assertTrue((out / PG.TRACE_FILE).is_file())
        return out

    def planted(self, change, expect_lines):
        base = self.baseline()
        change()
        out, sel = self.go(prior=base)
        self.assertEqual(sel["mode"], "selective", sel)
        self.assertEqual(self.keys(sel), sorted(str(n) for n in expect_lines), sel)
        self.assert_same_outputs(out, self.reference())
        return out, sel

    # --------------------------------------------------------------- tests
    def test_no_change_reuses_every_claim_with_identical_outputs(self):
        base = self.baseline()
        out, sel = self.go(prior=base)
        self.assertEqual((sel["mode"], sel["rechecked"], sel["reused"]), ("selective", 0, 3))
        self.assert_same_outputs(out, base)
        out2, sel2 = self.go(prior=out)  # a chain of selective runs stays exact
        self.assertEqual(sel2["rechecked"], 0)
        self.assert_same_outputs(out2, base)

    def test_changed_source_bytes_select_only_the_claims_citing_them(self):
        # EO_90003.txt is the ending source of every claim; EO_90001.txt the original of lines 1 and 3.
        # Line 2's clauses also cite EO_90001.txt (it reuses the first claim's clauses).
        p = self.repo / "research/stage21/original_sources/EO_90001.txt"
        self.planted(lambda: p.write_bytes(p.read_bytes() + b"tampered\n"), [1, 2, 3])

    def test_changed_ending_source_alone(self):
        claim = self.lines[0]
        self.lines[2] = dict(claim, instrument_id="EO:90004", operative_clauses=[], whole_order_end=None)
        self.write_claims(self.lines)
        p = self.repo / "research/stage21/original_sources/EO_90003.txt"
        self.planted(lambda: p.write_bytes(p.read_bytes() + b"tampered\n"), [1, 2])

    def test_changed_pdf_bytes_select_the_pdf_claim(self):
        p = self.repo / "research/stage21/original_sources/EO_90004.pdf"
        self.planted(lambda: p.write_bytes(p.read_bytes().replace(b"Council", b"Kouncil")), [2])

    def test_producer_record_change_selects_its_citers(self):
        p = self.repo / "jobs/other-job/output/SOURCES.jsonl"

        def change():
            lines = p.read_bytes().split(b"\n")
            rec = json.loads(lines[0])
            rec["instrument_ids"] = ["EO:90001"]
            lines[0] = json.dumps(rec).encode()
            p.write_bytes(b"\n".join(lines))
        self.planted(change, [1, 2, 3])  # every claim cites the savings source

    def test_unrelated_producer_record_selects_nothing(self):
        p = self.repo / "jobs/other-job/output/SOURCES.jsonl"
        rec = {"sha256": "7" * 64, "url": "https://example.gov/unrelated", "text_path": None}
        self.planted(lambda: p.write_bytes(p.read_bytes() + json.dumps(rec).encode() + b"\n"), [])

    def test_ledger_status_change_selects_that_order_only(self):
        p = self.repo / C.P["decided"]
        self.planted(lambda: p.write_text(p.read_text("utf-8").replace("EO:90004,yes", "EO:90004,no"), "utf-8"),
                     [2, 3])

    def test_signing_date_change_selects_that_order_only(self):
        p = self.repo / C.P["crosswalk"]
        self.planted(lambda: p.write_text(p.read_text("utf-8").replace("1950-03-03", "1962-01-01"), "utf-8"), [1])

    def test_universe_change_selects_claims_naming_the_order(self):
        p = self.repo / C.P["universe"]
        self.planted(lambda: p.write_text(p.read_text("utf-8").replace("EO:90002,1,1949\n", ""), "utf-8"),
                     [1, 2, 3])  # every claim's clause s2 cites Executive Order No. 90002

    def test_missing_text_that_appears_selects_its_claim(self):
        p = self.repo / "jobs/other-job/output/text/savings.txt"
        saved = p.read_bytes()
        p.unlink()
        self.planted(lambda: p.write_bytes(saved), [1, 2, 3])

    def test_evicted_text_cache_selects_the_pdf_claim(self):
        if not T.HAVE_PYPDF:
            self.skipTest("pypdf not installed")
        pdf = T.sha((self.repo / "research/stage21/original_sources/EO_90004.pdf").read_bytes())
        self.planted(lambda: (self.tmp / "cache" / "text" / f"{pdf}.json").unlink(), [2])

    def test_moved_and_new_lines_keep_exact_outputs(self):
        base = self.baseline()
        new = dict(T.good_claim(), research_rationale="a new claim line")
        self.write_claims([new] + self.lines)  # every old line moves down by one
        out, sel = self.go(prior=base)
        self.assertEqual((sel["mode"], self.keys(sel)), ("selective", ["1"]))
        self.assert_same_outputs(out, self.reference())

    def test_future_activity_date_is_rechecked_every_run(self):
        c = T.good_claim()
        c["later_source_search"][0]["checked_on"] = "2999-01-01"
        self.lines[2] = c
        self.write_claims(self.lines)
        base = self.baseline()
        out, sel = self.go(prior=base)
        self.assertEqual(self.keys(sel), ["3"])
        self.assertEqual(sel["recheck_reasons"], {"volatile": 1})

    def test_code_or_rule_change_forces_a_full_run(self):
        base = self.baseline()
        gate = self.repo / C.P["claim_gate_dir"] / "claim_gate.py"
        gate.write_text(gate.read_text("utf-8") + "# a rule edit\n", "utf-8")
        out, sel = self.go(prior=base)
        self.assertEqual((sel["mode"], sel["reason"], sel["rechecked"]), ("full", "code_or_rules_changed", 3))
        self.assertTrue(any(c.endswith("claim_gate.py") for c in sel["changed_code_or_rules"]), sel)

    def test_checker_module_change_forces_a_full_run(self):
        base = self.baseline()
        trace = self.read_trace(base)
        mine = [d for d in trace["code"] if d.endswith(os.sep + "palsgraf.py")]
        self.assertTrue(mine, "the checker's own modules are global dependencies")
        trace["code"][mine[0]] = "b" + "0" * 32  # as if palsgraf.py had different bytes last time
        self.write_trace(base, trace)
        out, sel = self.go(prior=base)
        self.assertEqual((sel["mode"], sel["reason"]), ("full", "code_or_rules_changed"))

    def test_code_loaded_from_bytecode_is_still_a_global_dependency(self):
        # Production imports the gate and norton/model.py from __pycache__; their sources must be recorded.
        self.baseline()
        out = self.baseline()  # the second load uses bytecode written by the first
        code = self.read_trace(out)["code"]
        for f in (T.REAL_GATE, T.REAL_REPO / "jobs/norton/model.py", T.REAL_REPO / "jobs/claim-kit/working_text.py"):
            self.assertIn("f:" + str(f.resolve()), code)
        self.assertFalse([d for d in code if "__pycache__" in d])

    def test_setting_change_forces_a_full_run(self):
        base = self.baseline()
        out, sel = self.go(prior=base, CLAIM_CHECKER_TEXT_PACK=str(self.tmp / "nope.gz"))
        self.assertEqual((sel["mode"], sel["reason"]), ("full", "code_or_rules_changed"))

    def test_untraced_modes_run_in_full_and_write_no_trace(self):
        base = self.baseline()
        out, sel = self.go(prior=base, JOB_LIMIT="2")
        self.assertEqual((sel["mode"], sel["reason"]), ("full", "job_limit"))
        self.assertFalse((out / PG.TRACE_FILE).exists())

    def test_weekly_full_run_reconciles(self):
        base = self.baseline()
        trace = self.read_trace(base)
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=PG.RECONCILE_DAYS, minutes=1)).isoformat()
        trace["last_full"]["utc"] = old
        self.write_trace(base, trace)
        out, sel = self.go(prior=base)
        self.assertEqual((sel["mode"], sel["reason"]), ("full", "periodic_full_reconcile"))
        self.assertEqual(sel["reconcile"], {"compared": 3, "mismatched": 0, "mismatched_line_sha256": []})
        self.assertNotEqual(self.read_trace(out)["last_full"]["utc"], old)

    def test_reconcile_fails_loudly_on_a_missed_dependency(self):
        base = self.baseline()
        trace = self.read_trace(base)
        # Plant a selector bug: forget that line 1 depends on its original text file.
        target = str(self.repo / "research/stage21/original_sources/EO_90001.txt")
        sha1 = C.hashlib.sha256(json.dumps(self.lines[0]).encode()).hexdigest()
        drop = {i for i, (d, _) in enumerate(trace["deps"]) if target in d or d.startswith(("i:", "u:"))}
        trace["claims"][sha1]["deps"] = [i for i in trace["claims"][sha1]["deps"] if i not in drop]
        self.write_trace(base, trace)
        p = pathlib.Path(target)
        p.write_bytes(p.read_bytes() + b"tampered\n")
        out, sel = self.go(prior=base)
        self.assertNotIn("1", self.keys(sel))  # the planted bug hides the change from selection ...
        with self.assertRaises(SystemExit):
            self.go(prior=base, CLAIM_CHECKER_FULL="1")  # ... and the reconciling full run catches it
        out = self.tmp / f"out{self.runs}"
        self.assertIn("reconcile failed", json.loads((out / "BLOCKED.json").read_text("utf-8"))["reason"])
        self.assertEqual(json.loads((out / PG.SELECTION_FILE).read_text("utf-8"))["reconcile"]["mismatched"], 1)

    def test_working_text_fragment_change_selects_the_transcription_claim(self):
        rel = "jobs/app-executive-orders/output/texts/EO_90001.txt"
        path = self.repo / rel
        path.parent.mkdir(parents=True)
        path.write_text(T.ORIGINAL_TEXT, encoding="utf-8")
        source = dict(T.good_claim()["original_representation"], text_path=rel, text_sha256=T.sha(T.ORIGINAL_TEXT.encode()),
                      grade="mirror_transcription", acceptable_as_original=False, instrument_id="EO:90001",
                      char_start=0, char_end=len(T.ORIGINAL_TEXT), quote=T.ORIGINAL_TEXT)
        frag = path.parent.parent / "FRAGMENTS.jsonl"
        frag.write_text(json.dumps({"kind": "original_representation", "instrument_id": "EO:90001",
                                    "data": source}) + "\n")
        claim = T.good_claim()
        claim["original_representation"] = source
        claim["working_text"] = C.W.blank([source])
        claim["working_text"]["confirmations"][0].update(identity_confirmed=True, complete_text_confirmed=True)
        self.write_claims(self.lines + [claim])

        def change():
            frag.write_text(json.dumps({"kind": "original_representation", "instrument_id": "EO:90001",
                                        "data": dict(source, complete_text=False)}) + "\n")
        self.planted(change, [1, 2, 3, 4])  # every line cites the original's SHA-256 (a fragment hash lookup)

    def confirmed_working_claim(self):
        """A transcription-dependent claim that reuses a Lachmann confirmation (jobs/lachmann/output)."""
        rel = "jobs/app-executive-orders/output/texts/EO_90001.txt"
        path = self.repo / rel
        path.parent.mkdir(parents=True)
        path.write_text(T.ORIGINAL_TEXT, encoding="utf-8")
        source = dict(T.good_claim()["original_representation"], text_path=rel,
                      text_sha256=T.sha(T.ORIGINAL_TEXT.encode()), grade="mirror_transcription",
                      acceptable_as_original=False, instrument_id="EO:90001",
                      char_start=0, char_end=len(T.ORIGINAL_TEXT), quote=T.ORIGINAL_TEXT)
        (path.parent.parent / "FRAGMENTS.jsonl").write_text(json.dumps(
            {"kind": "original_representation", "instrument_id": "EO:90001", "data": source}) + "\n")
        record = dict(C.W.confirmation(source), schema=C.W.CONFIRMATION_SCHEMA, method="machine",
                      acceptable_as_original=False, confirmed=True, identity_confirmed=True,
                      complete_text_confirmed=True, requires_page_check=False)
        conf = self.repo / C.W.CONFIRMATION_PATHS[0]
        conf.parent.mkdir(parents=True)
        conf.write_text(json.dumps(record) + "\n", "utf-8")
        prior = C.W.matching_confirmation(source, self.repo, index=C.W.Index(self.repo))
        self.assertIsNotNone(prior)
        claim = T.good_claim()
        claim["original_representation"] = source
        claim["working_text"] = C.W.blank([source], prior)
        self.write_claims(self.lines + [claim])
        return conf, record

    def test_lachmann_confirmation_of_another_order_selects_nothing(self):
        conf, record = self.confirmed_working_claim()
        other = dict(record, instrument_id="EO:90004")
        self.planted(lambda: conf.write_text(conf.read_text("utf-8") + json.dumps(other) + "\n", "utf-8"), [])

    def test_changed_lachmann_confirmation_selects_its_claim(self):
        conf, record = self.confirmed_working_claim()
        changed = dict(record, pages_confirmed=True, note="re-reviewed")
        out, sel = self.planted(lambda: conf.write_text(json.dumps(changed) + "\n", "utf-8"), [4])
        self.assertIn("working_text:prior_confirmation_stale", (out / "CLAIM_CHECKS.csv").read_text("utf-8"))

    # ------------------------------------------------------------- trace io
    def read_trace(self, out):
        with gzip.open(out / PG.TRACE_FILE, "rt", encoding="utf-8") as fh:
            return json.load(fh)

    def write_trace(self, out, trace):
        PG.write_trace(out, trace)


class DecideTests(unittest.TestCase):
    """The pure selection rule, without the checker."""

    def trace(self, **kw):
        t = {"schema": PG.SCHEMA, "settings": {"a": 1}, "code": {"f:/code.py": "x"},
             "last_full": {"utc": PG.utc_now().isoformat()}, "deps": [["f:/d1", "1"], ["m:t\0k", "2"]],
             "claims": {"A": {"deps": [0]}, "B": {"deps": [1]}, "V": {"deps": [], "volatile": ["today"]}}}
        t.update(kw)
        return t

    def test_rules(self):
        fp = {"f:/code.py": "x", "f:/d1": "1", "m:t\0k": "2"}
        sel = PG.decide(self.trace(), ["A", "B", "V", "N"], fp.get, {"a": 1})
        self.assertEqual((sel["mode"], sel["reuse"], sel["recheck"]), ("selective", ["A", "B"], ["V", "N"]))
        sel = PG.decide(self.trace(), ["A", "B"], dict(fp, **{"m:t\0k": "3"}).get, {"a": 1})
        self.assertEqual((sel["reuse"], sel["recheck"], sel["changed_dep_kinds"]), (["A"], ["B"], {"m": 1}))
        sel = PG.decide(self.trace(), ["A"], dict(fp, **{"f:/code.py": "y"}).get, {"a": 1})
        self.assertEqual((sel["mode"], sel["reason"], sel["recheck"]), ("full", "code_or_rules_changed", ["A"]))
        sel = PG.decide(self.trace(), ["A"], fp.get, {"a": 2})
        self.assertEqual(sel["reason"], "code_or_rules_changed")
        sel = PG.decide(self.trace(code={}), ["A"], fp.get, {"a": 1})
        self.assertEqual(sel["mode"], "full")
        sel = PG.decide(None, ["A"], fp.get, {"a": 1})
        self.assertEqual((sel["mode"], sel["reason"]), ("full", "no_previous_trace"))
        sel = PG.decide(self.trace(last_full={"utc": "2020-01-01T00:00:00Z"}), ["A", "N"], fp.get, {"a": 1})
        self.assertEqual((sel["reason"], sel["would_reuse"], sel["recheck"]), ("periodic_full_reconcile", ["A"], ["A", "N"]))
        sel = PG.decide(self.trace(last_full=None), ["A"], fp.get, {"a": 1})
        self.assertEqual(sel["reason"], "periodic_full_reconcile")

    def test_fingerprints_of_files_stats_and_tables(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "x"
            f.write_bytes(b"one")
            rec = PG.Recorder()
            fp = PG.Fingerprinter({"t": {"k": {"v": {1, 2}}}, "u": {"EO:1"}}, rec)
            a = (fp("f:" + str(f)), fp("s:" + str(f)), fp("l:" + d), fp("m:t\0k"), fp("m:t\0z"), fp("m:u\0EO:1"))
            self.assertEqual(a[1:], ("file:3", a[2], a[3], "absent", "in"))
            f.write_bytes(b"two")
            fp2 = PG.Fingerprinter({"t": {"k": {"v": {2, 1}}}, "u": set()}, rec)
            b = (fp2("f:" + str(f)), fp2("s:" + str(f)), fp2("l:" + d), fp2("m:t\0k"), fp2("m:t\0z"), fp2("m:u\0EO:1"))
            self.assertNotEqual(a[0], b[0])  # same size, other bytes
            self.assertEqual(a[1:5], b[1:5])  # sets compare by members, not order
            self.assertEqual(b[5], "out")
            self.assertEqual(fp2("s:" + d + "/missing"), "missing")


if __name__ == "__main__":
    unittest.main()
