import gzip
import json
import re

import pytest

import plants
import tiro
import tiro_common as C
import tiro_review
from conftest import WAVE_NAME, write_jsonl


def test_wave_resolution_and_scratch_guard(world):
    repo = world['repo']
    for spec in (WAVE_NAME, f'research/excavator/claude-{WAVE_NAME}', f'research/excavator/claude-{WAVE_NAME}/WAVE.json'):
        w = C.Wave(repo, spec, world['tmp'] / 'scr')
        assert (w.short, w.date, w.rel) == ('tw', '2026-01-02', f'research/excavator/claude-{WAVE_NAME}')
        assert w.adjudicator == f'claude-coordinator-{WAVE_NAME}'
    with pytest.raises(C.TiroError, match='inside the repository'):
        C.Wave(repo, WAVE_NAME, repo / 'scr')
    with pytest.raises(C.TiroError):
        C.Wave(repo, 'nosuch-2026-01-01', world['tmp'] / 'scr')


def test_packet_resolution_refuses_to_guess(world):
    w = world['wave']
    assert w.packet('b01') == world['packet']
    (world['packet'].parent / 'packet-v2').mkdir()
    (world['packet'].parent / 'packet-v2' / 'PREPARE.json').write_text('{}')
    with pytest.raises(C.TiroError, match='several packets'):
        w.packet('b01')
    assert w.packet('b01', 'packet-v2').name == 'packet-v2'


def test_every_route_renders_with_no_leftover_tokens_or_wave_names(world):
    for route in ('yes', 'no', 'undecided', 'correction', 'recovery', 'stale'):
        t, ok, blocked = tiro_review.producer_prompt(world['wave'], 'b01', route, 'tw', world['packet'])
        assert not re.search(r'\{\{|baldus|bartolus', t), route
        assert f'research/excavator/claude-{WAVE_NAME}/b01/packet' in t
        assert 'EO:3: mandatory source not held: ACT:EO:9 (bytes_not_held)' in t
    assert ok == ['EO:1', 'EO:2'] and blocked == ['EO:3']


def test_render_producer_writes_scratch_prompt(world, tmp_path):
    note = tmp_path / 'note.txt'
    note.write_text('Watch EO 9.')
    res = tiro_review.render_producer(world['wave'], 'b01', 'no', 'tw', world['packet'], note, 'b01-v2')
    t = open(res['prompt'], encoding='utf-8').read()
    assert res['prompt'].endswith('prompts/producer-b01-v2.txt') and t.endswith('COORDINATOR NOTE FOR THIS BATCH:\nWatch EO 9.')
    assert str(world['wave'].scratch / 'work' / 'b01') + '/' in t


def test_review_prep_dry_run_writes_nothing_in_the_packet(world):
    before = sorted(p.name for p in world['packet'].iterdir())
    res = tiro_review.review_prep(world['wave'], 'b01', world['packet'], 'applied-v1', dry_run=True)
    assert sorted(p.name for p in world['packet'].iterdir()) == before and res['packet_writes'] == []
    key = json.loads(world['wave'].key_path('b01').read_text())
    assert key['controls'][0]['kind'] == 'date_shift'
    rd = world['wave'].scratch / 'review' / 'b01'
    a = [c['instrument_id'] for c in C.load_jsonl(rd / 'REVIEW_SET_A.jsonl')]
    assert sorted(a) == ['EO:1', 'EO:2', 'EO:3']
    t = (world['wave'].scratch / 'prompts' / 'reviewer-b01-A.txt').read_text()
    assert '"claude-blind-reviewer-tw-b01-A-2026-01-02"' in t and str(rd / 'REVIEW_SET_A.jsonl') in t
    assert f'research/excavator/claude-{WAVE_NAME}/b01/packet/reviews/BLIND_REVIEW_A.jsonl' in t
    assert not re.search(r'\{\{|baldus|bartolus|//cruden', t)
    r = (world['wave'].scratch / 'prompts' / 'reveal-b01-B.txt').read_text()
    assert key['controls'][0]['instrument_id'] in r and 'AFTER_REVEAL_B.jsonl' in r
    with pytest.raises(C.TiroError, match='exists'):
        tiro_review.review_prep(world['wave'], 'b01', world['packet'], 'applied-v1', dry_run=True)
    tiro_review.review_prep(world['wave'], 'b01', world['packet'], 'applied-v1', force=True)
    assert (world['packet'] / 'APPLIED_FOR_REVIEW').read_text() == 'applied-v1\n'


def test_pool_prompt_inlines_each_set(world):
    write_jsonl(world['packet'].parent.parent / 'b02' / 'packet' / 'applied-v1' / 'CLAIMS.proposed.jsonl', world['claims'])
    tiro_review.review_prep(world['wave'], 'b01', world['packet'], 'applied-v1', dry_run=True)
    tiro_review.review_prep(world['wave'], 'b02', world['wave'].batch_dir('b02') / 'packet', 'applied-v1', dry_run=True)
    t = tiro_review.pool_prompt(world['wave'], ['b01', 'b02'], 'B')
    assert 'arm B, for 2 separate review sets: b01, b02' in t
    assert t.count('BLIND_REVIEW_B.jsonl') >= 2 and 'SET 2 of 2: batch b02, arm B' in t and 'BLIND_REVIEW_A' not in t
    with pytest.raises(C.TiroError):
        tiro_review.pool_prompt(world['wave'], ['b09'], 'A')


def test_current_reports_not_on_disk_and_current(world):
    (world['packet'] / 'PACKET.json').write_text('{}')
    other = world['wave'].batch_dir('b05') / 'packet'
    other.mkdir(parents=True)

    def handler(cmd, cwd, env):
        if 'config' in cmd:
            return C.Result(0, 'true\n', '')
        if 'ls-files' in cmd:
            return C.Result(0, 'S ' + cmd[-1] + '\n', '')
        if cmd[0] != 'git':
            return C.Result(0, json.dumps({'packet': cmd[-1], 'state': 'CURRENT'}) + '\n', '')
        return C.Result(0, 'true\n', '')
    world['fake'].handler = handler
    out = []
    rels = [world['wave'].relpath(world['packet']), world['wave'].relpath(other)]
    assert tiro.current(world['repo'], rels, emit=out.append) == 1
    assert out[0].startswith('NOT_ON_DISK ') and out[1] == f'CURRENT {rels[0]}' and 'sparse' in out[2]


def test_gzip_receipts_round_trip(tmp_path):
    p = tmp_path / 'c' / 'BIG.json'
    p.parent.mkdir()
    p.write_bytes(b'x' * 1000)
    done = tiro.gzip_receipts([tmp_path / 'c'], threshold=100, emit=lambda s: None)
    assert done == [str(p)] and not p.exists()
    assert gzip.decompress((tmp_path / 'c' / 'BIG.json.gz').read_bytes()) == b'x' * 1000
    assert json.loads((tmp_path / 'c' / 'BIG.COMPRESSED.json').read_text())['bytes_uncompressed'] == 1000


def test_ledger_and_cost(world, tmp_path):
    prices = world['repo'] / 'jobs/necker-costs/PRICES.json'
    prices.parent.mkdir(parents=True)
    prices.write_text(json.dumps({'models': [{'match': 'claude-sonnet', 'input': 3, 'cache_read': 0.3,
                                              'cache_write_1h': 6, 'cache_write_5m': 3.75, 'output': 15}]}))
    tr = tmp_path / 't.jsonl'
    rows = [{'message': {'id': 'm1', 'model': 'claude-sonnet-5-5', 'usage': {'input_tokens': 10, 'output_tokens': 1}}},
            {'message': {'id': 'm1', 'model': 'claude-sonnet-5-5', 'usage': {'input_tokens': 1000000, 'output_tokens': 0}}}]
    tr.write_text('\n'.join(json.dumps(r) for r in rows) + '\nnot json\n')
    c = tiro.transcript_cost(world['repo'], tr)
    assert c['calls'] == 1 and c['inp'] == 1000000 and abs(c['usd'] - 3.0) < 1e-9
    args = ['--repo', str(world['repo']), '--wave', WAVE_NAME, '--scratch', str(world['wave'].scratch)]
    out = []
    tiro.main(args + ['ledger', 'launch', 'b01', '--role', 'producer', '--model', 'sonnet', '--start', 'T0'], out.append)
    tiro.main(args + ['ledger', 'done', 'b01', '--role', 'producer', '--model', 'sonnet', '--agent-id', 'a1',
                      '--end', 'T1', '--start', 'T0', '--counts-from', '--transcript', str(tr)], out.append)
    assert out[0] == 'b01,launched,producer,sonnet,start=T0'
    assert out[1] == 'b01,a1,producer,sonnet,end=T1,start=T0,submitted=2,blocked=1,tokens=1000000,usd=3.0000'
    assert (world['wave'].scratch / 'WORKERS_DONE.csv').read_text().strip() == out[1]
    assert 'b01 agent-tool producer claude-sonnet-5-5 cost 3.0000' in (world['wave'].scratch / 'COSTS.log').read_text()


def test_adopt_wraps_standing_adoption(world):
    comp = world['packet'] / 'complete-v2'
    comp.mkdir()
    (comp / 'PUBLICATION.json').write_text(json.dumps({'mode': 'replacement_proposal'}))
    (world['packet'] / 'complete-v10').mkdir()
    (world['packet'] / 'complete-v10' / 'PUBLICATION.json').write_text(json.dumps({'mode': 'replacement_proposal'}))
    tiro.adopt(world['wave'], ['b01'], emit=lambda s: None)
    cmd = world['fake'].calls[0][0]
    assert '--standing' in cmd and '--write' not in cmd
    assert cmd[cmd.index('--completion') + 1].endswith('b01/packet/complete-v10')
    assert cmd[cmd.index('--target') + 1] == 'research/readiness/claims/novellae-2026-01-02-tw-b01.jsonl'
    (comp.parent / 'complete-v11').mkdir()
    (comp.parent / 'complete-v11' / 'PUBLICATION.json').write_text(json.dumps({'mode': 'own_claims'}))
    with pytest.raises(C.TiroError, match='not a replacement'):
        tiro.adopt(world['wave'], ['b01'], emit=lambda s: None)


def test_cli_prepare_needs_action_when_plan_has_several(world):
    plan = world['wave'].plan_path
    d = json.loads(plan.read_text())
    d['actions'].append({'id': 'production.claim_ready.yes.fr'})
    plan.write_text(json.dumps(d))
    with pytest.raises(C.TiroError, match='pass --action'):
        tiro.main(['--repo', str(world['repo']), '--wave', WAVE_NAME, '--scratch', str(world['wave'].scratch),
                   'prepare', 'b09', 'EO:1'], lambda s: None)


def test_plant_kind_registry_is_extensible():
    class Swap(plants.DateShift):
        name = 'swap'
        words = ('swap',)
    plants.KINDS['swap'] = Swap()
    try:
        made = plants.make_controls([{'instrument_id': 'EO:1', 'identity': {'signing_date': '1940-01-01'}}], 'b', kind='swap')
        assert made['controls'][0]['kind'] == 'swap'
        assert plants.names_defect({'verdict': 'rejected', 'defects': ['swap']}, made['controls'][0])
        assert not plants.names_defect({'verdict': 'rejected', 'defects': ['date']}, made['controls'][0])
    finally:
        del plants.KINDS['swap']
