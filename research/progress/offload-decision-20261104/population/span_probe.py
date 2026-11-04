#!/usr/bin/env python3
"""Experimental grouping of exact-byte/span predicates; no native checker changes.

This isolated predicate is intentionally narrower than source custody, page/identity
checks or legal review. Timings are local warm-cache engineering observations.
"""
import copy
import importlib.util
import json
import platform
import statistics
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('population_builder', HERE / 'build_population.py')
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
TEXT_PATH = B.EXAMPLE_INPUTS['EO_12553.txt'][0]
TEXT_FILE = HERE / '.source-cache/EO_12553.txt'


def load_occurrences():
    records = []
    for name, (path, blob, sha) in B.EXAMPLE_INPUTS.items():
        data = (HERE / '.source-cache' / name).read_bytes()
        assert B.blob(data) == blob and B.sha(data) == sha
        if not name.endswith('.jsonl'):
            continue
        for line in data.decode().splitlines():
            claim = json.loads(line)
            if claim['instrument_id'] not in B.EXAMPLE_IDS:
                continue
            for pointer, ref in B.refs(claim):
                if ref['text_path'] == TEXT_PATH:
                    records.append({'instrument_id': claim['instrument_id'], 'pointer': pointer, 'source': ref})
    records.sort(key=lambda r: (r['instrument_id'], r['pointer']))
    assert len(records) == 14
    return records


def valid_span(ref, size):
    start, end = ref['char_start'], ref['char_end']
    return (type(start) is int and type(end) is int and 0 <= start < end <= size
            and isinstance(ref['quote'], str) and bool(ref['quote']))


def span_status(text, ref, counters=None):
    if counters is not None:
        counters['span_status_calls'] = counters.get('span_status_calls', 0) + 1
    if not valid_span(ref, len(text)):
        return 'invalid_span'
    start, end = ref['char_start'], ref['char_end']
    return 'pass' if text[start:end] == ref['quote'] else 'quote_mismatch'


def disposition(record, status):
    return {'instrument_id': record['instrument_id'], 'pointer': record['pointer'],
            'full_source_dictionary_sha256': B.sha(B.canon(record['source'])), 'status': status}


def naive(records, reader, counters=None):
    outcomes = []
    for record in records:
        ref = record['source']
        data = reader(ref['text_path'])
        if B.sha(data) != ref['text_sha256']:
            status = 'source_hash_mismatch'
        else:
            try:
                text = data.decode()
            except UnicodeDecodeError:
                status = 'invalid_text_encoding'
            else:
                status = span_status(text, ref, counters)
        outcomes.append(disposition(record, status))
    return outcomes


def grouped(records, reader, counters=None):
    # Invocation-scoped cache; bytes are read and hashed again at every call.
    # Full ref metadata remains on all dispositions and never grants judgment.
    docs, decoded, spans, outcomes = {}, {}, {}, []
    for record in records:
        ref = record['source']
        path = ref['text_path']
        if path not in docs:
            data = reader(path)
            docs[path] = (B.sha(data), data)
        actual_hash, data = docs[path]
        if actual_hash != ref['text_sha256']:
            status = 'source_hash_mismatch'
        else:
            if path not in decoded:
                try:
                    decoded[path] = data.decode()
                except UnicodeDecodeError:
                    decoded[path] = None
            text = decoded[path]
            if text is None:
                outcomes.append(disposition(record, 'invalid_text_encoding'))
                continue
            # Validate types before building a key: Python bools alias integer
            # keys, so a cached integer span must never approve bool offsets.
            if not valid_span(ref, len(text)):
                outcomes.append(disposition(record, 'invalid_span'))
                continue
            key = (actual_hash, ref['char_start'], ref['char_end'], ref['quote'])
            if key not in spans:
                spans[key] = span_status(text, ref, counters)
            status = spans[key]
        outcomes.append(disposition(record, status))
    return outcomes


def per_claim(records, reader, counters=None):
    # A fairer competent baseline preserves source re-examination per claim.
    result = []
    for instrument_id in sorted({r['instrument_id'] for r in records}):
        result.extend(grouped([r for r in records if r['instrument_id'] == instrument_id], reader, counters))
    return result


def timed(func, records, rounds=200):
    elapsed, cpu = [], []
    for _ in range(rounds):
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        func(records, lambda path: TEXT_FILE.read_bytes())
        cpu.append(time.process_time_ns() - c0)
        elapsed.append(time.perf_counter_ns() - t0)
    vals = sorted(elapsed)
    return {'rounds': rounds, 'wall_median_ns': int(statistics.median(vals)),
            'wall_p10_ns': vals[len(vals) // 10], 'wall_p90_ns': vals[len(vals) * 9 // 10],
            'process_cpu_median_ns': int(statistics.median(cpu))}


def main():
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    records = load_occurrences()
    setup = {'observed_wall_ns': time.perf_counter_ns() - t0,
             'observed_process_cpu_ns': time.process_time_ns() - c0,
             'includes': 'Verify hashes of all four retained inputs, parse three claim files, select four claims and 14 target refs.'}
    data = TEXT_FILE.read_bytes()
    expected = naive(records, lambda path: data)
    actual = grouped(records, lambda path: data)
    assert expected == actual == per_claim(records, lambda path: data) and all(x['status'] == 'pass' for x in actual)
    probes = []
    for name, test_records, test_data in [
        ('changed_source_bytes', records, b'X' + data[1:]),
        ('changed_non_utf8_source_bytes', records, b'\xff' + data[1:]),
        ('truncated_source_bytes', records, data[:-1]),
        ('unchanged_source', records, data),
    ]:
        a = naive(test_records, lambda path: test_data)
        b = grouped(test_records, lambda path: test_data)
        assert a == b
        probes.append({'case': name, 'outcomes_equal': True, 'pass': sum(x['status'] == 'pass' for x in a),
                       'refusals': sum(x['status'] != 'pass' for x in a)})
    changed = copy.deepcopy(records)
    changed[0]['source']['quote'] += 'altered'
    a, b = naive(changed, lambda path: data), grouped(changed, lambda path: data)
    assert a == b and sum(x['status'] == 'quote_mismatch' for x in b) == 1
    probes.append({'case': 'one_altered_quote_same_source_and_span', 'outcomes_equal': True, 'pass': 13, 'refusals': 1})
    changed = copy.deepcopy(records)
    changed[0]['source']['char_end'] = len(data.decode()) + 1
    a, b = naive(changed, lambda path: data), grouped(changed, lambda path: data)
    assert a == b and sum(x['status'] == 'invalid_span' for x in b) == 1
    probes.append({'case': 'one_out_of_range_span', 'outcomes_equal': True, 'pass': 13, 'refusals': 1})
    changed = copy.deepcopy(records[:2])
    for record in changed:
        record['source'].update(char_start=1, char_end=2, quote=data.decode()[1:2])
    changed[1]['source']['char_start'] = True
    a, b = naive(changed, lambda path: data), grouped(changed, lambda path: data)
    assert a == b and [x['status'] for x in b] == ['pass', 'invalid_span']
    probes.append({'case': 'boolean_offset_after_cached_integer_span', 'outcomes_equal': True, 'pass': 1, 'refusals': 1})
    changed = copy.deepcopy(records)
    changed[0]['source'].update(char_start=1, char_end=1, quote='')
    a, b = naive(changed, lambda path: data), grouped(changed, lambda path: data)
    assert a == b and b[0]['status'] == 'invalid_span'
    probes.append({'case': 'one_zero_width_empty_quote', 'outcomes_equal': True, 'pass': 13, 'refusals': 1})
    # First correct then stale proves the invocation-scoped cache never masks
    # later mutation; persistent approval reuse would need a stronger contract.
    grouped(records, lambda path: data)
    stale = grouped(records, lambda path: data[:-1])
    assert all(x['status'] == 'source_hash_mismatch' for x in stale)
    probes.append({'case': 'stale_input_after_successful_previous_invocation', 'outcomes_equal': stale == naive(records, lambda path: data[:-1]), 'pass': 0, 'refusals': 14})
    # Negative boundary: mutable readers are not equivalent to one immutable
    # snapshot. Preserve this counterexample instead of treating it as a pass.
    def changing_reader():
        calls = []
        def read(path):
            calls.append(path)
            return data if len(calls) == 1 else data[:-1]
        return read
    mutable_naive = naive(records[:2], changing_reader())
    mutable_grouped = grouped(records[:2], changing_reader())
    assert mutable_naive != mutable_grouped
    mutable_boundary = {
        'case': 'source_mutates_between_reference_reads', 'outcomes_equal': False,
        'per_occurrence_statuses': [x['status'] for x in mutable_naive],
        'grouped_statuses': [x['status'] for x in mutable_grouped],
        'admissible_for_grouped_reuse': False,
        'required_admission': 'Already immutable pinned byte snapshot plus unchanged verification policy; mutable source paths are excluded.',
    }
    metrics = {}
    for name, func in [('naive_per_occurrence', naive), ('competent_per_claim', per_claim), ('per_document_and_exact_span', grouped)]:
        reads = []
        def reader(path):
            reads.append(path)
            return data
        counters = {}
        outcomes = func(records, reader, counters)
        metrics[name] = {'text_reads': len(reads), 'text_hashes': len(reads), 'dispositions': len(outcomes),
                         'span_checks': counters['span_status_calls'],
                         'timing': timed(func, records)}
    assert [metrics[k]['span_checks'] for k in metrics] == [14, 4, 2]
    result = {'schema': 'eo-exact-span-grouping-probe/v1', 'source_pin': B.MAIN,
              'source_text_sha256': B.sha(data), 'source_text_bytes': len(data),
              'orders': 4, 'published_versions': 4, 'source_dictionaries': 4, 'text_documents': 1,
              'equivalent_per_occurrence_dispositions': actual, 'equivalent_output_sha256': B.sha(B.canon(actual)),
              'setup': setup, 'operations': metrics, 'invalidation_probes': probes,
              'mutable_source_counterexample': mutable_boundary,
              'initial_prototype_rejections': [
                  'Review caught bool/integer cache-key alias approval before type validation.',
                  'Review caught empty zero-width span acceptance.',
                  'Review caught decoding non-UTF8 changed bytes before hash mismatch refusal.',
                  'All three were corrected in the isolated prototype; no native code or gates changed.'],
              'runtime': {'python': platform.python_version(), 'platform': platform.platform()},
              'interpretation': 'Local deterministic predicate experiment. Native verifier unchanged. No model/tool/source-review step removal or measured token, cash, labor or readiness saving.',
              'limits': ['Latest canonical claim versions unverified.', 'Raw PDF bytes and source-grade/identity/applicability checks not performed.',
                         'Reads use the local warm filesystem; rounds share an OS cache and are not network acquisition or production workload.',
                         'Setup and full-reference disposition costs are included explicitly; common source must stay available to every independent reviewer.',
                         'Grouped predicate is a candidate internal optimization, not a replacement verifier or production cache approval.',
                         'PR135 supplies an explicit mechanical verifier boundary; its exact reviewed verify_files loops over references and is not a pooled cache. This prototype does not replace it.',
                         'The four-claim grouping here does not establish that real ordinary invocations perform these 14 reads together.',
                         'Equivalence fails when source bytes mutate between per-reference reads; only immutable pinned byte snapshots can be admitted.',
                         'Future reuse requires immutable source identity and unchanged predicate policy; this prototype caches only within an invocation.']}
    (HERE / 'SPAN_PROBE.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'setup': setup, 'operations': metrics, 'probes': probes}))


if __name__ == '__main__':
    main()
