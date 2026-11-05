"""Fresh prepare/apply/batch-check replay of two retained Tribonian rows.

Pass --retained DIRECTORY containing exact o27 PACKET.json, decisions.csv,
clauses.csv and RATIONALES.json from state 2bc32c6. This does not reuse reviews
or publish claims. Temporary preparation stays under research and is removed.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def main(args):
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo / 'jobs/claim-kit'))
    import batch
    frozen = json.loads((args.retained / 'PACKET.json').read_bytes())
    decoded = batch.decode(frozen)  # evidence extraction only; never renew an old seal
    ids = ['EO:13128', 'EO:13274']
    os.environ.update(CLAIM_KIT_CACHE_DIR=str(out / 'cache'), CLAIM_CHECKER_VERIFY_DOWNLOADS='0')
    result = {'scope': 'engineering replay; no review renewal or publication', 'members': ids, 'steps': {}}
    with tempfile.TemporaryDirectory(prefix='runtime-economy-', dir=repo / 'research') as tmp:
        root = Path(tmp)
        paths = {}
        for iid in ids:
            p = root / (iid.replace(':', '_') + '.json')
            p.write_text(json.dumps(decoded[iid]))
            paths[iid] = p
        folder = root / 'packet'
        started = time.monotonic()
        result['steps']['prepare'] = batch.prepare(repo, repo / 'jobs/claim-kit/output', folder, ids,
                                                   'runtime-economy-engineering', dossier_paths=paths,
                                                   replacement_proposal=True)
        result['steps']['prepare_seconds'] = time.monotonic() - started
        for name, fields in (('decisions.csv', batch.ROW_FIELDS), ('clauses.csv', batch.CLAUSE_FIELDS)):
            rows = [r for r in batch.rows(args.retained / name) if r['instrument_id'] in ids]
            batch.csv_write(folder / name, fields, rows)
        shutil.copyfile(args.retained / 'RATIONALES.json', folder / 'RATIONALES.json')
        started = time.monotonic()
        result['steps']['apply'] = batch.apply(repo, folder, folder / 'applied')
        result['steps']['apply_seconds'] = time.monotonic() - started
        started = time.monotonic()
        result['steps']['batch_check'] = batch.check(repo, folder, folder / 'applied', actual=True)
        result['steps']['batch_check_seconds'] = time.monotonic() - started
        # The archived o27 root sheets are still unresolved. Keep that failed
        # attempt intact, then mechanically recheck the already filed exact
        # claims through the ordinary CLI. No producer or review assertion is
        # manufactured from the incomplete archived sheets.
        canonical = repo / 'research/readiness/claims/claude-2026-11-04-tribonian-o27.jsonl'
        retained = folder / 'retained-recheck'
        retained.mkdir()
        shutil.copyfile(canonical, retained / 'CLAIMS.proposed.jsonl')
        batch.dump(retained / 'AUDIT.json', [
            {'instrument_id': iid, 'outcome': 'retained_existing_claim', 'errors': []} for iid in ids])
        started = time.monotonic()
        with (out / 'BATCH_CHECK.log').open('w') as log:
            invocation = subprocess.run([sys.executable, '-B', str(repo / 'jobs/claim-kit/kit.py'),
                                         '--repo', str(repo), 'batch-check', str(folder), str(retained)],
                                        cwd=repo, stdout=log, stderr=subprocess.STDOUT)
        result['steps']['retained_cli_batch_check_returncode'] = invocation.returncode
        result['steps']['retained_cli_batch_check_seconds'] = time.monotonic() - started
        if (retained / 'CHECK_SUMMARY.json').exists():
            result['steps']['retained_cli_batch_check'] = json.loads((retained / 'CHECK_SUMMARY.json').read_bytes())
        shutil.copytree(retained, out / 'retained-recheck')
        # Retain exact candidate/checker outputs; these are not canonical filings.
        shutil.copytree(folder / 'applied', out / 'applied')
        for name in ('PREPARE.json', 'DISPATCH_CHECK.json'):
            shutil.copyfile(folder / name, out / name)
        result['candidate_bytes_equal_existing_retained_claims'] = (
            (folder / 'applied/CLAIMS.proposed.jsonl').read_bytes() == canonical.read_bytes())
    (out / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--retained', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    main(p.parse_args())
