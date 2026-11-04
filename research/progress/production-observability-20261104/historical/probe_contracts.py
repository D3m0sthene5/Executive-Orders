#!/usr/bin/env python3
"""Synthetic parser probes, separate from historical measured usage."""
import argparse
import json
import tempfile
import types
from pathlib import Path
import recover


def module(path):
    m = types.ModuleType(path)
    exec(compile(recover.load(path), path, 'exec'), m.__dict__)
    return m


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-cache', type=Path, default=recover.CACHE)
    args = parser.parse_args()
    recover.CACHE = args.source_cache.resolve()
    geddes = module('jobs/geddes/telemetry.py')
    hamilton = module('jobs/hamilton-token-audit/profile.py')
    usage = {'input_tokens': 3, 'cache_read_input_tokens': 10,
             'cache_creation_input_tokens': 2, 'output_tokens': 1}
    tool = {'type': 'tool_use', 'id': 'fixture-tool', 'name': 'Read', 'input': {'file_path': 'fixture.txt'}}
    first = {'id': 'fixture-message', 'model': 'fixture-model', 'usage': usage, 'content': [tool]}
    final = {**first, 'usage': {**usage, 'output_tokens': 9}, 'stop_reason': 'end_turn'}
    events = [{'type': 'assistant', 'timestamp': '2026-01-01T00:00:00Z', 'message': first},
              {'type': 'assistant', 'timestamp': '2026-01-01T00:00:02Z', 'message': final}]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'fixture.output'
        p.write_text(''.join(json.dumps(e) + '\n' for e in events))
        g = geddes.read_transcript(p)
        missing = {**first, 'id': 'fixture-missing-usage', 'usage': {'output_tokens': 2}}
        p.write_text(json.dumps({'type': 'assistant', 'message': missing}) + '\n')
        gm = geddes.read_transcript(p)
        no_id = [{**first, 'id': None}, {**final, 'id': None}]
        p.write_text(''.join(json.dumps({'type': 'assistant', 'message': m}) + '\n' for m in no_id))
        gi = geddes.read_transcript(p)
    h = hamilton.profile([(e['timestamp'], 'assistant', {'message': e['message']}) for e in events])
    assert g['output_tokens'] == 1 and g['read_calls'] == 2 and g['api_messages'] == 1
    assert h['tokens']['output'] == 9 and h['coverage']['output']['complete_final_usage_observed']
    assert gm['input_tokens'] == 0 and gi['api_messages'] == 1
    result = {'schema': 'eo-telemetry-contract-probes/v1', 'scope': 'synthetic parser behavior; no historical usage corrected',
        'source_ids': ['jobs/geddes/telemetry.py', 'jobs/hamilton-token-audit/profile.py'],
        'streamed_then_final': {'known_final_output_tokens': 9, 'geddes_output_tokens': g['output_tokens'],
            'hamilton_output_tokens': h['tokens']['output'], 'geddes_read_calls_for_one_repeated_tool_id': g['read_calls'],
            'hamilton_final_usage_marker': h['coverage']['output']['complete_final_usage_observed']},
        'missing_usage_categories': {'geddes_missing_input_tokens_rendered': gm['input_tokens'],
                                    'hamilton_usage_counts': hamilton.usage_counts({'output_tokens': 2})},
        'missing_message_ids': {'distinct_fixture_events': 2, 'geddes_api_messages': gi['api_messages'],
                                'note': 'Missing stable IDs cannot support safe per-call deduplication.'},
        'checks_passed': 4}
    recover.write('CONTRACT_PROBES.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
