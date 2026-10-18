"""Expose existing family candidates as connector-sized saved evidence packets."""
import collections,csv,json
from pathlib import Path

def write_catalog(root,out):
    with (root/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv').open(encoding='utf-8',newline='') as f:
        decided={r['instrument_id'] for r in csv.DictReader(f)}
    groups=collections.defaultdict(list)
    with (root/'jobs/later-events/output/FRAGMENTS.jsonl').open(encoding='utf-8') as f:
        for line in f:
            row=json.loads(line)
            if row.get('kind')=='whole_order_end_candidates' and row.get('instrument_id') in decided:
                for item in row.get('data',[]):
                    if item.get('actor'):groups[item['actor']].append({'target_id':row['instrument_id'],**item})
    ranked=sorted(groups.items(),key=lambda kv:(-len({x['target_id'] for x in kv[1]}),kv[0]))
    catalog=[]
    for rank,(actor,items) in enumerate(ranked,1):
        targets=sorted({x['target_id'] for x in items})
        name=actor.replace(':','_').replace('/','_')
        if not all(c.isalnum() or c in '_-.' for c in name):name='family_'+str(rank)
        rel='families/'+name+'.json'
        packet={'acting_id':actor,'rank':rank,'decided_targets':targets,'candidate_examples':items[:3],
                'notice':'Existing later-events editorial candidates only; no legal rule or ending is established.'}
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(packet,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
        catalog.append({'rank':rank,'acting_id':actor,'decided_targets':len(targets),'packet_path':rel})
    (out/'FAMILY_CATALOG.json').write_text(json.dumps(catalog,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
