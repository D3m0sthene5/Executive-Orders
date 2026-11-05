"""Native Lachmann -> tracker repetition, including invalidated evidence."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'jobs/readiness-tracker'))
import lachmann as L
import tracker
from test_lachmann import GOOD, ORDER


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class RepeatProduction(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'research/stage19/code', self.root / 'research/stage19/code',
                        ignore=shutil.ignore_patterns('test_*', '__pycache__'))
        for relative in tracker.P.values():
            if relative.endswith('.csv'):
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('instrument_id\n', encoding='utf-8')
        iid = ORDER['instrument_id']
        write_csv(self.root / tracker.P['universe'], [{'id': iid, 'included_in_bibliography': '1'}])
        write_csv(self.root / tracker.P['decided'], [
            {'instrument_id': iid, 'provisional_substantive_status': 'no', 'decision_origin': 'fixture'}])
        write_csv(self.root / L.REGISTER_CSV, [{k: ORDER[k] for k in
                  ('instrument_id', 'number', 'suffix', 'date', 'title')}])
        self.text = self.root / 'jobs/app-executive-orders/output/texts/EO_5077.txt'
        self.text.parent.mkdir(parents=True)
        self.text.write_text(GOOD, encoding='utf-8')
        self.fragment = self.root / 'jobs/app-executive-orders/output/FRAGMENTS.jsonl'
        self.fragment.write_text(json.dumps({
            'kind': 'original_representation', 'instrument_id': iid,
            'produced_by': 'app-executive-orders', 'data': {
                'url': 'https://example.invalid/eo5077', 'sha256': 'a' * 64,
                'text_path': self.text.relative_to(self.root).as_posix(),
                'text_sha256': hashlib.sha256(self.text.read_bytes()).hexdigest(),
                'grade': 'mirror_transcription', 'acceptable_as_original': False,
                'needs_page_check': False}}) + '\n', encoding='utf-8')
        self.output = self.root / 'jobs/lachmann/output'

    def recount(self):
        rows, _ = tracker.build(str(self.root))
        write_csv(self.root / L.TRACKER_CSV, rows)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['ready_for_human_review'], 'no')
        return rows[0]

    def first_pass(self):
        self.assertEqual(self.recount()['step_original_text'], 'open')
        self.assertEqual(L.run(self.root, self.output)['confirmed'], 1)
        row = self.recount()
        self.assertEqual(row['step_original_text'], 'provisional')
        self.assertEqual(row['provisional_text_method'], 'machine')

    def test_second_pass_revalidates_previously_provisional_text(self):
        self.first_pass()
        before = (self.output / 'CONFIRMATIONS.jsonl').read_bytes()
        self.assertEqual(L.run(self.root, self.output)['confirmed'], 1)
        self.assertEqual((self.output / 'CONFIRMATIONS.jsonl').read_bytes(), before)
        self.assertEqual(self.recount()['step_original_text'], 'provisional')

    def test_second_pass_refuses_changed_bytes_instead_of_carrying_approval(self):
        self.first_pass()
        self.text.write_text('Changed after confirmation', encoding='utf-8')
        result = L.run(self.root, self.output)
        self.assertEqual(result['assessed'], 1)
        self.assertEqual(result['confirmed'], 0)
        self.assertGreater(result['witnesses_skipped_hash_mismatch'], 0)
        self.assertEqual(self.recount()['step_original_text'], 'open')

    def test_second_pass_refuses_removed_declaration(self):
        self.first_pass()
        self.fragment.unlink()
        self.assertEqual(L.run(self.root, self.output)['confirmed'], 0)
        self.assertEqual(self.recount()['step_original_text'], 'open')

    def test_repeat_preserves_agent_rejection_precedence(self):
        self.first_pass()
        record = json.loads((self.output / 'CONFIRMATIONS.jsonl').read_text())
        record.update(method='agent', confirmed=False, complete_text_confirmed=False)
        agent_path = self.output / 'AGENT_CONFIRMATIONS.jsonl'
        agent_path.write_text(json.dumps(record) + '\n', encoding='utf-8')
        original = agent_path.read_bytes()
        self.assertEqual(self.recount()['step_original_text'], 'open')
        self.assertEqual(L.run(self.root, self.output)['confirmed'], 1)
        self.assertEqual(agent_path.read_bytes(), original)
        self.assertEqual(self.recount()['step_original_text'], 'open')


if __name__ == '__main__':
    unittest.main()
