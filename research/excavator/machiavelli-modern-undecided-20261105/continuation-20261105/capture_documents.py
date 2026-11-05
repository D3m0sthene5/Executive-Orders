"""Capture a bounded, already-queued HTML/XML manifest using source-ladder's client.

Raw custody and text derivation only; no source authentication or legal conclusion.
PDFs use the existing astra-source-retention job separately.
"""
from pathlib import Path
import hashlib, json, os, shutil, sys, time
repo=Path(os.environ['REPO_ROOT']).resolve()
sys.path.insert(0,str(repo/'jobs/source-ladder'))
from fetch_ladder import Fetcher, extract_text, now_utc
manifest=Path(os.environ['DOCUMENT_MANIFEST']).resolve(); out=Path(os.environ['OUTPUT_DIR']).resolve()
assert manifest.is_relative_to(repo) and out.is_relative_to(repo)
items=json.loads(manifest.read_text()); assert len(items)<=30
queue=[json.loads(x) for x in (repo/'research/readiness/FETCH_QUEUE.jsonl').read_text().splitlines() if x.strip()]
pairs={(q.get('instrument_id'),u) for q in queue for u in q.get('urls',[])}
assert all((i,x['url']) in pairs for x in items for i in x['instrument_ids'])
out.mkdir(parents=True,exist_ok=True)
fetcher=Fetcher(out/'cache',max_requests=75,max_bytes=100_000_000,max_retries=2,timeout=60)
start=time.monotonic(); records=[]; sources=[]
for item in items:
 record=dict(item)
 try:
  att=fetcher.fetch(item['url'],route='queued_machiavelli_continuation_document',expect=item['expect'])
  record['attempt']={k:v for k,v in att.items() if k!='path'}
  if att.get('accepted'):
   raw=Path(att['path']).read_bytes(); digest=hashlib.sha256(raw).hexdigest()
   assert digest==att['sha256']
   raw_path=out/'raw'/(digest+('.xml' if item['expect']=='xml' else '.html'));raw_path.parent.mkdir(exist_ok=True);raw_path.write_bytes(raw)
   text,info=extract_text(raw_path,att.get('content_type',''),item['expect'])
   source={'url':item['url'],'final_url':att.get('final_url'),'sha256':digest,'raw_path':raw_path.relative_to(repo).as_posix(),'bytes':len(raw),'requested_for_instrument_ids':item['instrument_ids'],'instrument_ids':[],'retrieved_utc':att.get('time_utc'),'route':'source-ladder.Fetcher queued capture','authentication_or_legal_approval':False,'extraction_info':info}
   if text is not None:
    tp=out/'texts'/(digest+'.txt');tp.parent.mkdir(exist_ok=True);tp.write_text(text,encoding='utf-8',newline='\n')
    source.update(text_path=tp.relative_to(repo).as_posix(),text_sha256=hashlib.sha256(tp.read_bytes()).hexdigest())
   sources.append(source);record['source']=source
 except Exception as exc:record['error']=type(exc).__name__+': '+str(exc)[:600]
 records.append(record)
 (out/'RESULTS.json').write_text(json.dumps(records,indent=2)+'\n')
 (out/'SOURCES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in sources))
 print(json.dumps({'url':item['url'],'retained':bool(record.get('source')),'error':record.get('error')}),flush=True)
summary={'generated_utc':now_utc(),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'requested':len(items),'attempted':len(records),'retained':len(sources),'http_requests':fetcher.requests,'download_bytes':fetcher.bytes_downloaded,'wall_seconds':time.monotonic()-start,'scientific_approval':False,'exhaustion':False}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
