"""Run frozen sample attempts with hard subprocess deadlines and explicit missingness."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from survey import PHASES,TOKEN_CATEGORIES,check_pins,csv_rows,lines,report,sha,write


def run(root,manifest,out,config):
    root=Path(root).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    check_pins(root,manifest['input_hashes']);t0=time.monotonic()
    ids={s['instrument_id'] for s in manifest['sample']}
    index={r['instrument_id']:r for r in json.loads((root/'jobs/claim-kit/output/INDEX.json').read_text()) if r['instrument_id'] in ids}
    leads={}
    with (root/'jobs/claim-kit/output/STATUS_LEADS.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if r['instrument_id'] in ids:leads[r['instrument_id']]=r
    access=defaultdict(list)
    for r in csv_rows(root/'jobs/source-ladder/output/RESULTS.csv'):
        if r['result']!='found' and re.search('robots|denied|subscription|access|permission|captcha',r.get('why',''),re.I):
            for iid in r['instrument_ids'].split('|'):
                if iid.strip() in ids:access[iid.strip()].append({'wanted_id':r['wanted_id'],'result':r['result'],'reason_class':'unresolved_access'})
    prepared={'index':index,'leads':leads,'access':dict(access)}
    shared=[{'event_id':'pilot-preparation','phase':'preparation','active_seconds':None,'access_wait_seconds':0,
             'machine_seconds':time.monotonic()-t0,'downstream_uses':sorted(ids),'coverage':'machine preparation only',
             'tokens':dict.fromkeys(TOKEN_CATEGORIES),'api_valuation_usd':None,'cash_expenditure_usd':None}]
    observations=[]
    with tempfile.TemporaryDirectory(prefix='neyman-attempt-') as td:
        td=Path(td)
        for i,member in enumerate(manifest['sample']):
            a=td/f'{i}.json';b=td/f'{i}-result.json'
            write(a,{'manifest':manifest,'member':member,'prepared':prepared,'byte_limit':config['source_read_limit_bytes']})
            start=time.monotonic()
            try:
                p=subprocess.run([sys.executable,'-I',str(root/'jobs/neyman/attempt.py'),'--root',str(root),'--input',str(a),'--out',str(b)],
                                 timeout=manifest['attempt_limit_seconds'],capture_output=True,text=True)
                if p.returncode:raise ValueError('attempt failed: '+p.stderr[-400:])
                o=json.loads(b.read_text())
            except (subprocess.TimeoutExpired,ValueError) as exc:
                censored=isinstance(exc,subprocess.TimeoutExpired)
                o={'schema':'neyman.observation/1','instrument_id':member['instrument_id'],
                   'manifest_sha256':manifest['manifest_sha256'],'outcome':'censored_limit' if censored else 'unsuccessful',
                   'right_censored':censored,'completion_effort_seconds':None,'phases':{
                       phase:{'active_seconds':None,'access_wait_seconds':None,'machine_seconds':None,
                              'coverage':'unavailable after interrupted attempt','tokens':dict.fromkeys(TOKEN_CATEGORIES)} for phase in PHASES},
                   'shared_event_ids':['pilot-preparation'],'correlation_keys':member['families'],
                   'failure_class':'attempt_deadline' if censored else 'invalid_or_missing_packet',
                   'residual_open_steps':member['open_steps'],'residual_blockers':member['blockers']}
            # End-to-end subprocess envelope includes startup/serialization; do not add its inner phases twice.
            envelope=time.monotonic()-start
            measured=sum(p['machine_seconds'] or 0 for p in o['phases'].values())
            o['phases']['coordination'].update(machine_seconds=max(0,envelope-measured),coverage='measured subprocess overhead; agent effort unavailable')
            o['attempt_wall_seconds']=envelope;observations.append(o)
            lines(out/'OBSERVATIONS.jsonl',observations)
    integration=time.monotonic()
    check_pins(root,manifest['input_hashes'])
    shared.append({'event_id':'pilot-integration','phase':'integration','active_seconds':None,'access_wait_seconds':0,
                   'machine_seconds':time.monotonic()-integration,'downstream_uses':sorted(ids),'coverage':'input revalidation only; later report/runner overhead excluded',
                   'tokens':dict.fromkeys(TOKEN_CATEGORIES),'api_valuation_usd':None,'cash_expenditure_usd':None})
    for o in observations:o['shared_event_ids'].append('pilot-integration')
    lines(out/'OBSERVATIONS.jsonl',observations);lines(out/'SHARED_COSTS.jsonl',shared)
    uncertainty=report(manifest,observations,shared);write(out/'UNCERTAINTY.json',uncertainty)
    write(out/'SUMMARY.json',{'attempts':len(observations),'complete_dossiers':sum(o['outcome']=='complete' for o in observations),
                             'outcomes':dict(Counter(o['outcome'] for o in observations)),'legal_decisions_added':0,
                             'human_certifications_added':0,'manifest_sha256':manifest['manifest_sha256'],
                             'api_metering':'unavailable','observed_model_api_calls':0})
    return observations,uncertainty
