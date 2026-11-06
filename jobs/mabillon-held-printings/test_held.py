"""Offline tests for Mabillon held printings: segmenting, the neighbour margin, the error bound, and the real run."""
import collections
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import held as H  # noqa: E402

PAGE = """Executive Order
AMENDMENT OF THE CIVIL SERVICE RULES FOR THE WAR DEPARTMENT IN PUERTO RICO
By virtue of the authority vested in me the rules are amended to permit employment of laborers at San Juan.
The White House, July 6, 1936.
[No. 7405]
Executive Order
POWER SITE RESERVE NO. 116 COLORADO RIVER MODIFIED FOR THE DENVER AND SALT LAKE WESTERN RAILROAD
It is ordered that power site reserve no. 116 be modified to enable approval of the railroad right of way.
The White House, July 6, 1936.
[No. 7406]
"""


class HeldTests(unittest.TestCase):
    def test_own_segment_cuts_neighbours(self):
        seg, kind = H.own_segment(PAGE, "7406")
        self.assertEqual(kind, "closing_number_tag")
        self.assertIn("POWER SITE", seg)
        self.assertNotIn("San Juan", seg)
        seg, kind = H.own_segment(PAGE, "7405")
        self.assertIn("San Juan", seg)
        self.assertNotIn("POWER SITE", seg)

    def test_upper_bound(self):
        self.assertAlmostEqual(H.wilson_upper(0, 4382), 0.0007, places=4)
        self.assertIsNone(H.wilson_upper(0, 0))
        self.assertGreater(H.wilson_upper(1, 100), 0.01)

    def test_margin_rejects_a_near_twin(self):
        a = "code of fair competition for the widget industry approved with labor provisions for widget makers in ohio"
        b = "code of fair competition for the widget industry approved with labor provisions for widget makers in iowa"
        refs = {"EO:6221C": a, "EO:6221D": b}
        df = collections.Counter()
        n = 2
        comp = H.Competitors(refs, df, n)
        rival, who = comp.best(a, "6221", "EO:6221C")
        self.assertEqual(who, "EO:6221D")
        self.assertGreater(rival, 0.6)  # the twin scores high on its sibling's text: the margin is what rejects it

    def test_real_run_controls(self):
        """On the committed data the planted controls pass and no false pair is accepted."""
        if not (H.REPO / H.HATHI / "FRAGMENTS.jsonl").is_file():
            self.skipTest("hathi-gpo-orders output not present")
        with tempfile.TemporaryDirectory() as d:
            s = H.main(out=Path(d))
            self.assertTrue(s["controls"]["passed"])
            self.assertEqual(s["controls"]["negatives_accepted"], 0)
            frags = [json.loads(x) for x in (Path(d) / "FRAGMENTS.jsonl").read_text().splitlines()]
            self.assertTrue(all(f["acceptable_as_original"] is False for f in frags))
            self.assertTrue(all(f["data"]["needs_page_check"] == (f["confidence_note"].find("Every strong") < 0)
                                for f in frags))


if __name__ == "__main__":
    unittest.main()
