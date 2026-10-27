from pathlib import Path
import json,hashlib,datetime,time
r=Path('research/excavator/production-cost-trace-2026-10-26'); p=r/'packet-b2-correction-v9'
items=[]
def add(phase,path,seconds,key=None,qual=None):
 f=r/path
 items.append({'phase':phase,'receipt':str(f),'receipt_sha256':hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None,'observed_elapsed_seconds':seconds,'value_key':key,'qualification':qual,'active_agent_labor_seconds':None})
add('batch1 initial producer','recovery/production-claims-v5/TIMING_RECOVERED_FACTS.json',1106.511679879,'original_assignment.observed_elapsed_seconds','Two members,shared research counted once; export272.8s is contained, not additional.')
add('batch1 EO8514 correction producer','recovery/production-claims-v5/TIMING_RECOVERED_FACTS.json',120.275886263,'correction_v4.observed_elapsed_seconds')
add('batch1 initial source review through corrected version','recovery/recovered-production-review1/RECONSTRUCTED_PHASE_HISTORY.json',795.014373,None,'UTC envelope includes waits; disjoint phase details retained. Blind review465.492433s,after-reveal/source91.746099s,exact correction78.048452s are contained, not additional.')
add('batch1 producer first reset recovery','recovery/production-claims-v5/RECOVERY_DONE.json',803.436267981,'observed_worker_seconds','Includes reconstruction,validation and coordination waits; additional cost, not saving.')
add('batch1 reviewer first reset recovery','recovery/recovered-production-review1/RECOVERY_COST.json',232.5886691429987,'observed_seconds','Additional recovery; idle until final versions separately documented.')
add('batch1 exact new-version recovery review','recovery/review-v5/COST.new-v6.json',354.7069886190002,'observed_seconds','Additional exact-version review, includes72.360s alias correction.')
add('batch1 native completion','recovery/complete-b1-v1/TALLY.json',61.63915563699993,'wall_seconds','Machine execution inside coordinator envelope.')
add('batch2 initial producer','packet-b2-final-v8/producers/batch2/COST.v1.json',1391.012998615,'observed_worker_interval_seconds','Two members;437.443s export/check/failure/retry/audit is contained,not additional.')
add('batch2 source review and second reset recovery','recovery2/review2/COST.new.json',1801.004563,'observed_utc_seconds_start_to_costannex','Includes source findings,April hold,invalid/unscored control attempt,reset and preservation; source review seal1753.958195s is contained.')
add('batch2 April correction and second recovery timeline','packet-b2-correction-v9/producers/batch2/COST.corrected-v1.json',2032.758530601,'correction_recovery_timeline_elapsed_seconds','Includes blocking and idle, not continuous active worker interval;311.420s new export is contained. Overlaps initial reviewer and root recovery.')
add('batch2 fresh independent final source/control/after-reveal review','packet-b2-correction-v9/review-final/COST.final.json',799.860351,'observed_artifact_interval_seconds','Lower-bound occupancy;initial protocol reads unmeasured;633.302s blind interval is contained,not additional.')
if (r/'packet-b2-correction-v9/complete-v1/TALLY.json').exists():
 c=json.loads((r/'packet-b2-correction-v9/complete-v1/TALLY.json').read_bytes());add('batch2 native completion','packet-b2-correction-v9/complete-v1/TALLY.json',c['wall_seconds'],'wall_seconds','Machine execution inside coordinator envelope.')
if (r/'packet-b2-correction-v9/combined-four-replay-v1/RESULT.json').exists():
 c=json.loads((r/'packet-b2-correction-v9/combined-four-replay-v1/RESULT.json').read_bytes());add('combined four-case actual tracker replay','packet-b2-correction-v9/combined-four-replay-v1/RESULT.json',c['wall_seconds'],'wall_seconds','Machine execution inside coordinator envelope;isolated outputs.')
for label,folder in [('supplement engineering','engineering-v2'),('source notes engineering','source-notes-review'),('human citation coverage engineering','source-notes-human-gate-review'),('hash fix engineering','prior-hash-review')]:
 f=r/'recovery'/folder/'REVIEW.json'
 if f.exists():
  j=json.loads(f.read_bytes());items.append({'phase':label,'receipt':str(f),'receipt_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'recorded_timing_fields':{k:v for k,v in j.items() if any(x in k.lower() for x in ['second','elapsed','cost','time'])},'active_agent_labor_seconds':None,'qualification':'Engineering/retests additional; no presumed amortization.'})
start=json.loads((r/'ROOT_CLOCK_START.json').read_bytes());now=datetime.datetime.now(datetime.timezone.utc)
ledger={'schema':'eo-production-cost-ledger/v1','generated_utc':now.isoformat(),'coordinator_observed_envelope':{'start_utc':start['utc'],'end_utc':now.isoformat(),'utc_elapsed_seconds':(now-datetime.datetime.fromisoformat(start['utc'])).total_seconds(),'scope':'Coordinator gross envelope includes acquisitions,preparation,engineering,test,corrections,integration,publishing,two workspace resets,waits and overlapping worker execution. Not exclusive active labor; final publication may extend beyond timestamp.'},'observations':items,'tokens':None,'cache_tokens':None,'cash':None,'exclusive_agent_hours':None,'per_order_total_cost':None,'aggregate_rule':'Do not sum coordinator envelope,worker envelopes and contained machine/subphase intervals as a labor total. Shared sources counted once per recorded phase. Original missing bytes,unmeasured gaps and different phase definitions remain explicit.','net_total_agent_hour_reduction_established':False,'campaign_savings_established':False}
(p/'COST_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n');print(json.dumps({'observations':len(items),'coordinator_hours':ledger['coordinator_observed_envelope']['utc_elapsed_seconds']/3600}))
