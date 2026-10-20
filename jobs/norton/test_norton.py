import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).parent))
from model import (application_errors, evidence_errors, fingerprint, question_key, review_errors, sha, source_span)
from norton import compile_reviews, possible_duplicates, search_sources

ROOT = Path(__file__).resolve().parents[2]

class FactualBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name)
        self.text=('Harbor Commission submitted the harbor survey report on January 15, 1983.\n\n'
                   'The harbor survey function of Harbor Commission is transferred to Coastal Office, except port licensing.\n')
        (self.repo/'text.txt').write_text(self.text)
        (self.repo/'raw.html').write_bytes(self.text.encode())
        self.src={'url':'https://example.gov/report','sha256':sha(self.text),'text_path':'text.txt',
                  'text_sha256':sha(self.text),'raw_path':'raw.html','page_or_item':'transmittal page 1',
                  'primary':True,'edition':'1983 original','route':'held_primary','retrieved_utc':'2026-10-20T15:00:00Z'}
        self.q={'entity_id':'Harbor Commission established 1981','object':'harbor survey report',
                'scope':'final report to President','interval_start':'1981-01-01','interval_end':'1983-12-31',
                'proposition':'Was this final report delivered to the President, and on what date?', 'event_kind':'report_delivery'}
        self.q['question_key']=question_key(self.q)
        self.e={'id':'NE:1','question_key':self.q['question_key'],'event_kind':'report_delivery',
                'entity_id':self.q['entity_id'],'source':self.src,'char_start':0,'char_end':len(self.text),
                'text':self.text,'event_date':'1983-01-15'}
        self.e['instrument_id']='EO:1'
        self.app={'id':'NA:1','question_key':self.q['question_key'],'instrument_id':'EO:1','scope_id':'EO:1#sec2',
                  'legal_effect':'unresolved','state':'candidate','producer':'producer-a','clause_evidence':self.e}

    def test_exact_key_keeps_every_dimension(self):
        for k,v in [('entity_id','Harbor Commission established 1946'),('object','harbor progress report'),
                    ('scope','report to Congress'),('interval_start','1982-01-01'),('interval_end','1983-11-30'),
                    ('proposition','Was it published?'),('event_kind','report_publication')]:
            q=dict(self.q,**{k:v});self.assertNotEqual(question_key(q),question_key(self.q),k)

    def test_no_fuzzy_or_case_merge(self):
        q=dict(self.q,object='Harbor Survey Report')
        self.assertNotEqual(question_key(q),question_key(self.q))

    def test_deadline_and_publication_are_not_delivery(self):
        for kind in ['report_publication','appointment','recurring_performance']:
            self.assertIn('event_kind_mismatch',evidence_errors(self.repo,self.q,dict(self.e,event_kind=kind)))
        self.assertIn('event_date_outside_interval_or_unknown',evidence_errors(self.repo,self.q,dict(self.e,event_date=None)))

    def test_wrong_entity(self):
        self.assertIn('entity_mismatch',evidence_errors(self.repo,self.q,dict(self.e,entity_id='Harbor Commission 1946')))

    def test_wrong_historical_edition(self):
        self.assertIn('wrong_historical_edition',evidence_errors(self.repo,dict(self.q,edition_required='1981 original'),self.e))

    def test_stale_source_cannot_prove_current_performance(self):
        q=dict(self.q,event_kind='recurring_performance',interval_end='2026-10-14');q['question_key']=question_key(q)
        e=dict(self.e,event_kind=q['event_kind'],question_key=q['question_key'])
        self.assertIn('performance_coverage_gap',evidence_errors(self.repo,q,e))

    def test_source_bytes_and_text_hashes(self):
        self.assertEqual([],evidence_errors(self.repo,self.q,self.e))
        (self.repo/'raw.html').unlink()
        self.assertIn('source_bytes_not_held',evidence_errors(self.repo,self.q,self.e))
        (self.repo/'text.txt').write_text('stale')
        self.assertIn('text_hash_mismatch',source_span(self.repo,self.e))

    def test_review_does_not_allow_self_review_or_changed_answer(self):
        r={'producer':'producer-a','id':'NFA:1'}
        review={'schema':'norton-factual-review/v1','record_kind':'answer','record_sha256':fingerprint(r),
                'reviewer_type':'independent_ai','reviewer':'reviewer-b','independent':True,'decision':'uphold',
                'reviewed_on':'2026-10-20','rationale':'Read the held transmittal and tested the named addressee and date.', 'd6_searched':True}
        self.assertEqual([],review_errors(self.repo,r,review,'answer'))
        self.assertIn('review_not_independent',review_errors(self.repo,r,dict(review,reviewer='producer-a'),'answer'))
        self.assertIn('changed_after_review',review_errors(self.repo,dict(r,id='changed'),review,'answer'))

    def test_applicability_requires_all_five_per_clause_checks(self):
        self.assertEqual([],application_errors(self.repo,self.q,self.app))
        self.assertEqual(5,len([e for e in application_errors(self.repo,self.q,dict(self.app,state='ai_reviewed')) if e.startswith('unsupported_applicability')]))
        self.assertIn('factual_record_cannot_decide_legal_effect',application_errors(self.repo,self.q,dict(self.app,legal_effect='terminated')))

    def test_reviewed_answer_never_automatically_reviews_application(self):
        data={k:[] for k in ['reviews','evidence','answers','applications']}
        data['applications']=[dict(self.app,state='ai_reviewed',_origin={})]
        answers,apps,rejected=compile_reviews(self.repo,data,[self.q])
        self.assertFalse(apps);self.assertIn('reviewed_answer_missing',rejected[0]['errors'])

    def test_wrong_clause_order_and_duplicate_application_are_rejected(self):
        self.assertIn('clause_evidence_wrong_order',application_errors(self.repo,self.q,dict(self.app,instrument_id='EO:2',scope_id='EO:2#sec2')))
        r=dict(self.app,_origin={})
        data={'reviews':[],'evidence':[],'answers':[],'applications':[r,r]}
        _,apps,rejections=compile_reviews(self.repo,data,[self.q])
        self.assertFalse(apps);self.assertEqual(2,len(rejections))

    def test_possible_duplicates_are_review_queue_only(self):
        a=dict(self.q,object='Harbor survey report',instrument_id='EO:1')
        b=dict(a,question_key='other',instrument_id='EO:2')
        pairs,_=possible_duplicates([a,b]);self.assertEqual('possible_duplicate_review_required',pairs[0]['state'])

    def test_partial_transfer_without_eo_number_remains_candidate(self):
        # Reuse Panizzi from the actual repo without copying a new source ladder.
        (self.repo/'jobs/source-ladder').mkdir(parents=True)
        (self.repo/'jobs/source-ladder/report_dates.py').write_bytes((ROOT/'jobs/source-ladder/report_dates.py').read_bytes())
        span={k:self.e[k] for k in ('source','text','char_start','char_end')}
        q=dict(self.q,event_kind='function_succession')
        q['question_key']=question_key(q)
        q['aliases']=[{'kind':'institution','entity_id':q['entity_id'],'text':'Harbor Commission','evidence':span},
                      {'kind':'function','entity_id':q['entity_id'],'text':'harbor survey','evidence':span}]
        candidates,holds=search_sources(self.repo,[q],[(self.src,self.text)])
        self.assertEqual(1,len(candidates));self.assertEqual('machine_candidate',candidates[0]['state'])
        self.assertIn('except',candidates[0]['qualifiers']);self.assertIsNone(candidates[0]['event_date'])
        self.assertNotIn('whole_order_status',candidates[0])

if __name__=='__main__':unittest.main()
