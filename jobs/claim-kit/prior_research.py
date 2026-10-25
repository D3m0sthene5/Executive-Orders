"""Read-only, attributed prior work for the existing prepare/resume interfaces.

Discovery uses current research artifacts, never Git history or directory recency.
A hash-matched review is a recorded assessment, not approval of a new claim.
"""
import csv
import hashlib
import json
from pathlib import Path
import re

from assemble import canonical_sha

SCHEMA = 'eo-claim-kit-prior-research/v1'
NOTICE = ('Prior producer/reviewer assertions, not new findings or automatic approval. '
          'Reuse only after checking the exact version, source, proposition and scope. '
          'Rejected versions and contradictory assertions remain visible; whole-case review is still required.')
MANIFEST = re.compile(r'(?:selection|selected|manifest|checkpoint|freeze)', re.I)
REVIEW_KEYS = ('artifact_type', 'schema', 'reviewer', 'reviewer_role', 'review_kind',
    'candidate_version', 'verdict', 'verdict_scope', 'disposition', 'reasons',
    'substantive_lifecycle_verdict', 'rejection_reason', 'only_claim_change',
    'preserved_prior_review', 'substantive_findings', 'limits_retained',
    'human_certification', 'full_readiness_certification', 'checker_run',
    'unresolved_material_legal_gaps', 'retained_material_gaps_as_written',
    'scope', 'global_limits', 'state_standard', 'reviewer_family', 'clause_attestations',
    'remaining_gaps_preserved', 'errors', 'reviewed_changes_from_v2', 'v2_rejection_resolved')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def walk(value, pointer=''):
    if isinstance(value, dict):
        yield pointer, value
        for key, child in value.items():
            yield from walk(child, pointer + '/' + str(key).replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, pointer + '/' + str(index))


def source_key(source):
    return tuple(source.get(k) for k in ('sha256', 'text_path', 'text_sha256'))


def clause_key(clause):
    return (clause.get('original_operative_text', clause.get('text')), source_key(
        clause.get('original_source', clause.get('source', {}))))


STATUS_DECISION_SCHEMA = 'eo-status-history-decision/v1'
STATUS_HOLD_SCHEMA = 'eo-pending-adoption-procedural-hold/v1'
STATUS_SCOPE = ('Provisional instrument status only; no inherited lifecycle approval, '
                'first-cessation finding, any-effect determination or human certification.')


def status_context(repo, iid, decisions, reviews, pin, adoption_rows):
    """Adapt actual status records without turning a recorded verdict into authority."""
    def load(rel):
        path = (repo / rel).resolve()
        if not path.is_relative_to(repo):
            return None
        try:
            value = json.loads(path.read_bytes())
            return value if isinstance(value, dict) else None
        except (ValueError, OSError):
            return None

    def fingerprint(value):
        return canonical_sha({k: v for k, v in value.items() if k != 'fingerprint'})

    def dependency_pins(value):
        return [pin(item['path'], item['sha256']) for _, item in walk(value)
                if isinstance(item.get('path'), str) and item.get('sha256')]

    result = []
    attached = set()
    for record, decision in decisions:
        evidence_path = str(Path(record['path']).parent / 'EVIDENCE.json')
        evidence_pin = pin(evidence_path)
        evidence = load(evidence_path)
        evidence_state = 'missing_or_unreadable'
        source_pins = []
        if evidence:
            source_pins = [pin(path, digest) for path, digest in evidence.get('source_fingerprints', {}).items()]
            history = evidence.get('history_packet', {}).get('history', {})
            base = evidence.get('base_dossier', {})
            evidence_state = 'exact' if (
                evidence.get('schema') == 'eo-status-overlay-evidence/v1'
                and evidence.get('instrument_id') == iid
                and evidence.get('fingerprint') == fingerprint(evidence) == decision.get('evidence_sha256')
                and evidence.get('history_sha256') == decision.get('history_sha256')
                and history.get('instrument_id') == iid
                and history.get('fingerprint') == fingerprint(history) == decision.get('history_sha256')
                and isinstance(base, dict) and base.get('schema') == 'eo-claim-kit-dossier/v1'
                and base.get('instrument_id') == iid and base.get('whole_order_status') is None
                and base.get('fingerprint') == canonical_sha(base)
            ) else 'stale_or_mismatched'
        summary = {**record, 'decision_sha256': canonical_sha(decision),
            'producer': decision.get('agent'), 'recommended_provisional_status': decision.get('recommended_provisional_status'),
            'rationale': decision.get('rationale'), 'material_gaps': decision.get('material_gaps', []),
            'basis_evidence_ids': decision.get('basis_evidence_ids', []),
            'producer_scope': decision.get('notice', STATUS_SCOPE),
            'evidence': {**evidence_pin, 'canonical_binding': evidence_state,
                'expected_fingerprint': decision.get('evidence_sha256'),
                'expected_history_fingerprint': decision.get('history_sha256')},
            'source_pins': source_pins, 'reviews': [], 'automatic_approval': False,
            'remaining_questions': ['Whole-lifecycle inventory, first endings, continuing predicates, savings and counterevidence still require scoped research and independent review.']}
        for n, (review_record, review, parent) in enumerate(reviews):
            cross = parent.get('schema') == 'sinclair-cross-family-lean-review/v1'
            matching_files = [p for p in review.get('input_files', []) if p.get('path') == record['path']]
            if cross and not matching_files:
                continue
            if not cross and review.get('decision_sha256') != summary['decision_sha256']:
                # Keep stale same-location reviews visible, but never bind by directory alone.
                if Path(review_record['path']).parent != Path(record['path']).parent:
                    continue
            attached.add(n)
            deps = dependency_pins(review)
            deps.extend(dependency_pins({k: parent[k] for k in ('ruling', 'pending_input', 'historical_review') if k in parent}))
            if cross:
                input_issues = []
                required_inputs = ((record['path'], record['file_sha256']),
                                   (evidence_path, evidence_pin.get('sha256')))
                for required_path, actual in required_inputs:
                    members = [p for p in review.get('input_files', []) if p.get('path') == required_path]
                    if len(members) != 1:
                        input_issues.append({'path': required_path, 'expected_sha256': None,
                            'state': 'missing_review_input' if not members else 'duplicate_review_input',
                            'review_path': review_record['path'], 'review_pointer': review_record['pointer']})
                    elif not re.fullmatch(r'[0-9a-f]{64}', str(members[0].get('sha256') or '')):
                        input_issues.append({'path': required_path, 'expected_sha256': members[0].get('sha256'),
                            'state': 'missing_or_invalid_review_input_sha256',
                            'review_path': review_record['path'], 'review_pointer': review_record['pointer']})
                    elif members[0]['sha256'] != actual:
                        input_issues.append(pin(required_path, members[0]['sha256']))
                deps.extend(input_issues)
                exact = (not input_issues
                    and review.get('producer') == decision.get('agent')
                    and review.get('evidence_canonical_fingerprint') == decision.get('evidence_sha256'))
            else:
                exact = (review.get('decision_sha256') == summary['decision_sha256']
                    and review.get('evidence_sha256') == decision.get('evidence_sha256')
                    and review.get('history_sha256') == decision.get('history_sha256'))
            exact = exact and review.get('instrument_id') == iid and evidence_state == 'exact'
            propositions = []
            for question, finding in review.get('checklist', {}).items():
                if isinstance(finding, dict):
                    propositions.append({'pointer': review_record['pointer'] + '/checklist/' + question, **finding})
            d6 = review.get('d6', {})
            summary['reviews'].append({**review_record,
                'reviewer': review.get('reviewer'), 'reviewer_provenance': parent.get('reviewer'),
                'review_kind': review.get('review_kind', review.get('schema')),
                'verdict': review.get('verdict', review.get('decision')),
                'scope': review.get('scope', review.get('notice', STATUS_SCOPE)),
                'version_binding': 'exact' if exact else 'stale_or_mismatched',
                'dependency_pins': deps, 'rationale': review.get('rationale'),
                'dependency_state': 'all_historical_pins_match' if evidence_state == 'exact' and all(p['state'] == 'match' for p in deps) else 'reconciliation_required',
                'basis_sources': [pin(p['path'], p.get('sha256')) for p in review.get('sources', []) if p.get('path')],
                'checked_evidence_ids': review.get('checked_evidence_ids', []),
                'propositions': propositions,
                'd6': {key: d6[key] for key in ('assessment', 'coverage') if key in d6},
                'basis_spans_pointer': review_record['pointer'] + '/held_basis_spans' if cross else None,
                'review_authority': 'recorded_assessment_only_no_inherited_approval',
                'full_lifecycle_approved': False})
        row = adoption_rows.get(iid)
        bound_reviews = [r for r in summary['reviews'] if r['path'] in (row or {}).get('decision_origin', '')
                         and r['version_binding'] == 'exact' and r['verdict'] in ('accept', 'uphold')]
        summary['adoption'] = {'state': 'not_recorded_in_current_authority' if not row else (
            'recorded_provisional_status_for_review' if bound_reviews and
            row.get('provisional_substantive_status') == decision.get('recommended_provisional_status') else
            'current_status_present_version_reconciliation_required'), 'current_row': row,
            'authority_path': 'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv',
            'legal_approval_inferred': False}
        problems = [p for p in source_pins if p['state'] != 'match']
        for review in summary['reviews']:
            problems.extend(p for p in review['dependency_pins'] if p['state'] != 'match')
            if review['version_binding'] != 'exact':
                summary['remaining_questions'].append('Reconcile stale or mismatched review: ' + review['path'])
        if evidence_state != 'exact':
            summary['remaining_questions'].append('Reconcile producer evidence/history binding: ' + evidence_path)
            problems.append({**evidence_pin, 'state': 'invalid_evidence_binding' if evidence else 'missing_or_unreadable_evidence',
                'canonical_binding': evidence_state,
                'detail': 'Reconcile evidence, history and frozen base-dossier identities and seals; no status or review approval inferred.'})
        if not summary['reviews']:
            summary['remaining_questions'].append('No matching status review discovered; no review or adoption approval inferred.')
        summary['reconciliation_tasks'] = list({(p['path'], p.get('expected_sha256'), p['state']): p for p in problems}.values())
        result.append(summary)
    unattached = [{**record, 'verdict': review.get('verdict', review.get('decision')),
        'scope': review.get('scope', review.get('notice', STATUS_SCOPE)),
        'record': review, 'version_binding': 'producer_version_not_discovered_for_instrument',
        'dependency_pins': dependency_pins(review), 'full_lifecycle_approved': False}
        for n, (record, review, _) in enumerate(reviews) if n not in attached]
    return result, unattached


def status_hold(repo, iid, record, row, parent, pin):
    """Keep the real procedural hold and its historical review separate from approval."""
    review_path = parent.get('review_file')
    review_pin = pin(review_path, parent.get('review_file_sha256')) if review_path else None
    pointer = row.get('original_review_pointer', '')
    original_review = None
    match = re.fullmatch(r'/verdicts/(\d+)', pointer)
    if review_path and match:
        path = (repo / review_path).resolve()
        if path.is_relative_to(repo):
            try:
                candidate = json.loads(path.read_bytes())['verdicts'][int(match[1])]
                if candidate.get('instrument_id') == iid:
                    original_review = candidate
            except (OSError, ValueError, KeyError, IndexError, TypeError):
                pass
    references = [{**r, 'current_pin': pin(r['cited_path'])}
                  for r in parent.get('ruling_references', []) if r.get('cited_path')]
    return {**record, 'record': row, 'state': row.get('current_disposition', parent.get('disposition')),
        'notice': parent.get('label'), 'reason': parent.get('reason'),
        'historical_review': {'file': review_pin, 'pointer': pointer, 'record': original_review,
            'binding': 'exact' if original_review and review_pin['state'] == 'match' else 'reconciliation_required',
            'producer_version_binding': 'not_established_by_procedural_hold'},
        'ruling_references': references,
        'source_access': pin(row['original_review_source_file']) if row.get('original_review_source_file') else None,
        'automatic_approval': False, 'full_lifecycle_approved': False}


def collect(repo, dossiers, exclude=None):
    """Compact current-file inventory. Additions, edits and removals change its hash."""
    repo = Path(repo).resolve()
    excluded = [Path(p).resolve() for p in (exclude if isinstance(exclude, (list, tuple)) else [exclude]) if p]
    ids = set(dossiers)
    claims = {iid: {} for iid in ids}
    reviews = {iid: [] for iid in ids}
    checkpoints = {iid: [] for iid in ids}
    manifests = {iid: [] for iid in ids}
    pins = {}
    status_decisions = {iid: [] for iid in ids}
    status_reviews = {iid: [] for iid in ids}
    status_holds = {iid: [] for iid in ids}
    issues = []
    control_paths = {}
    excluded_controls = []

    def pin(rel, expected=None):
        p = (repo / rel).resolve()
        if not p.is_relative_to(repo):
            return {'path': rel, 'expected_sha256': expected, 'state': 'outside_repository'}
        if not p.is_file():
            pins[rel] = None
            return {'path': rel, 'expected_sha256': expected, 'state': 'missing'}
        # Hash streamed bytes, including large sources; never read a raw PDF as text.
        if rel not in pins:
            with p.open('rb') as handle:
                pins[rel] = hashlib.file_digest(handle, 'sha256').hexdigest()
        actual = pins[rel]
        return {'path': rel, 'expected_sha256': expected, 'sha256': actual,
                'state': 'match' if expected == actual else ('changed' if expected else 'unqualified')}

    # Existing blinded controls are identified by their reveal plus frozen file
    # hashes, not by treating every blinded/reviewed proposal as a control.
    for reveal_path in sorted((repo / 'research').rglob('*REVEAL*.json')):
        try:
            reveal = json.loads(reveal_path.read_bytes())
        except (ValueError, OSError):
            continue
        if not isinstance(reveal, dict) or not isinstance(reveal.get('controls'), dict):
            continue
        for freeze_path in sorted(reveal_path.parent.rglob('FREEZE.json')):
            try:
                freeze = json.loads(freeze_path.read_bytes())
            except (ValueError, OSError):
                continue
            candidates = freeze.get('candidates', {})
            for label, reason in reveal['controls'].items():
                if label not in candidates or not isinstance(label, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', label):
                    continue
                candidate = freeze_path.parent / (label + '.json')
                if candidate.exists():
                    control_paths[candidate.resolve()] = {
                        'reason': reason, 'expected_frozen_file_sha256': candidates[label],
                        'reveal_path': reveal_path.relative_to(repo).as_posix(),
                        'freeze_path': freeze_path.relative_to(repo).as_posix()}

    # Existing claims, reviews, selected-version manifests and unfinished producer
    # checkpoints can live in any research session. Do not consume generated packet
    # copies or recurse through arbitrary nested claims in reports.
    for path in sorted((repo / 'research').rglob('*')):
        if any(path.resolve().is_relative_to(p) for p in excluded):
            continue
        if path.suffix.lower() not in ('.json', '.jsonl') or not path.is_file():
            continue
        if path.name in ('PACKET.json', 'EVIDENCE.json'):
            continue
        raw = path.read_bytes()
        if not any(iid.encode() in raw for iid in ids):
            continue
        rel = path.relative_to(repo).as_posix()
        if path.resolve() in control_paths:
            qualification = control_paths[path.resolve()]
            for key in ('reveal_path', 'freeze_path'):
                pin(qualification[key])
            pins[rel] = sha(raw)
            excluded_controls.append({'path': rel, 'file_sha256': sha(raw), **qualification,
                'binding': 'exact' if sha(raw) == qualification['expected_frozen_file_sha256'] else 'changed_control_copy',
                'state': 'control_excluded_from_research_assertions'})
            continue
        try:
            values = [(f'line:{n}', json.loads(line)) for n, line in enumerate(raw.splitlines(), 1) if line.strip()] if path.suffix == '.jsonl' else [('', json.loads(raw))]
        except (ValueError, UnicodeError) as exc:
            # Ignore unrelated research formats; surface malformed candidate input.
            if 'claim' in path.name.lower() or 'review' in path.name.lower() or MANIFEST.search(path.name):
                pins[rel] = sha(raw)
                issues.append({'path': rel, 'issue': 'unreadable research artifact', 'detail': str(exc)})
            continue
        for location, value in values:
            if not isinstance(value, dict) or value.get('schema') == SCHEMA or ('prior_research' in value and value.get('schema') != 'eo-source-blocked-work/v1'):
                continue
            iid = value.get('instrument_id')
            record = {'path': rel, 'pointer': location, 'file_sha256': sha(raw)}
            if iid in ids and value.get('schema') == STATUS_DECISION_SCHEMA:
                pins[rel] = sha(raw)
                status_decisions[iid].append((record, value))
            elif iid in ids and value.get('schema') == 'eo-status-overlay-review/v1':
                pins[rel] = sha(raw)
                status_reviews[iid].append((record, value, value))
            elif value.get('schema') == 'sinclair-cross-family-lean-review/v1':
                for number, row in enumerate(value.get('verdicts', [])):
                    if row.get('instrument_id') in ids:
                        pins[rel] = sha(raw)
                        status_reviews[row['instrument_id']].append((
                            {**record, 'pointer': '/verdicts/' + str(number)}, row, value))
            elif value.get('schema') == STATUS_HOLD_SCHEMA:
                for number, row in enumerate(value.get('proposals', [])):
                    target = row.get('instrument_id')
                    if target in ids:
                        pins[rel] = sha(raw)
                        status_holds[target].append(status_hold(repo, target,
                            {**record, 'pointer': '/proposals/' + str(number)}, row, value, pin))
            if 'review' in value.get('schema', '').lower() or value.get('reviewer'):
                for pointer, row in walk(value):
                    target = row.get('instrument_id')
                    if pointer and target in ids and 'verdict' in row and 'claim_sha256' in row:
                        pins[rel] = sha(raw)
                        inherited = {k: value[k] for k in REVIEW_KEYS if k in value}
                        inherited.update(claim_path=value.get('claim_path', value.get('claim_file')),
                                         claim_file_sha256=value.get('claim_file_sha256'))
                        reviews[target].append(({**record, 'pointer': location + pointer}, {**inherited, **row}))
            if iid in ids and value.get('schema') == 'eo-lifecycle-claim/v1':
                pins[rel] = sha(raw)
                key = canonical_sha(value)
                entry = claims[iid].setdefault(key, {'claim': value, 'locations': []})
                entry['locations'].append(record)
            elif iid in ids and ('verdict' in value and ('claim_sha256' in value or 'claim_path' in value)):
                pins[rel] = sha(raw)
                reviews[iid].append((record, value))
            elif iid in ids and (value.get('schema', '').endswith('checkpoint/v1') or path.name == 'IN_PROGRESS.json' or value.get('schema') == 'eo-source-blocked-work/v1'):
                pins[rel] = sha(raw)
                checkpoint = {k:v for k,v in value.items() if k != 'prior_research'}
                dependencies = [pin(item['path'], item['sha256']) for _,item in walk(checkpoint)
                                if isinstance(item.get('path'), str) and item.get('sha256')]
                dependencies.extend(pin(rel) for rel in checkpoint.get('result_paths', []) if isinstance(rel, str))
                checkpoints[iid].append({**record, 'record': checkpoint, 'dependency_pins': dependencies})
            elif MANIFEST.search(path.name):
                for target in ids & set(value):
                    if isinstance(value[target], dict) and 'version' in value[target]:
                        pins[rel] = sha(raw)
                        manifests[target].append({**record, 'pointer': location + '/' + target, 'record': value[target]})
                for pointer, row in walk(value):
                    target = row.get('instrument_id')
                    if target in ids and any(k in row for k in ('claim_sha256', 'canonical_claim_sha256', 'claim_path', 'produced', 'selected_version')):
                        pins[rel] = sha(raw)
                        manifests[target].append({**record, 'pointer': location + pointer, 'record': row})

    ruling_pins = [pin(path.relative_to(repo).as_posix())
                   for path in sorted((repo / 'research/readiness/owner_rulings').glob('*.md'))]
    adoption_rows = {}
    authority = repo / 'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv'
    if any(status_decisions.values()) or any(status_reviews.values()) or any(status_holds.values()):
        pin(authority.relative_to(repo).as_posix())
        if authority.is_file():
            with authority.open(encoding='utf-8', newline='') as handle:
                adoption_rows = {row['instrument_id']: row for row in csv.DictReader(handle) if row['instrument_id'] in ids}

    result = {'schema': SCHEMA, 'notice': NOTICE, 'automatic_approvals': 0,
              'whole_case_review_required': True, 'orders': {}, 'input_file_pins': pins,
              'discovery_scope': 'Current materialized research files; unmaterialized work is not inferred absent. No Git history read.',
              'discovery_issues': issues, 'excluded_control_records': excluded_controls,
              'current_rulings': ruling_pins}
    for iid in sorted(ids):
        versions = claims[iid]
        active = []
        for key, entry in versions.items():
            for loc in entry['locations']:
                if loc['path'].startswith('research/readiness/claims/'):
                    active.append((loc['path'], int(loc['pointer'].split(':')[-1]), key))
        current_key = max(active)[2] if active else None
        current = versions[current_key]['claim'] if current_key else None
        base_clauses = (current or {}).get('operative_clauses', dossiers[iid].get('clauses', []))
        summaries = []
        all_assertions = {}
        for key, entry in sorted(versions.items()):
            claim = entry['claim']
            sources = {}
            for pointer, item in walk(claim):
                if item.get('text_path') and item.get('text_sha256'):
                    source_id = canonical_sha({k: item.get(k) for k in ('url','sha256','text_path','text_sha256','page_or_item')})
                    if source_id not in sources:
                        sources[source_id] = {k: item[k] for k in ('url', 'sha256', 'text_path', 'text_sha256', 'page_or_item') if k in item}
                        sources[source_id]['held_text'] = pin(item['text_path'], item['text_sha256'])
                        sources[source_id]['raw_source_verification'] = 'not_reestablished_by_preparation'
                    sources[source_id].setdefault('claim_pointers', []).append(pointer)
            attached = []
            for record, review in reviews[iid]:
                matching_hash = review.get('claim_sha256') == key
                matching_path = any(loc['path'] == review.get('claim_path') for loc in entry['locations'])
                if not matching_hash and not matching_path:
                    continue
                expected_file = review.get('claim_file_sha256')
                file_matches = any((not review.get('claim_path') or loc['path'] == review['claim_path']) and
                    (not expected_file or loc['file_sha256'] == expected_file) for loc in entry['locations'])
                exact = matching_hash and file_matches
                dependencies = []
                for _, item in walk(review):
                    if isinstance(item.get('path'), str) and item.get('sha256'):
                        dependencies.append(pin(item['path'], item['sha256']))
                attached.append({**record, **{k: v for k, v in review.items() if k in REVIEW_KEYS or k.endswith('_approved') or k.endswith('_certified')},
                    'reviewed_claim_sha256': review.get('claim_sha256'),
                    'reviewed_claim_file_sha256': expected_file,
                    'version_binding': 'exact' if exact else 'stale_or_mismatched',
                    'dependency_pins': dependencies,
                    'review_authority': 'recorded_assessment_only_no_inherited_approval'})
            def compact(value):
                if isinstance(value, dict):
                    if value.get('text_path') and value.get('text_sha256'):
                        sid = canonical_sha({k:value.get(k) for k in ('url','sha256','text_path','text_sha256','page_or_item')})
                        return {'source_id': sid, 'quoted_parts_sha256': canonical_sha(value.get('quoted_parts', []))}
                    return {k: compact(v) for k,v in value.items()}
                return [compact(v) for v in value] if isinstance(value, list) else value
            scopes = []
            for number, clause in enumerate(claim.get('operative_clauses', [])):
                matches = [base for base in base_clauses if clause_key(base) == clause_key(clause)
                           and clause_key(clause)[0] and all(re.fullmatch(r'[0-9a-f]{64}', str(h or ''))
                           for h in (clause_key(clause)[1][0], clause_key(clause)[1][2]))]
                proposition = {field: clause.get(field) for field in
                    ('state_at_cutoff', 'first_end', 'current_predicate', 'later_events')}
                # Quotes are already located by source pointers. Preserve all proposition
                # qualifiers but collapse repeated source dictionaries to compact IDs.
                delta = []
                if matches:
                    delta = [field for field in proposition if clause.get(field) != matches[0].get(field)]
                scopes.append({'scope_id': clause.get('scope_id'), 'claim_pointer': '/operative_clauses/' + str(number),
                    'original_quote_sha256': sha(str(clause_key(clause)[0]).encode()),
                    'original_source': compact(clause.get('original_source', {})),
                    'alignment': 'exact_quote_and_source' if matches else 'scope_or_source_reconciliation_required',
                    'aligned_current_scopes': [base.get('scope_id') for base in matches],
                    'proposition': compact(proposition), 'different_current_fields': delta})
                ck = canonical_sha(clause_key(clause))
                assertion = {k: compact(v) for k, v in proposition.items() if v is not None and v != []}
                all_assertions.setdefault(ck, []).append({'claim_sha256': key, 'scope_id': clause.get('scope_id'), 'assertion': assertion})
            summaries.append({'claim_sha256': key, 'locations': entry['locations'], 'current_canonical': key == current_key,
                'research_rationale': claim.get('research_rationale'), 'whole_order_end': compact(claim.get('whole_order_end')),
                'savings_residuals': compact(claim.get('savings_residuals')),
                'reported_material_gaps': claim.get('unresolved_material_gaps', []),
                'reviews': attached, 'scopes': scopes, 'sources': sources})
        conflicts = []
        for group in all_assertions.values():
            fields = sorted({field for a in group for field in a['assertion'] if
                len({canonical_sha(other['assertion'][field]) for other in group if field in other['assertion']}) > 1})
            if fields:
                conflicts.append({'kind': 'different_assertions_same_quote_and_source', 'fields': fields,
                    'versions': [{'claim_sha256': a['claim_sha256'], 'scope_id': a['scope_id']} for a in group],
                    'resolution': 'unresolved_by_preparation'})
        unattached = [{**r, 'record': v, 'version_binding': 'claim_version_not_discovered'} for r,v in reviews[iid]
                      if not any(v.get('claim_sha256') == key or any(loc['path'] == v.get('claim_path') for loc in e['locations']) for key,e in versions.items())]
        status, unattached_status = status_context(repo, iid, status_decisions[iid], status_reviews[iid], pin, adoption_rows)
        result['orders'][iid] = {'state': 'prior_work_located' if summaries or checkpoints[iid] or reviews[iid] or manifests[iid] or status or unattached_status or status_holds[iid] else 'no_prior_research_located',
            'status_research': status, 'unattached_status_reviews': unattached_status, 'status_holds': status_holds[iid],
            'current_canonical_claim_sha256': current_key, 'versions': summaries,
            'unattached_reviews': unattached, 'selection_and_checkpoint_records': manifests[iid],
            'unfinished_work': checkpoints[iid], 'conflicting_versions': conflicts,
            'remaining_delta': {'current_reported_gaps': (current or {}).get('unresolved_material_gaps', []),
                'existing_lifecycle_questions_notice': 'Current dossier research prompts, not new gap findings or overrides of prior claim/review conclusions.',
                'existing_lifecycle_questions': [{key: obligation[key] for key in
                    ('scope_id', 'clause_sha256', 'state', 'questions', 'own_term_evidence_ids', 'later_actor_evidence_ids')
                    if key in obligation} | {'dossier_pointer': '/lifecycle_obligations/' + str(number)}
                    for number, obligation in enumerate(dossiers[iid].get('lifecycle_obligations', []))],
                'prior_differences_require_scope_source_proposition_review': True,
                'new_legal_gaps_invented': [], 'dossier_fingerprint': dossiers[iid].get('fingerprint')}}
    result['input_file_pins'] = dict(sorted(pins.items()))
    return result


def brief(context, iid):
    """Small entry point; exact qualifications and all propositions stay in PACKET."""
    order = context['orders'][iid]
    versions = []
    for version in order['versions']:
        versions.append({k: version[k] for k in ('claim_sha256', 'locations', 'current_canonical',
            'research_rationale', 'reported_material_gaps')} | {
            'source_pins': [{k: source[k] for k in ('text_path','text_sha256','sha256','held_text')}
                            for source in version['sources'].values()],
            'review_dependency_issues': [{'review_path': r['path'], **dep} for r in version['reviews']
                                         for dep in r['dependency_pins'] if dep['state'] != 'match'],
            'reviews': [{k: r[k] for k in ('path', 'pointer', 'file_sha256', 'candidate_version',
                'verdict', 'verdict_scope', 'version_binding', 'review_kind', 'scope', 'limits_retained',
                'full_lifecycle_approved') if k in r} for r in version['reviews']],
            'scopes': [{k: c[k] for k in ('scope_id', 'alignment', 'aligned_current_scopes', 'different_current_fields')}
                       for c in version['scopes']]})
    status = []
    for item in order.get('status_research', []):
        status.append({key: item[key] for key in ('path', 'pointer', 'file_sha256', 'decision_sha256',
            'producer', 'recommended_provisional_status', 'rationale', 'producer_scope', 'material_gaps',
            'evidence', 'adoption', 'remaining_questions', 'reconciliation_tasks')} | {
            'source_pins': item['source_pins'],
            'reviews': [{key: review[key] for key in ('path', 'pointer', 'file_sha256', 'reviewer',
                'verdict', 'scope', 'version_binding', 'propositions', 'rationale', 'd6',
                'basis_spans_pointer', 'basis_sources', 'checked_evidence_ids', 'dependency_state',
                'full_lifecycle_approved') if key in review} for review in item['reviews']]})
    return {'notice': context['notice'], 'state': order['state'], 'versions': versions,
            'status_research': status, 'unattached_status_reviews': order.get('unattached_status_reviews', []),
            'status_holds': [{key: hold[key] for key in ('path', 'pointer', 'file_sha256', 'state', 'notice',
                'reason', 'source_access', 'automatic_approval', 'full_lifecycle_approved')} | {
                'record': {key: hold['record'][key] for key in ('instrument_id', 'hold_reason',
                    'original_review_locus', 'original_review_q2', 'original_review_defects') if key in hold['record']},
                'historical_review': {key: hold['historical_review'][key] for key in
                    ('file', 'pointer', 'binding', 'producer_version_binding')}} for hold in order.get('status_holds', [])],
            'current_rulings': context.get('current_rulings', []),
            'selection_and_checkpoint_records': order['selection_and_checkpoint_records'],
            'unfinished_work': order['unfinished_work'], 'conflicting_versions': order['conflicting_versions'],
            'remaining_delta': order['remaining_delta'],
            'full_context': 'PACKET.json#/prior_research/orders/' + iid}
