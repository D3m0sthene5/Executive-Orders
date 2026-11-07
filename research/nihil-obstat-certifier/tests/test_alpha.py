"""Tests for alpha.py against published worked examples and hand derivations.

Run:  py -I tests/test_alpha.py
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import alpha  # noqa: E402

S = None  # a missing observation


def units_from(rows):
    """rows: {coder: [value per unit]} -> list of units."""
    n = len(next(iter(rows.values())))
    return [[rows[c][u] for c in rows] for u in range(n)]


class PublishedExamples(unittest.TestCase):
    def test_wikipedia_three_coders_fifteen_units(self):
        # Source: https://en.wikipedia.org/wiki/Krippendorff%27s_alpha ("Example": coders A, B, C; 15 units;
        # '*' = no observation). Page states n = 26 pairable values and nominal alpha = 0.691
        # (retrieved 2026-11-06). Units 2 and 14 hold no observation and are not pairable.
        rows = {"A": [S, S, S, S, S, 3, 4, 1, 2, 1, 1, 3, 3, S, 3],
                "B": [1, S, 2, 1, 3, 3, 4, 3, S, S, S, S, S, S, S],
                "C": [S, S, 2, 1, 3, 4, 4, S, 2, 1, 1, 3, 3, S, 4]}
        r = alpha.alpha_nominal(units_from(rows), detail=True)
        self.assertEqual(round(r["n"]), 26)
        self.assertAlmostEqual(r["alpha"], 0.691, places=3)

    def test_krippendorff_2011_nominal_example(self):
        # Source: Krippendorff (2011), "Computing Krippendorff's Alpha-Reliability", Departmental Papers (ASC) 43,
        # Univ. of Pennsylvania: four observers, twelve units, nominal values; published alpha = 0.743 with 40
        # pairable values. NOTE: the data rows below were written from the paper as remembered; the PDF could
        # not be re-fetched when this test was written, so check them against the paper.
        rows = {"A": [1, 2, 3, 3, 2, 1, 4, 1, 2, S, S, S],
                "B": [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, S, 3],
                "C": [S, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, S],
                "D": [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, S]}
        r = alpha.alpha_nominal(units_from(rows), detail=True)
        self.assertEqual(round(r["n"]), 40)
        self.assertAlmostEqual(r["alpha"], 0.743, places=3)
        self.assertAlmostEqual(r["d_o"], 0.200, places=3)


class HandDerived(unittest.TestCase):
    def test_two_coders_binary_ten_units(self):
        # Hand derivation (not a published value): 8 agreements (4 a, 4 b) and 2 disagreements.
        # n = 20, n_a = n_b = 10, sum o_ck (c != k) = 4, sum n_c n_k (c != k) = 200,
        # alpha = 1 - (n - 1) * 4 / 200 = 0.62.
        pairs = [("a", "a")] * 4 + [("b", "b")] * 4 + [("a", "b")] * 2
        self.assertAlmostEqual(alpha.alpha_nominal([list(p) for p in pairs]), 0.62, places=9)

    def test_perfect_agreement_is_one(self):
        self.assertAlmostEqual(alpha.alpha_nominal([["x", "x"], ["y", "y"], ["x", "x", "x"]]), 1.0)

    def test_no_variation_is_undefined(self):
        self.assertIsNone(alpha.alpha_nominal([["x", "x"], ["x", "x"]]))

    def test_unpairable_units_are_ignored(self):
        base = [["a", "a"], ["a", "b"], ["b", "b"]]
        self.assertAlmostEqual(alpha.alpha_nominal(base), alpha.alpha_nominal(base + [["a", S], [S, S]]))

    def test_coder_order_does_not_matter(self):
        u = [["a", "b", "a"], ["b", "b", S], ["a", "a", "b"]]
        self.assertAlmostEqual(alpha.alpha_nominal(u), alpha.alpha_nominal([list(reversed(x)) for x in u]))

    def test_systematic_disagreement_is_negative(self):
        self.assertLess(alpha.alpha_nominal([["a", "b"], ["b", "a"], ["a", "b"], ["b", "a"]]), 0)


def record(coder, sha, overall, elements=None, when="2026-11-07T00:00:00Z", secs=60):
    return {"schema": "eo-nihil-obstat-decision/v1", "reviewer": {"name": coder}, "claim_sha256": sha, "overall": overall,
            "decided_utc": when, "active_seconds": secs,
            "elements": [{"element": k, "decision": v} for k, v in (elements or {}).items()]}


class FromDecisionFiles(unittest.TestCase):
    def write(self, recs):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "d.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
            fh.write("\n")
        return p

    def test_report_on_exported_records(self):
        recs = []
        for i, (a, b) in enumerate([("certify", "certify")] * 4 + [("reject", "reject")] * 4 + [("certify", "reject")] * 2):
            recs += [record("Alice", f"s{i}", a), record(" bob ", f"s{i}", b)]
        recs.append(record("Alice", "solo", "certify"))           # one coder only: not pairable
        rep = alpha.report([self.write(recs)])
        self.assertEqual(rep["coders"], ["alice", "bob"])
        self.assertEqual(rep["units_coded"], 11)
        self.assertEqual(rep["units_with_two_or_more_coders"], 10)
        self.assertAlmostEqual(rep["alpha"], 0.62, places=9)
        self.assertEqual(rep["active_seconds_per_claim"]["claims_per_hour_at_median"], 60.0)

    def test_latest_duplicate_wins_and_error_mode(self):
        recs = [record("A", "s", "reject", when="2026-11-07T01:00:00Z"), record("A", "s", "certify", when="2026-11-07T02:00:00Z"),
                record("B", "s", "certify")]
        units, _secs, dropped = alpha.build_units([dict(r, _where="x") for r in recs])
        self.assertEqual(dropped, 1)
        self.assertEqual(units["s"], {"a": "certify", "b": "certify"})
        with self.assertRaises(SystemExit):
            alpha.build_units([dict(r, _where="x") for r in recs], duplicates="error")

    def test_element_level_units(self):
        recs = [record("A", "s", "certify", {"original": "certify", "clause:0": "reject"}),
                record("B", "s", "certify", {"original": "certify", "clause:0": "certify"})]
        units, _s, _d = alpha.build_units([dict(r, _where="x") for r in recs], level="elements")
        self.assertEqual(set(units), {("s", "original"), ("s", "clause:0")})

    def test_bootstrap_is_deterministic(self):
        u = [["a", "a"], ["b", "b"], ["a", "b"], ["b", "b"], ["a", "a"], ["a", "a"]] * 3
        self.assertEqual(alpha.bootstrap_ci(u, 200, 1), alpha.bootstrap_ci(u, 200, 1))

    def test_other_schemas_are_ignored(self):
        p = self.write([{"schema": "something-else", "claim_sha256": "z"}, record("A", "s", "certify")])
        self.assertEqual(len(alpha.read_records([p])), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
