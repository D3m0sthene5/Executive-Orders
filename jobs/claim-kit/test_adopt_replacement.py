"""Novellae: owner-adopted replacement proposals filed as claims of record, and every refusal."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import adopt_replacement as A
import batch
import completion

DECISION = 'D-20990101-adopt'
RULING = 'research/readiness/owner_rulings/2099-01-01-adopt.md'
FOLDER = 'research/excavator/w/c/complete-v1'
PROPOSAL = 'research/excavator/w/c/REPLACEMENT_PROPOSAL.jsonl'
OLD = 'research/readiness/claims/justinian-2099-r3.jsonl'
TARGET = 'research/readiness/claims/novellae-2099-adopt.jsonl'
RECEIPT = 'research/excavator/w/REPLACEMENT_ADOPTION.json'
GATE = '''def validate_claim(claim, expected_status=None):
    return ['gate_bad'] if claim.get('bad') else []
'''


def line(record):
    return (json.dumps(record, sort_keys=True) + '\n').encode()


class AdoptReplacementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve()
        self.new = [{'instrument_id': 'EO:5', 'whole_order_status': 'no', 'v': 2},
                    {'instrument_id': 'EO:7', 'whole_order_status': 'no', 'v': 2}]
        self.write(OLD, line({'instrument_id': 'EO:5', 'whole_order_status': 'no', 'v': 1}) +
                   line({'instrument_id': 'EO:7', 'whole_order_status': 'no', 'v': 1}) +
                   line({'instrument_id': 'EO:9', 'whole_order_status': 'yes', 'v': 1}))
        self.write('research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv',
                   b'instrument_id,provisional_substantive_status\nEO:5,no\nEO:7,no\nEO:9,yes\n')
        self.write('research/stage19/code/claim_gate.py', GATE.encode())
        self.write(A.DECISIONS, line({'id': DECISION, 'rev': 0, 'date': '2099-01-01', 'ruling': 'adopt'}))
        self.write(A.ASKS, line({'id': 'A-1', 'rev': 0, 'status': 'open', 'question': 'Adopt EO 5 and 7?'}) +
                   line({'id': 'A-1', 'rev': 1, 'status': 'answered', 'decision': DECISION, 'question': 'Adopt EO 5 and 7?'}))
        self.write(RULING, ('Owner: yes. ' + DECISION + '\n').encode())
        self.publish()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, raw):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def publish(self, claims=None, publication=None, tally=None, pins=None):
        claims = self.new if claims is None else claims
        raw = b''.join(line(c) for c in claims)
        self.write(PROPOSAL, raw)
        self.write(FOLDER + '/PUBLICATION.json', json.dumps(dict(
            {'mode': 'replacement_proposal', 'owner_acceptance_required': True, 'written': True,
             'independent_human_certifications': 0, 'path': PROPOSAL, 'sha256': hashlib.sha256(raw).hexdigest()},
            **(publication or {}))).encode())
        outcomes = [{'instrument_id': c['instrument_id'], 'outcome': 'eligible', 'claim_sha256': completion.claim_sha(c),
                     'publication_kind': 'whole_case', 'source_review_upheld': True} for c in claims]
        self.write(FOLDER + '/TALLY.json', json.dumps(dict(
            {'plants_placed': 1, 'plants_caught': 1, 'controls': [{'instrument_id': 'EO:1', 'caught': True}],
             'independent_human_certifications': 0, 'eligible': [c['instrument_id'] for c in claims], 'outcomes': outcomes},
            **(tally or {}))).encode())
        old = hashlib.sha256((self.repo / OLD).read_bytes()).hexdigest()
        self.write(FOLDER + '/INPUTS.json', json.dumps({'dependency_sha256': {OLD: old} if pins is None else pins}).encode())

    def run_adopt(self, write=True, target=TARGET):
        return A.adopt(self.repo, DECISION, RULING, [FOLDER], target, RECEIPT, write)

    def refuses(self, message, **kwargs):
        before = sorted(p.name for p in (self.repo / A.CLAIMS_DIR).iterdir())
        with self.assertRaisesRegex(ValueError, message):
            self.run_adopt(**kwargs)
        self.assertEqual(sorted(p.name for p in (self.repo / A.CLAIMS_DIR).iterdir()), before)
        self.assertFalse((self.repo / RECEIPT).exists())

    def test_dry_run_writes_nothing(self):
        receipt = self.run_adopt(write=False)
        self.assertFalse(receipt['written'])
        self.assertEqual([c['instrument_id'] for c in receipt['claims']], ['EO:5', 'EO:7'])
        self.assertFalse((self.repo / TARGET).exists())
        self.assertFalse((self.repo / RECEIPT).exists())

    def test_write_files_byte_identical_and_becomes_claim_of_record(self):
        old_bytes = (self.repo / OLD).read_bytes()
        receipt = self.run_adopt()
        self.assertEqual((self.repo / TARGET).read_bytes(), (self.repo / PROPOSAL).read_bytes())
        self.assertEqual((self.repo / OLD).read_bytes(), old_bytes)  # replaced file untouched
        owners = batch.owners(self.repo)
        self.assertEqual(owners['EO:5']['path'], TARGET)
        self.assertEqual(owners['EO:7']['line'], 2)
        self.assertEqual(owners['EO:9']['path'], OLD)  # orders outside the adoption keep their claim
        stored = json.loads((self.repo / RECEIPT).read_text())
        self.assertEqual(stored, receipt)
        self.assertEqual((stored['decision'], stored['asks'], stored['independent_human_certifications']), (DECISION, ['A-1'], 0))
        self.assertEqual(stored['claims'][0]['replaces']['path'], OLD)
        with self.assertRaisesRegex(ValueError, 'receipt already exists'):
            self.run_adopt()
        (self.repo / RECEIPT).unlink()
        with self.assertRaisesRegex(ValueError, 'target already exists'):
            self.run_adopt()
        self.assertEqual((self.repo / TARGET).read_bytes(), (self.repo / PROPOSAL).read_bytes())

    def test_filename_sort_rule(self):
        self.refuses('shadowed by an existing claim filename', target='research/readiness/claims/claude-2099-adopt.jsonl')

    def test_target_must_be_canonical_top_level(self):
        self.refuses('target must be', target='research/excavator/w/elsewhere.jsonl')

    def test_needs_kean_decision_and_answered_ask(self):
        self.write(A.DECISIONS, b'')
        self.refuses('Kean decision not found')

    def test_needs_ask_answered(self):
        self.write(A.ASKS, line({'id': 'A-1', 'rev': 0, 'status': 'open', 'decision': DECISION, 'question': 'EO 5 and 7?'}))
        self.refuses('no answered Kean ask')

    def test_order_must_be_named_in_ask(self):
        self.write(A.ASKS, line({'id': 'A-1', 'rev': 0, 'status': 'answered', 'decision': DECISION, 'question': 'Adopt EO 5?'}))
        self.refuses('not named in the owner-answered ask: EO:7')

    def test_ruling_must_name_decision(self):
        self.write(RULING, b'Owner: yes.\n')
        self.refuses('does not name')

    def test_proposal_bytes_must_match_publication(self):
        self.write(PROPOSAL, (self.repo / PROPOSAL).read_bytes().replace(b'"v": 2', b'"v": 3', 1))
        self.refuses('differ from the published sha256')

    def test_status_overlay_refused(self):
        self.publish(publication={'status_adoption_required': ['EO:5']})
        self.refuses('status-adoption route')

    def test_uncaught_control_refused(self):
        self.publish(tally={'plants_caught': 0})
        self.refuses('planted controls')

    def test_exact_version_must_be_eligible(self):
        self.publish()
        tally = json.loads((self.repo / FOLDER / 'TALLY.json').read_text())
        tally['outcomes'][1]['source_review_upheld'] = False
        self.write(FOLDER + '/TALLY.json', json.dumps(tally).encode())
        self.refuses('eligible and upheld: EO:7')

    def test_claim_of_record_changed_since_completion(self):
        self.write(OLD, (self.repo / OLD).read_bytes() + line({'instrument_id': 'EO:5', 'whole_order_status': 'no', 'v': 9}))
        self.refuses('changed since the completion pinned it')

    def test_newer_shadowing_file_refused(self):
        self.write('research/readiness/claims/zeno-2099.jsonl', line({'instrument_id': 'EO:5', 'whole_order_status': 'no', 'v': 8}))
        self.refuses('shadowed by an existing claim filename')

    def test_no_claim_of_record_is_not_a_replacement(self):
        self.publish(claims=self.new + [{'instrument_id': 'EO:11', 'whole_order_status': 'no'}])
        self.write(A.ASKS, line({'id': 'A-1', 'rev': 0, 'status': 'answered', 'decision': DECISION, 'question': 'EO 5, 7, 11'}))
        self.refuses('no claim of record to replace')

    def test_status_contest_refused(self):
        self.publish(claims=[self.new[0], dict(self.new[1], whole_order_status='yes')])
        self.refuses('contests the ledger')

    def test_gate_errors_refused(self):
        self.publish(claims=[self.new[0], dict(self.new[1], bad=True)])
        self.refuses('Stage 19 gate errors for EO:7')

    def test_source_audit_hold_refused(self):
        self.write(A.HOLDS, line({'instrument_id': 'EO:5', 'claim_sha256': completion.claim_sha(self.new[0]), 'state': 'unresolved'}))
        self.refuses('source-audit hold')

    def test_cli_reports_refusal(self):
        code = A.main(['--repo', str(self.repo), '--decision', 'D-none', '--ruling', RULING, '--completion', FOLDER,
                       '--target', TARGET, '--receipt', RECEIPT])
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()
