"""Read-only comparison of held FR texts; discrepancies are leads, not verdicts."""
import collections, csv, hashlib, importlib.util, json, random, subprocess, sys, time, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
BASE = '899671f30776c715f66141291125dd0fda9da202'
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    spec.loader.exec_module(mod); return mod
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    start = time.monotonic()
    OUT.mkdir(parents=True,exist_ok=True)
    baseline = subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':jobs/claim-kit/excavate.py'])
    old = types.ModuleType('boundary_baseline');sys.modules[old.__name__]=old
    exec(compile(baseline,'baseline-excavate.py','exec'),old.__dict__)
    cd = module('boundary_existing_cd', ROOT/'jobs/clause-drafts/segment.py')
    ready = {r['instrument_id']: r for r in csv.DictReader((ROOT/'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv').open())}
    records = {}
    for folder in ('jobs/fr-originals/output','jobs/fr-originals/data/full_run'):
        for ln in (ROOT/folder/'SOURCES.jsonl').open():
            r = json.loads(ln)
            for iid in r.get('instrument_ids',[]):
                path = ROOT/folder/r.get('text_path','')
                if path.is_file(): records[iid] = (r,path)
    rows=[]; sample_records={}
    for iid,(rec,path) in sorted(records.items()):
        text=path.read_bytes().decode('utf-8')
        loc=cd.locate_order(text,iid.split(':',1)[1])
        if not loc or loc.heading_style != 'trailing_number': continue
        clauses=old.segment(iid,text,rec)['clauses']
        low=min((c['char_start'] for c in clauses), default=0)
        high=max((c['char_end'] for c in clauses), default=0)
        outside=sum(max(0,min(c['char_end'],loc.body_start)-c['char_start']) + max(0,c['char_end']-max(c['char_start'],loc.body_end)) for c in clauses)
        inside=sum(max(0,min(c['char_end'],loc.body_end)-max(c['char_start'],loc.body_start)) for c in clauses)
        # A cheap mechanical stratum; not a declaration of legal completeness.
        kind='disjoint' if inside==0 else 'outside' if outside>0 else 'inside'
        row=dict(instrument_id=iid,stratum=kind,old_start=low,old_end=high,old_clauses=len(clauses),locator_start=loc.body_start,locator_end=loc.body_end,
                 old_inside_characters=inside,old_outside_characters=outside,locator_signature_found=loc.signature_found,
                 location_confidence=rec.get('location_confidence'),source_sha256=rec['sha256'],text_path=path.relative_to(ROOT).as_posix(),text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                 unfinished=ready.get(iid,{}).get('ready_for_human_review')!='yes',provisional_status=ready.get(iid,{}).get('provisional_status',''),
                 ready_gate=ready.get(iid,{}).get('ready_for_human_review','unknown'))
        rows.append(row); sample_records[iid]=(rec,text)
    with (OUT/'SCREEN.csv').open('w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    known={'EO:8083','EO:8123','EO:8126','EO:8992'};rng=random.Random(20261026)
    samples=[]
    for group in ('discrepancy','agreement'):
        pool=[r for r in rows if r['instrument_id'] not in known and r['unfinished'] and (r['stratum']!='inside')==(group=='discrepancy')]
        for r in rng.sample(pool,min(8,len(pool))):samples.append(dict(r,sample_group=group))
    summary=dict(available_fr_text_orders=len(records),trailing_number_orders=len(rows),strata=dict(collections.Counter(r['stratum'] for r in rows)),
                 unfinished_strata=dict(collections.Counter(r['stratum'] for r in rows if r['unfinished'])),
                 high_confidence_strata=dict(collections.Counter(r['stratum'] for r in rows if r['location_confidence']=='high')),
                 known=[r for r in rows if r['instrument_id'] in known],machine_seconds=time.monotonic()-start,
                 caveat='Locator comparison only. Inside is not clean or complete; disjoint/outside are not independent primary-page verdicts. Unfinished means current ready flag !=yes, not unowned/unclaimed.',
                 inputs={p:sha(ROOT/p) for p in ('jobs/clause-drafts/segment.py','jobs/fr-originals/data/full_run/SOURCES.jsonl','jobs/fr-originals/output/SOURCES.jsonl','jobs/readiness-tracker/output/READINESS_BY_ORDER.csv')},baseline_excvate_sha256=hashlib.sha256(baseline).hexdigest(),base_commit=BASE)
    (OUT/'SCREEN_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'SAMPLE.json').write_text(json.dumps({'seed':20261026,'screen_sha256':sha(OUT/'SCREEN.csv'),'cases':samples},indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('known','inputs')}))
if __name__=='__main__':main()
