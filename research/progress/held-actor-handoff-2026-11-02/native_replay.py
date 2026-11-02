"""Replay the held actor handoff through existing native preparation, without claims.

This is a bounded engineering replay of the four Erasmus source-ID gaps. It does
not renew old packets, acquire sources, approve a source, or infer a legal event.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

import replay

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'jobs/claim-kit'))
import assemble as A
import batch as B
import source_supplement as S

IDS = ['EO:8129', 'EO:8163', 'EO:9949', 'EO:11026']


def audit(repo, dest, declaration, blocked):
    parent, before = B.load_packet(dest/'parent', repo)
    packet, after = B.load_packet(dest/'supplement', repo)
    result = {'schema': 'eo-held-actor-handoff-replay/v1',
              'native_verification': S.verify(repo, dest/'supplement'),
              'parent_packet_sha256': B.file_sha(dest/'parent/PACKET.json'),
              'supplement_packet_sha256': B.file_sha(dest/'supplement/PACKET.json'),
              'added_evidence': {}, 'blocked_sources': blocked, 'refusals': {},
              'producer_approval': False, 'independent_review': False,
              'scientific_adoption': False}
    for iid, d in after.items():
        inherited = deepcopy(d)
        inherited.pop('fingerprint'); inherited.pop('source_supplement')
        ids = d['source_supplement']['added_evidence_ids']
        result['added_evidence'][iid] = []
        for eid in ids:
            entry = inherited['evidence'].pop(eid)
            errors = []
            ref = A._reference(eid, d['evidence'], errors)
            assert not errors and A.decode_evidence_id(ref) == eid
            assert ref['quote'] == entry['text']
            assert not any(k in entry for k in ('mechanism', 'effective_date'))
            result['added_evidence'][iid].append({
                'id': eid, 'source': entry['source'],
                'char_start': entry['char_start'], 'char_end': entry['char_end'],
                'quote_sha256': B.digest(ref['quote'].encode('utf-8')),
                'native_reference_round_trip_exact': True})
        original = deepcopy(before[iid]); original.pop('fingerprint')
        assert inherited == original, 'inherited dossier changed'
    # Negative declarations are refused by the unchanged native validator. Do
    # not modify held files or rehash old dossiers to make the controls pass.
    controls = {}
    for key in ('sha256', 'text_sha256'):
        bad = deepcopy(declaration); bad['sources'][0]['source'][key] = '0'*64
        controls['changed_'+key] = (before, bad)
    bad = deepcopy(declaration); bad['sources'][0]['source']['grade'] = 'official'
    controls['invented_grade'] = (before, bad)
    bad = deepcopy(declaration); bad['sources'][0]['char_start'] = True
    controls['boolean_span'] = (before, bad)
    bad = deepcopy(declaration); bad['sources'][0]['instrument_ids'] = ['EO:999999']
    controls['foreign_member'] = (before, bad)
    stale = deepcopy(before); stale[IDS[0]]['fingerprint'] = '0'*64
    controls['stale_dossier'] = (stale, declaration)
    controls['already_supplemented'] = (after, declaration)
    for label, (ds, dec) in controls.items():
        try:
            S.derive(repo, ds, dec, {})
        except ValueError as exc:
            result['refusals'][label] = str(exc)
        else:
            raise AssertionError('negative control accepted: '+label)
    # Rehashing a counterfactual old packet cannot renew its dependency pins.
    # Exercise native load on a temporary copy, leaving the real packet intact.
    with tempfile.TemporaryDirectory() as temp:
        stale_packet = deepcopy(parent)
        stale_packet['preflight_dependency_sha256']['excavate.py'] = '0'*64
        stale_packet.pop('fingerprint')
        stale_packet['fingerprint'] = B.digest(B.canon(stale_packet).encode())
        folder = Path(temp); B.dump(folder/'PACKET.json', stale_packet)
        try:
            B.load_packet(folder, repo)
        except ValueError as exc:
            result['refusals']['rehashed_stale_packet'] = str(exc)
        else:
            raise AssertionError('stale dependency accepted after outer rehash')
    # No producer judgments are entered. The ordinary apply retains every
    # member and emits no claim, including the orders with new source IDs.
    result['native_apply'] = B.apply(repo, dest/'supplement',
                                     dest/'supplement/applied-unreviewed')
    assert result['native_apply']['counts'] == {'unresolved': len(IDS)}
    assert (dest/'supplement/applied-unreviewed/CLAIMS.proposed.jsonl').stat().st_size == 0
    result['inherited_dossiers_unchanged'] = True
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=HERE.parents[2])
    p.add_argument('--write', type=Path, required=True,
                   help='Fresh output directory under this repository research/')
    a = p.parse_args(); repo = a.repo.resolve(); dest = a.write.resolve()
    if dest.exists() or not dest.is_relative_to(repo/'research'):
        p.error('fresh research destination required')
    declaration, blocked = replay.declarations(repo)
    if not declaration['sources']:
        p.error('no exact held raw/text pair is available')
    B.dump(dest/'SOURCES.json', declaration)
    agent = 'codex-held-actor-handoff'
    B.prepare(repo, repo/'jobs/claim-kit/output', dest/'parent', IDS, agent)
    S.prepare(repo, dest/'parent', dest/'SOURCES.json', agent, dest/'supplement')
    result = audit(repo, dest, declaration, blocked)
    B.dump(dest/'RESULT.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
