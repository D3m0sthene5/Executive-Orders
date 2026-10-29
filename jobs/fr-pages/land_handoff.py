"""Bounded Shepard/PLO acquisition and held-page handoff to native source supplements.

Defaults read already-held extracts. Acquisition is an explicit separate command.
Nothing here determines an ending, approves a source grade or changes a claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

SCHEMA = 'eo-source-excerpt-declarations/v1'
DEFAULT_IDS = ('EO:7373', 'EO:7510')
MAX_SOURCES = 3
MAX_RAW = 4_000_000
MAX_TEXT = 1_000_000
HEX = re.compile(r'[0-9a-f]{64}\Z')
SETTINGS = {'max_requests': 24, 'max_download_bytes': 120_000_000,
            'max_issue_bytes': 40_000_000, 'commit_max_bytes': MAX_RAW,
            'commit_total_bytes': 12_000_000, 'min_interval_seconds': 1.0,
            'try_issue_slice': False, 'auto_from_shepard': {'enabled': False, 'max_items': 3}}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def within(root, path):
    path = Path(path).resolve()
    path.relative_to(root.resolve())
    return path


def child(root, base, rel):
    if not isinstance(rel, str) or '\\' in rel:
        raise ValueError('invalid provider-relative path')
    p = PurePosixPath(rel)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('unsafe provider-relative path')
    path = within(root, base.joinpath(*p.parts))
    path.relative_to(base.resolve())
    return path


def targets(ids):
    ids = tuple(dict.fromkeys(ids))
    if not 1 <= len(ids) <= 2 or any(not re.fullmatch(r'EO:\d+[A-Z]?', i) for i in ids):
        raise ValueError('select one or two explicit EO targets')
    return ids


def read_manifest(repo, manifest):
    manifest = within(repo, manifest)
    raw = manifest.read_bytes()
    if len(raw) > 8_000_000:
        raise ValueError('source manifest exceeds bound')
    rows = []
    for n, line in enumerate(raw.splitlines(), 1):
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError('non-object source record')
            rows.append((n, row))
    return manifest, raw, rows


def declaration(repo, manifest, ids):
    repo, ids = Path(repo).resolve(), targets(ids)
    manifest, raw, rows = read_manifest(repo, manifest)
    entries, holds, seen = [], [], set()
    for number, row in rows:
        use = sorted(set(row.get('instrument_ids') or []) & set(ids))
        actor = row.get('printed_instrument_id')
        if not use or not isinstance(actor, str) or not re.fullmatch(r'PLO:\d+', actor):
            continue
        pointer = manifest.relative_to(repo).as_posix() + ':' + str(number)
        try:
            if row.get('role') != 'official_federal_register_page_of_a_later_instrument':
                raise ValueError('source role is not an acting-instrument page')
            if row.get('location_confidence') != 'high' or row.get('needs_page_check') is not False:
                raise ValueError('location still requires page checking before this bounded handoff')
            if not str(row.get('url', '')).startswith('https://') or not row.get('page_or_item'):
                raise ValueError('missing HTTPS/page locator')
            paths = {}
            for name, hashkey, limit in [('cache_path', 'sha256', MAX_RAW), ('text_path', 'text_sha256', MAX_TEXT)]:
                path = child(repo, manifest.parent, row.get(name))
                if not HEX.fullmatch(str(row.get(hashkey, ''))) or not path.is_file() or path.stat().st_size > limit:
                    raise ValueError('missing/bounded source bytes: ' + name)
                content = path.read_bytes()
                if sha(content) != row[hashkey]:
                    raise ValueError('source hash mismatch: ' + name)
                paths[name] = path
            if not paths['cache_path'].read_bytes().startswith(b'%PDF-'):
                raise ValueError('raw extract is not PDF bytes')
            text = paths['text_path'].read_bytes().decode('utf-8')
            if not text.strip():
                raise ValueError('empty text')
            key = (actor, row['sha256'], row['text_sha256'])
            if key in seen:
                for entry in entries:
                    if (entry['actor_id'], entry['source']['sha256'], entry['source']['text_sha256']) == key:
                        entry['instrument_ids'] = sorted(set(entry['instrument_ids']) | set(use))
                continue
            if any(e['actor_id'] == actor and e['source']['sha256'] != row['sha256'] for e in entries):
                raise ValueError('conflicting actor versions; explicit source selection required')
            seen.add(key)
            entries.append({'alias': actor.replace(':', '_') + '_' + row['sha256'][:12] + '_' + row['text_sha256'][:8],
                'instrument_ids': use, 'actor_id': actor,
                'reason': 'Unreviewed acting-instrument excerpt from ' + pointer + '; verify identity, scope, dates and savings separately.',
                'source': {'url': row['url'], 'sha256': row['sha256'], 'text_sha256': row['text_sha256'],
                           'text_path': paths['text_path'].relative_to(repo).as_posix(),
                           'local_path': paths['cache_path'].relative_to(repo).as_posix(),
                           'page_or_item': row['page_or_item']},
                'char_start': 0, 'char_end': len(text)})
        except (OSError, ValueError, TypeError) as exc:
            holds.append({'source_record': pointer, 'actor_id': actor, 'targets': use, 'reason': str(exc)})
    # An ambiguous actor version must not silently leave one arbitrary version selected.
    conflicted = {h['actor_id'] for h in holds if h['reason'].startswith('conflicting actor versions')}
    entries = [e for e in entries if e['actor_id'] not in conflicted]
    if len(entries) > MAX_SOURCES:
        raise ValueError('more than three eligible extracts; narrow the source manifest')
    audit = {'schema': 'eo-land-source-handoff/1', 'source_manifest': manifest.relative_to(repo).as_posix(),
             'source_manifest_sha256': sha(raw), 'targets': list(ids), 'holds': holds,
             'eligible_sources': len(entries), 'legal_approval': False, 'original_text_attribution': False}
    return {'schema': SCHEMA, 'sources': entries}, audit


def fresh_research(repo, dest):
    dest = within(repo / 'research', dest)
    if dest.exists():
        raise ValueError('fresh research destination required')
    return dest


def export(repo, manifest, ids, dest):
    repo = Path(repo).resolve()
    dest = fresh_research(repo, Path(dest).resolve())
    declared, audit = declaration(repo, manifest, ids)
    dest.mkdir(parents=True)
    (dest / 'HANDOFF.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    if declared['sources']:
        (dest / 'DECLARATIONS.json').write_text(json.dumps(declared, indent=2) + '\n', encoding='utf-8')
    return dest, declared, audit


def acquire(repo, ids, dest, engine=None):
    """Explicit small native fr-pages run; canonical settings and outputs stay untouched."""
    repo, ids = Path(repo).resolve(), targets(ids)
    dest = fresh_research(repo, Path(dest).resolve())
    if engine is None:
        import frpages as engine
    plos = engine.plo_index(str(repo))
    selected = []
    held_path = repo / 'jobs/fr-pages/output/SOURCES.jsonl'
    held = set()
    if held_path.is_file():
        declarations, _ = declaration(repo, held_path, ids)
        held = {int(e['actor_id'].split(':')[1]) for e in declarations['sources']}
    for row in engine.auto_wanted(str(repo), plos, len(plos)):
        use = sorted(set(row['targets']) & set(ids))
        if use and row['plo'] not in held:
            selected.append(dict(row, targets=use))
        if len(selected) == MAX_SOURCES:
            break
    dest.mkdir(parents=True)
    config, out = dest / 'config', dest / 'sources'
    (config / 'data').mkdir(parents=True); out.mkdir()
    (config / 'data/WANTED.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in selected), encoding='utf-8')
    (config / 'settings.json').write_text(json.dumps(SETTINGS, indent=2) + '\n', encoding='utf-8')
    pins = {}
    for rel in (engine.PLO_TABLE, engine.SHEPARD_EDGES):
        p = repo / rel
        if p.is_file():
            pins[rel] = sha(p.read_bytes())
    (dest / 'PLAN.json').write_text(json.dumps({'targets': list(ids), 'wanted': selected, 'input_sha256': pins,
        'settings': SETTINGS, 'already_held_actors': sorted(held), 'legal_approval': False}, indent=2) + '\n')
    if not selected:
        return {'selected': 0, 'network_started': False}
    # Isolate an inherited request override so this opt-in command keeps its cap.
    old = os.environ.pop('JOB_MAX_REQUESTS', None)
    try:
        with tempfile.TemporaryDirectory(prefix='eo-land-cache-') as cache:
            return engine.run(str(repo), str(config), str(out), cache,
                              str(repo / 'jobs/fr-pages/output'))
    finally:
        if old is not None:
            os.environ['JOB_MAX_REQUESTS'] = old


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', default='.')
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('declare', 'prepare', 'acquire'):
        s = sub.add_parser(name)
        s.add_argument('--ids', nargs='+', default=list(DEFAULT_IDS))
        s.add_argument('--write', required=True)
        if name != 'acquire':
            s.add_argument('--sources', default='jobs/fr-pages/output/SOURCES.jsonl')
        if name == 'prepare':
            s.add_argument('--parent', required=True); s.add_argument('--agent', required=True)
    a = p.parse_args(); repo = Path(a.repo).resolve()
    dest = repo / a.write
    if a.command == 'acquire':
        result = acquire(repo, a.ids, dest)
    else:
        declared_dir = dest if a.command == 'declare' else dest.with_name(dest.name + '-source-handoff')
        folder, declarations, result = export(repo, repo / a.sources, a.ids, declared_dir)
        if a.command == 'prepare':
            if not declarations['sources']:
                raise SystemExit('No eligible held extracts; see HANDOFF.json holds')
            sys.path.insert(0, str(repo / 'jobs/claim-kit'))
            import source_supplement
            result = source_supplement.prepare(repo, repo / a.parent, folder / 'DECLARATIONS.json', a.agent, dest)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
