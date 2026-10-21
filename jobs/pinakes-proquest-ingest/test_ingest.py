"""Offline tests for Pinakes with synthetic PDFs and a fake OCR function."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import eo_pdf  # noqa: E402
import ingest  # noqa: E402

MINIMAL_PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
               b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\nxref\n0 4\n0000000000 65535 f \n"
               b"0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\n"
               b"startxref\n160\n%%EOF\n")


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


class Ingest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pinakes-")
        self.out = os.path.join(self.root, "_out")
        write_csv(os.path.join(self.root, ident.UNIVERSE), [
            {"id": "EO:4", "bibliographic_class": "validated_historical_index", "included_in_bibliography": "1", "date_effective": "1865", "year_group": "1862–1906"},
            {"id": "EO:125A", "bibliographic_class": "validated_numbered", "included_in_bibliography": "1", "date_effective": "1900", "year_group": "1862–1906"},
            {"id": "EO:3016E", "bibliographic_class": "validated_numbered", "included_in_bibliography": "1", "date_effective": "1918", "year_group": "1907–1936"}])
        os.makedirs(os.path.join(self.root, ident.PROQUEST_DIR, "_resume"))
        rows = [{"id": "EO:4", "n": "4", "y": 1865, "rec": "https://congressional.proquest.com/r4"},
                {"id": "EO:125A", "n": "125A", "y": 1900, "rec": "https://congressional.proquest.com/r125a"},
                {"id": "EO:9999", "n": "9999", "y": 1936, "rec": "https://congressional.proquest.com/r9999"}]
        with open(os.path.join(self.root, ident.PROQUEST_LINKS), "w", encoding="utf-8") as fh:
            fh.write("<html><script>const ROWS=" + json.dumps(rows) + ";</script></html>")
        up = os.path.join(self.root, "ProQuest Pre-1937 Orders")
        os.makedirs(up)
        for name, body in (("PT1-1865-EO-4.pdf", MINIMAL_PDF), ("PT1-1865-EO-4 (1).pdf", MINIMAL_PDF),
                           ("1900-EO-125-A.pdf", MINIMAL_PDF + b"\n%a"), ("1918-EO-3016-E_From_1_to_2.pdf", MINIMAL_PDF + b"\n%b"),
                           ("1930-EO-5300.pdf", MINIMAL_PDF + b"\n%c"), ("LRS-10-21-Cold-Calls-Plain.pdf", MINIMAL_PDF + b"\n%d"),
                           ("1901-EO-130.pdf", b"<html>Access is denied</html>")):
            with open(os.path.join(up, name), "wb") as fh:
                fh.write(body)
        self.ocr_calls = []

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def fake_ocr(self, path):
        self.ocr_calls.append(os.path.basename(path))
        if "5300" in path:
            return "", 0, "ocr failed"
        return "By virtue of the authority vested in me it is hereby ordered that the lands be reserved for public use.", 1, ""

    def test_inventory_orders_texts_and_reconciliation(self):
        s = ingest.run(self.root, self.out, ocr_pages_budget=100, ocr=self.fake_ocr)
        inv = {r["file"]: r for r in ident.read_csv(os.path.join(self.out, "INVENTORY.csv"))}
        self.assertEqual(inv["PT1-1865-EO-4 (1).pdf"]["duplicate_of"], "ProQuest Pre-1937 Orders/PT1-1865-EO-4.pdf")
        self.assertEqual(inv["1900-EO-125-A.pdf"]["instrument_id"], "EO:125A")
        self.assertEqual(inv["1918-EO-3016-E_From_1_to_2.pdf"]["page_range"], "1-2")
        self.assertEqual(inv["LRS-10-21-Cold-Calls-Plain.pdf"]["name_parsed"], "no")
        self.assertEqual(inv["1901-EO-130.pdf"]["pdf_signature"], "no")
        orders = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(self.out, "ORDERS.csv"))}
        self.assertEqual(sorted(orders), ["EO:125A", "EO:3016E", "EO:4", "EO:5300"])
        self.assertEqual(orders["EO:4"]["file"], "PT1-1865-EO-4.pdf")
        self.assertEqual(orders["EO:4"]["copies"], "2")
        self.assertEqual(orders["EO:4"]["text_source"], "ocr")
        self.assertTrue(os.path.exists(os.path.join(self.out, orders["EO:4"]["text_path"])))
        self.assertEqual(orders["EO:5300"]["text_source"], "none")
        self.assertEqual(orders["EO:5300"]["in_census"], "no")
        self.assertEqual(orders["EO:5300"]["ocr_error"], "ocr failed")
        recon = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(self.out, "SUPPLIED_LINKS_RECONCILED.csv"))}
        self.assertEqual(recon["EO:9999"]["pdf_in_repository"], "no")
        self.assertEqual([r["instrument_id"] for r in ident.read_csv(os.path.join(self.out, "MISSING_FROM_UPLOAD.csv"))], ["EO:9999"])
        stray = {r["file"] for r in ident.read_csv(os.path.join(self.out, "STRAY_FILES.csv"))}
        self.assertEqual(stray, {"LRS-10-21-Cold-Calls-Plain.pdf", "1901-EO-130.pdf"})
        self.assertEqual(s["supplied_links"]["pdfs_for_orders_not_on_list"], ["EO:3016E", "EO:5300"])
        frags = ident.read_jsonl(os.path.join(self.out, "FRAGMENTS.jsonl"))
        self.assertEqual(len(frags), 4)
        for f in frags:
            self.assertIs(f["acceptable_as_original"], False)
            self.assertIs(f["data"]["needs_page_check"], True)
            self.assertEqual(f["produced_by"], "pinakes-proquest-ingest")

    def test_ocr_budget_defers_and_prior_texts_are_carried_forward(self):
        s = ingest.run(self.root, self.out, ocr_pages_budget=1, ocr=self.fake_ocr)
        self.assertEqual(len(self.ocr_calls), 1, "one page of budget: one OCR")
        self.assertEqual(s["texts"]["still_without_text"], 3)
        orders = {r["instrument_id"]: r for r in ident.read_csv(os.path.join(self.out, "ORDERS.csv"))}
        self.assertIn("deferred", orders["EO:3016E"]["ocr_error"])
        # a committed prior output with a text for the same bytes is reused without OCR
        prior_dir = os.path.join(self.root, "jobs", "pinakes-proquest-ingest", "output")
        shutil.copytree(self.out, prior_dir)
        self.ocr_calls.clear()
        import prior_output
        real = prior_output.PriorOutput.from_git_head
        prior_output.PriorOutput.from_git_head = classmethod(lambda cls, repo, rel: real.__func__(cls, None, rel) if False else prior_output.PriorOutput.from_folder(prior_dir))
        try:
            s2 = ingest.run(self.root, self.out, ocr_pages_budget=100, ocr=self.fake_ocr)
        finally:
            prior_output.PriorOutput.from_git_head = real
        self.assertEqual(s2["texts"]["carried_from_prior_run"], 1)
        self.assertNotIn("PT1-1865-EO-4.pdf", self.ocr_calls)
        self.assertEqual(s2["texts"]["still_without_text"], 1, "only the order whose OCR failed")

    def test_text_quality_flags_handwriting(self):
        self.assertLess(eo_pdf.text_quality("/ (. / 7-,t1- * Ie '(cW(J 7UJ"), 0.2)
        self.assertTrue(eo_pdf.usable(500, 0.8))
        self.assertFalse(eo_pdf.usable(20, 0.9))
        garbage = "Clans we tn rehlllon apart Me Kolb Meakle anib hf be Dh EERO Cs Po fet bh fat ofl ee ee ee"
        prose = "it is hereby ordered that the lands described above be reserved for the use of the Department of War"
        self.assertLess(eo_pdf.common_share(garbage), 0.4)
        self.assertGreater(eo_pdf.common_share(prose), 0.5)
        self.assertFalse(eo_pdf.usable(500, 0.8, eo_pdf.common_share(garbage)))
        self.assertTrue(eo_pdf.usable(500, 0.8, eo_pdf.common_share(prose)))


if __name__ == "__main__":
    unittest.main()
