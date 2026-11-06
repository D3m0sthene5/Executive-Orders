"""Held excerpts reach undecided dossiers only through their frozen status-overlay evidence.

The supplement adds citable held evidence; it never sets a status, grade or review, and the
status-overlay gates (ending basis, current predicate, acceptable original, independent review)
apply unchanged to the supplemented evidence.
"""
from copy import deepcopy
import json
import shutil
import unittest
from unittest.mock import patch

import batch as B
import source_supplement as S
import status_overlay as O
import test_status_overlay as TSO


class UndecidedSupplementTests(unittest.TestCase):
    def setUp(self):
        self.fixture = TSO.OverlayTests('test_blank_decision_and_review_cannot_promote')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo, self.out = self.fixture.repo, self.fixture.out
        self.parent = self.repo / 'research/excavator/gratian/parent'
        B.prepare(self.repo, self.out, self.parent, ['EO:1'], 'synthetic-producer')
        code = self.repo / 'jobs/claim-kit/source_supplement.py'
        code.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(S.__file__, code)
        patcher = patch.object(S, '__file__', str(code))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.packet, self.dossiers = B.load_packet(self.parent, self.repo)
        base = self.dossiers['EO:1']
        actor = base['evidence'][self.fixture.ending]
        src = {k: actor['source'][k] for k in ['url', 'sha256', 'text_path', 'text_sha256', 'page_or_item']}
        src['local_path'] = src['text_path']
        self.entry = {'alias': 'acting-text', 'instrument_ids': ['EO:1'], 'actor_id': 'EO:5',
                      'reason': 'Producer must examine this exact held acting text.', 'source': src,
                      'char_start': actor['char_start'], 'char_end': actor['char_end']}
        self.decl = self.repo / 'research/excavator/gratian/sources.json'
        self.decl.write_text(json.dumps({'schema': S.SCHEMA, 'sources': [self.entry]}))
        self.dest = self.repo / 'research/excavator/gratian/supplemented'

    def prepare(self):
        return S.prepare(self.repo, self.parent, self.decl, 'synthetic-producer', self.dest)

    def frozen(self, folder):
        packet, dossiers = B.load_packet(folder, self.repo)
        entry = packet['undecided_evidence']['EO:1']
        return packet, dossiers, json.loads((self.repo / entry['path']).read_bytes()), entry

    def test_undecided_member_keeps_overlay_route_with_supplemented_evidence(self):
        receipt = self.prepare()
        self.assertEqual(receipt['undecided_overlay_members'], ['EO:1'])
        self.assertFalse(receipt['producer_approval'])
        packet, dossiers, evidence, entry = self.frozen(self.dest)
        d = dossiers['EO:1']
        self.assertIsNone(d['whole_order_status'])
        self.assertIn('SUPPLEMENT:acting-text', d['evidence'])
        self.assertEqual(d['evidence']['SUPPLEMENT:acting-text']['role'], 'unreviewed_source_excerpt')
        self.assertEqual(evidence['base_dossier'], d)
        self.assertEqual(evidence['source_supplement']['parent_evidence_sha256'],
                         self.packet['undecided_evidence']['EO:1']['evidence_sha256'])
        parent = json.loads((self.repo / self.packet['undecided_evidence']['EO:1']['path']).read_bytes())
        for key in ('authority', 'history_packet', 'history_sha256', 'compiled', 'legal_cutoff'):
            self.assertEqual(evidence[key], parent[key])
        self.assertTrue(O.validate_evidence(self.repo, evidence))
        decision = json.loads((self.repo / entry['status_decision']).read_bytes())
        self.assertEqual(decision['evidence_sha256'], evidence['fingerprint'])
        self.assertFalse(decision['approved'])
        self.assertIsNone(decision['recommended_provisional_status'])
        self.assertEqual(S.verify(self.repo, self.dest)['legal_approval'], False)

    def reviewed(self, evidence, basis):
        decision = O.extend_decision(evidence['history_packet'], evidence, 'synthetic-producer')
        decision.update(approved=True, identity_confirmed=True, basis_review_confirmed=True,
                        earlier_endings_checked=True, partial_scope_checked=True, savings_checked=True,
                        recommended_provisional_status='no', material_gaps=[],
                        observations_reviewed=['OBS:synthetic-1'], basis_evidence_ids=basis,
                        rationale='The synthetic original and exact acting provision were read; this fixture expressly ends every continuing duty.')
        review = O.blank_review(decision, evidence, 'synthetic-independent-reviewer')
        review.update(independence_confirmed=True, source_checks_confirmed=True, decision='accept',
                      checked_evidence_ids=basis + [evidence['base_dossier']['original_source_id']],
                      rationale='The independent synthetic review checked the frozen original and exact acting passage, including scope and earlier endings.')
        return decision, review

    def test_supplement_is_citable_but_cannot_replace_the_ending_basis(self):
        self.prepare()
        _, _, evidence, _ = self.frozen(self.dest)
        decision, review = self.reviewed(evidence, ['SUPPLEMENT:acting-text'])
        with self.assertRaisesRegex(ValueError, 'snapshot_only_or_missing_ending_basis'):
            O.propose(self.repo, decision, review, evidence)
        decision, review = self.reviewed(evidence, [self.fixture.ending, 'SUPPLEMENT:acting-text'])
        proposal = O.propose(self.repo, decision, review, evidence)
        self.assertFalse(proposal['owner_acceptance']['accepted'])
        self.assertFalse(proposal['canonical_status_written'])

    def test_review_must_check_the_supplement_it_relies_on(self):
        self.prepare()
        _, _, evidence, _ = self.frozen(self.dest)
        decision, review = self.reviewed(evidence, [self.fixture.ending, 'SUPPLEMENT:acting-text'])
        review['checked_evidence_ids'] = [self.fixture.ending, evidence['base_dossier']['original_source_id']]
        with self.assertRaisesRegex(ValueError, 'review_must_check_original_and_selected_basis'):
            O.propose(self.repo, decision, review, evidence)

    def test_tampered_supplemented_evidence_is_rejected(self):
        self.prepare()
        packet, _, evidence, entry = self.frozen(self.dest)
        evidence['base_dossier']['evidence']['SUPPLEMENT:acting-text']['text'] += ' invented'
        evidence['base_dossier']['fingerprint'] = O.canonical_sha(
            {k: v for k, v in evidence['base_dossier'].items() if k != 'fingerprint'})
        O._seal(evidence)
        path = self.repo / entry['path']
        path.write_text(json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        with self.assertRaises(ValueError):
            B.load_packet(self.dest, self.repo)

    def test_evidence_not_descended_from_parent_is_rejected(self):
        parent = json.loads((self.repo / self.packet['undecided_evidence']['EO:1']['path']).read_bytes())
        dossier = deepcopy(self.dossiers['EO:1'])
        dossier['source_supplement'] = {'parent_dossier_sha256': '0' * 64, 'added_evidence_ids': []}
        with self.assertRaisesRegex(ValueError, 'does not descend'):
            S.supplemented_evidence(self.repo, parent, dossier)

    def test_undecided_without_frozen_parent_evidence_is_still_refused(self):
        provenance = {'parent_packet': {}, 'declarations': {}, 'preparation_code': {}}
        with self.assertRaisesRegex(ValueError, 'existing status-overlay route'):
            S.derive(self.repo, self.dossiers, {'schema': S.SCHEMA, 'sources': [self.entry]}, provenance)

    def test_changed_parent_evidence_invalidates_supplement(self):
        self.prepare()
        path = self.repo / self.packet['undecided_evidence']['EO:1']['path']
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            B.load_packet(self.dest, self.repo)


if __name__ == '__main__':
    unittest.main()
