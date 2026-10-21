"""NORTON's factual records. No lifecycle/status decision is made here."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

CUTOFF = '2026-10-14'
KINDS = {'report_delivery', 'report_publication', 'recurring_performance', 'appointment',
         'transfer_event', 'function_succession', 'other_event'}
DIMENSIONS = ('entity_id', 'object', 'scope', 'interval_start', 'interval_end', 'proposition', 'event_kind')
CHECKS = ('scope', 'applicability', 'earlier_cessation', 'independent_commands', 'savings')

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()

def fingerprint(value):
    return sha(canonical(value))

def date(value):
    try:
        return isinstance(value, str) and dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False

def question_key(q):
    """Exact dimensions, including case/punctuation. Aliases never silently change a key."""
    for k in DIMENSIONS:
        if not isinstance(q.get(k), str) or not q[k].strip():
            raise ValueError('missing_question_dimension:' + k)
    if q['event_kind'] not in KINDS:
        raise ValueError('unknown_event_kind')
    if not date(q['interval_start']) or not date(q['interval_end']) or q['interval_start'] > q['interval_end']:
        raise ValueError('invalid_question_interval')
    if q['interval_end'] > CUTOFF:
        raise ValueError('question_after_cutoff')
    return 'NQ:' + fingerprint({k: q[k] for k in DIMENSIONS})

def safe_path(repo, name, base=None):
    if not isinstance(name, str) or not name or '\\' in name or '#' in name or '..' in Path(name).parts:
        raise ValueError('unsafe_path')
    if Path(name).is_absolute():
        raise ValueError('absolute_path')
    root = Path(repo).resolve()
    p = ((base or root) / name).resolve()
    if not p.is_relative_to(root):
        raise ValueError('path_escapes_repository')
    return p

def source_span(repo, record, require_bytes=False):
    """Verify an attributed extract, never JSON snippets. Retain raw-source holds."""
    src = record.get('source', {})
    errors = []
    for k in ('sha256', 'text_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', str(src.get(k, ''))):
            errors.append('missing_' + k)
    if not src.get('page_or_item'):
        errors.append('missing_page_or_item')
    if not (str(src.get('url', '')).startswith('https://') or src.get('archival_id')):
        errors.append('missing_source_identity')
    try:
        p = safe_path(repo, src.get('text_path'))
        if p.suffix.lower() not in ('.txt', '.html', '.htm', '.xml'):
            raise ValueError('serialized_record_is_not_source_text')
        raw = p.read_bytes()
        if raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise ValueError('lfs_pointer_not_bytes')
        if sha(raw) != src.get('text_sha256'):
            errors.append('text_hash_mismatch')
        text = raw.decode('utf-8')
        a, b = record.get('char_start'), record.get('char_end')
        if not (type(a) is int and type(b) is int and 0 <= a < b <= len(text)):
            errors.append('invalid_span')
        elif text[a:b] != record.get('text'):
            errors.append('quote_mismatch')
    except (OSError, ValueError, UnicodeError) as e:
        errors.append('text_unavailable:' + str(e))
    if require_bytes:
        try:
            raw = safe_path(repo, src.get('raw_path')).read_bytes()
            if raw.startswith(b'version https://git-lfs.github.com/spec/v1') or sha(raw) != src.get('sha256'):
                errors.append('source_bytes_hash_mismatch')
        except (OSError, ValueError):
            errors.append('source_bytes_not_held')
    return errors

def evidence_errors(repo, q, evidence):
    errors = source_span(repo, evidence, require_bytes=True)
    if evidence.get('schema') != 'norton-candidate-evidence/v1':
        errors.append('wrong_evidence_schema')
    if evidence.get('question_key') != question_key(q):
        errors.append('wrong_question')
    if evidence.get('event_kind') != q['event_kind']:
        errors.append('event_kind_mismatch')
    if evidence.get('entity_id') != q['entity_id']:
        errors.append('entity_mismatch')
    d = evidence.get('event_date')
    if not date(d) or not q['interval_start'] <= d <= q['interval_end']:
        errors.append('event_date_outside_interval_or_unknown')
    src = evidence.get('source', {})
    if not src.get('primary') or not src.get('retrieved_utc') or not src.get('route') or not src.get('edition'):
        errors.append('primary_source_provenance_incomplete')
    # An old historical edition can prove its dated event, never an uninterrupted current function.
    if q['event_kind'] == 'recurring_performance' and src.get('coverage_through', '') < q['interval_end']:
        errors.append('performance_coverage_gap')
    if q.get('edition_required') and src.get('edition') != q['edition_required']:
        errors.append('wrong_historical_edition')
    return errors

def review_errors(repo, record, review, kind):
    """Require a separately pinned factual review. Never accepts a lifecycle human-review schema."""
    errors = []
    if review.get('schema') != 'norton-factual-review/v1' or review.get('record_kind') != kind:
        errors.append('wrong_review_schema')
    if review.get('record_sha256') != fingerprint(record):
        errors.append('changed_after_review')
    if review.get('reviewer_type') not in ('independent_ai', 'independent_human'):
        errors.append('unknown_reviewer_type')
    if not review.get('reviewer') or review.get('reviewer') == record.get('producer') or review.get('independent') is not True:
        errors.append('review_not_independent')
    if review.get('decision') != 'uphold' or not date(review.get('reviewed_on')):
        errors.append('not_upheld_or_undated')
    if not isinstance(review.get('rationale'), str) or len(review['rationale']) < 40:
        errors.append('review_rationale_missing')
    if review.get('d6_searched') is not True:
        errors.append('later_event_review_missing')
    if kind == 'answer' and sorted(review.get('checked_evidence_ids',[])) != sorted(record.get('evidence_ids',[])):
        errors.append('unreviewed_answer_evidence')
    return errors

def application_errors(repo, q, app):
    errors = []
    if app.get('schema') != 'norton-application/v1':
        errors.append('wrong_application_schema')
    if app.get('question_key') != question_key(q):
        errors.append('wrong_question')
    iid, scope = app.get('instrument_id', ''), app.get('scope_id', '')
    if not iid.startswith('EO:') or not scope.startswith(iid + '#'):
        errors.append('wrong_clause_identity')
    if app.get('legal_effect') != 'unresolved':
        errors.append('factual_record_cannot_decide_legal_effect')
    clause = app.get('clause_evidence', {})
    if clause.get('instrument_id') != iid:
        errors.append('clause_evidence_wrong_order')
    errors.extend(source_span(repo, clause))
    if app.get('state') in ('ai_reviewed', 'human_accepted'):
        for k in CHECKS:
            v = app.get('checks', {}).get(k)
            if not isinstance(v, str) or len(v.strip()) < 30:
                errors.append('unsupported_applicability:' + k)
    return errors
