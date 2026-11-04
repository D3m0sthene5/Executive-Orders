"""Independently recheck retained source-delivery packet and selected sources."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import batch
import dispatch
import source_supplement


def audit(destination):
    destination = ROOT / destination
    receipt = json.loads((destination / 'RECEIPT.json').read_bytes())
    for rel, expected in receipt['pins'].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected, rel
    assert hashlib.sha256((destination / 'SOURCE_DECLARATIONS.json').read_bytes()).hexdigest() == receipt['declarations_sha256']
    assert hashlib.sha256((destination / 'supplemented/PACKET.json').read_bytes()).hexdigest() == receipt['packet_sha256']
    verified = source_supplement.verify(ROOT, destination / 'supplemented')
    parent_packet, parent = batch.load_packet(destination / 'parent', ROOT)
    packet, dossiers = batch.load_packet(destination / 'supplemented', ROOT)
    batch.validate_runtime(packet)
    refs = set()
    delivered = 0
    for iid, actual in dossiers.items():
        unchanged = {k: v for k, v in actual.items() if k not in ('fingerprint', 'source_supplement', 'evidence')}
        assert unchanged == {k: v for k, v in parent[iid].items() if k not in ('fingerprint', 'source_supplement', 'evidence')}
        assert {k: v for k, v in actual['evidence'].items() if not k.startswith('SUPPLEMENT:')} == parent[iid]['evidence']
        for eid, evidence in actual['evidence'].items():
            if not eid.startswith('SUPPLEMENT:'):
                continue
            source = evidence['source']
            assert hashlib.sha256((ROOT / source['local_path']).read_bytes()).hexdigest() == source['sha256']
            raw = (ROOT / source['text_path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == source['text_sha256']
            assert raw.decode('utf-8')[evidence['char_start']:evidence['char_end']] == evidence['text']
            refs.add(source['sha256'])
            assert eid in batch.views(ROOT, destination / 'supplemented', [iid])[iid]
            delivered += 1
    probes = json.loads((destination / 'supplemented/ENGINEERING_SOURCE_PROBES.json').read_bytes())
    arms = {}
    for name, claims in probes['arms'].items():
        expected = json.loads((destination / 'supplemented' / ('ENGINEERING_GUARD_' + name.upper() + '.json')).read_bytes())
        actual = dispatch.check_selected(ROOT, destination / 'supplemented', claims)
        assert actual['code_pins'] == expected['code_pins']
        assert actual['ok'] == expected['ok']
        assert actual['members'] == expected['members']
        arms[name] = {'ok': actual['ok'], 'members': len(actual['members']),
                      'unique_custody_checks': actual['unique_custody_checks'],
                      'consolidated_recovery_tasks': len(actual['source_recovery_tasks'])}
    assert arms['delivered_official_excerpts']['ok'] is True
    assert arms['inherited_mirror_excerpt']['ok'] is False
    return {'same_family_independent_engineering': True, 'native_verify': verified,
            'all_receipt_input_pins_verified': True, 'member_dossiers': len(dossiers),
            'delivered_excerpts': delivered, 'unique_original_sources': len(refs),
            'unchanged_parent_fields': True, 'independently_repeated_selected_source_arms': arms,
            'scientific_approval': False, 'legal_application_review': False}


if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1]), indent=2))
