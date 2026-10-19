from pathlib import Path
import tempfile
import json
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from history import normalized_span,temporal_history,api_anchor,row_chunks,blank_decision,show,compact,canon


class HistoryTests(unittest.TestCase):
    def snapshot(self,group):return {'kind':'printed_snapshot','group':group}
    def event(self,date,**extra):return dict(mechanism='revocation',candidate_date=date,qualifier='',date_flags='',verified_raw_span=True,**extra)

    def test_exact_offsets_preserve_whitespace_and_punctuation(self):
        text='Revoked by: EO  12534,\n June 30, 1986'
        r=normalized_span(text,'Revoked by: EO 12534, June 30, 1986')
        self.assertEqual(text[r['char_start']:r['char_end']],r['text'])
        self.assertEqual(r['match'],'whitespace_only')
        self.assertIsNone(normalized_span(text,'Revoked by EO 12534'))
        self.assertIsNone(normalized_span('EO 1; EO 1','EO 1'))

    def test_later_cleanup_does_not_supply_first_end(self):
        constraints,flags=temporal_history([self.snapshot('ended_by_1989')],[self.event('2001-01-01')],None)
        self.assertIn('KNOWN_LATER_CLEANUP_IS_NOT_FIRST_END_SEARCH_EARLIER',flags)
        self.assertEqual(constraints[0]['upper'],'1989-01-20')
        self.assertIsNone(constraints[0]['lower'])

    def test_active_snapshot_does_not_establish_current_effect(self):
        constraints,flags=temporal_history([self.snapshot('in_force_1989')],[],'no')
        self.assertEqual(constraints[0]['lower'],constraints[0]['upper'])
        self.assertIn('POST_SNAPSHOT_END_BASIS_NOT_LOCATED',flags)

    def test_partial_prior_change_is_conflict_not_conclusion(self):
        e=self.event('1980-01-01');e['qualifier']='in part'
        _,flags=temporal_history([self.snapshot('in_force_1989')],[e],None)
        self.assertIn('PRE_SNAPSHOT_END_LEAD_VS_ACTIVE_SNAPSHOT_CHECK_SCOPE_OR_REVIVAL',flags)
        self.assertIn('PARTIAL_OR_QUALIFIED_CHANGE_REQUIRES_CLAUSE_CHECK',flags)

    def test_empty_note_and_after_cutoff_cannot_imply_status(self):
        _,flags=temporal_history([{'kind':'api_observation','text':''}],[self.event('2026-10-15')],None)
        self.assertIn('POST_CUTOFF_EVENT_EXCLUDED_FROM_TEMPORAL_INFERENCE',flags)
        self.assertIn('EMPTY_CATALOG_NOTE_DOES_NOT_ESTABLISH_CURRENT_EFFECT',flags)

    def test_identity_anchor_preserves_raw_suffix_and_title(self):
        a=api_anchor({'executive_order_number':'10571','signing_date':'1954-10-18','title':'Forest'})
        b=api_anchor({'executive_order_number':'10571','signing_date':'1954-10-26','title':'-A Radio'})
        self.assertNotEqual(a,b)
        self.assertNotEqual(api_anchor({'executive_order_number':'9-2'}),api_anchor({'executive_order_number':'9'}))

    def test_chunk_quotes_do_not_claim_reconstructed_row_is_verbatim(self):
        p={'chunks':[[50,100,'12'],[266,100,'Revoked\nby EO 7'],[50,90,'13']]}
        quotes=row_chunks({'y':'100'},p,[100,90])
        self.assertEqual(len(quotes),2)
        self.assertEqual(quotes[1]['text'],'Revoked\nby EO 7')

    def test_status_sheet_is_blank_and_cannot_publish(self):
        r=blank_decision({'history':{'instrument_id':'EO:1','fingerprint':'a'*64,'flags':['gap']}},'test')
        self.assertFalse(r['approved']);self.assertIsNone(r['recommended_provisional_status'])
        self.assertEqual(r['proposed_intervals'],[])

    def test_failed_output_cannot_expose_an_old_history(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'FAILED.json').write_text('{"stale_outputs_must_not_be_used":true}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'stale outputs'):show(p,'EO:1')
            (p/'FAILED.json').unlink();(p/'STATUS.json').write_text('{"result":"failed"}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'did not succeed'):show(p,'EO:1')

    def test_startup_cap_discloses_overflow_and_preserves_full_pointer(self):
        h={'instrument_id':'EO:1','fingerprint':'a'*64,'legal_cutoff':'2026-10-14','provisional_status':None,
           'flags':[],'temporal_constraints_LEADS_ONLY':[],'next_actions':['Read full source.']}
        event={'id':'EV:1','actor_id':'EO:2','mechanism':'amendment','candidate_date':'1980-01-01',
           'date_meaning':'signing date only','qualifier':'x'*600,'verified_raw_span':True,'observation_id':'API:1'}
        p=compact({'history':h,'observations':[],'events':[event]*100},2000)
        self.assertLessEqual(len(canon(p).encode()),2000)
        self.assertGreater(p['omitted_event_records'],0)
        self.assertIn('--full',p['full_evidence_command'])


if __name__=='__main__':unittest.main()
