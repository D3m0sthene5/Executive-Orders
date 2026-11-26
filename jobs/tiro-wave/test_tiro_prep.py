import json
from pathlib import Path

import pytest

import tiro_common as C
import tiro_prep
from conftest import write_jsonl


def kit_prepare_handler(refuse_first=None, held=False, new_rows=None):
    """Fake kit prepare: refuses once naming `refuse_first`, then writes the packet (and -held)."""
    state = {'n': 0}

    def handler(cmd, cwd, env):
        if 'prepare' in cmd:
            state['n'] += 1
            target = cwd / cmd[cmd.index('--write') + 1]
            if refuse_first and state['n'] == 1:
                return C.Result(1, '', f'claim-kit: {refuse_first} is outside the Bentham action; EO:999 noted\n')
            out = target.with_name(target.name + '-held') if '--held-supplement' in cmd else target
            out.mkdir(parents=True)
            (out / 'PACKET.json').write_text('{}')
            ids = [c for c in cmd if c.startswith('EO:')]
            rows = new_rows or [{'instrument_id': i, 'dossier_sha256': 'new-' + i} for i in ids]
            C.write_csv(out / 'decisions.csv', rows, ['instrument_id', 'dossier_sha256'])
            return C.Result(0, 'prepared', '')
        if 'apply' in cmd:
            src = cwd / cmd[cmd.index('apply') + 1]
            dest = cwd / cmd[cmd.index('--write') + 1]
            claims = handler.claims
            write_jsonl(dest / 'CLAIMS.proposed.jsonl', claims)
            return C.Result(0, '', '')
    handler.claims = []
    return handler


def test_prepare_drops_refused_members_and_retries(world):
    world['fake'].handler = kit_prepare_handler(refuse_first='EO:2')
    res = tiro_prep.prepare(world['wave'], 'b02', ['EO:1', 'EO:2', 'EO:3'], 'tw', 'production.claim_ready.no.fr')
    assert res['state'] == 'ok' and res['ids'] == ['EO:1', 'EO:3'] and res['dropped'] == ['EO:2']
    prep = world['fake'].matching('prepare')
    assert len(prep) == 2 and 'EO:2' not in prep[1]
    assert prep[0][prep[0].index('--write') + 1] == 'research/excavator/claude-tw-2026-01-02/b02/packet'
    assert world['fake'].calls[0][1] == {'LARREY_LEVEL': 'hard'}
    assert 'b02 drop: EO:2 (claim-kit:' in (world['wave'].scratch / 'DROPPED.txt').read_text()
    views = world['fake'].matching('view')
    assert [v[v.index('view') + 2] for v in views] == ['EO:1', 'EO:3']
    assert views[0][-1].endswith('b02/packet/views/EO_1.json')
    assert world['fake'].matching('lookups')


def test_prepare_held_supplement_views_go_to_the_held_packet(world):
    world['fake'].handler = kit_prepare_handler()
    res = tiro_prep.prepare(world['wave'], 'b02', ['EO:1'], 'tw', 'production.claim_ready.no.fr', held=True,
                            rp=True)
    assert res['packet'].endswith('b02/packet-held')
    cmd = world['fake'].matching('prepare')[0]
    assert '--held-supplement' in cmd and '--replacement-proposal' in cmd
    assert world['fake'].matching('view')[0][-1].endswith('packet-held/views/EO_1.json')


def test_prepare_never_overwrites_and_fails_without_named_members(world):
    with pytest.raises(C.TiroError):
        tiro_prep.prepare(world['wave'], 'b01', ['EO:1'], 'tw', 'production.claim_ready.no.fr')
    world['fake'].handler = lambda cmd, cwd, env: C.Result(1, '', 'claim-kit: tracker is stale\n')
    res = tiro_prep.prepare(world['wave'], 'b03', ['EO:1'], 'tw', 'production.claim_ready.no.fr')
    assert res['state'] == 'fail' and 'tracker is stale' in res['reason']


def test_wave_action_rules(world):
    w = world['wave']
    assert w.action() == 'production.claim_ready.no.fr'
    with pytest.raises(C.TiroError):
        w.action('production.claim_ready.yes.fr')


def test_carry_sheets_refreshes_dossier_hashes(world, tmp_path):
    new = tmp_path / 'new'
    new.mkdir()
    C.write_csv(new / 'decisions.csv', [{'instrument_id': 'EO:1', 'dossier_sha256': 'fresh1'}],
                ['instrument_id', 'dossier_sha256'])
    res = tiro_prep.carry_sheets(world['packet'], new)
    rows = C.read_csv(new / 'decisions.csv')
    assert [r['dossier_sha256'] for r in rows] == ['fresh1', 'old2', 'old3']
    assert rows[0]['outcome'] == 'submit' and res['dossier_sha256_refreshed'] == 1
    assert (new / 'clauses.csv').read_text() == (world['packet'] / 'clauses.csv').read_text()
    assert (new / 'RATIONALES.json').exists()


def test_reapply_reports_reusable_when_only_dossier_hash_changes(world):
    h = kit_prepare_handler()
    claims = [dict(c, claim_kit={'dossier_sha256': 'e' * 64, 'v': 1}) for c in world['claims']]
    h.claims = claims
    world['fake'].handler = h
    out = []
    res = tiro_prep.reapply(world['wave'], 'b01', 'packet', 'applied-v1', 'packet-v2', held=True, emit=out.append)
    assert res['state'] == 'applied' and res['packet'].endswith('b01/packet-v2-held')
    assert res['dossier_sha256_only'] == 3 and res['reviews_reusable']
    cmd = world['fake'].matching('prepare')[0]
    assert cmd[cmd.index('--agent') + 1] == 'tw' and cmd[cmd.index('--action') + 1] == 'production.claim_ready.no.fr'
    assert [c for c in cmd if c.startswith('EO:')] == ['EO:1', 'EO:2', 'EO:3']
    q = world['packet'].parent / 'packet-v2-held'
    assert [r['dossier_sha256'] for r in C.read_csv(q / 'decisions.csv')] == ['new-EO:1', 'new-EO:2', 'new-EO:3']
    assert any("DIFF ['claim_kit'] claim_kit fields: dossier_sha256" in l for l in out)
