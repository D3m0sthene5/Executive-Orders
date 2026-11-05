"""Exact declaration/representation boundaries for held-source handoffs."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import current_evidence as C
import source_supplement as S
import working_text as W


class CurrentDeclarationPinsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.base = self.repo / 'jobs/current-law/output'
        self.base.mkdir(parents=True)
        self.text = 'The current wording remains subject to independent examination.\n'
        self.path = self.base / 'legal.txt'
        self.path.write_bytes(self.text.encode())
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.source = {'url': 'https://example.gov/legal', 'sha256': 'a' * 64}
        self.lead = {'source': self.source, 'snippet': 'current wording'}

    def declaration(self, **changes):
        row = dict(self.source, text_path='legal.txt', text_sha256=self.sha)
        row.update(changes)
        (self.base / 'SOURCES.jsonl').write_text(json.dumps(row) + '\n')

    def enrich(self, lead=None):
        original = copy.deepcopy(lead or self.lead)
        result, = C.enrich_current(self.repo, [original])
        self.assertEqual(original, lead or self.lead)
        return result

    def assert_gap(self, row):
        self.assertIn('evidence_gap', row)
        for key in ('text', 'char_start', 'char_end'):
            self.assertNotIn(key, row)

    def test_exact_manifest_pin_delivers_quote_with_provenance(self):
        self.declaration()
        row = self.enrich()
        self.assertEqual(row['source']['text_sha256'], self.sha)
        self.assertEqual(row['text'], 'current wording')
        self.assertEqual(self.text[row['char_start']:row['char_end']], row['text'])
        self.assertNotIn('evidence_gap', row)

    def test_changed_text_with_same_quote_cannot_renew_declaration(self):
        self.declaration()
        self.path.write_bytes((self.text + 'Different material outside the quote.\n').encode())
        self.assert_gap(self.enrich())

    def test_malformed_declared_pin_remains_uncitable(self):
        for value in ('', 'not-a-sha', 123, False):
            with self.subTest(value=value):
                self.declaration(text_sha256=value)
                self.assert_gap(self.enrich())

    def test_legacy_declaration_without_extract_pin_keeps_existing_behavior(self):
        self.declaration()
        p = self.base / 'SOURCES.jsonl'
        row = json.loads(p.read_text())
        row.pop('text_sha256')
        p.write_text(json.dumps(row) + '\n')
        self.assertNotIn('evidence_gap', self.enrich())

    def test_wrong_original_identity_does_not_deliver_text(self):
        for field, value in [('url', 'https://example.gov/wrong'), ('sha256', 'b' * 64)]:
            with self.subTest(field=field):
                self.declaration(**{field: value})
                self.assert_gap(self.enrich())

    def test_direct_exact_pin_does_not_depend_on_stale_alternative(self):
        self.declaration(text_sha256='b' * 64)
        lead = copy.deepcopy(self.lead)
        lead['source'].update(text_path='legal.txt', text_sha256=self.sha)
        self.assertNotIn('evidence_gap', self.enrich(lead))

    def test_unpinned_direct_source_path_cannot_bypass_stale_declaration(self):
        self.declaration(text_sha256='b' * 64)
        lead = copy.deepcopy(self.lead)
        lead['source']['text_path'] = 'legal.txt'
        self.assert_gap(self.enrich(lead))

    def test_unpinned_direct_item_path_cannot_bypass_stale_declaration(self):
        self.declaration(text_sha256='b' * 64)
        lead = copy.deepcopy(self.lead)
        lead['text_path'] = 'legal.txt'
        self.assert_gap(self.enrich(lead))

    def test_repo_relative_direct_alias_keeps_matching_declaration_pin(self):
        self.declaration(text_sha256='b' * 64)
        lead = copy.deepcopy(self.lead)
        lead['source']['text_path'] = self.path.relative_to(self.repo).as_posix()
        self.assert_gap(self.enrich(lead))

    def test_unpinned_direct_source_with_exact_manifest_pin_delivers_text(self):
        self.declaration()
        lead = copy.deepcopy(self.lead)
        lead['source']['text_path'] = 'legal.txt'
        self.assertNotIn('evidence_gap', self.enrich(lead))

    def test_legacy_duplicate_does_not_erase_matching_stale_pin(self):
        self.declaration(text_sha256='b' * 64)
        manifest = self.base / 'SOURCES.jsonl'
        legacy = dict(self.source, text_path='legal.txt')
        with manifest.open('a') as stream:
            stream.write(json.dumps(legacy) + '\n')
        self.assert_gap(self.enrich())

    def test_other_path_manifest_does_not_block_unpinned_direct_witness(self):
        self.declaration(text_path='different.txt', text_sha256='b' * 64)
        lead = copy.deepcopy(self.lead)
        lead['source']['text_path'] = 'legal.txt'
        self.assertNotIn('evidence_gap', self.enrich(lead))

    def test_original_cache_can_deliver_independently_of_stale_extract(self):
        cache = self.base / 'original.html'
        cache.write_bytes(self.text.encode())
        self.source['sha256'] = self.sha
        self.declaration(text_sha256='b' * 64, cache_path='original.html')
        row = self.enrich()
        self.assertEqual(row['source']['text_path'], cache.relative_to(self.repo).as_posix())
        self.assertEqual(row['source']['sha256'], self.sha)


class OfficialSupplementIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.path = self.repo / 'research/source/text.txt'
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b'An exact held excerpt with two declared representations.\n')
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.rel = self.path.relative_to(self.repo).as_posix()
        self.source = {'url': 'https://example.gov/official', 'sha256': 'a' * 64,
                       'text_path': self.rel, 'text_sha256': self.sha,
                       'local_path': 'research/source/raw.pdf', 'page_or_item': 'page 1'}
        self.rows = [self.record(False), self.record(True)]

    def record(self, official):
        return {'kind': 'original_representation', 'instrument_id': 'EO:13286',
                'produced_by': 'fr-originals' if official else 'app-executive-orders',
                'data': {'sha256': 'a' * 64 if official else 'c' * 64,
                         'url': 'https://example.gov/official' if official else 'https://example.test/mirror',
                         'grade': 'official_original' if official else 'mirror_transcription',
                         'acceptable_as_original': official, 'text_path': self.rel,
                         'text_sha256': self.sha, 'needs_page_check': False}}

    def index(self, rows=None):
        path = self.repo / 'jobs/future-source/output/FRAGMENTS.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(r) + '\n' for r in (rows if rows is not None else self.rows)))
        return W.Index(self.repo)

    def test_exact_official_selection_is_not_rewritten_to_shared_mirror(self):
        source = copy.deepcopy(self.source)
        self.assertIsNone(S.registered(self.repo, self.source, self.index()))
        self.assertEqual(source, self.source)

    def test_unregistered_source_does_not_acquire_official_identity(self):
        selected = copy.deepcopy(self.source)
        selected['url'] = 'https://example.gov/different'
        selected['sha256'] = 'd' * 64
        held = S.registered(self.repo, selected, self.index())
        self.assertEqual(held['grade'], 'mirror_transcription')
        self.assertFalse(held['acceptable_as_original'])
        self.assertEqual(held['sha256'], 'c' * 64)

    def test_changed_official_extract_cannot_keep_exact_official_exemption(self):
        index = self.index()
        self.path.write_bytes(self.path.read_bytes() + b'changed')
        self.assertFalse(index.exact_official(self.source))

    def test_existing_provisional_only_route_preserves_registered_grade(self):
        held = S.registered(self.repo, self.source, self.index(self.rows[:1]))
        self.assertEqual(held['grade'], 'mirror_transcription')
        self.assertEqual(held['instrument_id'], 'EO:13286')
        self.assertEqual(held['url'], 'https://example.test/mirror')
        self.assertNotIn('local_path', held)


if __name__ == '__main__':
    unittest.main()
