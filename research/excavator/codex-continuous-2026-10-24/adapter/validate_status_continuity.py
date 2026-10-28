#!/usr/bin/env python3
"""Bounded offline format/continuity audit, not a substantive legal review."""
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'jobs/claim-kit'))
import kit
import prior_research


def schema_scope(repo, exclude):
    """Count the actual status formats in current research files, not beneficiaries."""
    supported = {prior_research.STATUS_DECISION_SCHEMA, 'eo-status-overlay-review/v1',
                 'sinclair-cross-family-lean-review/v1', prior_research.STATUS_HOLD_SCHEMA}
    records = defaultdict(list)
    for path in sorted((repo/'research').rglob('*.json')):
        if path.is_relative_to(exclude) or path.name in ('PACKET.json', 'EVIDENCE.json'):
            continue
        try:
            value = json.loads(path.read_bytes())
        except (OSError, ValueError):
            continue
        if not isinstance(value, dict):
            continue
        schema = value.get('schema', '')
        if not isinstance(schema, str):
            continue
        if schema not in supported and not ('status' in schema or schema.startswith('sinclair-')):
            continue
        identities = ([value['instrument_id']] if value.get('instrument_id') else
            sorted({row['instrument_id'] for key in ('verdicts', 'proposals')
                    for row in value.get(key, []) if isinstance(row, dict) and row.get('instrument_id')}))
        records[schema].append({'path': path.relative_to(repo).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'instrument_ids': identities})
    return {'scope': 'Current materialized status research formats only; no inventory survey, legal eligibility, research deployment or savings inference.',
        'limitations': ['Top-level real schemas only; status evidence packets are accessed through decision pins.',
            'Unsupported historical/administrative formats remain source-accessible; no review approval inferred.',
            'Unmaterialized files and Git history are outside discovery.'],
        'schemas': {schema: {'directly_adapted': schema in supported, 'file_count': len(rows),
            'instrument_count': len({iid for row in rows for iid in row['instrument_ids']}),
            'records': rows} for schema, rows in sorted(records.items())}}


def main():
    start = time.monotonic()
    utc = datetime.now(timezone.utc).isoformat()
    dest = Path(__file__).resolve().parent
    review_root = REPO / 'research/excavator/sinclair-2026-10-20/lean-review-2026-10-22'
    review = json.loads((review_root / 'CROSS_FAMILY_REVIEW.json').read_text())
    holds = json.loads((review_root / 'HELD_PROPOSALS.json').read_text())
    with (review_root / 'CROSS_FAMILY_ADOPTION_ROWS.csv').open() as handle:
        cohort = [r['instrument_id'] for r in csv.DictReader(handle)]
    dossiers = {iid: kit.load_dossier(REPO / 'jobs/claim-kit/output', iid) for iid in cohort}
    extra = ['EO:9380', 'EO:9593'] + [r['instrument_id'] for r in holds['proposals']]
    for iid in extra:
        # These are deliberately unadopted: use the actual frozen full base dossier
        # only as a format-audit carrier, and disclose that it is not a current freeze.
        path = next((REPO/'research/excavator/sinclair-2026-10-20').rglob(iid.replace(':', '_') + '/proposal-v1/EVIDENCE.json'))
        dossiers[iid] = json.loads(path.read_text())['base_dossier']
    context = prior_research.collect(REPO, dossiers, exclude=dest.parent)
    checks = []
    for n, row in enumerate(review['verdicts']):
        iid = row['instrument_id']
        expected_path = next(p['path'] for p in row['input_files'] if p['path'].endswith('/STATUS_DECISION.json'))
        status = next(v for v in context['orders'][iid]['status_research'] if v['path'] == expected_path)
        found = next(r for r in status['reviews'] if r['path'].endswith('/CROSS_FAMILY_REVIEW.json'))
        assert found['pointer'] == '/verdicts/' + str(n)
        assert found['version_binding'] == 'exact', (iid, found['version_binding'])
        assert found['verdict'] == row['verdict']
        assert found['scope'] == row['scope']
        assert found['d6'] == {k: row['d6'][k] for k in ('assessment', 'coverage')}
        assert status['automatic_approval'] is False and found['full_lifecycle_approved'] is False
        assert all(p['state'] in ('match', 'missing', 'changed', 'outside_repository')
                   for p in status['source_pins'])
        brief = prior_research.brief(context, iid)
        if iid in cohort:
            assert status['adoption']['state'] == 'recorded_provisional_status_for_review'
        else:
            assert found['verdict'] == 'needs_research'
            assert status['adoption']['state'] == 'not_recorded_in_current_authority'
        if iid == 'EO:13975':
            assert '14006' in json.dumps(brief) and '14005' in json.dumps(brief)
            questions = brief['remaining_delta']['existing_lifecycle_questions']
            assert any(q['scope_id'] == 'EO:13975#sec4' and any('performance' in x for x in q['questions'])
                       for q in questions)
        if iid == 'EO:10704':
            assert 'Do not adopt the producer earlier-displacement theory' in json.dumps(brief)
        checks.append({'instrument_id': iid, 'status_decision_path': status['path'],
            'decision_sha256': status['decision_sha256'], 'review_pointer': found['pointer'],
            'binding': found['version_binding'], 'verdict': found['verdict'],
            'adoption': status['adoption']['state'], 'reconciliation_tasks': len(status['reconciliation_tasks']),
            'source_pin_states': dict(Counter(p['state'] for p in status['source_pins'])),
            'review_dependency_states': dict(Counter(p['state'] for p in found['dependency_pins'])),
            'brief_bytes': len(json.dumps(brief).encode())})
    hold_checks = []
    for row in holds['proposals']:
        iid = row['instrument_id'];found = context['orders'][iid]['status_holds']
        assert len(found) == 1 and found[0]['record']['hold_reason'] == row['hold_reason']
        assert found[0]['state'] == 'held_out_of_pending_adoption'
        assert found[0]['historical_review']['binding'] == 'exact'
        assert found[0]['historical_review']['record']['instrument_id'] == iid
        assert found[0]['historical_review']['producer_version_binding'] == 'not_established_by_procedural_hold'
        assert found[0]['automatic_approval'] is False and found[0]['full_lifecycle_approved'] is False
        assert all(s['adoption']['state'] == 'not_recorded_in_current_authority' for s in context['orders'][iid]['status_research'])
        hold_checks.append({'instrument_id': iid, 'hold_reason': row['hold_reason'], 'path': found[0]['path'],
            'historical_review_pointer': found[0]['historical_review']['pointer'],
            'historical_review_binding': found[0]['historical_review']['binding']})
    protected = ['research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv',
        'research/excavator/sinclair-2026-10-20/lean-review-2026-10-22/CROSS_FAMILY_REVIEW.json',
        'research/excavator/sinclair-2026-10-20/lean-review-2026-10-22/HELD_PROPOSALS.json']
    unchanged = {}
    for path in protected:
        baseline = json.loads((dest/'BASELINE_AUTHORITY_PINS.json').read_text())
        assert baseline['commit'] == '21f9fed4d52b565692cd3a81480435f7ef1ff143'
        raw = (REPO/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == baseline['sha256'][path], path
        unchanged[path] = hashlib.sha256(raw).hexdigest()
    (dest/'VALIDATED_CONTEXT.json').write_text(json.dumps(context, indent=2)+'\n')
    (dest/'FORMAT_SCOPE.json').write_text(json.dumps(schema_scope(REPO, dest.parent), indent=2)+'\n')
    result = {'schema': 'eo-status-continuity-validation/v1',
        'scope': 'Actual format/discovery/version-binding checks only; no new legal review or approval.',
        'cohort_dossiers': '29 current decided dossiers',
        'extra_dossiers': '2 withheld plus 6 held: historical frozen base dossiers solely as audit carriers',
        'start_utc': utc, 'end_utc': datetime.now(timezone.utc).isoformat(),
        'start_monotonic': start, 'end_monotonic': time.monotonic(),
        'elapsed_seconds': time.monotonic()-start, 'model_tokens': None, 'cached_tokens': None,
        'model_usage_limitation': 'Per-agent token/cache usage unavailable in tool runtime.',
        'cohort_count': len(cohort), 'cross_family_records': checks, 'parent_holds': hold_checks,
        'protected_unchanged_sha256': unchanged, 'automatic_approvals': context['automatic_approvals']}
    (dest/'VALIDATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'validated_cohort': len(cohort), 'withheld': 2, 'holds': len(hold_checks),
        'elapsed_seconds': result['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
