import pathlib,json,hashlib,sys,shutil
root=pathlib.Path('/workspace/scratch/c478176c789b/eo-neyman');p=root/'research/excavator/counterexample-first-2026-10-26/packet';out=root/'jobs/astra-source-retention/output';canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False);sha=lambda b:hashlib.sha256(b).hexdigest()
selected=[json.loads(l) for l in (p/'PROPOSED_SELECTION.v1.jsonl').read_text().splitlines()];selected=[json.load(open(p/'producers/EO_8123/MANUAL_CLAIM.v2.json')) if c['instrument_id']=='EO:8123' else c for c in selected];(p/'PROPOSED_SELECTION.v2.jsonl').write_text(''.join(canon(c)+'\n' for c in selected))
rows=[];seen=set();pins=[];raws={}
for c in selected:
 def walk(v):
  if isinstance(v,dict):
   if v.get('text_path') and v.get('sha256') and v.get('text_sha256'):
    path=(root/v['text_path']).resolve();assert path.is_relative_to(root) and path.is_file();raw=path.read_bytes();assert sha(raw)==v['text_sha256'];digest=v['sha256'];pdf=out/'pdf'/f'{digest}.pdf';assert pdf.is_file();raws.setdefault(digest,sha(pdf.read_bytes()));assert raws[digest]==digest
    key=(digest,v['text_sha256'],v.get('url'));dest=out/'pages'/digest/'attributed-derivatives'/f'{v["text_sha256"]}.txt'
    if key not in seen:
     seen.add(key);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
     rows.append({'source_id':'reviewed-pdf-extraction:'+digest[:12]+':'+v['text_sha256'][:12],'url':v.get('url'),'sha256':digest,'bytes':pdf.stat().st_size,'cache_path':pdf.relative_to(out).as_posix(),'text_path':dest.relative_to(out).as_posix(),'text_sha256':v['text_sha256'],'page_or_item':v.get('page_or_item'),'instrument_ids':[],'requested_targets':[c['instrument_id']],'route':'attributed_retained_pdf_text_derivative','evidence_tier':'document_text','note':'Exact already source-reviewed PDF extraction registered through existing SOURCES interface. Requested targets confer no original identity/source grade. Raw bytes rehashed; text kept byte-exact; original extraction provenance in pinned source_path.','source_path':v['text_path']})
     pins.append({'source_path':v['text_path'],'source_sha256':v['text_sha256'],'copied_path':str(dest.relative_to(root)),'pdf_path':str(pdf.relative_to(root)),'pdf_sha256':digest})
   for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 walk(c)
sp=out/'SOURCES.jsonl';before=sp.read_bytes();(p/'SOURCES.before_derivative_registration.jsonl').write_bytes(before);existing={json.loads(s).get('source_id') for s in before.splitlines() if s.strip()};add=[r for r in rows if r['source_id'] not in existing];sp.write_bytes(before+''.join(canon(r)+'\n' for r in add).encode());(p/'DERIVATIVE_REGISTRATION.json').write_text(json.dumps({'schema':'eo-attributed-derivative-registration/v1','route':'Existing native retention/source-checker SOURCES.jsonl interface, no runtime or gate changes','before_sha256':sha(before),'after_sha256':sha(sp.read_bytes()),'new_records':len(add),'raw_objects_verified':len(raws),'copies':pins,'source_truth_limit':'Registration establishes bytes/path association, not legal truth, source grade, authenticated original identity or human approval. Exact raw PDF and derivative/page review remain separately pinned.'},indent=2)+'\n');print({'derivatives_registered':len(add),'raws_verified':len(raws)})
