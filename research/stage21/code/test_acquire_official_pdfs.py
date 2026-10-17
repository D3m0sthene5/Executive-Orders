import unittest
from acquire_official_pdfs import filename_for,selected,validate_pdf

class SourceFetcherTests(unittest.TestCase):
    def test_no_guessed_sources(self):
        a=[{"instrument_id":"EO:10001","format":"pdf_url",
            "literal_url":"https://www.govinfo.gov/content/pkg/FR-1949/pdf/10001.pdf"}]
        self.assertEqual(len(selected(a)),1)
        with self.assertRaises(ValueError):
            selected([{"instrument_id":"EO:10001","format":"pdf_url",
                "literal_url":"https://bad.example/content/pkg/10001.pdf"}])
        with self.assertRaises(ValueError):
            selected(a+a)
    def test_pdf_header_and_end_marker(self):
        b=b"%PDF-1.5\n"+b"a"*405+b"\n%%EOF\n"
        self.assertEqual(len(validate_pdf(b)),64)
        with self.assertRaises(ValueError):
            validate_pdf(b"%PDF-1.4\n"+b"a"*405)
    def test_safe_filename(self):
        self.assertEqual(filename_for("EO:7784A"),"EO_7784A.pdf")
        with self.assertRaises(ValueError):
            filename_for("EO:../../escape")

if __name__=="__main__":
    unittest.main()
