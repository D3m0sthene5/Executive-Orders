"""Generate actor and blind workpacks AFTER building cached text vault."""
import csv,pathlib,sqlite3,sys,json,importlib.util
root=pathlib.Path(sys.argv[1]);db=sqlite3.connect(root/'DATA/EO_SOURCE_DEPENDENCY_GRAPH.sqlite')
spec=importlib.util.spec_from_file_location('eoleverage',root/'SCRIPTS/eo_leverage_engine.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
rows=list(csv.DictReader(open(root/'QUEUES/REUSABLE_CONTROLLING_SOURCE_QUEUE.csv',newline='')))
for i,r in enumerate(rows[:20],1):
 mod.dumpjson(root/'WORKPACKS'/(f'{i:02d}_'+r['actor'].replace(':','_')+'.json'),mod.actor_packet(db,r['actor'],max_targets=90))
for k,kind,i in db.execute('SELECT instrument_id,kind,ordinal FROM audit_sample ORDER BY ordinal'):
 mod.dumpjson(root/'WORKPACKS/BLIND_60'/(f'{i:02d}_'+k.replace(':','_')+'.json'),mod.single_packet(db,k,blind=True))
print('Regenerated',min(20,len(rows)),'actor workpacks and 60 blind-safe case briefs, including available cached-source hints')
