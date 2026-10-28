"""Read-only adapters for real claim-kit receipts; no legal/status authority.

The production schema is separate from the historical offline probe schema.
Files are read through confined, hash-pinned references; no commands are run.
"""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

SHA = re.compile(r'[0-9a-f]{64}\Z')
IID = re.compile(r'EO:[A-Za-z0-9_.:-]+\Z')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def number(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            'invalid nonnegative measurement: ' + label)
    return value


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def parse(raw, jsonl=False):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key: ' + key)
            out[key] = value
        return out
    def reject(value):
        raise ValueError('nonfinite JSON constant: ' + value)
    def one(line):
        return json.loads(line, object_pairs_hook=pairs, parse_constant=reject)
    return [one(line) for line in raw.splitlines() if line.strip()] if jsonl else one(raw)


def timestamp(text):
    require(isinstance(text, str), 'timestamp required')
    dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
    require(dt.tzinfo is not None, 'timezone required')
    return dt.timestamp()


def interval(start, end):
    a, b = timestamp(start), timestamp(end)
    require(a <= b, 'reversed interval')
    return [a, b]


def union_seconds(intervals):
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return sum(b-a for a, b in merged)


class Reader:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.pins = {}

    def path(self, rel):
        require(isinstance(rel, str) and rel and not Path(rel).is_absolute(),
                'repository-relative path required')
        p = (self.root / rel).resolve()
        require(p.is_relative_to(self.root), 'path escapes repository: ' + rel)
        return p

    def raw(self, ref):
        require(isinstance(ref, dict) and SHA.fullmatch(str(ref.get('sha256', ''))),
                'exact sha256 reference required')
        p = self.path(ref.get('path'))
        require(p.is_file() and p.stat().st_size <= 32_000_000,
                'missing or oversized input: ' + ref['path'])
        raw = p.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        require(actual == ref['sha256'], 'changed input: ' + ref['path'])
        rel = p.relative_to(self.root).as_posix()
        require(rel not in self.pins or self.pins[rel] == actual, 'conflicting input version')
        self.pins[rel] = actual
        return raw

    def ref(self, rel):
        p = self.path(rel)
        require(p.is_file() and p.stat().st_size <= 32_000_000, 'missing or oversized input: ' + rel)
        return {'path': p.relative_to(self.root).as_posix(),
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

    def value(self, ref):
        value = parse(self.raw(ref), ref['path'].endswith('.jsonl'))
        pointer = ref.get('pointer', '')
        require(isinstance(pointer, str) and (not pointer or pointer.startswith('/')),
                'invalid JSON pointer')
        for token in pointer.split('/')[1:] if pointer else []:
            token = token.replace('~1', '/').replace('~0', '~')
            if isinstance(value, list):
                require(token.isdigit(), 'invalid list pointer')
                value = value[int(token)]
            else:
                value = value[token]
        return value


def tally(reader, ref):
    data = reader.value(ref)
    require(data.get('schema') == 'eo-claim-kit-completion/v1', 'unsupported completion schema')
    rows = data.get('outcomes')
    require(isinstance(rows, list), 'completion outcomes required')
    seen = set()
    for row in rows:
        iid = row.get('instrument_id')
        require(isinstance(iid, str) and IID.fullmatch(iid) and iid not in seen,
                'invalid or duplicate completion member')
        seen.add(iid)
        require(row.get('outcome') in ('eligible', 'exception', 'blocked', 'unresolved', 'route_owner'),
                'unknown completion outcome')
        if row['outcome'] == 'eligible':
            require(SHA.fullmatch(str(row.get('claim_sha256', ''))) and
                    row.get('source_review_upheld') is True and
                    row.get('publication_kind') in ('whole_case', 'partial_research'),
                    'eligible outcome lacks exact scoped source review')
    duration = data.get('wall_seconds')
    if duration is not None:
        number(duration, 'completion machine seconds')
    span = interval(data['started_utc'], data['finished_utc'])
    return {'receipt': ref, 'attempt_id': 'completion:' + ref['sha256'],
            'outcomes': rows, 'machine_seconds': duration, 'interval': span,
            'reported_model_tokens': data.get('model_tokens'),
            'reported_model_cost': data.get('model_cost')}


def source_check(reader, spec):
    """Inspect identity/bytes/text/span, never establish proposition adequacy."""
    iid = spec['instrument_id']
    require(isinstance(iid, str) and IID.fullmatch(iid), 'invalid source-check identity')
    record = reader.value(spec['record'])
    ids = record.get('instrument_ids', [record.get('instrument_id')])
    require(isinstance(ids, list), 'source identity list required')
    states = []
    if not any(ids):
        states.append('identity_not_recorded')
    elif iid not in ids:
        states.append('wrong_identity')
    else:
        states.append('metadata_identity_match')
    if 'edition_year' in spec:
        states.append('edition_not_recorded' if record.get('edition_year') is None else
                      'edition_mismatch' if record['edition_year'] != spec['edition_year'] else 'metadata_edition_match')
    for key, hash_keys in [('raw', ('sha256',)),
                           ('text', ('text_sha256', 'extracted_text_sha256'))]:
        if key not in spec:
            states.append(key + '_not_checked')
            continue
        ref = spec[key]
        require(isinstance(ref, dict) and SHA.fullmatch(str(ref.get('sha256', ''))), 'source reference hash required')
        path = reader.path(ref['path'])
        if not path.exists():
            reader.pins[path.relative_to(reader.root).as_posix()] = None
            states.append(key + '_bytes_unavailable_in_checkout')
            continue
        raw = reader.raw(spec[key])
        expected = next((record[k] for k in hash_keys if record.get(k)), None)
        if expected != hashlib.sha256(raw).hexdigest():
            states.append(key + '_record_hash_mismatch')
        if key == 'text' and 'span' in spec:
            text = raw.decode('utf-8')
            s = spec['span']; a, b = s['start'], s['end']
            require(type(a) is int and type(b) is int and 0 <= a < b <= len(text),
                    'invalid source span')
            states.append('span_exact' if text[a:b] == s['quote'] else 'span_mismatch')
    return {'instrument_id': iid, 'record': spec['record'], 'states': states,
            'identity_check_scope': 'metadata association only; source-content identity requires existing checker/reviewer',
            'proposition_adequacy': 'requires_substantive_review', 'source_grade_changed': False}


def checkpoint(reader, ref):
    data = reader.value(ref)
    require(data.get('schema') == 'eo-source-blocked-work/v1' and
            data.get('state') == 'source_blocked', 'unsupported source checkpoint')
    require(IID.fullmatch(str(data.get('instrument_id', ''))), 'checkpoint identity required')
    requests = []
    for index, request in enumerate(data.get('source_requests', [])):
        original = request.get('original_request', {})
        require(original.get('instrument_id') == data['instrument_id'], 'wrong checkpoint request target')
        requests.append({'citation': original.get('citation'), 'needed_evidence': original.get('note'),
                         'step': original.get('step'), 'urls': original.get('urls', []),
                         'ref': dict(ref, pointer='/source_requests/' + str(index))})
    results = data.get('source_results', [])
    versions = []
    for rel in data.get('result_paths', []):
        if not rel.endswith('.jsonl') or not reader.path(rel).is_file():
            continue
        expected = data.get('prior_research', {}).get('input_file_pins', {}).get(rel)
        claim_ref = {'path': rel, 'sha256': expected} if expected else reader.ref(rel)
        for claim in reader.value(claim_ref):
            if claim.get('schema') == 'eo-lifecycle-claim/v1' and claim.get('instrument_id') == data['instrument_id']:
                versions.append({'claim_sha256': canonical(claim), 'ref': claim_ref,
                                 'qualification': 'historical_file_pin' if expected else 'current_referenced_file'})
    return {'instrument_id': data['instrument_id'], 'ref': ref, 'reason': data.get('reason'),
            'attribution': 'checkpoint author; not independent causal verification',
            'referenced_claim_versions': versions,
            'requests': requests,
            'no_route': [{'citation': r.get('citation'), 'why': r.get('why')}
                         for r in results if r.get('result') == 'no_route'],
            'reported_document_text_records': sum(r.get('evidence_tier') == 'document_text' for r in results),
            'exhaustion_established': False}


def import_production(reader, manifest):
    require(manifest.get('schema') == 'neyman.production-import/1', 'unsupported import schema')
    require(manifest.get('cohort_kind') in ('retrospective_convenience', 'prospective_probability', 'ordinary_production'),
            'explicit cohort kind required')
    require(re.fullmatch('[0-9a-f]{40}', str(manifest.get('base_commit', ''))), 'base commit required')
    selection = reader.value(manifest['selection'])
    require(isinstance(selection, list) and selection, 'nonempty selection required')
    ids = [r['instrument_id'] for r in selection]
    require(len(ids) == len(set(ids)) and all(IID.fullmatch(i) for i in ids), 'duplicate/invalid selection')
    refs = list(manifest.get('completion_receipts', []))
    if 'completion_index' in manifest:
        index = reader.value(manifest['completion_index'])
        refs += [{'path': x['path'], 'sha256': x['sha256']} for x in index['invocations']]
    attempts = {}; aliases = []
    for ref in refs:
        item = tally(reader, ref)
        key = item['attempt_id']
        if key in attempts:
            aliases.append(ref)
        else:
            attempts[key] = item
    research = []
    seen_research = set()
    for ref in manifest.get('research_attempts', []):
        r = reader.value(ref)
        require(r.get('schema') == 'neyman.research-attempt/1' and r.get('instrument_id') in ids,
                'research attempt schema/target mismatch')
        require(isinstance(r.get('attempt_id'), str) and r['attempt_id'] and r.get('assessor') and r.get('question')
                and r.get('outcome') in ('blocked', 'censored', 'unfinished', 'stage_result'),
                'incomplete research attempt')
        require(r['attempt_id'] not in seen_research, 'duplicate research attempt id')
        seen_research.add(r['attempt_id'])
        interval(r['started_utc'], r['finished_utc'])
        require(r.get('basis'), 'research attempt evidence references required')
        for basis in r['basis']:
            reader.value(basis)
        research.append(dict(r, receipt=ref, assessment_authority='reported research observation; not automatic review approval'))
    require(attempts or research, 'real completion or research attempt receipts required')
    observed_ids = {r['instrument_id'] for a in attempts.values() for r in a['outcomes']}
    require(observed_ids <= set(ids), 'completion has unselected member; include it explicitly')
    cases = []
    for s in selection:
        iid = s['instrument_id']
        if not s.get('completion'):
            own = [r for r in research if r['instrument_id'] == iid]
            require(own, 'selected unfinished case has no actual attempt receipt')
            require(not s.get('claim_sha256'), 'unfinished claim cannot inherit a selected claim hash')
            cases.append({'schema': 'neyman.production-observation/1', 'instrument_id': iid,
                          'claim_sha256': None, 'reviewed_output': 'no_reviewed_result',
                          'whole_case_gate_pass': False, 'gate_errors': [],
                          'ready_in_isolated_replay': False, 'tracker_blockers': [],
                          'research_attempts': own, 'right_censored': any(r['outcome'] == 'censored' for r in own),
                          'attempt_ids': [r['attempt_id'] for r in own], 'human_certifications_added': 0})
            continue
        expected = s['claim_sha256']
        require(SHA.fullmatch(str(expected)), 'selection claim hash required')
        final_ref = reader.ref(s['completion'] + '/TALLY.json')
        final = tally(reader, final_ref)
        require(final['attempt_id'] in attempts, 'final receipt absent from attempt history')
        row = next((r for r in final['outcomes'] if r['instrument_id'] == iid), None)
        require(row is not None and row.get('claim_sha256') == expected and
                row.get('publication_kind') == s['publication_kind'] and row['outcome'] == 'eligible',
                'final selection/version mismatch')
        claims_ref = reader.ref(s['completion'] + '/CLAIMS.selected.jsonl')
        claims = reader.value(claims_ref)
        require(sum(c.get('instrument_id') == iid and canonical(c) == expected for c in claims) == 1,
                'selected claim bytes do not match canonical selection')
        replay_ref = reader.ref(s['completion'] + '/TRACKER_REPLAY.json')
        replay = reader.value(replay_ref)
        require(replay.get('canonical_outputs_modified') is False, 'isolated replay required')
        state = replay['selected'][iid]['after']
        require(state.get('instrument_id') == iid, 'tracker target mismatch')
        errors = row.get('gate_errors')
        require(isinstance(errors, list), 'explicit gate outcome required')
        require(row['publication_kind'] != 'whole_case' or not errors, 'whole-case proposal still has gate errors')
        whole = row['publication_kind'] == 'whole_case' and not errors
        cases.append({'schema': 'neyman.production-observation/1', 'instrument_id': iid,
                      'claim_sha256': expected, 'completion_receipt': final_ref,
                      'selected_claims': claims_ref, 'tracker_receipt': replay_ref,
                      'reviewed_output': 'whole_case_proposal' if whole else 'partial_research',
                      'whole_case_gate_pass': whole, 'gate_errors': errors,
                      'ready_in_isolated_replay': state.get('ready_for_human_review') == 'yes',
                      'tracker_blockers': state.get('blockers', '').split('|') if state.get('blockers') else [],
                      'attempt_ids': sorted(a['attempt_id'] for a in attempts.values()
                                            if any(r['instrument_id'] == iid for r in a['outcomes'])),
                      'human_certifications_added': 0})
    sample = None
    if manifest['cohort_kind'] == 'prospective_probability':
        require('sample_manifest' in manifest, 'probability cohort needs frozen NEYMAN manifest')
        sample = reader.value(manifest['sample_manifest'])
        from survey import verify_manifest
        verify_manifest(sample)
        require(set(ids) <= {r['instrument_id'] for r in sample['sample']}, 'case absent from frozen sample')
    checkpoints = [checkpoint(reader, ref) for ref in manifest.get('checkpoints', [])]
    require(all(c['instrument_id'] in ids for c in checkpoints), 'unselected checkpoint')
    return {'schema': 'neyman.production-imported/1', 'base_commit': manifest['base_commit'],
            'cohort_kind': manifest['cohort_kind'], 'observations': cases,
            'attempts': list(attempts.values()), 'duplicate_receipt_aliases': aliases,
            'research_attempts': research,
            'source_checks': [source_check(reader, x) for x in manifest.get('source_checks', [])],
            'checkpoints': checkpoints,
            'sample_unobserved': sorted({r['instrument_id'] for r in sample['sample']} - set(ids)) if sample else [],
            'population_cost_estimate': None, 'net_savings': None}
