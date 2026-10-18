"""Readiness-aware source planning and historical intake; no legal decisions.

Consumes claim-kit rather than assembling another dossier. All lower bounds on
new readiness are zero until the real checker/tracker have run.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'jobs/source-ladder'))
from plan import queue_fingerprint, queue_inputs, opportunity, rank_actions
import ladder_queue

CUTOFF = '2026-10-14'
STEPS = ('provisional_status', 'original_text', 'clause_inventory',
         'ending_or_current_basis', 'savings_residuals', 'counterevidence',
         'shared_sources', 'opus_media')
CENSUS = 'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv'
TRACKER = 'jobs/readiness-tracker/output/READINESS_BY_ORDER.csv'


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2)+'\n').encode())


def write_lines(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as fh:
        for row in rows:
            fh.write(canonical(row)+'\n')


class Inputs:
    def __init__(self, root):
        self.root = root.resolve()
        self.hashes = {}
        self.problems = []

    def raw(self, rel, required=False):
        path = (self.root/rel).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError('unsafe input path')
        if not path.is_file():
            self.hashes[rel] = None
            if required:
                raise ValueError('required input missing: '+rel)
            self.problems.append('missing: '+rel)
            return None
        raw = path.read_bytes()
        self.hashes[rel] = digest(raw)
        return raw

    def js(self, rel, default=None, required=False):
        raw = self.raw(rel, required)
        return json.loads(raw) if raw is not None else default

    def csv(self, rel, required=False):
        raw = self.raw(rel, required)
        return list(csv.DictReader(raw.decode('utf-8-sig').splitlines())) if raw is not None else []

    def lines(self, rel):
        raw = self.raw(rel)
        return [json.loads(s) for s in raw.decode('utf-8-sig').splitlines() if s.strip()] if raw else []


def open_steps(row):
    return [s for s in STEPS if row.get('step_'+s) == 'open']


def source_type(source):
    url = source.get('url', '').lower()
    if 'govinfo.gov' in url:
        return 'official_govinfo'
    if 'archives.gov' in url or 'loc.gov' in url or 'gpo.gov' in url:
        return 'official_archive_or_compilation'
    if 'presidency.ucsb.edu' in url or 'wikisource' in url or 'gutenberg' in url:
        return 'derivative_or_mirror'
    return 'other_attributed' if url else 'no_located_source'


def era(row):
    # This inherited census field can be only a year. Never use it as a legal
    # effective date; it is used for historical workload stratification only.
    match = re.match(r'(\d{4})', row.get('date_effective', ''))
    if not match:
        return 'undated'
    year = int(match[1])
    for last, label in [(1861, '1789-1861'), (1906, '1862-1906'),
                        (1936, '1907-1936'), (1989, '1937-1989'), (2026, '1990-2026')]:
        if year <= last:
            return label
    return 'post_cutoff_year'



def build(root, out, limit=12):
    t0 = time.monotonic()
    if not 1 <= limit <= 50:
        raise ValueError('source limit must be 1..50')
    inp = Inputs(root)
    census = {r['id']: r for r in inp.csv(CENSUS, True) if r['included_in_bibliography'] == '1'}
    rows = {r['instrument_id']: r for r in inp.csv(TRACKER, True)}
    if set(census) != set(rows) or len(rows) > 20000:
        raise ValueError('tracker/census identity mismatch or corpus bound exceeded')
    summary = inp.js('jobs/readiness-tracker/output/SUMMARY.json', required=True)
    actual = {'orders_total': len(rows), 'orders_with_provisional_status': sum(r['step_provisional_status']=='done' for r in rows.values()),
              'ready_for_human_review': sum(r['ready_for_human_review']=='yes' for r in rows.values())}
    if any(summary[k] != v for k, v in actual.items()):
        raise ValueError('committed tracker summary disagrees with rows')
    index = inp.js('jobs/claim-kit/output/INDEX.json', [], True)
    kit = {r['instrument_id']: r for r in index}
    families = inp.js('jobs/claim-kit/output/FAMILIES.json', [], True)
    kit_summary = inp.js('jobs/claim-kit/output/SUMMARY.json', {}, True)
    memberships = defaultdict(set)
    for f in families:
        for iid in f['instrument_ids']:
            memberships[iid].add(f['family_id'])
    for lead in inp.lines('jobs/claim-kit/output/STATUS_LEADS.jsonl'):
        iid=lead['instrument_id']
        memberships[iid].update('actor:'+actor for actor in lead.get('lead_actor_ids',[]))
        memberships[iid].update('own_term:'+term['kind'] for term in lead.get('own_terms',[]) if isinstance(term,dict) and term.get('kind'))
    # One lightweight source attribution per identity; evidence stays with its
    # original producer and the kit. Distinct representations remain visible.
    sources = defaultdict(set)
    for job, folder in [('fr-originals','data/full_run'), ('fr-originals','output'),
                        ('ofr-compilations','output'), ('isthmian-canal-1911','output'),
                        ('indian-reservations-1912','output'), ('richardson-volumes','output')]:
        rel = f'jobs/{job}/{folder}/FRAGMENTS.jsonl'
        for f in inp.lines(rel):
            if f.get('kind') == 'original_representation' and f.get('instrument_id') in rows:
                for s in f.get('sources', []):
                    sources[f['instrument_id']].add('compiled_transcription_lead' if job=='richardson-volumes' else source_type(s))
    profile = Counter()
    order_rows = []
    for iid, r in sorted(rows.items()):
        # Families overlap and must never be added to form a corpus total.
        mechanisms = sorted(m for m in memberships[iid] if m.startswith(('actor:', 'own_term:'))) or ['no_surfaced_mechanism']
        types = sorted(sources[iid]) or ['no_located_source']
        opens = open_steps(r)
        for mech in mechanisms:
            for st in types:
                for step in opens:
                    profile[(era(census[iid]), mech, st, step)] += 1
        order_rows.append({'instrument_id': iid, 'era': era(census[iid]), 'date_value': census[iid].get('date_effective'),
                           'date_meaning': 'inherited census dating for stratification, not legal effect',
                           'source_types': types, 'open_steps': opens, 'blockers': r['blockers'].split('|') if r['blockers'] else [],
                           'ready_for_human_review': r['ready_for_human_review'],
                           'kit_dossier': ('jobs/claim-kit/output/'+kit[iid]['dossier']) if iid in kit else None,
                           'dossier_sha256': kit.get(iid, {}).get('fingerprint'),
                           'next_action': 'claim-kit dossier and source review' if iid in kit else 'claim-kit STATUS_LEADS.jsonl; establish provisional evidence without changing status'})
    # Use precisely the ladder's queue constructors; URLs and hashes are not
    # reinvented in this job. Date/routing metadata lives in the input manifest.
    items, queue_problems = queue_inputs(root)
    for rel in ('research/readiness/FETCH_QUEUE.jsonl', ladder_queue.SHARED,
                ladder_queue.STATUTE, ladder_queue.STATUTE_INDEX, ladder_queue.HINTS,
                ladder_queue.OPUS_REFETCH):
        inp.raw(rel)
    prior = inp.csv('jobs/source-ladder/output/RESULTS.csv')
    receipts = inp.lines('jobs/source-ladder/output/SOURCES.jsonl')
    found = {r['wanted_id'] for r in receipts if r.get('sha256') and r.get('matches_expected_sha256') is not False}
    actions = rank_actions([opportunity(w, rows, found) for w in items])
    # A media step can require several distinct files. Credit only orders whose
    # whole remaining media requirement fits in the proposed batch.
    selected = [a for a in actions if a['potential_step_completions']][:limit]
    selected_ids = {a['wanted_id'] for a in selected}
    media_needs = defaultdict(set)
    for w in items:
        if w.wanted_id.startswith('opus-refetch:') and w.wanted_id not in found:
            for iid in w.instrument_ids:
                media_needs[iid].add(w.wanted_id)
    ceiling = {iid for a in selected for iid in a['near_ready_order_ids']
               if a['step'] != 'opus_media' or media_needs[iid] <= selected_ids}
    failures = [r for r in prior if r['result'] not in ('found',)]
    discovery = discover(inp, census)
    statuses = {}
    for job in ('readiness-tracker','claim-kit','source-ladder','census-candidates','ofr-codification-1989'):
        statuses[job] = inp.js(f'jobs/{job}/output/STATUS.json', {})
        if statuses[job].get('result') != 'succeeded':
            inp.problems.append('upstream job not successful: '+job)
    code = {str(p.relative_to(root)).replace('\\','/'): digest(p.read_bytes()) for p in
            [Path(__file__), root/'jobs/source-ladder/plan.py', root/'jobs/source-ladder/ladder_queue.py']}
    manifest = {'inputs': dict(sorted(inp.hashes.items())), 'code': code, 'source_limit': limit}
    fingerprint = digest(canonical(manifest).encode())
    out.mkdir(parents=True, exist_ok=True)
    write_json(out/'INPUTS.json', dict(manifest, fingerprint=fingerprint))
    write_lines(out/'ORDER_FRONTIER.jsonl', order_rows)
    write_lines(out/'BOTTLENECKS.jsonl', [dict(zip(('era','mechanism_family','source_type','blocked_step','identities'), (*k,v))) for k,v in sorted(profile.items())])
    write_lines(out/'SOURCE_ACTIONS.jsonl', actions)
    write_lines(out/'DISCOVERY.jsonl', discovery)
    write_json(out/'UPSTREAM_STATUS.json', statuses)
    write_lines(out/'UNRESOLVED_RETRIEVALS.jsonl', failures)
    plan = {'schema': 'eo-source-plan/v1', 'legal_cutoff': CUTOFF,
            'queue_fingerprint': queue_fingerprint(items), 'input_fingerprint': fingerprint,
            'wanted_ids': [a['wanted_id'] for a in selected], 'max_requests': 80,
            'ready_ceiling_order_ids': sorted(ceiling), 'ready_lower_bound': 0}
    write_json(out/'SOURCE_PLAN.json', plan)
    family_rows = []
    for f in families:
        ids = [i for i in f['instrument_ids'] if i in rows and rows[i]['ready_for_human_review'] != 'yes']
        family_rows.append({'family_id':f['family_id'], 'members_not_ready':len(ids),
           'original_step_done':sum(rows[i]['step_original_text']=='done' for i in ids),
           'remaining_step_tasks':sum(len(open_steps(rows[i])) for i in ids),
           'per_target_clause_exception_checks_required':len(ids), 'ready_lower_bound':0,
           'next_action':'consume claim-kit evidence; review each target; family membership is not an unlock'})
    write_lines(out/'FAMILY_WORK.jsonl', sorted(family_rows,key=lambda r:(r['remaining_step_tasks'],r['family_id'])))
    report = {'schema':'eo-excavator-baseline/v1', **actual, 'without_provisional_status':len(rows)-actual['orders_with_provisional_status'],
       'legal_cutoff':CUTOFF,'input_fingerprint':fingerprint,'blocked_by_step':dict(Counter(s for r in rows.values() for s in open_steps(r))),
       'near_complete_orders':[r for r in order_rows if len(r['open_steps'])==1],
       'source_plan_items':len(selected),'source_plan_potential_step_memberships':sum(a['potential_step_completions'] for a in selected),
       'source_plan_readiness_ceiling':len(ceiling),'source_plan_ready_lower_bound':0,
       'discovery_records_outside_census':len(discovery),'discovery_by_kind':dict(Counter(r['kind'] for r in discovery)),
       'newly_authenticated_identities':0,'new_census_admissions':0,
       'kit_input_warning_count':len(kit_summary.get('warnings',[])), 'queue_problems':queue_problems,
       'input_problems':inp.problems,'billed_tokens':None,'agent_minutes':None,'reviewer_minutes':None,
       'cost_per_correctly_advanced_order':None,'corpus_scale_cost':None,
       'limits':['Profile mechanism/source groups overlap; use ORDER_FRONTIER for disjoint counts.',
                 'Source opportunity is not legal readiness; multiple-file and other blockers remain.',
                 'No billed usage, full-agent timing, reviewer rate or corpus-scale cost inferred from payloads.',
                 'Successful upstream status does not establish freshness; exact committed inputs are fingerprinted.']}
    write_json(out/'BASELINE.json', report)
    lines = ['# Excavator baseline and next work', '', f"Legal cutoff: {CUTOFF}. Inputs: `{fingerprint}`.", '',
             f"Verified committed tracker: {len(rows):,} identities; {report['without_provisional_status']:,} undecided; {actual['ready_for_human_review']} ready for human review.", '',
             '## Ranked bounded source pass', '', '| Rank | Source queue item | Open step memberships | Other step tasks left |', '|---:|---|---:|---:|']
    lines += [f"| {n} | {a['wanted_id']} | {a['potential_step_completions']} | {a['remaining_step_tasks']} |" for n,a in enumerate(selected,1)]
    lines += ['',f"Readiness ceiling if the entire pass succeeds: {len(ceiling)}; demonstrated readiness gain before execution: 0.",
              '', 'Use SOURCE_PLAN.json with source-ladder JOB_PLAN_FILE. It contains existing queued requests only.',
              'All per-order remaining work is in ORDER_FRONTIER.jsonl. Claim-kit owns dossiers, decisions and assembly.',
              f"Historical discovery: {len(discovery)} witness/candidate/gap records outside the census, zero authenticated identities or admissions. Source pointers and next decisions are in DISCOVERY.jsonl.",
              'Read UPSTREAM_STATUS and UNRESOLVED_RETRIEVALS before reuse. Retrieval failure never means search exhaustion.']
    (out/'REPORT.md').write_bytes(('\n'.join(lines)+'\n').encode())
    write_json(out/'METRICS.json', {'runner_seconds':round(time.monotonic()-t0,4),
               'billed_input_tokens':None,'cached_input_tokens':None,'output_tokens':None,'reasoning_tokens':None})
    return report


def discover(inp, census):
    """Exact number joins only. Date-only historical identity matches are forbidden."""
    output = []
    provenance=inp.js('jobs/ofr-codification-1989/data/PROVENANCE.json',{})
    book=provenance.get('book',{})
    custody={k:book.get(k) for k in ('handle_url','pdf','pdf_sha256','text','text_sha256','supplied')}
    rel = 'jobs/ofr-codification-1989/output/DISPOSITION_1989.csv'
    for n,r in enumerate(inp.csv(rel),2):
        key = r.get('key','')
        iid = key if key.startswith('EO:') else None
        # Producer keys are eo:NUMBER (or date:...). Preserve suffixes exactly.
        if key.startswith('eo:'):
            iid = 'EO:'+key[3:]
        if iid and iid not in census:
            output.append({'candidate_id':iid,'kind':'numbered_editorial_witness','source_path':rel,'line':n,
               'source_record_sha256':digest(canonical(r).encode()),'raw':r,'source_custody':custody,'confidence':r.get('pairing_confidence'),
               'next_action':'authenticate numbered identity and official original; reconcile exact census form; no automatic admission',
               'date_meaning':'editorial observation as of 1989-01-20; never a present legal finding'})
        elif key.startswith('date:') and r.get('in_census') != 'yes':
            output.append({'candidate_id':'OFR1989:row:'+r['seq'],'kind':'unnumbered_editorial_witness',
               'source_path':rel,'line':n,'source_record_sha256':digest(canonical(r).encode()),'raw':r,'source_custody':custody,
               'confidence':r.get('pairing_confidence'),'next_action':'inspect source page, signer, scope and codebook inclusion; date alone cannot merge identities',
               'date_meaning':'historical date printed in an editorial table; legal effect unproved'})
    # Ordinary numbered holes are gaps, not recovered identities.
    nums={int(i[3:]) for i in census if re.fullmatch(r'EO:\d+',i)}
    for number in range(min(nums, default=1),max(nums, default=0)+1):
        if number not in nums:
            output.append({'candidate_id':'SERIES-GAP:'+str(number),'kind':'numbered_series_gap',
               'source_path':CENSUS,'confidence':'gap only; numbering may be unused or require a suffix',
               'next_action':'reconcile official numbered-series indexes and suffixes; request original if a witness exists'})
    for n,r in enumerate(inp.lines('jobs/census-candidates/output/ITEM_CANDIDATES.jsonl'),1):
        output.append({'candidate_id':r['candidate_id'],'kind':'historical_catalog_candidate',
             'source_path':'jobs/census-candidates/output/ITEM_CANDIDATES.jsonl','line':n,
             'source_record_sha256':digest(canonical(r).encode()),'raw':r,'confidence':r.get('grade'),
             'next_action':'compare retained original pages/transcript, establish presidential directive and codebook inclusion; do not admit catalog hits'})
    by_key=defaultdict(list)
    for r in output:
        if r['kind']=='unnumbered_editorial_witness':by_key[r['raw']['key']].append(r['candidate_id'])
    for r in output:
        if r['kind']=='unnumbered_editorial_witness':
            r['possible_duplicate_witnesses']=[i for i in by_key[r['raw']['key']] if i!=r['candidate_id']]
            r['identity_merge_performed']=False
    return sorted(output,key=lambda r:(r['kind'],r['candidate_id']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=ROOT)
    p.add_argument('--out',type=Path,default=HERE/'output')
    p.add_argument('--limit',type=int,default=12)
    a=p.parse_args(); root=a.repo.resolve(); out=a.out.resolve()
    if not out.is_relative_to(root/'jobs/corpus-excavator/output'):
        raise ValueError('job writes only jobs/corpus-excavator/output')
    try:
        result=build(root,out,a.limit)
        print(canonical({k:result[k] for k in ('orders_total','ready_for_human_review','source_plan_items','source_plan_readiness_ceiling')}))
    except Exception as exc:
        write_json(out/'FAILED.json',{'error':type(exc).__name__+': '+str(exc),'stale_outputs_must_not_be_used':True})
        raise
    (out/'FAILED.json').unlink(missing_ok=True)


if __name__=='__main__':
    main()
