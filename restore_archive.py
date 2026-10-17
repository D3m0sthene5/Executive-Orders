#!/usr/bin/env python3
"""Restore the exact consolidated ZIP from its two GitHub release assets."""
from pathlib import Path
import hashlib

here = Path(__file__).resolve().parent
base = 'EO_STAGE17_CONSOLIDATED_INPUTS_2026-10-16.zip'
expected = '52edb4d40d07fb713514968684f1adeb7cd65a52b9f89c9216fd44c590fc8775'
target = here / base
if target.exists():
    raise FileExistsError(f'Move the existing {base} aside before restoring')
digest = hashlib.sha256()
with target.open('wb') as out:
    for number in (1, 2):
        part = here / f'{base}.part{number:02d}'
        if not part.is_file():
            raise FileNotFoundError(part)
        with part.open('rb') as inp:
            for block in iter(lambda: inp.read(4 * 1024 * 1024), b''):
                out.write(block)
                digest.update(block)
if digest.hexdigest() != expected:
    target.unlink()
    raise ValueError('Restored archive failed SHA-256 verification')
print(f'Verified {target.name}: {digest.hexdigest()}')
