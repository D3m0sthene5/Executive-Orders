"""Build/verify bounded derived histories from exact sealed source reviews.

Use --write NEW research/progress directory once; --verify EXISTING replays without
writing. Every producer record remains intact; only exact independently upheld
review scopes enter the separate accepted ledger. No canonical records change.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'jobs/claim-kit'))
import provision_history as H

PINS = {
    'source-production/CANDIDATES.json': 'a7195245ed6fb9b8af25beb9b709c645a12ed676ec22de863259307c352243cd',
    'typed-records/CANDIDATES.json': '2909930e72674c4b581b66f2f77651681a47d37738b29a68d6f19bff48582542',
    'independent-source-review/BLIND_REVIEW.json': '9535354051453236dd527a5bec6a96f16d76ab2ce4f4e0c08c7de2492770438a',
    'independent-source-review/AFTER_REVEAL.json': 'd8c118654227d4c1d39ddfc53205d5ac23db56f70a555c97d8f6d88ba12f7663',
    'independent-source-review/TYPED_DATE_REVIEW.json': '57b1a3b9ba2944ac3a70f7c7902ff5f5d2b0d0acaabaaae8aa2e82fc5c5c1c87',
}
QUERIES = [
    ('P:13934:sec3c-chapeau','2019-01-01'),
    ('P:13934:sec3c-chapeau','2020-08-01'),
    ('P:13934:sec3c-chapeau','2021-02-01'),
    ('P:13934:sec3c-chapeau','2022-01-01'),
    ('P:13934:sec3c-chapeau','2025-02-01'),
    ('P:13934:sec3cii-access','2025-02-01'),
    ('P:13933:sec5','2025-02-01'),
    ('P:13933:sec3a','2025-02-01'),
    ('P:13978:sec6-report','2025-02-01'),
    ('P:10900:food-for-peace-coordination','1961-02-01'),
    ('P:10900:food-for-peace-coordination','1966-01-01'),
    ('P:10900:food-for-peace-coordination','1978-01-01'),
    ('P:10900:food-for-peace-coordination','1981-01-01'),
    ('P:10893:sec111-food-for-peace','1961-10-01'),
]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(v):
    return (json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def inputs():
    docs = {}
    for rel, sha in PINS.items():
        raw = (HERE/rel).read_bytes()
        if digest(raw) != sha:
            raise ValueError('changed sealed source/review input: '+rel)
        docs[rel] = json.loads(raw)
    bundle = deepcopy(docs['typed-records/CANDIDATES.json'])
    records = {r.get('provision_id',r.get('transition_id')):r for r in bundle['provisions']+bundle['transitions']}
    selected = {}
    for rel in ('independent-source-review/BLIND_REVIEW.json', 'independent-source-review/AFTER_REVEAL.json',
                'independent-source-review/TYPED_DATE_REVIEW.json'):
        for r in docs[rel]['records']:
            rid = r['record_id']
            if r['verdict'] != 'upheld' or rid not in records or r['record_sha256'] != H.canonical_sha(records[rid]):
                continue
            k = (rid,r['scope'])
            if k in selected:
                raise ValueError('duplicate exact scope approval')
            selected[k] = {**r,'review_artifact':str((HERE/rel).relative_to(ROOT)),
                           'review_artifact_sha256':PINS[rel]}
    if sum(scope=='text' for _,scope in selected) != len(records):
        raise ValueError('not every genuine record has exact independent text review')
    ledger = {'schema':H.REVIEW_SCHEMA,'reviews':[selected[k] for k in sorted(selected)],
              'notice':'Exact upheld scopes only. Full blind rejections and unresolved effects remain in the sealed review artifacts. No whole-order or human certification.'}
    return bundle,ledger


def results(dest):
    bundle_path = dest/'BUNDLE.json'
    queries = [H.query(ROOT,bundle_path,pid,on) for pid,on in QUERIES]
    all_results = {'schema':'eo-provision-history-results/v1','queries':queries,
                   'notice':'Selected source-examined operations only; no complete legal interval or cutoff status.'}
    changed = {'record:T:13978:030-amend-13934-chapeau':'0'*64}
    impact = H.revalidation_report(all_results,changed)
    assert impact['affected_provisions']==['provision:P:13934:sec3c-chapeau']
    by = {(q['provision_id'],q['on']):q for q in queries}
    prior = by[('P:13934:sec3c-chapeau','2019-01-01')]
    assert prior['text_version'] is None, 'no text before its document witness'
    original = by[('P:13934:sec3c-chapeau','2020-08-01')]['text_version']
    amended = by[('P:13934:sec3c-chapeau','2021-02-01')]['text_version']
    restored = by[('P:13934:sec3c-chapeau','2025-02-01')]['text_version']
    assert original['text'] != amended['text'] == restored['text']
    assert restored['version_id']=='T:13978:030-amend-13934-chapeau'
    access = by[('P:13934:sec3cii-access','2025-02-01')]
    assert 'as expeditiously as possible' in access['text_version']['text']
    expiry = by[('P:13933:sec5','2025-02-01')]
    assert expiry['operative_state']=='unknown' and expiry['known_sunset_end_exclusive'] is None
    transfer = by[('P:10900:food-for-peace-coordination','1966-01-01')]
    assert transfer['executor'] and 'State' in transfer['executor']
    renumbered = by[('P:10900:food-for-peace-coordination','1978-01-01')]
    assert '5' in renumbered['label'] and renumbered['provision_id']==transfer['provision_id']
    retro = by[('P:10893:sec111-food-for-peace','1961-10-01')]
    assert any(x['retroactive_effect'] for x in retro['transition_details'])
    assert retro['operative_state']=='unknown', 'source date alone does not prove provision-wide effect'
    for q in queries:
        assert not q['canonical_approval'] and not q['human_certified'] and not q['completeness_guaranteed']
    summary = {'provisions':7,'transitions':16,'dated_queries':len(queries),
               'exact_text_reviewed_records':23,'legal_effect_reviewed_records':1,
               'checked_features':['correct amended restoration','same-actor distinct amendment','pre-witness text refusal',
                    'conditional expiry stays unresolved','stable renumbered identity','reviewed transfer',
                    'retroactivity disclosure','separate text/legal-effect scopes','Valla revalidation closure'],
               'canonical_writes':0,'model_tokens':None,'notice':all_results['notice']}
    return {'QUERIES.json':all_results,'CHANGED_HASHES.json':changed,'REVALIDATION.json':impact,'SUMMARY.json':summary}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--write',type=Path);group.add_argument('--verify',type=Path)
    a=p.parse_args();dest=(a.write or a.verify).resolve()
    if not dest.is_relative_to(ROOT/'research/progress'):
        raise ValueError('output outside research/progress')
    bundle,ledger=inputs();ledger_raw=encoded(ledger)
    bundle['review_file']={'path':str((dest/'ACCEPTED_REVIEWS.json').relative_to(ROOT)),'sha256':digest(ledger_raw)}
    bundle['review_process']={'type':'independent_ai_scoped_review','different_family':False,
                              'frozen_inputs':PINS,'control_count':3,'controls_caught':3}
    first={'ACCEPTED_REVIEWS.json':ledger,'BUNDLE.json':bundle}
    if a.write:
        dest.mkdir(parents=True,exist_ok=False)
        for name,doc in first.items():(dest/name).write_bytes(encoded(doc))
    else:
        for name,doc in first.items():
            if (dest/name).read_bytes()!=encoded(doc):raise ValueError('changed derived input: '+name)
    derived=results(dest)
    for name,doc in derived.items():
        if a.write:(dest/name).write_bytes(encoded(doc))
        elif (dest/name).read_bytes()!=encoded(doc):raise ValueError('changed derived result: '+name)
    print(json.dumps(derived['SUMMARY.json'],sort_keys=True))


if __name__=='__main__':main()
