"""Three deliberately narrow routes over held evidence; no network, no status writes."""
import collections
import csv
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlparse
from model import (CUTOFF, application_errors, canonical, evidence_errors, fingerprint,
                   question_key, review_errors, safe_path, sha, source_span)

REGISTRY = 'research/readiness/factual'
EVENT = re.compile(r'\b(report|submit|deliver|transmit|appoint|transfer|retain|abolish|perform|function|completion)\w*\b', re.I)
PERFORMANCE = re.compile(r'\b(submitted|delivered|transmitted|presented|published|issued|appointed|completed|performed|transferred|retained|abolished|approved|established)\b', re.I)
SUCCESSION = re.compile(r'\b(transferred|retained|abolished|modified|continued|except|excluding|remain)\b', re.I)

def rows(path):
    if not path.is_file():
        return
    with path.open(encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    v = json.loads(line)
                except ValueError as e:
                    raise ValueError(f'{path.name}:{n}: invalid JSON') from e
                if not isinstance(v, dict):
                    raise ValueError(f'{path.name}:{n}: expected object')
                yield n, v

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def write_rows(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for r in values:
            f.write(canonical(r) + '\n')

def load_panizzi(repo):
    path = repo / 'jobs/source-ladder/report_dates.py'
    spec = importlib.util.spec_from_file_location('norton_panizzi', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def origin(repo, path, n, row):
    return {'path': path.relative_to(repo).as_posix(), 'line': n, 'record_sha256': fingerprint(row)}

def extract_obligations(repo):
    """Keep uncertainty in identity. An unbound entity is NEVER merged across orders."""
    leads, counts = [], collections.Counter()
    base = repo / 'jobs/claim-kit/output'
    for path in sorted(base.glob('OWN_TERMS*.jsonl')):
        for n, r in rows(path):
            counts['own_term_records'] += 1
            text = r.get('text', '')
            if not EVENT.search(text):
                continue
            kind = r.get('kind')
            # Keep all raw report tags in the audit, including the military "report for" false positives.
            eligible = (kind in ('until_event', 'condition', 'report_deadline') and
                        bool(re.search(r'\b(?:report|recommendations?|findings)\b', text, re.I)) and
                        bool(re.search(r'\b(?:submit|transmit|deliver|make|present)\w*\b', text, re.I)))
            function = kind in ('condition', 'until_event') and bool(re.search(r'\b(?:function|duties|transfer|appoint)\w*\b', text, re.I))
            if not eligible and not function:
                counts['screened_out_event_tags'] += 1
                continue
            iid, scope = r.get('instrument_id'), r.get('scope_id')
            if not iid or not scope:
                counts['unscoped_obligations'] += 1
                continue
            q = {'entity_id': 'UNRESOLVED:' + iid + ':' + scope,
                 'object': text, 'scope': scope, 'interval_start': r.get('source', {}).get('signing_date') or '1789-01-01',
                 'interval_end': CUTOFF, 'proposition': 'Establish the actual event identified in this exact obligation.',
                 'event_kind': 'report_delivery' if eligible else 'function_succession'}
            try:
                key = question_key(q)
            except ValueError:
                counts['invalid_time_interval'] += 1
                continue
            leads.append(dict(q, question_key=key, instrument_id=iid, scope_id=scope, origin=origin(repo, path, n, r),
                              clause_evidence={k:r[k] for k in ('source','text','char_start','char_end') if k in r},
                              state='entity_binding_required', question_origin='machine_extracted'))
    # Claims and reviewer findings remain verbatim, attributed obligations until a person binds their dimensions.
    for folder in ('claims', 'reviews'):
        for path in sorted((repo / 'research/readiness' / folder).rglob('*.jsonl')):
            for n, r in rows(path):
                for key in ('unresolved_material_gaps', 'findings', 'reasons', 'reason', 'rationale'):
                    value = r.get(key, [])
                    values = value if isinstance(value, list) else [value]
                    for text in values:
                        if isinstance(text, str) and EVENT.search(text) and re.search(r'\b(?:missing|unresolved|unheld|unproved|unknown|needed|requires|no evidence)\b', text, re.I):
                            leads.append({'state':'dimensions_required', 'instrument_id':r.get('instrument_id'),
                                          'obligation':text, 'origin':origin(repo,path,n,r), 'question_origin':'machine_extracted'})
                            counts[folder + '_obligations'] += 1
    return leads, dict(counts)

def possible_duplicates(leads, limit=1000):
    """Review queue only. Buckets are deliberately bounded and never change exact keys."""
    buckets = collections.defaultdict(list)
    pairs, omitted = [], 0
    for r in leads:
        if not r.get('question_key'):
            continue
        tokens = sorted(set(re.findall(r'[a-z]{5,}', r['object'].lower())))
        anchor = tuple(tokens[:4])
        bucket = buckets[(r['event_kind'], anchor)]
        for other in bucket[:8]:
            if other['question_key'] != r['question_key']:
                if len(pairs) < limit:
                    pairs.append({'left':other['question_key'], 'right':r['question_key'],
                                  'state':'possible_duplicate_review_required',
                                  'warning':'Shared words do not establish shared entity, object, scope, interval or proposition.'})
                else:
                    omitted += 1
        if len(bucket) < 8:
            bucket.append(r)
        else:
            omitted += 1
    return pairs, omitted

def load_registry(repo):
    data = {k:[] for k in ('questions','applications','evidence','answers','reviews')}
    for kind in data:
        for p in sorted((repo / REGISTRY).glob('*/' + kind + '.jsonl')):
            for n, r in rows(p):
                data[kind].append(dict(r, _origin=origin(repo,p,n,r)))
    if len({r.get('instrument_id') for r in data['applications']}) > 12:
        raise ValueError('pilot_limit_exceeded: expansion requires a separately reviewed implementation change')
    return data

def clean(r):
    return {k:v for k,v in r.items() if not k.startswith('_')}

def pin_registry_sources(repo, value, pins):
    """Live fact/application source bytes must survive the consumer boundary."""
    if isinstance(value,dict):
        src=value.get('source')
        if isinstance(src,dict):
            for key in ('text_path','raw_path'):
                if src.get(key):
                    try:
                        p=safe_path(repo,src[key])
                        if p.is_file():pins[p.relative_to(repo).as_posix()]=sha(p.read_bytes())
                    except (OSError,ValueError):pass  # The record validator retains the source hold.
        for item in value.values():pin_registry_sources(repo,item,pins)
    elif isinstance(value,list):
        for item in value:pin_registry_sources(repo,item,pins)

def held_sources(repo, holds, pins, max_text_bytes=250_000_000):
    """Reuse source declarations. No raw-byte store or alternative acquisition path."""
    seen, total = set(), 0
    for path in sorted((repo / 'jobs').glob('*/output/SOURCES*.jsonl')):
        if path.parent.parent.name == 'norton':
            continue
        pins[path.relative_to(repo).as_posix()] = sha(path.read_bytes())
        status = path.parent / 'STATUS.json'
        if status.exists():
            pins[status.relative_to(repo).as_posix()] = sha(status.read_bytes())
        if status.exists() and json.loads(status.read_bytes()).get('result') != 'succeeded':
            holds.append({'source_manifest':path.relative_to(repo).as_posix(), 'reason':'upstream_run_not_succeeded'})
            continue
        for n, r in rows(path):
            raw = r.get('text_path')
            if not raw or '#' in raw:
                continue
            try:
                p = safe_path(repo, raw, repo if raw.startswith(('jobs/','research/')) else path.parent)
                if p.suffix.lower() not in ('.txt','.html','.htm','.xml'):
                    continue
                pair = (r.get('sha256'), p.relative_to(repo).as_posix())
                if pair in seen:
                    continue
                seen.add(pair)
                size = p.stat().st_size
                if size > 5_000_000 or total + size > max_text_bytes:
                    holds.append({'origin':origin(repo,path,n,r), 'reason':'held_text_scan_byte_bound', 'bytes':size})
                    continue
                raw_text = p.read_bytes(); total += size
                text = raw_text.decode('utf-8')
                if raw_text.startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError('lfs_pointer')
                digest = sha(raw_text)
                if r.get('text_sha256') and r['text_sha256'] != digest:
                    raise ValueError('text_hash_mismatch')
                src = dict(r, text_path=p.relative_to(repo).as_posix(), text_sha256=digest)
                cache = r.get('cache_path') or r.get('local_path')
                if cache:
                    cp = safe_path(repo,cache,repo if cache.startswith(('jobs/','research/')) else path.parent)
                    if cp.is_file():
                        src['raw_path'] = cp.relative_to(repo).as_posix()
                pins[src['text_path']] = digest
                yield src, text
            except (OSError, ValueError, UnicodeError) as e:
                holds.append({'origin':origin(repo,path,n,r), 'reason':'held_text_unavailable', 'detail':str(e)[:200]})

def aliases(repo, q):
    verified, holds = [], []
    panizzi = load_panizzi(repo)
    for a in q.get('aliases', []):
        if (not isinstance(a.get('text'), str) or len(a['text']) < 4 or
                a.get('entity_id') != q['entity_id'] or a.get('kind') not in ('institution','function','object') or
                source_span(repo, a.get('evidence', {})) or
                panizzi.norm_text(a.get('text','')) not in panizzi.norm_text(a.get('evidence',{}).get('text',''))):
            holds.append('unverified_alias:' + str(a.get('text')))
        else:
            verified.append(a)
    return verified, holds

def search_sources(repo, questions, sources):
    """Find exact alias + provision spans, including provisions with NO EO number."""
    panizzi = load_panizzi(repo)
    found, holds = [], []
    for q in questions:
        aa, errors = aliases(repo,q)
        holds.extend({'question_key':q['question_key'], 'reason':e} for e in errors)
        institutions = [a['text'] for a in aa if a['kind']=='institution']
        objects = [a['text'] for a in aa if a['kind'] in ('object','function')]
        if not institutions or not objects:
            holds.append({'question_key':q['question_key'], 'reason':'institution_and_object_alias_binding_required'})
            continue
        count = 0
        for src, text in sources:
            # Avoid paragraph parsing an entire source which has no relevant institution.
            normalized_source = panizzi.norm_text(text)
            if not (any(panizzi.norm_text(a) in normalized_source for a in institutions) and
                    any(panizzi.norm_text(a) in normalized_source for a in objects)):
                continue
            for m in re.finditer(r'[^\n]+(?:\n(?!\s*\n)[^\n]+)*',text):
                passage = m.group(0)
                if len(passage) > 12000:
                    continue
                normal = panizzi.norm_text(passage)
                if not (any(panizzi.norm_text(a) in normal for a in institutions) and
                        any(panizzi.norm_text(a) in normal for a in objects)):
                    continue
                route = 'function_succession' if q['event_kind']=='function_succession' else 'completion_receipt'
                action = SUCCESSION if route=='function_succession' else PERFORMANCE
                if not action.search(passage):
                    continue
                # Panizzi supplies date leads; no inferred receipt, effective date or currency.
                dates = panizzi.parse_dates(passage)
                observed = ('report_publication' if q['event_kind'].startswith('report_') and
                            re.search(r'\b(?:published|issued)\b', passage, re.I) else q['event_kind'])
                r = {'schema':'norton-candidate-evidence/v1', 'question_key':q['question_key'],
                     'entity_id':q['entity_id'], 'event_kind':observed, 'question_event_kind':q['event_kind'], 'route':route,
                     'source':src, 'text':passage, 'char_start':m.start(), 'char_end':m.end(),
                     'date_candidates':dates, 'date_meaning':'unreviewed', 'event_date':None,
                     'state':'machine_candidate', 'reviewer_type':None,
                     'qualifiers':re.findall(r'\b(?:except|excluding|subject to|in part|retained|until|unless)\b',passage,re.I),
                     'warning':'Identity, occurrence, edition, exceptions and gaps require review; a date line is not delivery or legal cessation.'}
                r['id'] = 'NE:' + fingerprint(r)
                found.append(r); count += 1
                if count >= 20:
                    holds.append({'question_key':q['question_key'],'reason':'candidate_bound_reached','limit':20})
                    break
            if count >= 20:
                break
        if count == 0:
            holds.append({'question_key':q['question_key'], 'reason':'no_held_alias_and_event_span',
                          'warning':'Not evidence of nonperformance or agency/duty cessation.'})
    return found, holds

def compile_reviews(repo, data, questions):
    qs = {q['question_key']:q for q in questions}
    by_review = collections.defaultdict(list)
    for r in data['reviews']:
        by_review[(r.get('record_kind'), r.get('record_id'))].append(clean(r))
    rejected, evidence, answers, apps = [], {}, {}, []
    duplicates = {kind:{key for key,n in collections.Counter(r.get('id') for r in data[kind]).items() if n>1}
                  for kind in ('evidence','answers','applications')}
    for r in data['evidence']:
        v=clean(r); q=qs.get(v.get('question_key'))
        errors=evidence_errors(repo,q,v) if q else ['unknown_question']
        if not v.get('id') or v.get('id') in duplicates['evidence']:errors.append('missing_or_duplicate_evidence_id')
        evidence[v.get('id')]=(v,errors)
        if errors:rejected.append({'record':v,'errors':errors,'origin':r['_origin']})
    for r in data['answers']:
        v=clean(r); q=qs.get(v.get('question_key')); errors=[]
        if v.get('schema')!='norton-factual-answer/v1':errors.append('wrong_answer_schema')
        if not isinstance(v.get('answer'),str) or len(v['answer'].strip())<40 or not v.get('producer'):
            errors.append('factual_answer_missing')
        if not v.get('id') or v.get('id') in duplicates['answers']:errors.append('missing_or_duplicate_answer_id')
        if not q:errors.append('unknown_question')
        if not v.get('evidence_ids'):errors.append('answer_without_evidence')
        for eid in v.get('evidence_ids',[]):
            ev, ee=evidence.get(eid,({},['unknown_evidence']))
            errors+=ee
            if ev.get('question_key') != v.get('question_key'):errors.append('answer_evidence_wrong_question')
        review=by_review.get(('answer',v.get('id')),[])
        if len(review)!=1:errors.append('missing_or_duplicate_answer_review')
        else:errors+=review_errors(repo,v,review[0],'answer')
        if not errors:
            answers[v['id']]=dict(v, factual_review_status='human_accepted' if review[0]['reviewer_type']=='independent_human' else 'ai_reviewed',
                                  reviewer_type=review[0]['reviewer_type'], review=review[0])
        else:rejected.append({'record':v,'errors':sorted(set(errors)),'origin':r['_origin']})
    for r in data['applications']:
        v=clean(r); q=qs.get(v.get('question_key'))
        errors=application_errors(repo,q,v) if q else ['unknown_question']
        if not v.get('id') or v.get('id') in duplicates['applications']:errors.append('missing_or_duplicate_application_id')
        if v.get('state') in ('ai_reviewed','human_accepted'):
            review=by_review.get(('application',v.get('id')),[])
            if len(review)!=1:errors.append('missing_or_duplicate_application_review')
            else:
                errors+=review_errors(repo,v,review[0],'application')
                if v['state']=='human_accepted' and review[0].get('reviewer_type')!='independent_human':errors.append('not_human_accepted')
            if v.get('answer_id') not in answers:errors.append('reviewed_answer_missing')
            elif answers[v['answer_id']].get('question_key') != v.get('question_key'):errors.append('application_answer_wrong_question')
        elif v.get('state')!='candidate':errors.append('unknown_application_state')
        if errors:rejected.append({'record':v,'errors':sorted(set(errors)),'origin':r['_origin']})
        else:apps.append(v)
    return answers, apps, rejected

def build(repo,out):
    started=time.monotonic();repo=Path(repo).resolve();out=Path(out).resolve()
    code_hashes={p.name:sha(p.read_bytes()) for p in Path(__file__).parent.glob('*.py')}
    if out==repo or not out.is_relative_to(repo):raise ValueError('OUTPUT_DIR must be inside repository')
    out.mkdir(parents=True,exist_ok=True)
    pins={};holds=[]; data=load_registry(repo)
    pin_registry_sources(repo,data,pins)
    for folder in ('claims','reviews'):
        for p in (repo/'research/readiness'/folder).rglob('*.jsonl'):
            pins[p.relative_to(repo).as_posix()]=sha(p.read_bytes())
    for name in ('report_dates.py','ladder_queue.py','fetch_ladder.py','embedded_cites.py'):
        p=repo/'jobs/source-ladder'/name
        pins[p.relative_to(repo).as_posix()]=sha(p.read_bytes())
    for p in sorted((repo/REGISTRY).rglob('*.jsonl')):
        pins[p.relative_to(repo).as_posix()]=sha(p.read_bytes())
    leads,counts=extract_obligations(repo)
    for p in (repo/'jobs/claim-kit/output').glob('OWN_TERMS*.jsonl'):
        pins[p.relative_to(repo).as_posix()]=sha(p.read_bytes())
    questions=[];seen=set()
    for r in data['questions']:
        q=clean(r)
        try:
            key=question_key(q)
            if key in seen:raise ValueError('duplicate_question_definition')
            if q.get('question_key',key)!=key:raise ValueError('question_key_mismatch')
            if q.get('origin') not in ('owner_seeded','machine_extracted'):raise ValueError('question_origin_required')
            seen.add(key);questions.append(dict(q,question_key=key))
        except ValueError as e:holds.append({'origin':r['_origin'],'reason':str(e)})
    possible,omitted=possible_duplicates(leads)
    sources=list(held_sources(repo,holds,pins))
    candidates,route_holds=search_sources(repo,questions,sources);holds+=route_holds
    answers,applications,rejected=compile_reviews(repo,data,questions)
    census=repo/'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv'
    pins[census.relative_to(repo).as_posix()]=sha(census.read_bytes())
    with census.open(encoding='utf-8',newline='') as f:
        known_ids={r.get('id') or r.get('instrument_id') for r in csv.DictReader(f)
                   if r.get('included_in_bibliography','1')=='1'}
    outside=[a for a in applications if a['instrument_id'] not in known_ids]
    rejected.extend({'record':a,'errors':['outside_known_inventory']} for a in outside)
    applications=[a for a in applications if a['instrument_id'] in known_ids]
    groups=collections.defaultdict(set)
    for a in applications:groups[a['question_key']].add((a['instrument_id'],a['scope_id']))
    reused={k:len(v) for k,v in groups.items() if len(v)>1}
    unique=collections.defaultdict(set)
    for r in leads:
        if r.get('question_key'):unique[r['question_key']].add((r['instrument_id'],r['scope_id']))
    summary={'schema':'norton-census/v1','legal_cutoff':CUTOFF,'counts':dict(counts,
        extracted_obligations=len(leads),distinct_unbound_exact_questions=len(unique),
        unbound_questions_repeated_across_applications=sum(len(v)>1 for v in unique.values()),
        registered_questions=len(questions),valid_candidate_applications=len(applications),
        exact_reusable_questions=len(reused),applications_of_reusable_questions=sum(reused.values()),
        held_source_texts_scanned=len(sources),candidate_evidence=len(candidates),reviewed_answers=len(answers),
        reviewed_applications=sum(a.get('state') in ('ai_reviewed','human_accepted') for a in applications),
        rejected_records=len(rejected),source_and_route_holds=len(holds)),
        'questions':[{'question_key':q['question_key'],'event_kind':q['event_kind'],'clause_investigations':len(groups[q['question_key']]),
                      'orders':sorted({i for i,s in groups[q['question_key']]})} for q in questions],
        'possible_duplicate_limit':1000,'possible_duplicate_omitted':omitted,
        'additional_integrated_ready_cases':0,'verified_savings':False,
        'notice':'Known inventory only. Unbound wording groups are not proven reusable facts. No lifecycle authority, readiness promotion or historical census estimate.'}
    fragments=[]
    for a in applications:
        answer=answers.get(a.get('answer_id')) if a.get('state') in ('ai_reviewed','human_accepted') else None
        fragments.append({'instrument_id':a['instrument_id'],'kind':'shared_factual_obligations',
                          'data':{'application':a,'question':next(q for q in questions if q['question_key']==a['question_key']),
                                  'reviewed_answer':answer, 'candidate_evidence_ids':[c['id'] for c in candidates if c['question_key']==a['question_key']],
                                  'registry_path':REGISTRY,'legal_effect':'unresolved',
                                  'factual_review_status':a['state'],'machine_lead':True}})
    for name,rs in [('QUESTION_LEADS',leads),('QUESTIONS',questions),('POSSIBLE_DUPLICATES',possible),('CANDIDATE_EVIDENCE',candidates),
                    ('REVIEWED_ANSWERS',list(answers.values())),('APPLICATIONS',applications),('REJECTIONS',rejected),('HOLDS',holds),('FRAGMENTS',fragments)]:
        write_rows(out/(name+'.jsonl'),rs)
    # Missing evidence requests are validated with the SAME queue reader; job never appends durable requests.
    requests=[]
    for q in questions:
        if not any(a['question_key']==q['question_key'] for a in answers.values()):
            dependent_orders=sorted({a['instrument_id'] for a in applications if a['question_key']==q['question_key']})
            if dependent_orders:
                requests.append({'instrument_id':dependent_orders[0],'citation':q.get('source_request') or q['proposition'],
                                 'step':'ending_or_current_basis','requested_by':'sol-norton',
                                 'note':'Exact factual question '+q['question_key']+'; dependent orders '+', '.join(dependent_orders)+'; one request per question. Do not substitute deadline, agency name, or current edition.'})
    queue=out/'FETCH_QUEUE_PROPOSED.jsonl';write_rows(queue,requests)
    import sys
    ladder=str(repo/'jobs/source-ladder')
    if ladder not in sys.path:sys.path.insert(0,ladder)
    from ladder_queue import read_fetch_queue
    wanted,errors=read_fetch_queue(queue)
    if errors:raise ValueError('source_ladder_queue_validation:'+canonical(errors))
    write_json(out/'QUEUE_VALIDATION.json',{'requests':len(requests),'validated_wanted_items':len(wanted),'errors':errors,'durable_submission':'coordinator append required'})
    write_json(out/'CENSUS.json',summary)
    reviewed_groups=collections.defaultdict(set)
    for a in applications:
        if a.get('state') in ('ai_reviewed','human_accepted'):
            reviewed_groups[a['question_key']].add((a['instrument_id'],a['scope_id']))
    reviewed_reuse=sum(len(v)>=2 for v in reviewed_groups.values())
    write_json(out/'FEASIBILITY.json',{'independently_reviewed_reused_answers':reviewed_reuse,
        'reviewed_distinct_applications':sum(len(v) for v in reviewed_groups.values()),
        'materially_improved_dossiers':len({iid for values in reviewed_groups.values() for iid,scope in values}),
        'feasibility_passed':reviewed_reuse>=1,'expansion_allowed':False,
        'full_cost_comparison':'unmeasured','additional_integrated_ready_cases':0,
        'reason':'No automatic expansion. Independently reviewed reuse and full matched integration cost evidence are required.'})
    if code_hashes != {p.name:sha(p.read_bytes()) for p in Path(__file__).parent.glob('*.py')}:
        raise ValueError('compiler_changed_during_run')
    # claim-kit clears its old output before consuming factual fragments. Its
    # previous own-term generation is a census input, not the source of a reviewed
    # fact. Retain that snapshot's hashes without creating a circular live-file
    # dependency; registry, primary text, source manifests and compiler remain live.
    lagged={k:v for k,v in pins.items() if k.startswith('jobs/claim-kit/output/OWN_TERMS')}
    write_json(out/'INPUTS.json',{'input_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
                                'sha256':pins,'lagged_census_sha256':lagged,
                                'consumer_sha256':{k:v for k,v in pins.items() if k not in lagged},'code_sha256':code_hashes})
    write_json(out/'METRICS.json',{'wall_seconds':time.monotonic()-started,'model_tokens':None,'cost_usd':None,'independent_review_seconds':None})
    print(canonical(summary['counts']))
    return summary
