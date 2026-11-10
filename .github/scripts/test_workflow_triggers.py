"""Adversarial tests for the workflow trigger policy (workflow_triggers.py).

Each attack below is a way someone could, on purpose or by accident, bring back push-started job
runs or tag-started workflows. Every one must be reported; the ordinary forms must pass.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('workflow_triggers', ROOT / '.github/scripts/workflow_triggers.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

GOOD_RUN_JOBS = """name: Run jobs

on:
  # comment lines are fine
  schedule:
    - cron: "17 9 * * *"
    - cron: "47 */3 * * *"
  workflow_dispatch:
    inputs:
      job:
        description: "Job names"
        required: true
      only:
        type: boolean
        options:
          - a

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - run: echo push
"""

ORDINARY = """name: Checks
on:
  pull_request:
    paths: ['jobs/**']
  push:
    branches: [main]
    paths:
      - 'jobs/**'
jobs:
  test:
    runs-on: ubuntu-latest
"""


def run_jobs(on_block):
    return "name: Run jobs\n\non:\n" + on_block + "\njobs:\n  plan:\n    runs-on: ubuntu-latest\n"


def other(on_block, body="jobs:\n  t:\n    runs-on: ubuntu-latest\n"):
    return "name: Other\non:\n" + on_block + "\n" + body


class TriggerPolicyTest(unittest.TestCase):
    def assertRefused(self, name, text, fragment=''):
        problems = policy.check(name, text)
        self.assertTrue(problems, f'{name} was accepted:\n{text}')
        if fragment:
            self.assertTrue(any(fragment in p for p in problems), problems)

    def assertAccepted(self, name, text):
        self.assertEqual(policy.check(name, text), [])

    def test_the_repository_follows_the_policy(self):
        self.assertEqual(policy.check_repository(), [])

    def test_ordinary_forms_pass(self):
        self.assertAccepted('run-jobs.yml', GOOD_RUN_JOBS)
        self.assertAccepted('run-jobs.yml', GOOD_RUN_JOBS.replace('\n', '\r\n'))
        self.assertAccepted('checks.yml', ORDINARY)
        self.assertAccepted('kean.yml', other('  pull_request:\n  push:\n    branches: [main]\n'))
        self.assertAccepted('stage21-batchforge.yml', other('  workflow_dispatch:\n'))
        # A manual-only workflow may start Run jobs (daily-dispatch.yml does).
        self.assertAccepted('daily.yml', other('  workflow_dispatch:\n',
                                               'jobs:\n  d:\n    steps:\n      - run: gh workflow run run-jobs.yml\n'))
        # Listening for Run jobs to finish is not starting it.
        self.assertAccepted('refresh.yml', other("  workflow_run:\n    workflows: ['Run jobs']\n    types: [completed]\n    branches: [main]\n"))

    def test_run_jobs_never_starts_on_push_in_any_spelling(self):
        attacks = {
            'inline scalar': 'name: Run jobs\non: push\njobs: {}\n',
            'inline list': 'name: Run jobs\non: [push, workflow_dispatch]\njobs: {}\n',
            'inline mapping': 'name: Run jobs\non: {push: {branches: [main]}}\njobs: {}\n',
            'double-quoted key': 'name: Run jobs\n"on":\n  push:\n    branches: [main]\n  schedule:\n    - cron: "1 * * * *"\njobs: {}\n',
            'single-quoted key': "name: Run jobs\n'on':\n  push:\n    branches: [main]\njobs: {}\n",
            'YAML 1.1 true key': 'name: Run jobs\ntrue:\n  push:\n    branches: [main]\njobs: {}\n',
            'push to main only': run_jobs('  schedule:\n    - cron: "1 * * * *"\n  push:\n    branches: [main]\n'),
            'flow-mapped push': run_jobs('  schedule:\n    - cron: "1 * * * *"\n  push: {branches: [main]}\n'),
            'pull request': run_jobs('  schedule:\n    - cron: "1 * * * *"\n  pull_request:\n'),
            'pull_request_target': run_jobs('  schedule:\n    - cron: "1 * * * *"\n  pull_request_target:\n'),
            'workflow_run chain': run_jobs('  schedule:\n    - cron: "1 * * * *"\n  workflow_run:\n    workflows: [X]\n'),
            'reusable call': run_jobs('  schedule:\n    - cron: "1 * * * *"\n  workflow_call:\n'),
            'second on key': run_jobs('  schedule:\n    - cron: "1 * * * *"\n') + 'on:\n  push:\n',
            'anchor merge': run_jobs('  schedule: &s\n    - cron: "1 * * * *"\n  <<: *t\n'),
            'alias value': run_jobs('  schedule:\n    - cron: "1 * * * *"\n  push: *p\n'),
            'tab indentation': run_jobs('\tpush:\n'),
            'no schedule': run_jobs('  workflow_dispatch:\n'),
        }
        for label, text in attacks.items():
            with self.subTest(label):
                self.assertRefused('run-jobs.yml', text)

    def test_push_triggers_never_fire_on_tags(self):
        attacks = {
            'paths only': '  push:\n    paths: [jobs/**]\n',
            'bare push': '  push:\n',
            'empty branches': '  push:\n    branches: []\n',
            'wildcard branches': "  push:\n    branches: ['**']\n",
            'pattern branch': '  push:\n    branches:\n      - release/*\n',
            'negated branch': "  push:\n    branches: [main, '!main']\n",
            'tags': '  push:\n    branches: [main]\n    tags: [v*]\n',
            'tags-ignore': '  push:\n    branches: [main]\n    tags-ignore: [x]\n',
            'branches-ignore': '  push:\n    branches-ignore: [gh-pages]\n',
            'inline push': '  push: {}\n',
        }
        for label, block in attacks.items():
            with self.subTest(label):
                if label == 'inline push':
                    self.assertRefused('x.yml', other(block), 'push')
                else:
                    self.assertRefused('x.yml', other(block))

    def test_retired_workflows_stay_manual(self):
        for name in sorted(policy.RETIRED):
            with self.subTest(name):
                self.assertRefused(name, other('  workflow_dispatch:\n  schedule:\n    - cron: "1 * * * *"\n'), 'retired')
                self.assertRefused(name, other('  workflow_dispatch:\n  pull_request:\n'), 'retired')
                self.assertRefused(name, other('  workflow_dispatch:\n  push:\n    branches: [main]\n'), 'retired')
                self.assertAccepted(name, other('  workflow_dispatch:\n'))

    def test_automatic_workflows_cannot_start_run_jobs_indirectly(self):
        bodies = {
            'gh dispatch': 'jobs:\n  a:\n    steps:\n      - run: gh workflow run run-jobs.yml -f job=x\n',
            'api dispatch': 'jobs:\n  a:\n    steps:\n      - run: curl -X POST $API/actions/workflows/run-jobs.yml/dispatches\n',
            'reusable call': 'jobs:\n  a:\n    uses: ./.github/workflows/run-jobs.yml\n',
            'by name': "jobs:\n  a:\n    steps:\n      - run: gh workflow run 'Run jobs'\n",
        }
        for trigger in ('  push:\n    branches: [main]\n', '  pull_request:\n',
                        "  workflow_run:\n    workflows: ['Kean']\n"):
            for label, body in bodies.items():
                with self.subTest(trigger=trigger.split(':')[0].strip(), attack=label):
                    self.assertRefused('sneaky.yml', other(trigger, body), 'may not start Run jobs')
        # A mention in a comment is not a dispatch.
        self.assertAccepted('note.yml', other('  pull_request:\n', 'jobs:\n  a:\n    # see run-jobs.yml\n    runs-on: x\n'))

    def test_repository_scan_covers_yaml_files_and_a_missing_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / '.github/workflows'
            folder.mkdir(parents=True)
            (folder / 'sneaky.yaml').write_text(other('  push:\n    paths: [x]\n'), encoding='utf-8')
            problems = policy.check_repository(tmp)
            self.assertTrue(any('sneaky.yaml' in p for p in problems), problems)
            self.assertTrue(any('run-jobs.yml is missing' in p for p in problems), problems)

    def test_each_defense_holds_on_its_own(self):
        # Mutation testing showed attacks refused for the wrong reason; pin each rule's own message.
        self.assertRefused('run-jobs.yml', 'name: Run jobs\non: push\njobs: {}\n', 'not inline')
        self.assertRefused('run-jobs.yml', run_jobs('  schedule:\n    - cron: "1 * * * *"\n  push: {branches: [main]}\n'), 'as a block')
        self.assertRefused('x.yml', other('  push:\n    branches: *b\n'), 'anchors')
        self.assertRefused('x.yml', other('  push:\n    branches: [main]\n    paths: &p [x]\n'), 'anchors')
        self.assertRefused('x.yml', other('  push:\n\t  branches: [main]\n'), 'tabs')
        for key in ('"on"', "'on'", 'true', '"true"'):
            with self.subTest(key):
                text = GOOD_RUN_JOBS.replace('\non:\n', '\n' + key + ':\n')
                self.assertAccepted('run-jobs.yml', text)
                bad = text.replace('  workflow_dispatch:\n', '  push:\n    branches: [main]\n  workflow_dispatch:\n')
                self.assertRefused('run-jobs.yml', bad, 'Run jobs may start only')

    def test_this_guard_stays_wired_into_ci(self):
        # Dropping the guard from the road tests, or the road tests from workflow changes, fails here.
        roads = (ROOT / '.github/scripts/test_roads.py').read_text(encoding='utf-8')
        self.assertIn("'.github/scripts/test_workflow_triggers.py'", roads)
        workflow = (ROOT / '.github/workflows/road-tests.yml').read_text(encoding='utf-8')
        events = policy.triggers(workflow)
        self.assertIn('.github/**', events['pull_request']['paths'])
        self.assertIn('.github/**', events['push']['paths'])
        self.assertEqual(events['push']['branches'], ['main'])
        self.assertIn('run: python .github/scripts/test_roads.py', workflow)

    def test_unreadable_trigger_blocks_fail_closed(self):
        for label, block in {'empty': '', 'only comments': '  # nothing\n',
                             'list at event level': '  - push\n', 'odd line': '  push branches main\n'}.items():
            with self.subTest(label):
                self.assertRefused('x.yml', other(block))


if __name__ == '__main__':
    unittest.main()
