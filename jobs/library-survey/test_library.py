import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("survey",str(Path(__file__).with_name("job.py")))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class TestRouting(unittest.TestCase):
 def test_ocr_selective(self):
  self.assertTrue(module.ocr_needed("","",True))
  self.assertFalse(module.ocr_needed("","",False))
  self.assertFalse(module.ocr_needed("Searchable text "*15,"",True))
 def test_input_needs(self):
  self.assertTrue((Path(__file__).parent/"needs.txt").is_file())
if __name__=="__main__":unittest.main()
