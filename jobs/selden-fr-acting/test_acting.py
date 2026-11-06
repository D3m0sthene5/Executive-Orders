"""Offline tests with a fake govinfo: link-service redirect, an issue 'PDF' whose page texts are injected."""
import csv
import io
import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import acting  # noqa: E402

PAGE = ("FEDERAL REGISTER 1086 RULES AND REGULATIONS\nPublic Land Order 570\nREVOKING EXECUTIVE ORDER NO. 7373 OF "
        "MAY 20, 1936\nBy virtue of the authority vested in the President, it is ordered as follows: Executive Order "
        "No. 7373 of May 20, 1936, withdrawing public lands in aid of legislation, is hereby revoked. "
        "Executive Order No. 73730 is not cited here.\n[F. R. Doc. 49-1800; Filed, Mar. 9, 1949]\n")
ISSUE = b"%PDF-1.4 fake issue"


def transport(url, headers, timeout):
    p = urllib.parse.urlsplit(url)
    if p.path == "/robots.txt":
        return 404, {}, io.BytesIO(b"")
    if p.path == "/link/fr/14/1086":
        return 302, {"location": "https://www.govinfo.gov/content/pkg/FR-1949-03-10/pdf/FR-1949-03-10.pdf#page=8"}, \
            io.BytesIO(b"")
    if p.path == "/content/pkg/FR-1949-03-10/pdf/FR-1949-03-10.pdf":
        return 200, {"content-length": str(len(ISSUE))}, io.BytesIO(ISSUE)
    return 404, {}, io.BytesIO(b"")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class Acting(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.repo = Path(self.tmp.name) / "repo"
        write_csv(r / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
                  [{"instrument_id": "EO:7373"}, {"instrument_id": "EO:9000"}])
        write_csv(r / "jobs/later-events/output/CATALOG_INDEX.csv", [{"id": "EO:9000", "signing_date": "1941-12-01"}])
        write_csv(r / "jobs/domesday-register/output/REGISTER.csv", [{"instrument_id": "EO:7373", "date": "1936-05-20"}])
        write_csv(r / "jobs/shepard-citations/output/PLO_TABLE.csv",
                  [{"plo_id": "PLO:570", "fr_volume": "14", "fr_page": "1086", "eo_refs": "EO:7373@1936-05-20=revocation"}])
        edge = {"acting_id": "PLO:570", "target_id": "EO:7373", "mechanism": "revocation", "acting_label": "PLO 570",
                "evidence_type": "shepard_blm_plo_table"}
        write_csv(r / "jobs/shepard-citations/output/EDGES.csv",
                  [edge, dict(edge, acting_id="EO:9100", target_id="EO:9000"),
                   dict(edge, target_id="EO:9999"), dict(edge, mechanism="cross_reference", target_id="EO:9000")])
        write_csv(r / "jobs/later-events/output/EDGES.csv", [dict(edge, acting_id="", target_id="EO:9000",
                  acting_label="Federal Aviation Agency regulations of June 28, 1960 (25 FR 5925)",
                  evidence_type="ofr_note_on_target")])
        self.out = Path(self.tmp.name) / "out"
        self.orig = (acting.frpages.pdf_pages, acting.frpages.extract_pdf)
        acting.frpages.pdf_pages = lambda raw, wanted=None: (["x"] * 7 + [PAGE] + ["y"] * 5) if raw == ISSUE else []
        acting.frpages.extract_pdf = lambda raw, a, b: (b"%PDF extract " + bytes([a, b]), "pypdf test")

    def tearDown(self):
        acting.frpages.pdf_pages, acting.frpages.extract_pdf = self.orig
        self.tmp.cleanup()

    def test_wanted(self):
        w = acting.wanted(self.repo)
        keys = {(i["actor"], i["vol"], i["page"]) for i in w}
        self.assertIn(("PLO:570", 14, 1086), keys)
        self.assertIn(("FRPAGE:25-5925", 25, 5925), keys)
        self.assertFalse(any(i["actor"].startswith("EO:") for i in w))
        plo = next(i for i in w if i["actor"] == "PLO:570")
        self.assertEqual(sorted(plo["targets"]), ["EO:7373"])  # non-census and cross_reference dropped

    def test_end_to_end(self):
        premis = lambda pkg: {"gpo_sha256": acting.S.sha256(ISSUE), "result": "match", "premis_url": "u"}
        s = acting.main(self.repo, self.out, Path(self.tmp.name) / "cache", transport=transport, premis=premis,
                        env={"JOB_WORKERS": "2"}, extract_procs=0)
        self.assertEqual(s["issues_gpo_premis_match"], 1)
        self.assertEqual(s["pairs_acting_on_target"], 1)
        frag = [json.loads(l) for l in (self.out / "FRAGMENTS.jsonl").read_text().splitlines()][0]["data"][0]
        self.assertEqual(frag["mechanism"], "revocation")
        self.assertTrue(frag["date_matches_target"])
        srcs = [json.loads(l) for l in (self.out / "SOURCES.jsonl").read_text().splitlines()]
        ext = next(x for x in srcs if x["source_id"].startswith("fr-extract:"))
        self.assertEqual(frag["source_sha256"], ext["sha256"])
        self.assertEqual(acting.S.sha256((self.out / ext["cache_path"]).read_bytes()), ext["sha256"])
        text = (self.out / frag["text_path"]).read_text()
        lo, hi = map(int, frag["quote_span"].split("-"))
        self.assertEqual(text[lo:hi], frag["quote"])
        self.assertEqual(ext["instrument_ids"][0], "PLO:570")
        ctl = json.loads((self.out / "CONTROLS.json").read_text())
        self.assertTrue(ctl["passed"])
        self.assertEqual(ctl["positives_located"], 1)
        fails = [json.loads(l) for l in (self.out / "FAILURES.jsonl").read_text().splitlines()]
        self.assertTrue(any(f["actor"] == "FRPAGE:25-5925" for f in fails))  # link service 404 recorded


if __name__ == "__main__":
    unittest.main()
