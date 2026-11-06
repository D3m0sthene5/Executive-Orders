"""Build ONE kit.py completion manifest for several reviewed Dorotheus batches and run kit.py complete
(coordinator tool; scoring rules fixed in advance, no legal judgment).

usage: python3 -I complete_wave.py NAME OUTDIR PUBLICATION_PATH MODE BATCH[:APPLIED] [...] [--publish]
  MODE own_claims (decided packets, CLAIMS from PACKET/APPLIED/CLAIMS.proposed.jsonl, one member per decisions.csv
  row) or replacement_proposal (undecided overlay batches ux1/ux2: one member per overlay bundle claim).
Rules (same as finish.py):
  * arms = every reviews/BLIND_REVIEW_<arm>.jsonl of the batch. An arm catches a date-shift control if it rejects
    the exact planted hash and names a date defect; it catches a Mountweazel plant if it rejects that hash.
  * Corrected versions: CORRECTION_REVIEW_<arm>.jsonl records count as that arm's review of the new hash;
    an overlay bundle's CLAIMS.working-v2.jsonl, when present, is the selected version.
  * If any arm missed any plant and no arm C exists, the batch is reported need_arm_C and excluded.
  * Kit control adjudication: caught if every arm caught it, or arm C and at least one other arm caught it; the
    control review ref is an arm that caught it. A miss stays visible in the adjudication text and PLANTS.json.
  * A genuine claim files only if EVERY arm upheld it (blind "upheld"; control genuine versions
    "upheld_after_reveal" in every arm). Others become blocked members carrying each arm's defects.
PUBPACKET (env, optional): a fresh claim-kit packet prepared for exactly the members to be filed, whose dossiers
  equal the producing packets' dossiers. Completion output inside a producing packet changes every OTHER packet's
  prior-research context, so a multi-packet filing is completed inside one publication packet (OUTDIR under it).
Writes OUTDIR/COMPLETION.json, per-batch completion/ receipts and PLANTS.json, then
kit.py complete OUTDIR/COMPLETION.json --write OUTDIR/complete-vN [--publish].
"""
import csv, glob, hashlib, json, os, subprocess, sys
from pathlib import Path
E = Path('/tmp/claude-0/dorotheus-wave'); REPO = Path('/home/user/Executive-Orders')
SW = REPO / 'research/excavator/dorotheus-sample-2026-11-06'; YW = REPO / 'research/excavator/dorotheus-yesprobe-2026-11-06'
def jl(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()] if Path(p).exists() else []
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
def rel(p): return Path(p).resolve().relative_to(REPO).as_posix()
def lineref(p, sha):
    for i, l in enumerate(open(p, encoding='utf-8'), 1):
        if l.strip():
            r = json.loads(l)
            if (r.get('claim_sha256') or canon(r)) == sha: return {'path': rel(p), 'sha256': fsha(p), 'line': i}, r
    return None, None
def dated(r): return any(w in json.dumps(r.get('defects', []), ensure_ascii=False).lower() for w in ('date', 'first_end', 'whole_order_end', 'year', 'effective', 'signing'))
def batch_dir(b): return (YW / b / 'packet') if b.startswith('y') else (SW / b if b.startswith('ux') else SW / b / 'packet')
def main(name, outdir, pub, mode, *specs):
    publish = '--publish' in specs; specs = [s for s in specs if s != '--publish']
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    members, controls, receipts, plants, report = [], [], [], [], {}
    for spec in specs:
        b, _, applied = spec.partition(':'); P = batch_dir(b); rv = P / 'reviews'
        if not (E / 'keys' / f'{b}.json').exists():  # no submission, so no review: blocked rows only
            for row in csv.DictReader(open(P / 'decisions.csv', encoding='utf-8-sig')):
                members.append({'instrument_id': row['instrument_id'], 'outcome': 'blocked', 'reason': (row.get('unresolved_material_gaps') or row['outcome'])[:3000]})
            report[b] = 'no_submissions'; continue
        key = json.loads((E / 'keys' / f'{b}.json').read_text())
        arms = sorted(Path(p).stem.rsplit('_', 1)[1] for p in glob.glob(str(rv / 'BLIND_REVIEW_*.jsonl')))
        blindf = {a: rv / f'BLIND_REVIEW_{a}.jsonl' for a in arms}; afterf = {a: rv / f'AFTER_REVEAL_{a}.jsonl' for a in arms}
        corrf = {a: rv / f'CORRECTION_REVIEW_{a}.jsonl' for a in arms}
        blind = {a: {r.get('claim_sha256'): r for r in jl(blindf[a]) + jl(corrf[a])} for a in arms}
        after = {a: {r.get('claim_sha256'): r for r in jl(afterf[a])} for a in arms}
        bp = []
        for k in key['controls']:
            for a in arms:
                r = blind[a].get(k['planted'])
                bp.append({'packet': b, 'plant_id': f"{b}:{k['instrument_id']}", 'defect_type': k['type'], 'arm': a, 'iid': k['instrument_id'],
                           'caught': 'yes' if r and r.get('verdict') == 'rejected' and dated(r) else 'no'})
        mw = key.get('mountweazel') or {}
        for it in mw.get('items', []):
            if it['is_seeded']:
                for a in arms:
                    r = blind[a].get(it['claim_sha256'])
                    bp.append({'packet': b, 'plant_id': f"{mw['batch_id']}:{it['item_id']}", 'defect_type': 'mountweazel_' + str(it['defect_code']),
                               'arm': a, 'caught': 'yes' if r and r.get('verdict') == 'rejected' else 'no'})
        plants += bp
        if any(p['caught'] == 'no' for p in bp) and 'C' not in arms:
            report[b] = 'need_arm_C'; continue
        cdir = P / 'completion'; cdir.mkdir(exist_ok=True)
        ok_all = True; bctl = []
        for k in key['controls']:
            res = {p['arm']: p['caught'] == 'yes' for p in bp if p.get('iid') == k['instrument_id']}
            ok = all(res.values()) or (res.get('C', False) and sum(res.values()) >= 2)
            ok_all &= ok
            arm = next((a for a in ['A', 'B', 'C'] if res.get(a)), arms[0])
            seed = {'schema': 'eo-claim-kit-control-seed/v1', 'instrument_id': k['instrument_id'], 'planted_claim_sha256': k['planted'],
                    'genuine_claim_sha256': k['genuine'], 'seeded_by': 'dorotheus-coordinator-2026-11-06'}
            sp = cdir / ('SEED_RECEIPT_' + k['instrument_id'].replace(':', '_') + '.json'); sp.write_text(json.dumps(seed, indent=1) + '\n')
            ref, _ = lineref(blindf[arm], k['planted'])
            adj = {'instrument_id': k['instrument_id'], 'planted_claim_sha256': k['planted'], 'review': ref,
                   'adjudicator': 'dorotheus-coordinator-2026-11-06', 'caught': bool(ok), 'scoring': 'strict',
                   'rationale': f"Planted version: {k['defect']}. Per-arm results {res} (caught = rejected the exact planted hash and named the date defect). Rule fixed in advance: caught if every arm caught it, or arm C and at least one other arm did; {'caught' if ok else 'not caught'}."}
            ap = cdir / ('CONTROL_ADJUDICATION_' + k['instrument_id'].replace(':', '_') + '.json'); ap.write_text(json.dumps(adj, indent=1) + '\n')
            bctl.append({'instrument_id': k['instrument_id'], 'planted_claim_sha256': k['planted'],
                             'seed': {'path': rel(sp), 'sha256': fsha(sp)}, 'review': ref, 'adjudication': {'path': rel(ap), 'sha256': fsha(ap)}})
        if not ok_all: report[b] = 'control_missed_batch_not_filed'
        else: controls.extend(bctl)
        for a in arms:
            for f in (blindf[a], afterf[a], corrf[a]):
                if f.exists(): receipts.append({'path': rel(f), 'sha256': fsha(f)})
        ctl = {k['instrument_id'] for k in key['controls']}
        def verdicts(iid, sha):
            src = after if iid in ctl else blind; want = 'upheld_after_reveal' if iid in ctl else 'upheld'
            return {a: src[a].get(sha) for a in arms}, want
        if mode == 'own_claims':
            cpath = P / applied / 'CLAIMS.proposed.jsonl'
            claims = {json.loads(l)['instrument_id']: (i, json.loads(l)) for i, l in enumerate(open(cpath, encoding='utf-8'), 1) if l.strip()}
            PP = Path(os.environ['PUBPACKET']) if os.environ.get('PUBPACKET') else P  # publication packet (see docstring)
            pk = {'path': rel(PP / 'PACKET.json'), 'sha256': fsha(PP / 'PACKET.json')}
            for row in csv.DictReader(open(P / 'decisions.csv', encoding='utf-8-sig')):
                iid = row['instrument_id']
                if row['outcome'] != 'submit' or iid not in claims:
                    members.append({'instrument_id': iid, 'outcome': 'blocked', 'reason': (row.get('unresolved_material_gaps') or row['outcome'])[:3000]}); continue
                line, c = claims[iid]; sha = canon(c); v, want = verdicts(iid, sha)
                bad = {a: (r.get('defects') if r else 'no record for this exact version') for a, r in v.items() if not r or r.get('verdict') != want}
                if bad or not ok_all:
                    members.append({'instrument_id': iid, 'outcome': 'blocked', 'reason': ('Not upheld by every reviewing arm: ' + json.dumps(bad, ensure_ascii=False))[:3000] if bad else 'batch control not caught'}); continue
                m = {'instrument_id': iid, 'outcome': 'submit', 'claim_sha256': sha, 'claim': {'path': rel(cpath), 'sha256': fsha(cpath), 'line': line},
                     'publication_kind': 'whole_case', 'packet': pk}
                m['after_reveal_review' if iid in ctl else 'review'] = lineref((afterf if iid in ctl else blindf)['A'], sha)[0]
                members.append(m)
        else:
            for iid in json.load(open(E / 'batches.json'))['review_batches'][b]:
                bundle = next(Path(p) for p in glob.glob(str(SW / 'u*/packet/overlay' / iid.replace(':', '_') / 'proposal-v1')))
                cpath = bundle / ('CLAIMS.working-v2.jsonl' if (bundle / 'CLAIMS.working-v2.jsonl').exists() else 'CLAIMS.working.jsonl'); c = jl(cpath)[0]; sha = canon(c); v, want = verdicts(iid, sha)
                bad = {a: (r.get('defects') if r else 'no record for this exact version') for a, r in v.items() if not r or r.get('verdict') != want}
                if bad or not ok_all:
                    members.append({'instrument_id': iid, 'outcome': 'blocked', 'reason': ('Not upheld by every reviewing arm: ' + json.dumps(bad, ensure_ascii=False))[:3000] if bad else 'batch control not caught'}); continue
                m = {'instrument_id': iid, 'outcome': 'submit', 'claim_sha256': sha, 'claim': {'path': rel(cpath), 'sha256': fsha(cpath), 'line': 1},
                     'publication_kind': 'whole_case',
                     'overlay_bundle': {k: {'path': rel(bundle / n), 'sha256': fsha(bundle / n)} for k, n in
                                        (('evidence', 'EVIDENCE.json'), ('decision', 'STATUS_DECISION.json'), ('review', 'STATUS_REVIEW.json'), ('proposal', 'PROMOTION_PROPOSAL.json'))}}
                m['after_reveal_review' if iid in ctl else 'review'] = (lineref((afterf if iid in ctl else blindf)['A'], sha)[0]
                                                                         or lineref(corrf['A'], sha)[0])
                members.append(m)
        (cdir / 'PLANTS.json').write_text(json.dumps([{k: v for k, v in p.items() if k != 'iid'} for p in bp], indent=1) + '\n')
        report.setdefault(b, 'included')
    # MECH_BLOCK (env, optional): JSON file {instrument_id: reason} for members that passed review but that an
    # earlier dry-run completion's actual checker refused; they are retained as blocked with that exact reason.
    if os.environ.get('MECH_BLOCK'):
        mb = json.load(open(os.environ['MECH_BLOCK']))
        members = [({'instrument_id': m['instrument_id'], 'outcome': 'blocked', 'reason': mb[m['instrument_id']]}
                    if m['instrument_id'] in mb and m['outcome'] == 'submit' else m) for m in members]
    manifest = {'schema': 'eo-claim-kit-completion/v1', 'agent': 'dorotheus', 'producer_model_family': 'Anthropic',
                'independence_requirement': 'same_family_separate_context', 'publication': {'mode': mode, 'path': pub},
                'members': members, 'controls': controls, 'receipts': receipts}
    (outdir / 'COMPLETION.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n')
    (outdir / 'BATCHES.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'name': name, 'batches': report, 'members': len(members), 'submit': sum(m['outcome'] == 'submit' for m in members), 'controls': len(controls)}))
    if not controls or not any(m['outcome'] == 'submit' for m in members): print('nothing to complete'); return 0
    n = 1
    while (outdir / f'complete-v{n}').exists(): n += 1
    p = subprocess.run(['python3', 'jobs/claim-kit/kit.py', 'complete', str(outdir / 'COMPLETION.json'), '--write', str(outdir / f'complete-v{n}')] + (['--publish'] if publish else []),
                       cwd=REPO, capture_output=True, text=True)
    (outdir / f'COMPLETE_v{n}.log').write_text(p.stdout + '\n' + p.stderr)
    print(p.stdout[-2500:], p.stderr[-800:], 'exit', p.returncode); return p.returncode
if __name__ == '__main__': sys.exit(main(*sys.argv[1:]))
