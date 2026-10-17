#!/usr/bin/env python3
"""Opt-in throttled official-source cache retriever.
Reads the output of build_official_source_manifest.py. Fetches only explicit
metadata URLs on approved hosts. A download is not a proof of legal sufficiency.
No silent retry/replace; checks file size, records errors and raw SHA256.

Example:
 python fetch_verified_official_urls.py --manifest QUEUES/OFFICIAL_DIRECT_DOCUMENT_FETCH_MANIFEST.csv --destination SOURCES/OFFICIAL_PRIMARY_CACHE --limit 10 --delay 2.0

Network access can be blocked in some research environments; failure is logged.
"""
import argparse,csv,hashlib,json,pathlib,time,urllib.request,urllib.error,urllib.parse
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--destination',required=True);p.add_argument('--limit',type=int,default=10);p.add_argument('--delay',type=float,default=1.5);p.add_argument('--max-bytes',type=int,default=8000000);a=p.parse_args()
assert 0<a.limit<=250 and a.delay>=1
out=pathlib.Path(a.destination);out.mkdir(parents=True,exist_ok=True)
all=list(csv.DictReader(open(a.manifest,encoding='utf8')))
log=[]
for r in all[:a.limit]:
 u=r['url'];parsed=urllib.parse.urlsplit(u)
 if parsed.hostname not in {'www.federalregister.gov','www.govinfo.gov'} or parsed.scheme!='https':raise RuntimeError('Blocked URL: '+u)
 ext='.pdf' if r['field']=='pdf_url' else '.xml' if r['field']=='full_text_xml_url' else '.html'
 dest=out/(r['instrument_id'].replace(':','_')+'_'+hashlib.sha256(u.encode()).hexdigest()[:12]+ext)
 item={'instrument_id':r['instrument_id'],'url':u,'local_path':str(dest),'status':'UNKNOWN'}
 try:
  if dest.exists(): item.update(status='CACHED_EXISTS_UNVERIFIED',sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),size=dest.stat().st_size)
  else:
   req=urllib.request.Request(u,headers={'User-Agent':'EO-Afterlife-Research/1.0 (source-preserving independent historical research)','Accept':'text/html,application/pdf,application/xml'})
   with urllib.request.urlopen(req,timeout=18) as response:
    content=response.read(a.max_bytes+1);typ=response.headers.get('Content-Type','')
    if len(content)>a.max_bytes:raise ValueError('size limit exceeded')
    if len(content)<50:raise ValueError('truncated/empty response')
    if b'captcha' in content[:5000].lower() or b'blocked' in content[:500].lower():raise ValueError('automated access restriction')
    dest.write_bytes(content);item.update(status='RAW_BYTES_SAVED_NOT_LEGAL_VERIFICATION',sha256=hashlib.sha256(content).hexdigest(),size=len(content),content_type=typ)
 except Exception as e:item.update(status='FETCH_FAILED_OR_REJECTED',error=repr(e))
 log.append(item)
 print(r['instrument_id'],item['status'])
 time.sleep(a.delay)
with open(out/'FETCH_LOG.jsonl','a',encoding='utf8') as f:
 for item in log:f.write(json.dumps(item)+'\n')
