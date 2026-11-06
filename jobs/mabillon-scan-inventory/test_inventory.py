import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import inventory as I  # noqa: E402

CAT = (b'<a href="/wiki/Category:Executive_orders_of_Woodrow_Wilson">x</a>'
       b'<a href="/wiki/File:Executive_Orders_6071-6250.djvu">f</a><a href="/wiki/File:Map.png">m</a>')
SUB = b'<a href="/wiki/File:Executive_Orders_2000-2200.pdf">g</a>'
IA = json.dumps({"response": {"docs": [{"identifier": "eo1", "title": "Executive orders nos. 100-300",
                                         "date": "1910"}]}}).encode()


class Pool:
    requests = 0

    def fetch(self, url):
        self.requests += 1
        body = IA if "advancedsearch" in url else SUB if "Woodrow" in url else CAT
        return {"body": body}


class T(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(I.ranges_in("File:Executive_Orders_6071-6250.djvu"), [(6071, 6250)])
        self.assertEqual(I.ranges_in("Executive orders nos. 100 to 300"), [(100, 300)])
        self.assertEqual(I.ranges_in("Report 1910-1911"), [])

    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            I.FRAME = Path(d) / "F.csv"
            I.FRAME.write_text("instrument_id,number\nEO:150,150\nEO:2100,2100\nEO:6100,6100\n")
            s = I.main(out=Path(d) / "o", pool=Pool())
            self.assertEqual(s["commons_files"], 2)
            self.assertEqual(s["frame_orders_below_5076_inside_a_listed_range"], 2)


if __name__ == "__main__":
    unittest.main()
