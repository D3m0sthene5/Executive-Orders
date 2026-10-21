"""Actual performance-until-revocation and repeated-blocked-work regressions."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lifecycle_obligations as L


class LifecycleTests(unittest.TestCase):
    def test_deadline_and_performance_are_not_an_end(self):
        rows = L.obligations('EO:1', [{'scope_id':'EO:1#2d', 'text':'The Secretary shall submit a report within 45 days.'}], [], [{'id':'ACT:1>2','verb':'revoke'}])
        self.assertTrue({'deadline','performance_command'} <= set(rows[0]['wording_features']))
        self.assertIsNone(rows[0]['established_ending'])
        self.assertTrue(any('before the later revocation' in s for s in rows[0]['questions']))

    def test_recurring_sunset_and_renewal_distinct(self):
        f = L.clause_features('The Board shall submit annual reports. It shall terminate on June 1, 2000 unless renewed.')
        self.assertTrue({'recurring_duty','fixed_sunset','contingent_end','renewal'} <= set(f))
        self.assertNotIn('actual_performance_lead', f)

    def test_completed_wording_needs_verification(self):
        r = L.obligations('EO:1', [{'scope_id':'EO:1#a','text':'The report was submitted on June 1, 2000.'}], [], [])[0]
        self.assertIn('actual_performance_lead', r['wording_features'])
        self.assertIsNone(r['established_ending'])

    def test_source_block_defers_until_relevant_inputs_change(self):
        d = {'instrument_id':'EO:1','fingerprint':'a'*64}
        q = [{'id':'needed-report','citation':'actual report submission'}]
        old = L.blocked_checkpoint(d,q,'b'*64,'report not held',['attempt-1.json'])
        self.assertEqual(L.resume_decision(old,d,q,'b'*64)['action'],'defer_unchanged_source_block')
        for nd,nq,route in [({**d,'evidence':{'report':'submitted'}},q,'b'*64),(d,q+[{'id':'new-route'}],'b'*64),(d,q,'c'*64)]:
            self.assertEqual(L.resume_decision(old,nd,nq,route)['action'],'reopen')
        self.assertEqual(old['result_paths'],['attempt-1.json'])

    def test_changed_evidence_reopens_even_with_stale_embedded_fingerprint(self):
        d={'instrument_id':'EO:1','fingerprint':'stale','evidence':{'report':None}}
        q=[{'id':'report'}]
        old=L.blocked_checkpoint(d,q,'a'*64,'missing',['attempt'])
        changed={**d,'evidence':{'report':{'sha256':'b'*64,'status':'found'}}}
        self.assertEqual(L.resume_decision(old,changed,q,'a'*64)['action'],'reopen')

    def test_receipt_reopens_before_dossier_rebuild_but_retry_time_does_not(self):
        d={'instrument_id':'EO:1'};q=[{'id':'report'}]
        receipts=[{'request_id':'report','status':'blocked','retrieved_utc':'one'}]
        old=L.blocked_checkpoint(d,q,'a'*64,'missing',['attempt'],receipts)
        retry=[{**receipts[0],'retrieved_utc':'two'}]
        self.assertEqual(L.resume_decision(old,d,q,'a'*64,retry)['action'],'defer_unchanged_source_block')
        found=[{'request_id':'report','status':'found','sha256':'b'*64}]
        self.assertEqual(L.resume_decision(old,d,q,'a'*64,found)['action'],'reopen')

    def test_cannot_hide_failure_or_mix_identities(self):
        with self.assertRaises(ValueError): L.blocked_checkpoint({'instrument_id':'EO:1'},[],'a'*64,'',[])
        old=L.blocked_checkpoint({'instrument_id':'EO:1'},[{'id':'r'}],'a'*64,'missing',['result'])
        with self.assertRaises(ValueError): L.resume_decision(old,{'instrument_id':'EO:2'},[{'id':'r'}],'a'*64)


if __name__ == '__main__': unittest.main()
