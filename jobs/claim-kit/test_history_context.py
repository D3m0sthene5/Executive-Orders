"""Ordinary consumers retain bounded histories and refuse stale research."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import history_context as C
import provision_history as H
import test_provision_history as F
import test_build as B
import batch


class HistoryContextTests(unittest.TestCase):
    setUp = F.ProvisionHistoryTests.setUp
    source = F.ProvisionHistoryTests.source
    add_provision = F.ProvisionHistoryTests.add_provision
    write = F.ProvisionHistoryTests.write

    def test_scopes_unknowns_and_no_unrelated_order(self):
        self.bundle['provisions'][0]['valid_start'] = None
        self.review_scopes[self.bundle['provisions'][0]['provision_id']] = ('text',)
        self.write()
        c = C.collect(self.repo, ['EO:1'], [self.bundle_path])
        q = C.for_order(c, 'EO:1')['queries'][0]
        self.assertEqual(q['operative_state'], 'unknown')
        self.assertFalse(q['canonical_approval'])
        self.assertEqual(C.for_order(c, 'EO:2')['queries'], [])
        C.verify(self.repo, ['EO:1'], c)
        earlier = C.collect(self.repo, ['EO:1'], [self.bundle_path], '2020-01-01')
        with self.assertRaisesRegex(ValueError, 'query date differs'):
            C.verify(self.repo, ['EO:1'], earlier)

    def test_changed_source_bundle_review_or_adapter_refused(self):
        self.write()
        c = C.collect(self.repo, ['EO:1'], [self.bundle_path])
        changed = deepcopy(c); changed['adapter_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'changed reviewed history'):
            C.verify(self.repo, ['EO:1'], changed)
        self.bundle['coverage_notice'] = 'changed coverage'
        self.write()
        with self.assertRaisesRegex(ValueError, 'changed reviewed history'):
            C.verify(self.repo, ['EO:1'], c)
        c = C.collect(self.repo, ['EO:1'], [self.bundle_path])
        self.review_path.write_bytes(self.review_path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            C.verify(self.repo, ['EO:1'], c)

    def test_bounded_explicit_safe_selection(self):
        self.write()
        for paths in ([], [self.bundle_path] * 2, [self.repo.parent/'outside.json']):
            with self.assertRaises(ValueError):
                C.collect(self.repo, ['EO:1'], paths)
        with self.assertRaisesRegex(ValueError, 'no selected order'):
            C.collect(self.repo, ['EO:77'], [self.bundle_path])


class BatchHistoryTests(unittest.TestCase):
    setUp = B.BuildIntegrationTests.setUp
    run_build = B.BuildIntegrationTests.run_build

    def test_ordinary_prepare_view_and_live_refusal(self):
        # Use source-history fixture in the real offline builder's repository.
        f = F.ProvisionHistoryTests(); f.setUp(); self.addCleanup(f.doCleanups)
        f.write()
        import shutil
        shutil.copytree(f.repo/'research', self.repo/'research', dirs_exist_ok=True)
        self.run_build()
        folder = self.repo/'research/packet'
        history_path = self.repo/'research/history.json'
        batch.prepare(self.repo,self.out,folder,['EO:1','EO:2'],'producer',history_bundles=[history_path])
        packet, dossiers = batch.load_packet(folder,self.repo)
        self.assertIn('reviewed_histories', packet)
        self.assertIn('Reviewed provision histories', (folder/'READ.md').read_text())
        many = batch.views(self.repo,folder,['EO:1','EO:2'])
        self.assertEqual(many['EO:1'], batch.view(self.repo,folder,'EO:1'))
        self.assertIn('P17-EO_1-duty', many['EO:1'])
        self.assertNotIn('P17-EO_1-duty', many['EO:2'])
        # Source is no longer valid; the ordinary consumer must refuse.
        src = self.repo/f.bundle['provisions'][0]['source']['text_path']
        src.write_bytes(src.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'stale_source'):
            batch.view(self.repo,folder,'EO:1')

    def test_many_matches_legacy_and_validates_selection(self):
        self.run_build(); folder=self.repo/'research/plain'
        batch.prepare(self.repo,self.out,folder,['EO:1','EO:2'],'producer')
        self.assertEqual(batch.views(self.repo,folder,['EO:1','EO:2']),
                         {i:batch.view(self.repo,folder,i) for i in ['EO:1','EO:2']})
        for ids in ([],['EO:1','EO:1'],['EO:88']):
            with self.assertRaises(ValueError):batch.views(self.repo,folder,ids)


if __name__ == '__main__':unittest.main()
