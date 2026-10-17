"""Deterministic one-fetch order startup packets. No legal adjudication."""
from __future__ import annotations
import collections, csv, hashlib, json, os, re, statistics
from pathlib import Path
LIMIT = 29_900

def canon(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def sha(x): return hashlib.sha256(x).hexdigest()
def emit(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(canon(x)+'\n',encoding='utf-8',newline='\n')
def lines(p):
    if p.is_file():
        with p.open(encoding='utf-8') as f:
            for n,s in enumerate(f,1):
                if s.strip(): yield n,json.loads(s)
def csvrows(p):
    if not p.is_file(): return []
    with p.open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def pointer(root,p,obj,line=None):
    return {'path':p.relative_to(root).as_posix(),'line':line,'record_sha256':sha(canon(obj).encode())}
def trim(obj,n=500):
    if isinstance(obj,str) and len(obj)>n:return {'preview':obj[:n],'characters':len(obj),'sha256_utf8':sha(obj.encode()),'truncated':True}
    if isinstance(obj,list):return [trim(x,n) for x in obj]
    if isinstance(obj,dict):return {k:trim(v,n) for k,v in obj.items()}
    return obj

def bounded(packet):
    if len((canon(packet)+'\n').encode())<=LIMIT:return packet
    # Complete arrays remain addressable through exact row hashes and local file pointers.
    for key in ('fragments','later_events','current_law_hits','conflicts','claim_draft'):
        full=packet[key]
        packet.setdefault('overflow',{})[key]={'sha256':sha(canon(full).encode()),'reason':'30 KB startup budget; follow record pointers for complete evidence'}
        if isinstance(full,list):
            packet[key]=[{'record':x['record'],'sources':trim(x.get('sources',[]),150),'preview':trim(x.get('data',x.get('preview',{})),120)} if isinstance(x,dict) and 'record' in x else trim(x,120) for x in full]
        else: packet[key]={'record':packet['draft_record'],'preview':trim(full,120)}
        if len((canon(packet)+'\n').encode())<=LIMIT:return packet
    # Pathological cases: retain every fragment pointer, all sections, and the order's blocker summary.
    for key in ('fragments','later_events','current_law_hits','conflicts'):
        packet[key]=[{'record':x.get('record') or packet['draft_record'],'sources':x.get('sources',[]),'summary':'See complete record at pointer'} for x in packet[key]]
    packet['claim_draft']={'record':packet['draft_record'],'summary':'See complete draft at pointer'}
    if len((canon(packet)+'\n').encode())>LIMIT:
        for item in packet['text_pointers']:
            if 'first_1500_characters' in item:
                item['preview_truncated_for_budget']=True
                item['first_1500_characters']=item['first_1500_characters'][:400]
    if len((canon(packet)+'\n').encode())>LIMIT:
        # Dense current-law fragments can cite hundreds of sources. Keep their
        # exact source-set hash/count and the full fragment pointer, rather than
        # pretending every citation can fit inside a fixed startup budget.
        for key in ('fragments','later_events','current_law_hits','conflicts'):
            for item in packet[key]:
                refs=item.get('sources',[])
                if refs:
                    item['sources']={'in_full_record':item['record'],'count':len(refs),'canonical_sha256':sha(canon(refs).encode())}
    if len((canon(packet)+'\n').encode())>LIMIT:
        for item in packet['text_pointers']:
            item.pop('first_1500_characters',None)
            item['preview_omitted_for_budget']=True
    if len((canon(packet)+'\n').encode())>LIMIT:raise ValueError('Order exceeds startup budget even as pointers; no silent omission: '+packet['instrument_id'])
    return packet

def run(root,out,tokenizer=None):
    drafts=root/'jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl'
    if not drafts.is_file():raise FileNotFoundError(drafts)
    wanted={r['instrument_id'] for r in csvrows(root/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv')}
    ready={r['instrument_id']:r for r in csvrows(root/'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv')}
    fragments=collections.defaultdict(list); events=collections.defaultdict(list); hits=collections.defaultdict(list)
    source_records=collections.defaultdict(list)
    inputs=[]
    for p in sorted((root/'jobs').glob('*/output/FRAGMENTS.jsonl')):
        if p.parent.parent.name=='case-bundles':continue
        inputs.append({'path':p.relative_to(root).as_posix(),'sha256':sha(p.read_bytes())})
        for n,f in lines(p):
            iid=f.get('instrument_id')
            if iid not in wanted:continue
            row={'record':pointer(root,p,f,n),'kind':f.get('kind'),'sources':f.get('sources',[]),'data':f.get('data')}
            fragments[iid].append(row)
            if f.get('kind')=='later_event_candidates':events[iid].append(row)
            if f.get('kind')=='current_predicate_candidates':hits[iid].append(row)
    for p in sorted((root/'jobs').glob('*/output/SOURCES.jsonl')):
        for n,s in lines(p):
            ids=s.get('instrument_ids',[])
            if isinstance(s.get('instrument_id'),str):ids=[*ids,s['instrument_id']]
            for iid in ids:
                if iid in wanted:source_records[iid].append((p,s,n))
    index=[]; metrics=[]
    for n,d in lines(drafts):
        iid=d.get('instrument_id') or d.get('claim',{}).get('instrument_id')
        if iid not in wanted:continue
        meta=d.get('_draft',{}); texts=[]; seen=set()
        for p,s,sn in source_records[iid]:
            rel=s.get('text_path') or s.get('text_file')
            if not isinstance(rel,str):continue
            q=(p.parent/rel).resolve()
            if not q.is_relative_to(root.resolve()) or not q.is_file() or q in seen:continue
            seen.add(q);raw=q.read_bytes()
            texts.append({'path':q.relative_to(root).as_posix(),'sha256':sha(raw),'source':pointer(root,p,s,sn),
                          'first_1500_characters':raw.decode('utf-8',errors='replace')[:1500]})
        packet={'schema':'eo-case-bundle/v1','instrument_id':iid,'status':meta.get('provisional_status'),
            'readiness':ready.get(iid,{}),'readiness_blockers':meta.get('missing_evidence',[]),
            'gate_errors':meta.get('gate',{}).get('errors_now',[]),'draft_record':pointer(root,drafts,d,n),
            'claim_draft':d,'fragments':fragments[iid],'text_pointers':texts,'later_events':events[iid],
            'current_law_hits':hits[iid],'conflicts':meta.get('conflicts',[]),
            'notice':'Research startup packet; statuses remain provisional. Overflow records are explicit and require their source pointers.'}
        before=canon(packet).encode(); packet=bounded(packet);after=(canon(packet)+'\n').encode()
        num=iid.removeprefix('EO:'); safe=re.sub('[^0-9A-Za-z_-]','_',num);prefix=safe.zfill(5)[:2]
        rel=f'bundles/{prefix}/EO_{safe}.json';emit(out/rel,packet)
        index.append({'instrument_id':iid,'path':rel,'bytes':len(after),'sha256':sha(after),'overflow_sections':len(packet.get('overflow',{}))})
        m={'instrument_id':iid,'assembled_bytes_before':len(before),'bundle_bytes_after':len(after),'startup_fetches_before':1+len({x['record']['path'] for x in fragments[iid]})+len(texts),'startup_fetches_after':1}
        if tokenizer:m.update(tokens_before=len(tokenizer(before.decode())),tokens_after=len(tokenizer(after.decode())))
        metrics.append(m)
    out.mkdir(parents=True,exist_ok=True)
    with (out/'INDEX.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['instrument_id','path','bytes','sha256','overflow_sections'],lineterminator='\n');w.writeheader();w.writerows(index)
    emit(out/'INPUTS.json',inputs)
    emit(out/'METRICS.json',{'job':'case-bundles','orders':len(metrics),'max_bundle_bytes':max((x['bundle_bytes_after'] for x in metrics),default=0),
        'comparison':'Same assembled evidence, before compact startup budget versus emitted bundle; excludes tool wrappers and agent reasoning.',
        'median_fetches_before':statistics.median([x['startup_fetches_before'] for x in metrics]) if metrics else 0,
        'median_fetches_after':1,'tokenizer':'cl100k_base' if tokenizer else 'not measured','orders_measured':metrics})
    return index
