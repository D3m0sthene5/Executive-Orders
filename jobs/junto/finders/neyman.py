"""Thin registered NEYMAN aggregate finder, using Junto's existing CLI contract."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve();REPO=HERE.parents[3]
sys.path.insert(0,str(HERE.parents[1]))
from contracts import validate_contract
from junto import privacy_problems

ALLOWED={'schema','manifest_sha256','frame_population','attempts','outcomes','blocker_counts','shared_events',
         'active_phase_coverage','api_token_valuation_usd','actual_cash_expenditure_usd'}
TEMPLATES=[
 ('neyman_shared_acquisition_once','shared_acquisition','Shared-source acquisition and preparation once',
  'Shared source acquisition followed by per-order evidence handling without a reuse receipt.',
  'One acquisition plus a hashed reuse receipt for each downstream order.',
  'Use identical source bytes, attribution and order-specific checks; independent review must show no increased rejection rate.'),
 ('neyman_prerequisite_batch','missing_prerequisites','Test paired prerequisite closures before production',
  'Production attempts start with the current committed prerequisite state.',
  'Acquire the named pair of missing prerequisites before the same matched attempt.',
  'Same selected cases, legal codebook, checker and independent review; measure usable outcomes per attempt including failures.'),
 ('neyman_blocked_handoff','blocked_attempts','Compact handoff for blocked research attempts',
  'Resume blocked work by rereading its full previous dossier and acquisition history.',
  'Resume using a hash-pinned gap receipt plus the same required source inspection.',
  'Every unresolved blocker and prior failure remains visible; independent review must show no increased omission or rejection rate.')]


def candidates(agg):
    if not isinstance(agg,dict) or set(agg)!=ALLOWED or agg.get('schema')!='neyman.aggregate/1':raise ValueError('sanitized aggregate schema required')
    if len(agg.get('manifest_sha256',''))!=64:raise ValueError('missing manifest hash')
    if not 0<=agg['attempts']<=24 or agg['frame_population']<agg['attempts']:raise ValueError('invalid counts')
    if privacy_problems(agg):raise ValueError('aggregate privacy failure')
    result=[]
    for key,cause,title,baseline,treatment,quality in TEMPLATES:
        c={'saver_key':key,'title':title,'targets':[cause],'status':'unverified','rev':0,
           'origin':'owner-seeded','origin_reference':'NEYMAN owner implementation request, 2026-10-20',
           'evidence':[{'cause_key':cause,'attempts':agg['attempts'],'frame_population':agg['frame_population'],
                        'aggregate':'jobs/neyman-pilot/output/JUNTO_AGGREGATE.json'}],
           'estimate':{'usd_per_session':None,'tokens_per_session':None,'basis':'No measured efficiency comparison; workload is not a saving.'},
           'proposed_test':treatment,
           'test_contract':{'schema':'junto.test-contract/1','unit_of_work':'investigated_order_attempt',
                'baseline':baseline,'quality_requirement':quality,
                'stopping_rule':'Stop at 12 matched attempts per arm or 30 seconds per attempt; retain blocked/censored cases. Stop verification when telemetry or independent quality data are missing.',
                'result_location':'research/neyman/efficiency-tests/'+key+'.json'}}
        validate_contract(c)
        if privacy_problems(c):raise ValueError('candidate privacy failure')
        result.append(c)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--profiles',type=Path)
    a=p.parse_args();start=time.monotonic()
    if a.data.resolve().is_relative_to(REPO):return 3
    try:
        path=a.data/'NEYMAN_AGGREGATE.json';raw=path.read_bytes();records=candidates(json.loads(raw))
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(''.join(json.dumps(c,sort_keys=True)+'\n' for c in records))
        Path(str(a.out)+'.run.json').write_text(json.dumps({'finder_id':'F-neyman','finder_version':'1','run_id':a.run_id,
            'wall_seconds':time.monotonic()-start,'inputs':{'sanitized_aggregates':1,'attempts':json.loads(raw)['attempts']},
            'data_digest':hashlib.sha256(raw).hexdigest(),'usd_spent':None}))
    except (OSError,ValueError,TypeError,KeyError):return 2
    print('neyman: 3 owner-seeded candidates, all unverified; no savings credited')
    return 0


if __name__=='__main__':raise SystemExit(main())
