import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'SCRIPTS'))
from legal_gate import LegalProposal,assess

class TestLegalGate(unittest.TestCase):
 def test_without_original_cannot_mass_no(self):
  self.assertEqual(assess(LegalProposal(proposed_status='no'))['state'],'HOLD')
 def test_partial_insofar_cannot_mass_no(self):
  p=LegalProposal(proposed_status='no',identity_verified=True,whole_ending_endpoint_proven=True,effective_date_checked=True,later_events_checked_to_cutoff=True,source_independent_review_done=True,evidence_ids=['EO11408'],amendment_present=True,saved_rights_traced=True,residual_scopes_traced=False,material_unresolved_scopes=True)
  x=assess(p);self.assertEqual(x['state'],'HOLD');self.assertTrue(any('unresolved' in e for e in x['errors']))
 def test_revocation_bound_not_first_cause(self):
  p=LegalProposal(proposed_status='indeterminate',first_cause_asserted=True,ever_operated_proven=True,first_cause_date_evidenced=True,first_cause_event_evidenced=False,first_cause_precedes_formal_revocation_checked=False)
  x=assess(p);self.assertEqual(x['state'],'HOLD');self.assertGreaterEqual(len(x['errors']),2)
 def test_yes_one_current_norm_but_still_needs_checks(self):
  p=LegalProposal(proposed_status='yes',currently_operative_predicate=True)
  self.assertEqual(assess(p)['state'],'HOLD')
 def test_complete_current_norm_review_ready_only(self):
  p=LegalProposal(proposed_status='yes',identity_verified=True,effective_date_checked=True,later_events_checked_to_cutoff=True,currently_operative_predicate=True,source_independent_review_done=True,evidence_ids=['EO:host:section','CFR:current:provision'])
  x=assess(p);self.assertEqual(x['state'],'READY_FOR_FURTHER_LEGAL_REVIEW');self.assertFalse(x['automatic_status_promotion'])
 def test_no_requires_residual_and_savings(self):
  p=LegalProposal(proposed_status='no',identity_verified=True,whole_ending_endpoint_proven=True,effective_date_checked=True,later_events_checked_to_cutoff=True,source_independent_review_done=True,evidence_ids=['source1'],saved_rights_traced=False,residual_scopes_traced=False,material_unresolved_scopes=True)
  self.assertEqual(assess(p)['state'],'HOLD')
 def test_true_first_cause_requires_all(self):
  p=LegalProposal(proposed_status='indeterminate',first_cause_asserted=True,ever_operated_proven=True,first_cause_precedes_formal_revocation_checked=True,first_cause_date_evidenced=True,first_cause_event_evidenced=True)
  self.assertEqual(assess(p)['state'],'READY_FOR_FURTHER_LEGAL_REVIEW')

if __name__=='__main__': unittest.main()
