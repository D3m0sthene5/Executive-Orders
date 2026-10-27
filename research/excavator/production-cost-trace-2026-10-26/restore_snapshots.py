"""Restore exact archived machine snapshots; refuse altered bytes or overwrites."""
from pathlib import Path
import gzip, hashlib, json
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
manifest=json.loads((RUN/'SNAPSHOTS.json').read_bytes())
for row in manifest['files']:
 dest=(ROOT/row['path']).resolve();src=(ROOT/row['compressed_path']).resolve()
 if not dest.is_relative_to(ROOT) or not src.is_relative_to(ROOT):raise ValueError('unsafe path')
 compressed=src.read_bytes()
 if hashlib.sha256(compressed).hexdigest()!=row['compressed_sha256']:raise ValueError('compressed hash mismatch')
 data=gzip.decompress(compressed)
 if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('archive hash mismatch')
 if dest.exists():
  if dest.read_bytes()!=data:raise ValueError('refusing overwrite '+str(dest))
 else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
print(json.dumps({'snapshots_verified_or_restored':len(manifest['files'])}))
