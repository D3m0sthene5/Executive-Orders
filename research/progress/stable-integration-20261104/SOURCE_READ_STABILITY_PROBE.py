import hashlib,importlib.util,json,os,stat,tempfile,types
from pathlib import Path
from unittest.mock import patch
source=Path('jobs/claim-kit/blind_verify.py').resolve()
import argparse, subprocess
parser = argparse.ArgumentParser(description='Reproduce exact-byte source-read metadata comparisons.')
parser.add_argument('--baseline', default='d52f611496de659c1c046bc717a724c00a2b651d',
                    help='Published commit with the original source implementation; exact source SHA is checked.')
args = parser.parse_args()
baseline_raw = subprocess.check_output(['git', 'show', args.baseline + ':jobs/claim-kit/blind_verify.py'])
assert hashlib.sha256(baseline_raw).hexdigest() == 'e666b1a5094898a9f02dcbf9720f4ee8ea6a65a29c2f7912d3c1445e185aa74f', 'baseline source SHA256 mismatch'
current=types.ModuleType('norton_read_before');current.__file__=str(source)
exec(compile(baseline_raw.decode('utf-8'),str(source),'exec'),current.__dict__)
spec=importlib.util.spec_from_file_location('norton_read_after',source);fixed=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixed)
results=[]
with tempfile.TemporaryDirectory() as d:
 root=Path(d);p=root/'source.txt';payload=b'exact retained source\r\n';p.write_bytes(payload)
 for field in ('unchanged','st_atime','st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink','st_uid','st_gid'):
  row={'mutation':field}
  for label,module in [('before',current),('after',fixed)]:
   original=module._path;calls=[0]
   def altered_path(*args):
    path=original(*args);calls[0]+=1
    if calls[0]!=2:return path
    s=path.stat();values=list(s);ns={k:getattr(s,k)for k in ('st_atime_ns','st_mtime_ns','st_ctime_ns')}
    indices={'st_mode':0,'st_ino':1,'st_dev':2,'st_nlink':3,'st_uid':4,'st_gid':5,'st_size':6,'st_atime':7,'st_mtime_ns':8,'st_ctime_ns':9}
    if field!='unchanged':
     i=indices[field];values[i]+=1
     if field.endswith('_ns'):ns[field]+=1000000000
     if field=='st_atime':ns['st_atime_ns']+=1000000000
    observed=os.stat_result(values,ns)
    if field=='st_atime':
     assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(observed.st_dev,observed.st_ino,observed.st_size,observed.st_mtime_ns,observed.st_ctime_ns)
     assert observed.st_atime!=s.st_atime
    return types.SimpleNamespace(stat=lambda:observed)
   try:
    with patch.object(module,'_path',side_effect=altered_path):raw=module._read(root,'source.txt',(root,))
    assert raw==payload
    row[label]='exact_bytes_returned'
   except ValueError as exc:row[label]=str(exc)
  results.append(row)
 assert results[0]['before']=='exact_bytes_returned'
 assert next(r for r in results if r['mutation']=='st_atime')['before']=='source_changed_during_read'
 for f in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns'):
  r=next(r for r in results if r['mutation']==f);assert r['after']=='source_changed_during_read'
 assert all(r['after']=='source_changed_during_read'for r in results if r['mutation']not in ('unchanged','st_atime'))
print(json.dumps({'baseline_commit':args.baseline,'baseline_source_sha256':hashlib.sha256(baseline_raw).hexdigest(),'current_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'results':results},indent=2))
