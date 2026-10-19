"""American Presidency Project pages from app-executive-orders as fallback, transcription-based draft inputs.

Offline fixture repo (the one test_build.py builds) plus an app-executive-orders output folder.
"""

import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build  # noqa: E402
import sources as SRC  # noqa: E402
from test_build import build_fixture_repo  # noqa: E402

BODY = ("By virtue of the authority vested in me as President, it is hereby ordered as follows:\n\n"
        "1. The Secretary of the Interior shall withdraw the lands described below from settlement.\n\n"
        "2. This order shall remain in force until revoked by the President.\n\n"
        "FRANKLIN D ROOSEVELT\n\nThe White House,\nMarch 3, {year}.\n")


def app_doc(number, slug, heading, text_path, text_sha, date="1938-03-03", lane="archive"):
    rec = {"instrument_id": f"EO:{number}", "heading": heading, "date": date, "app_node": "1",
           "url": f"https://www.presidency.ucsb.edu/documents/{slug}",
           "final_url": f"https://www.presidency.ucsb.edu/documents/{slug}", "path": f"/documents/{slug}",
           "sha256": "9" * 64, "bytes": 5000, "text_path": text_path, "text_sha256": text_sha,
           "retrieved_utc": "2026-10-18T00:00:00Z", "footnote": "", "categories": [], "attributes": []}
    if lane == "archive":
        rec.update(route="archive/common-crawl",
                   capture={"archive": "common-crawl", "captured_utc": "2025-10-10T10:30:10Z"})
    return rec


class AppInputs(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.root = self.tmp / "repo"
        build_fixture_repo(self.root)
        with open(self.root / build.UNIVERSE, "a", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerows([[f"EO:{n}", "1938", "1937–1989"] for n in (8100, 8200, 8300, 8400, 8500, 8600)])
        self.app = self.root / "jobs" / SRC.APP_JOB / "output"
        (self.app / "texts").mkdir(parents=True)
        self.archive, self.live = [], []

    def text(self, slug, body):
        (self.app / "texts" / f"{slug}.txt").write_text(body, encoding="utf-8", newline="")
        return f"texts/{slug}.txt", hashlib.sha256(body.encode("utf-8")).hexdigest()

    def add(self, number, heading=None, slug=None, year="1938", date="1938-03-03", wrong_hash=False, lane="archive"):
        slug = slug or f"executive-order-{number}-withdrawal-public-lands"
        tp, sha = self.text(f"{slug}-{lane}", BODY.format(year=year))
        heading = heading or f"Executive Order {number}—Withdrawal of Public Lands"
        rec = app_doc(number, slug, heading, tp, "0" * 64 if wrong_hash else sha, date=date, lane=lane)
        (self.archive if lane == "archive" else self.live).append(rec)

    def run_build(self, **env_extra):
        for name, rows in (("MIRROR_DOCUMENTS.jsonl", self.archive), ("DOCUMENTS.jsonl", self.live)):
            with open(self.app / name, "w", encoding="utf-8") as fh:
                fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        out = self.tmp / "out"
        env = {"OUTPUT_DIR": str(out), "REPO_ROOT": str(self.root), "JOB_CACHE_DIR": str(self.tmp / "cache"),
               "JOB_LIMIT": "", "JOB_IDS": "", "CLAUSE_INPUT_JOBS": "fr-originals", "CLAUSE_ALLOW_PARTIAL_INPUTS": "",
               "CLAUSE_MEASURE_ALL": "1"}
        env.update(env_extra)
        with mock.patch.dict(os.environ, env), mock.patch("sys.stdout", new=io.StringIO()):
            build.main()
        frags = {}
        for name in ("FRAGMENTS.jsonl", build.APP_FRAGMENTS):
            for line in (out / name).read_text(encoding="utf-8").splitlines():
                f = json.loads(line)
                self.assertEqual(name == build.APP_FRAGMENTS, bool(f.get("transcription_based")), name)
                frags[f["instrument_id"]] = f
        with open(out / "IDENTITY_QUARANTINE.csv", encoding="utf-8", newline="") as fh:
            quarantine = {r["instrument_id"]: r for r in csv.DictReader(fh)}
        problems = (out / "INPUT_PROBLEMS.csv").read_text(encoding="utf-8")
        summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
        return out, frags, quarantine, problems, summary

    def test_app_page_gives_a_labelled_transcription_based_draft(self):
        self.add(8100)
        out, frags, _, _, summary = self.run_build()
        f = frags["EO:8100"]
        self.assertEqual(f["source_grade"], "mirror_transcription_app")
        self.assertTrue(f["transcription_based"])
        self.assertFalse(f["acceptable_as_original"])
        self.assertEqual(f["representation_type"], "secondary_compilation_transcription")
        self.assertTrue(f["confidence_note"].startswith("TRANSCRIPTION-BASED"))
        self.assertEqual([c["scope_id"] for c in f["data"]], ["EO:8100#para1", "EO:8100#para2"])
        saved = (out / f["data"][0]["text_offsets"]["text_path"]).read_text(encoding="utf-8")
        self.assertTrue(saved.startswith("Executive Order 8100—Withdrawal of Public Lands"))
        for c in f["data"]:
            self.assertIn(c["original_operative_text"], saved)
            self.assertIn("transcription; not an official edition", c["original_source"]["page_or_item"])
            self.assertEqual(c["original_source"]["sha256"], "9" * 64)
        self.assertEqual(summary["fragments_from_app_transcription"], 1)
        self.assertTrue(summary["self_check"]["passed"])
        self.assertIn("app_transcription_job", summary["segmentation_outcomes_by_input"]["by_input"])

    def test_an_official_copy_is_preferred_over_an_app_page(self):
        # EO:7000 has a fr-originals text; EO:13500 a Stage 21 PDF.
        self.add(7000, year="1935", date="1935-03-01")
        self.add(13500, year="2005", date="2005-01-02")
        _, frags, _, _, summary = self.run_build()
        self.assertNotEqual(frags["EO:7000"]["source_grade"], "mirror_transcription_app")
        self.assertNotIn("transcription_based", frags["EO:7000"])
        self.assertEqual(frags["EO:13500"]["source_grade"], "official_fr_pdf_text_layer")
        self.assertIn("mirror_transcription_app", {a["grade"] for a in frags["EO:7000"]["alternate_sources"]})
        self.assertEqual(summary["fragments_from_app_transcription"], 0)

    def test_wrong_order_protection(self):
        self.add(8200, heading="Executive Order 8201—Withdrawal of Public Lands")         # heading names another order
        self.add(8300, heading="Statement on Signing the Public Lands Order")             # not an executive order
        self.add(8400, slug="executive-order-8401-withdrawal-public-lands")              # address names another order
        self.add(8500, date="1950-03-03")                                                 # page date far from census year
        self.add(8600, wrong_hash=True)                                                   # text is another capture's
        _, frags, quarantine, problems, _ = self.run_build()
        for iid in ("EO:8200", "EO:8300", "EO:8400", "EO:8500", "EO:8600"):
            self.assertNotIn(iid, frags, iid)
        self.assertIn("app_heading_names_another_order_8201", problems)
        self.assertIn("app_heading_is_not_a_numbered_executive_order", problems)
        self.assertIn("app_text_file_holds_another_capture", problems)
        self.assertIn("app_page_title_number_8400_differs_from_url_number_8401", quarantine["EO:8400"]["reasons"])
        self.assertIn("identity_doubt_app_page_date_1950_vs_census_year_1938", quarantine["EO:8500"]["reasons"])

    def test_live_and_archive_copies_of_one_text_are_one_candidate_and_input_can_be_turned_off(self):
        self.add(8100, lane="live")
        self.add(8100, lane="archive")
        cands, _, seen = SRC.app_job_candidates(self.root, {"EO:8100"}, {"EO:8100": "1938"})
        self.assertEqual(len(cands), 0)  # nothing written yet
        _, frags, _, _, summary = self.run_build()
        self.assertEqual(summary["inputs"]["app_transcriptions"],
                         {"DOCUMENTS.jsonl": "1 order-text candidates", "MIRROR_DOCUMENTS.jsonl": "0 order-text candidates"})
        self.assertIn("EO:8100", frags)
        _, frags, _, _, summary = self.run_build(CLAUSE_APP_INPUT="0")
        self.assertNotIn("EO:8100", frags)
        self.assertEqual(summary["fragments_from_app_transcription"], 0)


if __name__ == "__main__":
    unittest.main()
