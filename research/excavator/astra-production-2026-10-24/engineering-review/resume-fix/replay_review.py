"""Narrow independent replay of the time_utc normalization repair.

The real EO4314 receipts are treated only as fingerprint inputs. This script
does not review their substantive historical or legal assertions.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
DATA = ROOT / 'research/excavator/astra-production-2026-10-24/difficult'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def main():
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    engine = ROOT / 'jobs/claim-kit/lifecycle_obligations.py'
    test = ROOT / 'jobs/claim-kit/test_lifecycle_obligations.py'
    spec = importlib.util.spec_from_file_location('independently_reviewed_resume', engine)
    new = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(new)
    old_source = subprocess.check_output(['git', 'show', 'HEAD:jobs/claim-kit/lifecycle_obligations.py'], cwd=ROOT)
    old = types.ModuleType('historical_resume_engine')
    exec(compile(old_source, '<read-only HEAD lifecycle_obligations.py>', 'exec'), old.__dict__)
    author = read(DATA / 'review/time_utc_fix/REPLAY.json')
    protected = {p: sha(p) for p in (DATA / 'review/v1').rglob('*') if p.is_file()}
    protected.update({ROOT / rel: sha(ROOT / rel) for rel in author['input_pins']})
    pins_match = all(sha(ROOT / rel) == digest for rel, digest in author['input_pins'].items())
    dossier = read(DATA / 'EO_4314_PRIOR_DOSSIER.json')
    requests = read(DATA / 'EO_4314_UNRESOLVED_REQUESTS.json')
    prior = read(DATA / 'EO_4314_PRIOR_ATTEMPTS.json')
    current = read(DATA / 'EO_4314_CURRENT_RECEIPTS.json')
    context = read(DATA / 'EO_4314_PRIOR_RESEARCH_CONTEXT.json')
    checkpoint = read(DATA / 'EO_4314_RECONSTRUCTED_PRIOR_CHECKPOINT.json')
    route = checkpoint['route_fingerprint']
    retry = deepcopy(prior)
    retry[0]['time_utc'] = author['only_receipt_change']['after']
    historical = read(DATA / 'review/v1/CHECKS.json')
    normalized = new.blocked_checkpoint(dossier, requests, route, checkpoint['reason'],
                                        checkpoint['result_paths'], prior, context)
    replays = {
        'old_engine_timestamp_only': old.resume_decision(checkpoint, dossier, requests, route, retry, context),
        'new_engine_unmigrated_checkpoint': new.resume_decision(checkpoint, dossier, requests, route, prior, context),
        'new_engine_unchanged_failure': new.resume_decision(normalized, dossier, requests, route, prior, context),
        'new_engine_timestamp_only': new.resume_decision(normalized, dossier, requests, route, retry, context),
        'new_engine_new_source': new.resume_decision(normalized, dossier, requests, route, prior + current, context),
    }
    checks = {
        'author_input_pins_match': pins_match,
        'old_engine_matches_original_failed_probe_pin': hashlib.sha256(old_source).hexdigest() == historical['retry_timestamp_contract_probe']['engine_sha256'],
        'old_real_failure_reproduced': replays['old_engine_timestamp_only'] == historical['resume_replays']['same_failure_time_utc_only'],
        'new_normalized_checkpoint_exact': normalized == read(DATA / 'review/time_utc_fix/NORMALIZED_CHECKPOINT.json'),
        'old_checkpoint_is_not_silently_migrated': replays['new_engine_unmigrated_checkpoint']['action'] == 'reopen',
        'unchanged_failure_defers': replays['new_engine_unchanged_failure']['action'] == 'defer_unchanged_source_block',
        'timestamp_only_defers': replays['new_engine_timestamp_only']['action'] == 'defer_unchanged_source_block',
        'new_meaningful_receipt_reopens': replays['new_engine_new_source']['action'] == 'reopen',
        'original_attempt_timestamp_preserved': prior[0]['time_utc'] == author['only_receipt_change']['before'],
        'original_result_paths_preserved': normalized['result_paths'] == checkpoint['result_paths'],
        'recorded_normalized_replays_exact': all(replays[key] == author['replays'][label] for key, label in (
            ('new_engine_unchanged_failure', 'unchanged_failure'),
            ('new_engine_timestamp_only', 'same_failure_time_utc_only'),
            ('new_engine_new_source', 'new_source_receipt'))),
    }
    for key, value in [('status', 200), ('error', 'different substantive failure'), ('sha256', 'b' * 64)]:
        changed = deepcopy(retry)
        changed[0][key] = value
        result = new.resume_decision(normalized, dossier, requests, route, changed, context)
        replays['changed_' + key] = result
        checks['changed_' + key + '_reopens'] = result['action'] == 'reopen'
    checks['protected_original_bytes_unchanged'] = all(sha(path) == digest for path, digest in protected.items())
    unit = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'test_lifecycle_obligations'],
        cwd=ROOT / 'jobs/claim-kit', capture_output=True, text=True)
    (OUT / 'UNIT_TESTS.log').write_text(unit.stdout + unit.stderr)
    checks['eight_lifecycle_tests_pass'] = unit.returncode == 0 and 'Ran 8 tests' in unit.stderr
    result = {'schema': 'eo-independent-resume-fix-review/v1', 'scope': 'time_utc receipt normalization only',
        'independence': 'separate same-family engineering context', 'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(), 'monotonic_seconds': time.monotonic() - clock,
        'reviewed_sha256': {'jobs/claim-kit/lifecycle_obligations.py': sha(engine),
                           'jobs/claim-kit/test_lifecycle_obligations.py': sha(test)},
        'old_engine_sha256': hashlib.sha256(old_source).hexdigest(),
        'input_sha256': {p.relative_to(ROOT).as_posix(): digest for p, digest in protected.items()},
        'checks': checks, 'passed': sum(checks.values()), 'total': len(checks), 'replays': replays,
        'decision': 'approved' if all(checks.values()) else 'blocked', 'blocking_findings': [],
        'actual_model_tokens': None, 'cached_model_tokens': None, 'model_cost': None,
        'aggregate_active_agent_seconds': None, 'legal_conclusion': None}
    with (OUT / 'REVIEW.json').open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({key: result[key] for key in ('decision', 'passed', 'total', 'monotonic_seconds', 'reviewed_sha256')}, indent=2))
    if not all(checks.values()):
        raise AssertionError([key for key, passed in checks.items() if not passed])


if __name__ == '__main__':
    main()
