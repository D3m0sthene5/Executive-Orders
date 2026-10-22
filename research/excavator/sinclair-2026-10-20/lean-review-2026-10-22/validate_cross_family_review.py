#!/usr/bin/env python3
"""Offline custody/adoption checks; does not automate the substantive verdicts.

Run from any directory in a checkout containing the pinned held inputs.
Use --write to refresh the adjacent validation receipt after a successful check.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / '.git').exists())
REL = HERE.relative_to(ROOT)
LEDGER = Path('research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False).encode('utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(record):
    require(sha((ROOT / record['path']).read_bytes()) == record['sha256'],
            'Pin mismatch: ' + record['path'])


def rows(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf-8'))))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def validate():
    review = read(REL / 'CROSS_FAMILY_REVIEW.json')
    pending = read(REL / 'PENDING_CROSS_FAMILY_REVIEW.json')
    inputs = read(REL / 'CROSS_FAMILY_INPUTS.json')
    controls = read(REL / 'CROSS_FAMILY_CONTROLS.json')
    base = review['base_commit']
    require(inputs['base_commit'] == controls['base_commit'] == base, 'Base mismatch')
    for item in [review['ruling'], review['pending_input'], review['historical_review']]:
        pin(item)
    for item in inputs['sources']:
        pin(item)
        require((ROOT / item['path']).read_bytes() == git('show', base + ':' + item['path']),
                'Held source changed from baseline: ' + item['path'])
    proposals = {p['instrument_id']: p for p in pending['proposals']}
    verdicts = {v['instrument_id']: v for v in review['verdicts']}
    require(len(proposals) == len(verdicts) == len(review['verdicts']) == 31, 'Coverage count')
    require(proposals.keys() == verdicts.keys(), 'Coverage identities')
    upheld = {k for k, v in verdicts.items() if v['verdict'] == 'uphold'}
    unresolved = {k for k, v in verdicts.items() if v['verdict'] == 'needs_research'}
    require(len(upheld) == 29 and unresolved == {'EO:9380', 'EO:9593'}, 'Disposition mismatch')
    holds = pending['existing_six_holds']
    pin(holds)
    require(not set(holds['instrument_ids']) & verdicts.keys(), 'Excluded hold reviewed')
    require(set(review['fixed_checklist']) == {f'q{i}' for i in range(1, 8)}, 'Checklist')
    for iid, verdict in verdicts.items():
        proposal = proposals[iid]
        require(sha(proposal['original_csv_record_utf8'].encode('utf-8')) ==
                verdict['pending_proposal_record_sha256'] == proposal['original_csv_record_sha256'],
                'Pending row pin: ' + iid)
        require(set(verdict['checklist']) == set(review['fixed_checklist']), 'Checklist coverage')
        for item in verdict['input_files'] + verdict['sources']:
            pin(item)
            require((ROOT / item['path']).read_bytes() == git('show', base + ':' + item['path']),
                    'Producer/source changed: ' + item['path'])
        files = {Path(p['path']).name: read(p['path']) for p in verdict['input_files']}
        ev, dec, prop = (files[n] for n in ('EVIDENCE.json', 'STATUS_DECISION.json', 'PROMOTION_PROPOSAL.json'))
        fingerprint = canonical({k: v for k, v in ev.items() if k != 'fingerprint'})
        require(fingerprint == ev['fingerprint'] == dec['evidence_sha256'] ==
                verdict['evidence_canonical_fingerprint'], 'Evidence fingerprint: ' + iid)
        require(canonical(dec) == prop['decision_sha256'], 'Decision fingerprint: ' + iid)
        require(dec['instrument_id'] == prop['instrument_id'] == iid, 'Producer identity')
        require(dec['recommended_provisional_status'] == prop['recommended_provisional_status'] == 'no',
                'Producer status')
        for source in verdict['sources']:
            require(ev['source_fingerprints'][source['path']] == source['sha256'], 'Producer source pin')
        text = (ROOT / proposal['original_review_source_file']).read_text(encoding='utf-8')
        require(bool(verdict['held_basis_spans']), 'Missing basis span: ' + iid)
        for span in verdict['held_basis_spans']:
            require(0 <= span['char_start'] < span['char_end'] <= len(text) and
                    text[span['char_start']:span['char_end']] == span['text'], 'Basis span: ' + iid)
        require(verdict['checklist']['q5']['answer'].startswith('performed'), 'D6 missing')
        require(verdict['checklist']['q6']['first_cessation_certified'] is False, 'Certification drift')
    counts = controls['counts']
    require((counts['items_reviewed'], counts['planted_controls'], counts['strict_caught'],
             counts['lenient_caught'], counts['genuine_controls'], counts['genuine_accepted'],
             counts['genuine_flagged'], counts['missing_verdicts']) == (9, 3, 3, 3, 6, 6, 0, 0),
            'Control score mismatch')
    require(all(controls['checks'].values()), 'Control custody failure')
    for item in controls['strict_correspondence']:
        pin({'path': item['held_source'], 'sha256': item['source_sha256']})
    baseline = git('show', base + ':' + str(LEDGER))
    current = (ROOT / LEDGER).read_bytes()
    require(current.startswith(baseline), 'Existing CSV bytes changed')
    old, new = rows(baseline), rows(current)
    adoption = rows((HERE / 'CROSS_FAMILY_ADOPTION_ROWS.csv').read_bytes())
    require(len(old) == 3374 and len(new) == 3403, 'Ledger counts')
    require(new[:len(old)] == old and new[len(old):] == adoption, 'Append mismatch')
    require(len({r['instrument_id'] for r in new}) == len(new), 'Duplicate instrument')
    require(len(adoption) == 29 and {r['instrument_id'] for r in adoption} == upheld, 'Adoption identities')
    for row in adoption:
        original = proposals[row['instrument_id']]['original_proposal_row']
        changed = {k for k in original if original[k] != row[k]}
        require(changed == {'decision_origin', 'audit_next_step'}, 'Unexpected row change')
        require('CROSS_FAMILY_REVIEW.json' in row['decision_origin'], 'Review provenance missing')
        require(row['provisional_substantive_status'] == 'no' and
                row['whole_order_first_cessation_verified_by_this_audit'] == 'no' and
                row['human_certified_by_this_release'] == 'no', 'Scope widened')
    require(sum(r['human_certified_by_this_release'] == 'yes' for r in new) ==
            sum(r['human_certified_by_this_release'] == 'yes' for r in old) == 0, 'Certified count changed')
    names = {'CROSS_FAMILY_REVIEW.json', 'CROSS_FAMILY_INPUTS.json', 'CROSS_FAMILY_CONTROLS.json',
             'CROSS_FAMILY_ADOPTION_ROWS.csv', 'CROSS_FAMILY_REPORT.md', 'CROSS_FAMILY_VALIDATION.json',
             'validate_cross_family_review.py'}
    allowed = {str(REL / name) for name in names} | {str(LEDGER), 'HANDOFF/notes-codex.md'}
    changed = set(git('diff', '--name-only', base).decode().splitlines())
    changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    require(changed <= allowed, 'Unexpected changed files: ' + str(sorted(changed - allowed)))
    for name in ('PENDING_CROSS_FAMILY_REVIEW.json', 'HELD_PROPOSALS.json', 'LEAN_REVIEW.json',
                 'PLANT_SCORE.json', 'ADOPTION_ROWS.csv', 'REPORT.md'):
        path = REL / name
        require((ROOT / path).read_bytes() == git('show', base + ':' + str(path)), 'Historical edit: ' + name)
    git('diff', '--check', base)
    return {'schema': 'sinclair-cross-family-validation/v1', 'base_commit': base, 'result': 'pass',
            'reviewed': 31, 'upheld_and_appended': 29, 'unresolved': sorted(unresolved),
            'excluded_holds_unchanged': holds['instrument_ids'], 'held_source_pins': len(inputs['sources']),
            'baseline_rows': len(old), 'proposed_rows': len(new), 'baseline_bytes_preserved': True,
            'human_certified_count': 0, 'controls_strict_caught': 3, 'controls_genuine_accepted': 6,
            'scope': 'Offline custody, exact coverage, frozen source pins, quote offsets, canonical producer fingerprints, append-only adoption, historical preservation and changed-file allowlist. Substantive verdicts remain manual; aggregate control audit is checked, not independently re-scored here.'}


if __name__ == '__main__':
    result = validate()
    encoded = json.dumps(result, indent=2) + '\n'
    if '--write' in sys.argv[1:]:
        (HERE / 'CROSS_FAMILY_VALIDATION.json').write_text(encoded, encoding='utf-8')
    print(encoded, end='')
