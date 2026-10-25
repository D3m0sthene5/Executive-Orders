"""Independent mechanical binding probes against an explicitly supplied module.

Uses temporary synthetic records only. This is no legal/source review.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--write', type=Path, required=True)
    args = parser.parse_args()
    sys.path[:0] = [str(args.stage), str(args.repo/'jobs/claim-kit')]
    import prior_research as prior
    # Imported kit helpers may prepend their own directory to sys.path. Load
    # the explicitly requested fixture file, rather than a same-named live one.
    spec = importlib.util.spec_from_file_location('review_status_fixture',
        args.stage/'test_status_continuity.py')
    fixture_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture_module)
    StatusContinuityTests = fixture_module.StatusContinuityTests

    def fixture():
        case = StatusContinuityTests('test_exact_producer_and_scoped_corrections_reach_brief')
        case.setUp()
        return case

    def result(case):
        item = case.item()
        review = next(r for r in item['reviews'] if r['path'] == case.cross_path)
        return {'evidence_binding': item['evidence']['canonical_binding'],
            'review_binding': review['version_binding'], 'dependency_state': review.get('dependency_state'),
            'adoption_state': item['adoption']['state'],
            'reconciliation_tasks': item['reconciliation_tasks'],
            'remaining_questions': item['remaining_questions'],
            'basis_sources': review.get('basis_sources'),
            'automatic_approval': item['automatic_approval']}

    outputs = {}
    case = fixture()
    try:
        wrong = deepcopy(case.evidence)
        wrong['instrument_id'] = 'EO:14006'
        wrong['fingerprint'] = prior.canonical_sha({k:v for k,v in wrong.items() if k != 'fingerprint'})
        other = case.folder + '/WRONG_EVIDENCE.json'
        case.write(other, wrong)
        cross = deepcopy(case.cross)
        cross['verdicts'][0]['input_files'][1] = {'path': other, 'sha256': case.digest(other)}
        case.write(case.cross_path, cross)
        outputs['wrong_evidence_manifest_member'] = result(case)
    finally:
        case.doCleanups()

    case = fixture()
    try:
        evidence = deepcopy(case.evidence)
        evidence['base_dossier'] = {'schema': 'eo-claim-kit-dossier/v1', 'instrument_id': 'EO:14006'}
        evidence['base_dossier']['fingerprint'] = prior.canonical_sha(evidence['base_dossier'])
        evidence['fingerprint'] = prior.canonical_sha({k:v for k,v in evidence.items() if k != 'fingerprint'})
        case.write(case.folder + '/EVIDENCE.json', evidence)
        decision = {**case.decision, 'evidence_sha256': evidence['fingerprint']}
        case.write(case.decision_path, decision)
        cross = deepcopy(case.cross)
        cross['verdicts'][0]['input_files'][0]['sha256'] = case.digest(case.decision_path)
        cross['verdicts'][0]['input_files'][1]['sha256'] = case.digest(case.folder + '/EVIDENCE.json')
        cross['verdicts'][0]['evidence_canonical_fingerprint'] = evidence['fingerprint']
        case.write(case.cross_path, cross)
        outputs['wrong_embedded_dossier_identity'] = result(case)
    finally:
        case.doCleanups()

    case = fixture()
    try:
        cross = deepcopy(case.cross)
        cross['verdicts'][0]['input_files'][1].pop('sha256')
        case.write(case.cross_path, cross)
        outputs['missing_evidence_manifest_hash'] = result(case)
    finally:
        case.doCleanups()

    outputs['reviewed_module_sha256'] = hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()
    args.write.write_text(json.dumps(outputs, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: {n:v for n,v in r.items() if n in ('evidence_binding','review_binding','dependency_state','adoption_state','reconciliation_tasks')}
        for k,r in outputs.items() if isinstance(r,dict)}, indent=2))


if __name__ == '__main__':
    main()
