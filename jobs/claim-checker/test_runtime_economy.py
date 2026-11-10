import builtins
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('runtime_economy_sources', Path(__file__).with_name('sources.py'))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


class SourceStreamingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.path = self.repo / 'jobs/a/output/SOURCES.jsonl'
        self.path.parent.mkdir(parents=True)
        self.sha = 'a' * 64

    def test_rows_order_paths_counts_and_duplicates(self):
        rows = [
            {'sha256': self.sha, 'url': 'http://example.org/a#x', 'instrument_ids': [' EO 1 '], 'cache_path': 'saved.pdf', 'text_path': 'text.txt'},
            {'sha256': self.sha, 'url': 'https://example.org/a', 'instrument_ids': ['EO 2'], 'text_path': '../../escape'},
            {'sha256': 'bad'}, [], None,
        ]
        (self.path.parent / 'saved.pdf').write_bytes(b'x')
        self.path.write_text('\n'.join(json.dumps(r) for r in rows) + '\ninvalid-json\n\n', encoding='utf8')
        idx = S.HeldIndex(); S.load_job_sources(idx, self.repo)
        copies = idx.lookup_sha(self.sha)
        self.assertEqual([c.instrument_ids for c in copies], [['EO 1'], ['EO 2']])
        self.assertEqual(idx.lookup_url('https://example.org/a'), copies)
        self.assertEqual([c.custody for c in copies], ['job_cache', 'record_only'])
        self.assertEqual(copies[0].local_path, self.path.parent / 'saved.pdf')
        self.assertIsNone(copies[1].text_path)
        self.assertEqual(idx.origin_counts, {'jobs/a/output/SOURCES.jsonl': 2})
        self.assertEqual(idx.notes, ['jobs/a/output/SOURCES.jsonl: 2 source records (1 with saved bytes on this machine); ignored 3 non-object/non-JSON lines, 1 records without a usable sha256, 1 unusable text_path/cache_path values'])

    def test_add_failure_is_counted_and_later_records_survive(self):
        self.path.write_text('\n'.join(json.dumps(r) for r in [
            {'sha256': self.sha, 'url': ['unusual']},
            {'sha256': 'b' * 64, 'url': 'https://example.org/b'},
        ]) + '\n', encoding='utf8')
        class FaultyIndex(S.HeldIndex):
            def add(self, copy):
                super().add(copy)
                if copy.sha256 == 'a' * 64:
                    raise ValueError('injected add failure')
        idx = FaultyIndex(); S.load_job_sources(idx, self.repo)
        # Baseline add may have mutated the index before raising; retain that
        # behavior while continuing and counting the row as skipped.
        self.assertEqual(len(idx.lookup_sha(self.sha)), 1)
        self.assertEqual(len(idx.lookup_sha('b' * 64)), 1)
        self.assertIn('1 source records', idx.notes[0])
        self.assertIn('1 records without a usable sha256', idx.notes[0])

    def test_read_jsonl_wrapper_retains_bad_count(self):
        self.path.write_text('{"x":1}\nnull\ninvalid\n', encoding='utf8')
        problems = []
        self.assertEqual(S._read_jsonl(self.path, problems), [{'x': 1}])
        self.assertEqual(problems, [2])

    def test_custody_observed_after_reader_closes(self):
        self.path.write_text(json.dumps({'sha256': self.sha, 'cache_path': 'late.pdf', 'unused': 'x' * 100000}) + '\n', encoding='utf8')
        real_open = builtins.open
        path = self.path
        class ClosingReader:
            def __init__(self, fh): self.fh = fh
            def __enter__(self): return self.fh.__enter__()
            def __exit__(self, *args):
                result = self.fh.__exit__(*args)
                (path.parent / 'late.pdf').write_bytes(b'appeared on close')
                return result
        def open_file(target, *args, **kwargs):
            fh = real_open(target, *args, **kwargs)
            return ClosingReader(fh) if Path(target) == path else fh
        idx = S.HeldIndex()
        with mock.patch('builtins.open', side_effect=open_file):
            S.load_job_sources(idx, self.repo)
        self.assertEqual(idx.lookup_sha(self.sha)[0].custody, 'job_cache')

    def _failure(self, error):
        self.path.write_text(json.dumps({'sha256': self.sha}) + '\n', encoding='utf8')
        real_open = builtins.open
        class Faulty:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def __iter__(self):
                yield json.dumps({'sha256': self.sha}) + '\n'
                raise error
        # Avoid coupling the iterator to TestCase's `self`.
        fault = Faulty(); fault.sha = self.sha
        def open_file(path, *args, **kwargs):
            return fault if Path(path) == self.path else real_open(path, *args, **kwargs)
        idx = S.HeldIndex()
        with mock.patch('builtins.open', side_effect=open_file):
            if isinstance(error, OSError):
                S.load_job_sources(idx, self.repo)
                self.assertEqual(idx.notes, ['jobs/a/output/SOURCES.jsonl: unreadable (OSError); skipped'])
            else:
                with self.assertRaises(type(error)):
                    S.load_job_sources(idx, self.repo)
        self.assertEqual(idx.by_sha, {})
        self.assertEqual(idx.by_url, {})
        self.assertEqual(idx.origin_counts, {})

    def test_mid_read_oserror_discards_entire_file(self):
        self._failure(OSError('injected read failure'))

    def test_mid_read_unicode_error_propagates_without_partial_index(self):
        self._failure(UnicodeError('injected decoding failure'))


class PergamonCustodyTests(unittest.TestCase):
    """A SOURCES.jsonl record with a Pergamon locator is fetched, re-hashed here, and counted as held bytes."""

    def setUp(self):
        import hashlib, os, sys
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.body = b'%PDF-1.4 stored outside git'
        self.sha = hashlib.sha256(self.body).hexdigest()
        path = self.repo / 'jobs/a/output/SOURCES.jsonl'
        path.parent.mkdir(parents=True)
        good = {'sha256': self.sha, 'url': 'https://example.org/a.pdf', 'instrument_ids': ['EO 1'], 'cache_path': None,
                'pergamon': {'sha256': self.sha, 'backend': 'release', 'ext': '.pdf', 'bytes': len(self.body),
                             'locator': 'mem://' + self.sha + '.pdf'}}
        wrong = {'sha256': 'b' * 64, 'url': 'https://example.org/b.pdf', 'cache_path': None,
                 'pergamon': {'sha256': 'c' * 64, 'backend': 'release', 'ext': '.pdf', 'locator': 'mem://x'}}
        path.write_text(chr(10).join(json.dumps(r) for r in (good, wrong)) + chr(10), encoding='utf8')
        self.idx = S.HeldIndex(); S.load_job_sources(self.idx, self.repo)
        self.copy = self.idx.lookup_sha(self.sha)[0]
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib'))
        import pergamon_store as PS
        objects = {self.sha + '.pdf': self.body}

        class Mem:
            name = 'release'
            def locator_for(self, sha, ext): return 'mem://' + sha + ext
            def get(self, locator, max_bytes=0):
                if locator[6:] not in objects: raise PS.NotFound(locator)
                return objects[locator[6:]]
        self.objects, self.PS = objects, PS
        patcher = mock.patch.object(PS.Store, 'from_env', classmethod(lambda cls, *a, **k: cls(Mem())))
        patcher.start(); self.addCleanup(patcher.stop)
        self.cache = self.repo / 'cache'

    def test_loader_marks_only_consistent_locators_as_stored(self):
        self.assertEqual(self.copy.custody, 'pergamon_store')
        self.assertTrue(self.copy.bytes_kept)
        self.assertEqual(self.idx.lookup_sha('b' * 64)[0].custody, 'record_only')   # locator names another hash

    def test_fetch_rehash_and_text_use_the_saved_cache_file(self):
        reader = S.TextReader(self.cache)
        self.assertTrue(reader.verify_bytes(self.copy))
        self.assertEqual(self.copy.local_path, self.cache / 'pergamon' / self.sha[:2] / (self.sha + '.pdf'))
        self.assertEqual(reader.read_bytes(self.copy)[0], self.body)

    def test_store_returning_wrong_bytes_leaves_the_copy_unverified(self):
        self.objects[self.sha + '.pdf'] = b'swapped'
        self.assertIsNone(S.TextReader(self.cache).verify_bytes(self.copy))
        self.assertIsNone(self.copy.local_path)

    def test_tampered_cache_file_is_caught_by_the_local_rehash(self):
        reader = S.TextReader(self.cache)
        self.assertTrue(reader.verify_bytes(self.copy))
        self.copy.local_path.write_bytes(b'tampered')
        self.assertFalse(S.TextReader(self.cache).verify_bytes(self.copy))

    def test_fetch_budget_zero_disables_the_network_step(self):
        with mock.patch.dict('os.environ', {'CLAIM_CHECKER_PERGAMON_FETCHES': '0'}):
            self.assertIsNone(S.TextReader(self.cache).verify_bytes(self.copy))


if __name__ == '__main__': unittest.main()
