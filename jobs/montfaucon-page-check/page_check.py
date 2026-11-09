"""Fail-closed Montfaucon page checks. No source fragment is modified."""
import copy
import hashlib
import json
import re
from pathlib import Path

OFFICIAL = frozenset(('fr-originals', 'ofr-compilations', 'isthmian-canal-1911',
    'indian-reservations-1912', 'tischendorf-originals', 'mabillon-held-printings',
    'photius-gpo-volumes', 'photius-csc-printings', 'photius-free-printings'))
REPLICA = frozenset(('pinakes-proquest-ingest', 'photius-replica-check'))
LEGACY_OFFICIAL = {'fr-originals': 'official/govinfo_fr_issue_pdf',
    'ofr-compilations': 'official/ofr_compilation_1974',
    'isthmian-canal-1911': 'official/ic_compilation_1911',
    'indian-reservations-1912': 'official/gpo_compilation_1912'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ':' in relative:
        raise ValueError('unsafe path')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('path escapes repository')
    return path


def mabillon_legacy_header(source):
    """The provenance header mabillon-held-printings wrote above each passage until 2026-11-09, rebuilt from the
    source fragment's own fields (every byte of it came from them; checked on all 2,015 committed files)."""
    data = source['data']
    kind = (data.get('match') or {}).get('source_kind')
    return (f"Instrument: {source['instrument_id']}\nSource: {data.get('url')}\nSHA-256 of the source file: "
            f"{data.get('sha256')}\nLocation: {data.get('page_or_item')}\nGovernment-printed passage saved by "
            f"hathi-gpo-orders ({kind}); machine OCR, may contain recognition errors and neighbouring text.\n\n"
            ).encode('utf-8')


def validate(root, record, source_cache=None):
    """Return (lane, derived fragment), or reject. Reviews pin the whole record target."""
    root = root.resolve()
    if record.get('schema') != 'montfaucon-page-check/v1' or record.get('final') not in ('pass', 'fail', 'unsure', 'blocked'):
        raise ValueError('invalid final verdict')
    passing = record['final'] == 'pass'
    target = record['target']
    source_path = safe_path(root, target['fragment_path'])
    parts = Path(target['fragment_path']).parts
    if len(parts) < 4 or parts[0] != 'jobs' or parts[2] not in ('output', 'data'):
        raise ValueError('unapproved fragment path')
    job = parts[1]
    lane = 'official' if job in OFFICIAL else 'replica' if job in REPLICA else None
    if lane != record.get('lane'):
        raise ValueError('wrong source lane')
    if source_cache is None:
        source_cache = {}
    if source_path not in source_cache:
        index = {}
        for line in source_path.read_text('utf-8').splitlines():
            if line.strip():
                row = json.loads(line)
                index.setdefault(digest(row), []).append(row)
        source_cache[source_path] = index
    matches = source_cache[source_path].get(target['fragment_sha256'], [])
    if len(matches) != 1:
        raise ValueError('source fragment changed or ambiguous')
    source = matches[0]
    data = source['data']
    # A lead can name a page while declaring no immutable scan hash or held
    # transcription. Such a record may retain a negative finding, never credit.
    negative_missing = not passing and (not data.get('sha256') or not data.get('text_path'))
    if record['final'] == 'blocked' or negative_missing:
        missing = record.get('missing')
        if (not isinstance(missing, dict) or
                not all(isinstance(missing.get(k), str) and missing[k].strip() for k in ('item', 'reason'))):
            raise ValueError('negative lead requires named missing source or span')
    legacy = ('grade' not in source and 'grade' not in data and lane == 'official'
              and (LEGACY_OFFICIAL.get(job) == data.get('route') or
                   (job == 'fr-originals' and data.get('route') in
                    ('official/govinfo_link_fr', 'official/ofr_index_pdf_url'))))
    qualified_gpo = (lane == 'official' and job == 'tischendorf-originals'
        and data.get('route') == 'official/ia_fulltext'
        and data.get('match', {}).get('source_kind') == 'government-printed compilation of executive orders'
        and source.get('grade') == 'machine_read_government_printed_copy'
        and data.get('grade') in (None, 'machine_read_government_printed_copy'))
    qualified_fr = (lane == 'official' and job == 'tischendorf-originals'
        and data.get('route') == 'official/fr_issue_by_date'
        and data.get('match', {}).get('source_kind') == 'govinfo scan of the printed Federal Register daily issue'
        and isinstance(data.get('url'), str)
        and re.fullmatch(r'https://www\.govinfo\.gov/content/pkg/FR-(\d{4}-\d{2}-\d{2})/pdf/FR-\1\.pdf',
                         data['url']) is not None
        and source.get('grade') == 'machine_read_government_printed_copy'
        and data.get('grade') in (None, 'machine_read_government_printed_copy'))
    qualified_mab_fr = (lane == 'official' and job == 'mabillon-held-printings'
        and data.get('route') == 'held/govinfo_fr'
        and data.get('match', {}).get('source_kind') == 'govinfo scan of the printed Federal Register daily issue'
        and isinstance(data.get('url'), str)
        and re.fullmatch(r'https://www\.govinfo\.gov/content/pkg/FR-(\d{4}-\d{2}-\d{2})/pdf/FR-\1\.pdf',
                         data['url']) is not None
        and source.get('grade') == 'machine_read_government_printed_copy'
        and data.get('grade') in (None, 'machine_read_government_printed_copy'))
    rechecked_replica = (lane == 'replica' and job == 'photius-replica-check'
        and source.get('grade') == data.get('grade') == 'archival_replica_check_failed_or_pending'
        and record.get('adjudication') == 'new_independent_page_check')
    if passing and not legacy and not qualified_gpo and not qualified_fr and not qualified_mab_fr and (source.get('grade') != data.get('grade') or not isinstance(data.get('grade'), str)):
        raise ValueError('missing or conflicting immutable grade')
    allowed_grade = 'official_printing' if lane == 'official' else 'archival_replica_checked'
    if passing and not legacy and not rechecked_replica and not qualified_gpo and not qualified_fr and not qualified_mab_fr and data['grade'] != allowed_grade:
        raise ValueError('source grade not admitted for this lane')
    if passing and lane == 'official' and data.get('match', {}).get('source_kind') == 'non-government publication':
        raise ValueError('non-government publication')
    images = target.get('page_images', [])
    if not isinstance(images, list) or (passing and not images):
        raise ValueError('passing check requires nonempty held page_images')
    if negative_missing and record['final'] != 'blocked' and not images:
        raise ValueError('unhashed fail or unsure requires inspected page image')
    if negative_missing and not data.get('sha256') and images:
        inspected = record.get('inspection_source')
        if (not isinstance(inspected, dict) or
                not isinstance(inspected.get('url'), str) or not inspected['url'].startswith('https://') or
                not isinstance(inspected.get('sha256'), str) or
                not re.fullmatch('[0-9a-f]{64}', inspected['sha256']) or
                any(not image.get('url', '').startswith(inspected['url'] + '#page=') for image in images)):
            raise ValueError('unhashed source requires pinned inspection PDF and page URLs')
    labels = set()
    for image in images:
        validate_image(root, image, job, lane)
        if image.get('source_url') != target['url'] or image.get('cited_scope') != target['page_or_item']:
            raise ValueError('page image does not pin cited source item/page')
        if image['page_or_item'] in labels:
            raise ValueError('duplicate page image label')
        labels.add(image['page_or_item'])

    if source.get('instrument_id') != record['instrument_id'] or source.get('kind') != 'original_representation':
        raise ValueError('wrong instrument or kind')
    for key in ('sha256', 'url', 'page_or_item', 'text_sha256', 'text_path'):
        if key == 'text_sha256' and key not in data:
            if negative_missing and target.get(key) not in (None, ''):
                raise ValueError('invented held text SHA-256 pin')
            continue  # The exact held text bytes are still hashed below.
        if negative_missing and key in ('sha256', 'text_sha256', 'text_path'):
            if target.get(key) != data.get(key):
                raise ValueError('changed missing source ' + key)
            continue
        if not isinstance(target.get(key), str) or not target[key] or target[key] != data.get(key):
            raise ValueError('changed or missing source ' + key)
    required_hashes = ('fragment_sha256',) if negative_missing else ('sha256', 'text_sha256', 'fragment_sha256')
    if not all(isinstance(target.get(key), str) and re.fullmatch('[0-9a-f]{64}', target[key]) for key in required_hashes):
        raise ValueError('invalid SHA-256 pin')
    body_scope = (job == 'mabillon-held-printings'
                  and target.get('text_hash_scope') == 'body_after_first_blank_line')
    if target.get('text_hash_scope') is not None and not body_scope:
        raise ValueError('unsupported held text hash scope')
    if body_scope:
        if (not isinstance(target.get('text_file_sha256'), str) or
                not re.fullmatch('[0-9a-f]{64}', target['text_file_sha256'])):
            raise ValueError('missing full held text file SHA-256 pin')
    elif target.get('text_file_sha256') is not None:
        raise ValueError('unexpected full held text file SHA-256 pin')
    if target.get('text_path'):
        text = safe_path(root, (source_path.parent / target['text_path']).relative_to(root).as_posix())
        text_parts = text.relative_to(root).parts
        if text_parts[:2] != ('jobs', job) and text_parts[:2] != ('research', 'montfaucon') and not (
                lane == 'replica' and text_parts[:2] == ('jobs', 'pinakes-proquest-ingest')):
            raise ValueError('held text outside declared dependencies')
        if not isinstance(target.get('text_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', target['text_sha256']):
            raise ValueError('invalid held text SHA-256 pin')
        held = text.read_bytes()
        if body_scope:
            if hashlib.sha256(held).hexdigest() == target['text_sha256']:
                # Since 2026-11-09 Mabillon writes the passage alone. The header it used to prepend was built only
                # from fields of the pinned source fragment, so rebuild it and still require the pinned full file.
                whole = mabillon_legacy_header(source) + held
            else:
                if b'\n\n' not in held:
                    raise ValueError('held text body delimiter missing')
                whole, held = held, held.split(b'\n\n', 1)[1]
            if hashlib.sha256(whole).hexdigest() != target['text_file_sha256']:
                raise ValueError('held text file changed')
        if hashlib.sha256(held).hexdigest() != target['text_sha256']:
            raise ValueError('held text changed')
    reviews = record['reviews']
    if not isinstance(reviews, list) or len(reviews) != 2:
        raise ValueError('two independent reviews required')
    adjudicator = record.get('adjudicator')
    disagreement = reviews[0].get('verdict') != reviews[1].get('verdict')
    if disagreement and not isinstance(adjudicator, dict):
        raise ValueError('review disagreement requires third independent adjudication')
    if adjudicator is not None and not disagreement:
        raise ValueError('adjudicator supplied without pair disagreement')
    examined_reviews = reviews + ([adjudicator] if disagreement else [])
    contexts, verdicts = set(), []
    for review in examined_reviews:
        if review.get('verdict') not in ('pass', 'fail', 'unsure', 'blocked') or review.get('target_sha256') != digest(target):
            raise ValueError('review does not pin exact target')
        verdicts.append(review['verdict'])
        if review['verdict'] == 'pass':
            if not all(review.get(key) is True for key in ('identity_confirmed', 'complete_start_and_closing',
                       'cited_pages_confirmed', 'wording_compared', 'image_source_and_page_confirmed')):
                raise ValueError('pass lacks explicit four-part examination')
            if review.get('substantive_differences') != []:
                raise ValueError('pass has substantive differences or missing comparison list')
        for key in ('context_id', 'reviewer', 'evidence', 'number_seen', 'date_seen',
                    'signature_seen', 'first_words', 'last_words'):
            if not isinstance(review.get(key), str) or not review[key].strip():
                raise ValueError('missing review ' + key)
        contexts.add(review['context_id'])
    if len(contexts) != len(examined_reviews):
        raise ValueError('reviews share a context')
    expected = adjudicator['verdict'] if disagreement else verdicts[0]
    if record['final'] != expected:
        raise ValueError('final contradicts independent verdicts')
    if not passing:
        return lane, None
    result = copy.deepcopy(source)
    result.update(produced_by='montfaucon-page-check', acceptable_as_original=False)
    if legacy or rechecked_replica or qualified_gpo or qualified_fr or qualified_mab_fr:
        result['grade'] = result['data']['grade'] = allowed_grade
    result['data'].update(location_verified=False, needs_page_check=False,
                          acceptable_as_original=False, montfaucon_record_sha256=digest(record))
    result['data']['montfaucon_page_check'] = {'final': 'pass', 'record': record}
    for container in (result, result['data']):
        for key in ('human_reviewed', 'human_verified', 'location_verified'):
            if key in container:
                container[key] = False
    return lane, result


def validate_image(root, image, job, lane):
    if image.get('provenance') != ('official_government_printing' if lane == 'official' else 'proquest_replica'):
        raise ValueError('page image provenance not admitted')
    for key in ('url', 'page_or_item', 'path', 'sha256'):
        if not isinstance(image.get(key), str) or not image[key].strip():
            raise ValueError('missing page image ' + key)
    image_parts = Path(image['path']).parts
    if image_parts[:2] != ('research', 'montfaucon') and image_parts[:2] != ('jobs', job):
        raise ValueError('page image outside declared dependencies')
    if hashlib.sha256(safe_path(root, image['path']).read_bytes()).hexdigest() != image['sha256']:
        raise ValueError('page image bytes changed')


def assemble(root, outcomes=None):
    rows, rejected = [], []
    source_cache = {}  # Exact current source bytes, discarded after this assembly.
    directory = root / 'research/montfaucon'
    paths = ([directory / 'CHECKS.jsonl'] if (directory / 'CHECKS.jsonl').exists() else [])
    paths += sorted((directory / 'checks').glob('*.jsonl'))
    for path in paths:
        for number, line in enumerate(path.read_text('utf-8').splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError('record must be an object')
                rows.append((f'{path.relative_to(root)}:{number}', row))
            except ValueError:
                rejected.append({'record': f'{path.relative_to(root)}:{number}', 'reason': 'invalid JSON'})
    if rejected:
        # An unreadable negative could otherwise leave a matching pass in force.
        return {'official': [], 'replica': []}, rejected
    # Conflicts on one exact source lose credit; other witnesses can coexist.
    def source_key(row):
        target = row.get('target')
        if not isinstance(target, dict):
            target = {}
        return digest([row.get('instrument_id'), row.get('lane'), target.get('fragment_path'),
                       target.get('sha256'), target.get('url'), target.get('page_or_item')])
    keys = [source_key(row) for _, row in rows]
    out = {'official': [], 'replica': []}
    for label, row in rows:
        try:
            if keys.count(source_key(row)) != 1:
                raise ValueError('duplicate exact source target')
            lane, fragment = validate(root, row, source_cache)
            if outcomes is not None:
                outcomes.append({'record': label, 'instrument_id': row['instrument_id'],
                                 'lane': lane, 'final': row['final'], 'record_sha256': digest(row)})
            if fragment is not None:
                out[lane].append(fragment)
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
            rejected.append({'record': label, 'reason': str(error)})
    return out, rejected


def validated_output(root, fragment, lane):
    """Revalidate committed output at consumption time; stale outputs earn no credit."""
    try:
        record = fragment['data']['montfaucon_page_check']['record']
        current, _ = assemble(root)
        return any(row == fragment for row in current[lane]) and validate(root, record) == (lane, fragment)
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        return False
