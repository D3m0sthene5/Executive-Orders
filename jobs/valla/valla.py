"""VALLA: exact reasoning lineage and targeted preparation. Never decides law."""
import argparse
import csv
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCHEMA = 'eo-valla-index/v1'
PROTOCOLS = ['jobs/claim-kit/AGENT_PROTOCOL.md', 'jobs/claim-kit/BATCH.md',
             'research/stage19/CLAIM_SCHEMA.md', 'research/stage19/code/claim_gate.py',
             'research/stage15/LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json']
NOTICE = ('Review lead only. Every case needs separate applicability, earlier-ending, scope, '
          'independent-command, savings and independent whole-case review.')
REASON_FIELDS = {'research_rationale', 'rationale', 'reason', 'mechanism', 'legal_basis',
                 'earlier_end_check', 'scope_check', 'independent_command_check', 'savings_check'}


def canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(v):
    return hashlib.sha256(canon(v).encode()).hexdigest()


def file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def safe(repo, rel):
    p = (Path(repo) / rel).resolve()
    if not p.is_relative_to(Path(repo).resolve()):
        raise ValueError('dependency outside repository')
    return p


def rows(path):
    if not Path(path).exists():
        return []
    return [json.loads(l) for l in Path(path).read_text('utf-8').splitlines() if l.strip()]


def escape(key):
    return str(key).replace('~', '~0').replace('/', '~1')


def at(obj, pointer):
    if not pointer:
        return obj
    if not pointer.startswith('/'):
        raise ValueError('JSON pointer required')
    for part in pointer[1:].split('/'):
        key = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj


def walk(obj, pointer=''):
    yield pointer, obj
    if isinstance(obj, dict):
        for k, v in sorted(obj.items()):
            yield from walk(v, pointer + '/' + escape(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, pointer + '/' + str(i))


def production_claim(c):
    return (isinstance(c, dict) and c.get('schema') == 'eo-lifecycle-claim/v1'
            and str(c.get('instrument_id', '')).startswith('EO:')
            and not any(c.get(k) for k in ('SEEDED', 'seeded', 'synthetic')))


def active_claims(repo):
    """Exactly the existing filename/line winner convention; retain old version refs."""
    active = {}; history = []
    for p in sorted((Path(repo) / 'research/readiness/claims').glob('*.jsonl')):
        for line, text in enumerate(p.read_text('utf-8').splitlines(), 1):
            if not text.strip():
                continue
            c = json.loads(text)
            if not production_claim(c):
                raise ValueError('nonproduction claim in canonical claims: ' + str(p))
            ref = {'path': p.relative_to(repo).as_posix(), 'line': line, 'claim_sha256': sha(c)}
            history.append({'instrument_id': c['instrument_id'], **ref})
            active[c['instrument_id']] = {'claim': c, 'ref': ref}
    return active, history


def normalize(text):
    """Case/space/punctuation only, with Unicode-character back map; keep numbers."""
    out = []; offsets = []
    for i, char in enumerate(text):
        for ch in (char.casefold() if char.isalnum() else ' '):
            if ch == ' ' and (not out or out[-1] == ' '):
                continue
            out.append(ch); offsets.append(i)
    return ''.join(out), offsets


def spans(text, patterns):
    normalized, offsets = normalize(text); found = []
    for p in patterns:
        for expr in p['expressions']:
            for m in re.finditer(expr, normalized):
                a, b = offsets[m.start()], offsets[m.end() - 1] + 1
                rec = {'pattern_id': p['id'], 'char_start': a, 'char_end': b,
                       'exact_text': text[a:b], 'span_sha256': sha(text[a:b]),
                       'rule_refs': p['rule_refs'], 'question': p['question']}
                if rec not in found:
                    found.append(rec)
    return sorted(found, key=lambda x: (x['char_start'], x['char_end'], x['pattern_id']))


def source_dependencies(c):
    return [{'pointer': p, 'source_sha256': sha(v), 'text_path': v.get('text_path'),
             'text_sha256': v.get('text_sha256'),
             'artifact_sha256': v.get('sha256') or v.get('local_file_sha256')}
            for p, v in walk(c) if isinstance(v, dict) and
            (p.endswith('/source') or p.endswith('_source') or p == '/original_representation')]


def pins(repo, paths):
    return {p: file_sha(safe(repo, p)) if safe(repo, p).is_file() else None for p in sorted(set(paths))}


def package_paths(repo):
    # The tracked registry is stable across sparse checkouts. Runtime correction
    # packets are deliberately excluded, preventing self-input and output cycles.
    result=subprocess.run(['git','ls-files','--','research/excavator/**/RATIONALES.json',
                           'research/production/**/RATIONALES.json'],cwd=repo,capture_output=True,text=True)
    if result.returncode:
        return [], ['tracked package inventory unavailable']
    paths=sorted(set(result.stdout.splitlines()))
    if len(paths)>100:
        raise ValueError('package inventory exceeds bounded 100-package limit')
    loaded=[];missing=[]
    for rel in paths:
        folder=Path(repo)/Path(rel).parent
        if not (folder/'RATIONALES.json').is_file():missing.append(rel)
        else:loaded.append(folder)
    return loaded, missing


def shared_lineage(repo, packages):
    """Observed references only; a package reference never proves claim derivation."""
    result = []
    folders=sorted(set(Path(p).resolve() for p in packages))
    if len(folders)>100:
        raise ValueError('at most 100 packages per index')
    for folder in folders:
        if not folder.is_relative_to(Path(repo).resolve() / 'research'):
            raise ValueError('packages must be under research')
        rp = folder / 'RATIONALES.json'
        if not rp.exists():
            continue
        shared = json.loads(rp.read_bytes())
        for name in ('decisions.csv', 'clauses.csv'):
            p = folder / name
            if not p.exists():
                continue
            with p.open(encoding='utf-8-sig', newline='') as f:
                for line, r in enumerate(csv.DictReader(f), 2):
                    for field, value in r.items():
                        if isinstance(value, str) and value.startswith('@rationale:'):
                            result.append({'instrument_id': r.get('instrument_id'), 'scope_id': r.get('scope_id'),
                                           'path': p.relative_to(repo).as_posix(), 'file_sha256': file_sha(p),
                                           'line': line, 'field': field, 'reference': value,
                                           'rationales_path': rp.relative_to(repo).as_posix(),
                                           'rationales_sha256': file_sha(rp), 'resolved_text': shared.get(value[11:]),
                                           'causal_derivation_established': False})
    return result


def conclusions(c):
    result = ['/whole_order_end', '/savings_residuals']
    for i, clause in enumerate(c.get('operative_clauses', [])):
        for k in ('first_end', 'current_predicate', 'later_events', 'state_at_cutoff'):
            if k in clause:
                result.append('/operative_clauses/' + str(i) + '/' + k)
    return result


def component(c, selector):
    """Preparation fields only; an ending theory cannot masquerade as a fact."""
    kind = selector['kind']; scope = selector.get('scope_id')
    clauses = c.get('operative_clauses', [])
    clause = next((x for x in clauses if x.get('scope_id') == scope), None)
    if kind == 'source_identity':
        return c['original_representation']
    if kind == 'exact_quotation' and clause:
        return {'scope_id': scope, 'text': clause['original_operative_text'], 'source': clause['original_source']}
    if kind == 'clause_inventory':
        return [{'scope_id': x['scope_id'], 'text': x['original_operative_text'], 'source': x['original_source']} for x in clauses]
    if kind == 'factual_finding' and selector.get('pointer', '').startswith('/claim_kit/factual_findings/'):
        return at(c, selector['pointer'])
    raise ValueError('unsupported preparation component or scope')


def reviewed_record(repo, ref):
    p = safe(repo, ref['path']); rel = p.relative_to(Path(repo).resolve()).as_posix()
    if not rel.startswith('research/') or rel.startswith('research/readiness/claims/'):
        raise ValueError('review artifact must be a separate research record')
    if file_sha(p) != ref['file_sha256']:
        raise ValueError('review artifact changed')
    rs = rows(p) if p.suffix == '.jsonl' else [json.loads(p.read_bytes())]
    matches = [r for r in rs if r.get('record_id') == ref['record_id']]
    if len(matches) != 1:
        raise ValueError('review record missing or ambiguous')
    return matches[0]


def dependencies_valid(repo, dependencies, c, invalidated):
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError('explicit nonempty dependencies required')
    keys = set()
    for d in dependencies:
        key = d['key']
        if key in keys:
            raise ValueError('duplicate dependency')
        keys.add(key)
        if any(key == x or key.startswith(x + '/') or x.startswith(key + '/') for x in invalidated):
            raise ValueError('dependent conclusion or premise invalidated: ' + key)
        if d['kind'] in ('file', 'rule'):
            actual = file_sha(safe(repo, key))
        elif d['kind'] == 'claim_field':
            actual = sha(at(c, key))
        else:
            raise ValueError('unknown dependency kind')
        if actual != d['sha256']:
            raise ValueError('dependency changed: ' + key)


def closure(changed, edges):
    """Edges (dependent, prerequisite); cycles cannot make a component reusable."""
    invalid = set(changed)
    while True:
        new = {a for a, b in edges if b in invalid} - invalid
        if not new:
            return invalid
        invalid.update(new)


def validate_attestation(repo, a, c, invalidated=()):
    try:
        if a.get('schema') != 'eo-component-attestation/v1' or not production_claim(c):
            raise ValueError('schema or production boundary')
        if a['instrument_id'] != c['instrument_id']:
            raise ValueError('wrong instrument')
        old_ref = a['reviewed_claim_ref']
        old_path = safe(repo, old_ref['path'])
        if not old_path.relative_to(Path(repo).resolve()).as_posix().startswith('research/'):
            raise ValueError('reviewed claim must be held in research')
        old = rows(old_path)[old_ref['line'] - 1]
        if not production_claim(old) or sha(old) != a['reviewed_claim_sha256'] or old['instrument_id'] != c['instrument_id']:
            raise ValueError('reviewed claim version not held')
        producer = old.get('claim_kit', {}).get('agent')
        if not producer or a.get('producer') != producer or a.get('reviewer') == producer:
            raise ValueError('producer/reviewer identity not established')
        if a.get('independent') is not True or a.get('review_kind') != 'independent_ai_component':
            raise ValueError('explicit independent component review required')
        if not isinstance(a.get('reviewer'), str) or not a['reviewer'].strip():
            raise ValueError('reviewer identity required')
        date.fromisoformat(a['reviewed_on'])
        required = ['attestation_id', 'instrument_id', 'component_selector', 'component_sha256',
                    'producer', 'reviewer', 'independent', 'review_kind', 'method', 'dependencies',
                    'verdict', 'reviewed_claim_sha256', 'reviewed_claim_ref', 'reviewed_on']
        r = reviewed_record(repo, a['review_ref'])
        if r.get('schema') != 'eo-component-review/v1' or any(r.get(k) != a.get(k) for k in required):
            raise ValueError('attestation differs from explicit component review')
        if a.get('verdict') != 'upheld' or not isinstance(r.get('rationale'), str) or len(r['rationale']) < 40:
            raise ValueError('no substantive field-level approval')
        if not a.get('method') or not a.get('reviewed_on') or not a.get('reviewed_claim_sha256'):
            raise ValueError('missing scope/method/version')
        value = component(c, a['component_selector'])
        if sha(value) != a['component_sha256'] or sha(component(old, a['component_selector'])) != a['component_sha256']:
            raise ValueError('component changed')
        dependencies_valid(repo, a['dependencies'], c, invalidated)
        if not any(d['kind'] == 'rule' for d in a['dependencies']):
            raise ValueError('method version dependency missing')
        if not any(d['kind'] == 'file' for d in a['dependencies']):
            raise ValueError('source dependency missing')
        source_paths = {v['text_path'] for _, v in walk(value) if isinstance(v, dict) and v.get('text_path')}
        files = {d['key'] for d in a['dependencies'] if d['kind'] == 'file'}
        if not source_paths or not source_paths <= files:
            raise ValueError('every held source path must be an explicit dependency')
        if a['component_selector']['kind'] == 'source_identity':
            artifact = a['component_selector']['artifact_path']
            if artifact not in files or file_sha(safe(repo, artifact)) != (value.get('sha256') or value.get('local_file_sha256')):
                raise ValueError('source identity requires the exact reviewed source artifact')
        if a['component_selector']['kind'] == 'exact_quotation':
            src = value['source']; raw = safe(repo, src['text_path']).read_bytes(); text = raw.decode('utf-8')
            lo, hi = src['char_start'], src['char_end']
            if hashlib.sha256(raw).hexdigest() != src['text_sha256'] or type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= len(text) or text[lo:hi] != value['text']:
                raise ValueError('quotation is not the exact held span')
            if not any(d['kind'] == 'file' and d['key'] == src['text_path'] for d in a['dependencies']):
                raise ValueError('held text dependency missing')
        return {'valid': True, 'attestation_id': a['attestation_id'], 'component_selector': a['component_selector'],
                'review_ref': a['review_ref'], 'reviewed_claim_sha256': a['reviewed_claim_sha256'],
                'current_claim_sha256': sha(c), 'method': a['method'], 'value': value,
                'approval_scope': 'preparation_component_only', 'whole_case_review_required': True}
    except (ValueError, KeyError, IndexError, TypeError, OSError, UnicodeError, StopIteration) as exc:
        return {'valid': False, 'attestation_id': a.get('attestation_id'), 'reason': str(exc)}


def confirmed_findings(repo, active):
    good = []; refused = []
    for p in sorted((Path(repo) / 'research/readiness/method_reviews').glob('*.jsonl')):
        for f in rows(p):
            try:
                if f.get('schema') != 'eo-method-dependency-review/v1' or f.get('independent') is not True or f.get('verdict') != 'revalidate':
                    raise ValueError('explicit revalidation review required')
                if f.get('review_kind') != 'independent_ai_method_review' or not isinstance(f.get('reviewer'), str) or not f['reviewer'].strip():
                    raise ValueError('named independent methodological reviewer required')
                date.fromisoformat(f['reviewed_on'])
                r = reviewed_record(repo, f['review_ref'])
                if any(r.get(k) != v for k, v in f.items() if k != 'review_ref'):
                    raise ValueError('method review artifact differs')
                c = active[f['instrument_id']]['claim']
                if sha(c) != f['claim_sha256']:
                    raise ValueError('stale claim')
                if f['producer'] != c.get('claim_kit', {}).get('agent') or f['reviewer'] == f['producer']:
                    raise ValueError('not independent of claim producer')
                text = at(c, f['rationale_pointer']); a, b = f['char_start'], f['char_end']
                if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text) or sha(text[a:b]) != f['span_sha256']:
                    raise ValueError('changed rationale span')
                if not f['conclusion_pointers'] or any(ptr not in conclusions(c) for ptr in f['conclusion_pointers']):
                    raise ValueError('unknown conclusion pointer')
                for key in ('applicability', 'earlier_ending', 'scope', 'independent_commands', 'savings', 'unresolved_question', 'analysis'):
                    if not isinstance(f.get(key), str) or len(f[key].strip()) < 20:
                        raise ValueError('missing case-specific examination: ' + key)
                dependencies_valid(repo, f['dependencies'], c, ())
                good.append(f)
            except (ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
                refused.append({'path': p.relative_to(repo).as_posix(), 'record_id': f.get('record_id'), 'reason': str(exc)})
    return good, refused


def build(repo, packages=(), ids=None):
    repo = Path(repo).resolve(); active, history = active_claims(repo)
    all_active = active
    if ids is not None:
        active = {i: v for i, v in active.items() if i in ids}
    library = json.loads((HERE / 'premises.json').read_bytes()); protocol_pins = pins(repo, PROTOCOLS)
    discovered, missing_packages = package_paths(repo)
    shared = shared_lineage(repo, [*discovered, *packages])
    # Findings for other IDs are filtered without treating them as bad records.
    findings, refused = confirmed_findings(repo, all_active)
    attestations = [a for p in sorted((repo / 'research/readiness/component_attestations').glob('*.jsonl')) for a in rows(p)]
    claims = {}; groups = {}; queue = []
    for iid, entry in sorted(active.items()):
        c = entry['claim']; nodes = []
        for ptr, v in walk(c):
            if not isinstance(v, str) or ptr.rsplit('/', 1)[-1] not in REASON_FIELDS:
                continue
            if any(part in ('source', 'original_source', 'original_representation') for part in ptr.split('/')):
                continue
            normalized, _ = normalize(v); matches = spans(v, library['patterns'])
            nodes.append({'pointer': ptr, 'text_sha256': sha(v), 'normalization_sha256': sha(normalized),
                          'exact_text': v, 'matches': matches})
            for m in matches:
                queue.append({'instrument_id': iid, 'claim_ref': entry['ref'], 'rationale_pointer': ptr, **m,
                              'state': 'textual_review_lead', 'candidate_conclusion_pointers': conclusions(c),
                              'dependency_confirmed': False, 'notice': NOTICE})
            if normalized.strip():
                groups.setdefault(sha(normalized), []).append({'instrument_id': iid, 'pointer': ptr, 'text_sha256': sha(v)})
        fs = [f for f in findings if f['instrument_id'] == iid]
        edges = [('/whole_order_end', '/operative_clauses/' + str(i) + '/first_end')
                 for i, clause in enumerate(c.get('operative_clauses', [])) if clause.get('first_end')]
        invalidated = closure({ptr for f in fs for ptr in f['conclusion_pointers']}, edges)
        for f in fs:
            queue.append({'instrument_id': iid, 'claim_ref': entry['ref'], 'state': 'independently_examined_revalidation',
                          'dependency_confirmed': True, 'finding': f, 'notice': NOTICE})
        salvage = [validate_attestation(repo, a, c, invalidated) for a in attestations if a.get('instrument_id') == iid]
        claims[iid] = {'claim_ref': entry['ref'], 'producer': c.get('claim_kit', {}).get('agent'),
                       'template_lineage': c.get('claim_kit', {}).get('template'),
                       'template_lineage_unknown': not bool(c.get('claim_kit', {}).get('template')),
                       'rationales': nodes, 'source_dependencies': source_dependencies(c),
                       'shared_rationale_references': [x for x in shared if x['instrument_id'] == iid],
                       'invalidated_conclusion_pointers': sorted(invalidated), 'component_reviews': salvage}
    doc = {'schema': SCHEMA, 'notice': NOTICE, 'claim_versions': history, 'claims': claims,
           'shared_rationale_references': shared,
           'protocol_pins': protocol_pins, 'controlling_codebook_version': 'not separately located; protocol pins do not amend the codebook',
           'premise_library_sha256': file_sha(HERE / 'premises.json'),
           'package_scan': {'tracked_packages_loaded': len(discovered), 'unmaterialized_packages': missing_packages,
                            'causal_derivation_inferred': False},
           'textual_groups': [v for v in groups.values() if len({x['instrument_id'] for x in v}) > 1],
           'review_queue': queue, 'refused_method_reviews': refused,
           'summary': {'active_claims': len(claims), 'textual_leads': sum(x['state'] == 'textual_review_lead' for x in queue),
                       'shared_rationale_references': len(shared),
                       'examined_dependencies': sum(f['instrument_id'] in active for f in findings),
                       'valid_components': sum(r['valid'] for c in claims.values() for r in c['component_reviews']),
                       'legal_promotions': 0, 'model_calls': 0}}
    doc['fingerprint'] = sha(doc)
    return doc


def attach(repo, ids):
    """Fresh bounded packet context, without cached-output dependency cycles."""
    index = build(repo, ids=ids)
    return {'schema': 'eo-valla-packet-context/v1', 'notice': NOTICE,
            'valla_code_sha256': file_sha(HERE / 'valla.py'),
            'package_scan': index['package_scan'],
            'protocol_pins': index['protocol_pins'], 'premise_library_sha256': index['premise_library_sha256'],
            'claims': index['claims'], 'review_queue': index['review_queue'],
            'whole_case_review_required': True, 'automatic_approvals': 0}


def correction(repo, out, ids, dest, agent):
    sys.path.insert(0, str(Path(repo) / 'jobs/claim-kit'))
    import batch
    # Existing reservation, replacement-proposal and no-overwrite checks remain controlling.
    batch.prepare(Path(repo), Path(out), Path(dest), ids, agent, replacement_proposal=True)
    packet, _ = batch.load_packet(Path(dest), Path(repo))
    return {'orders': ids, 'packet_fingerprint': packet['fingerprint'], 'replacement_proposal': True,
            'claims_published': 0, 'owner_acceptance': False, 'independent_whole_case_review_required': True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=REPO)
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('build'); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--package', type=Path, action='append', default=[])
    p = sub.add_parser('correction'); p.add_argument('ids', nargs='+')
    p.add_argument('--kit-output', type=Path); p.add_argument('--write', type=Path, required=True); p.add_argument('--agent', required=True)
    args = parser.parse_args(argv)
    if args.cmd == 'build':
        doc = build(args.repo, args.package); dump(args.output / 'INDEX.json', doc)
        dump(args.output / 'SUMMARY.json', doc['summary']); print(canon(doc['summary']))
    else:
        print(canon(correction(args.repo, args.kit_output or args.repo / 'jobs/claim-kit/output', args.ids, args.write, args.agent)))


if __name__ == '__main__':
    main()
