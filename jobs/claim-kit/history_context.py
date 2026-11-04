"""Explicit, source-validated MAITLAND research in ordinary work packages.

Context is never a claim source or an approval. Rebuilding it verifies the live
bundle, every source/review and the current history method before consumption.
"""
from pathlib import Path
import hashlib

import provision_history as history

SCHEMA = 'eo-claim-kit-history-context/v1'
NOTICE = ('Selected reviewed provision histories only. Text and legal effect have '
          'separate scopes; unknowns and coverage limits remain. No complete order, '
          'canonical claim, independent whole-case approval or human certification.')


def collect(repo, ids, bundles, on='2026-10-14'):
    repo = Path(repo).resolve()
    if not isinstance(bundles, (list, tuple)) or not 1 <= len(bundles) <= 20:
        raise ValueError('bounded explicit history bundle list required')
    entries = []
    seen = set()
    for supplied in bundles:
        path = Path(supplied)
        path = (repo / path).resolve() if not path.is_absolute() else path.resolve()
        if not path.is_relative_to(repo / 'research'):
            raise ValueError('history bundle must stay under repository research')
        rel = path.relative_to(repo).as_posix()
        if rel in seen:
            raise ValueError('duplicate history bundle')
        seen.add(rel)
        # Public API verifies current sources, independent scoped reviews, and
        # transition membership. It makes no inference from previous answers.
        result = history.dated_query(repo, path, on)
        selected = [q for q in result['queries'] if q['instrument_id'] in ids]
        if not selected:
            raise ValueError('history bundle has no selected order: ' + rel)
        entries.append({'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'queries': selected})
    return {'schema': SCHEMA, 'on': on, 'notice': NOTICE,
            'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'bundles': sorted(entries, key=lambda e: e['path'])}


def verify(repo, ids, context, on='2026-10-14'):
    if not isinstance(context, dict) or context.get('schema') != SCHEMA:
        raise ValueError('invalid reviewed history context')
    if context.get('on') != on:
        raise ValueError('reviewed history query date differs from packet cutoff')
    current = collect(repo, ids, [e['path'] for e in context['bundles']], on)
    if current != context:
        raise ValueError('changed reviewed history context; prepare a new version')


def for_order(context, iid):
    return {'notice': context['notice'], 'on': context['on'],
            'queries': [{'bundle_path': e['path'], 'bundle_sha256': e['sha256'], **q}
                        for e in context['bundles'] for q in e['queries']
                        if q['instrument_id'] == iid]}
