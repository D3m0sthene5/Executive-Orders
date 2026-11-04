#!/usr/bin/env python3
"""Bridge a separately held NEW source review through Valla in a temporary tree.

Does not install queue records, prepare claims, or write any canonical research.
The output is a reproducible research receipt; no replacement ending is proposed.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = '600ae3018f71025b3e53dc8538b8f92e6e159b76'
TARGET = 'EO:13792'
FRESH = 'research/progress/maitland/valla-fresh-review/'
LEDGER = FRESH + 'METHOD_REVIEWS.jsonl'
EXAMINATION = FRESH + 'REVIEW.json'
EXPECTED = {LEDGER: '70aac20cd1db8c6f995a6acfa8a9347994aa58eb979198d00702451c139e22bf',
            EXAMINATION: '2d3d41e59d2b371c96200cd2cac047069fb3decbd538861fe54d25b3a4c3e312'}
QUEUE = 'research/readiness/method_reviews/maitland-fresh-eo13792.jsonl'
CLAIM_PATH = 'research/readiness/claims/claude-lambertini-s02-2026-10-20.jsonl'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_rows(raw):
    return [json.loads(x) for x in raw.decode().splitlines() if x.strip()]


def main():
    inputs = {}

    def read(path, expected=None):
        data = (REPO / path).read_bytes()
        if expected is not None and sha(data) != expected:
            raise ValueError('input changed: ' + path)
        inputs[path] = data
        return data

    for path, expected in EXPECTED.items():
        read(path, expected)
    records = parse_rows(inputs[LEDGER])
    assert len(records) == 2 and {r['instrument_id'] for r in records} == {TARGET}
    expected_pointers = {'/operative_clauses/11/first_end', '/operative_clauses/12/first_end'}
    assert {p for r in records for p in r['conclusion_pointers']} == expected_pointers
    assert all(r['replacement_first_end'] is None and r['research_only'] is True for r in records)
    for record in records:
        assert 'review_ref' not in record
        for dependency in record['dependencies']:
            if dependency['kind'] in ('file', 'rule'):
                read(dependency['key'], dependency['sha256'])
    for path in [CLAIM_PATH, 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl',
                 'jobs/valla/valla.py', 'jobs/valla/premises.json', 'jobs/claim-kit/BATCH.md',
                 'research/readiness/method_reviews/sol-valla-20261020.jsonl',
                 'research/valla/pilot-2026-10-20/METHOD_REVIEWS.jsonl',
                 'research/valla/pilot-2026-10-20/METHOD.md']:
        read(path)

    queue = [{**r, 'review_ref': {'path': LEDGER, 'file_sha256': EXPECTED[LEDGER],
                                'record_id': r['record_id']}} for r in records]
    native_paths = ['jobs/claim-kit/output/dossiers/EO_13792.json', 'jobs/claim-kit/output/SUMMARY.json']
    missing_native = [p for p in native_paths if not (REPO / p).is_file()]
    native_paths.append('jobs/claim-kit/output/INDEX.json')
    missing_native = [p for p in native_paths if not (REPO / p).is_file()]
    compiler_drift = []
    if not missing_native:
        dossier = json.loads(read(native_paths[0]))
        summary = json.loads(read(native_paths[1]))
        read(native_paths[2])
        for name, expected in summary.get('compiled_code_sha256', {}).items():
            path = (Path('jobs/claim-kit') / name).as_posix()
            actual = sha((REPO / path).read_bytes()) if (REPO / path).is_file() else None
            if actual != expected:
                compiler_drift.append({'path': path, 'compiled_sha256': expected, 'current_sha256': actual})
        source_hashes = {}

        def source_paths(value):
            if isinstance(value, dict):
                if value.get('text_path'):
                    source_hashes.setdefault(value['text_path'], set()).add(value.get('text_sha256'))
                for child in value.values():
                    source_paths(child)
            elif isinstance(value, list):
                for child in value:
                    source_paths(child)

        source_paths(dossier)
        for path, expected_hashes in source_hashes.items():
            if not (REPO / path).is_file():
                missing_native.append(path)
            else:
                raw = read(path)
                if any(h and h != sha(raw) for h in expected_hashes):
                    raise ValueError('dossier source changed: ' + path)
        lock = 'research/readiness/CLAIM_KIT_LOCK.json'
        if not (REPO / lock).is_file():
            missing_native.append(lock)
        else:
            read(lock)
        # Existing API modules and exact policy/preflight dependencies. No compiler
        # outputs or method pins are regenerated to fit these current bytes.
        for p in (REPO / 'jobs/claim-kit').glob('*.py'):
            if not p.name.startswith('test_'):
                read(p.relative_to(REPO).as_posix())
        for path in ['jobs/norton/model.py', 'jobs/clause-drafts/segment.py',
                     'jobs/later-events/later_events.py', 'jobs/claim-kit/AGENT_PROTOCOL.md',
                     'research/stage19/CLAIM_SCHEMA.md', 'research/stage19/code/claim_gate.py',
                     'research/stage15/LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json']:
            if (REPO / path).is_file():
                read(path)
    before_original = {p: sha(b) for p, b in inputs.items()}
    with tempfile.TemporaryDirectory(prefix='valla-fresh-research-') as td:
        sandbox = Path(td)
        for path, data in inputs.items():
            dest = sandbox / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        subprocess.run(['git', 'init', '-q'], cwd=sandbox, check=True)
        spec = importlib.util.spec_from_file_location('fresh_replay_valla', sandbox / 'jobs/valla/valla.py')
        valla = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(valla)
        active, _ = valla.active_claims(sandbox)
        target = active[TARGET]
        assert target['ref']['line'] == 3 and target['ref']['path'] == CLAIM_PATH
        assert all(r['claim_sha256'] == target['ref']['claim_sha256'] for r in records)
        baseline = valla.build(sandbox)
        assert baseline['claims'][TARGET]['invalidated_conclusion_pointers'] == []

        path = sandbox / QUEUE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(valla.canon(r) + '\n' for r in queue))
        current, _ = valla.active_claims(sandbox)
        good, refused = valla.confirmed_findings(sandbox, current, frozenset([TARGET]))
        assert {r['record_id'] for r in good} == {r['record_id'] for r in records}
        assert all(r['record_id'].startswith('VALLA-M-') for r in refused), refused
        updated = valla.build(sandbox)
        expected_invalidated = sorted(expected_pointers | {'/whole_order_end'})
        assert updated['claims'][TARGET]['invalidated_conclusion_pointers'] == expected_invalidated
        assert updated['summary']['examined_dependencies'] == 2
        assert updated['summary']['legal_promotions'] == updated['summary']['model_calls'] == 0
        assert baseline['claim_versions'] == updated['claim_versions']
        unrelated = sorted(set(updated['claims']) - {TARGET})
        assert all(baseline['claims'][iid] == updated['claims'][iid] for iid in unrelated)
        assert valla.conclusions(target['claim']) == valla.conclusions(current[TARGET]['claim'])
        assert valla.sha(target['claim']) == target['ref']['claim_sha256']
        holds_before = valla.file_sha(sandbox / 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl')

        mutation_results = []
        checked = sorted({d['key'] for r in records for d in r['dependencies'] if d['kind'] in ('file', 'rule')} | {LEDGER})
        for dependency in checked:
            changed_path = sandbox / dependency
            original = changed_path.read_bytes()
            changed_path.write_bytes(original + b'\n')
            accepted, rejected = valla.confirmed_findings(sandbox, current, frozenset([TARGET]))
            fresh_rejected = [r for r in rejected if r['record_id'] in {x['record_id'] for x in records}]
            assert not accepted and len(fresh_rejected) == 2, (dependency, accepted, fresh_rejected)
            changed_index = valla.build(sandbox)
            assert changed_index['claims'][TARGET]['invalidated_conclusion_pointers'] == []
            assert all(changed_index['claims'][iid] == baseline['claims'][iid] for iid in unrelated)
            mutation_results.append({'changed_path': dependency, 'accepted_fresh_records': len(accepted),
                                     'fresh_records_refused': fresh_rejected,
                                     'conclusions_automatically_changed': False})
            changed_path.write_bytes(original)
        assert valla.file_sha(sandbox / 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl') == holds_before
        assert valla.build(sandbox)['fingerprint'] == updated['fingerprint']

        preparation = {'state': 'blocked_missing_native_input', 'missing_paths': sorted(set(missing_native)),
                       'explanation': 'No source, dossier, lock or compiler pin was fabricated or renewed.',
                       'compiled_generation_current_runtime_drift': compiler_drift}
        if not missing_native:
            dest = sandbox / 'research/progress/maitland/valla-audit/correction-packet-v1'
            try:
                result = valla.correction(sandbox, sandbox / 'jobs/claim-kit/output', [TARGET],
                                          dest, 'codex-maitland-valla-research')
                import batch
                packet, dossiers = batch.load_packet(dest, sandbox)
                decisions = batch.rows(dest / 'decisions.csv')
                assert all(r['approved'] == 'false' and r['outcome'] == 'unresolved' for r in decisions)
                ctx = packet['valla_context']
                assert ctx['claims'][TARGET]['invalidated_conclusion_pointers'] == expected_invalidated
                assert sum(q.get('dependency_confirmed') is True for q in ctx['review_queue']) == 2
                assert ctx['automatic_approvals'] == 0 and ctx['whole_case_review_required']
                freshness = []
                for dependency in ['jobs/fr-originals/data/full_run/texts/EO_13792.txt', LEDGER]:
                    p = sandbox / dependency
                    original = p.read_bytes()
                    p.write_bytes(original + b'\n')
                    try:
                        batch.load_packet(dest, sandbox)
                    except (ValueError, OSError) as exc:
                        freshness.append({'changed_path': dependency, 'refused': True, 'reason': str(exc)})
                    else:
                        raise AssertionError('changed source/review did not stale correction packet: ' + dependency)
                    finally:
                        p.write_bytes(original)
                assert batch.load_packet(dest, sandbox)[0] == packet
                retained = OUT / 'correction-packet-v1'
                if retained.exists():
                    shutil.rmtree(retained)
                shutil.copytree(dest, retained)
                preparation = {'state': 'native_research_packet_prepared_and_reloaded', 'api_result': result,
                               'packet_fingerprint': packet['fingerprint'],
                               'packet_sha256': sha((dest / 'PACKET.json').read_bytes()),
                               'dossier_fingerprint': dossiers[TARGET]['fingerprint'],
                               'all_decision_approvals_false': True, 'all_decision_outcomes_unresolved': True,
                               'packet_freshness_probes': freshness,
                               'compiled_generation_current_runtime_drift': compiler_drift,
                               'scope': 'Exact selected dossier/index and held source bytes in a bounded disposable tree. Current API prepared and reloaded the packet; compiler SUMMARY pins are preserved, with drift disclosed. Not production-tree freshness or a complete lifecycle result.',
                               'retained_path': 'research/progress/maitland/valla-audit/correction-packet-v1',
                               'packet_files': [{'path': p.name, 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size}
                                                for p in sorted(dest.iterdir()) if p.is_file()]}
            except Exception as exc:
                preparation = {'state': 'native_preparation_refused', 'reason': str(exc),
                               'compiled_generation_current_runtime_drift': compiler_drift,
                               'failed_attempt_retained': True, 'pins_renewed': False}
                if dest.exists():
                    retained = OUT / 'correction-failed-v1'
                    if retained.exists():
                        shutil.rmtree(retained)
                    shutil.copytree(dest, retained)

        all_conclusions = valla.conclusions(target['claim'])
        receipt = {
            'schema': 'maitland-fresh-valla-replay/v1', 'base_commit': BASE,
            'runtime_valla_sha256': sha(inputs['jobs/valla/valla.py']),
            'claim_ref': target['ref'], 'new_method_records': [r['record_id'] for r in good],
            'new_method_review_count': len(good),
            'accepted_conclusion_pointers': sorted(expected_pointers),
            'existing_runtime_closure': expected_invalidated,
            'unrelated_target_conclusion_pointers_not_invalidated': sorted(set(all_conclusions) - set(expected_invalidated)),
            'unchanged_other_frozen_claims': unrelated,
            'frozen_claim_scope_notice': 'Other claims are unchanged frozen siblings in the held claim file; no assertion that each remains the latest canonical version.',
            'baseline_summary': baseline['summary'], 'updated_summary': updated['summary'],
            'refused_older_method_reviews': refused,
            'mutation_probes': mutation_results,
            'source_examination_record': {'path': EXAMINATION, 'sha256': EXPECTED[EXAMINATION]},
            'exposure_disclosure': json.loads(inputs[EXAMINATION])['scope']['other_agent_conclusions_exposure'],
            'queue_copy': {'temporary_path': QUEUE, 'canonical_write_performed': False,
                           'separately_held_ledger': LEDGER, 'ledger_sha256': EXPECTED[LEDGER]},
            'correction_preparation': preparation,
            'claims_changed': 0, 'holds_changed': 0, 'production_jobs_launched': 0,
            'replacement_claims_created': 0, 'replacement_first_end_adopted': None,
            'independent_human_certifications': 0,
            'pins': [{'path': p, 'sha256': sha(b), 'bytes': len(b)} for p, b in sorted(inputs.items())],
        }
    assert all(sha((REPO / p).read_bytes()) == digest for p, digest in before_original.items()), 'original input changed during replay'
    (OUT / 'FRESH_QUEUE_PROPOSALS.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in queue))
    (OUT / 'FRESH_REPLAY.json').write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['new_method_review_count', 'existing_runtime_closure',
                                           'claims_changed', 'holds_changed', 'correction_preparation']}))


if __name__ == '__main__':
    main()
