#!/usr/bin/env python3
"""Restore Stage 12–17 EO research archives from reproducible GitHub fragments.

Usage:
 python research/releases/restore_releases.py --all
 python research/releases/restore_releases.py --release 17 --out ./recovered
 python research/releases/restore_releases.py --database
 python research/releases/restore_releases.py --workpapers

All content is verified against SHA-256. No input chunks are modified.
Public Stage 15 is intentionally missing the sealed baseline labels for blind QA.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, subprocess, tarfile

HERE = pathlib.Path(__file__).resolve().parent
CHUNKS = json.loads((HERE / 'RELEASES_MANIFEST.json').read_text())

def restore_one(item:dict, dest:pathlib.Path, stem:str)->pathlib.Path:
    dest.mkdir(parents=True,exist_ok=True)
    out=dest/stem
    digest=hashlib.sha256()
    with out.open('wb') as fh:
        for part in item['parts']:
            path=HERE/part['path'].removeprefix('research/releases/')
            if not path.exists():
                raise FileNotFoundError(f'GitHub archive fragment unavailable: {path}')
            data=path.read_bytes()
            if len(data)!=part['size_bytes'] or hashlib.sha256(data).hexdigest()!=part['sha256']:
                raise ValueError(f'Bad archive part: {path}')
            digest.update(data);fh.write(data)
    expected=item.get('published_sha256',item.get('sha256'))
    if digest.hexdigest()!=expected:
        out.unlink(missing_ok=True)
        raise ValueError(f'Whole-archive SHA-256 mismatch: {out.name}')
    print(f'VERIFIED {out}  SHA-256 {digest.hexdigest()}')
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--all',action='store_true')
    parser.add_argument('--release',type=int,choices=range(12,18))
    parser.add_argument('--database',action='store_true')
    parser.add_argument('--workpapers',action='store_true')
    parser.add_argument('--decompress',action='store_true',help='Decompress zstd packs after SHA-256 validation (requires zstd CLI)')
    parser.add_argument('--out',default='restored_research')
    args=parser.parse_args()
    if not any([args.all,args.release,args.database,args.workpapers]):
        parser.error('Choose --all, --release N, --database or --workpapers')
    dest=pathlib.Path(args.out)
    for a in CHUNKS['releases']:
        if args.all or args.release==a['stage']:
            restore_one(a,dest,a['name'])
    for a in CHUNKS['research_packs']:
        if args.all or (args.database and a['label']=='database') or (args.workpapers and a['label']=='workpapers'):
            zst=restore_one(a,dest,a['name'])
            if args.decompress:
                subprocess.run(['zstd','-d','-q','-f',str(zst),'-o',str(zst.with_suffix(''))],check=True)
                if a['label']=='database':
                    expected='c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1'
                    actual=hashlib.sha256(zst.with_suffix('').read_bytes()).hexdigest()
                    if actual!=expected:raise ValueError('Canonical Stage17 SQLite SHA-256 mismatch')
                    print('VERIFIED CANONICAL SQLITE '+actual)
    return 0

if __name__=='__main__':raise SystemExit(main())
