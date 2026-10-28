"""One investigation may start before status adoption; no gate is promoted."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import assemble as A
import batch
import kit
import status_overlay as O
from test_status_overlay import OverlayTests


class ContinuousRouteTests(unittest.TestCase):
    def setUp(self):
        self.fixture=OverlayTests('test_blank_decision_and_review_cannot_promote')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo,self.out=self.fixture.repo,self.fixture.out

    def prepare(self):
        dest=self.repo/'research/excavator/continuous/packet'
        batch.prepare(self.repo,self.out,dest,['EO:1'],'synthetic-producer')
        return dest

    def test_ordinary_undecided_preparation_has_full_dossier_and_no_approval(self):
        folder=self.prepare();packet,ds=batch.load_packet(folder,self.repo)
        self.assertEqual(ds['EO:1'],self.fixture.evidence['base_dossier'])
        self.assertTrue(ds['EO:1']['actor_provisions'])
        self.assertIsNone(ds['EO:1']['whole_order_status'])
        entry=packet['undecided_evidence']['EO:1']
        decision=json.loads((self.repo/entry['status_decision']).read_bytes())
        self.assertFalse(decision['approved'])
        self.assertIsNone(decision['recommended_provisional_status'])
        self.assertEqual(kit.load_dossier(self.out,'EO:1',self.repo),ds['EO:1'])
        self.assertIn('one investigation',(folder/'READ.md').read_text())

    def test_changed_frozen_input_and_wrong_reservation_are_rejected(self):
        folder=self.prepare();packet,_=batch.load_packet(folder,self.repo)
        evidence=self.repo/packet['undecided_evidence']['EO:1']['path']
        evidence.write_bytes(evidence.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'changed frozen undecided evidence'):
            batch.load_packet(folder,self.repo)
        lock=self.repo/'research/readiness/CLAIM_KIT_LOCK.json'
        batch.dump(lock,{'orders':{'EO:1':{'agent':'someone-else'}}})
        with self.assertRaisesRegex(ValueError,'reservation belongs'):
            batch.prepare(self.repo,self.out,folder.parent/'v2',['EO:1'],'synthetic-producer')

    def test_next_can_reserve_unadopted_full_research_and_detect_stale_inputs(self):
        selected=kit.pick(self.repo,self.out,'synthetic-producer',1,scope='undecided')
        self.assertEqual([r['instrument_id'] for r in selected],['EO:1'])
        self.assertIsNone(selected[0]['whole_order_status'])
        self.assertEqual(selected[0]['history_sha256'],self.fixture.evidence['history_sha256'])
        summary=self.out/'SUMMARY.json';summary.write_bytes(summary.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'changed undecided reservation inputs'):
            self.prepare()

    def test_apply_preserves_research_without_emitting_unset_status_claim(self):
        folder=self.prepare();orders=batch.rows(folder/'decisions.csv')
        row=orders[0];row.update(outcome='submit',research_rationale='The same investigation is retained.',
            savings_state='unresolved',savings_reason='The saved source questions remain open.')
        for key in ('earlier_end_check','scope_check','independent_command_check','savings_check'):
            row[key]='Substantive source examination is recorded here; no legal conclusion yet.'
        batch.csv_write(folder/'decisions.csv',batch.ROW_FIELDS,orders)
        result=batch.apply(self.repo,folder,folder/'applied')
        self.assertEqual(result['counts'],{'awaiting_status_review':1})
        self.assertEqual((folder/'applied/CLAIMS.proposed.jsonl').read_text(),'')
        sheet=json.loads((folder/'applied/decisions/EO_1.json').read_bytes())
        self.assertIn('same investigation',sheet['research_rationale'])
        self.assertEqual(sheet['dossier_sha256'],self.fixture.evidence['base_dossier']['fingerprint'])

    def test_overlay_policy_change_requires_new_packet(self):
        folder=self.prepare();packet,_=batch.load_packet(folder,self.repo)
        key='jobs/claim-kit/status_overlay.py'
        self.assertEqual(packet['policy_code_sha256'][key],batch.file_sha(Path(O.__file__)))
        changed={**batch.policy_code_pins(),key:'0'*64}
        with patch.object(batch,'policy_code_pins',return_value=changed):
            with self.assertRaisesRegex(ValueError,'direct policy code changed'):
                batch.apply(self.repo,folder,folder/'changed-policy')

    def test_reviewed_overlay_carries_research_and_rejects_wrong_version(self):
        evidence=self.fixture.evidence
        sheet=A.blank_sheet(evidence['base_dossier'],'synthetic-producer')
        sheet['research_rationale']='Retain the investigated inventory, earlier endings and open questions.'
        sheet['unresolved_material_gaps']=['Independent lifecycle review remains necessary.']
        sheet['approved']=True
        dest=self.repo/'research/excavator/continuous/overlay/v1'
        O.write_bundle(self.repo,dest,self.fixture.propose(),self.fixture.decision,
            self.fixture.review,evidence,lifecycle_sheet=sheet)
        working=json.loads((dest/'LIFECYCLE_DECISION.json').read_bytes())
        self.assertEqual(working['research_rationale'],sheet['research_rationale'])
        self.assertEqual(working['clauses'],sheet['clauses'])
        self.assertFalse(working['approved'])
        self.assertNotEqual(working['dossier_sha256'],sheet['dossier_sha256'])
        receipt=json.loads((dest/'LIFECYCLE_CONTINUITY.json').read_bytes())
        self.assertEqual(receipt['source_sheet_sha256'],A.canonical_sha(sheet))
        self.assertEqual(json.loads((dest/receipt['source_sheet_path']).read_bytes()),sheet)
        self.assertTrue(receipt['producer_reconfirmation_required'])
        self.assertTrue(receipt['independent_lifecycle_review_required'])
        wrong=deepcopy(sheet);wrong['instrument_id']='EO:2'
        with self.assertRaisesRegex(ValueError,'must_match_frozen_base_dossier'):
            O.write_bundle(self.repo,dest.parent/'v2',self.fixture.propose(),self.fixture.decision,
                self.fixture.review,evidence,lifecycle_sheet=wrong)
        wrong=deepcopy(sheet);wrong['dossier_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'must_match_frozen_base_dossier'):
            O.write_bundle(self.repo,dest.parent/'v3',self.fixture.propose(),self.fixture.decision,
                self.fixture.review,evidence,lifecycle_sheet=wrong)
        wrong=deepcopy(sheet);wrong['schema']='wrong-decision-schema'
        with self.assertRaisesRegex(ValueError,'must_match_frozen_base_dossier'):
            O.write_bundle(self.repo,dest.parent/'v4',self.fixture.propose(),self.fixture.decision,
                self.fixture.review,evidence,lifecycle_sheet=wrong)


if __name__=='__main__':unittest.main()
