"""Ingestion of agent-located ACT records (act_overrides).

The scanner in excavate.py cannot find every provision that revokes or changes a
target (OCR, number tables, references by title). An agent may locate one and a
separate reviewer may uphold it. This module lets such a record enter
ACTING_PROVISIONS with provenance "agent_located", and refuses everything else.

Input: research/readiness/act_overrides/*.jsonl, one record per line. A record has
the ACT fields of excavate.py plus:
  provision_sha256, target_naming.sha256   sha256 of the quoted spans
  target_text_sha256                       sha256 of the held target text, or null
  review {verdict:"upheld", independent:true, reviewer, review_kind, d6_searched, d6_found,
          source_file}

review.source_file names the committed reviewer ledger (REVIEW.jsonl under research/). Its
line for the record id must say verdict "upheld" with the same reviewer, review_kind and D6
fields, and the sibling UPHELD_ACT_RECORDS.jsonl must hold the reviewed record with every ACT
field equal, so no field can change after review. Unknown fields are refused.

A record is accepted only when the pair is currently unlocated ("target provision
not located"), every span is an exact slice of the held actor text whose sha256 the
record names, and an independent reviewer (not the producer) upheld it after a D6
search. Seeded, planted, example and not-located records are refused, and so is every line
of a pair or id that appears more than once. Nothing here decides law or status.
"""
import datetime, hashlib, json, re
from pathlib import Path

DIRECTORY = 'research/readiness/act_overrides'
PROVENANCE = 'agent_located'
VERBS = {'revoke', 'supersede', 'terminate', 'abolish', 'rescind', 'nullify', 'amend', 'modify',
         'suspend', 'extend', 'continue', 'supplement', 'ratify', 'transfer', 'other'}
SCOPES = {'whole', 'partial', 'whole_via_parent'}
REQUIRED = ('id', 'target_id', 'actor_id', 'producer', 'actor_source', 'char_start', 'char_end',
            'provision_text', 'provision_sha256', 'target_naming', 'verb', 'scope', 'names_target',
            'effective_class', 'effective_date', 'exceptions_text', 'savings_phrases', 'review')
OPTIONAL = ('provision_label', 'reaches_target_via', 'effective_wording', 'notes', 'producer_d6',
            'effective_basis', 'target_text_sha256', 'additional_target_namings', 'located')
PLANT_KEYS = ('seeded', 'planted', 'plant', 'SEEDED')
EFFECTIVE_CLASSES = {'on_signing', 'agency_variable', 'filing', 'relative', 'stated_date', 'unknown'}
# Fields the reviewer upheld; they must equal the reviewed record exactly.
REVIEWED = tuple(f for f in REQUIRED + OPTIONAL if f not in ('review', 'provision_sha256', 'target_text_sha256', 'located'))
SHA256 = re.compile(r'[0-9a-f]{64}')
MARKER = re.compile(r'seeded|planted|\bplant\b|mountweazel|synthetic|fixture|example', re.I)


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load(repo):
    """Return [(relative_path, line_number, parsed_or_None, parse_error)] for every line."""
    rows = []
    for path in sorted((Path(repo) / DIRECTORY).glob('*.jsonl')):
        rel = str(path.relative_to(repo))
        for n, text in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if not text.strip():
                continue
            try:
                rows.append((rel, n, json.loads(text), None))
            except ValueError as e:
                rows.append((rel, n, None, 'invalid_json: ' + str(e)))
    return rows


def _strings(value):
    """Every string anywhere inside a parsed JSON value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _date(value):
    try:
        return datetime.date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _span(errors, name, text, start, end, want, digest, digest_required=True):
    if digest_required and not (isinstance(digest, str) and SHA256.fullmatch(digest)):
        errors.append('span_sha256_missing:' + name)
        return
    if not (_int(start) and _int(end) and 0 <= start < end <= len(text)):
        errors.append('bad_span:' + name)
        return
    if not isinstance(want, str) or text[start:end] != want:
        errors.append('span_text_mismatch:' + name)
    elif digest is not None and digest != sha(want):
        errors.append('span_sha256_mismatch:' + name)


def _review_ledger(repo, rec, review, cache):
    """Check the record against the reviewer's own ledger; return refusal codes."""
    rel = review.get('source_file')
    if repo is None:
        return ['review_ledger_unchecked']
    if not isinstance(rel, str) or not rel.startswith('research/') or '..' in Path(rel).parts \
            or Path(rel).name != 'REVIEW.jsonl' or Path(rel).is_relative_to(DIRECTORY):
        return ['review_source_file_invalid']
    root = Path(repo).resolve()
    # The reviewer ledger must really live under research/ (no symlink out of it).
    if not (root / rel).resolve().is_relative_to(root / 'research') \
            or (root / rel).resolve().is_relative_to((root / DIRECTORY).resolve()):
        return ['review_source_file_invalid']
    if rel not in cache:
        found = {}
        for name, key in (('REVIEW.jsonl', 'review'), ('UPHELD_ACT_RECORDS.jsonl', 'upheld')):
            path = Path(repo) / Path(rel).parent / name
            rows = {}
            try:
                for text in path.read_text(encoding='utf-8').splitlines():
                    if text.strip():
                        row = json.loads(text)
                        rows.setdefault(row.get('id'), []).append(row)
            except (OSError, ValueError, AttributeError):
                rows = None
            found[key] = rows
        cache[rel] = found
    ledger = cache[rel]
    if ledger['review'] is None:
        return ['review_ledger_unreadable']
    entries = ledger['review'].get(rec['id']) or []
    if len(entries) != 1:
        return ['review_ledger_entry_missing' if not entries else 'review_ledger_entry_duplicate']
    entry = entries[0]
    if entry.get('verdict') != 'upheld':
        return ['review_ledger_not_upheld']
    if any(entry.get(k) != review.get(k) for k in ('reviewer', 'review_kind', 'd6_searched', 'd6_found')) \
            or entry.get('target_id') != rec['target_id'] or entry.get('actor_id') != rec['actor_id']:
        return ['review_ledger_mismatch']
    reviewed = (ledger['upheld'] or {}).get(rec['id']) or []
    if len(reviewed) != 1:
        return ['reviewed_record_missing']
    reviewed = reviewed[0]
    errors = []
    for f in REVIEWED:
        mine, theirs = rec.get(f), reviewed.get(f)
        if f == 'target_naming' and isinstance(mine, dict):
            mine = {k: v for k, v in mine.items() if k != 'sha256'}
        if mine != theirs:
            errors.append('changed_after_review:' + f)
    return errors


def names_number(number, text):
    """True when `text` names the order number `number` as a whole token. A lettered number
    ("7975A") also matches its hyphenated, spaced or lowercase forms ("7975-A", "7975 A",
    "7975a"); an unlettered number ("7975") never matches a lettered one ("7975A", "7975-A")."""
    m = re.fullmatch(r'(\d+)([A-Za-z]+)', number)
    if m:
        pattern = r'(?<!\d)' + m.group(1) + r'[-\s]?(?i:' + re.escape(m.group(2)) + r')(?![A-Za-z\d])'
    else:
        pattern = r'(?<!\d)' + re.escape(number) + r'(?!\d)(?!-?[A-Za-z](?![A-Za-z]))'
    return re.search(pattern, str(text)) is not None


def verify(rec, selected, universe, missing_pairs, repo=None, _ledgers=None):
    """Return (accepted_record_or_None, [refusal codes]). `selected` maps instrument id to
    the held representation (with 'text' and 'source'); `missing_pairs` is the set of
    (target, actor) pairs the scanner reported as "target provision not located"."""
    if not isinstance(rec, dict):
        return None, ['not_an_object']
    errors = ['missing_field:' + f for f in REQUIRED if f not in rec]
    errors += ['unknown_field:' + f for f in sorted(rec) if f not in REQUIRED + OPTIONAL + PLANT_KEYS]
    if errors:
        return None, errors
    target, actor, review = rec['target_id'], rec['actor_id'], rec['review']
    if not all(isinstance(rec[k], str) and rec[k] for k in ('id', 'target_id', 'actor_id', 'producer')):
        return None, ['bad_identity_fields']
    # Planted / seeded / example records never enter.
    if any(rec.get(k) for k in PLANT_KEYS):
        errors.append('seeded_or_planted')
    labels = [rec.get('id'), rec.get('producer'), rec.get('origin')]
    if isinstance(review, dict):
        labels += [review.get('reviewer'), review.get('review_kind'), review.get('origin')]
        if any(review.get(k) for k in PLANT_KEYS):
            errors.append('seeded_or_planted')
    if any(isinstance(v, str) and MARKER.search(v) for v in labels):
        errors.append('seeded_or_planted')
    # The pre-gate example record marks its fields "EXAMPLE ONLY"; such text anywhere refuses.
    if any('EXAMPLE ONLY' in v.upper() for v in _strings(rec)):
        errors.append('seeded_or_planted')
    if 'located' in rec and rec['located'] is not True:
        errors.append('not_located_record')
    # Independent review marker.
    if not isinstance(review, dict) or review.get('verdict') != 'upheld':
        errors.append('not_upheld')
    else:
        reviewer, producer = str(review.get('reviewer') or '').strip(), str(rec.get('producer') or '').strip()
        if review.get('independent') is not True or not reviewer or not review.get('review_kind'):
            errors.append('review_not_independent')
        elif reviewer.lower() == producer.lower() or not producer:
            errors.append('reviewer_is_producer')
        if not str(review.get('d6_searched') or '').strip() or not str(review.get('d6_found') or '').strip():
            errors.append('d6_step_missing')
    if errors:
        return None, errors
    if target not in universe or actor not in universe or target == actor:
        return None, ['identity_not_in_census']
    if (target, actor) not in missing_pairs:
        return None, ['pair_not_unlocated']
    if rec['id'].split('@')[0] != 'ACT:' + target + '>' + actor:
        errors.append('id_does_not_match_pair')
    ar = selected.get(actor)
    if not ar:
        return None, ['actor_text_not_held']
    text, src = ar['text'], ar['source']
    given = rec['actor_source'] if isinstance(rec['actor_source'], dict) else {}
    if given.get('text_sha256') != src.get('text_sha256') or sha(text) != src.get('text_sha256'):
        errors.append('actor_text_sha256_mismatch')
    if given.get('text_path') != ar.get('text_path'):
        errors.append('actor_text_path_mismatch')
    tr = selected.get(target)
    want_target = rec.get('target_text_sha256')
    if tr is not None and want_target != tr['source'].get('text_sha256'):
        errors.append('target_text_sha256_mismatch')
    if tr is None and want_target:
        errors.append('target_text_not_held')
    if rec['verb'] not in VERBS:
        errors.append('bad_verb')
    if rec['scope'] not in SCOPES:
        errors.append('bad_scope')
    if rec['effective_class'] not in EFFECTIVE_CLASSES:
        errors.append('bad_effective_class')
    if rec['effective_date'] is not None and not _date(rec['effective_date']):
        errors.append('bad_effective_date')
    if errors:
        return None, errors
    _span(errors, 'provision', text, rec['char_start'], rec['char_end'], rec['provision_text'], rec['provision_sha256'])
    naming = rec['target_naming'] if isinstance(rec['target_naming'], dict) else {}
    _span(errors, 'target_naming', text, naming.get('char_start'), naming.get('char_end'), naming.get('text'), naming.get('sha256'))
    number = target.split(':', 1)[-1]
    if rec['names_target'] is True:
        if not names_number(number, naming.get('text')):
            errors.append('target_number_not_in_naming_span')
    elif not str(rec.get('reaches_target_via') or '').strip() or rec['scope'] == 'whole':
        errors.append('indirect_record_needs_reaches_target_via_and_non_whole_scope')
    if rec['names_target'] is True and str(rec.get('reaches_target_via') or '').strip():
        errors.append('names_target_with_reaches_target_via')
    for field in ('effective_wording', 'additional_target_namings'):
        spans = rec.get(field) or []
        if not isinstance(spans, list):
            errors.append('bad_spans:' + field)
            continue
        for i, w in enumerate(spans):
            w = w if isinstance(w, dict) else {}
            _span(errors, '%s[%d]' % (field, i), text, w.get('char_start'), w.get('char_end'), w.get('text'),
                  w.get('sha256'), digest_required=False)
    if errors:
        return None, errors
    errors = _review_ledger(repo, rec, review, {} if _ledgers is None else _ledgers)
    if errors:
        return None, errors
    out = {k: v for k, v in rec.items() if k in REQUIRED + OPTIONAL and k not in ('located', 'target_text_sha256')}
    out.update(id='ACT:' + target + '>' + actor, override_id=rec['id'], provenance=PROVENANCE,
               signing_date=ar.get('signing_date'), filing_date=ar.get('filing_date'),
               confidence='agent_located_independently_upheld',
               actor_source=dict(src, text_path=ar['text_path']),
               notes=(str(rec.get('notes') or '') + ' Agent-located record (act_overrides); an independent AI review upheld it. '
                      'Hypothesis only: not human certification and not a status.').strip())
    return out, []


def ingest(repo, selected, universe, missing_pairs, rows=None):
    """Return (accepted {(target, actor): record}, report rows). When two lines name the same
    pair or the same id, every one of them is refused: no file order decides which one enters."""
    rows = load(repo) if rows is None else rows
    report, ledgers, verified = [], {}, []
    pairs, ids = {}, {}
    for rel, n, rec, error in rows:
        if isinstance(rec, dict):
            pair = (str(rec.get('target_id')), str(rec.get('actor_id')))
            pairs[pair] = pairs.get(pair, 0) + 1
            ids[str(rec.get('id'))] = ids.get(str(rec.get('id')), 0) + 1
    for rel, n, rec, error in rows:
        row = {'file': rel, 'line': n, 'id': rec.get('id') if isinstance(rec, dict) else None}
        if error:
            report.append(dict(row, status='refused', reasons=[error]))
            continue
        out, reasons = verify(rec, selected, universe, missing_pairs, repo, ledgers)
        if isinstance(rec, dict) and (pairs[(str(rec.get('target_id')), str(rec.get('actor_id')))] > 1 or ids[str(rec.get('id'))] > 1):
            out, reasons = None, ['duplicate_pair'] + reasons
        if out is None:
            report.append(dict(row, status='refused', reasons=reasons))
        else:
            verified.append(out)
            report.append(dict(row, status='ingested', reasons=[]))
    return {(o['target_id'], o['actor_id']): o for o in verified}, report
