import importlib.util
import json
import os
import random
import subprocess
import sys

import pytest

import plant_fixtures
import plants
import tiro_common as C
from conftest import claim

REPO = C.DEFAULT_REPO
sys.path.insert(0, str(REPO / 'jobs/geddes'))
import prereview_checks as G  # noqa: E402


def _load_gate():
    spec = importlib.util.spec_from_file_location('claim_gate', REPO / 'research/stage19/code/claim_gate.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GATE = _load_gate()
NEW_KINDS = ('event_drop', 'clause_misdescription', 'citation_drop')


def flags(c, repo, dossier=None):
    return {(f['code'], f.get('field') or json.dumps(f.get('fields'))) for f in G.check(c, dossier, repo)['flags']}


def plant(kind, c, seed='s'):
    k = plants.KINDS[kind]
    ctx = {'claims': [c]}
    assert k.eligible(c, ctx), kind
    return k.plant_one(c, random.Random(seed), ctx)


# The original kind --------------------------------------------------------------------------------------------------
def test_shift_date_and_leap_day():
    assert plants.shift_date('1950-06-30') == '1947-06-30'
    assert plants.shift_date('1960-02-29') == '1957-02-28'
    assert plants.shift_date('1950-06-30T00:00') == '1947-06-30T00:00'
    assert plants.shift_date('unknown') == 'unknown'
    assert plants.shift_date(None) is None


def test_control_count_matches_old_rounding():
    assert [plants.control_count(n) for n in (0, 1, 15, 22, 23, 30, 37, 38)] == [0, 1, 1, 1, 2, 2, 2, 3]


def test_end_mode_plants_only_end_dates_and_keys_hash_both_versions():
    claims = [claim('EO:1'), claim('EO:2', end='1960-02-29'), claim('EO:3', end=None)]
    made = plants.make_controls(claims, 'b01', kind='date_shift')
    assert made['mode'] == 'end' and len(made['controls']) == 1
    k = made['controls'][0]
    assert k['instrument_id'] in ('EO:1', 'EO:2') and k['kind'] == 'date_shift' and k['type'] == 'date_shift_end'
    planted = next(r for r in made['review_rows'] if r['instrument_id'] == k['instrument_id'])
    genuine = made['genuine'][0]
    assert C.canon(planted) == k['planted'] and C.canon(genuine) == k['genuine']
    assert planted['identity'] == genuine['identity']
    assert planted['whole_order_end']['date'] != genuine['whole_order_end']['date']
    assert [r['instrument_id'] for r in made['review_rows']] == ['EO:1', 'EO:2', 'EO:3']
    # Seeded by batch name: the same draw every time.
    assert plants.make_controls(claims, 'b01', kind='date_shift')['controls'] == made['controls']


def test_event_and_signing_modes():
    ev = [claim('EO:5', end=None, events=[{'effective_date': '1970-01-01'}])]
    made = plants.make_controls(ev, 'x', kind='date_shift')
    assert made['mode'] == 'event'
    assert made['review_rows'][0]['operative_clauses'][0]['later_events'][0]['effective_date'] == '1967-01-01'
    made = plants.make_controls([claim('EO:6', end=None)], 'x', kind='date_shift')
    assert made['mode'] == 'signing' and made['review_rows'][0]['identity']['signing_date'] == '1937-01-15'


def test_names_defect_uses_the_kind_words_and_old_keys_default_to_date_shift():
    old_key = {'instrument_id': 'EO:1', 'defect': 'x'}  # written before kinds existed
    assert plants.names_defect({'verdict': 'rejected', 'defects': ['first_end wrong year']}, old_key)
    assert not plants.names_defect({'verdict': 'rejected', 'defects': ['quote mismatch']}, old_key)
    assert not plants.names_defect({'verdict': 'upheld', 'defects': ['date']}, old_key)
    assert not plants.names_defect(None, old_key)


# The three new kinds on realistic claims -----------------------------------------------------------------------------
@pytest.fixture
def real(tmp_path):
    yes, no = plant_fixtures.build(tmp_path)
    return tmp_path, yes, no


def test_fixture_claims_pass_the_gate_and_geddes(real):
    repo, yes, no = real
    for c in (yes, no):
        assert GATE.validate_claim(c) == [], c['instrument_id']
        assert G.check(c, None, repo)['flags'] == [], c['instrument_id']


@pytest.mark.parametrize('kind,which', [(k, w) for k in NEW_KINDS for w in ('yes', 'no')])
def test_new_kinds_stay_schema_valid_and_trip_no_geddes_check(real, kind, which):
    repo, yes, no = real
    c = yes if which == 'yes' else no
    k = plants.KINDS[kind]
    if not k.eligible(c, {'claims': [c]}):
        assert (kind, which) == ('event_drop', 'no')  # the NO fixture records no later events
        return
    p, info = plant(kind, c)
    assert C.canon(p) != C.canon(c) and info['changed'] and info['defect'] and info['match']
    assert GATE.validate_claim(p) == []
    assert flags(p, repo) <= flags(c, repo) == set()
    # Every source the plant cites is one the genuine claim already cites (the kit's dossier-evidence rule).
    cited = lambda x: {json.dumps(s, sort_keys=True) for s in _sources(x)}
    assert cited(p) <= cited(c)


def _sources(o):
    if isinstance(o, dict):
        if 'text_path' in o and 'quote' in o:
            yield o
        for v in o.values():
            yield from _sources(v)
    elif isinstance(o, list):
        for v in o:
            yield from _sources(v)


def test_date_shift_is_caught_mechanically_by_geddes(real):
    repo, yes, no = real
    p, _ = plants.DateShift().plant(no, 'end')
    assert 'end_year_conflicts_reasons' in {f[0] for f in flags(p, repo)}
    p, _ = plants.DateShift().plant(yes, 'event')
    assert 'date_before_signing' in {f[0] for f in flags(p, repo)}


def test_event_drop_removes_one_unnamed_middle_notice_and_lowers_the_count(real):
    repo, yes, _ = real
    p, info = plant('event_drop', yes)
    actors = [e['actor'] for e in p['operative_clauses'][0]['later_events']]
    assert actors == ['FRDOC:2002-0001', 'FRDOC:2004-0001', 'EO:33333']  # not the named amendment, not an edge notice
    assert 'two continuation notices' in p['research_rationale'] and 'three' not in p['research_rationale']
    assert info['match'] == ['FRDOC:2003-0001', '2003-0001'] and 'lowered from 3 to 2' in info['defect']


def test_event_drop_keeps_the_fr_capture_disclosure_exact(real):
    repo, yes, _ = real
    for e in yes['operative_clauses'][0]['later_events'][:3]:
        e['source']['instrument_id'] = e['actor']
    rows = [{k: e['source'][k] for k in ('instrument_id', 'url', 'sha256', 'text_path', 'text_sha256')}
            for e in yes['operative_clauses'][0]['later_events'][:3]]
    yes['fr_fulltext_captures'] = {'grade': 'g', 'captures': rows}
    p, _ = plant('event_drop', yes)
    assert [r['instrument_id'] for r in p['fr_fulltext_captures']['captures']] == ['FRDOC:2002-0001', 'FRDOC:2004-0001']


def test_clause_misdescription_modes(real):
    repo, yes, no = real
    p, info = plant('clause_misdescription', yes)
    x = p['operative_clauses'][1]
    assert info['mode'] == 'ended_to_operative' and x['state_at_cutoff'] == 'operative' and 'first_end' not in x
    assert x['current_predicate']['source'] == x['original_source'] and x['current_predicate']['checked_through'] == '2026-10-14'
    p, info = plant('clause_misdescription', no)
    assert info['mode'] == 'state_swap' and 'never_activated' in [x['state_at_cutoff'] for x in p['operative_clauses']]


def test_citation_drop_removes_the_foreign_source_everywhere_and_keeps_the_conclusion(real):
    repo, yes, no = real
    p, info = plant('citation_drop', no)
    assert all(x['first_end']['source'] == x['original_source'] for x in p['operative_clauses'])
    assert p['whole_order_end']['source'] == p['original_representation']
    assert p['whole_order_end']['date'] == no['whole_order_end']['date'] and 'EO:22223' in info['match']
    p, info = plant('citation_drop', yes)
    assert p['operative_clauses'][1]['first_end']['source'] == yes['operative_clauses'][1]['original_source']
    assert p['operative_clauses'][0] == yes['operative_clauses'][0]  # the amendment's source is a later event's: kept


def test_rotation_is_seeded_recorded_and_falls_back(real):
    repo, yes, no = real
    claims = [yes, no] + [claim(f'EO:{i}') for i in range(100, 128)]  # 30 claims -> 2 controls
    made = plants.make_controls(claims, 'b07')
    assert made['seed'] == 'b07' and made['rotation'] == plants.rotation_order('b07') and len(made['controls']) == 2
    assert made == plants.make_controls(claims, 'b07')
    kinds = [k['kind'] for k in made['controls']]
    assert len(set(kinds)) == 2 and all(k in plants.KINDS for k in kinds)
    other = plants.make_controls(claims, 'b07', seed='another')
    assert other['seed'] == 'another'
    starts = {plants.rotation_order(f'y{i:02d}')[0] for i in range(1, 30)}
    assert starts == set(plants.ROTATION)  # over a wave's batch names every kind leads somewhere
    for k in made['controls']:
        assert k['defect'] and k['mode'] and k['type'].startswith(k['kind'])


def test_single_kind_with_no_eligible_claim_is_a_refusal():
    with pytest.raises(ValueError, match='fits no claim'):
        plants.make_controls([claim('EO:1')], 'b01', kind='citation_drop')


def test_names_defect_for_new_kinds_needs_the_identifier_and_a_kind_word():
    k = {'kind': 'event_drop', 'match': ['FRDOC:2003-0001', '2003-0001']}
    yes = {'verdict': 'rejected', 'defects': [{'field': 'later_events', 'problem': 'the 2003 notice (FR Doc. 2003-0001) is missing'}]}
    assert plants.names_defect(yes, k)
    assert not plants.names_defect({'verdict': 'rejected', 'defects': ['later events missing for 2007']}, k)
    assert not plants.names_defect({'verdict': 'rejected', 'defects': ['2003-0001 quoted fine']}, k)
    c = {'kind': 'clause_misdescription', 'match': ['EO:12345#sec2', 'sec2']}
    assert plants.names_defect({'verdict': 'rejected', 'defects': ['operative_clauses[EO:12345#sec2].state_at_cutoff is wrong: revoked in 2003']}, c)
    assert not plants.names_defect({'verdict': 'rejected', 'defects': ['sec2-a state_at_cutoff wrong']}, c)


# Real claims from today's waves (read from git; skipped when the history is not available) --------------------------
REAL = [('research/excavator/claude-baldus-2026-11-25/y16/packet-v3/applied-v1/CLAIMS.proposed.jsonl', 'EO:13757'),
        ('research/excavator/claude-baldus-2026-11-25/n02/packet-v2/applied-v1/CLAIMS.proposed.jsonl', 'EO:13322'),
        ('research/excavator/claude-baldus-2026-11-25/y05/packet/applied-v1/CLAIMS.proposed.jsonl', 'EO:11755')]


def _git_claim(path, iid):
    r = subprocess.run(['git', '-c', 'gc.auto=0', 'show', f'HEAD:{path}'], cwd=REPO, capture_output=True, text=True)
    if r.returncode:
        pytest.skip(f'{path} not in this checkout history')
    return next(json.loads(l) for l in r.stdout.splitlines() if l.strip() and json.loads(l)['instrument_id'] == iid)


@pytest.mark.parametrize('path,iid', REAL)
def test_real_claims_every_new_kind_passes_gate_and_geddes(path, iid):
    c = _git_claim(path, iid)
    base_gate, base = GATE.validate_claim(c), flags(c, REPO)
    tried = 0
    for kind in NEW_KINDS:
        if not plants.KINDS[kind].eligible(c, {'claims': [c]}):
            continue
        p, info = plant(kind, c, iid)
        tried += 1
        assert set(GATE.validate_claim(p)) <= set(base_gate), (iid, kind)
        assert flags(p, REPO) <= base, (iid, kind, info['defect'])
    assert tried


@pytest.mark.skipif(not os.environ.get('TIRO_KIT_CHECK'), reason='slow (about 20 s a claim): set TIRO_KIT_CHECK=1')
@pytest.mark.parametrize('path,iid', REAL)
def test_real_claims_pass_the_claim_kit_check_where_the_genuine_does(path, iid):
    sys.path.insert(0, str(REPO / 'jobs/claim-kit'))
    import assemble
    import batch
    pk = subprocess.run(['git', '-c', 'gc.auto=0', 'show', f"HEAD:{path.rsplit('/applied-', 1)[0]}/PACKET.json"],
                        cwd=REPO, capture_output=True, text=True)
    if pk.returncode:
        pytest.skip('PACKET.json not in history')
    dossier = batch.decode(json.loads(pk.stdout))[iid]
    c = _git_claim(path, iid)
    base = set(assemble.check_claim(c, REPO, dossier))
    for kind in NEW_KINDS:
        if plants.KINDS[kind].eligible(c, {'claims': [c]}):
            p, _ = plant(kind, c, iid)
            assert set(assemble.check_claim(p, REPO, dossier)) <= base, (iid, kind)
