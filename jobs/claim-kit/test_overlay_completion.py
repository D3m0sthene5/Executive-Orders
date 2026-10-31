"""Completion consumes exact experimental overlays without adopting statuses."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

REPO = Path(os.environ.get('CLAIM_KIT_TEST_REPO', str(Path(__file__).resolve().parents[2])))
sys.path.insert(0, str(REPO/'jobs/claim-kit'))
import completion as C
import batch
import status_overlay as O
from test_status_overlay import OverlayTests


class OverlayCompletionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = OverlayTests('test_full_overlay_dossier_runs_existing_assembler')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo,self.out = self.fixture.repo,self.fixture.out
        self.packet = self.repo/'research/excavator/synthetic/packet'
        batch.prepare(self.repo,self.out,self.packet,['EO:1'],'synthetic-producer')
        self.bundle = self.repo/'research/excavator/synthetic/overlay/v1'
        proposal = self.fixture.propose()
        O.write_bundle(self.repo,self.bundle,proposal,self.fixture.decision,self.fixture.review,self.fixture.evidence)
        dossier = json.loads((self.bundle/'DOSSIER.json').read_bytes())
        self.claim,errors = O.assemble_working(self.repo,self.fixture.lifecycle_sheet(dossier),
            proposal,self.fixture.decision,self.fixture.review,self.fixture.evidence)
        self.assertEqual(errors,[])
        self.claim_path = self.bundle/'CLAIMS.working.jsonl'
        self.claim_path.write_bytes((json.dumps(self.claim,separators=(', ',': '))+'\r\n').encode())
        self.review_path = self.bundle/'LIFECYCLE_REVIEW.json'
        self.review = {'instrument_id':'EO:1','claim_sha256':C.claim_sha(self.claim),
            'reviewer':'separate-lifecycle-reviewer','model_family':'OpenAI','independent':True,
            'separate_context':True,'review_kind':'independent_ai_source_review',
            'scope':'whole_case','verdict':'upheld'}
        batch.dump(self.review_path,self.review)
        self.member = {'instrument_id':'EO:1','claim_sha256':C.claim_sha(self.claim),
            'outcome':'submit','claim':self.ref(self.claim_path,line=1),
            'publication_kind':'whole_case','review':self.ref(self.review_path),
            'overlay_bundle':{key:self.ref(self.bundle/name) for key,name in {
                'evidence':'EVIDENCE.json','decision':'STATUS_DECISION.json',
                'review':'STATUS_REVIEW.json','proposal':'PROMOTION_PROPOSAL.json'}.items()}}
        self.manifest = {'schema':C.SCHEMA,'agent':'synthetic-producer',
            'producer_model_family':'OpenAI','independence_requirement':'same_family_separate_context',
            'controls':[],'members':[self.member],
            'publication':{'mode':'replacement_proposal','path':'research/excavator/synthetic/PROPOSAL.jsonl'}}

    def ref(self,path,**selector):
        return {'path':path.relative_to(self.repo).as_posix(),'sha256':batch.file_sha(path),**selector}

    def select(self):
        return C.selected_claim(C.Inputs(self.repo),self.member,self.manifest,set(),set())

    def rewrite_claim_and_review(self):
        self.claim_path.write_text(json.dumps(self.claim)+'\n')
        self.review['claim_sha256'] = C.claim_sha(self.claim)
        batch.dump(self.review_path,self.review)
        self.member.update(claim=self.ref(self.claim_path,line=1),claim_sha256=C.claim_sha(self.claim),
            review=self.ref(self.review_path))

    def test_legacy_overlay_needs_no_ordinary_packet_and_retains_exact_bytes(self):
        claim,raw,detail = self.select()
        self.assertEqual(claim,self.claim)
        self.assertEqual(raw,self.claim_path.read_bytes())
        self.assertTrue(detail['experimental_status_overlay'])
        self.assertTrue(detail['owner_adoption_required'])
        self.assertFalse(detail['canonical_filing_allowed'])
        self.assertFalse(claim['claim_kit']['status_overlay']['owner_accepted'])
        self.assertFalse((self.repo/'research/readiness/claims').exists())

    def test_optional_old_packet_is_only_exact_base_provenance(self):
        self.member['packet'] = self.ref(self.packet/'PACKET.json')
        # New status/lifecycle review records made the old context stale. Its
        # source/base dossier remains exactly the independently checked overlay.
        with self.assertRaisesRegex(ValueError,'changed prior research'):
            batch.load_packet(self.packet,self.repo)
        self.assertTrue(self.select()[2]['experimental_status_overlay'])

    def test_changed_archived_base_cannot_substitute_another_dossier(self):
        self.member['packet'] = self.ref(self.packet/'PACKET.json')
        path = self.packet/'PACKET.json'
        packet = json.loads(path.read_bytes())
        packet['agent'] = 'wrong-producer'
        packet.pop('fingerprint');packet['fingerprint'] = batch.digest(batch.canon(packet).encode())
        batch.dump(path,packet);self.member['packet'] = self.ref(path)
        with self.assertRaisesRegex(ValueError,'another producer'):
            self.select()

    def test_unadopted_overlay_cannot_select_for_canonical_filing(self):
        self.manifest['publication'] = {'mode':'own_claims',
            'path':'research/readiness/claims/synthetic-producer-2026-10-25.jsonl'}
        with self.assertRaisesRegex(ValueError,'unadopted status overlay'):
            self.select()

    def test_missing_status_review_is_not_lifecycle_approval(self):
        (self.bundle/'STATUS_REVIEW.json').unlink()
        with self.assertRaisesRegex(ValueError,'missing input'):
            self.select()

    def test_stale_status_review_decision_is_rejected(self):
        path = self.bundle/'STATUS_DECISION.json';decision=json.loads(path.read_bytes())
        decision['rationale'] += ' Changed reviewed proposition.'
        batch.dump(path,decision);self.member['overlay_bundle']['decision'] = self.ref(path)
        with self.assertRaisesRegex(ValueError,'stale_review_decision'):
            self.select()

    def test_changed_claim_keeps_exact_review_failure(self):
        self.claim_path.write_text(json.dumps({**self.claim,'research_rationale':'changed'})+'\n')
        with self.assertRaisesRegex(ValueError,'changed input'):
            self.select()

    def test_forged_owner_or_wrong_target_overlay_metadata_is_not_bypassed(self):
        for key,value in [('owner_accepted',True),('proposal_id','status-overlay:EO:2:'+'a'*20)]:
            with self.subTest(key=key):
                before=deepcopy(self.claim)
                self.claim['claim_kit']['status_overlay'][key]=value
                self.rewrite_claim_and_review()
                with self.assertRaisesRegex(ValueError,'working_claim_status_overlay_label_required'):
                    self.select()
                self.claim=before;self.rewrite_claim_and_review()

    def test_source_change_rejects_both_legacy_and_continuous_routes(self):
        source=next(iter(self.fixture.evidence['source_fingerprints']))
        (self.repo/source).write_bytes(b'changed source')
        with self.assertRaisesRegex(ValueError,'changed dependency|stale_held_source'):
            self.select()

    def test_exact_lifecycle_review_remains_separate_from_status_review(self):
        self.member['review']=self.member['overlay_bundle']['review']
        with self.assertRaisesRegex(ValueError,'selected exact claim'):
            self.select()

    def test_unknown_identity_is_not_created_by_overlay_selection(self):
        self.member['instrument_id']='EO:999999'
        with self.assertRaisesRegex(ValueError,'selected producer version mismatch'):
            self.select()

    def test_declared_overlay_cannot_drop_its_working_status_label(self):
        self.claim['claim_kit'].pop('status_overlay')
        self.rewrite_claim_and_review()
        with self.assertRaisesRegex(ValueError,'working_claim_status_overlay_label_required'):
            self.select()

    def complete(self,publish=True,change_status=False):
        seed = self.bundle/'CONTROL_SEED.json'
        batch.dump(seed,{'schema':'eo-claim-kit-control-seed/v1','instrument_id':'EO:2',
            'planted_claim_sha256':'b'*64,'genuine_claim_sha256':'c'*64,'seeded_by':'planter'})
        review = self.bundle/'CONTROL_REVIEW.json'
        batch.dump(review,{**self.review,'instrument_id':'EO:2','claim_sha256':'b'*64,'verdict':'rejected'})
        adjudication = self.bundle/'CONTROL_ADJUDICATION.json'
        batch.dump(adjudication,{'instrument_id':'EO:2','planted_claim_sha256':'b'*64,
            'review':self.ref(review),'adjudicator':'scorer','rationale':'Explicit synthetic material defect caught.',
            'scoring':'strict','caught':True})
        self.manifest['controls']=[{'instrument_id':'EO:2','planted_claim_sha256':'b'*64,
            'seed':self.ref(seed),'review':self.ref(review),'adjudication':self.ref(adjudication)}]
        manifest_path=self.bundle/'COMPLETION.json';batch.dump(manifest_path,self.manifest)
        dest=self.bundle/'complete'
        def checker(repo,claims,folder):
            folder.mkdir()
            rows=[{'instrument_id':c['instrument_id'],'claim_sha256':C.claim_sha(c),
                'mechanical_result':'pass','all_checks_passed':True,'gate_errors':[]}
                for c in map(json.loads,claims.read_bytes().splitlines())]
            if change_status:
                with self.fixture.fixture.status.open('a') as handle:handle.write('EO:1,no\n')
            return {'claims':rows,'by_instrument':{r['instrument_id']:r for r in rows}}
        with patch.object(C,'run_checker',side_effect=checker),patch.object(C,'run_tracker',return_value={
            'selected':{'EO:1':{'after':{'ready_for_human_review':'no'}}},'canonical_outputs_modified':False}):
            result=C.complete(self.repo,manifest_path,dest,publish=publish)
        return result,dest

    def test_complete_publishes_only_isolated_proposal_with_adoption_requirement(self):
        result,dest=self.complete()
        self.assertEqual(result['eligible'],['EO:1'])
        self.assertEqual(result['claims_published'],0)
        self.assertEqual((self.repo/self.manifest['publication']['path']).read_bytes(),self.claim_path.read_bytes())
        publication=json.loads((dest/'PUBLICATION.json').read_bytes())
        self.assertEqual(publication['status_adoption_required'],['EO:1'])
        self.assertFalse(publication['canonical_filing_allowed'])
        self.assertTrue(publication['owner_acceptance_required'])

    def test_publish_true_cannot_file_overlay_canonically(self):
        self.manifest['publication']={'mode':'own_claims',
            'path':'research/readiness/claims/synthetic-producer-2026-10-25.jsonl'}
        result,dest=self.complete()
        self.assertEqual(result['eligible'],[])
        self.assertFalse((self.repo/self.manifest['publication']['path']).exists())
        self.assertEqual((dest/'CLAIMS.publishable.jsonl').read_bytes(),b'')

    def test_authority_change_during_checker_requires_new_nonoverlay_version(self):
        result,dest=self.complete(change_status=True)
        self.assertEqual(result['eligible'],[])
        self.assertFalse((self.repo/self.manifest['publication']['path']).exists())
        self.assertTrue(any('authoritative_provisional_status' in e['error']
            for e in json.loads((dest/'EXCEPTIONS.json').read_bytes())))


if __name__ == '__main__':
    unittest.main()
