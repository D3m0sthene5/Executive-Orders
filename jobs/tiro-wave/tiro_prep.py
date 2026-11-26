"""Tiro prepare and reapply (coordinator bookkeeping; no legal judgment).

prepare: kit.py prepare for one batch, dropping and retrying when the kit refuses naming member orders (each drop
logged in SCR/DROPPED.txt), then cruden lookups and one Geddes slim view per member in the packet producers use
(<packet>-held with --held-supplement).

reapply: the stale-packet recovery. Re-prepare the same orders into a new packet, carry the producer's sheets over
(decisions.csv with each dossier_sha256 refreshed to the new dossier, clauses.csv, RATIONALES.json), apply, and
compare the new claims with the reviewed ones.
"""
import json
import re
import shutil
from pathlib import Path

import tiro_common as C
from tiro_common import TiroError
from tiro_reuse import compare_claims, compare_lines

REFUSAL = 'claim-kit:'
ID_RE = re.compile(r'EO:[0-9]+[A-Z]?')


def dispatch_dir(target, held):
    target = Path(target)
    return target.with_name(target.name + '-held') if held else target


def view_name(iid):
    return 'EO_' + iid[3:].replace(':', '_') + '.json' if iid.startswith('EO:') else iid.replace(':', '_') + '.json'


def kit_prepare_cmd(ids, agent, action, target, held=False, rp=False):
    return C.kit('prepare', *ids, '--agent', agent, '--action', action,
                 *(['--replacement-proposal'] if rp else []), *(['--held-supplement'] if held else []),
                 '--write', target)


def lookups_and_views(wave, packet, ids, log):
    """cruden lookups, then one Geddes view per member into packet/views/. Returns the failure marks."""
    fails = []
    r = C.run(C.py(C.CRUDEN, 'lookups', wave.relpath(packet), isolated=True), wave.repo)
    C.append_log(log, r.stdout + r.stderr)
    if r.returncode:
        fails.append('LOOKUPS_FAIL')
    (Path(packet) / 'views').mkdir(exist_ok=True)
    for iid in ids:
        r = C.run(C.py(C.GEDDES, 'view', wave.relpath(Path(packet) / 'PACKET.json'), iid, '--write',
                       wave.relpath(Path(packet) / 'views' / view_name(iid)), isolated=True), wave.repo)
        C.append_log(log, r.stdout + r.stderr)
        if r.returncode:
            fails.append(f'VIEWFAIL {iid}')
    for f in fails:
        C.append_log(log, f)
    return fails


def refused_members(log_text, ids):
    """(first kit refusal line, the member ids it names)."""
    line = next((l for l in log_text.splitlines() if REFUSAL in l), '')
    named = []
    for i in ID_RE.findall(line):
        if i in ids and i not in named:
            named.append(i)
    return line, named


def prepare(wave, batch, ids, agent, action, level='hard', packet='packet', held=False, rp=False, retries=5,
            drop=True, lookups=True):
    """Returns a summary dict; 'state' is ok, empty (every member dropped) or fail."""
    ids = list(dict.fromkeys(ids))
    if not ids:
        raise TiroError('no orders to prepare')
    target = wave.batch_dir(batch) / packet
    final = dispatch_dir(target, held)
    if target.exists() or final.exists():
        raise TiroError(f'{wave.relpath(target) if target.exists() else wave.relpath(final)} exists: prepare never '
                        'overwrites a packet; choose a new --packet name (packet-v2, ...)')
    target.parent.mkdir(parents=True, exist_ok=True)
    log = wave.scr('logs', f'prep-{batch}.log' if packet == 'packet' else f'prep-{batch}-{packet}.log')
    dropped_all = []
    for attempt in range(1, retries + 1):
        for d in (target, final):  # only this run's own failed attempt is removed
            if d.exists():
                shutil.rmtree(d)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f"PREPARE {batch} agent={agent} rp={int(rp)} held={int(held)} action={action} attempt={attempt} "
                       f"start {C.now()} {' '.join(ids)}\n", encoding='utf-8')
        r = C.run(kit_prepare_cmd(ids, agent, action, wave.relpath(target), held, rp), wave.repo, env={'LARREY_LEVEL': level})
        C.append_log(log, r.stdout + r.stderr)
        if r.returncode:
            C.append_log(log, f'PREPARE_EXIT {r.returncode}')
        if (final / 'PACKET.json').exists():
            fails = lookups_and_views(wave, final, ids, log) if lookups else []
            C.append_log(log, f'DONE {batch} {C.now()}')
            return {'batch': batch, 'state': 'ok', 'packet': wave.relpath(final), 'orders': len(ids), 'ids': ids,
                    'dropped': dropped_all, 'attempts': attempt, 'failures': fails, 'log': str(log)}
        line, named = refused_members(log.read_text(encoding='utf-8'), ids)
        if not drop or not named:
            return {'batch': batch, 'state': 'fail', 'reason': (line or f'prepare exit {r.returncode}, no refusal line')[:200],
                    'dropped': dropped_all, 'attempts': attempt, 'log': str(log)}
        C.append_log(wave.scr('DROPPED.txt'), f"{batch} drop: {' '.join(named)} ({line[:90]})")
        dropped_all += named
        ids = [i for i in ids if i not in named]
        if not ids:
            return {'batch': batch, 'state': 'empty', 'dropped': dropped_all, 'attempts': attempt, 'log': str(log)}
    return {'batch': batch, 'state': 'fail', 'reason': f'still refused after {retries} attempts', 'dropped': dropped_all,
            'log': str(log)}


def carry_sheets(old, new):
    """Copy the producer's sheets from the old packet into the re-prepared one: decisions.csv rows with each
    dossier_sha256 replaced by the new packet's (other columns unchanged), clauses.csv, and RATIONALES.json."""
    old, new = Path(old), Path(new)
    fresh = {r['instrument_id']: r['dossier_sha256'] for r in C.read_csv(new / 'decisions.csv')}
    rows = C.read_csv(old / 'decisions.csv')
    if not rows:
        raise TiroError(f'{old}/decisions.csv has no rows')
    for r in rows:
        r['dossier_sha256'] = fresh.get(r['instrument_id'], r['dossier_sha256'])
    C.write_csv(new / 'decisions.csv', rows, list(rows[0].keys()))
    shutil.copy(old / 'clauses.csv', new / 'clauses.csv')
    carried = ['decisions.csv', 'clauses.csv']
    if (old / 'RATIONALES.json').exists():
        shutil.copy(old / 'RATIONALES.json', new / 'RATIONALES.json')
        carried.append('RATIONALES.json')
    return {'carried': carried, 'dossier_sha256_refreshed': sum(r['instrument_id'] in fresh for r in rows)}


def reapply(wave, batch, old_packet, old_applied, new_packet, held=False, rp=False, action=None, agent=None,
            level='hard', emit=print):
    bdir = wave.batch_dir(batch)
    old = bdir / old_packet
    if not (old / old_applied / 'CLAIMS.proposed.jsonl').exists():
        raise TiroError(f'no {wave.rel}/{batch}/{old_packet}/{old_applied}/CLAIMS.proposed.jsonl')
    meta = C.packet_meta(old)
    ids = meta['ids']
    if not ids:
        raise TiroError(f'cannot read the member orders of {wave.rel}/{batch}/{old_packet}')
    act = wave.action(action or meta['action'])
    agent = agent or meta['agent'] or wave.short
    target = bdir / new_packet
    q = dispatch_dir(target, held)
    if target.exists() or q.exists():
        raise TiroError(f'{wave.relpath(q if q.exists() else target)} exists: choose a new packet name')
    log = wave.scr('logs', f'reapply-{batch}-{q.name}.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"REAPPLY {batch} {old_packet}/{old_applied} -> {q.name} agent={agent} action={act} start {C.now()}\n",
                   encoding='utf-8')
    r = C.run(kit_prepare_cmd(ids, agent, act, wave.relpath(target), held, rp), wave.repo, env={'LARREY_LEVEL': level})
    C.append_log(log, r.stdout + r.stderr)
    if r.returncode:
        C.append_log(log, f'PREPARE_EXIT {r.returncode}')
    if not q.is_dir():
        tail = '\n'.join(log.read_text(encoding='utf-8').splitlines()[-3:])
        raise TiroError(f'no {wave.relpath(q)} after prepare:\n{tail}')
    carried = carry_sheets(old, q)
    applied = q / 'applied-v1'
    a = C.run(C.kit('apply', wave.relpath(q), '--write', wave.relpath(applied)), wave.repo)
    C.append_log(log, a.stdout + a.stderr)
    emit(f'apply {batch} {a.returncode}')
    if a.returncode or not (applied / 'CLAIMS.proposed.jsonl').exists():
        return {'batch': batch, 'state': 'apply_failed', 'packet': wave.relpath(q), 'log': str(log)}
    cmp = compare_claims(old / old_applied / 'CLAIMS.proposed.jsonl', applied / 'CLAIMS.proposed.jsonl')
    for line in compare_lines(cmp):
        emit(line)
    return {'batch': batch, 'state': 'applied', 'packet': wave.relpath(q), 'applied': 'applied-v1', **carried,
            'identical': len(cmp['identical']), 'dossier_sha256_only': len(cmp['dossier_only']),
            'other_diffs': len(cmp['other']), 'only_old': cmp['only_old'], 'only_new': cmp['only_new'],
            'reviews_reusable': cmp['reusable'], 'log': str(log)}
