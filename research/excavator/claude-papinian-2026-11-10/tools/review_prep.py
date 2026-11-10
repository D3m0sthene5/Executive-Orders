"""Papinian: plant controls and build two blind review sets for one batch (coordinator tool; no legal judgment).
usage: python -I review_prep.py BATCH APPLIED_DIRNAME [NOTE_FILE]
  Plants max(1, round(n/15)) controls among the submitted claims (seeded by batch name): every first_end and
  whole_order_end date moved back three years; if no claim has an end date, every later_events date; else every
  signing_date. Writes (outside the repository) SCR/review/BATCH/REVIEW_SET.jsonl, REVIEW_SET_{A,B}.jsonl (separately
  shuffled), GENUINE_CONTROLS.jsonl, the private key SCR/keys/BATCH.json, and the reviewer and reveal prompts."""
import copy, hashlib, json, random, sys
from pathlib import Path
REPO = Path('C:/Users/danie/eo-wt/papinian'); SCR = Path('C:/Users/danie/AppData/Local/Temp/papinian')
T = Path(__file__).resolve().parent / 'prompts'
def canon(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
def shift(d):
    if not isinstance(d, str) or len(d) < 10 or not d[:4].isdigit(): return d
    md = d[4:10]; md = '-02-28' if md == '-02-29' else md
    return f"{int(d[:4]) - 3:04d}{md}{d[10:]}"
def has_end(c):
    return (isinstance(c.get('whole_order_end'), dict) and c['whole_order_end'].get('date')) or any(
        isinstance(x.get('first_end'), dict) and x['first_end'].get('date') for x in c.get('operative_clauses', []))
def has_event(c): return any(isinstance(e, dict) and (e.get('effective_date') or e.get('date')) for x in c.get('operative_clauses', []) for e in x.get('later_events', []))
def plant(c, mode):
    p = copy.deepcopy(c); n = 0
    if mode == 'end':
        we = p.get('whole_order_end')
        if isinstance(we, dict) and we.get('date'): we['date'] = shift(we['date']); n += 1
        for x in p.get('operative_clauses', []):
            fe = x.get('first_end')
            if isinstance(fe, dict) and fe.get('date'): fe['date'] = shift(fe['date']); n += 1
    elif mode == 'event':
        for x in p.get('operative_clauses', []):
            for e in x.get('later_events', []):
                for k in ('effective_date', 'date'):
                    if isinstance(e, dict) and e.get(k): e[k] = shift(e[k]); n += 1
    else:
        def walk(o):
            nonlocal n
            if isinstance(o, dict):
                for k in list(o):
                    if k == 'signing_date' and isinstance(o[k], str): o[k] = shift(o[k]); n += 1
                    else: walk(o[k])
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(p)
    return p, n
DEFECT = {'end': 'every first_end and whole_order_end date moved back three years',
          'event': 'every later_events effective date moved back three years',
          'signing': 'every signing_date of the order moved back three years'}
def main(b, applied, note=None):
    P = REPO / 'research/excavator/claude-papinian-2026-11-10' / b / 'packet'
    claims = [json.loads(l) for l in open(P / applied / 'CLAIMS.proposed.jsonl', encoding='utf-8') if l.strip()]
    elig = [c for c in claims if has_end(c)]; mode = 'end'
    if not elig: elig = [c for c in claims if has_event(c)]; mode = 'event'
    if not elig: elig = list(claims); mode = 'signing'
    n = max(1, round(len(claims) / 15)) if claims else 0
    rng = random.Random(hashlib.sha256(('papinian-controls:' + b).encode()).hexdigest())
    picks = {c['instrument_id'] for c in rng.sample(sorted(elig, key=lambda c: c['instrument_id']), min(n, len(elig)))}
    out, genuine, key = [], [], {'batch': b, 'applied': applied, 'controls': []}
    for c in claims:
        if c['instrument_id'] in picks:
            p, k = plant(c, mode); assert k, c['instrument_id']
            out.append(p); genuine.append(c)
            key['controls'].append({'instrument_id': c['instrument_id'], 'planted': canon(p), 'genuine': canon(c),
                                    'defect': DEFECT[mode], 'type': 'date_shift_' + mode})
        else:
            out.append(c)
    rd = SCR / 'review' / b; rd.mkdir(parents=True, exist_ok=True)
    w = lambda path, rows: path.write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in rows), encoding='utf-8')
    w(rd / 'REVIEW_SET.jsonl', out); w(rd / 'GENUINE_CONTROLS.jsonl', genuine)
    (SCR / 'keys' / f'{b}.json').write_text(json.dumps(key, indent=1), encoding='utf-8')
    (P / 'reviews').mkdir(exist_ok=True)
    (P / 'APPLIED_FOR_REVIEW').write_text(applied + '\n', encoding='utf-8')
    bn = Path(note).read_text(encoding='utf-8').strip() if note else ''
    pk = P.relative_to(REPO).as_posix()
    for arm in 'AB':
        rows = list(out); random.Random(f'papinian-{b}-{arm}').shuffle(rows)
        sp = rd / f'REVIEW_SET_{arm}.jsonl'; w(sp, rows)
        rs = f'C:/Users/danie/AppData/Local/Temp/papinian/rev/{b}-{arm}/'
        t = (T / 'reviewer.txt').read_text(encoding='utf-8')
        t = t.replace('SETPATH', sp.as_posix()).replace('PACKETDIR', pk).replace('BATCHNOTE', bn).replace('REVSCRATCH', rs)
        t = t.replace('BATCH', b).replace('ARM', arm)
        (SCR / 'prompts' / f'reviewer-{b}-{arm}.txt').write_text(t, encoding='utf-8')
        ids = ', '.join(k['instrument_id'] for k in key['controls'])
        defects = '; '.join(sorted({k['defect'] for k in key['controls']}))
        r = (f"After-reveal step for batch {b}, arm {arm}. The claim(s) for {ids} in your review set were planted controls ({defects}). "
             f"The genuine version(s) the producer filed are in {(rd / 'GENUINE_CONTROLS.jsonl').as_posix()} (one JSON claim per line). "
             "Review each genuine version on its merits with the same blinding and the same standard as your blind review (it must pass every check you applied to other claims; do not uphold it just because it is the genuine one). "
             f"Write one JSON object per genuine claim to {pk}/reviews/AFTER_REVEAL_{arm}.jsonl, in the same format as your BLIND_REVIEW_{arm}.jsonl records, with claim_sha256 computed the same way over the genuine claim, the same reviewer name, verdict \"upheld_after_reveal\" if it is right or \"rejected\" with defects if not, and started_utc/ended_utc. "
             f"Do not change BLIND_REVIEW_{arm}.jsonl. Reply in at most 60 words with each order and its verdict.")
        (SCR / 'prompts' / f'reveal-{b}-{arm}.txt').write_text(r, encoding='utf-8')
    print(json.dumps({'batch': b, 'claims': len(claims), 'mode': mode, 'controls': sorted(picks)}))
if __name__ == '__main__':
    main(*sys.argv[1:])
