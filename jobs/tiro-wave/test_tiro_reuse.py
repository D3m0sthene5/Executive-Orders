import json

import pytest

import tiro_common as C
import tiro_reuse
from conftest import write_jsonl


def make_new(world, claims, name='packet-v2'):
    q = world['packet'].parent / name
    write_jsonl(q / 'applied-v1' / 'CLAIMS.proposed.jsonl', claims)
    return q


def with_reviews(world):
    rv = world['packet'] / 'reviews'
    rows = [{'instrument_id': c['instrument_id'], 'claim_sha256': C.canon(c), 'verdict': 'upheld'} for c in world['claims']]
    write_jsonl(rv / 'BLIND_REVIEW_A.jsonl', rows)
    write_jsonl(rv / 'BLIND_REVIEW_B.jsonl', rows)
    key = {'controls': [{'instrument_id': 'EO:1', 'planted': 'p', 'genuine': C.canon(world['claims'][0])}]}
    kp = world['wave'].key_path('b01')
    kp.parent.mkdir(parents=True, exist_ok=True)
    kp.write_text(json.dumps(key))
    return rows


def test_compare_claims_classifies(world, tmp_path):
    old = world['claims']
    new = [old[0], dict(old[1], claim_kit={'dossier_sha256': 'x', 'v': 1}), dict(old[2], whole_order_end={'date': '1'}),
           {'instrument_id': 'EO:9'}]
    write_jsonl(tmp_path / 'o.jsonl', old)
    write_jsonl(tmp_path / 'n.jsonl', new)
    res = tiro_reuse.compare_claims(tmp_path / 'o.jsonl', tmp_path / 'n.jsonl')
    assert res['identical'] == ['EO:1'] and res['dossier_only'] == ['EO:2'] and res['other'] == ['EO:3']
    assert res['only_new'] == ['EO:9'] and not res['reusable']
    lines = tiro_reuse.compare_lines(res)
    assert 'EO:1 IDENTICAL' in lines and "EO:3 DIFF ['whole_order_end']" in lines and 'EO:9 only in new' in lines


def test_reuse_identical_copies_bytes_and_leaves_key(world):
    with_reviews(world)
    q = make_new(world, world['claims'])
    before = world['wave'].key_path('b01').read_text()
    res = tiro_reuse.reuse_reviews(world['wave'], 'b01', 'packet', 'applied-v1', 'packet-v2', 'applied-v1',
                                   emit=lambda s: None)
    assert res['mode'] == 'byte_identical' and res['rows_remapped'] == 0
    assert (q / 'reviews/BLIND_REVIEW_B.jsonl').read_bytes() == (world['packet'] / 'reviews/BLIND_REVIEW_B.jsonl').read_bytes()
    assert world['wave'].key_path('b01').read_text() == before
    rec = json.loads((q / 'REVIEW_REUSE.json').read_text())
    assert rec['decision'] == 'D-20261125-reuse-identical-reviews' and rec['decision_rev'] == 1
    assert (q / 'APPLIED_FOR_REVIEW').read_text() == 'applied-v1\n'
    assert world['fake'].matching('batch-check')


def test_reuse_dossier_only_remaps_rows_and_key(world):
    with_reviews(world)
    new = [dict(c, claim_kit={'dossier_sha256': 'e' * 64, 'v': 1}) for c in world['claims']]
    q = make_new(world, new)
    res = tiro_reuse.reuse_reviews(world['wave'], 'b01', 'packet', 'applied-v1', 'packet-v2', 'applied-v1',
                                   batch_check=False, emit=lambda s: None)
    assert res['mode'] == 'dossier_sha256_only' and res['rows_remapped'] == 6
    rows = C.load_jsonl(q / 'reviews/BLIND_REVIEW_A.jsonl')
    assert [r['claim_sha256'] for r in rows] == [C.canon(c) for c in new]
    assert rows[0]['review_reused_from_claim_sha256'] == C.canon(world['claims'][0])
    key = json.loads(world['wave'].key_path('b01').read_text())
    assert key['controls'][0]['genuine'] == C.canon(new[0])
    assert (world['wave'].key_path('b01').parent / 'b01.json.pre-remap').exists()


def test_reuse_refuses_real_differences_and_failed_batch_check(world):
    with_reviews(world)
    make_new(world, [world['claims'][0], world['claims'][1], dict(world['claims'][2], operative_clauses=[])])
    with pytest.raises(C.TiroError, match='not reusable'):
        tiro_reuse.reuse_reviews(world['wave'], 'b01', 'packet', 'applied-v1', 'packet-v2', 'applied-v1',
                                 batch_check=False, emit=lambda s: None)
    world['fake'].handler = lambda cmd, cwd, env: C.Result(1, '', 'fail')
    with pytest.raises(C.TiroError, match='batch-check failed'):
        tiro_reuse.reuse_reviews(world['wave'], 'b01', 'packet', 'applied-v1', 'packet-v2', 'applied-v1',
                                 emit=lambda s: None)
