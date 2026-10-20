"""Reproducible bounded pilot. Creates no review attestations or legal decisions.

Uses already-authored, source-pinned reviews. All tasks remain blocked pending
actual-event research and independent whole-case review; timings concern machine
preparation only. Run with --output a new directory outside production outputs.
"""
import argparse
import csv
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import valla as V

BASE = '91116f879978902343dafa88490b9b19587b10da'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def run(repo, out, run_id):
    repo = Path(repo).resolve(); out = Path(out).resolve()
    if out.exists():
        raise ValueError('new output directory required')
    out.mkdir(parents=True)
    started = time.monotonic(); sample = json.loads((repo / 'research/valla/pilot-2026-10-20/SAMPLE.json').read_bytes())
    if sample['patterns_sha256'] != V.file_sha(V.HERE / 'premises.json'):
        raise ValueError('pilot patterns changed after sample freeze')
    before_claims = V.pins(repo, [r['path'] for r in sample['claims'].values()])
    active, _ = V.active_claims(repo)
    for iid, ref in sample['claims'].items():
        if active[iid]['ref'] != ref:
            raise ValueError('pilot claim changed: ' + iid)
    index = V.build(repo); V.dump(out / 'INDEX.json', index)
    V.dump(out / 'SUMMARY.json', index['summary'])
    sys.path.insert(0, str(repo / 'jobs/claim-kit'))
    import batch
    runtime = repo / 'research/valla/pilot-runtime' / run_id
    if runtime.exists():
        raise ValueError('new runtime version required')
    runtime.mkdir(parents=True)
    comparison = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); baseline = subprocess.run(['git', 'show', BASE + ':jobs/claim-kit/batch.py'], cwd=repo,
                                                capture_output=True, check=True).stdout
        (td / 'batch.py').write_bytes(baseline)
        (td / 'assemble.py').write_bytes((repo / 'jobs/claim-kit/assemble.py').read_bytes())
        reference = load_module('valla_reference_batch', td / 'batch.py')
        # Three identical real tasks, both orders of arms, every failed/blocked attempt kept.
        for n, iid in enumerate(sample['seed'][:3]):
            arms = [('baseline', reference), ('assisted', batch)]
            if n % 2:
                arms.reverse()
            for arm, module in arms:
                dest = runtime / arm / iid.replace(':', '_')
                t0 = time.monotonic()
                try:
                    metrics = module.prepare(repo, repo / 'jobs/claim-kit/output', dest, [iid], 'sol-valla-pilot', replacement_proposal=True)
                    preparation = time.monotonic() - t0
                    rs = module.rows(dest / 'decisions.csv')
                    for r in rs:
                        r['outcome'] = 'blocked'
                        r['unresolved_material_gaps'] = json.dumps(['Actual performance and its legal scope remain unresolved; retain independent whole-case review.'])
                    module.csv_write(dest / 'decisions.csv', module.ROW_FIELDS, rs)
                    t1 = time.monotonic(); applied = module.apply(repo, dest, dest / 'applied-v1')
                    apply_seconds = time.monotonic() - t1
                    t1 = time.monotonic(); checked = module.check(repo, dest, dest / 'applied-v1')
                    integration_seconds = time.monotonic() - t1
                    comparison.append({'instrument_id': iid, 'arm': arm, 'outcome': 'blocked_retained',
                        'producer_preparation_machine_seconds': preparation,
                        'correction_machine_seconds': apply_seconds, 'integration_machine_seconds': integration_seconds,
                        'whole_case_review_seconds': None, 'coordination_active_seconds': None,
                        'producer_active_seconds': None, 'model_tokens': None, 'session_cost_usd': None,
                        'complete_total_cost_measured': False, 'packet_sha256': V.file_sha(dest / 'PACKET.json'),
                        'blocked_members': checked['outcomes_including_blocked'], 'submitted_claims': checked['claims_checked'],
                        'source_files_validated': metrics['source_files_validated']})
                except Exception as exc:
                    comparison.append({'instrument_id': iid, 'arm': arm, 'outcome': 'failed_retained',
                        'machine_seconds': time.monotonic() - t0, 'reason': str(exc), 'complete_total_cost_measured': False})
    # One concrete owner-routed correction packet for all five; no legal fields pre-approved.
    correction = runtime / 'correction-v1'
    V.correction(repo, repo / 'jobs/claim-kit/output', sample['seed'], correction, 'sol-valla-pilot')
    packet, _ = batch.load_packet(correction, repo)
    assert packet['valla_context']['automatic_approvals'] == 0
    assert all(r['approved'] == 'false' for r in batch.rows(correction / 'decisions.csv'))
    assert sum(len([r for r in x['component_reviews'] if r['valid']]) for x in packet['valla_context']['claims'].values()) == 5
    assert all(x['invalidated_conclusion_pointers'] for x in packet['valla_context']['claims'].values())
    V.dump(out / 'COMPARISON.json', {'schema': 'valla-correction-comparison/v1', 'tasks': comparison,
        'unit': 'one blocked real correction task with all member-specific research outstanding',
        'baseline_batch_code_sha256': __import__('hashlib').sha256(baseline).hexdigest(),
        'assisted_batch_code_sha256': V.file_sha(repo / 'jobs/claim-kit/batch.py'),
        'limitations': ['No independent whole-case corrections were completed in either arm.',
                       'Same-session crossover measures mechanical preparation, with order/cache contamination.',
                       'Producer, reviewer, correction, coordination and integration model costs are unavailable; no total saving is claimed.'],
        'verified_rework_savings_usd': None, 'efficiency_verdict': 'unverified'})
    # Actually run the existing checker on five frozen existing claims (not replacements).
    selected = out / 'existing-claims.jsonl'
    selected.write_text(''.join(V.canon(active[i]['claim']) + '\n' for i in sample['seed']))
    env = {**os.environ, 'REPO_ROOT': str(repo), 'OUTPUT_DIR': str(out / 'checker'),
           'CLAIM_CHECKER_VERIFY_DOWNLOADS': '0', 'PYTHONIOENCODING': 'utf-8'}
    with (out / 'CHECKER.log').open('w') as log:
        result = subprocess.run([sys.executable, '-B', str(repo / 'jobs/claim-checker/checker.py'), '--claims', str(selected)],
                                cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError('existing checker execution failed; see retained CHECKER.log')
    # Tracker runs against unchanged canonical files and committed checker output.
    env['OUTPUT_DIR'] = str(out / 'tracker')
    with (out / 'TRACKER.log').open('w') as log:
        result = subprocess.run([sys.executable, '-B', str(repo / 'jobs/readiness-tracker/tracker.py')],
                                cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError('tracker execution failed; see retained TRACKER.log')
    if before_claims != V.pins(repo, before_claims):
        raise ValueError('canonical claims changed during pilot')
    checker = json.loads((out / 'checker/SUMMARY.json').read_bytes())
    proof = {'schema': 'valla-integrated-pilot/v1', 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
             'github_run_id': os.environ.get('GITHUB_RUN_ID'), 'valla_summary': index['summary'],
             'index_fingerprint': index['fingerprint'], 'canonical_claims_unchanged': True,
             'independent_whole_case_replacement_reviews': 0, 'replacement_claims_published': 0,
             'checker_existing_claims': {k: checker.get(k) for k in ('claims_checked', 'claims_all_checks_passed', 'claims_gate_passed')},
             'correction_packet_path': correction.relative_to(repo).as_posix(), 'correction_packet_sha256': V.file_sha(correction / 'PACKET.json'),
             'comparison_arms_retained': len(comparison), 'wall_seconds': time.monotonic() - started,
             'verified_rework_saving': False}
    V.dump(out / 'INTEGRATED.json', proof)
    print(V.canon(proof))
    return proof


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--repo', type=Path, default=V.REPO)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--run-id', required=True)
    a = p.parse_args(); run(a.repo, a.output, a.run_id)
