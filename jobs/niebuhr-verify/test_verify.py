import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify  # noqa: E402


class Fake:
    def __init__(self, pages):
        self.pages = pages

    def __call__(self, url, headers, timeout):
        if url.endswith("/robots.txt"):
            return 200, {"content-type": "text/plain"}, io.BytesIO(b"User-agent: *\nAllow: /\n")
        if url in self.pages:
            return 200, {"content-type": "text/html"}, io.BytesIO(self.pages[url].encode())
        return 404, {}, io.BytesIO(b"")


class Verify(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_quote_folding(self):
        self.assertEqual(verify.quote_on_page("Alaska  Townsite Withdrawal No. 5", "<p>alaska townsite withdrawal no 5 established</p>")[0], "exact")
        self.assertEqual(verify.quote_on_page("one two three four five six", "one two three four zzz")[0], "partial")
        self.assertEqual(verify.quote_on_page("nothing here at all", "different words")[0], "no")
        self.assertEqual(verify.quote_on_page("", "x")[0], "no_quote")

    def test_run_checks_each_source_and_holds_text(self):
        root = os.path.join(self.tmp, "repo")
        d = os.path.join(root, "research", "niebuhr", "results")
        os.makedirs(d)
        rec = {"target_id": "EO:2103", "outcome": "identified_no_text", "sources": [
            {"url": "https://a.test/p", "kind": "secondary", "quote": "Alaska Townsite Withdrawal No. 5"},
            {"url": "https://a.test/missing", "kind": "secondary", "quote": "x"}]}
        with open(os.path.join(d, "b01.jsonl"), "w") as fh:
            fh.write(json.dumps(rec) + "\n\nnot json\n")
        out = os.path.join(self.tmp, "out")
        s = verify.run(root, out, os.path.join(self.tmp, "c"),
                       transport=Fake({"https://a.test/p": "<html><body>EO 2103: Alaska Townsite Withdrawal No. 5 established.</body></html>"}))
        self.assertEqual(s["sources_checked"], 2)
        self.assertEqual(s["quote_check"], {"exact": 1, "page_not_fetched": 1})
        self.assertEqual(s["targets_with_an_exact_quote"], 1)
        self.assertEqual(len(os.listdir(os.path.join(out, "pages"))), 1)


if __name__ == "__main__":
    unittest.main()
