"""Bind parent-retained custody objects; never fetch or alter shared source files."""
from pathlib import Path
import json, hashlib, re, datetime
OUT=Path(__file__).parent
BASE=OUT.parent
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
requests=json.loads((OUT/'SOURCE_REQUESTS.json').read_text())
maps=sorted(BASE.glob('SOURCE_MAP*.json'))
sources={}
for p in maps:
 for s in json.loads(p.read_text()).get('sources',[]): sources[s['url']]=s
findings=json.loads((OUT/'SOURCE_FINDINGS.json').read_text())
rows=[]
for request in requests:
 s=sources.get(request['url'])
 if not s: continue
 raw=Path(s['raw_path'])
 if not raw.exists() or sha(raw)!=s['sha256']: raise RuntimeError('native custody hash mismatch '+str(raw))
 row={'url':request['url'],'instrument_ids':request['instrument_ids'],'raw_path':str(raw),'raw_sha256':s['sha256'],'raw_bytes':raw.stat().st_size,'raw_hash_verified':True,'custody_only':True,'native_registry_admission':False,'scientific_approval':False,'selected_texts':[]}
 for text in s.get('selected_texts',[]):
  p=Path(text['path'])
  if sha(p)!=text['sha256']: raise RuntimeError('native selected-text hash mismatch '+str(p))
  t=p.read_text();spans=[]
  # These are exact locator windows, not a finding that every occurrence has legal effect.
  pattern=r'Effective:|effective (?:on|date)|January 21, 2021|February 22, 2021|October 25, 2022|Executive Order 10582|Executive Order 13881|E\.O\. 13881|October 1, 2026|September 30, 2027|April 1, 1959|\b3279\b|5-203\.|603\(e\)|654\.1[123]|25\.10[156]|25\.20[14]'
  for match in list(re.finditer(pattern,t,re.I))[:18]:
   a=match.start();b=min(len(t),a+220);end=t.find('\n',b)
   if end>=0 and end<b+150:b=end
   q=t[a:b];marks=list(re.finditer(r'=== PDF page (\d+)(?: of \d+)? ===',t[:a]))
   spans.append({'char_start':a,'char_end':b,'offset_units':'Unicode code points in exact text_path','pdf_page':int(marks[-1].group(1)) if marks else None,'quote':q,'quote_sha256':hashlib.sha256(q.encode()).hexdigest()})
  row['selected_texts'].append({'text_path':str(p),'text_sha256':text['sha256'],'hash_verified':True,'exact_locator_spans':spans})
 rows.append(row)
 request['status']='native_retained_hash_verified_not_approved'
 request['held_sha256']=s['sha256'];request['held_path']=str(raw)
for old in findings['held_source_checks']:
 match=next((s for s in sources.values() if s.get('sha256')==old['source']['sha256']),None)
 if match:
  p=Path(match['raw_path']);old.update(raw_pdf_exists=True,raw_pdf_path=str(p),raw_pdf_hash_verified=sha(p)==old['source']['sha256'])
for observation in findings['new_primary_observations']:
 match=next((s for s in rows if s['url']==observation['url']),None)
 if observation['id']=='WEB:Proc3279':
  match=next((s for s in rows if '1781-1784.pdf' in s['url']),match)
 if match:
  observation.update(custody='native_retained_hash_verified_registry_admission_pending',sha256=match['raw_sha256'],raw_path=match['raw_path'],exact_local_offsets=[{'text_path':t['text_path'],'text_sha256':t['text_sha256'],'spans':t['exact_locator_spans']} for t in match['selected_texts']])
findings['new_retained_source_checks']=rows
findings['native_binding']={'map_paths':[str(p) for p in maps],'bound_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_count':len(requests),'retained_count':len(rows),'not_retained':[r['url'] for r in requests if r['url'] not in {s['url'] for s in rows}],'scope':'Custody and exact locator spans only. Substantive findings and remaining gaps remain separately stated; no automatic source registration, approval or cutoff exhaustiveness.'}
save(OUT/'SOURCE_REQUESTS.json',requests);save(OUT/'SOURCE_FINDINGS.json',findings)
print(json.dumps(findings['native_binding'],indent=2))
