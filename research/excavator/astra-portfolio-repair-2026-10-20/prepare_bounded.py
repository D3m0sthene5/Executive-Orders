"""Reproduce the seven-case, isolated preparation package; no claims published.

Run from the repository root. The existing batch preparer enforces ownership,
lossless encoding, source pins and new-directory semantics. New documents are
research leads and cannot establish an ending merely by entering this packet.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
import batch
from assemble import canonical_sha
from lifecycle_obligations import obligations, blocked_checkpoint, resume_decision, digest
sys.path.insert(0,str(ROOT/'jobs/source-ladder'))
from request_contract import normalize_request


def write(path,value):
    if path.exists():raise ValueError('Refusing to replace historical preparation: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def main():
    ids=['EO:13792','EO:13101','EO:13148','EO:13783','EO:13807','EO:11513','EO:13037']
    acquired=ROOT/'research/production/astra-portfolio-repair-2026-10-20/panizzi/live-probe'
    manifest=json.loads((acquired/'PRIMARY_FILES.json').read_text())
    dossiers={};input_pins={}
    for iid in ids:
        original=ROOT/'jobs/claim-kit/output/dossiers'/(iid.replace(':','_')+'.json')
        d=json.loads(original.read_text())
        if canonical_sha(d)!=d['fingerprint']:raise ValueError('Stale original dossier: '+iid)
        input_pins[original.relative_to(ROOT).as_posix()]=hashlib.sha256(original.read_bytes()).hexdigest()
        d['new_source_leads']=[]
        for row in manifest:
            if not row['wanted_id'].startswith('queue:'+iid+':'):continue
            binary=acquired/row['retained_file'];text_file=acquired/row['text_path']
            if hashlib.sha256(binary.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Changed primary document')
            text=text_file.read_text();eid='PERFORMANCE_LEAD:'+row['sha256'][:24]
            d['evidence'][eid]={'id':eid,'kind':'performance_document_lead','text':text,
                'char_start':0,'char_end':len(text),'established_ending':None,
                'source':{'url':row['url'],'sha256':row['sha256'],
                    'repo_path':binary.relative_to(ROOT).as_posix(),
                    'text_path':text_file.relative_to(ROOT).as_posix(),
                    'text_sha256':hashlib.sha256(text_file.read_bytes()).hexdigest(),
                    'evidence_tier':'document_text','acceptable_as_original':False},
                'notice':'Held document for clause-specific research; not this EO original, not an adopted performance date or legal ending.'}
            d['new_source_leads'].append(eid)
        d['lifecycle_obligations']=obligations(iid,d['clauses'],
            [d['evidence'][eid] for eid in d.get('own_terms',[])],
            [d['evidence'][eid] for eid in d.get('actor_provisions',[])])
        d['fingerprint']=canonical_sha(d)
        p=BASE/'isolated-dossiers-v1'/(iid.replace(':','_')+'.json')
        write(p,d);dossiers[iid]=p
    metrics=batch.prepare(ROOT,ROOT/'jobs/claim-kit/output',BASE/'bounded-preparation',ids,
        'astra-portfolio-repair',dossier_paths=dossiers,replacement_proposal=True)
    write(BASE/'PREPARATION_INPUTS.json',{'schema':'astra-bounded-preparation/v1',
        'upstream_dossiers_sha256':input_pins,'primary_manifest_sha256':hashlib.sha256((acquired/'PRIMARY_FILES.json').read_bytes()).hexdigest(),
        'claims_published':0,'owner_acceptance':False,'human_certified_added':0,'metrics':metrics})

    d=json.loads(dossiers['EO:11513'].read_text())
    requests=[json.loads(line) for line in (ROOT/'research/readiness/FETCH_QUEUE.jsonl').read_text().splitlines()
              if line.strip() and json.loads(line).get('instrument_id')=='EO:11513']
    validated=[normalize_request(r) for r in requests]
    if any(r['errors'] or not r['tasks'] for r in validated):raise ValueError('Blocked case has an invalid source request')
    routes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [ROOT/'jobs/source-ladder'/n for n in ['fetch_ladder.py','ladder_queue.py','report_dates.py','request_contract.py']]}
    route_sha=digest(routes)
    results=['research/excavator/lamm-2026-10-20/sunsets3/batch_01/OWN_TERM_END_RECORDS.jsonl',
             'research/excavator/lamm-2026-10-20/sunsets3/batch_01/review/REVIEW.jsonl']
    receipts=[{'instrument_id':'EO:11513','status':'source_blocked',
               'reason':'Actual report submission date remains unestablished; deadline is not the occurrence.'}]
    checkpoint=blocked_checkpoint(d,validated,route_sha,receipts[0]['reason'],results,receipts)
    write(BASE/'lamm-resume-v1/CHECKPOINT.json',checkpoint)
    write(BASE/'lamm-resume-v1/VALIDATED_REQUESTS.json',validated)
    write(BASE/'lamm-resume-v1/ROUTE_PINS.json',routes)
    write(BASE/'lamm-resume-v1/UNCHANGED_DECISION.json',resume_decision(checkpoint,d,validated,route_sha,receipts))
    print(json.dumps({'orders':len(ids),'new_primary_documents':len(manifest),
        'claims_published':0,'unchanged_blocked_work':'deferred','packet':str(BASE/'bounded-preparation/PACKET.json')}))


if __name__=='__main__':main()
