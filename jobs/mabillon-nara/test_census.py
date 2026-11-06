"""Offline tests for the NARA census: S3 paging, schema-agnostic reading, number parsing, coverage."""
import io
import os
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import census  # noqa: E402

LIST1 = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>true</IsTruncated>
<NextContinuationToken>tok</NextContinuationToken>
<Contents><Key>descriptions/record-groups/rg_11/rg_11-1.jsonl</Key><Size>10</Size><ETag>"a"</ETag></Contents>
</ListBucketResult>"""
LIST2 = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>false</IsTruncated>
<Contents><Key>descriptions/record-groups/rg_11/rg_11-2.jsonl</Key><Size>20</Size><ETag>"b"</ETag></Contents>
</ListBucketResult>"""

SERIES = {"title": "Executive Orders", "naId": 100, "levelOfDescription": "series"}
REC_ITEM = {"record": {"naId": 1, "title": "Executive Order 1234-A", "levelOfDescription": "item",
                       "ancestors": [SERIES], "digitalObjects": [
                           {"objectUrl": "https://s3.amazonaws.com/NARAprodstorage/x/1.jpg", "objectType": "Image (JPG)"}]}}
REC_BARE = {"naId": 2, "title": "No. 77", "levelOfDescription": "item", "ancestors": [SERIES]}
REC_OTHER = {"naId": 3, "title": "Treaty with Spain", "levelOfDescription": "item",
             "ancestors": [{"title": "Treaties", "naId": 9, "levelOfDescription": "series"}]}
REC_RANGE = {"naId": 4, "title": "Executive Orders 5000-5100", "levelOfDescription": "fileUnit", "ancestors": [SERIES],
             "digitalObjects": [{"objectUrl": "https://example.gov/f.pdf"}]}
CHUNK1 = "\n".join(json.dumps(r) for r in (REC_ITEM, REC_OTHER)).encode()
CHUNK2 = "\n".join(json.dumps(r) for r in (REC_BARE, REC_RANGE)).encode()


class FakePool:
    def __init__(self):
        self.requests = 0
        self.bytes_downloaded = 0

    def fetch(self, url):
        self.requests += 1
        if "delimiter" in url:
            body = (b'<?xml version="1.0"?><ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                    b'<CommonPrefixes><Prefix>descriptions/record-groups/rg_010/</Prefix></CommonPrefixes>'
                    b'<CommonPrefixes><Prefix>descriptions/record-groups/rg_11/</Prefix></CommonPrefixes>'
                    b'</ListBucketResult>')
        elif "continuation-token=tok" in url:
            body = LIST2
        elif "list-type" in url:
            body = LIST1
        elif url.endswith("rg_11-1.jsonl"):
            body = CHUNK1
        elif url.endswith("rg_11-2.jsonl"):
            body = CHUNK2
        else:
            raise RuntimeError("HTTP 404")
        return {"url": url, "sha256": "x" * 64, "bytes": len(body), "body": body}

    def map(self, f, items):
        return [f(i) for i in items]


class CensusTests(unittest.TestCase):
    def test_group_folders_match_by_number(self):
        self.assertEqual(census.resolve_groups(FakePool(), ["11", "10", "59"]),
                         [(11, "descriptions/record-groups/rg_11/"), (10, "descriptions/record-groups/rg_010/")])

    def test_numbers(self):
        self.assertEqual(census.numbers_in("Executive Order No. 1234")[0], [(1234, "")])
        self.assertEqual(census.numbers_in("Executive Order 1234-A")[0], [(1234, "A")])
        self.assertEqual(census.numbers_in("E.O. 77")[0], [(77, "")])
        self.assertEqual(census.numbers_in("Executive Orders 5000-5100")[1], [(5000, 5100)])
        self.assertEqual(census.numbers_in("Treaty with Spain")[0], [])

    def test_unwrap_and_objects(self):
        rec = census.unwrap(REC_ITEM)
        self.assertEqual(rec["naId"], 1)
        objs = census.digital_objects(rec)
        self.assertEqual(objs[0]["url"], "https://s3.amazonaws.com/NARAprodstorage/x/1.jpg")
        self.assertTrue(census.is_eo(REC_BARE))
        self.assertFalse(census.is_eo(REC_OTHER))

    def test_main_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            frame = Path(d) / "FRAME.csv"
            frame.write_text("instrument_id,number,band,era,best_held\nEO:1234A,1234,01000-01499,x,y\n"
                             "EO:77,77,00000-00499,x,y\nEO:5050,5050,05000-05499,x,y\nEO:9,9,00000-00499,x,y\n")
            old = census.FRAME
            census.FRAME = frame
            os.environ["NARA_RECORD_GROUPS"] = "11"
            try:
                s = census.main(out=Path(d) / "out", pool=FakePool())
            finally:
                census.FRAME = old
            self.assertEqual(s["chunks_read"], 2)
            self.assertEqual(s["eo_records"], 3)
            self.assertEqual(s["frame_item_described"], 2)      # 1234A by title, 77 by bare number under EO series
            self.assertEqual(s["frame_item_with_objects"], 1)   # only 1234A has an image
            self.assertEqual(s["frame_range_with_objects"], 1)  # 5050 by the file unit's range
            cov = (Path(d) / "out/FRAME_COVERAGE.csv").read_text()
            self.assertIn("EO:9,9", cov)


if __name__ == "__main__":
    unittest.main()
