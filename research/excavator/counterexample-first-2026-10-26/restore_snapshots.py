"""Restore byte-exact archived large execution snapshots; never overwrite a mismatch."""
from pathlib import Path
import gzip,hashlib,json
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
manifest=json.loads((RUN/'PUBLICATION_STORAGE.json').read_bytes())
for row in manifest['compressed_files']:
 dest=(ROOT/row['path']).resolve();src=(ROOT/row['archive']).resolve()
 if not dest.is_relative_to(ROOT) or not src.is_relative_to(ROOT):raise ValueError('unsafe path')
 data=gzip.decompress(src.read_bytes())
 if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('archive hash mismatch')
 if dest.exists():
  if dest.read_bytes()!=data:raise ValueError('refusing overwrite '+str(dest))
 else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
print(json.dumps({'snapshots_verified_or_restored':len(manifest['compressed_files'])}))
