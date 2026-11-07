"""Tests for score.py with synthetic references. Run: py -I test_score.py"""
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score as S


REF = "Sec. 11, lots 1 to 4, inclusive, S½NW¼, NE¼SW¼;"


class TestText(unittest.TestCase):
    def test_norm_strict_keeps_glyph_errors(self):
        self.assertEqual(S.norm(" a \n b\t c "), "a b c")
        self.assertNotEqual(S.norm("NE¼"), S.norm("NEy4"))

    def test_norm_lenient_folds_marks_and_space_before_punct(self):
        self.assertEqual(S.norm("it’s “x” ;", "lenient"), "it's \"x\";")
        self.assertEqual(S.norm("39°15′ W", "lenient"), "39°15' W")

    def test_edit_distance_and_cer(self):
        self.assertEqual(S.edit_distance("kitten", "sitting"), 3)
        self.assertEqual(S.cer("abcd", "abcd"), 0)
        self.assertAlmostEqual(S.cer("abcd", "abxd"), 0.25)
        self.assertEqual(S.cer("", ""), 0)

    def test_edit_ops_counts(self):
        d, ins, dele, sub, run = S.edit_ops("abcdef", "abXXXcdef")
        self.assertEqual((d, ins, dele, sub, run), (3, 3, 0, 0, 3))
        d, ins, dele, sub, run = S.edit_ops("abcdef", "abdef")
        self.assertEqual((d, ins, dele, sub, run), (1, 0, 1, 0, 0))

    def test_invention_threshold(self):
        ref = "the lands described below are withdrawn"
        self.assertFalse(S.invents(ref, ref))
        self.assertFalse(S.invents(ref, ref.replace("below", "belov")))          # substitution
        self.assertFalse(S.invents(ref, ref + " ab"))                            # 3 inserted chars
        self.assertTrue(S.invents(ref, ref + " and are hereby restored"))        # fabricated continuation
        self.assertTrue(S.invents(ref, "the lands described below below below are withdrawn"))  # duplicated word
        # a garbled fraction (1 sub + 1 ins) must not count as invention
        self.assertFalse(S.invents("NE¼NE¼", "NEy4NEy4"))

    def test_wilson_interval(self):
        lo, hi = S.wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertTrue(0.2 < hi < 0.35)
        self.assertEqual(S.wilson(0, 0), (0.0, 0.0))


def readings_fixture():
    return {
        # owner passage, GPO garbles the fractions, surya and claude right, tesseract wrong, paddle wrong differently
        "H1": {"gpo-layer": "Sec. 11, lots 1 to 4, inclusive, SyNWi, NEi4SW%;", "tesseract-psm6": "Sec. 11, lots 1 to 4 inclusive SYNWY",
               "tesseract-psm3": "x", "surya": REF, "paddleocr": "Sec. 11, lots 1 to 4, inclusive, S1/2NW1/4, NE1/4SW1/4;",
               "claude": REF},
        "H2": {"gpo-layer": "garbled", "tesseract-psm6": "garbled2", "tesseract-psm3": "x", "surya": REF, "paddleocr": REF,
               "claude": REF},
        "H3": {"gpo-layer": "Sec. 5 NWi", "tesseract-psm6": "bad", "tesseract-psm3": "x", "surya": "Sec. 5, NW¼;",
               "paddleocr": "Sec. 5 NW1/4", "claude": "Sec. 5, NW¼;"},
        "H4": {"gpo-layer": "Sec. 6 SEi", "tesseract-psm6": "bad", "tesseract-psm3": "x", "surya": "Sec. 6, SE¼;",
               "paddleocr": "Sec. 6 SE", "claude": "Sec. 6, SE¼;"},
        # clean agreed passages
        "C1": {"gpo-layer": "This order shall take effect.", "tesseract-psm6": "This order shall take effect.", "tesseract-psm3": "x",
               "surya": "This order  shall take effect.", "paddleocr": "This order shall take effect.", "claude": "This order shall take effect."},
        "C2": {"gpo-layer": "Approved June 5, 1946.", "tesseract-psm6": "Approved June 5, 1946.", "tesseract-psm3": "x",
               "surya": "Approved June 5, 1946.", "paddleocr": "Approved June 5, 1946.",
               "claude": "Approved June 5, 1946. It shall be unlawful to keep any alley dwelling"},  # invents
        "C3": {"gpo-layer": "Washington, D. C.", "tesseract-psm6": "Washington, D. C.", "tesseract-psm3": "x",
               "surya": "Washington, D. C.", "paddleocr": "Washington, D. C.", "claude": "Washington, D. C."},
        # clean where GPO and surya disagree -> left out
        "C4": {"gpo-layer": "Thc President", "tesseract-psm6": "The President", "tesseract-psm3": "x", "surya": "The President",
               "paddleocr": "The President", "claude": "The President"},
    }


def passages_fixture():
    cat = {"H1": "hard", "H2": "hard", "H3": "hard", "H4": "hard", "C1": "clean", "C2": "clean", "C3": "clean", "C4": "clean"}
    return {p: {"id": p, "category": c} for p, c in cat.items()}


class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.rd, self.ps = readings_fixture(), passages_fixture()
        self.owner = {"H1", "H2", "H3", "H4"}

    def test_agreed_builder_uses_exact_whitespace_folded_agreement(self):
        agreed, dis = S.build_agreed(self.rd, self.ps, self.owner)
        self.assertEqual(sorted(agreed), ["C1", "C2", "C3"])
        self.assertEqual(dis, ["C4"])

    def test_agreed_builder_never_includes_owner_passages(self):
        agreed, _ = S.build_agreed(self.rd, self.ps, self.owner)
        self.assertFalse(self.owner & set(agreed))

    def test_single_engine_scores_on_owner_set(self):
        refs = {"H1": REF, "H2": REF, "H3": "Sec. 5, NW¼;", "H4": "Sec. 6, SE¼;"}
        sc = S.score_set(sorted(refs), refs, self.rd, S.RULES)
        self.assertEqual(sc["gpo-layer"]["exact"], 0)
        self.assertEqual(sc["surya"]["exact"], 4)
        self.assertEqual(sc["claude"]["exact"], 4)
        self.assertEqual(sc["paddleocr"]["exact"], 1)
        self.assertEqual(sc["tesseract-psm6"]["exact"], 0)
        self.assertEqual(sc["surya"]["cer_mean"], 0)
        self.assertGreater(sc["gpo-layer"]["cer_mean"], 0.2)

    def test_majority_exact_abstains_without_three_identical(self):
        self.assertIsNone(S.rule_output("majority-exact", self.rd["H1"]))
        self.assertEqual(S.rule_output("majority-exact", self.rd["C3"]), "Washington, D. C.")

    def test_medoid_picks_central_reading(self):
        self.assertEqual(S.norm(S.rule_output("medoid", self.rd["H2"])), S.norm(REF))

    def test_claude_judge_cannot_invent_text_no_engine_produced(self):
        out = S.rule_output("claude-judge", self.rd["C2"])
        self.assertEqual(out, "Approved June 5, 1946.")
        self.assertIn(out, [self.rd["C2"][e] for e in S.VOTERS])

    def test_agree3_else_claude(self):
        self.assertEqual(S.rule_output("agree3-else-claude", self.rd["C3"]), "Washington, D. C.")
        self.assertEqual(S.rule_output("agree3-else-claude", self.rd["H1"]), REF)  # no 3-way agreement -> Claude

    def test_adoption_test(self):
        refs_o = {"H1": REF, "H2": REF, "H3": "Sec. 5, NW¼;", "H4": "Sec. 6, SE¼;"}
        agreed, _ = S.build_agreed(self.rd, self.ps, self.owner)
        owner_sc = S.score_set(sorted(refs_o), refs_o, self.rd, S.RULES)
        clean_ids = [p for p in sorted(agreed) if self.ps[p]["category"] == "clean"]
        clean_sc = S.score_set(clean_ids, agreed, self.rd, S.RULES)
        ad = S.adoption(owner_sc, clean_sc, S.RULES)
        # surya halves GPO's failures (0 vs 4) and cannot invent on agreed passages where it equals the reference
        self.assertTrue(ad["surya"]["adopt"])
        # claude halves failures too, but invents on C2 -> not adopted
        self.assertTrue(ad["claude"]["halves_gpo_failures"])
        self.assertEqual(ad["claude"]["clean_invented"], 1)
        self.assertFalse(ad["claude"]["adopt"])
        # claude-judge picks an engine reading, so it invents nothing
        self.assertTrue(ad["claude-judge"]["invents_nothing_on_clean"])
        # paddleocr fails 3 of 4 owner passages: 3 > 4/2, not halved
        self.assertFalse(ad["paddleocr"]["halves_gpo_failures"])
        self.assertFalse(ad["paddleocr"]["adopt"])

    def test_adoption_not_testable_when_gpo_barely_fails(self):
        owner_sc = {"gpo-layer": {"failures": 1}, "surya": {"failures": 0}}
        clean_sc = {"surya": {"n": 3, "invents": 0}}
        ad = S.adoption(owner_sc, clean_sc, ["gpo-layer", "surya"])
        self.assertFalse(ad["surya"]["testable"])
        self.assertFalse(ad["surya"]["adopt"])

    def test_end_to_end_cli(self):
        with tempfile.TemporaryDirectory() as d:
            rp = os.path.join(d, "r.jsonl")
            with open(rp, "w", encoding="utf-8") as fh:
                for pid, eng in self.rd.items():
                    for e, t in eng.items():
                        fh.write(json.dumps({"passage_id": pid, "engine": e, "output_text": t}) + "\n")
            pp = os.path.join(d, "p.csv")
            with open(pp, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["id", "category"])
                w.writeheader()
                for p in self.ps.values():
                    w.writerow(p)
            op = os.path.join(d, "o.json")
            with open(op, "w", encoding="utf-8") as fh:
                json.dump({"ids": sorted(self.owner)}, fh)
            orf = os.path.join(d, "or.csv")
            with open(orf, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["id", "reference"])
                w.writerow(["H1", REF])
                w.writerow(["H2", REF])
                w.writerow(["H3", "Sec. 5, NW¼;"])
                w.writerow(["H4", "Sec. 6, SE¼;"])
            sp = os.path.join(d, "s.csv")
            with open(sp, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["id", "ok", "corrected"])
                w.writerow(["C3", "no", "Washington, D.C."])
            out = os.path.join(d, "out.json")
            rep = S.main(["--readings", rp, "--passages", pp, "--owner-set", op, "--owner-refs", orf, "--spotcheck", sp,
                          "--out", out])
            self.assertEqual(rep["agreed"]["n_agreed"], 3)
            self.assertEqual(rep["agreed"]["n_disagreed_left_out"], 1)
            self.assertEqual(rep["spotcheck"]["agreed_texts_found_wrong"], ["C3"])
            # the human correction replaces the agreed text: GPO is now wrong on C3 under strict scoring
            self.assertEqual(rep["strict"]["scores"]["agreed_clean"]["gpo-layer"]["exact"], 2)
            self.assertIn("PREVIEW_pairwise_cer_NO_REFERENCES", rep)
            self.assertTrue(os.path.exists(out))


if __name__ == "__main__":
    unittest.main(verbosity=1)
