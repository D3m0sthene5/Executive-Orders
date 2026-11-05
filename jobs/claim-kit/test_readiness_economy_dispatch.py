"""Source-readiness boundaries and late-selected evidence on native packets."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import unittest
from unittest.mock import patch

import assemble
import batch
import dispatch
import test_build as T
import test_dispatch as D


class ReadinessEconomyTests(unittest.TestCase):
    setUp = T.BuildIntegrationTests.setUp
    run_build = T.BuildIntegrationTests.run_build
    dossier = T.BuildIntegrationTests.dossier
    retain = D.DispatchTests.retain
    packet = D.DispatchTests.packet

    def claims(self, ids=('EO:1', 'EO:2')):
        result = []
        for iid in ids:
            sheet = T.BuildIntegrationTests.decision(self, iid)
            claim, errors = assemble.assemble(sheet, self.dossier(iid), self.repo)
            self.assertFalse(errors, errors)
            result.append(claim)
        return result

    def test_shared_missing_actor_is_one_task_with_two_applicabilities(self):
        folder = self.packet(missing=('EO:5',))
        result = dispatch.check(self.repo, folder)
        self.assertTrue(result['ok'])  # No theory selected yet.
        tasks = result['source_recovery_tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['native_wanted']['instrument_ids'], ['EO:1', 'EO:2'])
        self.assertIn('custody_record_only', tasks[0]['check_statuses'])
        self.assertFalse(tasks[0]['automatically_submitted'])
        self.assertGreater(len(tasks[0]['affected_references']), 1)
        self.assertEqual(dispatch.summary(result)['legal_requirement_coverage'], 'unknown')

    def test_newly_selected_optional_actor_blocks_before_review(self):
        folder = self.packet(missing=('EO:5',))
        self.assertTrue(dispatch.check(self.repo, folder)['ok'])
        claims = self.claims()
        result = dispatch.check_selected(self.repo, folder, claims)
        self.assertFalse(result['ok'])
        self.assertEqual(len(result['source_recovery_tasks']), 1)
        self.assertEqual([m['instrument_id'] for m in result['members']], ['EO:1', 'EO:2'])
        for member in result['members']:
            self.assertIn('selected_source_custody', {b['kind'] for b in member['blockers']})
        self.retain()
        repaired = dispatch.check_selected(self.repo, folder, claims)
        self.assertTrue(repaired['ok'])
        self.assertEqual([m['claim_sha256'] for m in result['members']],
                         [m['claim_sha256'] for m in repaired['members']])

    def test_ready_comparator_passes_and_rechecks_changed_raw_bytes(self):
        folder = self.packet()
        claims = self.claims()
        good = dispatch.check_selected(self.repo, folder, claims)
        self.assertTrue(good['ok'])
        self.assertEqual(good['unique_custody_checks'], 3)
        (self.repo / 'jobs/future-source/output/raw/EO_5.bin').write_bytes(b'changed')
        bad = dispatch.check_selected(self.repo, folder, claims)
        self.assertFalse(bad['ok'])
        self.assertIn('held_record_but_local_bytes_differ', json.dumps(bad))

    def test_yes_without_current_source_remains_an_open_research_question(self):
        folder = self.packet(ids=('EO:3',))
        result = dispatch.check(self.repo, folder)
        self.assertTrue(result['ok'])
        scope = result['members'][0]['readiness_scope']
        self.assertEqual(scope['legal_requirement_coverage'], 'unknown')
        self.assertTrue(any('Current legal predicate' in q for q in scope['dossier_reported_questions']))

    def test_explicit_wrong_instrument_marker_is_a_known_original_defect(self):
        provenance = self.repo / 'jobs/future-source/data/PROVENANCE.json'
        document = json.loads(provenance.read_bytes())
        record = next(r for r in document['representations'] if r['instrument_id'] == 'EO:1')
        text_path = self.repo / record['text_path']
        text_path.write_bytes(b'Instrument: EO:999\n' + text_path.read_bytes())
        digest = batch.file_sha(text_path)
        record['source'].update(sha256=digest, text_sha256=digest)
        T.write_json(provenance, document)
        folder = self.packet(ids=('EO:1',))
        result = dispatch.check(self.repo, folder)
        self.assertFalse(result['ok'])
        self.assertIn('required_source_wrong_instrument', json.dumps(result['members'][0]['blockers']))

    def test_wrong_instrument_substitution_and_changed_claim_versions(self):
        folder = self.packet()
        claims = self.claims(('EO:1',))
        before = dispatch.check_selected(self.repo, folder, claims)
        changed = deepcopy(claims)
        changed[0]['research_rationale'] += ' New research qualification.'
        after = dispatch.check_selected(self.repo, folder, changed)
        self.assertTrue(after['ok'])
        self.assertNotEqual(before['members'][0]['claim_sha256'], after['members'][0]['claim_sha256'])
        changed[0]['instrument_id'] = 'EO:2'
        rejected = dispatch.check_selected(self.repo, folder, changed)
        self.assertFalse(rejected['ok'])
        self.assertIn('selected_claim_stale_dossier', json.dumps(rejected))

    def test_selected_source_substitution_cannot_reuse_another_evidence_id(self):
        folder = self.packet()
        claims = self.claims(('EO:1',))
        claims[0]['operative_clauses'][0]['first_end']['source']['sha256'] = '0' * 64
        result = dispatch.check_selected(self.repo, folder, claims)
        self.assertFalse(result['ok'])
        self.assertIn('selected_source_not_dossier_evidence', json.dumps(result))
        self.assertIn('held_but_different_hash', json.dumps(result))

    def test_stale_packet_source_and_runtime_are_refused(self):
        folder = self.packet()
        claims = self.claims(('EO:1',))
        packet_path = folder / 'PACKET.json'
        original = packet_path.read_bytes()
        doc = json.loads(original)
        doc.pop('fingerprint')
        doc['assembler_code_sha256'] = '0' * 64
        doc['fingerprint'] = batch.digest(batch.canon(doc).encode())
        batch.dump(packet_path, doc)
        with self.assertRaisesRegex(ValueError, 'assembler changed'):
            dispatch.check_selected(self.repo, folder, claims)
        packet_path.write_bytes(original)
        (self.repo / 'jobs/future-source/data/texts/EO_1.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed held source'):
            dispatch.check_selected(self.repo, folder, claims)

    def test_selected_guard_offline_readonly_and_cli_receipt_immutable(self):
        folder = self.packet(missing=('EO:5',))
        claims = self.claims(('EO:1',))
        checker = dispatch.actual_checker()
        checker._VERIFY['left'] = 100
        before = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        with patch.object(dispatch, 'actual_checker', return_value=checker), \
                patch.object(checker, 'verify_by_download', side_effect=AssertionError('network')), \
                patch.object(checker, 'verify_by_archive', side_effect=AssertionError('network')):
            report = dispatch.check_selected(self.repo, folder, claims)
        after = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(report['network_requests'], 0)
        proposed = folder / 'proposed.jsonl'
        T.write_jsonl(proposed, claims)
        receipt = folder / 'selected-v1.json'
        with redirect_stdout(io.StringIO()):
            self.assertEqual(dispatch.main(['--repo', str(self.repo), str(folder), '--claims', str(proposed), '--write', str(receipt)]), 1)
            self.assertEqual(dispatch.main(['--repo', str(self.repo), str(folder), '--claims', str(proposed), '--write', str(receipt)]), 2)
        self.assertTrue(receipt.exists())


if __name__ == '__main__':
    unittest.main()
