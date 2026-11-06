import csv,hashlib,io,json,pathlib,subprocess,sys
out=pathlib.Path(__file__).resolve().parent
repo=sys.argv[1]; pin='51914da4b58fb425b710e070ef10c20da6f119a4'
paths=['research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv','jobs/readiness-tracker/output/READINESS_BY_ORDER.csv','jobs/readiness-tracker/output/SUMMARY.json']
data=[subprocess.check_output(['git','-C',repo,'show',pin+':'+p]) for p in paths]
c,t=[list(csv.DictReader(io.StringIO(x.decode('utf-8-sig')))) for x in data[:2]]
c={x['id']:x for x in c if x['included_in_bibliography']=='1'}
assert len(c)==len(t)==len(set(x['instrument_id'] for x in t))==14972 and set(c)==set(x['instrument_id'] for x in t)
summary=json.loads(data[2]); assert summary['ready_for_human_review']==sum(x['ready_for_human_review']=='yes' for x in t)==1331
def h(b):return hashlib.sha256(b).hexdigest()
freeze={'pin':pin,'design':'Committed seed before outputs: hash-as-random ordering; SHA-256 over literal EO-2026-10-14-independent-eval-v1|frame|trimmed lowercased instrument_id; ascending hex then ID. Full operational census, using tracker working-text evidence tier. Lowercase key affects ranking only. No prior-work filters on frames.','cutoff':'2026-10-14','input_sha256':{p:h(b) for p,b in zip(paths,data)},'frames':{}}
for frame,k in [('early',6),('transfer',3)]:
 rows=[]
 for x in t:
  i=x['instrument_id']; date=c[i]['date_effective']; yr=int(date[:4]) if date[:4].isdigit() else 0
  if not (x['ready_for_human_review']=='no' and not x['provisional_status'] and (1907<=yr<=1936 and x['text_evidence_tier']=='missing' if frame=='early' else yr>=1937 and date<='2026-10-14' and x['text_evidence_tier']=='original_supported')):continue
  dig=h(f"EO-2026-10-14-independent-eval-v1|{frame}|{i.strip().lower()}".encode())
  rows.append({'sha256':dig,'instrument_id':i,'date_effective':date,'text_evidence_tier':x['text_evidence_tier'],'step_original_text':x['step_original_text'],'provisional_status':x['provisional_status'],'ready_for_human_review':x['ready_for_human_review']})
 rows.sort(key=lambda r:(r['sha256'],r['instrument_id']))
 p=out/(frame+'_frame.csv')
 with p.open('w') as f:
  w=csv.DictWriter(f,fieldnames=['rank','reservation']+list(rows[0]));w.writeheader()
  for ix,row in enumerate(rows,1):w.writerow({'rank':ix,'reservation':'primary' if ix<=k else 'alternate' if ix<=2*k else '',**row})
 freeze['frames'][frame]=dict(population=len(rows),primary=[r['instrument_id'] for r in rows[:k]],alternates=[r['instrument_id'] for r in rows[k:2*k]],nominal_probability=f'{k}/{len(rows)}',frame_sha256=h(p.read_bytes()))
(out/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
print(json.dumps(freeze['frames']))
