import json
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent
def load(p): return json.loads(p.read_text(encoding='utf-8'))
for p in sorted((BASE/'dossiers').glob('*.json')):
    d=load(p);s=load(BASE/'producer/decisions'/p.name)
    print('\nCASE',d['instrument_id'],'fingerprint',d['fingerprint'])
    for k in ['own_terms','conflicts','current_law_leads','machine_searches','missing']:
        print(k,json.dumps(d[k],ensure_ascii=False))
    print('EVIDENCE_INDEX')
    for k,e in d['evidence'].items():
        source=e.get('source',e.get('actor_source',{}))
        print(k,'keys',list(e),'source',source)
    print('DECISION_HEADER',json.dumps({k:v for k,v in s.items() if k not in ('clauses','inventory_overrides')},ensure_ascii=False))
    print('INVENTORY_OVERRIDES',json.dumps(s.get('inventory_overrides'),ensure_ascii=False))
    print('CLAUSE_DECISIONS',json.dumps(s['clauses'],ensure_ascii=False))
