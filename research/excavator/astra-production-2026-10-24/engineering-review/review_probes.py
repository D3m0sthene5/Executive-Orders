"""Independent engineering probes using actual checker/tracker and tiny source corpus.

Run from the repository root. Synthetic fixtures establish engineering behavior
only; they make no claim about any historical executive order.
"""
from datetime import datetime, timezone
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
if len(sys.argv) > 1:
    OUT = OUT / sys.argv[1]
    OUT.mkdir(exist_ok=False)
sys.path.insert(0, str(REPO / 'jobs/claim-kit'))
sys.path.insert(0, str(REPO / 'jobs/readiness-tracker'))
import completion as C
import batch
import test_completion as fixtures
import test_tracker as tracker_fixtures

CODE = ['jobs/claim-kit/completion.py', 'jobs/claim-kit/test_completion.py',
        'jobs/claim-kit/kit.py', 'jobs/claim-kit/COMPLETION.md',
        'jobs/claim-kit/BATCH.md', 'jobs/claim-kit/AGENT_PROTOCOL.md',
        'AGENTS.md', 'research/readiness/README.md',
        'jobs/claim-checker/checker.py', 'jobs/readiness-tracker/tracker.py']


def fixture():
    f = fixtures.CompletionTests('test_exact_producer_bytes_and_all_consumed_receipts_preserved')
    f.setUp()
    f.setup_completion()
    # This probe covers the supported ordinary-claim path, independent of the
    # packet producer. Its exact source spans still go through the real gates.
    f.claim.pop('claim_kit')
    f.producer.write_bytes((json.dumps(f.claim, ensure_ascii=False) + '\r\n').encode())
    f.review['claim_sha256'] = C.claim_sha(f.claim)
    batch.dump(f.review_path, f.review)
    f.manifest['members'][0].update(claim=f.ref(f.producer, line=1),
        claim_sha256=C.claim_sha(f.claim), review=f.ref(f.review_path))
    f.add_control()
    t = tracker_fixtures.TrackerTest('test_complete_claim_makes_an_order_ready')
    t.setUp()
    for key, rel in tracker_fixtures.tracker.P.items():
        if key not in ('universe', 'decided', 'claims', 'claim_gate_dir') and (t.root / rel).is_file():
            target = f.repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(t.root / rel, target)
    t.tearDown()
    (f.repo / 'research/readiness/claims').mkdir(parents=True, exist_ok=True)
    f.status.write_text('instrument_id,provisional_substantive_status,decision_origin\n' +
                        ''.join(f'EO:{n},{"yes" if n == 3 else "no"},synthetic\n' for n in (1,2,3,5,6)))
    for rel in ('jobs/claim-checker/checker.py', 'jobs/claim-checker/sources.py',
                'jobs/readiness-tracker/tracker.py', 'jobs/claim-kit/working_text.py',
                'jobs/claim-kit/factual_events.py', 'jobs/norton/model.py'):
        target = f.repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, target)
    sources = []
    for source in sorted((f.repo / 'jobs/future-source/data/texts').glob('*.txt')):
        raw = f.repo / 'jobs/future-source/output/raw' / source.name
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(source.read_bytes())
        sources.append({'url': 'https://example.gov/' + source.stem,
            'sha256': batch.file_sha(raw), 'cache_path': 'raw/' + raw.name,
            'text_path': 'raw/' + raw.name, 'instrument_ids': [source.stem.replace('_', ':')]})
    receipt = f.repo / 'jobs/future-source/output/SOURCES.jsonl'
    receipt.write_text(''.join(json.dumps(row) + '\n' for row in sources))
    dates = f.repo / 'jobs/future-source/output/SIGNING_DATES.csv'
    dates.write_text('instrument_id,signing_date\n' + ''.join(f'EO:{n},1990-01-01\n' for n in (1,2,3,4,5,6)))
    return f


def execute(name, mutate=None, configure=None):
    f = fixture()
    try:
        if configure:
            configure(f)
        batch.dump(f.manifest_path, f.manifest)
        target = f.repo / f.manifest['publication']['path']
        previous_target = target.read_bytes() if target.exists() else None
        actual_checker = C.run_checker
        mutation = {}
        def checker(repo, claims, dest):
            result = actual_checker(repo, claims, dest)
            if mutate:
                mutation.update(mutate(f))
            return result
        api_error = None
        with patch.object(C, 'run_checker', side_effect=checker):
            try:
                result = C.complete(f.repo, f.manifest_path, f.dest, True)
            except (ValueError, OSError) as exc:
                result = {}
                api_error = type(exc).__name__ + ': ' + str(exc)
        replay = f.dest / 'TRACKER_REPLAY.json'
        checked = json.loads((f.dest / 'checker/PER_CLAIM.json').read_text()) if (f.dest / 'checker/PER_CLAIM.json').exists() else {}
        item = {'name': name, 'result': result, 'mutation': mutation,
                'api_error': api_error,
                'target_exists': target.exists(),
                'target_bytes_match_producer': target.exists() and target.read_bytes() == f.producer.read_bytes(),
                'preexisting_target_unchanged': previous_target is not None and target.read_bytes() == previous_target,
                'producer_raw_sha256': batch.file_sha(f.producer),
                'actual_checker_claims': checked.get('claims', []),
                'tracker_selected': json.loads(replay.read_text()).get('selected') if replay.exists() else None}
        artifact = OUT / ('probe-' + name)
        if artifact.exists():
            raise ValueError('fresh artifact path required: ' + str(artifact))
        if f.dest.exists():
            shutil.copytree(f.dest, artifact, ignore=shutil.ignore_patterns('cache'))
        return item
    finally:
        f.doCleanups()


def corrupt_raw(f):
    path = f.repo / 'jobs/future-source/output/raw/EO_1.txt'
    old = batch.file_sha(path)
    path.write_bytes(b'Corrupted raw copy after the actual checker finished.\n')
    return {'path': path.relative_to(f.repo).as_posix(), 'before_sha256': old,
            'after_sha256': batch.file_sha(path)}


def partial(f):
    f.manifest['members'][0]['publication_kind'] = 'partial_research'
    f.review['scope'] = 'partial_research'
    f.review.pop('expected_gate_errors', None)
    batch.dump(f.review_path, f.review)
    f.manifest['members'][0]['review'] = f.ref(f.review_path)
    after = f.folder / 'AFTER_REVEAL.json'
    batch.dump(after, dict(f.review, verdict='upheld_after_reveal'))
    f.manifest['members'][0]['after_reveal_review'] = f.ref(after)


def concurrent_owner(f):
    path = f.repo / 'research/readiness/claims/other-owner-2026-10-24.jsonl'
    path.write_bytes(f.producer.read_bytes())
    return {'path': path.relative_to(f.repo).as_posix(), 'sha256': batch.file_sha(path)}


def concurrent_frozen_owner(f):
    path = f.repo / 'research/production/claim-kit-pilot-2026-10-18/FREEZE_MANIFEST.json'
    batch.dump(path, {'accepted': [{'instrument_id': 'EO:1', 'canonical_claim_sha256': C.claim_sha(f.claim)}]})
    return {'path': path.relative_to(f.repo).as_posix(), 'sha256': batch.file_sha(path)}


def partial_status_mismatch(f):
    f.claim['operative_clauses'][0]['first_end'] = None
    f.claim['whole_order_end'] = None
    f.claim['unresolved_material_gaps'] = ['The exact first cessation is unresolved.']
    f.producer.write_bytes((json.dumps(f.claim, ensure_ascii=False) + '\r\n').encode())
    f.review.update(claim_sha256=C.claim_sha(f.claim), scope='partial_research',
                    expected_gate_errors=C._gate(f.repo).validate_claim(f.claim))
    batch.dump(f.review_path, f.review)
    f.manifest['members'][0].update(claim=f.ref(f.producer, line=1),
        claim_sha256=C.claim_sha(f.claim), review=f.ref(f.review_path), publication_kind='partial_research')
    f.add_control()
    f.status.write_text(f.status.read_text().replace('EO:1,no,synthetic', 'EO:1,yes,synthetic'))


def partial_machine_exhausted(f):
    partial_status_mismatch(f)
    f.status.write_text(f.status.read_text().replace('EO:1,yes,synthetic', 'EO:1,no,synthetic'))
    shared = f.repo / tracker_fixtures.tracker.P['shared']
    with shared.open() as stream:
        rows = list(csv.DictReader(stream))
    tracker_fixtures.write_csv(shared, [row for row in rows if row['cited_in'] != 'EO:1'])
    exhausted = f.repo / tracker_fixtures.tracker.P['exhausted']
    exhausted.write_text(json.dumps({'instrument_id': 'EO:1', 'step': 'ending_or_current_basis',
        'searched': ['Complete synthetic corpus'], 'recorded_by': 'synthetic', 'recorded_on': '2026-10-24'}) + '\n')


def owned(f):
    concurrent_owner(f)


def replacement(f):
    owned(f)
    f.manifest['publication'] = {'mode': 'replacement_proposal',
                                'path': 'research/isolated/REPLACEMENT.jsonl'}


def preexisting(f):
    target = f.repo / f.manifest['publication']['path']
    target.write_bytes(b'Existing destination must remain untouched.\n')


def no_controls(f):
    f.manifest['controls'] = []


def same_family_with_space(f):
    f.manifest['independence_requirement'] = 'different_family'
    f.manifest['producer_model_family'] = 'OpenAI '


def unsafe_seed_container(f):
    ref = f.manifest['controls'][0]['seed']
    path = f.repo / ref['path']
    safe = json.loads(path.read_text())
    batch.dump(path, {'seed': safe, 'private_key': 'Synthetic key must never be copied.'})
    f.manifest['controls'][0]['seed'] = f.ref(path, pointer='/seed')


def main():
    started = datetime.now(timezone.utc).isoformat()
    timer = time.monotonic()
    result = {'started_utc': started, 'code_sha256': {rel: batch.file_sha(REPO / rel) for rel in CODE},
              'actual_model_tokens': None, 'cached_model_tokens': None, 'model_cost': None,
              'probes': []}
    for name, mutate, configure in [('actual_consumers_baseline', None, None),
            ('raw_custody_changed_after_checker', corrupt_raw, None),
            ('partial_without_exact_gap_attestation', None, partial),
            ('canonical_owner_appears_during_checker', concurrent_owner, None),
            ('frozen_owner_appears_during_checker', concurrent_frozen_owner, None),
            ('partial_canonical_status_mismatch', None, partial_status_mismatch),
            ('partial_cannot_gain_machine_exhausted_ready', None, partial_machine_exhausted),
            ('existing_other_owner_rejected', None, owned),
            ('isolated_replacement_proposal', None, replacement),
            ('existing_destination_no_clobber', None, preexisting),
            ('empty_controls_rejected', None, no_controls),
            ('whitespace_does_not_create_different_family', None, same_family_with_space),
            ('safe_seed_cannot_select_unsafe_container', None, unsafe_seed_container)]:
        try:
            result['probes'].append(execute(name, mutate, configure))
        except Exception as exc:
            result['probes'].append({'name': name, 'probe_error': type(exc).__name__ + ': ' + str(exc)})
    result['finished_utc'] = datetime.now(timezone.utc).isoformat()
    result['wall_seconds'] = time.monotonic() - timer
    checks = []
    for p in result['probes']:
        name = p['name']
        success = name in ('actual_consumers_baseline', 'isolated_replacement_proposal')
        valid = not p.get('probe_error')
        if success:
            valid = valid and p['result'].get('eligible') == ['EO:1'] and p['target_bytes_match_producer']
            valid = valid and p['result'].get('claims_published') == (0 if name == 'isolated_replacement_proposal' else 1)
        elif name == 'existing_destination_no_clobber':
            valid = valid and bool(p['api_error']) and p['preexisting_target_unchanged']
        else:
            valid = valid and not p.get('target_exists') and not p.get('result', {}).get('eligible')
        if name == 'raw_custody_changed_after_checker':
            valid = valid and p['actual_checker_claims'][0]['all_checks_passed'] is True
        if name == 'partial_cannot_gain_machine_exhausted_ready':
            valid = valid and p['tracker_selected']['EO:1']['after']['ready_tier'] == 'machine_exhausted'
        checks.append({'name': name, 'expected_outcome_passed': bool(valid)})
    result['assertions'] = checks
    result['passed'] = sum(c['expected_outcome_passed'] for c in checks)
    batch.dump(OUT / 'PROBE_RESULTS.json', result)
    print(json.dumps({'wall_seconds': result['wall_seconds'], 'probes': [
        {'name': p['name'], 'error': p.get('probe_error'), 'eligible': p.get('result',{}).get('eligible'),
         'target_exists': p.get('target_exists'), 'exceptions': p.get('result',{}).get('exceptions')}
        for p in result['probes']], 'passed': result['passed'], 'total': len(checks)}, indent=2))
    if result['passed'] != len(checks):
        raise AssertionError('Unexpected independent probe outcome; inspect PROBE_RESULTS.json')


if __name__ == '__main__':
    main()
