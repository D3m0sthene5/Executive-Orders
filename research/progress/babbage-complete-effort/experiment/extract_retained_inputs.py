#!/usr/bin/env python3
"""Bounded, offline extraction of exact retained experiment inputs, never approval."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

REF = '2bc32c6d4ea87abf969c406dd4049dc3dddcc3c7'
BLOBS = {
    'o25': '42c26bf6fba795b658aaab3e401fe3ce329b7736',
    'o28': 'a058108653833c736f69143ac741b724ae0d8ca3',
    'o29': '0711c4e6f9ed09e3a2f7c34e5faf169a7957fae6',
    'o30': '1754d746137d9e211335a2bea119ac7aee72973e',
}


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def read(batch, cache):
    raw = (cache / (batch + '-PACKET.json')).read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != BLOBS[batch]:
        raise ValueError(f'{batch}: changed retained packet {blob}')
    packet = json.loads(raw)
    return packet, {'ref': REF, 'git_blob': blob, 'sha256': hashlib.sha256(raw).hexdigest(),
                    'path': f'research/excavator/claude-tribonian-2026-11-04/{batch}/packet/PACKET.json'}


def decode(value, packet):
    if isinstance(value, list):
        return [decode(v, packet) for v in value]
    if not isinstance(value, dict):
        return value
    if len(value) == 1:
        if '@eo:ref' in value:
            return decode(packet['shared_objects'][value['@eo:ref']], packet)
        if '@eo:source' in value:
            return decode(packet['sources'][value['@eo:source']], packet)
        if '@eo:span' in value:
            name, start, end = value['@eo:span']
            block = packet['text_blocks'][name]
            if not block['char_start'] <= start < end <= block['char_end']:
                raise ValueError('invalid retained text span')
            return block['text'][start-block['char_start']:end-block['char_start']]
    return {k: decode(v, packet) for k, v in value.items()}


def extract(batches, cache):
    packets, members, pinlist = {}, [], []
    for batch in batches:
        packet, pin = read(batch, cache)
        pinlist.append({'batch': batch, **pin})
        packets[batch] = {'source': pin, 'packet_fingerprint': packet['fingerprint'],
                          'preflight': packet['preflight']}
        for iid, encoded in packet['dossiers'].items():
            dossier = decode({k: encoded[k] for k in ('fingerprint', 'whole_order_status', 'current_law_leads') if k in encoded}, packet)
            members.append({'batch': batch, 'instrument_id': iid,
                            'fingerprint': dossier['fingerprint'],
                            'whole_order_status': dossier.get('whole_order_status'),
                            'current_law_leads': dossier.get('current_law_leads', []),
                            'preflight': packet['preflight'][iid]})
    ids = [m['instrument_id'] for m in members]
    if len(ids) != len(set(ids)):
        raise ValueError('overlapping retained membership')
    keys, empty_members, sources, scopekeys = Counter(), set(), {}, set()
    for member in members:
        iid = member['instrument_id']
        for task in member['preflight']['mechanical_tasks']:
            if task['kind'] == 'operative_current_law':
                keys[task['shared_key']] += 1
                if task['shared_key'] == '{}':
                    empty_members.add(iid)
        for lead in member['current_law_leads']:
            proposal, meta = lead.get('proposal', lead), lead.get('meta', lead)
            source = proposal.get('source') or {}
            sourcekey = canon({k: source[k] for k in ('sha256', 'url') if k in source})
            group = sources.setdefault(sourcekey, {'source': json.loads(sourcekey), 'occurrences': 0, 'orders': set()})
            group['occurrences'] += 1
            group['orders'].add(iid)
            identity = {'source': source}
            for field in ('text_path', 'text_sha256', 'basis_code', 'where', 'edition'):
                value = source.get(field, meta.get(field, lead.get(field)))
                if value is not None:
                    identity[field] = value
            scopekeys.add(canon(identity))
    population = {
        'source_pins': pinlist, 'members': ids, 'distinct_members': len(ids),
        'members_with_current_law_tasks': sum(any(t['kind'] == 'operative_current_law' for t in m['preflight']['mechanical_tasks']) for m in members),
        'current_law_task_occurrences': sum(keys.values()), 'existing_unique_shared_keys': len(keys),
        'empty_shared_key_occurrences': keys['{}'], 'empty_shared_key_members': sorted(empty_members),
        'candidate_pointer_scopes_under_declared_identity': len(scopekeys),
        'archive_hash_url_groups': [dict(g, orders=sorted(g['orders'])) for g in sources.values()],
        'coverage': 'Conditional research-routing candidates from the retained snapshot; not current unassigned work, proven necessary prerequisites, review reuse, or legal holds.',
        'observation_limit': 'Snapshot is 17:25Z. Later REPORT/log and earlier DISPOSITION differ; no post-snapshot execution status inferred.'
    }
    return packets, members, population


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, default=Path(__file__).parent / '.source-cache')
    parser.add_argument('--out', type=Path, default=Path(__file__).parent / 'inputs')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for label, batches in [('o25', ['o25']), ('remaining', ['o28', 'o29', 'o30'])]:
        packets, members, population = extract(batches, args.cache)
        outputs = {f'{label}-preflight-exact.json': {'schema': 'babbage-real-preflight-input/v1', 'packets': packets},
                   f'{label}-source-leads-exact.json': {'schema': 'babbage-real-source-leads-input/v1', 'members': members},
                   f'{label}-population-exact.json': population}
        for name, payload in outputs.items():
            (args.out / name).write_text(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n')
        print(json.dumps({'scope': label, 'members': population['distinct_members'],
                          'current_task_members': population['members_with_current_law_tasks'],
                          'task_occurrences': population['current_law_task_occurrences'],
                          'unique_shared_keys': population['existing_unique_shared_keys']}))


if __name__ == '__main__':
    main()
