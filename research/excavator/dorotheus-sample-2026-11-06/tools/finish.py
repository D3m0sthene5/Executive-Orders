"""Finish one Dorotheus decided-route packet after blind and after-reveal reviews (coordinator; rules fixed in
advance, no legal judgment).

usage: python3 -I finish.py BATCH APPLIED_VERSION
  Arms: every reviews/BLIND_REVIEW_<arm>.jsonl present (A, B and, after a missed plant, C).
  Date-shift control: an arm CATCHES it if its blind review of the exact planted hash is "rejected" and names a
  date defect. Mountweazel plant: an arm catches it if it rejects the exact planted hash (strict locus scoring is
  done separately with mountweazel.py score). If any arm missed any plant, a fresh third arm (C) is required; the
  script reports "need_arm_C" and stops until BLIND_REVIEW_C.jsonl exists.
  Kit control adjudication: caught when every arm caught it, or (after a miss) when arm C and at least one other
  arm caught it; the miss stays recorded in the adjudication text and PLANTS rows.
  A genuine claim files only if EVERY arm that reviewed it upheld it (blind "upheld"; genuine control versions
  "upheld_after_reveal" in every arm's AFTER_REVEAL file).
  Writes PACKET/completion/ (seed receipts, adjudications, COMPLETION.json, MULTI_ARM_RULE.json), runs
  kit.py complete WITHOUT --publish into PACKET/complete-vN (a dry check), and prints PLANTS rows as JSON.
  Publication happens once per wave with merge.py.
"""
import glob, hashlib, json, subprocess, sys
from pathlib import Path
E = Path('/tmp/claude-0/dorotheus-wave'); REPO = Path('/home/user/Executive-Orders')
MAKE = REPO / 'research/excavator/claude-nira-sweep-2026-10-29/make_completion.py'
def load(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()] if Path(p).exists() else []
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dated(r): return any(w in json.dumps(r.get('defects', []), ensure_ascii=False).lower() for w in ('date', 'first_end', 'whole_order_end', 'year', 'effective'))
def main(b, version):
    W = REPO / ('research/excavator/dorotheus-yesprobe-2026-11-06' if b.startswith('y') else 'research/excavator/dorotheus-sample-2026-11-06')
    packet = W / b / 'packet'; applied = packet / version; rv = packet / 'reviews'
    key = json.loads((E / 'keys' / f'{b}.json').read_text())
    arms = sorted(Path(p).stem.rsplit('_', 1)[1] for p in glob.glob(str(rv / 'BLIND_REVIEW_*.jsonl')))
    blind = {a: {r.get('claim_sha256'): r for r in load(rv / f'BLIND_REVIEW_{a}.jsonl')} for a in arms}
    after = {a: {r.get('claim_sha256'): r for r in load(rv / f'AFTER_REVEAL_{a}.jsonl')} for a in arms}
    plants = []
    for k in key['controls']:
        for a in arms:
            r = blind[a].get(k['planted'])
            plants.append({'packet': b, 'plant_id': f"{b}:{k['instrument_id']}", 'defect_type': k['type'], 'arm': a,
                           'caught': 'yes' if r and r.get('verdict') == 'rejected' and dated(r) else 'no', 'kit': k})
    mw = key.get('mountweazel') or {}
    for it in mw.get('items', []):
        if not it['is_seeded']: continue
        for a in arms:
            r = blind[a].get(it['claim_sha256'])
            plants.append({'packet': b, 'plant_id': f"{mw['batch_id']}:{it['item_id']}", 'defect_type': 'mountweazel_' + str(it['defect_code']),
                           'arm': a, 'caught': 'yes' if r and r.get('verdict') == 'rejected' else 'no'})
    missed = [p for p in plants if p['caught'] == 'no']
    if missed and 'C' not in arms:
        print(json.dumps({'batch': b, 'need_arm_C': sorted({p['plant_id'] + '/' + p['arm'] for p in missed})})); return 3
    out = packet / 'completion'; out.mkdir(exist_ok=True)
    judg, kit_missed = [], []
    for k in key['controls']:
        res = {p['arm']: p['caught'] == 'yes' for p in plants if p.get('kit') is k}
        ok = all(res.values()) or (res.get('C') and sum(res.values()) >= 2)
        seed = {'schema': 'eo-claim-kit-control-seed/v1', 'instrument_id': k['instrument_id'], 'planted_claim_sha256': k['planted'],
                'genuine_claim_sha256': k['genuine'], 'seeded_by': 'dorotheus-coordinator-2026-11-06'}
        (out / ('SEED_RECEIPT_' + k['instrument_id'].replace(':', '_') + '.json')).write_text(json.dumps(seed, indent=1) + '\n')
        why = (f"Planted version: {k['defect']}. Arm results {res} (caught = rejected and named the date defect); "
               + ('caught under the multi-arm rule.' if ok else 'not caught under the multi-arm rule.'))
        judg.append(f"{k['instrument_id']}={'caught' if ok else 'missed'}|{why}")
        if not ok: kit_missed.append(k['instrument_id'])
    # control review ref: an arm that caught it (prefer A)
    catch_arm = next((a for a in arms if all(p['caught'] == 'yes' for p in plants if p.get('kit') and p['arm'] == a)), arms[0])
    pub = f"research/readiness/claims/dorotheus-2026-11-06-{'yesprobe' if b.startswith('y') else 'sample'}.jsonl"
    cmd = ['python3', '-I', str(MAKE), str(packet), str(applied), str(rv / 'BLIND_REVIEW_A.jsonl'),
           str(rv / 'AFTER_REVEAL_A.jsonl') if (rv / 'AFTER_REVEAL_A.jsonl').exists() else '-',
           str(E / 'keys' / f'{b}.json'), pub, 'dorotheus-coordinator-2026-11-06', *judg,
           '--planted-review', str(rv / f'BLIND_REVIEW_{catch_arm}.jsonl')]
    receipts = [str(p) for a in arms if a != 'A' for p in (rv / f'BLIND_REVIEW_{a}.jsonl', rv / f'AFTER_REVEAL_{a}.jsonl') if p.exists()]
    if receipts: cmd += ['--receipt', *receipts]
    print(subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=True).stdout.strip())
    mpath = out / 'COMPLETION.json'; m = json.loads(mpath.read_text())
    controls = {k['instrument_id'] for k in key['controls']}
    rule = {'rule': 'a claim files only if every arm that reviewed it upheld it', 'arms': arms, 'blocked': {}}
    for i, mem in enumerate(m['members']):
        if mem['outcome'] != 'submit': continue
        sha = mem['claim_sha256']; src = after if mem['instrument_id'] in controls else blind
        want = 'upheld_after_reveal' if mem['instrument_id'] in controls else 'upheld'
        bad = {a: src[a].get(sha) for a in arms if not src[a].get(sha) or src[a][sha].get('verdict') != want}
        if bad:
            why = {a: (r.get('defects') if r else 'no record for this exact version') for a, r in bad.items()}
            m['members'][i] = {'instrument_id': mem['instrument_id'], 'outcome': 'blocked',
                               'reason': 'Not upheld by every reviewing arm: ' + json.dumps(why, ensure_ascii=False)[:3000]}
            rule['blocked'][mem['instrument_id']] = sorted(bad)
    (out / 'MULTI_ARM_RULE.json').write_text(json.dumps(rule, indent=1) + '\n')
    m['receipts'].append({'path': str((out / 'MULTI_ARM_RULE.json').relative_to(REPO)), 'sha256': fsha(out / 'MULTI_ARM_RULE.json')})
    mpath.write_text(json.dumps(m, indent=1, ensure_ascii=False) + '\n')
    (out / 'PLANTS.json').write_text(json.dumps([{k: v for k, v in p.items() if k != 'kit'} for p in plants], indent=1) + '\n')
    if kit_missed:
        print(json.dumps({'batch': b, 'kit_missed_controls': kit_missed, 'action': 'batch does not file'})); return 2
    n = 1
    while (packet / f'complete-v{n}').exists(): n += 1
    p = subprocess.run(['python3', 'jobs/claim-kit/kit.py', 'complete', str(mpath), '--write', str(packet / f'complete-v{n}')],
                       cwd=REPO, capture_output=True, text=True)
    (packet / f'COMPLETE_v{n}.log').write_text(p.stdout + '\n' + p.stderr)
    print(json.dumps(rule), p.stdout[-1200:], p.stderr[-600:], 'exit', p.returncode)
    return p.returncode
if __name__ == '__main__': sys.exit(main(*sys.argv[1:]))
