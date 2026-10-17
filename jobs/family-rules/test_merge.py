import importlib.util,sys,tempfile,unittest,json
from pathlib import Path
class MergeTests(unittest.TestCase):
    def test_family_certificates_are_discovered_without_status_fill(self):
        p=Path(__file__).resolve().parents[1]/'claim-drafts/drafts.py'
        spec=importlib.util.spec_from_file_location('road_drafts',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertIn('family_rule_checks',m.FRAGMENT_KINDS)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'jobs/family-rules/output';out.mkdir(parents=True)
            (out/'FRAGMENTS.jsonl').write_text(json.dumps({'instrument_id':'EO:10','kind':'family_rule_checks','data':{'result':'blocked'},'produced_by':'family-rules'})+'\n')
            ins,notes=m.discover_inputs(root,None);merged=m.load_inputs(ins)
            self.assertEqual(merged.frags['EO:10']['family_rule_checks'][0][1]['data']['result'],'blocked')
            self.assertNotIn('whole_order_end_candidates',merged.frags['EO:10'])
if __name__=='__main__':unittest.main()
