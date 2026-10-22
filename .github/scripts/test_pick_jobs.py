"""Offline regression tests for scheduling and the repository's wiring contract."""
import ast
import fnmatch
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

    def test_dispatch_deduplicates_and_orders_consumers(self):
        self.job('producer')
        self.job('consumer', after=['producer'])
        output = Path('outputs.txt')
        with patch.dict(os.environ, EVENT='workflow_dispatch', INPUT_JOB='jobs/producer,producer', GITHUB_OUTPUT=str(output)):
            picker.main()
        self.assertEqual(output.read_text(), 'jobs=producer consumer\n')


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

    def test_outer_workflow_covers_declared_inputs(self):
        # The outer filter intentionally uses directory-wide **. The selector
        # retains the precise fnmatch patterns, so irrelevant changes run no jobs.
        workflow = (ROOT / '.github/workflows/run-jobs.yml').read_text()
        section = workflow.split('    paths:\n', 1)[1].split('  schedule:', 1)[0]
        patterns = re.findall(r'^\s+- "([^"]+)"', section, flags=re.M)
        for name in picker.all_jobs():
            for trigger in picker.job_list(name, 'triggers.txt'):
                self.assertTrue(any(trigger == pattern or (pattern.endswith('/**') and trigger.startswith(pattern[:-2]))
                                    for pattern in patterns), f'{name}: outer workflow excludes {trigger}')

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


if __name__ == '__main__':
    unittest.main()
