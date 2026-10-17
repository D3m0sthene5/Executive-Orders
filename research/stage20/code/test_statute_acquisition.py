import io
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from acquire_shared_statutes import sha_bytes, cited_statutes, summarize, download_source

class FetchTest(unittest.TestCase):
 def test_reject_html_even_with_success_status(self):
  class Page(io.BytesIO):
   status=200
   def __init__(self,url,body):super().__init__(body);self.url=url
   def geturl(self):return self.url
   def __enter__(self):return self
   def __exit__(self,*a):self.close()
  url='https://www.govinfo.gov/content/pkg/STATUTE-70/pdf/STATUTE-70-Pg786.pdf'
  with patch('acquire_shared_statutes.urllib.request.urlopen',return_value=Page(url,b'<html>error</html>')):
   with self.assertRaises(ValueError):download_source(url)
  with patch('acquire_shared_statutes.urllib.request.urlopen',return_value=Page(url,b'%PDF-1.4\nfixture\n%%EOF')):
   self.assertEqual(download_source(url)[:5],b'%PDF-')
 def test_citation_frame_exact_and_reproducible(self):
  rows=cited_statutes()
  self.assertEqual(len(rows),10)
  self.assertIn('https://www.govinfo.gov/content/pkg/STATUTE-70/pdf/STATUTE-70-Pg786.pdf',[x['source_url'] for x in rows])
  self.assertEqual(summarize([])['original_source_authority_or_legal_effect_human_verified'],0)
if __name__=='__main__':unittest.main()
