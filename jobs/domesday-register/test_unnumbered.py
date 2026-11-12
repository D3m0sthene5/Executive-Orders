"""Offline tests for the catalogued_unnumbered identities: dedup rule, census match, Chapman interval, seed."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unnumbered as un  # noqa: E402


def mention(mid, source, date, precision, tokens, label="x", link_wpa=""):
    return {"source": source, "mention_id": mid, "date": date, "precision": precision, "label": label,
            "tokens": "|".join(tokens), "link_wpa": link_wpa}


def edge(a, sa, b, sb, kind="blind_date_and_token"):
    return {"kind": kind, "source_a": sa, "a": a, "source_b": sb, "b": b}


def seed(n, date, cert, subject="s", page="10", cluster=""):
    return {"seed_id": f"CU:{n}", "lord_page": page, "date": date, "date_certainty": cert, "subject": subject, "cluster_id": cluster}


class Dedup(unittest.TestCase):
    def test_exact_date_and_two_words_merge_but_date_alone_never(self):
        ms = [mention("LORD:U:0001", "LORD", "1850-03-04", "day", ["fuel", "island", "michigan"]),
              mention("LORD:U:0002", "LORD", "1850-03-05", "day", ["alpha", "bravo"]),
              mention("LORD:U:0003", "LORD", "1850-03-06", "day", ["delta"]),
              mention("GLO:1", "GLO_1884", "1850-03-04", "day", ["fuel", "island", "other"]),
              mention("GLO:2", "GLO_1884", "1850-03-05", "day", ["alpha"]),            # one shared word only
              mention("GLO:3", "GLO_1884", "1850-03-06", "day", ["zulu"])]             # same date, no word
        mt = [edge("LORD:U:0001", "LORD", "GLO:1", "GLO_1884"), edge("LORD:U:0002", "LORD", "GLO:2", "GLO_1884")]
        cl = [{"cluster_id": "LORD:U:0001", "members": "LORD:U:0001|GLO:1", "label": "a", "sources": "GLO_1884|LORD"},
              {"cluster_id": "LORD:U:0002", "members": "LORD:U:0002|GLO:2", "label": "b", "sources": "GLO_1884|LORD"},
              {"cluster_id": "LORD:U:0003", "members": "LORD:U:0003", "label": "c", "sources": "LORD"},
              {"cluster_id": "GLO:3", "members": "GLO:3", "label": "d", "sources": "GLO_1884"}]
        sd = [seed(1, "1850-03-04", "day"), seed(2, "1850-03-05", "day"), seed(3, "1850-03-06", "day")]
        rows, _ = un.build_identities(sd, ms, mt, cl)
        by = {r["lord_seed_ids"] or r["cluster_ids"]: r for r in rows}
        self.assertEqual(by["CU:1"]["sources"], "LORD|GLO_1884")          # merged
        self.assertEqual(by["CU:1"]["cluster_ids"], "LORD:U:0001")
        self.assertEqual(by["CU:2"]["sources"], "LORD")                  # one shared word: not merged
        self.assertEqual(len(rows), 5)                                   # CU:1+GLO:1 merged; CU:2, CU:3, GLO:2, GLO:3 alone
        loose, _ = un.build_identities(sd, ms, mt, cl, min_shared=1)
        self.assertEqual(len(loose), 4)                                  # threshold 1 also merges CU:2 and GLO:2

    def test_month_and_year_precise_lord_dates_never_merge(self):
        ms = [mention("LORD:U:0001", "LORD", "1850-03", "month", ["fuel", "island"]),
              mention("GLO:1", "GLO_1884", "1850-03-04", "day", ["fuel", "island"])]
        mt = [edge("LORD:U:0001", "LORD", "GLO:1", "GLO_1884", "blind_year_and_two_tokens")]
        rows, _ = un.build_identities([seed(1, "1850-03", "month")], ms, mt, [])
        self.assertEqual(len(rows), 2)

    def test_numbered_cluster_mentions_are_left_out_and_lord_row_flagged(self):
        ms = [mention("LORD:U:0001", "LORD", "1880-01-02", "day", ["fuel", "island"]),
              mention("WPA:1", "WPA", "1880-01-02", "day", ["fuel", "island"]),
              mention("GLO:1", "GLO_1884", "1880-01-02", "day", ["fuel", "island"])]
        mt = [edge("LORD:U:0001", "LORD", "GLO:1", "GLO_1884"), edge("WPA:1", "WPA", "GLO:1", "GLO_1884")]
        cl = [{"cluster_id": "LORD:U:0001", "members": "LORD:U:0001|WPA:1|GLO:1", "label": "a", "sources": "GLO_1884|LORD|WPA"}]
        rows, info = un.build_identities([seed(1, "1880-01-02", "day")], ms, mt, cl)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sources"], "LORD")
        self.assertEqual(info["lord_rows_in_numbered_clusters"], ["CU:1"])

    def test_census_id_only_on_firm_match(self):
        census = [{"id": "EO:UNN:LORD1944:p10:1863-03-10"}, {"id": "EO:UN:executive-orders-01:row:1"}]
        ms = [mention("LORD:U:0001", "LORD", "1863-03-10", "day", [])]
        rows, _ = un.build_identities([seed(1, "1863-03-10", "day", page="10")], ms, [], [], census)
        self.assertEqual(rows[0]["census_id_if_any"], "EO:UNN:LORD1944:p10:1863-03-10")
        rows, _ = un.build_identities([seed(1, "1863-03-10", "day", page="11")], ms, [], [], census)   # wrong page
        self.assertEqual(rows[0]["census_id_if_any"], "")
        rows, _ = un.build_identities([seed(1, "1863-03", "month", page="10")], ms, [], [], census)    # no day
        self.assertEqual(rows[0]["census_id_if_any"], "")


class Estimator(unittest.TestCase):
    def test_chapman_textbook(self):
        r = un.chapman(100, 80, 20)
        self.assertAlmostEqual(r["N_hat"], 101 * 81 / 21 - 1, places=1)
        self.assertEqual(r["observed_union"], 160)
        lo, hi = r["ci95"]
        self.assertLess(lo, r["N_hat"])
        self.assertGreater(hi, r["N_hat"])
        self.assertGreaterEqual(lo, 160)

    def test_complete_overlap_is_degenerate_not_a_crash(self):
        r = un.chapman(10, 10, 10)
        self.assertEqual(r["ci95"], [10.0, 10.0])
        self.assertIsNone(un.chapman(0, 5, 0))

    def test_estimate_restricts_to_day_precise_years_to_1899(self):
        def row(l, c, d, cert="day"):
            return {"lord_seed_ids": l, "cluster_ids": c, "date": d, "date_certainty": cert}
        rows = [row("CU:1", "a", "1850-01-01"), row("CU:2", "", "1851-01-01"), row("", "b", "1852-01-01"),
                row("CU:3", "", "1900-01-01"), row("CU:4", "", "1850", "year"), row("CU:5", "c", "1853-01-01")]
        e = un.estimate(rows)["1789-1899"]
        self.assertEqual((e["n1"], e["n2"], e["m"]), (3, 3, 2))
        e = un.estimate(rows, exclude_seeds=["CU:5"])["1789-1899"]
        self.assertEqual((e["n1"], e["n2"], e["m"]), (2, 2, 1))


class Seed(unittest.TestCase):
    def test_dates_are_as_precise_as_printed(self):
        self.assertEqual(un.iso_date("1790", "Aug 28"), ("1790-08-28", "day"))
        self.assertEqual(un.iso_date("1790", "Sept. 7"), ("1790-09-07", "day"))
        self.assertEqual(un.iso_date("1790", "Sept"), ("1790-09", "month"))
        self.assertEqual(un.iso_date("1790", ""), ("1790", "year"))
        self.assertEqual(un.iso_date("1891", "July 37"), ("1891-07", "month"))   # impossible day is not invented

    def test_committed_seed_matches_lords_list_when_available(self):
        root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
        src = os.path.join(root, un.WPA_UNNUMBERED)
        cl = os.path.join(root, un.COMPLETENESS, "CLUSTERS.csv")
        if not (os.path.isfile(src) and os.path.isfile(cl)):
            self.skipTest("Lord list or clusters not on disk")
        committed = un.read_csv(os.path.join(HERE, un.SEED_REL))
        self.assertEqual(committed, un.build_seed(un.read_csv(src), un.read_csv(cl)))
        self.assertEqual(len(committed), 1562)
        self.assertTrue(all(len(r["subject"]) <= 300 for r in committed))


class Run(unittest.TestCase):
    def test_run_writes_outputs_on_a_tiny_repository(self):
        root = tempfile.mkdtemp(prefix="unnum-")
        try:
            d = os.path.join(root, un.COMPLETENESS)
            os.makedirs(d)

            def w(name, rows, fields):
                un.write_csv(os.path.join(d, name), rows, fields)
            w("MENTIONS.csv", [mention("LORD:U:0001", "LORD", "1850-03-04", "day", ["fuel", "island"]),
                               mention("GLO:1", "GLO_1884", "1850-03-04", "day", ["fuel", "island"]),
                               mention("GLO:2", "GLO_1884", "1851-05-06", "day", ["lone", "tract"])],
              ["source", "mention_id", "date", "precision", "label", "tokens", "link_wpa"])
            w("MATCHES.csv", [edge("LORD:U:0001", "LORD", "GLO:1", "GLO_1884")], ["kind", "source_a", "a", "source_b", "b"])
            w("CLUSTERS.csv", [{"cluster_id": "LORD:U:0001", "members": "LORD:U:0001|GLO:1", "label": "a", "sources": "GLO_1884|LORD"},
                               {"cluster_id": "GLO:2", "members": "GLO:2", "label": "lone tract", "sources": "GLO_1884"}],
              ["cluster_id", "members", "label", "sources"])
            seed_path = os.path.join(root, "SEED.csv")
            un.write_csv(seed_path, [seed(1, "1850-03-04", "day")], un.SEED_FIELDS)
            out = os.path.join(root, "_out")
            s = un.run(root, out, seed_path)
            self.assertEqual(s["unnumbered_series_observed"], 2)
            self.assertEqual(s["identities_in_both_lord_and_cluster"], 1)
            self.assertEqual(s["non_lord_residue_targets"], 1)
            rows = un.read_csv(os.path.join(out, "UNNUMBERED.csv"))
            self.assertEqual(list(rows[0]), un.OUT_FIELDS)
            with open(os.path.join(out, "TARGETS_NON_LORD_RESIDUE.txt")) as fh:
                body = [x for x in fh.read().splitlines() if not x.startswith("#")]
            self.assertEqual(body, ["CUN:M:GLO:2"])
            self.assertIn("assumptions", json.loads(open(os.path.join(out, "UNNUMBERED_SUMMARY.json")).read())["capture_recapture"])
            self.assertIsNone(s["unnumbered_series_estimate_95"], "the model interval is never reported as an estimate")
            self.assertEqual(s["raw_catalogue_identities"], 2)
            # With the census audit's identities present, the series is counted from them (D-20261112-graunt-apply).
            ad = os.path.join(root, "jobs", "domesday-register", "data"); os.makedirs(ad)
            un.write_csv(os.path.join(ad, "GRAUNT_UNNUMBERED.csv"),
                         [{"graunt_id": "A", "inferred_presidential_attribution": "no"}, {"graunt_id": "B", "inferred_presidential_attribution": "yes"},
                          {"graunt_id": "C", "inferred_presidential_attribution": "no"}], ["graunt_id", "inferred_presidential_attribution"])
            s2 = un.run(root, os.path.join(root, "_out2"), seed_path)
            self.assertEqual((s2["unnumbered_series_observed"], s2["unnumbered_series_observed_conservative"]), (3, 2))
            self.assertEqual(s2["raw_catalogue_identities"], 2)
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
