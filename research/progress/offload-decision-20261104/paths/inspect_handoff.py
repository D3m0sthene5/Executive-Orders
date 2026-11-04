"""Bounded static/render-only examination; never a current Valla validation.

Reads exact retained source bytes and historical packet, invokes the existing
native per-member projection expression, and records practical slim omission.
Production must call native batch.view/views, which call load_packet and
recompute current Valla context. This script grants no reuse permission.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'inputs/pr135/jobs/claim-kit/batch.py'
SLIM = ROOT / 'inputs/pr135/jobs/geddes/geddes.py'
PACKET = ROOT / 'inputs/pr133/research/progress/maitland/valla-audit/correction-packet-v1/PACKET.json'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def inspect():
    bt, st = ast.parse(BASE.read_text()), ast.parse(SLIM.read_text())
    functions = {n.name: n for n in bt.body if isinstance(n, ast.FunctionDef)}
    for name in ('view', 'views'):
        assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'load_packet'
                   for n in ast.walk(functions[name])), 'native route lost live load_packet gate'
    load_text = ast.get_source_segment(BASE.read_text(), functions['load_packet'])
    assert "valla_context(repo" in load_text and "changed Valla review context" in load_text
    # Direct field/reference omission, rather than a fabricated source-reading run.
    slim_valla_references = [n.value for n in ast.walk(st) if isinstance(n, ast.Constant)
                             and isinstance(n.value, str) and 'valla' in n.value.lower()]
    assert not slim_valla_references
    packet = json.loads(PACKET.read_text())
    assert packet['fingerprint'] == sha(canonical({k:v for k,v in packet.items() if k != 'fingerprint'}).encode())
    iid, ctx = 'EO:13792', packet['valla_context']
    # Evaluate the exact existing native renderer's Valla payload expression.
    projections = [n.args[0] for n in ast.walk(functions['_view_loaded'])
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'canon'
                   and n.args and isinstance(n.args[0], ast.Dict)
                   and any(isinstance(k, ast.Constant) and k.value == 'review_queue' for k in n.args[0].keys)]
    assert len(projections) == 1
    result = eval(compile(ast.Expression(projections[0]), str(BASE), 'eval'), {'ctx':ctx, 'order':iid})
    assert result['claim'] == ctx['claims'][iid]
    assert result['review_queue'] == [q for q in ctx['review_queue'] if q['instrument_id'] == iid]
    assert result['refused_method_reviews'] == [q for q in ctx['refused_method_reviews'] if q.get('instrument_id') == iid]
    output = {'schema':'eo-valla-historical-render-preview/v1',
              'current_live_validation_performed':False,
              'notice':'Historical rendering only. Native live load_packet validation is required before current use; no approvals or reuse permissions are issued.',
              'packet_ref':'c733e69dbd0fa1e57a1f2614a33d77bdd600f122',
              'packet_fingerprint':packet['fingerprint'], 'instrument_id':iid,
              'native_member_projection':result}
    (ROOT/'NATIVE_VALLA_PREVIEW.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    receipt = {'schema':'eo-offload-static-handoff-inspection/v1',
               'input_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (BASE,SLIM,PACKET)},
               'slim_valla_references':len(slim_valla_references),
               'native_view_and_views_call_live_load_packet':True,
               'native_loader_recomputes_valla_context':True,
               'retained_context_only':{'claims':len(ctx['claims']), 'review_queue_entries':len(ctx['review_queue']),
                    'source_examined_entries':sum(q.get('dependency_confirmed') is True for q in ctx['review_queue']),
                    'refused_method_reviews':len(ctx['refused_method_reviews']),
                    'invalidated_conclusion_pointers':len(result['claim']['invalidated_conclusion_pointers']),
                    'valid_components':sum(c.get('valid') is True for c in result['claim']['component_reviews']),
                    'automatic_approvals':ctx['automatic_approvals'],
                    'whole_case_review_required':ctx['whole_case_review_required']},
               'native_projection_json_bytes':len(canonical(result).encode()),
               'current_live_validation_performed':False,
               'source_verification_or_legal_approval':False,
               'model_tokens_saved':None,'total_cost_saved':None,
               'recommended_consumer':'For flagged repair assignments, use current native kit.py view/views --order output after dispatch-check; a future slim projection must retain that live gate.'}
    (ROOT/'HANDOFF_INSPECTION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    print(json.dumps(inspect(),ensure_ascii=False,indent=2))
