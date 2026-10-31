"""Adversarial native Valla closure tests; all Git writes use disposable fixtures.

No production corpus, downloads, source checkout changes, or certificate mocks.
The fixture certifies the actual copied implementation at its own HEAD and then
commits the certificate separately, matching the production certificate protocol.
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2]
SCRIPTS = SOURCE / '.github/scripts'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VallaMaterializationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='valla-closure-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.repo.mkdir()
        self.old_cwd = Path.cwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, self.old_cwd)
        self.old_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        self.addCleanup(setattr, sys, 'dont_write_bytecode', self.old_bytecode)
        for name in ('materialize_job_inputs.py', 'result_freshness.py', 'run_jobs.py', 'run_jobs.sh'):
            self.copy(SCRIPTS / name, '.github/scripts/' + name)
        for name in ('valla.py', 'premises.json', 'job.py', 'needs.txt', 'inputs.txt', 'triggers.txt'):
            source = SOURCE / 'jobs/valla' / name
            if source.exists():
                self.copy(source, 'jobs/valla/' + name)
        self.copy(SOURCE / 'jobs/_lib/cache_cap.py', 'jobs/_lib/cache_cap.py')
        self.write('.gitignore', '__pycache__/\n.job-cache/\noversized/\nignored/\n')
        self.write('.github/workflows/run-jobs.yml', 'name: fixture\n')
        self.write('unrelated/body.txt', 'must stay absent in certified selection\n')
        self.write('jobs/unrelated/output/LARGE.txt', 'unrelated prior output\n')
        self.write('jobs/valla/output/INDEX.json', '{"prior":"successful"}\n')
        self.write('jobs/valla/output/STATUS.json', '{"result":"succeeded"}\n')
        self.V = load(self.repo / 'jobs/valla/valla.py', 'fixture_valla')
        for path in self.V.PROTOCOLS:
            self.write(path, 'Fixture protocol: deadline is not performance.\n')
        self.make_evidence()
        self.make_package('research/excavator/package')
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'core.autocrlf', 'false')
        self.git('config', 'core.symlinks', 'true')
        self.commit('fixture implementation and evidence')
        self.F = load(self.repo / '.github/scripts/result_freshness.py', 'fixture_freshness')
        old = sys.modules.get('result_freshness')
        sys.modules['result_freshness'] = self.F
        try:
            self.M = load(self.repo / '.github/scripts/materialize_job_inputs.py', 'fixture_materializer')
        finally:
            if old is None:
                del sys.modules['result_freshness']
            else:
                sys.modules['result_freshness'] = old
        signature = self.M.narrow_signature('valla')
        self.write('.github/scripts/materialization_certificates.json', json.dumps({'valla': signature}))
        self.commit('separate fixture certificate')
        # Reload exactly as a fresh runner process loads the committed certificate.
        old = sys.modules.get('result_freshness')
        sys.modules['result_freshness'] = self.F
        try:
            self.M = load(self.repo / '.github/scripts/materialize_job_inputs.py', 'certified_materializer')
        finally:
            if old is None:
                del sys.modules['result_freshness']
            else:
                sys.modules['result_freshness'] = old
        self.assertTrue(self.F.valla_certified())
        self.assertEqual(self.M.fallback_jobs(['valla']), {})

    def copy(self, source, target):
        target = self.repo / target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def write(self, path, value):
        path = self.repo / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')
        return path

    def record(self, path, value):
        return self.write(path, self.V.canon(value) + '\n')

    def git(self, *args, input=None):
        return subprocess.run(['git', *args], cwd=self.repo, input=input,
                              capture_output=True, check=True).stdout

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)
        return self.git('rev-parse', 'HEAD').decode().strip()

    def make_package(self, root):
        self.write(root + '/RATIONALES.json', '{"rule":"A shared examined rationale."}\n')
        self.write(root + '/decisions.csv', 'instrument_id,research_rationale\nEO:1,@rationale:rule\n')
        self.write(root + '/clauses.csv', 'instrument_id,scope_id,rationale\nEO:1,EO:1#a,@rationale:rule\n')

    def make_evidence(self):
        text = 'A quoted command, with a deadline.\nAnother continuing duty.'
        self.source_path = 'jobs/arbitrary-provider/output/held-body.txt'
        source_file = self.write(self.source_path, text)
        self.extra_path = 'research/separate/body.bin'
        extra_file = self.write(self.extra_path, 'An additional held artifact.\n')
        source = {'text_path': self.source_path, 'text_sha256': self.V.file_sha(source_file),
                  'char_start': 0, 'char_end': 34, 'sha256': 'a' * 64,
                  'url': 'https://example.invalid/source', 'page_or_item': '1'}
        old = {'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:1',
               'claim_kit': {'agent': 'original-producer'}, 'original_representation': source,
               'operative_clauses': [{'scope_id': 'EO:1#a', 'original_operative_text': text[:34],
                                     'original_source': source, 'first_end': {'date': '2001-01-01'},
                                     'state_at_cutoff': 'terminated', 'later_events': []}],
               'research_rationale': 'Every clause remains part of the order until revoked.',
               'whole_order_end': {'date': '2001-01-01'}, 'savings_residuals': {}}
        self.historical_path = 'research/history/held-claim.jsonl'
        self.record(self.historical_path, old)
        self.claim = copy.deepcopy(old)
        self.claim['claim_kit']['agent'] = 'current-producer'
        self.claim['operative_clauses'][0]['first_end']['date'] = '1999-01-01'
        self.record('research/readiness/claims/one.jsonl', self.claim)
        deps = [{'kind': 'file', 'key': self.source_path, 'sha256': self.V.file_sha(source_file)},
                {'kind': 'file', 'key': self.extra_path, 'sha256': self.V.file_sha(extra_file)},
                {'kind': 'rule', 'key': 'jobs/claim-kit/BATCH.md',
                 'sha256': self.V.file_sha(self.repo / 'jobs/claim-kit/BATCH.md')}]
        selector = {'kind': 'exact_quotation', 'scope_id': 'EO:1#a'}
        self.attestation = {'schema': 'eo-component-attestation/v1', 'attestation_id': 'A1',
                            'instrument_id': 'EO:1', 'component_selector': selector,
                            'component_sha256': self.V.sha(self.V.component(old, selector)),
                            'producer': 'original-producer', 'reviewer': 'quote-reviewer',
                            'independent': True, 'review_kind': 'independent_ai_component',
                            'verdict': 'upheld', 'method': 'exact-held-text-span-v1',
                            'reviewed_claim_sha256': self.V.sha(old),
                            'reviewed_claim_ref': {'path': self.historical_path, 'line': 1},
                            'reviewed_on': '2026-10-20', 'dependencies': deps}
        body = {**self.attestation, 'schema': 'eo-component-review/v1', 'record_id': 'Q1',
                'rationale': 'I examined the exact held quotation. This approves only the specified component.'}
        path = self.record('research/separate/quote-review.jsonl', body)
        self.attestation['review_ref'] = {'path': path.relative_to(self.repo).as_posix(),
                                        'file_sha256': self.V.file_sha(path), 'record_id': 'Q1'}
        self.record('research/readiness/component_attestations/one.jsonl', self.attestation)
        rationale = self.claim['research_rationale']
        self.method = {'schema': 'eo-method-dependency-review/v1', 'record_id': 'M1',
                       'instrument_id': 'EO:1', 'claim_sha256': self.V.sha(self.claim),
                       'independent': True, 'verdict': 'revalidate',
                       'review_kind': 'independent_ai_method_review', 'reviewed_on': '2026-10-20',
                       'producer': 'current-producer', 'reviewer': 'method-reviewer',
                       'rationale_pointer': '/research_rationale', 'char_start': 0,
                       'char_end': len(rationale), 'span_sha256': self.V.sha(rationale),
                       'conclusion_pointers': ['/operative_clauses/0/first_end'], 'dependencies': deps}
        for key in ('applicability', 'earlier_ending', 'scope', 'independent_commands', 'savings', 'unresolved_question', 'analysis'):
            self.method[key] = 'Case-specific examination establishes a need for separate correction.'
        path = self.record('research/separate/method-review.jsonl', self.method)
        self.method['review_ref'] = {'path': path.relative_to(self.repo).as_posix(),
                                   'file_sha256': self.V.file_sha(path), 'record_id': 'M1'}
        self.record('research/readiness/method_reviews/one.jsonl', self.method)

    def bootstrap(self):
        self.git('sparse-checkout', 'init', '--no-cone')
        self.git('sparse-checkout', 'set', '--no-cone', '--stdin', input=(
            '/*\n!/*/\n/.github/**\n/jobs/**\n!/jobs/*/output/**\n').encode())

    def materialize(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.M.materialize(['valla'])

    def native(self):
        out = Path(self.temp.name) / 'native'
        env = {**os.environ, 'REPO_ROOT': str(self.repo), 'OUTPUT_DIR': str(out),
               'PYTHONDONTWRITEBYTECODE': '1'}
        subprocess.run([sys.executable, str(self.repo / 'jobs/valla/job.py')], cwd=self.repo,
                       env=env, capture_output=True, check=True, timeout=10)
        return (out / 'INDEX.json').read_bytes(), (out / 'SUMMARY.json').read_bytes()

    def capture(self):
        target = self.repo / 'jobs/valla/output' / self.F.MANIFEST
        self.F.capture('valla', target)
        return json.loads(target.read_text())

    def check(self, names=('valla',)):
        report = Path(self.temp.name) / 'freshness.json'
        with contextlib.redirect_stdout(io.StringIO()):
            code = self.F.check('HEAD', list(names), report)
        return code, json.loads(report.read_text())

    def test_real_certificate_native_full_selected_outputs_equal(self):
        full = self.native()
        index = json.loads(full[0])
        self.assertEqual(index['summary']['examined_dependencies'], 1)
        self.assertTrue(index['claims']['EO:1']['component_reviews'][0]['valid'])
        self.assertIn('/whole_order_end', index['claims']['EO:1']['invalidated_conclusion_pointers'])
        self.assertEqual(index['package_scan']['unmaterialized_packages'], [])
        self.bootstrap()
        self.assertFalse((self.repo / self.source_path).exists())
        receipt = self.materialize()
        self.assertEqual(receipt['compatibility_fallback_jobs'], {})
        self.assertFalse((self.repo / 'unrelated/body.txt').exists())
        self.assertFalse((self.repo / 'jobs/unrelated/output/LARGE.txt').exists())
        self.assertEqual(self.native(), full)
        self.assertEqual((self.repo / 'jobs/valla/output/INDEX.json').read_text(), '{"prior":"successful"}\n')

    def test_sparse_providers_resolve_historical_and_separate_review_bodies(self):
        self.bootstrap()
        refs, complete = self.F.valla_references()
        self.assertTrue(complete)
        for path in (self.source_path, self.extra_path, self.historical_path,
                     'research/separate/quote-review.jsonl', 'research/separate/method-review.jsonl'):
            self.assertIn(path, refs)
        self.materialize()
        self.assertTrue(self.F.scope('valla')['implementation_certified'])
        self.assertTrue(self.V.build(self.repo)['claims']['EO:1']['component_reviews'][0]['valid'])

    def test_new_dynamic_provider_and_dependency_are_captured(self):
        self.capture()
        dep = 'jobs/new-provider/output/new-body.txt'
        self.write(dep, 'New same-run dependency\n')
        self.record('research/readiness/component_attestations/new.jsonl',
                    {'dependencies': [{'kind': 'file', 'key': dep, 'sha256': '0' * 64}]})
        scope = self.F.scope('valla')
        self.assertTrue(scope['dynamic_complete'])
        self.assertIn(dep, self.F.working(scope))
        self.commit('new dynamic provider and body')
        code, report = self.check()
        self.assertEqual(code, 3)
        paths = [p['path'] if isinstance(p, dict) else p
                 for issue in report['problems'] for p in issue.get('changed_paths', [])]
        self.assertIn('research/readiness/component_attestations/new.jsonl', paths)

    def test_referenced_dependency_edit_delete_and_missing_are_versioned(self):
        baseline = self.F.working(self.F.scope('valla'))
        for path in (self.source_path, self.extra_path):
            with self.subTest(path=path):
                original = (self.repo / path).read_bytes()
                self.write(path, 'changed bytes')
                self.assertNotEqual(self.F.working(self.F.scope('valla'))[path], baseline[path])
                (self.repo / path).unlink()
                self.assertNotIn(path, self.F.working(self.F.scope('valla')))
                self.assertIn(path, self.F.scope('valla')['referenced_files'])
                (self.repo / path).write_bytes(original)
        self.assertTrue(self.F.scope('valla')['dynamic_complete'])
        self.assertEqual(self.F.working(self.F.scope('valla')), baseline)

    def test_dynamic_provider_edit_and_working_deletion_do_not_resurrect_head(self):
        path = 'research/readiness/component_attestations/one.jsonl'
        dep = 'jobs/new-provider/output/new-body.txt'
        provider = copy.deepcopy(self.attestation)
        provider['dependencies'].append({'kind': 'file', 'key': dep, 'sha256': '0' * 64})
        self.record(path, provider)
        self.assertIn(dep, self.F.scope('valla')['referenced_files'])
        (self.repo / path).unlink()
        # Ordinary working deletion must not read its historical HEAD record.
        refs = self.F.scope('valla')['referenced_files']
        self.assertNotIn(dep, refs)
        self.assertNotIn(self.historical_path, refs)
        self.assertTrue(self.F.scope('valla')['dynamic_complete'])

    def test_missing_dependency_arrival_is_tracked_even_when_ignored(self):
        path = 'ignored/late-body.txt'
        self.record('research/readiness/component_attestations/late.jsonl',
                    {'dependencies': [{'kind': 'file', 'key': path, 'sha256': '0' * 64}]})
        self.assertNotIn(path, self.F.working(self.F.scope('valla')))
        self.write(path, 'ignored dependency materialized after capture')
        first = self.F.working(self.F.scope('valla'))[path]
        self.write(path, 'changed ignored dependency')
        self.assertNotEqual(self.F.working(self.F.scope('valla'))[path], first)
        (self.repo / path).unlink()
        self.assertNotIn(path, self.F.working(self.F.scope('valla')))

    def test_package_triples_add_edit_delete_freshness(self):
        self.capture()
        for base in ('research/excavator/new', 'research/production/new'):
            self.make_package(base)
            self.commit('new package triples')
            self.assertEqual(self.check()[0], 3)
            self.capture()
            self.assertEqual(self.check()[0], 0)
            for name in ('RATIONALES.json', 'decisions.csv', 'clauses.csv'):
                with self.subTest(base=base, name=name):
                    path = base + '/' + name
                    original = (self.repo / path).read_text()
                    self.write(path, original + '\n')
                    self.commit('edit package member')
                    self.assertEqual(self.check()[0], 3)
                    self.capture()
                    (self.repo / path).unlink()
                    self.commit('delete package member')
                    self.assertEqual(self.check()[0], 3)
                    self.capture()
                    self.assertEqual(self.check()[0], 0)

    def test_same_run_provider_output_and_later_mutation(self):
        producer = 'arbitrary-provider'
        destination = self.repo / 'jobs' / producer / 'output' / self.F.MANIFEST
        self.F.capture(producer, destination)
        self.write(self.source_path, 'same-run changed held body')
        self.capture()
        code, report = self.check((producer, 'valla'))
        self.assertEqual(code, 0, report)
        self.assertEqual(report['input_generations']['valla'][producer], 'same_run_candidate')
        self.write(self.source_path, 'changed after consumer capture')
        self.assertEqual(self.check((producer, 'valla'))[0], 3)

    def test_changed_implementation_resolver_and_materializer_both_decline_certificate(self):
        for path in ('jobs/valla/valla.py', 'jobs/valla/inputs.txt', 'jobs/_lib/cache_cap.py',
                     '.github/scripts/result_freshness.py', '.github/scripts/materialize_job_inputs.py',
                     '.github/scripts/run_jobs.py', '.github/scripts/run_jobs.sh',
                     '.github/workflows/run-jobs.yml'):
            with self.subTest(path=path):
                file = self.repo / path
                original = file.read_bytes()
                file.write_bytes(original + b'\n# adversarial change\n')
                self.assertFalse(self.F.valla_certified())
                self.assertIn('*', self.F.scope('valla')['patterns'])
                entries, _, patterns = self.M.input_closure(['valla'])
                self.assertIn('unrelated/body.txt', entries)
                self.assertIn('/**', patterns['valla'])
                file.write_bytes(original)
        self.assertTrue(self.F.valla_certified())

    def test_unknown_certificate_and_committed_changed_code_restore_repository(self):
        certificate = self.repo / '.github/scripts/materialization_certificates.json'
        certificate.unlink()
        self.assertFalse(self.F.valla_certified())
        self.assertIn('unrelated/body.txt', self.M.input_closure(['valla'])[0])
        self.write('.github/scripts/materialization_certificates.json', '{"valla":"' + '0' * 64 + '"}')
        self.commit('unknown certificate')
        self.assertIn('*', self.F.scope('valla')['patterns'])
        self.write('jobs/valla/valla.py', (self.repo / 'jobs/valla/valla.py').read_text() + '\n# changed\n')
        self.commit('unknown code version')
        self.assertIn('unrelated/body.txt', self.M.input_closure(['valla'])[0])
        self.assertEqual(self.M.fallback_jobs(['valla']), {'valla': 'audited_version_changed'})

    def test_committed_code_change_with_original_certificate_restores_repository(self):
        self.write('jobs/valla/valla.py', (self.repo / 'jobs/valla/valla.py').read_text() + '\n# changed\n')
        self.commit('changed implementation, retained original certificate')
        self.assertFalse(self.F.valla_certified())
        self.assertEqual(self.M.fallback_jobs(['valla']), {'valla': 'audited_version_changed'})
        self.assertIn('unrelated/body.txt', self.M.input_closure(['valla'])[0])

    def test_symlink_parent_traversal_and_external_symlink_decline_narrowing(self):
        (self.repo / 'research/link').symlink_to('separate', target_is_directory=True)
        (self.repo / 'research/outside').symlink_to(Path(self.temp.name), target_is_directory=True)
        for dep in ('research/link/../history/held-claim.jsonl', 'research/outside/body.txt'):
            with self.subTest(dep=dep):
                self.record('research/readiness/component_attestations/link.jsonl',
                            {'dependencies': [{'kind': 'file', 'key': dep}]})
                self.assertFalse(self.F.scope('valla')['dynamic_complete'])
                self.assertIn('*', self.F.scope('valla')['patterns'])
                self.assertIn('unrelated/body.txt', self.M.input_closure(['valla'])[0])

    def test_malformed_metadata_conservatively_restores_everything(self):
        path = 'research/readiness/component_attestations/malformed.jsonl'
        for record in ('not json\n', '[]\n', '{"review_ref":null}\n',
                       '{"dependencies":null}\n', '{"dependencies":[{"kind":"file"}]}\n',
                       '{"dependencies":[{"kind":"rule","key":true}]}\n'):
            with self.subTest(record=record):
                self.write(path, record)
                self.assertFalse(self.F.scope('valla')['dynamic_complete'])
                self.assertIn('*', self.F.scope('valla')['patterns'])
                entries, _, patterns = self.M.input_closure(['valla'])
                self.assertIn('unrelated/body.txt', entries)
                self.assertIn('/**', patterns['valla'])

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_sparse_tracked_symlink_ancestor_declines_narrowing(self):
        (self.repo / 'research/link').symlink_to('separate', target_is_directory=True)
        self.record('research/readiness/component_attestations/link.jsonl',
                    {'dependencies': [{'kind': 'file', 'key': 'research/link/body.bin'}]})
        self.commit('tracked symlink ancestor')
        self.bootstrap()
        self.assertFalse((self.repo / 'research/link').is_symlink())
        self.assertFalse(self.F.scope('valla')['dynamic_complete'])
        self.assertIn('/**', self.M.input_closure(['valla'])[2]['valla'])
        self.materialize()
        self.assertTrue((self.repo / 'unrelated/body.txt').exists())

    def ignore_tracked_path(self, path):
        self.write('.gitignore', (self.repo / '.gitignore').read_text() + '/' + path + '\n')
        self.git('rm', '--cached', '--', path)
        self.commit('leave directly read file ignored and untracked')
        self.assertTrue((self.repo / path).is_file())
        self.assertEqual(self.git('ls-files', '--', path), b'')
        self.git('check-ignore', '--', path)
        self.assertTrue(self.F.valla_certified())

    def test_ignored_untracked_sheet_beside_git_rationales_is_captured_and_rejected(self):
        path = 'research/excavator/package/decisions.csv'
        self.ignore_tracked_path(path)
        native = self.V.build(self.repo)
        self.assertTrue(any(row['path'] == path for row in native['shared_rationale_references']))
        manifest = self.capture()
        self.assertIn(path, manifest['scope']['referenced_files'])
        self.assertIn(path, manifest['inputs'])
        self.assertTrue(manifest['scope']['dynamic_complete'])
        code, report = self.check()
        self.assertEqual(code, 3, report)
        self.assertTrue(any(issue['reason'] == 'inputs_changed' and
                            any(row['path'] == path for row in issue['changed_paths'])
                            for issue in report['problems']))

    def test_ignored_fixed_protocol_is_captured_and_rejected_when_absent_from_git(self):
        # This protocol is deliberately not one of the fixture's review dependencies.
        path = 'jobs/claim-kit/AGENT_PROTOCOL.md'
        self.ignore_tracked_path(path)
        manifest = self.capture()
        self.assertIn(path, manifest['scope']['referenced_files'])
        self.assertIn(path, manifest['inputs'])
        self.assertEqual(self.check()[0], 3)

    def test_ignored_live_canonical_seed_is_captured_and_rejected(self):
        path = 'research/readiness/claims/ignored.jsonl'
        self.write('.gitignore', (self.repo / '.gitignore').read_text() + '/' + path + '\n')
        self.commit('ignore a live canonical seed')
        self.record(path, {'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:2',
                           'research_rationale': 'A live ignored canonical claim.'})
        self.assertIn('EO:2', self.V.build(self.repo)['claims'])
        manifest = self.capture()
        self.assertIn(path, manifest['scope']['referenced_files'])
        self.assertIn(path, manifest['inputs'])
        self.assertEqual(self.check()[0], 3)

    def test_new_ignored_claim_after_capture_changes_native_build_and_rejects(self):
        path = 'research/readiness/claims/late-ignored.jsonl'
        self.write('.gitignore', (self.repo / '.gitignore').read_text() + '/' + path + '\n')
        baseline = self.commit('ignore a future canonical seed')
        before = self.V.build(self.repo)
        manifest = self.capture()
        self.assertNotIn(path, manifest['scope']['referenced_files'])
        self.assertNotIn(path, manifest['inputs'])
        self.assertEqual(self.check()[0], 0)
        self.record(path, {'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:2',
                           'research_rationale': 'A canonical claim arriving after the captured snapshot.'})
        self.git('check-ignore', '--', path)
        self.assertEqual(self.git('ls-files', '--', path), b'')
        after = self.V.build(self.repo)
        self.assertNotIn('EO:2', before['claims'])
        self.assertIn('EO:2', after['claims'])
        self.assertEqual(self.git('rev-parse', 'HEAD').decode().strip(), baseline)
        code, report = self.check()
        self.assertEqual(code, 3, report)
        self.assertTrue(any(issue['reason'] == 'referenced_input_changed_during_run'
                            and any(row['path'] == path for row in issue['changed_paths'])
                            for issue in report['problems']))

    def test_new_ignored_method_provider_after_capture_changes_native_refusals_and_rejects(self):
        path = 'research/readiness/method_reviews/late-ignored.jsonl'
        self.write('.gitignore', (self.repo / '.gitignore').read_text() + '/' + path + '\n')
        baseline = self.commit('ignore a future method provider')
        before = self.V.build(self.repo)
        manifest = self.capture()
        self.assertNotIn(path, manifest['scope']['referenced_files'])
        self.assertNotIn(path, manifest['inputs'])
        self.assertEqual(self.check()[0], 0)
        # Well-formed provider metadata; the separate held review does not approve
        # this new record ID, so native Valla adds an explicit refused-review row.
        self.record(path, {**self.method, 'record_id': 'LATE-UNAPPROVED'})
        self.git('check-ignore', '--', path)
        self.assertEqual(self.git('ls-files', '--', path), b'')
        after = self.V.build(self.repo)
        self.assertEqual(before['refused_method_reviews'], [])
        self.assertTrue(any(row['path'] == path for row in after['refused_method_reviews']))
        self.assertTrue(self.F.scope('valla')['dynamic_complete'])
        self.assertEqual(self.git('rev-parse', 'HEAD').decode().strip(), baseline)
        code, report = self.check()
        self.assertEqual(code, 3, report)
        self.assertTrue(any(issue['reason'] == 'referenced_input_changed_during_run'
                            and any(row['path'] == path for row in issue['changed_paths'])
                            for issue in report['problems']))

    def test_new_ignored_unresolved_provider_after_capture_prevents_publication(self):
        path = 'research/readiness/method_reviews/late-unresolved.jsonl'
        self.write('.gitignore', (self.repo / '.gitignore').read_text() + '/' + path + '\n')
        baseline = self.commit('ignore a future unresolved provider')
        self.capture()
        self.assertEqual(self.check()[0], 0)
        self.record(path, {**self.method, 'record_id': 'LATE-UNRESOLVED', 'dependencies': None})
        self.assertFalse(self.F.scope('valla')['dynamic_complete'])
        self.assertEqual(self.git('rev-parse', 'HEAD').decode().strip(), baseline)
        code, report = self.check()
        self.assertEqual(code, 3, report)
        self.assertTrue(any(issue['reason'] == 'unresolved_read_closure_after_execution'
                            for issue in report['problems']))

    def test_absent_ignored_target_arrival_after_capture_rejected_without_tree_change(self):
        path = 'ignored/late-after-capture.txt'
        self.record('research/readiness/component_attestations/late.jsonl',
                    {'dependencies': [{'kind': 'file', 'key': path, 'sha256': '0' * 64}]})
        baseline = self.commit('reference an absent ignored target')
        manifest = self.capture()
        self.assertIn(path, manifest['scope']['referenced_files'])
        self.assertNotIn(path, manifest['inputs'])
        self.assertEqual(self.check()[0], 0)
        self.write(path, 'A target arrives after Valla captured its inputs.')
        self.assertEqual(self.git('rev-parse', 'HEAD').decode().strip(), baseline)
        code, report = self.check()
        self.assertEqual(code, 3, report)
        self.assertTrue(any(issue['reason'] == 'referenced_input_changed_during_run'
                            and any(row['path'] == path for row in issue['changed_paths'])
                            for issue in report['problems']))

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_unresolved_symlink_to_ignored_source_is_broad_and_cannot_publish(self):
        original = (self.repo / self.source_path).read_text()
        target = self.write('ignored/source-body.txt', original)
        source = self.repo / self.source_path
        source.unlink()
        source.symlink_to(os.path.relpath(target, source.parent))
        self.commit('source alias with ignored body')
        self.assertEqual(self.git('ls-files', '--', 'ignored/source-body.txt'), b'')
        self.assertTrue(self.F.valla_certified())
        scope = self.F.scope('valla')
        self.assertFalse(scope['dynamic_complete'])
        self.assertIn('*', scope['patterns'])
        self.assertIn('unrelated/body.txt', self.M.input_closure(['valla'])[0])
        # Native reads succeed; broad restoration alone cannot version ignored target bytes.
        self.assertTrue(self.V.build(self.repo)['claims']['EO:1']['component_reviews'][0]['valid'])
        self.capture()
        code, report = self.check()
        self.assertEqual(code, 3, report)
        self.assertTrue(any(issue['reason'] == 'missing_or_invalid_manifest'
                            and 'Unresolved Valla read closure' in issue['detail']
                            for issue in report['problems']))

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_fixed_protocol_symlink_forces_repository_fallback(self):
        path = self.repo / 'jobs/claim-kit/AGENT_PROTOCOL.md'
        target = self.write('ignored/protocol.txt', path.read_text())
        path.unlink()
        path.symlink_to(os.path.relpath(target, path.parent))
        self.commit('fixed protocol alias')
        self.assertTrue(self.F.valla_certified())
        self.assertFalse(self.F.scope('valla')['dynamic_complete'])
        self.assertIn('/**', self.M.input_closure(['valla'])[2]['valla'])
        self.assertIn('unrelated/body.txt', self.M.input_closure(['valla'])[0])

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_provider_directory_symlink_forces_repository_fallback(self):
        provider = self.repo / 'research/readiness/component_attestations'
        target = self.repo / 'ignored/component-providers'
        target.parent.mkdir(parents=True, exist_ok=True)
        provider.rename(target)
        provider.symlink_to(os.path.relpath(target, provider.parent), target_is_directory=True)
        self.commit('provider directory alias')
        self.assertTrue(self.F.valla_certified())
        self.assertFalse(self.F.scope('valla')['dynamic_complete'])
        self.assertIn('*', self.F.scope('valla')['patterns'])
        self.assertIn('/**', self.M.input_closure(['valla'])[2]['valla'])
        self.assertIn('unrelated/body.txt', self.M.input_closure(['valla'])[0])

    def test_actual_runner_preserves_selected_prior_output_on_valla_failure(self):
        prior = {p.name: p.read_bytes() for p in (self.repo / 'jobs/valla/output').iterdir()}
        self.bootstrap()
        self.materialize()
        self.write('research/readiness/claims/broken.jsonl', 'not json\n')
        env = {**os.environ, 'JOBS': 'valla', 'GITHUB_RUN_ID': 'fixture-failure',
               'GITHUB_RUN_ATTEMPT': '1', 'RATTLE_HEARTBEAT_SECONDS': '0.01',
               'PYTHONDONTWRITEBYTECODE': '1'}
        result = subprocess.run([sys.executable, '.github/scripts/run_jobs.py'], cwd=self.repo,
                                env=env, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout.decode() + result.stderr.decode())
        self.assertEqual({p.name: p.read_bytes() for p in (self.repo / 'jobs/valla/output').iterdir()}, prior)
        attempt = self.repo / 'jobs/_attempts/valla/fixture-failure-1'
        self.assertEqual(json.loads((attempt / 'STATUS.json').read_text())['result'], 'failed')
        self.assertTrue((attempt / self.F.MANIFEST).exists())
        receipts = json.loads((self.repo / 'oversized/runner-freshness/ATTEMPTS.json').read_text())
        self.assertTrue(receipts[0]['previous_output_preserved'])
        self.assertFalse(receipts[0]['publish_output'])


if __name__ == '__main__':
    unittest.main()
