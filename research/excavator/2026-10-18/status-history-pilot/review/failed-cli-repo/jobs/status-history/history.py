"""Compile dated editorial observations once; prepare research, never decide law.

Raw API fields and positioned volume OCR remain separate witnesses. Dates are
typed. Candidate event dates never become effective dates or accepted statuses.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CUTOFF='2026-10-14'
SNAPSHOT='1989-01-20'
CENSUS='research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv'
STATUSES='research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv'
CATALOG='jobs/later-events/output/CATALOG_INDEX.csv'
EDGES='jobs/later-events/output/EDGES.csv'
TABLE='jobs/ofr-codification-1989/output/DISPOSITION_1989.csv'
CHUNKS='jobs/ofr-codification-1989/data/codification_1989_eo_table_chunks.jsonl'
BOOK_PROV='jobs/ofr-codification-1989/data/PROVENANCE.json'
API_DIR='jobs/fr-originals/data/ofr_index'
END_MECHANISMS={'revocation','supersession','termination','abolition','nullification','rescission','voiding','expiration','supersession_or_revocation'}


def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def sha(v):return hashlib.sha256(v).hexdigest()
def objsha(v):return sha(canon(v).encode())
def name(iid):return 'EO_'+iid[3:] if re.fullmatch(r'EO:[A-Za-z0-9_.-]+',iid) else 'ID_'+sha(iid.encode())[:24]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())


class Reader:
    def __init__(self,root):self.root=root;self.hashes={}
    def raw(self,rel):
        p=(self.root/rel).resolve()
        if not p.is_relative_to(self.root):raise ValueError('unsafe input')
        data=p.read_bytes();self.hashes[rel]=sha(data);return data
    def js(self,rel):return json.loads(self.raw(rel))
    def csv(self,rel):
        # StringIO/newline preserves embedded newlines in fields.
        import io
        return list(csv.DictReader(io.StringIO(self.raw(rel).decode('utf-8-sig'),newline='')))
    def lines(self,rel):return [json.loads(s) for s in self.raw(rel).decode('utf-8').splitlines() if s.strip()]


def normalized_span(text,quote):
    """Match only whitespace differences, returning an exact *raw* source slice.

    No OCR substitutions, punctuation edits or identity normalization are allowed.
    Multiple occurrences remain ambiguous instead of choosing the first.
    """
    chars=[(i,c) for i,c in enumerate(text) if not c.isspace()]
    compact=''.join(c for _,c in chars);needle=''.join(quote.split())
    if not needle:return None
    found=[m.start() for m in re.finditer(re.escape(needle),compact)]
    if len(found)!=1:return None
    a=chars[found[0]][0];b=chars[found[0]+len(needle)-1][0]+1
    return {'char_start':a,'char_end':b,'text':text[a:b],
            'match':'exact' if text[a:b]==quote else 'whitespace_only'}


def api_anchor(r):
    return (str(r.get('executive_order_number') or r.get('executive_order_number_raw') or ''),
            r.get('signing_date') or '',r.get('title') or '')


def row_chunks(row,page,neighbors):
    """Expose the original row neighborhood, not a fabricated contiguous quote.

    Row/column pairing is inherited from the existing volume parser. Quotes are
    exact individual positioned OCR chunks, including any neighboring furniture.
    They do not independently validate the parser's reconstructed row.
    """
    y=float(row['y']);lower=max((v for v in neighbors if v<y-1),default=95.0)
    result=[]
    for n,(x,cy,text) in enumerate(page['chunks']):
        if lower+2.5<cy<=y+2.5:
            result.append({'json_pointer':f'/chunks/{n}/2','x':x,'y':cy,
                           'text':text,'char_start':0,'char_end':len(text),'text_sha256':sha(text.encode())})
    return result


def temporal_history(observations,events,status):
    flags=set();constraints=[]
    groups={o.get('group') for o in observations if o['kind']=='printed_snapshot'}
    if 'ended_by_1989' in groups:
        constraints.append({'kind':'editorial_ended_by_bound','lower':None,'upper':SNAPSHOT,
           'upper_inclusive':True,'meaning':'Conditional bound on the editor-described disposition, not a proven legal first end.'})
        if status=='yes':flags.add('PROVISIONAL_YES_VS_ENDED_SNAPSHOT_REQUIRES_RECONCILIATION')
    if 'in_force_1989' in groups:
        constraints.append({'kind':'editorial_active_at_point','lower':SNAPSHOT,'upper':SNAPSHOT,
           'meaning':'Editorial observation at one date; no continuity before/after and no present legal predicate inferred.'})
    endings=[e for e in events if e['mechanism'] in END_MECHANISMS]
    dates=[e['candidate_date'] for e in endings if e.get('candidate_date') and e['candidate_date']<=CUTOFF]
    if 'ended_by_1989' in groups and dates and min(dates)>SNAPSHOT:
        flags.add('KNOWN_LATER_CLEANUP_IS_NOT_FIRST_END_SEARCH_EARLIER')
    if 'in_force_1989' in groups and any(d<=SNAPSHOT for d in dates):
        flags.add('PRE_SNAPSHOT_END_LEAD_VS_ACTIVE_SNAPSHOT_CHECK_SCOPE_OR_REVIVAL')
    if 'in_force_1989' in groups and status=='no' and not any(d>SNAPSHOT for d in dates):
        flags.add('POST_SNAPSHOT_END_BASIS_NOT_LOCATED')
    if any(e.get('qualifier') or 'partial' in e.get('date_flags','').lower() for e in endings):
        flags.add('PARTIAL_OR_QUALIFIED_CHANGE_REQUIRES_CLAUSE_CHECK')
    if any(e.get('candidate_date','')>CUTOFF for e in events):flags.add('POST_CUTOFF_EVENT_EXCLUDED_FROM_TEMPORAL_INFERENCE')
    if any(not e.get('verified_raw_span') for e in events):flags.add('EVENT_QUOTE_NOT_VERIFIED_AGAINST_HELD_RAW_API')
    if 'ended_by_1989' in groups and 'in_force_1989' in groups:flags.add('CONFLICTING_SNAPSHOT_ROWS')
    if any(o.get('identity_ambiguous') for o in observations):flags.add('AMBIGUOUS_RAW_IDENTITY')
    if any(not o.get('text','').strip() for o in observations if o['kind']=='api_observation'):
        flags.add('EMPTY_CATALOG_NOTE_DOES_NOT_ESTABLISH_CURRENT_EFFECT')
    if not observations:flags.add('RELATIONAL_LEADS_WITHOUT_TARGET_STATUS_OBSERVATION')
    return constraints,sorted(flags)


def tasks_for(status,observations,events,flags):
    tasks=['Confirm identity and read the cited source field/page; editorial observations are leads.']
    if status is None:tasks.append('Recommend a provisional status with a source rationale through the established adjudication process; this packet cannot write one.')
    if any(o.get('group')=='ended_by_1989' for o in observations):tasks.append('Read original operative clauses and acting authority; establish actual first-effective cessation, including earlier ends and residual effects.')
    if any(o.get('group')=='in_force_1989' for o in observations):tasks.append('Trace changes after 1989-01-20 through 2026-10-14; a snapshot cannot establish present operation.')
    if events:tasks.append('Check each candidate event for identity, partial scope, effective wording, savings and contrary evidence; signing dates are not effective dates.')
    if flags:tasks.append('Resolve every flag explicitly; retain unresolved material gaps.')
    tasks.append('Use claim-kit original/clause/chain evidence and its existing decision/assembly workflow after a provisional status is established.')
    return tasks


def blank_decision(packet,agent=''):
    h=packet['history']
    return {'schema':'eo-status-history-decision/v1','instrument_id':h['instrument_id'],
            'history_sha256':h['fingerprint'],'agent':agent,'approved':False,
            'identity_confirmed':False,'observations_reviewed':[],
            'proposed_intervals':[],'conflict_resolutions':{},
            'recommended_provisional_status':None,'rationale':'',
            'material_gaps':list(h['flags']),
            'notice':'Research decision only. No command publishes a provisional status, legal claim or human certification.'}


def build(root,out):
    started=time.monotonic();root=Path(root).resolve();out=Path(out).resolve()
    if not out.is_relative_to(root/'jobs/status-history/output'):raise ValueError('output must be under jobs/status-history/output')
    out.mkdir(parents=True,exist_ok=True);(out/'FAILED.json').unlink(missing_ok=True)
    rd=Reader(root)
    census={r['id']:r for r in rd.csv(CENSUS) if r.get('included_in_bibliography')=='1'}
    if not census or len(census)>20000:raise ValueError('empty census or corpus bound exceeded')
    statuses={r['instrument_id']:r['provisional_substantive_status'] for r in rd.csv(STATUSES) if r['provisional_substantive_status'] in ('yes','no')}
    table=rd.csv(TABLE);catalog=rd.csv(CATALOG);edges=rd.csv(EDGES)
    book=rd.js(BOOK_PROV)['book'];chunks=rd.lines(CHUNKS)
    if rd.hashes[CHUNKS]!=book['table_chunks_sha256']:raise ValueError('volume positioned-text hash mismatch')
    pages={r['page']:r for r in chunks};ys=defaultdict(list)
    for r in table:ys[int(r['page'])].append(float(r['y']))
    obs={};obs_by=defaultdict(list);events={};events_by=defaultdict(list);unmatched=[];source_reads=defaultdict(set)
    book_source={'url':book['handle_url'],'sha256':book['pdf_sha256'],'text_path':CHUNKS,
                 'text_sha256':rd.hashes[CHUNKS],'retrieval_description':book['supplied'],
                 'edition_role':'editorial codification, as amended; never an official original of a target order'}
    for n,r in enumerate(table,2):
        iid=r.get('census_id') if r.get('census_id') in census else None
        page=pages[int(r['page'])];quotes=row_chunks(r,page,ys[page['page']])
        oid='S1989:'+objsha(r)[:24]
        o={'id':oid,'instrument_id':iid,'witness_key':r['key'],'kind':'printed_snapshot','as_of':SNAPSHOT,
           'date_meaning':'editorial snapshot date, not signing/publication/effective date',
           'group':r['group'],'category':r['category'],'producer_interpretation':r['disposition'],
           'amendments_interpretation':r['amendments'],'actor_ids':r['acting_documents'].split(' | ') if r['acting_documents'] else [],
           'confidence':r['pairing_confidence'],'flags':r['flags'].split('|') if r['flags'] else [],
           'source':dict(book_source,pdf_page=page['page'],printed_page=r['printed'],record_sha256=objsha(page)),
           'quotes':quotes,'input_row':{'path':TABLE,'csv_record':n-1,'record_sha256':objsha(r)},
           'identity_ambiguous':iid is None,'notice':'Reconstructed row interpretation with exact OCR neighborhood. Image/scope review remains necessary.'}
        obs[oid]=o
        if iid:obs_by[iid].append(oid);source_reads[f'book:PDF:{page["page"]}'].add(iid)
        else:unmatched.append({'kind':'unresolved_snapshot_identity','observation_id':oid,'witness_key':r['key'],'candidate_is_admitted':False})
    # Bind raw API records to the EXISTING catalog crosswalk using all three
    # identity anchors. In particular, 10571/10571A and suffixes are not guessed.
    by_anchor=defaultdict(list)
    for n,c in enumerate(catalog,1):
        if c['id'] in census:by_anchor[api_anchor(c)].append((n,c))
    api_prov=rd.js(API_DIR+'/PROVENANCE.json');raw_by=defaultdict(list);mapped=set();counts=Counter()
    captured=re.search(r'\b\d{4}-\d{2}-\d{2}\b',api_prov.get('retrieved',''))
    captured=captured[0] if captured else None
    for f in api_prov['files']:
        rel=API_DIR+'/'+f['file'];raw=gzip.decompress(rd.raw(rel))
        if len(raw)>10_000_000 or sha(raw)!=f['uncompressed_sha256']:raise ValueError('raw API response hash/bound mismatch: '+rel)
        response=json.loads(raw)
        for number,r in enumerate(response['results']):
            matches=by_anchor.get(api_anchor(r),[])
            # When duplicate raw records share anchors, publication/document
            # identity can disambiguate; otherwise retain the ambiguity.
            exact=[v for v in matches if all((v[1].get(k) or '')==(r.get(k) or '') for k in ('publication_date','document_number'))]
            if exact:matches=exact
            if len(matches)!=1:
                unmatched.append({'kind':'raw_api_identity_not_unique','source_path':rel,'json_pointer':f'/results/{number}',
                   'record_sha256':objsha(r),'raw_number':r.get('executive_order_number'),'candidate_matches':[m[1]['id'] for m in matches],
                   'candidate_is_admitted':False});counts['raw_identity_unresolved']+=1;continue
            cnum,c=matches[0];iid=c['id'];mapped.add(iid);note=r.get('disposition_notes') or ''
            source={'url':api_prov['api_query']+'&page='+str(int(f['file'].split('_')[-1].split('.')[0])),
                'sha256':sha(raw),'compressed_path':rel,'compressed_sha256':rd.hashes[rel],
                'json_pointer':f'/results/{number}/disposition_notes','record_sha256':objsha(r),
                'text_sha256':sha(note.encode()),'retrieved_description':api_prov['retrieved'],
                'retrieved_on':captured,'retrieval_date_is_not_legal_as_of':True}
            oid='API:'+objsha([source,iid])[:24]
            o={'id':oid,'instrument_id':iid,'kind':'api_observation','as_of':None,'retrieved_on':captured,
               'date_meaning':'Capture date only; editorial event dates are separately typed candidates.',
               'text':note,'char_start':0,'char_end':len(note),'source':source,'identity_ambiguous':False,
               'identity_crosswalk':{'path':CATALOG,'csv_record':cnum,'record_sha256':objsha(c),
                   'anchors':['raw EO number','signing date','title','publication/document fields when available']},
               'metadata':{k:r.get(k) for k in ('executive_order_number','title','signing_date','publication_date','document_number','citation')},
               'confidence':'raw field exact; editorial legal interpretation unreviewed'}
            obs[oid]=o;obs_by[iid].append(oid);raw_by[iid].append(o);source_reads['api:'+rel].add(iid)
    # Preserve the later derived catalog as another observation where the raw
    # capture cannot support it. Never relabel an export as held API bytes.
    for n,c in enumerate(catalog,1):
        iid=c['id']
        if iid not in census:continue
        if iid not in mapped:
            oid='INDEX:'+objsha(c)[:24]
            obs[oid]={'id':oid,'instrument_id':iid,'kind':'derived_catalog_observation','as_of':None,
                'text':c.get('disposition_notes',''),'source':{'path':CATALOG,'csv_record':n,'record_sha256':objsha(c),'sha256':rd.hashes[CATALOG]},
                'flags':['RAW_API_IDENTITY_OR_RESPONSE_MISSING'],'identity_ambiguous':True,
                'date_meaning':'Derived index; capture date and original response unavailable here. Not a legal as-of date.'}
            obs_by[iid].append(oid)
    # Locate each existing editorial edge in the actual held raw field. An
    # unlocated edge stays visibly unverified and cannot become exact evidence.
    for n,e in enumerate(edges,1):
        if not e['evidence_type'].startswith('ofr_note') or e['target_id'] not in census:continue
        candidates=[]
        for o in raw_by.get(e['stated_on'],[]):
            span=normalized_span(o['text'],e['quote'])
            if span:candidates.append((o,span))
        verified=bool(candidates)
        if verified:
            o,span=candidates[0];oid=o['id'];quote=span['text']
        else:oid=None;span=None;quote=e['quote']
        event={'id':'EV:'+e['edge_id'],'target_id':e['target_id'],'actor_id':e['acting_id'],
            'mechanism':e['mechanism'],'qualifier':e['qualifier'],'candidate_date':e['date_candidate'],
            'date_meaning':e['date_basis'],'date_flags':e['date_flags'],
            'stated_effective_date_candidate':e['stated_effective_date'] or None,
            'verified_raw_span':verified,'observation_id':oid,'exact_span':span,
            'source_observation_sha256':objsha(o) if verified else None,
            'quote':quote,'quote_kind':'exact_raw_API_field_slice' if verified else 'existing_parsed_edge_UNVERIFIED',
            'input_edge':{'path':EDGES,'csv_record':n,'record_sha256':objsha(e)},
            'scope':'requires per-clause check; an unqualified editorial relation is not whole-order proof',
            'source_dependency_group':'OFR editorial data; acting/target notes are not necessarily independent corroboration'}
        events[event['id']]=event;events_by[e['target_id']].append(event['id'])
        counts['editorial_edges_seen']+=1;counts['editorial_edges_raw_span_verified']+=verified
    manifest={'inputs':dict(sorted(rd.hashes.items())),'code_sha256':sha(Path(__file__).read_bytes()),'legal_cutoff':CUTOFF}
    fp=objsha(manifest);dump(out/'INPUTS.json',dict(manifest,fingerprint=fp))
    # Shared immutable records are sharded by ID. Histories contain pointers,
    # so reading one acting note for many targets never requires duplicate files.
    for kind,records in [('observations',obs),('events',events)]:
        shards=defaultdict(list)
        for rid,record in sorted(records.items()):shards[sha(rid.encode())[:2]].append(record)
        for shard,records2 in shards.items():
            folder=out/kind;folder.mkdir(exist_ok=True)
            (folder/(shard+'.jsonl')).write_bytes((''.join(canon(r)+'\n' for r in records2)).encode())
    index=[];fragments=[];histories=[];writes=0;reuse=0
    for iid in sorted(census):
        oids=sorted(set(obs_by[iid]));eids=sorted(set(events_by[iid]));oset=[obs[v] for v in oids];eset=[events[v] for v in eids]
        if not oids and not eids:
            index.append({'instrument_id':iid,'status':statuses.get(iid),'observations':0,'events':0,'history':None,'flags':['NO_STATUS_OBSERVATION_LOCATED']});continue
        constraints,flags=temporal_history(oset,eset,statuses.get(iid))
        history={'schema':'eo-status-history/v1','instrument_id':iid,'legal_cutoff':CUTOFF,
            'provisional_status':statuses.get(iid),'observation_ids':oids,
            'event_ids':sorted(eids,key=lambda v:(events[v]['candidate_date'] or '9999',v)),
            'observation_fingerprints':{v:objsha(obs[v]) for v in oids},
            'event_fingerprints':{v:objsha(events[v]) for v in eids},
            'temporal_constraints_LEADS_ONLY':constraints,'flags':flags,
            'next_actions':tasks_for(statuses.get(iid),oset,eset,flags),
            'source_record_directory':'jobs/status-history/output',
            'accepted_legal_intervals':[],'current_legal_status':None,'human_certified':False,
            'notice':'Sourced observation history only. No effective date, first end, status change or continuity is established.'}
        history['fingerprint']=objsha(history)
        rel='histories/'+name(iid)+'.json';path=out/rel;data=(json.dumps(history,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
        if path.exists() and path.read_bytes()==data:reuse+=1
        else:path.parent.mkdir(exist_ok=True);path.write_bytes(data);writes+=1
        index.append({'instrument_id':iid,'status':statuses.get(iid),'observations':len(oids),'events':len(eids),
                      'history':rel,'fingerprint':history['fingerprint'],'flags':flags})
        fragments.append({'instrument_id':iid,'kind':'status_history_candidates','data':{
            'history_path':'jobs/status-history/output/'+rel,'history_sha256':sha(data),'fingerprint':history['fingerprint'],
            'observation_count':len(oids),'event_count':len(eids),'flags':flags,'legal_cutoff':CUTOFF,
            'notice':'Editorial leads, not an original, legal conclusion, provisional-status assignment or human certification.'}})
        histories.append(history)
    dump(out/'INDEX.json',index)
    (out/'FRAGMENTS.jsonl').write_bytes((''.join(canon(f)+'\n' for f in fragments)).encode())
    (out/'UNRESOLVED_WITNESSES.jsonl').write_bytes((''.join(canon(r)+'\n' for r in unmatched)).encode())
    dump(out/'SHARED_SOURCE_READS.json',[{'source':s,'order_memberships':len(ids),'instrument_ids':sorted(ids)} for s,ids in sorted(source_reads.items())])
    covered={r['instrument_id'] for r in index if r['history']};own={r['instrument_id'] for r in index if r['observations']}
    summary={'schema':'eo-status-history-summary/v1','legal_cutoff':CUTOFF,'input_fingerprint':fp,
       'census_identities':len(census),'identities_with_history':len(covered),'identities_with_own_observation':len(own),
       'undecided_with_history':sum(i not in statuses for i in covered),'undecided_with_own_observation':sum(i not in statuses for i in own),
       'printed_snapshot_records':len(table),'printed_snapshot_identity_joins':sum(bool(o['instrument_id']) for o in obs.values() if o['kind']=='printed_snapshot'),
       'printed_snapshot_undecided_identities':len({o['instrument_id'] for o in obs.values() if o['kind']=='printed_snapshot' and o['instrument_id'] and o['instrument_id'] not in statuses}),
       'raw_api_response_files':len(api_prov['files']),'raw_api_observations':sum(o['kind']=='api_observation' for o in obs.values()),
       'status_observations':len(obs),'unresolved_witness_records':len(unmatched),**dict(counts),
       'flags_by_identity':dict(Counter(f for h in histories for f in h['flags'])),
       'per_order_shared_source_lookup_memberships':sum(len(v) for v in source_reads.values()),
       'distinct_shared_source_units':len(source_reads),'legal_findings':0,'statuses_changed':0,'census_admissions':0,
       'model_input_tokens':None,'model_cached_tokens':None,'model_output_tokens':None,'model_reasoning_tokens':None,
       'limits':['Exact OCR/API spans authenticate stored text, not legal meaning or page images.',
                 'Intervals are conditional editorial constraints; no first-effective end or continuity is inferred.',
                 'No-note catalog entries and public-land exclusions never establish present legal status.',
                 'Source reuse counts measure addressable memberships, not observed billed usage or agent reads.']}
    dump(out/'SUMMARY.json',summary)
    dump(out/'METRICS.json',{'runner_seconds':round(time.monotonic()-started,4),'histories_written':writes,'unchanged_histories_reused':reuse,
         'output_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'network_requests':0})
    return summary


def record(out,kind,rid,cache=None):
    if cache is not None and (kind,rid) in cache:return cache[(kind,rid)]
    shard=sha(rid.encode())[:2]
    for line in (out/kind/(shard+'.jsonl')).read_text('utf-8').splitlines():
        row=json.loads(line)
        if cache is not None:cache[(kind,row['id'])]=row
        if row['id']==rid:return row
    raise ValueError('record absent from current shard: '+rid)


def show(out,iid,index=None,cache=None):
    if (out/'FAILED.json').exists():raise ValueError('status-history run failed; stale outputs must not be used')
    status=out/'STATUS.json'
    if status.exists() and json.loads(status.read_bytes()).get('result')!='succeeded':
        raise ValueError('status-history runner did not succeed; inspect STATUS.json')
    index=json.loads((out/'INDEX.json').read_bytes()) if index is None else index
    row=next((r for r in index if r['instrument_id']==iid),None)
    if not row or not row['history']:raise ValueError('no dated history located for '+iid)
    h=json.loads((out/row['history']).read_bytes());body={k:v for k,v in h.items() if k!='fingerprint'}
    if objsha(body)!=h['fingerprint'] or h['fingerprint']!=row['fingerprint']:raise ValueError('stale/tampered history')
    packet={'history':h,'observations':[record(out,'observations',v,cache) for v in h['observation_ids']],
            'events':[record(out,'events',v,cache) for v in h['event_ids']]}
    for kind in ('observations','events'):
        expected=h['observation_fingerprints' if kind=='observations' else 'event_fingerprints']
        if any(objsha(r)!=expected.get(r['id']) for r in packet[kind]):raise ValueError('changed shared history evidence')
    supports=sorted({e['observation_id'] for e in packet['events'] if e['verified_raw_span']}-set(h['observation_ids']))
    packet['supporting_observations']=[record(out,'observations',v,cache) for v in supports]
    obs={o['id']:o for o in packet['observations']+packet['supporting_observations']}
    if any(e['verified_raw_span'] and objsha(obs[e['observation_id']])!=e['source_observation_sha256'] for e in packet['events']):
        raise ValueError('changed acting-note source observation')
    return packet


def validate_packet(root,packet,cache=None):
    """Recheck exact stored fields/chunks, caching each actual source once.

    Deliberately does not certify images, legal scope, identity inclusion or dates.
    """
    root=Path(root).resolve();cache={} if cache is None else cache;errors=[]
    def load(rel,kind):
        key=(rel,kind)
        if key not in cache:
            path=(root/rel).resolve()
            if not path.is_relative_to(root):raise ValueError('unsafe source')
            raw=path.read_bytes()
            if kind=='gzip':
                decoded=gzip.decompress(raw)
                cache[key]=(sha(raw),sha(decoded),json.loads(decoded))
            elif kind=='pages':cache[key]=(sha(raw),{r['page']:r for r in (json.loads(s) for s in raw.decode().splitlines() if s)})
        return cache[key]
    observations={o['id']:o for o in packet['observations']+packet.get('supporting_observations',[])}
    for o in observations.values():
        s=o['source']
        if o['kind']=='api_observation':
            gzsha,rawsha,body=load(s['compressed_path'],'gzip')
            n=int(s['json_pointer'].split('/')[2]);r=body['results'][n]
            text=r.get('disposition_notes') or ''
            if (gzsha!=s['compressed_sha256'] or rawsha!=s['sha256'] or objsha(r)!=s['record_sha256']
                or text!=o['text'] or sha(text.encode())!=s['text_sha256']):errors.append(o['id']+':raw_API_mismatch')
        elif o['kind']=='printed_snapshot':
            file_sha,pages=load(s['text_path'],'pages');page=pages[s['pdf_page']]
            if file_sha!=s['text_sha256'] or objsha(page)!=s['record_sha256']:errors.append(o['id']+':page_hash')
            for q in o['quotes']:
                n=int(q['json_pointer'].split('/')[2]);text=page['chunks'][n][2]
                if text[q['char_start']:q['char_end']]!=q['text'] or sha(q['text'].encode())!=q['text_sha256']:
                    errors.append(o['id']+':chunk_not_exact')
    # An acting note can be an observation of a different order, so load it by
    # ID from the shared directory instead of pretending it belongs to target.
    for e in packet['events']:
        if not e['verified_raw_span']:continue
        o=observations.get(e['observation_id'])
        if o is None:o=record(root/'jobs/status-history/output','observations',e['observation_id'])
        span=e['exact_span'];text=o['text']
        if text[span['char_start']:span['char_end']]!=e['quote']:errors.append(e['id']+':event_not_exact')
    return errors


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=ROOT);p.add_argument('--out',type=Path,default=HERE/'output')
    sub=p.add_subparsers(dest='cmd',required=True);sub.add_parser('build');s=sub.add_parser('show');s.add_argument('instrument_id')
    a=p.parse_args()
    if a.cmd=='show':print(json.dumps(show(a.out,a.instrument_id),ensure_ascii=False,indent=2))
    else:
        try:print(canon(build(a.repo,a.out)))
        except Exception as e:dump(a.out/'FAILED.json',{'error':type(e).__name__+': '+str(e),'stale_outputs_must_not_be_used':True});raise
