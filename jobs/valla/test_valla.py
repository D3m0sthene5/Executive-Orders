"""Fail-closed lineage, false grouping and explicit component-review boundaries."""
import copy
import json
from pathlib import Path
import tempfile
import subprocess
from unittest import mock
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

    def test_all_premise_families_have_positive_and_unmatched_controls(self):
        patterns=json.loads((V.HERE/'premises.json').read_bytes())['patterns']
        examples={'performance_irrelevant_until_revocation':"No clause's first end needs a report date.",
                  'deadline_as_completion':'The report was completed on the deadline.',
                  'silence_as_continuation':'No later revocation was found, so it continues in effect.',
                  'automatic_duty_succession':'The successor automatically inherited all duties.'}
        for expected,text in examples.items():
            with self.subTest(expected=expected):
                self.assertIn(expected,{m['pattern_id'] for m in V.spans(text,patterns)})
        self.assertFalse(V.spans('A receipt records delivery on June 1. The transfer instrument preserves only the named records.',patterns))

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

    def test_zero_or_boolean_reviewed_claim_line_is_not_a_version_reference(self):
        for line in (0,True,-1):
            self.a['reviewed_claim_ref']['line']=line;self.commit_review()
            self.assertFalse(self.valid()['valid'])

    def test_boolean_method_cannot_count_as_an_explicit_method_attestation(self):
        self.a['method']=True;self.commit_review()
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

    def test_tracked_package_discovery_excludes_runtime_and_reports_sparse_gaps(self):
        subprocess.run(['git','init','-q'],cwd=self.repo,check=True)
        p=self.repo/'research/excavator/real';p.mkdir(parents=True)
        V.dump(p/'RATIONALES.json',{'x':'A shared premise.'})
        (p/'decisions.csv').write_text('instrument_id,research_rationale\nEO:1,@rationale:x\n')
        runtime=self.repo/'research/valla/pilot-runtime/test';runtime.mkdir(parents=True)
        V.dump(runtime/'RATIONALES.json',{'x':'Runtime must not feed itself.'})
        subprocess.run(['git','add','.'],cwd=self.repo,check=True)
        loaded,missing=V.package_paths(self.repo)
        self.assertEqual(loaded,[p]);self.assertFalse(missing)
        self.assertEqual(V.build(self.repo)['summary']['shared_rationale_references'],1)
        (p/'RATIONALES.json').unlink()
        loaded,missing=V.package_paths(self.repo)
        self.assertFalse(loaded);self.assertEqual(len(missing),1)

    def test_empty_or_stale_method_review_cannot_invalidate(self):
        p = self.repo / 'research/readiness/method_reviews'; p.mkdir()
        (p / 'bad.jsonl').write_text(V.canon({'schema': 'eo-method-dependency-review/v1', 'independent': True, 'verdict': 'revalidate'}) + '\n')
        d = V.build(self.repo); self.assertEqual(d['summary']['examined_dependencies'], 0)
        self.assertEqual(len(d['refused_method_reviews']), 1)

    def method_review(self, record_id='M1', iid='EO:1', write=True):
        text=self.claim['research_rationale']
        f={'schema':'eo-method-dependency-review/v1','record_id':record_id,'instrument_id':iid,
           'claim_sha256':V.sha(self.claim),'independent':True,'verdict':'revalidate',
           'review_kind':'independent_ai_method_review','reviewed_on':'2026-10-20',
           'producer':'original-producer','reviewer':'separate-reviewer',
           'rationale_pointer':'/research_rationale','char_start':0,'char_end':len(text),
           'span_sha256':V.sha(text),'conclusion_pointers':['/operative_clauses/0/first_end'],
           'dependencies':self.a['dependencies']}
        for key in ('applicability','earlier_ending','scope','independent_commands','savings','unresolved_question','analysis'):
            f[key]='This case-specific question remains for independently reviewed correction.'
        p=self.repo/('research/reviews/method-%s.jsonl'%record_id);p.write_text(V.canon(f)+'\n')
        f['review_ref']={'path':p.relative_to(self.repo).as_posix(),'file_sha256':V.file_sha(p),'record_id':record_id}
        if write:
            target=self.repo/'research/readiness/method_reviews';target.mkdir(exist_ok=True)
            (target/('%s.jsonl'%record_id)).write_text(V.canon(f)+'\n')
        return f

    def test_reviewed_dependency_targets_only_conclusions_and_preserves_quote(self):
        self.method_review()
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


    # ---- request-scoped packet context (attach) ----
    IDS = ['EO:1']

    def git_init(self):
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)

    def package(self, name, iids, base='research/excavator', track=True):
        p = self.repo / base / name; p.mkdir(parents=True, exist_ok=True)
        V.dump(p / 'RATIONALES.json', {'k': 'Shared %s.' % name})
        (p / 'decisions.csv').write_text('instrument_id,research_rationale\n' + ''.join('%s,@rationale:k\n' % i for i in iids))
        if track:
            subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        return p

    def ctx(self, ids=None, **kw):
        return V.canon(V.attach(self.repo, ids or self.IDS, **kw))

    def add_claim(self, iid, name='other.jsonl', **extra):
        p = self.repo / 'research/readiness/claims' / name
        with p.open('a') as f:
            f.write(V.canon({'schema': 'eo-lifecycle-claim/v1', 'instrument_id': iid, **extra}) + '\n')

    def test_unrelated_tracked_packages_do_not_change_context(self):
        self.git_init(); base = self.ctx()
        self.package('other', ['EO:2']); self.package('near', ['EO:10', 'EO:11'])
        self.assertEqual(self.ctx(), base)
        for n in range(101):
            self.package('bulk%03d' % n, ['EO:%d' % (500 + n)], track=False)
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        self.assertEqual(self.ctx(), base)
        scan = V.attach(self.repo, self.IDS)['package_scan']
        self.assertEqual(scan, {'scope': 'requested_instruments', 'relevant_packages': [], 'excluded_folders': [],
                                'unmaterialized_packages': [], 'causal_derivation_inferred': False})

    def test_own_packet_folder_excluded_only_when_passed(self):
        self.git_init(); folder = self.repo / 'research/excavator/packet'
        base = self.ctx(exclude=[folder])
        self.package('packet', ['EO:1'])
        self.assertEqual(self.ctx(exclude=[folder]), base)
        self.assertEqual(self.ctx(exclude=['research/excavator/packet/']), base)
        self.assertNotEqual(self.ctx(), base)
        self.assertNotEqual(V.attach(self.repo, self.IDS)['claims'], V.attach(self.repo, self.IDS, exclude=[folder])['claims'])
        self.assertEqual(V.attach(self.repo, self.IDS, exclude=[folder])['package_scan']['excluded_folders'],
                         ['research/excavator/packet'])
        # Exclusion is recorded even when the folder neither exists nor is tracked; nested packages are skipped too.
        self.assertEqual(V.attach(self.repo, self.IDS, exclude=['nowhere/x'])['package_scan']['excluded_folders'], ['nowhere/x'])
        self.package('packet/sub', ['EO:1'])
        self.assertEqual(self.ctx(exclude=[folder]), base)

    def test_relevant_package_add_edit_delete_change_context(self):
        self.git_init(); base = self.ctx()
        p = self.package('rel', ['EO:1']); added = self.ctx(); self.assertNotEqual(added, base)
        self.assertEqual(V.attach(self.repo, self.IDS)['package_scan']['relevant_packages'],
                         ['research/excavator/rel/RATIONALES.json'])
        ref = V.attach(self.repo, self.IDS)['claims']['EO:1']['shared_rationale_references'][0]
        self.assertEqual(ref['resolved_text'], 'Shared rel.')
        V.dump(p / 'RATIONALES.json', {'k': 'Edited.'}); edited = self.ctx(); self.assertNotEqual(edited, added)
        (p / 'decisions.csv').write_text('instrument_id,research_rationale\nEO:1,@rationale:k\nEO:1,@rationale:k\n')
        self.assertNotEqual(self.ctx(), edited)
        (p / 'RATIONALES.json').unlink()
        self.assertNotEqual(self.ctx(), edited)
        self.assertEqual(V.attach(self.repo, self.IDS)['package_scan']['unmaterialized_packages'],
                         ['research/excavator/rel/RATIONALES.json'])
        subprocess.run(['git', 'rm', '-q', '-f', '--cached', '-r', 'research/excavator/rel'], cwd=self.repo, check=True)
        self.assertEqual(self.ctx(), base)

    def test_more_than_bound_of_relevant_packages_refused(self):
        self.git_init()
        for n in range(V.MAX_PACKAGES_PER_QUERY + 1):
            self.package('rel%03d' % n, ['EO:1'], track=False)
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        with self.assertRaises(ValueError):
            V.attach(self.repo, self.IDS)
        subprocess.run(['git', 'rm', '-q', '-f', '--cached', '-r', 'research/excavator/rel100'], cwd=self.repo, check=True)
        self.assertEqual(len(V.attach(self.repo, self.IDS)['package_scan']['relevant_packages']), V.MAX_PACKAGES_PER_QUERY)

    def test_scan_bytes_bound_refused(self):
        self.git_init(); self.package('other', ['EO:2'])
        with mock.patch.object(V, 'MAX_SCAN_BYTES', 10), self.assertRaises(ValueError):
            V.attach(self.repo, self.IDS)

    def test_canonical_claim_changes_only_for_requested_ids(self):
        self.git_init(); base = self.ctx()
        self.add_claim('EO:9', research_rationale='Unrelated.'); self.assertEqual(self.ctx(), base)
        (self.repo / 'research/readiness/claims/bad.jsonl').write_text('{"schema":"x","instrument_id":"EO:8","synthetic":true}\n')
        self.assertEqual(self.ctx(), base)
        with self.assertRaises(ValueError):
            V.build(self.repo)
        self.add_claim('EO:1', name='zzz.jsonl', research_rationale='A new winner.')
        changed = V.attach(self.repo, self.IDS)
        self.assertNotEqual(V.canon(changed), base)
        self.assertEqual(changed['claims']['EO:1']['claim_ref']['path'], 'research/readiness/claims/zzz.jsonl')
        self.assertEqual(changed['claims']['EO:1']['claim_ref']['line'], 1)

    def test_scoped_claim_refs_match_full_build(self):
        self.add_claim('EO:2', name='aaa.jsonl'); self.add_claim('EO:1', name='zzz.jsonl', research_rationale='Later.')
        (self.repo / 'research/readiness/claims/zzz.jsonl').write_text(
            '\n' + V.canon({'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:2'}) + '\n'
            + V.canon({'schema': 'eo-lifecycle-claim/v1', 'instrument_id': 'EO:1', 'research_rationale': 'Later.'}) + '\n')
        full, _ = V.active_claims(self.repo); scoped, history = V.active_claims(self.repo, frozenset(['EO:1']))
        self.assertEqual(scoped['EO:1']['ref'], full['EO:1']['ref']); self.assertEqual(scoped['EO:1']['ref']['line'], 3)
        self.assertEqual(set(scoped), {'EO:1'})

    def test_attestation_and_method_review_for_requested_id_change_context(self):
        self.git_init(); base = self.ctx()
        self.method_review('M1', 'EO:1'); with_review = self.ctx(); self.assertNotEqual(with_review, base)
        self.assertEqual(V.attach(self.repo, self.IDS)['claims']['EO:1']['invalidated_conclusion_pointers'].count('/whole_order_end'), 1)
        target = self.repo / 'research/readiness/component_attestations'; target.mkdir()
        (target / 'one.jsonl').write_text(V.canon(self.a) + '\n')
        self.assertNotEqual(self.ctx(), with_review)

    def test_invalid_method_review_for_unrelated_id_is_ignored_when_scoped(self):
        self.git_init(); self.add_claim('EO:2'); base = self.ctx()
        p = self.repo / 'research/readiness/method_reviews'; p.mkdir()
        (p / 'bad.jsonl').write_text(V.canon({'schema': 'eo-method-dependency-review/v1', 'instrument_id': 'EO:2',
                                              'independent': True, 'verdict': 'revalidate'}) + '\n')
        self.assertEqual(self.ctx(), base)
        d = V.build(self.repo, ids=self.IDS); self.assertEqual(d['refused_method_reviews'], [])
        self.assertEqual(len(V.build(self.repo)['refused_method_reviews']), 1)
        self.assertEqual(len(V.build(self.repo, ids=['EO:2'])['refused_method_reviews']), 1)

    def test_protocol_premise_and_code_pins_change_context(self):
        self.git_init(); base = self.ctx()
        self.rule.write_text('changed protocol'); changed = self.ctx(); self.assertNotEqual(changed, base)
        self.assertEqual(V.attach(self.repo, self.IDS)['protocol_pins']['jobs/claim-kit/BATCH.md'], V.file_sha(self.rule))
        stage = self.repo / 'valla-copy'; stage.mkdir()
        for name in ('premises.json', 'valla.py'):
            (stage / name).write_bytes((V.HERE / name).read_bytes())
        with mock.patch.object(V, 'HERE', stage):
            same = self.ctx()
            (stage / 'premises.json').write_text((stage / 'premises.json').read_text() + '\n')
            self.assertNotEqual(self.ctx(), same)
            same = self.ctx(); (stage / 'valla.py').write_text((stage / 'valla.py').read_text() + '\n#\n')
            self.assertNotEqual(self.ctx(), same)

    def test_full_build_reports_all_packages_and_keeps_bound(self):
        self.git_init(); self.package('a', ['EO:1']); self.package('b', ['EO:2'])
        d = V.build(self.repo); scan = d['package_scan']
        self.assertEqual((scan['scope'], scan['tracked_packages_loaded']), ('full_index', 2))
        self.assertEqual(d['summary']['shared_rationale_references'], 2)
        with mock.patch.object(V, 'MAX_INDEX_PACKAGES', 1), self.assertRaises(ValueError):
            V.build(self.repo)
        # The per-query path is not limited by the index bound.
        with mock.patch.object(V, 'MAX_INDEX_PACKAGES', 1):
            self.assertEqual(len(V.attach(self.repo, self.IDS)['package_scan']['relevant_packages']), 1)
        self.assertEqual(V.build(self.repo, exclude=[self.repo / 'research/excavator/a'])['package_scan']['tracked_packages_loaded'], 1)


if __name__ == '__main__':
    unittest.main()
