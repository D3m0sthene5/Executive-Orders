"""Offline tests: a fake govinfo link service and a small real PDF fixture."""
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
import statutes  # noqa: E402

PDF = (HERE / "fixtures" / "statute.pdf").read_bytes()
GRAN = "https://www.govinfo.gov/content/pkg/STATUTE-48/pdf/STATUTE-48-Pg195.pdf"


def transport(url, headers, timeout):
    p = urllib.parse.urlsplit(url)
    if p.path == "/robots.txt":
        return 404, {}, io.BytesIO(b"")
    if p.path in ("/link/statute/48/195", "/link/statute/73/public/67"):
        return 302, {"location": GRAN}, io.BytesIO(b"")
    if p.path == "/content/pkg/STATUTE-48/pdf/STATUTE-48-Pg195.pdf":
        return 200, {"content-length": str(len(PDF))}, io.BytesIO(PDF)
    return 404, {}, io.BytesIO(b"")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class Statutes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.repo = Path(self.tmp.name) / "repo"
        base = {"text_evidence_tier": "original_supported", "provisional_status": "no",
                "step_ending_or_current_basis": "open"}
        write_csv(r / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
                  [dict(base, instrument_id="EO:6205"), dict(base, instrument_id="EO:6595")])
        write_csv(r / "jobs/later-events/output/EDGES.csv",
                  [{"acting_id": "STAT:48-195", "target_id": "EO:6205", "mechanism": "ratification",
                    "acting_label": "Act of June 16, 1933 (48 Stat. 195)"},
                   {"acting_id": "PL:73-67", "target_id": "EO:9999", "mechanism": "repeal", "acting_label": ""}])
        order = r / "jobs/fr-originals/output/texts/EO_6595.txt"
        order.parent.mkdir(parents=True)
        order.write_text("By virtue of the authority vested in me by title I of the National Industrial Recovery Act "
                         "(48 Stat. 195), I hereby order as follows. Sec. 2. Done.")
        (r / "jobs/fr-originals/output/FRAGMENTS.jsonl").write_text(json.dumps(
            {"instrument_id": "EO:6595", "kind": "original_representation",
             "data": {"text_path": "texts/EO_6595.txt", "sha256": "0" * 64, "url": "https://x"}}) + "\n")
        self.out = Path(self.tmp.name) / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def test_end_to_end(self):
        s = statutes.main(self.repo, self.out, Path(self.tmp.name) / "cache", transport=transport,
                          env={"JOB_WORKERS": "2"})
        self.assertEqual(s["held"], 1)
        self.assertEqual(s["page_number_printed"], 1)
        self.assertEqual(s["orders_with_held_basis_statute"], 1)
        src = json.loads((self.out / "SOURCES.jsonl").read_text().splitlines()[0])
        self.assertEqual(statutes.S.sha256((self.out / src["cache_path"]).read_bytes()), src["sha256"])
        self.assertEqual(src["sha256"], statutes.S.sha256(PDF))
        self.assertIn("EO:6595", src["instrument_ids"])
        basis = json.loads((self.out / "BASIS.jsonl").read_text().splitlines()[0])
        order_text = (self.repo / basis["order_text_path"]).read_text()
        lo, hi = map(int, basis["quote_span"].split("-"))
        self.assertEqual(order_text[lo:hi], basis["quote"])
        self.assertIn("48 Stat. 195", basis["quote"])
        frag = json.loads((self.out / "FRAGMENTS.jsonl").read_text().splitlines()[0])["data"][0]
        self.assertEqual(frag["target_id"], "EO:6205")
        text = (self.out / frag["text_path"]).read_text()
        lo, hi = map(int, frag["quote_span"].split("-"))
        self.assertEqual(text[lo:hi], frag["quote"])


if __name__ == "__main__":
    unittest.main()
