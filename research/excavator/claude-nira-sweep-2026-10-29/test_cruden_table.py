"""Conservative, opt-in table leads against synthetic and held text."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cruden_table_target", HERE / "cruden.py")
cruden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cruden)


INTRO = ("By the authority vested in me, it is hereby ordered that the following "
         "Executive Orders, and any amendments thereto, are revoked:\n\n")


class TableTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="cruden-table-")
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.folder = self.repo / "jobs/held/output/texts"
        self.folder.mkdir(parents=True)
        old_repo = cruden.REPO
        cruden.REPO = self.repo
        self.addCleanup(setattr, cruden, "REPO", old_repo)
        env = patch.dict(os.environ, {"CRUDEN_CACHE_DIR": str(self.repo / "cache")})
        env.start()
        self.addCleanup(env.stop)

    def run_query(self, *queries):
        with contextlib.redirect_stdout(io.StringIO()):
            return cruden.table_number_search(queries)

    def test_bare_cells_repeat_heading_and_spans(self):
        source = self.folder / "EO_12553.txt"
        source.write_text(INTRO + "No. Subject\n\n9949 Amending provisions for transfer of personnel.\n\n"
                          "No. Subject.\n\n6444-A Establishing another commission.\n\n"
                          "RONALD REAGAN\n9949 Unrelated trailing number.\n", encoding="utf-8")
        result = self.run_query("EO:9949", "EO:6444A", "EO:6444", "EO:99490")
        for q in ("EO:9949", "EO:6444A"):
            self.assertEqual(result["queries"][q]["matches"], 1)
            hit = result["queries"][q]["hits"][0]
            text = source.read_text()
            for field, start, end in (("match", "char_start", "char_end"),
                                      ("row", "row_char_start", "row_char_end"),
                                      ("subject", "subject_char_start", "subject_char_end"),
                                      ("header", "header_char_start", "header_char_end"),
                                      ("introduction", "introduction_char_start", "introduction_char_end")):
                self.assertEqual(hit[field], text[hit[start]:hit[end]])
            self.assertEqual(hit["pdf_page"], None)
            self.assertEqual(hit["raw_sha256"], cruden.sha(source))
        self.assertEqual(result["queries"]["EO:6444"]["matches"], 0)
        self.assertEqual(result["queries"]["EO:99490"]["matches"], 0)

    def test_refuses_prose_columns_neighbor_and_missing_intro(self):
        source = self.folder / "lookalikes.txt"
        source.write_text("No. Subject\n9949 Amending an order.\n" + INTRO +
                          "No. Subject\n99490 Amending an order.\n"
                          "10949 Amending Executive Order No. 9949.\n"
                          "9949\nAmending an order in a neighboring column.\n"
                          "9949 2020\n"
                          "A 9949 Amending an order.\n"
                          "9949-A Amending a different order.\n", encoding="utf-8")
        self.assertEqual(self.run_query("EO:9949")["queries"]["EO:9949"]["matches"], 0)
        source.write_text("No. Subject\n9949 Amending an order.\n", encoding="utf-8")
        self.assertEqual(self.run_query("EO:9949")["queries"]["EO:9949"]["matches"], 0)

    def test_unrelated_heading_does_not_suppress_later_introduced_table(self):
        source = self.folder / "two.txt"
        source.write_text("No. Subject\n9949 Unrelated first table.\n" + INTRO +
                          "No. Subject\n9949 Actual revocation table row.\n", encoding="utf-8")
        hit = self.run_query("EO:9949")["queries"]["EO:9949"]
        self.assertEqual(hit["matches"], 1)
        self.assertIn("Actual", hit["hits"][0]["subject"])

    def test_boundaries_expire_context_across_later_headers_and_rows(self):
        source = self.folder / "boundary.txt"
        for boundary in ("RONALD REAGAN", "The White House,", "THE W HITE HOUSE,",
                         "[Filed with the Office of the Federal Register]",
                         "[FR Doc. 86-4455 Filed]", "Billing code 3195-01-M",
                         "Editorial note: Following material is unrelated.",
                         "Executive Order 12554 of February 28, 1986",
                         "Proclamation 1234 of March 1, 1986"):
            with self.subTest(boundary=boundary):
                source.write_text(INTRO + "No. Subject\n1000 Actual table row.\n" +
                                  boundary + "\n9949 Unrelated trailing row.\n" +
                                  "No. Subject\n9949 Unrelated later table.\n", encoding="utf-8")
                self.assertEqual(self.run_query("EO:9949")["queries"]["EO:9949"]["matches"], 0)
        source.write_text(INTRO + "No. Subject\n1000 First table row.\nRONALD REAGAN\n" +
                          INTRO + "No. Subject\n9949 Newly introduced table.\n", encoding="utf-8")
        self.assertEqual(self.run_query("EO:9949")["queries"]["EO:9949"]["matches"], 1)

    def test_exact_attached_suffix_counts_and_limit(self):
        (self.folder / "repeat.txt").write_text(INTRO + "No. Subject\n" +
            "9949A Amending a different order.\n" +
            "9949-A Amending a different order.\n" +
            "99490 Amending a neighboring order.\n" +
            "9949 Amending the queried order.\n" * 5, encoding="utf-8")
        result = self.run_query("EO:9949", "EO:9949A", "EO:9949")
        bare = result["queries"]["EO:9949"]
        self.assertEqual((bare["matches"], bare["matching_files"], len(bare["hits"]), bare["truncated"]), (5, 1, 3, True))
        self.assertEqual(result["queries"]["EO:9949A"]["matches"], 2)
        for query in ("9949", "EO:9949a", "EO:9949\n", "EO:9949-A", "EO:", "EO:9949 extra"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                self.run_query(query)
        with self.assertRaises(ValueError):
            self.run_query()

    def test_mutations_refuse_before_result_publication(self):
        candidate = self.folder / "table.txt"
        candidate.write_text(INTRO + "No. Subject\n9949 Amending an order.\n", encoding="utf-8")
        unrelated = self.folder / "other.txt"
        unrelated.write_text("No relevant digits.", encoding="utf-8")
        output = self.repo / "result.json"
        output.write_text("previous result", encoding="utf-8")
        original_rows = cruden.table_rows
        def mutated_rows(text):
            yield from original_rows(text)
            unrelated.write_text("Now contains 9949.", encoding="utf-8")
        with patch.object(cruden, "table_rows", mutated_rows), self.assertRaises(cruden.SnapshotChanged):
            cruden.table_number_search(["EO:9949"], output)
        self.assertEqual(output.read_text(), "previous result")
        def inventory_rows(text):
            yield from original_rows(text)
            (self.folder / "new.txt").write_text("Added source.", encoding="utf-8")
        with patch.object(cruden, "table_rows", inventory_rows), self.assertRaises(cruden.SnapshotChanged):
            cruden.table_number_search(["EO:9949"], output)
        self.assertEqual(output.read_text(), "previous result")
        original_read = cruden.Snapshot.read_source
        def candidate_mutation(snapshot, record):
            candidate.write_text("Changed source.", encoding="utf-8")
            return original_read(snapshot, record)
        with patch.object(cruden.Snapshot, "read_source", candidate_mutation), self.assertRaises(cruden.SnapshotChanged):
            cruden.table_number_search(["EO:9949"], output)
        self.assertEqual(output.read_text(), "previous result")

    def test_write_emits_bound_result_and_small_summary(self):
        (self.folder / "table.txt").write_text(INTRO + "No. Subject\n9949 Amending an order.\n", encoding="utf-8")
        output = self.repo / "result.json"
        summary = io.StringIO()
        with contextlib.redirect_stdout(summary):
            result = cruden.table_number_search(["EO:9949"], output)
        self.assertEqual(json.loads(output.read_text()), result)
        receipt = json.loads(summary.getvalue())
        self.assertEqual(receipt["sha256"], cruden.sha(output))
        self.assertEqual(receipt["queries"]["EO:9949"]["returned_hits"], 1)
        self.assertEqual(receipt["coverage"]["discovered_count"], 1)

    def test_subject_digits_are_not_page_furniture_and_invalid_page_refused(self):
        text = "=== PDF page 10 of 20 ===\nNo. Subject\n9949 Transfers in 7238 are mentioned.\n"
        self.assertEqual(cruden.table_page(text, len(text))["printed_page"], None)
        self.assertEqual(cruden.table_page(text.replace("10 of 20", "21 of 20"), len(text))["pdf_page"], None)
        self.assertEqual(cruden.table_page(text.replace("10 of 20", "0 of 20"), len(text))["pdf_page"], None)

    def test_pdf_page_only_when_marker_is_held(self):
        source = self.folder / "fr.txt"
        source.write_text(INTRO + "=== PDF page 10 of 200 ===\n7238 Federal Register\n"
                          "No. Subject\n9949 Amending an order.\n", encoding="utf-8")
        hit = self.run_query("EO:9949")["queries"]["EO:9949"]["hits"][0]
        self.assertEqual((hit["pdf_page"], hit["printed_page"]), (10, "7238"))

    def test_held_eo_12553_app_table_when_available(self):
        held = HERE.parents[2] / "jobs/app-executive-orders/output/texts/executive-order-12553-revocation-various-executive-orders.txt"
        if not held.is_file():
            self.skipTest("held APP text not checked out")
        text = held.read_text(encoding="utf-8")
        rows = [row for row in cruden.table_rows(text) if row[:2] == ("9949", "")]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(text[row[2]:row[3]], "9949")
        self.assertIn("transfer of personnel", text[row[6]:row[7]])


if __name__ == "__main__":
    unittest.main()
