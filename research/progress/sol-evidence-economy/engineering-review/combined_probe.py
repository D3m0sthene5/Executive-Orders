"""Usage: python3 -B combined_probe.py <combined checkout>. Only temp fixture writes."""
import json,sys,shutil,tempfile,io,contextlib
from pathlib import Path
repo=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(repo/'jobs/claim-kit'))
import test_dispatch as TD,test_history_context as TH
f=TD.DispatchTests(); f.setUp()
h=TH.HistoryContextTests();h.setUp()
r={}
try:
    h.write();shutil.copytree(h.repo/'research',f.repo/'research',dirs_exist_ok=True)
    f.retain(missing=('EO:1',));f.run_build()
    bundle=f.repo/'research/history.json';folder=f.repo/'research/combined-research'
    def cli(name,exp,*args):
        code,data=f.cli(*args); r[name]={'expected_rc':exp,'rc':code}
        assert code==exp,(name,code,exp)
        return data
    folder0=f.repo/'research/combined-production'
    raw=cli('source_blocked_production_with_history',1,'prepare','EO:1','--agent','fixture','--write',folder0,'--history-bundle',bundle)
    raw=cli('source_blocked_research_with_history',0,'prepare','EO:1','--agent','fixture','--write',folder,'--research-only','--history-bundle',bundle)
    x=json.loads(raw);assert x['research_only'] and not x['dispatch_check']['ok'] and x['dispatch_check']['source_blocked_ids']==['EO:1']
    doc=json.loads((folder/'PACKET.json').read_bytes());assert doc['reviewed_histories']
    cli('explicit_blocked_member_refused',1,'dispatch-check',folder,'--order','EO:1')
    assert 'Reviewed provision histories' in cli('normal_view',0,'view',folder,'--order','EO:1')
    assert 'Reviewed provision histories' in cli('normal_views',0,'views',folder,'EO:1')
    slim=json.loads(cli('slim_views',0,'views',folder,'EO:1','--slim'));assert slim[0]['reviewed_histories']['queries']
    a=json.loads(cli('factual_at',0,'factual-at',folder,'--order','EO:1','--on','1999-01-01'))
    assert not a['observations'] and a['legal_effect']=='unresolved' and not a['human_certified']
    cli('factual_at_bad_date',2,'factual-at',folder,'--order','EO:1','--on','not-a-date')
    # A newly retained exact raw reopens only custody; packet bytes untouched.
    before=(folder/'PACKET.json').read_bytes();f.retain()
    acc=json.loads(cli('exact_raw_reopens_dispatch',0,'dispatch-check',folder,'--order','EO:1'))
    assert (folder/'PACKET.json').read_bytes()==before and acc['dispatchable_ids']==['EO:1']
    (f.repo/'jobs/future-source/output/raw/EO_1.bin').write_bytes(b'corrupt')
    cli('changed_raw_again_refuses',1,'dispatch-check',folder,'--order','EO:1')
    f.retain()
    target=f.repo/h.bundle['provisions'][0]['source']['text_path']
    target.write_bytes(target.read_bytes()+b'stale only history')
    cli('fresh_raw_but_changed_history_refuses_dispatch',2,'dispatch-check',folder,'--order','EO:1')
    cli('changed_history_refuses_factual_query',2,'factual-at',folder,'--order','EO:1','--on','1999-01-01')
    cli('changed_history_refuses_slim_query',2,'views',folder,'EO:1','--slim')
finally:
    f.doCleanups();h.doCleanups()
print(json.dumps(r,indent=2))
