import unittest
from build_causal_cues import date_contexts, build

class CueTests(unittest.TestCase):
 def test_unclassified_dates_do_not_become_causal_proof(self):
  x={'review_problems_verbatim':'Statute repealed effective 1952-07-25; reviewer checked on 2026-10-17.',
     'what_remains_inferential_verbatim':'Earlier legal effects unresolved.'}
  rows=date_contexts(x)
  self.assertEqual(len(rows),2)
  self.assertTrue(all(v['legal_effect_and_source_unverified'] for v in rows))

 def test_shard_shared_between_orders_cannot_certify(self):
  def one(n):
   return {'instrument_id':f'EO:{n}','verdict':'no','opus_lane':'G',
    'opus_footprint_complete_claim':'True','evidence_dir_in_archive':'evidence/shards/X/',
    'review_dir_in_archive':'evidence/reviews/Y/',
    'review_problems_verbatim':'Possible expiration 1950-01-01',
    'what_remains_inferential_verbatim':'Unresolved','explicit_references_not_verified':[]}
  images=[{'manifest_path':'evidence/shards/X/originals/p1.pdf','sha256':'a'*64,
           'bytes':'100','source_bytes_verified':'yes'}]
  packets,queue,media,summary=build([one(1),one(2)],images)
  self.assertEqual(summary['image_members_with_many_accepted_case_batch_paths'],1)
  self.assertEqual(summary['human_certified_whole_lifecycle_dossiers'],0)
  self.assertTrue(all(not p['human_certified'] for p in packets))
  self.assertTrue(all(x['association_grade']=='no_case_specific_evidence' for x in media))

if __name__=='__main__':
 unittest.main()
