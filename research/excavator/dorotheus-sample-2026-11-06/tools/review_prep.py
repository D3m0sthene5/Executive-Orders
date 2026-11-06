"""Build one blind review set for a Dorotheus packet (coordinator tool; no legal judgment).

usage: python3 -I review_prep.py BATCH CLAIMS_JSONL MWCODE [ARMS]
  1. Date-shift control (ice core plant.py rule; fallbacks: later-event dates, then every signing_date): picks max(1, round(n/15)) submitted claims (seeded by batch name)
     carrying first_end/whole_order_end dates and moves every such date back exactly three years. If no claim
     has an end date (an all-YES set), it moves every later_events effective date back three years instead.
  2. Mountweazel control: `mountweazel.py seed --track C --n 2 --share 0.5 --codes MWCODE` (one plant on a real
     filed claim plus one real filed claim), excluding every order of this wave. Seed output stays in scratch.
  3. Writes REVIEW_SET.jsonl (claims as reviewers see them), one seeded shuffle per arm, GENUINE_CONTROLS.jsonl,
     the private key keys/BATCH.json, and renders reviewer prompts for each arm.
"""
import copy, hashlib, json, random, subprocess, sys
from pathlib import Path
REPO = Path('/home/user/Executive-Orders'); E = Path('/tmp/claude-0/dorotheus-wave')
T = Path(__file__).resolve().parent / 'prompts'
def canon(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
def shift(d):
    if not isinstance(d, str) or len(d) < 10 or not d[:4].isdigit(): return d
    md = d[4:10]; md = '-02-28' if md == '-02-29' else md
    return f"{int(d[:4]) - 3:04d}{md}{d[10:]}"
def has_end(c):
    return isinstance(c.get('whole_order_end'), dict) or any(isinstance(x.get('first_end'), dict) and x['first_end'].get('date') for x in c.get('operative_clauses', []))
def has_event(c): return any(e.get('effective_date') or e.get('date') for x in c.get('operative_clauses', []) for e in x.get('later_events', []) if isinstance(e, dict))
def plant(c, mode):
    p = copy.deepcopy(c); n = 0
    if mode == 'end':
        we = p.get('whole_order_end')
        if isinstance(we, dict) and we.get('date'): we['date'] = shift(we['date']); n += 1
        for x in p.get('operative_clauses', []):
            fe = x.get('first_end')
            if isinstance(fe, dict) and fe.get('date'): fe['date'] = shift(fe['date']); n += 1
    elif mode == 'signing':
        def walk(o):
            nonlocal n
            if isinstance(o, dict):
                for k in list(o):
                    if k == 'signing_date' and isinstance(o[k], str): o[k] = shift(o[k]); n += 1
                    else: walk(o[k])
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(p)
    else:
        for x in p.get('operative_clauses', []):
            for e in x.get('later_events', []):
                for k in ('effective_date', 'date'):
                    if isinstance(e, dict) and e.get(k): e[k] = shift(e[k]); n += 1
    return p, n
def SW_REL(c):
    import glob as g
    hits = g.glob(str(REPO / 'research/excavator/dorotheus-sample-2026-11-06/u*/packet/overlay' / c['instrument_id'].replace(':', '_') / 'proposal-v1'))
    return hits[0] if hits else '?'
def main(b, claims_path, mwcode, arms='AB'):
    W = REPO / ('research/excavator/dorotheus-yesprobe-2026-11-06' if b.startswith('y') else 'research/excavator/dorotheus-sample-2026-11-06')
    P = W / b / 'packet' if not b.startswith('ux') else W / b
    claims = [json.loads(l) for l in open(claims_path, encoding='utf-8') if l.strip()]
    elig = [c for c in claims if has_end(c)]; mode, defect = 'end', 'every first_end and whole_order_end date moved back three years'
    if not elig:
        elig = [c for c in claims if has_event(c)]; mode, defect = 'event', 'every later_events effective date moved back three years'
    if not elig:
        elig = list(claims); mode, defect = 'signing', 'every signing_date of the order moved back three years'
    n = max(1, round(len(claims) / 15)) if claims else 0
    rng = random.Random(hashlib.sha256(('dorotheus-controls:' + b).encode()).hexdigest())
    picks = {c['instrument_id'] for c in rng.sample(sorted(elig, key=lambda c: c['instrument_id']), min(n, len(elig)))}
    out, key, genuine = [], {'batch': b, 'controls': [], 'mountweazel': None}, []
    for c in claims:
        if c['instrument_id'] in picks:
            p, k = plant(c, mode); assert k, c['instrument_id']
            out.append(p); genuine.append(c)
            key['controls'].append({'instrument_id': c['instrument_id'], 'planted': canon(p), 'genuine': canon(c), 'defect': defect, 'type': 'date_shift_' + mode})
        else: out.append(c)
    # Mountweazel plant on a real filed claim (exclude every order of this wave)
    wave = json.load(open(E / 'batches.json'))
    excl = sorted({i for v in wave['packets'].values() for i in v} | {k.split('|')[-1] for k in wave['pre_routed']})
    idx = sorted(wave['packets']).index(b) if b in wave['packets'] else 30 + int(b[2:])
    mwid = f'MW-C{700 + idx}'
    r = subprocess.run(['python3', '-I', 'jobs/mountweazel/mountweazel.py', 'seed', '--track', 'C', '--batch-id', mwid,
                        '--seed', 'dorotheus-2026-11-06-' + b, '--n', '2', '--share', '0.5', '--codes', mwcode,
                        '--exclude-orders', ','.join(excl), '--out', str(E / 'mw'), '--fixtures-dir', str(E / 'mw/fixtures')],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode == 0:
        man = json.loads((E / 'mw' / mwid / 'batch/MANIFEST.json').read_text())
        mk = json.loads((E / 'mw' / mwid / 'key/KEY.sealed.json').read_text())
        items = []
        for it in man['items']:
            d = json.loads((E / 'mw' / mwid / 'batch/items' / f'{it}.json').read_text())
            ent = next(x for x in mk['items'] if x['item_id'] == it)
            items.append({'item_id': it, 'instrument_id': d['claim']['instrument_id'], 'claim_sha256': canon(d['claim']),
                          'is_seeded': ent['is_seeded'], 'defect_code': ent.get('defect_code'), 'field': ent.get('field')})
            out.append(d['claim'])
        key['mountweazel'] = {'batch_id': mwid, 'key': str(E / 'mw' / mwid / 'key/KEY.sealed.json'), 'items': items}
    else:
        key['mountweazel'] = {'batch_id': mwid, 'error': (r.stdout + r.stderr)[-600:], 'requested_code': mwcode}
    rd = E / 'review' / b; rd.mkdir(parents=True, exist_ok=True)
    (rd / 'REVIEW_SET.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in out))
    (rd / 'GENUINE_CONTROLS.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in genuine))
    (E / 'keys').mkdir(exist_ok=True); (E / 'keys' / f'{b}.json').write_text(json.dumps(key, indent=1))
    (P / 'reviews').mkdir(exist_ok=True)
    und = (P / 'undecided').exists() or b.startswith('ux')
    unote = ('Some claims are undecided orders filed through the isolated status-overlay route: their whole_order_status is the producer\'s own reviewed status proposal, not a ledger status; judge whether held sources support that status and lifecycle on the order\'s own terms and the recorded bounded searches. An explicit empty status history is not evidence either way.' if und else '')
    for arm in arms:
        rows = list(out); random.Random(f'dorotheus-{b}-{arm}').shuffle(rows)
        (rd / f'REVIEW_SET_{arm}.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in rows))
        t = (T / 'reviewer.txt').read_text().replace('SETPATH', str(rd / f'REVIEW_SET_{arm}.jsonl')).replace('PACKETDIR', str(P))
        t = t.replace('NCLAIMS', str(len(rows))).replace('UNDECIDEDNOTE', unote).replace('SCRATCH', f'/tmp/claude-0/dorotheus-scratch/{b}-{arm}')
        t = t.replace('BATCH', b).replace('ARM', arm)
        if b.startswith('ux'):
            ev = '; '.join(f"{c['instrument_id']}: {SW_REL(c)}" for c in claims)
            t = t.replace(f'Frozen packet for this batch: {P}/PACKET.json (load with jobs/claim-kit/batch.py load_packet(folder, repo, check_sources=False), absolute paths); a claim whose claim_kit metadata names a different packet is reviewed from the repository sources it cites.',
                          'These claims come from several undecided packets. For each, the frozen evidence is the overlay bundle named here (read only its EVIDENCE.json and DOSSIER.json; DOSSIER.json carries the working status): ' + ev + '. A claim not listed here is reviewed from the repository sources it cites.')
            t = t.replace(f'{P}/reviews/BLIND_REVIEW_{arm}.jsonl', f'{P}/reviews/BLIND_REVIEW_{arm}.jsonl')
        (E / 'prompts' / f'reviewer-{b}-{arm}.txt').write_text(t)
    print(json.dumps({'batch': b, 'claims': len(claims), 'review_set': len(out), 'controls': sorted(picks), 'mode': mode,
                      'mountweazel': {k: v for k, v in key['mountweazel'].items() if k != 'key'}}))
if __name__ == '__main__': main(*sys.argv[1:])
