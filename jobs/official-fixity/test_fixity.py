"""Tests for fixity.py (no network)."""

import csv
import json
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path

import fixity

PREMIS = """<?xml version="1.0"?><premis xmlns="info:lc/xmlns/premis-v2">
<object><objectIdentifier><objectIdentifierValue>R1</objectIdentifierValue></objectIdentifier>
<objectCharacteristics><fixity><messageDigestAlgorithm>SHA-256</messageDigestAlgorithm>
<messageDigest>{dig}</messageDigest><messageDigestOriginator>FDsys</messageDigestOriginator></fixity>
</objectCharacteristics><originalName>FR-1975-01-02.pdf</originalName></object>
<object><objectIdentifier><objectIdentifierValue>R2</objectIdentifierValue></objectIdentifier>
<originalName>other.xml</originalName></object>
""" + ("<object><originalName>filler.txt</originalName></object>\n" * 5000) + "</premis>"
A, B = "a" * 64, "b" * 64


def chunked(text, size=1000):
    data = text.encode()
    state = {"served": 0}

    def gen():
        for i in range(0, len(data), size):
            state["served"] += 1
            yield data[i:i + size]
    return gen(), state


class Scan(unittest.TestCase):
    def test_finds_digest_and_stops_early(self):
        chunks, state = chunked(PREMIS.format(dig=A))
        alg, dig, read = fixity.scan_premis(chunks, "FR-1975-01-02.pdf")
        self.assertEqual((alg, dig), ("SHA-256", A))
        self.assertLess(read, 2000)              # stopped after the first object, not 200 KB in
        self.assertLess(state["served"], 3)

    def test_not_listed_stops_after_cap(self):
        chunks, _ = chunked(PREMIS.format(dig=A) * 3)
        alg, dig, read = fixity.scan_premis(chunks, "94-32388.pdf", max_bytes=50_000)
        self.assertEqual((alg, dig), (None, None))
        self.assertLess(read, 60_000)

    def test_prefixed_tags(self):
        text = "<premis:object><premis:messageDigestAlgorithm>SHA-256</premis:messageDigestAlgorithm>" \
               f"<premis:messageDigest>{A.upper()}</premis:messageDigest><premis:originalName>x.pdf" \
               "</premis:originalName></premis:object>"
        self.assertEqual(fixity.scan_premis(iter([text.encode()]), "x.pdf")[1], A)

    def test_split_url(self):
        self.assertEqual(fixity.split_url("https://www.govinfo.gov/content/pkg/FR-1975-01-02/pdf/FR-1975-01-02.pdf#page=4"),
                         ("FR-1975-01-02", "FR-1975-01-02.pdf"))
        self.assertIsNone(fixity.split_url("https://www.federalregister.gov/d/1"))


class CheckAndRun(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, True)
        out = self.repo / "jobs/fr-originals/data/full_run"
        out.mkdir(parents=True)
        url = "https://www.govinfo.gov/content/pkg/FR-1975-01-02/pdf/FR-1975-01-02.pdf"
        recs = [{"url": url, "sha256": A, "instrument_ids": ["EO:11829"]},
                {"url": url, "sha256": A, "instrument_ids": ["EO:11830"]},
                {"url": "https://www.govinfo.gov/content/pkg/FR-1995-01-03/pdf/94-32388.pdf", "sha256": B,
                 "instrument_ids": ["EO:12945"]},
                {"url": "https://www.govinfo.gov/content/pkg/FR-1962-03-06/pdf/FR-1962-03-06.pdf", "sha256": B,
                 "instrument_ids": ["EO:11000"], "sha256_is_of_url_bytes": False}]
        (out / "SOURCES.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
        self.calls = []

    def opener(self, url):
        self.calls.append(url)
        if "FR-1995" in url:
            return iter([PREMIS.format(dig=B).replace("FR-1975-01-02.pdf", "FR-1995-01-03.pdf").encode()])
        return iter([PREMIS.format(dig=A).encode()])

    def test_collect_merges_orders_and_skips_excerpts(self):
        items = fixity.collect_sources(self.repo)
        self.assertEqual([i["filename"] for i in items], ["FR-1975-01-02.pdf", "94-32388.pdf"])
        self.assertEqual(items[0]["ids"], {"EO:11829", "EO:11830"})

    def test_run_classifies_and_carries_forward(self):
        out = self.repo / "out"
        s = fixity.run(self.repo, out, workers=2, open_chunks=self.opener, log=lambda *a: None)
        self.assertEqual(s["results"], {"match": 1, "not_listed": 1})
        self.assertFalse(any("FR-1995" in c for c in self.calls))  # granules are never fetched
        self.assertEqual(s["orders_with_a_gpo_matched_file"], 2)
        with open(out / "FIXITY.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.calls.clear()
        s2 = fixity.run(self.repo, self.repo / "out2", prior_rows=rows, workers=2, open_chunks=self.opener,
                        log=lambda *a: None)
        self.assertEqual((s2["checked_this_run"], s2["carried_forward"]), (0, 2))
        self.assertEqual(self.calls, [])        # nothing re-requested
        with open(self.repo / "out2" / "MATCHED_BY_SHA256.json", encoding="utf-8") as fh:
            self.assertIn(A, json.load(fh))

    def test_mismatch_and_unavailable(self):
        it = {"url": "u", "package": "FR-1975-01-02", "filename": "FR-1975-01-02.pdf", "shas": {B}, "ids": set(),
              "found_in": set()}
        self.assertEqual(fixity.check_one(it, lambda url: iter([PREMIS.format(dig=A).encode()]))["result"], "mismatch")

        def boom(url):
            raise urllib.error.HTTPError(url, 503, "busy", {}, None)
        row = fixity.check_one(it, boom, retries=1, sleep=lambda s: None)
        self.assertEqual(row["result"], "unavailable")

        def gone(url):
            raise urllib.error.HTTPError(url, 404, "nope", {}, None)
        self.assertEqual(fixity.check_one(it, gone, sleep=lambda s: None)["result"], "no_premis_record")


if __name__ == "__main__":
    unittest.main()
