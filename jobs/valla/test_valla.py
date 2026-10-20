"""Fail-closed lineage, false grouping and explicit component-review boundaries."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import valla as V


class VallaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.repo = Path(self.temp.name)
        self.src = self.repo / 'jobs/fr-originals/data/text.txt'; self.src.parent.mkdir(parents=True)
        self.src.write_text('A quoted command, with a deadline.\nAnother continuing duty.')
        (self.repo / 'research/readiness/claims').mkdir(parents=True)
        (self.repo / 'research/reviews').mkdir(parents=True)
        self.rule = self.repo / 'jobs/claim-kit/BATCH.md'; self.rule.parent.mkdir(parents=True)
        self.rule.write_text('Deadline is not performance. Separate whole-case review remains necessary.')
        self.source = {'text_path': self.src.relative_to(self.repo).as_posix(), 'text_sha256': V.file_sha(self.src),
                       'char_start': 0, 'char_end': 34, 'sha256': 'a' * 64,
                       'url': 'https://example.gov/order', 'page_or_item': '1'}
        self.claim = {'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:1',
                      'claim_kit': {'agent': 'original-producer'}, 'original_representation': self.source,
                      'operative_clauses': [{'scope_id': 'EO:1#a', 'original_operative_text': self.src.read_text()[:34],
                        'original_source': self.source, 'first_end': {'date': '2001-01-01'}, 'state_at_cutoff': 'terminated', 'later_events': []}],
                      'research_rationale': 'Every clause remains part of the order until revoked.',
                      'whole_order_end': {'date': '2001-01-01'}, 'savings_residuals': {}}
        self.path = self.repo / 'research/readiness/claims/one.jsonl'; self.path.write_text(V.canon(self.claim) + '\n')
        self.a = {'schema': 'eo-component-attestation/v1', 'attestation_id': 'Q1', 'instrument_id': 'EO:1',
                  'component_selector': {'kind': 'exact_quotation', 'scope_id': 'EO:1#a'},
                  'component_sha256': V.sha(V.component(self.claim, {'kind': 'exact_quotation', 'scope_id': 'EO:1#a'})),
                  'producer': 'original-producer', 'reviewer': 'independent-reviewer', 'independent': True,
                  'review_kind': 'independent_ai_component', 'verdict': 'upheld', 'method': 'exact-held-text-span-v1',
                  'reviewed_claim_sha256': V.sha(self.claim), 'reviewed_claim_ref': {'path': self.path.relative_to(self.repo).as_posix(), 'line': 1},
                  'reviewed_on': '2026-10-20', 'dependencies': [
                      {'kind': 'file', 'key': self.source['text_path'], 'sha256': V.file_sha(self.src)},
                      {'kind': 'rule', 'key': 'jobs/claim-kit/BATCH.md', 'sha256': V.file_sha(self.rule)}]}
        self.commit_review()

    def tearDown(self):
        self.temp.cleanup()

    def commit_review(self, updates=None):
        record = {**self.a, 'schema': 'eo-component-review/v1', 'record_id': 'R1',
                  'rationale': 'I checked this specified quotation against its exact held source span. Identity and completeness are not approved.'}
        record.pop('review_ref', None)
        if updates:
            record.update(updates)
        p = self.repo / 'research/reviews/component.jsonl'; p.write_text(V.canon(record) + '\n')
        self.a['review_ref'] = {'path': p.relative_to(self.repo).as_posix(), 'file_sha256': V.file_sha(p), 'record_id': 'R1'}

    def valid(self, claim=None, invalidated=()):
        return V.validate_attestation(self.repo, self.a, claim or self.claim, invalidated)

    def test_exact_unicode_span_normalization_preserves_entity_numbers(self):
        ps = [{'id': 'x', 'expressions': ['no clause s first end needs a report date'], 'rule_refs': [], 'question': '?'}]
        text = 'Évidence: No clause’s\n first end needs a report date.'
        match = V.spans(text, ps)[0]
        self.assertEqual(match['exact_text'], text[match['char_start']:match['char_end']])
        self.assertNotEqual(V.normalize('EO 13101')[0], V.normalize('EO 13148')[0])

    def test_pattern_is_review_lead_never_confirmed_dependency(self):
        d = V.build(self.repo)
        self.assertTrue(d['review_queue']); self.assertTrue(all(not q['dependency_confirmed'] for q in d['review_queue']))
        self.assertEqual(d['claims']['EO:1']['invalidated_conclusion_pointers'], [])

    def test_match_of_quoted_source_is_not_producer_reasoning(self):
        self.claim['original_representation']['reason'] = 'Every clause remains until revoked.'
        self.path.write_text(V.canon(self.claim) + '\n')
        d = V.build(self.repo)
        self.assertFalse(any(n['pointer'].startswith('/original_representation') for n in d['claims']['EO:1']['rationales']))

    def test_false_grouping_negation_remains_lead(self):
        patterns = json.loads((V.HERE / 'premises.json').read_bytes())['patterns']
        self.assertTrue(V.spans('It is wrong to say no clause\'s first end needs a report date.', patterns))
        self.assertFalse(V.spans('The successor does not inherit duties without a transfer provision.', patterns))

    def test_whole_uphold_or_reviewer_silence_cannot_attest_field(self):
        self.commit_review({'schema': 'eo-lifecycle-review/v1', 'verdict': 'upheld'})
        self.assertFalse(self.valid()['valid'])

    def test_no_artifact_and_self_review_refused(self):
        self.a['review_ref']['file_sha256'] = '0' * 64
        self.assertFalse(self.valid()['valid'])
        self.a['reviewer'] = 'original-producer'; self.commit_review()
        self.assertFalse(self.valid()['valid'])

    def test_sound_quote_survives_ending_change_and_new_producer(self):
        changed = copy.deepcopy(self.claim); changed['operative_clauses'][0]['first_end']['date'] = '1999-01-01'
        changed['claim_kit']['agent'] = 'correction-producer'
        self.assertTrue(self.valid(changed, {'/operative_clauses/0/first_end', '/whole_order_end'})['valid'])

    def test_ending_dependency_invalidates_component_even_if_words_match(self):
        self.a['dependencies'].append({'kind': 'claim_field', 'key': '/operative_clauses/0/first_end', 'sha256': V.sha(self.claim['operative_clauses'][0]['first_end'])})
        self.commit_review()
        self.assertFalse(self.valid(invalidated={'/operative_clauses/0/first_end'})['valid'])

    def test_ancestor_dependency_invalidated_transitively(self):
        self.a['dependencies'].append({'kind': 'claim_field', 'key': '/operative_clauses', 'sha256': V.sha(self.claim['operative_clauses'])})
        self.commit_review()
        self.assertFalse(self.valid(invalidated={'/operative_clauses/0/first_end'})['valid'])
        self.assertEqual(V.closure({'a'}, [('b', 'a'), ('c', 'b'), ('b', 'c')]), {'a', 'b', 'c'})

    def test_source_method_quote_and_inventory_changes_refused(self):
        self.assertTrue(self.valid()['valid'])
        original = self.src.read_bytes(); self.src.write_text('changed')
        self.assertFalse(self.valid()['valid']); self.src.write_bytes(original)
        self.rule.write_text('changed method'); self.assertFalse(self.valid()['valid'])
        self.rule.write_text('Deadline is not performance. Separate whole-case review remains necessary.')
        c = copy.deepcopy(self.claim); c['operative_clauses'][0]['original_operative_text'] += 'changed'
        self.assertFalse(self.valid(c)['valid'])

    def test_every_source_dependency_and_exact_span_required(self):
        self.a['dependencies'] = [d for d in self.a['dependencies'] if d['kind'] != 'file']; self.commit_review()
        self.assertFalse(self.valid()['valid'])

    def test_component_cannot_salvage_legal_first_end(self):
        with self.assertRaises(ValueError):
            V.component(self.claim, {'kind': 'factual_finding', 'pointer': '/operative_clauses/0/first_end'})

    def test_changed_reviewed_claim_is_not_approved(self):
        self.path.write_text(V.canon({**self.claim, 'research_rationale': 'different frozen object'}) + '\n')
        self.assertFalse(self.valid()['valid'])

    def test_version_precedence_and_synthetic_boundary(self):
        (self.path.parent / 'zzz.jsonl').write_text(V.canon({**self.claim, 'research_rationale': 'latest'}) + '\n')
        active, hist = V.active_claims(self.repo)
        self.assertEqual(active['EO:1']['claim']['research_rationale'], 'latest'); self.assertEqual(len(hist), 2)
        self.path.write_text(V.canon({**self.claim, 'synthetic': True}) + '\n')
        with self.assertRaises(ValueError):V.active_claims(self.repo)

    def test_shared_references_are_exact_and_not_causal_inference(self):
        p = self.repo / 'research/package'; p.mkdir(); V.dump(p / 'RATIONALES.json', {'rule': 'Shared reasoning.'})
        (p / 'decisions.csv').write_text('instrument_id,research_rationale\nEO:1,@rationale:rule\n')
        rs = V.shared_lineage(self.repo, [p]); self.assertEqual(rs[0]['resolved_text'], 'Shared reasoning.')
        self.assertFalse(rs[0]['causal_derivation_established'])

    def test_empty_or_stale_method_review_cannot_invalidate(self):
        p = self.repo / 'research/readiness/method_reviews'; p.mkdir()
        (p / 'bad.jsonl').write_text(V.canon({'schema': 'eo-method-dependency-review/v1', 'independent': True, 'verdict': 'revalidate'}) + '\n')
        d = V.build(self.repo); self.assertEqual(d['summary']['examined_dependencies'], 0)
        self.assertEqual(len(d['refused_method_reviews']), 1)

    def test_reviewed_dependency_targets_only_conclusions_and_preserves_quote(self):
        text=self.claim['research_rationale']
        f={'schema':'eo-method-dependency-review/v1','record_id':'M1','instrument_id':'EO:1',
           'claim_sha256':V.sha(self.claim),'independent':True,'verdict':'revalidate',
           'review_kind':'independent_ai_method_review','reviewed_on':'2026-10-20',
           'producer':'original-producer','reviewer':'separate-reviewer',
           'rationale_pointer':'/research_rationale','char_start':0,'char_end':len(text),
           'span_sha256':V.sha(text),'conclusion_pointers':['/operative_clauses/0/first_end'],
           'dependencies':self.a['dependencies']}
        for key in ('applicability','earlier_ending','scope','independent_commands','savings','unresolved_question','analysis'):
            f[key]='This case-specific question remains for independently reviewed correction.'
        p=self.repo/'research/reviews/method.jsonl';p.write_text(V.canon(f)+'\n')
        f['review_ref']={'path':p.relative_to(self.repo).as_posix(),'file_sha256':V.file_sha(p),'record_id':'M1'}
        target=self.repo/'research/readiness/method_reviews';target.mkdir()
        (target/'one.jsonl').write_text(V.canon(f)+'\n')
        target=self.repo/'research/readiness/component_attestations';target.mkdir()
        (target/'one.jsonl').write_text(V.canon(self.a)+'\n')
        d=V.build(self.repo);c=d['claims']['EO:1']
        self.assertEqual(d['summary']['examined_dependencies'],1)
        self.assertEqual(set(c['invalidated_conclusion_pointers']),{'/whole_order_end','/operative_clauses/0/first_end'})
        self.assertTrue(c['component_reviews'][0]['valid'])
        self.path.write_text(V.canon({**self.claim,'research_rationale':'changed'})+'\n')
        self.assertEqual(V.build(self.repo)['summary']['examined_dependencies'],0)

    def test_source_identity_needs_reviewed_artifact_not_only_exact_words(self):
        self.a['component_selector']={'kind':'source_identity'}
        self.a['component_sha256']=V.sha(self.claim['original_representation']);self.commit_review()
        self.assertFalse(self.valid()['valid'])


if __name__ == '__main__':
    unittest.main()
