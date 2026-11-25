"""Naude held-source catalogue at prepare, its supplement, and the advisory Gilbreth pre-screen (offline)."""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import batch as B
import dispatch
import fragment_cache as FC
import held_sources as H
import kit
import source_supplement as S
import test_build as F

STATUTE = ('PUBLIC LAW 1-2\nAN ACT to reorganize the First Board.\nSEC. 3. The duties of the First Board under '
           'the order of 1990 are transferred to the Office, effective January 1, 1995.\n')


class HeldSourcesTests(unittest.TestCase):
    def setUp(self):
        cache = tempfile.TemporaryDirectory(); self.addCleanup(cache.cleanup)
        env = patch.dict(os.environ, {'CLAIM_KIT_CACHE_DIR': cache.name}); env.start(); self.addCleanup(env.stop)
        FC._SHARED.clear(); self.addCleanup(FC._SHARED.clear)
        self.f = F.BuildIntegrationTests(); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.repo = self.f.repo
        code = self.repo / 'jobs/claim-kit/source_supplement.py'
        code.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(S.__file__, code)
        p = patch.object(S, '__file__', str(code)); p.start(); self.addCleanup(p.stop)

    def register(self, held=True, text=STATUTE, ids=('EO:1',), extra=None):
        """A source-ladder-style request row for EO:1: a statute that does not print the order's number."""
        out = self.repo / 'jobs/ladder/output'
        raw = b'%PDF-1.4 synthetic statute bytes\n'
        (out / 'texts').mkdir(parents=True, exist_ok=True)
        (out / 'texts/statute.txt').write_bytes(text.encode())
        if held:
            (out / 'blobs').mkdir(parents=True, exist_ok=True)
            (out / 'blobs/statute.pdf').write_bytes(raw)
        row = {'sha256': hashlib.sha256(raw).hexdigest(), 'url': 'https://example.gov/statute.pdf',
               'cache_path': 'blobs/statute.pdf', 'text_path': 'texts/statute.txt', 'instrument_ids': list(ids),
               'page_or_item': '1 Stat. 2', 'citation': 'Pub. L. 1-2 sec. 3', 'wanted_id': 'queue:EO:1:Pub. L. 1-2',
               **(extra or {})}
        F.write_jsonl(out / 'SOURCES.jsonl', [row])
        return row

    def retain(self):
        """Hold the fixture originals' bytes, as test_dispatch does, so members are dispatchable."""
        records = json.loads((self.repo/'jobs/future-source/data/PROVENANCE.json').read_text())['representations']
        rows = []
        for r in records:
            raw = 'raw/' + r['instrument_id'].replace(':', '_') + '.bin'
            path = self.repo/'jobs/future-source/output'/raw
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((self.repo/r['text_path']).read_bytes())
            rows.append({**r['source'], 'text_path': r['text_path'], 'cache_path': raw,
                         'instrument_ids': [r['instrument_id']]})
        F.write_jsonl(self.repo/'jobs/future-source/output/SOURCES.jsonl', rows)

    def prepare(self, ids=('EO:1', 'EO:2'), dest='research/test/packet'):
        self.retain()
        self.f.run_build()
        folder = self.repo / dest
        B.prepare(self.repo, self.f.out, folder, list(ids), 'producer')
        return folder

    def cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = kit.main(['--repo', str(self.repo), *map(str, args)])
        return code, out.getvalue()

    def test_held_request_source_becomes_supplement_declaration(self):
        row = self.register()
        folder = self.prepare()
        held = json.loads((folder / 'HELD_SOURCES.json').read_text())
        (item,) = held['members']['EO:1']
        self.assertEqual(item['state'], 'supplement_ready')
        self.assertEqual(item['custody_status'], 'held_bytes_verified')
        self.assertEqual(item['excerpts'], [{'char_start': 0, 'char_end': len(STATUTE)}])
        self.assertEqual(held['members']['EO:2'], [])
        decl = json.loads((folder / 'HELD_SUPPLEMENT.json').read_text())
        self.assertEqual(decl['schema'], S.SCHEMA)
        (entry,) = decl['sources']
        self.assertEqual(entry['instrument_ids'], ['EO:1'])
        self.assertEqual(entry['source']['sha256'], row['sha256'])
        self.assertEqual(entry['source']['local_path'], 'jobs/ladder/output/blobs/statute.pdf')
        self.assertEqual(json.loads((folder / 'PREPARE.json').read_text())['held_sources']['declared_excerpts'], 1)

    def test_record_only_bytes_are_listed_for_acquisition_never_declared(self):
        self.register(held=False)
        folder = self.prepare()
        (item,) = json.loads((folder / 'HELD_SOURCES.json').read_text())['members']['EO:1']
        self.assertEqual(item['state'], 'bytes_not_held')
        self.assertEqual(item['custody_status'], 'custody_record_only')
        self.assertFalse((folder / 'HELD_SUPPLEMENT.json').exists())

    def test_own_text_declarations_and_cited_sources_are_not_listed(self):
        # A non-request row declaring the order's own text (an APP mirror, say) is not a source about it.
        self.register(extra={'wanted_id': None})
        folder = self.prepare()
        self.assertEqual(json.loads((folder / 'HELD_SOURCES.json').read_text())['members']['EO:1'], [])
        # A request that fetched a copy printing the order's own text is not listed either.
        self.register(text='EXECUTIVE ORDER 1\nThe First Board shall perform the specified duties.\n')
        folder = self.prepare(dest='research/test/packet2')
        self.assertEqual(json.loads((folder / 'HELD_SOURCES.json').read_text())['members']['EO:1'], [])

    def test_large_unnamed_text_needs_a_declared_span(self):
        self.register(text=STATUTE + ('filler line of the statute\n' * 3000))
        folder = self.prepare()
        (item,) = json.loads((folder / 'HELD_SOURCES.json').read_text())['members']['EO:1']
        self.assertEqual(item['state'], 'held_needs_span')
        self.assertFalse((folder / 'HELD_SUPPLEMENT.json').exists())

    def test_cli_held_supplement_seals_citable_excerpt(self):
        self.register()
        self.retain(); self.f.run_build()
        dest = self.repo / 'research/test/cli'
        code, out = self.cli('prepare', 'EO:1', 'EO:2', '--agent', 'producer', '--write', dest, '--held-supplement')
        result = json.loads(out)
        self.assertEqual(code, 0, out)
        target = self.repo / 'research/test/cli-held'
        self.assertEqual(result['held_supplement']['packet'], str(target))
        self.assertTrue(result['held_supplement']['dispatch_check']['ok'])
        _, dossiers = B.load_packet(target, self.repo)
        added = [k for k in dossiers['EO:1']['evidence'] if k.startswith('SUPPLEMENT:')]
        self.assertEqual(len(added), 1)
        record = dossiers['EO:1']['evidence'][added[0]]
        self.assertEqual(record['text'], STATUTE)
        self.assertEqual(record['role'], 'unreviewed_source_excerpt')
        self.assertFalse(record['basis_eligible'])
        # The supplemented packet cites the source, so it lists nothing further.
        self.assertEqual(json.loads((target / 'HELD_SOURCES.json').read_text())['members']['EO:1'], [])
        self.assertTrue(S.verify(self.repo, target)['exact_lineage_and_source_bytes'])

    def test_cli_held_supplement_without_ready_sources_keeps_one_packet(self):
        self.register(held=False)
        self.retain(); self.f.run_build()
        dest = self.repo / 'research/test/cli'
        code, out = self.cli('prepare', 'EO:1', '--agent', 'producer', '--write', dest, '--held-supplement')
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(out)['held_supplement'], {'packet': None, 'declared_excerpts': 0})
        self.assertFalse((self.repo / 'research/test/cli-held').exists())


class PrescreenTests(unittest.TestCase):
    TASKS = [{'kind': 'actual_event_fact'}]
    ROUTE = 'owner_reviewable_replacement_proposal'

    def source(self, eid, status, page='other page', path='jobs/x/output/t.txt'):
        return {'evidence_id': eid, 'source': {'page_or_item': page, 'text_path': path},
                'checks': [{'status': status, 'result': 'pass' if status in dispatch.PRESCREEN_PASS else 'skip'}]}

    def test_flags_correction_order_without_held_event_source(self):
        sources = [self.source('ORIGINAL:EO:1', 'held_bytes_verified', page='own page'),
                   self.source('TERM:EO:1#5', 'held_bytes_verified', page='own page'),
                   self.source('FACT:report', 'custody_record_only')]
        result = dispatch.prescreen(sources, self.TASKS, self.ROUTE)
        self.assertTrue(result['flag'])
        self.assertTrue(result['advisory_only'])
        self.assertEqual((result['event_sources'], result['event_sources_held']), (1, 0))

    def test_held_event_source_or_no_event_task_is_not_flagged(self):
        held = [self.source('FACT:report', 'held_bytes_in_release_or_repo')]
        self.assertFalse(dispatch.prescreen(held, self.TASKS, self.ROUTE)['flag'])
        self.assertFalse(dispatch.prescreen([], [{'kind': 'operative_current_law'}], self.ROUTE)['flag'])
        # A Presidency Project mirror of the order is not an event source.
        mirror = [self.source('TERM:EO:1#9', 'held_bytes_verified', path='jobs/app-transcriptions/output/t.txt')]
        self.assertTrue(dispatch.prescreen(mirror, self.TASKS, self.ROUTE)['flag'])

    def test_yes_route_is_never_screened(self):
        result = dispatch.prescreen([], self.TASKS, 'new_producer_proposal')
        self.assertEqual((result['applies'], result['flag']), (False, False))

    def test_prepare_records_prescreen_without_changing_dispatch(self):
        t = HeldSourcesTests('test_held_request_source_becomes_supplement_declaration'); t.setUp()
        self.addCleanup(t.doCleanups)
        folder = t.prepare()
        report = json.loads((folder / 'DISPATCH_CHECK.json').read_text())
        self.assertTrue(report['ok'])
        self.assertEqual(report['prescreen']['flagged_ids'], [])
        self.assertTrue(report['prescreen']['advisory_only'])
        self.assertTrue(all(m['prescreen']['applies'] is False for m in report['members']))
        self.assertIn('prescreen', dispatch.summary(report))
        with patch.object(dispatch, 'prescreen', return_value={'rule': 'gilbreth_r3r', 'applies': True, 'flag': True}):
            flagged = dispatch.check(t.repo, folder)
        self.assertEqual(flagged['prescreen']['flagged_ids'], ['EO:1', 'EO:2'])
        self.assertTrue(flagged['ok'])
        self.assertEqual(flagged['dispatchable_ids'], report['dispatchable_ids'])


if __name__ == '__main__':
    unittest.main()
