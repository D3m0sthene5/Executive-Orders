#!/usr/bin/env python3
"""Read-only explicit actual-input replay, writing only assigned report files.

Sources and old blind card are already retained externally by the operator;
this script neither fetches nor infers them. No control identities are known.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', required=True, type=Path)
    parser.add_argument('--historical-card', required=True, type=Path)
    args = parser.parse_args()
    clock = datetime.now(timezone.utc).isoformat()
    trials = [
        ('MAITLAND_MECHANICAL.json', 'research/progress/maitland/blind-review-input/RECORDS.json',
         '482e39ae55f461aaba4e63f9aa57c250a883ac360e30c0e7172170f1e032157c'),
        ('HISTORICAL_BLIND_MECHANICAL.json', str(args.historical_card),
         '6c6e8e2205986f67564eaa73bd263d9bce1f8593f7e13d5704394758303d8660')]
    receipts = []
    for destination, card, pin in trials:
        # The historical digest below is recorded from its fetched blinded blob;
        # an unexpected card is an exception, not a newly accepted input.
        command = [sys.executable, '-I', str(REPO / 'jobs/claim-kit/blind_verify.py'),
                   '--card', card, '--expected-card-sha256', pin,
                   '--source-root', str(args.sources), '--allow-source-root',
                   'jobs/fr-originals/data/full_run/texts']
        start = time.monotonic()
        run = subprocess.run(command, cwd=REPO, capture_output=True)
        seconds = time.monotonic() - start
        report = json.loads(run.stdout)
        target = HERE / destination
        target.write_bytes(run.stdout)
        sources = [s for c in report['cards'] for s in c['sources']]
        receipts.append({'destination': destination, 'exit_code': run.returncode,
                         'elapsed_seconds': seconds, 'stdout_sha256': hashlib.sha256(run.stdout).hexdigest(),
                         'stderr': run.stderr.decode('utf-8'), 'cards': len(report['cards']),
                         'source_occurrences': len(sources), 'text_verified': sum(s['text_verified'] for s in sources),
                         'raw_verified': sum(s['raw_verified'] for s in sources),
                         'errors': sum(len(s['errors']) for s in sources),
                         'unresolved_occurrences': sum(bool(s['unresolved']) for s in sources)})
    pins = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in
            ('jobs/claim-kit/blind_verify.py', 'jobs/claim-kit/test_blind_verify.py',
             'jobs/claim-kit/assemble.py')}
    (HERE / 'REPLAY.json').write_text(json.dumps({'clock_utc': clock, 'model': 'gpt-6.1-sol',
        'provider': 'OpenAI', 'tokens': None, 'cash_cost': None, 'active_labor_seconds': None,
        'code_sha256': pins, 'trials': receipts}, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
