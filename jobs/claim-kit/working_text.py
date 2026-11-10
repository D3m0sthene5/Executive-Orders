"""Owner-authorized provisional working texts, never original authentication.

This is a validator over existing fragment records and held text; it creates no
source store and grants no custody, ending, current-law or review waiver.
"""
from copy import deepcopy
import hashlib
import json
import re
from pathlib import Path

RULING = 'research/readiness/owner_rulings/2026-10-21-transcription-as-text.md'
NOTE = 'original not yet held; replace and re-check quotes when an official copy is retrieved.'
CONFIRMATION_SCHEMA = 'eo-lachmann-confirmation/v1'
CONFIRMATION_METHODS = frozenset({'machine', 'agent'})
CONFIRMATION_PATHS = ('jobs/lachmann/output/CONFIRMATIONS.jsonl',
                      'jobs/lachmann/output/AGENT_CONFIRMATIONS.jsonl')
PINNED_FIELDS = ('instrument_id', 'grade', 'sha256', 'text_sha256', 'text_path')
OFFICIAL_PRODUCERS = frozenset({'fr-originals', 'ofr-compilations',
    'isthmian-canal-1911', 'indian-reservations-1912'})
GRADES = frozenset({'compiled_transcription', 'compiled_transcription_lead',
    'mirror_transcription', 'government_printed_copy', 'machine_read_government_printed_copy',
    'government_printed_reproduction', 'archival_replica_scan_pending_codebook'})
REPLICA_PATH = 'jobs/photius-replica-check/output/FRAGMENTS.jsonl'
REPLICA_GRADE = 'archival_replica_checked'
REPLICA_FLAG = 'REPLICA_CHECKED_PROQUEST_BYTES'


def replica_version(row, declaration_path):
    data = row.get('data') if isinstance(row.get('data'), dict) else {}
    return (declaration_path == REPLICA_PATH and row.get('kind') == 'original_representation'
            and row.get('produced_by') == 'photius-replica-check'
            and row.get('acceptable_as_original') is False
            and data.get('acceptable_as_original') is False)


def replica_declaration(row, declaration_path):
    data = row.get('data') if isinstance(row.get('data'), dict) else {}
    check = data.get('check') if isinstance(data.get('check'), dict) else {}
    return (replica_version(row, declaration_path)
            and row.get('grade') == data.get('grade') == REPLICA_GRADE
            and data.get('needs_page_check') is False
            and data.get('requires_page_check') is not True
            and data.get('complete_text') is not False
            and check.get('final') == 'pass')


def checked_replica(ref, index):
    if ref.get('grade') != REPLICA_GRADE or ref.get('acceptable_as_original') is not False:
        return False
    version = [r for r in index.match(ref) if r.get('replica_version')
               and all(r.get(k) == ref.get(k) for k in ('instrument_id', 'sha256', 'text_sha256', 'text_path'))]
    return bool(version) and all(r.get('checked_replica') for r in version)


def _child(root, value, base=None):
    if not isinstance(value, str) or not value:
        raise ValueError('missing_path')
    root = Path(root).resolve()
    p = (Path(base or root) / value).resolve()
    p.relative_to(root)
    return p


def references(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = path + '.' + k if path else k
            if k in ('original_representation', 'original_source', 'source') and isinstance(v, dict):
                yield p, v
            elif k in ('sources', 'source_refs') and isinstance(v, list):
                for n, ref in enumerate(v):
                    if isinstance(ref, dict):
                        yield f'{p}[{n}]', ref
            yield from references(v, p)
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from references(v, f'{path}[{n}]')


def source_sha(ref):
    """Recognize every hash spelling accepted by the mechanical source checker.

    Recognition is canonical; the exact declaration and confirmation checks below
    still reject altered or missing sha256 fields rather than silently rewriting them.
    """
    for key in ('sha256', 'local_file_sha256'):
        value = ref.get(key)
        if isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value.strip().lower()):
            return value.strip().lower()
    return None


class Index:
    """Existing order-specific fragment declarations; loaded once per execution."""
    def __init__(self, repo):
        self.repo = Path(repo).resolve()
        self.by_sha = {}
        self.official = {}
        self.official_by_sha = {}
        paths = set(self.repo.glob('jobs/*/output/FRAGMENTS*.jsonl'))
        paths.update(self.repo.glob('jobs/*/data/**/FRAGMENTS*.jsonl'))
        for path in sorted(paths):
            if path.parts[-3] == 'claim-kit':
                continue
            try:
                fh = path.open(encoding='utf-8')
            except OSError:
                continue
            with fh:
                for line in fh:
                    try:
                        row = json.loads(line)
                    except (ValueError, UnicodeError):
                        continue
                    if not isinstance(row, dict) or row.get('kind') != 'original_representation':
                        continue
                    data = row.get('data') if isinstance(row.get('data'), dict) else {}
                    iid = row.get('instrument_id')
                    grade = data.get('grade') or row.get('grade')
                    acceptable = data.get('acceptable_as_original', row.get('acceptable_as_original'))
                    sha = data.get('sha256')
                    if not isinstance(iid, str) or not source_sha({'sha256': sha}):
                        continue
                    try:
                        text_path = _child(self.repo, data.get('text_path'), path.parent)
                        # Some producers publish repo-relative text paths.
                        if not text_path.is_file():
                            text_path = _child(self.repo, data.get('text_path'))
                        rel = text_path.relative_to(self.repo).as_posix()
                    except (ValueError, TypeError):
                        continue
                    rec = {'instrument_id': iid, 'grade': grade, 'acceptable_as_original': acceptable,
                           'sha256': sha, 'text_sha256': data.get('text_sha256'), 'text_path': rel,
                           'declaration_path': path.relative_to(self.repo).as_posix(),
                           'requires_page_check': bool(data.get('needs_page_check') or data.get('requires_page_check')),
                           'complete_text': data.get('complete_text'), 'url': data.get('url')}
                    if replica_version(row, rec['declaration_path']):
                        rec['replica_version'] = True
                        rec['checked_replica'] = replica_declaration(row, rec['declaration_path'])
                    if acceptable is False:
                        self.by_sha.setdefault(source_sha(rec), []).append(rec)
                    elif (acceptable is not False and (acceptable is True or row.get('produced_by') in OFFICIAL_PRODUCERS)
                          and data.get('needs_page_check') is False and text_path.is_file()):
                        # Candidate availability only. This neither authenticates the
                        # source nor substitutes it into a claim.
                        self.official.setdefault(iid, []).append(rec)
                        self.official_by_sha.setdefault(source_sha(rec), []).append(rec)

    def exact_official(self, ref):
        """A shared PDF hash cannot erase an independently declared official representation."""
        if ref.get('acceptable_as_original') is False or ref.get('grade') in GRADES:
            return False
        for candidate in self.official_by_sha.get(source_sha(ref), []):
            if (ref.get('text_path') == candidate['text_path'] and ref.get('url') == candidate.get('url')
                    and isinstance(ref.get('text_sha256'), str)):
                try:
                    raw = _child(self.repo, candidate['text_path']).read_bytes()
                    actual = hashlib.sha256(raw).hexdigest()
                    if actual == ref['text_sha256'] and (not candidate.get('text_sha256') or actual == candidate['text_sha256']):
                        return True
                except (OSError, ValueError):
                    continue
        return False

    def match(self, ref):
        found = self.by_sha.get(source_sha(ref), [])
        if ref.get('text_path'):
            found = [r for r in found if r['text_path'] == ref['text_path']]
        elif ref.get('url'):
            found = [r for r in found if not r['url'] or r['url'] == ref['url']]
        return found


def confirmation(ref):
    return {k: ref.get(k) for k in ('instrument_id', 'grade', 'sha256', 'text_sha256', 'text_path')}


def key(ref):
    return tuple(ref.get(k) for k in PINNED_FIELDS)


def load_confirmations(repo):
    """Last record per order wins, including a negative agent review."""
    root = Path(repo)
    result = {}
    for rel in CONFIRMATION_PATHS:
        path = root / rel
        if not path.is_file():
            continue
        with path.open(encoding='utf-8') as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict) and isinstance(record.get('instrument_id'), str):
                    result[record['instrument_id']] = {'source_path': rel, 'record': record}
    return result


def confirmation_rejection(c, index, root):
    """The tracker and claim-kit share the existing exact-record acceptance rule."""
    if not isinstance(c, dict):
        return 'malformed_record_or_unknown_schema_or_method'
    if (c.get('schema') != CONFIRMATION_SCHEMA or not isinstance(c.get('instrument_id'), str)
            or c.get('method') not in CONFIRMATION_METHODS):
        return 'malformed_record_or_unknown_schema_or_method'
    if c.get('acceptable_as_original') is not False:
        return 'acceptable_as_original_not_false'
    if c.get('grade') not in GRADES:
        return 'grade_not_a_working_text_grade'
    if c.get('confirmed') is not True:
        return 'not_confirmed'
    if c.get('identity_confirmed') is not True:
        return 'identity_not_confirmed'
    if c.get('complete_text_confirmed') is not True:
        return 'complete_text_not_confirmed'
    matches = [r for r in index.by_sha.get(source_sha({'sha256': c.get('sha256')}) or '', [])
               if all(r.get(k) == c.get(k) for k in PINNED_FIELDS)]
    if not matches:
        return 'pinned_fields_match_no_loaded_fragment'
    if ((c.get('requires_page_check') is not False or any(r['requires_page_check'] for r in matches))
            and c.get('pages_confirmed') is not True):
        return 'pages_not_confirmed_but_page_check_required'
    if any(r.get('complete_text') is False for r in matches):
        return 'fragment_declares_text_incomplete'
    try:
        raw = _child(root, c['text_path']).read_bytes()
    except (OSError, ValueError, KeyError):
        return 'text_file_missing_or_hash_mismatch'
    if hashlib.sha256(raw).hexdigest() != c.get('text_sha256'):
        return 'text_file_missing_or_hash_mismatch'
    return None


def matching_confirmation(ref, repo, records=None, index=None):
    """Only the selected representation may inherit a current valid confirmation."""
    records = load_confirmations(repo) if records is None else records
    current = records.get(ref.get('instrument_id'))
    if not current or key(current['record']) != key(ref):
        return None
    if index is None:
        # Existing provider cache verifies all fragment bytes and consulted path
        # resolutions on each use; it never caches confirmation records or text.
        from fragment_cache import shared
        index = shared(repo)
    if confirmation_rejection(current['record'], index, repo):
        return None
    # Preserve the applicable declaration set, including its page requirements.
    # A later source edit must not keep an old affirmation alive merely because
    # the five headline fields still happen to match.
    applicable = [r for r in index.by_sha.get(source_sha(current['record']), [])
                  if key(r) == key(current['record'])]
    return dict(deepcopy(current), fragments=sorted(deepcopy(applicable),
                 key=lambda r: json.dumps(r, sort_keys=True)))


# Lachmann skipped-witness rule (Gutenberg, 2026-11-09; owner switch, default "void" = the rule before that date).
# A frozen prior confirmation is compared with the current Lachmann record. Under "void", any difference makes it
# stale. On 2026-11-07 one Photius GPO printing joined evidence.skipped_witnesses of 193 confirmations whose verdict,
# grade, text and used witnesses were unchanged, and all 193 left the ready count (F-20261107-ready-drop-193-photius-
# witness; on 2026-11-09, 628 confirmations of 126 orders still differ only there). Under "flag", the only tolerated
# difference is skipped witnesses ADDED with a known reason; Lachmann never compared them, so what was confirmed did
# not change. Each addition is returned as a recheck flag instead (an official printing now exists: the h01 page
# check of D-20261108-photius-recheck is the substantive follow-up). Anything else stays stale: a removed or edited
# skipped witness, an unknown reason, any other field, the fragments list or the source file.
SWITCHES_PATH = 'jobs/claim-kit/WORKING_TEXT_SWITCHES.json'
SKIPPED_WITNESS_MODES = ('void', 'flag')
TOLERATED_SKIP_REASONS = frozenset({'grade_not_in_working_text_policy', 'text_hash_mismatch'})


_MODE_CACHE = {}


def skipped_witness_mode(repo):
    """The owner's switch; a missing, unreadable or unknown value keeps today's behaviour ("void")."""
    path = Path(repo) / SWITCHES_PATH
    try:
        st = path.stat()
        stamp = (str(path.resolve()), st.st_mtime_ns, st.st_size)
    except OSError:
        return 'void'
    if stamp not in _MODE_CACHE:
        try:
            mode = json.loads(path.read_text(encoding='utf-8')).get('skipped_witness_addition')
        except (OSError, ValueError, AttributeError):
            mode = None
        _MODE_CACHE.clear()
        _MODE_CACHE[stamp] = mode if mode in SKIPPED_WITNESS_MODES else 'void'
    return _MODE_CACHE[stamp]


def _canon(w):
    return json.dumps(w, sort_keys=True)


def confirmation_drift(prior, current, mode='void'):
    """("same" | "flag" | "stale", added skipped witnesses). Never "flag" under mode "void"."""
    if current == prior:
        return 'same', []
    if mode != 'flag' or not isinstance(prior, dict) or not isinstance(current, dict):
        return 'stale', []
    try:
        pw = list(prior['record']['evidence']['skipped_witnesses'])
        cw = list(current['record']['evidence']['skipped_witnesses'])
    except (KeyError, TypeError):
        return 'stale', []
    remaining = [_canon(w) for w in cw]
    for w in pw:
        if _canon(w) not in remaining:
            return 'stale', []          # a prior skipped witness was removed or edited
        remaining.remove(_canon(w))
    added = [json.loads(w) for w in remaining]
    if not added or any(not isinstance(w, dict) or w.get('why') not in TOLERATED_SKIP_REASONS for w in added):
        return 'stale', []
    # Everything except the skipped-witness list must be identical.
    p2, c2 = deepcopy(prior), deepcopy(current)
    p2['record']['evidence']['skipped_witnesses'] = c2['record']['evidence']['skipped_witnesses'] = []
    if p2 != c2:
        return 'stale', []
    return 'flag', added


def recheck_flag(w):
    return 'working_text:skipped_witness_added_recheck:' + str(w.get('grade')) + ':' + str(w.get('why'))


def require_current_confirmation(dossier, repo, records=None, index=None):
    prior = dossier.get('working_text_confirmation')
    if prior is None:
        return
    original = dossier.get('evidence', {}).get(dossier.get('original_source_id'), {})
    ref = original.get('source', {})
    current = matching_confirmation(ref, repo, records, index)
    state, added = confirmation_drift(prior, current, skipped_witness_mode(repo))
    if state == 'stale':
        raise ValueError('changed or invalid working-text confirmation: ' + str(dossier.get('instrument_id')))
    return [recheck_flag(w) for w in added]


def blank(disclosed_refs, prior=None):
    distinct = {key(ref): ref for ref in disclosed_refs}
    return {'ruling': RULING, 'standing_note': NOTE,
            'replacement_required': True, 'quotation_recheck_required': True,
            'confirmations': [dict(confirmation(ref),
                                   identity_confirmed=bool(prior and key(prior['record']) == key(ref)),
                                   complete_text_confirmed=bool(prior and key(prior['record']) == key(ref)),
                                   pages_confirmed=(prior['record'].get('pages_confirmed') is True)
                                       if prior and key(prior['record']) == key(ref) else False,
                                   **({'prior_confirmation': deepcopy(prior)}
                                      if prior and key(prior['record']) == key(ref) else {}))
                              for ref in distinct.values()]}


def policy(claim, repo, index=None, flags=None):
    """Return (errors, exact dependent refs). Bytes/quotes are additional checks.

    ``flags``, when a list, receives non-blocking recheck flags (the owner's skipped-witness switch only).

    No claim may relabel a derivative as original. Identity/completeness are
    explicit producer confirmations pinned to the declared representation; the
    independent reviewer must substantiate them from the held sources.
    """
    index = index or Index(repo)
    errors, dependent = [], []
    replica_used = any(checked_replica(ref, index) for _, ref in references(claim))
    if replica_used:
        if REPLICA_FLAG not in (claim.get('informational_flags') or []):
            errors.append('checked_replica:proquest_bytes_flag_required')
    elif REPLICA_FLAG in (claim.get('informational_flags') or []):
        errors.append('checked_replica:proquest_bytes_flag_without_pass')
    for path, ref in references(claim):
        matches = index.match(ref)
        known_derivative_hash = bool(index.by_sha.get(source_sha(ref)))
        flagged = ref.get('acceptable_as_original') is False or ref.get('grade') in GRADES
        # Recognition must not trust a claim-controlled path: an alias cannot
        # erase the derivative classification attached to the actual source hash.
        if (not known_derivative_hash and not flagged) or index.exact_official(ref) or checked_replica(ref, index):
            continue
        dependent.append(ref)
        if ref.get('acceptable_as_original') is not False or ref.get('grade') not in GRADES:
            errors.append(path + ':working_text_exact_grade_and_false_flag_required')
        exact = [r for r in matches if all(r.get(k) == ref.get(k)
                 for k in ('instrument_id', 'grade', 'sha256', 'text_path', 'text_sha256'))
                 and isinstance(r.get('text_sha256'), str) and len(r['text_sha256']) == 64]
        if not exact:
            errors.append(path + ':working_text_fragment_identity_or_grade_mismatch')
            continue
        if path == 'original_representation' or path.endswith('.original_source'):
            if ref.get('instrument_id') != claim.get('instrument_id'):
                errors.append(path + ':working_text_wrong_order')
        if any(r.get('complete_text') is False for r in exact):
            errors.append(path + ':working_text_known_incomplete')
        try:
            raw = _child(repo, ref.get('text_path')).read_bytes()
            text = raw.decode('utf-8')
            if hashlib.sha256(raw).hexdigest() != ref.get('text_sha256'):
                errors.append(path + ':working_text_text_hash_mismatch')
            start, end = ref.get('char_start'), ref.get('char_end')
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                    or text[start:end] != ref.get('quote')):
                errors.append(path + ':working_text_quote_mismatch')
            if path == 'original_representation' and (start != 0 or end != len(text)):
                errors.append(path + ':working_text_incomplete_representation_span')
        except (OSError, ValueError, UnicodeError, TypeError):
            errors.append(path + ':working_text_missing_bytes')
    for n, clause in enumerate(claim.get('operative_clauses', []) if isinstance(claim, dict) else []):
        if not isinstance(clause, dict):
            continue
        ref = clause.get('original_source')
        if isinstance(ref, dict) and (ref.get('acceptable_as_original') is False or index.by_sha.get(source_sha(ref))) and not index.exact_official(ref):
            if clause.get('original_operative_text') != ref.get('quote'):
                errors.append(f'operative_clauses[{n}]:working_text_operative_quote_mismatch')
    if not dependent:
        if claim.get('working_text'):
            errors.append('working_text:disclosure_without_dependent_source')
        return errors, dependent
    disclosure = claim.get('working_text')
    if not isinstance(disclosure, dict):
        return errors + ['working_text:disclosure_required'], dependent
    if (disclosure.get('ruling') != RULING or disclosure.get('standing_note') != NOTE
            or disclosure.get('replacement_required') is not True
            or disclosure.get('quotation_recheck_required') is not True):
        errors.append('working_text:replacement_and_recheck_note_required')
    confirmations = disclosure.get('confirmations')
    if not isinstance(confirmations, list) or any(not isinstance(c, dict) for c in confirmations):
        return errors + ['working_text:confirmations_required'], dependent
    by_key = {key(c): c for c in confirmations}
    if len(by_key) != len(confirmations) or set(by_key) != {key(r) for r in dependent}:
        errors.append('working_text:confirmation_membership_mismatch')
    reused_records = load_confirmations(repo) if any(c.get('prior_confirmation') is not None for c in confirmations) else {}
    current_by_key = {}
    for ref in dependent:
        for candidate in index.official.get(ref.get('instrument_id'), []):
            if candidate['sha256'] == ref.get('sha256'):
                continue
            try:
                raw = _child(repo, candidate['text_path']).read_bytes()
                if candidate.get('text_sha256') and hashlib.sha256(raw).hexdigest() != candidate['text_sha256']:
                    continue
                if raw.strip():
                    errors.append('working_text:official_copy_available_recheck_required')
                    break
            except (OSError, ValueError):
                continue
        c = by_key.get(key(ref), {})
        prior = c.get('prior_confirmation')
        if prior is not None:
            if key(ref) not in current_by_key:
                current_by_key[key(ref)] = matching_confirmation(ref, repo, records=reused_records, index=index)
            current = current_by_key[key(ref)]
            state, added = confirmation_drift(prior, current, skipped_witness_mode(repo))
            if state == 'stale':
                errors.append('working_text:prior_confirmation_stale')
            elif c != blank([ref], prior)['confirmations'][0]:
                errors.append('working_text:prior_confirmation_changed')
            elif added and flags is not None:
                flags.extend(recheck_flag(w) for w in added)
        if c.get('identity_confirmed') is not True or c.get('complete_text_confirmed') is not True:
            errors.append('working_text:identity_and_complete_text_confirmation_required')
        if any(r['requires_page_check'] for r in index.match(ref)) and c.get('pages_confirmed') is not True:
            errors.append('working_text:page_confirmation_required')
    return list(dict.fromkeys(errors)), dependent
