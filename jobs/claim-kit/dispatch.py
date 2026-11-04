"""Offline, bounded source/freshness screen before spending model tokens.

This is a preparation diagnostic, never a source authentication or legal verdict.
It reuses frozen-packet validation and the actual checker's custody policy. No
downloads, source requests, reservations, decisions or scientific outputs change.
"""
import importlib.util
import time
from pathlib import Path
from types import SimpleNamespace

import batch

# These are existing unresolved preparation tasks, not legal classifications.
# New kinds need an explicit caller contract before they can block assignments.
ASSIGNMENT_TASK_KINDS = frozenset({'operative_current_law'})


def _assignment_prerequisites(preflight, ids, require_task_kinds=None):
    """Classify retained known tasks only; this pure slice never approves dispatch.

    The ordinary caller runs it after current packet/runtime validation. A replay
    on an older preflight demonstrates prerequisite routing, not source currency,
    custody, legal feasibility or permission to launch that historical packet.
    """
    kinds = [] if require_task_kinds is None else require_task_kinds
    if (not isinstance(kinds, (list, tuple)) or
            any(not isinstance(k, str) or k not in ASSIGNMENT_TASK_KINDS for k in kinds) or
            len(set(kinds)) != len(kinds)):
        raise ValueError('Distinct supported assignment task kinds required: ' + ', '.join(sorted(ASSIGNMENT_TASK_KINDS)))
    if (not isinstance(preflight, dict) or not isinstance(ids, (list, tuple)) or
            not 1 <= len(ids) <= 50 or any(not isinstance(i, str) for i in ids) or
            len(set(ids)) != len(ids) or set(ids) - set(preflight)):
        raise ValueError('Distinct existing assignment members required')
    member_blockers = {iid: [] for iid in ids}
    groups = {}
    if kinds:
        for iid in ids:
            member = preflight[iid]
            tasks = member.get('mechanical_tasks') if isinstance(member, dict) else None
            if not isinstance(tasks, list) or any(not isinstance(t, dict) for t in tasks):
                raise ValueError('Invalid assignment prerequisite tasks: ' + iid)
            for task in tasks:
                if task.get('kind') not in kinds:
                    continue
                key = task.get('shared_key')
                if (not isinstance(key, str) or not key or task.get('instrument_id') != iid or
                        not isinstance(task.get('reason'), str) or not task['reason']):
                    raise ValueError('Incomplete assignment prerequisite task: ' + iid)
                member_blockers[iid].append({'kind': 'assignment_prerequisite_unresolved', 'task': task})
                # Empty metadata is not evidence of one shared question/source.
                # Keep its original key but scope grouping to the member.
                groupable_key = key != '{}'
                marker = (task['kind'], key, None if groupable_key else iid)
                entry = groups.setdefault(marker, {'kind': task['kind'], 'shared_key': key,
                    'grouped_by_shared_key': groupable_key, 'affected_orders': [], 'member_tasks': []})
                if iid not in entry['affected_orders']:
                    entry['affected_orders'].append(iid)
                entry['member_tasks'].append(task)
    return member_blockers, {'required_task_kinds': list(kinds), 'unresolved': list(groups.values()),
        'notice': 'Only this explicitly declared assignment scope is blocked by these known tasks. Literal task-key grouping establishes no source identity, common legal consequence or reusable answer. Absence of a task is not complete source coverage, a supported current predicate or whole-case feasibility. Other legal research paths remain available; no scientific decision or source request is made.'}


def actual_checker():
    path = Path(__file__).resolve().parents[1] / 'claim-checker/checker.py'
    spec = importlib.util.spec_from_file_location('claim_kit_dispatch_checker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(repo, folder, orders=None, *, require_task_kinds=None):
    """Recheck the whole seal; screen the explicitly requested members (all by default).

    Required original/inventory evidence blocks dispatch when mechanically unusable.
    Unselected actor/current-law/contrary leads stay visible and do not select a
    legal theory. Once selected in a claim, all sources face ordinary full checks.
    An explicit require_task_kinds declaration refuses only an assignment that
    requires resolution of those existing unresolved preparation tasks. It does
    not make that requirement universal or decide which ending theory applies.
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
    prerequisite_blockers, prerequisites = _assignment_prerequisites(packet['preflight'], ids, require_task_kinds)
    checker = actual_checker()
    index = checker.S.build_index(repo, Path(checker.__file__).parent, exclude_jobs=('claim-checker',))
    # Only custody APIs are needed; avoid Context's unrelated status, gate and
    # signing loads. allow_download=False is explicit, independent of env/global budgets.
    ctx = SimpleNamespace(index=index, reader=checker.S.TextReader(packed=index.packed_texts),
                          gpo_matched=checker.load_gpo_matched(repo), archive_captures={}, cache_dir=None)
    checked, texts, members = {}, {}, []
    for iid in ids:
        d = dossiers[iid]
        evidence = d.get('evidence', {})
        required = {d.get('original_source_id')} | {c.get('id') for c in d.get('clauses', [])}
        required.discard(None)
        blockers, source_results = list(prerequisite_blockers[iid]), []
        tasks = packet['preflight'][iid]['mechanical_tasks']
        if not d.get('original_source_id') or not d.get('clauses'):
            blockers.append({'kind': 'original_or_inventory_absent', 'reason': 'Held original and nonempty inventory required for production; retain packet for source research.'})
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
                      'source': {k: ref[k] for k in ('url', 'sha256', 'local_file_sha256') if k in ref},
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
                        'research_tasks': tasks})
    blocked = [m['instrument_id'] for m in members if m['blockers']]
    report = {'schema': 'eo-claim-kit-dispatch-check/v1', 'packet_sha256': batch.file_sha(folder/'PACKET.json'),
            'code_pins': {p.name: batch.file_sha(p) for p in (Path(__file__), Path(checker.__file__), Path(checker.S.__file__))},
            'packet_fingerprint': packet['fingerprint'], 'packet_members': list(dossiers), 'checked_ids': ids,
            'state': 'source_blocked' if blocked else 'dispatchable_for_research', 'ok': not blocked,
            'dispatchable_ids': [m['instrument_id'] for m in members if not m['blockers']],
            'source_blocked_ids': blocked, 'members': members, 'unique_custody_checks': len(checked),
            'unique_required_text_checks': len(texts), 'wall_seconds': round(time.monotonic()-started, 6),
            'source_index_notes': index.notes,
            'network_requests': 0, 'model_tokens': None, 'scientific_approval': False,
            'notice': 'Re-run immediately before assignment. A receipt is not a lasting dispatch permit. Optional source gaps remain research tasks; all selected claim sources still require the actual checker and independent review.'}
    if prerequisites['required_task_kinds']:
        report['assignment_prerequisites'] = prerequisites
    return report


def summary(result):
    """Keep routine agent output small; full source checks belong in the receipt."""
    out = {k: result[k] for k in ('state', 'ok', 'packet_sha256', 'dispatchable_ids', 'source_blocked_ids',
                                  'unique_custody_checks', 'wall_seconds', 'scientific_approval')}
    out['exceptions'] = [{'instrument_id': m['instrument_id'],
                          'blockers': [{'kind': b['kind'], 'evidence_id': b.get('evidence_id'),
                                        **({'task_kind': b['task']['kind'], 'shared_key': b['task']['shared_key']}
                                           if b['kind'] == 'assignment_prerequisite_unresolved' else {})} for b in m['blockers']],
                          'optional_source_gaps': [s['evidence_id'] for s in m['sources']
                                                   if not s['required'] and any(c['result'] != 'pass' for c in s['checks'])]}
                         for m in result['members'] if m['blockers'] or any(
                             not s['required'] and any(c['result'] != 'pass' for c in s['checks']) for s in m['sources'])]
    if 'assignment_prerequisites' in result:
        p = result['assignment_prerequisites']
        out['assignment_prerequisites'] = {'required_task_kinds': p['required_task_kinds'],
            'unresolved_task_groups': len(p['unresolved']),
            'affected_orders': [m['instrument_id'] for m in result['members'] if any(
                b['kind'] == 'assignment_prerequisite_unresolved' for b in m['blockers'])],
            'notice': p['notice']}
    return out
