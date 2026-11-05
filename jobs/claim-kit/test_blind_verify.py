"""Explicit-card byte verification: confinement, exactness and blind boundaries."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('blind_verify_tested', HERE / 'blind_verify.py')
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)


class BlindVerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'held').mkdir()
        self.text = 'préface\r\nThe board shall act.\r\n尾\n'
        (self.root / 'held/text.txt').write_bytes(self.text.encode('utf-8'))
        (self.root / 'held/raw.pdf').write_bytes(b'%PDF retained exact original\r\n')
        self.source = {'text_path': 'held/text.txt',
                       'text_sha256': hashlib.sha256(self.text.encode()).hexdigest(),
                       'char_start': 9, 'char_end': 29, 'quote': self.text[9:29],
                       'sha256': hashlib.sha256((self.root / 'held/raw.pdf').read_bytes()).hexdigest(),
                       'local_path': 'held/raw.pdf'}
        self.card = {'item_id': 'opaque-a', 'track': 'C',
                     'claim': {'schema': 'eo-lifecycle-claim/v1', 'source': self.source}}
        self.file = self.root / 'card.json'

    def verify(self, card=None):
        self.file.write_text(json.dumps(self.card if card is None else card), encoding='utf-8')
        return B.verify_files([self.file], self.root, ['held'])

    def only_source(self, report):
        self.assertEqual(len(report['cards']), 1, report)
        self.assertEqual(len(report['cards'][0]['sources']), 1, report)
        return report['cards'][0]['sources'][0]

    def card_only_reader(self):
        original = B._read
        def read(root, name, allowed):
            if root / name != self.file:
                raise AssertionError('must not read sources')
            return original(root, name, allowed)
        return read

    def test_native_card_exact_crlf_unicode_pass_and_determinism(self):
        first = self.verify()
        self.assertTrue(first['ok'], first)
        self.assertTrue(first['cards'][0]['text_checks_passed'])
        self.assertEqual(first, B.verify_files([self.file], self.root, ['held']))
        self.assertEqual(len(self.only_source(first)['files']), 2)

    def read_with_final_stat_change(self, field):
        original = B._path
        calls = []

        def observed_path(*args):
            path = original(*args)  # Preserve actual confinement/symlink checks.
            calls.append(path)
            if len(calls) != 2:
                return path
            saved = path.stat()
            values = list(saved)
            nanoseconds = {k: getattr(saved, k) for k in ('st_atime_ns', 'st_mtime_ns', 'st_ctime_ns')}
            position = {'st_mode': 0, 'st_ino': 1, 'st_dev': 2, 'st_nlink': 3,
                        'st_uid': 4, 'st_gid': 5, 'st_size': 6, 'st_atime': 7,
                        'st_mtime_ns': 8, 'st_ctime_ns': 9}[field]
            values[position] += 1
            if field.endswith('_ns'):
                nanoseconds[field] += 1_000_000_000
            elif field == 'st_atime':
                nanoseconds['st_atime_ns'] += 1_000_000_000
            changed = os.stat_result(values, nanoseconds)
            if field == 'st_atime':
                stable = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                          'st_size', 'st_mtime_ns', 'st_ctime_ns')
                self.assertEqual(tuple(getattr(saved, k) for k in stable),
                                 tuple(getattr(changed, k) for k in stable))
                self.assertNotEqual(saved.st_atime, changed.st_atime)
            return SimpleNamespace(stat=lambda: changed)

        with patch.object(B, '_path', side_effect=observed_path):
            return B._read(self.root, 'held/text.txt', (self.root / 'held',))

    def test_source_read_accepts_only_access_metadata_drift(self):
        expected = (self.root / 'held/text.txt').read_bytes()
        self.assertEqual(B._read(self.root, 'held/text.txt', (self.root / 'held',)), expected)
        self.assertEqual(self.read_with_final_stat_change('st_atime'), expected)

    def test_source_read_refuses_each_stable_metadata_change(self):
        for field in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                      'st_size', 'st_mtime_ns', 'st_ctime_ns'):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'source_changed_during_read'):
                self.read_with_final_stat_change(field)

    def read_with_descriptor_stat_change(self, position=None, field=None):
        original_path = B._path
        original_fstat = B.os.fstat
        events, descriptors = [], []
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                  'st_size', 'st_mtime_ns', 'st_ctime_ns')

        def observed_path(*args):
            path = original_path(*args)
            events.append('path')
            if len(events) > 1:
                self.assertEqual(events, ['path', 'fd', 'fd', 'path'])
                # Final path validation must happen while the descriptor is open.
                original_fstat(descriptors[0])
            return path

        def observed_fstat(fd):
            saved = original_fstat(fd)
            descriptors.append(fd)
            events.append('fd')
            values = {key: getattr(saved, key) for key in fields}
            # Stable within fstat, deliberately different from path stat.
            values['st_ctime_ns'] += 1_000_000_000
            if len(descriptors) == position:
                values[field] += 1
            return SimpleNamespace(**values)

        with patch.object(B, '_path', side_effect=observed_path), \
                patch.object(B.os, 'fstat', side_effect=observed_fstat):
            raw = B._read(self.root, 'held/text.txt', (self.root / 'held',))
        return raw, events

    def test_same_api_stability_accepts_windows_ctime_difference(self):
        raw, events = self.read_with_descriptor_stat_change()
        self.assertEqual(raw, (self.root / 'held/text.txt').read_bytes())
        self.assertEqual(events, ['path', 'fd', 'fd', 'path', 'fd'])

    def test_each_descriptor_metadata_mutation_still_refused(self):
        for position in (1, 2, 3):
            for field in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                          'st_size', 'st_mtime_ns', 'st_ctime_ns'):
                with self.subTest(position=position, field=field), \
                        self.assertRaisesRegex(ValueError, 'source_changed_during_read'):
                    self.read_with_descriptor_stat_change(position, field)

    def test_existing_assembler_exact_routine_is_used(self):
        with patch.object(B.A, '_source_errors', wraps=B.A._source_errors) as reuse:
            self.assertTrue(self.verify()['ok'])
            reuse.assert_called_once()

    def test_mutations_fail_closed(self):
        mutations = [{'text_sha256': '0' * 64}, {'sha256': '0' * 64},
                     {'text_sha256': 'bad'}, {'sha256': None}, {'char_start': True},
                     {'char_end': False}, {'char_start': -1}, {'char_end': 10000},
                     {'char_end': 9}, {'char_start': '9'}, {'quote': 'plausible but not held'},
                     {'quote': ''}, {'quote': None}, {'text_path': None},
                     {'local_path': ''}, {'local_path': 'held/missing.pdf'},
                     {'text_path': 'held/missing.txt'}]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                card = deepcopy(self.card)
                card['claim']['source'].update(mutation)
                report = self.verify(card)
                self.assertFalse(report['ok'], mutation)
                self.assertTrue(self.only_source(report)['errors'], report)

    def test_missing_offsets_not_reconstructed_from_matching_quote(self):
        del self.source['char_start']
        self.assertIn('quote_offsets', self.only_source(self.verify())['errors'])

    def test_no_newline_translation_or_byte_offset_substitution(self):
        self.source['char_start'] += 1  # UTF-8 bytes differ from code points here.
        self.assertFalse(self.verify()['ok'])
        self.source['char_start'] -= 1
        self.source['quote'] = self.source['quote'].replace('\r\n', '\n')
        # Select a span containing CRLF to make the newline distinction explicit.
        self.source.update(char_start=0, char_end=len(self.text), quote=self.text.replace('\r\n', '\n'))
        self.assertFalse(self.verify()['ok'])

    def test_raw_required_for_claims_and_unresolved_for_text_records(self):
        del self.source['local_path']
        self.assertIn('raw_path_missing', self.only_source(self.verify())['errors'])
        record = {'records': [{'source': self.source, 'norm_text': self.source['quote']}]}
        report = self.verify(record)
        self.assertFalse(report['ok'])
        self.assertTrue(report['cards'][0]['text_checks_passed'])
        source = self.only_source(report)
        self.assertEqual(source['unresolved'], ['raw_path_missing'])
        self.assertEqual(source['errors'], [])
        self.assertFalse(source['raw_verified'])
        del self.source['sha256']
        source = self.only_source(self.verify(record))
        self.assertTrue(source['text_verified'])
        self.assertEqual(source['errors'], [])

    def test_all_raw_aliases_checked(self):
        self.source['download_path'] = 'held/missing.pdf'
        self.assertFalse(self.verify()['ok'])
        self.source['download_path'] = 'held/raw.pdf'
        self.source['local_file'] = 'held/raw.pdf'
        self.assertTrue(self.verify()['ok'])

    def test_archival_hash_alias(self):
        self.source['archival_id'] = 'opaque archive'
        self.source['local_file_sha256'] = self.source.pop('sha256')
        self.assertTrue(self.verify()['ok'])

    def test_rejects_all_unsafe_paths_before_any_source_read(self):
        (self.root / 'other').mkdir()
        (self.root / 'other/key.json').write_text('private')
        for name in ('../outside', 'held/../other/key.json', '/absolute',
                     'C:/Windows/key', 'held\\key', 'other/key.json', 'held/./text.txt'):
            with self.subTest(name=name):
                card = deepcopy(self.card)
                card['claim']['source']['local_path'] = name
                with patch.object(B, '_read', side_effect=self.card_only_reader()), \
                     patch.object(B.A, '_source_errors', side_effect=AssertionError('must not read')):
                    self.assertFalse(self.verify(card)['ok'])

    def test_symlink_escapes_and_inroot_symlinks_refused(self):
        link = self.root / 'held/link'
        try:
            link.symlink_to(self.root / 'card.json')
        except OSError:
            self.skipTest('symlinks unavailable')
        self.source['text_path'] = 'held/link'
        self.assertFalse(self.verify()['ok'])
        link.unlink()
        link.symlink_to(self.root / 'held/text.txt')
        self.assertFalse(self.verify()['ok'])

    def test_symlink_loops_return_json_refusal(self):
        loop = self.root / 'held/loop'
        try:
            loop.symlink_to('loop')
        except OSError:
            self.skipTest('symlinks unavailable')
        self.source['text_path'] = 'held/loop'
        self.assertFalse(self.verify()['ok'])
        self.assertFalse(B.verify_files([self.file], loop, ['held'])['ok'])
        self.assertFalse(B.verify_files([self.file], self.root, ['held/loop'])['ok'])
        self.assertFalse(B.verify_files([loop], self.root, ['held'])['ok'])

    def test_directories_and_malformed_utf8_refused(self):
        self.source['text_path'] = 'held'
        self.assertFalse(self.verify()['ok'])
        self.source['text_path'] = 'held/text.txt'
        (self.root / 'held/text.txt').write_bytes(b'\xff')
        self.assertFalse(self.verify()['ok'])

    def test_nested_interval_bound_and_source_refs_checked(self):
        payload = {'occurrence_interval': {'start_basis': {'witness': deepcopy(self.source)}},
                   'source_refs': [deepcopy(self.source)]}
        report = self.verify(payload)
        self.assertTrue(report['ok'], report)
        self.assertEqual(len(report['cards'][0]['sources']), 2)
        payload['occurrence_interval']['start_basis']['witness']['quote'] = 'changed interval quote'
        self.assertFalse(self.verify(payload)['ok'])

    def test_actual_norton_nested_bound_witness_shape(self):
        raw_source = deepcopy(self.source)
        raw_source['raw_path'] = raw_source.pop('local_path')
        witness = {'source': {k: v for k, v in raw_source.items()
                              if k not in ('quote', 'char_start', 'char_end')},
                   'text': raw_source['quote'], 'char_start': raw_source['char_start'],
                   'char_end': raw_source['char_end']}
        self.source['norton_factual_event'] = {'occurrence_interval': {
            'start': '2000-01-01', 'end': '2000-02-01', 'occurrence': 'established',
            'start_basis': {'reason': 'Supplied dated source witness.', 'witness': witness},
            'end_basis': {'reason': 'Same source marks upper bound.', 'witness': 'occurrence_span'}}}
        report = self.verify()
        self.assertTrue(report['ok'], report)
        self.assertEqual(len(report['cards'][0]['sources']), 2)
        witness['text'] = 'changed witness'
        self.assertFalse(self.verify()['ok'])
        witness['text'] = raw_source['quote']
        witness['source']['raw_path'] = '../forbidden-key'
        self.assertFalse(self.verify()['ok'])
        witness['source']['raw_path'] = 'held/raw.pdf'
        witness['source']['char_start'] = 0
        report = self.verify()
        self.assertFalse(report['ok'], report)
        self.assertEqual(len(report['cards']), 1, report)
        sources = {source['locus']: source for source in report['cards'][0]['sources']}
        bound = '$.source.norton_factual_event.occurrence_interval.start_basis.witness.source'
        self.assertEqual(set(sources), {'$.source', bound}, report)
        self.assertIn('conflicting_record_span', sources[bound]['errors'], report)

    def test_lfs_pointer_is_not_retained_source_bytes_even_with_matching_pin(self):
        pointer = b'version https://git-lfs.github.com/spec/v1\noid sha256:' + b'0' * 64 + b'\nsize 20\n'
        (self.root / 'held/raw.pdf').write_bytes(pointer)
        self.source['sha256'] = hashlib.sha256(pointer).hexdigest()
        report = self.verify()
        self.assertFalse(report['ok'])
        self.assertIn('original_lfs_pointer', self.only_source(report)['errors'])
        (self.root / 'held/text.txt').write_bytes(pointer)
        self.source.update(text_sha256=hashlib.sha256(pointer).hexdigest(), char_start=0,
                           char_end=7, quote='version')
        report = self.verify()
        self.assertFalse(report['cards'][0]['text_checks_passed'])
        self.assertIn('text_lfs_pointer', self.only_source(report)['errors'])

    def test_raw_path_alias_and_conflicting_alias_bytes(self):
        self.source['raw_path'] = self.source.pop('local_path')
        self.assertTrue(self.verify()['ok'])
        (self.root / 'held/other.pdf').write_bytes(b'wrong bytes')
        self.source['local_path'] = 'held/other.pdf'
        self.assertFalse(self.verify()['ok'])

    def test_fingerprint_field_is_retained_in_canonical_card_hash(self):
        self.card['claim']['fingerprint'] = 'one'
        one = self.verify()['cards'][0]['payload_sha256']
        self.card['claim']['fingerprint'] = 'two'
        self.assertNotEqual(one, self.verify()['cards'][0]['payload_sha256'])

    def test_no_canonical_lookup_or_key_reads(self):
        # Those files need not even exist; their metadata is intentionally inert.
        self.card['claim'].update(claim_kit={'dossier_sha256': '0' * 64},
                                  official_fixity_record='forbidden/key.json',
                                  source_notes='opaque reviewer supplied note')
        accessed = []
        original = Path.read_bytes
        def read(path):
            accessed.append(path)
            return original(path)
        with patch.object(Path, 'read_bytes', read), \
             patch.object(B.A, 'check_claim', side_effect=AssertionError('no claim lookup')):
            self.assertTrue(self.verify()['ok'])
        self.assertEqual(accessed, [])
        # Source reads use explicit descriptors. The shared assembler routine
        # consumes the pinned bytes without opening files or reading siblings.

    def test_empty_no_sources_and_malformed_card_fail(self):
        for value in ([], {'records': []}, {'claim': None}, {}, 8):
            with self.subTest(value=value):
                self.assertFalse(self.verify(value)['ok'])
        self.assertFalse(B.verify_files([], self.root, ['held'])['ok'])
        self.assertFalse(B.verify_files([self.file], self.root, [])['ok'])
        self.assertFalse(B.verify_files([self.file], self.root, ['missing'])['ok'])

    def test_json_duplicate_nonfinite_and_invalid_utf8_refused(self):
        for raw in (b'{"claim":{},"claim":{}}', b'{"x":NaN}', b'{"x":1e999}', b'\xff', b'{'):
            self.file.write_bytes(raw)
            self.assertEqual(B.verify_files([self.file], self.root, ['held'])['inputs'][0]['errors'],
                             ['card_unavailable_or_malformed'])

    def test_multiple_cards_jsonl_and_repeat_files(self):
        self.file = self.root / 'cards.jsonl'
        self.file.write_text('\n'.join(json.dumps(self.card) for _ in range(2)) + '\n')
        report = B.verify_files([self.file, self.file], self.root, ['held'])
        self.assertTrue(report['ok'])
        self.assertEqual(len(report['cards']), 4)

    def test_source_changes_during_reused_check_refused(self):
        original = B.A._source_errors
        def changed(*args, **kwargs):
            errors = original(*args, **kwargs)
            (self.root / 'held/raw.pdf').write_bytes(b'changed')
            return errors
        with patch.object(B.A, '_source_errors', changed):
            self.assertFalse(self.verify()['ok'])

    def test_frozen_card_pin_catches_changed_interval_before_source_reads(self):
        self.card['claim']['occurrence_interval'] = {'start': '2000-01-01', 'end': '2000-02-01'}
        self.verify()
        pin = hashlib.sha256(self.file.read_bytes()).hexdigest()
        self.assertTrue(B.verify_files([self.file], self.root, ['held'], [pin])['ok'])
        self.card['claim']['occurrence_interval']['end'] = '2000-03-01'
        self.verify()
        with patch.object(B, '_read', side_effect=self.card_only_reader()):
            report = B.verify_files([self.file], self.root, ['held'], [pin])
        self.assertFalse(report['ok'])
        self.assertEqual(report['inputs'][0]['errors'], ['card_hash_mismatch'])
        self.assertFalse(B.verify_files([self.file], self.root, ['held'], [])['ok'])
        self.assertFalse(B.verify_files([self.file], self.root, ['held'], ['bad'])['ok'])

    def test_bad_unicode_card_is_machine_refusal(self):
        self.file.write_bytes(b'{"quote":"\\ud800"}')
        report = B.verify_files([self.file], self.root, ['held'])
        self.assertFalse(report['ok'])
        self.assertEqual(report['cards'][0]['errors'], ['card_not_canonical_json'])

    def test_cli_stdout_is_machine_report_and_exit_codes(self):
        self.verify()
        command = [sys.executable, '-I', str(HERE / 'blind_verify.py'), '--card', str(self.file),
                   '--source-root', str(self.root), '--allow-source-root', 'held']
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(run.stdout)['ok'])
        self.source['char_end'] = False
        self.verify()
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertFalse(json.loads(run.stdout)['ok'])
        self.assertEqual(subprocess.run(command[:-2], capture_output=True).returncode, 2)


if __name__ == '__main__':
    unittest.main()
