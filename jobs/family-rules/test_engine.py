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
if __name__ == '__main__': unittest.main()
