"""Pinned, lossless family work packages and explicit compact decision rows.

This module prepares work and calls the existing assembler. It neither decides
law nor publishes claims/statuses. All failed/blocked members remain in reports.
"""
from collections import Counter,defaultdict
from copy import deepcopy
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from assemble import blank_sheet,assemble,check_claim,canonical_sha
from build import filename

SCHEMA='eo-claim-kit-work-package/v1'
ROW_FIELDS=['instrument_id','dossier_sha256','agent','outcome','approved','original_confirmed',
 'original_pages_confirmed','inventory_confirmed','research_rationale','savings_state','savings_source_id',
 'savings_reason','search_ids','conflict_resolutions','unresolved_material_gaps','earlier_end_check',
 'scope_check','independent_command_check','savings_check']
CLAUSE_FIELDS=['instrument_id','scope_id','clause_id','state','end_id','effective_date',
 'effective_date_confirmed','current_basis_id','current_legal_basis','checked_through',
 'later_event_ids','later_events','reason','inventory_source_id','inventory_char_start',
 'inventory_char_end','inventory_reason']
TAG='@eo:'

def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(v):return hashlib.sha256(v).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
def safe(root,rel):
    p=(root/rel).resolve()
    if not p.is_relative_to(root):raise ValueError('path outside repository: '+str(rel))
    return p
def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csv_write(path,fields,values):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(values)


def encode(dossiers,repo):
    """Share exact source dictionaries, source-text ranges and repeated objects.

    Text ranges are merged only within the same actual text hash. Every span is
    verified against the held file before compression. Unverified text stays
    literal; this codec cannot repair or invent evidence.
    """
    repo=Path(repo).resolve();sources={};files={};spans={};candidates=defaultdict(list);issues=[]
    def scan(v):
        if isinstance(v,dict):
            if any(str(k).startswith(TAG) for k in v):raise ValueError('reserved codec key in original dossier')
            s=v.get('source') or v.get('actor_source')
            if isinstance(s,dict) and isinstance(v.get('text'),str) and s.get('text_path') and s.get('text_sha256'):
                rel=s['text_path']
                if rel not in files:
                    try:
                        p=safe(repo,rel)
                        if p.stat().st_size>32_000_000:raise ValueError('parent file exceeds inline validation bound')
                        raw=p.read_bytes();files[rel]=(digest(raw),raw.decode('utf-8'))
                    except (OSError,ValueError,UnicodeError) as exc:
                        files[rel]=None;issues.append({'path':rel,'kind':'held_source_not_loaded','reason':str(exc)})
                loaded=files[rel];a=v.get('char_start',s.get('char_start'));b=v.get('char_end',s.get('char_end'))
                if loaded and loaded[0]==s['text_sha256'] and type(a) is int and type(b) is int and 0<=a<b<=len(loaded[1]) and loaded[1][a:b]==v['text']:
                    spans[id(v)]=(loaded[0],a,b);candidates[loaded[0]].append((a,b,rel))
                else:issues.append({'path':rel,'kind':'text_not_compressed','reason':'source hash/span not exactly verified; original value retained'})
            for child in v.values():scan(child)
        elif isinstance(v,list):
            for child in v:scan(child)
    scan(dossiers);blocks={};ranges=defaultdict(list)
    for sha,entries in sorted(candidates.items()):
        merged=[]
        for a,b,rel in sorted(entries):
            if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1]);merged[-1][3].add(rel)
            else:merged.append([a,b,rel,{rel}])
        for a,b,rel,aliases in merged:
            key='T'+digest((sha+':'+str(a)+':'+str(b)).encode())[:24]
            blocks[key]={'text_sha256':sha,'char_start':a,'char_end':b,'paths':sorted(aliases),'text':files[rel][1][a:b]}
            ranges[sha].append((a,b,key))
    def special(v):
        if isinstance(v,dict):
            out={}
            for k,value in v.items():
                if k in ('source','actor_source') and isinstance(value,dict):
                    sid='S'+digest(canon(value).encode())[:24];sources[sid]=deepcopy(value);out[k]={TAG+'source':sid}
                elif k=='text' and id(v) in spans:
                    sha,a,b=spans[id(v)];lo,hi,key=next(r for r in ranges[sha] if r[0]<=a and b<=r[1])
                    out[k]={TAG+'span':[key,a-lo,b-lo]}
                else:out[k]=special(value)
            return out
        if isinstance(v,list):return [special(x) for x in v]
        return v
    tree=special(dossiers);counts=Counter()
    def count(v):
        if isinstance(v,(dict,list)):
            key=canon(v)
            if len(key)>=96:counts[key]+=1
            for child in (v.values() if isinstance(v,dict) else v):count(child)
        elif isinstance(v,str) and len(v)>=96:counts[canon(v)]+=1
    count(tree);shared={}
    def intern(v,top=False):
        key=canon(v)
        use=not top and counts[key]>1 and len(key)>=96
        if use:
            rid='R'+digest(key.encode())[:24]
            if rid not in shared:shared[rid]=intern(v,True)
            return {TAG+'ref':rid}
        if isinstance(v,dict):return {k:intern(x) for k,x in v.items()}
        if isinstance(v,list):return [intern(x) for x in v]
        return v
    packed=intern(tree,True)
    return {'dossiers':packed,'sources':sources,'text_blocks':blocks,'shared_objects':shared,
            'codec_issues':issues,'held_text_file_pins':{p:v[0] for p,v in sorted(files.items()) if v}}


def decode(packet):
    def expand(v,stack=()):
        if isinstance(v,dict):
            if set(v)=={TAG+'source'}:return deepcopy(packet['sources'][v[TAG+'source']])
            if set(v)=={TAG+'span'}:
                key,a,b=v[TAG+'span'];text=packet['text_blocks'][key]['text']
                if not 0<=a<b<=len(text):raise ValueError('invalid text span')
                return text[a:b]
            if set(v)=={TAG+'ref'}:
                key=v[TAG+'ref']
                if key in stack:raise ValueError('cyclic shared object')
                return expand(packet['shared_objects'][key],stack+(key,))
            return {k:expand(x,stack) for k,x in v.items()}
        if isinstance(v,list):return [expand(x,stack) for x in v]
        return v
    dossiers=expand(packet['dossiers'])
    for iid,d in dossiers.items():
        if d.get('instrument_id')!=iid or d.get('fingerprint')!=canonical_sha(d):raise ValueError('reconstructed dossier fingerprint mismatch: '+iid)
    return dossiers


def owners(repo):
    result={}
    for p in sorted((repo/'research/readiness/claims').glob('*.jsonl')):
        for n,line in enumerate(p.read_text('utf-8').splitlines(),1):
            if not line.strip():continue
            r=json.loads(line);iid=r.get('instrument_id')
            if iid:result[iid]={'owner':p.stem,'path':p.relative_to(repo).as_posix(),'line':n,'claim_sha256':canonical_sha(r)}
    # These frozen proposals are owned even when their branch is not yet merged.
    freeze=repo/'research/production/claim-kit-pilot-2026-10-18/FREEZE_MANIFEST.json'
    if freeze.exists():
        for r in json.loads(freeze.read_bytes()).get('accepted',[]):
            result.setdefault(r['instrument_id'],{'owner':'sol-2026-10-18','path':str(freeze.relative_to(repo)),
                'claim_sha256':r.get('canonical_claim_sha256'),'role':'frozen upstream proposal'})
    return result


def preflight(d,repo):
    """Conservative mechanical gaps; later legal inability is a separate outcome."""
    iid=d['instrument_id'];tasks=[]
    def add(kind,key,reason,state='research_required'):
        tasks.append({'task_id':'TASK:'+digest((kind+'|'+key).encode())[:24],'kind':kind,
                      'shared_key':key,'instrument_id':iid,'reason':reason,'availability':state})
    original=d.get('evidence',{}).get(d.get('original_source_id'),{})
    if not original:add('official_original',iid,'No original evidence in dossier','absent_from_packet')
    elif original.get('acceptable_as_original') is False:add('official_original',iid,'Held representation is a lead','held_lead_not_official_original')
    if original.get('requires_page_check'):
        s=original.get('source',{});add('official_page_image',str(s.get('sha256') or s.get('url') or iid),
            'Explicit original page/image confirmation still required','held_text_images_not_confirmed')
    for r in d.get('actor_contexts',[]):
        if r.get('overflow'):
            p=repo/'jobs/claim-kit/output'/r['overflow']
            add('load_actor_overflow',r['actor_id'],'Read full overflow before scope/savings decision',
                'held_not_loaded' if p.exists() else 'absent_from_checkout')
    for r in d.get('current_law_leads',[]):
        if isinstance(r,dict) and r.get('evidence_gap'):
            key=canon({k:r.get(k) for k in ('source','citation','url','text_path','basis_code') if r.get(k)}) or iid
            add('operative_current_law',key,r['evidence_gap'],'citation_or_pointer_only')
    for text in d.get('missing',[]):
        if 'acting text absent:' in text:add('acting_original',text.split(': ',1)[-1],text,'absent_from_packet')
        elif 'target provision not located:' in text:add('locate_held_provision',text.split(': ',1)[-1],text,'held_not_loaded')
    for eid in d.get('own_terms',[]):
        r=d['evidence'].get(eid,{})
        if r.get('kind') in ('report_deadline','condition'):
            add('actual_event_fact',iid+':'+eid,'Determine actual report/transfer/completion fact; a deadline/condition is not proof it happened')
    if not d.get('clauses'):add('complete_inventory',iid,'No complete operative inventory located','absent_from_packet')
    return {'instrument_id':iid,'mechanical_tasks':tasks,'evidence_preflight':'blocked_or_research' if tasks else 'no_known_mechanical_gap',
        'decisions_still_required':['complete original/inventory','earlier ending','partial scope and effective date',
             'independent commands','savings/residuals','contrary evidence and cutoff predicate'],
        'notice':'No known gap is not a legal-readiness finding. Review may expose new facts.'}


def family_groups(dossiers):
    groups=defaultdict(list)
    literal_counts=Counter((e.get('actor_id'),canon(e.get('source')),e.get('text'))
        for d in dossiers.values() for eid in d.get('actor_provisions',[])
        for e in [d['evidence'].get(eid,{})] if e.get('text'))
    for iid,d in dossiers.items():
        seen=set()
        for eid in d.get('actor_provisions',[]):
            e=d['evidence'].get(eid,{})
            if not e.get('text') or not e.get('source'):continue
            s=e['source'];text=e['text']
            # Normalize only the named target number. Everything else, including
            # exceptions, provision scope and operative wording, must agree.
            target=iid.split(':',1)[-1]
            pattern=text if literal_counts[(e.get('actor_id'),canon(s),text)]>1 else re.sub(r'(?<![\w.-])'+re.escape(target)+r'(?![\w.-])','<TARGET>',text)
            key={'actor_id':e.get('actor_id'),'source_sha256':s.get('sha256'),
                'text_sha256':s.get('text_sha256'),'operative_pattern_sha256':digest(pattern.encode()),
                'scope':e.get('scope'),'reaches_target_via':e.get('reaches_target_via'),
                'exception_terms':sorted(set(re.findall(r'\b(?:except|unless|provided|in part|subject to|as amended)\b',text,re.I)))}
            gid='FAMILY:'+digest(canon(key).encode())[:24]
            if gid in seen:continue
            groups[gid].append({'instrument_id':iid,'evidence_id':eid,'shared_evidence':key});seen.add(gid)
    return [{'family_id':gid,'members':members,'orders':len({m['instrument_id'] for m in members}),
             'notice':'Shared evidence only. Every target requires its own earlier-end/scope/independent-command/savings checks.'}
            for gid,members in sorted(groups.items(),key=lambda x:(-len(x[1]),x[0]))]


def load_packet(folder,repo,check_sources=True):
    packet=json.loads((folder/'PACKET.json').read_bytes());fp=packet.pop('fingerprint',None)
    if packet.get('schema')!=SCHEMA or digest(canon(packet).encode())!=fp:raise ValueError('changed work package')
    packet['fingerprint']=fp;dossiers=decode(packet)
    if check_sources:
        for rel,sha in packet['held_text_file_pins'].items():
            if file_sha(safe(repo,rel))!=sha:raise ValueError('changed held source: '+rel)
    return packet,dossiers


def render(packet,dossiers):
    """Readable source-once view; the lossless packet is always beside it."""
    lines=['# Pinned family work package','', 'Research preparation. No family approval, legal status or human certification.',
      'Read each common source independently, then record every member-specific check.',
      'Full lossless evidence and metadata: PACKET.json. Missing/overflow records are retained below.','',
      '## Source catalogue','']
    for sid,s in sorted(packet['sources'].items()):
        lines.append('- **'+sid+'**: '+str(s.get('url') or s.get('archival_id') or 'no URL'))
        lines.append('  '+canon(s))
    lines.extend(['','## Shared source texts',''])
    for tid,b in sorted(packet['text_blocks'].items()):
        lines.extend(['### '+tid,'',f"Text hash {b['text_sha256']}; absolute characters {b['char_start']}–{b['char_end']}; files: "+', '.join(b['paths']),''])
        fence='`'*max(3,max((len(m[0])+1 for m in re.finditer(r'`+',b['text'])),default=3))
        lines.extend([fence+'text',b['text'],fence,''])
    # Text lacking attributable spans is never silently dropped by the renderer.
    rendered_text={b['text'] for b in packet['text_blocks'].values()}
    for iid,d in dossiers.items():
        lines.extend(['## '+iid,'', 'Fingerprint: '+d['fingerprint']+'; provisional status: '+str(d['whole_order_status']),
            'Ownership/routing: '+canon(packet['ownership'].get(iid,{})),
            'Required member checks: earlier ending; scope; independent commands; savings.','',
            '### Evidence index',''])
        for eid,e in d.get('evidence',{}).items():
            meta={k:v for k,v in e.items() if k not in ('text','source','actor_source','provision_text','alternative_provisions')}
            source=e.get('source') or e.get('actor_source')
            sid='S'+digest(canon(source).encode())[:24] if isinstance(source,dict) else None
            lines.append('- **'+eid+'**; '+str(sid)+'; '+canon(meta))
            text=e.get('text')
            if isinstance(text,str) and text and not any(text in full for full in rendered_text):
                lines.extend(['  Exact retained record text (unshared):',text]);rendered_text.add(text)
        lines.extend(['','### Complete operative inventory',''])
        for c in d.get('clauses',[]):lines.append('- '+c['scope_id']+' → '+str(c.get('id'))+'; characters '+str(c.get('char_start'))+'–'+str(c.get('char_end')))
        for key in ('own_terms','actor_contexts','actor_provisions','chain','current_law_leads','machine_searches',
                    'draft_gate_errors','conflicts','draft_material_gaps','missing','status_history','notice'):
            if key in d:lines.extend(['','### '+key,'',canon(d[key])])
        remaining={k:v for k,v in d.items() if k not in {'schema','instrument_id','whole_order_status','fingerprint',
            'legal_cutoff','original_source_id','clauses','evidence','own_terms','actor_contexts','actor_provisions',
            'chain','current_law_leads','machine_searches','draft_gate_errors','conflicts','draft_material_gaps',
            'missing','status_history','notice'}}
        if remaining:lines.extend(['','### Additional dossier metadata','',canon(remaining)])
        lines.extend(['','### Preflight','',canon(packet['preflight'][iid]),''])
    lines.extend(['## Shared tasks','',canon(packet['shared_tasks']),'','## Explicit overflow and codec warnings','',canon(packet['codec_issues'])])
    return '\n'.join(lines)+'\n'


def prepare(repo,out,dest,ids,agent,dossier_paths=None,replacement_proposal=False):
    started=time.monotonic();repo=Path(repo).resolve();out=Path(out).resolve();dest=Path(dest).resolve()
    if dest.exists():raise ValueError('prepare destination exists; refusing overwrite')
    if not dest.is_relative_to(repo/'research') or not 1<=len(ids)<=50 or len(set(ids))!=len(ids):raise ValueError('bounded distinct IDs and research destination required')
    owned=owners(repo);locks_path=repo/'research/readiness/CLAIM_KIT_LOCK.json'
    locks=json.loads(locks_path.read_bytes()).get('orders',{}) if locks_path.exists() else {}
    dossiers={};pins={};routing={};flight={};shared={}
    for iid in ids:
        p=Path(dossier_paths[iid]) if dossier_paths else out/'dossiers'/(filename(iid)+'.json')
        d=json.loads(p.read_bytes())
        if d.get('instrument_id')!=iid or d.get('fingerprint')!=canonical_sha(d):raise ValueError('stale dossier '+iid)
        if iid in locks and locks[iid].get('agent')!=agent:raise ValueError('reservation belongs to '+str(locks[iid].get('agent'))+': '+iid)
        if iid in owned and not replacement_proposal:raise ValueError('route existing claim to owner or explicitly prepare replacement proposal: '+iid)
        dossiers[iid]=d;pins[iid]={'file_sha256':file_sha(p),'fingerprint':d['fingerprint'],'path':str(p.relative_to(repo))}
        routing[iid]={**owned.get(iid,{}),'route':'owner_reviewable_replacement_proposal' if iid in owned else 'new_producer_proposal'}
        flight[iid]=preflight(d,repo)
        for task in flight[iid]['mechanical_tasks']:
            entry=shared.setdefault(task['task_id'],{k:v for k,v in task.items() if k not in ('instrument_id','reason')})
            entry.setdefault('affected_orders',[]).append(iid);entry.setdefault('reasons',[]).append(task['reason'])
    encoded=encode(dossiers,repo)
    packet={'schema':SCHEMA,'legal_cutoff':'2026-10-14','agent':agent,'input_pins':pins,
        'codec_code_sha256':file_sha(Path(__file__)),'assembler_code_sha256':file_sha(Path(__file__).with_name('assemble.py')),
        'ownership':routing,'preflight':flight,'families':family_groups(dossiers),'shared_tasks':list(shared.values()),**encoded}
    if decode(packet)!=dossiers:raise ValueError('lossless reconstruction failed')
    packet['fingerprint']=digest(canon(packet).encode());dest.mkdir(parents=True)
    dump(dest/'PACKET.json',packet)
    (dest/'READ.md').write_bytes(render(packet,dossiers).encode())
    decisions=[];clauses=[]
    for iid,d in dossiers.items():
        sheet=blank_sheet(d,agent)
        decisions.append({**{k:'' for k in ROW_FIELDS},'instrument_id':iid,'dossier_sha256':d['fingerprint'],'agent':agent,
            'outcome':'unresolved','approved':'false','original_confirmed':'false','original_pages_confirmed':'false',
            'inventory_confirmed':'false','search_ids':'[]','conflict_resolutions':'{}','unresolved_material_gaps':canon(sheet['unresolved_material_gaps'])})
        for c in sheet['clauses']:
            row={k:'' for k in CLAUSE_FIELDS};row.update(instrument_id=iid)
            for k,v in c.items():row[k]=canon(v) if isinstance(v,(list,dict,bool)) else ('' if v is None else v)
            clauses.append(row)
    csv_write(dest/'decisions.csv',ROW_FIELDS,decisions);csv_write(dest/'clauses.csv',CLAUSE_FIELDS,clauses)
    dump(dest/'RATIONALES.json',{})
    metrics={'orders':len(ids),'source_files_validated':len(packet['held_text_file_pins']),
        'input_pretty_json_bytes':sum(len((json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()) for d in dossiers.values()),
        'lossless_packet_json_bytes':(dest/'PACKET.json').stat().st_size,'readable_view_bytes':(dest/'READ.md').stat().st_size,
        'round_trip_exact':True,'shared_text_blocks':len(packet['text_blocks']),'source_catalogue_entries':len(packet['sources']),
        'known_mechanical_tasks':len(shared),'bounded_preparation_seconds':round(time.monotonic()-started,4),
        'model_tokens':None,'no_legal_outcomes_inferred':True}
    dump(dest/'PREPARE.json',metrics);return metrics


def boolean(v):
    if v not in ('true','false'):raise ValueError('explicit true/false required')
    return v=='true'
def json_field(v,kind):
    r=json.loads(v)
    if not isinstance(r,kind):raise ValueError('wrong JSON field type')
    return r
def rationale(v,shared):
    if v.startswith('@rationale:'):
        key=v.split(':',1)[1]
        if not isinstance(shared.get(key),str) or not shared[key].strip():raise ValueError('missing shared rationale: '+key)
        return shared[key]
    return v


def apply(repo,folder,write):
    started=time.monotonic();repo=Path(repo).resolve();folder=Path(folder).resolve();write=Path(write).resolve()
    if write.exists():raise ValueError('apply destination exists; refusing overwrite')
    if not write.is_relative_to(folder):raise ValueError('apply results must stay under frozen work package; no automatic publication')
    packet,dossiers=load_packet(folder,repo)
    if packet['assembler_code_sha256']!=file_sha(Path(__file__).with_name('assemble.py')):raise ValueError('assembler changed; prepare a reviewed package')
    order_rows=rows(folder/'decisions.csv');clause_rows=rows(folder/'clauses.csv');shared=json.loads((folder/'RATIONALES.json').read_bytes())
    counts=Counter(r.get('instrument_id') for r in order_rows)
    if set(counts)!=set(dossiers) or any(n!=1 for n in counts.values()):raise ValueError('decision rows must name every packet member exactly once')
    by=defaultdict(list)
    for c in clause_rows:
        if c['instrument_id'] not in dossiers:raise ValueError('clause row outside packet')
        by[c['instrument_id']].append(c)
    write.mkdir(parents=True);report=[];claims=[]
    for r in order_rows:
        iid=r['instrument_id'];errors=[];claim=None;sheet=None
        try:
            if r['dossier_sha256']!=dossiers[iid]['fingerprint']:raise ValueError('stale decision fingerprint')
            if r['outcome'] not in ('submit','unresolved','blocked','route_owner'):raise ValueError('explicit outcome required')
            if r['outcome']!='submit':
                report.append({'instrument_id':iid,'outcome':r['outcome'],'errors':[],
                    'remaining_gaps':json_field(r['unresolved_material_gaps'],list),'ownership':packet['ownership'][iid]});continue
            sheet=blank_sheet(dossiers[iid],r['agent'])
            for k in ('approved','original_confirmed','original_pages_confirmed','inventory_confirmed'):sheet[k]=boolean(r[k])
            checks={k:rationale(r[k],shared) for k in ('earlier_end_check','scope_check','independent_command_check','savings_check')}
            if any(not v.strip() for v in checks.values()):raise ValueError('every member-specific legal check requires substantive rationale')
            sheet['research_rationale']=rationale(r['research_rationale'],shared)+'\nMember checks: '+canon(checks)
            sheet['savings']={'state':r['savings_state'] or None,'source_id':r['savings_source_id'] or None,'reason':rationale(r['savings_reason'],shared)}
            sheet['search_ids']=json_field(r['search_ids'],list);sheet['conflict_resolutions']=json_field(r['conflict_resolutions'],dict)
            sheet['unresolved_material_gaps']=json_field(r['unresolved_material_gaps'],list);sheet['clauses']=[];overrides=[]
            correction=any(c['inventory_source_id'] for c in by[iid])
            for c in by[iid]:
                clause={k:(c[k] or None) for k in ('scope_id','clause_id','state','end_id','effective_date','current_basis_id','current_legal_basis','checked_through')}
                clause.update(effective_date_confirmed=boolean(c['effective_date_confirmed'] or 'false'),
                    later_event_ids=json_field(c['later_event_ids'] or '[]',list),later_events=json_field(c['later_events'] or '[]',list),reason=rationale(c['reason'],shared))
                if correction:
                    overrides.append({'scope_id':c['scope_id'],'source_id':c['inventory_source_id'],
                        'char_start':int(c['inventory_char_start']),'char_end':int(c['inventory_char_end']),
                        'reason':rationale(c['inventory_reason'],shared)})
                    clause.pop('clause_id',None)
                sheet['clauses'].append(clause)
            sheet['inventory_overrides']=overrides
            claim,errors=assemble(sheet,dossiers[iid],repo)
            if not errors:claims.append(claim)
        except (ValueError,OSError,KeyError,TypeError) as exc:errors=[type(exc).__name__+': '+str(exc)]
        if sheet:dump(write/'decisions'/(filename(iid)+'.json'),sheet)
        report.append({'instrument_id':iid,'outcome':'assembled_proposal' if not errors else 'rejected',
            'errors':errors,'ownership':packet['ownership'][iid],'claim_sha256':canonical_sha(claim) if claim and not errors else None})
    with (write/'CLAIMS.proposed.jsonl').open('w',encoding='utf-8',newline='\n') as f:
        for c in claims:f.write(canon(c)+'\n')
    summary={'schema':'eo-claim-kit-batch-apply/v1','packet_fingerprint':packet['fingerprint'],
        'apply_code_sha256':file_sha(Path(__file__)),
        'counts':dict(Counter(r['outcome'] for r in report)),'total_packet_members':len(dossiers),
        'wall_seconds':round(time.monotonic()-started,4),'extraction_calls':0,'source_file_hashes_checked':len(packet['held_text_file_pins']),
        'claims_published':0,'statuses_published':0,'owner_acceptance_required_for_replacements':True}
    dump(write/'AUDIT.json',report);dump(write/'SUMMARY.json',summary);return summary


def check(repo,folder,applied,actual=True):
    repo=Path(repo).resolve();folder=Path(folder).resolve();applied=Path(applied).resolve();packet,dossiers=load_packet(folder,repo)
    audit=json.loads((applied/'AUDIT.json').read_bytes());claim_rows=[];errors=[]
    for n,l in enumerate((applied/'CLAIMS.proposed.jsonl').read_text('utf-8').splitlines(),1):
        if not l.strip():continue
        c=json.loads(l);iid=c['instrument_id'];es=check_claim(c,repo,dossiers.get(iid))
        claim_rows.append({'instrument_id':iid,'line':n,'errors':es,'claim_sha256':canonical_sha(c)})
        errors.extend(es)
    result={'schema':'eo-claim-kit-batch-check/v1','packet_members':len(dossiers),'claims_checked':len(claim_rows),
        'strict_claim_pass':sum(not r['errors'] for r in claim_rows),'strict_claim_fail':sum(bool(r['errors']) for r in claim_rows),
        'outcomes_including_blocked':dict(Counter(r['outcome'] for r in audit)),
        'actionable_failures':[{'instrument_id':r['instrument_id'],'errors':r['errors']} for r in audit if r['errors']],
        'requires_actual_claim_checker':True,'independent_human_certifications':0}
    if actual and claim_rows:
        script=repo/'jobs/claim-checker/checker.py'
        if not script.exists():raise ValueError('actual claim-checker code unavailable')
        target=applied/'actual-checker';target.mkdir(exist_ok=True)
        env=dict(os.environ,REPO_ROOT=str(repo),OUTPUT_DIR=str(target),JOB_LIMIT='',
                 JOB_CACHE_DIR=str(folder/'.validation-cache'),CLAIM_CHECKER_VERIFY_DOWNLOADS='0',PYTHONIOENCODING='utf-8')
        with (applied/'CHECKER.log').open('w',encoding='utf-8') as log:
            run=subprocess.run([sys.executable,'-B',str(script),'--claims',str(applied/'CLAIMS.proposed.jsonl')],
                               cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
        if run.returncode:raise ValueError('actual claim-checker failed; inspect '+str(applied/'CHECKER.log'))
        actual_summary=json.loads((target/'SUMMARY.json').read_bytes())
        result['actual_claim_checker']={k:actual_summary.get(k) for k in ('claims_checked','claims_all_checks_passed',
            'claims_mechanical_pass','claims_mechanical_unverified','claims_mechanical_fail','claims_gate_passed')}
        result['requires_actual_claim_checker']=False
        result['actual_checker_full_audit']='actual-checker/'
        result['actual_checker_network_downloads_enabled']=False
    elif actual:
        result['actual_claim_checker']={'claims_checked':0,'notice':'No submitted claims; blocked members remain in outcomes.'}
    result['check_code_sha256']=file_sha(Path(__file__))
    dump(applied/'CHECK_AUDIT.json',claim_rows);dump(applied/'CHECK_SUMMARY.json',result);return result
