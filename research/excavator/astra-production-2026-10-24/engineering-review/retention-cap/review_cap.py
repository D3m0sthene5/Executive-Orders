"""Independent actual-size runner probe; all generated data stays temporary."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import test_result_freshness as T

PIN_PATHS = ['.github/scripts/run_jobs.py', '.github/scripts/test_result_freshness.py',
             '.github/scripts/result_freshness.py', 'jobs/astra-source-retention/MAX_OUTPUT_FILE_BYTES',
             'jobs/astra-source-retention/README.md', 'jobs/README.md']
PDF = ROOT / 'jobs/astra-source-retention/output/pdf/aacf815d01c9c3d797d7c516d9ccddd1f723dc1a44e47f8899ba742d988e2127.pdf'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    started = datetime.now(timezone.utc).isoformat()
    timer = time.monotonic()
    pins = {p: sha(ROOT / p) for p in PIN_PATHS}
    original_pdf = sha(PDF)
    checks = {'exact_held_pdf_bytes': PDF.stat().st_size == 104612053 and original_pdf == PDF.stem,
              'default_95_mib_unchanged': T.run_jobs.LIMIT == 99614720,
              'only_retention_opts_in': [p.parent.name for p in (ROOT / 'jobs').glob('*/MAX_OUTPUT_FILE_BYTES')] == ['astra-source-retention'],
              'configured_cap_strictly_below_100_mib': T.run_jobs.output_file_limit(ROOT / 'jobs/astra-source-retention') == 104857599}
    fixture = T.FreshnessTests('test_output_cap_is_per_job_keeps_boundary_and_moves_oversized_bytes')
    fixture.setUp()
    try:
        os.link(PDF, fixture.repo / 'inputs/held.pdf')
        fixture.put('jobs/source/MAX_OUTPUT_FILE_BYTES', '104857599\n')
        producer = """import os
from pathlib import Path
out = Path(os.environ['OUTPUT_DIR'])
os.link(Path(os.environ['REPO_ROOT']) / 'inputs/held.pdf', out / 'retained.pdf')
for name, size in [('at-limit.bin', 104857599), ('over-limit.bin', 104857600)]:
    with (out / name).open('wb') as stream:
        stream.truncate(size)
"""
        fixture.put('jobs/source/job.py', producer)
        fixture.put('jobs/other/job.py', producer)
        run = fixture.shell('run_jobs.sh', 'source other')
        (OUT / 'ACTUAL_SIZE_RUN.log').write_text(run.stdout + run.stderr)
        source = fixture.repo / 'jobs/source/output'
        other = fixture.repo / 'jobs/other/output'
        status = json.loads((source / 'STATUS.json').read_text())
        default_status = json.loads((other / 'STATUS.json').read_text())
        manifest = json.loads((source / T.freshness.MANIFEST).read_text())
        checks.update({
            'actual_runner_success': run.returncode == 0,
            'actual_pdf_retained_byte_identical': sha(source / 'retained.pdf') == original_pdf,
            'exact_cap_file_retained': (source / 'at-limit.bin').stat().st_size == 104857599,
            'cap_plus_one_relocated': not (source / 'over-limit.bin').exists() and (fixture.repo / 'oversized/source/over-limit.bin').stat().st_size == 104857600,
            'opted_in_status_exact': status['max_output_file_bytes'] == 104857599 and status['oversized_files_moved_to_run_download'] == ['over-limit.bin'],
            'default_actual_pdf_relocated_byte_identical': not (other / 'retained.pdf').exists() and sha(fixture.repo / 'oversized/other/retained.pdf') == original_pdf,
            'default_status_exact': default_status['max_output_file_bytes'] == 99614720 and set(default_status['oversized_files_moved_to_run_download']) == {'retained.pdf', 'at-limit.bin', 'over-limit.bin'},
            'cap_config_captured': 'jobs/source/MAX_OUTPUT_FILE_BYTES' in manifest['inputs'],
            'runner_source_captured': '.github/scripts/run_jobs.py' in manifest['inputs'],
            'job_source_captured': 'jobs/source/job.py' in manifest['inputs'],
            'declared_actual_source_captured': 'inputs/held.pdf' in manifest['inputs'],
        })
        captured = manifest['inputs']
        fixture.put('jobs/source/MAX_OUTPUT_FILE_BYTES', '104857598\n')
        changed = T.freshness.working(T.freshness.scope('source'))
        checks['cap_change_changes_exact_freshness_input'] = changed['jobs/source/MAX_OUTPUT_FILE_BYTES'] != captured['jobs/source/MAX_OUTPUT_FILE_BYTES']
        fixture.put('jobs/source/MAX_OUTPUT_FILE_BYTES', '104857599\n')
        fixture.put('inputs/request.json', 'changed declared source input\n')
        changed = T.freshness.working(T.freshness.scope('source'))
        checks['source_change_changes_exact_freshness_input'] = changed['inputs/request.json'] != captured['inputs/request.json']
        (OUT / 'ACTUAL_SIZE_STATUS.json').write_text(json.dumps({'opted_in': status, 'default': default_status}, indent=2) + '\n')
        (OUT / 'CAPTURED_INPUTS.json').write_text(json.dumps(manifest, indent=2) + '\n')
    finally:
        fixture.doCleanups()
    invalid = T.FreshnessTests('test_unsafe_output_cap_fails_before_generation_and_preserves_previous_output')
    invalid.setUp()
    try:
        before = {p.relative_to(invalid.repo / 'jobs/source/output').as_posix(): sha(p) for p in (invalid.repo / 'jobs/source/output').rglob('*') if p.is_file()}
        invalid.put('jobs/source/MAX_OUTPUT_FILE_BYTES', '104857600\n')
        invalid.put('jobs/source/job.py', "from pathlib import Path\nPath('PRODUCER_RAN').write_text('must not execute')\n")
        run = invalid.shell('run_jobs.sh', 'source consumer')
        (OUT / 'INVALID_CONFIG_RUN.log').write_text(run.stdout + run.stderr)
        after = {p.relative_to(invalid.repo / 'jobs/source/output').as_posix(): sha(p) for p in (invalid.repo / 'jobs/source/output').rglob('*') if p.is_file()}
        records = json.loads((invalid.repo / 'oversized/runner-freshness/ATTEMPTS.json').read_text())
        checks.update({'invalid_config_fails': run.returncode != 0,
                       'invalid_config_never_executes_producer': not (invalid.repo / 'PRODUCER_RAN').exists(),
                       'invalid_config_preserves_all_prior_output_bytes': before == after,
                       'invalid_config_blocks_dependent_publication': [r['publish_output'] for r in records] == [False, False]})
        (OUT / 'INVALID_CONFIG_ATTEMPTS.json').write_text(json.dumps(records, indent=2) + '\n')
    finally:
        invalid.doCleanups()
    unit = subprocess.run([sys.executable, '-B', '-m', 'unittest',
        'test_result_freshness.OutputFileLimitTests',
        'test_result_freshness.FreshnessTests.test_output_cap_is_per_job_keeps_boundary_and_moves_oversized_bytes',
        'test_result_freshness.FreshnessTests.test_unsafe_output_cap_fails_before_generation_and_preserves_previous_output'],
        cwd=ROOT / '.github/scripts', capture_output=True, text=True)
    (OUT / 'FOCUSED_TESTS.log').write_text(unit.stdout + unit.stderr)
    checks['four_focused_tests_pass'] = unit.returncode == 0 and 'Ran 4 tests' in unit.stderr
    checks['reviewed_code_unchanged'] = all(sha(ROOT / p) == digest for p, digest in pins.items())
    checks['held_pdf_unchanged'] = sha(PDF) == original_pdf
    result = {'schema': 'eo-independent-retention-cap-review/v1', 'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(), 'monotonic_seconds': time.monotonic() - timer,
        'reviewed_sha256': pins, 'held_pdf': {'path': PDF.relative_to(ROOT).as_posix(), 'bytes': PDF.stat().st_size, 'sha256': original_pdf},
        'checks': checks, 'passed': sum(checks.values()), 'total': len(checks),
        'decision': 'approved' if all(checks.values()) else 'blocked', 'blocking_findings': [],
        'actual_model_tokens': None, 'cached_model_tokens': None, 'model_cost': None,
        'aggregate_active_agent_seconds': None, 'network_requests': 0,
        'scope': 'Existing runner cap, boundary relocation, invalid-config transaction and input capture only; no remote retention run.'}
    with (OUT / 'REVIEW.json').open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ('decision', 'passed', 'total', 'monotonic_seconds')}, indent=2))
    if not all(checks.values()):
        raise AssertionError([k for k, passed in checks.items() if not passed])


if __name__ == '__main__':
    main()
