#!/usr/bin/env python3
"""Read pinned git objects; exercise existing Valla on five real historical reviews.

Only writes this research directory and a disposable temporary tree. Does not run
the pilot, prepare claims, renew reviews, publish, or launch a production job.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = '600ae3018f71025b3e53dc8538b8f92e6e159b76'
PILOT = 'research/valla/pilot-2026-10-20/'
METHODS = 'research/readiness/method_reviews/sol-valla-20261020.jsonl'
COMPONENTS = 'research/readiness/component_attestations/sol-valla-20261020.jsonl'
RULE = 'jobs/claim-kit/BATCH.md'


def blob(path, rev=BASE):
    return subprocess.check_output(['git', 'show', rev + ':' + path], cwd=REPO)


def rows(raw):
    return [json.loads(x) for x in raw.decode().splitlines() if x.strip()]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    inputs = {}

    def get(path):
        if path not in inputs:
            inputs[path] = blob(path)
        return inputs[path]

    index_raw = get('jobs/valla/output/INDEX.json')
    index = json.loads(index_raw)
    methods = rows(get(METHODS))
    attestations = rows(get(COMPONENTS))
    sample = json.loads(get(PILOT + 'SAMPLE.json'))
    ids = sample['seed']
    assert len(methods) == len(attestations) == len(ids) == 5
    for p in [PILOT + 'METHOD.md', PILOT + 'METHOD_REVIEWS.jsonl',
              PILOT + 'COMPONENT_REVIEWS.jsonl', RULE, 'jobs/valla/valla.py',
              'research/readiness/SOURCE_AUDIT_HOLDS.jsonl']:
        get(p)
    for iid in ids:
        get(sample['claims'][iid]['path'])
    for record in methods + attestations:
        for d in record['dependencies']:
            if d['kind'] in ('file', 'rule'):
                get(d['key'])

    with tempfile.TemporaryDirectory(prefix='valla-research-only-') as td:
        sandbox = Path(td)
        for p, data in inputs.items():
            dest = sandbox / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        spec = importlib.util.spec_from_file_location('pinned_valla', sandbox / 'jobs/valla/valla.py')
        valla = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(valla)
        active = {}
        for iid in ids:
            ref = index['claims'][iid]['claim_ref']
            c = rows(get(ref['path']))[ref['line'] - 1]
            assert c['instrument_id'] == iid and valla.sha(c) == ref['claim_sha256']
            assert ref == sample['claims'][iid], 'historical seed has been superseded; do not silently reuse'
            active[iid] = {'claim': c, 'ref': ref}

        good, refused = valla.confirmed_findings(sandbox, active, frozenset(ids))
        current_components = [valla.validate_attestation(sandbox, a, active[a['instrument_id']]['claim']) for a in attestations]
        traces = []
        holds = rows(get('research/readiness/SOURCE_AUDIT_HOLDS.jsonl'))
        for f in methods:
            c = active[f['instrument_id']]['claim']
            drift = []
            for d in f['dependencies']:
                actual = valla.sha(valla.at(c, d['key'])) if d['kind'] == 'claim_field' else sha(get(d['key']))
                if actual != d['sha256']:
                    drift.append({**d, 'actual_sha256': actual})
            edges = [('/whole_order_end', '/operative_clauses/' + str(i) + '/first_end')
                     for i, clause in enumerate(c['operative_clauses']) if clause.get('first_end')]
            traces.append({'instrument_id': f['instrument_id'], 'claim_ref': active[f['instrument_id']]['ref'],
                           'record_id': f['record_id'], 'rationale_pointer': f['rationale_pointer'],
                           'exact_rationale_span': valla.at(c, f['rationale_pointer'])[f['char_start']:f['char_end']],
                           'span_char_range': [f['char_start'], f['char_end']], 'span_sha256': f['span_sha256'],
                           'historically_examined_conclusion_pointers': f['conclusion_pointers'],
                           'existing_closure_if_review_revalidated': sorted(valla.closure(set(f['conclusion_pointers']), edges)),
                           'dependency_drift': drift,
                           'existing_unresolved_exact_claim_holds': [h for h in holds if h['instrument_id'] == f['instrument_id'] and h['claim_sha256'] == valla.sha(c) and h['state'] == 'unresolved'],
                           'remaining_question': f['unresolved_question']})

        # A declared historical control, not a review renewal: restore the exact
        # old BATCH bytes from the pilot input commit in this temporary tree only.
        old_rule = blob(RULE, sample['input_head'])
        assert all(next(d for d in f['dependencies'] if d['key'] == RULE)['sha256'] == sha(old_rule) for f in methods)
        (sandbox / RULE).write_bytes(old_rule)
        old_good, old_refused = valla.confirmed_findings(sandbox, active, frozenset(ids))
        historical_components = [valla.validate_attestation(sandbox, a, active[a['instrument_id']]['claim']) for a in attestations]
        assert len(good) == 0 and len(refused) == 5
        assert len(old_good) == 5 and not old_refused
        assert all(c['valid'] for c in historical_components)
        selected = active['EO:13792']['claim']
        selected_evidence = {
            'instrument_id': 'EO:13792', 'claim_ref': active['EO:13792']['ref'],
            'research_rationale': selected['research_rationale'],
            'affected_clause': selected['operative_clauses'][12],
            'whole_order_end_assertion': selected['whole_order_end'],
            'original_representation': selected['original_representation'],
            'source_text': get('jobs/fr-originals/data/full_run/texts/EO_13792.txt').decode(),
            'method_record': next(f for f in methods if f['instrument_id'] == 'EO:13792'),
            'component_attestation': next(a for a in attestations if a['instrument_id'] == 'EO:13792'),
            'research_proposal_only': True, 'new_source_examination_performed': False,
        }
        result = {
            'base_commit': BASE, 'scientific_status': 'diagnostic; no new independent source examination or approval',
            'committed_index_summary': index['summary'],
            'committed_index_sha256': sha(index_raw),
            'pinned_runtime_current_dependencies': {'accepted_method_reviews': len(good), 'refused': refused, 'component_results': current_components},
            'temporary_historical_rule_control': {'input_commit': sample['input_head'], 'BATCH_sha256': sha(old_rule),
                                                'accepted_method_reviews': len(old_good), 'refused': old_refused,
                                                'valid_components': sum(c['valid'] for c in historical_components),
                                                'review_renewal': False},
            'trace': traces,
            'pins': [{'path': p, 'sha256': sha(b), 'bytes': len(b), 'commit': BASE} for p, b in sorted(inputs.items())],
            'canonical_mutations': 0, 'production_jobs_launched': 0,
        }
        for name, value in [('DIAGNOSTIC.json', result), ('EO_13792_EVIDENCE.json', selected_evidence)]:
            (OUT / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        print(json.dumps({'accepted_current': len(good), 'accepted_historical_rule_control': len(old_good),
                          'valid_current_components': sum(c['valid'] for c in current_components),
                          'valid_historical_rule_components': sum(c['valid'] for c in historical_components),
                          'trace': [{k: t[k] for k in ('instrument_id', 'dependency_drift', 'existing_closure_if_review_revalidated')} for t in traces]}))


if __name__ == '__main__':
    main()
