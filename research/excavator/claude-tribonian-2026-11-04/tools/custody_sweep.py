"""Queue byte retention for every claim source the actual checker marks custody_record_only (coordinator tool).

usage: python3 custody_sweep.py BATCH [BATCH ...]
  Reads each batch's newest applied-vN/actual-checker/CLAIM_CHECKS.csv and CLAIMS.proposed.jsonl, collects the cited
  (url, sha256) pairs, appends APP pages to jobs/cotton-capture-custody/data/WANTED.jsonl and other https sources to
  research/readiness/FETCH_QUEUE.jsonl, and writes up to 30 not-yet-retained sources to
  jobs/astra-source-retention/REQUESTS.json (the rest stay in scratch retention_backlog.json). No judgment.
"""
import csv, glob, json, re, sys
from pathlib import Path
REPO = Path('/home/claude/executive-orders'); R = REPO / 'research/excavator/claude-tribonian-2026-11-04'
SCR = Path('/tmp/claude-0/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/scratchpad/tribonian')
need = {}
for b in sys.argv[1:]:
    ds = sorted(glob.glob(str(R / b / 'packet/applied-v*')), key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', p.rsplit('applied-v', 1)[1])])
    if not ds or not Path(ds[-1], 'actual-checker/CLAIM_CHECKS.csv').exists():
        print(b, 'no checker output'); continue
    d = Path(ds[-1]); bad = {}
    for r in csv.DictReader(open(d / 'actual-checker/CLAIM_CHECKS.csv')):
        if r['status'] == 'custody_record_only':
            bad.setdefault(r['instrument_id'], set()).add(r['field'])
    for line in open(d / 'CLAIMS.proposed.jsonl'):
        c = json.loads(line)
        for fld in bad.get(c['instrument_id'], ()):
            o = c
            for part in re.findall(r'[^.\[\]]+|\[\d+\]', fld):
                o = o[int(part[1:-1])] if part.startswith('[') else o[part]
            if o.get('url') and o.get('sha256'):
                need.setdefault((o['url'], o['sha256']), set()).add(c['instrument_id'])
wp = REPO / 'jobs/cotton-capture-custody/data/WANTED.jsonl'
have = {(json.loads(l)['sha256'], json.loads(l).get('instrument_id')) for l in open(wp) if l.strip() and not l.startswith('#')}
retained = set()
src = REPO / 'jobs/astra-source-retention/output/SOURCES.jsonl'
if src.exists():
    retained = {json.loads(l).get('sha256') for l in open(src) if l.strip()}
queue = [json.loads(l) for l in open(REPO / 'research/readiness/FETCH_QUEUE.jsonl') if l.strip()]
queued = {(q.get('instrument_id'), u) for q in queue for u in q.get('urls', [])}
cot, fq, backlog = [], [], []
for (url, sha), ids in sorted(need.items()):
    if 'presidency.ucsb.edu' in url:
        cot += [{'instrument_id': i, 'sha256': sha, 'url': url} for i in sorted(ids) if (sha, i) not in have]
    elif url.startswith('https://') and sha not in retained:
        fq += [{'instrument_id': i, 'urls': [url], 'citation': url, 'requested_by': 'Claude Tribonian 2026-11-04',
                'note': 'Retain the exact bytes cited by a reviewed Tribonian claim; custody copy only.'} for i in sorted(ids) if (i, url) not in queued]
        backlog.append({'url': url, 'instrument_ids': sorted(ids), 'expected_sha256': sha, 'pages': []})
with open(wp, 'a') as f:
    for x in cot: f.write(json.dumps(x) + '\n')
with open(REPO / 'research/readiness/FETCH_QUEUE.jsonl', 'a') as f:
    for x in fq: f.write(json.dumps(x) + '\n')
old = json.loads((SCR / 'retention_backlog.json').read_text()) if (SCR / 'retention_backlog.json').exists() else []
seen = {x['url'] for x in backlog}
backlog += [x for x in old if x['url'] not in seen and x['expected_sha256'] not in retained]
json.dump(backlog[:30], open(REPO / 'jobs/astra-source-retention/REQUESTS.json', 'w'), indent=2)
json.dump(backlog[30:], open(SCR / 'retention_backlog.json', 'w'), indent=2)
print(json.dumps({'sources_needed': len(need), 'cotton_added': len(cot), 'fetch_queue_added': len(fq),
                  'retention_requested': min(30, len(backlog)), 'retention_backlog': max(0, len(backlog) - 30)}))
