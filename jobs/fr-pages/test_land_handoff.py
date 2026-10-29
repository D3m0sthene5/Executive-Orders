import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import land_handoff as h


class LandHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.out = self.repo / 'jobs/fr-pages/output'; self.out.mkdir(parents=True)
        self.raw, self.text = b'%PDF-1.4\nfixture\n', 'Unreviewed PLO excerpt.\n'
        (self.out / 'extract.pdf').write_bytes(self.raw)
        (self.out / 'text.txt').write_text(self.text)
        self.row = {'url': 'https://example.invalid/issue.pdf#page=2',
                    'sha256': h.sha(self.raw), 'text_sha256': h.sha(self.text.encode()),
                    'cache_path': 'extract.pdf', 'text_path': 'text.txt', 'page_or_item': 'test page',
                    'printed_instrument_id': 'PLO:570', 'instrument_ids': ['PLO:570','EO:7373'],
                    'role': 'official_federal_register_page_of_a_later_instrument',
                    'location_confidence': 'high', 'needs_page_check': False}
        self.manifest = self.out / 'SOURCES.jsonl'
        self.write()

    def write(self, rows=None):
        self.manifest.write_text(''.join(json.dumps(r)+'\n' for r in ([self.row] if rows is None else rows)))

    def run_it(self):
        return h.declaration(self.repo, self.manifest, h.DEFAULT_IDS)

    def test_exact_native_schema_and_actor_separation(self):
        d, a = self.run_it(); entry = d['sources'][0]
        self.assertEqual(d['schema'], 'eo-source-excerpt-declarations/v1')
        self.assertEqual(set(entry), {'alias','instrument_ids','actor_id','reason','source','char_start','char_end'})
        self.assertEqual(set(entry['source']), {'url','sha256','text_path','text_sha256','page_or_item','local_path'})
        self.assertEqual(entry['actor_id'], 'PLO:570')
        self.assertEqual(entry['instrument_ids'], ['EO:7373'])
        self.assertEqual(entry['char_end'], len(self.text))
        self.assertFalse(a['legal_approval']); self.assertFalse(a['original_text_attribution'])

    def test_raw_hash_mismatch_held(self):
        (self.out/'extract.pdf').write_bytes(b'%PDF-changed')
        d,a=self.run_it(); self.assertFalse(d['sources']); self.assertTrue(a['holds'])

    def test_text_hash_mismatch_held(self):
        (self.out/'text.txt').write_text('changed')
        self.assertFalse(self.run_it()[0]['sources'])

    def test_missing_raw_record_only_never_exported(self):
        (self.out/'extract.pdf').unlink()
        self.assertFalse(self.run_it()[0]['sources'])

    def test_medium_confidence_stays_held(self):
        self.row['location_confidence']='medium'; self.write()
        self.assertFalse(self.run_it()[0]['sources'])

    def test_no_target_original_inference(self):
        self.row['printed_instrument_id']='EO:7373'; self.write()
        self.assertFalse(self.run_it()[0]['sources'])

    def test_path_escape_held(self):
        self.row['cache_path']='../../../outside.pdf'; self.write()
        self.assertFalse(self.run_it()[0]['sources'])

    def test_duplicates_merge_target_associations(self):
        self.write([self.row,dict(self.row,instrument_ids=['PLO:570','EO:7510'])])
        d,_=self.run_it(); self.assertEqual(len(d['sources']),1)
        self.assertEqual(d['sources'][0]['instrument_ids'],['EO:7373','EO:7510'])

    def test_conflicting_actor_versions_hold_both(self):
        raw=b'%PDF-1.4\nother\n'; (self.out/'other.pdf').write_bytes(raw)
        self.write([self.row,dict(self.row,cache_path='other.pdf',sha256=h.sha(raw))])
        d,a=self.run_it(); self.assertFalse(d['sources']); self.assertTrue(a['holds'])

    def test_fresh_output_only_and_manifest_pin(self):
        dest=self.repo/'research/handoff'
        _,d,a=h.export(self.repo,self.manifest,h.DEFAULT_IDS,dest)
        self.assertEqual(a['source_manifest_sha256'],h.sha(self.manifest.read_bytes()))
        self.assertTrue((dest/'DECLARATIONS.json').is_file())
        with self.assertRaises(ValueError): h.export(self.repo,self.manifest,h.DEFAULT_IDS,dest)
        with self.assertRaises(ValueError): h.export(self.repo,self.manifest,h.DEFAULT_IDS,self.repo/'jobs/new')

    def test_explicit_acquisition_is_bounded_and_skips_held(self):
        engine=mock.Mock()
        engine.PLO_TABLE='jobs/shepard-citations/output/PLO_TABLE.csv'
        engine.SHEPARD_EDGES='jobs/shepard-citations/output/EDGES.csv'
        engine.plo_index.return_value={570:{},1249:{},4079:{},5000:{},5001:{}}
        engine.auto_wanted.return_value=[{'plo':n,'targets':['EO:7373'],'want_id':str(n)} for n in [570,1249,4079,5000,5001]]
        def run(repo,config,out,cache,prior):
            selected=[json.loads(l) for l in (Path(config)/'data/WANTED.jsonl').read_text().splitlines()]
            settings=json.loads((Path(config)/'settings.json').read_text())
            self.assertEqual([r['plo'] for r in selected],[1249,4079,5000])
            self.assertEqual(settings['max_requests'],24)
            self.assertFalse(settings['try_issue_slice'])
            self.assertFalse(settings['auto_from_shepard']['enabled'])
            self.assertNotIn('JOB_MAX_REQUESTS',os.environ)
            return {'selected':len(selected)}
        engine.run.side_effect=run
        with mock.patch.dict(os.environ,{'JOB_MAX_REQUESTS':'9999'}):
            result=h.acquire(self.repo,h.DEFAULT_IDS,self.repo/'research/acquire',engine=engine)
            self.assertEqual(os.environ['JOB_MAX_REQUESTS'],'9999')
        self.assertEqual(result['selected'],3)

    def test_no_missing_selection_does_not_run_downloader(self):
        engine=mock.Mock(); engine.PLO_TABLE='no-table'; engine.SHEPARD_EDGES='no-edges'
        engine.plo_index.return_value={570:{}}
        engine.auto_wanted.return_value=[{'plo':570,'targets':['EO:7373']}]
        self.assertFalse(h.acquire(self.repo,h.DEFAULT_IDS,self.repo/'research/noop',engine=engine)['network_started'])
        engine.run.assert_not_called()


if __name__=='__main__': unittest.main()
