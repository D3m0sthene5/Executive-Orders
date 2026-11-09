"""Gutenberg (2026-11-09): the owner's skipped-witness switch. Default keeps today's rule; "flag" tolerates only
skipped witnesses added with a known reason, and raises a recheck flag for each."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import working_text as W

GPO = {'grade': 'official_printing', 'text_path': 'jobs/photius-gpo-volumes/output/texts/EO_7.txt',
       'why': 'grade_not_in_working_text_policy'}


class SwitchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        tp = self.repo / 'jobs/source/output/order.txt'
        tp.parent.mkdir(parents=True)
        tp.write_text('Executive Order 7\nThe Board shall report.\n', encoding='utf-8', newline='\n')
        sha = hashlib.sha256(tp.read_bytes()).hexdigest()
        self.record = {'schema': W.CONFIRMATION_SCHEMA, 'method': 'machine', 'instrument_id': 'EO:7',
                       'grade': 'mirror_transcription', 'sha256': 'a' * 64, 'text_sha256': sha,
                       'text_path': 'jobs/source/output/order.txt', 'acceptable_as_original': False,
                       'confirmed': True, 'identity_confirmed': True, 'complete_text_confirmed': True,
                       'requires_page_check': False, 'pages_confirmed': None,
                       'evidence': {'identity_route': 'r', 'skipped_witnesses': []}}
        frag = {'kind': 'original_representation', 'instrument_id': 'EO:7',
                'data': {'grade': 'mirror_transcription', 'acceptable_as_original': False, 'sha256': 'a' * 64,
                         'text_sha256': sha, 'text_path': 'jobs/source/output/order.txt'}}
        (self.repo / 'jobs/source/output/FRAGMENTS.jsonl').write_text(json.dumps(frag) + '\n')
        self.machine = self.repo / W.CONFIRMATION_PATHS[0]
        self.machine.parent.mkdir(parents=True)
        self.machine.write_text(json.dumps(self.record) + '\n')
        prior = W.matching_confirmation(self.record, self.repo, index=W.Index(self.repo))
        text = tp.read_text()
        ref = dict(self.record, char_start=0, char_end=len(text), quote=text)
        for k in ('schema', 'method', 'confirmed', 'identity_confirmed', 'complete_text_confirmed',
                  'requires_page_check', 'pages_confirmed', 'evidence'):
            ref.pop(k)
        self.claim = {'instrument_id': 'EO:7', 'original_representation': ref, 'working_text': W.blank([ref], prior)}
        self.prior = prior

    def switch(self, mode):
        p = self.repo / W.SWITCHES_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({'skipped_witness_addition': mode}))

    def relachmann(self, **evidence):
        rec = deepcopy(self.record)
        rec['evidence'].update(evidence)
        self.machine.write_text(json.dumps(rec) + '\n')

    def policy(self):
        flags = []
        errors, _ = W.policy(self.claim, self.repo, W.Index(self.repo), flags)
        return errors, flags

    def test_unchanged_passes_in_both_modes(self):
        for mode in ('void', 'flag'):
            self.switch(mode)
            self.assertEqual(self.policy(), ([], []))

    def test_default_and_garbage_switch_keep_todays_rule(self):
        self.relachmann(skipped_witnesses=[GPO])
        self.assertIn('working_text:prior_confirmation_stale', self.policy()[0])  # no switch file
        for bad in ('flagged', None, 1):
            self.switch(bad)
            self.assertEqual(W.skipped_witness_mode(self.repo), 'void')
            self.assertIn('working_text:prior_confirmation_stale', self.policy()[0])
        (self.repo / W.SWITCHES_PATH).write_text('{not json')
        self.assertEqual(W.skipped_witness_mode(self.repo), 'void')

    def test_flag_tolerates_an_added_skipped_witness_and_flags_it(self):
        """The Photius case: 193 ready orders voided by one added GPO printing, verdict unchanged."""
        self.switch('flag')
        self.relachmann(skipped_witnesses=[GPO])
        errors, flags = self.policy()
        self.assertEqual(errors, [])
        self.assertEqual(flags, ['working_text:skipped_witness_added_recheck:official_printing:'
                                 'grade_not_in_working_text_policy'])
        # the dossier path agrees with the claim path
        dossier = {'instrument_id': 'EO:7', 'working_text_confirmation': self.prior, 'original_source_id': 's',
                   'evidence': {'s': {'source': self.claim['original_representation']}}}
        self.assertEqual(len(W.require_current_confirmation(dossier, self.repo, index=W.Index(self.repo))), 1)

    def test_flag_still_voids_every_other_difference(self):
        self.switch('flag')
        cases = [
            {'skipped_witnesses': [GPO], 'identity_route': 'other'},                 # added witness plus a real change
            {'skipped_witnesses': [dict(GPO, why='contradicts_chosen_text')]},       # unknown reason
            {'identity_route': 'other'},                                             # no witness added
        ]
        for ev in cases:
            self.relachmann(**ev)
            self.assertIn('working_text:prior_confirmation_stale', self.policy()[0], ev)
        # a prior skipped witness removed or edited
        self.record['evidence']['skipped_witnesses'] = [GPO]
        self.machine.write_text(json.dumps(self.record) + '\n')
        prior = W.matching_confirmation(self.record, self.repo, index=W.Index(self.repo))
        self.claim['working_text'] = W.blank([self.claim['original_representation']], prior)
        self.assertEqual(self.policy(), ([], []))
        for ev in ({'skipped_witnesses': []}, {'skipped_witnesses': [dict(GPO, grade='archival_replica_checked')]}):
            self.relachmann(**ev)
            self.assertIn('working_text:prior_confirmation_stale', self.policy()[0], ev)
        # a confirmed field that changes
        self.record['confirmed'] = False
        self.machine.write_text(json.dumps(dict(self.record, evidence={'identity_route': 'r',
                                                                         'skipped_witnesses': [GPO, GPO]})) + '\n')
        self.assertIn('working_text:prior_confirmation_stale', self.policy()[0])

    def test_drift_function_directly(self):
        cur = deepcopy(self.prior)
        cur['record']['evidence']['skipped_witnesses'] = [GPO]
        self.assertEqual(W.confirmation_drift(self.prior, cur, 'void'), ('stale', []))
        self.assertEqual(W.confirmation_drift(self.prior, cur, 'flag'), ('flag', [GPO]))
        cur['fragments'] = []
        self.assertEqual(W.confirmation_drift(self.prior, cur, 'flag')[0], 'stale')
        self.assertEqual(W.confirmation_drift(self.prior, None, 'flag')[0], 'stale')

    def test_committed_switch_matches_the_owner_decision(self):
        """Owner 2026-11-09 (A-20261109-skipped-witness): flag. A flag without the ruling file would be unauthorised."""
        here = Path(__file__).resolve().parents[2]
        self.assertEqual(W.skipped_witness_mode(here), 'flag')
        self.assertTrue((here / 'research/readiness/owner_rulings/2026-11-09-skipped-witness-flag.md').is_file())


if __name__ == '__main__':
    unittest.main()
