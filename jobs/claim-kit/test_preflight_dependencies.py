"""Live preflight code must match every pinned dependency before work resumes."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import batch
import test_batch as B
import test_build as T
import test_completion as C


class PreflightDependencyTests(unittest.TestCase):
    # Reuse the small offline corpus and ordinary workflow helpers without
    # inheriting (and running again) their unrelated integration test methods.
    setUp = T.BuildIntegrationTests.setUp
    run_build = T.BuildIntegrationTests.run_build
    dossier = T.BuildIntegrationTests.dossier
    decision = T.BuildIntegrationTests.decision
    packet = B.BatchTests.packet
    fill = B.BatchTests.fill
    setup_completion = C.CompletionTests.setup_completion
    ref = C.CompletionTests.ref
    checker = C.CompletionTests.checker
    run_completion = C.CompletionTests.run_completion
    add_control = C.CompletionTests.add_control

    def assert_refused(self):
        for check_sources in (True, False):
            with self.subTest(check_sources=check_sources):
                with self.assertRaisesRegex(ValueError, 'preflight dependencies changed'):
                    batch.load_packet(self.folder, self.repo, check_sources=check_sources)
        destination = self.folder / 'refused-apply'
        with self.assertRaisesRegex(ValueError, 'preflight dependencies changed'):
            batch.apply(self.repo, self.folder, destination)
        self.assertFalse(destination.exists())
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], [])
        self.assertIn('preflight dependencies changed', result['outcomes'][0]['error'])
        self.assertFalse((self.repo / self.manifest['publication']['path']).exists())

    def test_ordinary_packet_pins_actual_modules_and_completes(self):
        self.setup_completion()
        packet, dossiers = batch.load_packet(self.folder, self.repo)
        source_root = Path(batch.__file__).resolve().parents[2]
        expected = {
            'excavate.py': batch.file_sha(source_root / 'jobs/claim-kit/excavate.py'),
            'jobs/clause-drafts/segment.py': batch.file_sha(source_root / 'jobs/clause-drafts/segment.py'),
        }
        self.assertEqual(packet['preflight_dependency_sha256'], expected)
        self.assertEqual(batch.preflight_dependency_pins(), expected)
        self.assertEqual(dossiers, {'EO:1': self.dossier('EO:1')})
        self.assertEqual(self.run_completion()['eligible'], ['EO:1'])

    def changed_dependency(self, relative):
        self.setup_completion()
        dependency = Path(batch.__file__).resolve().parents[2] / relative
        original_sha = batch.file_sha
        # Model changed source bytes only for the actual imported dependency;
        # every packet, policy, assembler and evidence hash stays real.
        changed_sha = hashlib.sha256(dependency.read_bytes() + b'\n# changed dependency\n').hexdigest()
        def file_sha(path):
            return changed_sha if Path(path).resolve() == dependency else original_sha(path)
        with patch.object(batch, 'file_sha', side_effect=file_sha):
            self.assert_refused()

    def test_locator_change_refuses_load_apply_and_completion(self):
        self.changed_dependency('jobs/claim-kit/excavate.py')

    def test_segment_change_refuses_load_apply_and_completion(self):
        self.changed_dependency('jobs/clause-drafts/segment.py')

    def rewrite_receipt(self, change):
        self.setup_completion()
        path = self.folder / 'PACKET.json'
        packet = json.loads(path.read_bytes())
        change(packet['preflight_dependency_sha256'])
        packet.pop('fingerprint')
        packet['fingerprint'] = batch.digest(batch.canon(packet).encode())
        batch.dump(path, packet)
        # Keep the outer selection exact; refusal must concern the incomplete
        # dependency receipt, not tampering or a stale manifest file digest.
        self.manifest['members'][0]['packet'] = self.ref(path)
        self.assert_refused()

    def test_old_one_entry_receipt_refuses_load_apply_and_completion(self):
        self.rewrite_receipt(lambda pins: pins.pop('jobs/clause-drafts/segment.py'))

    def test_unknown_dependency_receipt_refuses_load_apply_and_completion(self):
        self.rewrite_receipt(lambda pins: pins.update({'unrecognized.py': '0' * 64}))


if __name__ == '__main__':
    unittest.main()
