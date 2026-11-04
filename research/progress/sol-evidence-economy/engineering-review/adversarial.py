"""Independent boundary probes. Test inputs generated in disposable temp repos only.

Usage: python3 -B <this-file> > report.json    (from repository root)
Comparison of installed Geddes code to old historical view is separate.
"""
from pathlib import Path
import datetime, hashlib, sys, json, traceback, tempfile
from copy import deepcopy
root = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root/'jobs/claim-kit'))
import test_factual_events as F, test_blind_verify as B, test_history_context as H
import history_context, batch, shutil

result = {}
def probe(name, fun, expected):
    try:
        actual = fun()
        result[name] = dict(expected=expected, actual=actual, pass_=expected == actual)
    except Exception as e:
        result[name] = dict(expected=expected, unexpected_exception=repr(e),pass_=False)

def blind_probe():
    f = B.BlindVerifyTests(); f.setUp()
    try:
        nested = deepcopy(f.source)
        nested['raw_path'] = nested.pop('local_path')
        quote = nested.pop('quote'); lo=nested.pop('char_start'); hi=nested.pop('char_end')
        witness = dict(source=nested, text=quote, char_start=lo, char_end=hi)
        interval = {'start':'1999-12-01','end':'1999-12-31','occurrence':'established',
             'start_basis':{'reason':'independent witness locates the event within the interval','witness': witness}, 'end_basis':{'reason':'already established in the primary source','witness':'occurrence_span'}}
        f.source['norton_factual_event']={'occurrence_interval':interval}
        run = lambda: f.verify()
        probe('valid_nested_Norton_refs_includes_distinct_witness_locus',
            lambda:[run()['ok'],len(run()['cards'][0]['sources'])], [True,2])
        witness['text'] = 'substituted extract'
        probe('changed_nested_bound_quote_refused', lambda:run()['ok'], False)
        witness['text']=quote
        nested['raw_path']='held/absent.pdf'
        probe('missing_nested_bound_raw_refused', lambda:run()['ok'],False)
        nested['raw_path']='held/bound-link'
        (f.root/nested['raw_path']).symlink_to(f.root/'held/raw.pdf')
        probe('symlink_bound_raw_refused',lambda:run()['ok'],False)
        nested['raw_path']='held/raw.pdf'
        f.source['raw_path']='held/missing-second-alias'
        probe('nonexistent_raw_alias_on_outer_source_refused',lambda:run()['ok'],False)
        f.source.pop('raw_path')
        f.source['local_path']='held/ref-link'
        (f.root/f.source['local_path']).symlink_to(f.root/'held/raw.pdf')
        probe('symlink_top_raw_refused',lambda:run()['ok'],False)
        f.source['local_path']='held/loop'
        (f.root/f.source['local_path']).symlink_to('loop')
        probe('symlink_cycle_refused_in_report',lambda:run()['ok'],False)
    finally:f.doCleanups()

def interval_probe():
    f=F.FactualEventTests();f.setUp()
    try:
        sheet,ev=f.partial_sheet()
        claim, errors=F.A.assemble_interval_partial(sheet,f.base.dossier,f.repo)
        assert claim and errors == []
        probe('partial_native_gate_still_gapped',lambda:bool(F.A.check_claim(claim,f.repo,f.base.dossier)) and bool(claim['unresolved_material_gaps']), True)
        for key,val in [('state_at_cutoff','terminated'),('first_end',{'date':'1999-12-31'}),('current_predicate',{'legal_basis':'asserted continuing force'})]:
            altered=deepcopy(claim)
            altered['operative_clauses'][0][key]=val
            probe('edited_partial_strict_refuses_'+key,lambda:bool(F.F.claim_errors(altered,f.repo,f.base.dossier)),True)
        altered=deepcopy(claim); altered['whole_order_end']={'date':'1999-12-31'}
        probe('edited_partial_strict_refuses_whole_order_end',lambda:bool(F.F.claim_errors(altered,f.repo,f.base.dossier)),True)
        evidence=deepcopy(f.registry['evidence'][0]);q=f.registry['questions'][0]
        evidence['occurrence_interval']['end_basis']['witness']={'source':None,'text':'x','char_start':0,'char_end':1}
        probe('malformed_witness_source_structured_refusal',lambda:bool(F.F.MODEL.evidence_errors(f.repo,q,evidence)),True)
        for date in ['1999-11-30','1999-12-01','1999-12-15','1999-12-31','2000-01-01']:
            expected={'1999-11-30':'not_yet_occurred','1999-12-31':'occurred_by_this_date','2000-01-01':'occurred_by_this_date'}.get(date,'unknown_if_already_occurred')
            probe('presence_only_'+date,lambda:F.F.interval_classification(ev['occurrence_interval'],date),expected)
    finally:f.doCleanups()

def history_probe():
    f=H.BatchHistoryTests();f.setUp()
    h=H.HistoryContextTests();h.setUp()
    try:
        h.write();shutil.copytree(h.repo/'research',f.repo/'research',dirs_exist_ok=True)
        f.run_build(); folder=f.repo/'research/probe'; ids=['EO:1','EO:2']; bp=f.repo/'research/history.json'
        batch.prepare(f.repo,f.out,folder,ids,'producer',history_bundles=[bp])
        probe('native_reverse_order_views_equal_separate',lambda:batch.views(f.repo,folder,ids[::-1]) == {i: batch.view(f.repo,folder,i) for i in ids[::-1]}, True)
        # Genuine correctly recomputed packet fingerprint + valid earlier query.
        file=folder/'PACKET.json'; original=file.read_bytes();p=json.loads(original)
        p['reviewed_histories']=history_context.collect(f.repo,ids,[bp],'1950-01-01')
        p.pop('fingerprint');p['fingerprint']=batch.digest(batch.canon(p).encode())
        file.write_bytes(batch.canon(p).encode())
        def refused():
            try: batch.view(f.repo,folder,ids[0])
            except (ValueError,OSError,KeyError):return True
            return False
        probe('different_valid_query_date_with_new_packet_hash_refused',refused,True)
        p['legal_cutoff']='1950-01-01'
        p.pop('fingerprint');p['fingerprint']=batch.digest(batch.canon(p).encode())
        file.write_bytes(batch.canon(p).encode())
        probe('jointly_backdated_packet_and_query_refused',refused,True)
        file.write_bytes(original)
        src = f.repo/h.bundle['provisions'][0]['source']['text_path']
        src.write_bytes(src.read_bytes()+b'changed')
        def _other_member_refused():
            try:batch.view(f.repo,folder,ids[1])
            except (ValueError,OSError,KeyError):return True
            return False
        probe('changed_source_invalidates_even_unrelated_member_in_same_packet',lambda:bool(_other_member_refused()),True)
    finally:h.doCleanups();f.doCleanups()

for func in [blind_probe, interval_probe, history_probe]:
    try:func()
    except Exception as exc: result[func.__name__]=dict(unexpected_exception=traceback.format_exc(),pass_=False)
files=['jobs/claim-kit/'+f+'.py' for f in ('assemble','factual_events','build','batch','kit','completion','blind_verify','history_context','provision_history')]+['jobs/geddes/geddes.py','jobs/norton/model.py','jobs/norton/norton.py']
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':{f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files},'probes':result},indent=2,sort_keys=True))
