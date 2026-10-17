import importlib.util,tempfile,unittest,json
from pathlib import Path
sp=importlib.util.spec_from_file_location("reg",str(Path(__file__).with_name("job.py")))
mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
class TestIdentity(unittest.TestCase):
 def test_exact_item_identity(self):
  self.assertEqual(mod.item_id("https://www.loc.gov/item/mjm017456/?fo=json"),"mjm017456")
  self.assertIsNone(mod.item_id("https://www.loc.gov/resource/mjm.17/"))
 def test_separate_same_date(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for k,p in mod.INPUTS.items():(root/p).parent.mkdir(parents=True,exist_ok=True)
   def w(k,data):(root/mod.INPUTS[k]).write_text(data,encoding="utf-8")
   w("curated",json.dumps([{"candidate_id":"M","item_url":"https://www.loc.gov/item/mjm017456/","date_as_cataloged":"1814-08-13"}]))
   w("item_metadata","\n".join(json.dumps({"catalog_item_id":a,"item_date":"1814-08-13","status":"official_item_JSON_retrieved"}) for a in ("mjm017456","mjm017468")))
   w("page_images","catalog_item,source_state,stored_path\n")
   w("lord","candidate_id\nLORD:1\n")
   w("early_sources","candidate_id,primary_source_url,date\nR1,https://www.loc.gov/resource/xyz/,1814-08-13\n")
   w("census","id\nEO:1\n")
   result_path=root/"out";mod.build(root,result_path)
   d=json.loads((result_path/"SUMMARY.json").read_text())
   self.assertEqual(d["distinct_LOC_item_ID_candidates"],2)
   self.assertEqual(d["newly_admitted_EOs"],0)
   self.assertTrue(d["no_date_only_identity_merges"])
if __name__=="__main__":unittest.main()
