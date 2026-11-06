from pathlib import Path
import csv,json,subprocess,collections,io,hashlib,sys
O=Path(__file__).resolve().parent;repo=Path(sys.argv[1]);pin='51914da4b58fb425b710e070ef10c20da6f119a4'
def get(p):return subprocess.check_output(['git','-C',str(repo),'show',pin+':'+p])
def csvs(p):return list(csv.DictReader(io.StringIO(get(p).decode())))
A={r['instrument_id'] for r in csv.DictReader((O/'early_frame.csv').open())}
paths=set(subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','--name-only',pin]).decode().splitlines())
pp='jobs/pinakes-proquest-ingest/output/ORDERS.csv'; lp='jobs/lachmann/output/RESIDUAL.csv'
rr=[r for r in csvs(pp) if r['instrument_id'] in A]
res=[r for r in csvs(lp) if r['instrument_id'] in A]
data={'population':len(A),'inputs_sha256':{p:hashlib.sha256(get(p)).hexdigest() for p in (pp,lp)},'Pinakes_ORDERS_exact_ids':len(set(r['instrument_id'] for r in rr)),'Pinakes_ORDERS_raw_path_exists':len(set(r['instrument_id'] for r in rr if r['folder']+'/'+r['file'] in paths)),'Pinakes_ORDERS_text_usable_yes':len(set(r['instrument_id'] for r in rr if r['text_usable']=='yes')),'Lachmann_RESIDUAL_matches':len(set(r['instrument_id'] for r in res)),'Lachmann_residual_producers':dict(collections.Counter(r['chosen_producer'] for r in res)),'warning':'Exact metadata joins on the entire fixed early frame only. Real readable pages, transcript correction, diagram completeness, generalization, savings and legal status not screened. Unregistered raw source does not make a working text.'}
(O/'FRAME_SOURCE_LEADS.json').write_text(json.dumps(data,indent=2)+'\n');print(data)
