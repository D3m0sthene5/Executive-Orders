"""Offline tests: a tiny made-up repo, read back through claim-kit's real loader."""

import csv
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REAL_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REAL_ROOT / "jobs" / "claim-kit"))
import convert  # noqa: E402
import inputs  # noqa: E402  (claim-kit loader)

PAGE = "a" * 64


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.repo = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.app = self.repo / convert.SOURCE_OUT
        (self.app / "texts").mkdir(parents=True)
        census = self.repo / convert.UNIVERSE
        census.parent.mkdir(parents=True)
        with open(census, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["id", "included_in_bibliography"])
            w.writeheader()
            w.writerows({"id": f"EO:{n}", "included_in_bibliography": "1"} for n in (1, 2, 3, 4))
        self.out = self.repo / "jobs" / convert.JOB / "output"

    def text(self, slug, body):
        (self.app / "texts" / f"{slug}.txt").write_text(body, encoding="utf-8", newline="")
        return f"texts/{slug}.txt", sha(body)

    def frag(self, iid, tp, tsha, **over):
        data = {"acceptable_as_original": False, "grade": "mirror_transcription", "sha256": PAGE,
                "representation_type": "secondary_compilation_transcription", "text_path": tp, "text_sha256": tsha,
                "url": f"https://www.presidency.ucsb.edu/documents/executive-order-{iid[3:]}-x",
                "archival_id": f"app:node/{iid[3:]}", "page_or_item": f"Executive Order {iid[3:]}; capture"}
        rec = {"instrument_id": iid, "kind": "original_representation", "produced_by": "app-executive-orders",
               "grade": "mirror_transcription", "representation_type": "secondary_compilation_transcription",
               "acceptable_as_original": False, "data": data,
               "sources": [{k: data[k] for k in ("url", "sha256", "page_or_item", "archival_id")}]}
        rec.update(over)
        return rec

    def source(self, iid, tp, tsha, captured="", **over):
        rec = {"instrument_ids": [iid], "url": f"https://www.presidency.ucsb.edu/documents/executive-order-{iid[3:]}-x",
               "sha256": PAGE, "text_path": tp, "text_sha256": tsha, "grade": "mirror_transcription",
               "representation_type": "secondary_compilation_transcription", "acceptable_as_original": False,
               "source_id": f"s-{iid}-{captured}", "captured_utc": captured, "page_or_item": "p"}
        rec.update(over)
        return rec

    def jsonl(self, name, rows):
        with open(self.app / name, "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(r) + "\n" for r in rows)

    def test_archive_fragments_become_visible_to_claim_kit_as_leads_only(self):
        tp1, s1 = self.text("eo-1", "Body one.")
        tp2, s2 = self.text("eo-2", "Body two.")
        self.jsonl("MIRROR_FRAGMENTS.jsonl", [self.frag("EO:1", tp1, s1), self.frag("EO:2", tp2, s2)])
        before = inputs.load_corpus(self.repo)["texts"]
        self.assertEqual(before, [])  # MIRROR_ name: claim-kit never saw these
        s = convert.convert(self.repo, self.out)
        self.assertEqual(s["counts"]["fragments_written"], 2)
        corpus = inputs.load_corpus(self.repo)
        rows = corpus["texts"]
        self.assertEqual({r["instrument_id"] for r in rows}, {"EO:1", "EO:2"})
        self.assertTrue(all(r["acceptable_as_original"] is False for r in rows))
        self.assertTrue(all(r["grade"] == "mirror_transcription" for r in rows))
        self.assertEqual({r["text_path"] for r in rows},
                         {"jobs/app-executive-orders/output/texts/eo-1.txt", "jobs/app-executive-orders/output/texts/eo-2.txt"})
        self.assertEqual([w for w in corpus["warnings"] if "app-" in w], [])

    def test_records_claiming_to_be_originals_or_with_wrong_text_are_refused(self):
        tp1, s1 = self.text("eo-1", "Body one.")
        tp3, _ = self.text("eo-3", "Body three.")
        rows = [self.frag("EO:1", tp1, s1, acceptable_as_original=True),
                self.frag("EO:3", tp3, "b" * 64),            # file holds another capture's text
                self.frag("EO:4", "texts/missing.txt", "c" * 64),
                self.frag("EO:2", "../../../etc/passwd", "d" * 64)]
        rows[0]["data"]["acceptable_as_original"] = True
        self.jsonl("MIRROR_FRAGMENTS.jsonl", rows)
        s = convert.convert(self.repo, self.out)
        self.assertEqual(s["counts"]["fragments_written"], 0)
        self.assertEqual(s["problems_by_code"], {"record_not_marked_lead_only": 1, "text_file_holds_another_capture": 1,
                                                 "text_file_missing": 1, "unsafe_or_missing_text_path": 1})

    def test_one_source_record_per_order_live_first_then_newest_capture(self):
        tp1, s1 = self.text("eo-1", "Body one.")
        tp2, s2 = self.text("eo-2", "Body two.")
        self.jsonl("SOURCES.jsonl", [self.source("EO:1", tp1, s1, source_id="live-1")])
        self.jsonl("MIRROR_SOURCES.jsonl", [
            self.source("EO:1", tp1, s1, "2025-01-01T00:00:00Z", source_id="old-1"),
            self.source("EO:2", tp2, s2, "2024-01-01T00:00:00Z", source_id="old-2"),
            self.source("EO:2", tp2, s2, "2025-06-01T00:00:00Z", source_id="new-2"),
            self.source("EO:3", tp2, s2, instrument_ids=["EO:3", "EO:4"]),
        ])
        s = convert.convert(self.repo, self.out)
        written = [json.loads(l) for l in open(self.out / "SOURCES.jsonl", encoding="utf-8")]
        self.assertEqual([(r["instrument_ids"][0], r["source_id"]) for r in written],
                         [("EO:1", "live-1"), ("EO:2", "new-2")])
        self.assertEqual(s["problems_by_code"], {"not_exactly_one_order": 1})
        # The relative text path resolves from this job's output folder (later-events reads out / text_path).
        self.assertTrue(all((self.out / r["text_path"]).resolve().is_file() for r in written))
        # claim-kit reads SOURCES.jsonl too: the same representation is one text row, never an original.
        rows = inputs.load_corpus(self.repo)["texts"]
        self.assertEqual(sorted(r["instrument_id"] for r in rows), ["EO:1", "EO:2"])
        self.assertFalse(any(r["acceptable_as_original"] for r in rows))

    def test_categories_table(self):
        doc = {"instrument_id": "EO:1", "path": "/documents/x", "app_node": "1", "date": "1900-01-01",
               "president": "P", "categories": ["Presidential", "Executive Orders"], "attributes": ["Executive Orders"]}
        self.jsonl("DOCUMENTS.jsonl", [doc])
        self.jsonl("MIRROR_DOCUMENTS.jsonl", [doc, dict(doc, instrument_id="EO:9", path="/documents/y")])
        s = convert.convert(self.repo, self.out)
        with open(self.out / "CATEGORIES.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual([(r["instrument_id"], r["lane"], r["in_census"]) for r in rows],
                         [("EO:1", "live", "yes"), ("EO:9", "archive", "no")])
        self.assertEqual(s["categories"], {"Presidential": 2, "Executive Orders": 2})


if __name__ == "__main__":
    unittest.main()
