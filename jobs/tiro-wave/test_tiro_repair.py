import copy
import json

import pytest

import plant_fixtures
import tiro
import tiro_common as C
import tiro_finish
import tiro_repair
from conftest import claim, write_jsonl

PAGE = 'operative_clauses[EO:12345#sec3].original_source.page_or_item'


def rec(c, verdict, defects=(), reviewer='r'):
    return {'instrument_id': c['instrument_id'], 'claim_sha256': c if isinstance(c, str) else C.canon(c),
            'verdict': verdict, 'defects': list(defects), 'reviewer': reviewer, 'review_kind': 'independent_ai_source_review',
            'scope': 'whole_case'}


def page_defect(**kw):
    d = {'field': PAGE, 'problem': 'label says PDF page 2 but the span is on PDF page 1', 'class': 'page_label',
         'locality': 'LOCAL', 'fields': [PAGE]}
    d.update(kw)
    return d


@pytest.fixture
def batch(world):
    """b01 with a YES claim (EO:12345), a NO claim (EO:12346) and a planted control (EO:3)."""
    pk, wave = world['packet'], world['wave']
    yes, no = plant_fixtures.build(world['repo'])
    ctrl = claim('EO:3')
    claims = [yes, no, ctrl]
    write_jsonl(pk / 'applied-v1' / 'CLAIMS.proposed.jsonl', claims)
    (pk / 'APPLIED_FOR_REVIEW').write_text('applied-v1\n')
    key = {'batch': 'b01', 'applied': 'applied-v1',
           'controls': [{'instrument_id': 'EO:3', 'planted': 'p' * 64, 'genuine': C.canon(ctrl), 'kind': 'date_shift',
                         'defect': 'every first_end and whole_order_end date moved back three years'}]}
    wave.key_path('b01').parent.mkdir(parents=True, exist_ok=True)
    wave.key_path('b01').write_text(json.dumps(key))
    world.update(yes=yes, no=no, ctrl=ctrl, claims=claims)
    return world


def reviews(world, rejecting='A', yes_defects=None, no_b=None):
    pk, yes, no, ctrl = world['packet'], world['yes'], world['no'], world['ctrl']
    planted = {'instrument_id': 'EO:3', 'claim_sha256': 'p' * 64, 'verdict': 'rejected',
               'defects': ['whole_order_end date three years early'], 'reviewer': 'x'}
    other = 'B' if rejecting == 'A' else 'A'
    recs = {rejecting: [rec(yes, 'rejected', yes_defects or [page_defect()], reviewer=f'rev-{rejecting}')],
            other: [rec(yes, 'upheld', reviewer=f'rev-{other}')]}
    recs['A'] += [rec(no, 'upheld', reviewer='rev-A'), planted]
    recs['B'] += [no_b or rec(no, 'upheld', reviewer='rev-B'), planted]
    for a in 'AB':
        write_jsonl(pk / 'reviews' / f'BLIND_REVIEW_{a}.jsonl', recs[a])
        write_jsonl(pk / 'reviews' / f'AFTER_REVEAL_{a}.jsonl', [rec(ctrl, 'upheld_after_reveal', reviewer=f'rev-{a}')])


def repaired(world, name, edit):
    claims = copy.deepcopy(world['claims'])
    edit({c['instrument_id']: c for c in claims})
    write_jsonl(world['packet'] / name / 'CLAIMS.proposed.jsonl', claims)
    return {c['instrument_id']: c for c in claims}


def fix_page(cs):
    x = cs['EO:12345']['operative_clauses'][2]
    x['original_source']['page_or_item'] = x['current_predicate']['source']['page_or_item'] = '66 FR 1, PDF page 1'


# Paths ------------------------------------------------------------------------------------------------------------
def test_claim_diff_names_clauses_by_scope_and_events_by_actor(batch):
    a = batch['yes']
    b = copy.deepcopy(a)
    b['operative_clauses'][0]['later_events'].pop(1)
    b['operative_clauses'][1]['first_end']['date'] = '2003-03-04'
    b['research_rationale'] += ' More.'
    assert C.claim_diff(a, b) == ['operative_clauses[EO:12345#sec1].later_events[FRDOC:2003-0001]',
                                  'operative_clauses[EO:12345#sec2].first_end.date', 'research_rationale']
    assert C.value_at(a, 'operative_clauses[EO:12345#sec2].first_end.date') == '2003-03-03'
    assert C.value_at(a, 'operative_clauses[EO:12345#sec1].later_events[EO:33333].effective_date') == '2005-05-05'
    assert C.value_at(a, 'later_source_search[0].checked_on') == '2026-11-11'
    assert C.value_at(a, 'operative_clauses[EO:12345#nope]') is None
    assert C.claim_diff(a, copy.deepcopy(a)) == []


def test_field_map_is_conservative():
    page = [tiro_repair.normalize_defect(page_defect())]
    assert tiro_repair.allowed(PAGE, page)
    assert tiro_repair.allowed('operative_clauses[EO:12345#sec3].current_predicate.source.char_start', page)
    assert not tiro_repair.allowed('operative_clauses[EO:12345#sec3].original_source.quote', page)
    assert not tiro_repair.allowed('operative_clauses[EO:12345#sec3].judgment_reason', page)
    assert not tiro_repair.allowed('operative_clauses[EO:12345#sec2].original_source.page_or_item', page)
    mis = [tiro_repair.normalize_defect({'class': 'misdescription', 'locality': 'LOCAL',
                                         'fields': ['operative_clauses[S].state_at_cutoff']})]
    for p in ('operative_clauses[S].state_at_cutoff', 'operative_clauses[S].first_end', 'operative_clauses[S].current_predicate',
              'operative_clauses[S].judgment_reason'):
        assert tiro_repair.allowed(p, mis), p
    for p in ('operative_clauses[T].state_at_cutoff', 'whole_order_end', 'whole_order_status', 'operative_clauses[S].later_events[EO:1]'):
        assert not tiro_repair.allowed(p, mis), p
    om = [tiro_repair.normalize_defect({'class': 'omission', 'locality': 'LOCAL', 'fields': ['operative_clauses[S].later_events']})]
    assert tiro_repair.allowed('operative_clauses[S].later_events[EO:9]', om) and tiro_repair.allowed('fr_fulltext_captures', om)
    for cls in ('convention', 'other'):
        assert tiro_repair.normalize_defect({'class': cls, 'locality': 'LOCAL', 'fields': ['research_rationale']})['status'] \
            == f'class_{cls}_not_repairable'
    assert tiro_repair.normalize_defect({'field': 'x / y', 'problem': 'p'})['status'] == 'untagged'
    assert tiro_repair.normalize_defect(page_defect(locality='STRUCTURAL'))['status'] == 'structural'


# repair-prep ------------------------------------------------------------------------------------------------------
def test_repair_prep_lists_only_one_arm_local_rejections(batch):
    reviews(batch, no_b=rec(batch['no'], 'rejected', [{'field': 'whole_order_end', 'problem': 'cover date',
                                                        'class': 'convention', 'locality': 'LOCAL',
                                                        'fields': ['whole_order_end.date']}], reviewer='rev-B'))
    res = tiro_repair.repair_prep(batch['wave'], 'b01', batch['packet'])
    assert res['repairable'] == ['EO:12345']
    assert res['not_repairable'] == {'EO:12346': 'not_repairable: class_convention_not_repairable',
                                     'EO:3': 'planted_control_never_repairable'}
    t = open(res['prompt'], encoding='utf-8').read()
    assert 'label says PDF page 2 but the span is on PDF page 1' in t and 'page_or_item' in t
    assert 'applied-v2' in t and '{{' not in t and 'EO:12346' not in t
    assert sorted(p.name for p in batch['packet'].iterdir()) == sorted(
        ['ADMISSION.json', 'APPLIED_FOR_REVIEW', 'DISPATCH_CHECK.json', 'RATIONALES.json', 'applied-v1', 'clauses.csv',
         'decisions.csv', 'reviews'])  # nothing written in the packet


def test_repair_prep_refuses_both_arm_rejections_and_untagged_defects(batch, tmp_path):
    reviews(batch, yes_defects=[{'field': 'operative_clauses[EO:12345#sec3] / page', 'problem': 'wrong page'}],
            no_b=rec(batch['no'], 'rejected', [page_defect()], reviewer='rev-B'))
    pk = batch['packet']
    rows = C.load_jsonl(pk / 'reviews' / 'BLIND_REVIEW_A.jsonl')
    rows[1]['verdict'] = 'rejected'  # EO:12346 now rejected by both arms
    write_jsonl(pk / 'reviews' / 'BLIND_REVIEW_A.jsonl', rows)
    res = tiro_repair.repair_prep(batch['wave'], 'b01', pk)
    assert res['repairable'] == [] and res['prompt'] is None
    assert res['not_repairable']['EO:12346'] == 'rejected_by_both_arms_not_repairable'
    assert res['not_repairable']['EO:12345'] == 'not_repairable: untagged'
    tags = tmp_path / 'tags.json'
    tags.write_text(json.dumps({'EO:12345': [{'class': 'page_label', 'locality': 'LOCAL', 'fields': [PAGE]}]}))
    res = tiro_repair.repair_prep(batch['wave'], 'b01', pk, tags)
    assert res['repairable'] == ['EO:12345']
    plan = json.loads(open(res['plan']).read())
    d = next(r for r in plan['orders'] if r['instrument_id'] == 'EO:12345')['defects'][0]
    assert d['tag_source']['sha256'] == C.file_sha(tags)


# repair-check -----------------------------------------------------------------------------------------------------
def test_repair_check_accepts_a_fix_of_only_the_flagged_field(batch):
    reviews(batch)
    tiro_repair.repair_prep(batch['wave'], 'b01', batch['packet'])
    new = repaired(batch, 'applied-v2', fix_page)
    res = tiro_repair.repair_check(batch['wave'], 'b01', batch['packet'], 'applied-v2', batch_check=False)
    assert res['accepted'] == ['EO:12345'] and res['refused'] == {} and list(res['recheck_prompts']) == ['A']
    receipt = json.loads((batch['packet'] / 'REPAIR_RECEIPT.json').read_text())
    e = receipt['repairs'][0]
    assert e['new_claim_sha256'] == C.canon(new['EO:12345']) and e['rejecting_arm'] == 'A' and e['carried_arm'] == 'B'
    assert sorted(e['changed_paths']) == ['operative_clauses[EO:12345#sec3].current_predicate.source.page_or_item', PAGE]
    carried = C.load_jsonl(batch['packet'] / 'reviews' / 'REPAIR_CARRIED_B.jsonl')
    assert carried[0]['claim_sha256'] == e['new_claim_sha256'] and carried[0]['reviewer'] == 'rev-B'
    assert carried[0]['review_carried_from_claim_sha256'] == C.canon(batch['yes'])
    t = open(res['recheck_prompts']['A'], encoding='utf-8').read()
    assert 'RECHECK_A.jsonl' in t and '66 FR 1, PDF page 1' in t and 'flagged_point_only' in t and '{{' not in t
    assert C.load_jsonl(batch['wave'].scr('repair', 'b01', 'RECHECK_SET_A.jsonl'))[0] == new['EO:12345']


def test_repair_check_refuses_a_fix_beyond_the_flagged_point(batch):
    reviews(batch)
    tiro_repair.repair_prep(batch['wave'], 'b01', batch['packet'])

    def overreach(cs):
        fix_page(cs)
        cs['EO:12345']['operative_clauses'][2]['judgment_reason'] += ' Also reworded.'
    repaired(batch, 'applied-v2', overreach)
    out = []
    res = tiro_repair.repair_check(batch['wave'], 'b01', batch['packet'], 'applied-v2', batch_check=False, emit=out.append)
    assert res['accepted'] == [] and res['refused'] == {'EO:12345': ['operative_clauses[EO:12345#sec3].judgment_reason']}
    assert tiro.main(['--repo', str(batch['repo']), '--wave', 'tw-2026-01-02', '--scratch', str(batch['wave'].scratch),
                      'repair-check', 'b01', 'applied-v2', '--no-batch-check', '--force'], emit=out.append) == 1


def test_repair_check_refuses_when_another_order_changed_or_a_batch_check_fails(batch):
    reviews(batch)
    tiro_repair.repair_prep(batch['wave'], 'b01', batch['packet'])

    def stray(cs):
        fix_page(cs)
        cs['EO:12346']['research_rationale'] += ' x'
    repaired(batch, 'applied-v2', stray)
    with pytest.raises(C.TiroError, match='outside the repair plan'):
        tiro_repair.repair_check(batch['wave'], 'b01', batch['packet'], 'applied-v2', batch_check=False)
    repaired(batch, 'applied-v3', fix_page)
    batch['fake'].handler = lambda cmd, cwd, env: C.Result(1, '', 'fail') if 'batch-check' in cmd else None
    with pytest.raises(C.TiroError, match='batch-check failed'):
        tiro_repair.repair_check(batch['wave'], 'b01', batch['packet'], 'applied-v3')
    assert not (batch['packet'] / 'REPAIR_RECEIPT.json').exists()


def test_repair_check_refuses_when_the_reviewed_claims_changed(batch):
    reviews(batch)
    tiro_repair.repair_prep(batch['wave'], 'b01', batch['packet'])
    p = batch['packet'] / 'applied-v1' / 'CLAIMS.proposed.jsonl'
    p.write_text(p.read_text() + '\n')
    repaired(batch, 'applied-v2', fix_page)
    with pytest.raises(C.TiroError, match='changed since repair-prep'):
        tiro_repair.repair_check(batch['wave'], 'b01', batch['packet'], 'applied-v2', batch_check=False)


# finish with a receipt --------------------------------------------------------------------------------------------
def completion_handler(world):
    pk = world['packet']

    def handler(cmd, cwd, env):
        if any(x.endswith('make_completion.py') for x in cmd):
            i = next(n for n, x in enumerate(cmd) if x.endswith('make_completion.py'))
            applied = cmd[i + 2]
            members = [{'instrument_id': c['instrument_id'], 'outcome': 'submit', 'claim_sha256': C.canon(c)}
                       for c in C.load_jsonl(f'{applied}/CLAIMS.proposed.jsonl')]
            (pk / 'completion').mkdir(exist_ok=True)
            (pk / 'completion' / 'COMPLETION.json').write_text(json.dumps({'members': members, 'controls': []}))
            return C.Result(0, '{}', '')
        if 'publication-name' in cmd:
            return C.Result(0, json.dumps({'path': 'research/readiness/claims/x.jsonl', 'other_owner_members': []}), '')
        if 'complete' in cmd:
            return C.Result(0, 'completed', '')
    world['fake'].handler = handler


def run_finish(world):
    completion_handler(world)
    rc = tiro_finish.finish(world['wave'], 'b01', world['packet'], emit=lambda s: None,
                            repair_receipt=str(world['packet'] / 'REPAIR_RECEIPT.json'))
    m = json.loads((world['packet'] / 'completion' / 'COMPLETION.json').read_text())
    mk = next(c for c, _ in world['fake'].calls if any(x.endswith('make_completion.py') for x in c))
    return rc, {x['instrument_id']: x for x in m['members']}, mk


@pytest.mark.parametrize('rejecting', ['A', 'B'])
def test_finish_counts_the_carried_uphold_and_the_recheck_for_the_exact_new_hash(batch, rejecting):
    reviews(batch, rejecting=rejecting)
    tiro_repair.repair_prep(batch['wave'], 'b01', batch['packet'])
    new = repaired(batch, 'applied-v2', fix_page)
    tiro_repair.repair_check(batch['wave'], 'b01', batch['packet'], 'applied-v2', batch_check=False)
    # Without the re-check the repaired claim is blocked.
    rc, members, mk = run_finish(batch)
    assert rc == 0 and members['EO:12345']['outcome'] == 'blocked' and 'Fix-and-recheck' in members['EO:12345']['reason']
    assert members['EO:12346']['outcome'] == 'submit' and members['EO:3']['outcome'] == 'submit'
    i = next(n for n, x in enumerate(mk) if x.endswith('make_completion.py'))
    assert mk[i + 2].endswith('applied-v2')
    other = 'B' if rejecting == 'A' else 'A'
    if other == 'A':
        assert mk[i + 3].endswith('BLIND_REVIEW_A.jsonl,' + str(batch['packet'] / 'reviews' / 'REPAIR_CARRIED_A.jsonl'))
    # A re-check by someone other than the rejecting reviewer does not count.
    write_jsonl(batch['packet'] / 'reviews' / f'RECHECK_{rejecting}.jsonl',
                [rec(new['EO:12345'], 'upheld', reviewer='someone-else')])
    batch['fake'].calls.clear()
    rc, members, mk = run_finish(batch)
    assert members['EO:12345']['outcome'] == 'blocked' and 'not the rejecting reviewer' in members['EO:12345']['reason']
    write_jsonl(batch['packet'] / 'reviews' / f'RECHECK_{rejecting}.jsonl',
                [rec(new['EO:12345'], 'upheld', reviewer=f'rev-{rejecting}')])
    batch['fake'].calls.clear()
    rc, members, mk = run_finish(batch)
    assert rc == 0 and members['EO:12345']['outcome'] == 'submit' and members['EO:12345']['claim_sha256'] == C.canon(new['EO:12345'])
    assert f'RECHECK_{rejecting}.jsonl' in ' '.join(mk) and 'REPAIR_RECEIPT.json' in ' '.join(mk)


def test_finish_refuses_a_receipt_that_no_longer_matches(batch):
    reviews(batch)
    tiro_repair.repair_prep(batch['wave'], 'b01', batch['packet'])
    repaired(batch, 'applied-v2', fix_page)
    tiro_repair.repair_check(batch['wave'], 'b01', batch['packet'], 'applied-v2', batch_check=False)
    f = batch['packet'] / 'reviews' / 'REPAIR_CARRIED_B.jsonl'
    f.write_text(f.read_text().replace('rev-B', 'rev-Z'))
    with pytest.raises(C.TiroError, match='changed since repair-check'):
        run_finish(batch)


def test_pair_rule_with_repairs_unit():
    key = {'controls': []}
    members = [{'instrument_id': 'EO:1', 'outcome': 'submit', 'claim_sha256': 'n'}]
    good = {'n': {'records': {'A': {'verdict': 'upheld', 'claim_sha256': 'n'}, 'B': {'verdict': 'upheld', 'claim_sha256': 'n'}},
                  'problems': []}}
    out, demoted = tiro_finish.pair_rule(members, key, {'A': {}, 'B': {}}, {'A': {}, 'B': {}}, repairs=good)
    assert demoted == [] and out[0]['outcome'] == 'submit'
    bad = copy.deepcopy(good)
    bad['n']['records']['A'] = {'verdict': 'rejected', 'claim_sha256': 'n', 'defects': ['still wrong']}
    out, demoted = tiro_finish.pair_rule(members, key, {'A': {}, 'B': {}}, {'A': {}, 'B': {}}, repairs=bad)
    assert demoted == ['EO:1'] and 'still wrong' in out[0]['reason']


def test_cli_repair_prep(batch):
    reviews(batch)
    out = []
    assert tiro.main(['--repo', str(batch['repo']), '--wave', 'tw-2026-01-02', '--scratch', str(batch['wave'].scratch),
                      'repair-prep', 'b01'], emit=out.append) == 0
    assert json.loads(out[-1])['repairable'] == ['EO:12345']
