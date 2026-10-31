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
from assemble import blank_sheet, assemble, check_claim, canonical_sha
from build import build, dump, filename

HERE=Path(__file__).resolve().parent

def read(path,default=None):
    if not path.exists():return default
    return json.loads(path.read_text('utf-8'))

def load_dossier(out,iid,repo=None):
    row=next((r for r in read(out/'INDEX.json',[]) if r['instrument_id']==iid),None)
    if row is None:
        if repo is None:raise ValueError('Order absent from current decided INDEX: '+iid)
        import status_overlay
        return status_overlay.prepare_evidence(repo,out,iid)['base_dossier']
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

def pick(repo,out,agent,n,excluded=None,scope='all'):
    if n<1 or not re.fullmatch(r'[A-Za-z0-9_.-]+',agent):raise ValueError('agent must be a simple name and n positive')
    index=read(out/'INDEX.json',[]);by={r['instrument_id']:r for r in index}
    if not index:raise ValueError('Corpus INDEX.json missing or empty')
    if scope not in ('all','decided','undecided'):raise ValueError('unknown selection scope')
    if scope!='decided':
        histories={r['instrument_id']:r for r in read(repo/'jobs/status-history/output/INDEX.json',[])}
        summary=out/'SUMMARY.json'
        import hashlib
        summary_sha=hashlib.sha256(summary.read_bytes()).hexdigest() if summary.exists() else None
        for path in sorted(out.glob('STATUS_LEADS*.jsonl')):
            with path.open(encoding='utf-8') as fh:
                for line in fh:
                    if not line.strip():continue
                    lead=json.loads(line);iid=lead.get('instrument_id')
                    if iid not in by and iid in histories and lead.get('status') is None:
                        by[iid]={'instrument_id':iid,'status':None,'fingerprint':None,
                            'history_sha256':histories[iid]['fingerprint'],'compiled_summary_sha256':summary_sha}
    if scope=='undecided':by={iid:r for iid,r in by.items() if r.get('status') is None}
    from batch import owners,family_groups
    excluded=set(excluded or [])|existing_claims(repo)|set(owners(repo))
    families=read(out/'FAMILIES.json',[])
    # Rank actual remaining unlocks, never the obsolete original family size.
    with reservations(repo) as locks:
        unavailable=excluded|set(locks['orders'])
        eligible={iid for iid,row in by.items() if iid not in unavailable}
        ranked=[];candidate_dossiers={}
        for f in families:
            if not f['family_id'].startswith('actor:'):continue
            members=sorted(iid for iid in set(f['instrument_ids'])&eligible if by[iid].get('dossier'))
            for iid in members:
                if iid not in candidate_dossiers:
                    d=read(out/by[iid]['dossier'])
                    if not d or d.get('fingerprint')!=by[iid]['fingerprint'] or d.get('fingerprint')!=canonical_sha(d):
                        raise ValueError('Stale dossier while grouping: '+iid)
                    candidate_dossiers[iid]=d
        for f in family_groups(candidate_dossiers):
            members=sorted({m['instrument_id'] for m in f['members']})
            if len(members)>=2:ranked.append((members,f['family_id']))
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
            if by[iid].get('status') is None:
                locks['orders'][iid].update({k:by[iid][k] for k in ('history_sha256','compiled_summary_sha256')})
        return [{'instrument_id':iid,**locks['orders'][iid],
            'dossier':str(out/by[iid]['dossier']) if by[iid].get('dossier') else None,
            'preparation_route':'decided_dossier' if by[iid].get('status') is not None else 'frozen_full_undecided_dossier',
            'whole_order_status':by[iid].get('status')} for iid in selected]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=HERE.parents[1]);p.add_argument('--output',type=Path)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('build')
    s=sub.add_parser('next');s.add_argument('--agent',required=True);s.add_argument('--n',type=int,default=20);s.add_argument('--exclude',type=Path);s.add_argument('--scope',choices=('all','decided','undecided'),default='all')
    for cmd in ('dossier','sheet'):
        s=sub.add_parser(cmd);s.add_argument('instrument_id');s.add_argument('--agent',default='');s.add_argument('--write',type=Path)
    s=sub.add_parser('history');s.add_argument('instrument_id');s.add_argument('--full',action='store_true')
    s=sub.add_parser('status-sheet');s.add_argument('instrument_id');s.add_argument('--agent',required=True);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('prepare');s.add_argument('instrument_ids',nargs='+');s.add_argument('--agent',required=True);s.add_argument('--write',type=Path,required=True);s.add_argument('--replacement-proposal',action='store_true')
    s=sub.add_parser('apply');s.add_argument('packet',type=Path);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('batch-check');s.add_argument('packet',type=Path);s.add_argument('applied',type=Path)
    s=sub.add_parser('complete');s.add_argument('manifest',type=Path);s.add_argument('--write',type=Path,required=True);s.add_argument('--publish',action='store_true')
    for key in ('history','base-commit','write'):
        s.add_argument('--diagnostic-'+key)
    for key in ('final','research-attempt','effort','checkpoint','question'):
        s.add_argument('--diagnostic-'+key,action='append',default=[])
    s=sub.add_parser('publication-audit');g=s.add_mutually_exclusive_group();g.add_argument('--base',default='origin/main');g.add_argument('--merge-commit')
    s=sub.add_parser('view');s.add_argument('packet',type=Path);g=s.add_mutually_exclusive_group();g.add_argument('--order');g.add_argument('--source')
    s=sub.add_parser('overlay-prepare');s.add_argument('instrument_id');s.add_argument('--agent',required=True);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('overlay-review-sheet');s.add_argument('--evidence',type=Path,required=True);s.add_argument('--decision',type=Path,required=True);s.add_argument('--reviewer',required=True);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('overlay-propose');s.add_argument('--evidence',type=Path,required=True);s.add_argument('--decision',type=Path,required=True);s.add_argument('--review',type=Path,required=True);s.add_argument('--lifecycle-sheet',type=Path);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('overlay-assemble');s.add_argument('bundle',type=Path);s.add_argument('--sheet',type=Path,required=True);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('overlay-check');s.add_argument('bundle',type=Path);s.add_argument('claims',type=Path)
    s=sub.add_parser('assemble');s.add_argument('sheets',nargs='+',type=Path);s.add_argument('--write',type=Path,required=True)
    s=sub.add_parser('check');s.add_argument('claims',type=Path)
    sub.add_parser('status')
    s=sub.add_parser('release');s.add_argument('--agent',required=True);s.add_argument('instrument_ids',nargs='+')
    a=p.parse_args(argv);repo=a.repo.resolve();out=(a.output or repo/'jobs/claim-kit/output').resolve()
    try:
        if a.command=='publication-audit':
            from completion import publication_audit
            result=publication_audit(repo,None if a.merge_commit else a.base,a.merge_commit);print(json.dumps(result,ensure_ascii=False,indent=2));return int(not result['ok'])
        if a.command=='complete':
            from completion import complete
            diagnosis={key.removeprefix('diagnostic_'):value for key,value in vars(a).items() if key.startswith('diagnostic_')}
            diagnosis=diagnosis if any(diagnosis.values()) else None
            result=complete(repo,a.manifest,a.write,publish=a.publish,diagnosis=diagnosis)
            print(json.dumps({k:v for k,v in result.items() if k!='outcomes'},ensure_ascii=False,indent=2))
            return int(result['exceptions']>0)
        if a.command.startswith('overlay-'):
            import status_overlay as overlay
            if a.command in ('overlay-assemble','overlay-check'):
                bundle=overlay._destination(repo,a.bundle)
                evidence=read(bundle/'EVIDENCE.json');decision=read(bundle/'STATUS_DECISION.json')
                review=read(bundle/'STATUS_REVIEW.json');proposal=read(bundle/'PROMOTION_PROPOSAL.json')
                if a.command=='overlay-assemble':
                    dest=a.write.resolve()
                    if dest.exists() or not dest.is_relative_to(bundle):raise ValueError('new working claim must stay under isolated overlay bundle')
                    claim,errors=overlay.assemble_working(repo,read(a.sheet),proposal,decision,review,evidence)
                    if errors:print(json.dumps({'errors':errors,'claims_published':0}));return 1
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes((json.dumps(claim,ensure_ascii=False,sort_keys=True)+'\n').encode())
                    print(json.dumps({'working_claim':str(dest),'experimental_only':True,'claims_published':0}));return 0
                rows=[]
                for number,line in enumerate(a.claims.read_text('utf-8').splitlines(),1):
                    if line.strip():rows.append({'line':number,'errors':overlay.check_working_claim(repo,json.loads(line),proposal,decision,review,evidence)})
                print(json.dumps({'checked':len(rows),'failures':[r for r in rows if r['errors']],'experimental_only':True,'claims_published':0}))
                return int(not rows or any(r['errors'] for r in rows))
            if a.command=='overlay-prepare':
                if a.write.exists():raise ValueError('Overlay destination exists; refusing overwrite')
                mod=overlay._history_module(repo);packet=mod.show(repo/'jobs/status-history/output',a.instrument_id)
                telemetry={};evidence=overlay.freeze_evidence(repo,out,packet,telemetry)
                dest=overlay._destination(repo,a.write);dest.mkdir(parents=True)
                dump(dest/'EVIDENCE.json',evidence);dump(dest/'STATUS_DECISION.json',overlay.extend_decision(packet,evidence,a.agent))
                dump(dest/'FREEZE_TELEMETRY.json',telemetry)
                print(json.dumps({'instrument_id':a.instrument_id,'evidence_fingerprint':evidence['fingerprint'],'folder':str(dest),'statuses_published':0}));return 0
            evidence=read(a.evidence);decision=read(a.decision)
            if a.command=='overlay-review-sheet':
                if a.write.exists():raise ValueError('Review sheet exists; refusing overwrite')
                dump(a.write,overlay.blank_review(decision,evidence,a.reviewer));print(str(a.write));return 0
            review=read(a.review);proposal=overlay.propose(repo,decision,review,evidence)
            result=overlay.write_bundle(repo,a.write,proposal,decision,review,evidence,
                lifecycle_sheet=read(a.lifecycle_sheet) if a.lifecycle_sheet else None)
            print(json.dumps({'proposal_fingerprint':proposal['fingerprint'],'folder':str(a.write),'owner_acceptance':proposal['owner_acceptance'],'statuses_published':0}));return 0
        if a.command=='view':
            import batch
            print(batch.view(repo,a.packet,a.order,a.source));return 0
        if a.command in ('prepare','apply','batch-check'):
            import batch
            if a.command=='prepare':result=batch.prepare(repo,out,a.write,a.instrument_ids,a.agent,replacement_proposal=a.replacement_proposal)
            elif a.command=='apply':result=batch.apply(repo,a.packet,a.write)
            else:result=batch.check(repo,a.packet,a.applied)
            failed=(result.get('strict_claim_fail',0)>0 or result.get('counts',{}).get('rejected',0)>0)
            actual=result.get('actual_claim_checker',{})
            if a.command=='batch-check':failed=failed or actual.get('claims_all_checks_passed',0)!=result.get('claims_checked',0)
            print(json.dumps(result,ensure_ascii=False,indent=2));return int(failed)
        if a.command in ('history','status-sheet'):
            # Reuse the status-history producer; this creates no rival dossier,
            # claim assembler or automatic provisional-status publication path.
            import importlib.util
            spec=importlib.util.spec_from_file_location('claim_kit_status_history',repo/'jobs/status-history/history.py')
            mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
            packet=mod.show(repo/'jobs/status-history/output',a.instrument_id)
            validation=mod.validate_packet(repo,packet)
            if validation:raise ValueError('Status-history source validation failed: '+str(validation))
            if a.command=='history':
                print(json.dumps(packet,ensure_ascii=False,indent=2) if a.full else mod.canon(mod.compact(packet)))
            else:
                if a.write.exists():raise ValueError('Status decision exists; refusing overwrite')
                dump(a.write,mod.blank_decision(packet,a.agent));print(str(a.write))
            return 0
        if a.command=='build':build(repo,out,os.environ.get('JOB_CACHE_DIR'));return 0
        if a.command=='next':
            excluded=read(a.exclude,[]) if a.exclude else []
            print(json.dumps(pick(repo,out,a.agent,a.n,excluded,a.scope),indent=2));return 0
        if a.command in ('dossier','sheet'):
            d=load_dossier(out,a.instrument_id,repo)
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
            warnings=summary.pop('warnings',[])
            summary['warnings_count']=len(warnings)
            summary['warnings_file']=str(out/'SUMMARY.json')
            summary['committed_claim_identities']=len(existing_claims(repo))
            locked=read(repo/'research/readiness/CLAIM_KIT_LOCK.json',{}).get('orders',{})
            summary['reserved_orders']=len(locked)
            summary['reservations_by_agent']={name:sum(r.get('agent')==name for r in locked.values())
                for name in sorted({r.get('agent','unassigned') for r in locked.values()})}
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
