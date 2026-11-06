import datetime,json,tempfile,unittest
from pathlib import Path
from job import build
class DigestTests(unittest.TestCase):
    def test_bounded_and_repeatable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'jobs').mkdir();(root/'HANDOFF').mkdir()
            text,snap=build(root,datetime.date(2026,10,17),{})
            self.assertLess(len(text.splitlines()),150)
            self.assertEqual(text,build(root,datetime.date(2026,10,17),{})[0])
            self.assertIn('baseline',text);self.assertEqual(snap['date'],'2026-10-17')
if __name__=='__main__':unittest.main()


class GenerationTests(unittest.TestCase):
    """Justinian 2026-11-06: refuse a tracker whose SUMMARY and STATUS come from different executions."""
    def write(self, root, summary, status):
        folder = root / 'jobs/readiness-tracker/output'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'SUMMARY.json').write_text(json.dumps(summary), encoding='utf-8')
        (folder / 'STATUS.json').write_text(json.dumps(status), encoding='utf-8')

    def test_generation_rule(self):
        import job
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.write(root, {}, {})
            self.assertIsNone(job.generation_mismatch(root))
            self.write(root, {'generation_id': 'r1:abc'}, {'generation_id': 'r1:abc'})
            self.assertIsNone(job.generation_mismatch(root))
            self.write(root, {'generation_id': 'r1:abc'}, {'generation_id': 'r2:def'})
            self.assertIn('differs', job.generation_mismatch(root))
            self.write(root, {'generation_id': 'r1:abc'}, {})
            self.assertIn('differs', job.generation_mismatch(root))
