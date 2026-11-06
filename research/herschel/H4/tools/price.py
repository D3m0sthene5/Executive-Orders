"""price.py AGENT_USAGE.csv -> USD per agent and per phase, priced with jobs/bentham/measure.py usd()."""
import csv, json, sys
sys.path.insert(0,'/home/claude/executive-orders/jobs/bentham')
import measure
rows=list(csv.DictReader(open(sys.argv[1])))
tot={}; per=[]
for r in rows:
    fam='opus' if 'opus' in r['model'] else 'sonnet'
    t={'fresh_input':int(r['fresh_input'] or 0),'output':int(r['output'] or 0),'cache_read':int(r['cache_read'] or 0),
       'cache_write':int(r['cache_write_5m'] or 0)+int(r['cache_write_1h'] or 0)+int(r['cache_write_unclassified'] or 0)}
    u=measure.usd(fam,t); per.append((r['phase'],r['session_id'][:8],fam,round(u,3)))
    tot[r['phase']]=tot.get(r['phase'],0)+u
print(json.dumps({'by_phase':{k:round(v,2) for k,v in tot.items()},'total_usd':round(sum(tot.values()),2),'agents':len(rows)},indent=1))
