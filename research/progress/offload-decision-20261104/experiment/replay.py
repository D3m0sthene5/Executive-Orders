#!/usr/bin/env python3
"""Bounded representation replay; source/legal verification is deliberately absent.

Extract existing pure codec functions unchanged rather than importing the missing
sparse job dependency graph. No scientific source, counterpart or control read.
"""
import ast
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SCHEMA = 'eo-claim-kit-dossier/v1'


def canon(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('ambiguous_duplicate_json_key')
        out[key] = value
    return out


def load_json(raw):
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def pinned(path, pin):
    raw = path.read_bytes()
    if sha(raw) != pin['sha256']:
        raise ValueError('stale_source_pin')
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != pin['git_blob']:
        raise ValueError('git_blob_mismatch')
    return raw


def extract_functions(raw, names, namespace):
    tree = ast.parse(raw)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in functions} != set(names):
        raise ValueError('missing_pinned_function')
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<pinned-native-functions>', 'exec'), namespace)


def source_refs(value):
    if isinstance(value, dict):
        if all(k in value for k in ('text_path', 'text_sha256', 'quote', 'char_start', 'char_end')):
            yield value
        for child in value.values():
            yield from source_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from source_refs(child)


def stats(claims):
    refs = list(source_refs(claims))
    unique = {canon(s) for s in refs}
    spans = {(s['text_path'], s['text_sha256'], s['char_start'], s['char_end'], s['quote']) for s in refs}
    return {'source_dictionary_occurrences': len(refs), 'distinct_complete_source_dictionaries': len(unique),
            'duplicate_complete_source_dictionary_occurrences': len(refs) - len(unique),
            'distinct_exact_spans': len(spans),
            'distinct_text_path_hash_pairs': len({(s['text_path'], s['text_sha256']) for s in refs}),
            'literal_source_dictionary_bytes': sum(len(canon(s).encode()) for s in refs),
            'unique_source_dictionary_bytes': sum(len(s.encode()) for s in unique)}


def refused(call):
    try:
        call()
    except (ValueError, KeyError, RecursionError):
        return True
    return False


def main():
    started = time.time()
    pins = load_json((HERE / 'SOURCE_PINS.json').read_bytes())['sources']
    retained = {p['repository_path']: pinned(HERE / p['local_path'], p) for p in pins}
    native = {'Counter': Counter, 'defaultdict': defaultdict, 'deepcopy': deepcopy,
              'hashlib': hashlib, 'json': json, 'Path': Path, 'TAG': '@eo:', 'DOSSIER_SCHEMA': SCHEMA}
    extract_functions(retained['jobs/claim-kit/assemble.py'], ['canonical_sha'], native)
    extract_functions(retained['jobs/claim-kit/batch.py'], ['canon', 'digest', 'safe', 'encode', 'decode'], native)
    raw = retained['research/readiness/claims/claude-2026-11-02-erasmus-c1.jsonl']
    claims = [load_json(line) for line in raw.splitlines() if line.strip()]
    ids = [c['instrument_id'] for c in claims]
    if len(ids) != len(set(ids)):
        raise ValueError('ambiguous_instrument_selector')
    # Exact canonical claims are opaque payloads. The dossier shell supplies the
    # existing codec's normal integrity contract; it asserts no real dossier.
    wrapped = {}
    for claim in claims:
        item = {'schema': SCHEMA, 'instrument_id': claim['instrument_id'], 'historical_claim_payload': claim}
        item['fingerprint'] = native['canonical_sha'](item)
        wrapped[item['instrument_id']] = item
    # An empty, non-existing repository source root proves representation-only:
    # canonical quote dictionaries do not fit the codec text-block load shape.
    source_root = HERE / 'inputs' / 'no-source-root'
    if source_root.exists():
        raise ValueError('unexpected_source_root')

    def measure(tree):
        t = time.perf_counter(); packet = native['encode'](tree, source_root); encoded = canon(packet).encode()
        encode_seconds = time.perf_counter() - t
        t = time.perf_counter(); decoded = native['decode'](packet); decode_seconds = time.perf_counter() - t
        assert canon(decoded) == canon(tree)
        assert packet['held_text_file_pins'] == {} and packet['codec_issues'] == []
        return {'literal_bytes': len(canon(tree).encode()), 'encoded_bytes': len(encoded),
                'encoded_sha256': sha(encoded), 'reconstructed_sha256': sha(canon(decoded).encode()),
                'literal_sha256': sha(canon(tree).encode()), 'exact_canonical_roundtrip': True,
                'encode_seconds': encode_seconds, 'decode_seconds': decode_seconds,
                'shared_objects': len(packet['shared_objects']), 'source_dictionary_entries': len(packet['sources']),
                'source_files_read': 0, 'source_integrity_verdict': 'not_performed'}, packet

    pooled, packet = measure(wrapped)
    singles = []
    for iid in ids:
        result, _ = measure({iid: wrapped[iid]})
        singles.append({'instrument_id': iid, **result, **stats(wrapped[iid])})
    changed = deepcopy(packet)
    changed['dossiers'][ids[0]]['instrument_id'] = 'EO:stale'
    tampered_shared = deepcopy(packet)
    first_shared = next(iter(tampered_shared['shared_objects']))
    tampered_shared['shared_objects'][first_shared] = 'changed exact shared payload'
    missing = deepcopy(packet); missing['shared_objects'].pop(first_shared)
    cycle = deepcopy(packet); cycle['shared_objects'][first_shared] = {'@eo:ref': first_shared}
    malformed = deepcopy(wrapped); malformed[ids[0]]['@eo:reserved'] = 'collision'
    raw_pin = dict(pins[0]); raw_pin['sha256'] = '0' * 64
    probes = {
        'changed_member_version_refused': refused(lambda: native['decode'](changed)),
        'changed_dictionary_refused': refused(lambda: native['decode'](tampered_shared)),
        'missing_dictionary_refused': refused(lambda: native['decode'](missing)),
        'cyclic_dictionary_refused': refused(lambda: native['decode'](cycle)),
        'reserved_codec_marker_refused': refused(lambda: native['encode'](malformed, source_root)),
        'stale_raw_input_pin_refused': refused(lambda: pinned(HERE / pins[0]['local_path'], raw_pin)),
        'ambiguous_duplicate_json_keys_refused': refused(lambda: load_json('{"a":1,"a":2}')),
        'source_fields_preserved_exactly': canon(list(source_refs(native['decode'](packet)))) == canon(list(source_refs(wrapped))),
    }
    assert all(probes.values())
    summary = stats(wrapped)
    within = sum(r['duplicate_complete_source_dictionary_occurrences'] for r in singles)
    result = {'schema': 'offload-existing-codec-replay/v1', 'started_epoch': started, 'ended_epoch': time.time(),
              'actual_model': 'gpt-6.1-sol (configured worker; coordinator-provided identifier)',
              'scope': '15 historical genuine claims at main600ae3; representation experiment, no assignment/source/review execution',
              'literal_claim_payload_bytes': len(canon({c['instrument_id']: c for c in claims}).encode()),
              'claims': len(claims), 'pooled': pooled, 'per_order_cold': singles,
              'reference_tasks': {**summary, 'duplicates_within_order': within,
                                  'additional_duplicates_across_orders': summary['duplicate_complete_source_dictionary_occurrences'] - within,
                                  'distinct_dictionaries_summed_across_independent_order_views': sum(r['distinct_complete_source_dictionaries'] for r in singles),
                                  'distinct_source_reads_removed_from_independent_reviews': 0,
                                  'substantive_review_decisions_removed': 0,
                                  'observed_model_tool_calls_removed': 0},
              'probes': probes, 'tokens': None, 'cash': None, 'active_labor_seconds': None,
              'full_session_seconds': None, 'native_full_module_import_performed': False,
              'native_pure_functions_used_unchanged': ['canonical_sha', 'canon', 'digest', 'safe', 'encode', 'decode'],
              'production_model_context_or_token_measurement': False}
    (HERE / 'RESULTS.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'claims': len(claims), 'pooled': pooled, 'reference_tasks': result['reference_tasks'], 'probes': probes}, indent=2))


if __name__ == '__main__':
    main()
