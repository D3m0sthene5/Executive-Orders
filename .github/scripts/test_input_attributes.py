"""Byte-preservation regression for the input that blocked run40956514088."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class InputAttributesTests(unittest.TestCase):
    def test_hathi_source_json_keeps_exact_bytes(self):
        # Use actual repository rules, including the nested override.
        attrs = subprocess.check_output(['git', 'show', 'HEAD:.gitattributes'], cwd=ROOT)
        nested = (ROOT / 'jobs/hathi-gpo-orders/.gitattributes').read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / '.gitattributes').write_bytes(attrs)
            folder = repo / 'jobs/hathi-gpo-orders'
            (folder / 'data').mkdir(parents=True)
            (folder / '.gitattributes').write_bytes(nested)
            rel = 'jobs/hathi-gpo-orders/data/TARGETS.json'
            raw = b'{\r\n  "source": "retained"\r\n}\r\n'
            (repo / rel).write_bytes(raw)
            expected = subprocess.check_output(['git', 'hash-object', '--stdin'], input=raw, cwd=repo).strip()
            for autocrlf in ('false', 'true'):
                with self.subTest(autocrlf=autocrlf):
                    actual = subprocess.check_output(['git', '-c', 'core.autocrlf=' + autocrlf,
                                                      'hash-object', '--path=' + rel, rel], cwd=repo).strip()
                    self.assertEqual(actual, expected)
                    subprocess.run(['git', '-c', 'core.autocrlf=' + autocrlf, 'add', rel], cwd=repo, check=True)
                    (repo / rel).unlink()
                    subprocess.run(['git', '-c', 'core.autocrlf=' + autocrlf, 'checkout-index', '--', rel], cwd=repo, check=True)
                    self.assertEqual((repo / rel).read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
