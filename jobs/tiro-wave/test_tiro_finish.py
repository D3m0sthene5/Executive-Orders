import json

import pytest

import tiro_common as C
import tiro_finish
from conftest import write_jsonl


def review(c, verdict='upheld', defects=()):
    return {'instrument_id': c['instrument_id'], 'claim_sha256': c if isinstance(c, str) else C.canon(c),
            'verdict': verdict, 'defects': list(defects)}


def setup_batch(world, b_rejects=None, b_misses_control=False):
    pk, claims = world['packet'], world['claims'][:2]
    genuine, other = claims[0], claims[1]
    key = {'batch': 'b01', 'applied': 'applied-v1',
           'controls': [{'instrument_id': genuine['instrument_id'], 'planted': 'p' * 64, 'genuine': C.canon(genuine),
                         'defect': 'every first_end and whole_order_end date moved back three years',
                         'type': 'date_shift_end', 'kind': 'date_shift'}]}
    world['wave'].key_path('b01').parent.mkdir(parents=True, exist_ok=True)
    world['wave'].key_path('b01').write_text(json.dumps(key))
    (pk / 'APPLIED_FOR_REVIEW').write_text('applied-v1\n')
    rv = pk / 'reviews'
    caught = {'instrument_id': genuine['instrument_id'], 'claim_sha256': 'p' * 64, 'verdict': 'rejected',
              'defects': ['whole_order_end date is three years early']}
    write_jsonl(rv / 'BLIND_REVIEW_A.jsonl', [caught, review(other)])
    b_ctrl = dict(caught, defects=['quote mismatch']) if b_misses_control else caught
    b_other = review(other, 'rejected', ['later_events: missing EO 9']) if b_rejects else review(other)
    write_jsonl(rv / 'BLIND_REVIEW_B.jsonl', [b_ctrl, b_other])
    for arm in 'AB':
        write_jsonl(rv / f'AFTER_REVEAL_{arm}.jsonl', [review(genuine, 'upheld_after_reveal')])

    def handler(cmd, cwd, env):
        if any(x.endswith('make_completion.py') for x in cmd):
            (pk / 'completion').mkdir(exist_ok=True)
            members = [{'instrument_id': c['instrument_id'], 'outcome': 'submit', 'claim_sha256': C.canon(c)}
                       for c in claims]
            (pk / 'completion' / 'COMPLETION.json').write_text(json.dumps({'members': members, 'controls': []}))
            return C.Result(0, '{"members": 2}', '')
        if 'publication-name' in cmd:
            return C.Result(0, json.dumps({'path': 'research/readiness/claims/tw-2026-01-02-tw-b01.jsonl',
                                           'other_owner_members': []}), '')
        if 'complete' in cmd:
            return C.Result(0, 'completed', '')
    world['fake'].handler = handler
    return key


def test_finish_files_when_both_arms_uphold_and_names_publication_through_the_kit(world):
    setup_batch(world)
    out = []
    rc = tiro_finish.finish(world['wave'], 'b01', world['packet'], publish=True, emit=out.append)
    assert rc == 0
    m = json.loads((world['packet'] / 'completion/COMPLETION.json').read_text())
    assert [x['outcome'] for x in m['members']] == ['submit', 'submit']
    assert m['publication'] == {'mode': 'own_claims', 'path': 'research/readiness/claims/tw-2026-01-02-tw-b01.jsonl'}
    name = world['fake'].matching('publication-name')[0]
    assert name[name.index('--wave') + 1] == 'tw' and name[name.index('--date') + 1] == '2026-01-02'
    mk = next(c for c, _ in world['fake'].calls if any(x.endswith('make_completion.py') for x in c))
    assert 'claude-coordinator-tw-2026-01-02' in mk and any(x.startswith('EO:1=caught|') for x in mk)
    comp = world['fake'].matching('complete')[-1]
    assert '--publish' in comp and comp[comp.index('--write') + 1].endswith('complete-v1')
    assert (world['packet'] / 'COMPLETE_v1.log').exists()
    seed = json.loads((world['packet'] / 'completion/SEED_RECEIPT_EO_1.json').read_text())
    assert seed['seeded_by'] == 'claude-coordinator-tw-2026-01-02'


def test_arm_b_rejection_demotes_member(world):
    setup_batch(world, b_rejects=True)
    out = []
    assert tiro_finish.finish(world['wave'], 'b01', world['packet'], emit=out.append) == 0
    m = json.loads((world['packet'] / 'completion/COMPLETION.json').read_text())
    blocked = [x for x in m['members'] if x['outcome'] == 'blocked']
    assert [x['instrument_id'] for x in blocked] == ['EO:2'] and 'later_events' in blocked[0]['reason']
    assert '--publish' not in world['fake'].matching('complete')[-1]


def test_missed_control_stops_before_completion(world):
    setup_batch(world, b_misses_control=True)
    out = []
    assert tiro_finish.finish(world['wave'], 'b01', world['packet'], emit=out.append) == 2
    assert 'STOP' in out[-1] and world['fake'].calls == []


def test_replacement_mode_uses_the_wave_folder_and_skips_naming(world):
    setup_batch(world)
    assert tiro_finish.finish(world['wave'], 'b01', world['packet'], replacement=True, emit=lambda s: None) == 0
    m = json.loads((world['packet'] / 'completion/COMPLETION.json').read_text())
    assert m['publication'] == {'mode': 'replacement_proposal',
                                'path': 'research/excavator/claude-tw-2026-01-02/b01/REPLACEMENT_PROPOSAL.jsonl'}
    assert world['fake'].matching('publication-name') == []


def test_pair_rule_unit():
    key = {'controls': [{'instrument_id': 'EO:1'}]}
    members = [{'instrument_id': 'EO:1', 'outcome': 'submit', 'claim_sha256': 'g'},
               {'instrument_id': 'EO:2', 'outcome': 'submit', 'claim_sha256': 'h'},
               {'instrument_id': 'EO:3', 'outcome': 'blocked', 'reason': 'x'}]
    blind = {'A': {}, 'B': {'g': {'verdict': 'upheld'}}}            # a blind uphold does not clear a control
    after = {'A': {}, 'B': {'g': {'verdict': 'upheld_after_reveal'}}}
    out, demoted = tiro_finish.pair_rule(members, key, blind, after)
    assert demoted == ['EO:2'] and out[0]['outcome'] == 'submit' and out[2] == members[2]
    assert 'no arm B record' in out[1]['reason']
    out, demoted = tiro_finish.pair_rule(members, key, blind, {'A': {}, 'B': {}})
    assert demoted == ['EO:1', 'EO:2']


def test_finish_refuses_without_applied_for_review(world):
    with pytest.raises(C.TiroError):
        tiro_finish.finish(world['wave'], 'b01', world['packet'])
