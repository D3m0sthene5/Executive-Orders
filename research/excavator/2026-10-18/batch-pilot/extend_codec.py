"""Replay the frozen fifty and profile actual current-corpus shared provisions.

No source acquisition or legal adjudication. Large JSON stays on disk; only a
small metric receipt is printed. Frozen inputs are retrieved by exact Git blob.
"""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'jobs/claim-kit'))
import batch


def sha(raw): return hashlib.sha256(raw).hexdigest()
def pretty(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def run():
    started = time.perf_counter()
    pilot = ROOT/'research/production/claim-kit-pilot-2026-10-18'
    freeze = json.loads((pilot/'FREEZE_MANIFEST.json').read_bytes())
    dossiers, pins = {}, {}
    for path in sorted((pilot/'local-dossiers').glob('EO_*.json')):
        held = pilot/'full-dossiers'/path.name
        origin = held.relative_to(ROOT).as_posix()
        if held.exists(): raw = held.read_bytes()
        else:
            origin = freeze['output_commit']+':jobs/claim-kit/output/dossiers/'+path.name
            raw = subprocess.check_output(['git','show',origin],cwd=ROOT)
        d = json.loads(raw)
        assert d['fingerprint'] == batch.canonical_sha(d)
        dossiers[d['instrument_id']] = d
        pins[d['instrument_id']] = {'origin':origin,'file_sha256':sha(raw),'fingerprint':d['fingerprint']}
    assert len(dossiers) == 50
    encoded = batch.encode(dossiers, ROOT)
    assert batch.decode(encoded) == dossiers
    flight = {iid:batch.preflight(d,ROOT) for iid,d in dossiers.items()}
    tasks = {}
    for f in flight.values():
        for t in f['mechanical_tasks']:
            r = tasks.setdefault(t['task_id'],{**t,'affected_orders':[]})
            r['affected_orders'].append(f['instrument_id'])
    packet = {'schema':batch.SCHEMA,'agent':'codec-extension-only','input_pins':pins,
              'ownership':{},'preflight':flight,'shared_tasks':list(tasks.values()),
              'families':batch.family_groups(dossiers),**encoded}
    view = batch.render(packet,dossiers)
    nonredundant = []
    overflow = []
    for iid,d in dossiers.items():
        for eid,e in d['evidence'].items():
            if e.get('provision_text') and e['provision_text'] != e.get('text'):
                nonredundant.append({'instrument_id':iid,'evidence_id':eid,'field':'provision_text'})
            for a in e.get('alternative_provisions',[]):
                if not any(other.get('id')==a.get('id') and all(other.get(k)==v for k,v in a.items()) for other in d['evidence'].values()):
                    nonredundant.append({'instrument_id':iid,'evidence_id':eid,'field':'alternative_provisions'})
        for ctx in d.get('actor_contexts',[]):
            if ctx.get('overflow'): overflow.append({'instrument_id':iid,**ctx})
    baseline = sum(len(pretty(d)) for d in dossiers.values())
    results = {'schema':'eo-batch-fifty-codec-extension/v1','orders':50,
        'historical_outcomes':{'accepted_frozen':12,'unable':38},'exact_value_reconstruction':True,
        'baseline_pretty_json_bytes':baseline,'lossless_packet_bytes':len(pretty(packet)),
        'readable_bytes':len(view.encode()),'combined_representation_bytes':len(pretty(packet))+len(view.encode()),
        'unique_held_text_file_hash_checks':len(encoded['held_text_file_pins']),
        'shared_text_blocks':len(encoded['text_blocks']),'source_catalogue_entries':len(encoded['sources']),
        'shared_objects':len(encoded['shared_objects']),'codec_issues':encoded['codec_issues'],
        'nonredundant_excluded_metadata':nonredundant,'overflow_records':overflow,
        'frozen_output_commit':freeze['output_commit'],'input_pins':pins,
        'code_sha256':sha((ROOT/'jobs/claim-kit/batch.py').read_bytes()),
        'wall_seconds':round(time.perf_counter()-started,4),
        'limits':['Value reconstruction covers fifty; independent readable legal-material audit covers six.',
                  'Sizes are representations, not tokens; do not add separate representation savings.',
                  'No new legal or readiness conclusion follows from frozen historical outcome labels.']}
    batch.dump(HERE/'FIFTY_CODEC_EXTENSION.json',results)
    # One metadata-only corpus pass identifies where actual shared evidence exists.
    started = time.perf_counter()
    current = {}
    declarations = collections.Counter()
    for p in sorted((ROOT/'jobs/claim-kit/output/dossiers').glob('*.json')):
        d=json.loads(p.read_bytes());assert d['fingerprint']==batch.canonical_sha(d)
        current[d['instrument_id']] = d
        for e in d['evidence'].values():
            s=e.get('source') or e.get('actor_source') or {}
            if s.get('text_sha256'): declarations[s['text_sha256']] += 1
    groups=batch.family_groups(current)
    shared=[g for g in groups if g['orders']>1]
    corpus={'schema':'eo-batch-corpus-opportunity/v1','dossiers':len(current),
        'actual_shared_provision_groups':len(shared),
        'orders_in_shared_provision_groups':len({m['instrument_id'] for g in shared for m in g['members']}),
        'shared_provision_memberships':sum(g['orders'] for g in shared),
        'text_evidence_declarations':sum(declarations.values()),'distinct_text_hashes':len(declarations),
        'repeated_declarations_not_measured_agent_reads':sum(n-1 for n in declarations.values()),
        'largest_shared_provision_groups':shared[:20],
        'wall_seconds':round(time.perf_counter()-started,4),
        'limits':['Shared provenance/operative pattern is a grouping lead; per-member legal checks remain mandatory.',
                  'Repeated declarations are potential reuse, not measured avoided source reads or outcomes.']}
    batch.dump(HERE/'CORPUS_OPPORTUNITY.json',corpus)
    print(json.dumps({'fifty':{k:results[k] for k in ('orders','exact_value_reconstruction','baseline_pretty_json_bytes','lossless_packet_bytes','readable_bytes','unique_held_text_file_hash_checks','wall_seconds')},
                      'nonredundant_excluded_metadata':len(nonredundant),'overflow':len(overflow),
                      'corpus':{k:corpus[k] for k in ('dossiers','actual_shared_provision_groups','orders_in_shared_provision_groups','repeated_declarations_not_measured_agent_reads','wall_seconds')}}))

if __name__=='__main__':run()
