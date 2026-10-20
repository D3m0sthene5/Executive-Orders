import json
from pathlib import Path
import tempfile
import unittest

from prior_output import PriorOutput, UnionPriorOutput


class PriorUnionTests(unittest.TestCase):
    def prior(self, root, rows, rejected=()):
        root.mkdir()
        (root / 'RESULTS.csv').write_text('wanted_id,result\n' + ''.join(r['wanted_id'] + ',found\n' for r in rows))
        (root / 'SOURCES.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (root / 'REJECTED_PRIOR_SOURCES.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rejected))
        for r in rows:
            p = root / r['text_path']; p.parent.mkdir(exist_ok=True); p.write_text(r['sha256'])
        return PriorOutput.from_folder(root)

    def test_union_retains_both_generations_and_does_not_resurrect_quarantined_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = {'wanted_id':'a','sha256':'a'*64,'text_path':'texts/a.txt'}
            b = {'wanted_id':'b','sha256':'b'*64,'text_path':'texts/b.txt'}
            bad = {'wanted_id':'bad','sha256':'c'*64,'text_path':'texts/bad.txt'}
            one = self.prior(root/'one',[a],[bad])
            two = self.prior(root/'two',[a,b,bad])
            union = UnionPriorOutput([one,two])
            self.assertEqual({r['wanted_id'] for r in union.jsonl('SOURCES.jsonl')},{'a','b'})
            self.assertEqual(union.read(b['text_path']),b['sha256'].encode())
            self.assertEqual(union.jsonl('REJECTED_PRIOR_SOURCES.jsonl'),[bad])

    def test_import_must_pin_full_commit(self):
        for ref in ('main','abc123','../other'):
            with self.assertRaises(ValueError):PriorOutput.from_git_ref(Path('.'),'jobs/source-ladder/output',ref)
