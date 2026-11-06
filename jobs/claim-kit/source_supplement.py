"""Add declared held excerpts to a new native packet, without legal inference.

This is preparation only. A producer explicitly supplies any legal mechanism
and date; every member still needs ordinary source checks and independent review.

Undecided members (no provisional status) keep their status-overlay route: the
excerpt is added inside a new sealed copy of the parent packet's frozen overlay
evidence, so the status decision, its independent review and owner adoption run
on exactly the dossier the producer reads. The status gates are unchanged: a
supplement excerpt is citable held evidence, but a NO still needs an ACT:, TERM:
or ACTOR_TEXT: basis and a YES a CURRENT: basis.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import time

import assemble as A
import batch as B
import fragment_cache
import working_text as W

SCHEMA = 'eo-source-excerpt-declarations/v1'
EVIDENCE_SUPPLEMENT_SCHEMA = 'eo-status-overlay-evidence-supplement/v1'
SOURCE_KEYS = {'url', 'sha256', 'text_path', 'text_sha256', 'page_or_item', 'local_path'}
ENTRY_KEYS = {'alias', 'instrument_ids', 'actor_id', 'reason', 'source', 'char_start', 'char_end'}


def pin(repo, path):
    path = Path(path).resolve()
    if not path.is_relative_to(repo):
        raise ValueError('source supplement path outside repository')
    return {'path': path.relative_to(repo).as_posix(), 'sha256': B.file_sha(path)}


def checked(repo, record):
    if not isinstance(record, dict) or set(record) != {'path', 'sha256'}:
        raise ValueError('invalid source supplement pin')
    path = B.safe(repo, record['path'])
    if B.file_sha(path) != record['sha256']:
        raise ValueError('changed source supplement pin: ' + record['path'])
    return path


def registered(repo, source, index=None):
    """The producer-registered working-text form of a held excerpt, or None.

    An excerpt from a text a producer registered as a provisional working text (an American Presidency Project
    transcription, say) is cited the way ordinary dossiers cite it: the registered source hash, exact grade and
    acceptable_as_original false, so the working-text gate requires its disclosure. A declaring agent cannot
    choose the grade; it comes only from the registry, and an ambiguous registration is left ungraded."""
    rel = B.safe(repo, source['text_path']).relative_to(Path(repo).resolve()).as_posix()
    index = index or fragment_cache.shared(repo)
    # A separately registered official representation may share its extracted
    # text with a provisional mirror. Preserve the explicitly selected official
    # URL/raw hash; a text-path match must not silently replace its provenance.
    if index.exact_official(source):
        return None
    found = {(r['instrument_id'], r['grade'], r['sha256'], r['url']) for rows in index.by_sha.values() for r in rows
             if r['text_path'] == rel and r.get('text_sha256') == source['text_sha256'] and r['grade'] in W.GRADES}
    if len(found) != 1:
        return None
    (iid, grade, sha, url), = found
    form = {k: v for k, v in source.items() if k != 'local_path'}
    form.update(sha256=sha, grade=grade, acceptable_as_original=False, instrument_id=iid, text_path=rel)
    if url:
        form['url'] = url
    return form


def derive(repo, dossiers, declaration, provenance, undecided=None):
    """``undecided``: {instrument_id: frozen parent overlay evidence} for members without a status."""
    if not isinstance(declaration, dict) or set(declaration) != {'schema', 'sources'} or declaration['schema'] != SCHEMA:
        raise ValueError('invalid source declaration schema')
    entries = declaration['sources']
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError('bounded nonempty source declarations required')
    result = deepcopy(dossiers)
    for iid, d in result.items():
        if d.get('fingerprint') != A.canonical_sha(d) or d.get('source_supplement'):
            raise ValueError('stale or already supplemented parent dossier: ' + iid)
        if d.get('whole_order_status') is None:
            frozen = (undecided or {}).get(iid)
            if frozen is None or frozen.get('base_dossier') != dossiers[iid]:
                raise ValueError('undecided dossiers require their existing status-overlay route: '
                                 'frozen parent evidence missing or mismatched for ' + iid)
    aliases = set()
    index = fragment_cache.shared(repo)
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise ValueError('invalid source declaration fields')
        alias = entry['alias']
        if not isinstance(alias, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,95}', alias) or alias in aliases:
            raise ValueError('invalid or duplicate source alias')
        aliases.add(alias)
        ids = entry['instrument_ids']
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids) or not set(ids) <= set(result):
            raise ValueError('source targets must be distinct parent members')
        if not isinstance(entry['actor_id'], str) or not entry['actor_id'].strip() or not isinstance(entry['reason'], str) or len(entry['reason'].strip()) < 10:
            raise ValueError('explicit actor label and preparation reason required')
        source = entry['source']
        if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
            raise ValueError('source fields do not declare legal identity or grade')
        if not isinstance(source['url'], str) or not source['url'].startswith('https://') or not source['page_or_item']:
            raise ValueError('HTTPS source locator required')
        for key, pathkey in [('sha256', 'local_path'), ('text_sha256', 'text_path')]:
            if not isinstance(source[key], str) or not re.fullmatch(r'[0-9a-f]{64}', source[key]) or B.file_sha(B.safe(repo, source[pathkey])) != source[key]:
                raise ValueError('source supplement hash mismatch: ' + key)
        text_path = B.safe(repo, source['text_path'])
        if text_path.stat().st_size > 32_000_000:
            raise ValueError('source text exceeds bounded preparation limit')
        text = text_path.read_bytes().decode('utf-8')
        start, end = entry['char_start'], entry['char_end']
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
            raise ValueError('invalid source excerpt span')
        held = registered(repo, source, index)
        eid = 'SUPPLEMENT:' + alias
        for iid in ids:
            if eid in result[iid]['evidence']:
                raise ValueError('source evidence ID collision')
            result[iid]['evidence'][eid] = {
                'id': eid, 'source': deepcopy(held or source), 'text': text[start:end],
                'char_start': start, 'char_end': end, 'actor_id': entry['actor_id'],
                'role': 'unreviewed_source_excerpt', 'purpose': entry['reason'],
                'notice': 'Exact held excerpt only. Actor identity, scope, date, legal meaning and application require research and independent review.'}
    for iid, d in result.items():
        d['source_supplement'] = {
            'schema': 'eo-source-excerpt-preparation/v1', **deepcopy(provenance),
            'parent_dossier_sha256': dossiers[iid]['fingerprint'],
            'added_evidence_ids': sorted(set(d['evidence']) - set(dossiers[iid]['evidence'])),
            'scope': 'Preparation only; all inherited dossier fields unchanged; no legal or source-grade approval.'}
        d['fingerprint'] = A.canonical_sha(d)
    return result


def parent_evidence(repo, packet, dossiers):
    """The parent packet's frozen overlay evidence for its undecided members, checked against the packet pins."""
    found = {}
    for iid, entry in (packet.get('undecided_evidence') or {}).items():
        path = B.safe(repo, entry['path'])
        if B.file_sha(path) != entry['file_sha256']:
            raise ValueError('changed frozen undecided evidence: ' + iid)
        evidence = json.loads(path.read_bytes())
        if evidence.get('fingerprint') != entry['evidence_sha256'] or evidence.get('base_dossier') != dossiers.get(iid):
            raise ValueError('parent undecided evidence does not match its dossier: ' + iid)
        found[iid] = evidence
    return found


def supplemented_evidence(repo, parent, dossier):
    """A new sealed overlay evidence whose base dossier is the supplemented dossier.

    Everything else (authority snapshot, status history, compiled generation) is the parent's, unchanged; the
    supplement's held files are added to the source pins so ordinary overlay validation rechecks them."""
    import status_overlay as O
    O._sealed(parent, O.EVIDENCE_SCHEMA)
    base = parent['base_dossier']
    meta = dossier.get('source_supplement')
    if (not isinstance(meta, dict) or meta.get('parent_dossier_sha256') != base.get('fingerprint')
            or dossier.get('instrument_id') != parent['instrument_id'] or dossier.get('whole_order_status') is not None
            or base.get('whole_order_status') is not None or parent.get('source_supplement')):
        raise ValueError('supplemented undecided dossier does not descend from its frozen evidence')
    added = {}
    O._source_pins(repo, {'evidence': {k: dossier['evidence'][k] for k in meta['added_evidence_ids']}}, added)
    pins = dict(parent['source_fingerprints'])
    for rel, digest in added.items():
        if pins.setdefault(rel, digest) != digest:
            raise ValueError('supplement source conflicts with frozen source pin: ' + rel)
    evidence = {k: deepcopy(v) for k, v in parent.items() if k != 'fingerprint'}
    evidence['base_dossier'] = deepcopy(dossier)
    evidence['source_fingerprints'] = dict(sorted(pins.items()))
    evidence['source_supplement'] = {
        'schema': EVIDENCE_SUPPLEMENT_SCHEMA, 'parent_evidence_sha256': parent['fingerprint'],
        'added_evidence_ids': list(meta['added_evidence_ids']),
        'notice': 'Held excerpts added for preparation only; status history, authority and compiled records are '
                  'the parent evidence unchanged. No status, grade or review is implied.'}
    evidence['fingerprint'] = A.canonical_sha(evidence)
    return evidence


def prepare(repo, parent, declaration_file, agent, dest):
    started = time.monotonic()
    repo, parent, declaration_file, dest = [Path(p).resolve() for p in (repo, parent, declaration_file, dest)]
    if dest.exists() or not dest.is_relative_to(repo / 'research'):
        raise ValueError('fresh research destination required')
    packet, dossiers = B.load_packet(parent, repo)
    provenance = {'parent_packet': pin(repo, parent / 'PACKET.json'),
                  'declarations': pin(repo, declaration_file),
                  'preparation_code': pin(repo, Path(__file__))}
    frozen = parent_evidence(repo, packet, dossiers)
    derived = derive(repo, dossiers, json.loads(declaration_file.read_bytes()), provenance, frozen)
    evidences = {iid: supplemented_evidence(repo, frozen[iid], d) for iid, d in derived.items()
                 if d.get('whole_order_status') is None}
    folder = dest.with_name(dest.name + '-source-dossiers')
    if folder.exists():
        raise ValueError('derived dossier destination exists')
    paths = {iid: folder / (B.filename(iid) + '.json') for iid in derived}
    for iid, d in derived.items():
        B.dump(paths[iid], d)
    # A supplement of an owner-reviewable replacement packet stays a replacement packet: B.prepare
    # would otherwise refuse every already-claimed order. The parent's routing decides; nothing is inferred.
    replacement = any(r.get('route') == 'owner_reviewable_replacement_proposal'
                      for r in packet.get('ownership', {}).values() if isinstance(r, dict))
    stats = B.prepare(repo, parent, dest, list(derived), agent, dossier_paths=paths,
                      replacement_proposal=replacement, frozen_evidence=evidences or None)
    receipt = {'schema': 'eo-source-excerpt-prepare-receipt/v1', **provenance,
               'instrument_ids': list(derived), 'native_prepare': stats,
               'undecided_overlay_members': sorted(evidences),
               'wall_seconds': time.monotonic() - started,
               'producer_approval': False, 'independent_review': False}
    B.dump(dest / 'SOURCE_SUPPLEMENT.json', receipt)
    return receipt


def verify(repo, folder):
    repo, folder = Path(repo).resolve(), Path(folder).resolve()
    packet, actual = B.load_packet(folder, repo, check_sources=False)
    metas = [d.get('source_supplement') for d in actual.values()]
    if not metas or any(not isinstance(m, dict) for m in metas):
        raise ValueError('supplement lineage missing')
    provenance = {k: metas[0][k] for k in ('parent_packet', 'declarations', 'preparation_code')}
    if any(any(m[k] != v for k, v in provenance.items()) for m in metas):
        raise ValueError('mixed source supplement lineage')
    paths = {k: checked(repo, v) for k, v in provenance.items()}
    if paths['preparation_code'] != Path(__file__).resolve():
        raise ValueError('wrong source preparation code')
    parent, dossiers = B.load_packet(paths['parent_packet'].parent, repo, check_sources=False)
    for rel, sha in parent['held_text_file_pins'].items():
        if B.file_sha(B.safe(repo, rel)) != sha:
            raise ValueError('changed parent held source: ' + rel)
    frozen = parent_evidence(repo, parent, dossiers)
    expected = derive(repo, dossiers, json.loads(paths['declarations'].read_bytes()), provenance, frozen)
    if actual != expected:
        raise ValueError('changed supplemented dossier or inherited field')
    undecided = {iid for iid, d in expected.items() if d.get('whole_order_status') is None}
    if set(packet.get('undecided_evidence') or {}) != undecided:
        raise ValueError('undecided supplement members must keep frozen overlay evidence')
    for iid in sorted(undecided):
        entry = packet['undecided_evidence'][iid]
        path = B.safe(repo, entry['path'])
        if B.file_sha(path) != entry['file_sha256']:
            raise ValueError('changed frozen undecided evidence: ' + iid)
        if json.loads(path.read_bytes()) != supplemented_evidence(repo, frozen[iid], expected[iid]):
            raise ValueError('supplemented overlay evidence does not match its parent: ' + iid)
    return {'orders': len(actual), 'exact_lineage_and_source_bytes': True, 'legal_approval': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--parent', required=True); p.add_argument('--sources', required=True)
    p.add_argument('--agent', required=True); p.add_argument('--write', required=True)
    p = commands.add_parser('verify'); p.add_argument('packet')
    args = parser.parse_args()
    result = (prepare(args.repo, args.parent, args.sources, args.agent, args.write)
              if args.command == 'prepare' else verify(args.repo, args.packet))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
