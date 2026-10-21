import json
import hashlib
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

    def test_reextraction_of_same_pdf_keeps_old_quarantine_and_checks_current_pages(self):
        import fetch_ladder as fl
        import job
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = {'wanted_id':'a', 'sha256':'a'*64, 'text_path':'texts/a.txt',
                      'url':'https://example.gov/document.pdf', 'instrument_ids':['EO:1'],
                      'page_or_item':'PDF pages 1-1 of 3'}
            old_text = ('Original incomplete page. ' * 20).encode()
            quarantine = {**source, 'preserved_text_sha256':hashlib.sha256(old_text).hexdigest(),
                          'reason':'partial_extraction'}
            old = self.prior(root/'old', [], [quarantine])
            fixed = {**source, 'page_or_item':'PDF pages 2-3 of 3',
                     'supersedes_defective_source':{'sha256':source['sha256']}}
            incoming = self.prior(root/'incoming', [fixed])
            text_path = root/'incoming'/fixed['text_path']
            request = fl.Wanted('a', ['EO:1'], citation='PDF pages 2-3')
            for body, location, admitted in (
                    (old_text, 'PDF pages 2-3 of 3', False),
                    (b'Changed but still incomplete. '*20, 'PDF pages 1-1 of 3', False),
                    (b'Newly extracted requested pages. '*20, 'PDF pages 2-3 of 3', True)):
                text_path.write_bytes(body)
                fixed['page_or_item'] = location
                (root/'incoming'/'SOURCES.jsonl').write_text(json.dumps(fixed)+'\n')
                union = UnionPriorOutput([old, incoming], requests={'a':request})
                self.assertEqual(bool(union.jsonl('SOURCES.jsonl')), admitted)
                self.assertEqual(union.jsonl('REJECTED_PRIOR_SOURCES.jsonl'), [quarantine])
                if admitted:
                    valid, stale, _ = job.revalidate_previous(job.previous_found(union), {'a':request})
                    self.assertEqual(set(valid), {'a'})
                    self.assertEqual(stale, {})
            self.assertEqual(UnionPriorOutput([old,incoming]).jsonl('SOURCES.jsonl'), [])
