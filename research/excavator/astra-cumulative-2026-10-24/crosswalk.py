"""One case-reconciliation crosswalk of existing checkpoint and claim schemas."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT/'research/readiness/reviews/astra-2026-10-18'
def canonical(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def pin(p):
    return {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

checkpoint = json.loads((OLD/'CHECKPOINT_BATCH1_AUDIT.json').read_text())
selection = json.loads((OLD/'BATCH1_SELECTION.json').read_text())
current = {}
for p in sorted((ROOT/'research/readiness/claims').glob('*.jsonl')):
    for n,line in enumerate(p.read_text().splitlines(), 1):
        if not line.strip(): continue
        c = json.loads(line)
        current[c['instrument_id']] = (c, str(p.relative_to(ROOT)), n)
tracker_path = ROOT/'jobs/leverage-campaign-check/output/shared-source/readiness-tracker/READINESS_BY_ORDER.csv'
tracker = {r['instrument_id']: r for r in csv.DictReader(tracker_path.open())}
locks = json.loads((ROOT/'research/readiness/CLAIM_KIT_LOCK.json').read_text())['orders']
rows = []
for row in checkpoint['rows']:
    if not row['produced']: continue
    iid = row['instrument_id']; folder = 'EO_'+iid.split(':')[1]
    version = selection.get(iid, {}).get('version')
    selected = OLD/'producer'/folder
    if version: selected /= version
    selected /= 'claim.json'
    old = json.loads(selected.read_text())
    c, path, line = current.get(iid, ({}, None, None))
    versions = {}
    for p in (OLD/'producer'/folder).rglob('claim.json'):
        v=json.loads(p.read_text());versions.setdefault(canonical(v),[]).append(str(p.relative_to(ROOT)))
    original_hashes = lambda x: sorted({s.get('original_source',{}).get('sha256','') for s in x.get('operative_clauses',[])})
    rows.append({'instrument_id':iid,'historical_checkpoint_verdict':row['verdict'],
        'selected_claim':pin(selected),'selected_canonical_sha256':canonical(old),
        'matches_checkpoint_hash':canonical(old)==row['claim_sha256'],
        'distinct_historical_versions':len(versions),'version_paths':versions,
        'historical_gaps':old.get('unresolved_material_gaps',[]),
        'current_canonical':{'path':path,'line':line,'claim_sha256':canonical(c) if c else None,
                             'gaps':c.get('unresolved_material_gaps',[])},
        'same_original_raw_versions':bool(c) and original_hashes(old)==original_hashes(c),
        'PR56_overlap':iid in {'EO:11022','EO:11256','EO:11782','EO:11829'},
        'baseline_steps_done':tracker.get(iid,{}).get('steps_done'),
        'baseline_blockers':tracker.get(iid,{}).get('blockers'),
        'active_reservation':locks.get(iid),
        'action':'current reconciliation and independent review' if iid in {'EO:11782','EO:9452'} else 'attributed prior research exposed; no closure inferred',
        'qualification':'Historical whole-case AI verdict does not approve a component or override current rules; align scope/source/proposition before reuse.'})
other=[]
for p in sorted(OLD.glob('producer/*/IN_PROGRESS.json')):
    d=json.loads(p.read_text());other.append({'artifact':pin(p),'schema':d.get('schema'),'instrument_id':d.get('instrument_id'),'keys':sorted(d),'qualification':'unfinished producer work; no approval inferred'})
p=ROOT/'research/excavator/astra-portfolio-repair-2026-10-20/lamm-resume-v1/CHECKPOINT.json'
d=json.loads(p.read_text());other.append({'artifact':pin(p),'schema':d['schema'],'instrument_id':d['instrument_id'],'reason':d['reason'],'result_paths':d['result_paths'],'qualification':'existing source-blocked resume checkpoint and retained negative finding; not a new search or permanent ownership'})
result={'schema':'eo-research-crosswalk/v1','input_head':'9ecddf9fe82a1989c6133610a77308ec74454184','legal_cutoff':'2026-10-14',
        'checkpoint':pin(OLD/'CHECKPOINT_BATCH1_AUDIT.json'),'selected_versions':pin(OLD/'BATCH1_SELECTION.json'),
        'tracker_baseline':pin(tracker_path),'rows':rows,'additional_checkpoint_formats':other,
        'automatic_approvals':0,'savings_hours_claimed':None,'notice':'Prior-work reconciliation, not optimizer scoring or a count of completed obligations.'}
(OUT/'PRIOR_WORK_CROSSWALK.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
with (OUT/'PRIOR_WORK_CROSSWALK.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['instrument_id','historical_verdict','historical_versions','historical_gaps','current_claim','current_gaps','PR56_overlap','baseline_steps_done','active_reservation','action'])
    for r in rows:w.writerow([r['instrument_id'],r['historical_checkpoint_verdict'],r['distinct_historical_versions'],len(r['historical_gaps']),r['current_canonical']['path'],len(r['current_canonical']['gaps']),r['PR56_overlap'],r['baseline_steps_done'],r['active_reservation'],r['action']])
print(json.dumps({'checkpoint_cases':len(rows),'PR56_overlaps':sum(r['PR56_overlap'] for r in rows),'all_selected_hashes_match':all(r['matches_checkpoint_hash'] for r in rows),'additional_checkpoint_records':len(other),'active_reservations':sum(bool(r['active_reservation']) for r in rows)}))
