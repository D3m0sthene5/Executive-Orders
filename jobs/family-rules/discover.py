"""Offline family discovery; all evidence remains an unverified research lead."""
import collections, csv, json, os
from pathlib import Path
ROOT = Path(os.environ['REPO_ROOT'])
OUT = Path(os.environ['OUTPUT_DIR'])
OUT.mkdir(parents=True, exist_ok=True)
def rows(p):
    with p.open(encoding='utf-8', newline='') as f: return list(csv.DictReader(f))
def main():
    decided = {r['instrument_id'] for r in rows(ROOT/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv')}
    groups = collections.defaultdict(list)
    for line in (ROOT/'jobs/later-events/output/FRAGMENTS.jsonl').open(encoding='utf-8'):
        f = json.loads(line)
        if f['kind'] == 'whole_order_end_candidates' and f['instrument_id'] in decided:
            for item in f['data']: groups[item['actor']].append({'target': f['instrument_id'], **item})
    packets = []
    for actor, items in sorted(groups.items(), key=lambda kv: (-len({i['target'] for i in kv[1]}), kv[0]))[:5]:
        sources = []
        for folder in ['jobs/clause-drafts/output','jobs/fr-originals/output','jobs/fr-originals/data/full_run','jobs/source-ladder/output']:
            p = ROOT/folder/'SOURCES.jsonl'
            if not p.exists(): continue
            for line in p.open(encoding='utf-8'):
                r = json.loads(line)
                if actor in json.dumps(r):
                    for key in ('text_path','text_file'):
                        rel = r.get(key)
                        if rel:
                            q = ROOT/folder/rel
                            if q.is_file(): r['saved_excerpt'] = q.read_text(encoding='utf-8', errors='replace')[:24000]; r['repo_text_path'] = q.relative_to(ROOT).as_posix()
                    sources.append(r)
        packet = {'acting_id':actor, 'targets':len({i['target'] for i in items}), 'target_ids':sorted({i['target'] for i in items}), 'examples':items[:3], 'sources':sources[:8]}
        packets.append(packet)
    (OUT/'TOP_FAMILIES.json').write_text(json.dumps(packets, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
    print([(p['acting_id'],p['targets'],len(p['sources'])) for p in packets])
if __name__ == '__main__': main()
