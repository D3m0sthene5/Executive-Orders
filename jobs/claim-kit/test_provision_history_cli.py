"""Exercise public MAITLAND commands against exact reviewed native fixtures."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import unittest

import kit
import test_provision_history as fixtures


class ProvisionHistoryCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ProvisionHistoryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.write()
        self.repo = self.fixture.repo

    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            code = kit.main(['--repo', str(self.repo), *map(str, args)])
        return code, output.getvalue()

    def test_bundle_validation_is_not_scientific_approval(self):
        code, output = self.run_cli('history-check', self.fixture.bundle_path)
        self.assertEqual(code, 0)
        report = json.loads(output)
        self.assertTrue(report['mechanical_validation_passed'])
        self.assertFalse(report['canonical_approval'])
        self.assertFalse(report['human_certified'])

    def test_query_writes_only_new_progress_json(self):
        output_path = self.repo/'research/progress/answer.json'
        code, output = self.run_cli('history-at', self.fixture.bundle_path, '--provision', self.fixture.pid,
                                    '--on', '2020-06-01', '--write', output_path)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output), json.loads(output_path.read_text()))
        self.assertEqual(json.loads(output)['text_version']['text'], 'The board shall use red ink.')
        self.assertEqual(self.run_cli('history-at', self.fixture.bundle_path, '--provision', self.fixture.pid,
                                     '--on', '2020-06-01', '--write', output_path)[0], 2)

    def test_canonical_and_non_json_destinations_refused(self):
        for rel in ('research/readiness/claims/query.json', 'research/progress/query.jsonl'):
            path = self.repo/rel
            code, _ = self.run_cli('history-at', self.fixture.bundle_path, '--provision', self.fixture.pid,
                                    '--on', '2020-06-01', '--write', path)
            self.assertEqual(code, 2)
            self.assertFalse(path.exists())

    def test_changed_source_refuses_answer_without_writing(self):
        self.fixture.source('P17-EO_1-duty', 'Changed source.')
        dest = self.repo/'research/progress/refused.json'
        code, _ = self.run_cli('history-at', self.fixture.bundle_path, '--provision', self.fixture.pid,
                                '--on', '2020-06-01', '--write', dest)
        self.assertEqual(code, 2)
        self.assertFalse(dest.exists())

    def test_single_answer_revalidation_uses_existing_valla_closure(self):
        answer = self.repo/'research/progress/answer.json'
        code, _ = self.run_cli('history-at', self.fixture.bundle_path, '--provision', self.fixture.pid,
                                '--on', '2020-06-01', '--write', answer)
        self.assertEqual(code, 0)
        result = json.loads(answer.read_text())
        dependency = next(k for k in result['dependencies'] if k.startswith('source:'))
        changed = self.repo/'research/progress/changed.json'
        changed.write_text(json.dumps({dependency: '0'*64}))
        code, output = self.run_cli('history-impact', answer, '--changed', changed)
        self.assertEqual(code, 0)
        impact = json.loads(output)
        self.assertEqual(impact['affected_queries'], [result['query_id']])
        self.assertEqual(impact['affected_provisions'], ['provision:'+self.fixture.pid])

    def test_impact_refuses_missing_or_malformed_json_shapes(self):
        changed=self.repo/'research/changed.json';changed.write_text('{}')
        saved=self.repo/'research/missing.json'
        self.assertEqual(self.run_cli('history-impact',saved,'--changed',changed)[0],2)
        for value in ([],None,{'schema':'eo-provision-history-results/v1','queries':None},
                      {'schema':'eo-provision-history-results/v1','queries':[{'query_id':'q','provision_id':'p','dependencies':[]}]}):
            saved.write_text(json.dumps(value))
            self.assertEqual(self.run_cli('history-impact',saved,'--changed',changed)[0],2)


if __name__ == '__main__':
    unittest.main()
