"""Ordinary apply CLI with real assembly, frozen packets and offline custody."""
import json
import unittest

import batch
import test_batch as B
import test_build as T
import test_dispatch as D


class ApplySelectedSourceTests(unittest.TestCase):
    setUp = T.BuildIntegrationTests.setUp
    run_build = T.BuildIntegrationTests.run_build
    dossier = T.BuildIntegrationTests.dossier
    decision = T.BuildIntegrationTests.decision
    retain = D.DispatchTests.retain
    packet = D.DispatchTests.packet
    cli = D.DispatchTests.cli
    fill = B.BatchTests.fill

    def test_apply_checks_assembled_sources_and_rechecks_changed_raw_bytes(self):
        folder = self.packet(ids=('EO:1',))
        self.fill(folder)
        frozen = (folder/'PACKET.json').read_bytes()
        applied = folder/'applied-v1'
        code, stdout = self.cli('apply', folder, '--write', applied)
        result = json.loads(stdout)
        self.assertEqual(code, 0, stdout)
        self.assertEqual(result['counts'], {'assembled_proposal': 1})
        receipt = json.loads((applied/'SELECTED_SOURCE_CHECK.json').read_bytes())
        claim = T.read_jsonl(applied/'CLAIMS.proposed.jsonl')[0]
        self.assertTrue(receipt['ok'])
        self.assertEqual(receipt['members'][0]['claim_sha256'],
                         batch.digest(batch.canon(claim).encode()))
        self.assertEqual(result['selected_source_check']['packet_sha256'],
                         batch.file_sha(folder/'PACKET.json'))
        self.assertFalse(receipt['scientific_approval'])
        self.assertEqual(receipt['network_requests'], 0)
        first_receipt = (applied/'SELECTED_SOURCE_CHECK.json').read_bytes()
        (self.repo/'jobs/future-source/output/raw/EO_5.bin').write_bytes(b'changed')
        later = folder/'applied-v2'
        code, stdout = self.cli('apply', folder, '--write', later)
        self.assertEqual(code, 1, stdout)
        self.assertIn('held_record_but_local_bytes_differ',
                      (later/'SELECTED_SOURCE_CHECK.json').read_text())
        self.assertEqual((applied/'SELECTED_SOURCE_CHECK.json').read_bytes(), first_receipt)
        self.assertEqual((folder/'PACKET.json').read_bytes(), frozen)
        self.assertFalse((self.repo/'research/readiness/claims').exists())

    def test_apply_refuses_newly_selected_optional_actor_and_preserves_proposal(self):
        folder = self.packet(ids=('EO:1',), missing=('EO:5',))
        self.assertTrue(json.loads((folder/'DISPATCH_CHECK.json').read_bytes())['ok'])
        self.fill(folder)
        applied = folder/'applied-v1'
        code, stdout = self.cli('apply', folder, '--write', applied)
        result = json.loads(stdout)
        self.assertEqual(code, 1, stdout)
        self.assertEqual(result['counts'], {'assembled_proposal': 1})
        self.assertEqual(len(T.read_jsonl(applied/'CLAIMS.proposed.jsonl')), 1)
        receipt = json.loads((applied/'SELECTED_SOURCE_CHECK.json').read_bytes())
        self.assertFalse(receipt['ok'])
        self.assertIn('custody_record_only', json.dumps(receipt))
        self.assertEqual(len(receipt['source_recovery_tasks']), 1)
        self.assertEqual(receipt['source_recovery_tasks'][0]['native_wanted']['instrument_ids'], ['EO:1'])
        self.assertFalse((self.repo/'research/readiness/claims').exists())

    def test_apply_without_proposals_records_empty_state_and_keeps_unresolved_members(self):
        folder = self.packet(ids=('EO:1',))
        applied = folder/'unresolved-v1'
        code, stdout = self.cli('apply', folder, '--write', applied)
        result = json.loads(stdout)
        self.assertEqual(code, 0, stdout)
        self.assertEqual(result['counts'], {'unresolved': 1})
        self.assertEqual(result['selected_source_check'],
                         {'state': 'no_proposed_claims', 'scientific_approval': False})
        self.assertEqual((applied/'CLAIMS.proposed.jsonl').read_text(), '')
        self.assertEqual(json.loads((applied/'AUDIT.json').read_bytes())[0]['outcome'], 'unresolved')
        self.assertFalse((applied/'SELECTED_SOURCE_CHECK.json').exists())
        self.assertFalse((self.repo/'research/readiness/claims').exists())


if __name__ == '__main__':
    unittest.main()
