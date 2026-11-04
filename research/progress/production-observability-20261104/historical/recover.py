#!/usr/bin/env python3
"""Recover published aggregate usage and exact native outcomes, without private logs.

Run from any directory. All writes stay next to this script. Inputs are public
files at PIN, verified against SOURCE_MANIFEST.json and Git object identities.
No network, repository mutations, pricing, per-order allocation or legal judgment.
"""
import collections
import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = '600ae3018f71025b3e53dc8538b8f92e6e159b76'
SOURCE_BRANCH_PIN = '54db2cf5948d7c0cdd91c8f66a96349224aee6a1'
CAMPAIGNS = [('apollo', '2026-10-31', 'claude-apollo-2026-10-31'),
             ('erasmus', '2026-11-02', 'claude-erasmus-2026-11-02')]
COUNTS = ['input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens',
          'output_tokens', 'api_messages', 'tool_calls', 'bash_calls', 'read_calls']
MANIFEST = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text())
SOURCES = {s['path']: s for s in MANIFEST}
CACHE = HERE / '.source-cache'


def load(path):
    local = CACHE / path
    if local.is_file():
        data = local.read_bytes()
    else:
        result = subprocess.run(['git', 'show', PIN + ':' + path], cwd=HERE,
                                env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'}, capture_output=True)
        if result.returncode:
            raise RuntimeError('Missing pinned source: ' + path + '. Materialize it in --source-cache using the exact manifest ref and verify the hash. No network fetch is attempted.')
        data = result.stdout
    m = SOURCES[path]
    assert hashlib.sha256(data).hexdigest() == m['sha256'], path
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == m['git_blob'], path
    assert m['ref'] == PIN, path
    return data.decode('utf-8')


def obj(path):
    return json.loads(load(path))


def rows(path):
    return list(csv.DictReader(io.StringIO(load(path))))


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


def main():
    # Verify even evidence that contributes a contract or interpretation rather
    # than a numeric total. Fail closed on absent, substituted or damaged bytes.
    for path in SOURCES:
        load(path)
    campaigns, joins, worker_rows, reviews_all = [], [], [], []
    for cid, date, folder in CAMPAIGNS:
        prefix = 'research/excavator/' + folder + '/'
        telemetry_path = prefix + 'TELEMETRY.csv'
        raw = rows(telemetry_path)
        assert len({r['agent'] for r in raw}) == len(raw), 'duplicate worker scope'
        role_model = collections.defaultdict(collections.Counter)
        totals = collections.Counter()
        workers_by_batch = collections.defaultdict(list)
        for r in raw:
            n = {k: int(r[k]) for k in COUNTS}
            n['gap_filtered_event_seconds'] = float(r['active_seconds'])
            n['agents'] = 1
            assert all(v >= 0 for v in n.values())
            role_model[(r['role'], r['model'])].update(n)
            totals.update(n)
            worker = {'campaign_id': cid, 'batch': r['batch'], 'role': r['role'],
                      'model': r['model'], 'agent_id': r['agent'], **n,
                      'first_utc': r['first_utc'], 'last_utc': r['last_utc'],
                      'source_id': telemetry_path, 'scope': 'published worker aggregate; all resumptions in that worker transcript'}
            worker_rows.append(worker)
            workers_by_batch[r['batch']].append(r['agent'])
        role_rows = [{'role': k[0], 'model': k[1], **dict(v), 'source_id': telemetry_path}
                     for k, v in sorted(role_model.items())]
        review_files = sorted(p for p in SOURCES if p.startswith(prefix) and p.endswith(('/BLIND_REVIEW.jsonl', '/AFTER_REVEAL.jsonl')))
        reviews = []
        for p in review_files:
            batch = p[len(prefix):].split('/')[0]
            for line in load(p).splitlines():
                if line.strip():
                    r = json.loads(line)
                    reviews.append({k: r.get(k) for k in ['review_id', 'instrument_id', 'claim_sha256',
                        'model_family', 'independent', 'separate_context', 'review_kind', 'scope', 'verdict']} |
                        {'campaign_id': cid, 'batch': batch, 'source_id': p,
                         'review_phase': 'after_reveal' if p.endswith('AFTER_REVEAL.jsonl') else 'blind'})
        # A genuine control version is reviewed after reveal. Omit its planted
        # blind version from genuine-outcome rates; retain only an aggregate.
        revealed = {(r['batch'], r['instrument_id']) for r in reviews if r['review_phase'] == 'after_reveal'}
        genuine = [r for r in reviews if r['review_phase'] == 'after_reveal' or (r['batch'], r['instrument_id']) not in revealed]
        # Public records preserve exact genuine version outcomes without exposing
        # which cases were controls or how/when they were revealed.
        reviews_all.extend({k: v for k, v in r.items() if k not in ['review_id', 'review_phase', 'source_id']} |
                           {'verdict': 'upheld' if r['verdict'] == 'upheld_after_reveal' else r['verdict']}
                           for r in genuine)
        by_version = collections.defaultdict(list)
        for r in genuine:
            by_version[(r['instrument_id'], r['claim_sha256'])].append(r)
        completion_paths = sorted(p for p in SOURCES if p.startswith(prefix) and p.endswith('/TALLY.json'))
        native_counts, transitions, completions = collections.Counter(), collections.Counter(), []
        for p in completion_paths:
            t = obj(p)
            batch = p[len(prefix):].split('/')[0]
            pub_path = p.replace('/TALLY.json', '/PUBLICATION.json')
            replay_path = p.replace('/TALLY.json', '/TRACKER_REPLAY.json')
            pub, replay = obj(pub_path), obj(replay_path)
            assert pub['written'] and pub['claims'] == t['claims_published']
            assert t['counts'].get('eligible', 0) == t['claims_published']
            assert len(t['outcomes']) == t['attempted']
            assert not replay['canonical_outputs_modified']
            changed = collections.Counter()
            for iid, pair in replay['selected'].items():
                a = pair['after']['ready_for_human_review'] == 'yes'
                b = pair['before']['ready_for_human_review'] == 'yes'
                changed['not_ready_to_ready' if a and not b else 'ready_to_not_ready' if b and not a else 'unchanged_ready' if a else 'unchanged_not_ready'] += 1
            changed['global_net_ready'] = replay['after']['ready_for_human_review'] - replay['before']['ready_for_human_review']
            transitions.update(changed)
            for k in ['attempted', 'submitted', 'claims_published', 'independent_human_certifications', 'wall_seconds', 'plants_placed', 'plants_caught']:
                native_counts[k] += t[k]
            for k, v in t['counts'].items():
                native_counts['outcome_' + k] += v
            comp = {'batch': batch, 'source_id': p, 'publication_source_id': pub_path,
                    'tracker_replay_source_id': replay_path, 'counts': t['counts'],
                    'attempted': t['attempted'], 'submitted_after_review': t['submitted'],
                    'claims_published': t['claims_published'], 'publication_path': pub['path'],
                    'publication_sha256': pub['sha256'], 'deterministic_completion_wall_seconds': t['wall_seconds'],
                    'started_utc': t['started_utc'], 'finished_utc': t['finished_utc'],
                    'replay_transitions': dict(changed), 'telemetry_worker_ids': workers_by_batch[batch]}
            completions.append(comp)
            for outcome in t['outcomes']:
                exact = by_version.get((outcome['instrument_id'], outcome.get('claim_sha256')), [])
                if outcome['outcome'] == 'eligible':
                    assert exact and any(r['verdict'] in ['upheld', 'upheld_after_reveal'] for r in exact), (p, outcome)
                joins.append({'campaign_id': cid, 'batch': batch, 'instrument_id': outcome['instrument_id'],
                    'claim_sha256': outcome.get('claim_sha256'), 'outcome': outcome['outcome'],
                    'source_review_upheld': outcome.get('source_review_upheld'),
                    'source_id': p, 'exact_version_review_matched': bool(exact),
                    'publication_source_id': pub_path if outcome['outcome'] == 'eligible' else None,
                    'telemetry_scope': 'batch workers; no per-order tokens allocated',
                    'telemetry_worker_ids': workers_by_batch[batch]})
        review_counts = dict(collections.Counter('upheld' if r['verdict'] == 'upheld_after_reveal' else r['verdict'] for r in genuine))
        review_counts['genuine_versions'] = len(genuine)
        review_counts['planted_blind_versions_excluded'] = len(reviews) - len(genuine)
        uncompleted = sorted(set(workers_by_batch) - {c['batch'] for c in completions})
        coverage = {'basis': 'published historical transcript-derived aggregates; original private transcripts unavailable',
                    'coordinator': 'excluded; unknown usage', 'workers_in_csv': len(raw),
                    'possible_calls_denominator': None, 'provider_final_usage_verified': False,
                    'cache_write_ttl': None, 'money_cash_usd': None, 'money_api_equivalent_usd': None,
                    'cost_per_additional_ready_dossier_usd': None,
                    'per_order_allocation': None, 'worker_active_seconds': None,
                    'gap_filtered_time_method': 'sum consecutive event gaps <=600 seconds; not active labor or exclusive compute',
                    'batches_without_published_completion': uncompleted,
                    'phases': 'producer/reviewer/builder roles observed; preparation, acquisition, corrections, review and coordination inside role totals not separated'}
        coverage['model_label_basis'] = 'most frequent observed model per transcript; mixtures not retained by published exporter'
        coverage['review_control_pairs_recovered'] = review_counts['planted_blind_versions_excluded']
        if cid == 'erasmus':
            roster = rows(prefix + 'ROSTER.csv')
            assert {r['agent_id'] for r in roster} == {r['agent'] for r in raw}
            coverage['roster_workers'] = len(roster)
            coverage['report_agent_count'] = 27
            coverage['agent_count_note'] = 'Report says 27 including resumptions; roster and telemetry have 20 unique agent IDs. Resumption/API-call segmentation not recoverable.'
            coverage['report_control_count'] = 10
            coverage['control_coverage_note'] = 'Nine published blind/reveal pairs recovered; eight completed tallies and one uncompleted review batch. Report says ten; missing tenth not inferred.'
        five = [
          {'id': 'tokens_money', 'observed': 'Tokens by published worker, batch, role and modal model; coordinator excluded.',
           'unavailable': ['cash', 'dated model-specific API rates', 'cache-write TTL', 'all coordinator usage', 'phase-separated usage', 'provider final usage proof'], 'source_ids': [telemetry_path]},
          {'id': 'repeated_context', 'observed': 'Aggregate cache-read usage and Read tool counts; these do not identify repeated source bytes or avoidable waste.',
           'unavailable': ['source/page digests per load', 'context resets', 'per-call cache behavior', 'shared-versus-order-specific context'], 'source_ids': [telemetry_path]},
          {'id': 'late_blockers_retries', 'observed': 'Exact genuine review versions and native final completion outcomes, plus cross-campaign instrument joins.',
           'unavailable': ['cost before first blocker', 'first detection time for every blocker', 'all abandoned attempts', 'exact rejected canonical hashes where completion sets hash null'], 'source_ids': completion_paths + review_files},
          {'id': 'cost_per_ready', 'observed': 'Batch usage joined to exact reviewed/completed versions; native replay transitions retained separately from filing.',
           'unavailable': ['complete campaign cost', 'causal net new ready dossiers', 'cost per additional ready dossier', 'observed per-order usage'], 'source_ids': completion_paths},
          {'id': 'waiting_compute_worker', 'observed': 'Worker first/last event envelopes, gap-filtered event time and deterministic completion wall durations.',
           'unavailable': ['active labor', 'exclusive compute', 'exact token-reset wait intervals from CSV', 'queue waits', 'critical path', 'overlap-resolved activity'], 'source_ids': [telemetry_path] + completion_paths}]
        campaigns.append({'id': cid, 'date': date, 'telemetry': {'rows': len(raw), 'totals': dict(totals),
            'by_role_model': role_rows, 'coverage': coverage, 'source_id': telemetry_path},
            'outcomes': {'completions': completions, 'counts': dict(native_counts), 'review_counts': review_counts,
                         'replay_transitions': dict(transitions),
                         'replay_scope': 'sum of selected transitions in separate native completion replays; corrections can transition too; not causal campaign net gain'},
            'five_views': five})
    # Retry membership is observed at instrument/version level. Usage stays at
    # batch scope, including failed attempts and builder batches without filing.
    rejected_apollo = collections.defaultdict(list)
    for r in reviews_all:
        if r['campaign_id'] == 'apollo' and r['verdict'] == 'rejected':
            rejected_apollo[r['instrument_id']].append(r)
    retries = []
    for j in joins:
        if j['campaign_id'] == 'erasmus' and j['instrument_id'] in rejected_apollo:
            retries.append({'instrument_id': j['instrument_id'], 'apollo_rejected_versions': [r['claim_sha256'] for r in rejected_apollo[j['instrument_id']]],
                            'erasmus_batch': j['batch'], 'erasmus_claim_sha256': j['claim_sha256'],
                            'erasmus_outcome': j['outcome'], 'erasmus_source_id': j['source_id'],
                            'usage_attribution': 'batch only; no per-instrument token allocation'})
    out = {'schema': 'eo-historical-observability/v1', 'source_main_pin': PIN,
           'source_proposal_branch_pin': SOURCE_BRANCH_PIN, 'campaigns': campaigns,
           'interpretation': 'Dated historical examples; input categories, output, role totals and diagnostic views retain their own scopes; money and active labor unavailable.',
           'source_manifest': 'SOURCE_MANIFEST.json', 'exact_outcome_file': 'OUTCOMES.json'}
    write('RECOVERED.json', out)
    write('OUTCOMES.json', {'schema': 'eo-historical-outcome-joins/v1', 'completion_outcomes': joins,
                          'genuine_review_versions': reviews_all, 'apollo_to_erasmus_retry_membership': retries,
                          'workers': worker_rows})
    print(json.dumps([{'id': c['id'], 'workers': c['telemetry']['rows'], 'tokens': c['telemetry']['totals'],
                      'outcomes': c['outcomes']['counts'], 'reviews': c['outcomes']['review_counts'],
                      'replay': c['outcomes']['replay_transitions']} for c in campaigns], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-cache', type=Path, default=CACHE,
                        help='external, untracked cache of exact public source bytes, preserving repository paths')
    args = parser.parse_args()
    CACHE = args.source_cache.resolve()
    main()
