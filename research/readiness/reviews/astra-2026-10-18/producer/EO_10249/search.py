from pathlib import Path
import datetime, hashlib, json, re
out=Path(__file__).resolve().parent
roots=[('jobs/fr-originals/data/full_run/texts','*.txt'),('jobs/source-ladder/output/texts','*.txt'),('jobs/opus-media-match/output/text','*.txt'),('jobs/ofr-codification-1989/output/texts','*.txt'),('jobs/astra-source-retention/output/pages','*/selected-pages.txt')]
queries=[r'\b10249\b',r'foreign\s+data',r'foreign\s+service.{0,160}(?:reporting|reports|statistics)',r'(?:reporting|reports|statistics).{0,160}foreign\s+service',r'section\s+311.{0,100}foreign\s+service',r'foreign\s+service.{0,100}section\s+311',r'(?:Department\s+of\s+State|State\s+Department|Secretary\s+of\s+State).{0,180}(?:foreign\s+data|reporting\s+functions)',r'comprehensive\s+statement.{0,160}foreign',r'22\s+U\.?\s*S\.?\s*C\.?\s*846']
started=datetime.datetime.now(datetime.timezone.utc).isoformat();manifest=[];hits=[];counts=[]
for root,glob in roots:
    files=sorted(Path(root).glob(glob));counts.append({'root':root,'glob':glob,'recursive':False,'files_selected':len(files),'exclusions':[]})
    for p in files:
        b=p.read_bytes();t=b.decode('utf-8');norm=re.sub(r'\s+',' ',re.sub(r'[\u00ad-]\s*\n','',t));sha=hashlib.sha256(b).hexdigest()
        manifest.append({'path':p.as_posix(),'sha256':sha,'bytes':len(b),'lfs_pointer':b.startswith(b'version https://git-lfs.github.com/spec/v1')})
        for qi,q in enumerate(queries):
            mm=list(re.finditer(q,norm,re.I))
            if mm:hits.append({'path':p.as_posix(),'sha256':sha,'query_index':qi,'hit_count':len(mm),'normalized_contexts':[norm[max(0,m.start()-180):min(len(norm),m.end()+280)] for m in mm]})
for name,rows in [('search-file-manifest.jsonl',manifest),('search-hits.jsonl',hits)]:
    (out/name).open('x',encoding='utf-8',newline='\n').write(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
meta={'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':counts,'queries':queries,'normalization':'UTF-8, remove hyphen/soft-hyphen followed by whitespace and newline; collapse whitespace; case-insensitive regex. Full selected files including headers and neighboring text. No date filter or deduplication.','file_count':len(manifest),'query_file_hit_rows':len(hits),'scope_limit':'Only exact root/glob selections. Not a repository-wide, all-jobs, historical-statute or newly rerun U.S. Code/eCFR bulk search. All matched documents are not claimed fully read.'}
(out/'search-metadata.json').open('x',encoding='utf-8',newline='\n').write(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(meta,indent=2))
for h in hits:
    if h['query_index'] in [0,1,4,5,6,7,8]:print(json.dumps(h,ensure_ascii=False))
