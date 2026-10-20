"""Bounded offline attempt. Investigates held evidence; never decides legal status."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from survey import PHASES,TOKEN_CATEGORIES,sha,write


def blank_phase():
    return {'active_seconds':None,'access_wait_seconds':None,'machine_seconds':None,
            'tokens':dict.fromkeys(TOKEN_CATEGORIES),'coverage':'unavailable'}


def run(root, member, prepared, manifest, byte_limit):
    t0=time.monotonic();phases={p:blank_phase() for p in PHASES}
    sys.path.insert(0,str(root/'jobs/claim-kit'))
    from kit import load_dossier
    from assemble import canonical_sha
    iid=member['instrument_id'];kit=root/'jobs/claim-kit/output';record={}
    if iid in prepared['index']:
        record=load_dossier(kit,iid)
        if record.get('fingerprint')!=canonical_sha(record):raise ValueError('stale dossier fingerprint')
        source_rel='jobs/claim-kit/output/'+prepared['index'][iid]['dossier']
    else:
        record=prepared['leads'].get(iid)
        if record is None:raise ValueError('selected order absent from kit status leads')
        source_rel='jobs/claim-kit/output/STATUS_LEADS.jsonl'
    prep_end=time.monotonic()
    sources={}
    def visit(v):
        if isinstance(v,dict):
            if v.get('text_path') and v.get('text_sha256'):sources[v['text_path']]=v['text_sha256']
            for child in v.values():visit(child)
        elif isinstance(v,list):
            for child in v:visit(child)
    visit(record)
    held=[];missing=[];read_bytes=0
    for rel,expected in sorted(sources.items()):
        p=(root/rel).resolve()
        if not p.is_relative_to(root):raise ValueError('unsafe source path')
        if not p.is_file():missing.append({'path':rel,'reason':'held pointer unavailable in checkout'});continue
        if read_bytes+p.stat().st_size>byte_limit:
            missing.append({'path':rel,'reason':'prospective byte bound'});continue
        actual=sha(p)
        if actual!=expected:raise ValueError('held source hash mismatch: '+rel)
        data=p.read_text(encoding='utf-8');read_bytes+=p.stat().st_size
        held.append({'path':rel,'sha256':actual,'bytes':p.stat().st_size,'characters':len(data)})
    acquired=time.monotonic()
    # Gap analysis is an attempted preparation for legal production, never production acceptance.
    gaps=record.get('draft_material_gaps',record.get('missing',[]))
    blocked=bool(member['open_steps'])
    access=prepared.get('access',{}).get(iid,[])
    outcome='blocked_access' if access else ('blocked_prerequisite' if blocked or missing else 'incomplete_capability')
    end=time.monotonic()
    for phase,seconds in [('preparation',prep_end-t0),('acquisition',acquired-prep_end),('production',end-acquired)]:
        phases[phase].update(machine_seconds=seconds,access_wait_seconds=0.0,coverage='machine only; agent effort unavailable')
    return {'schema':'neyman.observation/1','instrument_id':iid,'manifest_sha256':manifest['manifest_sha256'],
            'outcome':outcome,'right_censored':False,'completion_effort_seconds':None,'phases':phases,
            'attempt_scope':manifest['pilot_scope'],'packet_path':source_rel,'packet_sha256':sha(root/source_rel),
            'dossier_fingerprint':record.get('fingerprint'),'held_sources_inspected':held,'unavailable_sources':missing,
            'research_gaps':gaps,'residual_open_steps':member['open_steps'],'residual_blockers':member['blockers'],
            'access_dependencies':access,'correlation_keys':sorted(set(member['families'])|set(sources)),
            'shared_event_ids':['pilot-preparation'],'legal_decisions_added':0,'human_certifications_added':0,
            'independent_review':'unavailable in this machine-only pilot; no completed dossier claimed'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();data=json.loads(a.input.read_text())
    write(a.out,run(a.root.resolve(),data['member'],data['prepared'],data['manifest'],data['byte_limit']))
