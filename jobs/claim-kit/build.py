"""One corpus pass; machine leads only. No fetching and no legal decisions."""
from __future__ import annotations
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import time

from inputs import load_corpus
from current_evidence import enrich_current
from excavate import segment, own_terms, acting_provision, discover_mentions, chain, generic_reference_count
from assemble import blank_sheet, canonical_sha, assemble

CUTOFF = '2026-10-14'

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')

def line(fh, obj):
    fh.write(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))+'\n')

def filename(iid):
    if not re.fullmatch(r'EO:[A-Za-z0-9_.-]+', iid):
        # Historical census identifiers can contain punctuation. Never conflate identities.
        return 'ID_'+hashlib.sha256(iid.encode()).hexdigest()[:24]
    return 'EO_'+iid[3:]

def rank_text(r):
    grade=str(r.get('grade') or '').lower()
    return (not bool(r.get('acceptable_as_original')), 'needs_page_check' in grade,
            'mirror' in grade or 'transcription' in grade, 'codification' in grade,
            r['text_path'])

def safe_read(repo, rel):
    p=(repo/rel).resolve()
    if not p.is_relative_to(repo.resolve()):
        raise ValueError('text path escapes repository')
    return p.read_bytes().decode('utf-8')

def package(iid, corpus, selected, clause_rec, terms, acts, chain_rec, missing):
    draft=corpus['drafts'].get(iid,{})
    d=draft.get('_draft',{})
    evidence={}
    clauses=[]
    rec=selected.get(iid)
    original_id=None
    if rec:
        original_id='ORIGINAL:'+iid
        evidence[original_id]={
            'id':original_id, 'source':rec['source'], 'text':rec['text'],
            'char_start':0, 'char_end':len(rec['text']),
            'acceptable_as_original':bool(rec.get('acceptable_as_original')),
            'grade':rec.get('grade'), 'actor_id':iid,
            'signing_date':rec.get('signing_date'), 'role':'original'}
    if clause_rec:
        for c in clause_rec.get('clauses',[]):
            v=dict(c,source=clause_rec['source'])
            v['id']='CLAUSES:'+v['scope_id']
            clauses.append(v)
            evidence[v['id']]=v
    for n,t in enumerate(terms):
        v=dict(t)
        eid=v.get('id') or f'TERM:{iid}#{n}'
        v.update(id=eid,actor_id=iid,effective_date=t.get('stated_end_date') or t.get('computed_end_candidate'),mechanism='own_terms_'+t['kind'])
        evidence[eid]=v
    for a in acts:
        v=dict(a)
        eid=v.get('id') or 'ACT:'+iid+'>'+a['actor_id']
        v.update(id=eid,source=a.get('actor_source'),text=a.get('provision_text',''))
        evidence[eid]=v
        for alt in a.get('alternative_provisions',[]):
            evidence[alt['id']]=dict(alt,source=alt.get('actor_source'),text=alt.get('provision_text',''))
        for n,e in enumerate(a.get('effective_wording',[])):
            if isinstance(e,dict) and e.get('text'):
                key=eid+f':effective#{n}'
                evidence[key]=dict(e, id=key, source=a['actor_source'],actor_id=a['actor_id'])
    actor_contexts=[]
    for actor in sorted({a['actor_id'] for a in acts}):
        ar=selected.get(actor)
        if not ar:continue
        key='ACTOR_TEXT:'+actor
        if len(ar['text'].encode('utf-8'))<=50000:
            evidence[key]={'id':key,'source':ar['source'],'text':ar['text'],'char_start':0,'char_end':len(ar['text']),'actor_id':actor,'role':'actor_context'}
            actor_contexts.append({'actor_id':actor,'evidence_id':key})
        else:
            pointer='actor-texts/'+filename(actor)+'.json'
            actor_contexts.append({'actor_id':actor,'overflow':pointer,'text_sha256':ar['source']['text_sha256']})
            missing.append('Large actor context must be read at '+pointer+' before deciding scope/savings.')
    # Current-law evidence keeps exact held-text offsets. A citation alone cannot be a predicate.
    current=[]
    for n,frag in enumerate(corpus.get('current_law',{}).get(iid,[])):
        current.append(frag)
        if isinstance(frag,dict) and frag.get('evidence_gap'):
            missing.append(frag['evidence_gap'])
        if isinstance(frag,dict) and all(k in frag for k in ('text','char_start','char_end','source')):
            key=f'CURRENT:{iid}#{n}'
            evidence[key]=dict(frag,id=key)
    searches=[]
    for item in d.get('proposals',{}).get('later_source_search_machine',[]):
        sid=item.get('search_id')
        entry=corpus['machine_searches'].get(sid)
        if entry:
            searches.append(dict(item, **{k:v for k,v in entry.items() if k!='search_id'}))
    missing=list(missing)
    if not rec: missing.append('No attributed held text located for this order.')
    elif not rec.get('acceptable_as_original'):
        missing.append('Held representation is a lead; complete official original requires confirmation/acquisition.')
    if not clauses: missing.append('No clause inventory extracted; do not submit an empty inventory.')
    if not searches: missing.append('No complete machine later-source search available.')
    if corpus['statuses'].get(iid)=='yes':
        missing.append('Current legal predicate and coverage through 2026-10-14 require judgment; a citation or 1989 snapshot cannot prove continuation.')
    dossier={'schema':'eo-claim-kit-dossier/v1','instrument_id':iid,
        'whole_order_status':corpus['statuses'].get(iid), 'legal_cutoff':CUTOFF,
        'original_source_id':original_id,'clauses':clauses,'evidence':evidence,
        'own_terms':[k for k in evidence if k.startswith('TERM:')],
        'actor_contexts':actor_contexts,
        'actor_provisions':[k for k in evidence if k.startswith('ACT:') and ':effective#' not in k],
        'chain':chain_rec,'current_law_leads':current,'machine_searches':searches,
        'draft_gate_errors':d.get('gate',{}).get('errors_now',[]),
        'conflicts':d.get('conflicts',[]),
        'draft_material_gaps':draft.get('claim',{}).get('unresolved_material_gaps',[]),
        'missing':sorted(set(missing)),
        'notice':'MACHINE LEADS ONLY. No segmentation, date, source grade, family or chain is a legal conclusion.'}
    if iid in corpus.get('status_histories',{}):
        dossier['status_history']=corpus['status_histories'][iid]
    dossier['fingerprint']=canonical_sha(dossier)
    return dossier

def build(repo, out, cache=None):
    started=time.monotonic();repo=Path(repo).resolve();out=Path(out).resolve()
    if out==repo or not out.is_relative_to(repo):
        raise ValueError('OUTPUT_DIR must be a child of the repository')
    rel=out.relative_to(repo)
    if rel.parts[0] in {'research','progress','HANDOFF','.github'}:
        raise ValueError('OUTPUT_DIR overlaps protected project inputs')
    if rel.parts[0]=='jobs' and (len(rel.parts)<3 or rel.parts[1]!='claim-kit'):
        raise ValueError('OUTPUT_DIR cannot overwrite another source job')
    if rel.parts[0]=='jobs' and rel.parts[2]!='output':
        raise ValueError('Claim-kit OUTPUT_DIR must be under jobs/claim-kit/output')
    corpus=load_corpus(repo)
    if any((repo/r['text_path']).resolve().is_relative_to(out) for r in corpus['texts']):
        raise ValueError('OUTPUT_DIR overlaps a held text input')
    out.mkdir(parents=True,exist_ok=True)
    universe=corpus['universe'];warnings=list(corpus.get('warnings',[]))
    law_keys=[];law_flat=[]
    for iid,leads in sorted(corpus.get('current_law',{}).items()):
        for lead in leads:law_keys.append(iid);law_flat.append(lead)
    law_enriched=enrich_current(repo,law_flat)
    corpus['current_law']={}
    for iid,lead in zip(law_keys,law_enriched):corpus['current_law'].setdefault(iid,[]).append(lead)
    selected={};segments={};terms={};primary_acts={};all_mentions=[];all_variants=collections.defaultdict(dict);all_terms=collections.defaultdict(dict);generic_refs=set();missing_by=collections.defaultdict(list)
    counts=collections.Counter(universe_orders=len(universe),decided_orders=len(corpus['statuses']))
    # Persistent cache is optional, never an output/provenance substitute. Hash includes parser code.
    code_hash=hashlib.sha256(Path(__file__).with_name('excavate.py').read_bytes()).hexdigest()
    cache_path=Path(cache).resolve() if cache else None
    if cache_path:cache_path.mkdir(parents=True,exist_ok=True)
    cache_hits=0
    text_records=sorted(corpus['texts'],key=lambda r:(rank_text(r),r['instrument_id']))
    with (out/'TEXT_CLAUSES.jsonl').open('w',encoding='utf-8') as all_clauses:
        for r in text_records:
            iid=r['instrument_id']
            if iid not in universe:continue
            try:text=safe_read(repo,r['text_path'])
            except (OSError,ValueError,UnicodeError) as e:
                missing_by[iid].append('Missing/unreadable held text: '+r['text_path']+' ('+type(e).__name__+')');counts['text_read_failures']+=1;continue
            if not text.strip():counts['empty_texts']+=1;continue
            source=dict(r['source'],text_path=r['text_path'],text_sha256=hashlib.sha256(text.encode()).hexdigest())
            key=canonical_sha({'parser':code_hash,'iid':iid,'source':source,'signing':r.get('signing_date'),'filing':r.get('filing_date')})
            cp=cache_path/(key+'.json') if cache_path else None
            data=None
            if cp and cp.exists():
                try:data=json.loads(cp.read_text('utf-8'));cache_hits+=1
                except (ValueError,OSError):pass
            if data is None:
                c=segment(iid,text,source)
                ts=own_terms(iid,text,source,c.get('clauses',[]))
                ms=discover_mentions(iid,text,source,r.get('signing_date'),r.get('filing_date'))
                data={'clauses':c,'terms':ts,'mentions':ms}
                if cp:dump(cp,data)
            line(all_clauses,data['clauses'])
            for term in data['terms']:
                term=dict(term)
                term['id']=(term.get('id') or f'TERM:{iid}#'+str(term['char_start']))+'@'+source['text_sha256'][:16]
                all_terms[iid][term['id']]=term
            if generic_reference_count(text):generic_refs.add((iid,source['text_sha256'],generic_reference_count(text)))
            counts['held_texts_scanned']+=1
            if iid not in selected:
                selected[iid]=dict(r,source=source,text=text)
                segments[iid]=data['clauses']
            all_mentions.extend(dict(a,_representation_rank=rank_text(r)) for a in data['mentions'])
    terms={iid:list(values.values()) for iid,values in all_terms.items()}
    for iid,rec in sorted(selected.items()):
        if len(rec['text'].encode('utf-8'))>50000:
            dump(out/'actor-texts'/(filename(iid)+'.json'),{'instrument_id':iid,'source':rec['source'],'text':rec['text'],'notice':'Shared full held text; lead only.'})
    # Every known target/actor pair, plus explicitly named changes discovered in every held text.
    pairs={(p['target_id'],p['actor_id'],p.get('parent_id')):p for p in corpus['pairs'] if p.get('target_id') in universe}
    for a in all_mentions:
        target,actor=a.get('target_id'),a.get('actor_id')
        if target not in universe or actor not in universe or target==actor:continue
        variant={k:v for k,v in a.items() if not k.startswith('_')}
        variant['id']='ACT:'+target+'>'+actor+'@'+canonical_sha(variant)[:16]
        all_variants[(target,actor)][variant['id']]=variant
        key=(target,actor,None);pairs.setdefault(key,{'target_id':target,'actor_id':actor})
        if key not in primary_acts or a['_representation_rank']<primary_acts[key]['_representation_rank']:
            primary_acts[key]=a
    generic_total=sum(n for _,_,n in generic_refs)
    # Parent-as-amended is a separately identified indirect LEAD, never a legal inference of target termination.
    parents=collections.defaultdict(set)
    for a in all_mentions:
        if a.get('verb')=='amend' and a.get('actor_id') in selected and a.get('target_id') in universe:
            parents[a['target_id']].add(a['actor_id'])
    for a in list(primary_acts.values()):
        if re.search(r'\bas\s+amended\b',a.get('provision_text',''),re.I):
            for child in parents.get(a.get('target_id'),set()):
                if child!=a['actor_id']:
                    pairs.setdefault((child,a['actor_id'],a['target_id']),{'target_id':child,'actor_id':a['actor_id'],'parent_id':a['target_id']})
    actors_by=collections.defaultdict(list);missing_sources=[];located_pairs={}
    for key,p in sorted(pairs.items(),key=lambda kv:str(kv[0])):
        target,actor,parent=key
        if actor not in universe:
            missing_by[target].append('Acting identity absent from census: '+actor);continue
        ar=selected.get(actor)
        a=None
        if ar:
            a=acting_provision(target,actor,ar['text'],ar['source'],ar.get('signing_date'),ar.get('filing_date'),parent_id=parent)
        if not a:a=primary_acts.get(key)
        if a and a.get('provision_text'):
            pair=(target,actor)
            a={k:v for k,v in a.items() if not k.startswith('_')}
            if pair not in located_pairs or (not parent and not a.get('reaches_target_via')):
                located_pairs[pair]=a
        else:
            row={'target_id':target,'actor_id':actor,'parent_id':parent,'reason':'acting text absent' if not ar else 'target provision not located','source_event':p.get('source_event')}
            missing_sources.append(row);missing_by[target].append(row['reason']+': '+actor)
    for (target,actor),a in sorted(located_pairs.items()):
        a['alternative_provisions']=list(all_variants.get((target,actor),{}).values())
        actors_by[target].append(a)
    with (out/'ACTING_REPRESENTATIONS.jsonl').open('w',encoding='utf-8') as fh:
        for pair,values in sorted(all_variants.items()):
            for variant in values.values():line(fh,variant)
    counts['known_pairs']=len({(t,a) for t,a,_ in pairs});counts['located_actor_pairs']=sum(map(len,actors_by.values()))
    counts['orders_with_held_text']=len(selected);counts['generic_references_excluded']=generic_total
    families=collections.defaultdict(set)
    index=[]
    with (out/'CLAUSES.jsonl').open('w',encoding='utf-8') as cf, (out/'OWN_TERMS.jsonl').open('w',encoding='utf-8') as tf, (out/'ACTING_PROVISIONS.jsonl').open('w',encoding='utf-8') as af, (out/'CHAINS.jsonl').open('w',encoding='utf-8') as chf, (out/'STATUS_LEADS.jsonl').open('w',encoding='utf-8') as sf:
        for iid in sorted(universe):
            c=segments.get(iid)
            if c:line(cf,c)
            ts=terms.get(iid,[])
            for t in ts:line(tf,t)
            acts=actors_by.get(iid,[])
            for a in acts:
                line(af,a)
                families['actor:'+a['actor_id']].add(iid)
                if a.get('reaches_target_via'):families['parent:'+str(a['reaches_target_via'])].add(iid)
            for t in ts:
                families['own_term:'+t['kind']].add(iid)
            if iid in selected:
                src=selected[iid]['source']
                families['source:'+str(src.get('sha256') or src.get('url'))].add(iid)
            chain_rec=chain(iid,acts,generic_refs_excluded=generic_total)
            line(chf,chain_rec)
            if iid not in corpus['statuses']:
                line(sf,{'instrument_id':iid,'status':None,'lead_actor_ids':sorted({a['actor_id'] for a in acts}),'own_terms':ts,'has_held_text':iid in selected,'current_law_leads':corpus.get('current_law',{}).get(iid,[]),'status_history':corpus.get('status_histories',{}).get(iid),'missing':missing_by[iid],'notice':'Separate status-lead queue. Does not decide or write a status.'})
                continue
            dossier=package(iid,corpus,selected,c,ts,acts,chain_rec,missing_by[iid])
            name=filename(iid)
            dump(out/'dossiers'/(name+'.json'),dossier)
            dump(out/'sheets'/(name+'.decision.json'),blank_sheet(dossier))
            index.append({'instrument_id':iid,'status':corpus['statuses'][iid], 'dossier':'dossiers/'+name+'.json','clauses':len(dossier['clauses']),'actors':len(acts),'missing':len(dossier['missing']),'conflicts':len(dossier['conflicts']),'fingerprint':dossier['fingerprint']})
    decided=set(corpus['statuses']);family_rows=[]
    for key,ids in families.items():
        ids=sorted(ids&decided)
        if ids:family_rows.append({'family_id':key,'orders_unlocked':len(ids),'instrument_ids':ids})
    family_rows.sort(key=lambda x:(-x['orders_unlocked'],x['family_id']))
    # Same-actor single-clause tables are review conveniences, with blank decisions.
    for fam in family_rows:
        if not fam['family_id'].startswith('actor:'):continue
        members=[iid for iid in fam['instrument_ids'] if len(segments.get(iid,{}).get('clauses',[]))==1]
        if len(members)<2:continue
        actor=fam['family_id'].split(':',1)[1]
        with (out/(filename(actor)+'_BATCH_REVIEW.csv')).open('w',encoding='utf-8',newline='') as fh:
            w=csv.writer(fh);w.writerow(['instrument_id','dossier','scope_id','actor_id','state','end_id','effective_date','savings','reason','reviewer_decision'])
            for iid in members:
                w.writerow([iid,'dossiers/'+filename(iid)+'.json',segments[iid]['clauses'][0]['scope_id'],actor,'','','','','',''])
    dump(out/'INDEX.json',index);dump(out/'FAMILIES.json',family_rows)
    with (out/'MISSING_SOURCES.jsonl').open('w',encoding='utf-8') as fh:
        for row in missing_sources:line(fh,row)
    # Assemble committed producer decision sheets. Never writes claims/, statuses, or reviews.
    assembly=[];accepted=0
    with (out/'ASSEMBLED_CLAIMS.jsonl').open('w',encoding='utf-8') as fh:
        for path in sorted((repo/'research/readiness/decisions').glob('*/*.json')):
            try:
                sheet=json.loads(path.read_text('utf-8'))
                if not isinstance(sheet,dict):raise ValueError('Decision sheet must be a JSON object')
                iid=sheet.get('instrument_id')
                if not isinstance(iid,str):raise ValueError('Decision instrument_id must be a string')
                if iid not in corpus['statuses']:raise ValueError('No current provisional status for '+str(iid))
                dp=out/'dossiers'/(filename(iid)+'.json')
                dossier=json.loads(dp.read_text('utf-8'))
                claim,errors=assemble(sheet,dossier,repo)
                assembly.append({'sheet':str(path.relative_to(repo)),'instrument_id':iid,'errors':errors})
                if not errors:line(fh,claim);accepted+=1
            except (ValueError,KeyError,TypeError,OSError) as e:
                assembly.append({'sheet':str(path.relative_to(repo)),'errors':[type(e).__name__+': '+str(e)]})
    dump(out/'ASSEMBLY_REPORT.json',assembly)
    counts.update(dossiers=len(index),status_leads=len(universe)-len(decided),families=len(family_rows),assembled_claims=accepted)
    summary={'schema':'eo-claim-kit-summary/v1','counts':dict(sorted(counts.items())), 'baseline_expected':{'universe':14972,'decided':3359},'warnings':warnings,'lead_only':True,'legal_cutoff':CUTOFF}
    dump(out/'SUMMARY.json',summary)
    dump(out/'METRICS.json',{'wall_seconds':round(time.monotonic()-started,3),'cache_hits':cache_hits,'output_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())})
    print(json.dumps(summary['counts'],sort_keys=True))
    return summary
