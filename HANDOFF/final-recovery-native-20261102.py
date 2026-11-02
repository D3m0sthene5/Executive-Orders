"""Read-only audit of the published final recovery generation from Git objects."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import posixpath
import subprocess
import types

BASE = 'aeafe6ef3b5d53d38d34b6fec7fc25fb8851efd0'
RUN = 'https://github.com/D3m0sthene5/Executive-Orders/actions/runs/41504614771'
JOBS = ['claim-checker', 'claim-drafts', 'claim-kit', 'kean', 'readiness-tracker']

def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout

def raw(ref, path):
    return git('show', f'{ref}:{path}')

def read(ref, path):
    return json.loads(raw(ref, path))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('published')
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    f = types.ModuleType('freshness')
    f.__file__ = '.github/scripts/result_freshness.py'
    protocol = raw(BASE, f.__file__)
    exec(compile(protocol, f.__file__, 'exec'), f.__dict__)
    pub = git('rev-parse', args.published).decode().strip()
    git('merge-base', '--is-ancestor', BASE, pub)
    base, current = f.tree(BASE), f.tree(pub)
    evidence = {'schema': 'eo-final-recovery-native-audit/v1', 'base_commit': BASE,
                'published_commit': pub, 'run_url': RUN,
                'audit_protocol_sha256': hashlib.sha256(protocol).hexdigest(),
                'jobs': {}, 'problems': []}
    problems = evidence['problems']
    for position, name in enumerate(JOBS):
        folder = f'jobs/{name}/output/'
        status = read(pub, folder + 'STATUS.json')
        m = read(pub, folder + 'RUNNER_INPUTS.json')
        if not (status['result'] == 'succeeded' and status['exit_code'] == 0
                and status['commit_run'] == BASE and status['run_url'] == RUN):
            problems.append({'job': name, 'reason': 'wrong_or_failed_status', 'status': status})
        if not (m['schema'] == 1 and m['job'] == name and m['base_commit'] == BASE
                and m['run_url'] == RUN and f.digest(m['inputs']) == m['inputs_sha256']
                and f.digest(f.output(base, name)) == m['base_output_sha256']):
            problems.append({'job': name, 'reason': 'invalid_manifest'})
        projected = dict(current)
        generations = {}
        for j, producer in enumerate(JOBS):
            baseline = f.output(base, producer)
            produced = f.output(current, producer)
            captured = f.output(m['inputs'], producer)
            chosen = produced if j < position else baseline
            if not (captured or f.select(chosen, m['scope'])):
                continue
            # Earlier consumers necessarily captured later producer baselines.
            generation = 'same_run_candidate' if j < position else 'captured_base'
            if captured != f.select(chosen, m['scope']):
                problems.append({'job': name, 'producer': producer, 'reason': 'wrong_input_generation'})
            generations[producer] = generation
            projected = {p: v for p, v in projected.items()
                         if not f.under(p, f'jobs/{producer}/output')}
            projected.update(chosen)
        actual = f.select(projected, m['scope'])
        differences = sorted(p for p in actual.keys() | m['inputs'].keys()
                             if actual.get(p) != m['inputs'].get(p))
        if differences:
            problems.append({'job': name, 'reason': 'captured_input_mismatch',
                             'count': len(differences), 'paths': differences[:50]})
        evidence['jobs'][name] = {'status': status, 'captured_input_count': len(m['inputs']),
            'inputs_sha256': m['inputs_sha256'], 'independently_projected_sha256': f.digest(actual),
            'input_generations': generations,
            'status_sha256': hashlib.sha256(raw(pub, folder + 'STATUS.json')).hexdigest(),
            'manifest_sha256': hashlib.sha256(raw(pub, folder + 'RUNNER_INPUTS.json')).hexdigest()}
    pins = read(pub, 'research/progress/lachmann-verified-text-reuse/RECOVERY_AUTHORITY_BOUNDARY.json')
    original = f.tree(pins['baseline'])
    scientific = {p for p in original.keys() | current.keys()
                  if any(f.under(p, scope) for scope in pins['scientific_path_scopes'])}
    changed = sorted(p for p in scientific if original.get(p) != current.get(p))
    evidence['authority_boundary'] = {'baseline': pins['baseline'],
                                    'path_count': len(scientific), 'changed_paths': changed,
                                    'claims_published_by_recovery': 0, 'statuses_adopted_by_recovery': 0,
                                    'human_certifications_by_recovery': 0}
    if changed:
        problems.append({'reason': 'scientific_paths_changed', 'paths': changed})
    summaries = {name: read(pub, f'jobs/{name}/output/SUMMARY.json') for name in JOBS}
    evidence['native_summaries'] = summaries
    if summaries['claim-kit'].get('input_commit') != BASE:
        problems.append({'reason': 'compiler_summary_input_commit_mismatch'})
    population = read(pub, 'jobs/claim-kit/output/POPULATION_VALIDATION.json')
    evidence['native_population_validation'] = population
    index = read(pub, 'jobs/claim-kit/output/INDEX.json')
    evidence['index_type'] = type(index).__name__
    evidence['index_count'] = len(index)
    decided_path = 'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv'
    rows = list(csv.DictReader(io.StringIO(raw(pub, decided_path).decode('utf-8-sig'))))
    statuses = {r['instrument_id']: r['provisional_substantive_status'] for r in rows}
    compiled = {r['instrument_id']: r['status'] for r in index}
    certified = [r['instrument_id'] for r in rows
                 if r.get('human_certified_by_this_release', '').lower() not in ('', 'no', 'false', '0')]
    evidence['independent_population_comparison'] = {
        'canonical_rows': len(rows), 'canonical_unique_ids': len(statuses),
        'index_rows': len(index), 'index_unique_ids': len(compiled),
        'exact_status_map_match': compiled == statuses, 'human_certified_rows': certified}
    if not (len(rows) == len(statuses) == len(index) == len(compiled) == 4291
            and compiled == statuses and not certified
            and population['universe'] == 14972 and population['decided'] == 4291
            and population['historical_decided'] + population['authorized_additions'] == 4291):
        problems.append({'reason': 'independent_population_comparison_failed'})
    code_pins = summaries['claim-kit']['compiled_code_sha256']
    changed_code = [p for p, digest in code_pins.items()
                    if hashlib.sha256(raw(pub, posixpath.normpath('jobs/claim-kit/' + p))).hexdigest() != digest]
    evidence['compiler_code_pins'] = {'count': len(code_pins), 'mismatches': changed_code}
    if changed_code:
        problems.append({'reason': 'native_compiler_code_pin_mismatch', 'paths': changed_code})
    # Store a precise native sample; this does not claim full dossier revalidation.
    dossier = read(pub, 'jobs/claim-kit/output/dossiers/EO_1079.json')
    evidence['native_EO1079_working_text_confirmation'] = dossier.get('working_text_confirmation')
    evidence['native_EO1079_top_level_keys'] = sorted(dossier)
    prior = dossier.get('working_text_confirmation')
    effective = None
    for path in ('jobs/lachmann/output/CONFIRMATIONS.jsonl',
                 'jobs/lachmann/output/AGENT_CONFIRMATIONS.jsonl'):
        if path not in current:
            continue
        for line in raw(pub, path).splitlines():
            if line.strip():
                record = json.loads(line)
                if record.get('instrument_id') == 'EO:1079':
                    effective = {'source_path': path, 'record': record}
    exact = bool(prior and effective and prior['source_path'] == effective['source_path']
                 and prior['record'] == effective['record'])
    text_hash = hashlib.sha256(raw(pub, effective['record']['text_path'])).hexdigest() if effective else None
    record_hash = effective['record']['text_sha256'] if effective else None
    selected_evidence = dossier['evidence'][dossier['original_source_id']]
    selected_source = selected_evidence.get('source', selected_evidence)
    selected_pins_match = bool(effective and all(
        selected_source.get(key) == effective['record'].get(key)
        for key in ('instrument_id', 'grade', 'sha256', 'text_sha256', 'text_path', 'acceptable_as_original')))
    evidence['EO1079_independent_confirmation_comparison'] = {
        'exact_current_last_wins_record': exact, 'actual_held_text_sha256': text_hash,
        'record_text_sha256': record_hash,
        'selected_source_pins_match': selected_pins_match,
        'acceptable_as_original': effective['record']['acceptable_as_original'] if effective else None}
    if not exact or not selected_pins_match or text_hash != record_hash or effective['record']['acceptable_as_original'] is not False:
        problems.append({'reason': 'native_EO1079_confirmation_not_exact'})
    checker_path = 'jobs/claim-checker/output/PER_CLAIM.json'
    tracker = read(pub, 'jobs/readiness-tracker/output/RUNNER_INPUTS.json')
    evidence['tracker_same_run_checker_blob'] = {
        'captured': tracker['inputs'].get(checker_path), 'published': current.get(checker_path)}
    if tracker['inputs'].get(checker_path) != current.get(checker_path):
        problems.append({'reason': 'tracker_checker_not_same_run'})
    evidence['limitations'] = [
        'Git object/input-generation audit, native population validation and one compiler sample; not a second full scientific review.',
        'Five retained PDFs still require actual page examination; no PNGs were produced and three page texts were empty.',
        'EO11029 names EO11025; application to EO11026 is unexamined.',
        'No total research time, token, cost or legal-review savings are inferred.',
        'Live dashboard remains its dated 498-ready snapshot; archive integration did not republish it.'
    ]
    evidence['result'] = 'passed' if not problems else 'failed'
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'result': evidence['result'], 'published': pub,
                      'jobs': {k: {'status': v['status']['result'], 'inputs': v['captured_input_count']}
                               for k, v in evidence['jobs'].items()},
                      'index_count': len(index), 'problems': problems}, indent=2))
    return bool(problems)

if __name__ == '__main__':
    raise SystemExit(main())
