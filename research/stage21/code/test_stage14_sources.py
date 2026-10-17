import unittest
from attach_stage14_sources import crosswalk,safe_source

class IndexTest(unittest.TestCase):
    def test_literal_government_urls_only(self):
        self.assertTrue(safe_source({"field":"pdf_url","url":"https://www.govinfo.gov/content/pkg/FR-1949/pdf/FR-1949.pdf"}))
        self.assertFalse(safe_source({"field":"pdf_url","url":"https://bad.example/content/pkg/FR-1949.pdf"}))
    def test_no_auto_legal_conclusion(self):
        m=[{"instrument_id":"EO:10005","field":"pdf_url",
            "url":"https://www.govinfo.gov/content/pkg/FR-1949/pdf/FR-1949.pdf",
            "signing_date":"1948-10-05","citation":"13 FR 100"}]
        d=[{"instrument_id":"EO:10005","whole_lifecycle_completed":"no",
            "provisional_status":"no","research_triage_not_confidence":"15"}]
        joins,requests,stats=crosswalk(m,d,{},strict=False)
        self.assertEqual(stats["provisional_cases_with_direct_OFFICIAL_URLs"],1)
        self.assertEqual(joins[0]["document_identity_authenticated"],"no")
        self.assertEqual(stats["human_certified_dossiers"],0)
    def test_duplicated_provenance_rejected(self):
        m=[{"instrument_id":"EO:10005","field":"pdf_url",
            "url":"https://www.govinfo.gov/content/pkg/FR-1949/pdf/FR-1949.pdf"}]
        d=[{"instrument_id":"EO:10005","whole_lifecycle_completed":"no",
            "provisional_status":"no"}]
        with self.assertRaises(ValueError):
            crosswalk(m+m,d,{},strict=False)

if __name__=="__main__":
    unittest.main()
