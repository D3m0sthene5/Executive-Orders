"""Usage: python babbage_overlap.py MAIN_REPO PR141_REPO OUTPUT; both commits must be locally available."""
import csv,hashlib,json,subprocess as s,sys
from pathlib import Path
main,pr,out=sys.argv[1:];out=Path(out)
def raw(repo,pin,path):return s.check_output(['git','-C',repo,'show',pin+':'+path])
p0='51914da4b58fb425b710e070ef10c20da6f119a4';p1='654dccb98d81106a66b236dad861022d98bbcd46';path='research/excavator/claude-tribonian-2026-11-04/tools/batches.json'
b=raw(pr,p1,path);batch=json.loads(b);rows=list(csv.DictReader((out/'fr_original_raw.csv').open()));B={r['instrument_id'] for r in rows}
fr={i:r for r in map(json.loads,raw(main,p0,'jobs/fr-originals/output/SOURCES.jsonl').splitlines()) for i in r['instrument_ids']}
data={}
for k in ['o25','o28','o29','o30']:
 members=batch[k];hs={fr[i]['sha256'] for i in members if i in fr}; shared=hs & {r['sha256'] for r in rows};matches=[r for r in rows if r['sha256'] in shared]
 data[k]=dict(batch_members=len(members),same_order_id=len(B.intersection(members)),batch_fr_records=sum(i in fr for i in members),shared_fr_source_hashes=len(shared),unfinished_orders_sharing_file=len(matches),shared_hashes=sorted(shared),shared_file_native_present_orders=sum(bool(r['native_retention_pdf_path']) for r in matches),shared_hash_native_present_count=len({r['sha256'] for r in matches if r['native_retention_pdf_path']}))
cp='research/progress/babbage-complete-effort/experiment/COMPARISON.json';comp=raw(pr,p1,cp)
o=dict(pr=141,head=p1,batch_path=path,batch_file_sha256=hashlib.sha256(b).hexdigest(),comparison_path=cp,comparison_sha256=hashlib.sha256(comp).hexdigest(),comparison=json.loads(comp),shared_with_frozen_B_by_batch=data)
(out/'babbage_overlap.json').write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
