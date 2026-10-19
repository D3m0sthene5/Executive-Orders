"""Independent evidence-only packet audit; never imports production batch code.

Read paths are explicitly bounded to A/dossiers, B/PACKET/READ/PREPARE,
source text paths named by the packet, and code source. Producer artifacts and
decision outputs are deliberately outside this audit's read set.
"""
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
MATCHED=ROOT/'research/excavator/2026-10-18/batch-pilot/matched'
IDS={'EO:12696','EO:12720','EO:12722','EO:12734','EO:12813','EO:12817'}

def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def dump(path,v):path.write_text(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
def docfingerprint(v):return digest(canonical({k:x for k,x in v.items() if k!='fingerprint'}).encode())

def audit(packet_path,read_path,output_prefix):
    start=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    failures=[];warnings=[];details={};read_pins={}
    def loadraw(path):
        raw=path.read_bytes();read_pins[str(path.relative_to(ROOT)).replace('\\','/')]={'bytes':len(raw),'sha256':digest(raw)};return raw
    rawpacket=loadraw(packet_path);rawread=loadraw(read_path)
    packet=json.loads(rawpacket);read=rawread.decode('utf8')
    baseline={}
    baseline_bytes=0;pretty_bytes=0
    for path in sorted((MATCHED/'A/dossiers').glob('*.json')):
        raw=loadraw(path);d=json.loads(raw)
        baseline[d['instrument_id']]=d;baseline_bytes+=len(raw)
        pretty_bytes+=len((json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
    def require(condition,kind,**fields):
        if not condition:failures.append({'kind':kind,**fields})
    require(set(baseline)==IDS,'baseline_cohort_changed')
    require(set(packet['dossiers'])==IDS,'packet_cohort_changed')
    pcopy={k:v for k,v in packet.items() if k!='fingerprint'}
    require(digest(canonical(pcopy).encode())==packet['fingerprint'],'packet_fingerprint')
    reference_counts={'source':0,'span':0,'ref':0}
    # Independent recursive interpreter, with strict singleton tags, index bounds,
    # source/object identity checks and cycle detection. No call to batch.decode.
    def expand(node,chain=()):
        if type(node) is list:return [expand(x,chain) for x in node]
        if type(node) is not dict:return copy.deepcopy(node)
        if len(node)==1:
            tag,value=next(iter(node.items()))
            if tag=='@eo:source':
                reference_counts['source']+=1
                return copy.deepcopy(packet['sources'][value])
            if tag=='@eo:span':
                reference_counts['span']+=1
                block,lo,hi=value;body=packet['text_blocks'][block]['text']
                if type(lo) is not int or type(hi) is not int or not 0<=lo<hi<=len(body):raise ValueError('Invalid independent expansion span')
                return body[lo:hi]
            if tag=='@eo:ref':
                reference_counts['ref']+=1
                if value in chain:raise ValueError('Independent expansion cycle')
                return expand(packet['shared_objects'][value],chain+(value,))
        return {key:expand(value,chain) for key,value in node.items()}
    decoded=expand(packet['dossiers'])
    for eo,d in baseline.items():
        require(decoded.get(eo)==d,'independent_json_value_roundtrip',instrument_id=eo)
        require(docfingerprint(d)==d['fingerprint'],'baseline_fingerprint',instrument_id=eo)
        require(docfingerprint(decoded[eo])==d['fingerprint'],'decoded_fingerprint',instrument_id=eo)
        pin=packet['input_pins'][eo]
        require(pin['fingerprint']==d['fingerprint'],'packet_input_fingerprint',instrument_id=eo)
        sourcepath=(ROOT/pin['path']).resolve()
        require(sourcepath.is_relative_to(ROOT),'input_pin_path_escape',instrument_id=eo)
        require(digest(loadraw(sourcepath))==pin['file_sha256'],'packet_input_file_hash',instrument_id=eo)
    # Verify full file custody separately from inline range correctness.
    source_text={}
    for rel,expected in packet['held_text_file_pins'].items():
        path=(ROOT/rel).resolve()
        require(path.is_relative_to(ROOT),'held_source_path_escape',path=rel)
        raw=loadraw(path);require(digest(raw)==expected,'held_file_hash',path=rel)
        source_text[rel]=raw.decode('utf8')
    for blockid,b in packet['text_blocks'].items():
        require(b['char_end']-b['char_start']==len(b['text']),'block_extent',block=blockid)
        for rel in b['paths']:
            require(rel in source_text,'block_alias_not_pinned',block=blockid,path=rel)
            require(packet['held_text_file_pins'].get(rel)==b['text_sha256'],'block_parent_hash',block=blockid,path=rel)
            require(source_text[rel][b['char_start']:b['char_end']]==b['text'],'block_vs_held_file',block=blockid,path=rel)
    for sid,source in packet['sources'].items():
        require(sid=='S'+digest(canonical(source).encode())[:24],'source_dictionary_identity',source_id=sid)

    # Parse the readable material independently. Fences are treated as literal
    # source content; heading-shaped source lines cannot become dossier headings.
    fence_ranges=[];read_blocks={};source_catalogue={}
    for blockid,b in packet['text_blocks'].items():
        heading='### '+blockid+'\n\n';at=read.find(heading)
        require(at>=0,'readable_block_heading',block=blockid)
        if at<0:continue
        metalo=at+len(heading);metaend=read.find('\n',metalo);metadata=read[metalo:metaend]
        expectedmeta=f"Text hash {b['text_sha256']}; absolute characters {b['char_start']}–{b['char_end']}; files: "+', '.join(b['paths'])
        require(metadata==expectedmeta,'readable_block_metadata',block=blockid)
        opening=re.search(r'^(`{3,})text\n',read[metaend+1:],re.M)
        if opening is None:require(False,'readable_block_fence',block=blockid);continue
        fstart=metaend+1+opening.start();bodylo=metaend+1+opening.end()
        close=re.search(r'^'+re.escape(opening.group(1))+r'\n',read[bodylo:],re.M)
        if close is None:require(False,'readable_block_close',block=blockid);continue
        bodyhi=bodylo+close.start();body=read[bodylo:bodyhi]
        require(body.endswith('\n'),'readable_block_separator',block=blockid)
        body=body[:-1] # remove the renderer's one joining newline, not source whitespace
        require(body==b['text'],'readable_source_text_exact',block=blockid)
        read_blocks[blockid]={**b,'text':body}
        fence_ranges.append((fstart,bodylo+close.end()))
    def outside_fences(pos):return not any(lo<=pos<hi for lo,hi in fence_ranges)
    for match in re.finditer(r'^- \*\*(S[0-9a-f]+)\*\*: [^\n]*\n  (\{[^\n]*\})\n',read,re.M):
        if outside_fences(match.start()):source_catalogue[match.group(1)]=json.loads(match.group(2))
    require(source_catalogue==packet['sources'],'readable_source_catalogue_exact')
    starts=[m for m in re.finditer(r'^## (EO:\d+)\n',read,re.M) if outside_fences(m.start())]
    sections={}
    for i,m in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(read)
        sections[m.group(1)]=read[m.end():end]
    require(set(sections)==IDS,'readable_cohort_exact')
    coverage=[]
    for eo,d in baseline.items():
        section=sections.get(eo,'');index={}
        for match in re.finditer(r'^- \*\*(.+?)\*\*; (S[0-9a-f]+|None); (\{[^\n]*\})$',section,re.M):
            index[match.group(1)]={'source_id':match.group(2),'metadata':json.loads(match.group(3))}
        require(set(index)==set(d['evidence']),'readable_evidence_index_exact',instrument_id=eo)
        record_counts={'evidence':len(d['evidence']),'text_records':0,'original_records':0,'actor_context_records':0,
                       'alternative_records_redundant_in_index':0,'provision_text_aliases':0,
                       'exception_or_savings_records':0,'clause_records':len(d['clauses'])}
        for eid,e in d['evidence'].items():
            row=index.get(eid,{})
            expectedmeta={k:v for k,v in e.items() if k not in ['text','source','actor_source','provision_text','alternative_provisions']}
            require(row.get('metadata')==expectedmeta,'readable_evidence_metadata_exact',instrument_id=eo,evidence_id=eid)
            source=e.get('source') or e.get('actor_source')
            if source:
                require(source_catalogue.get(row.get('source_id'))==source,'readable_evidence_source_exact',instrument_id=eo,evidence_id=eid)
            if e.get('source') and e.get('actor_source'):
                require(e['source']==e['actor_source'],'readable_dual_source_not_redundant',instrument_id=eo,evidence_id=eid)
            text=e.get('text')
            if isinstance(text,str) and text:
                record_counts['text_records']+=1
                if eid.startswith('ORIGINAL:'):record_counts['original_records']+=1
                if eid.startswith('ACTOR_TEXT:'):record_counts['actor_context_records']+=1
                lo=e.get('char_start',source.get('char_start') if source else None)
                hi=e.get('char_end',source.get('char_end') if source else None)
                possible=[]
                if source and type(lo) is int and type(hi) is int:
                    for blockid,b in read_blocks.items():
                        if b['text_sha256']==source.get('text_sha256') and b['char_start']<=lo<hi<=b['char_end']:
                            possible.append(b['text'][lo-b['char_start']:hi-b['char_start']])
                # Literal fallback must be present if no verified attributed range exists.
                require(text in possible or text in section,'readable_evidence_text_accessible',instrument_id=eo,evidence_id=eid)
            if e.get('provision_text'):
                record_counts['provision_text_aliases']+=1
                require(e['provision_text']==e.get('text'),'readable_nonredundant_provision_text_dropped',instrument_id=eo,evidence_id=eid)
            for alternative in e.get('alternative_provisions',[]):
                hits=[v for k,v in d['evidence'].items() if k in index and v.get('id')==alternative.get('id')]
                require(any(all(k in v and v[k]==x for k,x in alternative.items()) for v in hits),
                        'readable_nonredundant_alternative_dropped',instrument_id=eo,evidence_id=eid,alternative_id=alternative.get('id'))
                record_counts['alternative_records_redundant_in_index']+=1
            if e.get('exceptions_text') or e.get('savings_phrases'):record_counts['exception_or_savings_records']+=1
        for c in d['clauses']:
            require(c==d['evidence'].get(c.get('id')),'readable_inventory_record_not_redundant',instrument_id=eo,clause_id=c.get('id'))
            require('- '+c['scope_id']+' → '+str(c.get('id'))+'; characters '+str(c.get('char_start'))+'–'+str(c.get('char_end')) in section,
                    'readable_inventory_index',instrument_id=eo,clause_id=c.get('id'))
        for key in ['own_terms','actor_contexts','actor_provisions','chain','current_law_leads','machine_searches',
                    'draft_gate_errors','conflicts','draft_material_gaps','missing','status_history','notice']:
            if key in d:
                require('\n### '+key+'\n\n'+canonical(d[key])+'\n' in section,'readable_material_section_exact',instrument_id=eo,section=key)
        # Detect material fields outside the renderer's known list rather than
        # assuming an audit of today's corpus proves future renderer completeness.
        known={'schema','instrument_id','whole_order_status','fingerprint','legal_cutoff','original_source_id','clauses','evidence','own_terms','actor_contexts','actor_provisions','chain','current_law_leads','machine_searches','draft_gate_errors','conflicts','draft_material_gaps','missing','status_history','notice'}
        extra={k:v for k,v in d.items() if k not in known}
        require(not extra or '\n### Additional dossier metadata\n\n'+canonical(extra)+'\n' in section,
                'readable_additional_metadata',instrument_id=eo)
        coverage.append({'instrument_id':eo,'fingerprint':d['fingerprint'],**record_counts})
    # Readable warnings, shared tasks and each actual overflow pointer are explicit.
    require('\n## Shared tasks\n\n'+canonical(packet['shared_tasks'])+'\n' in read,'readable_shared_tasks_exact')
    require('\n## Explicit overflow and codec warnings\n\n'+canonical(packet['codec_issues'])+'\n' in read,'readable_codec_warnings_exact')
    overflows=[]
    for eo,d in baseline.items():
        for x in d.get('actor_contexts',[]):
            if x.get('overflow'):
                path=ROOT/'jobs/claim-kit/output'/x['overflow']
                overflows.append({'instrument_id':eo,'pointer':x['overflow'],'exists':path.is_file()})
                require(x['overflow'] in sections[eo],'readable_overflow_pointer',instrument_id=eo)
    # Current code can legitimately move after preparation. The original pin is
    # preserved and discrepancy is recorded, not silently re-labelled current.
    code=loadraw(ROOT/'jobs/claim-kit/batch.py');assembler=loadraw(ROOT/'jobs/claim-kit/assemble.py')
    packet_era=HERE/'initial/PACKET_ERA_BATCH.py'
    packet_era_sha=digest(loadraw(packet_era)) if packet_era.exists() else None
    require(packet_era_sha==packet['codec_code_sha256'],'packet_era_code_hash_unverified')
    if digest(code)!=packet['codec_code_sha256']:warnings.append('Current batch.py differs from packet-era codec hash; this audit uses an independent interpreter and pins both identities.')
    require(digest(assembler)==packet['assembler_code_sha256'],'assembler_code_pin_changed')
    warnings.extend(['JSON values and canonical fingerprints are exact; physical baseline files contain four extra trailing LF bytes not represented by the codec.',
                     'No actual overflow entries occur in these six; this audit cannot validate all50 overflow behavior.',
                     'The renderer omits redundant provision_text/alternative_provisions containers; this cohort passes only because every provision_text equals text and all alternative records are independently present in the evidence index.',
                     'The readable packet has no direct per-evidence text-block link: provenance hash and absolute character bounds resolve texts, which the audit checked independently.',
                     'No legal truth, source-image authentication or producer outcome was evaluated.'])
    # Pin producer inputs a second time; do not let a concurrent rewrite escape review.
    changed=[]
    for rel,pin in read_pins.items():
        if rel.startswith('jobs/claim-kit/'):continue # Record code movement as warning separately.
        if digest((ROOT/rel).read_bytes())!=pin['sha256']:changed.append(rel)
    require(not changed,'inputs_changed_during_audit',paths=changed)
    result={'schema':'eo-independent-packet-completeness-audit/v1','started_utc':started,
            'finished_utc':datetime.now(timezone.utc).isoformat(),'seconds':round(time.perf_counter()-start,6),
            'verdict':'PASS_FOR_PINNED_SIX_EVIDENCE_COMPLETENESS' if not failures else 'FAIL_REQUIRES_CORRECTION_AND_REREVIEW',
            'scope':'Evidence preparation only; no producer outputs, decisions or applied records read.',
            'orders':len(baseline),'independent_decoder_used':True,'production_decoder_imported':False,
            'references_expanded':reference_counts,'readable_coverage':coverage,'failures':failures,'warnings':warnings,
            'overflow_records':overflows,'source_records':len(packet['sources']),'shared_text_blocks':len(packet['text_blocks']),
            'held_source_files_verified':len(source_text),'shared_objects':len(packet['shared_objects']),
            'byte_metrics':{'raw_baseline_files':baseline_bytes,'canonical_pretty_json_baseline':pretty_bytes,
                            'lossless_packet':len(rawpacket),'readable_view':len(rawread),
                            'packet_reduction_vs_canonical':round(1-len(rawpacket)/pretty_bytes,9),
                            'readable_reduction_vs_canonical':round(1-len(rawread)/pretty_bytes,9),
                            'prototype_numeric_reproduction':'Not claimed: prior684097/349648 member identities unknown.'},
            'packet_fingerprint':packet['fingerprint'],'packet_codec_code_sha256':packet['codec_code_sha256'],
            'verified_packet_era_code_sha256':packet_era_sha,
            'current_codec_code_sha256':digest(code),'packet_assembler_code_sha256':packet['assembler_code_sha256'],
            'read_pins':read_pins}
    dump(HERE/(output_prefix+'.json'),result)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--live',action='store_true');ap.add_argument('--prefix',default='INITIAL_REVIEW');a=ap.parse_args()
    base=MATCHED/'B' if a.live else HERE/'initial'
    result=audit(base/'PACKET.json',base/'READ.md',a.prefix)
    print(json.dumps({k:result[k] for k in ['verdict','orders','seconds','source_records','shared_text_blocks','held_source_files_verified','byte_metrics','failures']},indent=2))
