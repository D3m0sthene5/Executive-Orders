"""Finish an explicitly reviewed batch. Selection and filing are clerical only.

The manifest names exact producer lines and independently recorded judgments.
No verdict, control catch, legal correction, or latest version is inferred here.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

import batch
from assemble import _gate, check_claim

SCHEMA = 'eo-claim-kit-completion/v1'
SHA = re.compile(r'[0-9a-f]{64}')
CLAIMS_PATTERN = 'research/readiness/claims/*.jsonl'
LOCK_REL = 'research/readiness/.claim-publication.lock'
LOCK_TIMEOUT_ENV = 'CLAIM_KIT_PUBLICATION_LOCK_TIMEOUT'
LOCK_TIMEOUT_DEFAULT = 900.0
LOCK_POLL_SECONDS = 0.5


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


class Inputs:
    """Pin and copy every consumed review/producer receipt, without reserializing."""
    def __init__(self, repo):
        self.repo = repo
        self.files = {}
        self.pins = {}
        self.absent = set()
        self.file_sets = {}
        self.additive = set()       # patterns where disjoint NEW files are tolerated
        self.concurrent = []        # permitted additions seen by the last unchanged()
        self.packets = {}           # (folder, PACKET.json sha256) -> verified snapshot

    def pin(self, rel, sha=None):
        path = batch.safe(self.repo, rel)
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        require(sha is None or actual == sha, 'changed dependency: ' + rel)
        require(self.pins.setdefault(rel, actual) == actual, 'dependency changed during completion: ' + rel)

    def optional(self, rel):
        if batch.safe(self.repo, rel).exists():
            self.pin(rel)
        else:
            self.absent.add(rel)

    def claim_files(self):
        self.pattern(CLAIMS_PATTERN)
        self.additive.add(CLAIMS_PATTERN)

    def packet(self, ref):
        """Pin PACKET.json and verify it once per (folder, sha256) per invocation.

        Later members reuse the verified (packet, dossiers). Callers must treat the
        returned objects as read-only; selected_claim deep-copies a member dossier.
        """
        require(isinstance(ref, dict), 'packet reference must be an object')
        require(Path(ref['path']).name == 'PACKET.json', 'packet reference must pin PACKET.json')
        self.pin(ref['path'], ref['sha256'])
        folder = batch.safe(self.repo, ref['path']).parent
        key = (folder, ref['sha256'])  # pin() just proved the file has exactly this digest
        entry = self.packets.get(key)
        if entry is None:
            started = time.monotonic()
            packet, dossiers = batch.load_packet(folder, self.repo)
            entry = self.packets[key] = {'folder': folder, 'packet': packet, 'dossiers': dossiers,
                                         'fingerprint': packet.get('fingerprint'), 'loads': 1,
                                         'load_seconds': time.monotonic() - started, 'rechecks': 0,
                                         'recheck_seconds': 0.0}
        return entry['packet'], entry['dossiers']

    def recheck_packets(self):
        """Reverify every cached packet's dynamic dependencies right before publication."""
        for entry in self.packets.values():
            rel = entry['folder'].relative_to(self.repo).as_posix()
            started = time.monotonic()
            try:
                packet, _ = batch.load_packet(entry['folder'], self.repo)
                same = packet.get('fingerprint') == entry['fingerprint']
            except Exception:
                same = False
            entry['loads'] += 1
            entry['rechecks'] += 1
            entry['recheck_seconds'] += time.monotonic() - started
            require(same, 'packet dependencies changed during completion: ' + rel)

    def pattern(self, pattern):
        paths = sorted(p.relative_to(self.repo).as_posix() for p in self.repo.glob(pattern) if p.is_file())
        self.file_sets[pattern] = paths
        for rel in paths:
            self.pin(rel)

    def file(self, ref):
        require(isinstance(ref, dict), 'file reference must be an object')
        path = batch.safe(self.repo, ref['path'])
        require(path.is_file(), 'missing input: ' + ref['path'])
        raw = path.read_bytes()
        require(batch.digest(raw) == ref['sha256'], 'changed input: ' + ref['path'])
        rel = path.relative_to(self.repo).as_posix()
        previous = self.files.setdefault(rel, raw)
        require(previous == raw, 'input changed during completion: ' + rel)
        return raw

    def object(self, ref):
        raw = self.file(ref)
        require(not ('line' in ref and 'pointer' in ref), 'use line or pointer, not both')
        if 'line' in ref:
            line = ref['line']
            require(type(line) is int and line > 0, 'line must be a positive integer')
            lines = raw.splitlines(keepends=True)
            require(line <= len(lines), 'missing exact line')
            value = read_json(lines[line - 1])
        else:
            value = read_json(raw)
            pointer = ref.get('pointer', '')
            require(isinstance(pointer, str) and (not pointer or pointer.startswith('/')), 'invalid JSON pointer')
            for token in pointer.split('/')[1:] if pointer else []:
                token = token.replace('~1', '/').replace('~0', '~')
                value = value[int(token)] if isinstance(value, list) else value[token]
        require(isinstance(value, dict), 'referenced record must be an object')
        return value

    def unchanged(self, selected_ids=None):
        """Strictly recheck every pin; the claims pattern alone tolerates disjoint new files."""
        self.concurrent = []
        for rel, raw in self.files.items():
            require(batch.safe(self.repo, rel).read_bytes() == raw, 'input changed during completion: ' + rel)
        for rel, sha in self.pins.items():
            path = batch.safe(self.repo, rel)
            require(path.is_file(), 'dependency removed during completion: ' + rel)
            with path.open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == sha, 'dependency changed during completion: ' + rel)
        for rel in self.absent:
            require(not batch.safe(self.repo, rel).exists(), 'dependency appeared during completion: ' + rel)
        for pattern, paths in self.file_sets.items():
            current = sorted(p.relative_to(self.repo).as_posix() for p in self.repo.glob(pattern) if p.is_file())
            if current == paths:
                continue
            if pattern in self.additive and selected_ids is not None and set(paths) <= set(current):
                self.disjoint_additions(set(current) - set(paths), set(selected_ids))
                continue
            raise ValueError('input file set changed during completion: ' + pattern)

    def disjoint_additions(self, added, selected_ids):
        for rel in sorted(added):
            raw = batch.safe(self.repo, rel).read_bytes()
            ids = []
            for line in raw.splitlines():
                if not line.strip():
                    continue
                row = read_json(line)
                require(isinstance(row, dict), 'concurrent claims file has a non-object line: ' + rel)
                if row.get('instrument_id') is not None:
                    ids.append(row['instrument_id'])
            for iid in ids:
                require(iid not in selected_ids, 'concurrent publication for selected instrument %s: %s' % (iid, rel))
            self.concurrent.append({'path': rel, 'sha256': batch.digest(raw), 'instrument_ids': sorted(set(map(str, ids)))})

    def save(self, dest):
        for rel, raw in self.files.items():
            path = dest / 'receipts' / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        batch.dump(dest / 'INPUTS.json', {'preserved_receipts': {rel: batch.digest(raw) for rel, raw in sorted(self.files.items())},
                                        'dependency_sha256': dict(sorted(self.pins.items())),
                                        'absent_dependencies': sorted(self.absent), 'file_sets': self.file_sets,
                                        'concurrent_disjoint_claim_files': self.concurrent,
                                        'tracker_replay_basis': ('after-replay union: start snapshot of canonical claims plus selected lines; '
                                                                 'before-replay: canonical claims present when the tracker ran. Selected '
                                                                 'rows depend only on their own claims.' + (
                                                                 ' Concurrent disjoint files are excluded from the union.'
                                                                 if self.concurrent else ''))})
        batch.dump(dest / 'PACKETS.json', [
            {'packet': e['folder'].relative_to(self.repo).as_posix() + '/PACKET.json', 'fingerprint': e['fingerprint'],
             'packet_sha256': key[1], 'loads': e['loads'], 'load_seconds': e['load_seconds'],
             'rechecks': e['rechecks'], 'recheck_seconds': e['recheck_seconds']}
            for key, e in sorted(self.packets.items(), key=lambda item: str(item[0][0]))])


def review_record(inputs, ref, member, manifest, after_reveal=False):
    review = inputs.object(ref)
    require(review.get('instrument_id') == member['instrument_id'] and
            review.get('claim_sha256') == member['claim_sha256'], 'review is not for selected exact claim')
    require(review.get('review_kind') == 'independent_ai_source_review' and
            review.get('independent') is True and review.get('reviewer') and
            review['reviewer'] != manifest['agent'], 'independent source review required')
    family = review.get('model_family')
    require(isinstance(family, str) and bool(family.strip()), 'reviewer model_family required')
    requirement = manifest['independence_requirement']
    require(requirement in ('same_family_separate_context', 'different_family'), 'unknown independence requirement')
    if requirement == 'different_family':
        require(family.strip().casefold() != manifest['producer_model_family'].strip().casefold(), 'different model family required')
    require(review.get('separate_context') is True, 'separate reviewer context required')
    require(review.get('scope') == member['publication_kind'], 'review scope differs from publication kind')
    wanted = 'upheld_after_reveal' if after_reveal else 'upheld'
    require(review.get('verdict') == wanted, 'exact claim not ' + wanted)
    return review


def controls(inputs, manifest):
    """Validate a person's recorded semantic adjudication; never parse reasons."""
    result = []
    keys = set()
    for control in manifest['controls']:
        iid, sha = control['instrument_id'], control['planted_claim_sha256']
        require(SHA.fullmatch(sha) is not None and (iid, sha) not in keys, 'duplicate/invalid planted version')
        keys.add((iid, sha))
        require('line' not in control['seed'] and 'pointer' not in control['seed'], 'seed receipt must be a standalone safe JSON object')
        seed = inputs.object(control['seed'])
        require(set(seed) == {'schema', 'instrument_id', 'planted_claim_sha256', 'genuine_claim_sha256', 'seeded_by'} and
                seed.get('schema') == 'eo-claim-kit-control-seed/v1' and seed.get('instrument_id') == iid and
                seed.get('planted_claim_sha256') == sha and SHA.fullmatch(seed.get('genuine_claim_sha256', '')) and
                seed['genuine_claim_sha256'] != sha and seed.get('seeded_by'), 'safe exact control seed receipt required')
        review = inputs.object(control['review'])
        require(review.get('instrument_id') == iid and review.get('claim_sha256') == sha, 'control review version mismatch')
        require(review.get('review_kind') == 'independent_ai_source_review' and review.get('independent') is True and
                review.get('separate_context') is True and review.get('reviewer') and review['reviewer'] != manifest['agent'] and
                review['reviewer'] != seed['seeded_by'] and isinstance(review.get('model_family'), str) and
                review['model_family'].strip(), 'independent control source review required')
        if manifest['independence_requirement'] == 'different_family':
            require(review['model_family'].strip().casefold() != manifest['producer_model_family'].strip().casefold(), 'different control reviewer family required')
        adjudication = inputs.object(control['adjudication'])
        require(adjudication.get('instrument_id') == iid and adjudication.get('planted_claim_sha256') == sha,
                'control adjudication version mismatch')
        require(adjudication.get('review') == control['review'], 'adjudication must pin the scored review')
        require(adjudication.get('adjudicator') and adjudication.get('rationale') and
                adjudication.get('scoring') in ('strict', 'lenient') and type(adjudication.get('caught')) is bool,
                'recorded semantic control adjudication required')
        require(not adjudication['caught'] or review.get('verdict') == 'rejected', 'caught control must have a rejected review')
        # A caught=false receipt remains an observed failure, never overwritten.
        result.append({'instrument_id': iid, 'planted_claim_sha256': sha,
                       'caught': adjudication['caught'], 'scoring': adjudication['scoring']})
    return result


def claim_sha(claim):
    # Same canonical JSON as Stage 19, retaining every claim field.
    return batch.digest(batch.canon(claim).encode('utf-8'))


def held_versions(inputs):
    path = inputs.repo / 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
    if not path.exists():
        return set()
    raw = path.read_bytes()
    inputs.file({'path': path.relative_to(inputs.repo).as_posix(), 'sha256': batch.digest(raw)})
    result = set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        hold = read_json(line)
        require(hold.get('schema') == 'eo-source-audit-hold/v1' and hold.get('state') == 'unresolved' and
                hold.get('reason') and SHA.fullmatch(hold.get('claim_sha256', '')), 'invalid source audit hold')
        inputs.file({'path': hold['review_path'], 'sha256': hold['review_sha256']})
        result.add((hold['instrument_id'], hold['claim_sha256']))
    return result


def working_overlay(inputs, member, manifest, claim):
    """Validate the existing isolated overlay route, never adopt its status."""
    import status_overlay as overlay
    require(manifest['publication']['mode'] == 'replacement_proposal',
            'unadopted status overlay requires isolated replacement_proposal publication')
    refs = member['overlay_bundle']
    names = {'evidence': 'EVIDENCE.json', 'decision': 'STATUS_DECISION.json',
             'review': 'STATUS_REVIEW.json', 'proposal': 'PROMOTION_PROPOSAL.json'}
    require(isinstance(refs, dict) and set(refs) == set(names), 'four exact overlay bundle references required')
    paths = []
    values = {}
    for key, name in names.items():
        ref = refs[key]
        require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'} and
                Path(ref['path']).name == name, 'whole-file exact overlay reference required: ' + key)
        paths.append(batch.safe(inputs.repo, ref['path']).parent)
        values[key] = inputs.object(ref)
    require(len(set(paths)) == 1, 'overlay inputs must share one exact isolated bundle')
    overlay._destination(inputs.repo, paths[0])
    evidence = values['evidence']
    # The complete current source/history/authority/compiler checks and exact
    # reviewed working-status label are the existing overlay contract.
    errors = overlay.check_working_claim(inputs.repo, claim, values['proposal'],
        values['decision'], values['review'], evidence)
    for rel, sha in {**evidence['source_fingerprints'], **evidence['authority']['files']}.items():
        inputs.pin(rel, sha)
    for name, sha in evidence['compiled']['code_sha256'].items():
        inputs.pin('jobs/claim-kit/' + name, sha)
    inputs.pin(evidence['compiled']['output'] + '/SUMMARY.json')
    # A continuous producer may retain its earlier undecided packet as exact
    # provenance. It is not the experimental dossier and its old context/code
    # stamp cannot approve this claim. The overlay independently revalidates all
    # dependencies above; a legacy individual overlay needs no ordinary packet.
    if 'packet' in member:
        require(Path(member['packet']['path']).name == 'PACKET.json', 'packet reference must pin PACKET.json')
        packet = inputs.object(member['packet'])
        fingerprint = packet.get('fingerprint')
        require(packet.get('schema') == batch.SCHEMA and
                batch.digest(batch.canon({k:v for k,v in packet.items() if k != 'fingerprint'}).encode()) == fingerprint,
                'changed archived preparation packet')
        require(packet.get('agent') == manifest['agent'], 'packet belongs to another producer')
        require(batch.decode(packet).get(member['instrument_id']) == evidence['base_dossier'],
                'archived packet does not match frozen overlay base dossier')
    return errors


def selected_claim(inputs, member, manifest, planted, held):
    iid, sha = member['instrument_id'], member['claim_sha256']
    require(SHA.fullmatch(sha) is not None, 'explicit canonical claim_sha256 required')
    require((iid, sha) not in planted, 'planted version cannot be filed')
    require((iid, sha) not in held, 'exact version has unresolved source audit hold')
    ref = member['claim']
    require('line' in ref and 'pointer' not in ref, 'producer claim requires an exact JSONL line')
    claim = inputs.object(ref)
    require(claim.get('instrument_id') == iid and claim_sha(claim) == sha, 'selected producer version mismatch')
    def pin_texts(value):
        if isinstance(value, dict):
            if value.get('text_path') and value.get('text_sha256'):
                inputs.pin(value['text_path'], value['text_sha256'])
            for child in value.values():
                pin_texts(child)
        elif isinstance(value, list):
            for child in value:
                pin_texts(child)
    pin_texts(claim)
    raw_line = inputs.file(ref).splitlines(keepends=True)[ref['line'] - 1]
    require(raw_line.endswith(b'\n'), 'producer line must retain a newline terminator')
    require(member['publication_kind'] in ('whole_case', 'partial_research'), 'explicit publication_kind required')
    after_reveal = any(i == iid for i, _ in planted)
    review = review_record(inputs, member['after_reveal_review'] if after_reveal else member['review'],
                           member, manifest, after_reveal)
    dossier = None
    is_overlay = ('overlay_bundle' in member or
                  isinstance(claim.get('claim_kit'), dict) and 'status_overlay' in claim['claim_kit'])
    if 'claim_kit' in claim:
        require(claim['claim_kit'].get('agent') == manifest['agent'], 'claim belongs to another producer')
    if is_overlay:
        strict_errors = working_overlay(inputs, member, manifest, claim)
    elif 'claim_kit' in claim:
        packet_ref = member['packet']
        packet, dossiers = inputs.packet(packet_ref)
        require(packet['agent'] == manifest['agent'], 'packet belongs to another producer')
        require(packet.get('codec_code_sha256') == batch.file_sha(Path(batch.__file__)) and
                packet.get('policy_code_sha256') == batch.policy_code_pins() and
                packet.get('assembler_code_sha256') == batch.file_sha(Path(batch.__file__).with_name('assemble.py')) and
                packet.get('preflight_code_sha256') == batch.file_sha(Path(batch.__file__).with_name('evidence_preflight.py')) and
                packet.get('preflight_dependency_sha256') == {'excavate.py': batch.file_sha(Path(batch.__file__).with_name('excavate.py'))},
                'packet code changed; prepare and review a new version')
        dossier = deepcopy(dossiers[iid])  # the cached packet snapshot is shared and immutable
    gate_errors = _gate(inputs.repo).validate_claim(claim, expected_status=claim.get('whole_order_status'))
    if not is_overlay:
        strict_errors = check_claim(claim, inputs.repo, dossier)
    require(not [e for e in strict_errors if e not in gate_errors], 'strict claim checks failed: ' + str(strict_errors))
    if member['publication_kind'] == 'whole_case':
        require(not gate_errors, 'whole-case gate failed: ' + str(gate_errors))
    else:
        require(isinstance(review.get('expected_gate_errors'), list) and bool(review['expected_gate_errors']),
                'partial review requires explicit nonempty expected_gate_errors; complete claims need whole_case review')
        require(sorted(review['expected_gate_errors']) == sorted(gate_errors),
                'partial-research completeness gaps differ from exact review')
    detail = {'gate_errors': gate_errors, 'after_reveal': after_reveal, 'source_review_upheld': True,
              'publication_kind': member['publication_kind']}
    if is_overlay:
        detail.update(experimental_status_overlay=True, owner_adoption_required=True,
                      authoritative_status=None, canonical_filing_allowed=False)
    return claim, raw_line, detail


def run_checker(repo, claims, dest):
    dest.mkdir()
    env = dict(os.environ, REPO_ROOT=str(repo), OUTPUT_DIR=str(dest), JOB_LIMIT='',
               JOB_CACHE_DIR=str(dest / 'cache'), CLAIM_CHECKER_VERIFY_DOWNLOADS='0',
               CLAIM_CHECKER_CACHE_ROOTS='', PYTHONIOENCODING='utf-8')
    command = [sys.executable, '-B', str(repo / 'jobs/claim-checker/checker.py'), '--claims', str(claims)]
    started = time.monotonic()
    with (dest / 'RUN.log').open('w', encoding='utf-8') as log:
        run = subprocess.run(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)
    batch.dump(dest / 'RUN.json', {'command': command, 'returncode': run.returncode,
                                 'wall_seconds': time.monotonic() - started, 'network_verification': False})
    require(run.returncode == 0, 'actual checker failed; inspect checker/RUN.log')
    return read_json((dest / 'PER_CLAIM.json').read_bytes())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pin_checker_inputs(inputs, selected):
    """Reuse the actual SourceIndex; freeze its relevant raw bytes and metadata."""
    repo = inputs.repo
    script = repo / 'jobs/claim-checker/checker.py'
    if not script.exists():
        return  # The actual invocation will report missing checker code.
    checker = load_module('claim_kit_completion_checker', script)
    for rel in checker.S.INPUTS.values():
        inputs.optional(rel)
    for key in ('universe', 'decided', 'crosswalk', 'stage14_fetch'):
        inputs.optional(checker.P[key])
    for pattern in ('jobs/*/output/SOURCES.jsonl', 'jobs/*/data/PROVENANCE.json',
                    'jobs/*/output/FRAGMENTS*.jsonl', 'jobs/*/data/**/FRAGMENTS*.jsonl',
                    'research/readiness/factual/*/*.jsonl', 'jobs/official-fixity/output/*',
                    'jobs/claim-checker/data/*'):
        inputs.pattern(pattern)
    index = checker.S.build_index(repo, repo / 'jobs/claim-checker', exclude_jobs=('claim-checker',))
    hashes = set()
    def visit(value):
        if isinstance(value, dict):
            for key in ('sha256', 'local_file_sha256'):
                if isinstance(value.get(key), str) and SHA.fullmatch(value[key]):
                    hashes.add(value[key])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    for claim, _ in selected.values():
        visit(claim)
    for sha in hashes:
        for copy in index.lookup_sha(sha):
            paths = [copy.local_path, copy.text_path]
            paths.extend(pair[0] for pair in copy.zip_members)
            for path in paths:
                if isinstance(path, tuple):
                    path = path[0]
                if path is not None and Path(path).is_file():
                    inputs.pin(Path(path).resolve().relative_to(repo).as_posix())


def run_tracker(repo, selected, checker, dest, inputs=None):
    """Use actual tracker build/summarise twice with isolated input substitutions."""
    tracker = load_module('claim_kit_completion_tracker', repo / 'jobs/readiness-tracker/tracker.py')
    # The actual tracker reports missing required CSVs as problems; these are
    # input omissions, not a meaningful before/after comparison.
    for key, rel in tracker.P.items():
        if key not in ('claims', 'exhausted', 'claim_gate_dir'):
            require((repo / rel).is_file(), 'tracker input missing: ' + rel)
    if inputs is not None:
        rels = [v for k, v in tracker.P.items() if k not in ('claims', 'claim_gate_dir')]
        for value in tracker.J.values():
            rels.extend(value if isinstance(value, list) else [value])
        snapshot = inputs.file_sets.get(CLAIMS_PATTERN)  # files added since the start are judged by unchanged()
        rels.extend(snapshot if snapshot is not None else
                    (p.relative_to(repo).as_posix() for p in (repo / 'research/readiness/claims').glob('*.jsonl')))
        for rel in sorted(set(rels)):
            inputs.optional(rel)
    before, problems = tracker.build(str(repo))
    before_summary = tracker.summarise(before, problems)
    tracker.write_outputs(dest / 'tracker-before', before, before_summary, {'replay': 'actual current canonical inputs'})
    union = dest / 'TRACKER_CLAIMS.jsonl'
    canonical = []
    snapshot = inputs.file_sets.get(CLAIMS_PATTERN) if inputs is not None else None
    for path in (sorted(repo / rel for rel in snapshot) if snapshot is not None else
                 sorted((repo / 'research/readiness/claims').glob('*.jsonl'))):
        for line in path.read_bytes().splitlines(keepends=True):
            if line.strip() and read_json(line).get('instrument_id') not in selected:
                canonical.append(line if line.endswith(b'\n') else line + b'\n')
    union.write_bytes(b''.join(canonical) + b''.join(value[1] for value in selected.values()))
    previous = repo / tracker.J['checker']
    checked = read_json(previous.read_bytes()) if previous.exists() else {'by_instrument': {}, 'claims': []}
    checked['by_instrument'] = dict(checked.get('by_instrument', {}))
    checked['claims'] = [row for row in checked.get('claims', []) if row.get('instrument_id') not in selected]
    checked['claims'].extend(row for row in checker.get('claims', []) if row.get('instrument_id') in selected)
    for iid in selected:
        checked['by_instrument'].pop(iid, None)
        require(iid in checker.get('by_instrument', {}), 'checker lacks exact tracker receipt: ' + iid)
        require(checker['by_instrument'][iid].get('claim_sha256') == claim_sha(selected[iid][0]), 'tracker checker version mismatch: ' + iid)
        checked['by_instrument'][iid] = checker['by_instrument'][iid]
    replay = dest / 'TRACKER_CHECKER.json'
    batch.dump(replay, checked)
    tracker.P['claims'] = str(union)
    tracker.J['checker'] = str(replay)
    after, problems = tracker.build(str(repo))
    after_summary = tracker.summarise(after, problems)
    tracker.write_outputs(dest / 'tracker-after', after, after_summary, {'replay': 'selected proposed bytes; no canonical write'})
    before_by = {r['instrument_id']: r for r in before}
    after_by = {r['instrument_id']: r for r in after}
    return {'before': before_summary, 'after': after_summary,
            'selected': {iid: {'before': before_by.get(iid), 'after': after_by.get(iid)} for iid in selected},
            'canonical_outputs_modified': False}


def lock_path(repo):
    """Outside the working tree when Git is available (the shared common directory, so linked
    worktrees serialize too and the lock can never be committed); otherwise LOCK_REL."""
    try:
        run = subprocess.run(['git', 'rev-parse', '--git-common-dir'], cwd=repo, capture_output=True, text=True)
    except OSError:
        run = None
    if run is not None and run.returncode == 0 and run.stdout.strip():
        common = (Path(repo) / run.stdout.strip()).resolve()
        if common.is_dir():
            return common / 'claim-kit-publication.lock'
    return Path(repo) / LOCK_REL


def holder_dead(path):
    """True only when the recorded holder is a process on this host that no longer exists (POSIX)."""
    if os.name != 'posix':
        return False
    try:
        holder = json.loads(path.read_bytes())
        pid = holder['pid']
        if holder.get('host') != socket.gethostname() or type(pid) is not int or pid <= 0:
            return False
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return False


class PublicationLock:
    """Exclusive O_EXCL lock file for the short recheck-and-write transaction.

    A lock whose recorded holder is a dead process on this host is removed (and receipted);
    any other held lock is waited for and then fails closed, naming the lock.
    """
    def __init__(self, repo, dest):
        self.path = lock_path(repo)
        self.dest = dest
        self.held = False
        self.broken = []

    def acquire(self):
        try:
            timeout = float(os.environ.get(LOCK_TIMEOUT_ENV, LOCK_TIMEOUT_DEFAULT))
        except ValueError:
            raise ValueError('invalid %s' % LOCK_TIMEOUT_ENV)
        deadline = time.monotonic() + timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if holder_dead(self.path):
                    try:
                        self.broken.append(json.loads(self.path.read_bytes()))
                        self.path.unlink()
                    except (OSError, ValueError):
                        pass
                    continue
                if time.monotonic() >= deadline:
                    raise ValueError('publication lock held by another completion (a lock is removed automatically only '
                                     'when its holder is a dead process on this host): ' + self.path.as_posix())
                time.sleep(min(LOCK_POLL_SECONDS, max(0.0, deadline - time.monotonic())))
                continue
            self.held = True
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump({'pid': os.getpid(), 'host': socket.gethostname(),
                           'started_utc': datetime.now(timezone.utc).isoformat(), 'dest': str(self.dest)}, stream)
            return self

    def release(self):
        if self.held:
            self.held = False
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


def complete(repo, manifest_path, dest, publish=False):
    started = time.monotonic()
    start_utc = datetime.now(timezone.utc).isoformat()
    repo, dest = Path(repo).resolve(), Path(dest).resolve()
    manifest_path = Path(manifest_path).resolve()
    require(not dest.exists() and dest.is_relative_to(repo / 'research') and
            not dest.is_relative_to(repo / 'research/readiness/claims'), 'fresh research result directory required')
    inputs = Inputs(repo)
    manifest = inputs.object({'path': manifest_path.relative_to(repo).as_posix(), 'sha256': batch.file_sha(manifest_path)})
    require(manifest.get('schema') == SCHEMA, 'unknown completion manifest schema')
    require(re.fullmatch(r'[A-Za-z0-9_.-]+', manifest['agent']) is not None, 'simple agent name required')
    require(isinstance(manifest.get('producer_model_family'), str) and manifest['producer_model_family'].strip(), 'producer model family required')
    require(manifest.get('independence_requirement') in ('same_family_separate_context', 'different_family'), 'independence requirement required')
    members = manifest['members']
    require(isinstance(members, list) and 1 <= len(members) <= 50, '1–50 explicit members required')
    require(len({m['instrument_id'] for m in members}) == len(members), 'conflicting or duplicate selected member versions')
    require(isinstance(manifest.get('controls'), list) and bool(manifest['controls']), 'nonempty planted controls required for ordinary completion')
    publication = manifest['publication']
    mode = publication['mode']
    require(mode in ('own_claims', 'replacement_proposal'), 'explicit publication mode required')
    target = batch.safe(repo, publication['path'])
    require(not target.exists() and target.suffix == '.jsonl', 'publication must create a new JSONL file')
    if mode == 'own_claims':
        require(target.parent == repo / 'research/readiness/claims' and target.name.startswith(manifest['agent'] + '-'), 'publication must be an own-agent claims file')
    else:
        require(target.is_relative_to(repo / 'research') and not target.is_relative_to(repo / 'research/readiness'), 'replacement proposals must stay outside canonical readiness')
    dest.mkdir(parents=True)
    outcomes, exceptions, selected, control_results = [], [], {}, []
    blocked_batch = False
    lock = PublicationLock(repo, dest)
    try:
        for rel in ('research/stage19/code/claim_gate.py', 'jobs/claim-kit/completion.py',
                    'jobs/claim-kit/kit.py', 'jobs/claim-kit/batch.py',
                    'jobs/claim-kit/assemble.py', 'jobs/claim-kit/evidence_preflight.py',
                    'jobs/claim-kit/excavate.py', 'jobs/claim-checker/checker.py',
                    'jobs/claim-checker/sources.py', 'jobs/readiness-tracker/tracker.py'):
            if (repo / rel).exists():
                inputs.pin(rel)
        for rel in batch.POLICY_CODE_FILES:
            if (repo / rel).exists():
                inputs.pin(rel)
        inputs.claim_files()
        inputs.optional('research/readiness/SOURCE_AUDIT_HOLDS.jsonl')
        inputs.optional('research/production/claim-kit-pilot-2026-10-18/FREEZE_MANIFEST.json')
        held = held_versions(inputs)
        control_results = controls(inputs, manifest)
        require(all(row['caught'] for row in control_results), 'control was not caught; affected batch filing stopped')
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        held = set()
        blocked_batch = True
        exceptions.append({'scope': 'batch', 'error': str(exc)})
    planted = {(c.get('instrument_id'), c.get('planted_claim_sha256')) for c in manifest['controls'] if isinstance(c, dict)}
    existing = batch.owners(repo)
    for member in members:
        iid = member['instrument_id']
        row = {'instrument_id': iid, 'claim_sha256': member.get('claim_sha256'), 'outcome': member.get('outcome')}
        try:
            require(member.get('outcome') in ('submit', 'blocked', 'unresolved', 'route_owner'), 'explicit member outcome required')
            if member['outcome'] != 'submit':
                require(isinstance(member.get('reason'), str) and member['reason'].strip(), 'non-submission reason required')
                row['reason'] = member['reason']
            else:
                require(not blocked_batch, 'batch control/hold evidence exception blocks filing')
                if iid in existing and mode != 'replacement_proposal':
                    owner = existing[iid]['owner']
                    require(owner == manifest['agent'] or owner.startswith(manifest['agent'] + '-'), 'existing claim belongs to another owner; explicit replacement proposal required')
                    require(target.name > Path(existing[iid]['path']).name, 'own replacement would be shadowed by an existing claim filename')
                claim, raw, detail = selected_claim(inputs, member, manifest, planted, held)
                selected[iid] = (claim, raw)
                row.update(detail, outcome='selected')
        except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
            row.update(outcome='exception', error=str(exc))
            exceptions.append({'instrument_id': iid, 'claim_sha256': member.get('claim_sha256'), 'error': str(exc)})
        outcomes.append(row)
    try:
        for ref in manifest.get('receipts', []):
            inputs.file(ref)
        proposed = dest / 'CLAIMS.selected.jsonl'
        proposed.write_bytes(b''.join(value[1] for value in selected.values()))
        if selected:
            pin_checker_inputs(inputs, selected)
        checker = run_checker(repo, proposed, dest / 'checker') if selected else {'claims': [], 'by_instrument': {}}
        for iid in list(selected):
            matches = [r for r in checker['claims'] if r.get('instrument_id') == iid and
                       r.get('claim_sha256') == claim_sha(selected[iid][0])]
            row = next(r for r in outcomes if r['instrument_id'] == iid)
            if len(matches) != 1 or matches[0].get('mechanical_result') != 'pass' or (
                    row['publication_kind'] == 'whole_case' and not matches[0].get('all_checks_passed')) or (
                    row['publication_kind'] == 'partial_research' and sorted(matches[0].get('gate_errors', [])) != sorted(row['gate_errors'])):
                row.update(outcome='rejected_mechanical', checker=matches)
                exceptions.append({'instrument_id': iid, 'error': 'actual checker did not pass exact version', 'receipts': matches})
                del selected[iid]
            else:
                row['outcome'] = 'eligible'
        tracker_result = run_tracker(repo, selected, checker, dest, inputs)
        batch.dump(dest / 'TRACKER_REPLAY.json', tracker_result)
        for row in outcomes:
            if row.get('publication_kind') == 'partial_research' and row['instrument_id'] in selected:
                after = tracker_result.get('selected', {}).get(row['instrument_id'], {}).get('after') or {}
                require(after.get('ready_for_human_review') != 'yes',
                        'partial review cannot supply complete-history/ready credit; whole_case review required: ' + row['instrument_id'])
        for member in members:
            iid = member['instrument_id']
            if iid in selected and 'status_overlay' in selected[iid][0].get('claim_kit', {}):
                allowed = next(row['gate_errors'] for row in outcomes if row['instrument_id'] == iid)
                require(not [error for error in working_overlay(inputs, member, manifest, selected[iid][0]) if error not in allowed],
                        'overlay changed during completion: ' + iid)
        # The final recheck is the start of the publication transaction: lock first,
        # then re-verify packet dependencies and every pin before anything is written.
        if publish and selected:
            lock.acquire()
        inputs.recheck_packets()
        inputs.unchanged(set(selected))
        require(not target.exists(), 'publication target appeared during completion: ' + publication['path'])
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        exceptions.append({'scope': 'batch', 'error': str(exc)})
        for row in outcomes:
            if row['outcome'] in ('selected', 'eligible'):
                row.update(outcome='exception', error=str(exc))
        selected = {}
        lock.release()  # nothing will be published
    except BaseException:
        lock.release()
        raise
    try:
        raw = b''.join(value[1] for value in selected.values())
        artifact = dest / 'CLAIMS.publishable.jsonl'
        artifact.write_bytes(raw)
        publication.update(artifact=artifact.relative_to(repo).as_posix(), sha256=batch.digest(raw),
                           claims=len(selected), owner_acceptance_required=mode == 'replacement_proposal',
                           independent_human_certifications=0)
        overlay_ids = [iid for iid,(claim,_) in selected.items() if 'status_overlay' in claim.get('claim_kit', {})]
        if overlay_ids:
            publication.update(status_adoption_required=overlay_ids, canonical_filing_allowed=False,
                               tracker_uses_authoritative_statuses=True)
        inputs.save(dest)
        tally = {'schema': SCHEMA, 'attempted': len(members), 'counts': dict(Counter(r['outcome'] for r in outcomes)),
                 'submitted': sum(m['outcome'] == 'submit' for m in members), 'controls': control_results,
                 'plants_placed': len(manifest['controls']), 'plants_caught': sum(c['caught'] for c in control_results),
                 'eligible': list(selected), 'claims_published': 0,
                 'source_review_upheld': sum(r.get('source_review_upheld', False) for r in outcomes),
                 'eligible_per_attempt': len(selected) / len(members),
                 'independent_human_certifications': 0, 'exceptions': len(exceptions), 'outcomes': outcomes,
                 'concurrent_disjoint_claim_files': inputs.concurrent,
                 'packet_loads': {e['folder'].relative_to(repo).as_posix(): e['loads'] for e in inputs.packets.values()},
                 'stale_publication_locks_removed': lock.broken,
                 'started_utc': start_utc, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                 'wall_seconds': time.monotonic() - started, 'model_tokens': None, 'model_cost': None,
                 'usage_note': 'Completion is deterministic. Agent/research token and cost telemetry is not supplied.'}
        batch.dump(dest / 'PUBLICATION.json', publication)
        batch.dump(dest / 'EXCEPTIONS.json', exceptions)
        batch.dump(dest / 'TALLY.json', tally)
        publication['written'] = False
        batch.dump(dest / 'PUBLICATION.json', publication)
        # Preserve all receipts before the sole externally visible write. Exclusive
        # creation refuses races and never appends or overwrites another claim file.
        if publish and raw:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(raw)
            publication['written'] = True
            batch.dump(dest / 'PUBLICATION.json', publication)
            tally['claims_published'] = len(selected) if mode == 'own_claims' else 0
            batch.dump(dest / 'TALLY.json', tally)
        return tally
    finally:
        lock.release()
