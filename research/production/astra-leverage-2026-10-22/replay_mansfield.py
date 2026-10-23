"""Replay the six held Mansfield preparation diagnostics; never publish claims.

Run from the repository root. The baseline commit must already be present.
This writes only the adjacent diagnostic receipt, not job outputs or evidence.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import batch
import excavate
import evidence_preflight

BASE = '46a29e15d6ed4c252416b28e0ccc0590fcf6abc2'
IDS = [10915, 11927, 12975, 9333, 12607, 8072]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def historical_module(name):
    data = subprocess.check_output(['git', 'show', BASE + ':jobs/claim-kit/' + name], cwd=ROOT)
    ns = {'__file__': str(ROOT / 'jobs/claim-kit' / name)}
    exec(compile(data, name + '@' + BASE, 'exec'), ns)
    return ns


def main():
    started = time.monotonic()
    baseline = historical_module('batch.py')
    old_excavate = historical_module('excavate.py')
    rows = []
    for number in IDS:
        path = ROOT / f'jobs/claim-kit/output/dossiers/EO_{number}.json'
        d = json.loads(path.read_bytes())
        before = baseline['preflight'](d, ROOT)
        after = batch.preflight(d, ROOT)
        row = {'instrument_id': d['instrument_id'],
               'dossier_file_sha256': sha(path), 'dossier_fingerprint': d['fingerprint'],
               'before': before, 'after': after,
               'new_ready_dossiers': 0, 'legal_review_complete': False}
        if number == 12607:
            original = d['evidence'][d['original_source_id']]
            text = (ROOT / original['source']['text_path']).read_bytes().decode('utf-8')
            old = old_excavate['segment'](d['instrument_id'], text, original['source'])
            new = excavate.segment(d['instrument_id'], text, original['source'])
            row['bounded_segmentation_replay'] = {
                'before_scope_ids': [c['scope_id'] for c in old['clauses']],
                'after_scope_ids': [c['scope_id'] for c in new['clauses']],
                'restored_first_clause': new['clauses'][0],
                'selected_source_still_truncated': True,
                'canonical_dossier_changed': False}
        rows.append(row)
    controls = []
    for number in [10032, 10056]:
        path = ROOT / f'jobs/claim-kit/output/dossiers/EO_{number}.json'
        if path.exists():
            d = json.loads(path.read_bytes())
            screen = evidence_preflight.inspect(d, ROOT)
            controls.append({'instrument_id': d['instrument_id'], 'dossier_file_sha256': sha(path),
                             'added_evidence_tasks': screen['tasks'],
                             'held_text_receipts': screen['held_text_receipts'],
                             'notice': 'Unaffected preparation control; not a legal-readiness finding.'})
        else:
            controls.append({'instrument_id': f'EO:{number}', 'result': 'untested_missing_dossier'})
    result = {
        'schema': 'eo-mansfield-preparation-diagnostic/v1', 'base_commit': BASE,
        'mansfield_pr54_head': 'd8613babe75bbee5ac6b46d9e756835a8d61c5ab',
        'scope': 'Six known failures, necessary diagnostic controls; not a representative sample.',
        'rows': rows, 'unaffected_controls': controls,
        'summary': {'cases': len(rows), 'new_ready_dossiers': 0,
            'source_acquisitions': 0, 'legal_findings': 0,
            'before_tasks': sum(len(r['before']['mechanical_tasks']) for r in rows),
            'after_tasks': sum(len(r['after']['mechanical_tasks']) for r in rows),
            'bounded_segmentation_repairs': 1},
        'cost': {'machine_seconds': round(time.monotonic() - started, 6),
            'uncached_input_tokens': None, 'cached_input_tokens': None,
            'cache_write_tokens': None, 'output_tokens': None,
            'aggregate_agent_seconds': None, 'verified_efficiency_savings': None},
        'code_sha256': {name: sha(ROOT / 'jobs/claim-kit' / name)
                       for name in ['batch.py', 'evidence_preflight.py', 'excavate.py']},
        'notice': 'Preflight diagnoses obligations; it does not fix raw custody, replace a source, approve an ACT, decide law, or clear an existing hold.'}
    path = Path(__file__).with_name('MANSFIELD_REPAIRS.json')
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    main()
