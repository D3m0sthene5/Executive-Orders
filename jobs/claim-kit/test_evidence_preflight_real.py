"""Frozen, source-examined R2 regressions; no scientific claims are adopted."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

import evidence_preflight as preflight

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT/'research/progress/r2-preflight-repair'


class RealEvidencePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (RESEARCH/'FREEZE.json').is_file():
            raise unittest.SkipTest('R2 frozen research cohort not hydrated')
        cls.freeze = json.loads((RESEARCH/'FREEZE.json').read_text())
        missing = [c['text_path'] for c in cls.freeze['cases'] if not (ROOT/c['text_path']).is_file()]
        if missing:
            raise unittest.SkipTest('Hydrate exact held cohort texts: '+', '.join(missing))

    def dossier(self, case):
        file = ROOT/case['frozen_dossier']
        self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), case['frozen_sha256'])
        text = ROOT/case['text_path']
        self.assertEqual(hashlib.sha256(text.read_bytes()).hexdigest(), case['text_sha256'])
        return json.loads(file.read_text())

    def test_seven_frozen_inventories_gain_no_command_or_identity_warning(self):
        for case in self.freeze['cases']:
            with self.subTest(case=case['instrument_id']):
                d = self.dossier(case)
                before = copy.deepcopy(d)
                tasks = preflight.inspect(d,ROOT)['tasks']
                self.assertFalse({'original_identity','inventory_command_coverage'} & {t['kind'] for t in tasks})
                self.assertEqual(d,before)

    def test_exact_source_bound_omission_controls_report_raw_locations(self):
        comparison = json.loads((RESEARCH/'COMPARISON.json').read_text())
        controls = [c for c in comparison['results'] if c['variant']=='disclosed_omission_control']
        self.assertEqual({c['instrument_id'] for c in controls}, {'EO:7952','EO:8123','EO:13613'})
        self.assertEqual(len(controls), 3)
        for control in comparison['results']:
            if control['variant'] != 'disclosed_omission_control':
                continue
            case = next(c for c in self.freeze['cases'] if c['instrument_id'] == control['instrument_id'])
            with self.subTest(case=case['instrument_id']):
                d = self.dossier(case)
                body = d['evidence'][d['original_source_id']]['text']
                a, b = control['omitted']['char_start'], control['omitted']['char_end']
                self.assertEqual(body[a:b],control['omitted']['text'])
                clauses = []
                for c in d['clauses']:
                    for ga, gb in ((c['char_start'],min(c['char_end'],a)),
                                   (max(c['char_start'],b),c['char_end'])):
                        if ga < gb:
                            clauses.append({'char_start':ga,'char_end':gb,'text':body[ga:gb]})
                d['clauses'] = clauses
                task = next(t for t in preflight.inspect(d,ROOT)['tasks'] if t['kind']=='inventory_command_coverage')
                self.assertEqual(task['text_sha256'],case['text_sha256'])
                self.assertEqual(task['source_sha256'],case['source_sha256'])
                self.assertTrue(task['uncovered_regions'])
                for gap in task['uncovered_regions']:
                    self.assertEqual(body[gap['char_start']:gap['char_end']],gap['text'])
                    self.assertGreater(min(gap['char_end'],b)-max(gap['char_start'],a),0)

    def test_heldout_native_declaration_gap_with_annex_limit_disclosed(self):
        manifest = RESEARCH/'ATTACHMENT_FREEZE.json'
        if not manifest.is_file():
            self.skipTest('Held-out attachment cohort not hydrated')
        case = json.loads(manifest.read_text())
        if not (ROOT/case['text_path']).is_file():
            self.skipTest('Hydrate exact EO12978 held text')
        d = self.dossier(case)
        body = d['evidence'][d['original_source_id']]['text']
        task = next(t for t in preflight.inspect(d,ROOT)['tasks'] if t['kind']=='inventory_command_coverage')
        self.assertTrue(any('hereby declare a national emergency' in g['text'] for g in task['uncovered_regions']))
        for gap in task['uncovered_regions']:
            self.assertEqual(body[gap['char_start']:gap['char_end']],gap['text'])
            self.assertLessEqual(gap['char_end'],task['document_extent']['body_end'])
        # Annex membership has no modal and is outside this body-only screen.
        # Its source-backed correction proposal remains separate; this is not
        # a claim that coverage of the declaration completes the inventory.


if __name__=='__main__':
    unittest.main()
