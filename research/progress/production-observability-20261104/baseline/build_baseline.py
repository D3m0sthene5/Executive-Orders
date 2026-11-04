#!/usr/bin/env python3
"""Read-only, offline normalization of retained/pinned production evidence.

Writes only beside this script. Refuses changed inputs before replacing BASELINE.
The large native CSV is reused from the existing control-center copy only when
its Git object identity equals the exact GitHub native tracker blob.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
PIN = '600ae3018f71025b3e53dc8538b8f92e6e159b76'
PROTECTED = 'cacfb8f4af6db949476bd7bec8220a464055c931'
CSV_BLOB = 'd1c074ce575749d48b4c6509399f74a2c19cd689'
TALLIES_SHA256 = '2d85c3dd9608afda80d6a680b4356f031c19a21f21fd62b95a8655df8506b165'
CHECKS = {
    'text': ['original_text'],
    'commands': ['clause_inventory'],
    'lifecycle': ['provisional_status', 'ending_or_current_basis', 'savings_residuals'],
    'evidence': ['counterevidence', 'shared_sources', 'opus_media'],
}
ACCEPTED = {'done', 'provisional', 'n/a'}

def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def read(path, pin=PIN):
    return json.loads((ROOT / 'inputs' / pin / path).read_text())

def url(path, pin=PIN):
    return f'https://github.com/D3m0sthene5/Executive-Orders/blob/{pin}/{path}'

def main():
    sources = json.loads((ROOT / 'SOURCES.json').read_text())
    for s in sources:
        data = (ROOT / s['local_path']).read_bytes()
        assert blob(data) == s['sha'], f"Changed pinned input: {s['path']}"
        assert hashlib.sha256(data).hexdigest() == s['sha256']
    csv_path = REPO / 'research/progress/control-center/orders.csv'
    data = csv_path.read_bytes()
    assert blob(data) == CSV_BLOB, 'Native readiness CSV identity changed; retain last good BASELINE'
    rows = list(csv.DictReader(data.decode().splitlines()))
    ids = {r['instrument_id'] for r in rows}
    assert len(ids) == len(rows)
    by_id = {r['instrument_id']: r for r in rows}
    summary = read('jobs/readiness-tracker/output/SUMMARY.json')
    tracker = read('jobs/readiness-tracker/output/STATUS.json')
    checker_status = read('jobs/claim-checker/output/STATUS.json')
    checker = read('jobs/claim-checker/output/SUMMARY.json')
    human = read('research/stage19/output/PROGRESS.json')
    assert tracker['result'] == checker_status['result'] == 'succeeded'
    assert tracker['commit_run'] == checker_status['commit_run']
    ready = sum(r['ready_for_human_review'] == 'yes' for r in rows)
    assert len(rows) == summary['orders_total'] and ready == summary['ready_for_human_review']
    assert sum(bool(r['provisional_status']) for r in rows) == summary['orders_with_provisional_status']
    partition = Counter({k: 0 for k in [*CHECKS, 'gates', 'ready']})
    overlap = Counter({k: 0 for k in [*CHECKS, 'gates']})
    only_missing = Counter({k: 0 for k in [*CHECKS, 'gates']})
    blockers = Counter()
    singleton = Counter()
    cross = {k: Counter() for k in [*CHECKS, 'gates']}
    for row in rows:
        # Native SUMMARY counts unique blocker families per order. Raw CSV codes
        # may carry source ids, audit ids or step suffixes after the first colon.
        codes = {x.split(':', 1)[0] for x in filter(None, row['blockers'].split('|'))}
        blockers.update(codes)
        if len(codes) == 1:
            singleton.update(codes)
        if row['ready_for_human_review'] == 'yes':
            partition['ready'] += 1
            continue
        missing = [k for k, fields in CHECKS.items() if any(row['step_' + f] not in ACCEPTED for f in fields)]
        first = missing[0] if missing else 'gates'
        partition[first] += 1
        for cp in missing or ['gates']:
            overlap[cp] += 1
        if len(missing) == 1 or not missing:
            only_missing[first] += 1
        cross[first].update(codes)
    assert sum(partition.values()) == len(rows)
    assert dict(blockers) == {k: v for k, v in summary['orders_blocked_by'].items() if v}
    reservations = read('research/readiness/CLAIM_KIT_LOCK.json')['orders']
    protected_reservations = read('research/readiness/CLAIM_KIT_LOCK.json', PROTECTED)['orders']
    assert reservations == protected_reservations
    batches = read('research/excavator/claude-tribonian-2026-11-04/tools/batches.json', PROTECTED)
    members = [x for group in batches.values() for x in group]
    assert len(members) == len(set(members)) and set(members) <= ids
    tally_bytes = (ROOT / 'ERASMUS_TALLIES.json').read_bytes()
    assert hashlib.sha256(tally_bytes).hexdigest() == TALLIES_SHA256, 'Sanitized tally snapshot changed; retain last good BASELINE'
    retained = json.loads(tally_bytes)
    outcomes = Counter()
    publication_ids = []
    for receipt in retained:
        tally = receipt['tally']
        assert tally['attempted'] == len(tally['outcomes'])
        for outcome in tally['outcomes']:
            assert outcome['instrument_id'] in ids
            outcomes[outcome['outcome']] += 1
            if outcome['outcome'] == 'eligible':
                publication_ids.append(outcome['instrument_id'])
                assert by_id[outcome['instrument_id']]['claim_present'] == 'yes'
    assert sum(x['tally']['claims_published'] for x in retained) == 52
    source = {
        'repository': 'D3m0sthene5/Executive-Orders', 'commit': PIN,
        'tracker': tracker, 'checker': checker_status,
        'readiness': {'path': 'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv', 'git_blob': CSV_BLOB,
                      'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                      'url': url('jobs/readiness-tracker/output/READINESS_BY_ORDER.csv'),
                      'recovery': 'GitHub fetch_file returned empty content for large file; existing control-center/orders.csv is byte-identical to returned native Git blob.'},
        'human': {'path': 'research/stage19/output/PROGRESS.json', 'url': url('research/stage19/output/PROGRESS.json'),
                  'generation_utc': None, 'note': 'Native progress file has no generation timestamp; legacy provisional-status count is not the current status denominator.'},
    }
    gaps = [
        ('worker_active', 'all production', None, 'unavailable', 'No census of current local worker phases or active intervals; publication gaps do not prove inactivity.'),
        ('assigned', 'all production', None, 'unavailable', 'Nine historical reservation records are observed separately; freshness, current assignments and worker activity are not.'),
        ('queued', 'all production', None, 'unavailable', 'Protected plan membership covers1218 orders in40 batches separately. Dispatch and current phase queues are unknown.'),
        ('held', 'protected Tribonian run', None, 'owner_observed_pause', 'Owner reports active run paused waiting for Claude token reset; phase/order membership and elapsed wait not published.'),
        ('awaiting_review', 'all production', None, 'unavailable', 'Tracker has no separate current review queue; latest historical reviews do not give a population denominator.'),
        ('rework', 'Erasmus historical cohort', 1, 'dated_report_open_correction', 'EO11303 correction rejected after reveal; four filed Apollo claims flagged overall. This is not the project rework queue.'),
        ('awaiting_filing', 'all production', None, 'unavailable', 'No complete current join of exact upheld versions, completion and publication states.'),
        ('filed', 'Erasmus Nov2 historical cohort', 52, 'native_tallies', '32 recovered rejects plus20 superseding corrections;52 published claims are not52 net new ready dossiers.'),
        ('ready', 'full pinned census', ready, 'native_tracker', 'Machine readiness for independent human review; no human certification inferred.'),
        ('human_certified', 'native Stage19 documented lower bound', human['independently_reviewed_whole_lifecycle_complete'], 'native_progress', 'Distinct scope from tracker readiness and AI examination.'),
    ]
    queues = [{'queue': a, 'scope': b, 'observed_count': c, 'status': d, 'reason': e} for a,b,c,d,e in gaps]
    job_coverage = [
        {'checkpoint': 'text', 'jobs': ['fr-originals', 'opus-media-match', 'ofr-compilations', 'isthmian-canal-1911', 'indian-reservations-1912', 'richardson-volumes', 'app-executive-orders', 'hathi-gpo-orders', 'numbered-early-orders', 'wikisource-texts', 'csc-annual-reports', 'pinakes-proquest-ingest', 'lachmann', 'source-ladder'], 'consumer': 'readiness-tracker', 'actual_consumption': {k:v for k,v in summary['inputs']['job_outputs_used'].items() if k not in {'claim-checker', 'machine later-source search'}}, 'labor_remaining': 'Retrieval hit is not identity/page examination, original authentication or approved legal text.'},
        {'checkpoint': 'commands', 'jobs': ['clause-drafts', 'claim-kit', 'geddes'], 'consumer': 'claim-checker -> readiness-tracker step_clause_inventory', 'actual_consumption': {'effective_claims_passing_clause_inventory': checker['steps_checker_passed_effective_claims']['clause_inventory']}, 'labor_remaining': 'Source examination for complete operative inventory; heuristic diagnostics do not establish completeness.'},
        {'checkpoint': 'lifecycle', 'jobs': ['later-events', 'current-law', 'corpus-excavator', 'valla', 'claim-kit'], 'consumer': 'claims -> claim-checker -> readiness-tracker', 'actual_consumption': {'machine_later_source_search_records': summary['inputs']['job_outputs_used']['machine later-source search']}, 'labor_remaining': 'Case-specific applicability, occurrence, first ending/current basis and savings reasoning; cached evidence is not a conclusion.'},
        {'checkpoint': 'evidence', 'jobs': ['later-events', 'current-law', 'opus-media-match', 'cruden', 'mountweazel'], 'consumer': 'claims plus shared/media/search inputs -> readiness-tracker', 'actual_consumption': {'shared_sources_applicable': summary['step_done_among_decided']['shared_sources']['applicable'], 'opus_media_applicable': summary['step_done_among_decided']['opus_media']['applicable']}, 'labor_remaining': 'Examine contrary leads and specific sources; independent review may properly repeat source reads.'},
        {'checkpoint': 'gates', 'jobs': ['claim-kit completion', 'mountweazel', 'claim-checker', 'readiness-tracker'], 'consumer': 'exact version review -> completion -> authorized filing -> checker -> tracker', 'actual_consumption': {'claims_checked': checker['claims_checked'], 'orders_with_claim': checker['orders_with_claim'], 'all_checks_passed_claim_records': checker['claims_all_checks_passed'], 'ready_orders': ready}, 'labor_remaining': 'Independent source/legal review, exact-version correction, authorized filing and refreshed native receipts; claim records and order counts differ.'},
    ]
    result = {
        'schema': 'eo-observability-baseline/v1', 'source_pin': PIN, 'finished_utc': tracker['finished_utc'], 'source': source,
        'orders_total': len(rows), 'ready': ready, 'unfinished': len(rows)-ready,
        'human_certified': human['independently_reviewed_whole_lifecycle_complete'],
        'counts': {'orders_total': len(rows), 'ready_for_human_review': ready, 'unfinished': len(rows)-ready,
                   'provisional_status': summary['orders_with_provisional_status'], 'human_certified': human['independently_reviewed_whole_lifecycle_complete'],
                   'ready_by_text_evidence_tier': summary['ready_by_text_evidence_tier'], 'claims_checked': checker['claims_checked'], 'orders_with_claim': checker['orders_with_claim']},
        'first_missing': dict(partition), 'open_anywhere': dict(overlap), 'only_missing_checkpoint': dict(only_missing),
        'final_gate_residuals': [{'instrument_id': r['instrument_id'], 'claim_record_errors': r['claim_record_errors'], 'blockers': r['blockers'], 'scope': 'all listed checks closed but native ready flag is no; not an observed filing queue'} for r in rows if r['ready_for_human_review'] != 'yes' and all(r['step_'+f] in ACCEPTED for fields in CHECKS.values() for f in fields)],
        'display_semantics': 'first_missing partitions every order by first missing check in display order; open_anywhere overlaps unfinished checkpoints. Neither is observed worker location or a sequential production model. Gates counts only unfinished rows with all listed checks closed, not the entire review or filing queue.',
        'blockers': [{'code': code, 'count': count, 'only_recorded_blocker_family': singleton[code]} for code,count in sorted(blockers.items(), key=lambda x: (-x[1], x[0]))],
        'blockers_by_first_missing': {k: dict(sorted(v.items(), key=lambda x: (-x[1], x[0]))) for k,v in cross.items()},
        'queue_coverage': queues,
        'reservations': {'source_path': 'research/readiness/CLAIM_KIT_LOCK.json', 'git_blob': '77897cb71211cff96a7420a06a86f629f5285a4d', 'records': len(reservations), 'by_agent': dict(Counter(x['agent'] for x in reservations.values())), 'protected_branch_same_register': True, 'activity_inference': None},
        'protected_run': {'branch': 'claude/tribonian-2026-11-04', 'commit': PROTECTED, 'plan_batches': len(batches), 'plan_distinct_members': len(set(members)), 'plan_members_ready_at_baseline': sum(by_id[x]['ready_for_human_review']=='yes' for x in members), 'plan_reserved_in_main_register': len(set(members)&set(reservations)), 'local_progress': None, 'usage': None, 'phase_queue_counts': None, 'protection': 'All planned assignments remain protected despite absent reservation entries or published outputs.'},
        'historical_outcomes': {'cohort': 'Erasmus 2026-11-02', 'native_completion_receipts': len(retained), 'sanitized_tallies_sha256': TALLIES_SHA256, 'completion_attempt_members': sum(x['tally']['attempted'] for x in retained), 'completion_outcomes': dict(outcomes), 'claims_published': 52, 'distinct_published_orders': len(set(publication_ids)), 'new_lifecycle_claims_reported': 32, 'superseding_corrections_reported': 20, 'exact_claim_hash_to_global_checker_join': 'not recovered; sample tallies retain exact eligible claim hashes, native summary confirms combined scope only', 'net_new_ready_attributable': None, 'current_queue_inference': None},
        'job_coverage': job_coverage,
        'coverage_limits': ['Published evidence only; no private Opus/Claude logs or quota used.', 'Native tracker generation is Nov2; later published source acquisition is not reflected in that generation.', 'Reservation register is not a live dispatch or labor monitor.', 'Historical completion outcomes include failed and retried versions and must not be summed as unique orders or current queue sizes.', 'Blockers overlap; only-recorded-blocker counts are descriptive and never predicted readiness gains.', 'Reviewer capacity, integration delay and reporting lag cannot be causally apportioned from these records.'],
    }
    target = ROOT / 'BASELINE.json'
    temporary = ROOT / 'BASELINE.json.tmp'
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    temporary.replace(target)
    print(json.dumps({'first_missing': dict(partition), 'open_anywhere': dict(overlap), 'historical_outcomes': result['historical_outcomes']}))

if __name__ == '__main__':
    main()
