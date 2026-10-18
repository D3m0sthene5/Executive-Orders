import csv
import json
import pathlib
import random
import tempfile
import unittest

import complete as C

HERE = pathlib.Path(__file__).resolve().parent


class Estimators(unittest.TestCase):
    def test_wilson(self):
        p, lo, hi = C.wilson(181, 188)
        self.assertAlmostEqual(p, 0.9628, places=3)
        self.assertLess(lo, p)
        self.assertGreater(hi, p)
        self.assertEqual(C.wilson(0, 0), (None, None, None))

    def test_chapman_textbook(self):
        # 100 marked, 100 recaptured, 20 marked among them: Chapman gives 101*101/21 - 1 = 484.7
        r = C.chapman(100, 100, 20)
        self.assertAlmostEqual(r["N_hat"], 484.8, places=1)
        self.assertLessEqual(r["ci95"][0], 484.8)
        self.assertGreaterEqual(r["ci95"][1], 484.8)

    def test_mt_mle_two_lists_equals_petersen(self):
        # Two lists of 100 with 20 shared: S = 180; Mt MLE solves (1-100/N)^2 = 1-180/N -> N = 500 (Petersen)
        self.assertAlmostEqual(C.mt_mle([100, 100], 180), 500.0, places=0)
        self.assertIsNone(C.mt_mle([100], 100))
        self.assertEqual(C.mt_mle([50, 50], 50), 50.0)
        ci = C.mt_ci(500.0, [100, 100], 180)
        self.assertLess(ci[0], 500)
        self.assertGreater(ci[1], 500)
        self.assertIsNone(C.chapman(0, 10, 0))

    def test_chao1(self):
        r = C.chao1({1: 20, 2: 10, 3: 5}, 35)
        self.assertEqual(r["N_hat"], 55.0)
        self.assertEqual(r["undiscovered_hat"], 20.0)
        self.assertLess(r["ci95"][0], 55)
        self.assertGreater(r["ci95"][1], 55)
        r = C.chao1({1: 4}, 4)
        self.assertEqual(r["N_hat"], 10.0)
        r = C.chao1({2: 5, 3: 2}, 7)
        self.assertEqual(r["undiscovered_hat"], 0.0)


class Matching(unittest.TestCase):
    def test_date_alone_never_matches(self):
        a = C.mention("LORD", "LORD:U:0001", "1838-01-10", "day", "Certain lands on Pensacola Bay reserved for naval purposes", "p", seq=1)
        b = C.mention("MR_1916", "MR_1916:p55:1", "1838-01-10", "day", "FORT BARRANCAS Pensacola Harbor", "p")
        c = C.mention("GLO_1894", "GLO_1894:p10:1", "1838-01-10", "day", "Bois Blanc fuel Mackinac", "p")
        matches, ambiguous = C.match_mentions([a, b, c])
        pairs = {(m["a"], m["b"]) for m in matches}
        self.assertIn(("LORD:U:0001", "MR_1916:p55:1"), pairs)
        self.assertEqual(len([m for m in matches if "GLO" in m["a"] + m["b"]]), 0)
        self.assertEqual(len(ambiguous), 2)

    def test_year_only_lord_entry_needs_two_words(self):
        a = C.mention("LORD", "LORD:U:0021", "1830", "year", "Fort Brooke Military Reservation Florida Territory Hillsboro", "p", seq=21)
        b = C.mention("MR_1916", "MR_1916:p478:1", "1830-12-10", "day", "BROOKE FORT FLA Hillsboro executive order", "p")
        c = C.mention("MR_1916", "MR_1916:p9:1", "1830-03-01", "day", "SITKA barracks Hillsboro", "p")
        matches, _ = C.match_mentions([a, b, c])
        kinds = {(m["b"], m["kind"]) for m in matches}
        self.assertIn(("MR_1916:p478:1", "blind_year_and_two_tokens"), kinds)
        self.assertNotIn(("MR_1916:p9:1", "blind_year_and_two_tokens"), kinds)

    def test_numbered_orders_are_set_aside(self):
        a = C.mention("LORD", "LORD:U:0010", "1865-04-29", "day", "Restrictions upon commercial intercourse discontinued", "p", seq=10)
        b = C.mention("RICH_VI", "RICH_VI-150", "1865-04-29", "day", "EXECUTIVE ORDER commercial intercourse restrictions", "p", link_wpa=["EO:3"], signer="president", form="order")
        w = C.mention("WPA", "EO:3", "1865-04-29", "day", "Restrictions upon commercial intercourse discontinued", "p")
        matches, _ = C.match_mentions([a, b, w])
        cl = C.clusters([a, b, w], matches, {m["kind"] for m in matches})
        self.assertEqual(len(cl), 1)
        self.assertTrue(cl[0]["numbered"])
        est = C.estimate(cl, ["LORD", "RICH_VI", "WPA"])["1862-1899"]
        self.assertEqual(est["clusters_observed"], 0)
        self.assertEqual(est["numbered_orders_excluded"], 1)

    def test_citation_links_are_their_own_kind(self):
        a = C.mention("LORD", "LORD:U:0184", "1862-10-20", "day", "Provisional court Louisiana Peabody", "p", seq=184)
        b = C.mention("RICH_VI", "RICH_VI-061", "1862-10-20", "day", "EXECUTIVE MANSION provisional court", "p", link_lord=["184"], signer="president", form="order")
        matches, _ = C.match_mentions([a, b])
        self.assertEqual(sorted(m["kind"] for m in matches), ["blind_date_and_token", "citation_link"])
        cl = C.clusters([a, b], matches, {"citation_link"})
        self.assertEqual(len(cl), 1)
        self.assertEqual(cl[0]["sources"], ["LORD", "RICH_VI"])

    def test_book_mentions_dedupe_by_date_and_heading(self):
        pages = [{"image": 60, "printed": 52, "text": "WASHINGTON BARRACKS.\nThis reservation is on Greenleaf's Point.\nannounced by Executive order dated July 25, 1798. The area\nis 86 acres.\nFORT WASHINGTON.\nReserved by Executive order dated July 25, 1798 as well.\nand by Executive order dated July 25, 1798 again."}]
        ms = C.book_mentions("MR_1916", pages)
        self.assertEqual(len(ms), 2)
        self.assertEqual(ms[0]["date"], "1798-07-25")
        self.assertIn("barracks", ms[0]["tokens"])
        self.assertIn("washington", ms[1]["tokens"])


class SyntheticPopulation(unittest.TestCase):
    """A hidden population of 400 orders; three lists catch them with different probabilities. The
    estimators must recover the truth within their intervals and the blind matcher must link them."""

    def test_recovers_known_population(self):
        rng = random.Random(7)
        names = ["mackinac", "barrancas", "pembina", "totten", "brooke", "morgan", "gaines", "pickens", "sitka", "vancouver", "laramie", "kearny", "snelling", "leavenworth", "monroe", "sumter"]
        truth = []
        for i in range(400):
            y = rng.randint(1801, 1861)
            d = f"{y:04d}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
            truth.append((d, f"{names[i % len(names)]} reservation number{i} established"))
        mentions = []
        catch = {"LORD": 0.7, "MR_1916": 0.5, "GLO_1890": 0.4}
        for src, p in catch.items():
            for i, (d, label) in enumerate(truth):
                if rng.random() < p:
                    mentions.append(C.mention(src, f"{src}:{i}", d, "day", label, "p", seq=i))
        matches, ambiguous = C.match_mentions(mentions)
        cl = C.clusters(mentions, matches, {"blind_date_and_token"})
        self.assertLessEqual(len(cl), 400)
        est = C.estimate(cl, ["LORD", "MR_1916", "GLO_1890"])["1801-1861"]
        mt = est["mt_all_lists"]
        self.assertLessEqual(mt["ci95"][0], 400, mt)
        self.assertGreaterEqual(mt["ci95"][1], 400, mt)
        self.assertAlmostEqual(mt["N_hat"], 400, delta=25)
        # Chao1 assumes heterogeneity across orders, not lists; with lists this different it runs high.
        self.assertGreater(est["chao1_all_lists"]["N_hat"], mt["N_hat"])
        for src in ("MR_1916", "GLO_1890"):
            c = est["lord_vs_each_list"][src]["chapman_vs_lord"]
            self.assertLessEqual(c["ci95"][0], 400, src)
            self.assertGreaterEqual(c["ci95"][1], 400, src)
            self.assertAlmostEqual(est["lord_vs_each_list"][src]["lord_coverage"], 0.7, delta=0.1)


class EndToEnd(unittest.TestCase):
    def test_runs_on_committed_inputs(self):
        repo = HERE.parent.parent
        if not (repo / "jobs/richardson-volumes/output/RICH_VI_ORDERS.csv").is_file():
            self.skipTest("richardson-volumes output not in this checkout")
        with tempfile.TemporaryDirectory() as tmp:
            s = C.run(repo, HERE, pathlib.Path(tmp) / "out", books_dir=pathlib.Path(tmp) / "no-books")
            for name in ("MENTIONS.csv", "MATCHES.csv", "AMBIGUOUS_MATCHES.csv", "CLUSTERS.csv", "OVERLAP_MATRIX.csv", "ESTIMATES.json", "COVERAGE_BY_SERIES.csv", "REPORT.md", "SUMMARY.json"):
                self.assertTrue((pathlib.Path(tmp) / "out" / name).is_file(), name)
            self.assertGreater(s["mentions"]["LORD"], 1000)
            self.assertIn("RICH_VI", s["mentions"])
            self.assertGreater(s["matches"].get("citation_link", 0), 100)
            self.assertIsNotNone(s["estimates_all_matches"]["1789-1899"]["mt_all_lists"])

    def test_source_universe_map_is_well_formed(self):
        with (HERE / "data/SOURCE_UNIVERSE.csv").open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertGreater(len(rows), 20)
        keys = [r["series_key"] for r in rows]
        self.assertEqual(len(keys), len(set(keys)))
        for r in rows:
            self.assertIn(r["search_status"], ("searched_to_end", "sampled", "planned", "not_searched", "inaccessible_online"), r["series_key"])
            self.assertTrue(r["era_from"].isdigit() and r["era_to"].isdigit(), r["series_key"])


if __name__ == "__main__":
    unittest.main()
