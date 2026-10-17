import unittest,sqlite3,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'CODE'))
from policy import Review,authorize_status,authorize_first_cause,DecisionRejected,SharedSourceInference,assess_mass_inference
from estimators import probability_sample_estimate,competing_risk_survival,ScientificInferenceUnavailable
DB=R/'DATA/AFTERLIFE_STAGE16_CANONICAL.sqlite'
class TestStage16(unittest.TestCase):
 def setUp(self):self.c=sqlite3.connect(str(DB))
 def tearDown(self):self.c.close()
 def one(self,q,*a):return self.c.execute(q,a).fetchone()[0]
 def test_input_preservation(self):
  self.assertEqual(self.one('select count(*) from original_stage11_rows'),15010)
  self.assertEqual(self.one('select sum(include_proxy) from instruments'),14972)
  self.assertEqual(self.one("select count(*) from instruments where include_proxy=1 and original_legacy_status='no'"),2322)
 def test_source_recovery_future_ingestion(self):
  self.assertEqual(self.one('select count(*) from source_observations'),11164)
  self.assertEqual(self.one('select count(*) from candidate_relationships where eligible_for_research=1'),7084)
  self.assertEqual(self.one("select count(*) from candidate_relationships where provenance_type='NARA_1989_source_row_discovered' and eligible_for_research=1"),510)
  self.assertEqual(self.one('select count(*) from candidate_relationships where eligible_for_research=0'),121)
  self.assertEqual(self.one("select eligible_for_research from candidate_relationships where actor='EO:13257' and predecessor='EO:13333' limit 1"),0)
  self.assertEqual(self.one("select count(*) from candidate_relationships where actor='EO:12553' and predecessor in ('EO:11920','EO:12395') and eligible_for_research=0"),2)
 def test_bypass_of_v3_determinate_source_gate_is_rejected(self):
  with self.assertRaises(sqlite3.IntegrityError):
   self.c.execute("INSERT INTO v3_effect_assessments VALUES('EO:10180','no','unknown','unknown','unknown','source_reviewed_not_independently_certified',NULL,'Unsourced attempt',1)")
  with self.assertRaises(sqlite3.IntegrityError):
   self.c.execute("UPDATE v3_effect_assessments SET normative_status='yes',review_grade='source_reviewed_not_independently_certified' WHERE id='EO:13286'")
 def test_invalid_graph_promotion_is_rejected(self):
  with self.assertRaises(sqlite3.IntegrityError):
   self.c.execute("update candidate_relationships set decision_promotion_allowed=1 where candidate_key='S14:1'")
 def test_historical_census_held_separate(self):
  self.assertEqual(self.one('select count(*) from lord_date_markers'),1023)
  self.assertEqual(self.one('select count(*) from lord_date_markers where document_authenticated=1'),0)
  self.assertEqual(self.one('select count(*) from source_date_references'),18)
  self.assertGreaterEqual(self.one("select count(*) from lord_source_excerpts where extraction_grade='SOURCE_OCR_CONTEXT_NOT_AUTHENTICATED'"),900)
  self.assertEqual(self.one('select count(*) from lord_source_excerpts'),1023)
  self.assertIsNone(self.c.execute("select estimated_size from census_methodology where estimand='all_historically_issued_executive_orders'").fetchone()[0])
  self.assertEqual(self.one('select count(*) from lord_nara_date_matches'),5)
 def test_delegated_order_not_misidentified(self):
  self.assertEqual(self.one("select signature_authenticated from instruments where id='EO:3016K'"),0)
  self.assertEqual(self.c.execute("select signer_claim from instruments where id='EO:3016N'").fetchone()[0],'unverified')
 def test_first_cause_gated(self):
  with self.assertRaises(DecisionRejected):authorize_first_cause(ever_operative=True,source_for_episode='x',source_for_cause=None,first_date_type='exact',alternative_earlier_end_excluded=False,successor_not_only_latest_bound=False)
  with self.assertRaises(sqlite3.IntegrityError):
   self.c.execute("INSERT INTO legal_event VALUES('BAD','EO:3461','EO:2596','1921-05-16','day','revocation','x','NARA_EO3461','PROVEN_WHOLE_ORDER_FIRST_CESSATION','metadata_only')")
 def test_12553_scope_does_not_create_cause(self):
  self.assertEqual(self.one("select count(*) from legal_event where actor_instrument='EO:12553'"),386)
  self.assertEqual(self.one("select count(*) from legal_event where actor_instrument='EO:12553' and first_cessation_claim like 'PROVEN%'"),0)
  self.assertEqual(self.one("select count(*) from candidate_relationships where actor='EO:12553' and eligible_for_research=1"),769)
 def test_3461_savings(self):
  self.assertEqual(self.one("select count(*) from legal_event where actor_instrument='EO:3461'"),45)
  self.assertEqual(self.one("select count(*) from legal_event where actor_instrument='EO:3461' and first_cessation_claim like 'PROVEN%'"),0)
 def test_date_specific_episodes_and_residuals(self):
  for i,n in [('EO:14129',1),('EO:14133',1),('EO:14371',2)]:
   self.assertEqual(self.one('select count(*) from legal_episode where instrument_id=? and first_cessation_proven=1',i),2*n)
   self.assertEqual(self.one("select count(*) from legal_episode where instrument_id=? and state='indeterminate'",i),2)
   self.assertEqual(self.c.execute('select normative_status from v3_effect_assessments where id=?',(i,)).fetchone()[0],'indeterminate')
 def test_6877_original_sunset_is_not_cause(self):
  self.assertEqual(self.one("select count(*) from legal_episode where instrument_id='EO:6877' and first_cessation_proven=1"),0)
  self.assertEqual(self.one("select count(*) from legal_event where event_id='EO:6955A#AMEND6877'"),1)
  self.assertEqual(self.c.execute("select valid_to_exclusive from legal_episode where episode_id='EO:6877#AMENDED_WOOL_ADMINISTRATION_WINDOW'").fetchone()[0],None)
 def test_v3_not_legacy_relabel(self):
  self.assertEqual(self.one("select count(*) from v3_effect_assessments where normative_status='no'"),1)
  self.assertEqual(self.one("select count(*) from legal_readiness where v3_certified=1"),0)
  self.assertEqual(self.c.execute("select normative_status from v3_effect_assessments where id='EO:13286'").fetchone()[0],'indeterminate')
  self.assertEqual(self.c.execute("select original_legacy_status from instruments where id='EO:13286'").fetchone()[0],'yes')
 def test_deceptive_statistical_estimation_rejected(self):
  self.assertEqual(self.one('select count(*) from probability_sample'),120)
  self.assertAlmostEqual(self.one('select sum(design_weight) from probability_sample'),14972,places=3)
  with self.assertRaises(ScientificInferenceUnavailable):probability_sample_estimate(DB)
  with self.assertRaises(ScientificInferenceUnavailable):competing_risk_survival(DB)
 def test_sample_verdict_without_reviewer_blocked(self):
  with self.assertRaises(sqlite3.IntegrityError):self.c.execute("update probability_sample set review_state='REVIEWED',independent_verdict='no' where id=(select id from probability_sample limit 1)")
 def test_seven_shared_root_families_are_gated(self):
  fields=['original_all_clauses_known','surviving_independent_clause_excluded','savings_and_rights_checked','exact_successor_scope_proved','host_amendments_traced','grant_exercise_proved_if_relied_on','residual_institutional_authority_traced','continuing_duties_traced','primary_text_available','evidence_of_actual_cessation']
  x=SharedSourceInference(**{k:True for k in fields})
  self.assertFalse(assess_mass_inference(x)['automatically_classify_predecessors'])
  self.assertTrue(assess_mass_inference(x)['family_rule_usable_for_source_based_review'])
  for field in fields:
   kwargs={k:True for k in fields};kwargs[field]=False
   self.assertFalse(assess_mass_inference(SharedSourceInference(**kwargs))['family_rule_usable_for_source_based_review'],field)
  self.assertFalse(assess_mass_inference(SharedSourceInference(**{k:True for k in fields},first_cause_claimed=True))['family_rule_usable_for_source_based_review'])
  self.assertFalse(assess_mass_inference(SharedSourceInference(**{k:True for k in fields},source_is_only_editorial_silence=True))['family_rule_usable_for_source_based_review'])
 def test_decision_requires_referenced_original_and_review_for_certification(self):
  with self.assertRaises(DecisionRejected): authorize_status('no',Review())
  passable=Review(document_verified=True,whole_original_scope_verified=True,later_events_checked=True,saved_rights_checked=True,host_amendment_checked=True,residual_checked=True,unresolved_material_scope=False,original_evidence_ref='OFFICIAL')
  self.assertIn('source_reviewed',authorize_status('no',passable))
  with self.assertRaises(DecisionRejected):authorize_status('no',passable,certified=True)
 def test_sql_integrity(self):self.assertEqual(self.c.execute('pragma integrity_check').fetchone()[0],'ok')
if __name__=='__main__':unittest.main()
