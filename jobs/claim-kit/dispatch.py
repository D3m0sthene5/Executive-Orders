"""Offline, bounded source/freshness screen before spending model tokens.

This is a preparation diagnostic, never a source authentication or legal verdict.
It reuses frozen-packet validation and the actual checker's custody policy. No
downloads, source requests, reservations, decisions or scientific outputs change.
"""
import importlib.util
import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace

import batch
import assemble
import working_text


def actual_checker():
    path = Path(__file__).resolve().parents[1] / 'claim-checker/checker.py'
    spec = importlib.util.spec_from_file_location('claim_kit_dispatch_checker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_context(repo, checker):
    """Use the ordinary offline custody policy without loading unrelated gates."""
    index = checker.S.build_index(repo, Path(checker.__file__).parent, exclude_jobs=('claim-checker',))
    return SimpleNamespace(index=index, reader=checker.S.TextReader(packed=index.packed_texts),
                           gpo_matched=checker.load_gpo_matched(repo), archive_captures={}, cache_dir=None)


def recovery_tasks(members):
    """Deduplicate acquisition work, retaining every affected order and source role.

    These are native source-ladder Wanted proposals, not submitted requests or a
    source-grade decision. A matching URL cannot replace the requested byte hash.
    """
    tasks = {}
    for member in members:
        for source in member['sources']:
            if source['checks'] and all(c['result'] == 'pass' for c in source['checks']):
                continue
            ref = source['source']
            raw_sha = working_text.source_sha(ref)
            key = raw_sha or batch.canon(ref)
            ident = 'SOURCE:' + batch.digest(key.encode())[:24]
            task = tasks.setdefault(ident, {
                'task_id': ident, 'expected_sha256': raw_sha, 'affected_references': [],
                'check_statuses': [], 'source_locators': [],
                'next_action': ('Retain the exact original bytes through the existing source provider or source-ladder, '
                    'verify the requested hash, and register custody before rechecking. A URL match or text extract alone is insufficient.'
                    if raw_sha else 'Repair the missing or malformed original-source hash from evidence; do not invent it.'),
                'native_wanted': {'wanted_id': 'dispatch-' + ident[7:], 'instrument_ids': [], 'urls': [],
                    'citation': '', 'step': 'source_custody', 'requested_by': 'claim-kit dispatch-check'},
                'automatically_submitted': False, 'scientific_approval': False})
            affected = {'instrument_id': member['instrument_id'], 'evidence_id': source.get('evidence_id'),
                        'field': source.get('field'), 'required': source.get('required', True)}
            if affected not in task['affected_references']:
                task['affected_references'].append(affected)
            if ref not in task['source_locators']:
                task['source_locators'].append(ref)
            for check in source['checks']:
                status = check.get('status')
                if status and status not in task['check_statuses']:
                    task['check_statuses'].append(status)
            wanted = task['native_wanted']
            if member['instrument_id'] not in wanted['instrument_ids']:
                wanted['instrument_ids'].append(member['instrument_id'])
            if ref.get('url') and ref['url'] not in wanted['urls']:
                wanted['urls'].append(ref['url'])
    return list(tasks.values())


def readiness_scope(dossier, flight, prior, sources):
    """Describe checked prerequisites separately from qualified research leads.

    The existing task contract does not attest legal necessity. Neither a YES
    status nor a missing machine match makes every current-law lead mandatory.
    """
    unavailable = [s['evidence_id'] for s in sources if s['checks'] and
                   any(c['result'] != 'pass' for c in s['checks'])]
    return {
        'checked_contract': 'Original/inventory custody, exact held spans, frozen packet and runtime only; no predicted filing yield.',
        'required_evidence_ids': sorted(({dossier.get('original_source_id')} |
            {c.get('id') for c in dossier.get('clauses', [])}) - {None}),
        'unusable_declared_source_ids': unavailable,
        'unresolved_research': flight.get('mechanical_tasks', []),
        'dossier_reported_questions': dossier.get('missing', []),
        'recorded_source_blocks': [
            {'path': r['path'], 'pointer': r.get('pointer'), 'file_sha256': r['file_sha256'],
             'reason': r['record'].get('reason'), 'source_requests': r['record'].get('source_requests', []),
             'input_fingerprint': r['record'].get('input_fingerprint'),
             'qualification': 'Attributed prior source block; re-evaluate exact scope and relevant evidence before reassignment.'}
            for r in prior.get('unfinished_work', []) if r.get('record', {}).get('schema') == 'eo-source-blocked-work/v1'],
        'legal_requirement_coverage': 'unknown', 'scientific_approval': False}


def check(repo, folder, orders=None):
    """Recheck the whole seal; screen the explicitly requested members (all by default).

    Required original/inventory evidence blocks dispatch when mechanically unusable.
    Unselected actor/current-law/contrary leads stay visible and do not select a
    legal theory. Once selected in a claim, all sources face ordinary full checks.
    """
    started = time.monotonic()
    repo, folder = Path(repo).resolve(), Path(folder).resolve()
    packet, dossiers = batch.load_packet(folder, repo, check_sources=True)
    batch.validate_runtime(packet)
    if not 1 <= len(dossiers) <= 50:
        raise ValueError('dispatch requires 1-50 packet members')
    ids = list(dossiers) if orders is None else list(orders)
    if not ids or len(set(ids)) != len(ids) or set(ids) - set(dossiers):
        raise ValueError('dispatch order selection must be distinct packet members')
    checker = actual_checker()
    # Only custody APIs are needed; avoid Context's unrelated status, gate and
    # signing loads. allow_download=False is explicit, independent of env/global budgets.
    ctx = source_context(repo, checker)
    checked, texts, members = {}, {}, []
    for iid in ids:
        d = dossiers[iid]
        evidence = d.get('evidence', {})
        required = {d.get('original_source_id')} | {c.get('id') for c in d.get('clauses', [])}
        required.discard(None)
        blockers, source_results = [], []
        if not d.get('original_source_id') or not d.get('clauses'):
            blockers.append({'kind': 'original_or_inventory_absent', 'reason': 'Held original and nonempty inventory required for production; retain packet for source research.'})
        for task in packet['preflight'][iid]['mechanical_tasks']:
            if task.get('kind') == 'original_identity' and task.get('availability') == 'wrong_order':
                blockers.append({'kind': 'required_source_wrong_instrument', 'evidence_id': d.get('original_source_id'),
                                 'task_id': task['task_id'], 'observed_identity': task.get('observed_identity')})
        for eid in sorted(required - set(evidence)):
            blockers.append({'kind': 'required_evidence_absent', 'evidence_id': eid})
        for eid, item in sorted(evidence.items()):
            ref = item.get('source') or item.get('actor_source')
            mandatory = eid in required
            if not isinstance(ref, dict):
                if mandatory:
                    blockers.append({'kind': 'required_source_absent', 'evidence_id': eid})
                continue
            # Custody depends on byte hash/URL/archive id, not producer prose or grade.
            key = batch.canon({k: ref.get(k) for k in ('sha256', 'local_file_sha256', 'url', 'archival_id')})
            if key not in checked:
                rows = []
                checker.check_source(ref, 'source', ctx, rows, allow_download=False)
                checked[key] = rows
            results = checked[key]
            result = {'evidence_id': eid, 'required': mandatory,
                      'source': {k: ref[k] for k in ('url', 'sha256', 'local_file_sha256', 'archival_id',
                                                   'text_path', 'text_sha256', 'page_or_item') if k in ref},
                      'checks': results}
            source_results.append(result)
            if mandatory and (not results or any(r['result'] != 'pass' for r in results)):
                blockers.append({'kind': 'required_source_custody', 'evidence_id': eid,
                                 'checks': results, 'source': result['source']})
            if mandatory:
                rel, sha = ref.get('text_path'), ref.get('text_sha256')
                tkey = (rel, sha)
                if tkey not in texts:
                    try:
                        if not isinstance(rel, str) or not checker.S.sha_hex(sha):
                            raise ValueError('required text path/hash absent')
                        path = batch.safe(repo, rel)
                        if path.stat().st_size > 32_000_000:
                            raise ValueError('required text exceeds bounded screen')
                        raw = path.read_bytes()
                        if batch.digest(raw) != sha.lower():
                            raise ValueError('required text hash mismatch')
                        texts[tkey] = raw.decode('utf-8')
                    except (OSError, ValueError, UnicodeError) as exc:
                        texts[tkey] = exc
                body = texts[tkey]
                if isinstance(body, Exception):
                    blockers.append({'kind': 'required_text_unavailable', 'evidence_id': eid, 'reason': str(body)})
                else:
                    a, b = item.get('char_start', ref.get('char_start')), item.get('char_end', ref.get('char_end'))
                    quote = item.get('text', item.get('provision_text'))
                    if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(body) or body[a:b] != quote:
                        blockers.append({'kind': 'required_span_not_verified', 'evidence_id': eid})
        members.append({'instrument_id': iid, 'state': 'source_blocked' if blockers else 'dispatchable_for_research',
                        'blockers': blockers, 'sources': source_results,
                        'research_tasks': packet['preflight'][iid]['mechanical_tasks'],
                        'readiness_scope': readiness_scope(d, packet['preflight'][iid],
                            packet.get('prior_research', {}).get('orders', {}).get(iid, {}), source_results)})
    blocked = [m['instrument_id'] for m in members if m['blockers']]
    return {'schema': 'eo-claim-kit-dispatch-check/v1', 'packet_sha256': batch.file_sha(folder/'PACKET.json'),
            'code_pins': {p.name: batch.file_sha(p) for p in (Path(__file__), Path(checker.__file__), Path(checker.S.__file__))},
            'packet_fingerprint': packet['fingerprint'], 'packet_members': list(dossiers), 'checked_ids': ids,
            'state': 'source_blocked' if blocked else 'dispatchable_for_research', 'ok': not blocked,
            'dispatchable_ids': [m['instrument_id'] for m in members if not m['blockers']],
            'source_blocked_ids': blocked, 'members': members, 'unique_custody_checks': len(checked),
            'unique_required_text_checks': len(texts), 'wall_seconds': round(time.monotonic()-started, 6),
            'source_index_notes': ctx.index.notes, 'source_recovery_tasks': recovery_tasks(members),
            'legal_requirement_coverage': 'unknown',
            'network_requests': 0, 'model_tokens': None, 'scientific_approval': False,
            'notice': 'Re-run immediately before assignment. A receipt is not a lasting dispatch permit. Optional source gaps remain research tasks; all selected claim sources still require the actual checker and independent review.'}


def summary(result):
    """Keep routine agent output small; full source checks belong in the receipt."""
    out = {k: result[k] for k in ('state', 'ok', 'packet_sha256', 'dispatchable_ids', 'source_blocked_ids',
                                  'unique_custody_checks', 'wall_seconds', 'scientific_approval')}
    out['exceptions'] = [{'instrument_id': m['instrument_id'],
                          'blockers': [{'kind': b['kind'], 'evidence_id': b.get('evidence_id')} for b in m['blockers']],
                          'optional_source_gaps': [s['evidence_id'] for s in m['sources']
                                                   if not s['required'] and any(c['result'] != 'pass' for c in s['checks'])]}
                         for m in result['members'] if m['blockers'] or any(
                             not s['required'] and any(c['result'] != 'pass' for c in s['checks']) for s in m['sources'])]
    out['research_boundaries'] = [{'instrument_id': m['instrument_id'],
        'tasks': [{k: t.get(k) for k in ('task_id', 'kind', 'availability')}
                  for t in m['research_tasks']],
        'reported_question_count': len(m['readiness_scope']['dossier_reported_questions']),
        'prior_source_blocks': [{k: r.get(k) for k in ('path', 'pointer', 'reason')}
                               for r in m['readiness_scope']['recorded_source_blocks']]}
        for m in result['members'] if m['research_tasks'] or m['readiness_scope']['dossier_reported_questions'] or
        m['readiness_scope']['recorded_source_blocks']]
    out['source_recovery_tasks'] = [{k: t[k] for k in
        ('task_id', 'expected_sha256', 'check_statuses', 'native_wanted', 'next_action')}
        for t in result['source_recovery_tasks']]
    out['legal_requirement_coverage'] = result['legal_requirement_coverage']
    return out


def check_selected(repo, folder, claims):
    """Check newly selected claim sources before independent review/completion.

    This point-in-time diagnostic neither assembles nor approves a claim. It
    accepts exact proposed claims (including partial research), revalidates the
    packet/runtime, binds each reference to immutable dossier evidence, and uses
    the actual checker's OFFLINE custody rule. Call again after any claim/source
    change; there is deliberately no receipt-as-permission or cache bypass.
    """
    started = time.monotonic()
    repo, folder = Path(repo).resolve(), Path(folder).resolve()
    packet, dossiers = batch.load_packet(folder, repo, check_sources=True)
    batch.validate_runtime(packet)
    if not isinstance(claims, list) or not 1 <= len(claims) <= 50:
        raise ValueError('selected-source check requires 1-50 exact proposed claims')
    ids = [c.get('instrument_id') for c in claims if isinstance(c, dict)]
    if len(ids) != len(claims) or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids) or set(ids) - set(dossiers):
        raise ValueError('selected claims must name distinct packet members')
    checker = actual_checker()
    ctx = source_context(repo, checker)
    custody, texts, members = {}, {}, []
    for claim in claims:
        iid = claim['instrument_id']
        d = dossiers[iid]
        blockers, sources = [], []
        metadata = claim.get('claim_kit')
        if not isinstance(metadata, dict) or metadata.get('dossier_sha256') != d['fingerprint']:
            blockers.append({'kind': 'selected_claim_stale_dossier'})
            metadata = metadata if isinstance(metadata, dict) else {}
        evidence = assemble._records(d)
        overrides = metadata.get('inventory_overrides', [])
        if overrides:
            _, derived, errors = assemble.derive_inventory(d, overrides)
            evidence.update(derived)
            blockers.extend({'kind': 'selected_inventory_mismatch', 'reason': e} for e in errors)
        for task in packet['preflight'][iid]['mechanical_tasks']:
            if task.get('kind') == 'original_identity' and task.get('availability') == 'wrong_order':
                blockers.append({'kind': 'required_source_wrong_instrument', 'task_id': task['task_id']})
        # Match the checker's reference enumeration, including lists. Sources in
        # qualifications and newly selected source notes are not silently omitted.
        for path, key, value, _ in checker.walk(claim):
            refs = []
            if key in checker.SOURCE_KEYS:
                if not isinstance(value, dict):
                    blockers.append({'kind': 'selected_source_malformed', 'field': path})
                else:
                    refs.append((path, value))
            elif key in checker.SOURCE_LIST_KEYS:
                if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
                    blockers.append({'kind': 'selected_source_list_malformed', 'field': path})
                else:
                    refs.extend((f'{path}[{n}]', ref) for n, ref in enumerate(value))
            for field, ref in refs:
                ident = assemble._reference_id(ref)
                errors = []
                expected = assemble._reference(ident, evidence, errors)
                if errors or ref != expected:
                    blockers.append({'kind': 'selected_source_not_dossier_evidence', 'field': field,
                                     'evidence_id': ident})
                ckey = batch.canon({k: ref.get(k) for k in ('sha256', 'local_file_sha256', 'url', 'archival_id')})
                if ckey not in custody:
                    rows = []
                    checker.check_source(ref, 'source', ctx, rows, allow_download=False)
                    custody[ckey] = rows
                checks = custody[ckey]
                result = {'field': field, 'evidence_id': ident, 'required': True,
                          'source': {k: ref[k] for k in ('url', 'sha256', 'local_file_sha256', 'archival_id',
                                                       'text_path', 'text_sha256', 'page_or_item') if k in ref},
                          'checks': checks}
                sources.append(result)
                if not checks or any(c['result'] != 'pass' for c in checks):
                    blockers.append({'kind': 'selected_source_custody', 'field': field,
                                     'evidence_id': ident, 'checks': checks})
                rel, sha = ref.get('text_path'), ref.get('text_sha256')
                tkey = (rel, sha)
                if tkey not in texts:
                    try:
                        if not isinstance(rel, str) or not checker.S.sha_hex(sha):
                            raise ValueError('selected text path/hash absent')
                        text_path = batch.safe(repo, rel)
                        if text_path.stat().st_size > 32_000_000:
                            raise ValueError('selected text exceeds bounded screen')
                        raw = text_path.read_bytes()
                        if batch.digest(raw) != sha.lower():
                            raise ValueError('selected text hash mismatch')
                        texts[tkey] = raw.decode('utf-8')
                    except (OSError, ValueError, UnicodeError) as exc:
                        texts[tkey] = exc
                body = texts[tkey]
                if isinstance(body, Exception):
                    blockers.append({'kind': 'selected_text_unavailable', 'field': field, 'reason': str(body)})
                else:
                    a, b = ref.get('char_start'), ref.get('char_end')
                    if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(body) or body[a:b] != ref.get('quote'):
                        blockers.append({'kind': 'selected_span_not_verified', 'field': field, 'evidence_id': ident})
        if not sources:
            blockers.append({'kind': 'selected_sources_absent'})
        members.append({'instrument_id': iid, 'claim_sha256': batch.digest(batch.canon(claim).encode()),
                        'state': 'source_blocked' if blockers else 'selected_sources_mechanically_usable',
                        'blockers': blockers, 'sources': sources})
    return {'schema': 'eo-claim-kit-selected-sources/v1', 'ok': not any(m['blockers'] for m in members),
        'packet_sha256': batch.file_sha(folder / 'PACKET.json'), 'packet_fingerprint': packet['fingerprint'],
        'code_pins': {p.name: batch.file_sha(p) for p in (Path(__file__), Path(assemble.__file__),
                                                       Path(checker.__file__), Path(checker.S.__file__))},
        'members': members, 'source_recovery_tasks': recovery_tasks(members),
        'unique_custody_checks': len(custody), 'unique_text_checks': len(texts),
        'source_index_notes': ctx.index.notes, 'network_requests': 0,
        'wall_seconds': round(time.monotonic() - started, 6), 'model_tokens': None,
        'scientific_approval': False,
        'notice': 'Fresh selected-source check only. Exact claim hashes identify this observation; changed claims/sources require a new check. Legal applicability, source grades, independent review and ordinary checker/completion gates remain required.'}


def selected_summary(result):
    return {k: result[k] for k in ('schema', 'ok', 'packet_sha256', 'unique_custody_checks', 'wall_seconds',
                                   'scientific_approval')} | {
        'members': [{k: m[k] for k in ('instrument_id', 'claim_sha256', 'state')} | {
            'blockers': [{k: b[k] for k in ('kind', 'field', 'evidence_id', 'reason') if k in b} | {
                'custody_statuses': [c['status'] for c in b.get('checks', [])]}
                for b in m['blockers']]} for m in result['members']],
        'source_recovery_tasks': [{k: t[k] for k in ('task_id', 'expected_sha256', 'native_wanted', 'next_action')}
                                  for t in result['source_recovery_tasks']]}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline selected-source guard before review; no scientific approval.')
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('packet', type=Path)
    parser.add_argument('--claims', type=Path, required=True, help='Exact proposed claims JSONL, maximum 50 claims')
    parser.add_argument('--write', type=Path, help='New receipt path inside the packet; never overwrite')
    args = parser.parse_args(argv)
    try:
        if args.claims.stat().st_size > 32_000_000:
            raise ValueError('claims exceed bounded selected-source screen')
        claims = [json.loads(line) for line in args.claims.read_text(encoding='utf-8').splitlines() if line.strip()]
        if args.write is not None and (args.write.exists() or not args.write.resolve().is_relative_to(args.packet.resolve())):
            raise ValueError('new receipt path inside packet required')
        result = check_selected(args.repo, args.packet, claims)
        if args.write is not None:
            batch.dump(args.write, result)
        print(json.dumps(selected_summary(result), sort_keys=True))
        return 0 if result['ok'] else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc), 'scientific_approval': False}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
