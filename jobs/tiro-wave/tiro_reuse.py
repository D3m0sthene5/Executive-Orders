"""Tiro claim comparison and review reuse (coordinator bookkeeping; no legal judgment).

Owner standing rule D-20261125-reuse-identical-reviews (rev 1): reuse both arms' reviews if a re-prepared claim is
byte-identical or differs only in claim_kit.dossier_sha256. reuse_reviews() refuses every other case: an order
whose claim differs in any other field, or an order present in only one of the two claim files.
"""
import copy
import json
import shutil
from pathlib import Path

import tiro_common as C
from tiro_common import TiroError

DECISION = 'D-20261125-reuse-identical-reviews'
DECISION_REV = 1
RULE = ("Owner 2026-11-25: reuse both arms' reviews if a re-prepared claim is byte-identical or differs only in "
        "claim_kit.dossier_sha256.")


def _canon_text(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def _by_id(path):
    return {c['instrument_id']: c for c in C.load_jsonl(path)}


def _without_dossier_sha(c):
    c = copy.deepcopy(c)
    if isinstance(c.get('claim_kit'), dict):
        c['claim_kit'].pop('dossier_sha256', None)
    return c


def compare_claims(old_path, new_path):
    """Classify every order of two CLAIMS.proposed.jsonl files: identical, dossier_only (differs only in
    claim_kit.dossier_sha256), other (with the differing top-level fields and claim_kit subfields), only_old,
    only_new. 'map' takes each reusable order's old claim_sha256 to its new one."""
    a, b = _by_id(old_path), _by_id(new_path)
    res = {'identical': [], 'dossier_only': [], 'other': [], 'only_old': [], 'only_new': [], 'map': {}, 'detail': {}}
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if y is None:
            res['only_old'].append(k)
            continue
        if x is None:
            res['only_new'].append(k)
            continue
        if _canon_text(x) == _canon_text(y):
            res['identical'].append(k)
            res['map'][C.canon(x)] = C.canon(y)
            continue
        dk = sorted(f for f in set(x) | set(y) if _canon_text(x.get(f)) != _canon_text(y.get(f)))
        sub = []
        if dk == ['claim_kit'] and isinstance(x.get('claim_kit'), dict) and isinstance(y.get('claim_kit'), dict):
            sub = sorted(f for f in set(x['claim_kit']) | set(y['claim_kit'])
                         if _canon_text(x['claim_kit'].get(f)) != _canon_text(y['claim_kit'].get(f)))
        res['detail'][k] = {'fields': dk, 'claim_kit_fields': sub}
        if C.canon(_without_dossier_sha(x)) == C.canon(_without_dossier_sha(y)):
            res['dossier_only'].append(k)
            res['map'][C.canon(x)] = C.canon(y)
        else:
            res['other'].append(k)
    res['reusable'] = not (res['other'] or res['only_old'] or res['only_new'])
    return res


def compare_lines(res):
    """The per-order lines /tmp/claimcmp.py printed: IDENTICAL, DIFF [fields] claim_kit fields: ..., only in."""
    lines = []
    for k in sorted(set(res['identical']) | set(res['dossier_only']) | set(res['other']) | set(res['only_old'])
                    | set(res['only_new'])):
        if k in res['only_old']:
            lines.append(f'{k} only in old')
        elif k in res['only_new']:
            lines.append(f'{k} only in new')
        elif k in res['identical']:
            lines.append(f'{k} IDENTICAL')
        else:
            d = res['detail'][k]
            sub = (' claim_kit fields: ' + ','.join(d['claim_kit_fields'])) if d['claim_kit_fields'] else ''
            lines.append(f"{k} DIFF {d['fields']}{sub}")
    return lines


def _backup(path):
    n, b = 1, Path(str(path) + '.pre-remap')
    while b.exists():
        n += 1
        b = Path(f'{path}.pre-remap-{n}')
    shutil.copy(path, b)
    return b


def reuse_reviews(wave, batch, old_packet, old_applied, new_packet, new_applied, batch_check=True, force=False,
                  reason='', emit=print):
    """Carry the blind and after-reveal reviews of OLD to NEW under the standing rule. Writes NEW/reviews/ (row
    claim_sha256 remapped, with review_reused_from_claim_sha256 kept), NEW/REVIEW_REUSE.json, NEW/APPLIED_FOR_REVIEW,
    and updates the key's genuine hashes (old key kept as KEY.pre-remap)."""
    bdir = wave.batch_dir(batch)
    P, Q = bdir / old_packet, bdir / new_packet
    oc, nc = P / old_applied / 'CLAIMS.proposed.jsonl', Q / new_applied / 'CLAIMS.proposed.jsonl'
    for f in (oc, nc):
        if not f.exists():
            raise TiroError(f'no {wave.relpath(f)}')
    if not (P / 'reviews').is_dir() or not any((P / 'reviews').iterdir()):
        raise TiroError(f'no reviews in {wave.relpath(P)}/reviews')
    keyf = wave.key_path(batch)
    if not keyf.exists():
        raise TiroError(f'no key {keyf}')
    nrv = Q / 'reviews'
    if nrv.exists() and any(nrv.iterdir()) and not force:
        raise TiroError(f'{wave.relpath(nrv)} already holds files; pass --force to overwrite them')
    if batch_check:
        log = wave.scr('logs', f'bc-{batch}-{new_packet}.log')
        r = C.run(C.kit('batch-check', wave.relpath(Q), wave.relpath(Q / new_applied)), wave.repo)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(r.stdout + '\n' + r.stderr, encoding='utf-8')
        emit(f'batch-check {batch} {r.returncode}')
        if r.returncode:
            raise TiroError(f'batch-check failed for {wave.relpath(Q / new_applied)} (log {log}); reviews not reused')
    res = compare_claims(oc, nc)
    if not res['reusable']:
        for line in compare_lines(res):
            if 'IDENTICAL' not in line:
                emit(line)
        raise TiroError(f'{batch}: not reusable under {DECISION}: other diffs {res["other"]}, only old {res["only_old"]}, '
                        f'only new {res["only_new"]}')
    m = {o: n for o, n in res['map'].items() if o != n}
    nrv.mkdir(parents=True, exist_ok=True)
    rows, files = 0, []
    for f in sorted((P / 'reviews').iterdir()):
        if not f.is_file():
            continue
        files.append(f.name)
        if f.suffix != '.jsonl' or not m:
            shutil.copy(f, nrv / f.name)
            continue
        out, changed = [], False
        for line in f.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get('claim_sha256') in m:
                r['review_reused_from_claim_sha256'] = r['claim_sha256']
                r['claim_sha256'] = m[r['claim_sha256']]
                rows += 1
                changed = True
            out.append(json.dumps(r, ensure_ascii=False))
        if changed:
            (nrv / f.name).write_text('\n'.join(out) + '\n', encoding='utf-8')
        else:
            shutil.copy(f, nrv / f.name)
    key = json.loads(keyf.read_text(encoding='utf-8'))
    key_updated = [c['instrument_id'] for c in key.get('controls', []) if c.get('genuine') in m]
    backup = None
    if key_updated:
        backup = _backup(keyf)
        for c in key['controls']:
            if c.get('genuine') in m:
                c['genuine'] = m[c['genuine']]
        keyf.write_text(json.dumps(key, indent=1) + '\n', encoding='utf-8')
    receipt = {'schema': 'tiro-review-reuse/v1', 'decision': DECISION, 'decision_rev': DECISION_REV, 'rule': RULE,
               'batch': batch, 'wave': wave.name,
               'mode': 'byte_identical' if not res['dossier_only'] else 'dossier_sha256_only',
               'reason': reason,
               'old_claims': {'path': wave.relpath(oc), 'sha256': C.file_sha(oc)},
               'new_claims': {'path': wave.relpath(nc), 'sha256': C.file_sha(nc)},
               'identical_orders': res['identical'], 'dossier_sha256_only_orders': res['dossier_only'],
               'claim_sha256_map': m, 'review_files': files, 'review_rows_remapped': rows,
               'key_genuine_hashes_updated': key_updated}
    (Q / 'REVIEW_REUSE.json').write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    (Q / 'APPLIED_FOR_REVIEW').write_text(new_applied + '\n', encoding='utf-8')
    return {'batch': batch, 'mode': receipt['mode'], 'orders': len(res['map']), 'rows_remapped': rows,
            'key_backup': str(backup) if backup else None, 'receipt': wave.relpath(Q / 'REVIEW_REUSE.json')}
