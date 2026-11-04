"""Independent read-only replay, exact retained Geddes baseline + real packet CLI.
Usage: python3 -B consumer_replay.py <hydrated retained fixture repo> <base geddes.py> <live history PACKET.json>
"""
import hashlib, importlib.util, json, sys, time, tempfile, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root/'jobs/geddes'))
import geddes
fixture, old_source, history_packet=map(Path,sys.argv[1:])
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def canonical(x):return hashlib.sha256(json.dumps(x, sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
spec=importlib.util.spec_from_file_location('geddes_old',old_source);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
packet=fixture/'research/excavator/claude-apollo-2026-10-31/n01/packet/PACKET.json'
ids=list(json.loads(packet.read_bytes())['dossiers'])[::-1]
report={'retained_packet_sha256':sha(packet),'baseline_git_blob':subprocess.check_output(['git','hash-object',old_source],text=True).strip(),'geddes_sha256':sha(root/'jobs/geddes/geddes.py'),'orders':ids,'parity':{}}
for full in [False,True]:
    many=geddes.view_many(packet, ids, repo=fixture, full_claim=full)
    old_views=[old.view(packet,i,repo=fixture,full_claim=full) for i in ids]
    report['parity']['full' if full else 'normal']={'old_view_array_sha256':canonical(old_views),'new_view_array_sha256':canonical(many),'same_per_order':sum(a==b for a,b in zip(many,old_views)),'n':len(ids)}
    assert many==old_views
with tempfile.TemporaryDirectory() as td:
    out=Path(td); sentinel=out/'sentinel'
    sentinel.write_bytes(b'unchanged')
    filename=ids[1].replace(':','_')+'.view.json';(out/filename).symlink_to(sentinel)
    try: geddes.view_many(packet,ids[:2],out,repo=fixture)
    except (ValueError,OSError) as e: report['collision_refusal']=str(e)
    assert len(list(out.iterdir()))==2 and sentinel.read_bytes()==b'unchanged' and 'collision_refusal' in report
h=json.loads(history_packet.read_bytes()); members=list(h['dossiers']); iid=members[0];report['history_packet_sha256']=sha(history_packet)
report['native_history']={}
for label,args in [('view',['view',str(history_packet.parent),'--order',iid]),('views',['views',str(history_packet.parent),iid]),('slim',['views',str(history_packet),iid,'--slim'])]:
    proc=subprocess.run([sys.executable,'-B',str(root/'jobs/claim-kit/kit.py'),*args],capture_output=True,text=True,cwd=root)
    item=report['native_history'][label]={'returncode':proc.returncode,'stderr_tail':proc.stderr[-500:]}
    if proc.returncode==0:
        item['contains_history']=('reviewed_histories' in proc.stdout or 'Reviewed provision histories' in proc.stdout)
        item['contains_unknown']='unknown' in proc.stdout
        item['stdout_sha256']=hashlib.sha256(proc.stdout.encode()).hexdigest()
        if label=='slim':
            v=json.loads(proc.stdout)[0]; q=v['reviewed_histories']['queries']
            item['queries']=[{'id':r.get('provision_id'),'state':r.get('operative_state'),'canonical_approval':r.get('canonical_approval')} for r in q]
with tempfile.TemporaryDirectory() as td:
    args=[sys.executable,'-B',str(root/'jobs/claim-kit/kit.py'),'views',str(history_packet.parent),iid,'--slim','--write-dir',td]
    proc=subprocess.run(args,capture_output=True,text=True,cwd=root)
    err=proc.stderr[-500:]
    report['slim_folder_export']={'exit':proc.returncode,'stderr':err}
    if proc.returncode==0:
        dest=Path(td)/(iid.replace(':','_')+'.view.json')
        v=json.loads(dest.read_bytes())
        summary=json.loads(proc.stdout)
        report['slim_folder_export'].update(exported_view_has_scoped_history=bool(v['reviewed_histories']['queries']),summary_matches=summary==[geddes.view_summary(dict(v,written_to=str(dest)))])
print(json.dumps(report,indent=2))
