import json
from pathlib import Path
import tempfile
import unittest
import paired
import mountweazel


class PairedTests(unittest.TestCase):
    def test_isolation_key_seal_and_material_gap_scoring(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'practice'; paired.prepare(p)
            batch = json.loads((p / 'batch.json').read_bytes())
            self.assertTrue(all('schema' in mountweazel.seeded_gate_errors(i) and 'instrument_id' in mountweazel.seeded_gate_errors(i) for i in batch))
            key = json.loads((p / 'KEY.json').read_bytes())
            verdicts = [{'item_id': k['item_id'], 'findings': k['expected'], 'reason': 'The stipulated rule and supplied evidence support this label.'} for k in key['items']]
            v = Path(d) / 'verdicts.json'; v.write_text(json.dumps(verdicts))
            score = paired.score(p / 'KEY.json', p / 'batch.json', v)
            self.assertEqual(score['items_passed'], 12); self.assertFalse(score['blinding_technically_enforced'])
            self.assertFalse(score['legal_accuracy_estimated'])
            # Ignoring removed evidence fails the material pair.
            gap = next(r for r in verdicts if r['findings'] == ['performance_gap'])
            gap['findings'] = ['delivery_supported']; v.write_text(json.dumps(verdicts))
            self.assertLess(paired.score(p / 'KEY.json', p / 'batch.json', v)['items_passed'], 12)
            key['items'][0]['expected'] = ['other']; (p / 'KEY.json').write_text(json.dumps(key))
            with self.assertRaises(ValueError):paired.score(p / 'KEY.json', p / 'batch.json', v)

    def test_repository_output_and_missing_duplicate_verdicts_refused(self):
        with self.assertRaises(ValueError):paired.prepare(paired.REPO / 'practice-forbidden')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'practice'; paired.prepare(p)
            v = Path(d) / 'verdicts.json'; v.write_text('[]')
            with self.assertRaises(ValueError):paired.score(p / 'KEY.json', p / 'batch.json', v)


if __name__ == '__main__':
    unittest.main()
