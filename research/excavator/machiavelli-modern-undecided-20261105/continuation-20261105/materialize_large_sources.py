"""Restore exact large retained PDFs from committed parts, without network access.

This is byte materialization only. Native custody and scientific gates are unchanged.
"""
from pathlib import Path
import argparse,hashlib,json,os,tempfile,zipfile

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def child(root,value):
 p=Path(value)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe relative source path')
 result=(root/p).resolve()
 if not result.is_relative_to(root):raise ValueError('Source path escapes selected root')
 return result

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[4])
 parser.add_argument('--output-root',type=Path)
 parser.add_argument('--skip-images',action='store_true',help='Restore primary PDFs only; individual page-image paths remain unavailable.')
 args=parser.parse_args();repo=args.repo.resolve();dest=(args.output_root or repo).resolve()
 manifest=json.loads((Path(__file__).parent/'LARGE_SOURCE_PARTS.json').read_text())
 if manifest.get('schema')!='eo-retained-source-parts/v1':raise ValueError('Wrong source-parts schema')
 results=[]
 for entry in manifest['sources']:
  target=child(dest,entry['target'])
  if target.name!=entry['sha256']+'.pdf':raise ValueError('Target is not the declared content-addressed PDF')
  if target.exists():
   if target.stat().st_size!=entry['bytes'] or digest(target)!=entry['sha256']:raise ValueError('Existing target differs; refusing overwrite')
   results.append({'target':entry['target'],'state':'already_exact','sha256':entry['sha256']});continue
  target.parent.mkdir(parents=True,exist_ok=True);tmp=None
  try:
   with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.source-parts-',delete=False) as output:
    tmp=Path(output.name)
    for part in entry['parts']:
     path=child(repo,part['path'])
     if not path.is_file() or path.is_symlink() or path.stat().st_size!=part['bytes'] or digest(path)!=part['sha256']:raise ValueError('Missing or changed source part: '+part['path'])
     with path.open('rb') as f:
      for block in iter(lambda:f.read(1048576),b''):output.write(block)
   if tmp.stat().st_size!=entry['bytes'] or digest(tmp)!=entry['sha256']:raise ValueError('Restored source does not match original bytes')
   if target.exists():raise ValueError('Target appeared during restoration; refusing overwrite')
   os.replace(tmp,target);tmp=None
   results.append({'target':entry['target'],'state':'restored_exact','bytes':entry['bytes'],'sha256':entry['sha256']})
  finally:
   if tmp is not None:tmp.unlink(missing_ok=True)
 images={'restored':0,'already_exact':0,'bundles_checked':0}
 if not args.skip_images:
  image_manifest=json.loads((Path(__file__).parent/'IMAGE_BUNDLES.json').read_text())
  if image_manifest.get('schema')!='eo-retained-page-images/v1':raise ValueError('Wrong image-bundle schema')
  for bundle in image_manifest['bundles']:
   path=child(repo,bundle['path'])
   if path.stat().st_size!=bundle['bytes'] or digest(path)!=bundle['sha256']:raise ValueError('Changed image bundle')
   with zipfile.ZipFile(path) as z:
    for record in bundle['files']:
     if record['member']!=record['sha256']+'.png':raise ValueError('Unsafe image member')
     for value in record['targets']:
      target=child(dest,value)
      if target.suffix!='.png':raise ValueError('Unexpected image target')
      if target.exists():
       if target.stat().st_size!=record['bytes'] or digest(target)!=record['sha256']:raise ValueError('Existing image differs; refusing overwrite')
       images['already_exact']+=1;continue
      data=z.read(record['member'])
      if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Image bytes differ')
      target.parent.mkdir(parents=True,exist_ok=True)
      with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.source-image-',delete=False) as out:
       temporary=Path(out.name);out.write(data)
      try:
       if target.exists():raise ValueError('Image target appeared; refusing overwrite')
       os.replace(temporary,target)
      finally:temporary.unlink(missing_ok=True)
      images['restored']+=1
   images['bundles_checked']+=1
 print(json.dumps({'sources':results,'images':images,'network_requests':0,'source_grade_or_scientific_approval':False},indent=2))

if __name__=='__main__':main()
