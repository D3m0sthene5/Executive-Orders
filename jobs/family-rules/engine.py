"""Bounded, fail-closed rule proofs; never adjudicates legal status."""
from __future__ import annotations
import collections, csv, datetime, hashlib, importlib.util, json, re
from pathlib import Path

CUTOFF = '2026-10-14'
ENDS = {'revocation', 'rescission', 'supersession_or_revocation', 'supersession'}
SAVINGS = re.compile(r'\b(savings?|except|insofar|in so far|pending|accrued|vested|without prejudice|shall (?:remain|continue)|heretofore|until modified)\b', re.I)
def canonical(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def digest(x): return hashlib.sha256(x).hexdigest()
def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(canonical(obj)+'\n', encoding='utf-8', newline='\n')
def jsonl(p):
    if not p.is_file(): return []
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def csvrows(p):
    if not p.is_file(): return []
    with p.open(encoding='utf-8', newline='') as f: return list(csv.DictReader(f))
def child(root, rel):
    p = Path(str(rel).replace('\\', '/'))
    if p.is_absolute() or '..' in p.parts or ':' in str(p): raise ValueError('unsafe source path')
    q = (root/p).resolve()
    if not q.is_relative_to(root.resolve()): raise ValueError('source outside repository')
    return q

def valid_date(s):
    try: return isinstance(s, str) and datetime.date.fromisoformat(s).isoformat() == s
    except (TypeError, ValueError): return False

def rule_errors(rule, root):
    errors = []
    if rule.get('review_state') != 'source_reviewed': errors.append('RULE_REQUIRES_SOURCE_REVIEW')
    if rule.get('mechanism') not in ENDS: errors.append('RULE_MECHANISM_UNSUPPORTED')
    if not valid_date(rule.get('effective_date')) or rule['effective_date'] > CUTOFF: errors.append('RULE_EFFECTIVE_DATE_UNPROVEN')
    if rule.get('scope', {}).get('kind') != 'explicit_targets' or not rule.get('scope', {}).get('targets'): errors.append('RULE_SCOPE_UNPROVEN')
    if not rule.get('exceptions_savings', {}).get('reviewed'): errors.append('RULE_SAVINGS_UNREVIEWED')
    src = rule.get('source') or {}
    if not src.get('original_custody_verified'): errors.append('ORIGINAL_SOURCE_CUSTODY_UNVERIFIED')
    if not src.get('url', '').startswith('https://') or not re.fullmatch('[a-f0-9]{64}', src.get('sha256', '')) or not src.get('page'): errors.append('RULE_CUSTODY_INCOMPLETE')
    try:
        raw = child(root, src.get('text_path', '')).read_bytes()
        text = raw.decode('utf-8')
        if digest(raw) != src.get('text_sha256'): errors.append('RULE_TEXT_HASH_MISMATCH')
        if not rule.get('quoted_clause') or rule['quoted_clause'] not in text: errors.append('RULE_QUOTE_NOT_EXACT')
    except (OSError, ValueError, UnicodeError): errors.append('RULE_TEXT_UNAVAILABLE')
    return errors

def assess(rule, target, edges, texts, mentions, sweep, errors):
    reasons = list(errors)
    relevant = [e for e in edges if e.get('target_id') == target]
    matching = [e for e in relevant if e.get('acting_id') == rule['acting_id'] and e.get('mechanism') == rule.get('mechanism')]
    if target not in rule.get('scope', {}).get('targets', []): reasons.append('TARGET_OUTSIDE_RULE_SCOPE')
    if not matching: reasons.append('NO_MATCHING_END_EDGE')
    if any(e.get('qualifier') for e in relevant if e.get('acting_id') == rule['acting_id']): reasons.append('QUALIFIED_OR_CONFLICTING_SCOPE')
    date = rule.get('effective_date') or ''
    for e in relevant:
        d = e.get('stated_effective_date') or e.get('date_candidate')
        # signing date may differ only if rule carries a source-reviewed effective-date explanation.
        if e.get('acting_id') == rule['acting_id'] and (e.get('date_flags') and 'sentence_states_effective_date_' not in e['date_flags'] or not valid_date(d) or d != date and not rule.get('effective_date_basis')):
            reasons.append('DATE_CONFLICT_OR_UNKNOWN')
        if e.get('acting_id') != rule['acting_id'] and e.get('mechanism') in ENDS and (not valid_date(d) or d <= date): reasons.append('EARLIER_OR_UNDATED_ENDING')
        if e.get('mechanism') in {'reinstatement', 'ratification'} and (not valid_date(d) or d >= date): reasons.append('REVIVAL_LEAD')
    if not texts: reasons.append('TARGET_ORIGINAL_TEXT_MISSING')
    if any(SAVINGS.search(t) for t in texts) or rule.get('exceptions_savings', {}).get('leads'): reasons.append('INDEPENDENT_CLAUSE_OR_SAVINGS_LEAD')
    # Text parsing alone cannot prove that every independent clause was extinguished.
    if target not in rule.get('target_scope_reviewed', []): reasons.append('TARGET_INDEPENDENT_CLAUSES_UNREVIEWED')
    if mentions: reasons.append('CURRENT_LAW_USE_LEAD')
    if sweep: reasons.append('LATER_OR_UNDATED_SAVED_TEXT_USE')
    return {'schema':'eo-family-proof/v1', 'instrument_id':target, 'acting_id':rule['acting_id'],
            'rule_sha256':digest(canonical(rule).encode()), 'result':'blocked' if reasons else 'bounded_checks_passed',
            'blockers':sorted(set(reasons)), 'edge_ids':sorted({e['edge_id'] for e in matching}),
            'counterexamples':sweep, 'current_law_hits':mentions,
            'scope_note':'Saved corpus only; passing is a research draft, never a legal finding or readiness acceptance.'}

def run(root, out):
    edges = csvrows(root/'jobs/later-events/output/EDGES.csv')
    catalog = {r['id']: r for r in csvrows(root/'jobs/later-events/output/CATALOG_INDEX.csv')}
    mentions = collections.defaultdict(list)
    for r in csvrows(root/'jobs/current-law/output/MENTIONS.csv'):
        iid = r.get('instrument_id') or r.get('target_id') or r.get('order_id')
        if iid: mentions[iid].append(r)
    for f in jsonl(root/'jobs/current-law/output/FRAGMENTS.jsonl'):
        if f.get('kind') == 'current_predicate_candidates': mentions[f['instrument_id']].append({'fragment_kind':f['kind'], 'source_refs':f.get('sources',[])})
    # Index every saved source-text derivative, including ones not in source manifests.
    paths = sorted({p for base in (root/'jobs', root/'research') if base.exists() for p in base.rglob('*')
                    if p.is_file() and p.suffix.lower() in {'.txt', '.xml', '.html', '.htm'}
                    and p.name not in {'needs.txt','requirements.txt','triggers.txt','after.txt','log.txt','install-log.txt'}
                    and 'family-rules' not in p.parts and 'case-bundles' not in p.parts})
    docs = []
    refs_path = root/'jobs/current-law/eo_refs.py'
    spec = importlib.util.spec_from_file_location('family_eo_refs', refs_path)
    refs = importlib.util.module_from_spec(spec); spec.loader.exec_module(refs)
    manifest = []
    own_texts = collections.defaultdict(list)
    for p in paths:
        raw = p.read_bytes(); text = raw.decode('utf-8', errors='replace')
        ids = {f"EO:{h['number']}{h['suffix']}" for h in refs.find_eo_refs(text)}
        # A file's earliest heading is only an identity hint; lack of reliable date blocks any match.
        heading = next(iter(refs.find_eo_refs(text[:1000])), None)
        owner = f"EO:{heading['number']}{heading['suffix']}" if heading else ''
        d = catalog.get(owner, {}).get('signing_date', '')
        rel = p.relative_to(root).as_posix()
        docs.append((rel, ids, owner, d, text)); manifest.append({'path':rel,'sha256':digest(raw),'date_hint':d})
        if owner: own_texts[owner].append(text)
    sweep_hash = digest(canonical(manifest).encode())
    rules = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((root/'research/readiness/rules').glob('*.json'))]
    fragments, certs = [], []
    for rule in rules:
        errors = rule_errors(rule, root)
        if not (root/'jobs/current-law/output/FRAGMENTS.jsonl').is_file(): errors.append('CURRENT_LAW_SCAN_UNAVAILABLE')
        if not docs: errors.append('SAVED_TEXT_SWEEP_UNAVAILABLE')
        targets = sorted({e['target_id'] for e in edges if e.get('acting_id') == rule['acting_id'] and e.get('mechanism') in ENDS})
        for target in targets:
            hits = [{'text_path':p, 'owner_hint':owner, 'date_hint':d, 'reason':'later use' if d else 'undated use'}
                    for p, ids, owner, d, _ in docs if target in ids and owner != rule['acting_id'] and (not d or d > (rule.get('effective_date') or ''))]
            cert = assess(rule, target, edges, own_texts[target], mentions[target], hits, errors)
            cert.update(sweep_manifest_sha256=sweep_hash, saved_texts_scanned=len(docs))
            evidence={'counterexamples':cert['counterexamples'],'current_law_hits':cert['current_law_hits']}
            evidence_rel=f"evidence/{rule['acting_id'].replace(':','_')}/{target.replace(':','_')}.json"
            write(out/evidence_rel,evidence)
            cert['counterexample_count']=len(cert['counterexamples'])
            cert['current_law_hit_count']=len(cert['current_law_hits'])
            cert['evidence_pointer']={'path':evidence_rel,'record_sha256':digest(canonical(evidence).encode())}
            cert['counterexamples']=cert['counterexamples'][:1]
            cert['current_law_hits']=[{'source_refs':x.get('source_refs',[])} for x in cert['current_law_hits'][:1]]
            certs.append(cert)
            fragments.append({'instrument_id':target,'kind':'family_rule_checks','produced_by':'family-rules','data':cert,'sources':[rule.get('source') or {}]})
            write(out/'certificates'/rule['acting_id'].replace(':','_')/(target.replace(':','_')+'.json'), cert)
            if cert['result'] == 'bounded_checks_passed':
                src = rule['source']; ref = {'url':src['url'],'sha256':src['sha256'],'page_or_item':src['page']}
                fragments.append({'instrument_id':target,'kind':'whole_order_end_candidates','produced_by':'family-rules',
                    'sources':[ref], 'confidence_note':'Source-reviewed family rule; bounded mechanical proof only. Agent review remains required.',
                    'data':[{'actor':rule['acting_id'],'mechanism':rule['mechanism'],'date_candidate':rule['effective_date'],
                             'source':ref,'quote':rule['quoted_clause'],'edge_ids':cert['edge_ids'],'flags':['family_rule_bounded_proof'],
                             'proof_certificate':f"certificates/{rule['acting_id'].replace(':','_')}/{target.replace(':','_')}.json",'status':'CANDIDATE_UNVERIFIED'}]})
    out.mkdir(parents=True, exist_ok=True)
    (out/'FRAGMENTS.jsonl').write_text(''.join(canonical(f)+'\n' for f in fragments), encoding='utf-8', newline='\n')
    write(out/'SWEEP_MANIFEST.json', manifest)
    write(out/'SUMMARY.json', {'job':'family-rules','rules':len(rules),'targets':len(certs),'bounded_checks_passed':sum(c['result']=='bounded_checks_passed' for c in certs),
          'blocked':sum(c['result']=='blocked' for c in certs),'saved_texts_scanned':len(docs),'sweep_manifest_sha256':sweep_hash,
          'blockers':dict(sorted(collections.Counter(b for c in certs for b in c['blockers']).items()))})
    try:
        import tiktoken
        enc=tiktoken.get_encoding('cl100k_base')
        tokens=lambda obj:len(enc.encode(canonical(obj),disallowed_special=()))
        metrics=[]
        for rule in rules:
            cs=[c for c in certs if c['acting_id']==rule['acting_id']]
            src=rule.get('source',{})
            try:text=child(root,src['text_path']).read_text(encoding='utf-8')
            except (KeyError,OSError,ValueError):text=None
            source_tokens=len(enc.encode(text,disallowed_special=())) if text else None
            cert_tokens=sum(tokens(c) for c in cs)
            metrics.append({'acting_id':rule['acting_id'],'targets':len(cs), 'source_tokens':source_tokens,
                'per_order_repeated_source_tokens':None if source_tokens is None else len(cs)*source_tokens,
                'one_family_source_and_all_certificate_tokens':None if source_tokens is None else source_tokens+cert_tokens,
                'certificate_tokens':cert_tokens,
                'measured_input_tokens_saved':None if source_tokens is None else (len(cs)-1)*source_tokens-cert_tokens})
        write(out/'METRICS.json',{'tokenizer':'cl100k_base','comparison':'Repeated acting-source input per target versus reading it once plus every generated proof certificate. Excludes follow-up evidence retrieval, model reasoning and tool wrappers; blocked certificates remain blocked.','families':metrics})
    except ImportError:
        write(out/'METRICS.json',{'tokenizer':'unavailable','tokens_measured':False})
    return certs
