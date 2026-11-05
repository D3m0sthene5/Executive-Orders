"""Native Lachmann -> tracker repetition, including invalidated evidence."""
import copy
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

    def file_dependent_claim(self):
        # A synthetic current checker receipt isolates tracker/confirmation
        # liveness; this fixture does not assert a legal or source-check result.
        from test_tracker import COMPLETE_NO_CLAIM
        import claim_gate
        iid = ORDER['instrument_id']
        held_text = self.text.read_bytes().decode('utf-8')
        ref = dict(json.loads(self.fragment.read_text())['data'], instrument_id=iid,
                   char_start=0, char_end=len(held_text), quote=held_text, page_or_item='fixture')
        prior = tracker.W.matching_confirmation(ref, self.root)
        self.assertIsNotNone(prior)

        def sources(value):
            if isinstance(value, dict):
                return {k: (copy.deepcopy(ref) if k in ('original_representation', 'original_source', 'source')
                            else sources(v)) for k, v in value.items()}
            return [sources(v) for v in value] if isinstance(value, list) else value

        claim = sources(copy.deepcopy(COMPLETE_NO_CLAIM))
        claim['instrument_id'] = iid
        claim['operative_clauses'][0]['original_operative_text'] = held_text
        claim['working_text'] = tracker.W.blank([ref], prior)
        self.assertEqual(claim_gate.validate_claim(claim, expected_status='no'), [])
        path = self.root / 'research/readiness/claims/filed.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(claim) + '\n', encoding='utf-8')
        receipt = self.root / tracker.J['checker']
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({'by_instrument': {iid: {
            'claim_sha256': claim_gate.claim_sha(claim),
            'steps_checker_passed': {step: True for step in tracker.STEP_NAMES}}}}), encoding='utf-8')
        row = tracker.build(str(self.root))[0][0]
        write_csv(self.root / L.TRACKER_CSV, [row])
        self.assertEqual(row['ready_for_human_review'], 'yes', row)
        self.assertEqual(row['step_original_text'], 'done')
        self.assertEqual(row['text_evidence_tier'], 'transcription_dependent')
        self.assertEqual(row['provisional_text_method'], '')

    def test_repeat_revalidates_confirmation_pinned_by_filed_claim(self):
        self.first_pass()
        self.file_dependent_claim()
        before = (self.output / 'CONFIRMATIONS.jsonl').read_bytes()
        self.assertEqual(L.run(self.root, self.output)['confirmed'], 1)
        self.assertEqual((self.output / 'CONFIRMATIONS.jsonl').read_bytes(), before)
        row = tracker.build(str(self.root))[0][0]
        self.assertEqual(row['ready_for_human_review'], 'yes')
        self.assertEqual(row['working_text_policy_errors'], '')

    def test_filed_claim_confirmation_is_not_carried_after_changed_bytes(self):
        self.first_pass()
        self.file_dependent_claim()
        self.text.write_text('Changed after filing', encoding='utf-8')
        result = L.run(self.root, self.output)
        self.assertEqual(result['assessed'], 1)
        self.assertEqual(result['confirmed'], 0)
        row = tracker.build(str(self.root))[0][0]
        self.assertEqual(row['ready_for_human_review'], 'no')
        self.assertIn('working_text:prior_confirmation_stale', row['working_text_policy_errors'])

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
