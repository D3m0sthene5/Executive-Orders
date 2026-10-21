"""PANIZZI: tests for citations embedded in prose, Public Law / Reorganization Plan / CFR routes,
the whole-run byte budget and the queue-first plan. Small fixtures, no network."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import embedded_cites as ec  # noqa: E402
import fetch_ladder as fl  # noqa: E402
import ladder_queue  # noqa: E402
import plan as plan_mod  # noqa: E402
from test_fetch_ladder import Base, FakeTransport, make_pdf  # noqa: E402


def cites(text, **kw):
    return [c["cite"] for c in ec.find_embedded(text, **kw)]


class EmbeddedCitationTests(unittest.TestCase):
    def test_statutes_and_public_laws_from_real_queue_lines(self):
        self.assertEqual(cites("71 Stat. 78 (sec. 202, Dept. of Commerce and Related Agencies Appropriation Act, 1958) "
                               "and 71 Stat. 312 (sec. 608, Dept. of Defense Appropriation Act, 1958)"),
                         ["71 Stat. 78", "71 Stat. 312"])
        # Public Law + Stat. of the same enactment: the exact Stat. page wins, the Public Law is not fetched twice.
        self.assertEqual(cites("Pub. L. 94-412, National Emergencies Act, sec. 101(a), 90 Stat. 1255 (Sept. 14, 1976)"),
                         ["90 Stat. 1255"])
        self.assertEqual(cites("Termination of the emergency (National Emergencies Act, Pub. L. 94-412 sec. 101, 1978)"),
                         ["Pub. L. 94-412"])
        # Congress-first and run-together spellings from the queue.
        self.assertEqual(cites("Pub. L. 453, 83d Cong., sec. 103 and Pub. L. 458, 83d Cong., sec. 710"),
                         ["Pub. L. 83-453", "Pub. L. 83-458"])
        self.assertEqual(cites("Foreign Service Act of 1946, Public Law724, 79th Congress, August13,1946,60Stat999"),
                         ["60 Stat. 999"])
        self.assertEqual(cites("P.L.96-88,93Stat668; actual reorganization"), ["93 Stat. 668"])
        self.assertEqual(cites("Public Law93-531, Dec22,1974, 88 Stat1712"), ["88 Stat. 1712"])
        self.assertEqual(cites("Public Law 92-463, 86 Stat. 770-776; sections 3(2) and 14"), ["86 Stat. 770"])
        self.assertEqual(cites("Water Quality Improvement Act of 1970, Pub. L. 91-224 (84 Stat. 91, April 3, 1970)"),
                         ["84 Stat. 91"])
        self.assertEqual(cites("Pub. L. 98-525 (98 Stat. 2492, Department of Defense Authorization Act, 1985)"),
                         ["98 Stat. 2492"])

    def test_not_a_statute_cite(self):
        self.assertEqual(cites("Statutes at Large, page 5; the 7 Statesmen"), [])
        self.assertEqual(cites("Public Resolution 83, 75th Congress"), [])

    def test_code_and_cfr(self):
        text = ("50 U.S.C. 98 note ('Ex. Ord. No. 12626'); current Act, 15 U.S.C. 714b(h), and the title 40 "
                "successor of 40 U.S.C. 485(f)")
        self.assertEqual(cites(text), ["50 U.S.C. 98", "15 U.S.C. 714b", "40 U.S.C. 485"])
        self.assertEqual(cites("36 U.S.C. ch. 21 (American Battle Monuments Commission)"), [])
        self.assertEqual(cites("5 U.S.C. 5312-5316"), ["5 U.S.C. 5312"])
        self.assertEqual(cites("22 CFR part 22 (consular fee provisions) and 46 CFR 393.3"),
                         ["22 CFR 22", "46 CFR 393.3"])
        self.assertEqual(cites("41 CFR 102-74.315 (eCFR, current through 2026-10-14)"), ["41 CFR 102-74.315"])
        # Title 3 is the compilation of presidential documents; "CFR" is never read as "FR".
        self.assertEqual(cites("EO 9704 (11 FR 2675; 3 CFR 1943-1948 Comp. p. 519)", skip_fr=[(11, 2675)]), [])
        self.assertEqual([c["kind"] for c in ec.find_embedded("5 CFR Part 6 in 1953")], ["CFR"])

    def test_federal_register_and_own_page_skip(self):
        self.assertEqual(cites("65 FR 39279; 77 FR 38459"), ["65 FR 39279", "77 FR 38459"])
        self.assertEqual(cites("65 FR 39279; 77 FR 38459", skip_fr=[(65, 39279)]), ["77 FR 38459"])
        self.assertEqual(cites("EO11829 40 FR1497 PDF page11; retain page images"), ["40 FR 1497"])

    def test_reorganization_plans(self):
        self.assertEqual(cites("Reorganization Plan No. 2 of 1968 (urban mass transportation functions of HUD)"),
                         ["Reorganization Plan No. 2 of 1968"])
        # A plan whose line already gives its Stat. cite is fetched by that cite.
        self.assertEqual(cites("Reorganization Plan No. 3 of 1970 (35 FR 15623; 84 Stat. 2086)"),
                         ["35 FR 15623", "84 Stat. 2086"])
        self.assertEqual(cites("Reorganization Plan No. 2 of 1946 (60 Stat. 1095; abolition)"), ["60 Stat. 1095"])

    def test_limit_and_overflow(self):
        text = " ".join(f"{v} Stat. 1" for v in range(10, 20))
        kept, extra = ec.find_embedded_with_overflow(text)
        self.assertEqual(len(kept), ec.MAX_CITES_PER_LINE)
        self.assertEqual(len(extra), 4)
        self.assertEqual([c["cite"] for c in kept], [f"{v} Stat. 1" for v in range(10, 16)])

    def test_deterministic(self):
        t = "Pub. L. 453, 83d Cong.; 50 U.S.C. 98; 71 Stat. 78"
        self.assertEqual(ec.find_embedded(t), ec.find_embedded(t))


class RouteTests(unittest.TestCase):
    def test_parse_new_kinds(self):
        self.assertEqual(fl.parse_citation("Pub. L. 98-525"), ("PLAW", {"congress": 98, "number": 525}))
        self.assertEqual(fl.parse_citation("Reorganization Plan No. 2 of 1968"), ("RP", {"number": 2, "year": 1968}))
        self.assertEqual(fl.parse_citation("41 CFR 102-74.315"), ("CFR", {"title": 41, "part": "102-74", "section": "315"}))
        self.assertEqual(fl.parse_citation("5 CFR 352")[1]["part"], 352)
        # still a whole-string parser: prose is not a citation
        self.assertEqual(fl.parse_citation("Pub. L. 98-525 (98 Stat. 2492, Department of Defense Authorization Act)"), (None, {}))

    def urls(self, citation, **kw):
        return [(r.route, r.url) for r in fl.official_routes(fl.Wanted("x", ["EO:1"], citation=citation, **kw))[0]]

    def test_public_law_routes(self):
        old = self.urls("Pub. L. 98-525")
        self.assertEqual(old, [("govinfo_link_statute_publaw", "https://www.govinfo.gov/link/statute/98/public/525")])
        new = self.urls("Pub. L. 104-1")
        self.assertEqual([r for r, _ in new], ["govinfo_link_plaw", "govinfo_link_statute_publaw"])
        self.assertEqual(new[0][1], "https://www.govinfo.gov/link/plaw/104/public/1?link-type=pdf")

    def test_cfr_has_no_robots_disallowed_renderer_api_route(self):
        # ecfr.gov/robots.txt disallows /api/renderer/v1/content/ (checked 2026-10-20); the ladder obeys robots.txt.
        names = [n for n, _ in self.urls("22 CFR 22.1")]
        self.assertEqual(names, ["govinfo_link_cfr", "ecfr_on_cutoff"])
        self.assertIn("/link/cfr/41/102-74?", self.urls("41 CFR 102-74.315")[0][1])

    def test_reorganization_plan_route_is_an_index_not_a_source(self):
        routes, kind, _ = fl.official_routes(fl.Wanted("x", ["EO:1"], citation="Reorganization Plan No. 2 of 1968"))
        self.assertEqual(kind, "RP")
        self.assertTrue(routes and all(r.kind == "rp_index" for r in routes))
        self.assertIn("USCODE-2024-title5-app.pdf", routes[0].url)

    def test_prose_with_a_given_link_falls_back_to_embedded_official_routes(self):
        w = fl.Wanted("x", ["EO:1"], urls=["https://www.govinfo.gov/content/pkg/STATUTE-93/pdf/STATUTE-93-Pg668.pdf"],
                      citation="Public Law 96-88, Department of Education Organization Act, 93 Stat. 668; savings")
        plan = fl.plan_routes(w)
        self.assertEqual(plan[0].tier, "given")
        official = [r.url for r in plan if r.tier == "official"]
        self.assertIn("https://www.govinfo.gov/link/statute/93/668", official)
        # ...but never the Federal Register page where an order was printed
        w2 = fl.Wanted("y", ["EO:1"], urls=["https://www.govinfo.gov/content/pkg/FR-1990-05-02/pdf/90-1.pdf"],
                       citation="40 FR 1497 PDF page 11; retain page images")
        self.assertFalse([r for r in fl.plan_routes(w2) if r.tier == "official"])


class ReviewRegressionTests(unittest.TestCase):
    """Adversarial review (2026-10-20): defects found and fixed."""

    def test_an_unrelated_stat_cite_does_not_drop_a_public_law_or_plan(self):
        # 90 Stat. is the 94th Congress; Pub. L. 98-525 is in 98 Stat., so it is a different enactment.
        self.assertEqual(cites("sec. 1632 of Pub. L. 98-525; compare National Emergencies Act, 90 Stat. 1255"),
                         ["Pub. L. 98-525", "90 Stat. 1255"])
        self.assertEqual(cites("Reorganization Plan No. 2 of 1946; compare 90 Stat. 1255"),
                         ["Reorganization Plan No. 2 of 1946", "90 Stat. 1255"])
        self.assertEqual(cites("Reorganization Plan No. 3 of 1970 (35 FR 15623; 84 Stat. 2086)"), ["35 FR 15623", "84 Stat. 2086"])

    def test_code_section_does_not_swallow_et_seq(self):
        self.assertEqual(cites("5USC3345etseq;EO13472,11030"), ["5 U.S.C. 3345"])
        self.assertEqual(cites("15USC657b;PublicLaw110-186section102"), ["15 U.S.C. 657b", "Pub. L. 110-186"])

    def test_fallback_only_for_the_document_the_link_names(self):
        w = fl.Wanted("x", ["EO:12978"], urls=["https://www.ecfr.gov/current/title-31/part-536"],
                      citation="Most recent continuation notice under 50 U.S.C. 1622(d) ... and 31 CFR part 536")
        official = [r.url for r in fl.plan_routes(w) if r.tier == "official"]
        self.assertTrue(official and all("title-31" in u or "/cfr/31/" in u for u in official), official)
        # a link to a dated Code edition gets no current-edition fallback
        w2 = fl.Wanted("y", ["EO:12095"], citation="Railway Labor Act section10, 45 USC160, historical text",
                       urls=["https://www.govinfo.gov/content/pkg/USCODE-1976-title45/pdf/USCODE-1976-title45-chap8-subchapI-sec160.pdf"])
        self.assertFalse([r for r in fl.plan_routes(w2) if r.tier == "official"])
        # an index page names no document
        w3 = fl.Wanted("z", ["EO:13054"], citation="5USC3301,3302;22USC3310;EO13054",
                       urls=["https://www.congress.gov/public-laws/119th-congress"])
        self.assertFalse([r for r in fl.plan_routes(w3) if r.tier == "official"])
        # the same Act's Stat. granule (Public Law in a volume of its Congress) still falls back
        w4 = fl.Wanted("v", ["EO:12095"], citation="Airline Deregulation Act of1978, Public Law95-504, especially section44",
                       urls=["https://www.govinfo.gov/content/pkg/STATUTE-92/pdf/STATUTE-92-Pg1705.pdf"])
        self.assertIn("https://www.govinfo.gov/link/statute/95/public/504", [r.url for r in fl.plan_routes(w4)])

    def test_title5_appendix_is_never_tried_through_wayback(self):
        routes = fl.plan_routes(fl.Wanted("x", ["EO:1"], citation="Reorganization Plan No. 2 of 1968"))
        self.assertTrue(routes)
        self.assertEqual({r.kind for r in routes}, {"rp_index"})


class QueueExpansionTests(Base):
    def read(self, lines, idx=None):
        p = self.tmp / "FETCH_QUEUE.jsonl"
        p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
        return ladder_queue.read_fetch_queue(p, idx or {})

    def test_prose_becomes_one_item_per_embedded_cite(self):
        items, problems = self.read([
            {"instrument_id": "EO:10568", "step": "ending_or_current_basis", "requested_by": "Craigellachie",
             "citation": "Pub. L. 453, 83d Cong., sec. 103 and Pub. L. 458, 83d Cong., sec. 710: text and duration"}])
        self.assertEqual(problems, [])
        self.assertEqual([w.citation for w in items], ["Pub. L. 83-453", "Pub. L. 83-458"])
        self.assertEqual(items[0].wanted_id, "queue:EO:10568:" + items[0].extra["parent_citation"] + " <Pub. L. 83-453>")
        self.assertEqual(items[0].instrument_ids, ["EO:10568"])
        self.assertEqual(items[0].step, "ending_or_current_basis")
        self.assertTrue(all(fl.plan_routes(w) for w in items))
        self.assertEqual(len({w.wanted_id for w in items}), 2)

    def test_the_orders_own_federal_register_page_is_not_requested_again(self):
        idx = {"EO:12616": {"primary": {"citation": "52 FR 46729"}, "others": []}}
        items, _ = self.read([{"instrument_id": "EO:12616", "step": "ending_or_current_basis",
                               "citation": "Proclamation 5748 of Nov. 24, 1987 (printed with EO 12616, 52 FR 46729); record of withdrawal"}], idx)
        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0].extra.get("parent_wanted_id"))      # nothing to expand
        self.assertEqual(fl.plan_routes(items[0]), [])                  # kept, so the no_route failure is recorded

    def test_lines_with_a_link_or_a_bare_cite_are_untouched(self):
        items, _ = self.read([
            {"instrument_id": "EO:1", "citation": "93 Stat. 29"},
            {"instrument_id": "EO:2", "citation": "Public Law 92-463, 86 Stat. 770-776",
             "urls": ["https://www.govinfo.gov/content/pkg/STATUTE-86/pdf/STATUTE-86-Pg770.pdf"]}])
        self.assertEqual([w.citation for w in items], ["93 Stat. 29", "Public Law 92-463, 86 Stat. 770-776"])


class ResolverWalkTests(Base):
    def ladder(self, transport, **kw):
        return fl.Ladder(self.fetcher(transport, **kw), tiers=("official",))

    def test_public_law_found_through_the_statute_link_service(self):
        pdf = make_pdf([["PUBLIC LAW 98-525", "98 STAT. 2492", "Department of Defense Authorization Act, 1985" * 3]])
        url = "https://www.govinfo.gov/link/statute/98/public/525"
        t = FakeTransport({url: [(200, {"content-type": "application/pdf"}, pdf)]})
        w = fl.Wanted("q <Pub. L. 98-525>", ["EO:12499"], citation="Pub. L. 98-525", step="ending_or_current_basis",
                      extra={"parent_citation": "Text of sec. 1632 of Pub. L. 98-525 ..."})
        res = self.ladder(t).walk(w)
        src = res["source"]
        self.assertIsNotNone(src, res["attempts"])
        self.assertEqual(src["route"], "official/govinfo_link_statute_publaw")
        self.assertEqual(src["sha256"], fl.sha256_bytes(pdf))
        self.assertIn("public law 98-525 seen", src["notes"])
        self.assertTrue(src["embedded_in_request"].startswith("Text of sec. 1632"))

    def test_public_law_not_found_is_kept_as_a_failure(self):
        res = self.ladder(FakeTransport({})).walk(fl.Wanted("q", ["EO:1"], citation="Pub. L. 82-504"))
        self.assertIsNone(res["source"])
        self.assertEqual(res["attempts"][0]["url"], "https://www.govinfo.gov/link/statute/82/public/504")
        self.assertEqual(res["attempts"][0]["error"], "http_404")
        self.assertEqual(res["outcome"], "exhausted")      # a definitive 404 is only a PROPOSAL, as for any item

    def test_reorganization_plan_is_resolved_through_the_title_5_appendix(self):
        index = make_pdf([["TITLE 5, APPENDIX - REORGANIZATION PLAN NO. 2 OF 1970 MESSAGE OF THE PRESIDENT"],
                          ["REORGANIZATION PLAN NO. 2 OF 1970", "Eff. July 1, 1970, 35 F.R. 7959, 84 Stat. 2085, as amended"]])
        plan_pdf = make_pdf([["REORGANIZATION PLAN NO. 2 OF 1970", "Prepared by the President" * 10]])
        idx_url = "https://www.govinfo.gov/content/pkg/USCODE-2024-title5/pdf/USCODE-2024-title5-app.pdf"
        stat_url = "https://www.govinfo.gov/link/statute/84/2085"
        t = FakeTransport({idx_url: [(200, {"content-type": "application/pdf"}, index)],
                           stat_url: [(200, {"content-type": "application/pdf"}, plan_pdf)]})
        w = fl.Wanted("q <Reorganization Plan No. 2 of 1970>", ["EO:11367"], citation="Reorganization Plan No. 2 of 1970")
        res = self.ladder(t).walk(w)
        src = res["source"]
        self.assertIsNotNone(src, res["attempts"])
        self.assertEqual(src["route"], "official/govinfo_link_statute_from_rp_index")
        self.assertEqual(src["sha256"], fl.sha256_bytes(plan_pdf))        # the original, never the compilation
        self.assertNotEqual(src["sha256"], fl.sha256_bytes(index))
        self.assertEqual(res["attempts"][0]["note"], "index lists FR 35/7959; STAT 84/2085")
        self.assertNotIn("USCODE-2023", " ".join(t.calls))                 # the second edition was not needed

    def test_plan_missing_from_the_appendix_is_retry_later_never_exhausted(self):
        index = make_pdf([["REORGANIZATION PLAN NO. 2 OF 1970", "Eff. July 1, 1970, 35 F.R. 7959, 84 Stat. 2085"]])
        ok = {"content-type": "application/pdf"}
        t = FakeTransport({
            "https://www.govinfo.gov/content/pkg/USCODE-2024-title5/pdf/USCODE-2024-title5-app.pdf": [(200, ok, index)],
            "https://www.govinfo.gov/content/pkg/USCODE-2023-title5/pdf/USCODE-2023-title5-app.pdf": [(200, ok, index)]})
        res = self.ladder(t).walk(fl.Wanted("q", ["EO:1"], citation="Reorganization Plan No. 9 of 1999"))
        self.assertIsNone(res["source"])
        self.assertEqual(res["outcome"], "retry_later")
        self.assertEqual({a["error"] for a in res["attempts"]}, {"rp_not_found_in_title5_appendix"})
        self.assertIsNone(res["exhausted"])

    def test_a_compilation_copy_is_rejected_as_a_plans_source(self):
        index = make_pdf([["TITLE 5, APPENDIX", "REORGANIZATION PLAN NO. 2 OF 1968 text " * 20]])
        url = "https://web.archive.org/web/2024id_/https://www.govinfo.gov/content/pkg/USCODE-2024-title5/pdf/USCODE-2024-title5-app.pdf"
        t = FakeTransport({url: [(200, {"content-type": "application/pdf"}, index)]})
        w = fl.Wanted("q", ["EO:11299"], citation="Reorganization Plan No. 2 of 1968")
        res = fl.Ladder(self.fetcher(t)).walk(w, routes=[fl.Route("wayback_id_", url, "pdf", tier="wayback_official")])
        self.assertIsNone(res["source"])
        self.assertIn("compilation", res["attempts"][0]["reject_reason"])

    def test_rp_index_cites_reads_both_heading_forms(self):
        self.assertEqual(fl.rp_index_cites("REORGANIZATION PLAN NO. 3 OF 1970 Eff. Dec. 2, 1970, 35 F.R. 15623, 84 Stat. 2086, as amended",
                                           3, 1970), {"fr": (35, 15623), "stat": (84, 2086)})
        self.assertEqual(fl.rp_index_cites("Reorganization Plan No. 2 of 1968, 33 F.R. 6965, 82 Stat. 1369, as amended", 2, 1968),
                         {"fr": (33, 6965), "stat": (82, 1369)})
        # a running page header followed by prose is not a heading with cites
        self.assertEqual(fl.rp_index_cites("TITLE 5, APPENDIX REORGANIZATION PLAN NO. 2 OF 1946 MESSAGE OF THE PRESIDENT in 12 F.R. 5",
                                           2, 1946), {})

    def test_govinfo_metadata_is_never_the_found_document(self):
        pdf_url = "https://www.govinfo.gov/content/pkg/STATUTE-95/pdf/STATUTE-95-Pg357.pdf"
        meta_url = "https://www.govinfo.gov/metadata/pkg/STATUTE-95/premis.xml"
        t = FakeTransport({meta_url: [(200, {"content-type": "application/xml"}, b"<premis>" + b"<event/>" * 300 + b"</premis>")]})
        w = fl.Wanted("q", ["EO:12075"], urls=[pdf_url, meta_url], citation="P.L.97-35,95Stat357; block grant provisions")
        res = fl.Ladder(self.fetcher(t), tiers=("given",)).walk(w)
        self.assertIsNone(res["source"])
        meta = [a for a in res["attempts"] if a["url"] == meta_url][0]
        self.assertTrue(meta["sha256"])                               # the metadata bytes are still hashed and logged
        self.assertIn("metadata", meta["reject_reason"])


class BudgetAndPlanTests(Base):
    def test_total_download_budget_stops_the_run(self):
        body = make_pdf([["Statute text " * 20]])
        t = FakeTransport({f"https://www.govinfo.gov/link/statute/1/{n}": [(200, {"content-type": "application/pdf"}, body)]
                           for n in (1, 2, 3)})
        f = self.fetcher(t, max_total_bytes=len(body) + 1)
        self.assertTrue(f.fetch("https://www.govinfo.gov/link/statute/1/1", "a", "pdf")["accepted"])
        self.assertTrue(f.fetch("https://www.govinfo.gov/link/statute/1/2", "a", "pdf")["accepted"])   # 1 byte under budget
        before = f.requests
        with self.assertRaises(fl.BudgetExceeded):
            f.fetch("https://www.govinfo.gov/link/statute/1/3", "a", "pdf")
        self.assertEqual(f.requests, before)       # nothing further was requested

    def tracker(self, ids_open):
        p = self.tmp / "READINESS.csv"
        cols = "instrument_id,step_ending_or_current_basis,step_shared_sources,blockers"
        p.write_text(cols + "\n" + "\n".join(f"{i},{s},closed," for i, s in ids_open) + "\n", encoding="utf-8")
        return p

    def test_queue_first_plan(self):
        W = lambda wid, iid, step="ending_or_current_basis": fl.Wanted(wid, [iid], citation="71 Stat. 78", step=step)
        items = [W("shared-a", "EO:3", "shared_sources"), W("queue:EO:1:a", "EO:1"), W("queue:EO:2:b", "EO:2"),
                 W("queue:EO:9:closed", "EO:9"), W("queue:EO:4:done", "EO:4")]
        tr = self.tracker([("EO:1", "open"), ("EO:2", "open"), ("EO:3", "closed"), ("EO:9", "closed"), ("EO:4", "open")])
        p = plan_mod.make_queue_first_plan(items, found={"queue:EO:4:done"}, tried={"queue:EO:1:a"}, tracker_path=tr)
        # requested lines first (untried before tried; a closed step still counts because someone asked),
        # found ones dropped, shared-source item last and only if it could complete a step (here it cannot).
        self.assertEqual(p["wanted_ids"], ["queue:EO:2:b", "queue:EO:9:closed", "queue:EO:1:a"])
        self.assertEqual((p["max_requests"], p["schema"]), (300, "eo-source-plan/v1"))
        self.assertEqual(plan_mod.select_plan(items, p), [items[2], items[3], items[1]])
        again = plan_mod.make_queue_first_plan(items, found={"queue:EO:4:done"}, tried={"queue:EO:1:a"}, tracker_path=tr)
        self.assertEqual(p, again)

    def test_queue_first_plan_is_bounded(self):
        items = [fl.Wanted(f"queue:EO:{n}:x", [f"EO:{n}"], citation="71 Stat. 78") for n in range(1, 80)]
        tr = self.tracker([(f"EO:{n}", "open") for n in range(1, 80)])
        p = plan_mod.make_queue_first_plan(items, set(), set(), tr)
        self.assertEqual(len(p["wanted_ids"]), 50)
        self.assertEqual(p["max_requests"], 300)
        with self.assertRaises(ValueError):
            plan_mod.make_queue_first_plan(items, set(), set(), tr, limit=51)
        with self.assertRaises(ValueError):
            plan_mod.make_queue_first_plan(items, set(), set(), tr, budget=301)


if __name__ == "__main__":
    unittest.main()
