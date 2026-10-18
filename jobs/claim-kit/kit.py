#!/usr/bin/env python3
"""Model-neutral offline interface. Run from any directory with --repo."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode=True
from assemble import blank_sheet, assemble, check_claim
from build import build, dump, filename

HERE=Path(__file__).resolve().parent

def read(path,default=None):
    if not path.exists():return default
    return json.loads(path.read_text('utf-8'))

def load_dossier(out,iid):
    row=next((r for r in read(out/'INDEX.json',[]) if r['instrument_id']==iid),None)
    if row is None:raise ValueError('Order absent from current decided INDEX: '+iid)
    d=read(out/'dossiers'/(filename(iid)+'.json'))
    if d and (d.get('fingerprint')!=row['fingerprint'] or d.get('whole_order_status')!=row['status']):raise ValueError('Dossier does not match current INDEX')
    if not d:raise ValueError('Dossier not found: '+iid+'; run the corpus job first.')
    return d

@contextmanager
def reservations(repo):
    folder=repo/'research/readiness';folder.mkdir(parents=True,exist_ok=True)
    guard=folder/'CLAIM_KIT_LOCK.guard';path=folder/'CLAIM_KIT_LOCK.json'
    # O_EXCL works across processes, including Windows. Never silently steal a stale guard.
    deadline=time.monotonic()+10
    while True:
        try:fd=os.open(guard,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);break
        except FileExistsError:
            if time.monotonic()>=deadline:raise ValueError('Reservation guard busy; inspect '+str(guard)+' before retrying.')
            time.sleep(.05)
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd)
        lock=read(path,{'schema':'eo-claim-kit-reservations/v1','orders':{}})
        yield lock
        temp=path.with_suffix('.tmp')
        dump(temp,lock);os.replace(temp,path)
    finally:guard.unlink(missing_ok=True)

def existing_claims(repo):
    found=set()
    for path in sorted((repo/'research/readiness/claims').glob('*.jsonl')):
        for n,s in enumerate(path.read_text('utf-8').splitlines(),1):
            if not s.strip():continue
            try:r=json.loads(s)
            except ValueError:raise ValueError(f'Malformed claim at {path}:{n}; refuse duplicate assignment')
            if r.get('instrument_id'):found.add(r['instrument_id'])
    return found

def pick(repo,out,agent,n,excluded=None):
    if n<1 or not re.fullmatch(r'[A-Za-z0-9_.-]+',agent):raise ValueError('agent must be a simple name and n positive')
    index=read(out/'INDEX.json',[]);by={r['instrument_id']:r for r in index}
    if not index:raise ValueError('Corpus INDEX.json missing or empty')
    excluded=set(excluded or [])|existing_claims(repo)
    families=read(out/'FAMILIES.json',[])
    # Rank actual remaining unlocks, never the obsolete original family size.
    with reservations(repo) as locks:
        unavailable=excluded|set(locks['orders'])
        eligible={iid for iid,row in by.items() if iid not in unavailable}
        ranked=[]
        for f in families:
            members=sorted(set(f['instrument_ids'])&eligible)
            if members:ranked.append((members,f['family_id']))
        ranked.sort(key=lambda f:(-len(f[0]),f[1]))
        selected=[]
        for members,family in ranked:
            for iid in members:
                if iid not in selected:
                    selected.append(iid)
                    locks['orders'][iid]={'agent':agent,'family':family,'dossier_sha256':by[iid]['fingerprint'],'reserved_on':datetime.now(timezone.utc).isoformat()}
                if len(selected)>=n:break
            if len(selected)>=n:break
        for iid in sorted(eligible-set(selected)):
            if len(selected)>=n:break
            selected.append(iid);locks['orders'][iid]={'agent':agent,'family':None,'dossier_sha256':by[iid]['fingerprint'],'reserved_on':datetime.now(timezone.utc).isoformat()}
        return [{'instrument_id':iid,**locks['orders'][iid],'dossier':str(out/by[iid]['dossier'])} for iid in selected]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=HERE.parents[1]);p.add_argument('--output',type=Path)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('build')
    s=sub.add_parser('next');s.add_argument('--agent',required=True);s.add_argument('--n',type=int,default=20);s.add_argument('--exclude',type=Path)
    for cmd in ('dossier','sheet'):
        s=sub.add_parser(cmd);s.add_argument('instrument_id');s.add_argument('--agent',default='');s.add_argument('--write',type=Path)
    s=sub.add_parser('assemble');s.add_argument('sheets',nargs='+',type=Path);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('check');s.add_argument('claims',type=Path)
    sub.add_parser('status')
    s=sub.add_parser('release');s.add_argument('--agent',required=True);s.add_argument('instrument_ids',nargs='+')
    a=p.parse_args(argv);repo=a.repo.resolve();out=(a.output or repo/'jobs/claim-kit/output').resolve()
    try:
        if a.command=='build':build(repo,out,os.environ.get('JOB_CACHE_DIR'));return 0
        if a.command=='next':
            excluded=read(a.exclude,[]) if a.exclude else []
            print(json.dumps(pick(repo,out,a.agent,a.n,excluded),indent=2));return 0
        if a.command in ('dossier','sheet'):
            d=load_dossier(out,a.instrument_id)
            if a.command=='sheet':
                d=blank_sheet(d,a.agent)
                dest=a.write or repo/'research/readiness/decisions'/((a.agent or 'unassigned')+'-'+datetime.now(timezone.utc).date().isoformat())/(filename(a.instrument_id)+'.decision.json')
                if dest.exists():raise ValueError('Decision file exists; refusing overwrite: '+str(dest))
                dump(dest,d);print(str(dest));return 0
            if a.write:dump(a.write,d);print(str(a.write))
            else:print(json.dumps(d,ensure_ascii=False,indent=2))
            return 0
        if a.command=='release':
            with reservations(repo) as locks:
                for iid in a.instrument_ids:
                    if iid in locks['orders'] and locks['orders'][iid]['agent']!=a.agent:raise ValueError('Reservation belongs to another agent: '+iid)
                for iid in a.instrument_ids:locks['orders'].pop(iid,None)
            return 0
        if a.command=='status':
            summary=read(out/'SUMMARY.json',{'error':'No corpus run'})
            summary['committed_claim_identities']=len(existing_claims(repo))
            summary['reservations']=read(repo/'research/readiness/CLAIM_KIT_LOCK.json',{}).get('orders',{})
            print(json.dumps(summary,indent=2));return 0
        if a.command=='assemble':
            if a.write.exists():raise ValueError('Output file exists; refusing overwrite: '+str(a.write))
            claims=[];report=[]
            paths=[]
            for path in a.sheets:paths.extend(sorted(path.glob('*.json')) if path.is_dir() else [path])
            for path in paths:
                iid=None;claim=None
                try:
                    sheet=read(path)
                    if not isinstance(sheet,dict):raise ValueError('Decision sheet must be a JSON object')
                    iid=sheet.get('instrument_id')
                    if not isinstance(iid,str):raise ValueError('Decision instrument_id must be a string')
                    d=load_dossier(out,iid);claim,errors=assemble(sheet,d,repo)
                except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
                    errors=[type(e).__name__+': '+str(e)]
                report.append({'sheet':str(path),'instrument_id':iid,'errors':errors})
                if not errors:claims.append(claim)
            # Failed rows cannot silently disappear into a superficially successful batch.
            dump(a.write.with_suffix('.report.json'),report)
            if any(r['errors'] for r in report):print(json.dumps(report,indent=2));return 1
            a.write.parent.mkdir(parents=True,exist_ok=True)
            with a.write.open('w',encoding='utf-8',newline='\n') as fh:
                for claim in claims:fh.write(json.dumps(claim,ensure_ascii=False,sort_keys=True)+'\n')
            print(json.dumps({'assembled':len(claims),'claims':str(a.write),'report':str(a.write.with_suffix('.report.json'))}));return 0
        if a.command=='check':
            report=[]
            for n,s in enumerate(a.claims.read_text('utf-8').splitlines(),1):
                if not s.strip():continue
                try:
                    claim=json.loads(s);d=load_dossier(out,claim['instrument_id']);errors=check_claim(claim,repo,d)
                except (ValueError,TypeError,KeyError) as e:errors=[str(e)]
                report.append({'line':n,'errors':errors})
            print(json.dumps(report,indent=2));return int(any(r['errors'] for r in report))
    except (ValueError,OSError,KeyError,TypeError) as e:
        print('claim-kit: '+str(e),file=sys.stderr);return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
