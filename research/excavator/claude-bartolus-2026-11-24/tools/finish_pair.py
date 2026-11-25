"""Finish one Papinian batch reviewed by two independent blind arms (coordinator; scoring rule fixed in advance).
usage: python -I finish_pair.py BATCH [--publish]     (env REPLACEMENT=1: isolated replacement proposal)
  A planted control is CAUGHT only if BOTH arms rejected its exact planted hash and named a date defect (defect text
  mentions date, first_end, whole_order_end, signing, later_event, effective or year). Any miss stops the batch
  before completion. Builds the completion manifest with make_completion.py from arm A's records, then applies the
  both-uphold rule: a submitted member files only if arm B also upheld the exact same claim hash (blind, or
  upheld_after_reveal for a genuine control); otherwise it becomes a blocked member quoting arm B's defects. Arm B's
  review files are pinned as receipts. Then runs kit.py complete into a new complete-vN (--publish only when asked).
  Publication (own claims): the claim kit chooses the file name (`kit.py publication-name`, completion.py
  own_publication_path): AGENT-2026-11-24-bartolus-BATCH.jsonl when that sorts after every existing claim file of the
  submitted members, otherwise LAST_STEM_corrected-2026-11-24-bartolus-BATCH.jsonl after the member file that sorts
  last. (Files this wave already published used hand-chosen names: bartolus-2026-11-24-BATCH.jsonl and
  claude-2026-11-24-bartolus-BATCH.jsonl.) A hand-made dated name sorts before older undated files and completion
  refuses it (EO 14006, Bracton p04, 2026-11-25)."""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path('/home/claude/d3m0sthene5/executive-orders')
SCR = Path('/home/claude/bartolus-scr')
RUN = REPO / 'research/excavator/claude-bartolus-2026-11-24'
MAKE = REPO / 'research/excavator/claude-nira-sweep-2026-10-29/make_completion.py'
ADJ = 'claude-coordinator-bartolus-2026-11-24'
DATE, WAVE = '2026-11-24', 'bartolus'
WORDS = ('date', 'first_end', 'whole_order_end', 'signing', 'later_event', 'effective', 'year')


def load(p):
    return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()] if Path(p).exists() else []


def caught(rec):
    if not rec or rec.get('verdict') != 'rejected':
        return False
    text = json.dumps([rec.get('defects', []), rec.get('reasons', ''), rec.get('reason', '')], ensure_ascii=False).lower()
    return any(w in text for w in WORDS)


def main(batch, *flags):
    packet = RUN / batch / 'packet'
    applied = packet / (packet / 'APPLIED_FOR_REVIEW').read_text(encoding='utf-8').strip()
    key = json.loads((SCR / 'keys' / f'{batch}.json').read_text(encoding='utf-8'))
    agent = json.loads((packet / 'PACKET.json').read_text(encoding='utf-8'))['agent']
    rv = packet / 'reviews'
    blind = {a: {r['claim_sha256']: r for r in load(rv / f'BLIND_REVIEW_{a}.jsonl')} for a in 'AB'}
    after = {a: {r['claim_sha256']: r for r in load(rv / f'AFTER_REVEAL_{a}.jsonl')} for a in 'AB'}
    out = packet / 'completion'
    out.mkdir(exist_ok=True)
    judg, missed = [], []
    for k in key['controls']:
        iid = k['instrument_id']
        seed = {'schema': 'eo-claim-kit-control-seed/v1', 'instrument_id': iid, 'planted_claim_sha256': k['planted'],
                'genuine_claim_sha256': k['genuine'], 'seeded_by': ADJ}
        (out / ('SEED_RECEIPT_' + iid.replace(':', '_') + '.json')).write_text(json.dumps(seed, indent=1) + '\n', encoding='utf-8')
        ok = {a: caught(blind[a].get(k['planted'])) for a in 'AB'}
        if all(ok.values()):
            why = f"Planted version: {k['defect']}; both independent blind arms (A and B) rejected that exact planted hash and named the date defect."
        else:
            why = f"Planted version: {k['defect']}; arm(s) {','.join(a for a in 'AB' if not ok[a])} did not reject it for the date defect."
        judg.append(f"{iid}={'caught' if all(ok.values()) else 'missed'}|{why}")
        if not all(ok.values()):
            missed.append(iid)
    if missed:
        print(json.dumps({'batch': batch, 'missed_controls': missed, 'action': 'STOP: not completed'}))
        return 2
    if os.environ.get('REPLACEMENT'):
        pub = f'research/excavator/claude-bartolus-2026-11-24/{batch}/REPLACEMENT_PROPOSAL.jsonl'
    else:
        pub = f'research/readiness/claims/{agent}-{DATE}-{WAVE}-{batch}.jsonl'  # placeholder; chosen below
    receipts = [str(rv / f) for f in ('BLIND_REVIEW_B.jsonl', 'AFTER_REVEAL_B.jsonl') if (rv / f).exists()]
    for extra in ('CARRY.json', 'PRODUCER_REPORT.md', 'ASSESSMENT.jsonl'):
        if (packet / extra).exists():
            receipts.append(str(packet / extra))
    cmd = ['python3', '-X', 'utf8', '-I', str(MAKE), str(packet), str(applied), str(rv / 'BLIND_REVIEW_A.jsonl'),
           str(rv / 'AFTER_REVEAL_A.jsonl') if (rv / 'AFTER_REVEAL_A.jsonl').exists() else '-',
           str(SCR / 'keys' / f'{batch}.json'), pub, ADJ, *judg, '--receipt', *receipts]
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.strip(), r.stderr.strip()[-600:])
    if r.returncode:
        return r.returncode
    mpath = out / 'COMPLETION.json'
    m = json.loads(mpath.read_text(encoding='utf-8'))
    ctrl = {k['instrument_id'] for k in key['controls']}
    demoted = []
    for i, mem in enumerate(m['members']):
        if mem['outcome'] != 'submit':
            continue
        rec = (after['B'] if mem['instrument_id'] in ctrl else blind['B']).get(mem['claim_sha256'])
        need = 'upheld_after_reveal' if mem['instrument_id'] in ctrl else 'upheld'
        if not rec or rec.get('verdict') != need:
            why = json.dumps(rec.get('defects'), ensure_ascii=False) if rec else 'no arm B record for this exact version'
            m['members'][i] = {'instrument_id': mem['instrument_id'], 'outcome': 'blocked',
                               'reason': 'Second independent blind reviewer (arm B) did not uphold this exact version: ' + why}
            demoted.append(mem['instrument_id'])
    if os.environ.get('REPLACEMENT'):
        m['publication'] = {'mode': 'replacement_proposal', 'path': pub}
    elif [x for x in m['members'] if x['outcome'] == 'submit']:  # nothing to file: the placeholder is never written
        ids = [x['instrument_id'] for x in m['members'] if x['outcome'] == 'submit']
        name = subprocess.run(['python3', '-X', 'utf8', 'jobs/claim-kit/kit.py', 'publication-name', '--agent', agent,
                               '--date', DATE, '--wave', WAVE, '--batch', batch,
                               *[a for iid in ids for a in ('--order', iid)]],
                              cwd=REPO, capture_output=True, text=True, encoding='utf-8')
        if name.returncode:
            print(json.dumps({'batch': batch, 'publication_name_refused': name.stderr.strip()[-600:],
                              'action': 'STOP: not completed'}))
            return name.returncode
        chosen = json.loads(name.stdout)
        if chosen['other_owner_members']:
            print(json.dumps({'batch': batch, 'other_owner_members_need_REPLACEMENT_run': chosen['other_owner_members']}))
        pub = chosen['path']
        m['publication'] = {'mode': 'own_claims', 'path': pub}
    mpath.write_text(json.dumps(m, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'batch': batch, 'agent': agent, 'publication': pub,
                      'submit_after_pair_rule': sum(x['outcome'] == 'submit' for x in m['members']),
                      'demoted_by_arm_B': demoted}))
    n = 1
    while (packet / f'complete-v{n}').exists():
        n += 1
    ccmd = ['python3', '-X', 'utf8', 'jobs/claim-kit/kit.py', 'complete', str(mpath), '--write',
            str(packet / f'complete-v{n}')] + (['--publish'] if '--publish' in flags else [])
    p = subprocess.run(ccmd, cwd=REPO, capture_output=True, text=True, encoding='utf-8')
    (packet / f'COMPLETE_v{n}.log').write_text(p.stdout + '\n' + p.stderr, encoding='utf-8')
    print(p.stdout[-1500:], p.stderr[-800:], 'exit', p.returncode)
    return p.returncode


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
