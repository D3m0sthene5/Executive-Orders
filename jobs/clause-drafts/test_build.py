"""Tests for input collection and the whole build, on a tiny fixture repo.

No network. Builds a fake repo in a temp folder with: a universe CSV, a Stage 21
custody list + a generated 2-page PDF, a small Opus-style zip (APP page text +
meta, a layout text that must be skipped, a meta without SHA-256), and an
"other job" output folder with SOURCES.jsonl + texts/ in the shared SOURCE
RECORD format.
"""

import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build  # noqa: E402
import sources as SRC  # noqa: E402

# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


def make_pdf(pages):
    """A minimal valid PDF with one Helvetica text line per list item."""
    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None]
    kids = []
    for lines in pages:
        content = "BT /F1 10 Tf 12 TL 40 760 Td " + " ".join(f"({esc(l)}) Tj T*" for l in lines) + " ET"
        page_no = len(objs) + 1
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 FONT 0 R >> >> /Contents {page_no + 1} 0 R >>")
        objs.append(f"<< /Length {len(content)} >>\nstream\n{content}\nendstream")
        kids.append(f"{page_no} 0 R")
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    font = len(objs)
    objs = [o.replace("FONT", str(font)) if o else o for o in objs]
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out = b"%PDF-1.4\n"
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


PDF_PAGES = [
    [
        "Presidential Documents",
        "61001",
        "Federal Register",
        "Vol. 70, No. 1",
        "Executive Order 13500 of January 2, 2005",
        "Example Coordination Order",
        "By the authority vested in me as President by the Constitution and the",
        "laws of the United States of America, it is hereby ordered as follows:",
        "Section 1. Policy. It is the policy of the United States to coordinate.",
        "Sec. 2. Duties. (a) The Secretary shall coordinate the work of the agencies",
    ],
    [
        "61002 Federal Register / Vol. 70, No. 1 / Monday, January 3, 2005 / Presidential Documents",
        "named in this order.",
        "(b) The Secretary shall report to the President annually.",
        "Sec. 3. Executive Order 12000 of May 1, 1977, is hereby revoked.",
        "THE WHITE HOUSE,",
        "January 2, 2005.",
        "[FR Doc. 05-100 Filed 1-2-05; 8:45 am]",
    ],
]

APP_TEXT = (
    "Executive Order 9001—Example Wartime Contracts | The American Presidency Project\n\nSkip to main content\n\n"
    "Executive Order 9001—Example Wartime Contracts\n\nDecember 27, 1941\n\n"
    "By virtue of the authority vested in me by the First War Powers Act, it is hereby ordered as follows:\n\n"
    "1. The War Department is authorized to enter into contracts for the prosecution of the war.\n\n"
    "2. This order shall not be construed to authorize contracts on a cost-plus basis.\n\n"
    "FRANKLIN D ROOSEVELT\n\nThe White House,\nDecember 27, 1941.\n\n"
    "Franklin D. Roosevelt, Executive Order 9001—Example Online by Gerhard Peters and John T. Woolley, The American Presidency Project\n"
)

JOB_TEXT = (
    "Executive Order 7000\n\nIt is hereby ordered that the lands described in the act are withdrawn from entry.\n\n"
    "FRANKLIN D ROOSEVELT\n\nThe White House,\nMarch 1, 1935.\n"
)


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def build_fixture_repo(root: Path):
    write_csv(root / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
              ["id", "date_effective", "year_group"],
              [["EO:13500", "2005", "1990–2026"], ["EO:9001", "1941", "1937–1989"], ["EO:7000", "1935", "1907–1936"],
               ["EO:12000", "1977", "1937–1989"], ["EO:8000", "1938", "1937–1989"]])
    write_csv(root / "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv",
              ["instrument_id", "provisional_substantive_status"], [["EO:13500", "no"]])
    pdf = make_pdf(PDF_PAGES)
    pdf_rel = "research/stage21/original_sources/EO_13500.pdf"
    (root / pdf_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / pdf_rel).write_bytes(pdf)
    write_csv(root / "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
              ["instrument_id", "official_PDF_candidate_URL", "custody_state", "sha256_source_bytes_if_present",
               "source_repository_path", "bytes", "attempted_utc", "retrieval_error"],
              [["EO:13500", "https://www.govinfo.gov/content/pkg/FR-2005-01-03/pdf/05-100.pdf", "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED",
                hashlib.sha256(pdf).hexdigest(), pdf_rel, len(pdf), "2026-10-17T00:00:00+00:00", ""],
               ["EO:12000", "https://www.govinfo.gov/x.pdf", "NOT_CAPTURED", "", "", "", "", "HTTP 404"]])
    write_csv(root / "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv",
              ["instrument_id", "FR_citation_from_cached_index"], [["EO:13500", "70 FR 61001"]])
    zpath = root / SRC.OPUS_ZIP
    zpath.parent.mkdir(parents=True, exist_ok=True)
    base = "OPUS_STAGE11_FINITE_STATUS_DELTA/evidence/shards/S11_X/cache/"
    meta = {"url": "https://www.presidency.ucsb.edu/documents/executive-order-9001-example", "sha256": "a" * 64,
            "retrieved_utc": "2026-10-16T00:00:00Z", "content_type": "text/html; charset=utf-8", "bytes": "1234"}
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr(base + "app_eo9001.txt", APP_TEXT)
        z.writestr(base + "app_eo9001.meta.json", json.dumps(meta))
        z.writestr(base + "app_eo9001.lay.txt", APP_TEXT)  # layout variant: skipped
        z.writestr(base + "app_eo8000.txt", APP_TEXT.replace("9001", "8000"))
        z.writestr(base + "app_eo8000.meta.json", json.dumps({**meta, "sha256": ""}))  # no hash: skipped
    job_out = root / "jobs/fr-originals/output"
    (job_out / "texts").mkdir(parents=True, exist_ok=True)
    (job_out / "texts/eo7000.txt").write_text(JOB_TEXT, encoding="utf-8", newline="")
    rec = {"source_id": "fr-originals:eo7000", "instrument_ids": ["EO:7000"], "url": "https://www.govinfo.gov/content/pkg/FR-1935-03-02/pdf/x.pdf",
           "sha256": "b" * 64, "bytes": 10, "content_type": "application/pdf", "retrieved_utc": "2026-10-17T00:00:00Z",
           "route": "test", "page_or_item": "FR issue 1935-03-02 p. 3", "text_path": "texts/eo7000.txt", "cache_path": None, "notes": ""}
    bad = {**rec, "source_id": "bad", "sha256": "nothex"}
    (job_out / "SOURCES.jsonl").write_text(json.dumps(rec) + "\n" + json.dumps(bad) + "\n", encoding="utf-8")
    return pdf


def source_ok(ref):
    """Same rule as research/stage19/code/claim_gate.py source_ok (online case)."""
    return bool(ref.get("page_or_item") and isinstance(ref.get("url"), str) and ref["url"].startswith("https://")
                and ref.get("sha256"))


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


class SourceHelperTests(unittest.TestCase):
    def test_grades(self):
        self.assertEqual(SRC.grade_for_url("https://www.govinfo.gov/content/pkg/FR-1995-01-03/pdf/94-32388.pdf"), "official_fr_pdf_text_layer")
        self.assertEqual(SRC.grade_for_url("https://www.govinfo.gov/content/pkg/FR-1942-01-20/pdf/FR-1942-01-20.pdf"), "official_fr_scan_ocr_text")
        self.assertEqual(SRC.grade_for_url("https://www.presidency.ucsb.edu/documents/executive-order-8802-x"), "mirror_transcription_app")
        self.assertIsNone(SRC.grade_for_url("https://www.federalregister.gov/api/v1/documents.json?x=1"))
        self.assertIsNone(SRC.grade_for_url("http://www.presidency.ucsb.edu/documents/executive-order-1"))
        self.assertIsNone(SRC.grade_for_url("https://www.archives.gov/federal-register/codification/executive-order/12281.html"))

    def test_ids_and_years(self):
        self.assertEqual(SRC.to_instrument_id("4359-A", {"EO:4359A"}), "EO:4359A")
        self.assertEqual(SRC.to_instrument_id("012944", set()), "EO:12944")
        self.assertIsNone(SRC.to_instrument_id("99999", {"EO:1"}))
        self.assertEqual(SRC.app_number_from_url("https://www.presidency.ucsb.edu/documents/executive-order-6513-j-amendments"), "6513-J")
        self.assertEqual(SRC.issue_year("https://www.govinfo.gov/content/pkg/FR-2003-01-28/html/03-2069.htm"), 2003)

    def test_meta_lookup(self):
        names = {"a/cache/FR-1941-01-16.meta.json", "a/cache/x.meta.json"}
        self.assertEqual(SRC._meta_for("a/cache/FR-1941-01-16.raw.txt", names), "a/cache/FR-1941-01-16.meta.json")
        self.assertEqual(SRC._meta_for("a/cache/x.norm.txt", names), "a/cache/x.meta.json")
        self.assertIsNone(SRC._meta_for("a/cache/y.txt", names))

    def test_pdf_text_removes_furniture_and_keeps_pages(self):
        text, starts, raw_first = SRC.pdf_text(make_pdf(PDF_PAGES))
        self.assertEqual(len(starts), 2)
        self.assertNotIn("Federal Register / Vol.", text)
        self.assertIn("(b) The Secretary shall report", text[starts[1]:])


class BuildIntegrationTest(unittest.TestCase):
    def test_build_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            build_fixture_repo(root)
            out = Path(tmp) / "out"
            env = {"OUTPUT_DIR": str(out), "REPO_ROOT": str(root), "JOB_CACHE_DIR": str(Path(tmp) / "cache"),
                   "JOB_LIMIT": "", "JOB_IDS": "", "CLAUSE_INPUT_JOBS": "fr-originals,source-ladder"}
            with mock.patch.dict(os.environ, env), mock.patch("sys.stdout", new=io.StringIO()):
                build.main()
            summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["self_check"]["passed"])
            frags = {json.loads(l)["instrument_id"]: json.loads(l) for l in (out / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines()}
            self.assertEqual(sorted(frags), ["EO:13500", "EO:7000", "EO:9001"])
            self.assertEqual(summary["fragments_written"], 3)
            # Stage 21 PDF: sections, FR page attribution, revocation target
            f = frags["EO:13500"]
            ids = [c["scope_id"] for c in f["data"]]
            self.assertEqual(ids, ["EO:13500#sec1", "EO:13500#sec2(a)", "EO:13500#sec2(b)", "EO:13500#sec3"])
            self.assertEqual(f["data"][2]["original_source"]["page_or_item"], "70 FR 61002 (PDF p. 2); Sec. 2(b)")
            self.assertIn("70 FR 61001-61002", f["data"][1]["original_source"]["page_or_item"])
            self.assertEqual(f["data"][3]["clause_kind"], "revokes_or_supersedes_other_order")
            self.assertEqual(f["source_grade"], "official_fr_pdf_text_layer")
            # APP text from the zip
            g = frags["EO:9001"]
            self.assertEqual([c["scope_id"] for c in g["data"]], ["EO:9001#para1", "EO:9001#para2"])
            self.assertEqual(g["sources"][0]["sha256"], "a" * 64)
            # other job's SOURCE RECORD
            h = frags["EO:7000"]
            self.assertEqual([c["scope_id"] for c in h["data"]], ["EO:7000#whole"])
            for frag in frags.values():
                self.assertEqual(frag["kind"], "operative_clauses")
                self.assertEqual(frag["produced_by"], "clause-drafts")
                for c in frag["data"]:
                    self.assertTrue(source_ok(c["original_source"]))
                    self.assertIsNone(c["state_at_cutoff"])
                    self.assertEqual(c["later_events"], [])
                    self.assertIn("state_at_cutoff", c["needs_judgment"])
                    saved = (out / c["text_offsets"]["text_path"]).read_text(encoding="utf-8")
                    self.assertIn(c["original_operative_text"], saved)
            # sources file in the shared format
            recs = [json.loads(l) for l in (out / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(recs), 3)
            for r in recs:
                for k in ("source_id", "instrument_ids", "url", "sha256", "bytes", "content_type", "retrieved_utc", "route", "page_or_item", "text_path", "cache_path", "notes"):
                    self.assertIn(k, r)
                self.assertTrue((out / r["text_path"]).exists())
            with open(out / "CLAUSES.csv", encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 7)
            problems = (out / "INPUT_PROBLEMS.csv").read_text(encoding="utf-8")
            self.assertIn("stage21_no_pdf_captured", problems)
            self.assertIn("source_record_unusable", problems)
            self.assertEqual(summary["inputs"]["opus_zip"]["skipped"].get("layout_columns_text"), 1)
            self.assertEqual(summary["inputs"]["opus_zip"]["skipped"].get("no_original_sha256"), 1)

    def test_job_limit_and_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            build_fixture_repo(root)
            out = Path(tmp) / "out"
            env = {"OUTPUT_DIR": str(out), "REPO_ROOT": str(root), "JOB_CACHE_DIR": str(Path(tmp) / "cache"),
                   "JOB_LIMIT": "1", "JOB_IDS": "", "CLAUSE_INPUT_JOBS": "fr-originals"}
            with mock.patch.dict(os.environ, env), mock.patch("sys.stdout", new=io.StringIO()):
                build.main()
            self.assertEqual(json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))["fragments_written"], 1)
            env["JOB_LIMIT"] = ""
            env["JOB_IDS"] = "EO:9001"
            with mock.patch.dict(os.environ, env), mock.patch("sys.stdout", new=io.StringIO()):
                build.main()
            lines = (out / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual([json.loads(l)["instrument_id"] for l in lines], ["EO:9001"])


if __name__ == "__main__":
    unittest.main()
