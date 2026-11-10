"""Offline regression tests for scheduling and the repository's wiring contract."""
import ast
import fnmatch
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('picker_under_test', ROOT / '.github/scripts/pick_jobs.py')
picker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(picker)


def shared_imports(path, modules):
    """Imports in production Python, including conditional/local imports."""
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split('.')[-1] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or '').split('.')[-1])
            names.update(alias.name for alias in node.names)
    return names & modules


def library_dependencies(job):
    library = ROOT / 'jobs/_lib'
    modules = {p.stem: p for p in library.glob('*.py') if not p.name.startswith('test_')}
    found = set()
    for path in (ROOT / 'jobs' / job).rglob('*.py'):
        if any(p in {'output', 'data', '__pycache__'} for p in path.relative_to(ROOT / 'jobs' / job).parts):
            continue
        if not path.name.startswith('test_'):
            found |= shared_imports(path, set(modules))
    pending = list(found)
    while pending:
        for dep in shared_imports(modules[pending.pop()], set(modules)) - found:
            found.add(dep)
            pending.append(dep)
    return {f'jobs/_lib/{name}.py' for name in found}


class SchedulerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = Path.cwd()
        os.chdir(self.tmp.name)
        Path('jobs').mkdir()
        # No test reaches GitHub; tests of the run-history lookup patch github() themselves.
        history = patch.object(picker, 'previous_sweep_commit', return_value=None)
        history.start()
        self.addCleanup(history.stop)

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def job(self, name, after=(), triggers=(), runnable=True):
        folder = Path('jobs') / name
        folder.mkdir(parents=True)
        if runnable:
            (folder / 'job.py').touch()
        (folder / 'after.txt').write_text('\n'.join(after))
        (folder / 'triggers.txt').write_text('\n'.join(triggers))

    def test_upload_selects_producer_then_consumers_without_upstream_fetch(self):
        self.job('ingest', triggers=['ProQuest Pre-1937 Orders/*', 'research/pre-1937-sources/*'])
        self.job('ladder')
        self.job('tracker', after=['ingest', 'ladder'])
        self.job('clark', after=['tracker'])
        self.job('lewis', after=['clark', 'tracker'])
        self.job('register', after=['clark', 'lewis'])
        for path in ['ProQuest Pre-1937 Orders/1900-EO-1.pdf', 'research/pre-1937-sources/pdfs/1.pdf']:
            selected = picker.ordered(picker.with_consumers(picker.for_changes([path])))
            self.assertEqual(selected, ['ingest', 'tracker', 'clark', 'lewis', 'register'])

    def test_outputs_unrelated_files_and_shared_docs_do_not_start_jobs(self):
        self.job('ingest', triggers=['jobs/*', 'jobs/_lib/fetch_pool.py'])
        for path in ['jobs/ingest/output/FRAGMENTS.jsonl', 'README.md', 'HANDOFF/notes-codex.md']:
            self.assertEqual(picker.for_changes([path]), [])
        self.job('other')
        self.assertEqual(picker.for_changes(['jobs/_lib/fetch_pool.py']), ['ingest'])

    def test_library_patterns_are_narrow(self):
        self.job('fetcher', triggers=['jobs/_lib/fetch_pool.py'])
        self.job('search', triggers=['jobs/_lib/eo_websearch.py', 'jobs/_lib/search_engines.json'])
        self.assertEqual(picker.for_changes(['jobs/_lib/eo_websearch.py']), ['search'])
        self.assertEqual(picker.for_changes(['jobs/_lib/README.md']), [])
        self.assertEqual(picker.for_changes(['jobs/_lib/test_fetch_pool.py']), [])

    def test_runner_edits_only_select_smoke_test(self):
        self.job('example-hello')
        self.job('heavy')
        self.assertEqual(picker.for_changes(['.github/scripts/run_jobs.py']), ['example-hello'])

    def test_cycles_fail_with_actionable_path(self):
        self.job('a', after=['b'])
        self.job('b', after=['a'])
        with self.assertRaisesRegex(ValueError, 'a -> b -> a'):
            picker.ordered(['a', 'b'])

    def test_manual_harvested_predecessor_is_not_made_runnable(self):
        self.job('harvest', runnable=False)
        self.job('consumer', after=['harvest'])
        self.assertEqual(picker.all_jobs(), ['consumer'])
        self.assertEqual(picker.ordered(picker.with_consumers(['consumer'])), ['consumer'])

    def run_main(self, **env):
        output = Path('outputs.txt')
        output.write_text('')
        with patch.dict(os.environ, GITHUB_OUTPUT=str(output), **env):
            picker.main()
        return dict(line.split('=', 1) for line in output.read_text().splitlines())

    def test_push_runs_only_edited_jobs_and_nothing_downstream(self):
        self.job('producer', triggers=['inputs/*'])
        self.job('consumer', after=['producer'])
        with patch.object(picker, 'changed_files', return_value=['inputs/data.csv', 'jobs/consumer/job.py']):
            out = self.run_main(EVENT='push', AFTER='x')
        self.assertEqual(out, {'jobs': 'consumer', 'direct': 'consumer'})
        with patch.object(picker, 'changed_files', return_value=['inputs/data.csv', 'HANDOFF/notes-claude.md']):
            out = self.run_main(EVENT='push', AFTER='x')
        self.assertEqual(out, {'direct': '', 'jobs': ''})

    def test_sweep_runs_triggered_jobs_and_consumers_and_marks_downstream(self):
        self.job('producer', triggers=['inputs/*'])
        self.job('consumer', after=['producer'])
        self.job('unrelated')
        with patch.object(picker, 'recent_changes', return_value=['inputs/data.csv']):
            out = self.run_main(EVENT='schedule', SCHEDULE='47 */3 * * *')
        self.assertEqual(out, {'direct': 'producer', 'jobs': 'producer consumer', 'downstream': 'consumer'})

    def test_sweep_adds_daily_jobs_without_a_recent_receipt(self):
        # Justinian 2026-11-06 (B4): GitHub delivers only the sweep, so each sweep runs a DAILY job
        # whose newest receipt is older than DAILY_STALE_HOURS (or missing), at full strength.
        for name in ('stale', 'fresh', 'never'):
            self.job(name)
            Path(f'jobs/{name}/DAILY').touch()
        self.job('consumer', after=['stale'])
        ages = {'stale': picker.DAILY_STALE_HOURS + 1, 'fresh': 2, 'never': None}
        with patch.object(picker, 'recent_changes', return_value=[]), \
                patch.object(picker, 'receipt_age_hours', side_effect=lambda name, now=None: ages[name]):
            out = self.run_main(EVENT='schedule', SCHEDULE='47 */3 * * *')
        jobs = out['jobs'].split()
        self.assertEqual(set(jobs), {'never', 'stale', 'consumer'})
        self.assertLess(jobs.index('stale'), jobs.index('consumer'))
        self.assertEqual(out.get('downstream'), 'consumer')

    def test_daily_run_runs_daily_jobs_with_consumers_at_full_strength(self):
        self.job('producer')
        Path('jobs/producer/DAILY').touch()
        self.job('consumer', after=['producer'])
        # The daily run is also a sweep (2026-11-09), so it reads changes too; none here.
        with patch.object(picker, 'sweep_changes', return_value=[]):
            out = self.run_main(EVENT='schedule', SCHEDULE=picker.DAILY_CRON)
        self.assertEqual(out, {'direct': 'producer', 'jobs': 'producer consumer'})

    def test_daily_run_is_also_a_sweep(self):
        # Every scheduled run is a sweep, so the previous scheduled run is always the previous sweep.
        self.job('producer')
        Path('jobs/producer/DAILY').touch()
        self.job('edited')
        self.job('reader', after=['edited'])
        with patch.object(picker, 'sweep_changes', return_value=['jobs/edited/job.py']):
            out = self.run_main(EVENT='schedule', SCHEDULE=picker.DAILY_CRON)
        self.assertEqual(set(out['jobs'].split()), {'producer', 'edited', 'reader'})
        self.assertEqual(out.get('downstream'), 'reader')

    def test_sweep_runs_jobs_whose_own_folder_changed(self):
        # With no push trigger, the sweep is what runs a job edited on main.
        self.job('edited')
        self.job('reader', after=['edited'])
        with patch.object(picker, 'sweep_changes', return_value=['jobs/edited/job.py', 'jobs/reader/output/X.csv']):
            out = self.run_main(EVENT='schedule', SCHEDULE='47 */3 * * *')
        self.assertEqual(out, {'direct': 'edited', 'jobs': 'edited reader', 'downstream': 'reader'})

    def test_only_runs_exactly_the_named_jobs_and_publishes(self):
        self.job('producer')
        self.job('consumer', after=['producer'])
        out = self.run_main(EVENT='workflow_dispatch', INPUT_JOB='producer', ONLY='true')
        self.assertEqual(out, {'jobs': 'producer', 'direct': 'producer'})
        out = self.run_main(EVENT='workflow_dispatch', INPUT_JOB='producer', ONLY='false')
        self.assertEqual(out['jobs'], 'producer consumer')

    def test_dispatch_deduplicates_and_orders_consumers(self):
        self.job('producer')
        self.job('consumer', after=['producer'])
        output = Path('outputs.txt')
        with patch.dict(os.environ, EVENT='workflow_dispatch', INPUT_JOB='jobs/producer,producer', GITHUB_OUTPUT=str(output)):
            picker.main()
        self.assertEqual(output.read_text(), 'jobs=producer consumer\ndirect=producer\n')


    def test_diagnostic_runs_only_named_jobs_in_dependency_order(self):
        self.job('producer')
        self.job('consumer', after=['producer'])
        self.job('tracker', after=['consumer'])
        out = self.run_main(EVENT='workflow_dispatch', INPUT_JOB='consumer,producer,consumer',
                            DIAGNOSTIC='true')
        self.assertEqual(out['jobs'], 'producer consumer')

    def test_runtime_push_exemption_is_exact_and_push_only(self):
        self.job('claim-kit')
        runtime = ['jobs/claim-kit/batch.py', 'jobs/claim-kit/completion.py']
        with patch.object(picker, 'claim_kit_runtime_only', wraps=picker.claim_kit_runtime_only) as guard:
            self.assertEqual(picker.for_changes(runtime), ['claim-kit'])
            guard.assert_not_called()
        with patch.object(picker, 'claim_kit_runtime_only', return_value=True):
            self.assertEqual(picker.for_changes(runtime, triggers=False, runtime_push=True), [])
        for extra in ('jobs/claim-kit/build.py', 'jobs/claim-kit/prior_research.py',
                      'jobs/claim-kit/inputs.txt', 'jobs/claim-kit/data/new.json',
                      'jobs/claim-kit/new_runtime.py', 'research/readiness/decisions/new.json',
                      'jobs/clause-drafts/segment.py', 'README.md'):
            self.assertFalse(picker.claim_kit_runtime_only(runtime + [extra]), extra)
            self.assertEqual(picker.for_changes(runtime + [extra], triggers=False, runtime_push=True),
                             ['claim-kit'], extra)

    def test_compiler_guard_hashes_files_and_fails_closed(self):
        runtime = ['jobs/claim-kit/completion.py']
        self.job('claim-kit')
        compiler = Path('compiler.py')
        raw = b'compiler version\n'
        compiler.write_bytes(raw)
        pins = {str(compiler): (hashlib.sha256(raw).hexdigest(),)}
        with patch.object(picker, 'CLAIM_KIT_COMPILER_SHA256', pins):
            self.assertTrue(picker.claim_kit_runtime_only(runtime))
            compiler.write_bytes(raw + b'from completion import anything\n')
            self.assertFalse(picker.claim_kit_runtime_only(runtime))
            self.assertEqual(picker.for_changes(runtime, triggers=False, runtime_push=True), ['claim-kit'])
            compiler.unlink()
            with patch.object(picker.subprocess, 'run') as git_show:
                git_show.return_value.returncode = 1
                self.assertFalse(picker.claim_kit_runtime_only(runtime))
                git_show.return_value.returncode = 0
                git_show.return_value.stdout = raw
                self.assertTrue(picker.claim_kit_runtime_only(runtime))

    def test_runtime_push_keeps_daily_sweep_and_manual_rebuilds(self):
        self.job('claim-kit')
        Path('jobs/claim-kit/DAILY').touch()
        runtime = ['jobs/claim-kit/completion.py']
        with patch.object(picker, 'claim_kit_runtime_only', return_value=True):
            with patch.object(picker, 'changed_files', return_value=runtime):
                self.assertEqual(self.run_main(EVENT='push', AFTER='x'), {'direct': '', 'jobs': '', 'runtime_tests': 'claim-kit'})
            with patch.object(picker, 'recent_changes', return_value=runtime):
                self.assertEqual(self.run_main(EVENT='schedule', SCHEDULE='47 */3 * * *'), {'direct': 'claim-kit', 'jobs': 'claim-kit'})
            with patch.object(picker, 'sweep_changes', return_value=[]):
                self.assertEqual(self.run_main(EVENT='schedule', SCHEDULE=picker.DAILY_CRON), {'direct': 'claim-kit', 'jobs': 'claim-kit'})
            self.assertEqual(self.run_main(EVENT='workflow_dispatch', INPUT_JOB='claim-kit'), {'direct': 'claim-kit', 'jobs': 'claim-kit'})


@unittest.skipUnless((ROOT / 'jobs').is_dir(), 'repository integration fixtures not present')
class RepositoryWiringTest(unittest.TestCase):
    def setUp(self):
        self.old = Path.cwd()
        os.chdir(ROOT)

    def tearDown(self):
        os.chdir(self.old)

    def test_dependency_graph_has_no_cycles_or_missing_producers(self):
        jobs = picker.all_jobs()
        ordered = picker.ordered(jobs)
        for name in jobs:
            for dep in picker.job_list(name, 'after.txt'):
                self.assertTrue((ROOT / 'jobs' / dep).is_dir(), f'{name}: unknown producer {dep}')
                if dep in jobs:
                    self.assertLess(ordered.index(dep), ordered.index(name), f'{dep} must precede {name}')

    def test_python_library_consumers_declare_transitive_triggers(self):
        missing = []
        for name in picker.all_jobs():
            patterns = picker.job_list(name, 'triggers.txt')
            for dep in library_dependencies(name):
                if not any(fnmatch.fnmatchcase(dep, pattern) for pattern in patterns):
                    missing.append(f'{name}: {dep}')
        self.assertEqual(missing, [], '\n'.join(missing))

    def test_no_push_starts_runs_and_the_sweep_is_scheduled(self):
        # Owner 2026-11-09 (Kean D-20261109-no-push-runs): only the schedule and manual runs start
        # Run jobs. .github/scripts/test_workflow_triggers.py holds the full trigger policy.
        workflow = (ROOT / '.github/workflows/run-jobs.yml').read_text()
        on = workflow.split('\non:\n', 1)[1].split('\n\n', 1)[0]
        self.assertNotRegex(on, r'(?m)^  (push|pull_request|workflow_run|workflow_call):')
        self.assertIn(f'cron: "{picker.DAILY_CRON}"', workflow)
        self.assertIn('cron: "47 */3 * * *"', workflow)
        self.assertIn('SCHEDULE: ${{ github.event.schedule }}', workflow)
        self.assertIn('ONLY: ${{ github.event.inputs.only }}', workflow)
        plan = workflow.split('\n  plan:\n', 1)[1].split('\n  execute:\n', 1)[0]
        self.assertIn('      actions: read', plan.split('    outputs:', 1)[0])
        self.assertIn('GITHUB_TOKEN: ${{ github.token }}', plan)


    def test_runtime_allowlist_excludes_conservative_compiler_closure(self):
        if not picker.claim_kit_runtime_only(['jobs/claim-kit/completion.py']):
            self.skipTest('compiler certificate expired; pushes use default rebuild')
        self.assertFalse(set(picker.CLAIM_KIT_COMPILER_SHA256) & picker.CLAIM_KIT_RUNTIME_ONLY)
        tree = ast.parse((ROOT / 'jobs/claim-kit/inputs.py').read_text())
        declared = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'COMPILER_FILES' for t in n.targets))
        for path in declared:
            relative = (ROOT / 'jobs/claim-kit' / path).resolve().relative_to(ROOT).as_posix()
            self.assertIn(relative, picker.CLAIM_KIT_COMPILER_SHA256)
        # All static imports, including imports local to a function, stay in the
        # closure. The three literal dynamic imports are pinned explicitly.
        modules = {p.stem: p.relative_to(ROOT).as_posix()
                   for p in (ROOT / 'jobs/claim-kit').glob('*.py')}
        for relative in picker.CLAIM_KIT_COMPILER_SHA256:
            path = ROOT / relative
            if path.is_file():
                for name in shared_imports(path, set(modules)):
                    self.assertIn(modules[name], picker.CLAIM_KIT_COMPILER_SHA256, relative)
        for relative in ('jobs/claim-kit/prior_research.py', 'jobs/norton/model.py',
                         'jobs/clause-drafts/segment.py', 'research/stage19/code/claim_gate.py'):
            self.assertIn(relative, picker.CLAIM_KIT_COMPILER_SHA256)

    def test_runtime_ci_runs_tests_without_the_production_job(self):
        workflow = (ROOT / '.github/workflows/run-jobs.yml').read_text()
        section = workflow.split('      - name: Materialize claim-kit test fixtures', 1)[1].split(
            "      - name: Plan parallel stations", 1)[0]
        self.assertIn("steps.pick.outputs.runtime_tests == 'claim-kit'", section)
        self.assertIn("unittest.defaultTestLoader.discover('jobs/claim-kit'", section)
        self.assertIn("'/research/stage19/code/**' '/research/plans/claim_kit_contract/**'", section)
        self.assertNotIn('jobs/claim-kit/job.py', section)
        self.assertNotIn('/output/', section)

    def test_real_uploads_select_pinakes(self):
        for path in ['ProQuest Pre-1937 Orders/1873-EO-10.pdf',
                     'research/pre-1937-sources/pdfs/1873-EO-10.pdf',
                     'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv']:
            self.assertIn('pinakes-proquest-ingest', picker.for_changes([path]))

    def test_pinakes_and_csc_reach_readers_in_order(self):
        for producer in ['pinakes-proquest-ingest', 'csc-annual-reports']:
            selected = picker.ordered(picker.with_consumers([producer]))
            for reader in ['claim-drafts', 'claim-kit', 'readiness-tracker', 'clark-discovery', 'lewis-originals', 'domesday-register']:
                self.assertIn(reader, selected)
                self.assertLess(selected.index(producer), selected.index(reader))
            self.assertNotIn('source-ladder', selected)

    def test_ranger_outputs_reach_candidate_register_in_dependency_order(self):
        edges = [('early-ranger-scout', 'early-ranger-reparse'),
                 ('early-ranger-reparse', 'early-ranger-triage'),
                 ('early-ranger-triage', 'early-ranger-original-items'),
                 ('early-ranger-original-items', 'early-ranger-transcriptions'),
                 ('early-ranger-original-items', 'early-ranger-full-pages')]
        selected = picker.ordered(picker.with_consumers(['early-ranger-scout']))
        for producer, consumer in edges:
            self.assertIn(producer, picker.job_list(consumer, 'after.txt'))
            self.assertLess(selected.index(producer), selected.index(consumer))
        # Derive the register's direct job inputs from its literal INPUTS map,
        # so adding another reader cannot silently leave the wiring stale.
        tree = ast.parse((ROOT / 'jobs/census-candidates/job.py').read_text())
        inputs = next(ast.literal_eval(node.value) for node in tree.body
                      if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'INPUTS'
                                                             for t in node.targets))
        for path in inputs.values():
            if path.startswith('jobs/'):
                producer = path.split('/')[1]
                self.assertIn(producer, picker.job_list('census-candidates', 'after.txt'))
                chain = picker.ordered(picker.with_consumers([producer]))
                self.assertLess(chain.index(producer), chain.index('census-candidates'))
            else:
                self.assertIn('census-candidates', picker.for_changes([path]))
        # Refreshing existing transcripts must not refetch their predecessors.
        transcript_chain = picker.with_consumers(['early-ranger-transcriptions'])
        self.assertIn('census-candidates', transcript_chain)
        for upstream in ['early-ranger-scout', 'early-ranger-original-items', 'early-ranger-full-pages']:
            self.assertNotIn(upstream, transcript_chain)

    def test_ranger_research_inputs_select_only_actual_readers(self):
        self.assertIn('early-ranger-scout', picker.for_changes(['research/stage20/output/ARCHIVAL_COVERAGE_GRID.csv']))
        self.assertIn('early-ranger-triage', picker.for_changes(['research/stage18/data/EARLY_SOURCE_CANDIDATES.csv']))
        # Scout declares CURATED but never reads it: do not infer a fetch edge.
        self.assertNotIn('early-ranger-scout', picker.for_changes(['research/stage18/data/EARLY_SOURCE_CANDIDATES.csv']))
        selected = picker.for_changes(['research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv'])
        for reader in ['early-ranger-original-items', 'early-ranger-1862-1906', 'census-candidates']:
            self.assertIn(reader, selected)


class SweepRangeTest(unittest.TestCase):
    """The sweep reads commits after the previous sweep's input, not a clock window."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old = Path.cwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self.old)
        for args in (['init', '-q', '-b', 'main'], ['config', 'user.email', 't@example.invalid'], ['config', 'user.name', 't']):
            picker.git(*args)

    def commit(self, path, date=None):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(path + str(len(list(Path('.').rglob('*')))))
        picker.git('add', '-A')
        env = {**os.environ, **({'GIT_COMMITTER_DATE': date, 'GIT_AUTHOR_DATE': date} if date else {})}
        import subprocess
        subprocess.run(['git', 'commit', '-qm', path], check=True, env=env)
        return picker.git('rev-parse', 'HEAD').stdout.strip()

    def test_old_dated_and_late_commits_after_the_previous_sweep_are_seen(self):
        self.commit('jobs/before/job.py')
        base = self.commit('jobs/seen-by-previous/job.py')
        # A commit dated a week ago but pushed after the previous sweep: a time window misses it.
        self.commit('jobs/old-dated/job.py', date='2026-11-01T00:00:00Z')
        self.commit('research/readiness/claims/new.jsonl')
        with patch.object(picker, 'previous_sweep_commit', return_value=base):
            changed = picker.sweep_changes()
        self.assertEqual(changed, ['jobs/old-dated/job.py', 'research/readiness/claims/new.jsonl'])
        with patch.object(picker, 'previous_sweep_commit', return_value=base), \
                patch.object(picker, 'recent_changes', side_effect=AssertionError('fallback used')):
            picker.sweep_changes()

    def test_unknown_or_foreign_previous_sweep_falls_back_to_the_window(self):
        self.commit('jobs/a/job.py')
        for previous in (None, '0' * 40, 'f' * 40):
            with patch.object(picker, 'previous_sweep_commit', return_value=previous), \
                    patch.object(picker, 'recent_changes', return_value=['window']) as window:
                self.assertEqual(picker.sweep_changes(), ['window'])
                window.assert_called_once()
        # A commit that is not an ancestor (history rewritten) also falls back.
        picker.git('checkout', '-q', '-b', 'other')
        side = self.commit('jobs/side/job.py')
        picker.git('checkout', '-q', 'main')
        with patch.object(picker, 'previous_sweep_commit', return_value=side), \
                patch.object(picker, 'recent_changes', return_value=['window']):
            self.assertEqual(picker.sweep_changes(), ['window'])

    def run_history(self, runs, jobs, run_id='900', **env):
        def fake(path):
            if '/actions/workflows/run-jobs.yml/runs?' in path:
                self.assertIn('event=schedule', path)
                self.assertIn('branch=main', path)
                return {'workflow_runs': runs}
            rid = re.search(r'/actions/runs/(\d+)/jobs', path).group(1)
            return {'jobs': jobs[rid]}
        values = {'GITHUB_REPOSITORY': 'o/r', 'GITHUB_TOKEN': 't', 'GITHUB_RUN_ID': run_id, **env}
        with patch.dict(os.environ, values), patch.object(picker, 'github', side_effect=fake):
            return picker.previous_sweep_commit()

    def test_previous_sweep_is_the_newest_earlier_run_whose_plan_succeeded(self):
        sha = lambda c: c * 40
        runs = [
            {'id': 900, 'created_at': '2026-11-09T12:47:00Z', 'status': 'in_progress', 'conclusion': None, 'head_sha': sha('9')},
            {'id': 950, 'created_at': '2026-11-09T13:00:00Z', 'status': 'completed', 'conclusion': 'success', 'head_sha': sha('e')},
            {'id': 890, 'created_at': '2026-11-09T09:47:00Z', 'status': 'in_progress', 'conclusion': None, 'head_sha': sha('8')},
            {'id': 880, 'created_at': '2026-11-09T06:47:00Z', 'status': 'completed', 'conclusion': 'cancelled', 'head_sha': sha('7')},
            {'id': 870, 'created_at': '2026-11-09T03:47:00Z', 'status': 'completed', 'conclusion': 'failure', 'head_sha': sha('6')},
            {'id': 860, 'created_at': '2026-11-09T00:47:00Z', 'status': 'completed', 'conclusion': 'failure', 'head_sha': sha('5')},
            {'id': 850, 'created_at': '2026-11-08T21:47:00Z', 'status': 'completed', 'conclusion': 'success', 'head_sha': sha('4')},
        ]
        jobs = {'870': [{'name': 'plan', 'conclusion': 'failure'}],
                '860': [{'name': 'plan', 'conclusion': 'success'}, {'name': 'publish', 'conclusion': 'failure'}],
                '850': [{'name': 'plan', 'conclusion': 'success'}]}
        # Skips itself, a later run, an unfinished one, a cancelled one and one whose plan failed;
        # a run refused at publish still planned, and its refused jobs were re-queued.
        self.assertEqual(self.run_history(runs, jobs), sha('5'))

    def test_run_history_failures_never_guess(self):
        self.assertIsNone(self.run_history([], {}))
        bad = [{'id': 1, 'created_at': '2026-11-09T00:00:00Z', 'status': 'completed', 'conclusion': 'success', 'head_sha': 'not-a-sha'}]
        self.assertIsNone(self.run_history(bad, {'1': [{'name': 'plan', 'conclusion': 'success'}]}))
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'o/r', 'GITHUB_TOKEN': 't'}), \
                patch.object(picker, 'github', side_effect=OSError('rate limited')):
            self.assertIsNone(picker.previous_sweep_commit())
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'o/r', 'GITHUB_TOKEN': 't'}), \
                patch.object(picker, 'github', return_value={'unexpected': 1}):
            self.assertIsNone(picker.previous_sweep_commit())
        with patch.dict(os.environ, {'GITHUB_TOKEN': ''}), patch.object(picker, 'github', side_effect=AssertionError):
            self.assertIsNone(picker.previous_sweep_commit())


if __name__ == '__main__':
    unittest.main()
