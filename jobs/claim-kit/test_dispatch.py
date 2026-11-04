"""Real frozen packets and the actual custody policy; no model/network calls."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_build as T
import batch
import dispatch
import kit


class DispatchTests(unittest.TestCase):
    setUp = T.BuildIntegrationTests.setUp
    run_build = T.BuildIntegrationTests.run_build

    def retain(self, missing=()):
        records = json.loads((self.repo/'jobs/future-source/data/PROVENANCE.json').read_text())['representations']
        rows = []
        for r in records:
            raw = 'raw/' + r['instrument_id'].replace(':', '_') + '.bin'
            path = self.repo/'jobs/future-source/output'/raw
            if r['instrument_id'] not in missing:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((self.repo/r['text_path']).read_bytes())
            rows.append({**r['source'], 'text_path': r['text_path'], 'cache_path': raw,
                         'instrument_ids': [r['instrument_id']]})
        T.write_jsonl(self.repo/'jobs/future-source/output/SOURCES.jsonl', rows)

    def packet(self, ids=('EO:1', 'EO:2'), missing=()):
        self.retain(missing)
        self.run_build()
        folder = self.repo/'research/test/packet'
        batch.prepare(self.repo, self.out, folder, list(ids), 'producer')
        return folder

    def cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = kit.main(['--repo', str(self.repo), *map(str, args)])
        return code, out.getvalue()

    def test_prepare_wires_source_check_and_deduplicates_shared_references(self):
        folder = self.packet()
        report = json.loads((folder/'DISPATCH_CHECK.json').read_text())
        self.assertTrue(report['ok'])
        self.assertEqual(report['dispatchable_ids'], ['EO:1', 'EO:2'])
        # Original + inventory reuse one source; the shared EO:5 actor is checked once.
        self.assertEqual(report['unique_custody_checks'], 3)
        self.assertEqual(report['unique_required_text_checks'], 2)
        self.assertFalse(report['scientific_approval'])
        self.assertIsNone(report['model_tokens'])
        self.assertFalse(batch.rows(folder/'decisions.csv')[0]['approved'] == 'true')

    def test_record_only_blocks_then_exact_retained_bytes_reopen_without_reprepare(self):
        folder = self.packet(missing=('EO:1',))
        before = (folder/'PACKET.json').read_bytes()
        blocked = dispatch.check(self.repo, folder)
        self.assertEqual(blocked['source_blocked_ids'], ['EO:1'])
        self.assertEqual(blocked['dispatchable_ids'], ['EO:2'])
        self.assertIn('custody_record_only', json.dumps(blocked['members'][0]['blockers']))
        self.retain()
        self.assertTrue(dispatch.check(self.repo, folder)['ok'])
        self.assertEqual(before, (folder/'PACKET.json').read_bytes())

    def test_optional_actor_custody_gap_does_not_choose_or_block_legal_theory(self):
        folder = self.packet(missing=('EO:5',))
        report = dispatch.check(self.repo, folder)
        self.assertTrue(report['ok'])
        self.assertIn('custody_record_only', json.dumps(report))
        self.assertTrue(dispatch.summary(report)['exceptions'])

    def test_raw_corruption_refuses_but_text_unchanged(self):
        folder = self.packet()
        (self.repo/'jobs/future-source/output/raw/EO_1.bin').write_bytes(b'corrupt')
        report = dispatch.check(self.repo, folder)
        self.assertFalse(report['ok'])
        self.assertIn('held_record_but_local_bytes_differ', json.dumps(report))

    def test_provisional_working_text_remains_researchable_without_authentication(self):
        T.BuildIntegrationTests.confirmed_derivative(self)
        folder = self.packet(ids=('EO:2',))
        packet, dossiers = batch.load_packet(folder, self.repo)
        original = dossiers['EO:2']['evidence'][dossiers['EO:2']['original_source_id']]
        self.assertFalse(original['acceptable_as_original'])
        report = dispatch.check(self.repo, folder)
        self.assertTrue(report['ok'])
        self.assertFalse(report['scientific_approval'])
        self.assertTrue(report['members'][0]['research_tasks'])
        self.assertEqual(batch.rows(folder/'decisions.csv')[0]['original_confirmed'], 'false')

    def test_text_and_packet_tampering_refused(self):
        folder = self.packet()
        p = folder/'PACKET.json'
        original = p.read_bytes()
        p.write_bytes(original.replace(b'2026-10-14', b'2026-10-15'))
        with self.assertRaisesRegex(ValueError, 'changed work package'):
            dispatch.check(self.repo, folder)
        p.write_bytes(original)
        (self.repo/'jobs/future-source/data/texts/EO_1.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed held source'):
            dispatch.check(self.repo, folder)

    def test_runtime_change_refused_even_with_valid_packet_seal(self):
        folder = self.packet()
        p = folder/'PACKET.json'
        doc = json.loads(p.read_bytes())
        doc.pop('fingerprint')
        doc['assembler_code_sha256'] = '0'*64
        doc['fingerprint'] = batch.digest(batch.canon(doc).encode())
        batch.dump(p, doc)
        with self.assertRaisesRegex(ValueError, 'assembler changed'):
            dispatch.check(self.repo, folder)

    def test_new_relevant_ruling_requires_new_packet(self):
        folder = self.packet()
        rule = self.repo/'research/readiness/owner_rulings/new.md'
        rule.parent.mkdir(parents=True, exist_ok=True)
        rule.write_text('# Ruling\nEO:1 requires a different source examination.\n')
        with self.assertRaisesRegex(ValueError, 'changed prior research'):
            dispatch.check(self.repo, folder)

    def test_offline_even_if_download_budget_initialized_and_no_repository_writes(self):
        folder = self.packet(missing=('EO:1',))
        checker = dispatch.actual_checker()
        checker._VERIFY['left'] = 400
        before = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        with patch.object(dispatch, 'actual_checker', return_value=checker), \
             patch.object(checker, 'verify_by_download', side_effect=AssertionError('network')), \
             patch.object(checker, 'verify_by_archive', side_effect=AssertionError('network')):
            result = dispatch.check(self.repo, folder)
        after = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(result['network_requests'], 0)
        self.assertFalse(result['ok'])

    def test_mixed_packet_cli_nonzero_explicit_subset_and_immutable_receipts(self):
        folder = self.packet(missing=('EO:1',))
        receipt = folder/'dispatch-v2.json'
        code, stdout = self.cli('dispatch-check', folder, '--write', receipt)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)['source_blocked_ids'], ['EO:1'])
        code, _ = self.cli('dispatch-check', folder, '--order', 'EO:2')
        self.assertEqual(code, 0)
        self.assertEqual(self.cli('dispatch-check', folder, '--order', 'EO:999')[0], 2)
        self.assertEqual(self.cli('dispatch-check', folder, '--write', receipt)[0], 2)
        self.assertEqual(self.cli('dispatch-check', folder, '--write', self.repo/'outside.json')[0], 2)

    def test_prepare_cli_blocks_production_but_allows_explicit_source_research(self):
        self.retain(missing=('EO:1',))
        self.run_build()
        folder = self.repo/'research/blocked/packet'
        code, _ = self.cli('prepare', 'EO:1', '--agent', 'producer', '--write', folder)
        self.assertEqual(code, 1)
        self.assertTrue((folder/'PACKET.json').exists())
        other = self.repo/'research/source-research/packet'
        code, stdout = self.cli('prepare', 'EO:1', '--agent', 'producer', '--write', other, '--research-only')
        self.assertEqual(code, 0)
        result = json.loads(stdout)
        self.assertTrue(result['research_only'])
        self.assertFalse(result['dispatch_check']['ok'])


if __name__ == '__main__':
    unittest.main()
