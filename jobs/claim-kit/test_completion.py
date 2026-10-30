"""Exact reviewed versions, control judgments, holds, bytes, and replay routing."""
from copy import deepcopy
import json
import sys
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import batch
import completion as C
import test_batch as B


class CompletionTests(B.BatchTests):
    def setup_completion(self):
        self.folder = self.packet(('EO:1',))
        self.fill(self.folder)
        batch.apply(self.repo, self.folder, self.folder / 'applied')
        self.claim = json.loads((self.folder / 'applied/CLAIMS.proposed.jsonl').read_bytes())
        # Deliberately noncanonical spaces and CRLF: preserving producer bytes
        # is distinct from comparing Stage19's semantic claim hash.
        self.producer = self.folder / 'PRODUCER.jsonl'
        self.producer.write_bytes((json.dumps(self.claim, ensure_ascii=False, separators=(', ', ': ')) + '\r\n').encode())
        self.review = {'instrument_id': 'EO:1', 'claim_sha256': C.claim_sha(self.claim),
                       'reviewer': 'reviewer', 'model_family': 'OpenAI', 'independent': True,
                       'separate_context': True, 'review_kind': 'independent_ai_source_review',
                       'scope': 'whole_case', 'verdict': 'upheld'}
        self.review_path = self.folder / 'REVIEW.json'
        batch.dump(self.review_path, self.review)
        self.manifest = {'schema': C.SCHEMA, 'agent': 'producer', 'producer_model_family': 'OpenAI',
                         'independence_requirement': 'same_family_separate_context', 'controls': [],
                         'members': [{'instrument_id': 'EO:1', 'claim_sha256': C.claim_sha(self.claim),
                                      'outcome': 'submit', 'claim': self.ref(self.producer, line=1),
                                      'publication_kind': 'whole_case', 'review': self.ref(self.review_path),
                                      'packet': self.ref(self.folder / 'PACKET.json')}],
                         'publication': {'mode': 'own_claims', 'path': 'research/readiness/claims/producer-2026-10-24.jsonl'}}
        self.manifest_path = self.folder / 'COMPLETION.json'
        self.dest = self.folder / 'complete'
        self.add_control(after=False, iid='EO:2')
        self.manifest['members'].append({'instrument_id': 'EO:2', 'outcome': 'blocked', 'reason': 'Synthetic control-only member.'})

    def ref(self, path, **selector):
        return {'path': path.relative_to(self.repo).as_posix(), 'sha256': batch.file_sha(path), **selector}

    def checker(self, repo, claims, dest):
        dest.mkdir()
        rows = [{'instrument_id': c['instrument_id'], 'claim_sha256': C.claim_sha(c),
                 'mechanical_result': 'pass', 'all_checks_passed': not C._gate(repo).validate_claim(c),
                 'gate_errors': C._gate(repo).validate_claim(c)}
                for c in map(json.loads, claims.read_bytes().splitlines())]
        doc = {'claims': rows, 'by_instrument': {c['instrument_id']: c for c in rows}}
        batch.dump(dest / 'PER_CLAIM.json', doc)
        return doc

    def run_completion(self, publish=False):
        batch.dump(self.manifest_path, self.manifest)
        with patch.object(C, 'run_checker', side_effect=self.checker), patch.object(C, 'run_tracker', return_value={'actual_fixture': True}):
            return C.complete(self.repo, self.manifest_path, self.dest, publish)

    def add_control(self, caught=True, after=True, iid='EO:1', review_scope=None):
        planted = deepcopy(self.claim)
        planted['instrument_id'] = iid
        planted['research_rationale'] += ' Seeded defect for this fixture.'
        plant_path = self.folder / 'PLANT.jsonl'
        plant_path.write_bytes((json.dumps(planted) + '\n').encode())
        plant_review = dict(self.review, instrument_id=iid, claim_sha256=C.claim_sha(planted), verdict='rejected',
                            rationale='No keyword matching can establish whether this names the defect.')
        if review_scope is not None:
            plant_review['scope'] = review_scope
        review_path = self.folder / 'PLANT_REVIEW.json'
        batch.dump(review_path, plant_review)
        adjudication = {'instrument_id': iid, 'planted_claim_sha256': C.claim_sha(planted),
                        'review': self.ref(review_path), 'adjudicator': 'semantic-reviewer',
                        'caught': caught, 'scoring': 'strict', 'rationale': 'Explicit semantic adjudication.'}
        adjudication_path = self.folder / 'CONTROL_ADJUDICATION.json'
        batch.dump(adjudication_path, adjudication)
        seed_path = self.folder / 'SEED_RECEIPT.json'
        batch.dump(seed_path, {'schema': 'eo-claim-kit-control-seed/v1', 'instrument_id': iid,
                              'planted_claim_sha256': C.claim_sha(planted), 'genuine_claim_sha256': C.claim_sha(self.claim),
                              'seeded_by': 'planter'})
        self.manifest['controls'] = [{'instrument_id': iid, 'planted_claim_sha256': C.claim_sha(planted),
                                     'seed': self.ref(seed_path), 'review': self.ref(review_path),
                                     'adjudication': self.ref(adjudication_path)}]
        if after:
            path = self.folder / 'AFTER_REVEAL.json'
            batch.dump(path, dict(self.review, verdict='upheld_after_reveal'))
            self.manifest['members'][0]['after_reveal_review'] = self.ref(path)

    def test_exact_producer_bytes_and_all_consumed_receipts_preserved(self):
        self.setup_completion()
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], ['EO:1'])
        target = self.repo / self.manifest['publication']['path']
        self.assertEqual(target.read_bytes(), self.producer.read_bytes())
        self.assertEqual((self.dest / 'CLAIMS.publishable.jsonl').read_bytes(), self.producer.read_bytes())
        saved = self.dest / 'receipts' / self.review_path.relative_to(self.repo)
        self.assertEqual(saved.read_bytes(), self.review_path.read_bytes())
        self.assertFalse((self.dest / 'receipts' / (self.folder / 'PLANT.jsonl').relative_to(self.repo)).exists())
        self.assertEqual(result['independent_human_certifications'], 0)
        self.assertIsNone(result['model_tokens'])
        with self.assertRaisesRegex(ValueError, 'fresh research'):
            C.complete(self.repo, self.manifest_path, self.dest)

    def test_stale_exact_review_is_exception_and_no_publication(self):
        self.setup_completion()
        batch.dump(self.review_path, dict(self.review, claim_sha256='0' * 64))
        self.manifest['members'][0]['review'] = self.ref(self.review_path)
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], [])
        self.assertIn('selected exact', result['outcomes'][0]['error'])
        self.assertFalse((self.repo / self.manifest['publication']['path']).exists())

    def test_changed_file_does_not_silently_select_a_new_version(self):
        self.setup_completion()
        self.producer.write_bytes(self.producer.read_bytes() + self.producer.read_bytes())
        result = self.run_completion()
        self.assertIn('changed input', result['outcomes'][0]['error'])
        self.assertEqual(result['eligible'], [])

    def test_conflicting_selected_versions_are_refused(self):
        self.setup_completion()
        self.manifest['members'].append(dict(self.manifest['members'][0], claim_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'conflicting or duplicate'):
            self.run_completion()

    def test_exact_hold_blocks_but_a_different_held_version_does_not(self):
        self.setup_completion()
        path = self.repo / 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        hold = {'schema': 'eo-source-audit-hold/v1', 'state': 'unresolved', 'instrument_id': 'EO:1',
                'claim_sha256': C.claim_sha(self.claim), 'reason': 'Exact source audit conflict',
                'review_path': self.review_path.relative_to(self.repo).as_posix(),
                'review_sha256': batch.file_sha(self.review_path)}
        path.write_text(json.dumps(hold) + '\n')
        # Avoid refreshing the packet: holds are independently checked first.
        result = self.run_completion()
        self.assertIn('exact version has unresolved', result['outcomes'][0]['error'])
        hold['claim_sha256'] = '0' * 64
        path.write_text(json.dumps(hold) + '\n')
        self.assertNotIn(('EO:1', C.claim_sha(self.claim)), C.held_versions(C.Inputs(self.repo)))
        self.assertEqual(path.read_text(), json.dumps(hold) + '\n')

    def test_control_adjudication_not_reason_keywords_and_after_reveal_exact(self):
        self.setup_completion()
        self.add_control()
        result = self.run_completion()
        self.assertEqual(result['plants_caught'], 1)
        self.assertEqual(result['eligible'], ['EO:1'])
        self.assertTrue(result['outcomes'][0]['after_reveal'])

    def control_scope_refused(self, scope, message):
        # Reproduction from the lifecycle-assurance handoff (PR106 f750886a): a review of the planted version
        # in another task scope must not count as catching it; exact pins alone do not bind the task.
        self.setup_completion()
        self.add_control(review_scope=scope)
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], [])
        self.assertEqual(result['plants_caught'], 0)
        errors = json.loads((self.dest / 'EXCEPTIONS.json').read_bytes())
        self.assertTrue(any(message in e['error'] for e in errors), errors)
        self.assertFalse((self.repo / self.manifest['publication']['path']).exists())

    def test_control_review_of_an_unrelated_task_does_not_count(self):
        self.control_scope_refused('status_only_unrelated_scope', 'must review the planted lifecycle claim task')

    def test_control_review_scope_must_match_the_seeded_member(self):
        self.control_scope_refused('partial_research', 'differs from the seeded member task')

    def test_control_false_stops_batch_even_with_upheld_after_reveal(self):
        self.setup_completion()
        self.add_control(caught=False)
        result = self.run_completion(publish=True)
        self.assertEqual(result['eligible'], [])
        self.assertEqual(result['plants_caught'], 0)
        self.assertFalse((self.repo / self.manifest['publication']['path']).exists())

    def test_missing_adjudication_and_missing_after_reveal_fail_closed(self):
        self.setup_completion()
        self.add_control(after=False)
        result = self.run_completion()
        self.assertEqual(result['eligible'], [])
        self.assertIn('after_reveal_review', result['outcomes'][0]['error'])
        self.dest = self.folder / 'complete2'
        self.manifest['controls'][0].pop('adjudication')
        result = self.run_completion()
        self.assertEqual(result['eligible'], [])
        self.assertEqual(result['plants_caught'], 0)

    def test_planted_exact_claim_never_filed(self):
        self.setup_completion()
        self.add_control()
        control = self.manifest['controls'][0]
        self.manifest['members'][0].update(claim=self.ref(self.folder / 'PLANT.jsonl', line=1), claim_sha256=control['planted_claim_sha256'])
        result = self.run_completion()
        self.assertIn('planted version cannot be filed', result['outcomes'][0]['error'])

    def test_cross_family_requirement_and_reviewer_identity(self):
        self.setup_completion()
        self.manifest['independence_requirement'] = 'different_family'
        result = self.run_completion()
        self.assertEqual(result['eligible'], [])
        self.dest = self.folder / 'complete2'
        self.manifest['independence_requirement'] = 'same_family_separate_context'
        batch.dump(self.review_path, dict(self.review, reviewer='producer'))
        self.manifest['members'][0]['review'] = self.ref(self.review_path)
        result = self.run_completion()
        self.assertIn('independent source review', result['outcomes'][0]['error'])

    def test_no_controls_and_family_whitespace_do_not_bypass_guard(self):
        self.setup_completion()
        controls = self.manifest['controls']
        self.manifest['controls'] = []
        with self.assertRaisesRegex(ValueError, 'nonempty planted controls'):
            self.run_completion()
        self.manifest['controls'] = controls
        self.manifest['independence_requirement'] = 'different_family'
        self.manifest['producer_model_family'] = ' OpenAI '
        result = self.run_completion()
        self.assertEqual(result['eligible'], [])

    def test_seed_pointer_cannot_copy_an_enclosing_private_key(self):
        self.setup_completion()
        path = self.folder / 'UNSAFE_KEY.json'
        seed = json.loads((self.folder / 'SEED_RECEIPT.json').read_bytes())
        batch.dump(path, {'safe': seed, 'private_mutation_key': {'field': 'sensitive seeded value'}})
        self.manifest['controls'][0]['seed'] = self.ref(path, pointer='/safe')
        result = self.run_completion()
        self.assertEqual(result['eligible'], [])
        self.assertFalse((self.dest / 'receipts' / path.relative_to(self.repo)).exists())

    def make_partial(self):
        self.claim.pop('claim_kit')
        self.claim['operative_clauses'][0]['first_end'] = None
        self.claim['whole_order_end'] = None
        self.claim['unresolved_material_gaps'] = ['Exact first cessation unresolved.']
        self.producer.write_bytes((json.dumps(self.claim) + '\n').encode())
        errors = C._gate(self.repo).validate_claim(self.claim)
        batch.dump(self.review_path, dict(self.review, claim_sha256=C.claim_sha(self.claim),
                                         scope='partial_research', expected_gate_errors=errors))
        self.manifest['members'][0].update(claim=self.ref(self.producer, line=1), claim_sha256=C.claim_sha(self.claim),
                                           publication_kind='partial_research', review=self.ref(self.review_path))
        return errors

    def test_partial_keeps_full_gate_errors_and_does_not_repair_claim(self):
        self.setup_completion()
        errors = self.make_partial()
        result = self.run_completion()
        self.assertEqual(result['eligible'], ['EO:1'])
        self.assertEqual(result['outcomes'][0]['gate_errors'], errors)
        self.assertEqual((self.dest / 'CLAIMS.publishable.jsonl').read_bytes(), self.producer.read_bytes())

    def test_partial_requires_actual_checker_errors_equal_exact_review(self):
        self.setup_completion()
        self.make_partial()
        batch.dump(self.manifest_path, self.manifest)
        def mismatch(repo, claims, dest):
            result = self.checker(repo, claims, dest)
            result['claims'][0]['gate_errors'].append('whole_order_status_mismatch')
            return result
        with patch.object(C, 'run_checker', side_effect=mismatch), patch.object(C, 'run_tracker', return_value={}):
            result = C.complete(self.repo, self.manifest_path, self.dest, True)
        self.assertEqual(result['eligible'], [])
        self.assertEqual(result['outcomes'][0]['outcome'], 'rejected_mechanical')

    def test_partial_cannot_supply_ready_credit_through_exhaustion(self):
        self.setup_completion()
        self.make_partial()
        batch.dump(self.manifest_path, self.manifest)
        ready = {'selected': {'EO:1': {'after': {'ready_for_human_review': 'yes', 'ready_tier': 'machine_exhausted'}}}}
        with patch.object(C, 'run_checker', side_effect=self.checker), patch.object(C, 'run_tracker', return_value=ready):
            result = C.complete(self.repo, self.manifest_path, self.dest, True)
        self.assertEqual(result['eligible'], [])
        self.assertIn('whole_case review required', result['outcomes'][0]['error'])

    def test_complete_claim_cannot_use_partial_scope_without_explicit_gaps(self):
        self.setup_completion()
        batch.dump(self.review_path, dict(self.review, scope='partial_research'))
        self.manifest['members'][0].update(publication_kind='partial_research', review=self.ref(self.review_path))
        result = self.run_completion()
        self.assertIn('explicit nonempty expected_gate_errors', result['outcomes'][0]['error'])

    def test_new_canonical_claim_for_selected_id_or_hold_during_replay_stops_filing(self):
        for kind in ('claim', 'hold'):
            with self.subTest(kind=kind):
                if not hasattr(self, 'folder'):
                    self.setup_completion()
                self.dest = self.folder / ('complete-' + kind)
                batch.dump(self.manifest_path, self.manifest)
                path = self.repo / ('research/readiness/claims/other-new.jsonl' if kind == 'claim' else 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl')
                def changed(repo, claims, dest):
                    result = self.checker(repo, claims, dest)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('{"instrument_id": "EO:1"}\n' if kind == 'claim' else '{}\n')
                    return result
                with patch.object(C, 'run_checker', side_effect=changed), patch.object(C, 'run_tracker', return_value={}):
                    result = C.complete(self.repo, self.manifest_path, self.dest, True)
                self.assertEqual(result['eligible'], [])
                self.assertFalse((self.repo / self.manifest['publication']['path']).exists())
                path.unlink()

    def test_checker_failure_preserves_proposal_and_exception(self):
        self.setup_completion()
        batch.dump(self.manifest_path, self.manifest)
        with patch.object(C, 'run_checker', side_effect=ValueError('actual checker failed')), patch.object(C, 'run_tracker'):
            result = C.complete(self.repo, self.manifest_path, self.dest)
        self.assertEqual(result['eligible'], [])
        self.assertEqual((self.dest / 'CLAIMS.selected.jsonl').read_bytes(), self.producer.read_bytes())
        self.assertTrue((self.dest / 'EXCEPTIONS.json').exists())

    def test_changed_receipt_during_checker_cannot_publish(self):
        self.setup_completion()
        batch.dump(self.manifest_path, self.manifest)
        def changed(repo, claims, dest):
            result = self.checker(repo, claims, dest)
            self.review_path.write_text('{}')
            return result
        with patch.object(C, 'run_checker', side_effect=changed), patch.object(C, 'run_tracker', return_value={}):
            result = C.complete(self.repo, self.manifest_path, self.dest, True)
        self.assertEqual(result['eligible'], [])
        saved = self.dest / 'receipts' / self.review_path.relative_to(self.repo)
        self.assertEqual(json.loads(saved.read_bytes()), self.review)

    # ---- packet snapshot reuse, publication transaction, concurrent disjoint filings ----
    def setup_two(self):
        """EO:1 and EO:2 are both selectable from ONE packet; EO:3 is the planted control identity."""
        self.folder = self.packet(('EO:1', 'EO:2'))
        for iid in ('EO:1', 'EO:2'):
            self.fill(self.folder, iid)
        batch.apply(self.repo, self.folder, self.folder / 'applied')
        claims = {c['instrument_id']: c for c in map(json.loads, (self.folder / 'applied/CLAIMS.proposed.jsonl').read_bytes().splitlines())}
        self.assertEqual(sorted(claims), ['EO:1', 'EO:2'])
        self.claim = claims['EO:1']
        self.producer = self.folder / 'PRODUCER.jsonl'
        self.producer.write_bytes(b''.join((json.dumps(claims[i], ensure_ascii=False) + '\n').encode() for i in ('EO:1', 'EO:2')))
        self.review = {'instrument_id': 'EO:1', 'claim_sha256': C.claim_sha(self.claim), 'reviewer': 'reviewer',
                       'model_family': 'OpenAI', 'independent': True, 'separate_context': True,
                       'review_kind': 'independent_ai_source_review', 'scope': 'whole_case', 'verdict': 'upheld'}
        members = []
        for line, iid in enumerate(('EO:1', 'EO:2'), 1):
            review_path = self.folder / ('REVIEW-%d.json' % line)
            batch.dump(review_path, dict(self.review, instrument_id=iid, claim_sha256=C.claim_sha(claims[iid])))
            members.append({'instrument_id': iid, 'claim_sha256': C.claim_sha(claims[iid]), 'outcome': 'submit',
                            'claim': self.ref(self.producer, line=line), 'publication_kind': 'whole_case',
                            'review': self.ref(review_path), 'packet': self.ref(self.folder / 'PACKET.json')})
        self.manifest = {'schema': C.SCHEMA, 'agent': 'producer', 'producer_model_family': 'OpenAI',
                         'independence_requirement': 'same_family_separate_context', 'controls': [], 'members': members,
                         'publication': {'mode': 'own_claims', 'path': 'research/readiness/claims/producer-2026-10-24.jsonl'}}
        self.manifest_path = self.folder / 'COMPLETION.json'
        self.dest = self.folder / 'complete'
        self.add_control(after=False, iid='EO:3')
        self.manifest['members'].append({'instrument_id': 'EO:3', 'outcome': 'blocked', 'reason': 'Synthetic control-only member.'})
        self.target = self.repo / self.manifest['publication']['path']
        self.lock = self.repo / C.LOCK_REL
        self.target.parent.mkdir(parents=True, exist_ok=True)

    def complete_with(self, checker=None, publish=True):
        batch.dump(self.manifest_path, self.manifest)
        with patch.object(C, 'run_checker', side_effect=checker or self.checker), patch.object(C, 'run_tracker', return_value={}):
            return C.complete(self.repo, self.manifest_path, self.dest, publish)

    def after_checker(self, action):
        def run(repo, claims, dest):
            result = self.checker(repo, claims, dest)
            action()
            return result
        return run

    def batch_error(self, result):
        return [e['error'] for e in json.loads((self.dest / 'EXCEPTIONS.json').read_bytes()) if e.get('scope') == 'batch']

    def disjoint_file(self, name='other-agent-2026-10-24.jsonl', iid='EO:99'):
        path = self.repo / 'research/readiness/claims' / name
        return path, (json.dumps({'instrument_id': iid}) + '\n')

    def test_one_packet_load_for_many_members_plus_one_recheck(self):
        self.setup_two()
        calls = []
        real = batch.load_packet
        def counting(*args, **kwargs):
            calls.append(args[0])
            return real(*args, **kwargs)
        with patch.object(batch, 'load_packet', side_effect=counting):
            result = self.complete_with()
        self.assertEqual(result['eligible'], ['EO:1', 'EO:2'])
        self.assertEqual(len(calls), 2, 'one verification during selection plus one before publication')
        self.assertEqual(self.target.read_bytes(), self.producer.read_bytes())
        receipt = json.loads((self.dest / 'PACKETS.json').read_bytes())
        self.assertEqual(len(receipt), 1)
        self.assertEqual((receipt[0]['loads'], receipt[0]['rechecks']), (2, 1))
        self.assertGreaterEqual(receipt[0]['load_seconds'], 0)
        self.assertEqual(receipt[0]['packet_sha256'], self.manifest['members'][0]['packet']['sha256'])
        self.assertIn('preserved_receipts', json.loads((self.dest / 'INPUTS.json').read_bytes()))

    def test_failed_packet_verification_is_not_repeated_for_every_member(self):
        self.setup_two()
        calls = []
        def failing(*args, **kwargs):
            calls.append(args[0])
            raise ValueError('changed prior research; prepare a new version')
        with patch.object(batch, 'load_packet', side_effect=failing):
            result = self.complete_with()
        self.assertEqual(result['eligible'], [])
        self.assertEqual(len(calls), 1, 'one failed verification, raised again for the second member')
        errors = [e['error'] for e in json.loads((self.dest / 'EXCEPTIONS.json').read_bytes()) if e.get('instrument_id')]
        self.assertEqual(errors, ['changed prior research; prepare a new version'] * 2)
        self.assertFalse(self.target.exists())
        receipt = json.loads((self.dest / 'PACKETS.json').read_bytes())
        self.assertEqual((receipt[0]['loads'], receipt[0]['rechecks']), (1, 0))
        self.assertIn('changed prior research', receipt[0]['verification_error'])

    def test_cached_packet_dossier_is_not_mutated_by_member_checks(self):
        self.setup_two()
        cached = []
        real_packet = C.Inputs.packet
        def spy(inputs, ref):
            packet, dossiers = real_packet(inputs, ref)
            if not cached:
                cached.extend([dossiers, deepcopy(dossiers)])
            return packet, dossiers
        real = C.check_claim
        def mutating(claim, repo, dossier):
            errors = real(claim, repo, dossier)
            dossier['evidence'] = {}
            dossier['mutated'] = True
            return errors
        with patch.object(C.Inputs, 'packet', spy), patch.object(C, 'check_claim', side_effect=mutating):
            result = self.complete_with(publish=False)
        self.assertEqual(result['eligible'], ['EO:1', 'EO:2'])
        self.assertEqual(cached[0], cached[1])

    def test_held_source_changed_after_selection_blocks_publication(self):
        self.setup_two()
        packet, _ = batch.load_packet(self.folder, self.repo)
        rel = next(iter(packet['held_text_file_pins']))
        original = (self.repo / rel).read_bytes()
        result = self.complete_with(self.after_checker(lambda: (self.repo / rel).write_bytes(original + b' changed')))
        self.assertEqual(result['eligible'], [])
        self.assertTrue(any('packet dependencies changed during completion' in e for e in self.batch_error(result)))
        self.assertFalse(self.target.exists())
        self.assertFalse(self.lock.exists())

    def test_disjoint_claims_file_during_run_publishes_and_is_receipted(self):
        self.setup_two()
        path, text = self.disjoint_file()
        result = self.complete_with(self.after_checker(lambda: path.write_text(text)))
        self.assertEqual(result['eligible'], ['EO:1', 'EO:2'])
        self.assertEqual(self.target.read_bytes(), self.producer.read_bytes())
        row = {'path': path.relative_to(self.repo).as_posix(), 'sha256': batch.digest(text.encode()), 'instrument_ids': ['EO:99']}
        self.assertEqual(result['concurrent_disjoint_claim_files'], [row])
        inputs = json.loads((self.dest / 'INPUTS.json').read_bytes())
        self.assertEqual(inputs['concurrent_disjoint_claim_files'], [row])
        self.assertIn('excluded from the union', inputs['tracker_replay_basis'])
        self.assertFalse(self.lock.exists())

    def test_new_claims_file_for_selected_id_or_unparseable_blocks_publication(self):
        for name, text, message in (('other.jsonl', json.dumps({'instrument_id': 'EO:2'}) + '\n',
                                     'concurrent publication for selected instrument EO:2: research/readiness/claims/other.jsonl'),
                                    ('bad.jsonl', '{"instrument_id": "EO:99"}\nnot json\n', 'Expecting value'),
                                    ('list.jsonl', '[1]\n', 'non-object')):
            with self.subTest(name=name):
                if hasattr(self, 'folder'):
                    self.dest = self.folder / ('complete-' + name)
                else:
                    self.setup_two()
                path = self.repo / 'research/readiness/claims' / name
                result = self.complete_with(self.after_checker(lambda: path.write_text(text)))
                self.assertEqual(result['eligible'], [])
                self.assertTrue(any(message in e for e in self.batch_error(result)), self.batch_error(result))
                self.assertFalse(self.target.exists())
                self.assertFalse(self.lock.exists())
                path.unlink()

    def test_preexisting_claims_file_modified_or_deleted_blocks_publication(self):
        self.setup_two()
        existing = self.repo / 'research/readiness/claims/old-agent-2026-01-01.jsonl'
        existing.parent.mkdir(parents=True, exist_ok=True)
        original = json.dumps({'instrument_id': 'EO:99'}) + '\n'
        for kind in ('modified', 'deleted'):
            with self.subTest(kind=kind):
                existing.write_text(original)
                self.dest = self.folder / ('complete-' + kind)
                action = (lambda: existing.write_text(original + original)) if kind == 'modified' else existing.unlink
                result = self.complete_with(self.after_checker(action))
                self.assertEqual(result['eligible'], [])
                self.assertTrue(any('old-agent-2026-01-01.jsonl' in e for e in self.batch_error(result)), self.batch_error(result))
                self.assertFalse(self.target.exists())
                self.assertFalse(self.lock.exists())

    def test_publication_lock_held_by_another_fails_closed_and_is_never_removed(self):
        self.setup_two()
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        self.lock.write_text('{"pid": 1}')
        with patch.dict(os.environ, {C.LOCK_TIMEOUT_ENV: '0.2'}):
            result = self.complete_with()
        self.assertEqual(result['eligible'], [])
        self.assertTrue(any(C.LOCK_REL in e for e in self.batch_error(result)), self.batch_error(result))
        self.assertFalse(self.target.exists())
        self.assertEqual(self.lock.read_text(), '{"pid": 1}')
        # Without publication no lock is needed: the same rechecks run lock-free.
        self.dest = self.folder / 'complete-nopublish'
        result = self.complete_with(publish=False)
        self.assertEqual(result['eligible'], ['EO:1', 'EO:2'])
        self.assertFalse(self.target.exists())

    def test_dead_holder_on_this_host_is_removed_and_receipted(self):
        import socket, subprocess
        self.setup_two()
        dead = subprocess.Popen([sys.executable, '-c', 'pass']); dead.wait()
        holder = {'pid': dead.pid, 'host': socket.gethostname(), 'started_utc': 'x', 'dest': 'crashed'}
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        self.lock.write_text(json.dumps(holder))
        with patch.dict(os.environ, {C.LOCK_TIMEOUT_ENV: '0.2'}):
            result = self.complete_with()
        if os.name == 'posix':
            self.assertEqual(result['eligible'], ['EO:1', 'EO:2'])
            self.assertEqual(result['stale_publication_locks_removed'], [holder])
            self.assertFalse(self.lock.exists())
        else:
            self.assertEqual(result['eligible'], [])

    def test_dead_holder_is_not_removed_while_another_waiter_breaks_it(self):
        import socket, subprocess
        self.setup_two()
        dead = subprocess.Popen([sys.executable, '-c', 'pass']); dead.wait()
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        self.lock.write_text(json.dumps({'pid': dead.pid, 'host': socket.gethostname(), 'started_utc': 'x', 'dest': 'crashed'}))
        breaker = self.lock.with_name(self.lock.name + '.break'); breaker.write_text('')  # another waiter is removing it
        with patch.dict(os.environ, {C.LOCK_TIMEOUT_ENV: '0.2'}):
            result = self.complete_with()
        self.assertEqual(result['eligible'], [])  # waits and fails closed instead of racing the other waiter
        self.assertTrue(self.lock.exists()); self.assertTrue(breaker.exists())
        self.assertFalse(self.target.exists())

    def test_lock_lives_in_git_common_dir_when_available(self):
        import subprocess
        self.assertEqual(C.lock_path(self.repo), self.repo / C.LOCK_REL)
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)
        self.assertEqual(C.lock_path(self.repo), (self.repo / '.git').resolve() / 'claim-kit-publication.lock')

    def test_lock_is_released_after_success(self):
        self.setup_two()
        result = self.complete_with()
        self.assertEqual(result['eligible'], ['EO:1', 'EO:2'])
        self.assertFalse(self.lock.exists())

    def test_lock_holds_during_checks_records_holder_and_is_released_after_conflicting_target(self):
        self.setup_two()
        seen = {}
        real = C.Inputs.unchanged
        def racing(inputs, selected_ids=None):
            seen.update(json.loads(self.lock.read_text()))
            real(inputs, selected_ids)
            self.target.write_text('raced')  # appears after the pin checks, before the exclusive create
        with patch.object(C.Inputs, 'unchanged', racing):
            result = self.complete_with()
        self.assertEqual(result['eligible'], [])
        self.assertTrue(any('publication target appeared' in e for e in self.batch_error(result)), self.batch_error(result))
        self.assertFalse(self.lock.exists())
        self.assertEqual(self.target.read_text(), 'raced')
        self.assertEqual(set(seen), {'pid', 'host', 'started_utc', 'dest'})
        self.assertEqual((seen['pid'], seen['dest']), (os.getpid(), str(self.dest.resolve())))

    def test_two_sequential_completions_for_disjoint_ids_both_publish(self):
        self.setup_two()
        self.manifest['members'][1] = {'instrument_id': 'EO:2', 'outcome': 'blocked', 'reason': 'Left for the second run.'}
        first = self.complete_with()
        self.assertEqual(first['eligible'], ['EO:1'])
        # A second packet for EO:2 only (a packet's own prior-research scope sees its mates' filings).
        folder = self.repo / 'research/experiment/packet2'
        batch.prepare(self.repo, self.out, folder, ['EO:2'], 'producer')
        self.fill(folder, 'EO:2')
        batch.apply(self.repo, folder, folder / 'applied')
        line = (folder / 'applied/CLAIMS.proposed.jsonl').read_bytes()
        claim = json.loads(line)
        producer = folder / 'PRODUCER.jsonl'
        producer.write_bytes(line)
        review = folder / 'REVIEW.json'
        batch.dump(review, dict(self.review, instrument_id='EO:2', claim_sha256=C.claim_sha(claim)))
        self.manifest['members'][1] = {'instrument_id': 'EO:2', 'claim_sha256': C.claim_sha(claim), 'outcome': 'submit',
                                       'claim': self.ref(producer, line=1), 'publication_kind': 'whole_case',
                                       'review': self.ref(review), 'packet': self.ref(folder / 'PACKET.json')}
        self.manifest['members'][0] = {'instrument_id': 'EO:1', 'outcome': 'blocked', 'reason': 'Already filed.'}
        self.manifest['publication']['path'] = 'research/readiness/claims/producer-2026-10-26.jsonl'
        self.dest = folder / 'complete'
        second = self.complete_with()
        self.assertEqual(second['eligible'], ['EO:2'], second['outcomes'])
        self.assertEqual(len(list((self.repo / 'research/readiness/claims').glob('producer-*.jsonl'))), 2)
        self.assertFalse(self.lock.exists())


# Reuse the corpus fixture and packet helpers, not their tests.
for base in (B.BatchTests, B.T.BuildIntegrationTests):
    for name in vars(base):
        if name.startswith('test_') and name not in CompletionTests.__dict__:
            setattr(CompletionTests, name, None)
del base

class PublicationAuditTests(unittest.TestCase):
    """Separate clones bypass the lock; the merge-time audit must see what Git merges silently."""
    def setUp(self):
        import subprocess, tempfile
        self.temp = tempfile.TemporaryDirectory(); self.repo = Path(self.temp.name)
        self.git = lambda *a: subprocess.run(['git', *a], cwd=self.repo, check=True, capture_output=True)
        self.git('init', '-q', '-b', 'main'); self.git('config', 'user.email', 't@t'); self.git('config', 'user.name', 't')
        self.claims = self.repo / 'research/readiness/claims'; self.claims.mkdir(parents=True)
        (self.claims / 'old-2026-01-01.jsonl').write_text(json.dumps({'instrument_id': 'EO:1'}) + '\n')
        self.git('add', '-A'); self.git('commit', '-qm', 'base')

    def tearDown(self):
        self.temp.cleanup()

    def publish(self, branch, name, *iids):
        self.git('checkout', '-qb', branch, 'main')
        (self.claims / name).write_text(''.join(json.dumps({'instrument_id': i, 'v': branch}) + '\n' for i in iids))
        self.git('add', '-A'); self.git('commit', '-qm', branch)

    def test_competing_publications_from_separate_clones_are_reported(self):
        self.publish('clone-a', 'a-2026-10-29.jsonl', 'EO:2', 'EO:3')
        self.publish('clone-b', 'b-2026-10-29.jsonl', 'EO:3')
        self.git('checkout', '-q', 'clone-a'); self.git('merge', '-q', '--no-edit', 'clone-b')  # Git merges silently
        result = C.publication_audit(self.repo, 'main')
        self.assertFalse(result['ok'])
        self.assertEqual(sorted(w['path'] for w in result['duplicate_instruments']['EO:3']),
                         ['research/readiness/claims/a-2026-10-29.jsonl', 'research/readiness/claims/b-2026-10-29.jsonl'])

    def test_race_where_one_publication_landed_first_is_reported_both_ways(self):
        self.publish('clone-a', 'a-2026-10-29.jsonl', 'EO:3')
        self.publish('clone-b', 'b-2026-10-29.jsonl', 'EO:3')
        self.git('checkout', '-q', 'main'); self.git('merge', '-q', '--no-edit', 'clone-a')  # A lands first
        self.git('checkout', '-q', 'clone-b')
        before = C.publication_audit(self.repo, 'main')  # B's pull request against main
        self.assertFalse(before['ok']); self.assertEqual({w['side'] for w in before['duplicate_instruments']['EO:3']}, {'left', 'right'})
        self.git('checkout', '-q', 'main'); self.git('merge', '-q', '--no-edit', 'clone-b')  # merged silently
        after = C.publication_audit(self.repo, merge_commit='HEAD')
        self.assertFalse(after['ok']); self.assertIn('EO:3', after['duplicate_instruments'])

    def test_disjoint_publications_pass_and_other_changes_fail(self):
        self.publish('clone-a', 'a-2026-10-29.jsonl', 'EO:2')
        self.publish('clone-b', 'b-2026-10-29.jsonl', 'EO:3')
        self.git('checkout', '-q', 'main'); self.git('merge', '-q', '--no-edit', 'clone-a')
        self.git('checkout', '-q', 'clone-b')
        self.assertTrue(C.publication_audit(self.repo, 'main')['ok'])
        nested = self.claims / 'archive'; nested.mkdir()
        (nested / 'copy.jsonl').write_text(json.dumps({'instrument_id': 'EO:3'}) + '\n')  # not a canonical file
        self.git('add', '-A'); self.git('commit', '-qm', 'nested copy')
        self.assertTrue(C.publication_audit(self.repo, 'main')['ok'])
        cases = {'edited': lambda: (self.claims / 'old-2026-01-01.jsonl').write_text(json.dumps({'instrument_id': 'EO:1', 'x': 1}) + '\n'),
                 'deleted': lambda: (self.claims / 'old-2026-01-01.jsonl').unlink(),
                 'malformed': lambda: (self.claims / 'c-2026-10-29.jsonl').write_text('[1]\n{"no_id": true}\n')}
        for name, change in cases.items():
            with self.subTest(change=name):
                self.git('checkout', '-q', '-B', 'case-' + name, 'clone-b'); change()
                self.git('add', '-A'); self.git('commit', '-qm', name)
                result = C.publication_audit(self.repo, 'main')
                self.assertFalse(result['ok']); self.assertTrue(result['problems'])


if __name__ == '__main__':
    unittest.main()
