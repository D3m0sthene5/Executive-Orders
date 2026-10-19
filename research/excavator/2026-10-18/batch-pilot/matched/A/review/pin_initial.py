import hashlib,json,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'review'
canonical=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
sha=lambda b:hashlib.sha256(b).hexdigest()
initial=OUT/'initial'
initial.mkdir(exist_ok=True)
pins=[]
claims={c['instrument_id']:c for c in map(json.loads,(BASE/'producer/assembled-proposals.jsonl').read_text(encoding='utf8').splitlines())}
for f in sorted((BASE/'dossiers').glob('*.json')):
    d=json.loads(f.read_text(encoding='utf8'));s=BASE/'producer/decisions'/f.name
    dest=initial/('decision-'+f.name)
    if not dest.exists():shutil.copyfile(s,dest)
    c=claims.get(d['instrument_id'])
    if c:
        cp=initial/('claim-'+f.name)
        if not cp.exists():cp.write_bytes(json.dumps(c,ensure_ascii=False,sort_keys=True,indent=2).encode('utf8')+b'\n')
    pins.append({'instrument_id':d['instrument_id'],'dossier_file_sha256':sha(f.read_bytes()),'dossier_fingerprint':d['fingerprint'],'decision_file_sha256':sha(dest.read_bytes()),'claim_sha256':sha(canonical(c)) if c else None})
initial_audit=initial/'ASSEMBLER_AUDIT.json'
if not initial_audit.exists():shutil.copyfile(BASE/'producer/ASSEMBLER_AUDIT.json',initial_audit)
initial_outcomes=initial/'PRODUCER_OUTCOMES.json'
if not initial_outcomes.exists():shutil.copyfile(BASE/'producer/OUTCOMES.json',initial_outcomes)
(OUT/'INITIAL_INPUT_PINS.json').write_bytes(json.dumps(pins,sort_keys=True,indent=2).encode()+b'\n')
for p in pins:print(json.dumps(p))
for f in sorted((BASE/'dossiers').glob('*.json')):
    d=json.loads(f.read_text(encoding='utf8'))
    print(d['instrument_id'],'search_counts',[(s['search_id'],s.get('machine_hits_for_this_order')) for s in d['machine_searches']])
    print('chain',[(s['actor_id'],s['signing_date'],s['verb'],s['sections_touched']) for s in d['chain']['events']])
