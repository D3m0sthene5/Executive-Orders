import json
from pathlib import Path
import tempfile
import unittest
from build import ShardedJsonl, line

class ShardTests(unittest.TestCase):
    def test_every_unicode_record_retained_and_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'CLAUSES.jsonl'
            records=[{'i':i,'text':'é'*7} for i in range(20)]
            with ShardedJsonl(p,limit=95) as fh:
                for row in records:line(fh,row)
            paths=[p]+sorted(Path(d).glob('CLAUSES.part*.jsonl'))
            self.assertGreater(len(paths),1)
            self.assertTrue(all(x.stat().st_size<=95 for x in paths))
            got=[json.loads(s) for x in paths for s in x.read_text('utf-8').splitlines()]
            self.assertEqual(got,records)
            with ShardedJsonl(p,limit=95) as fh:line(fh,records[0])
            self.assertEqual(list(Path(d).glob('CLAUSES.part*.jsonl')),[])

if __name__=='__main__':unittest.main()
