"""Read-only ownership/scope screening. No reservation or finding is created."""
import csv, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def records(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
def csvs(path):
    return list(csv.DictReader(path.open(encoding='utf-8',newline='')))
owned={}
claude_ids=set()
for p in sorted((ROOT/'research/readiness/claims').glob('*.jsonl')):
    for c in records(p): owned[c['instrument_id']]=p.name
    if p.name.startswith('claude-'):
        claude_ids.update(re.findall(r'EO[:_ ]+(\d+[A-Za-z]?)',p.read_text(encoding='utf-8')))
report_ids=set()
for p in (ROOT/'research/excavator/2026-10-18').rglob('*.md'):
    report_ids.update('EO:'+x for x in re.findall(r'\bEO\s*[:_ ]?\s*(\d+[A-Za-z]?)\b',p.read_text(encoding='utf-8')))
ready={r['instrument_id']:r for r in csvs(ROOT/'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv')}
todo={r['instrument_id']:r for r in csvs(ROOT/'jobs/claim-drafts/output/TODO_BY_ORDER.csv')}
rules=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'research/readiness/rules').glob('*.json')]
eligible=[]
for rule in rules:
    actor=rule['acting_id']
    if actor.split(':')[-1] in claude_ids: continue
    targets=rule.get('scope',{}).get('targets',[])
    for iid in targets:
        if iid in owned or iid in report_ids or iid not in todo: continue
        r=todo[iid]
        eligible.append({'id':iid,'actor':actor,'only_judgment_left':r.get('only_judgment_left'),
                         'estimated_effort':r.get('estimated_effort'),'status':r.get('provisional_status'),
                         'blockers':ready.get(iid,{}).get('blockers'),'todo':r})
out={'other_owned_count':len(owned),'excavator_report_named_ids':sorted(report_ids),
     'claude_rule_actor_exclusions':sorted(rule['acting_id'] for rule in rules if rule['acting_id'].split(':')[-1] in claude_ids),
     'eligible':eligible,
     'own_claims':{i:f for i,f in owned.items() if f.startswith('astra-')}}
(Path(__file__).parent/'TARGET_SCREEN.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'eligible_count':len(eligible),'eligible':[{k:v for k,v in r.items() if k!='todo'} for r in eligible],
                  'own_claims':out['own_claims'],'excluded_report_count':len(report_ids),
                  'claude_rule_actor_exclusions':out['claude_rule_actor_exclusions']},indent=2))
