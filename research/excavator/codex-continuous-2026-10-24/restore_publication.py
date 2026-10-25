#!/usr/bin/env python3
"""Restore oversized exact consumer snapshots without altering research records."""
from pathlib import Path
import gzip,hashlib,json
root=Path(__file__).resolve().parents[3]
manifest=json.loads(Path(__file__).with_name('PUBLICATION_STORAGE.json').read_text())
for row in manifest['compressed_exact_snapshots']:
    raw=gzip.decompress((root/row['stored_path']).read_bytes())
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    dest=root/row['original_path']
    if dest.exists():
        assert dest.read_bytes()==raw, f'Refusing changed snapshot: {dest}'
    else:
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
print(f"Verified/restored {len(manifest['compressed_exact_snapshots'])} exact snapshots")
compiler_manifest=Path(__file__).parent/'route/compiler-snapshot/MANIFEST.json'
if compiler_manifest.exists():
    compiler=json.loads(compiler_manifest.read_text())
    for row in compiler['files']:
        packed=b''.join((root/p).read_bytes() for p in row['parts'])
        assert hashlib.sha256(packed).hexdigest()==row['stored_sha256']
        raw=gzip.decompress(packed)
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
        dest=root/row['original_path']
        if dest.exists():
            assert dest.read_bytes()==raw, f'Refusing changed compiler input: {dest}'
        else:
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    print(f"Verified/restored {len(compiler['files'])} exact sparse compiler inputs")
