"""NEYMAN: finite inventory survey. No legal decisions, allocator or savings score."""
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random

PHASES = ('preparation','acquisition','production','review','correction','coordination','integration')
TOKEN_CATEGORIES = ('input_uncached','cache_read','cache_write','output','reasoning')
OUTCOMES = {
    'complete': 'Full attempt through review, corrections and integration; all required evidence checked.',
    'blocked_prerequisite': 'Attempt stopped with missing research prerequisites; no completed dossier claimed.',
    'blocked_access': 'Attempt stopped at an unresolved access dependency; effort is not zero.',
    'censored_limit': 'Attempt reached its prospective limit; incomplete right-censored observation.',
    'incomplete_capability': 'Available execution cannot perform/measure remaining legal or review work.',
    'unsuccessful': 'Attempt ended without a usable result; effort remains in denominator.'}
CENSUS = 'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv'
TRACKER = 'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv'


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def write(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


def lines(path, rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None


def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def pins(root):
    """Pin complete consumed metadata membership, including absent optional inputs."""
    root=Path(root)
    tracker=load('neyman_pin_tracker',root/'jobs/readiness-tracker/tracker.py')
    exact={CENSUS,TRACKER,'jobs/readiness-tracker/output/SUMMARY.json',
           'jobs/readiness-tracker/tracker.py','jobs/llull/llull.py','jobs/junto/config.json',
           'jobs/claim-kit/output/INDEX.json','jobs/claim-kit/output/FAMILIES.json',
           'jobs/claim-kit/output/STATUS_LEADS.jsonl','jobs/source-ladder/output/RESULTS.csv',
           'jobs/status-history/output/INDEX.json','jobs/current-law/output/ORDERS_CURRENT_LAW.csv'}
    for val in tracker.P.values():
        if '*' not in val and val!=tracker.P['claim_gate_dir']:exact.add(val)
    for val in tracker.J.values():exact.update([val] if isinstance(val,str) else val)
    exact.add('research/readiness/SOURCE_AUDIT_HOLDS.jsonl')
    patterns=['research/readiness/claims/*.jsonl',
              'jobs/claim-kit/output/ACTING_PROVISIONS*.jsonl','jobs/claim-kit/output/OWN_TERMS*.jsonl',
              'research/stage19/code/*.py','jobs/neyman/*.py','jobs/neyman/config.json',
              'jobs/corpus-excavator/combinations.py','jobs/corpus-excavator/measure.py',
              'jobs/claim-kit/*.py','jobs/junto/finders/neyman.py','jobs/junto/contracts.py']
    holds=root/'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
    if holds.is_file():
        for line in holds.read_text().splitlines():
            if line.strip():exact.add(json.loads(line)['review_path'])
    for pattern in patterns:
        exact.update(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())
    return {p:sha(root/p) for p in sorted(exact)}


def verify_manifest(manifest):
    value=dict(manifest);expected=value.pop('manifest_sha256')
    actual=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    if actual!=expected:raise ValueError('frozen manifest content changed')
    if value['outcome_definitions']!=OUTCOMES:raise ValueError('outcome definitions changed')
    if len({s['instrument_id'] for s in value['sample']})!=len(value['sample']):raise ValueError('duplicate sample')
    if not 1<=len(value['sample'])<=24:raise ValueError('invalid sample bound')
    if not all(0<s['inclusion_probability']<=1 for s in value['sample']):raise ValueError('invalid inclusion probability')


def check_pins(root, expected):
    current=pins(root)
    if current!=expected:
        changed=sorted(k for k in set(current)|set(expected) if current.get(k)!=expected.get(k))
        raise ValueError('stale sampling inputs: '+', '.join(changed[:12]))


def era(date):
    try:y=int(date[:4])
    except (ValueError,TypeError):return 'undated'
    for end,name in [(1861,'1789-1861'),(1906,'1862-1906'),(1936,'1907-1936'),(1989,'1937-1989'),(2026,'1990-2026')]:
        if y<=end:return name
    return 'post_cutoff_year'


def frame(root):
    root=Path(root); llull=load('neyman_llull',root/'jobs/llull/llull.py');d=llull.Data(root)
    census_rows=[r for r in csv_rows(root/CENSUS) if r['included_in_bibliography']=='1']
    census={r['id']:r for r in census_rows};rows=d.tracker()
    if len(census)!=len(census_rows) or len({r['instrument_id'] for r in rows})!=len(rows) or set(census)!={r['instrument_id'] for r in rows}:
        raise ValueError('duplicate identities or tracker/census coverage mismatch')
    summary=json.loads((root/'jobs/readiness-tracker/output/SUMMARY.json').read_text())
    expected={'orders_total':len(rows),'ready_for_human_review':sum(r['ready_for_human_review']=='yes' for r in rows),
              'orders_with_provisional_status':sum(r['provisional_status'] in ('yes','no') for r in rows)}
    if any(summary[k]!=v for k,v in expected.items()):raise ValueError('tracker summary mismatch')
    memberships=defaultdict(set)
    for f in json.loads((root/'jobs/claim-kit/output/FAMILIES.json').read_text()):
        for iid in f['instrument_ids']:memberships[iid].add(f['family_id'])
    whole,named=d.acting();terms=d.term_end();current=d.current_leads()
    out=[]
    for r in sorted(rows,key=lambda r:r['instrument_id']):
        if r['ready_for_human_review']=='yes':continue
        iid=r['instrument_id'];status=r['provisional_status'] or 'unknown'
        # Held here means Llull's mechanical prerequisite, never a legally verified end.
        ending='held_candidate' if iid in whole|terms else ('lead' if iid in named else 'missing')
        cur='lead' if iid in current else 'missing'
        basis=('ending:'+ending,'current:'+cur,'tracker:'+r['step_ending_or_current_basis'])
        fam=tuple(sorted(memberships[iid])) or ('unknown_family',)
        dims=(era(census[iid].get('date_effective','')),status,r['step_original_text'],basis,fam)
        key=hashlib.sha256(json.dumps(dims).encode()).hexdigest()[:20]
        out.append({'instrument_id':iid,'era':dims[0],'provisional_status':status,
                    'original_text':dims[2],'basis_evidence':basis,'families':fam,'stratum':key,
                    'macro':dims[0]+'|'+status,'open_steps':[k[5:] for k,v in r.items() if k.startswith('step_') and v=='open'],
                    'blockers':r['blockers'].split('|') if r['blockers'] else []})
    return out,expected


def sample(rows, seed, n=24):
    """Macro strata: era x status. SRS detailed cells, then one SRS case per cell.

    Every nonempty joint cell has positive probability. Cell selection is not
    replaced by a product of marginal characteristics. Unsampled cells remain explicit.
    """
    if not 1<=n<=24:raise ValueError('initial sample must be 1..24')
    cells=defaultdict(list);macros=defaultdict(list)
    for r in rows:cells[r['stratum']].append(r)
    for key,rs in sorted(cells.items()):macros[rs[0]['macro']].append(key)
    if n<len(macros):raise ValueError('sample too small to cover era-status macro strata')
    allocation={g:1 for g in sorted(macros)}
    remaining=min(n,len(cells))-sum(allocation.values())
    while remaining:
        for g in allocation:
            if allocation[g]<len(macros[g]) and remaining:
                allocation[g]+=1;remaining-=1
    rng=random.Random(seed);selected=[]
    for g,k in allocation.items():
        h=len(macros[g])
        for cell in sorted(rng.sample(sorted(macros[g]),k)):
            rs=sorted(cells[cell],key=lambda r:r['instrument_id']);r=dict(rng.choice(rs))
            r.update(cell_population=len(rs),macro_cells=h,sampled_cells=k,
                     inclusion_probability=k/h/len(rs),weight=h*len(rs)/k)
            selected.append(r)
    return sorted(selected,key=lambda r:r['instrument_id']),allocation


def make_manifest(root, config):
    if not 0 < config['attempt_limit_seconds'] <= 30:
        raise ValueError('attempt limit must be positive and at most 30 seconds')
    if not 1 <= config['source_read_limit_bytes'] <= 1048576:
        raise ValueError('source reading bound must be 1..1048576 bytes')
    before=pins(root);rows,counts=frame(root);after=pins(root)
    if before!=after:raise ValueError('inputs changed while constructing frame')
    selected,allocation=sample(rows,config['seed'],config['attempts'])
    cfg=json.loads((Path(root)/'jobs/junto/config.json').read_text())
    allowance=cfg['round_budget_usd']*cfg['exploration_share']
    manifest={'schema':'neyman.manifest/1','seed':config['seed'],'input_hashes':before,
              'frame_population':len(rows),'inventory_counts':counts,'selection_design':'era-status macro strata; SRS joint cells; one SRS order per selected cell',
              'macro_allocation':allocation,'sample':selected,'outcome_definitions':OUTCOMES,
              'phases':PHASES,'token_categories':TOKEN_CATEGORIES,
              'attempt_limit_seconds':config['attempt_limit_seconds'],'pilot_scope':config['pilot_scope'],
              'exploration_allowance':{'source':'jobs/junto/config.json','round_budget_api_value_usd':cfg['round_budget_usd'],
                    'exploration_share':cfg['exploration_share'],'nominal_exploration_api_value_usd':allowance,
                    'allocation_to_neyman':None,'cash_budget':None,'metered_model_calls_allowed':0,
                    'note':'Existing allowance, not a new allocator. No model API calls in the job; session metering unavailable.'},
              'historical_samples_representative':False,'human_certification_boundary':'unchanged'}
    manifest['manifest_sha256']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    return rows,manifest


def validate_observations(manifest, observations, shared):
    sample_ids={r['instrument_id'] for r in manifest['sample']};seen=set();events={}
    for e in shared:
        if e['event_id'] in events:raise ValueError('duplicate shared event')
        if not set(e['downstream_uses'])<=sample_ids:raise ValueError('unknown shared use')
        events[e['event_id']]=e
    for o in observations:
        iid=o['instrument_id']
        if iid not in sample_ids or iid in seen:raise ValueError('duplicate/unsampled observation')
        seen.add(iid)
        if o['manifest_sha256']!=manifest['manifest_sha256']:raise ValueError('observation has stale manifest')
        if o['outcome'] not in OUTCOMES:raise ValueError('unfrozen outcome')
        if o['outcome']=='censored_limit' and not o.get('right_censored'):raise ValueError('lost censoring')
        if o['outcome']!='complete' and o.get('completion_effort_seconds') is not None:raise ValueError('incomplete completion value')
        if set(o['phases'])!=set(PHASES):raise ValueError('missing phase coverage')
        for phase in o['phases'].values():
            for k in ('active_seconds','access_wait_seconds','machine_seconds'):
                value=phase.get(k)
                if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value) or value<0):raise ValueError('invalid effort')
            if set(phase['tokens'])!=set(TOKEN_CATEGORIES):raise ValueError('missing token categories')
            if any(v is not None and (not isinstance(v,int) or v<0) for v in phase['tokens'].values()):raise ValueError('invalid tokens')
        for eid in o.get('shared_event_ids',[]):
            if eid not in events or iid not in events[eid]['downstream_uses']:raise ValueError('missing shared attribution')
    if seen!=sample_ids:raise ValueError('sample nonresponse must be recorded, not dropped')


def report(manifest, observations, shared):
    validate_observations(manifest,observations,shared)
    by_id={o['instrument_id']:o for o in observations}
    # Shared costs occur here exactly once. Never distribute then add the full event again.
    machine=sum(p.get('machine_seconds') or 0 for o in observations for p in o['phases'].values())+sum(e.get('machine_seconds') or 0 for e in shared)
    active_values=[p['active_seconds'] for o in observations for p in o['phases'].values()]
    active_values += [e.get('active_seconds') for e in shared]
    parent={i:i for i in by_id}
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    for e in shared:
        uses=e['downstream_uses']
        for iid in uses[1:]:parent[find(iid)]=find(uses[0])
    # A source/instrument shared across observations is a cluster even if no cost event was logged.
    resources=defaultdict(list)
    for o in observations:
        for key in o.get('correlation_keys',[]):resources[key].append(o['instrument_id'])
    for uses in resources.values():
        for iid in uses[1:]:parent[find(iid)]=find(uses[0])
    clusters=Counter(find(i) for i in parent)
    selected={s['stratum'] for s in manifest['sample']}
    total_cells=sum(s for s in {r['macro']:r['macro_cells'] for r in manifest['sample']}.values())
    return {'schema':'neyman.uncertainty/1','attempts':len(observations),'outcomes':dict(Counter(o['outcome'] for o in observations)),
            'known_inventory_unfinished':manifest['frame_population'],'joint_cells':total_cells,'observed_cells':len(selected),
            'completion_total_seconds':None,'completion_date':None,'confidence_interval':None,
            'observed_machine_seconds_lower_bound':machine,
            'observed_active_seconds_lower_bound':sum(v for v in active_values if v is not None),
            'active_phase_coverage':sum(v is not None for v in active_values),'active_phase_denominator':len(active_values),
            'token_category_coverage':{k:sum(p['tokens'][k] is not None for o in observations for p in o['phases'].values()) for k in TOKEN_CATEGORIES},
            'api_token_valuation_usd':None,'actual_cash_expenditure_usd':None,
            'shared_events_counted_once':len(shared),'correlation_components':sorted(clusters.values(),reverse=True),
            'uncertainty_method':'Withhold population completion estimate: incomplete/censored phases and unobserved joint cells; shared source/instrument costs form connected clusters, not independent case replicates.',
            'conditional_scenarios':{'formula':'sum over joint cells of population times assumed remaining active seconds per order, plus separately assumed future shared effort',
                'numeric_total':None,'requirements':['externally supplied per-cell completion assumptions','access dependencies resolved or separately timed','independent review and correction measured','future shared costs counted once'],
                'interpretation':'Conditional scenario, never a confidence interval or dollar saving.'},
            'unresolved_access_dependencies':sum(o['outcome']=='blocked_access' for o in observations),
            'human_review_effort':'unmeasured; outside machine readiness',
            'historical_census':'outside known inventory; incompletely bounded, excluded from survey weights and totals',
            'historical_convenience_samples':'planning information only; no representative observations imported'}
