"""Offline tests for Pinakes HTR: synthetic page images, a fake page reader and a fake recognizer (no GPU, no PDFs)."""
import csv
import json
import os
import shutil
import tempfile
import unittest

import numpy as np
from PIL import Image

import htr


def bars_page(n=5, h=1200, w=900, line_h=40, gap=50):
    g = np.full((h, w), 255, dtype=np.uint8)
    y = 120
    for _ in range(n):
        g[y:y + line_h, 100:780] = 30
        y += line_h + gap
    return g


class Segmentation(unittest.TestCase):
    def test_projection_finds_each_line(self):
        boxes = htr.projection_lines(bars_page(5))
        self.assertEqual(len(boxes), 5)
        for x0, y0, x1, y1 in boxes:
            self.assertGreater(x1 - x0, 600)
            self.assertLess(y1 - y0, 70)

    def test_touching_lines_are_cut(self):
        g = bars_page(6)
        g[250:300, 100:780] = 30  # the second and third lines run together into one tall band
        boxes = htr.projection_lines(g)
        self.assertGreaterEqual(len(boxes), 6)
        self.assertTrue(all(b[3] - b[1] < 90 for b in boxes))

    def test_wide_lines_are_split_for_the_model(self):
        g = np.full((100, 3000), 255, dtype=np.uint8)
        g[20:80, 10:1400] = 30
        g[20:80, 1500:2990] = 30
        parts = htr.split_wide(g, (0, 10, 3000, 90), htr.otsu(g))
        self.assertGreater(len(parts), 1)
        self.assertTrue(all((b[2] - b[0]) / (b[3] - b[1]) <= htr.MAX_ASPECT for b in parts))

    def test_word_fragments_on_a_row_are_merged_into_one_line(self):
        frags = [(100, 200, 180, 240), (200, 205, 300, 243), (320, 198, 420, 238),  # one row, three fragments
                 (100, 290, 400, 330),                                              # the next row
                 (500, 262, 510, 270)]                                              # a speck between rows
        rows = htr.merge_rows(frags)
        self.assertEqual(rows, [(100, 198, 420, 243), (100, 290, 400, 330)])

    def test_slanted_fragments_do_not_chain_down_the_page(self):
        stair = [(100 * i, 200 + 25 * i, 100 * i + 90, 240 + 25 * i) for i in range(8)]  # each overlaps the next by 15 px
        rows = htr.merge_rows(stair)
        self.assertTrue(all(r[3] - r[1] <= 64 for r in rows), rows)
        self.assertGreater(len(rows), 2)

    def test_blank_page_has_no_lines(self):
        self.assertEqual(htr.line_boxes(np.full((800, 600), 255, dtype=np.uint8), [])[0], [])


class Tesseract(unittest.TestCase):
    def test_parse_tsv(self):
        head = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
        rows = ["4\t1\t1\t1\t1\t0\t10\t20\t300\t40\t-1\t", "5\t1\t1\t1\t1\t1\t10\t20\t100\t40\t90\tExecutive",
                "5\t1\t1\t1\t1\t2\t120\t20\t100\t40\t70\tOrder", "4\t1\t1\t1\t2\t0\t10\t80\t300\t40\t-1\t",
                "5\t1\t1\t1\t2\t1\t10\t80\t100\t40\t50\treserved"]
        text, conf, boxes = htr.parse_tsv("\n".join([head] + rows))
        self.assertEqual(text, "Executive Order\nreserved")
        self.assertEqual(conf, 70.0)
        self.assertEqual(boxes, [(10, 20, 310, 60), (10, 80, 310, 120)])


class FakeReader:
    def __init__(self):
        self.calls = 0

    def read(self, crops):
        self.calls += len(crops)
        return [("the president hereby orders that the lands be reserved", 0.9)] * len(crops)

    def describe(self):
        return {"model_id": "fake", "gpu": ""}


class Run(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.out = os.path.join(self.root, "out")
        self.work = os.path.join(self.root, "work")
        os.makedirs(os.path.join(self.root, os.path.dirname(htr.PINAKES_ORDERS)))
        os.makedirs(self.work)
        rows = [{"instrument_id": "EO:4", "year": "1865", "file": "PT1-1865-EO-4.pdf", "folder": "ProQuest Pre-1937 Orders",
                 "sha256": "a" * 64, "pages": "1", "text_source": "ocr", "text_quality": "0.3", "common_share": "0.1", "text_usable": "no"},
                {"instrument_id": "EO:5", "year": "1866", "file": "PT1-1866-EO-5.pdf", "folder": "ProQuest Pre-1937 Orders",
                 "sha256": "b" * 64, "pages": "1", "text_source": "layer", "text_quality": "0.9", "common_share": "0.5", "text_usable": "yes"},
                {"instrument_id": "EO:9", "year": "1870", "file": "PT1-1870-EO-9.pdf", "folder": "ProQuest Pre-1937 Orders",
                 "sha256": "c" * 64, "pages": "1", "text_source": "ocr", "text_quality": "0.2", "common_share": "0.1", "text_usable": "no"}]
        with open(os.path.join(self.root, htr.PINAKES_ORDERS), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        self.prepared = []

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def fake_prepare(self, task):
        self.prepared.append(task["instrument_id"])
        d = os.path.join(self.work, task["instrument_id"].replace(":", "_"))
        os.makedirs(d, exist_ok=True)
        page = os.path.join(d, "page-000.png")
        Image.fromarray(bars_page(2)).save(page)
        return {"instrument_id": task["instrument_id"], "pages": [page], "tess_text": "Clans we tn rehlllon apart",
                "tess_conf": 41.0, "segments": [(0, b, "projection") for b in htr.projection_lines(bars_page(2))],
                "segmentation": "projection", "error": ""}

    def test_reads_only_orders_below_the_screen_and_resumes(self):
        reader = FakeReader()
        s = htr.run(self.root, self.out, reader=reader, prepare=self.fake_prepare)
        self.assertEqual(sorted(self.prepared), ["EO:4", "EO:9"])
        self.assertEqual(s["orders"], 2)
        self.assertEqual(s["trocr_passes_screen"], 2)
        self.assertEqual(s["tess300_passes_screen"], 0)
        self.assertEqual(reader.calls, 4)
        self.assertFalse(s["acceptable_as_source_text"])
        self.assertFalse(s["counts_toward_certification"])
        with open(os.path.join(self.out, "HTR.csv"), newline="", encoding="utf-8") as fh:
            rows = {r["instrument_id"]: r for r in csv.DictReader(fh)}
        self.assertEqual(rows["EO:4"]["trocr_text_path"], "texts/EO_4.trocr.txt")
        self.assertTrue(os.path.exists(os.path.join(self.out, "texts", "EO_4.trocr.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "texts", "EO_4.tess300.txt")))
        with open(os.path.join(self.out, "LINES.jsonl"), encoding="utf-8") as fh:
            lines = [json.loads(x) for x in fh]
        self.assertEqual(len(lines), 4)
        prov = json.load(open(os.path.join(self.out, "PROVENANCE.json"), encoding="utf-8"))
        self.assertEqual(prov["status"], "machine_hypothesis")
        self.assertIn("SAMPLE_FOR_PAGE_CHECK", open(os.path.join(self.out, "REPORT.md"), encoding="utf-8").read())
        with open(os.path.join(self.out, "SAMPLE_FOR_PAGE_CHECK.csv"), newline="", encoding="utf-8") as fh:
            self.assertEqual(len(list(csv.DictReader(fh))), 2)

        self.prepared.clear()
        s2 = htr.run(self.root, self.out, reader=FakeReader(), prepare=self.fake_prepare)
        self.assertEqual(self.prepared, [], "orders read with the same method key are not read again")
        self.assertEqual(s2["orders"], 2)
        with open(os.path.join(self.out, "LINES.jsonl"), encoding="utf-8") as fh:
            self.assertEqual(len(fh.readlines()), 4, "lines are carried forward, not duplicated")


class Compare(unittest.TestCase):
    def test_unconfirmed_words_are_marked(self):
        import compare
        marked, s = compare.compare_order({
            "vlm": "By virtue of the authority\nvested in me [illegible] hereby order",
            "trocr": "By virtue of the anthority vested in me I hereby order",
            "tess300": "By virtne of the authority vested in nie I hereby order"})
        self.assertEqual(s["backbone"], "vlm")
        self.assertEqual(s["readings"], "vlm+trocr+tess300")
        self.assertEqual(marked, "By virtue of the authority\nvested in me [illegible] hereby order")
        self.assertEqual(s["unconfirmed_words"], 0)
        self.assertEqual(s["illegible_marks"], 1)
        marked, s = compare.compare_order({"vlm": "The lands are reserved forever", "trocr": "The hands are reversed for ever"})
        self.assertEqual(marked, "The ⟦lands⟧ are ⟦reserved⟧ ⟦forever⟧")
        self.assertEqual(s["confirmed_share"], 0.4)
        self.assertEqual(s["confirmed_by_tess300_share"], "")

    def test_one_reading_is_not_a_comparison(self):
        import compare
        self.assertEqual(compare.compare_order({"vlm": "only one", "trocr": ""}), (None, None))


class FakeVLM:
    def __init__(self, loop_first=False):
        self.loop_first, self.retries = loop_first, 0

    def read_page(self, image, retry=False):
        self.retries += retry
        if self.loop_first and not retry:
            return "Executive Mansion" + " [illegible]" * 40
        return "Executive Mansion [illegible] 1865"


class VLMRun(Run):
    def test_vlm_reads_each_page_and_resumes(self):
        import vlm
        pages = lambda pdf, work: [Image.fromarray(bars_page(2)).save(os.path.join(work, "p-1.png")) or os.path.join(work, "p-1.png")]
        s = vlm.run(self.root, self.out, reader=FakeVLM(), pages_of=pages)
        self.assertEqual((s["orders"], s["read_this_run"], s["errors"]), (2, 2, 0))
        with open(os.path.join(self.out, "VLM.csv"), newline="", encoding="utf-8") as fh:
            rows = {r["instrument_id"]: r for r in csv.DictReader(fh)}
        self.assertEqual(rows["EO:4"]["vlm_illegible_marks"], "1")
        self.assertEqual(vlm.run(self.root, self.out, reader=FakeVLM(), pages_of=pages)["read_this_run"], 0)

    def test_a_looping_page_is_retried(self):
        import vlm
        pages = lambda pdf, work: [Image.fromarray(bars_page(2)).save(os.path.join(work, "p-1.png")) or os.path.join(work, "p-1.png")]
        reader = FakeVLM(loop_first=True)
        s = vlm.run(self.root, self.out, reader=reader, pages_of=pages)
        self.assertEqual((reader.retries, s["degenerate_orders"]), (2, 0))

    def test_loops_are_detected_and_collapsed(self):
        import vlm
        self.assertTrue(vlm.degenerate("By order" + " [illegible]" * 20))
        self.assertTrue(vlm.degenerate("\n".join(["Approved"] * 9 + ["A. Lincoln"])))
        self.assertFalse(vlm.degenerate("the lands of the United States are hereby reserved"))
        self.assertEqual(vlm.collapse("x\nx\nx\ny"), "x [repeated 3 times by the model]\ny")
        self.assertEqual(vlm.collapse("a b b b b b c"), "a b [repeated 5 times by the model] c")


if __name__ == "__main__":
    unittest.main()
