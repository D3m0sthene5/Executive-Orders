"""Bartolus: store completion receipts over 50 MB as lossless gzip with a SHA-256 record (Papinian precedent).
usage: python3 -I gzip_receipts.py COMPLETE_DIR [...]"""
import gzip, hashlib, json, sys
from pathlib import Path
for d in sys.argv[1:]:
    for p in Path(d).rglob('*'):
        if p.is_file() and p.suffix != '.gz' and p.stat().st_size > 50_000_000:
            raw = p.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
            gz = p.with_name(p.name + '.gz')
            with gzip.GzipFile(gz, 'wb', compresslevel=9, mtime=0) as f: f.write(raw)
            assert hashlib.sha256(gzip.decompress(gz.read_bytes())).hexdigest() == sha
            p.with_name(p.stem + '.COMPRESSED.json').write_text(json.dumps({'file': p.name, 'stored_as': gz.name, 'sha256_uncompressed': sha, 'bytes_uncompressed': len(raw), 'reason': 'GitHub 100 MB file limit; gzip -9n is lossless (verified by round trip)'}))
            p.unlink(); print('gz', p, len(raw), '->', gz.stat().st_size)
