import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fragment_cache as FC
import working_text as W


def legacy(repo):
    """The pre-cache Index construction, verbatim, as the behavioral oracle."""
    repo = Path(repo).resolve()
    by_sha, official, official_by_sha = {}, {}, {}
    paths = set(repo.glob('jobs/*/output/FRAGMENTS*.jsonl'))
    paths.update(repo.glob('jobs/*/data/**/FRAGMENTS*.jsonl'))
    for path in sorted(paths):
        if path.parts[-3] == 'claim-kit':
            continue
        try:
            fh = path.open(encoding='utf-8')
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except (ValueError, UnicodeError):
                    continue
                if not isinstance(row, dict) or row.get('kind') != 'original_representation':
                    continue
                data = row.get('data') if isinstance(row.get('data'), dict) else {}
                iid = row.get('instrument_id')
                grade = data.get('grade') or row.get('grade')
                acceptable = data.get('acceptable_as_original', row.get('acceptable_as_original'))
                sha = data.get('sha256')
                if not isinstance(iid, str) or not W.source_sha({'sha256': sha}):
                    continue
                try:
                    text_path = W._child(repo, data.get('text_path'), path.parent)
                    if not text_path.is_file():
                        text_path = W._child(repo, data.get('text_path'))
                    rel = text_path.relative_to(repo).as_posix()
                except (ValueError, TypeError):
                    continue
                rec = {'instrument_id': iid, 'grade': grade, 'acceptable_as_original': acceptable,
                       'sha256': sha, 'text_sha256': data.get('text_sha256'), 'text_path': rel,
                       'declaration_path': path.relative_to(repo).as_posix(),
                       'requires_page_check': bool(data.get('needs_page_check') or data.get('requires_page_check')),
                       'complete_text': data.get('complete_text'), 'url': data.get('url')}
                if acceptable is False:
                    by_sha.setdefault(W.source_sha(rec), []).append(rec)
                elif (acceptable is not False and (acceptable is True or row.get('produced_by') in W.OFFICIAL_PRODUCERS)
                      and data.get('needs_page_check') is False and text_path.is_file()):
                    official.setdefault(iid, []).append(rec)
                    official_by_sha.setdefault(W.source_sha(rec), []).append(rec)
    return by_sha, official, official_by_sha


def built(repo):
    """FC.build with its status recorded on the (genuine) Index for assertions."""
    idx, status, _, _ = FC.build(repo)
    idx.cache_status = status
    return idx


def h(n):
    return hashlib.sha256(str(n).encode()).hexdigest()


def row(iid, n, text_path, acceptable=None, produced_by=None, **data):
    body = {'sha256': h(n), 'text_path': text_path, 'text_sha256': h('t' + str(n)), 'needs_page_check': False}
    body.update(data)
    out = {'kind': 'original_representation', 'instrument_id': iid, 'data': body}
    if acceptable is not None:
        body['acceptable_as_original'] = acceptable
    if produced_by:
        out['produced_by'] = produced_by
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name, 'repo').resolve()
        self.cache = Path(self.tmp.name, 'cache')
        self.repo.mkdir()
        patcher = mock.patch.dict(os.environ, {'CLAIM_KIT_CACHE_DIR': str(self.cache)})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop('CLAIM_KIT_INDEX_CACHE', None)
        FC._SHARED.clear()
        self.addCleanup(FC._SHARED.clear)

    def write(self, rel, text):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def provider(self, rel, rows, raw=''):
        return self.write(rel, ''.join(json.dumps(r) + '\n' for r in rows) + raw)

    def seed(self):
        self.write('texts/a.txt', 'alpha')
        self.write('jobs/p1/output/b.txt', 'beta')
        self.write('jobs/p2/data/x/c.txt', 'gamma')
        self.provider('jobs/p1/output/FRAGMENTS.jsonl',
                      [row('EO:1', 1, 'texts/a.txt', acceptable=False, grade='compiled_transcription'),
                       row('EO:2', 2, 'b.txt', produced_by='fr-originals'),
                       row('EO:3', 3, 'missing.txt', acceptable=False),
                       row('EO:4', 4, '../../../outside.txt', acceptable=False),
                       {'kind': 'other', 'instrument_id': 'EO:9'}],
                      raw='not json\n')
        self.provider('jobs/p2/data/x/FRAGMENTS_more.jsonl',
                      [row('EO:5', 5, 'c.txt', acceptable=True),
                       row('EO:6', 6, 'jobs/p2/data/x/c.txt', acceptable=False)])
        self.provider('jobs/claim-kit/output/FRAGMENTS.jsonl', [row('EO:7', 7, 'texts/a.txt', acceptable=False)])

    def assert_same_as_legacy(self, idx):
        by_sha, official, official_by_sha = legacy(self.repo)
        self.assertEqual(idx.by_sha, by_sha)
        self.assertEqual(idx.official, official)
        self.assertEqual(idx.official_by_sha, official_by_sha)
        return idx

    def entries(self):
        return sorted(self.cache.glob('fragment-index-*.json')) if self.cache.exists() else []


class IndexCacheTests(Base):
    def test_cached_uncached_and_legacy_identical(self):
        self.seed()
        with mock.patch.dict(os.environ, {'CLAIM_KIT_INDEX_CACHE': '0'}):
            plain = self.assert_same_as_legacy(built(self.repo))
        self.assertEqual(plain.cache_status, 'disabled')
        self.assertEqual(self.entries(), [])
        first = self.assert_same_as_legacy(built(self.repo))
        self.assertEqual(first.cache_status, 'miss_stored')
        hit = self.assert_same_as_legacy(built(self.repo))
        self.assertEqual(hit.cache_status, 'hit')
        self.assertEqual((hit.by_sha, hit.official), (plain.by_sha, plain.official))
        self.assertEqual(len(self.entries()), 1)
        self.assertEqual(sorted(i for rows in hit.by_sha.values() for r in rows for i in [r['instrument_id']]),
                         ['EO:1', 'EO:3', 'EO:6'])  # claim-kit provider excluded; outside-repo path skipped
        self.assertIn('EO:2', hit.official)

    def test_hit_is_a_genuine_working_text_index(self):
        self.seed()
        built(self.repo)
        hit = built(self.repo)
        self.assertEqual(hit.cache_status, 'hit')
        self.assertIs(type(hit), W.Index)
        self.assertEqual(hit.repo, self.repo)
        ref = hit.official['EO:2'][0]
        text = self.repo / ref['text_path']
        probe = {'sha256': ref['sha256'], 'text_path': ref['text_path'], 'url': ref['url'],
                 'text_sha256': hashlib.sha256(text.read_bytes()).hexdigest()}
        self.assertEqual(hit.exact_official(probe), W.Index(self.repo).exact_official(probe))

    def test_reconstruction_mismatch_is_never_stored(self):
        self.seed()
        real = FC.resolve
        def skewed(*a):
            by_sha, official, official_by_sha, witness = real(*a)
            by_sha.clear()
            return by_sha, official, official_by_sha, witness
        with mock.patch.object(FC, 'resolve', skewed):
            self.assertEqual(built(self.repo).cache_status, 'miss_unverified')
        self.assertEqual(self.entries(), [])

    def test_env_disables_cache(self):
        self.seed()
        with mock.patch.dict(os.environ, {'CLAIM_KIT_INDEX_CACHE': '0'}):
            idx = self.assert_same_as_legacy(built(self.repo))
            self.assertEqual(idx.cache_status, 'disabled')
        self.assertEqual(self.entries(), [])

    def test_added_provider_file_changes_result(self):
        self.seed()
        built(self.repo)
        self.write('texts/n.txt', 'new')
        self.provider('jobs/p3/output/FRAGMENTS_new.jsonl', [row('EO:8', 8, 'texts/n.txt', acceptable=False)])
        idx = self.assert_same_as_legacy(built(self.repo))
        self.assertEqual(idx.cache_status, 'miss_stored')
        self.assertIn(h(8), idx.by_sha)
        self.assertEqual(built(self.repo).cache_status, 'hit')

    def test_deleted_provider_file_changes_result(self):
        self.seed()
        built(self.repo)
        (self.repo / 'jobs/p2/data/x/FRAGMENTS_more.jsonl').unlink()
        idx = self.assert_same_as_legacy(built(self.repo))
        self.assertNotIn('EO:5', idx.official)
        self.assertNotIn(h(6), idx.by_sha)

    def test_same_size_edit_changes_result(self):
        self.seed()
        p = self.repo / 'jobs/p2/data/x/FRAGMENTS_more.jsonl'
        before = p.read_bytes()
        built(self.repo)
        after = before.replace(b'EO:5', b'EO:A')
        self.assertEqual(len(before), len(after))
        os.utime(p, ns=(p.stat().st_atime_ns, p.stat().st_mtime_ns))
        st = p.stat()
        p.write_bytes(after)
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))  # identical size and mtime
        idx = self.assert_same_as_legacy(built(self.repo))
        self.assertIn('EO:A', idx.official)
        self.assertNotIn('EO:5', idx.official)

    def test_text_file_appearing_and_disappearing_is_honored_on_hit(self):
        self.seed()
        self.provider('jobs/p4/output/FRAGMENTS.jsonl', [row('EO:10', 10, 'late.txt', acceptable=True)])
        idx = self.assert_same_as_legacy(built(self.repo))
        self.assertNotIn('EO:10', idx.official)
        self.write('jobs/p4/output/late.txt', 'late')
        idx = self.assert_same_as_legacy(built(self.repo))
        self.assertEqual(idx.cache_status, 'hit')
        self.assertIn('EO:10', idx.official)
        (self.repo / 'jobs/p4/output/late.txt').unlink()
        idx = self.assert_same_as_legacy(built(self.repo))
        self.assertEqual(idx.cache_status, 'hit')
        self.assertNotIn('EO:10', idx.official)
        # by_sha path choice (provider-relative first, then repo-relative) follows the files too
        self.assertEqual({r['text_path'] for r in idx.by_sha[h(1)]}, {'texts/a.txt'})

    def test_corrupt_or_mismatched_cache_rebuilds(self):
        self.seed()
        built(self.repo)
        entry, = self.entries()
        for damage in (b'{not json', b'[]', b'', json.dumps({'format': FC.CACHE_FORMAT, 'key': 'x'}).encode(),
                       entry.read_bytes().replace(b'"rows":[[', b'"rows":[["bad"],[')):
            entry.write_bytes(damage)
            idx = self.assert_same_as_legacy(built(self.repo))
            self.assertEqual(idx.cache_status, 'miss_stored')
            self.assertEqual(built(self.repo).cache_status, 'hit')

    def test_forged_row_in_matching_envelope_is_not_trusted_when_shape_is_wrong(self):
        self.seed()
        built(self.repo)
        entry, = self.entries()
        doc = json.loads(entry.read_text())
        doc['rows'][0] = [['EO:1', 'short row']]
        entry.write_text(json.dumps(doc))
        self.assertEqual(self.assert_same_as_legacy(built(self.repo)).cache_status, 'miss_stored')

    def test_unwritable_cache_dir_is_silent(self):
        self.seed()
        blocker = Path(self.tmp.name, 'blocker')
        blocker.write_text('file, not a directory')
        with mock.patch.dict(os.environ, {'CLAIM_KIT_CACHE_DIR': str(blocker / 'sub')}):
            self.assert_same_as_legacy(built(self.repo))

    def test_old_entries_are_pruned(self):
        self.seed()
        for n in range(6):
            self.provider('jobs/p9/output/FRAGMENTS.jsonl', [row(f'EO:{n}', 100 + n, 'texts/a.txt', acceptable=False)])
            built(self.repo)
        self.assertEqual(len(self.entries()), FC.CACHE_KEEP)

    def test_inventory_key_covers_every_provider_file(self):
        self.seed()
        _, inv = FC.provider_inventory(self.repo)
        self.assertEqual([i[0] for i in inv], ['jobs/p1/output/FRAGMENTS.jsonl', 'jobs/p2/data/x/FRAGMENTS_more.jsonl'])
        for rel, size, sha in inv:
            data = (self.repo / rel).read_bytes()
            self.assertEqual((size, sha), (len(data), hashlib.sha256(data).hexdigest()))
        key = FC.inventory_key(inv)
        self.assertNotEqual(key, FC.inventory_key(inv[:1]))
        self.assertNotEqual(key, FC.inventory_key([(inv[0][0], inv[0][1], h('x'))] + inv[1:]))


class SharedIndexTests(Base):
    def test_shared_builds_once_per_inventory(self):
        self.seed()
        with mock.patch.object(FC, '_parse_file', wraps=FC._parse_file) as parse:
            a = FC.shared(self.repo)
            b = FC.shared(str(self.repo))
            self.assertIs(a, b)
            self.assertEqual(parse.call_count, 2)  # two provider files, parsed once
        self.assert_same_as_legacy(a)

    def test_shared_rebuilds_when_inventory_or_text_files_change(self):
        self.seed()
        a = FC.shared(self.repo)
        self.provider('jobs/p3/output/FRAGMENTS_new.jsonl', [row('EO:8', 8, 'texts/a.txt', acceptable=False)])
        b = FC.shared(self.repo)
        self.assertIsNot(a, b)
        self.assertIn(h(8), b.by_sha)
        self.provider('jobs/p4/output/FRAGMENTS.jsonl', [row('EO:10', 10, 'late.txt', acceptable=True)])
        c = FC.shared(self.repo)
        self.assertNotIn('EO:10', c.official)
        self.write('jobs/p4/output/late.txt', 'late')
        d = FC.shared(self.repo)
        self.assertIsNot(c, d)
        self.assertIn('EO:10', d.official)
        self.assert_same_as_legacy(d)

    def test_shared_with_cache_disabled_is_fresh(self):
        self.seed()
        with mock.patch.dict(os.environ, {'CLAIM_KIT_INDEX_CACHE': '0'}):
            self.assertIsNot(FC.shared(self.repo), FC.shared(self.repo))


@unittest.skipUnless(os.environ.get('CLAIM_KIT_REAL_REPO_INDEX_TEST') == '1', 'real repository comparison is opt-in')
class RealRepoTest(unittest.TestCase):
    def test_real_repo_identical(self):
        repo = Path(__file__).resolve().parents[2]
        idx = built(repo)
        by_sha, official, official_by_sha = legacy(repo)
        self.assertEqual((idx.by_sha, idx.official, idx.official_by_sha), (by_sha, official, official_by_sha))


if __name__ == '__main__':
    unittest.main()
