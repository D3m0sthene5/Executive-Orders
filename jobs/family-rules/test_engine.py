import copy, tempfile, unittest
from pathlib import Path
from engine import assess, rule_errors, digest

class ProofTests(unittest.TestCase):
    def setUp(self):
        self.rule = {'acting_id':'EO:20','review_state':'source_reviewed','mechanism':'revocation', 'effective_date':'1950-01-01',
            'scope':{'kind':'explicit_targets','targets':['EO:10']},'target_scope_reviewed':['EO:10'], 'exceptions_savings':{'reviewed':True,'leads':[]}}
        self.edge = {'edge_id':'LE-test','acting_id':'EO:20','target_id':'EO:10','mechanism':'revocation','qualifier':'','date_candidate':'1950-01-01'}
    def check(self, **kw):
        args = dict(rule=self.rule, target='EO:10', edges=[self.edge], texts=['All instructions end.'], mentions=[], sweep=[], errors=[])
        args.update(kw); return assess(**args)
    def test_positive_is_only_bounded(self): self.assertEqual(self.check()['result'],'bounded_checks_passed')
    def test_any_qualifier_blocks(self):
        for qualifier in ['section 2','unknown scope','as amended']:
            self.assertIn('QUALIFIED_OR_CONFLICTING_SCOPE',self.check(edges=[dict(self.edge, qualifier=qualifier)])['blockers'])
    def test_current_law_blocks(self): self.assertIn('CURRENT_LAW_USE_LEAD',self.check(mentions=[{'date':'2026-01-01'}])['blockers'])
    def test_counterexample_blocks(self): self.assertIn('LATER_OR_UNDATED_SAVED_TEXT_USE',self.check(sweep=[{'text_path':'later.txt'}])['blockers'])
    def test_date_conflict(self): self.assertIn('DATE_CONFLICT_OR_UNKNOWN',self.check(edges=[dict(self.edge,date_candidate='1951-01-01')])['blockers'])
    def test_earlier_end(self): self.assertIn('EARLIER_OR_UNDATED_ENDING',self.check(edges=[self.edge,dict(self.edge,acting_id='EO:15',date_candidate='1940-01-01')])['blockers'])
    def test_savings(self): self.assertIn('INDEPENDENT_CLAUSE_OR_SAVINGS_LEAD',self.check(texts=['Except pending proceedings.'])['blockers'])
    def test_missing_text(self): self.assertIn('TARGET_ORIGINAL_TEXT_MISSING',self.check(texts=[])['blockers'])
    def test_unreviewed_clause(self):
        r=copy.deepcopy(self.rule); r['target_scope_reviewed']=[]
        self.assertIn('TARGET_INDEPENDENT_CLAUSES_UNREVIEWED',self.check(rule=r)['blockers'])
    def test_scope(self):
        r=copy.deepcopy(self.rule);r['scope']['targets']=[]
        self.assertIn('TARGET_OUTSIDE_RULE_SCOPE',self.check(rule=r)['blockers'])
    def test_exact_quote_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); raw=b'Orders 10 and 11 are revoked.';(root/'text.txt').write_bytes(raw)
            r=dict(self.rule, quoted_clause=raw.decode(),source={'original_custody_verified':True,'url':'https://example.org','sha256':'a'*64,'page':'2','text_path':'text.txt','text_sha256':digest(raw)})
            self.assertEqual(rule_errors(r,root),[])
            r['quoted_clause']='Orders 10 are revoked.'
            self.assertIn('RULE_QUOTE_NOT_EXACT',rule_errors(r,root))
            r['source']['text_path']='../escape'
            self.assertIn('RULE_TEXT_UNAVAILABLE',rule_errors(r,root))
class CorpusDateTests(unittest.TestCase):
    def test_old_citation_does_not_date_an_unregistered_compilation(self):
        from engine import run, write
        from unittest.mock import patch
        import json
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'result'
            p=root/'jobs/later-events/output';p.mkdir(parents=True)
            (p/'EDGES.csv').write_text('edge_id,acting_id,target_id,mechanism,qualifier,date_candidate\nLE-1,EO:20,EO:10,revocation,,1950-01-01\n')
            (p/'CATALOG_INDEX.csv').write_text('id,signing_date\nEO:10,1940-01-01\n')
            p=root/'jobs/current-law';p.mkdir(parents=True)
            original=Path(__file__).resolve().parents[1]/'current-law/eo_refs.py'
            (p/'eo_refs.py').write_bytes(original.read_bytes())
            p=root/'jobs/mixed/output/texts';p.mkdir(parents=True)
            (p/'modern.txt').write_text('Executive Order 10 is discussed in this undated compilation.')
            rule={'acting_id':'EO:20','mechanism':'revocation','effective_date':'1950-01-01','scope':{'kind':'explicit_targets','targets':['EO:10']}}
            write(root/'research/readiness/rules/EO_20.json',rule)
            with patch.dict('sys.modules',{'tiktoken':None}):certs=run(root,out)
            self.assertEqual(certs[0]['counterexample_count'],1)
            self.assertIn('LATER_OR_UNDATED_SAVED_TEXT_USE',certs[0]['blockers'])

if __name__ == '__main__': unittest.main()
