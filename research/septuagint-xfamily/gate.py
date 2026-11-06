"""Gate for the Septuagint cross-family replay.

For each batch, every claim in the rebuilt review set must have canonical SHA-256
(json.dumps(claim, sort_keys=True, separators=(",", ":"), ensure_ascii=False)) equal to a claim_sha256 that the
original Claude arms recorded in BLIND_REVIEW_<arm>.jsonl, and the sets must be equal (same count, no extras).
It also compares each rebuilt per-arm shuffle with the order of the arm's committed file (informational) and the
rebuilt packet's SHA-256 with the packet_sha256 in the committed DISPATCH_CHECK.json.

usage: py -I gate.py E_DIR REBUILT_ROOT MAIN_REPO OUT_GATE_JSON
  E_DIR       review_prep output folder (E/review/<batch>/REVIEW_SET*.jsonl)
  REBUILT_ROOT the private folder holding the rebuilt packets (rebuilt/dorotheus-yesprobe-2026-11-06/<batch>/packet)
  MAIN_REPO   any clone that has origin/main (the committed originals are read with git show)
"""
import hashlib, json, subprocess, sys
from pathlib import Path

Y = 'research/excavator/dorotheus-yesprobe-2026-11-06'
BATCHES = {'y01': 'ABC', 'y02': 'ABC', 'y03': 'AB', 'y05': 'ABC'}


DROPPED = {
    'ux1': 'Gate not met. Three of its five producer claims (EO:5857, EO:5866, EO:10513) are not committed anywhere: the committed '
           'overlay-proposals file holds only the claims that were filed (EO:5700 and EO:7628 of this batch). The claims came from '
           'LLM-written status-overlay lifecycle sheets and reviews (STATUS_REVIEW.json, CLAIMS.working.jsonl) that stayed in the '
           'container scratch, so their canonical hashes cannot be reproduced and the overlay bundles (DOSSIER.json) cannot be rebuilt exactly.',
    'ux2': 'Gate not met. EO:10901, EO:11218 and EO:13348 reproduce from the committed overlay-proposals file, and the EO:10994 plant '
           'reproduces from the filed EO:10994 claim (hash 1a6f68d0), but the reviewed version of EO:13362 (claim_sha256 df747264...) '
           'was replaced by a corrected version before filing (the committed file holds 242bebb5...); the reviewed version is not '
           'committed. The overlay bundles (STATUS_REVIEW.json, DOSSIER.json) are also not committed. Not approximated.',
}


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def show(repo, path):
    r = subprocess.run(['git', '-C', str(repo), 'show', 'origin/main:' + path], capture_output=True)
    return r.stdout.decode('utf-8') if r.returncode == 0 else None


def jl(text):
    return [json.loads(l) for l in text.splitlines() if l.strip()]


def main(e_dir, src, repo, out):
    e_dir, src = Path(e_dir), Path(src)
    gate = {'schema': 'septuagint-gate/v1', 'source_commit': 'a8dd983983', 'batches': {}, 'dropped': DROPPED}
    for b, arms in BATCHES.items():
        rec = {'arms': {}, 'passed': False}
        dc = json.loads(show(repo, f'{Y}/{b}/packet/DISPATCH_CHECK.json'))
        mine = json.loads((src / Y.split('/')[-1] / b / 'packet/DISPATCH_CHECK.json').read_text(encoding='utf-8'))
        rec['packet_sha256_original'] = dc['packet_sha256']
        rec['packet_sha256_rebuilt'] = mine['packet_sha256']
        rec['packet_fingerprint_match'] = dc['packet_fingerprint'] == mine['packet_fingerprint']
        rec['packet_sha256_match'] = dc['packet_sha256'] == mine['packet_sha256']
        base = [json.loads(l) for l in (e_dir / 'review' / b / 'REVIEW_SET.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        rebuilt = {canon(c): c['instrument_id'] for c in base}
        rec['rebuilt_claims'] = {h: i for h, i in sorted(rebuilt.items(), key=lambda kv: kv[1])}
        ok = rec['packet_sha256_match']
        for a in arms:
            orig = jl(show(repo, f'{Y}/{b}/packet/reviews/BLIND_REVIEW_{a}.jsonl'))
            orig_h = [r['claim_sha256'] for r in orig]
            arm_rows = [json.loads(l) for l in (e_dir / 'review' / b / f'REVIEW_SET_{a}.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
            arm_h = [canon(c) for c in arm_rows]
            matched = len(set(arm_h) & set(orig_h))
            rec['arms'][a] = {'original_count': len(orig_h), 'rebuilt_count': len(arm_h), 'hash_matches': matched,
                              'sets_equal': set(arm_h) == set(orig_h) and len(arm_h) == len(orig_h),
                              'shuffle_order_equals_review_file_order': arm_h == orig_h}
            ok &= rec['arms'][a]['sets_equal']
        rec['passed'] = bool(ok)
        gate['batches'][b] = rec
    Path(out).write_text(json.dumps(gate, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    for b, r in gate['batches'].items():
        print(b, 'PASS' if r['passed'] else 'FAIL', 'packet_sha', r['packet_sha256_match'],
              {a: (v['hash_matches'], v['original_count'], v['shuffle_order_equals_review_file_order']) for a, v in r['arms'].items()})


if __name__ == '__main__':
    main(*sys.argv[1:5])
