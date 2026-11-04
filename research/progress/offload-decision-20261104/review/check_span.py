"""Independently exercise oracle vs grouping, malformed fields and per-scope freshness."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import importlib.util,json,sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parents[1]/'population/span_probe.py'
s=importlib.util.spec_from_file_location('span_worker',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
recs=m.load_occurrences(); data=m.TEXT_FILE.read_bytes()
def call(f, recs, get_bytes):
    paths=[]
    def read(path): paths.append(path);return get_bytes(len(paths))
    with patch.object(m,'span_status',wraps=m.span_status) as spy:
        result=f(recs,read);return dict(status=[r['status'] for r in result],reads=len(paths),span_calls=spy.call_count,receipt=m.B.sha(m.B.canon(result)))
baseline={f.__name__:call(f,recs,lambda _:data) for f in (m.naive,m.per_claim,m.grouped)}
assert {r['receipt'] for r in baseline.values()}=={'be3fdbfe224de6f101b3f9a1d45d2430b2c9161de6bd07d9e233dc23f23b1f5a'}
for k,(rd,sc) in {'naive':(14,14),'per_claim':(4,4),'grouped':(1,2)}.items():
    assert (baseline[k]['reads'],baseline[k]['span_calls'])==(rd,sc)
probes={}
test=deepcopy(recs[:2])
for r in test:r['source'].update(char_start=1,char_end=2,quote=data.decode()[1:2])
test[1]['source']['char_start']=True
tests=[
    ('bool_int_collision',test,data,['pass','invalid_span']),
    ('empty_span',[dict(test[0],source=dict(test[0]['source'],char_end=1,quote=''))],data,['invalid_span']),
    ('changed_nonutf8',test,b'\xff',['source_hash_mismatch']*2),
    ('changed_in_new_invocation',test,b'x'+data[1:],['source_hash_mismatch']*2)]
for k,rr,b,required in tests:
    a=call(m.naive,rr,lambda _:b)['status']; b=call(m.grouped,rr,lambda _,val=b:val)['status']
    probes[k]={'literal':a,'grouped':b}; assert a==b==required
# Mid-invocation change is specifically outside a shared immutable snapshot.
# Demonstrate why this experiment cannot be used for rotating/blinded files.
changing=lambda i: data if i==1 else b'x'+data[1:]
legacy=call(m.naive,recs[:2],changing)['status']
shared=call(m.grouped,recs[:2],changing)['status']
assert legacy==['pass','source_hash_mismatch'] and shared==['pass','pass']
print(json.dumps(dict(actual_baseline={k:{x:y for x,y in v.items() if x!='status'} for k,v in baseline.items()},probes=probes,changing_file_within_invocation={'fresh_reads':legacy,'single_read':shared,'boundary':'Require an immutable byte snapshot. Never pool mutable/blind/reviewer inputs merely because paths match.'}),indent=2,sort_keys=True))
