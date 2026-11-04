#!/usr/bin/env python3
"""Turn a review set of lifecycle claims into blind_verify cards and mechanical receipts.

stdlib only. Reads ONLY: the review-set JSONL given on the command line and the
source files those claims cite (through blind_verify, under the allowed roots).
Never opens control keys, GENUINE_CONTROLS files, other batches or registries.

Usage:
  python3 cards_from_review_set.py --review-set REVIEW_SET.jsonl \
      --repo-root /home/claude/executive-orders --out-dir OUT_DIR \
      [--verifier /tmp/claude-0/bv/repo/jobs/claim-kit/blind_verify.py] \
      [--allow-source-root jobs --allow-source-root research]

Per claim it writes OUT_DIR/cards/<id>.card.json (the claim unchanged, plus a
raw_path copied from the source's own cache_path/raw custody field when the
claim declares one and the file exists), runs blind_verify with the card's file
hash pinned, and writes OUT_DIR/<id>.MECHANICAL.json and OUT_DIR/SUMMARY.json.
<id> is instrument_id with ':' replaced by '_'.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

# Source-record fields that name a held raw file. The native blind_verify keys are
# left alone; the aliases are copied into raw_path only when the claim itself
# declares them and the file exists.
NATIVE_RAW = ('local_path', 'local_file', 'download_path', 'raw_path')
ALIAS_RAW = ('cache_path', 'raw_cache_path', 'pdf_path')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fill_raw(node, root, stats):
    """Walk the claim; for source-like dicts (have text_path) add raw_path from an alias."""
    if isinstance(node, dict):
        if 'text_path' in node:
            stats['source_refs'] += 1
            if not any(node.get(k) for k in NATIVE_RAW):
                for k in ALIAS_RAW:
                    v = node.get(k)
                    if isinstance(v, str) and v and (root / v).is_file():
                        node['raw_path'] = v
                        stats['raw_from_alias'] += 1
                        break
        for v in node.values():
            fill_raw(v, root, stats)
    elif isinstance(node, list):
        for v in node:
            fill_raw(v, root, stats)


def classify(code, report):
    """Mechanical classification from the verifier report only."""
    if code == 0:
        return 'pass'
    if not report:
        return 'refuse'
    errs = set(report.get('errors', []))
    for i in report.get('inputs', []):
        errs.update(i.get('errors', []))
    cards = report.get('cards', [])
    for c in cards:
        errs.update(c.get('errors', []))
    srcs = [s for c in cards for s in c.get('sources', [])]
    if errs or not srcs:
        return 'refuse'
    # unresolved custody: every source has its text verified and its only complaint
    # is missing raw custody.
    for s in srcs:
        if not (s['text_verified'] and set(s['errors']) <= {'raw_path_missing'}):
            return 'refuse'
    return 'unresolved_custody'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--review-set', required=True, type=Path)
    ap.add_argument('--repo-root', required=True, type=Path)
    ap.add_argument('--out-dir', required=True, type=Path)
    ap.add_argument('--verifier', type=Path, default=Path('/tmp/claude-0/bv/repo/jobs/claim-kit/blind_verify.py'))
    ap.add_argument('--allow-source-root', action='append', default=None)
    a = ap.parse_args(argv)
    allow = a.allow_source_root or ['jobs', 'research']
    root = a.repo_root.resolve(strict=True)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / 'cards').mkdir(exist_ok=True)
    t_all = time.time()
    claims = [json.loads(l) for l in a.review_set.read_text(encoding='utf-8').splitlines() if l.strip()]
    summary = {'schema': 'eo-blind-verify-adapter-summary/v1', 'review_set_sha256': sha(a.review_set.read_bytes()),
               'repo_root': str(root), 'allow_source_roots': allow, 'claims': 0,
               'counts': {'pass': 0, 'refuse': 0, 'unresolved_custody': 0}, 'by_claim': {},
               'source_refs': 0, 'raw_from_alias': 0}
    for claim in claims:
        iid = claim['instrument_id']
        fid = iid.replace(':', '_')
        stats = {'source_refs': 0, 'raw_from_alias': 0}
        fill_raw(claim, root, stats)
        card = a.out_dir / 'cards' / (fid + '.card.json')
        card_bytes = (json.dumps(claim, sort_keys=True, ensure_ascii=False, indent=1) + '\n').encode('utf-8')
        card.write_bytes(card_bytes)
        cmd = [sys.executable, '-I', str(a.verifier), '--card', str(card),
               '--expected-card-sha256', sha(card_bytes), '--source-root', str(root)]
        for r in allow:
            cmd += ['--allow-source-root', r]
        t0 = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True)
        dt = time.time() - t0
        try:
            report = json.loads(p.stdout)
        except ValueError:
            report = None
        status = classify(p.returncode, report)
        receipt = {'schema': 'eo-blind-verify-mechanical-receipt/v1', 'scope': 'mechanical_bytes_only',
                   'instrument_id': iid, 'card_file_sha256': sha(card_bytes),
                   'verifier_command': ['blind_verify.py' if c == str(a.verifier) else c for c in cmd[2:]],
                   'exit_status': p.returncode, 'classification': status,
                   'verifier_report': report, 'verifier_stderr': p.stderr[-2000:] if report is None else '',
                   'raw_paths_added_from_claim_aliases': stats['raw_from_alias']}
        (a.out_dir / (fid + '.MECHANICAL.json')).write_text(
            json.dumps(receipt, sort_keys=True, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        summary['claims'] += 1
        summary['counts'][status] += 1
        summary['source_refs'] += stats['source_refs']
        summary['raw_from_alias'] += stats['raw_from_alias']
        errs = {}
        for c in (report or {}).get('cards', []):
            for s in c.get('sources', []):
                for e in s['errors'] + s['unresolved']:
                    errs[e] = errs.get(e, 0) + 1
        summary['by_claim'][iid] = {'classification': status, 'exit_status': p.returncode,
                                    'seconds': round(dt, 3), 'error_counts': errs}
    summary['wall_seconds'] = round(time.time() - t_all, 3)
    (a.out_dir / 'SUMMARY.json').write_text(json.dumps(summary, sort_keys=True, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('claims', 'counts', 'wall_seconds')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
