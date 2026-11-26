"""Tiro finish: score the planted controls, apply the two-arm pair rule, build the completion manifest and run
kit.py complete (coordinator bookkeeping; the scoring rule is fixed in advance and makes no legal judgment).

Order of work, as finish_pair.py did it:
1. adjudicate_controls(): a planted control is CAUGHT only if BOTH arms rejected its exact planted hash and named
   the planted defect (plants.names_defect). Any miss stops the batch before completion.
2. make_completion.py builds COMPLETION.json from arm A's records (it already blocks a member arm A did not uphold).
3. pair_rule(): a submitted member files only if arm B also upheld the exact same claim hash; otherwise it becomes
   a blocked member quoting arm B's defects.
4. Publication: replacement mode writes WAVEDIR/BATCH/REPLACEMENT_PROPOSAL.jsonl; own claims take the name the
   claim kit chooses (kit.py publication-name), never one chosen by hand.
5. kit.py complete into a new complete-vN (--publish only when asked); its output goes to COMPLETE_vN.log.
"""
import json
from pathlib import Path

import plants
import tiro_common as C
from tiro_common import TiroError, load_jsonl

ARMS = 'AB'
SECOND_ARM = 'B'


def read_reviews(packet):
    rv = Path(packet) / 'reviews'
    blind = {a: {r['claim_sha256']: r for r in load_jsonl(rv / f'BLIND_REVIEW_{a}.jsonl')} for a in ARMS}
    after = {a: {r['claim_sha256']: r for r in load_jsonl(rv / f'AFTER_REVEAL_{a}.jsonl')} for a in ARMS}
    return blind, after


def adjudicate_controls(key, blind):
    """(judgment arguments for make_completion, missed instrument ids, seed receipts)."""
    judg, missed, seeds = [], [], []
    for k in key['controls']:
        iid = k['instrument_id']
        seeds.append({'schema': 'eo-claim-kit-control-seed/v1', 'instrument_id': iid, 'planted_claim_sha256': k['planted'],
                      'genuine_claim_sha256': k['genuine']})
        ok = {a: plants.names_defect(blind[a].get(k['planted']), k) for a in ARMS}
        if all(ok.values()):
            why = (f"Planted version: {k['defect']}; both independent blind arms (A and B) rejected that exact planted "
                   "hash and named the date defect." if plants.kind_of(k) == 'date_shift' else
                   f"Planted version: {k['defect']}; both independent blind arms (A and B) rejected that exact planted "
                   "hash and named the planted defect.")
        else:
            why = (f"Planted version: {k['defect']}; arm(s) {','.join(a for a in ARMS if not ok[a])} did not reject it "
                   f"for the {'date' if plants.kind_of(k) == 'date_shift' else 'planted'} defect.")
        judg.append(f"{iid}={'caught' if all(ok.values()) else 'missed'}|{why}")
        if not all(ok.values()):
            missed.append(iid)
    return judg, missed, seeds


def pair_rule(members, key, blind, after, arm=SECOND_ARM):
    """THE PAIR RULE (both arms must uphold). Arm A's verdicts are already applied by make_completion; this applies
    the second arm. A submitted member stays 'submit' only if `arm` upheld the exact same claim_sha256: verdict
    'upheld' in its blind review, or, for a genuine control, 'upheld_after_reveal' in its after-reveal review.
    Every other submitted member becomes blocked with that arm's defects as the reason.

    Returns (new member list, demoted instrument ids). Later routes (for example a fix-and-recheck pass) should
    extend this function, not add a second rule elsewhere."""
    ctrl = {k['instrument_id'] for k in key['controls']}
    out, demoted = [], []
    for mem in members:
        if mem.get('outcome') != 'submit':
            out.append(mem)
            continue
        is_ctrl = mem['instrument_id'] in ctrl
        rec = (after[arm] if is_ctrl else blind[arm]).get(mem['claim_sha256'])
        need = 'upheld_after_reveal' if is_ctrl else 'upheld'
        if rec and rec.get('verdict') == need:
            out.append(mem)
            continue
        why = json.dumps(rec.get('defects'), ensure_ascii=False) if rec else f'no arm {arm} record for this exact version'
        out.append({'instrument_id': mem['instrument_id'], 'outcome': 'blocked',
                    'reason': f'Second independent blind reviewer (arm {arm}) did not uphold this exact version: ' + why})
        demoted.append(mem['instrument_id'])
    return out, demoted


def finish(wave, batch, packet, publish=False, replacement=False, emit=print):
    """Returns the exit code (0 done; 2 a control missed or a refusal; otherwise the failing tool's code)."""
    packet = Path(packet)
    afr = packet / 'APPLIED_FOR_REVIEW'
    if not afr.exists():
        raise TiroError(f'no {wave.relpath(packet)}/APPLIED_FOR_REVIEW: run review-prep (or reuse-reviews) first')
    applied = packet / afr.read_text(encoding='utf-8').strip()
    keyf = wave.key_path(batch)
    if not keyf.exists():
        raise TiroError(f'no key {keyf}')
    key = json.loads(keyf.read_text(encoding='utf-8'))
    agent = C.packet_meta(packet)['agent']
    if not agent:
        raise TiroError(f'cannot read the packet agent from {wave.relpath(packet)} (PACKET.json or ADMISSION.json)')
    rv = packet / 'reviews'
    blind, after = read_reviews(packet)
    out = packet / 'completion'
    out.mkdir(exist_ok=True)
    judg, missed, seeds = adjudicate_controls(key, blind)
    for s in seeds:
        s['seeded_by'] = wave.adjudicator
        (out / ('SEED_RECEIPT_' + s['instrument_id'].replace(':', '_') + '.json')).write_text(
            json.dumps(s, indent=1) + '\n', encoding='utf-8')
    if missed:
        emit(json.dumps({'batch': batch, 'missed_controls': missed, 'action': 'STOP: not completed'}))
        return 2
    if replacement:
        pub = f'{wave.rel}/{batch}/REPLACEMENT_PROPOSAL.jsonl'
    else:
        pub = f'research/readiness/claims/{agent}-{wave.date}-{wave.short}-{batch}.jsonl'  # placeholder; chosen below
    receipts = [str(rv / f) for f in (f'BLIND_REVIEW_{SECOND_ARM}.jsonl', f'AFTER_REVEAL_{SECOND_ARM}.jsonl') if (rv / f).exists()]
    for extra in ('CARRY.json', 'PRODUCER_REPORT.md', 'ASSESSMENT.jsonl'):
        if (packet / extra).exists():
            receipts.append(str(packet / extra))
    cmd = C.py(C.MAKE_COMPLETION, packet, applied, rv / 'BLIND_REVIEW_A.jsonl',
               rv / 'AFTER_REVEAL_A.jsonl' if (rv / 'AFTER_REVEAL_A.jsonl').exists() else '-',
               keyf, pub, wave.adjudicator, *judg, '--receipt', *receipts, isolated=True)
    r = C.run(cmd, wave.repo)
    emit((r.stdout.strip() + ' ' + r.stderr.strip()[-600:]).strip())
    if r.returncode:
        return r.returncode
    mpath = out / 'COMPLETION.json'
    m = json.loads(mpath.read_text(encoding='utf-8'))
    m['members'], demoted = pair_rule(m['members'], key, blind, after)
    submit = [x['instrument_id'] for x in m['members'] if x['outcome'] == 'submit']
    if replacement:
        m['publication'] = {'mode': 'replacement_proposal', 'path': pub}
    elif submit:  # nothing to file: the placeholder is never written
        name = C.run(C.kit('publication-name', '--agent', agent, '--date', wave.date, '--wave', wave.short,
                           '--batch', batch, *[a for iid in submit for a in ('--order', iid)]), wave.repo)
        if name.returncode:
            emit(json.dumps({'batch': batch, 'publication_name_refused': name.stderr.strip()[-600:],
                             'action': 'STOP: not completed'}))
            return name.returncode
        chosen = json.loads(name.stdout)
        if chosen.get('other_owner_members'):
            emit(json.dumps({'batch': batch, 'other_owner_members_need_REPLACEMENT_run': chosen['other_owner_members']}))
        pub = chosen['path']
        m['publication'] = {'mode': 'own_claims', 'path': pub}
    mpath.write_text(json.dumps(m, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    emit(json.dumps({'batch': batch, 'agent': agent, 'publication': pub, 'submit_after_pair_rule': len(submit),
                     'demoted_by_arm_B': demoted}))
    target = C.next_version(packet, 'complete-v')
    n = target.name.rsplit('v', 1)[1]
    p = C.run(C.kit('complete', mpath, '--write', target) + (['--publish'] if publish else []), wave.repo)
    (packet / f'COMPLETE_v{n}.log').write_text(p.stdout + '\n' + p.stderr, encoding='utf-8')
    emit(f"{p.stdout[-1500:]} {p.stderr[-800:]} exit {p.returncode}")
    return p.returncode
