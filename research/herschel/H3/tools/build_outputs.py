"""Build H3 TRACE.jsonl and ORDER_OUTCOMES.csv from worker step files, launch logs and coordinator dispatch blocks.
Coordinator tool; no legal judgment (outcomes are copied from worker step files and dispatch-check receipts)."""
import csv, glob, json, re
from pathlib import Path
R = Path('/home/claude/executive-orders'); H = R / 'research/herschel/H3'
S = Path('/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H3')
A = json.load(open(R / 'research/herschel/frame/ASSIGNMENTS.json'))
mine = next(c for c in A['coordinators'] if c['name'] == 'H3')['orders']
ORD = {r['instrument_id']: r for r in csv.DictReader(open(R / 'research/herschel/frame/ORDERS.csv'))}
STEP = {'H3-w01': 'certification_reading', 'H3-w02': 'original_text', 'H3-w03': 'original_text', 'H3-w04': 'original_text',
        'H3-w11': 'original_text', 'H3-w05': 'lifecycle_claim', 'H3-w06': 'lifecycle_claim', 'H3-w07': 'provisional_status',
        'H3-w08': 'provisional_status', 'H3-w09': 'provisional_status', 'H3-w10': 'provisional_status',
        'H3-w12': 'review', 'H3-w13': 'review'}
LIFE = ['clause_inventory', 'ending_or_current_basis', 'savings_residuals', 'counterevidence']
MODEL = {}
starts = {}; ends = {}
for l in open(S / 'starts.jsonl'):
    d = json.loads(l); starts.setdefault(d['worker'], d); MODEL[d['worker']] = d['model']
for l in open(S / 'ends.jsonl'):
    d = json.loads(l); ends[d['worker']] = d['ended_utc']
LIMIT = re.compile(r'rate.?limit|usage limit|overloaded|429|529|quota', re.I)

def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if Path(p).exists() else []

# worker outcomes from step files
outc = {}   # (iid, step) -> (outcome, worker)
trace = []
for w in sorted(STEP):
    st = STEP[w]; rows = []
    for f in glob.glob(str(H / 'steps' / f'{w}_*.jsonl')):
        rows += jl(f)
    if w == 'H3-w01':
        rows = [{'instrument_id': r['instrument_id'], 'outcome': 'done'} for r in jl(H / 'CERT_READING.jsonl')]
    if st == 'review':
        b = 's2'; arm = 'A' if w == 'H3-w12' else 'B'
        key = json.load(open(S / 'keys' / f'{b}.json'))
        planted = {k['planted']: k['instrument_id'] for k in key['controls']}
        blind = jl(H / 'reviews' / b / f'BLIND_REVIEW_{arm}.jsonl')
        ctrl = {planted[r['proposal_sha256']]: ('caught' if r['verdict'] == 'rejected' and any(w_ in json.dumps(r['defects']).lower() for w_ in ('date', 'bound', '1938', '1941')) else 'missed')
                for r in blind if r.get('proposal_sha256') in planted}
        # Genuine verdict for a planted order is its after-reveal review; other orders keep the blind verdict.
        final = {r['instrument_id']: r for r in blind if r.get('proposal_sha256') not in planted}
        final.update({r['instrument_id']: r for r in jl(H / 'reviews' / b / f'AFTER_REVEAL_{arm}.jsonl')})
        rows = [{'instrument_id': i, 'outcome': 'upheld' if r['verdict'].startswith('upheld') else
                 'rejected:' + '; '.join(d.get('defect', '')[:160] for d in r.get('defects', []) if not d.get('defect', '').startswith(('Minor', 'Limit')))}
                for i, r in final.items()]
    o = {}
    for r in rows:
        x = r['outcome']
        if x.startswith('proposed:'): x = 'done:' + x
        elif x == 'submitted': x = 'done:submitted'
        o[r['instrument_id']] = x
    err = ''
    try: err = open(S / 'run' / f'{w}.err').read()
    except OSError: pass
    res = ''
    try: res = json.load(open(S / 'run' / f'{w}.json')).get('result', '')
    except Exception: pass
    events = [m.group(0) for m in LIMIT.finditer(err)]
    strata = sorted({ORD[i]['stratum'] for i in o if i in ORD}) or ['ready']
    extra = {'controls': ctrl, 'batch': 's2', 'after_reveal_resume': True} if st == 'review' else {}
    trace.append({'worker': w, 'step': st, 'model': MODEL.get(w), 'stratum': '|'.join(strata), 'orders': sorted(o), **extra,
                  'started_utc': starts[w]['started_utc'], 'ended_utc': ends.get(w),
                  'concurrent_workers_at_start': starts[w]['concurrent_workers_at_start'], 'limit_events': events,
                  'outcomes': o})
    for i, x in o.items():
        if st == 'lifecycle_claim':
            for s in LIFE: outc[(i, s)] = (x, w)
        elif st == 'review':
            prev = outc.get((i, st))
            if prev:   # both arms must uphold
                x = 'upheld' if prev[0] == 'upheld' and x == 'upheld' else ('rejected:' + ' | '.join(
                    f'{ww}:{xx}' for ww, xx in ((prev[1], prev[0]), (w, x))))
                w = prev[1] + '+' + w
            outc[(i, st)] = (x, w)
        elif st != 'certification_reading':
            outc[(i, st)] = (x, w)
# EO 6983 original_text: H3-w03 failed (no renderer); H3-w11 redid it. Both attempts are in TRACE; the final outcome is w11's.
# coordinator dispatch-check blocks (no worker): decided members whose required sources are custody_record_only
for b in ('y1', 'y2'):
    d = json.load(open(H / 'packets' / b / 'dispatch-pre.json'))
    for m in d['members']:
        if m['instrument_id'] in d['source_blocked_ids']:
            srcs = sorted({(x.get('source') or {}).get('page_or_item', '') for x in m['blockers']})
            x = 'blocked:retain raw source bytes (custody_record_only) of ' + ' / '.join(s[:70] for s in srcs)
            for s in LIFE:
                outc[(m['instrument_id'], s)] = (x, 'coordinator-dispatch-check')
rows = []
for i in mine:
    r = ORD[i]
    steps = r['open_steps'].split('|')
    for s in steps + ['review']:
        if (i, s) in outc:
            x, w = outc[(i, s)]
        elif s == 'opus_media':
            x, w = 'blocked:opus media refetch (cited files not packaged; zero-agent network job)', 'coordinator'
        elif s in LIFE and r['status'] == 'none':
            x, w = 'blocked:provisional status (no reviewed status proposal; kit lifecycle route needs one)', 'coordinator'
        elif s in LIFE:
            x, w = 'not_reached', ''
        elif s == 'review':
            x, w = 'blocked:no claim or status proposal to review (upstream steps blocked)', 'coordinator'
        else:
            x, w = 'not_reached', ''
        rows.append({'instrument_id': i, 'stratum': r['stratum'], 'step': s, 'outcome': x, 'worker': w})
with open(H / 'ORDER_OUTCOMES.csv', 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, ['instrument_id', 'stratum', 'step', 'outcome', 'worker']); wr.writeheader(); wr.writerows(rows)
with open(H / 'TRACE.jsonl', 'w', encoding='utf-8') as f:
    for t in trace: f.write(json.dumps(t, ensure_ascii=False) + '\n')
from collections import Counter
print(Counter((r['step'], r['outcome'].split(':')[0]) for r in rows))
