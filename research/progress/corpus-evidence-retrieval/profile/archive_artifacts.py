#!/usr/bin/env python3
"""Losslessly archive bulky raw profiler outputs; keep producer's b06 sidecar open."""
import hashlib
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent
archive = root/'RAW_ARTIFACTS.tar.gz'
if archive.exists():
    raise FileExistsError('Refusing to overwrite existing raw archive: '+str(archive))
paths = sorted(set(root.rglob('TEXT_MANIFEST.json')) | set(root.rglob('LOOKUPS.details.json')) | set(root.rglob('*.pstats')))
manifest = []
with tarfile.open(archive,'w:gz') as tar:
    for path in paths:
        raw = path.read_bytes()
        member = path.relative_to(root).as_posix()
        manifest.append({'member':member,'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest()})
        tar.add(path,arcname=member,recursive=False)
with tarfile.open(archive,'r:gz') as tar:
    for record in manifest:
        raw = tar.extractfile(record['member']).read()
        assert len(raw)==record['raw_bytes'] and hashlib.sha256(raw).hexdigest()==record['raw_sha256']
for path in paths:
    if path.relative_to(root).as_posix() != 'b06-repaired-reuse/LOOKUPS.details.json':
        path.unlink()
receipt = {'archive':archive.name,'archive_bytes':archive.stat().st_size,
           'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
           'members':manifest,'producer_sidecar_kept':'b06-repaired-reuse/LOOKUPS.details.json',
           'notice':'Raw bytes verified after archive creation before originals removed; b06 sidecar remains for active producer.'}
(root/'ARCHIVE_MANIFEST.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'archive_bytes':receipt['archive_bytes'],'members':len(manifest),'raw_bytes':sum(x['raw_bytes'] for x in manifest)}))
