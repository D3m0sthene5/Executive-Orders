"""Offline tests for Shepard (no network, no PDF library): python -I -m unittest -v test_shepard"""
import csv
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import blm  # noqa: E402
import cites as C  # noqa: E402
import shepard  # noqa: E402

FIX = HERE / "fixtures"


def fixture_pages(name):
    return blm.pages_from_text(FIX.joinpath(name).read_text(encoding="utf-8"))


class Dates(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(str(C.parse_date("Feb. 4, 1954")), "1954-02-04")
        self.assertEqual(str(C.parse_date("Sept. 3 2003")), "2003-09-03")
        self.assertEqual(str(C.parse_date("6th day of June, 1906")), "1906-06-06")
        self.assertEqual(str(C.parse_date("November nine, nineteen hundred and seven")), "1907-11-09")
        self.assertIsNone(C.parse_date("February 30, 1920"))


class Relations(unittest.TestCase):
    def classify_at(self, text, needle, prefer="text"):
        s = text.index(needle)
        return C.classify(text, s, s + len(needle), prefer=prefer)

    def test_hereby_after(self):
        t = "Executive Order No. 4810, of February 14, 1928, withdrawing public land, is hereby revoked."
        self.assertEqual(self.classify_at(t, "Executive Order No. 4810")["mechanism"], "revocation")

    def test_adjacent_word_wins(self):
        t = "in lieu of Executive Order No. 1304, dated February 18, 1911, the following lands are hereby restored"
        self.assertEqual(self.classify_at(t, "Executive Order No. 1304")["mechanism"], "replacement")

    def test_as_amended_by_names_an_actor(self):
        t = "withdrawn by Executive Order No. 2900, as amended by Executive Order No. 5414, are hereby restored"
        r = self.classify_at(t, "Executive Order No. 5414")
        self.assertTrue(r["actor_named"])

    def test_partial_and_negation(self):
        t = "Executive Order No. 6910 is hereby revoked in part."
        self.assertTrue(self.classify_at(t, "Executive Order No. 6910")["partial"])
        t = "This order shall not revoke Executive Order No. 6910."
        self.assertTrue(self.classify_at(t, "Executive Order No. 6910")["negated"])

    def test_number_and_date_mentions(self):
        t = "The Executive Order (No. 1237) of August 15, 1910, is rescinded. Executive orders dated November 9, 1907, and January 28, 1908."
        nums = C.eo_number_mentions(t)
        self.assertEqual(nums[0][2], "1237")
        self.assertEqual(str(nums[0][4]), "1910-08-15")
        self.assertEqual([str(d) for _, _, d, _ in C.eo_date_mentions(t)], ["1907-11-09", "1908-01-28"])
        self.assertEqual(C.reserve_mentions("Power-Site Reserve No. 325 and Public Water Reserve No. 155")[1][2:4], ("PWR", 155))


class PloTable(unittest.TestCase):
    def setUp(self):
        self.rows = C.parse_plo_table(fixture_pages("blm_table_695-2250_pages.txt"), 695, 2250)
        self.by = {r["number"]: r for r in self.rows}

    def test_rows_and_citations(self):
        self.assertEqual(sorted(self.by), [711, 936, 945, 1149])
        self.assertEqual(self.by[936]["fr_citation"], "19 FR 769")
        self.assertEqual(self.by[945]["fr_page"], 1583)  # the bracketed (19 FR 2353) is PLO 956's citation
        self.assertEqual(self.by[1149]["fr_citation"], "20 FR 3439")
        self.assertEqual(self.by[711]["date"], "1951-04-10")
        self.assertEqual(self.by[936]["pdf_page"], 1)
        self.assertEqual(self.by[945]["pdf_page"], 2)

    def test_subject_refs(self):
        refs = C.plo_subject_refs(self.by[936]["subject"])
        eos = [r["value"] for r in refs if r["kind"] == "eo_number"]
        self.assertEqual(eos, ["7185", "7212", "7452", "8331"])
        self.assertTrue(all(r["mechanism"] == "revocation" for r in refs if r["kind"] == "eo_number"))
        self.assertTrue(all(r["mechanism"] == "cross_reference" for r in refs if r["kind"] == "plo"))
        refs = C.plo_subject_refs(self.by[945]["subject"])
        eo = [r for r in refs if r["kind"] == "eo_number"][0]
        self.assertEqual((eo["value"], eo["stated_date"]), ("5214", "1929-10-30"))
        plo = [r for r in refs if r["kind"] == "plo"][0]
        self.assertEqual((plo["value"], plo["mechanism"], plo["actor_named"]), (956, "amendment", True))
        refs = C.plo_subject_refs(self.by[1149]["subject"])
        d = [r for r in refs if r["kind"] == "eo_date"][0]
        self.assertEqual((d["value"], d["mechanism"], d["partial"]), ("1926-04-17", "revocation", True))
        self.assertIn("PSR:26", [r["value"] for r in refs if r["kind"] == "reserve"])


class Contents(unittest.TestCase):
    def test_entries(self):
        entries, index = C.contents_entries(FIX.joinpath("fr_contents_1954.txt").read_text(encoding="utf-8"))
        got = {(e["section"], e["number"], e["acting_kind"], tuple(e["acting_numbers"]), e["page"]) for e in entries}
        self.assertIn(("EO", "4778", "PLO", (755,), 9816), got)
        self.assertIn(("EO", "8344", "PLO", (781,), 160), got)
        self.assertIn(("PLO", "151", "PLO", (806,), 1650), got)
        self.assertIn(("PLO", "637", "PLO", (905,), 4360), got)       # OCR-spaced page '4 3 6 0'
        self.assertIn(("PLO", "10", "PLO", (674,), None), got)        # '672 ____' is the next entry, not a page
        self.assertIn(("EO", "9526", "PLO", (674, 675), 6787), got)   # section carried to the next PDF page
        self.assertEqual(index[("PLO", "806")], 1650)
        self.assertEqual(index[("PLO", "672")], 6786)


class Wikisource(unittest.TestCase):
    def test_parts(self):
        body, off, notes = C.wikisource_parts(FIX.joinpath("wikisource_EO_1000.txt").read_text(encoding="utf-8"))
        self.assertTrue(body.lstrip().startswith("It is hereby ordered"))
        self.assertNotIn("Executive Order 1001", body)
        self.assertEqual([(n[0], n[3], n[4]) for n in notes], [("amendment", "EO", "709"), ("cross_reference", "EO", "1284")])


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class EndToEnd(unittest.TestCase):
    """A miniature repository: census, types, the 1989 table, two held texts, one BLM table, one FR contents text."""

    def build(self, root):
        ids = ["EO:1000", "EO:1237", "EO:4204", "EO:4810", "EO:6604", "EO:6679", "EO:709", "EO:7185", "EO:4872",
               "EO:5214", "EO:7212", "EO:7452"]
        write_csv(root / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
                  [{"id": i, "included_in_bibliography": "1", "date_effective": ""} for i in ids])
        dates = {"EO:1237": "1910-08-15", "EO:4204": "1925-04-15", "EO:4810": "1928-02-14", "EO:6679": "1934-04-16",
                 "EO:6604": "1934-02-16", "EO:709": "1907-11-09", "EO:1000": "1908-12-30", "EO:7185": "1935-10-14",
                 "EO:4872": "1928-05-03", "EO:5214": "1929-10-30", "EO:7212": "1935-10-30", "EO:7452": "1936-08-26"}
        write_csv(root / "jobs/x1-class-engine/output/TYPES.csv",
                  [{"instrument_id": i, "class": "land", "type": "land_withdrawal_general", "app_title": "", "wpa_summary": ""}
                   for i in ids])
        write_csv(root / "jobs/ofr-codification-1989/output/DISPOSITION_1989.csv", [
            {"seq": "276", "page": "1036", "printed": "1025", "key": "EO:4872", "census_id": "EO:4872",
             "amendments": "Amendedby EO 7415", "disposition": "Revokedby PLO 4620", "category": "revoked",
             "acting_documents": "PLO:4620", "pairing_confidence": "high"}])
        frag_dir = root / "jobs/pinakes-proquest-ingest/output"
        (frag_dir / "texts").mkdir(parents=True)
        texts = {
            "EO:4204": "The Executive Order (No. 1237) of August 15, 1910, reserving for naval purposes the following "
                       "described area of land. " + "Beginning at a point on the east bank. " * 30 +
                       "is hereby rescinded and the said area restored to its former status.",
            "EO:6679": "Executive Order No. 4810, of February 14, 1928, withdrawing public land, is hereby revoked.",
        }
        with (frag_dir / "FRAGMENTS.jsonl").open("w") as fh:
            for iid, text in texts.items():
                name = iid.replace(":", "_") + ".txt"
                (frag_dir / "texts" / name).write_text(text, encoding="utf-8")
                fh.write(json.dumps({"instrument_id": iid, "kind": "original_representation", "produced_by": "pinakes-proquest-ingest",
                                     "data": {"text_path": "texts/" + name, "sha256": "a" * 64, "url": "https://example.org/" + name,
                                              "signing_date": dates[iid]}}) + "\n")
        app = root / "jobs/app-executive-orders/output"
        (app / "texts").mkdir(parents=True)
        with (app / "FRAGMENTS.jsonl").open("w") as fh:
            for iid in ids:
                if iid not in texts:
                    (app / "texts" / (iid[3:] + ".txt")).write_text("Executive Order " + iid[3:], encoding="utf-8")
                    fh.write(json.dumps({"instrument_id": iid, "produced_by": "app-executive-orders",
                                         "data": {"text_path": "texts/" + iid[3:] + ".txt", "signing_date": dates[iid]}}) + "\n")
        sl = root / "jobs/source-ladder/output"
        (sl / "texts").mkdir(parents=True)
        (sl / "texts" / "c.txt").write_text(
            "=== PDF page 1 of 9 ===\nChapter II (Executive orders):\n6604 (revoked by PLO\n711) _____ 3348\n", encoding="utf-8")
        (sl / "SOURCES.jsonl").write_text(json.dumps({"url": "https://www.govinfo.gov/content/pkg/FR-1951-04-14/pdf/FR-1951-04-14.pdf",
                                                      "sha256": "b" * 64, "text_path": "texts/c.txt"}) + "\n")

    def test_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.build(root)
            out = root / "out"
            out.mkdir()
            table = {"name": "695-2250", "url": "https://www.blm.gov/x_695-2250.pdf", "lo": 695, "hi": 2250,
                     "sha256": "c" * 64, "pages": fixture_pages("blm_table_695-2250_pages.txt")}
            s = shepard.run(str(root), str(out), tables=[table], log=lambda *a: None)
            with (out / "EDGES.csv").open(encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                self.assertEqual(reader.fieldnames, shepard.EDGE_COLUMNS)
                rows = list(reader)
            got = {(r["acting_id"], r["target_id"], r["mechanism"], r["evidence_type"]) for r in rows}
            self.assertIn(("EO:4204", "EO:1237", "rescission", "shepard_text_number"), got)
            self.assertIn(("EO:6679", "EO:4810", "revocation", "shepard_text_number"), got)
            self.assertIn(("PLO:936", "EO:7185", "revocation", "shepard_blm_plo_table"), got)
            self.assertIn(("PLO:945", "EO:5214", "revocation", "shepard_blm_plo_table"), got)
            self.assertIn(("PLO:956", "PLO:945", "amendment", "shepard_blm_plo_table"), got)
            self.assertIn(("PLO:4620", "EO:4872", "revocation", "shepard_ofr1989_table"), got)
            self.assertIn(("EO:7415", "EO:4872", "amendment", "shepard_ofr1989_table"), got)
            self.assertIn(("PLO:711", "EO:6604", "revocation", "shepard_fr_contents"), got)
            plo711 = [r for r in rows if r["acting_id"] == "PLO:711" and r["target_id"] == "EO:6604"]
            self.assertTrue(all(r["date_candidate"] == "1951-04-10" for r in plo711))
            with (out / "PLO_TABLE.csv").open(encoding="utf-8") as fh:
                plo = {r["plo_number"]: r for r in csv.DictReader(fh)}
            self.assertEqual(plo["936"]["eo_ids"], "EO:7185|EO:7212|EO:7452|EO:8331")
            self.assertIn("16 FR 3348", plo["711"]["fr_contents_pages"])
            self.assertTrue(s["every_row_is_a_lead"])


class BlmFetch(unittest.TestCase):
    """The fetch path with an injected transport: robots 404, a listing page, two PDFs (one too large to commit)."""

    def test_fetch_and_carry_forward(self):
        listing = ('<a href="/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_1-694.pdf">1</a>'
                   * 1)
        bodies = {"https://www.blm.gov/robots.txt": (404, b""),
                  blm.LISTING_URL: (200, listing.encode()),
                  "https://www.blm.gov/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_1-694.pdf": (200, b"%PDF-1.4 small"),
                  "https://www.blm.gov/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_695-2250.pdf": (500, b"")}

        def transport(url, headers, timeout):
            status, body = bodies.get(url, (404, b""))
            return status, {"content-length": str(len(body))}, io.BytesIO(body)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            seed = tmp / "seed.json"
            seed.write_text(json.dumps({"listing_url": blm.LISTING_URL, "tables": [
                {"url": u, "lo": lo, "hi": hi} for u, lo, hi in [
                    ("https://www.blm.gov/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_1-694.pdf", 1, 694),
                    ("https://www.blm.gov/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_695-2250.pdf", 695, 2250)]]}))
            prior = tmp / "prior"
            (prior / "texts/blm").mkdir(parents=True)
            (prior / "texts/blm/plo_695-2250.txt").write_text(FIX.joinpath("blm_table_695-2250_pages.txt").read_text())
            (prior / "SOURCES.jsonl").write_text(json.dumps({
                "url": "https://www.blm.gov/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_695-2250.pdf",
                "sha256": "d" * 64, "bytes": 9, "text_path": "texts/blm/plo_695-2250.txt"}) + "\n")
            out = tmp / "out"
            out.mkdir()
            tables, records, stats = blm.fetch_tables(
                str(out), str(tmp / "cache"), str(prior), str(seed), transport=transport, commit_max_bytes=100,
                extract=lambda raw: ["1 June 20, 1942 California; withdrawing land. 7 FR 4866"], log=lambda *a: None)
            by = {t["name"]: t for t in tables}
            self.assertEqual(by["1-694"]["status"], "downloaded")
            self.assertTrue(by["1-694"]["committed"])
            self.assertTrue((out / "blm/plo_1-694.pdf").is_file())
            self.assertEqual(by["695-2250"]["status"], "carried_forward_from_previous_run")
            self.assertEqual(len(C.parse_plo_table(by["695-2250"]["pages"], 695, 2250)), 4)
            self.assertTrue(all(r["instrument_ids"] == [] for r in records))
            self.assertLessEqual(stats["requests"], 6)


if __name__ == "__main__":
    unittest.main()
