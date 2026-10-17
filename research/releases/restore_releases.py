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
import argparse, hashlib, json, pathlib, shutil, sqlite3, subprocess, tarfile, zipfile

HERE = pathlib.Path(__file__).resolve().parent
CHUNKS = json.loads((HERE / 'RELEASES_MANIFEST.json').read_text())

def hash_file(path:pathlib.Path)->str:
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(4*1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()

def decompress_zstd(source:pathlib.Path)->pathlib.Path:
    output=source.with_suffix('')
    if shutil.which('zstd'):
        subprocess.run(['zstd','-d','-q','-f',str(source),'-o',str(output)],check=True)
    else:
        try:
            import zstandard
        except ImportError as exc:
            raise RuntimeError('Install zstd CLI or run: python -m pip install zstandard') from exc
        with source.open('rb') as input_file,output.open('wb') as output_file:
            zstandard.ZstdDecompressor().copy_stream(input_file,output_file)
    return output

def extract_verified_workpapers(source:pathlib.Path,dest:pathlib.Path)->None:
    records=json.loads((HERE/'RESEARCH_FILES_SHA256.json').read_text())['files']
    expected={record['path']:record for record in records}
    with tarfile.open(source) as archive:
        members=archive.getmembers()
        if len(members)!=len(expected) or {m.name for m in members}!=set(expected):
            raise ValueError('Workpaper TAR membership differs from file manifest')
        for member in members:
            rel=pathlib.PurePosixPath(member.name)
            if not member.isfile() or rel.is_absolute() or '..' in rel.parts:
                raise ValueError(f'Unsafe workpaper member: {member.name}')
            data=archive.extractfile(member).read()
            record=expected[member.name]
            if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
                raise ValueError(f'Workpaper SHA-256 mismatch: {member.name}')
            output=dest.joinpath(*rel.parts)
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(data)
    print(f'VERIFIED {len(records)} WORKPAPERS in {dest}')

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
            release=restore_one(a,dest,a['name'])
            with zipfile.ZipFile(release) as archive:
                bad=archive.testzip()
                if bad:raise ValueError(f'Corrupt ZIP member: {bad}')
            print(f'VERIFIED ZIP {a["stage"]}')
    for a in CHUNKS['research_packs']:
        if args.all or (args.database and a['label']=='database') or (args.workpapers and a['label']=='workpapers'):
            zst=restore_one(a,dest,a['name'])
            if args.decompress:
                unpacked=decompress_zstd(zst)
                if a['label']=='database':
                    expected='c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1'
                    actual=hash_file(unpacked)
                    if actual!=expected:raise ValueError('Canonical Stage17 SQLite SHA-256 mismatch')
                    with sqlite3.connect(f'file:{unpacked.resolve().as_posix()}?mode=ro',uri=True) as db:
                        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',):
                            raise ValueError('Canonical Stage17 SQLite integrity check failed')
                    print('VERIFIED CANONICAL SQLITE '+actual)
                else:
                    extract_verified_workpapers(unpacked,dest/'workpapers')
    return 0

if __name__=='__main__':raise SystemExit(main())
