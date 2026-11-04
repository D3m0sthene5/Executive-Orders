"""Bounded, research-only provision histories using Stage17's record vocabulary.

Bundle ``eo-provision-history/v1`` contains producer, provisions, transitions and
review_file:{path,sha256}. Each provision has Stage17 provision_id, instrument_id,
scope, norm_text, source_id, valid_start, known_sunset_end_exclusive. Transitions
have transition_id, affected_provision_id, actor_id, event_date, kind, source_id.
Same-day operations require explicit distinct integer sequence; signing_date and
publication_date remain separate from effective_date; supersede preserves its mechanism.
Both carry source:{text_path,text_sha256,char_start,char_end,quote}; optional
raw_path/raw_sha256 pins held source bytes without authenticating their origin.
A separate ``eo-provision-history-review/v1`` ledger has reviews with record_id,
record_sha256, scope (text OR legal_effect), review_scope (exact provision_id),
verdict:upheld, reviewer, independent:true. Each scope needs its own exact row.
Missing reviews are unresolved research; malformed or stale reviews are errors.

Initial version is provision_id+'::v0'; amendments use transition_id as version.
Amend requires from_version_id, unique old_rule, new_rule, expected_new_text.
Reinstate requires restore_version_id. Renumber requires new_label; transfer
requires transfer_to. Effective timing needs effective_date (valid_start for
initial provision), date_basis AND separate legal_effect review. event_date alone
is textual chronology. Unknown effect never authorizes continuity or revival.
Initial signing_date/publication_date/text_date document chronology is separate
from valid_start. Undated or future text remains held_text_version only; dated
text_version requires documentary timing or explicitly reviewed retrospective
legal reconstruction. No public-availability/knowability claim is made.
No record is human certification, original authentication, or canonical approval.
"""
from __future__ import annotations

from copy import deepcopy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

from assemble import canonical_sha

SCHEMA = 'eo-provision-history/v1'
REVIEW_SCHEMA = 'eo-provision-history-review/v1'
KINDS = {'establish', 'amend', 'revoke', 'reinstate', 'renumber', 'transfer', 'supersede'}
NOTICE = ('Derived independent-AI research only; no human certification, original '
          'authentication, canonical approval or completeness guarantee. Dates outside '
          'examined coverage and omitted events remain unexamined.')


def _date(value, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise ValueError('invalid_date')
    try:
        if datetime.date.fromisoformat(value).isoformat() != value:
            raise ValueError('invalid_date')
    except ValueError as err:
        raise ValueError('invalid_date:' + str(value)) from err
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('missing_' + label)
    return value


def _safe(repo, rel):
    if not isinstance(rel, str) or Path(rel).is_absolute() or '..' in Path(rel).parts:
        raise ValueError('unsafe_path')
    target = (repo / rel).resolve()
    if not target.is_relative_to(repo):
        raise ValueError('unsafe_path')
    return target


def _bytes_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _source(repo, rec, dependencies, cache):
    src = rec.get('source')
    if not isinstance(src, dict):
        raise ValueError('missing_source')
    path = _safe(repo, src.get('text_path'))
    if path not in cache:
        cache[path] = path.read_bytes()
    raw = cache[path]
    if _bytes_sha(raw) != src.get('text_sha256'):
        raise ValueError('stale_source:' + str(src.get('text_path')))
    text = raw.decode('utf-8')
    a, b = src.get('char_start'), src.get('char_end')
    if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text)
            or text[a:b] != src.get('quote')):
        raise ValueError('source_span_mismatch')
    dependencies['source:' + src['text_path']] = src['text_sha256']
    if ('raw_path' in src) != ('raw_sha256' in src):
        raise ValueError('incomplete_raw_source_pin')
    if 'raw_path' in src:
        path = _safe(repo, src['raw_path'])
        if path not in cache:
            cache[path] = path.read_bytes()
        if _bytes_sha(cache[path]) != src['raw_sha256']:
            raise ValueError('stale_raw_source')
        dependencies['source:' + src['raw_path']] = src['raw_sha256']


def load(repo, bundle_path):
    """Validate a bounded bundle and its independent ledger; never write files."""
    repo = Path(repo).resolve()
    path = Path(bundle_path)
    if not path.is_absolute():
        path = _safe(repo, str(path))
    elif not path.resolve().is_relative_to(repo):
        raise ValueError('bundle_outside_repository')
    bundle = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(bundle, dict) or bundle.get('schema') != SCHEMA:
        raise ValueError('wrong_bundle_schema')
    producer = _text(bundle.get('producer'), 'producer')
    _date(bundle.get('legal_cutoff'))
    if (not isinstance(bundle.get('provisions'), list) or not bundle['provisions']
            or not isinstance(bundle.get('transitions'), list)):
        raise ValueError('invalid_records')
    if len(bundle['provisions']) + len(bundle['transitions']) > 1000:
        raise ValueError('bounded_bundle_limit')
    records, provisions, dependencies, cache = {}, {}, {}, {}
    for is_provision, rows in ((True, bundle['provisions']), (False, bundle['transitions'])):
        for rec in rows:
            if not isinstance(rec, dict):
                raise ValueError('invalid_record')
            key = _text(rec.get('provision_id' if is_provision else 'transition_id'), 'record_id')
            if key in records:
                raise ValueError('duplicate_record:' + key)
            _text(rec.get('producer', producer), 'record_producer')
            _text(rec.get('source_id'), 'source_id')
            if 'date_basis' in rec and rec['date_basis'] is not None:
                _text(rec['date_basis'], 'date_basis')
            questions = rec.get('unresolved_questions', [])
            if not isinstance(questions, list) or any(not isinstance(q, str) or not q.strip() for q in questions):
                raise ValueError('invalid_unresolved_questions')
            deps = {'record:' + key: canonical_sha(rec)}
            _source(repo, rec, deps, cache)
            for field, witness in rec.items():
                if field.endswith('_source'):
                    if not isinstance(witness, dict):
                        raise ValueError('invalid_auxiliary_source:' + field)
                    _source(repo, {'source': witness}, deps, cache)
            dependencies[key] = deps
            records[key] = rec
            if is_provision:
                _text(rec.get('instrument_id'), 'instrument_id')
                _text(rec.get('scope'), 'scope')
                if _text(rec.get('norm_text'), 'norm_text') not in rec['source']['quote']:
                    raise ValueError('unlocated_norm_text')
                _date(rec.get('signing_date'))
                _date(rec.get('publication_date'))
                _date(rec.get('text_date'))
                _date(rec.get('event_date'))
                _date(rec.get('valid_start'))
                _date(rec.get('known_sunset_end_exclusive'))
                provisions[key] = rec
            else:
                if rec.get('kind') not in KINDS:
                    raise ValueError('unknown_operation:' + str(rec.get('kind')))
                if rec.get('affected_provision_id') not in provisions:
                    raise ValueError('unknown_provision')
                _text(rec.get('actor_id'), 'actor_id')
                _date(rec.get('event_date'), True)
                _date(rec.get('effective_date'))
                _date(rec.get('signing_date'))
                _date(rec.get('publication_date'))
                if 'sequence' in rec and (type(rec['sequence']) is not int or rec['sequence'] < 0):
                    raise ValueError('invalid_sequence')
                _date(rec.get('known_sunset_end_exclusive'))
                if rec['kind'] == 'amend':
                    for name in ('from_version_id', 'old_rule', 'expected_new_text'):
                        _text(rec.get(name), name)
                    if not isinstance(rec.get('new_rule'), str):
                        raise ValueError('missing_new_rule')
                if rec['kind'] == 'reinstate':
                    _text(rec.get('restore_version_id'), 'restore_version_id')
                if rec['kind'] in ('renumber', 'transfer'):
                    _text(rec.get('new_label' if rec['kind'] == 'renumber' else 'transfer_to'), rec['kind'])
    # Version references must stay within the same provision and point backward;
    # this also rejects cycles without a second dependency engine.
    versions = {pid + '::v0': (pid, None) for pid in provisions}
    ordered = sorted(bundle['transitions'], key=lambda r: (r.get('effective_date') or r['event_date'], r.get('sequence', -1), r['transition_id']))
    seen_times = set()
    for rec in ordered:
        pid = rec['affected_provision_id']
        when = rec.get('effective_date') or rec['event_date']
        time_key = (pid, when, rec.get('sequence'))
        if time_key in seen_times or ((pid, when, None) in seen_times):
            raise ValueError('conflicting_same_time_operations:' + pid + ':' + when)
        if rec.get('sequence') is None and any(t[:2] == (pid, when) for t in seen_times):
            raise ValueError('conflicting_same_time_operations:' + pid + ':' + when)
        seen_times.add(time_key)
        for field in ('from_version_id', 'restore_version_id'):
            if field in rec:
                ref = versions.get(rec[field])
                if ref is None or ref[0] != pid or (ref[1] is not None and ref[1] >= (when, rec.get('sequence', -1))):
                    raise ValueError('cyclic_or_nonprior_version:' + str(rec[field]))
        if rec['kind'] in ('amend', 'establish'):
            if rec['transition_id'] in versions:
                raise ValueError('duplicate_version')
            versions[rec['transition_id']] = (pid, (when, rec.get('sequence', -1)))
    ref = bundle.get('review_file')
    if not isinstance(ref, dict) or not str(ref.get('path', '')).startswith('research/'):
        raise ValueError('independent_review_file_required')
    review_path = _safe(repo, ref.get('path'))
    if review_path.resolve() == path.resolve():
        raise ValueError('review_must_be_separate')
    raw = review_path.read_bytes()
    if _bytes_sha(raw) != ref.get('sha256'):
        raise ValueError('changed_review_file')
    ledger = json.loads(raw)
    if not isinstance(ledger, dict) or ledger.get('schema') != REVIEW_SCHEMA or not isinstance(ledger.get('reviews'), list):
        raise ValueError('wrong_review_schema')
    reviews = {}
    for review in ledger['reviews']:
        if not isinstance(review, dict):
            raise ValueError('invalid_review')
        rid, scope = review.get('record_id'), review.get('scope')
        if rid not in records or scope not in ('text', 'legal_effect'):
            raise ValueError('unknown_review_record_or_scope')
        key = (rid, scope)
        if key in reviews:
            raise ValueError('duplicate_review')
        rec = records[rid]
        pid = rid if rid in provisions else rec['affected_provision_id']
        if review.get('record_sha256') != canonical_sha(rec) or review.get('review_scope') != pid:
            raise ValueError('stale_or_wrong_scope_review:' + rid)
        if (review.get('verdict') != 'upheld' or review.get('independent') is not True
                or not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip()
                or review['reviewer'] == rec.get('producer', producer)):
            raise ValueError('independent_upheld_review_required')
        reviews[key] = review
    membership = {}
    for pid, provision in provisions.items():
        members = [r for r in ordered if r['affected_provision_id'] == pid]
        member_ids = {pid} | {r['transition_id'] for r in members}
        member_reviews = [review for (rid, scope), review in sorted(reviews.items()) if rid in member_ids]
        membership['membership:' + pid] = canonical_sha({
            'provision': provision, 'transitions': sorted(members, key=lambda r: r['transition_id']),
            'reviews': member_reviews,
            'bundle_context': {k: bundle.get(k) for k in ('producer', 'legal_cutoff', 'coverage_notice')}})
    return {'bundle': bundle, 'provisions': provisions, 'records': records,
            'membership': membership,
            'ordered': ordered, 'reviews': reviews, 'dependencies': dependencies,
            'review_file_dependency': {'review_file:' + ref['path']: ref['sha256']}}


def _reviewed(history, rec, scope):
    rid = rec.get('provision_id', rec.get('transition_id'))
    return (rid, scope) in history['reviews']


def _timed_effect(history, rec, initial=False):
    return (bool(rec.get('valid_start' if initial else 'effective_date'))
            and bool(rec.get('date_basis')) and _reviewed(history, rec, 'legal_effect'))


def _dependencies(history, rec):
    rid = rec.get('provision_id', rec.get('transition_id'))
    deps = dict(history['dependencies'][rid])
    deps.update(history['review_file_dependency'])
    deps['method:jobs/claim-kit/provision_history.py'] = _bytes_sha(Path(__file__).read_bytes())
    for scope in ('text', 'legal_effect'):
        review = history['reviews'].get((rid, scope))
        if review:
            deps['review:' + rid + ':' + scope] = canonical_sha(review)
    return deps


def _initial_document_date(provision):
    explicit = provision.get('signing_date') or provision.get('text_date') or provision.get('publication_date')
    if explicit:
        return explicit
    return None


def _query_one(history, pid, on):
    p = history['provisions'][pid]
    deps = _dependencies(history, p)
    deps['membership:' + pid] = history['membership']['membership:' + pid]
    questions = list(p.get('unresolved_questions', []))
    if p.get('remaining_gap'):
        questions.append(p['remaining_gap'])
    text_ok = _reviewed(history, p, 'text')
    initial_id = pid + '::v0'
    current = {'version_id': initial_id, 'text': p['norm_text'], 'dependencies': dict(deps),
               'document_date': _initial_document_date(p)} if text_ok else None
    versions = {initial_id: current} if current else {}
    state, episode = 'unknown', None
    if not text_ok:
        questions.append('Initial provision text has no exact independent text review.')
    initial_effect = text_ok and _timed_effect(history, p, True)
    start = p.get('valid_start')
    sunset = p.get('known_sunset_end_exclusive')
    if initial_effect and sunset and sunset < start:
        raise ValueError('sunset_precedes_reviewed_establishment:' + pid)
    if initial_effect:
        state = 'operative' if on >= start else 'not_yet_established'
        if on >= start:
            episode = {'episode_id': pid + '::episode0', 'start': start, 'end_exclusive': None}
    else:
        questions.append('Initial operative timing or legal effect has not been independently reviewed.')
    label, executor = p['scope'], None
    applied, gaps, details = [], [], []
    text_complete = text_ok
    expiry_reviewed = _reviewed(history, p, 'legal_effect')
    effective_reconstruction = bool(initial_effect and on >= start)
    for rec in history['ordered']:
        if rec['affected_provision_id'] != pid:
            continue
        when = rec.get('effective_date') or rec['event_date']
        if when > on:
            continue
        if state == 'operative' and expiry_reviewed and sunset and when >= sunset:
            state = 'expired'
            if episode:
                episode['end_exclusive'] = sunset
                if episode['start'] < sunset:
                    gaps.append(deepcopy(episode))
                episode = None
        deps.update(_dependencies(history, rec))
        questions.extend(rec.get('unresolved_questions', []))
        rid, kind = rec['transition_id'], rec['kind']
        details.append({k: rec.get(k) for k in ('transition_id', 'kind', 'event_date', 'effective_date', 'signing_date', 'publication_date', 'date_basis', 'sequence')})
        details[-1]['retroactive_effect'] = bool(rec.get('effective_date') and rec.get('signing_date') and rec['effective_date'] < rec['signing_date'])
        if details[-1]['retroactive_effect']:
            questions.append(rid + ': retrospective legal reconstruction using a later signed instrument; this does not establish what was knowable on the query date.')
        if not _reviewed(history, rec, 'text'):
            questions.append(rid + ': exact transition text not independently reviewed.')
            state = 'unknown'
            text_complete = False
            continue
        effect = _timed_effect(history, rec)
        if effect and initial_effect and when < start:
            raise ValueError('transition_precedes_reviewed_establishment:' + rid)
        if not effect:
            questions.append(rid + ': operative effect/effective timing unresolved; event_date is textual chronology only.')
            state = 'unknown'
        if kind == 'amend':
            if not text_complete:
                raise ValueError('amendment_base_unreviewed:' + rid)
            if current is None or rec['from_version_id'] != current['version_id']:
                raise ValueError('amendment_base_mismatch:' + rid)
            if current['text'].count(rec['old_rule']) != 1:
                raise ValueError('ambiguous_or_missing_old_rule:' + rid)
            new_text = current['text'].replace(rec['old_rule'], rec['new_rule'], 1)
            if new_text != rec['expected_new_text']:
                raise ValueError('expected_new_text_mismatch:' + rid)
            current = {'version_id': rid, 'text': new_text, 'dependencies': {**current['dependencies'], **_dependencies(history, rec)},
                       'document_date': rec.get('signing_date') or rec.get('event_date') or rec.get('publication_date')}
            effective_reconstruction = effect
            versions[rid] = current
        elif kind == 'establish':
            # A new establishment requires a complete exact located rule.
            rule = rec.get('new_rule')
            if not isinstance(rule, str) or not rule or rule not in rec['source']['quote']:
                raise ValueError('unlocated_established_rule:' + rid)
            current = {'version_id': rid, 'text': rule, 'dependencies': _dependencies(history, rec),
                       'document_date': rec.get('signing_date') or rec.get('event_date') or rec.get('publication_date')}
            effective_reconstruction = effect
            versions[rid] = current
            if effect:
                if state == 'operative':
                    raise ValueError('establishment_overlaps_episode')
                state = 'operative'
                episode = {'episode_id': rid + '::episode', 'start': when, 'end_exclusive': None}
        elif kind in ('revoke', 'supersede') and effect:
            if episode:
                episode['end_exclusive'] = when
                if episode['start'] < when:
                    gaps.append(deepcopy(episode))
            state, episode = ('superseded' if kind == 'supersede' else 'revoked'), None
        elif kind == 'reinstate':
            restored = versions.get(rec['restore_version_id'])
            if restored is None:
                raise ValueError('unreviewed_restored_version:' + rid)
            current = deepcopy(restored)
            current['document_date'] = rec.get('signing_date') or rec.get('event_date') or rec.get('publication_date')
            effective_reconstruction = effect
            text_complete = True
            deps.update(restored['dependencies'])
            if effect:
                if state == 'operative':
                    raise ValueError('reinstatement_overlaps_episode')
                state = 'operative'
                episode = {'episode_id': rid + '::episode', 'start': when, 'end_exclusive': None}
        elif kind == 'renumber':
            label = rec['new_label']
        elif kind == 'transfer':
            executor = rec['transfer_to'] if effect else None
        # Sunset changes are never inferred from a reinstatement or amendment.
        if 'known_sunset_end_exclusive' in rec:
            if effect:
                sunset = rec['known_sunset_end_exclusive']
                expiry_reviewed = True
            else:
                questions.append(rid + ': proposed expiry change lacks reviewed legal effect.')
        applied.append(rid)
    if state == 'operative' and sunset and not expiry_reviewed:
        state = 'unknown'
        questions.append('Original expiry is recorded but its legal effect has not been independently reviewed; revival cannot resolve that clock.')
    if state == 'operative' and expiry_reviewed and sunset and on >= sunset:
        state = 'expired'
        if episode:
            episode['end_exclusive'] = sunset
            if episode['start'] >= sunset:
                # Revival does not create a negative or fictional operative interval.
                episode = None
    outside_cutoff = bool(history['bundle'].get('legal_cutoff') and on > history['bundle']['legal_cutoff'])
    if outside_cutoff:
        state = 'unknown'
        questions.append('Query date is outside the bundle legal cutoff; no operative state is extrapolated beyond examined coverage.')
    if state in ('unknown', 'not_yet_established'):
        episode = None
    if current:
        deps.update(current['dependencies'])
    def text_date_state(document_date, reviewed_effect):
        if document_date and on >= document_date:
            return 'documented_by_query_date'
        if reviewed_effect:
            return 'reviewed_retrospective_reconstruction'
        return 'not_yet_documented' if document_date else 'unknown'
    initial_document_date = _initial_document_date(p)
    initial_text_date_state = text_date_state(initial_document_date, bool(initial_effect and on >= start)) if text_ok else 'unreviewed'
    dated_state = text_date_state(current.get('document_date'), effective_reconstruction) if current else 'unreviewed'
    held_version = {k: current[k] for k in ('version_id', 'text')} if current else None
    dated_supported = dated_state in ('documented_by_query_date', 'reviewed_retrospective_reconstruction')
    if not dated_supported:
        questions.append('Reviewed held text does not establish a textual version as of the query date; document chronology is ' + dated_state + '.')
    return {'schema': 'eo-provision-history-query/v1', 'notice': NOTICE,
            'query_id': 'query:' + pid + '@' + on, 'provision_id': pid,
            'instrument_id': p['instrument_id'], 'on': on, 'scope': p['scope'],
            'label': label, 'executor': executor,
            'text_version': held_version if dated_supported else None,
            'held_text_version': held_version,
            'initial_text_date_state': initial_text_date_state, 'text_date_state': dated_state,
            'initial_document_dates': {k: p.get(k) for k in ('signing_date', 'publication_date', 'text_date', 'event_date')},
            'initial_document_date_used': initial_document_date,
            'text_version_scope': 'reviewed textual reconstruction; operative finding is separately reported',
            'textual_coverage_complete': text_complete,
            'expiry_reviewed': expiry_reviewed,
            'initial_date_basis': p.get('date_basis'),
            'operative_state': state, 'operative_episode': episode,
            'operative_state_scope': 'state implied by supplied reviewed transitions, not a complete legal interval or cutoff-wide status',
            'prior_episodes': gaps, 'known_sunset_end_exclusive': sunset,
            'textual_transitions': applied, 'transition_details': details, 'unresolved_questions': list(dict.fromkeys(questions)),
            'dependencies': dict(sorted(deps.items())), 'human_certified': False,
            'canonical_approval': False, 'completeness_guaranteed': False,
            'coverage_notice': history['bundle'].get('coverage_notice'),
            'legal_cutoff': history['bundle'].get('legal_cutoff'),
            'outside_legal_cutoff': outside_cutoff}


def dated_query(repo, bundle_path, on, provision_id=None):
    """Return reviewed textual chronology separately from reviewed legal effect."""
    on = _date(on, True)
    history = load(repo, bundle_path)
    ids = [provision_id] if provision_id else sorted(history['provisions'])
    if any(pid not in history['provisions'] for pid in ids):
        raise ValueError('unknown_provision')
    results = [_query_one(history, pid, on) for pid in ids]
    return {'schema': 'eo-provision-history-results/v1', 'notice': NOTICE, 'on': on, 'queries': results}


def revalidation_report(results, changed):
    """Compute Valla closure from exact changed dependency hashes and prior queries.

    ``changed`` maps dependency IDs from query.dependencies to their current hash
    (or null for deletion). Pass prior query results; this report does not renew
    stale sources/reviews or authorize reuse. Unlisted queries remain unexamined.
    """
    if not isinstance(changed, dict) or results.get('schema') != 'eo-provision-history-results/v1':
        raise ValueError('invalid_revalidation_input')
    path = Path(__file__).resolve().parents[1] / 'valla' / 'valla.py'
    spec = importlib.util.spec_from_file_location('provision_history_valla', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    edges, invalid, observed = [], set(), set()
    for query in results['queries']:
        qid, pid = query['query_id'], 'provision:' + query['provision_id']
        edges.append((pid, qid))
        for key, digest in query['dependencies'].items():
            observed.add(key)
            edges.append((qid, key))
            if key in changed and changed[key] != digest:
                invalid.add(key)
    affected = module.closure(invalid, edges)
    return {'schema': 'eo-provision-history-revalidation/v1',
            'changed_dependencies': sorted(invalid),
            'affected_queries': sorted(x for x in affected if x.startswith('query:')),
            'affected_provisions': sorted(x for x in affected if x.startswith('provision:')),
            'unexamined_changes': sorted(set(changed) - observed),
            'notice': 'Revalidation required; no corrected claim or review has been produced.'}


def query(repo, bundle_path, provision_id, on):
    """Single-provision public interface used by kit.py history-at."""
    return dated_query(repo, bundle_path, on, provision_id)['queries'][0]


def membership_fingerprints(repo, bundle_path):
    """Current per-provision membership pins for comparing saved query results."""
    return dict(load(repo, bundle_path)['membership'])
