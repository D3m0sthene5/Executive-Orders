import datetime,tempfile,unittest
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
