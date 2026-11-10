"""Offline tests: a fake govinfo search API and content server, page texts injected in place of OCR."""
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
import cruden  # noqa: E402

# A 1954 order revoking a 1929 withdrawal (the real EO 5214 case), a Philippine order sharing a number, a sentence
# with the wrong date, a mention without a relation word, and the planted PLO control.
PAGES = {
    "FR-1954-03-24": [
        "FEDERAL REGISTER contents. Land Management Bureau: Alaska; revocation of E. O. 5214, Oct. 30, 1929 ..... 1583",
        "EXECUTIVE ORDER 10524\nREVOKING EXECUTIVE ORDER NO. 5214\nBy virtue of the authority vested in the President "
        "by section 1 of the act of June 25, 1910, it is ordered as follows: Executive Order No. 5214 of October 30, "
        "1929, withdrawing certain areas of land and water in Alaska for naval purposes, is hereby revoked.\n"
        "[F. R. Doc. 54-2001; Filed, Mar. 23, 1954]\n",
    ],
    "FR-1936-10-07": [
        "sugar allotments made under the terms of Executive Order No. 885 of the Governor General of the Philippine "
        "Islands, issued at Manila, October 12, 1935. The allocation provided for in this section shall be enforced.",
    ],
    "FR-1950-01-05": [
        "PUBLIC LAND ORDER 610\nBy virtue of the authority vested in the President, it is ordered as follows: Executive "
        "Order No. 4100 of December 1, 1924, reserving lands for a lighthouse, is hereby revoked.\n"
        "Executive Order No. 3000 of May 5, 1931, is hereby revoked.\n"
        "[F. R. Doc. 50-12; Filed, Jan. 4, 1950]\n",
    ],
    "FR-1960-06-01": [
        "PUBLIC LAND ORDER 2100\nIt is ordered as follows: Executive Order No. 4444 of March 8, 1926, withdrawing public "
        "lands for a ranger station, is hereby revoked so far as it affects the following described lands.\n"
        "[F. R. Doc. 60-50; Filed, May 31, 1960]\n",
    ],
}
SEARCH = {  # target -> FR packages
    "5214": ["FR-1954-03-24"], "885": ["FR-1936-10-07"], "3000": ["FR-1950-01-05"], "4444": ["FR-1960-06-01"],
    "4100": ["FR-1950-01-05"], "6000": [],
}


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener(req, timeout=60):
    assert req.get_header("X-api-key"), "the key goes in a header"
    assert "api_key" not in req.full_url
    q = json.loads(req.data)["query"]
    n = q.split('"Executive Order No. ')[1].split('"')[0]
    coll = q.split("collection:")[1].split(" ")[0]
    pk = SEARCH.get(n, []) if coll == "FR" else []
    body = {"count": len(pk), "results": [{"packageId": p, "dateIssued": p[3:], "title": p} for p in pk]}
    return FakeResp(json.dumps(body).encode())


def transport(url, headers, timeout):
    p = urllib.parse.urlsplit(url)
    if p.path == "/robots.txt":
        return 404, {}, io.BytesIO(b"")
    for pkg in PAGES:
        if p.path == f"/content/pkg/{pkg}/pdf/{pkg}.pdf":
            raw = b"%PDF-1.4 fake " + pkg.encode()
            return 200, {"content-length": str(len(raw))}, io.BytesIO(raw)
    return 404, {}, io.BytesIO(b"")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class Cruden(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.repo = Path(self.tmp.name) / "repo"
        write_csv(r / "jobs/linnaeus-types/output/CRUDEN_TARGETS.csv",
                  [{"instrument_id": f"EO:{n}", "family": "LAND_WITHDRAWAL", "era": "1907-1936"}
                   for n in ("885", "3000", "4444", "5214", "6000")])
        write_csv(r / "jobs/domesday-register/output/REGISTER.csv",
                  [{"instrument_id": "EO:885", "date": "1908-06-12"}, {"instrument_id": "EO:3000", "date": "1918-11-11"},
                   {"instrument_id": "EO:4444", "date": "1926-03-08"}, {"instrument_id": "EO:5214", "date": "1929-10-30"},
                   {"instrument_id": "EO:6000", "date": "1933-01-30"}, {"instrument_id": "EO:4100", "date": "1924-12-01"}])
        write_csv(r / "jobs/shepard-citations/output/PLO_TABLE.csv",
                  [{"plo_id": "PLO:610", "fr_volume": "15", "fr_page": "1", "eo_refs": "EO:4100@1924-12-01=revocation"}])
        self.out = Path(self.tmp.name) / "out"
        self.env = {"GOVINFO_API_KEY": "test-key", "CRUDEN_SEARCH_INTERVAL": "0", "JOB_WORKERS": "2",
                    "JOB_PRIOR_OUTPUT_DIR": str(Path(self.tmp.name) / "none"), "CRUDEN_COLLECTIONS": "FR,STATUTE"}
        self.orig = (cruden.pdf_pages, cruden.extract_pages)
        cruden.pdf_pages = lambda raw: (PAGES[raw.decode().split()[-1]], "test")
        cruden.extract_pages = lambda raw, a, b: (b"%PDF extract " + raw + f" {a}-{b}".encode(), "test")

    def tearDown(self):
        cruden.pdf_pages, cruden.extract_pages = self.orig
        self.tmp.cleanup()

    def run_job(self):
        return cruden.main(self.repo, self.out, Path(self.tmp.name) / "cache", env=self.env, transport=transport,
                           opener=opener, premis=lambda pkg: {"gpo_sha256": "", "result": "not_listed"})

    def frags(self):
        return [json.loads(x) for x in (self.out / "FRAGMENTS.jsonl").read_text().splitlines()]

    def test_acting_sentence_found_and_tied_by_number_and_date(self):
        s = self.run_job()
        f = {(x["instrument_id"], x["data"][0]["mechanism"]) for x in self.frags()}
        self.assertIn(("EO:5214", "revocation"), f)
        row = next(x["data"][0] for x in self.frags() if x["instrument_id"] == "EO:5214"
                   and x["data"][0]["acting_id"] == "EO:10524" and x["data"][0]["date_matches_target"])
        self.assertEqual(row["mechanism"], "revocation")
        self.assertEqual(row["acting_id"], "EO:10524")
        self.assertTrue(row["date_matches_target"])
        self.assertIn("publication_date_not_instrument_date", row["flags"])
        self.assertTrue(s["controls"]["passed"])

    def test_other_issuer_and_wrong_date_are_refused_not_published(self):
        self.run_job()
        ids = {x["instrument_id"] for x in self.frags()}
        self.assertNotIn("EO:885", ids)       # Philippine Governor General's order No. 885
        self.assertNotIn("EO:3000", ids)      # printed date May 5, 1931 is not EO 3000's
        located = list(csv.DictReader(open(self.out / "LOCATED.csv", encoding="utf-8")))
        why = {r["target_id"]: r["refused"] for r in located if r["refused"]}
        self.assertEqual(why["EO:885"], "another_issuer_printed_with_the_number")
        self.assertEqual(why["EO:3000"], "printed_date_disagrees_with_target")

    def test_other_issuer_without_date(self):
        txt = "under Executive Order No. 885 of the Governor General of the Philippine Islands the allotment"
        hits = cruden.locate(txt, "EO:885", "1908-06-12")
        self.assertEqual(hits[0][1], "another_issuer_printed_with_the_number")

    def test_partial_act_is_qualified(self):
        self.run_job()
        row = next(x["data"][0] for x in self.frags() if x["instrument_id"] == "EO:4444")
        self.assertEqual(row["acting_id"], "PLO:2100")
        self.assertEqual(row["qualifier"], "in part")

    def test_silence_is_never_a_fragment(self):
        s = self.run_job()
        self.assertNotIn("EO:6000", {x["instrument_id"] for x in self.frags()})
        rec = [json.loads(x) for x in (self.out / "SEARCHES.jsonl").read_text().splitlines()]
        r = next(x for x in rec if x["target_id"] == "EO:6000" and x["collection"] == "FR")
        self.assertEqual((r["status"], r["count"]), ("searched", 0))
        self.assertEqual(s["by_family"]["LAND_WITHDRAWAL"]["targets"], 5)

    def test_control_target_not_published_as_lead(self):
        s = self.run_job()
        self.assertNotIn("EO:4100", {x["instrument_id"] for x in self.frags()})
        self.assertEqual(s["controls"]["positives_located"], 1)

    def test_sources_record_hashes_and_never_one_order(self):
        self.run_job()
        src = [json.loads(x) for x in (self.out / "SOURCES.jsonl").read_text().splitlines()]
        self.assertTrue(src)
        for r in src:
            self.assertGreaterEqual(len(r["instrument_ids"]), 2)
            self.assertFalse(r["acceptable_as_original"])
            self.assertRegex(r["sha256"], "^[0-9a-f]{64}$")
            if r.get("cache_path"):
                import hashlib
                self.assertEqual(hashlib.sha256((self.out / r["cache_path"]).read_bytes()).hexdigest(), r["sha256"])

    def test_quote_span_points_into_held_text(self):
        self.run_job()
        for f in self.frags():
            d = f["data"][0]
            text = (self.out / d["text_path"]).read_text(encoding="utf-8")
            a, b = map(int, d["quote_span"].split("-"))
            self.assertEqual(text[a:b], d["quote"])

    def test_carry_forward_makes_no_new_downloads(self):
        self.run_job()
        prior = Path(self.tmp.name) / "prior"
        self.out.rename(prior)
        self.env["JOB_PRIOR_OUTPUT_DIR"] = str(prior)
        calls = []

        def counting(url, headers, timeout):
            calls.append(url)
            return transport(url, headers, timeout)
        s = cruden.main(self.repo, self.out, Path(self.tmp.name) / "cache2", env=self.env, transport=counting,
                        opener=lambda *a, **k: self.fail("no new search"),
                        premis=lambda pkg: {"gpo_sha256": "", "result": "not_listed"})
        self.assertEqual([u for u in calls if "/content/" in u], [])
        self.assertIn("EO:5214", {x["instrument_id"] for x in self.frags()})
        self.assertEqual(s["searches_made_this_run"], 0)

    def test_short_number_without_date_is_pointer_only(self):
        txt = "PUBLIC LAND ORDER 5\nExecutive Order No. 812 is hereby revoked.\n"
        h, why = cruden.locate(txt, "EO:812", "1908-05-01")[0]
        self.assertIsNone(why)
        self.assertIsNone(h["date_match"])

    def test_query_forms(self):
        q = cruden.query("EO:2656A", "FR", "1917-01-01")
        self.assertIn('"Executive Order No. 2656-A"', q)
        self.assertIn("publishdate:range(1936-03-14,1993-12-31)", q)
        self.assertNotIn("publishdate", cruden.query("EO:5214", "STATUTE", "1929-10-30"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
