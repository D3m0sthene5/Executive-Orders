"""Independent adversarial source-screen checks; fixture inputs are synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import assemble
import batch
import current_evidence
import dispatch
import test_readiness_economy_dispatch as fixtures


def run():
    start = time.monotonic()
    results = []
    fixture = fixtures.ReadinessEconomyTests()
    fixture.setUp()
    try:
        folder = fixture.packet()
        claims = fixture.claims(('EO:1',))
        def check(label, value, expect):
            report = dispatch.check_selected(fixture.repo, folder, value)
            assert report['ok'] is expect, (label, report)
            results.append({'case': label, 'ok': report['ok'], 'blockers': report['members'][0]['blockers']})
        check('unchanged exact assembled claim', claims, True)
        changed = copy.deepcopy(claims)
        changed[0].update(schema=assemble.DOSSIER_SCHEMA, fingerprint='first input version')
        first_hash = dispatch.check_selected(fixture.repo, folder, changed)['members'][0]['claim_sha256']
        changed[0]['fingerprint'] = 'second input version'
        second_hash = dispatch.check_selected(fixture.repo, folder, changed)['members'][0]['claim_sha256']
        assert first_hash != second_hash
        assert second_hash == batch.digest(batch.canon(changed[0]).encode())
        results.append({'case': 'spoof dossier schema cannot exclude fingerprint from exact input hash',
                        'hashes_differ': True, 'no_structural_approval': True})
        changed = copy.deepcopy(claims)
        changed[0]['operative_clauses'][0]['first_end']['source']['quote'] += ' altered'
        check('same evidence id altered quote', changed, False)
        changed = copy.deepcopy(claims)
        changed[0]['operative_clauses'][0]['first_end']['source']['evidence_id'] = '!!!'
        check('malformed encoded evidence id', changed, False)
        changed = copy.deepcopy(claims)
        changed[0]['source_refs'] = ['malformed']
        check('malformed selected source list', changed, False)
        changed = copy.deepcopy(claims)
        changed[0]['source_refs'] = [copy.deepcopy(changed[0]['original_representation'])]
        check('exact additional selected source list', changed, True)
        changed = copy.deepcopy(claims)
        changed[0]['claim_kit']['dossier_sha256'] = '0' * 64
        check('stale claim dossier marker', changed, False)
        try:
            dispatch.check_selected(fixture.repo, folder, claims + claims)
        except ValueError:
            results.append({'case': 'duplicate exact claims', 'refused': True})
        else:
            raise AssertionError('duplicate claims accepted')
    finally:
        fixture.doCleanups()
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory)
        base = repo / 'jobs/current-law/output'
        base.mkdir(parents=True)
        body = 'A uniquely cited current source sentence with retained evidence.\n'
        (base / 'legal.txt').write_bytes(body.encode())
        sha = hashlib.sha256(body.encode()).hexdigest()
        source = {'url': 'https://example.gov/legal', 'sha256': 'a' * 64}
        (base / 'SOURCES.jsonl').write_text(json.dumps(dict(source, text_path='legal.txt', text_sha256='b' * 64)) + '\n')
        for location in ('source', 'item'):
            lead = {'source': dict(source), 'snippet': 'uniquely cited current source sentence'}
            target = lead['source'] if location == 'source' else lead
            target['text_path'] = 'legal.txt'
            result, = current_evidence.enrich_current(repo, [lead])
            assert 'evidence_gap' in result and 'text' not in result, (location, result)
            results.append({'case': 'unpinned direct ' + location + ' cannot bypass stale declaration', 'refused': True})
        lead['source'].update(text_path='legal.txt', text_sha256=sha)
        result, = current_evidence.enrich_current(repo, [lead])
        assert result['text'] == lead['snippet'] and 'evidence_gap' not in result
        results.append({'case': 'independently pinned direct text survives stale alternative', 'accepted': True})
    return {'schema': 'sol-readiness-independent-engineering/v1', 'results': results,
            'code_pins': {name: hashlib.sha256((ROOT / 'jobs/claim-kit' / name).read_bytes()).hexdigest()
                          for name in ('dispatch.py', 'current_evidence.py', 'source_supplement.py')},
            'wall_seconds': time.monotonic() - start, 'model_tokens': None,
            'scientific_approval': False, 'same_family_review': True}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
