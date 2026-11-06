"""Offline tests: a fake Federal Register serves a search result and document texts."""
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
import citers  # noqa: E402

REVOKING = ("Executive Order 14100 of January 20, 2021\nSec. 2. Revocation. Executive Order 13879 of July 10, 2019 "
            "(Advancing American Kidney Health), is hereby revoked.\n")
AGENCY = "This rule responds to section 8 of Executive Order 13879, which directed the Secretary to act.\n"
NEARMISS = "Executive Order 138790 does not exist; Executive Order 1387 is unrelated.\n"
CONTROL = "Sec. 1. Executive Order 12000 of May 1, 1977, is hereby revoked.\n"


def fake_transport(url, headers, timeout):
    p = urllib.parse.urlsplit(url)
    if p.path == "/robots.txt":
        return 404, {}, io.BytesIO(b"")
    if p.path.endswith("documents.json"):
        q = urllib.parse.parse_qs(p.query)
        term = q["conditions[term]"][0]
        res = []
        if "13879" in term:
            res = [
                {"document_number": "2021-01", "type": "Presidential Document", "publication_date": "2021-01-25",
                 "signing_date": "2021-01-20", "citation": "86 FR 1", "title": "Revoking",
                 "raw_text_url": "https://www.federalregister.gov/t/2021-01.txt"},
                {"document_number": "2020-05", "type": "Rule", "publication_date": "2020-09-22",
                 "citation": "85 FR 5", "title": "Agency rule", "raw_text_url": "https://www.federalregister.gov/t/2020-05.txt"},
                {"document_number": "2019-15159", "type": "Presidential Document", "publication_date": "2019-07-15",
                 "raw_text_url": "https://www.federalregister.gov/t/own.txt"},
                {"document_number": "2022-09", "type": "Notice", "publication_date": "2022-01-01",
                 "raw_text_url": "https://www.federalregister.gov/t/2022-09.txt"},
            ]
        body = json.dumps({"count": len(res), "total_pages": 1, "results": res}).encode()
        return 200, {"content-length": str(len(body))}, io.BytesIO(body)
    texts = {"/t/2021-01.txt": REVOKING, "/t/2020-05.txt": AGENCY, "/t/2022-09.txt": NEARMISS,
             "/t/ctl.txt": CONTROL, "/t/own.txt": "Executive Order 13879 text"}
    if p.path in texts:
        b = texts[p.path].encode()
        return 200, {"content-length": str(len(b))}, io.BytesIO(b)
    return 404, {}, io.BytesIO(b"")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class Citers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        base = {"provisional_status": "yes", "text_evidence_tier": "original_supported",
                "step_ending_or_current_basis": "open", "step_counterevidence": "open"}
        write_csv(self.repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
                  [dict(base, instrument_id="EO:13879"), dict(base, instrument_id="EO:12000"),
                   dict(base, instrument_id="EO:2656A")])
        cat = [{"id": "EO:13879", "signing_date": "2019-07-10", "publication_date": "2019-07-15",
                "document_number": "2019-15159", "raw_text_url": "https://www.federalregister.gov/t/own.txt"},
               {"id": "EO:14100", "signing_date": "2021-01-20", "publication_date": "2021-01-25",
                "document_number": "2021-01", "raw_text_url": "https://www.federalregister.gov/t/2021-01.txt"},
               {"id": "EO:12001", "signing_date": "1997-05-01", "publication_date": "1997-05-03",
                "document_number": "97-1", "raw_text_url": "https://www.federalregister.gov/t/ctl.txt"},
               {"id": "EO:12000", "signing_date": "1977-05-01", "publication_date": "1977-05-03",
                "document_number": "", "raw_text_url": ""}]
        write_csv(self.repo / "jobs/later-events/output/CATALOG_INDEX.csv", cat)
        write_csv(self.repo / "jobs/later-events/output/EDGES.csv",
                  [{"acting_id": "EO:12001", "target_id": "EO:12000", "mechanism": "revocation",
                    "evidence_type": "ofr_note_on_target"}])
        self.out = Path(self.tmp.name) / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def run_job(self):
        env = {"JOB_PRIOR_OUTPUT_DIR": str(Path(self.tmp.name) / "none"), "JOB_WORKERS": "2"}
        return citers.main(self.repo, self.out, Path(self.tmp.name) / "cache", transport=fake_transport, env=env)

    def test_end_to_end(self):
        s = self.run_job()
        self.assertTrue(s["controls"]["passed"])
        self.assertEqual(s["controls"]["positives_located"], 1)
        frags = [json.loads(l) for l in (self.out / "FRAGMENTS.jsonl").read_text().splitlines()]
        by = {f["data"][0]["acting_id"]: f["data"][0] for f in frags}
        self.assertEqual(by["EO:14100"]["mechanism"], "revocation")
        self.assertIn("FRDOC:2020-05", by)
        self.assertEqual(by["FRDOC:2020-05"]["mechanism"], "cross_reference")
        self.assertNotIn("FRDOC:2022-09", by)  # near-miss numbers only
        srcs = {json.loads(l)["source_id"]: json.loads(l) for l in (self.out / "SOURCES.jsonl").read_text().splitlines()}
        rec = srcs["fr:doc:2021-01"]
        held = (self.out / rec["cache_path"]).read_bytes()
        self.assertEqual(citers.S.sha256(held), rec["sha256"])
        lo, hi = map(int, by["EO:14100"]["quote_span"].split("-"))
        self.assertEqual(held.decode()[lo:hi], by["EO:14100"]["quote"])
        self.assertEqual(rec["instrument_ids"][0], "EO:14100")
        searches = [json.loads(l) for l in (self.out / "SEARCHES.jsonl").read_text().splitlines()]
        s13879 = next(x for x in searches if x["instrument_id"] == "EO:13879")
        self.assertEqual(s13879["hits"], 3)  # own document excluded
        self.assertEqual(s13879["documents_acting_on_target"], 1)
        self.assertNotIn("EO:2656A", {x["instrument_id"] for x in searches})

    def test_resume_skips_searched(self):
        self.run_job()
        prior = self.out
        out2 = Path(self.tmp.name) / "out2"
        s = citers.main(self.repo, out2, Path(self.tmp.name) / "cache", transport=fake_transport,
                        env={"JOB_PRIOR_OUTPUT_DIR": str(prior), "JOB_WORKERS": "2"})
        self.assertEqual(s["targets_searched_this_run"], 0)
        self.assertEqual(s["sources_carried"], s["sources_kept"])
        self.assertTrue((out2 / "FRAGMENTS.jsonl").read_text())


if __name__ == "__main__":
    unittest.main()
