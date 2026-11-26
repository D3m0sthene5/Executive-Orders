"""Shared fixtures for Tiro's tests: a tiny temporary repository with one wave, and a fake command runner.

No test runs the real claim kit; every external command goes through tiro_common.run, which FakeRun replaces."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tiro_common as C  # noqa: E402

WAVE_NAME = 'tw-2026-01-02'


def claim(iid, end='1950-06-30', signing='1940-01-15', events=None, dossier='d' * 64):
    clause = {'clause_id': 'c1', 'first_end': {'date': end} if end else None, 'later_events': events or []}
    return {'instrument_id': iid, 'identity': {'signing_date': signing}, 'operative_clauses': [clause],
            'whole_order_end': {'date': end} if end else None, 'claim_kit': {'dossier_sha256': dossier, 'v': 1}}


def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')


class FakeRun:
    """Records each command; a handler(cmd_strings, cwd, env) may create files and return a Result."""

    def __init__(self, handler=None):
        self.calls = []
        self.handler = handler

    def __call__(self, cmd, cwd, env=None, timeout=None):
        cmd = [str(c) for c in cmd]
        self.calls.append((cmd, env))
        r = self.handler(cmd, Path(cwd), env) if self.handler else None
        return r or C.Result(0, '', '')

    def matching(self, word):
        return [c for c, _ in self.calls if word in c]


@pytest.fixture
def world(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    wdir = repo / 'research/excavator' / f'claude-{WAVE_NAME}'
    wdir.mkdir(parents=True)
    (wdir / 'WAVE.json').write_text(json.dumps({'wave': WAVE_NAME, 'actions': [{'id': 'production.claim_ready.no.fr'}]}))
    pk = wdir / 'b01' / 'packet'
    pk.mkdir(parents=True)
    (pk / 'ADMISSION.json').write_text(json.dumps({'agent': 'tw', 'bentham_action': 'production.claim_ready.no.fr',
                                                   'instrument_ids': ['EO:1', 'EO:2', 'EO:3']}))
    claims = [claim('EO:1'), claim('EO:2', end='1960-02-29'), claim('EO:3', end=None)]
    write_jsonl(pk / 'applied-v1' / 'CLAIMS.proposed.jsonl', claims)
    (pk / 'decisions.csv').write_text('instrument_id,dossier_sha256,agent,outcome\nEO:1,old1,tw,submit\n'
                                      'EO:2,old2,tw,submit\nEO:3,old3,tw,blocked\n', encoding='utf-8')
    (pk / 'clauses.csv').write_text('instrument_id,clause_id\nEO:1,c1\n', encoding='utf-8')
    (pk / 'RATIONALES.json').write_text('{}', encoding='utf-8')
    (pk / 'DISPATCH_CHECK.json').write_text(json.dumps({
        'dispatchable_ids': ['EO:1', 'EO:2'], 'source_blocked_ids': ['EO:3'],
        'source_recovery_tasks': [{'check_statuses': ['bytes_not_held'],
                                   'affected_references': [{'required': True, 'instrument_id': 'EO:3',
                                                            'evidence_id': 'ACT:EO:9'}]}]}))
    fake = FakeRun()
    monkeypatch.setattr(C, 'run', fake)
    wave = C.Wave(repo, WAVE_NAME, tmp_path / 'scr')
    return {'repo': repo, 'wave': wave, 'packet': pk, 'claims': claims, 'fake': fake, 'tmp': tmp_path}
