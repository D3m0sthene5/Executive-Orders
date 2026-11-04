#!/usr/bin/env python3
"""Bounded, offline population census and exact published-version example.

No job invocation, Git commands, source acquisition or scientific writes.
Raw inputs remain ignored; only sanitized aggregate summaries are written here.
"""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OBS = REPO / 'research/progress/production-observability-20261104'
MAIN = '600ae3018f71025b3e53dc8538b8f92e6e159b76'
PROTECTED = 'cacfb8f4af6db949476bd7bec8220a464055c931'
FIXED = {
    'research/progress/control-center/orders.csv': 'f12ac50863234c47bc6dd4b459bf75c5a27425233a0519c804713b4942fff0ca',
    'research/progress/production-observability-20261104/baseline/SOURCES.json': '3d0420ac70ed512d62416682683d40de2ccc9fea3978e7e9ed24d0ae4c4f3d1b',
    'research/progress/production-observability-20261104/historical/OUTCOMES.json': 'f0a31eda7febe1493161ce55032dfc2df0f94cc4a2fcec2b816fddd3df4dd3f2',
}
EXAMPLE_INPUTS = {
    'claude-mansfield-b01-2026-10-22.jsonl': ('research/readiness/claims/claude-mansfield-b01-2026-10-22.jsonl', 'f28a60b02c3d501b263f0efa0fb719fb91d13cae', 'f775ea3a68844679ef180f88438c3e66b55aa31bf58b2d41b7af93741094b21f'),
    'claude-mansfield-b02-2026-10-22.jsonl': ('research/readiness/claims/claude-mansfield-b02-2026-10-22.jsonl', '23127d7f8e25c3473579f934f81c7a90b5aa35bb', '4756fc816d2e9ad6f9c10d5306110dc65cc368ac4d966d0d0812ca303af0493f'),
    'claude-mansfield-b03-2026-10-22.jsonl': ('research/readiness/claims/claude-mansfield-b03-2026-10-22.jsonl', 'b379629209ef1bf78e5e1cc933feb178b75a43ab', 'e966a03744258d02e4475fed4ca93171eb39de375a31e17812b0414a38fa0ccd'),
    'EO_12553.txt': ('jobs/fr-originals/data/full_run/texts/EO_12553.txt', 'ae03df4078b06c8f46ccaa7b199fd190780455f2', '6361bdc557b6acaeae6e6908cded18f4f8fef9fde1a97cc11fb7c12c8cdea761'),
}
EXAMPLE_IDS = {'EO:10622', 'EO:11040', 'EO:11078', 'EO:9922'}
ACCEPTED = {'done', 'provisional', 'n/a'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def member_digest(ids):
    return sha(('\n'.join(sorted(ids)) + '\n').encode())


def refs(value, path='$'):
    if isinstance(value, dict):
        if {'text_path', 'text_sha256'} <= value.keys():
            yield path, value
        for key, child in value.items():
            yield from refs(child, path + '.' + key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from refs(child, f'{path}[{i}]')


def main():
    sources = []
    for path, expected in FIXED.items():
        data = (REPO / path).read_bytes()
        assert sha(data) == expected, 'Changed census/derived input: ' + path
        sources.append({'path': path, 'sha256': expected, 'bytes': len(data)})
    native = json.loads((OBS / 'baseline/SOURCES.json').read_bytes())
    retained = {}
    for item in native:
        data = (OBS / 'baseline' / item['local_path']).read_bytes()
        assert blob(data) == item['sha'] and sha(data) == item['sha256'], 'Changed native source: ' + item['path']
        retained[(item['commit'], item['path'])] = json.loads(data) if item['path'].endswith('.json') else None
        sources.append({'path': item['path'], 'ref': item['commit'], 'git_blob': item['sha'],
                        'sha256': item['sha256'], 'bytes': len(data), 'retained_via': 'baseline/SOURCES.json'})
    rows = list(csv.DictReader(io.StringIO((REPO / 'research/progress/control-center/orders.csv').read_text())))
    assert len(rows) == len({r['instrument_id'] for r in rows}) == 14972
    assert blob((REPO / 'research/progress/control-center/orders.csv').read_bytes()) == 'd1c074ce575749d48b4c6509399f74a2c19cd689'
    by_id = {r['instrument_id']: r for r in rows}
    all_ids = set(by_id)
    ready = {i for i, r in by_id.items() if r['ready_for_human_review'] == 'yes'}
    unfinished = all_ids - ready
    plan_path = 'research/excavator/claude-tribonian-2026-11-04/tools/batches.json'
    batches = retained[(PROTECTED, plan_path)]
    planned = [i for group in batches.values() for i in group]
    protected = set(planned)
    assert len(planned) == len(protected) == 1218 and protected <= unfinished
    lock_path = 'research/readiness/CLAIM_KIT_LOCK.json'
    reservations = set(retained[(MAIN, lock_path)]['orders'])
    assert retained[(MAIN, lock_path)] == retained[(PROTECTED, lock_path)]
    after_protected = unfinished - protected
    remaining = after_protected - reservations
    assert len(ready) == 784 and len(unfinished) == 14188
    assert len(after_protected) == 12970 and len(remaining) == 12963

    predicates = {
        'text_check_admitted': lambda r: r['step_original_text'] in ACCEPTED,
        'original_supported_tier': lambda r: r['text_evidence_tier'] == 'original_supported',
        'transcription_dependent_tier': lambda r: r['text_evidence_tier'] == 'transcription_dependent',
        'claim_present': lambda r: r['claim_present'] == 'yes',
        'shared_source_applicable': lambda r: r['step_shared_sources'] != 'n/a',
        'shared_source_open': lambda r: r['step_shared_sources'] == 'open',
        'opus_media_open': lambda r: r['step_opus_media'] == 'open',
        'text_and_inventory_admitted': lambda r: all(r[x] in ACCEPTED for x in ('step_original_text', 'step_clause_inventory')),
        'all_listed_checks_admitted': lambda r: all(r[k] in ACCEPTED for k in r if k.startswith('step_')),
    }
    sets = {k: {i for i in unfinished if pred(by_id[i])} for k, pred in predicates.items()}
    opportunities = {}
    for key, ids in sets.items():
        eligible_ceiling = ids & remaining
        opportunities[key] = {
            'unfinished_orders': len(ids), 'protected_overlap': len(ids & protected),
            'reservation_overlap_after_protection': len((ids - protected) & reservations),
            'remaining_structural_ceiling': len(eligible_ceiling),
            'remaining_membership_sha256': member_digest(eligible_ceiling),
            'actual_mechanically_eligible_orders': None,
            'unit': 'unique order identities, not versions, documents, calls or ready gains',
        }
    overlap_keys = ['text_check_admitted', 'claim_present', 'shared_source_applicable', 'shared_source_open', 'opus_media_open', 'transcription_dependent_tier']
    overlap = {a: {b: len(sets[a] & sets[b] & remaining) for b in overlap_keys} for a in overlap_keys}
    blockers = Counter()
    for i in remaining:
        blockers.update({v.split(':', 1)[0] for v in by_id[i]['blockers'].split('|') if v})
    current = json.loads((OBS / 'historical/OUTCOMES.json').read_bytes())
    historical = {}
    for key in ('completion_outcomes', 'genuine_review_versions'):
        records = current[key]
        orders = {x['instrument_id'] for x in records}
        versions = {(x['instrument_id'], x['claim_sha256']) for x in records if x.get('claim_sha256')}
        included = [x for x in records if x['instrument_id'] in remaining]
        historical[key] = {
            'records': len(records), 'unique_orders': len(orders), 'nonnull_order_version_pairs': len(versions),
            'null_version_records': sum(not x.get('claim_sha256') for x in records),
            'protected_order_overlap': len(orders & protected), 'unfinished_order_overlap': len(orders & unfinished),
            'remaining_unique_orders': len(orders & remaining), 'remaining_records': len(included),
            'remaining_nonnull_order_version_pairs': len({(x['instrument_id'], x['claim_sha256']) for x in included if x.get('claim_sha256')}),
            'remaining_dispositions': dict(Counter(x.get('outcome', x.get('verdict')) for x in included)),
        }
    assert historical['completion_outcomes']['remaining_records'] == 119
    assert historical['genuine_review_versions']['remaining_records'] == 2

    # Bounded exact published-version sample; never infer latest selection.
    claims = []
    for name, (path, expected_blob, expected_sha) in EXAMPLE_INPUTS.items():
        data = (HERE / '.source-cache' / name).read_bytes()
        assert blob(data) == expected_blob and sha(data) == expected_sha, 'Changed example source: ' + name
        sources.append({'path': path, 'ref': MAIN, 'git_blob': expected_blob, 'sha256': expected_sha,
                        'bytes': len(data), 'cache_path': '.source-cache/' + name})
        if name.endswith('.jsonl'):
            for line_number, line in enumerate(data.decode().splitlines(), 1):
                claim = json.loads(line)
                if claim['instrument_id'] in EXAMPLE_IDS:
                    claims.append((claim, path, line_number, sha(line.encode())))
    assert len(claims) == len(EXAMPLE_IDS) == 4
    assert EXAMPLE_IDS <= remaining & sets['claim_present']
    text_bytes = (HERE / '.source-cache/EO_12553.txt').read_bytes()
    text = text_bytes.decode()
    target_path = EXAMPLE_INPUTS['EO_12553.txt'][0]
    occurrences = []
    sample_versions = []
    all_sample_refs = []
    for claim, path, line, line_hash in sorted(claims, key=lambda x: x[0]['instrument_id']):
        selected = []
        for pointer, ref in refs(claim):
            all_sample_refs.append(ref)
            if ref['text_path'] != target_path:
                continue
            assert ref['text_sha256'] == sha(text_bytes)
            start, end, quote = ref['char_start'], ref['char_end'], ref['quote']
            assert type(start) is int and type(end) is int and 0 <= start <= end <= len(text)
            assert text[start:end] == quote, 'Span/quote mismatch'
            selected.append((pointer, ref))
            occurrences.append(ref)
        sample_versions.append({
            'instrument_id': claim['instrument_id'], 'source_path': path, 'line_1_based': line,
            'exact_jsonl_line_sha256': line_hash, 'canonical_object_sha256': sha(canon(claim)),
            'target_text_reference_occurrences': len(selected),
            'source_audit_hold_remains': 'OPEN_SOURCE_AUDIT' in by_id[claim['instrument_id']]['blockers'],
            'latest_canonical_version_verified': False,
        })
    full_refs = {sha(canon(r)) for r in occurrences}
    span_keys = {(r['text_sha256'], r['char_start'], r['char_end'], r['quote']) for r in occurrences}
    assert len(occurrences) == 14 and len(full_refs) == 4 and len(span_keys) == 2
    example = {
        'selection': 'Four known source-audit-held orders among the 114 claim-present remaining rows; published historical versions selected intentionally, not sampled randomly.',
        'orders': 4, 'published_versions': 4, 'target_text_documents': 1,
        'target_raw_pdf_sha256_values': sorted({r['sha256'] for r in occurrences}),
        'raw_pdf_bytes_verified_here': False,
        'all_source_reference_occurrences_in_four_claims': len(all_sample_refs),
        'target_source_reference_occurrences': len(occurrences), 'distinct_full_reference_dicts': len(full_refs),
        'distinct_exact_spans': len(span_keys), 'verbatim_span_passes': len(occurrences),
        'naive_per_occurrence_text_loads': len(occurrences), 'grouped_text_loads': 1,
        'naive_per_occurrence_span_checks': len(occurrences), 'grouped_span_checks': len(span_keys),
        'competent_per_claim_text_loads': 4, 'competent_per_claim_span_checks': 4,
        'full_reference_dispositions_preserved': len(occurrences),
        'source_dictionary_identity_does_not_imply_legal_applicability': True,
        'span_key_scope': 'exact text SHA256 + Unicode character offsets + exact quote; preserve full source dictionary separately',
        'versions': sample_versions,
        'extrapolation': None,
    }
    cases = []
    for i, lesson in [
        ('EO:14139', 'All listed checks admitted, but unresolved material gaps; no automatic filing opportunity.'),
        ('EO:12891', 'Original-supported row lacks filed claim; historical completion refusal cannot be repaired by table/source dictionary projection.'),
        ('EO:11303', 'Native census ready despite a rejected later correction; exact attempt/version scope matters.'),
        ('EO:10622', 'Verified common-source span still leaves clause-inventory failure and open source audit.'),
    ]:
        r = by_id[i]
        cases.append({'instrument_id': i, 'ready': i in ready, 'protected': i in protected,
                      'reserved': i in reservations, 'claim_present': r['claim_present'],
                      'native_claim_record_errors': r['claim_record_errors'], 'native_blockers': r['blockers'], 'lesson': lesson})
    result = {
        'schema': 'eo-bounded-offload-population/v1', 'source_pin': MAIN,
        'source_generation': 'native checker/tracker run 41504614771, Nov2; not live assignment or source-readiness census',
        'population': {'all_orders': len(all_ids), 'ready': len(ready), 'unfinished': len(unfinished),
                       'protected_planned_orders': len(protected), 'protected_plan_sha256': member_digest(protected),
                       'protected_plan_batches': len(batches), 'published_reservations': len(reservations),
                       'reservation_unfinished_overlap': len(reservations & unfinished),
                       'reservation_protected_overlap': len(reservations & protected),
                       'after_protected': len(after_protected), 'after_protected_and_reservations': len(remaining)},
        'opportunities': opportunities, 'remaining_intersections': overlap,
        'remaining_blocker_families_overlap': dict(sorted(blockers.items())),
        'historical_join': historical, 'verified_bounded_example': example,
        'challenging_cases': cases,
        'document_denominator': {'remaining_exact_source_documents': None, 'remaining_duplicate_context_loads': None,
                                 'remaining_source_span_operations': None,
                                 'reason': 'Native readiness rows do not carry exact canonical claim versions/source refs, per-load source digests or packet manifests.'},
        'per_claim_index_recovery': {'path': 'jobs/claim-checker/output/PER_CLAIM.json', 'ref': MAIN,
                                     'git_blob': '5a02cceddba050b54bd38d1a344455e91ceb8bfe',
                                     'observed_fetch_content': 'empty; blob metadata only', 'verified_bytes': False},
        'coverage_limits': [
            'No global source/span eligibility count established. Structural ceilings overlap and cannot be summed.',
            'Verified example is 4 published versions on remaining order identities; latest canonical selection and full source custody are unverified.',
            'Raw PDF checks, original-page review, legal identity/applicability and substantive independent review remain required.',
            'Published reservation records are conservatively excluded; exclusion does not assert activity. Unpublished assignments can further shrink availability.',
            'Historical review/completion cohorts are not current worker queues. Remaining historical memberships are blocked/rejected, not upheld versions ready for reuse.',
            'Shared-source applicability is not proof of duplicate exact documents, reusable legal judgment, redundant independent review or avoidable context.',
            'A native admitted text check may be provisional. Evidence tier and step status have different predicates and must not be equated.',
            'No legal/scientific claim, protected packet, assignment, reservation, checkpoint or quota was changed.',
        ],
    }
    for name, value in [('POPULATION.json', result), ('SOURCE_HASHES.json', sources)]:
        data = json.dumps(value, indent=2, sort_keys=True) + '\n'
        target = HERE / name
        temp = target.with_suffix(target.suffix + '.tmp')
        temp.write_text(data)
        temp.replace(target)
    print(json.dumps({'population': result['population'], 'ceilings': {k: v['remaining_structural_ceiling'] for k, v in opportunities.items()},
                      'sample': {k: example[k] for k in ['orders', 'published_versions', 'target_text_documents', 'target_source_reference_occurrences', 'distinct_full_reference_dicts', 'distinct_exact_spans']}}))


if __name__ == '__main__':
    main()
