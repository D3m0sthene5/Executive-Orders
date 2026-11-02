"""Bounded native EO:1079 reproduction; no canonical outputs or source bytes are edited."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
BASE = 'f07b023133640f288fd44c10c5176888c49f23e2'
DEST = Path(__file__).parent/(sys.argv[1] if len(sys.argv)>1 else 'native-demo')
IID = 'EO:1079'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def blob(rel): return subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT)
def write(root,rel,raw):
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

if DEST.exists():
    raise SystemExit('refusing overwrite: '+str(DEST))
DEST.mkdir()
pins={}
with tempfile.TemporaryDirectory(prefix='lachmann-native-') as tmp:
    seed=Path(tmp)/'seed'
    # Exact source bytes and record, bounded identity/status projections. These
    # copies are isolated evidence inputs, never authority-table edits.
    for rel in ['research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv',
                'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv']:
        raw=blob(rel);pins[rel]=sha(raw)
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        rows=[r for r in rows if (r.get('instrument_id') or r.get('id'))==IID]
        assert len(rows)==1
        out=io.StringIO();w=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
        write(seed,rel,out.getvalue().encode())
    rel='jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl'
    raw=blob(rel);pins[rel]=sha(raw)
    fragments=[r for r in map(json.loads,raw.decode().splitlines())
               if r.get('instrument_id')==IID and r.get('kind')=='original_representation']
    assert len(fragments)==1
    write(seed,rel,(json.dumps(fragments[0],sort_keys=True)+'\n').encode())
    rel='jobs/lachmann/output/CONFIRMATIONS.jsonl'
    raw=blob(rel);pins[rel]=sha(raw)
    confirmations=[r for r in map(json.loads,raw.decode().splitlines()) if r.get('instrument_id')==IID]
    assert len(confirmations)==1 and confirmations[0]['confirmed']
    c=confirmations[0]
    write(seed,rel,(json.dumps(c,sort_keys=True)+'\n').encode())
    rel=c['text_path'];raw=blob(rel);pins[rel]=sha(raw)
    assert pins[rel]==c['text_sha256']
    write(seed,rel,raw)
    rel='jobs/claim-kit/output/dossiers/EO_1079.json'
    raw=blob(rel);pins[rel]=sha(raw)
    native=json.loads(raw)
    assert all(native['evidence'][native['original_source_id']]['source'].get(k)==c.get(k)
               for k in ['instrument_id','grade','sha256','text_path','text_sha256'])
    dump(DEST/'MAIN_DOSSIER.json',native)
    assert 'working_text_confirmation' not in native
    # Code is isolated so baseline and patched native builds cannot share imports.
    for generation in ['baseline','repaired']:
        repo=Path(tmp)/generation;shutil.copytree(seed,repo)
        for folder in ['jobs/claim-kit','jobs/clause-drafts','jobs/norton','jobs/status-history','research/stage19/code']:
            for p in (ROOT/folder).glob('*.py'):
                if p.name.startswith('test_'):continue
                rel=p.relative_to(ROOT).as_posix()
                raw=blob(rel) if generation=='baseline' else p.read_bytes()
                write(repo,rel,raw)
        script='''import json,sys
from pathlib import Path
repo=Path(sys.argv[1]);sys.path.insert(0,str(repo/'jobs/claim-kit'))
import build,assemble,working_text,batch
out=repo/'jobs/claim-kit/output';build.build(repo,out)
d=json.loads((out/'dossiers/EO_1079.json').read_text())
s=assemble.blank_sheet(d,'engineering-replay')
assert not s['approved'] and not s['original_confirmed'] and not s['inventory_confirmed']
assert s['working_text']['replacement_required'] and s['working_text']['quotation_recheck_required']
print(json.dumps({'prior':d.get('working_text_confirmation'), 'confirmation':s['working_text']['confirmations'][0]}))
if sys.argv[2]=='repaired':
 p=repo/'research/demo/packet';batch.prepare(repo,out,p,['EO:1079'],'engineering-replay')
 batch.load_packet(p,repo)
 result=batch.apply(repo,p,p/'applied');assert result['counts']=={'unresolved':1}
 assert (p/'applied/CLAIMS.proposed.jsonl').read_text()==''
 c=d['working_text_confirmation']['record'];c.update(method='agent',confirmed=False)
 agent=repo/'jobs/lachmann/output/AGENT_CONFIRMATIONS.jsonl';agent.write_text(json.dumps(c)+'\\n')
 try:batch.load_packet(p,repo)
 except ValueError as exc:print('EXPECTED_REFUSAL: '+str(exc))
 else:raise AssertionError('negative review failed to stale packet')
'''
        result=subprocess.run([sys.executable,'-B','-c',script,str(repo),generation],capture_output=True,text=True)
        write(DEST,generation+'.log',(result.stdout+result.stderr).encode())
        assert result.returncode==0,result.stderr
        shutil.copy2(repo/'jobs/claim-kit/output/dossiers/EO_1079.json',DEST/(generation+'_DOSSIER.json'))
        shutil.copy2(repo/'jobs/claim-kit/output/sheets/EO_1079.decision.json',DEST/(generation+'_SHEET.json'))
        if generation=='repaired':shutil.copytree(repo/'research/demo/packet',DEST/'PACKET')
    shutil.copytree(seed,DEST/'INPUTS')
    dump(DEST/'RECEIPT.json',{'base':BASE,'instrument_id':IID,'canonical_input_sha256':pins,
        'scope':'bounded native build, prepare, blank apply and negative-review refusal; no legal review',
        'implementation_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [ROOT/'jobs/claim-kit'/n for n in ['working_text.py','fragment_cache.py','inputs.py','build.py','assemble.py','batch.py','status_overlay.py']]},
        'claims_emitted':0,'certifications':0,'authority_changes':0,
        'limits':['Single identity/status and fragment/confirmation projections omit unrelated corpus context.',
                  'Main native dossier retained to establish exact selected-source gap.',
                  'No claim check or scientific approval, measured corpus saving or source authentication inferred.']})
print(DEST)
