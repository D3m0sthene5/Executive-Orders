"""Explicit output-only consumer: frozen NEYMAN pilot, production replay and Junto."""
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
root=Path(os.environ.get('REPO_ROOT',HERE.parents[1])).resolve();out=Path(os.environ.get('OUTPUT_DIR',HERE/'output'))
out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'jobs/neyman'));sys.path.insert(0,str(root/'jobs/corpus-excavator'))
from survey import verify_manifest,check_pins,csv_rows,frame,sha,write
from pilot import run
from opportunities import aggregate
from combinations import load_tracker,replay,validate_predictions,historical_batches

subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(root/'jobs/junto'),'-p','test_*.py'],check=True)
manifest=json.loads((root/'research/neyman/pilot-20261020/MANIFEST.json').read_text())
verify_manifest(manifest)
check_pins(root,manifest['input_hashes'])
# Always compare against the real tracker, including exact blocker strings.
tracker=load_tracker(root);live,problems=tracker.build(str(root));committed=csv_rows(root/'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv')
fields=list(committed[0])
if [{k:str(r[k]) for k in fields} for r in live]!=committed:raise ValueError('stale committed tracker; run explicit consumer first')
observations,uncertainty=run(root,manifest,out,json.loads((root/'jobs/neyman/config.json').read_text()))
rows,counts=frame(root)
# Small owner-seeded combinations; closing a source does not close a legal claim.
proposals=[]
for key,step in [('original','original_text'),('basis','ending_or_current_basis'),('shared','shared_sources')]:
    closures={s['instrument_id']:[step] for s in manifest['sample'] if step in s['open_steps']}
    if closures:proposals.append({'key':key,'origin':'owner-seeded','assumption':'Assume '+step+' is satisfied for listed sampled orders; planning only, not evidence.','closures':closures})
_,combos=replay(root,proposals)
write(out/'COMBINATIONS.json',{'planning_only':True,'canonical_changes':0,'combinations':combos})
# Frozen no-intervention predictions tested after prospective attempts. An offline
# investigation cannot validate the causal effects of hypothetical acquisitions.
after,_=tracker.build(str(root))
pred=[{'instrument_id':s['instrument_id'],'residual_open_steps':s['open_steps']} for s in manifest['sample']]
validation={'prospective_no_intervention':validate_predictions(pred,after),
            'prospective_closure_effects':'unavailable: pilot acquired no new prerequisite evidence',
            'historical_batches':historical_batches(root,[
              'research/excavator/2026-10-18/batch-pilot/tracker-replay-v2/A_INDEPENDENTLY_ACCEPTED',
              'research/excavator/2026-10-18/batch-pilot/tracker-replay-v2/B_INDEPENDENTLY_ACCEPTED']),
            'historical_samples_representative':False,
            'historical_unique_orders':1,'historical_warning':'Both accepted arms reuse EO12720; not two independent successes or a representative sample.'}
write(out/'PREDICTION_VALIDATION.json',validation)
aggregate(manifest,rows,uncertainty,out/'JUNTO_AGGREGATE.json')
# Existing Junto requires --data outside the repo. Only a whitelist aggregate is
# staged there. Ledger mutations remain inside this job's output directory.
ledger=out/'junto-ledger';ledger.mkdir(exist_ok=True)
for p in (root/'jobs/junto/ledger').iterdir():
    if p.is_file():shutil.copyfile(p,ledger/p.name)
with tempfile.TemporaryDirectory(prefix='neyman-sanitized-') as td:
    shutil.copyfile(out/'JUNTO_AGGREGATE.json',Path(td)/'NEYMAN_AGGREGATE.json')
    base=[sys.executable,'-I',str(root/'jobs/junto/junto.py'),'--ledger',str(ledger),'--output',str(out/'junto')]
    for args in [('run','--data',td,'--finder','neyman'),('score',),('check',)]:
        subprocess.run(base+list(args),check=True)
board=json.loads((out/'junto/SCOREBOARD.json').read_text())
if next(f for f in board['finders'] if f['finder_id']=='F-neyman')['verified_usd']!=0:raise ValueError('unverified Neyman savings credited')
# Full consumed metadata unchanged through every replay and consumer.
check_pins(root,manifest['input_hashes'])
write(out/'INTEGRATION.json',{'canonical_input_hashes_unchanged':True,'actual_tracker_matches_committed':True,
                            'canonical_ready':counts['ready_for_human_review'],'cases_attempted':len(observations),
                            'prospective_residual_matches':sum(r['residual_match'] for r in validation['prospective_no_intervention']),
                            'junto_candidates_registered':3,'junto_verified_savings':0,'claim_or_status_writes':0,
                            'human_certifications_added':0,'quality_gate_missing_data_regression':'tested'})
(out/'REPORT.md').write_text(f'''# NEYMAN bounded pilot

Known inventory: {counts['orders_total']:,} orders, {len(rows):,} unfinished; {uncertainty['joint_cells']:,} actual joint strata.
The frozen seed selected {len(observations)} attempts in {len(manifest['macro_allocation'])} era/status macro strata.
Outcomes: {json.dumps(uncertainty['outcomes'],sort_keys=True)}. No completed legal dossiers or human certifications were added.

This pilot measured an offline prerequisite investigation. Machine execution lower bound: {uncertainty['observed_machine_seconds_lower_bound']:.3f} seconds, including shared preparation/integration once.
Active agent effort, full independent review, correction, campaign coordination, token categories, API token valuation and actual cash expenditure are unavailable.
No population completion total, confidence interval or completion date is justified. Blocked attempts remain in the denominator; their completion effort is null.
The current Junto configuration has a $10 API-value round and 20% nominal exploration share ($2), without an assigned NEYMAN allocation. The job makes no model API calls. Session-level valuation/cash and allowance compliance cannot be measured here.

{len(combos)} planning-only prerequisite combinations invoked the real tracker. They created no canonical evidence. The 24 frozen no-intervention residual predictions are checked against the actual tracker.
Two historical accepted batches are replayed on current held metadata; both contain the same EO12720. Their baseline drift and residual comparisons are reported separately. These retrospective checks do not establish legal correctness or validate future acquisition effects.

Three owner-seeded saver hypotheses were registered in the output-scoped Junto ledger, with prospective test contracts. All remain unverified with zero credited savings.
Junto now treats missing, partial, negative or zero-denominator quality counts as insufficient to verify a saving. There was no measured efficiency test in this pilot.

Unresolved access dependencies are separate from missing research prerequisites. Human review remains unmeasured. Historical census recovery beyond this inventory is incompletely bounded and excluded from the sample and effort totals.
Sampling guides the campaign; exhaustive research and the human-certification boundary remain required.
''')
print('NEYMAN pilot integration complete; all new hypotheses unverified')
