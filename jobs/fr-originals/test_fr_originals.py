"""Unit tests for fr-originals. Small fixtures, no network."""
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source-ladder"))
sys.path.insert(0, str(HERE))

import eo_extract  # noqa: E402
import fetch_ladder  # noqa: E402
import fr_originals  # noqa: E402
import ofr_index  # noqa: E402
from test_fetch_ladder import FakeTransport, make_pdf  # noqa: E402

ISSUE_URL = "https://www.govinfo.gov/content/pkg/FR-1937-01-12/pdf/FR-1937-01-12.pdf"
ISSUE = make_pdf([
    ["REGISTER VOLUME 2", "Executive Order", "ESTABLISHING A REFUGE", "[No. 7532]", "[F. R. Doc. 37-94; Filed]", "OTHER"],
    ["64 FEDERAL REGISTER, January 12, 1937", "EXECUTIVE ORDER 7534", "body", "[F. R. Doc. 37-95; Filed]"],
    ["FEDERAL REGISTER, January 12, 1937 65", "unrelated notice", "[F. R. Doc. 37-96; Filed]"],
])
DOC_URL = "https://www.govinfo.gov/content/pkg/FR-1995-01-05/pdf/95-1.pdf"
DOC = make_pdf([["Executive Order 12945 of January 3, 1995", "Text.", "[FR Doc. 95-1 Filed 1-4-95]"]])


def rec(num, citation, pub, **kw):
    r = {"executive_order_number": num, "citation": citation, "publication_date": pub, "signing_date": pub,
         "title": "T", "pdf_url": None, "document_number": None, "not_received_for_publication": None}
    r.update(kw)
    return r


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        (self.repo / "research/progress").mkdir(parents=True)
        (self.repo / "research/stage15/CENSUS").mkdir(parents=True)
        (self.repo / "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv").write_text(
            "instrument_id,provisional_substantive_status,decision_origin\nEO:12945,yes,x\nEO:7534,no,x\n", encoding="utf-8")
        (self.repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv").write_text(
            "id,included_in_bibliography,date_effective\nEO:7532,1,1937\nEO:7534,1,1937\nEO:7533,1,1937\n"
            "EO:12945,1,1995\nEO:7400,1,1936\nEO:7999,1,1938\nEO:100,1,1880\n", encoding="utf-8")
        rows = [rec("7532", "2 FR 63", "1937-01-12"), rec("7534", "2 FR 64", "1937-01-12"),
                rec("7533", None, None, not_received_for_publication=True),
                rec("12945", "60 FR 1", "1995-01-05", pdf_url=DOC_URL, document_number="95-1")]
        self.index = ofr_index.build_index(rows)
        eo_extract._TEXT_CACHE.clear()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ctx(self, transport):
        cache = self.tmp / "cache"
        f = fetch_ladder.Fetcher(cache, transport=transport, sleep=lambda s: None, clock=lambda: 0.0, log=lambda *a: None)
        return {"repo": self.repo, "fetcher": f, "ladder": fetch_ladder.Ladder(f, extract=eo_extract.eo_extract, log=lambda *a: None),
                "custody": fr_originals.load_custody(self.repo), "crosswalk": {},
                "state_dir": cache / "state", "state_texts": cache / "state" / "texts", "issue_blobs": set()}

    def transport(self):
        return FakeTransport({ISSUE_URL: [(200, {"content-type": "application/pdf"}, ISSUE)],
                              DOC_URL: [(200, {"content-type": "application/pdf"}, DOC)]})


class PlanTests(Base):
    def test_plan(self):
        plan = fr_originals.build_plan(self.repo, self.index)
        ids = [p["instrument_id"] for p in plan]
        self.assertEqual(ids[:3], ["EO:7534", "EO:12945", "EO:7532"])  # decided first, numeric order
        # no-network categories last, including 'not received for publication'
        self.assertEqual(ids[-3:], ["EO:7400", "EO:7533", "EO:7999"])
        cats = {p["instrument_id"]: p["category"] for p in plan}
        self.assertEqual(cats["EO:7400"], "fr_volume_1_1936")
        self.assertEqual(cats["EO:7999"], "not_in_ofr_index")
        self.assertNotIn("EO:100", cats)
        self.assertEqual(fr_originals.issue_key(plan[0]), "1937-01-12")
        self.assertIsNone(fr_originals.issue_key(plan[1]))


class RunTests(Base):
    def test_full_cycle(self):
        t = self.transport()
        ctx = self.ctx(t)
        plan = fr_originals.build_plan(self.repo, self.index)
        states, info = fr_originals.run(ctx, plan, log=lambda *a: None)
        s7532, s7534, s12945 = states["EO:7532"], states["EO:7534"], states["EO:12945"]
        self.assertEqual(s7532["status"], "found")
        self.assertEqual(s7532["source"]["page_or_item"], "2 FR 63, PDF pages 1-1")
        self.assertEqual(s7534["source"]["page_or_item"], "2 FR 64, PDF pages 2-2")
        self.assertEqual(s7532["source"]["sha256"], hashlib.sha256(ISSUE).hexdigest())
        self.assertEqual(s7532["source"]["location_confidence"], "high")
        self.assertEqual(s12945["source"]["page_or_item"], "60 FR 1, PDF pages 1-1")
        self.assertEqual(states["EO:7533"]["not_found"]["reason"], "ofr_index_not_received_for_publication")
        self.assertEqual(states["EO:7400"]["not_found"]["reason"], "fr_volume_1_1936_not_in_ofr_index")
        # the shared issue was downloaded once for both 1937 orders
        self.assertEqual(sum(1 for c in t.calls if c == ISSUE_URL), 1)
        frag = s7532["fragment"]
        self.assertEqual(frag["kind"], "original_representation")
        self.assertEqual(frag["produced_by"], "fr-originals")
        ref = frag["sources"][0]
        self.assertTrue(ref["url"].startswith("https://") and len(ref["sha256"]) == 64 and ref["page_or_item"])

        out = self.tmp / "out"
        summary = fr_originals.write_outputs(out, ctx, plan, states, info)
        self.assertEqual(summary["found"], 3)
        self.assertTrue((out / "texts" / "EO_7532.txt").read_text(encoding="utf-8").startswith("Instrument: EO:7532"))
        with open(out / "NOT_FOUND.csv", encoding="utf-8") as fh:
            nf = list(csv.DictReader(fh))
        self.assertEqual({r["instrument_id"] for r in nf}, {"EO:7533", "EO:7400", "EO:7999"})
        srcs = [json.loads(x) for x in (out / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines()]
        for s in srcs:
            for key in ("source_id", "instrument_ids", "url", "sha256", "bytes", "content_type", "retrieved_utc",
                        "route", "page_or_item", "text_path", "cache_path", "notes"):
                self.assertIn(key, s)

        # resume: nothing is fetched again
        before = len(t.calls)
        ctx2 = self.ctx(t)
        states2, info2 = fr_originals.run(ctx2, plan, log=lambda *a: None)
        self.assertEqual(len(t.calls), before)
        self.assertEqual(states2["EO:7532"]["source"]["sha256"], s7532["source"]["sha256"])
        self.assertEqual(info2["stats"]["resumed_from_state"], len(plan))

    def test_delete_issue_after_use_and_limit(self):
        ctx = self.ctx(self.transport())
        plan = fr_originals.build_plan(self.repo, self.index)
        states, info = fr_originals.run(ctx, plan, limit=1, keep_pdfs=False, log=lambda *a: None)
        # limit=1 selects EO:7534; EO:7532 shares its issue but was not selected
        self.assertEqual(set(states), {"EO:7534"})
        self.assertEqual(info["stats"].get("issue_pdfs_deleted_after_use"), 1)
        self.assertIsNone(ctx["fetcher"].cached(ISSUE_URL))
        self.assertEqual(states["EO:7534"]["source"]["sha256"], hashlib.sha256(ISSUE).hexdigest())

    def test_order_not_located(self):
        index = ofr_index.build_index([rec("7999", "2 FR 900", "1937-01-12")])
        ctx = self.ctx(self.transport())
        plan = [p for p in fr_originals.build_plan(self.repo, index) if p["instrument_id"] == "EO:7999"]
        states, _ = fr_originals.run(ctx, plan, log=lambda *a: None)
        nf = states["EO:7999"]["not_found"]
        self.assertEqual(nf["reason"], "downloaded_but_order_not_located")
        self.assertEqual(nf["downloaded_sha256"], hashlib.sha256(ISSUE).hexdigest())

    def test_stage21_reuse(self):
        d = self.repo / "research/stage21/original_sources"
        d.mkdir(parents=True)
        (d / "EO_12945.pdf").write_bytes(DOC)
        sha = hashlib.sha256(DOC).hexdigest()
        (d / "CASE_ORIGINAL_SOURCE_CUSTODY.csv").write_text(
            "instrument_id,official_PDF_candidate_URL,custody_state,sha256_source_bytes_if_present,source_repository_path,bytes,attempted_utc\n"
            f"EO:12945,{DOC_URL},PDF_BYTES_CAPTURED_NOT_AUTHENTICATED,{sha},research/stage21/original_sources/EO_12945.pdf,{len(DOC)},2026-10-17T17:49:56+00:00\n",
            encoding="utf-8")
        t = FakeTransport({})
        ctx = self.ctx(t)
        plan = [p for p in fr_originals.build_plan(self.repo, self.index) if p["instrument_id"] == "EO:12945"]
        states, _ = fr_originals.run(ctx, plan, log=lambda *a: None)
        src = states["EO:12945"]["source"]
        self.assertEqual(src["route"], "reuse/stage21_original_sources")
        self.assertEqual(src["sha256"], sha)
        self.assertEqual(src["url"], DOC_URL)
        self.assertEqual(t.calls, [])
        self.assertEqual(src["repo_path"], "research/stage21/original_sources/EO_12945.pdf")
        self.assertEqual(src["retrieved_utc"], "2026-10-17T17:49:56Z")


class ReviewFixTests(Base):
    def test_fragment_flags_and_lf_texts(self):
        ctx = self.ctx(self.transport())
        plan = fr_originals.build_plan(self.repo, self.index)
        states, info = fr_originals.run(ctx, plan, log=lambda *a: None)
        data = states["EO:7532"]["fragment"]["data"]
        self.assertIs(data["location_verified"], False)
        self.assertIs(data["needs_page_check"], False)       # high confidence
        out = self.tmp / "out"
        fr_originals.write_outputs(out, ctx, plan, states, info)
        for f in list((out / "texts").iterdir()) + [out / "SUMMARY.json"]:
            self.assertNotIn(b"\r\n", f.read_bytes(), f.name)

    def test_carry_forward_never_shrinks_and_limit_counts_new_work(self):
        t = self.transport()
        ctx = self.ctx(t)
        plan = fr_originals.build_plan(self.repo, self.index)
        states, info = fr_originals.run(ctx, plan, log=lambda *a: None)
        first = self.tmp / "first"
        fr_originals.write_outputs(first, ctx, plan, states, info)

        # A fresh machine (new cache, like GitHub) with the earlier output committed.
        import prior_output
        shutil.rmtree(self.tmp / "cache")
        t2 = FakeTransport({})
        ctx2 = self.ctx(t2)
        stats, prior_found = fr_originals.carry_forward(ctx2, plan, [prior_output.PriorOutput.from_folder(first)],
                                                        log=lambda *a: None)
        self.assertEqual(stats["found_carried"], 3)
        self.assertEqual(prior_found, 3)
        states2, info2 = fr_originals.run(ctx2, plan, limit=1, log=lambda *a: None)
        self.assertEqual(t2.calls, [])                       # nothing downloaded again
        second = self.tmp / "second"
        s2 = fr_originals.write_outputs(second, ctx2, plan, states2, info2, prior_found=prior_found)
        self.assertEqual(s2["found"], 3)
        self.assertEqual(s2["shrink_check"], "ok")
        self.assertEqual(s2["orders_carried_forward_from_committed_results"], 6)
        self.assertEqual((second / "texts" / "EO_7532.txt").read_bytes(), (first / "texts" / "EO_7532.txt").read_bytes())
        self.assertEqual((second / "FRAGMENTS.jsonl").read_bytes(), (first / "FRAGMENTS.jsonl").read_bytes())

        # JOB_LIMIT counts only orders still needing work: a new order is processed.
        index = ofr_index.build_index([rec("7532", "2 FR 63", "1937-01-12"), rec("7534", "2 FR 64", "1937-01-12"),
                                       rec("7533", None, None, not_received_for_publication=True),
                                       rec("12945", "60 FR 1", "1995-01-05", pdf_url=DOC_URL, document_number="95-1"),
                                       rec("7998", "2 FR 64", "1937-01-12")])
        plan3 = fr_originals.build_plan(self.repo, index)
        ctx3 = self.ctx(self.transport())
        states3, info3 = fr_originals.run(ctx3, plan3, limit=1, log=lambda *a: None)
        self.assertEqual(info3["selected"], 1)
        self.assertIn("EO:7998", states3)
        self.assertEqual(info3["already_finished"], len(plan3) - 1)

    def test_wrong_issue_falls_through_to_link_service(self):
        wrong_url = "https://www.govinfo.gov/content/pkg/FR-1950-08-17/pdf/FR-1950-08-17.pdf"
        right_url = "https://www.govinfo.gov/content/pkg/FR-1950-08-18/pdf/FR-1950-08-18.pdf"
        wrong = make_pdf([["5500 FEDERAL REGISTER, August 17, 1950", "under Executive Order 10153 the Board",
                           "[F. R. Doc. 50-1; Filed]"],
                          ["5501 FEDERAL REGISTER, August 17, 1950", "other"],
                          ["5502 FEDERAL REGISTER, August 17, 1950", "other"]])
        right = make_pdf([["5599 FEDERAL REGISTER, August 18, 1950", "x", "[F. R. Doc. 50-2; Filed]"],
                          ["5600 FEDERAL REGISTER, August 18, 1950", "EXECUTIVE ORDER 10153", "body",
                           "[F. R. Doc. 50-3; Filed]"],
                          ["5601 FEDERAL REGISTER, August 18, 1950", "next"]])
        t = FakeTransport({
            wrong_url: [(200, {"content-type": "application/pdf"}, wrong)],
            "https://www.govinfo.gov/link/fr/15/5600": [(302, {"location": right_url + "#page=2"}, b"")],
            right_url: [(200, {"content-type": "application/pdf"}, right)],
        })
        index = ofr_index.build_index([rec("10153", "15 FR 5600", "1950-08-17")])
        ctx = self.ctx(t)
        plan = [p for p in fr_originals.build_plan(self.repo, index) if p["instrument_id"] == "EO:10153"]
        states, _ = fr_originals.run(ctx, plan, log=lambda *a: None)
        src = states["EO:10153"]["source"]
        self.assertEqual(src["url"], right_url)
        self.assertEqual(src["route"], "official/govinfo_link_fr")
        self.assertEqual(src["page_or_item"], "15 FR 5600, PDF pages 2-2")
        self.assertEqual(src["location_confidence"], "high")

    def test_transient_failure_is_not_permanent(self):
        index = ofr_index.build_index([rec("7534", "2 FR 64", "1937-01-12")])

        def down(url, headers, timeout):
            raise ConnectionError("network is unreachable")
        cache = self.tmp / "cache"
        f = fetch_ladder.Fetcher(cache, transport=down, sleep=lambda s: None, clock=lambda: 0.0, log=lambda *a: None,
                                 max_retries=0)
        ctx = self.ctx(FakeTransport({}))
        ctx["fetcher"] = f
        ctx["ladder"] = fetch_ladder.Ladder(f, extract=eo_extract.eo_extract, log=lambda *a: None)
        plan = [p for p in fr_originals.build_plan(self.repo, index) if p["instrument_id"] == "EO:7534"]
        states, _ = fr_originals.run(ctx, plan, log=lambda *a: None)
        st = states["EO:7534"]
        self.assertEqual(st["status"], "not_found")
        self.assertFalse(st["permanent"])
        self.assertIn("retry later", st["not_found"]["detail"])

    def test_stage21_time_and_repo_path(self):
        self.assertEqual(fr_originals.normalise_utc("2026-10-17T17:49:56.920745+00:00"), "2026-10-17T17:49:56Z")
        self.assertEqual(fr_originals.normalise_utc("not a time"), "not a time")


if __name__ == "__main__":
    unittest.main()
