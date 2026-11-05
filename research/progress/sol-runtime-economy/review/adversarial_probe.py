#!/usr/bin/env python3
"""Independent exact-baseline differential probes; temporary fixtures only."""
import builtins
import hashlib
import importlib.util
import io
import json
import pathlib
import random
import subprocess
import tempfile
import types
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[4]
BASE = '2c85459cf38b08dc1eea6d7c84a74268fa45c28e'
SRC = ROOT / 'jobs/claim-checker/sources.py'
baseline = types.ModuleType('baseline_sources')
exec(compile(subprocess.check_output(['git','show',f'{BASE}:jobs/claim-checker/sources.py'],cwd=ROOT),'baseline_sources.py','exec'),baseline.__dict__)
spec=importlib.util.spec_from_file_location('candidate_sources',SRC)
candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)


def state(index):
    def copy(c):
        return {slot: str(v) if isinstance(v,pathlib.Path) else v for slot in c.__slots__ for v in [getattr(c,slot)]}
    return {'sha':{k:[copy(c) for c in v] for k,v in index.by_sha.items()},
            'url':{k:[copy(c) for c in v] for k,v in index.by_url.items()},
            'counts':index.origin_counts,'notes':index.notes,'packed':index.packed_texts}


def run(mod,repo,stream_factory=None,fault_add=None):
    index=mod.HeldIndex()
    if fault_add:
        orig=index.add
        def add(c):
            orig(c)
            if c.sha256=='a'*64: raise fault_add('injected add failure')
        index.add=add
    real_open=builtins.open
    def op(path,*a,**kw):
        if pathlib.Path(path).name=='SOURCES.jsonl': return stream_factory()
        return real_open(path,*a,**kw)
    error=None
    try:
        with mock.patch('builtins.open',side_effect=op) if stream_factory else mock.patch.dict({},{}):
            mod.load_job_sources(index,repo)
    except BaseException as exc:
        error=(type(exc).__name__,str(exc))
    return {'index':state(index),'error':error}


def main():
    report={'baseline':BASE,'candidate_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
            'model':'gpt-6.1-sol','reasoning':'high','tokens':None,'cash':None,'checks':[],'differences':[]}
    with tempfile.TemporaryDirectory() as td:
        repo=pathlib.Path(td); path=repo/'jobs/a/output/SOURCES.jsonl'; path.parent.mkdir(parents=True)
        (repo/'jobs/b/output').mkdir(parents=True); (path.parent/'held.bin').write_bytes(b'held')
        rng=random.Random(261104)
        choices={
          'sha256':['a'*64,'b'*64,' A'*32,'A'*64,None,True,1,[],{},'invalid',' a'+'a'*63+' '],
          'url':['https://EXAMPLE.org/a/','http://example.org/a#frag','https://[bad','https://example.org/b?q=x',None,1,[]],
          'cache_path':['held.bin','../held.bin','/tmp/held.bin','C:\\held.bin','x\x00y',None,'',[],1],
          'text_path':['text.txt','../../b/output/text.txt','../../escape','/tmp/text.txt','C:\\text.txt','x\x00y',None,{},1],
          'bytes':[True,False,1,-1,'12','１２','²',None,[],{},'1.0'],
          'instrument_ids':[[' EO 1 ','',1,None],None,'EO 1',{},[]],
          'page_or_item':[None,'p. 1',1,{},[]], 'route':['note',None,True,[],{}]}
        rows=[]
        for i in range(1200):
            rows.append({k:rng.choice(v) for k,v in choices.items() if rng.random()<.9})
        raw='\n'.join([json.dumps(r) for r in rows]+['null','[]','not-json','','{"sha256":"'+'c'*64+'"}'])+'\n'
        path.write_text(raw)
        b=run(baseline,repo); c=run(candidate,repo)
        assert b==c, 'stable corpus diverged'
        report['checks'].append({'name':'1200 adversarial records full-index/order/notes parity','result':'pass'})
        # Exact original replacement-decoding and malformed-line behavior.
        original_bytes=path.read_bytes()
        path.write_bytes(original_bytes+b'\xff\xfe\n'+b'{"sha256":"'+b'd'*64+b'","route":"\xff"}\n')
        assert run(baseline,repo)==run(candidate,repo)
        report['checks'].append({'name':'invalid UTF-8 replacement decoding and line counts','result':'pass'})
        path.write_bytes(original_bytes)
        for fault in [ValueError,OSError,AttributeError,TypeError]:
            assert run(baseline,repo,fault_add=fault)==run(candidate,repo,fault_add=fault)
            report['checks'].append({'name':'index.add partial mutation '+fault.__name__,'result':'pass'})
        valid=json.dumps({'sha256':'a'*64,'cache_path':'held.bin'})+'\n'
        for phase in ['open','read','close']:
          for error in [OSError,UnicodeError,ValueError,KeyboardInterrupt,SystemExit,MemoryError,RecursionError]:
            class Stream:
              def __enter__(self):
                if phase=='open': raise error('injected '+phase)
                return self
              def __iter__(self):
                yield valid
                if phase=='read': raise error('injected '+phase)
              def __exit__(self,*a):
                if phase=='close': raise error('injected '+phase)
                return False
            b=run(baseline,repo,Stream); c=run(candidate,repo,Stream)
            assert b==c,(phase,error,b,c)
            report['checks'].append({'name':phase+' '+error.__name__,'result':'pass'})
        # Close-time writes stand in for a deterministic interleaving with another job.
        for action in ['create','remove']:
            held=path.parent/'racing.bin'
            def factory():
                class ChangingStream:
                    def __enter__(self): return self
                    def __iter__(self):
                        yield json.dumps({'sha256':'a'*64,'cache_path':'racing.bin'})+'\n'
                    def __exit__(self,*a):
                        if action=='create': held.write_bytes(b'new')
                        else: held.unlink()
                        return False
                return ChangingStream()
            def reset():
                if held.exists(): held.unlink()
                if action=='remove': held.write_bytes(b'old')
            reset(); b=run(baseline,repo,factory)
            reset(); c=run(candidate,repo,factory)
            assert b==c, ('custody interleaving diverged', action, b, c)
            report['checks'].append({'name':'cache '+action+' during source close','result':'pass','baseline':b,'candidate':c})
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
