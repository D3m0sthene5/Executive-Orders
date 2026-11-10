"""Papinian undecided probe: blind lifecycle review set and finish for the u01b overlay proposals (coordinator tool;
rules fixed in advance, no legal judgment). Adapted from Haloander's finish_overlay.py and reviewer_ux.txt.

usage: python -I overlay_review.py prep BATCH DIR [DIR ...]        -> plants controls, writes review sets and prompts (outside the repo)
       python -I overlay_review.py finish BATCH DIR [DIR ...] [--publish]
  BATCH names the review batch (u01b; u23 = u02 and u03 reviewed together); DIRs are batch folders whose
  overlay/EO_*/proposal-v1 bundles are reviewed; reviews, completion and the proposal go under the first DIR's folder.
  prep: claims = every u01b/overlay/EO_*/proposal-v1/CLAIMS.working.jsonl; max(1, round(n/15)) controls (seeded), every
        first_end / whole_order_end date moved back three years.
  finish: a control is caught only if BOTH arms rejected its exact planted hash and named a date defect; any miss stops.
        A member files only if BOTH arms upheld its exact claim hash (upheld_after_reveal for the genuine control).
        Every member is published as an isolated replacement proposal (owner acceptance false; kit COMPLETION.md)."""
import copy, hashlib, json, random, subprocess, sys
from pathlib import Path

REPO = Path('C:/Users/danie/eo-wt/papinian'); SCR = Path('C:/Users/danie/AppData/Local/Temp/papinian')
RUN = REPO / 'research/excavator/claude-papinian-2026-11-10'
B, DIRS = 'u01b', ['u01b']
T = Path(__file__).resolve().parent / 'prompts'
ADJ = 'claude-coordinator-papinian-2026-11-10'
WORDS = ('date', 'first_end', 'whole_order_end', 'year')


def canon(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p): return Path(p).resolve().relative_to(REPO).as_posix()
def jl(p): return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()] if Path(p).exists() else []
def shift(d):
    if not isinstance(d, str) or len(d) < 10 or not d[:4].isdigit(): return d
    md = d[4:10]; md = '-02-28' if md == '-02-29' else md
    return f"{int(d[:4]) - 3:04d}{md}{d[10:]}"


def bundles(): return sorted([b for d in DIRS for b in (RUN / d).glob('overlay/EO_*/proposal-v1') if (b / 'CLAIMS.working.jsonl').exists()], key=lambda b: int(b.parent.name[3:]))


def prep():
    claims = [jl(b / 'CLAIMS.working.jsonl')[0] for b in bundles()]
    elig = [c for c in claims if isinstance(c.get('whole_order_end'), dict) and c['whole_order_end'].get('date')]
    n = max(1, round(len(claims) / 15))
    rng = random.Random(hashlib.sha256(('papinian-controls:' + B).encode()).hexdigest())
    picks = {c['instrument_id'] for c in rng.sample(sorted(elig, key=lambda c: c['instrument_id']), n)}
    out, genuine, key = [], [], {'batch': B, 'controls': []}
    for c in claims:
        if c['instrument_id'] in picks:
            p = copy.deepcopy(c); k = 0
            if isinstance(p.get('whole_order_end'), dict) and p['whole_order_end'].get('date'): p['whole_order_end']['date'] = shift(p['whole_order_end']['date']); k += 1
            for x in p.get('operative_clauses', []):
                if isinstance(x.get('first_end'), dict) and x['first_end'].get('date'): x['first_end']['date'] = shift(x['first_end']['date']); k += 1
            assert k
            out.append(p); genuine.append(c)
            key['controls'].append({'instrument_id': c['instrument_id'], 'planted': canon(p), 'genuine': canon(c),
                                    'defect': 'every first_end and whole_order_end date moved back three years'})
        else:
            out.append(c)
    rd = SCR / 'review' / B; rd.mkdir(parents=True, exist_ok=True)
    w = lambda path, rows: path.write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in rows), encoding='utf-8')
    w(rd / 'GENUINE_CONTROLS.jsonl', genuine)
    (SCR / 'keys' / f'{B}.json').write_text(json.dumps(key, indent=1), encoding='utf-8')
    (RUN / DIRS[0] / 'reviews').mkdir(exist_ok=True)
    U = RUN / DIRS[0]
    ovs = ' or '.join((RUN / d).relative_to(REPO).as_posix() + '/overlay' for d in DIRS)
    for arm in 'AB':
        rows = list(out); random.Random(f'papinian-{B}-{arm}').shuffle(rows)
        sp = rd / f'REVIEW_SET_{arm}.jsonl'; w(sp, rows)
        t = (T / 'reviewer_overlay.txt').read_text(encoding='utf-8')
        t = t.replace('SETPATH', sp.as_posix()).replace('OVERLAYDIR/EO_N', '(' + ovs + ')/EO_N').replace('OUTDIR', U.relative_to(REPO).as_posix() + '/reviews')
        t = t.replace('REVSCRATCH', f'C:/Users/danie/AppData/Local/Temp/papinian/rev/{B}-{arm}/').replace('BATCHNAME', B).replace('ARM', arm)
        (SCR / 'prompts' / f'reviewer-{B}-{arm}.txt').write_text(t, encoding='utf-8')
        ids = ', '.join(k['instrument_id'] for k in key['controls'])
        (SCR / 'prompts' / f'reveal-{B}-{arm}.txt').write_text(
            f"After-reveal step for batch {B}, arm {arm}. The claim(s) for {ids} in your review set were planted controls (every first_end and whole_order_end date moved back three years). "
            f"The genuine version(s) are in {(rd / 'GENUINE_CONTROLS.jsonl').as_posix()} (one JSON claim per line). Review each genuine version on its merits with the same blinding and the same standard as your blind review (do not uphold it just because it is the genuine one). "
            f"Write one JSON object per genuine claim to {U.relative_to(REPO).as_posix()}/reviews/AFTER_REVEAL_{arm}.jsonl, in the same format as your BLIND_REVIEW_{arm}.jsonl records, with claim_sha256 computed the same way over the genuine claim, the same reviewer name, verdict \"upheld_after_reveal\" if it is right or \"rejected\" with defects if not, and started_utc/ended_utc. Do not change BLIND_REVIEW_{arm}.jsonl. Reply in at most 60 words.", encoding='utf-8')
    print(json.dumps({'claims': len(claims), 'controls': sorted(picks)}))


def lineref(p, sha):
    for i, l in enumerate(open(p, encoding='utf-8'), 1):
        if l.strip() and json.loads(l).get('claim_sha256') == sha:
            return {'path': rel(p), 'sha256': fsha(p), 'line': i}
    return None


def dated(r):
    t = json.dumps([r.get('defects', []), r.get('reasons', ''), r.get('reason', '')], ensure_ascii=False).lower()
    return any(x in t for x in WORDS)


def finish(*flags):
    U = RUN / DIRS[0]; PUB = U.relative_to(REPO).as_posix() + '/overlay/REPLACEMENT_PROPOSAL.jsonl'
    rv = U / 'reviews'; key = json.loads((SCR / 'keys' / f'{B}.json').read_text(encoding='utf-8'))
    blindf = {a: rv / f'BLIND_REVIEW_{a}.jsonl' for a in 'AB'}; afterf = {a: rv / f'AFTER_REVEAL_{a}.jsonl' for a in 'AB'}
    blind = {a: {r['claim_sha256']: r for r in jl(blindf[a])} for a in 'AB'}
    after = {a: {r['claim_sha256']: r for r in jl(afterf[a])} for a in 'AB'}
    cdir = U / 'completion'; cdir.mkdir(exist_ok=True)
    controls, missed = [], []; ctl = {k['instrument_id'] for k in key['controls']}
    for k in key['controls']:
        iid = k['instrument_id']
        res = {a: bool(blind[a].get(k['planted']) and blind[a][k['planted']].get('verdict') == 'rejected' and dated(blind[a][k['planted']])) for a in 'AB'}
        if not all(res.values()): missed.append(iid)
        seed = {'schema': 'eo-claim-kit-control-seed/v1', 'instrument_id': iid, 'planted_claim_sha256': k['planted'], 'genuine_claim_sha256': k['genuine'], 'seeded_by': ADJ}
        sp = cdir / ('SEED_RECEIPT_' + iid.replace(':', '_') + '.json'); sp.write_text(json.dumps(seed, indent=1) + '\n', encoding='utf-8')
        ref = lineref(blindf['A'], k['planted'])
        adj = {'instrument_id': iid, 'planted_claim_sha256': k['planted'], 'review': ref, 'adjudicator': ADJ, 'caught': all(res.values()), 'scoring': 'strict',
               'rationale': f"Planted version: {k['defect']}. Per-arm results {res} (caught = rejected the exact planted hash and named the date defect). Rule fixed in advance: caught only if both arms caught it."}
        ap = cdir / ('CONTROL_ADJUDICATION_' + iid.replace(':', '_') + '.json'); ap.write_text(json.dumps(adj, indent=1) + '\n', encoding='utf-8')
        controls.append({'instrument_id': iid, 'planted_claim_sha256': k['planted'], 'seed': {'path': rel(sp), 'sha256': fsha(sp)}, 'review': ref,
                         'adjudication': {'path': rel(ap), 'sha256': fsha(ap)}})
    if missed:
        print(json.dumps({'missed_controls': missed, 'action': 'STOP: not completed'})); return 2
    members, agents = [], set()
    for b in bundles():
        cpath = b / 'CLAIMS.working.jsonl'; c = jl(cpath)[0]; iid, sha = c['instrument_id'], canon(c)
        agents.add((c.get('claim_kit') or {}).get('agent'))
        src, want = (after, 'upheld_after_reveal') if iid in ctl else (blind, 'upheld')
        bad = {a: (src[a][sha].get('defects') if sha in src[a] else 'no record for this exact version') for a in 'AB' if src[a].get(sha, {}).get('verdict') != want}
        if bad:
            members.append({'instrument_id': iid, 'outcome': 'blocked', 'reason': ('Not upheld by both independent arms: ' + json.dumps(bad, ensure_ascii=False))[:3000]}); continue
        m = {'instrument_id': iid, 'outcome': 'submit', 'claim_sha256': sha, 'claim': {'path': rel(cpath), 'sha256': fsha(cpath), 'line': 1}, 'publication_kind': 'whole_case',
             'overlay_bundle': {k: {'path': rel(b / n), 'sha256': fsha(b / n)} for k, n in (('evidence', 'EVIDENCE.json'), ('decision', 'STATUS_DECISION.json'), ('review', 'STATUS_REVIEW.json'), ('proposal', 'PROMOTION_PROPOSAL.json'))}}
        m['after_reveal_review' if iid in ctl else 'review'] = lineref((afterf if iid in ctl else blindf)['A'], sha)
        members.append(m)
    assert len(agents) == 1, agents
    receipts = [{'path': rel(f), 'sha256': fsha(f)} for a in 'AB' for f in (blindf[a], afterf[a]) if f.exists()]
    manifest = {'schema': 'eo-claim-kit-completion/v1', 'agent': agents.pop(), 'producer_model_family': 'Anthropic', 'independence_requirement': 'same_family_separate_context',
                'publication': {'mode': 'replacement_proposal', 'path': PUB}, 'members': members, 'controls': controls, 'receipts': receipts}
    (cdir / 'COMPLETION.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'members': len(members), 'submit': sum(m['outcome'] == 'submit' for m in members)}))
    n = 1
    while (cdir / f'complete-v{n}').exists(): n += 1
    p = subprocess.run(['python', '-X', 'utf8', 'jobs/claim-kit/kit.py', 'complete', str(cdir / 'COMPLETION.json'), '--write', str(cdir / f'complete-v{n}')] + (['--publish'] if '--publish' in flags else []),
                       cwd=REPO, capture_output=True, text=True, encoding='utf-8')
    (cdir / f'COMPLETE_v{n}.log').write_text(p.stdout + '\n' + p.stderr, encoding='utf-8')
    print(p.stdout[-1500:], p.stderr[-800:], 'exit', p.returncode)
    return p.returncode


if __name__ == '__main__':
    cmd, B = sys.argv[1], sys.argv[2]
    DIRS = [a for a in sys.argv[3:] if not a.startswith('--')]
    sys.exit(prep() if cmd == 'prep' else finish(*[a for a in sys.argv[3:] if a.startswith('--')]))
