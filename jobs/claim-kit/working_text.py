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
OFFICIAL_PRODUCERS = frozenset({'fr-originals', 'ofr-compilations',
    'isthmian-canal-1911', 'indian-reservations-1912'})
GRADES = frozenset({'compiled_transcription', 'compiled_transcription_lead',
    'mirror_transcription', 'government_printed_copy', 'machine_read_government_printed_copy',
    'government_printed_reproduction', 'archival_replica_scan_pending_codebook'})


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
    return tuple(ref.get(k) for k in ('instrument_id', 'grade', 'sha256', 'text_sha256', 'text_path'))


def blank(disclosed_refs):
    distinct = {key(ref): ref for ref in disclosed_refs}
    return {'ruling': RULING, 'standing_note': NOTE,
            'replacement_required': True, 'quotation_recheck_required': True,
            'confirmations': [dict(confirmation(ref), identity_confirmed=False,
                                   complete_text_confirmed=False, pages_confirmed=False)
                              for ref in distinct.values()]}


def policy(claim, repo, index=None):
    """Return (errors, exact dependent refs). Bytes/quotes are additional checks.

    No claim may relabel a derivative as original. Identity/completeness are
    explicit producer confirmations pinned to the declared representation; the
    independent reviewer must substantiate them from the held sources.
    """
    index = index or Index(repo)
    errors, dependent = [], []
    for path, ref in references(claim):
        matches = index.match(ref)
        known_derivative_hash = bool(index.by_sha.get(source_sha(ref)))
        flagged = ref.get('acceptable_as_original') is False or ref.get('grade') in GRADES
        # Recognition must not trust a claim-controlled path: an alias cannot
        # erase the derivative classification attached to the actual source hash.
        if (not known_derivative_hash and not flagged) or index.exact_official(ref):
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
        if c.get('identity_confirmed') is not True or c.get('complete_text_confirmed') is not True:
            errors.append('working_text:identity_and_complete_text_confirmation_required')
        if any(r['requires_page_check'] for r in index.match(ref)) and c.get('pages_confirmed') is not True:
            errors.append('working_text:page_confirmation_required')
    return list(dict.fromkeys(errors)), dependent
