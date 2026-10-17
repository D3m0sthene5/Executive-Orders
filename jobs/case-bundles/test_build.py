import json,tempfile,unittest
from pathlib import Path
from build import run,bounded,canon,LIMIT
class BundleTests(unittest.TestCase):
    def test_repeat_bytes_size_and_content(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); drafts=root/'jobs/claim-drafts/output';drafts.mkdir(parents=True)
            (drafts/'DRAFT_CLAIMS.jsonl').write_text(json.dumps({'instrument_id':'EO:10','claim':{},'_draft':{'gate':{'errors_now':['needs_review']}}})+'\n')
            p=root/'research/progress';p.mkdir(parents=True);(p/'DECIDED_CASE_COMPLETENESS_RECONCILED.csv').write_text('instrument_id\nEO:10\n')
            out=root/'out';rows=run(root,out);b=(out/rows[0]['path']).read_bytes();run(root,out)
            self.assertEqual(b,(out/rows[0]['path']).read_bytes());self.assertLess(len(b),30000)
            self.assertEqual(json.loads(b)['gate_errors'],['needs_review'])
    def test_oversized_draft_is_explicit(self):
        p={'instrument_id':'EO:1','draft_record':{'path':'draft.jsonl','line':1},'claim_draft':{'text':'a'*80000},'fragments':[], 'later_events':[], 'current_law_hits':[], 'conflicts':[], 'text_pointers':[]}
        q=bounded(p);self.assertLessEqual(len((canon(q)+'\n').encode()),LIMIT);self.assertIn('claim_draft',q['overflow']);self.assertIn('record',q['claim_draft'])
    def test_unicode_budget(self):
        p={'instrument_id':'EO:1','draft_record':{},'claim_draft':{'text':'漢'*50000},'fragments':[],'later_events':[],'current_law_hits':[],'conflicts':[],'text_pointers':[]}
        self.assertLess(len(canon(bounded(p)).encode()),30000)
if __name__=='__main__':unittest.main()
