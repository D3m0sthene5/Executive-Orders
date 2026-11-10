"""Offline tests for Mabillon held printings: segmenting, the neighbour margin, the error bound, and the real run."""
import collections
import hashlib
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
    def test_source_text_matching_hash(self):
        with tempfile.TemporaryDirectory() as d:
            body = PAGE.encode("utf-8")
            path = Path(d) / "texts/EO_7405.txt"
            path.parent.mkdir()
            path.write_bytes(body)
            data = {"text_path": "texts/EO_7405.txt", "text_sha256": hashlib.sha256(body).hexdigest(),
                    "sha256": hashlib.sha256(b"different raw source bytes").hexdigest()}
            self.assertEqual(H.verified_source_text(d, data), {"text_path": "texts/EO_7405.txt"})

    def test_source_text_mismatched_hash(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "text.txt").write_bytes(b"changed text")
            data = {"text_path": "text.txt", "text_sha256": hashlib.sha256(PAGE.encode("utf-8")).hexdigest()}
            with self.assertRaisesRegex(ValueError, "recorded text_sha256"):
                H.verified_source_text(d, data)

    def test_source_text_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            data = {"text_path": "missing.txt", "text_sha256": hashlib.sha256(b"").hexdigest()}
            with self.assertRaises(FileNotFoundError):
                H.verified_source_text(d, data)

    def test_source_text_outside_output(self):
        with tempfile.TemporaryDirectory() as d:
            for path in ("../outside.txt", str(Path(d).resolve() / "text.txt")):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    H.verified_source_text(d, {"text_path": path, "text_sha256": "0" * 64})

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
            for f in frags:
                # Papebroch hole 1: the file is the passage alone and text_sha256 is the hash of the file as written
                # (until 2026-11-09 it was the hash of the passage under a provenance header, so no file verified).
                body = (Path(d) / f["data"]["text_path"]).read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(), f["data"]["text_sha256"], f["instrument_id"])
                self.assertFalse(body.startswith(b"Instrument: "), f["instrument_id"])
                # nothing loses provenance: what the header said is in the fragment
                dd = f["data"]
                self.assertTrue(dd["url"] and dd["sha256"] and dd["page_or_item"] and dd["match"]["source_kind"])
                self.assertEqual(f["sources"], [{"url": dd["url"], "sha256": dd["sha256"],
                                                 "page_or_item": dd["page_or_item"]}])
            self.assertTrue(all(f["data"]["needs_page_check"] == (f["confidence_note"].find("Every strong") < 0)
                                for f in frags))


if __name__ == "__main__":
    unittest.main()
