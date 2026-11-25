"""Naude: held sources that the source registry names for a packet member but its dossier does not cite.

Named for Gabriel Naude, whose Advis pour dresser une bibliotheque (1627) held that a library's catalogue must
list what the library actually holds. Gilbreth (research/excavator/claude-bracton-2026-11-25/GILBRETH.md) measured
15 producer blocks on sources the repository already held but the packet's evidence catalogue lacked: the
registry rows were written for the order (a source-ladder request, say), but the compiler pairs a non-census text
with an order only through a later-event fragment, so the text never became dossier evidence.

Preparation only. For each member, `scan` lists every jobs/*/output/SOURCES.jsonl row whose instrument_ids or
requested_for_instrument_ids name it and whose bytes and text are not already cited by the dossier, with the
actual checker's offline custody status. Only a row whose original bytes pass custody and are on this machine,
and whose text file matches its hash, gets mechanical excerpt spans: the whole text up to the compiler's
ACTOR_TEXT limit, otherwise exact windows around lexical mentions of the order's number (the ACTOR_TEXT window
rule). `declaration` turns those spans into a source_supplement declaration (eo-source-excerpt-declarations/v1)
that `source_supplement.prepare` seals into a new packet. A source whose bytes are not held is listed for
acquisition and never declared. Nothing here selects a source as a basis, judges relevance or decides a status;
every excerpt keeps source_supplement's notice, checks and independent review.
"""
import json
from pathlib import Path
import re

import batch as B
import build
from source_supplement import SCHEMA as DECLARATION_SCHEMA

SCHEMA = 'eo-claim-kit-held-sources/v1'
PASS_STATUSES = {'held_bytes_verified', 'held_bytes_in_release_or_repo', 'gpo_published_hash_match'}
MAX_DECLARED = 100  # source_supplement accepts at most 100 declarations
MAX_TEXT_BYTES = 32_000_000
ACTING_ROLES = {'acting_instrument_text', 'official_federal_register_page_of_a_later_instrument'}
NON_EO_ACTOR = re.compile(r'(?:PLO|PROC|STAT|PL|PUBRES|ACT|NOTICE|MEMORANDUM|PRES_DETERMINATION|FRDOC|FRPAGE|'
                          r'FS_REG|CANAL_ZONE_ORDER):[A-Za-z0-9_.:/ -]{1,60}')
HEX64 = re.compile(r'[0-9a-f]{64}')


def _rel(repo, declaration, raw):
    """Repository-relative path of a registry text_path, resolved as the compiler resolves it, or None."""
    anchor = repo if raw.startswith(('jobs/', 'research/')) else declaration.parent
    try:
        return (anchor / raw).resolve().relative_to(repo).as_posix()
    except (OSError, ValueError):
        return None


def registry(repo, ids):
    """{member: [registry rows naming it]} from every jobs/*/output/SOURCES.jsonl, in file and line order."""
    repo = Path(repo).resolve()
    wanted = set(ids)
    found = {iid: [] for iid in ids}
    for path in sorted(repo.glob('jobs/*/output/SOURCES.jsonl')):
        decl = path.relative_to(repo).as_posix()
        with path.open(encoding='utf-8') as fh:
            for number, line in enumerate(fh, 1):
                if not any(i in line for i in wanted):
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict) or not isinstance(row.get('text_path'), str):
                    continue
                sha = str(row.get('sha256') or '').lower()
                if not HEX64.fullmatch(sha):
                    continue
                targets = set()
                for key in ('instrument_ids', 'requested_for_instrument_ids', 'mentioned_instrument_ids'):
                    if isinstance(row.get(key), list):
                        targets |= {t for t in row[key] if isinstance(t, str)}
                rel = _rel(repo, path, row['text_path'])
                for iid in sorted(targets & wanted):
                    found[iid].append({
                        'declaration_path': decl, 'line': number, 'sha256': sha, 'text_path': rel,
                        'text_sha256': row.get('text_sha256'),
                        'declares_order_text': row.get('instrument_ids') == [iid] and row.get('role') not in ACTING_ROLES,
                        'request_bound': any(row.get(k) for k in ('request_id', 'wanted_id', 'task_id',
                                                                    'requested_for_instrument_ids')),
                        'url': row.get('url'), 'page_or_item': row.get('page_or_item'),
                        'citation': row.get('citation') or row.get('embedded_in_request'),
                        'role': row.get('role'), 'grade': row.get('grade'),
                        'declared_instrument': (row['instrument_ids'][0] if row.get('role') in ACTING_ROLES
                                                and isinstance(row.get('instrument_ids'), list) and row['instrument_ids']
                                                and NON_EO_ACTOR.fullmatch(str(row['instrument_ids'][0])) else None)})
    return found


def cited(dossier):
    """(raw sha256s, text paths) of every source the dossier's evidence already cites."""
    shas, paths = set(), set()
    for item in dossier.get('evidence', {}).values():
        for key in ('source', 'actor_source'):
            ref = item.get(key) if isinstance(item, dict) else None
            if isinstance(ref, dict):
                for k in ('sha256', 'local_file_sha256'):
                    if isinstance(ref.get(k), str):
                        shas.add(ref[k].lower())
                if isinstance(ref.get('text_path'), str):
                    paths.add(ref['text_path'])
    return shas, paths


def _signing_date(dossier):
    original = dossier.get('evidence', {}).get(dossier.get('original_source_id') or '', {})
    return (original.get('source') or {}).get('signing_date') if isinstance(original, dict) else None


def custody(checker, ctx, sha, url):
    rows = []
    checker.check_source({'sha256': sha, 'url': url}, 'source', ctx, rows, allow_download=False)
    return rows[0]['status'] if rows else None


def local_bytes(repo, ctx, sha):
    """Repository-relative path of a file on this machine holding exactly these bytes, or None."""
    for copy in ctx.index.lookup_sha(sha):
        path = copy.local_path
        if path is None or not Path(path).is_file():
            continue
        try:
            rel = Path(path).resolve().relative_to(repo).as_posix()
        except ValueError:
            continue
        if B.file_sha(Path(path)) == sha:
            return rel
    return None


def excerpts(iid, text, signing_date):
    """Exact (start, end) spans, by the compiler's ACTOR_TEXT rule; [] when a large text never prints the number."""
    if len(text.encode('utf-8')) <= build.ACTOR_TEXT_LIMIT:
        return [(0, len(text))]
    windows = build.context_windows(text, build.target_mentions(iid, text, signing_date) or [])
    chosen, total = [], 0
    for a, b in windows:
        size = len(text[a:b].encode('utf-8'))
        if len(chosen) >= build.WINDOW_CAP or total + size > build.WINDOW_BYTES:
            continue
        chosen.append((a, b))
        total += size
    return chosen


def scan(repo, dossiers, checker, ctx):
    """Per member, the held sources the registry names for it that its dossier does not cite."""
    repo = Path(repo).resolve()
    rows = registry(repo, list(dossiers))
    members, memo = {}, {}
    for iid, d in dossiers.items():
        shas, paths = cited(d)
        seen, out = set(), []
        for row in rows[iid]:
            key = (row['sha256'], row['text_path'])
            if row['sha256'] in shas or row['text_path'] in paths or key in seen:
                continue
            if row['declares_order_text'] and not row['request_bound']:
                continue  # the producer declares the order's own text: the original and working-text routes govern it
            seen.add(key)
            item = {k: row[k] for k in ('declaration_path', 'line', 'sha256', 'text_path', 'url', 'page_or_item',
                                         'citation', 'declared_instrument')}
            if row['sha256'] not in memo:
                memo[row['sha256']] = custody(checker, ctx, row['sha256'], row['url'])
            item['custody_status'] = memo[row['sha256']]
            if item['custody_status'] not in PASS_STATUSES:
                item['state'] = 'bytes_not_held'
                item['next_action'] = ('Acquire and retain the original bytes through the owning source job, then '
                                       're-prepare; held text alone is not custody.')
                out.append(item)
                continue
            text_file = B.safe(repo, row['text_path']) if row['text_path'] else None
            text = None
            if text_file is not None and text_file.is_file() and text_file.stat().st_size <= MAX_TEXT_BYTES:
                raw = text_file.read_bytes()
                if not row['text_sha256'] or B.digest(raw) == str(row['text_sha256']).lower():
                    try:
                        text = raw.decode('utf-8')
                    except UnicodeError:
                        text = None
            if text is None:
                item['state'] = 'text_unavailable'
                out.append(item)
                continue
            if row['declares_order_text'] and build.prints_order(iid, text):
                continue  # a requested copy of the order's own text, not a source about it
            item['text_sha256'] = B.digest(text.encode('utf-8'))
            local = local_bytes(repo, ctx, row['sha256'])
            if local is None:
                item['state'] = 'held_bytes_not_on_this_machine'
                item['next_action'] = 'Materialize the held bytes in this checkout before preparing a supplement.'
                out.append(item)
                continue
            item['local_path'] = local
            spans = excerpts(iid, text, _signing_date(d))
            item['text_chars'] = len(text)
            if not spans:
                item['state'] = 'held_needs_span'
                item['next_action'] = ('Large held text that never prints this order\'s number: declare the exact span '
                                       'in a source supplement (no span is chosen mechanically).')
            elif not (isinstance(row['url'], str) and row['url'].startswith('https://') and row['page_or_item']):
                item['state'] = 'held_locator_incomplete'
            else:
                item['state'] = 'supplement_ready'
                item['excerpts'] = [{'char_start': a, 'char_end': b} for a, b in spans]
            out.append(item)
        members[iid] = out
        # Census actors whose large held text the compiler paired with this order but could not window (no located
        # provision and no lexical mention): the text is held, the dossier cites none of it.
        for entry in d.get('actor_contexts') or []:
            if isinstance(entry, dict) and entry.get('overflow') and not entry.get('evidence_ids'):
                out.append({'state': 'census_actor_text_without_evidence', 'actor_id': entry.get('actor_id'),
                            'overflow': entry['overflow'], 'text_sha256': entry.get('text_sha256'),
                            'next_action': ('The compiler found no provision or printed number to window (OCR or a '
                                            'long dated list): declare the exact span in a source supplement.')})
    counts = {}
    for items in members.values():
        for item in items:
            counts[item['state']] = counts.get(item['state'], 0) + 1
    return {'schema': SCHEMA, 'members': members, 'counts': dict(sorted(counts.items())),
            'network_requests': 0, 'model_tokens': None, 'scientific_approval': False,
            'notice': 'Registry rows only, each checked with the actual checker offline. A listed source is a lead '
                      'for the producer; relevance, identity, date and legal effect require research and review.'}


def _alias(iid, sha, n):
    stem = re.sub(r'[^A-Za-z0-9]', '-', iid.split(':', 1)[-1])
    return f'HELD{stem}_{n}_{sha[:12]}'[:96]


def declaration(held):
    """The source_supplement declaration for every supplement_ready excerpt (at most MAX_DECLARED), and overflow."""
    entries, overflow = [], 0
    for iid, items in held['members'].items():
        n = 0
        for item in items:
            if item['state'] != 'supplement_ready':
                continue
            for span in item['excerpts']:
                if len(entries) >= MAX_DECLARED:
                    overflow += 1
                    continue
                n += 1
                entries.append({
                    'alias': _alias(iid, item['sha256'], n), 'instrument_ids': [iid],
                    'actor_id': item['declared_instrument'] or 'UNREVIEWED_HELD_SOURCE',
                    'reason': ('Held source that ' + item['declaration_path'] + ' line ' + str(item['line']) +
                               ' registers for ' + iid + ': ' + str(item['citation'] or item['page_or_item'])[:400]),
                    'source': {'url': item['url'], 'sha256': item['sha256'], 'text_path': item['text_path'],
                               'text_sha256': item['text_sha256'], 'page_or_item': item['page_or_item'],
                               'local_path': item['local_path']},
                    'char_start': span['char_start'], 'char_end': span['char_end']})
    return {'schema': DECLARATION_SCHEMA, 'sources': entries}, overflow


def summary(held, declared, overflow):
    return {'counts': held['counts'], 'declared_excerpts': len(declared['sources']), 'declared_overflow': overflow,
            'members_with_held_sources': sorted(i for i, items in held['members'].items() if items)}
