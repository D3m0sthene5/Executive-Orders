import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("retention", Path(__file__).with_name("job.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RequestBoundary(unittest.TestCase):
    def setUp(self):
        self.item = {"url":"https://www.govinfo.gov/example.pdf", "instrument_ids":["EO:1"], "pages":[1,2], "expected_sha256":"a"*64}
        self.queue = [{"instrument_id":"EO:1", "urls":[self.item["url"]]}]

    def test_exact_queue_pair_required(self):
        module.validate_manifest([self.item], self.queue)
        with self.assertRaises(ValueError):
            module.validate_manifest([{**self.item, "instrument_ids":["EO:2"]}], self.queue)

    def test_https_and_duplicate_boundary(self):
        with self.assertRaises(ValueError):
            module.validate_manifest([{**self.item, "url":"http://www.govinfo.gov/example.pdf"}], self.queue)
        with self.assertRaises(ValueError):
            module.validate_manifest([self.item, self.item], self.queue)

    def test_page_and_hash_boundary(self):
        for pages in ([0], [True], [1.5], list(range(1,42))):
            with self.assertRaises(ValueError):
                module.validate_manifest([{**self.item, "pages":pages}], self.queue)
        with self.assertRaises(ValueError):
            module.validate_manifest([{**self.item, "expected_sha256":"not-a-hash"}], self.queue)

    def test_run_bound(self):
        with self.assertRaises(ValueError):
            module.validate_manifest([self.item]*31, self.queue)


if __name__ == "__main__":
    unittest.main()
