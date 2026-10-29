"""Bounded campaign analysis; joins existing outputs, makes no research decisions."""
import csv
import gzip
import io
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PINS = {}


def read(path):
    p = ROOT / path
    b = p.read_bytes()
    PINS[path] = hashlib.sha256(b).hexdigest()
    return b.decode('utf-8-sig')


def js(path):
    return json.loads(read(path))


def lines(path):
    return [json.loads(l) for l in read(path).splitlines() if l.strip()]


def rows(path):
    return list(csv.DictReader(read(path).splitlines()))


def write(name, value):
    content = json.dumps(value, indent=2, sort_keys=True) + '\n'
    if name == 'FEASIBILITY_SAMPLE.json' and (OUT / name).exists() and (OUT / name).read_text() != content:
        raise ValueError('Frozen feasibility sample differs; preserve it and use a new research directory.')
    (OUT / name).write_text(content)


def main():
    started = time.perf_counter()
    tracker_path = 'jobs/leverage-campaign-check/output/shared-source/readiness-tracker/READINESS_BY_ORDER.csv'
    tracker = {r['instrument_id']: r for r in rows(tracker_path)}
    assert len(tracker) == 14972
    # Preserve the six accepted PR56 stage results without replaying incomplete sparse inputs.
    correction = js('research/excavator/astra-source-first-2026-10-23/TRACKER_COMPARISON_V3.json')['after']
    tracker.update(correction)
    frontier = {r['instrument_id']: r for r in lines('jobs/corpus-excavator/output/ORDER_FRONTIER.jsonl')}
    types = {r['instrument_id']: r for r in rows('jobs/x1-class-engine/output/TYPES.csv')}
    clusters = {r['instrument_id']: r for r in rows('jobs/x1-class-engine/output/CLUSTER_MEMBERS.csv')}
    clones = defaultdict(list)
    for r in lines('jobs/x1-class-engine/output/CLONED_CLAUSES.jsonl'):
        clones[r['instrument_id']].append(r)
    families = js('jobs/claim-kit/output/FAMILIES.json')
    sources = lines('jobs/corpus-excavator/output/SOURCE_ACTIONS.jsonl')
    packets = lines('jobs/lambertini/output/SAVINGS_PACKETS.jsonl')
    ownership = defaultdict(set)
    for p in sorted((ROOT / 'research/readiness/claims').glob('*.jsonl')):
        for r in lines(p.relative_to(ROOT).as_posix()):
            ownership[r['instrument_id']].add(p.name)
    pr54 = js(OUT.relative_to(ROOT).as_posix() + '/PR54_EXCLUSIONS.json')
    for iid in pr54['instrument_ids']:
        ownership[iid].add('PR54:attempted_b01_b02_b03')
    reservations = js('research/readiness/CLAIM_KIT_LOCK.json')
    for iid in reservations.get('orders', {}):
        ownership[iid].add('reserved')
    holds = {r['instrument_id'] for r in lines('research/readiness/SOURCE_AUDIT_HOLDS.jsonl') if r.get('state') == 'unresolved'}
    tree = {}
    for l in subprocess.check_output(['git', 'ls-tree', '-r', 'HEAD'], cwd=ROOT, text=True).splitlines():
        meta, path = l.split('\t', 1)
        tree[path] = meta.split()[2]
    by_family = defaultdict(list)
    for f in families:
        for iid in f['instrument_ids']:
            by_family[iid].append(f['family_id'])
    by_demand = defaultdict(list)
    for s in sources:
        for iid in set(s['affected_order_ids']):
            by_demand[iid].append(s['wanted_id'])
    inventory = []
    for iid, t in sorted(tracker.items()):
        x = types.get(iid, {})
        text = x.get('text_path', '')
        f = frontier.get(iid, {})
        c = clusters.get(iid, {})
        excluded = []
        if t['ready_for_human_review'] == 'yes': excluded.append('already_ready')
        if ownership[iid]: excluded.append('producer_or_reservation')
        if iid in holds: excluded.append('exact_claim_hold')
        inventory.append(dict(instrument_id=iid, era=f.get('era', 'unknown'),
            provisional_status=t['provisional_status'] or 'undecided',
            open_steps='|'.join(k[5:] for k, v in t.items() if k.startswith('step_') and v == 'open'),
            original_step=t['step_original_text'], ready=t['ready_for_human_review'],
            exclusions='|'.join(excluded), owners='|'.join(sorted(ownership[iid])),
            x1_type=x.get('type', ''), x1_class=x.get('class', ''),
            text_path=text, text_git_blob=tree.get(text, ''), text_local=bool(text and (ROOT / text).is_file()),
            representation_grade=x.get('text_grade', ''), cluster=c.get('cluster_id', ''),
            clone_status=c.get('clone_status', ''), cloned_spans=len(clones[iid]),
            family_ids='|'.join(sorted(by_family[iid])),
            source_demands='|'.join(sorted(by_demand[iid])), blockers=t['blockers']))
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=list(inventory[0])); w.writeheader(); w.writerows(inventory)
    (OUT / 'INVENTORY.csv.gz').write_bytes(gzip.compress(f.getvalue().encode(), mtime=0))
    unowned = {r['instrument_id'] for r in inventory if not r['exclusions']}
    inv = {r['instrument_id']:r for r in inventory}
    groups = {}
    for typ in sorted({r['x1_type'] for r in inventory if r['x1_type']}):
        members = [r for r in inventory if r['x1_type'] == typ and r['instrument_id'] in unowned]
        groups['pattern:' + typ] = dict(
            associated_outstanding_ids=[r['instrument_id'] for r in members],
            tracked_working_text_ids=[r['instrument_id'] for r in members if r['text_git_blob']],
            clone_ids=[r['instrument_id'] for r in members if r['clone_status'] == 'cloned'],
            applicability='Classification/text/clone leads only; no legal applicability or evidence-completeness inference.',
            proven_eligible_count=None)
    for f in families:
        if not f['family_id'].startswith('actor:'): continue
        ids = sorted(set(f['instrument_ids']) & unowned)
        if len(ids) < 2: continue
        groups[f['family_id']] = dict(associated_outstanding_ids=ids,
            existing_lambertini_packet=any(p['acting_id'] == f['family_id'][6:] for p in packets),
            applicability='Association only. Existing source-led workflow is baseline.', proven_eligible_count=None)
    unique_demand = {}
    for s in sources:
        ids = sorted(set(s['affected_order_ids']) & unowned)
        if not ids: continue
        key = s.get('expected_sha256') or s['wanted_id']
        d = unique_demand.setdefault(key, {'aliases':set(), 'ids':set(), 'steps':set(), 'urls':set()})
        d['aliases'].add(s['wanted_id']);d['ids'].update(ids);d['steps'].add(s['step']);d['urls'].update(s.get('urls',[]))
    for key, d in unique_demand.items():
        groups['demand:' + key] = {k: sorted(v) for k,v in d.items()}
        groups['demand:' + key]['proven_eligible_count'] = None
    write('GROUPS.json', groups)
    summary = dict(population=len(inventory), ready=sum(r['ready']=='yes' for r in inventory),
        unfinished=sum(r['ready']!='yes' for r in inventory),
        undecided=sum(r['provisional_status']=='undecided' for r in inventory),
        unowned_unready_without_hold=len(unowned),
        unfinished_steps=dict(Counter(s for r in inventory if r['ready']!='yes' for s in r['open_steps'].split('|') if s)),
        eras=dict(Counter(r['era'] for r in inventory if r['ready']!='yes')),
        source_demand_objects=len(unique_demand),
        source_demand_outstanding_orders=len(set().union(*(d['ids'] for d in unique_demand.values()))),
        shared_source_demand_objects=sum(len(d['ids'])>1 for d in unique_demand.values()),
        largest_patterns=[dict(type=k[8:], classified=len(v['associated_outstanding_ids']),
            tracked_working_texts=len(v['tracked_working_text_ids']), clones=len(v['clone_ids']))
            for k,v in sorted(((k,v) for k,v in groups.items() if k.startswith('pattern:')), key=lambda kv:-len(kv[1]['tracked_working_text_ids']))[:12]],
        largest_actors=[dict(actor=k[6:], associated=len(v['associated_outstanding_ids']),
            existing_packet=v['existing_lambertini_packet']) for k,v in sorted(((k,v) for k,v in groups.items() if k.startswith('actor:')),key=lambda kv:-len(kv[1]['associated_outstanding_ids']))[:12]],
        provenance_note='Tracker: PR55 run40054968047 resultc30ba4b; six accepted PR56 partial stages overlaid. Older profiler/type/family inputs supply leads only; dates used only for stratification. Census gaps outside14972 excluded. No current whole-corpus build claimed.',
        measured_agent_time=None, measured_tokens=None, qualifying_intervention_identified=False,
        eligibility_note='No mechanism yet has demonstrated applicability plus positive marginal benefit; all group memberships are screening candidates.',
        machine_seconds=round(time.perf_counter()-started,3))
    # Existing Neyman selector on the enumerated NRA working-text subset, for feasibility only.
    spec=importlib.util.spec_from_file_location('neyman',ROOT/'jobs/neyman/survey.py')
    neyman=importlib.util.module_from_spec(spec);spec.loader.exec_module(neyman)
    sample_frame=[]
    for iid in groups.get('pattern:nra_code_approval',{}).get('tracked_working_text_ids',[]):
        r=inv[iid]
        dims=(r['provisional_status'],r['clone_status'],r['representation_grade'])
        sample_frame.append(dict(instrument_id=iid,macro=r['provisional_status'],
            stratum=hashlib.sha256(json.dumps(dims).encode()).hexdigest(),
            text_path=r['text_path'],text_git_blob=r['text_git_blob'],clone_status=r['clone_status']))
    sample,allocation=neyman.sample(sample_frame,20261024,n=12)
    write('FEASIBILITY_SAMPLE.json',dict(seed=20261024,method='Existing Neyman SRS cells then one case per cell',
        target_requested=12, actual=len(sample),sample=sample,allocation=allocation,
        pool=len(sample_frame),purpose='Input and baseline feasibility only; not a production efficiency experiment.',
        limit='Neyman emits one case per distinct cell; extra fixed holdout requires a separate draw, not handpicked replacements.'))
    write('SUMMARY.json',summary)
    write('INPUT_PINS.json',dict(base='9ecddf9fe82a1989c6133610a77308ec74454184',pins=PINS,
        canonical_generation='c30ba4b40d4a8e328cd5ddcec3c11d88e807228c',
        derived_inputs_are_mixed_vintage=True,consumed_file_count=len(PINS)))
    print(json.dumps(summary,indent=2))


if __name__ == '__main__': main()
